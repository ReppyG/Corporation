import logging
from typing import List, Optional

from agent_builder.llm.provider import InvalidAPIKey, LLMProvider

logger = logging.getLogger(__name__)

_ANTHROPIC_KEY_PREFIX = "sk-ant-"
_MIN_KEY_LENGTH = 20


def _looks_real(api_key: str) -> bool:
    return bool(api_key) and len(api_key) >= _MIN_KEY_LENGTH and api_key.startswith(_ANTHROPIC_KEY_PREFIX)


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider.

    Real API calls are made when *api_key* starts with ``sk-ant-``.  Shorter
    or non-prefixed keys fall back to a stub response for unit testing.
    """

    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
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
        import anthropic  # noqa: PLC0415

        self._client = anthropic.Anthropic(api_key=self.api_key)
        logger.debug("[anthropic] client initialised for model '%s'", self.model)

    # ------------------------------------------------------------------
    # LLMProvider interface
    # ------------------------------------------------------------------

    def validate_key(self) -> bool:
        """Verify the API key with a minimal Anthropic request.

        Raises
        ------
        InvalidAPIKey
        """
        if not _looks_real(self.api_key):
            raise InvalidAPIKey(
                "Anthropic API key should start with 'sk-ant-'."
            )
        try:
            if self._client is None:
                self._init_client()
            self._client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception as exc:
            raise InvalidAPIKey(f"Anthropic API key validation failed: {exc}") from exc

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
    ) -> str:
        """Generate a single-turn response."""
        if not _looks_real(self.api_key):
            return f"[anthropic:{self.model}] {system_prompt[:80]} :: {prompt}"

        temp = temperature if temperature is not None else self.temperature

        def _call():
            import anthropic  # noqa: PLC0415

            if self._client is None:
                self._init_client()
            try:
                kwargs = dict(
                    model=self.model,
                    max_tokens=self.MAX_TOKENS,
                    temperature=temp,
                    messages=[{"role": "user", "content": prompt}],
                )
                if system_prompt:
                    kwargs["system"] = system_prompt
                response = self._client.messages.create(**kwargs)
                text = response.content[0].text
                logger.info(
                    "[anthropic] generate model=%s prompt_len=%d response_len=%d",
                    self.model, len(prompt), len(text),
                )
                return text
            except anthropic.RateLimitError as exc:
                raise exc  # will be retried
            except anthropic.APIError as exc:
                logger.error("[anthropic] API error: %s", exc)
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
            import anthropic  # noqa: PLC0415

            if self._client is None:
                self._init_client()

            system_prompt = ""
            api_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "system":
                    system_prompt = content
                else:
                    api_messages.append({"role": role, "content": content})

            try:
                kwargs = dict(
                    model=self.model,
                    max_tokens=self.MAX_TOKENS,
                    messages=api_messages,
                )
                if system_prompt:
                    kwargs["system"] = system_prompt
                response = self._client.messages.create(**kwargs)
                text = response.content[0].text
                logger.info(
                    "[anthropic] generate_with_context model=%s msgs=%d",
                    self.model, len(messages),
                )
                return text
            except anthropic.RateLimitError as exc:
                raise exc
            except anthropic.APIError as exc:
                logger.error("[anthropic] API error: %s", exc)
                raise

        return self._retry_with_backoff(_call)

    def count_tokens(self, text: str) -> int:
        """Estimate token count using the Anthropic token-counting API."""
        if not _looks_real(self.api_key):
            return len(text.split())
        try:
            if self._client is None:
                self._init_client()
            response = self._client.messages.count_tokens(
                model=self.model,
                messages=[{"role": "user", "content": text}],
            )
            return response.input_tokens
        except Exception:
            return len(text.split())

    def get_cost_estimate(self, tokens_in: int, tokens_out: int) -> float:
        """Estimate cost in USD (Claude 3.5 Sonnet pricing, May 2026)."""
        # $3.00 / 1M input tokens, $15.00 / 1M output tokens
        return (tokens_in * 3.00 + tokens_out * 15.00) / 1_000_000
