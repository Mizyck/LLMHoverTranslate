"""翻译 Provider 抽象基类。

扩展新 LLM 服务商只需继承 TranslatorProvider 并实现 translate() 即可。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class TranslationResult:
    """翻译结果"""

    text: str
    source_lang: str | None = None
    target_lang: str | None = None
    model: str | None = None
    metadata: dict = field(default_factory=dict)


class TranslatorProvider(ABC):
    """翻译服务抽象基类。

    所有 LLM 翻译 Provider 必须实现此接口。
    """

    @abstractmethod
    def translate(
        self, text: str, source_lang: str, target_lang: str
    ) -> TranslationResult:
        """执行翻译。

        Args:
            text: 待翻译文本
            source_lang: 源语言代码 (如 "en", "auto")
            target_lang: 目标语言代码 (如 "zh")

        Returns:
            TranslationResult 包含译文及元信息
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider 名称，用于 UI 显示。"""
        ...

    @property
    @abstractmethod
    def available_models(self) -> list[str]:
        """该 Provider 可用的模型列表。"""
        ...
