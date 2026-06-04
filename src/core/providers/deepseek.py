"""通用 OpenAI 兼容翻译 Provider。

支持 DeepSeek、OpenAI 及任何兼容 OpenAI SDK 格式的 API 服务。
更换服务商只需改 base_url / api_key / model 三个参数，无需写新类。
"""

from openai import OpenAI

from .base import TranslatorProvider, TranslationResult


TRANSLATION_SYSTEM_PROMPT = """\
You are a professional translator. Translate the following text accurately and naturally.

Rules:
- Preserve the original meaning, tone, and style.
- Keep formatting (markdown, line breaks, code blocks) intact.
- For ambiguous terms, choose the most natural translation in context.
- Output ONLY the translated text. Do NOT add explanations, notes, or the original text.
"""


class OpenAICompatibleProvider(TranslatorProvider):
    """通用 OpenAI 兼容 API 翻译 Provider。

    支持所有兼容 OpenAI SDK 的服务：
      - DeepSeek:  base_url="https://api.deepseek.com"
      - OpenAI:    base_url="https://api.openai.com/v1"
      - 本地模型:   base_url="http://localhost:11434/v1" (Ollama 等)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-chat",
    ):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._base_url = base_url

    def translate(
        self, text: str, source_lang: str, target_lang: str
    ) -> TranslationResult:
        source_label = _LANG_DISPLAY.get(source_lang, source_lang)
        target_label = _LANG_DISPLAY.get(target_lang, target_lang)

        user_prompt = (
            f"Translate the following text from {source_label} to {target_label}:\n\n{text}"
        )

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": TRANSLATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )

        translated = response.choices[0].message.content.strip()

        return TranslationResult(
            text=translated,
            source_lang=source_lang,
            target_lang=target_lang,
            model=self._model,
        )

    @property
    def name(self) -> str:
        return "OpenAI Compatible"

    @property
    def available_models(self) -> list[str]:
        return [self._model]


# ── 向下兼容别名 ────────────────────────────────────────────
DeepSeekProvider = OpenAICompatibleProvider


# ── 语言代码 → 英文显示名（发给 LLM 用）─────────────────
_LANG_DISPLAY = {
    "auto": "Auto-detect",
    "zh": "Chinese",
    "zh-TW": "Traditional Chinese",
    "en": "English",
    "ja": "Japanese",
    "ko": "Korean",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "ru": "Russian",
    "pt": "Portuguese",
    "ar": "Arabic",
    "th": "Thai",
    "vi": "Vietnamese",
    "it": "Italian",
    "id": "Indonesian",
    "hi": "Hindi",
    "tr": "Turkish",
    "nl": "Dutch",
    "pl": "Polish",
}
