"""翻译工具入口。"""

import tkinter as tk

from src.config import SettingsManager
from src.core.locale import LocaleManager, AVAILABLE_LANGUAGES
from src.gui.main_window import TranslatorApp


def main():
    # 首次启动自动生成默认 settings.json
    sm = SettingsManager.instance()
    lang = sm.s.ui_language

    # 加载界面语言
    if lang in AVAILABLE_LANGUAGES:
        LocaleManager.instance().load(lang)

    root = tk.Tk()
    TranslatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
