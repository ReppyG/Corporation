"""Persistent shared-memory system for the agent-builder framework.

Storage layout (default root ``~/.openclaw/nexus/memory/``)::

    memory/
        shared_context.json        – organisation-wide shared state
        <agent_id>.json            – per-agent private memory
        messages_YYYY-MM-DD.json   – daily message logs
        decisions.json             – decision audit trail
        archive/
            messages_<range>.json  – archived message logs

Concurrent access is serialised with advisory file locks (``fcntl`` on
POSIX, ``msvcrt`` on Windows).
"""

import json
import os
import platform
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class MemoryLockTimeout(Exception):
    """Raised when a file lock cannot be acquired within the timeout."""


# ---------------------------------------------------------------------------
# File locking helpers
# ---------------------------------------------------------------------------

if platform.system() == "Windows":
    import msvcrt

    def _lock_file(fh) -> None:
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)

    def _unlock_file(fh) -> None:
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
else:
    import fcntl

    def _lock_file(fh) -> None:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)

    def _unlock_file(fh) -> None:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


class _FileLock:
    """Context-manager advisory lock around a JSON data file.

    A ``<filename>.lock`` file is created as the lock target.
    """

    TIMEOUT_SECONDS = 5.0

    def __init__(self, data_path: Path):
        self._lock_path = data_path.parent / (data_path.name + ".lock")
        self._fh = None

    def __enter__(self):
        import time

        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(self._lock_path, "w", encoding="utf-8")
        deadline = time.monotonic() + self.TIMEOUT_SECONDS
        while True:
            try:
                _lock_file(self._fh)
                return self
            except (IOError, OSError):
                if time.monotonic() >= deadline:
                    self._fh.close()
                    raise MemoryLockTimeout(
                        f"Could not acquire lock on {self._lock_path} "
                        f"within {self.TIMEOUT_SECONDS}s"
                    )
                time.sleep(0.05)

    def __exit__(self, *_):
        if self._fh:
            try:
                _unlock_file(self._fh)
            finally:
                self._fh.close()
                self._fh = None


# ---------------------------------------------------------------------------
# Low-level I/O helpers
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_write(path: Path, data: Dict[str, Any]) -> None:
    """Write *data* to *path* atomically (write-to-temp + rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
    except Exception:
        os.unlink(tmp_path)
        raise
    os.replace(tmp_path, str(path))


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class SharedMemory:
    """Persistent shared-memory store for agents.

    Parameters
    ----------
    storage_type:
        Only ``"json"`` is currently supported.
    data_dir:
        Root directory for memory files.  Defaults to
        ``~/.openclaw/nexus/memory/``.
    """

    DEFAULT_DIR = str(Path.home() / ".openclaw" / "nexus" / "memory")
    MAX_ACTIONS_PER_AGENT = 100

    def __init__(
        self,
        storage_type: str = "json",
        data_dir: str = DEFAULT_DIR,
    ):
        if storage_type != "json":
            raise ValueError("Only json storage_type is currently supported")
        self.storage_type = storage_type
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "archive").mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _agent_path(self, agent_id: str) -> Path:
        return self.data_dir / f"{agent_id}.json"

    def _shared_path(self) -> Path:
        return self.data_dir / "shared_context.json"

    def _messages_path(self, date_str: Optional[str] = None) -> Path:
        if date_str is None:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.data_dir / f"messages_{date_str}.json"

    def _decisions_path(self) -> Path:
        return self.data_dir / "decisions.json"

    def _read_store(self, path: Path) -> Dict[str, Any]:
        with _FileLock(path):
            return _read_json(path)

    def _write_store(self, path: Path, data: Dict[str, Any]) -> None:
        with _FileLock(path):
            _atomic_write(path, data)

    def _update_store(self, path: Path, updater) -> None:
        """Read → apply *updater(data)* → write, all under lock."""
        with _FileLock(path):
            data = _read_json(path)
            updater(data)
            _atomic_write(path, data)

    # ------------------------------------------------------------------
    # Core Operations
    # ------------------------------------------------------------------

    def save(self, key: str, value: dict, agent_id: Optional[str] = None) -> None:
        """Persist *value* under *key*.

        If *agent_id* is given the entry is stored in that agent's private
        file; otherwise it goes into the shared context.
        """
        path = self._agent_path(agent_id) if agent_id else self._shared_path()
        entry = {
            "value": value,
            "timestamp": _utc_now(),
            "creator": agent_id,
        }

        def _up(data):
            data[key] = entry

        self._update_store(path, _up)

    def load(self, key: str, agent_id: Optional[str] = None) -> Optional[dict]:
        """Load the value stored under *key*.

        Returns the raw value dict (without metadata), or ``None`` if not found.
        """
        path = self._agent_path(agent_id) if agent_id else self._shared_path()
        data = self._read_store(path)
        entry = data.get(key)
        if entry is None:
            return None
        # Support both the new format and the old flat format for backward compat
        if isinstance(entry, dict) and "value" in entry and "timestamp" in entry:
            return entry["value"]
        return entry

    def load_entry(self, key: str, agent_id: Optional[str] = None) -> Optional[dict]:
        """Like :meth:`load` but returns the full entry including timestamp and creator."""
        path = self._agent_path(agent_id) if agent_id else self._shared_path()
        data = self._read_store(path)
        return data.get(key)

    def delete(self, key: str, agent_id: Optional[str] = None) -> bool:
        """Remove *key* from memory.  Returns ``True`` if it existed."""
        path = self._agent_path(agent_id) if agent_id else self._shared_path()
        removed = [False]

        def _up(data):
            if key in data:
                del data[key]
                removed[0] = True

        self._update_store(path, _up)
        return removed[0]

    def search(
        self, query: str, agent_id: Optional[str] = None
    ) -> List[dict]:
        """Substring search across keys and values.

        Returns
        -------
        list of dict
            Matching entries with ``{key, value, timestamp, creator, score}``
            sorted by score descending.
        """
        path = self._agent_path(agent_id) if agent_id else self._shared_path()
        data = self._read_store(path)
        query_l = query.lower()
        results = []
        for k, entry in data.items():
            blob = json.dumps({"key": k, "entry": entry}, ensure_ascii=False).lower()
            if query_l in blob:
                count = blob.count(query_l)
                if isinstance(entry, dict) and "value" in entry:
                    value = entry.get("value")
                    timestamp = entry.get("timestamp")
                    creator = entry.get("creator")
                else:
                    value = entry
                    timestamp = None
                    creator = None
                results.append({
                    "key": k,
                    "value": value,
                    "timestamp": timestamp,
                    "creator": creator,
                    "score": count,
                })
        results.sort(key=lambda r: r["score"], reverse=True)
        return results

    # ------------------------------------------------------------------
    # Agent-Specific Context Management
    # ------------------------------------------------------------------

    def get_agent_context(self, agent_id: str, limit: int = 10) -> dict:
        """Retrieve recent context for *agent_id*.

        Returns
        -------
        dict
            ``{agent_id, recent_messages, task_queue, completed_tasks,
            last_update, matches}``
        """
        path = self._agent_path(agent_id)
        data = self._read_store(path)
        meta = data.get("metadata", {})
        actions = data.get("actions", [])

        recent_messages = [
            a for a in actions if a.get("action") == "receive_message"
        ][-limit:]

        task_queue = [
            a for a in actions if a.get("action") in ("assign_task", "receive_task")
        ][-limit:]

        completed_tasks = [
            a for a in actions if a.get("action") == "complete_task"
        ][-limit:]

        # Also return flat search matches for backward compat with old callers
        matches = self.search(agent_id)[:limit]

        return {
            "agent_id": agent_id,
            "recent_messages": recent_messages,
            "task_queue": task_queue,
            "completed_tasks": completed_tasks,
            "last_update": meta.get("last_updated"),
            "matches": matches,
        }

    def save_agent_action(
        self, agent_id: str, action: str, details: dict
    ) -> None:
        """Record an action in the agent's private memory (keeps last 100)."""
        path = self._agent_path(agent_id)
        now = _utc_now()

        def _up(data):
            if "metadata" not in data:
                data["metadata"] = {
                    "agent_id": agent_id,
                    "created": now,
                }
            data["metadata"]["last_updated"] = now

            actions = data.get("actions", [])
            actions.append({
                "timestamp": now,
                "action": action,
                **details,
            })
            # Prune to MAX_ACTIONS_PER_AGENT
            data["actions"] = actions[-self.MAX_ACTIONS_PER_AGENT:]

        self._update_store(path, _up)

    # ------------------------------------------------------------------
    # Organisation-Wide Context
    # ------------------------------------------------------------------

    def save_org_state(self, org_name: str, state: dict) -> None:
        """Persist the organisation's status dict."""
        path = self._shared_path()

        def _up(data):
            data["organization"] = org_name
            data["org_state"] = {**state, "last_updated": _utc_now()}

        self._update_store(path, _up)

    def get_org_state(self, org_name: str) -> dict:
        """Retrieve the organisation's status dict."""
        data = self._read_store(self._shared_path())
        return data.get("org_state", {})

    def save_decision(
        self,
        agent_id: str,
        decision: str,
        reasoning: str,
        authority_level: int,
    ) -> None:
        """Append a decision to the audit log."""
        path = self._decisions_path()

        def _up(data):
            decisions = data.get("decisions", [])
            decisions.append({
                "timestamp": _utc_now(),
                "agent_id": agent_id,
                "decision": decision,
                "reasoning": reasoning,
                "authority": authority_level,
            })
            data["decisions"] = decisions

        self._update_store(path, _up)

    # ------------------------------------------------------------------
    # Message History
    # ------------------------------------------------------------------

    def save_message(
        self, from_agent: str, to_agent: str, message: str
    ) -> None:
        """Persist a message in the daily message log."""
        path = self._messages_path()

        def _up(data):
            msgs = data.get("messages", [])
            msgs.append({
                "from": from_agent,
                "to": to_agent,
                "content": message,
                "timestamp": _utc_now(),
            })
            data["messages"] = msgs

        self._update_store(path, _up)

    def get_message_history(
        self,
        agent_id: Optional[str] = None,
        days: int = 7,
    ) -> List[dict]:
        """Retrieve messages from the last *days* days.

        If *agent_id* is given, only messages sent to or from that agent are
        returned.
        """
        results = []
        today = datetime.now(timezone.utc).date()
        for delta in range(days):
            date_str = (today - timedelta(days=delta)).strftime("%Y-%m-%d")
            path = self._messages_path(date_str)
            if not path.exists():
                continue
            data = self._read_store(path)
            for msg in data.get("messages", []):
                if agent_id is None or msg.get("from") == agent_id or msg.get("to") == agent_id:
                    results.append(msg)
        return results

    # ------------------------------------------------------------------
    # Cleanup & Archival
    # ------------------------------------------------------------------

    def archive_old_memory(self, days_threshold: int = 30) -> None:
        """Move message files older than *days_threshold* days to the archive."""
        archive_dir = self.data_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        cutoff = datetime.now(timezone.utc).date() - timedelta(days=days_threshold)

        for msg_file in self.data_dir.glob("messages_*.json"):
            try:
                date_str = msg_file.stem.replace("messages_", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                continue
            if file_date < cutoff:
                dest = archive_dir / msg_file.name
                msg_file.replace(dest)

    def cleanup_expired_context(
        self, agent_id: str, max_actions: int = 100
    ) -> None:
        """Trim the agent's action log to *max_actions* entries."""
        path = self._agent_path(agent_id)

        def _up(data):
            actions = data.get("actions", [])
            if len(actions) > max_actions:
                data["actions"] = actions[-max_actions:]

        self._update_store(path, _up)

    # ------------------------------------------------------------------
    # Memory Statistics
    # ------------------------------------------------------------------

    def get_memory_stats(self) -> dict:
        """Return overall memory statistics."""
        agent_ids = set()
        total_entries = 0
        total_bytes = 0
        oldest_ts: Optional[datetime] = None
        messages_today = 0

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        for json_file in self.data_dir.glob("*.json"):
            total_bytes += json_file.stat().st_size
            data = _read_json(json_file)

            if json_file.name == "shared_context.json":
                for k, v in data.items():
                    if isinstance(v, dict) and "timestamp" in v:
                        total_entries += 1
                        try:
                            ts = datetime.fromisoformat(v["timestamp"])
                            if oldest_ts is None or ts < oldest_ts:
                                oldest_ts = ts
                        except (ValueError, TypeError):
                            pass
            elif json_file.name.startswith("messages_"):
                if today_str in json_file.name:
                    messages_today += len(data.get("messages", []))
            elif json_file.name not in ("decisions.json",):
                # Agent file
                agent_id = json_file.stem
                agent_ids.add(agent_id)
                actions = data.get("actions", [])
                total_entries += len(actions)
                for a in actions:
                    try:
                        ts = datetime.fromisoformat(a.get("timestamp", ""))
                        if oldest_ts is None or ts < oldest_ts:
                            oldest_ts = ts
                    except (ValueError, TypeError):
                        pass

        oldest_days = 0
        if oldest_ts:
            oldest_days = (datetime.now(timezone.utc) - oldest_ts).days

        return {
            "agent_count": len(agent_ids),
            "total_entries": total_entries,
            "memory_size_mb": total_bytes / (1024 * 1024),
            "oldest_entry_days": oldest_days,
            "messages_today": messages_today,
        }
