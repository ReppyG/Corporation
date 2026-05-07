import logging
import time
from abc import ABC, abstractmethod
from typing import List, Optional

logger = logging.getLogger(__name__)


class InvalidAPIKey(Exception):
    """Raised when an LLM provider API key is missing or rejected."""


class LLMProvider(ABC):
    """Abstract base class for all LLM provider integrations.

    Parameters
    ----------
    api_key:
        Provider API key.
    model:
        Model identifier string (e.g. ``"gemini-2.5-flash"``).
    temperature:
        Default sampling temperature (0.0 – 1.0).  Concrete providers may
        override this per-request.
    """

    def __init__(self, api_key: str, model: str, temperature: float = 0.7):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
    ) -> str:
        """Generate a single-turn response.

        Parameters
        ----------
        prompt:
            User prompt text.
        system_prompt:
            Optional system-level instruction.
        temperature:
            Override sampling temperature for this request.

        Returns
        -------
        str
            Generated response text.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_with_context(self, messages: List[dict]) -> str:
        """Generate a response given a full conversation history.

        Parameters
        ----------
        messages:
            List of ``{role: "system"|"user"|"assistant", content: str}`` dicts.
            A ``"system"`` role message, if present, must be the first entry.

        Returns
        -------
        str
            Generated response text.
        """
        raise NotImplementedError

    @abstractmethod
    def validate_key(self) -> bool:
        """Return ``True`` if the API key is valid.

        Raises
        ------
        InvalidAPIKey
            If the key is rejected by the provider.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Optional helpers (default implementations)
    # ------------------------------------------------------------------

    def count_tokens(self, text: str) -> int:
        """Estimate the token count for *text* (whitespace tokenisation fallback).

        Concrete providers should override this with library-specific counting.
        """
        return len(text.split())

    def get_cost_estimate(self, tokens_in: int, tokens_out: int) -> float:
        """Return an estimated cost in USD for a request.

        Override in concrete providers with current pricing.
        """
        return 0.0

    # ------------------------------------------------------------------
    # Internal retry helper
    # ------------------------------------------------------------------

    @staticmethod
    def _retry_with_backoff(fn, retries: int = 3, base_delay: float = 1.0):
        """Call *fn* with exponential backoff on transient errors."""
        delay = base_delay
        last_exc: Optional[Exception] = None
        for attempt in range(1, retries + 1):
            try:
                return fn()
            except Exception as exc:
                last_exc = exc
                if attempt < retries:
                    logger.warning(
                        "LLM request failed (attempt %d/%d): %s – retrying in %.0fs …",
                        attempt, retries, exc, delay,
                    )
                    time.sleep(delay)
                    delay *= 2
        raise last_exc
