"""翻译工具主界面 — 暗黑模式 / 多 Provider / 划词翻译 / 多语言。"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, font as tkfont

import sv_ttk

from ..core.engine import TranslationEngine
from ..core.providers.deepseek import OpenAICompatibleProvider
from ..core.selection_monitor import SelectionMonitor
from ..core.locale import _, LocaleManager
from ..config import SettingsManager, get_api_key, save_api_key
from .settings_window import SettingsWindow
from .float_window import FloatWindow
from .tray_manager import TrayManager


class TranslatorApp:
    """翻译工具主窗口。"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(_("app.title"))
        self.root.geometry("900x600")
        self.root.minsize(700, 400)

        self._sm = SettingsManager.instance()
        self._lang_code_map: dict[str, str] = {}

        self._float_window: FloatWindow | None = None
        self._tray: TrayManager | None = None
        self._monitor: SelectionMonitor | None = None

        self.engine = self._init_engine()
        sv_ttk.set_theme(self._sm.s.theme)
        self._build_ui()
        self._apply_font_size()
        self._set_default_languages()
        self._refresh_text_widgets_theme()

        self.root.protocol("WM_DELETE_WINDOW", self._quit_app)

    # ── 引擎初始化 ────────────────────────────────────────────

    def _init_engine(self) -> TranslationEngine:
        api_key = get_api_key()
        s = self._sm.s
        if not api_key:
            api_key = self._prompt_api_key()

        return TranslationEngine(
            OpenAICompatibleProvider(
                api_key=api_key or "",
                base_url=s.api_base_url,
                model=s.api_model,
            )
        )

    def _reinit_engine(self) -> None:
        self.engine = self._init_engine()

    def _prompt_api_key(self) -> str:
        key = simpledialog.askstring(
            _("dialog.api_key_title"),
            _("dialog.api_key_prompt"),
            parent=self.root,
            show="*",
        )
        if key and key.strip():
            key = key.strip()
            save_api_key(key)
            import os
            os.environ["API_KEY"] = key
            os.environ["DEEPSEEK_API_KEY"] = key
            return key
        return ""

    # ── 生命周期 ──────────────────────────────────────────────

    def _quit_app(self):
        self._stop_hover_mode()
        self.root.quit()

    # ── UI 构建 ────────────────────────────────────────────────

    def _build_ui(self):
        self._build_top_bar()
        self._build_language_bar()
        self._build_action_bar()
        self._build_status_bar()
        self._build_text_panels()
        self._bind_hotkeys()

    def _build_top_bar(self):
        top = ttk.Frame(self.root, padding=(10, 8, 10, 0))
        top.pack(fill=tk.X)

        self._title_label = ttk.Label(top, text=_("app.title"), font=("", 12, "bold"))
        self._title_label.pack(side=tk.LEFT)

        self._settings_btn = ttk.Button(top, text=_("btn.settings"), command=self._open_settings)
        self._settings_btn.pack(side=tk.RIGHT, padx=(5, 0))

        self._hover_btn = ttk.Button(top, text=_("btn.hover"), command=self._start_hover_mode)
        self._hover_btn.pack(side=tk.RIGHT)

    def _open_settings(self):
        SettingsWindow(self.root, on_save=self._on_settings_saved)

    def _on_settings_saved(self):
        s = self._sm.s
        # 语言优先切换，后续文本刷新才能生效
        LocaleManager.instance().load(s.ui_language)
        self._reinit_engine()
        sv_ttk.set_theme(s.theme)
        self._refresh_texts()
        self._refresh_text_widgets_theme()
        self._apply_font_size()
        if self._float_window is not None:
            self._float_window.apply_theme(s.theme)

    def _refresh_texts(self):
        """语言切换后刷新全部界面文本。"""
        self.root.title(_("app.title"))
        self._title_label.configure(text=_("app.title"))
        self._settings_btn.configure(text=_("btn.settings"))
        self._hover_btn.configure(text=_("btn.hover"))
        self._src_lang_lbl.configure(text=_("label.source_lang"))
        self._tgt_lang_lbl.configure(text=_("label.target_lang"))
        self._swap_btn.configure(text=_("btn.swap"))
        self._src_frame.configure(text=_("frame.source"))
        self._tgt_frame.configure(text=_("frame.target"))
        self._translate_btn.configure(text=_("btn.translate"))
        self._copy_btn.configure(text=_("btn.copy"))
        self._clear_btn.configure(text=_("btn.clear"))
        self._refresh_language_dropdowns()
        current = self._status_var.get()
        if current == LocaleManager.instance().t("status.ready"):
            self._status_var.set(_("status.ready"))

    def _refresh_text_widgets_theme(self):
        is_dark = self._sm.s.theme == "dark"
        bg = "#1c1c1c" if is_dark else "#ffffff"
        fg = "#e0e0e0" if is_dark else "#000000"
        for widget in (self.source_text, self.target_text):
            widget.configure(bg=bg, fg=fg, insertbackground=fg)

    def _refresh_language_dropdowns(self):
        """语言切换时重建源语言/目标语言下拉框列表。"""
        # 保存当前选中项的语言代码
        src_code = self._get_lang_code(self.source_lang.get())
        tgt_code = self._get_lang_code(self.target_lang.get())

        # 用当前 UI 语言重新生成显示名列表
        codes = list(TranslationEngine.supported_languages().keys())
        display_names = [TranslationEngine.get_display_name(c) for c in codes]

        # 重建映射
        self._lang_code_map = dict(zip(display_names, codes))

        # 更新下拉框
        self.source_lang["values"] = display_names
        self.target_lang["values"] = display_names

        # 恢复选中
        src_name = TranslationEngine.get_display_name(src_code)
        tgt_name = TranslationEngine.get_display_name(tgt_code)
        if src_name in self._lang_code_map:
            self.source_lang.set(src_name)
        if tgt_name in self._lang_code_map:
            self.target_lang.set(tgt_name)

    def _build_language_bar(self):
        bar = ttk.Frame(self.root, padding=(10, 8, 10, 5))
        bar.pack(fill=tk.X)

        languages = TranslationEngine.supported_languages()
        self._lang_code_map = {name: code for code, name in languages.items()}
        display_names = list(languages.values())

        self._src_lang_lbl = ttk.Label(bar, text=_("label.source_lang"))
        self._src_lang_lbl.pack(side=tk.LEFT)
        self.source_lang = ttk.Combobox(bar, values=display_names, state="readonly", width=12)
        self.source_lang.pack(side=tk.LEFT, padx=(5, 10))
        self.source_lang.current(0)

        self._swap_btn = ttk.Button(bar, text=_("btn.swap"), command=self._swap_languages, width=8)
        self._swap_btn.pack(side=tk.LEFT, padx=5)

        self._tgt_lang_lbl = ttk.Label(bar, text=_("label.target_lang"))
        self._tgt_lang_lbl.pack(side=tk.LEFT, padx=(10, 0))
        self.target_lang = ttk.Combobox(bar, values=display_names, state="readonly", width=12)
        self.target_lang.pack(side=tk.LEFT, padx=5)
        if len(display_names) > 1:
            self.target_lang.current(1)

    def _build_text_panels(self):
        panel = ttk.Frame(self.root, padding=(10, 5))
        panel.pack(fill=tk.BOTH, expand=True)
        panel.columnconfigure(0, weight=1)
        panel.columnconfigure(1, weight=1)
        panel.rowconfigure(0, weight=1)

        family = "Microsoft YaHei" if self._is_windows() else "TkDefaultFont"
        self._font = (family, self._sm.s.font_size)

        self._src_frame = ttk.LabelFrame(panel, text=_("frame.source"), padding=3)
        self._src_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        self._src_frame.rowconfigure(0, weight=1)
        self._src_frame.columnconfigure(0, weight=1)

        self.source_text = tk.Text(self._src_frame, wrap=tk.WORD, font=self._font, undo=True, relief=tk.FLAT)
        self.source_text.grid(row=0, column=0, sticky="nsew")
        src_scroll = ttk.Scrollbar(self._src_frame, command=self.source_text.yview)
        src_scroll.grid(row=0, column=1, sticky="ns")
        self.source_text.configure(yscrollcommand=src_scroll.set)

        self._tgt_frame = ttk.LabelFrame(panel, text=_("frame.target"), padding=3)
        self._tgt_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        self._tgt_frame.rowconfigure(0, weight=1)
        self._tgt_frame.columnconfigure(0, weight=1)

        self.target_text = tk.Text(self._tgt_frame, wrap=tk.WORD, font=self._font, undo=True, relief=tk.FLAT)
        self.target_text.grid(row=0, column=0, sticky="nsew")
        tgt_scroll = ttk.Scrollbar(self._tgt_frame, command=self.target_text.yview)
        tgt_scroll.grid(row=0, column=1, sticky="ns")
        self.target_text.configure(yscrollcommand=tgt_scroll.set)

    def _build_action_bar(self):
        bar = ttk.Frame(self.root, padding=(10, 5, 10, 10))
        bar.pack(fill=tk.X, side=tk.BOTTOM)

        self._translate_btn = ttk.Button(bar, text=_("btn.translate"), command=self._translate)
        self._translate_btn.pack(side=tk.LEFT, padx=(0, 5))

        self._copy_btn = ttk.Button(bar, text=_("btn.copy"), command=self._copy_result)
        self._copy_btn.pack(side=tk.LEFT, padx=5)

        self._clear_btn = ttk.Button(bar, text=_("btn.clear"), command=self._clear_all)
        self._clear_btn.pack(side=tk.LEFT, padx=5)

    def _build_status_bar(self):
        self._status_var = tk.StringVar(value=_("status.ready"))
        status = ttk.Label(self.root, textvariable=self._status_var, relief=tk.SUNKEN, anchor=tk.W, padding=(6, 3))
        status.pack(fill=tk.X, side=tk.BOTTOM)

    def _bind_hotkeys(self):
        self.root.bind("<Control-Return>", lambda _e: self._translate())
        self.root.bind("<Control-c>", lambda _e: self._copy_result())

    # ── 外观工具 ────────────────────────────────────────────────

    def _apply_font_size(self):
        size = self._sm.s.font_size
        family = "Microsoft YaHei" if self._is_windows() else "TkDefaultFont"
        self._font = (family, size)
        self.source_text.configure(font=self._font)
        self.target_text.configure(font=self._font)

    def _set_default_languages(self):
        s = self._sm.s
        src_name = TranslationEngine.get_display_name(s.default_source_lang)
        tgt_name = TranslationEngine.get_display_name(s.default_target_lang)
        if src_name in self._lang_code_map:
            self.source_lang.set(src_name)
        if tgt_name in self._lang_code_map:
            self.target_lang.set(tgt_name)

    # ── 手动翻译 ───────────────────────────────────────────────

    def _swap_languages(self):
        src = self.source_lang.get()
        tgt = self.target_lang.get()
        self.source_lang.set(tgt)
        self.target_lang.set(src)

    def _get_lang_code(self, display_name: str) -> str:
        return self._lang_code_map.get(display_name, "auto")

    def _translate(self):
        text = self.source_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo(_("dialog.need_text"), _("dialog.need_text_msg"))
            return

        src_code = self._get_lang_code(self.source_lang.get())
        tgt_code = self._get_lang_code(self.target_lang.get())
        self._set_ui_state(translating=True)

        def _run():
            try:
                result = self.engine.translate(text, source_lang=src_code, target_lang=tgt_code)
                self.root.after(0, lambda: self._on_done(result))
            except Exception as exc:
                self.root.after(0, lambda: self._on_error(str(exc)))

        threading.Thread(target=_run, daemon=True).start()

    def _on_done(self, result):
        self.target_text.delete("1.0", tk.END)
        self.target_text.insert("1.0", result.text)
        self._set_ui_state(translating=False)
        self._status_var.set(_("status.done"))
        if self._sm.s.auto_copy:
            self._copy_result(silent=True)

    def _on_error(self, msg: str):
        self._set_ui_state(translating=False)
        self._status_var.set(_("status.failed"))
        messagebox.showerror(_("error.translate_failed"), _("error.translate_failed_msg", error=msg))

    def _set_ui_state(self, *, translating: bool):
        if translating:
            self._translate_btn.configure(state=tk.DISABLED, text=_("status.translating"))
            self._status_var.set(_("status.translating"))
        else:
            self._translate_btn.configure(state=tk.NORMAL, text=_("btn.translate"))

    def _copy_result(self, silent: bool = False):
        text = self.target_text.get("1.0", tk.END).strip()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            if not silent:
                self._status_var.set(_("status.copied"))

    def _clear_all(self):
        self.source_text.delete("1.0", tk.END)
        self.target_text.delete("1.0", tk.END)
        self._status_var.set(_("status.ready"))

    # ═══════════════════════════════════════════════════════════
    # 划词翻译
    # ═══════════════════════════════════════════════════════════

    def _start_hover_mode(self):
        self.root.withdraw()

        self._tray = TrayManager(
            root=self.root,
            on_show_main=self._stop_hover_mode,
            on_quit=self._quit_app,
        )
        self._tray.show()

        self._float_window = FloatWindow(
            parent=self.root,
            engine=self.engine,
            on_close=self._stop_hover_mode,
            on_toggle=self._on_hover_toggle,
            theme=self._sm.s.theme,
        )

        self._monitor = SelectionMonitor(on_selection=self._on_selection_detected)
        self._monitor.start()

    def _stop_hover_mode(self):
        if self._monitor is not None:
            self._monitor.stop()
            self._monitor = None

        if self._tray is not None:
            self._tray.hide()
            self._tray = None

        if self._float_window is not None:
            try:
                self._float_window.destroy()
            except tk.TclError:
                pass
            self._float_window = None

        self.root.deiconify()
        self.root.lift()

    def _on_hover_toggle(self, enabled: bool):
        if enabled:
            if self._monitor is None:
                self._monitor = SelectionMonitor(on_selection=self._on_selection_detected)
                self._monitor.start()
        else:
            if self._monitor is not None:
                self._monitor.stop()
                self._monitor = None

    def _on_selection_detected(self, text: str):
        if self._float_window is None:
            return

        self._float_window.set_source(text)

        src_code = self._float_window.source_lang_code
        tgt_code = self._float_window.target_lang_code
        self._float_window.set_lang_info(src_code, tgt_code)

        def _run():
            try:
                result = self.engine.translate(text, source_lang=src_code, target_lang=tgt_code)
                self.root.after(0, lambda: self._on_float_result(result))
            except Exception:
                if self._float_window:
                    self.root.after(0, self._float_window.set_status_failed)

        threading.Thread(target=_run, daemon=True).start()

    def _on_float_result(self, result):
        if self._float_window is not None:
            self._float_window.set_target(result.text)
            self._float_window.set_lang_info(
                self._float_window.source_lang_code,
                self._float_window.target_lang_code,
            )

    @staticmethod
    def _is_windows() -> bool:
        import sys
        return sys.platform == "win32"
