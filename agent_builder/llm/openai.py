import logging
from typing import List, Optional

from agent_builder.llm.provider import InvalidAPIKey, LLMProvider

logger = logging.getLogger(__name__)

_OPENAI_KEY_PREFIX = "sk-"
_MIN_KEY_LENGTH = 20


def _looks_real(api_key: str) -> bool:
    return bool(api_key) and len(api_key) >= _MIN_KEY_LENGTH and api_key.startswith(_OPENAI_KEY_PREFIX)


class OpenAIProvider(LLMProvider):
    """OpenAI GPT LLM provider.

    Real API calls are made when *api_key* starts with ``sk-`` and is at
    least 20 characters.  Shorter keys fall back to a stub response for unit
    testing.
    """

    DEFAULT_MODEL = "gpt-4o-mini"
    MAX_TOKENS = 4096

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
    ):
        super().__init__(api_key, model, temperature)
        self._client = None
        if _looks_real(api_key):
            self._init_client()

    def _init_client(self) -> None:
        import openai  # noqa: PLC0415

        self._client = openai.OpenAI(api_key=self.api_key)
        logger.debug("[openai] client initialized for model '%s'", self.model)

    # ------------------------------------------------------------------
    # LLMProvider interface
    # ------------------------------------------------------------------

    def validate_key(self) -> bool:
        """Verify the API key with a minimal completion request.

        Raises
        ------
        InvalidAPIKey
        """
        if not _looks_real(self.api_key):
            raise InvalidAPIKey(
                "OpenAI API key should start with 'sk-' and be at least 20 characters."
            )
        try:
            if self._client is None:
                self._init_client()
            self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
            )
            return True
        except Exception as exc:
            raise InvalidAPIKey(f"OpenAI API key validation failed: {exc}") from exc

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
    ) -> str:
        """Generate a single-turn response."""
        if not _looks_real(self.api_key):
            return f"[openai:{self.model}] {system_prompt[:80]} :: {prompt}"

        temp = temperature if temperature is not None else self.temperature

        def _call():
            import openai  # noqa: PLC0415

            if self._client is None:
                self._init_client()
            try:
                msgs = []
                if system_prompt:
                    msgs.append({"role": "system", "content": system_prompt})
                msgs.append({"role": "user", "content": prompt})
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=msgs,
                    temperature=temp,
                    max_tokens=self.MAX_TOKENS,
                )
                text = response.choices[0].message.content
                logger.info(
                    "[openai] generate model=%s prompt_len=%d response_len=%d "
                    "tokens_in=%d tokens_out=%d",
                    self.model,
                    len(prompt),
                    len(text),
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                )
                return text
            except openai.RateLimitError as exc:
                raise exc  # will be retried
            except openai.APIError as exc:
                logger.error("[openai] API error: %s", exc)
                raise

        return self._retry_with_backoff(_call)

    def generate_with_context(self, messages: List[dict]) -> str:
        """Generate a response for a multi-turn conversation."""
        if not _looks_real(self.api_key):
            system = next(
                (m["content"] for m in messages if m.get("role") == "system"), ""
            )
            last_user = next(
                (m["content"] for m in reversed(messages) if m.get("role") == "user"),
                "",
            )
            return self.generate(prompt=last_user, system_prompt=system)

        def _call():
            import openai  # noqa: PLC0415

            if self._client is None:
                self._init_client()
            try:
                # OpenAI natively accepts system/user/assistant roles
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.MAX_TOKENS,
                )
                text = response.choices[0].message.content
                logger.info(
                    "[openai] generate_with_context model=%s msgs=%d tokens_in=%d tokens_out=%d",
                    self.model,
                    len(messages),
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                )
                return text
            except openai.RateLimitError as exc:
                raise exc
            except openai.APIError as exc:
                logger.error("[openai] API error: %s", exc)
                raise

        return self._retry_with_backoff(_call)

    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        try:
            import tiktoken  # noqa: PLC0415

            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except Exception:
            return len(text.split())

    def get_cost_estimate(self, tokens_in: int, tokens_out: int) -> float:
        """Estimate cost in USD (gpt-4o-mini pricing, May 2026)."""
        # gpt-4o-mini: $0.15 / 1M input, $0.60 / 1M output
        return (tokens_in * 0.15 + tokens_out * 0.60) / 1_000_000
