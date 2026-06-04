"""界面多语言支持。

使用 JSON 翻译文件 (locales/*.json)，格式简单，零编译。
用法:
    from src.core.locale import _

    title = _("app.title")              # → "翻译工具" / "Translator"
    msg = _("error.msg", error="...")   # → 支持 format 参数
"""

import json
import sys
from pathlib import Path


def _get_locales_dir() -> Path:
    if getattr(sys, "frozen", False):
        # PyInstaller 打包后：语言文件在临时解压目录
        return Path(sys._MEIPASS) / "locales"  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent.parent / "locales"


LOCALES_DIR = _get_locales_dir()

# 支持的语言
AVAILABLE_LANGUAGES: dict[str, str] = {
    "zh": "中文",
    "en": "English",
    "ja": "日本語",
}


class LocaleManager:
    """单例语言管理器。"""

    _instance: "LocaleManager | None" = None

    def __init__(self) -> None:
        self._strings: dict[str, str] = {}
        self._current: str = "zh"
        self.load("zh")

    @classmethod
    def instance(cls) -> "LocaleManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── 加载 ─────────────────────────────────────────────────

    def load(self, lang: str) -> "LocaleManager":
        if lang not in AVAILABLE_LANGUAGES:
            lang = "zh"

        path = LOCALES_DIR / f"{lang}.json"
        if path.exists():
            try:
                self._strings = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass  # 保持当前语言不变

        self._current = lang
        return self

    # ── 查询 ─────────────────────────────────────────────────

    def t(self, key: str, **kwargs: object) -> str:
        """根据 key 取翻译文本，支持 {name} 格式化。"""
        text = self._strings.get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, ValueError):
                return text
        return text

    @property
    def current(self) -> str:
        return self._current

    @property
    def current_name(self) -> str:
        return AVAILABLE_LANGUAGES.get(self._current, self._current)


# ── 模块级快捷函数 ──────────────────────────────────────────

def _(key: str, **kwargs: object) -> str:
    """返回当前语言的翻译文本。"""
    return LocaleManager.instance().t(key, **kwargs)
