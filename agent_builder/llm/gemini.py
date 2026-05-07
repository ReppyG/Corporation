import logging
import time
from typing import List, Optional

from agent_builder.llm.provider import InvalidAPIKey, LLMProvider

logger = logging.getLogger(__name__)

# Minimum length that a real Google API key would have.
_MIN_KEY_LENGTH = 20


def _looks_real(api_key: str) -> bool:
    return bool(api_key) and len(api_key) >= _MIN_KEY_LENGTH


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider.

    When *api_key* looks like a real key (≥ 20 characters) the provider makes
    live calls to the Google Generative AI API.  Short / placeholder keys fall
    back to a stub response so that unit tests continue to work without
    credentials.
    """

    DEFAULT_MODEL = "gemini-2.5-flash"

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
    ):
        super().__init__(api_key, model, temperature)
        self._client = None
        self._model_instance = None
        if _looks_real(api_key):
            self._init_client()

    def _init_client(self) -> None:
        import google.generativeai as genai  # noqa: PLC0415

        genai.configure(api_key=self.api_key)
        self._client = genai
        self._model_instance = genai.GenerativeModel(self.model)
        logger.debug("[gemini] client initialized for model '%s'", self.model)

    # ------------------------------------------------------------------
    # LLMProvider interface
    # ------------------------------------------------------------------

    def validate_key(self) -> bool:
        """Check whether the API key is accepted by Google.

        Raises
        ------
        InvalidAPIKey
        """
        if not _looks_real(self.api_key):
            raise InvalidAPIKey("Gemini API key appears to be a placeholder.")
        try:
            if self._model_instance is None:
                self._init_client()
            self._model_instance.count_tokens("ping")
            return True
        except Exception as exc:
            raise InvalidAPIKey(f"Gemini API key validation failed: {exc}") from exc

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
    ) -> str:
        """Generate a single-turn response."""
        if not _looks_real(self.api_key):
            return f"[gemini:{self.model}] {system_prompt[:80]} :: {prompt}"

        temp = temperature if temperature is not None else self.temperature

        def _call():
            try:
                import google.generativeai as genai  # noqa: PLC0415
                from google.api_core.exceptions import ResourceExhausted  # noqa: PLC0415

                if self._model_instance is None:
                    self._init_client()

                full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                model = genai.GenerativeModel(
                    self.model,
                    generation_config=genai.types.GenerationConfig(temperature=temp),
                )
                response = model.generate_content(full_prompt)
                tokens_used = getattr(response, "usage_metadata", None)
                logger.info(
                    "[gemini] generate model=%s prompt_len=%d tokens=%s",
                    self.model, len(prompt), tokens_used,
                )
                return response.text
            except ResourceExhausted as exc:
                raise exc  # will be retried
            except Exception as exc:
                logger.error("[gemini] generate error: %s", exc)
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
            import google.generativeai as genai  # noqa: PLC0415

            if self._model_instance is None:
                self._init_client()

            system_prompt = ""
            chat_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "system":
                    system_prompt = content
                elif role == "assistant":
                    chat_messages.append({"role": "model", "parts": [content]})
                else:
                    chat_messages.append({"role": "user", "parts": [content]})

            model = genai.GenerativeModel(
                self.model,
                system_instruction=system_prompt or None,
            )
            if len(chat_messages) <= 1:
                user_content = chat_messages[0]["parts"][0] if chat_messages else ""
                response = model.generate_content(user_content)
            else:
                chat = model.start_chat(history=chat_messages[:-1])
                response = chat.send_message(chat_messages[-1]["parts"][0])

            logger.info("[gemini] generate_with_context model=%s msgs=%d", self.model, len(messages))
            return response.text

        return self._retry_with_backoff(_call)

    def count_tokens(self, text: str) -> int:
        """Count tokens using the Gemini token-counting API."""
        if not _looks_real(self.api_key):
            return len(text.split())
        try:
            if self._model_instance is None:
                self._init_client()
            result = self._model_instance.count_tokens(text)
            return result.total_tokens
        except Exception:
            return len(text.split())

    def get_cost_estimate(self, tokens_in: int, tokens_out: int) -> float:
        """Estimate cost in USD (Gemini 2.5 Flash pricing, May 2026)."""
        # $0.075 / 1M input tokens, $0.30 / 1M output tokens
        return (tokens_in * 0.075 + tokens_out * 0.30) / 1_000_000
