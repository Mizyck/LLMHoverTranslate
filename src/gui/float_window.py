"""翻译浮窗 —— 划词翻译显示界面，内置源语言/目标语言选择。"""

import tkinter as tk
from tkinter import ttk
from typing import Callable

from ..core.engine import TranslationEngine
from ..core.locale import _


class FloatWindow(tk.Toplevel):
    """划词翻译浮窗。"""

    def __init__(
        self,
        parent: tk.Tk,
        engine: TranslationEngine,
        on_close: Callable[[], None],
        on_toggle: Callable[[bool], None],
        theme: str = "light",
    ):
        super().__init__(parent)
        self.title(_("float.title"))
        self.geometry("420x420")
        self.minsize(300, 280)
        self.attributes("-topmost", True)

        self._engine = engine
        self._on_close = on_close
        self._on_toggle = on_toggle
        self._theme = theme

        # 语言映射
        langs = TranslationEngine.supported_languages()
        self._lang_code_map: dict[str, str] = {name: code for code, name in langs.items()}
        self._display_names = list(langs.values())

        self._build_ui()
        self._apply_theme()
        self.protocol("WM_DELETE_WINDOW", self._close)

    # ── 公开属性 ──────────────────────────────────────────────

    @property
    def source_lang_code(self) -> str:
        display = self._src_combo.get()
        return self._lang_code_map.get(display, "auto")

    @property
    def target_lang_code(self) -> str:
        display = self._tgt_combo.get()
        return self._lang_code_map.get(display, "zh")

    # ── UI 构建 ────────────────────────────────────────────────

    def _build_ui(self):
        # ── 标题 + 开关 ──
        header = ttk.Frame(self, padding=(10, 8, 10, 4))
        header.pack(fill=tk.X)
        self._header_lbl = ttk.Label(header, text=_("float.header"), font=("", 11, "bold"))
        self._header_lbl.pack(side=tk.LEFT)

        self._toggle_var = tk.BooleanVar(value=True)
        self._toggle_btn = ttk.Checkbutton(
            header, text=_("float.toggle"), variable=self._toggle_var,
            command=self._on_toggle_changed, style="Switch.TCheckbutton",
        )
        self._toggle_btn.pack(side=tk.RIGHT)

        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, padx=10)

        # ── 语言选择栏 ──
        lang_bar = ttk.Frame(self, padding=(10, 6, 10, 2))
        lang_bar.pack(fill=tk.X)

        self._src_combo = ttk.Combobox(
            lang_bar, values=self._display_names, state="readonly", width=12,
        )
        self._src_combo.pack(side=tk.LEFT)
        # 默认选"自动检测"（即列表第一项）
        self._src_combo.current(0)

        self._swap_btn = ttk.Button(lang_bar, text="⇄", command=self._swap_langs, width=3)
        self._swap_btn.pack(side=tk.LEFT, padx=4)

        self._tgt_combo = ttk.Combobox(
            lang_bar, values=self._display_names, state="readonly", width=12,
        )
        self._tgt_combo.pack(side=tk.LEFT)
        # 默认选第一个非 auto 的语言
        if len(self._display_names) > 1:
            self._tgt_combo.current(1)

        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, padx=10, pady=(4, 0))

        # ── 原文 ──
        src_frame = ttk.LabelFrame(self, text=_("float.frame_source"), padding=3)
        src_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(6, 3))
        self._source_text = tk.Text(
            src_frame, wrap=tk.WORD, height=3,
            font=("Microsoft YaHei", 10), relief=tk.FLAT, state=tk.DISABLED,
        )
        self._source_text.pack(fill=tk.BOTH, expand=True)

        # ── 译文 ──
        tgt_frame = ttk.LabelFrame(self, text=_("float.frame_target"), padding=3)
        tgt_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(3, 6))
        self._target_text = tk.Text(
            tgt_frame, wrap=tk.WORD, height=3,
            font=("Microsoft YaHei", 10), relief=tk.FLAT, state=tk.DISABLED,
        )
        self._target_text.pack(fill=tk.BOTH, expand=True)

        # ── 底部 ──
        bottom = ttk.Frame(self, padding=(10, 0, 10, 8))
        bottom.pack(fill=tk.X)
        self._lang_label = ttk.Label(bottom, text=self._lang_info_text())
        self._lang_label.pack(side=tk.LEFT)
        self._copy_btn = ttk.Button(bottom, text=_("float.btn.copy"), command=self._copy)
        self._copy_btn.pack(side=tk.RIGHT)

    # ── 公开方法 ───────────────────────────────────────────────

    def set_source(self, text: str) -> None:
        self._source_text.configure(state=tk.NORMAL)
        self._source_text.delete("1.0", tk.END)
        self._source_text.insert("1.0", text)
        self._source_text.configure(state=tk.DISABLED)

    def set_target(self, text: str) -> None:
        self._target_text.configure(state=tk.NORMAL)
        self._target_text.delete("1.0", tk.END)
        self._target_text.insert("1.0", text)
        self._target_text.configure(state=tk.DISABLED)

    def set_lang_info(self, source: str, target: str) -> None:
        src_name = TranslationEngine.get_display_name(source)
        tgt_name = TranslationEngine.get_display_name(target)
        self._lang_label.configure(text=f"{src_name} → {tgt_name}")

    def set_status_failed(self) -> None:
        self._lang_label.configure(text=_("float.status.failed"))

    def apply_theme(self, theme: str) -> None:
        self._theme = theme
        self._apply_theme()

    # ── 内部 ──────────────────────────────────────────────────

    def _on_toggle_changed(self):
        self._on_toggle(self._toggle_var.get())

    def _swap_langs(self):
        src = self._src_combo.get()
        tgt = self._tgt_combo.get()
        self._src_combo.set(tgt)
        self._tgt_combo.set(src)

    def _lang_info_text(self) -> str:
        src = TranslationEngine.get_display_name(self.source_lang_code)
        tgt = TranslationEngine.get_display_name(self.target_lang_code)
        return f"{src} → {tgt}"

    def _copy(self):
        text = self._target_text.get("1.0", tk.END).strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._lang_label.configure(text=_("float.status.copied"))

    def _close(self):
        self._on_close()
        self.destroy()

    def _apply_theme(self):
        is_dark = self._theme == "dark"
        bg = "#1c1c1c" if is_dark else "#ffffff"
        fg = "#e0e0e0" if is_dark else "#000000"
        for widget in (self._source_text, self._target_text):
            widget.configure(bg=bg, fg=fg, insertbackground=fg)
