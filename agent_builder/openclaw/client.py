"""OpenClaw API client for communicating with OpenClaw instances on Oracle Cloud."""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, Future
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class OpenClawError(Exception):
    """Base exception for all OpenClaw errors."""

    def __init__(self, message: str, status_code: int = 0, details: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class OpenClawTimeout(OpenClawError):
    """Raised when a request to OpenClaw times out."""


class AgentNotFound(OpenClawError):
    """Raised when the requested agent does not exist in OpenClaw."""


class AgentCreationError(OpenClawError):
    """Raised when agent creation fails."""


class AgentInitializationError(OpenClawError):
    """Raised when agent initialization fails."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _with_backoff(fn: Callable, retries: int = 3, base_delay: float = 1.0):
    """Call *fn* with exponential backoff retries.

    Waits 1 s → 2 s → 4 s between attempts.  Reraises the last exception if
    all retries are exhausted.
    """
    delay = base_delay
    last_exc: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except (OpenClawTimeout, requests.exceptions.Timeout) as exc:
            last_exc = exc
            if attempt < retries:
                logger.warning(
                    "OpenClaw request timed out (attempt %d/%d), retrying in %.0fs …",
                    attempt, retries, delay,
                )
                time.sleep(delay)
                delay *= 2
        except OpenClawError as exc:
            # Only retry on 5xx server errors
            if exc.status_code >= 500 and attempt < retries:
                last_exc = exc
                logger.warning(
                    "OpenClaw server error %d (attempt %d/%d), retrying in %.0fs …",
                    exc.status_code, attempt, retries, delay,
                )
                time.sleep(delay)
                delay *= 2
            else:
                raise
    raise last_exc


def _build_session(auth_token: Optional[str] = None) -> requests.Session:
    """Build a requests.Session with connection pooling and a retry adapter."""
    session = requests.Session()
    if auth_token:
        session.headers.update({"Authorization": f"Bearer {auth_token}"})
    session.headers.update({"Content-Type": "application/json"})

    # Only retry on connection-level failures (not on HTTP errors so we can
    # inspect the status code ourselves).
    adapter = HTTPAdapter(
        max_retries=Retry(
            total=0,
            connect=2,
            read=0,
            backoff_factor=0.5,
        )
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


# ---------------------------------------------------------------------------
# Main Client
# ---------------------------------------------------------------------------

class OpenClawClient:
    """Client for the OpenClaw agent runtime API.

    Parameters
    ----------
    gateway_url:
        Base URL of the OpenClaw gateway (default ``http://localhost:18789``).
    auth_token:
        Optional bearer token for authenticated requests.
    connect_timeout:
        Seconds to wait for a TCP connection.
    read_timeout:
        Seconds to wait for the server to send a response.
    """

    DEFAULT_GATEWAY = "http://localhost:18789"
    REQUEST_TIMEOUT = 30  # seconds for most requests
    PROMPT_TIMEOUT = 60   # seconds for think/prompt requests

    def __init__(
        self,
        gateway_url: str = DEFAULT_GATEWAY,
        auth_token: Optional[str] = None,
        connect_timeout: float = 5.0,
        read_timeout: float = REQUEST_TIMEOUT,
        validate_on_init: bool = True,
    ):
        self.gateway_url = gateway_url.rstrip("/")
        self.auth_token = auth_token
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self._session = _build_session(auth_token)
        self._executor = ThreadPoolExecutor(max_workers=4)

        if validate_on_init:
            if not self.health_check():
                logger.warning(
                    "OpenClaw at %s did not respond to health check during init.",
                    self.gateway_url,
                )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _url(self, path: str) -> str:
        return f"{self.gateway_url}/{path.lstrip('/')}"

    def _request(
        self,
        method: str,
        path: str,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> requests.Response:
        """Execute an HTTP request with logging and error mapping."""
        url = self._url(path)
        effective_timeout = (self.connect_timeout, timeout or self.read_timeout)

        logger.debug("[openclaw] %s %s", method.upper(), url)
        start = time.monotonic()
        try:
            resp = self._session.request(method, url, timeout=effective_timeout, **kwargs)
        except requests.exceptions.Timeout as exc:
            elapsed = time.monotonic() - start
            logger.error("[openclaw] %s %s timed out after %.2fs", method.upper(), url, elapsed)
            raise OpenClawTimeout(
                f"Request to {url} timed out after {elapsed:.1f}s"
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise OpenClawError(f"Cannot connect to OpenClaw at {self.gateway_url}: {exc}") from exc

        elapsed = time.monotonic() - start
        logger.debug(
            "[openclaw] %s %s → %d (%.3fs)", method.upper(), url, resp.status_code, elapsed
        )

        self._raise_for_status(resp)
        return resp

    @staticmethod
    def _raise_for_status(resp: requests.Response) -> None:
        """Map HTTP status codes to OpenClaw exceptions."""
        code = resp.status_code
        if code < 400:
            return

        try:
            body = resp.json()
            message = body.get("error") or body.get("message") or resp.text
        except Exception:
            message = resp.text or f"HTTP {code}"

        if code == 401:
            raise OpenClawError("Unauthorized – check your auth token.", code, {"body": message})
        if code == 404:
            raise AgentNotFound(f"Resource not found: {message}", code)
        if code == 400:
            raise OpenClawError(f"Bad request: {message}", code)
        if code == 503:
            raise OpenClawError(f"OpenClaw service unavailable: {message}", code)
        raise OpenClawError(f"OpenClaw error {code}: {message}", code)

    def _request_with_backoff(self, method: str, path: str, **kwargs) -> requests.Response:
        """Execute request with exponential backoff retry logic."""
        return _with_backoff(lambda: self._request(method, path, **kwargs))

    # ------------------------------------------------------------------
    # Health & Monitoring
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Return ``True`` if OpenClaw responds to the ``/health`` endpoint."""
        try:
            self._request("GET", "/health", timeout=5.0)
            return True
        except (OpenClawError, OpenClawTimeout):
            return False

    def get_system_stats(self) -> dict:
        """Return system-level statistics from OpenClaw.

        Returns
        -------
        dict
            ``{agents_online, agents_total, memory_used_mb, uptime_seconds}``
        """
        resp = self._request_with_backoff("GET", "/api/system/stats")
        return resp.json()

    # ------------------------------------------------------------------
    # Agent Lifecycle
    # ------------------------------------------------------------------

    def create_agent(self, agent_id: str, config: dict) -> dict:
        """Create a new agent in OpenClaw.

        Parameters
        ----------
        agent_id:
            Unique identifier for the new agent.
        config:
            Agent configuration dict (``name``, ``role``, ``model``).

        Returns
        -------
        dict
            ``{workspace_id: str, status_code: int}``

        Raises
        ------
        AgentCreationError
            If the API returns an error.
        """
        payload = {"agent_id": agent_id, **config}

        def _do():
            try:
                resp = self._request("POST", "/api/agents/create", json=payload)
            except OpenClawError as exc:
                raise AgentCreationError(
                    f"Failed to create agent '{agent_id}': {exc}",
                    exc.status_code,
                    exc.details,
                ) from exc
            body = resp.json()
            return {
                "workspace_id": body.get("workspace_id", ""),
                "status_code": resp.status_code,
            }

        return _with_backoff(_do)

    def initialize_agent(self, agent_id: str) -> dict:
        """Activate an agent inside OpenClaw and wait for acknowledgment.

        Raises
        ------
        AgentInitializationError
        """
        def _do():
            try:
                resp = self._request(
                    "POST",
                    f"/api/agents/{agent_id}/initialize",
                    timeout=2.0,
                )
            except OpenClawError as exc:
                raise AgentInitializationError(
                    f"Failed to initialize agent '{agent_id}': {exc}",
                    exc.status_code,
                    exc.details,
                ) from exc
            return resp.json()

        result = _with_backoff(_do)
        logger.info("[openclaw] Agent '%s' initialized: %s", agent_id, result)
        return result

    def delete_agent(self, agent_id: str) -> bool:
        """Remove an agent from OpenClaw.

        Returns
        -------
        bool
            ``True`` on success, ``False`` if the agent was not found.
        """
        try:
            self._request_with_backoff("DELETE", f"/api/agents/{agent_id}")
            return True
        except AgentNotFound:
            return False

    def get_agent_status(self, agent_id: str) -> dict:
        """Query an agent's online/offline status.

        Returns
        -------
        dict
            ``{status: "online"|"offline", last_seen: ISO8601 timestamp}``
        """
        resp = self._request_with_backoff("GET", f"/api/agents/{agent_id}/status")
        return resp.json()

    # ------------------------------------------------------------------
    # Message Routing
    # ------------------------------------------------------------------

    def send_message(self, from_agent: str, to_agent: str, message: str) -> bool:
        """Send a message from one agent to another.

        Returns
        -------
        bool
            ``True`` on success.
        """
        payload = {
            "from_agent_id": from_agent,
            "to_agent_id": to_agent,
            "content": message,
            "timestamp": _utc_now(),
        }
        resp = self._request_with_backoff("POST", "/api/messages/send", json=payload)
        body = resp.json()
        logger.debug(
            "[openclaw] Message sent from '%s' to '%s', message_id=%s",
            from_agent, to_agent, body.get("message_id"),
        )
        return True

    def broadcast_message(
        self, from_agent: str, to_agents: List[str], message: str
    ) -> dict:
        """Send a message to multiple agents simultaneously.

        Returns
        -------
        dict
            ``{message_id: str, delivery_status: {agent_id: bool, ...}}``
        """
        payload = {
            "from_agent_id": from_agent,
            "to_agent_ids": to_agents,
            "content": message,
            "timestamp": _utc_now(),
        }
        resp = self._request_with_backoff("POST", "/api/messages/broadcast", json=payload)
        return resp.json()

    def get_inbox(self, agent_id: str) -> List[dict]:
        """Retrieve (and clear) pending messages for *agent_id*.

        Returns
        -------
        list of dict
            Each entry: ``{from_agent, content, timestamp, message_id}``
        """
        resp = self._request_with_backoff("GET", f"/api/agents/{agent_id}/inbox")
        return resp.json().get("messages", [])

    # ------------------------------------------------------------------
    # Agent Communication Channels
    # ------------------------------------------------------------------

    def send_prompt(
        self, agent_id: str, prompt: str, system_context: str = ""
    ) -> str:
        """Send a thinking prompt to an agent and return its response.

        Parameters
        ----------
        agent_id:
            Target agent.
        prompt:
            The prompt text.
        system_context:
            Optional system-level context injected before the prompt.

        Returns
        -------
        str
            The agent's response text.

        Raises
        ------
        OpenClawTimeout
            If the agent does not respond within 60 seconds.
        OpenClawError
            On any other server-side failure.
        """
        payload = {
            "prompt": prompt,
            "system_prompt": system_context,
            "temperature": 0.7,
        }

        def _do():
            resp = self._request(
                "POST",
                f"/api/agents/{agent_id}/think",
                json=payload,
                timeout=self.PROMPT_TIMEOUT,
            )
            body = resp.json()
            return body.get("response", "")

        return _with_backoff(_do)

    def subscribe_to_agent_updates(
        self, agent_id: str, callback: Callable[[dict], None]
    ) -> Future:
        """Register a callback for agent state changes.

        The callback is invoked (in a background thread) whenever the agent
        transitions state or receives a message.  This implementation polls
        the status endpoint every 5 seconds.

        Parameters
        ----------
        agent_id:
            Agent to monitor.
        callback:
            Callable that accepts a state-change dict.

        Returns
        -------
        concurrent.futures.Future
            Can be cancelled to stop polling.
        """
        def _poll():
            last_status: Optional[str] = None
            while True:
                try:
                    status_data = self.get_agent_status(agent_id)
                    current = status_data.get("status")
                    if current != last_status:
                        callback(status_data)
                        last_status = current
                except OpenClawError as exc:
                    logger.warning(
                        "[openclaw] subscribe_to_agent_updates error for '%s': %s",
                        agent_id, exc,
                    )
                time.sleep(5)

        return self._executor.submit(_poll)

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._session.close()
        self._executor.shutdown(wait=False)
