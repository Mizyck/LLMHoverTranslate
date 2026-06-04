"""翻译引擎 —— 编排 Provider 调用，提供统一的翻译入口。

扩展点：
- 后续可在此层添加术语表替换、翻译记忆、批量翻译等功能。
"""

from .providers.base import TranslatorProvider, TranslationResult


# ── 支持的语言 ─────────────────────────────────────────────────
# 后续可改为从配置文件加载
LANGUAGES: dict[str, str] = {
    "auto": "自动检测",
    "zh": "中文",
    "en": "英语",
    "ja": "日语",
    "ko": "韩语",
    "fr": "法语",
    "de": "德语",
    "es": "西班牙语",
    "ru": "俄语",
    "pt": "葡萄牙语",
    "ar": "阿拉伯语",
    "th": "泰语",
    "vi": "越南语",
    "it": "意大利语",
    "id": "印尼语",
    "hi": "印地语",
    "tr": "土耳其语",
    "nl": "荷兰语",
    "pl": "波兰语",
}


class TranslationEngine:
    """翻译引擎，封装 Provider 调用和预处理/后处理逻辑。"""

    def __init__(self, provider: TranslatorProvider):
        self._provider = provider

    def translate(
        self, text: str, source_lang: str = "auto", target_lang: str = "zh"
    ) -> TranslationResult:
        """翻译文本。

        Args:
            text: 待翻译文本
            source_lang: 源语言代码，默认 "auto" 自动检测
            target_lang: 目标语言代码，默认 "zh"

        Returns:
            TranslationResult

        Raises:
            ValueError: 文本为空时抛出
        """
        if not text.strip():
            raise ValueError("翻译文本不能为空")

        return self._provider.translate(text, source_lang, target_lang)

    @property
    def provider_name(self) -> str:
        return self._provider.name

    @property
    def available_models(self) -> list[str]:
        return self._provider.available_models

    @staticmethod
    def get_display_name(code: str) -> str:
        """语言代码 → 当前 UI 语言的显示名。"""
        from .locale import _
        key = f"lang.{code}"
        name = _(key)
        if name != key:
            return name
        # 降级：locale 中没有时用内置中文名
        return LANGUAGES.get(code, code)

    @staticmethod
    def supported_languages() -> dict[str, str]:
        """返回支持的语言映射 {code: display_name}（按当前 UI 语言）。"""
        return {code: TranslationEngine.get_display_name(code) for code in LANGUAGES}
