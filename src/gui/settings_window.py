"""设置对话框 —— API / 外观 / 翻译 / 行为 四栏。"""

import tkinter as tk
from tkinter import ttk
from typing import Callable

from ..config import SettingsManager, PROVIDER_PRESETS, get_api_key, save_api_key
from ..core.engine import TranslationEngine
from ..core.locale import _, LocaleManager, AVAILABLE_LANGUAGES


class SettingsWindow(tk.Toplevel):
    """设置窗口（模态对话框）。"""

    def __init__(
        self,
        parent: tk.Tk,
        on_save: Callable[[], None] | None = None,
    ):
        super().__init__(parent)
        self.title(_("settings.title"))
        self.geometry("480x530")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._sm = SettingsManager.instance()
        self._on_save = on_save

        self._build_ui()
        self._load_values()

        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_x(), parent.winfo_y()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

    # ── UI 构建 ────────────────────────────────────────────────

    def _build_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))

        self._build_api_tab(notebook)
        self._build_appearance_tab(notebook)
        self._build_translation_tab(notebook)
        self._build_behavior_tab(notebook)

        btn_frame = ttk.Frame(self, padding=(10, 10))
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text=_("settings.btn.cancel"), command=self.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text=_("settings.btn.save"), command=self._save).pack(side=tk.RIGHT)

    # ── API ────────────────────────────────────────────────────

    def _build_api_tab(self, notebook: ttk.Notebook):
        tab = ttk.Frame(notebook, padding=15)
        notebook.add(tab, text=_("settings.tab.api"))
        row = 0

        ttk.Label(tab, text=_("settings.api.provider"), font=("", 10, "bold")).grid(row=row, column=0, sticky="w", pady=(0, 2))
        row += 1
        preset_names = [v["name"] for v in PROVIDER_PRESETS.values()]
        preset_keys = list(PROVIDER_PRESETS.keys())
        self._preset_var = tk.StringVar()
        self._preset_combo = ttk.Combobox(tab, textvariable=self._preset_var, values=preset_names, state="readonly", width=20)
        self._preset_combo.grid(row=row, column=0, sticky="w", pady=(0, 10))
        self._preset_combo.bind("<<ComboboxSelected>>", self._on_preset_changed)
        row += 1
        self._preset_key_map = dict(zip(preset_names, preset_keys))
        self._preset_name_map = dict(zip(preset_keys, preset_names))

        ttk.Label(tab, text=_("settings.api.key")).grid(row=row, column=0, sticky="w", pady=(0, 2))
        row += 1
        self._api_key_var = tk.StringVar()
        ttk.Entry(tab, textvariable=self._api_key_var, show="•", width=50).grid(row=row, column=0, sticky="ew", pady=(0, 10))
        row += 1

        ttk.Label(tab, text=_("settings.api.base_url")).grid(row=row, column=0, sticky="w", pady=(0, 2))
        row += 1
        self._base_url_var = tk.StringVar()
        self._base_url_entry = ttk.Entry(tab, textvariable=self._base_url_var, width=50)
        self._base_url_entry.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        row += 1

        ttk.Label(tab, text=_("settings.api.model")).grid(row=row, column=0, sticky="w", pady=(0, 2))
        row += 1
        self._model_var = tk.StringVar()
        self._model_combo = ttk.Combobox(tab, textvariable=self._model_var, state="readonly", width=30)
        self._model_combo.grid(row=row, column=0, sticky="w", pady=(0, 10))
        row += 1

        self._api_tip = ttk.Label(tab, text=_("settings.api.tip"), foreground="gray")
        self._api_tip.grid(row=row, column=0, sticky="w", pady=(10, 0))
        tab.columnconfigure(0, weight=1)

    def _on_preset_changed(self, _event=None):
        preset_name = self._preset_var.get()
        preset_key = self._preset_key_map.get(preset_name, "custom")
        preset = PROVIDER_PRESETS.get(preset_key)
        if preset is None:
            return
        self._base_url_var.set(preset["base_url"])
        models = preset["models"]
        self._model_combo["values"] = models
        if preset_key == "custom":
            self._model_combo.configure(state="normal")
            self._base_url_entry.configure(state="normal")
        else:
            self._model_combo.configure(state="readonly")
            self._base_url_entry.configure(state="normal")
            if models:
                self._model_var.set(models[0])

    # ── 外观 ──────────────────────────────────────────────────

    def _build_appearance_tab(self, notebook: ttk.Notebook):
        tab = ttk.Frame(notebook, padding=15)
        notebook.add(tab, text=_("settings.tab.appearance"))
        row = 0

        # 界面语言
        ttk.Label(tab, text=_("settings.appearance.ui_lang"), font=("", 10, "bold")).grid(row=row, column=0, sticky="w", pady=(0, 2))
        row += 1
        self._ui_lang_var = tk.StringVar()
        ui_lang_names = list(AVAILABLE_LANGUAGES.values())
        self._ui_lang_key_map = {name: code for code, name in AVAILABLE_LANGUAGES.items()}
        ttk.Combobox(tab, textvariable=self._ui_lang_var, values=ui_lang_names, state="readonly", width=18).grid(
            row=row, column=0, sticky="w", pady=(0, 15)
        )
        row += 1

        # 主题
        ttk.Label(tab, text=_("settings.appearance.theme"), font=("", 10, "bold")).grid(row=row, column=0, sticky="w", pady=(0, 5))
        row += 1
        self._theme_var = tk.StringVar()
        theme_frame = ttk.Frame(tab)
        theme_frame.grid(row=row, column=0, sticky="w", pady=(0, 15))
        ttk.Radiobutton(theme_frame, text=_("settings.appearance.theme_light"), variable=self._theme_var, value="light").pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(theme_frame, text=_("settings.appearance.theme_dark"), variable=self._theme_var, value="dark").pack(side=tk.LEFT)
        row += 1

        # 字体
        ttk.Label(tab, text=_("settings.appearance.font_size"), font=("", 10, "bold")).grid(row=row, column=0, sticky="w", pady=(0, 5))
        row += 1
        size_frame = ttk.Frame(tab)
        size_frame.grid(row=row, column=0, sticky="w")
        self._font_size_var = tk.IntVar()
        ttk.Spinbox(size_frame, from_=8, to=20, textvariable=self._font_size_var, width=5).pack(side=tk.LEFT)
        ttk.Label(size_frame, text=_("settings.appearance.font_size_range")).pack(side=tk.LEFT)

    # ── 翻译 ──────────────────────────────────────────────────

    def _build_translation_tab(self, notebook: ttk.Notebook):
        tab = ttk.Frame(notebook, padding=15)
        notebook.add(tab, text=_("settings.tab.translation"))
        langs = TranslationEngine.supported_languages()
        display_names = list(langs.values())
        row = 0

        ttk.Label(tab, text=_("settings.translation.src")).grid(row=row, column=0, sticky="w", pady=(0, 2))
        row += 1
        self._src_lang_var = tk.StringVar()
        ttk.Combobox(tab, textvariable=self._src_lang_var, values=display_names, state="readonly", width=18).grid(row=row, column=0, sticky="w", pady=(0, 15))
        row += 1

        ttk.Label(tab, text=_("settings.translation.tgt")).grid(row=row, column=0, sticky="w", pady=(0, 2))
        row += 1
        self._tgt_lang_var = tk.StringVar()
        ttk.Combobox(tab, textvariable=self._tgt_lang_var, values=display_names, state="readonly", width=18).grid(row=row, column=0, sticky="w", pady=(0, 15))
        row += 1

        ttk.Label(tab, text=_("settings.translation.temp")).grid(row=row, column=0, sticky="w", pady=(0, 2))
        row += 1
        temp_frame = ttk.Frame(tab)
        temp_frame.grid(row=row, column=0, sticky="w")
        self._temp_var = tk.DoubleVar()
        ttk.Scale(temp_frame, from_=0.0, to=2.0, variable=self._temp_var, length=220).pack(side=tk.LEFT)
        self._temp_label = ttk.Label(temp_frame, width=4)
        self._temp_label.pack(side=tk.LEFT, padx=(8, 0))
        def _update_temp(*_):
            self._temp_label.configure(text=f"{self._temp_var.get():.1f}")
        self._temp_var.trace_add("write", _update_temp)
        row += 1
        ttk.Label(tab, text=_("settings.translation.temp_tip"), foreground="gray").grid(row=row, column=0, sticky="w", pady=(2, 0))

    # ── 行为 ──────────────────────────────────────────────────

    def _build_behavior_tab(self, notebook: ttk.Notebook):
        tab = ttk.Frame(notebook, padding=15)
        notebook.add(tab, text=_("settings.tab.behavior"))

        self._auto_copy_var = tk.BooleanVar()
        ttk.Checkbutton(tab, text=_("settings.behavior.auto_copy"), variable=self._auto_copy_var).grid(row=0, column=0, sticky="w", pady=(0, 10))

        ttk.Separator(tab, orient="horizontal").grid(row=1, column=0, sticky="ew", pady=10)
        ttk.Label(tab, text=_("settings.behavior.more"), foreground="gray").grid(row=2, column=0, sticky="w")
        tab.columnconfigure(0, weight=1)

    # ── 数据加载 / 保存 ────────────────────────────────────────

    def _load_values(self):
        s = self._sm.s
        lang_map = {name: code for code, name in TranslationEngine.supported_languages().items()}

        # Provider
        current_preset = s.provider_preset
        preset_name = self._preset_name_map.get(current_preset, "自定义")
        self._preset_var.set(preset_name)

        # API
        self._api_key_var.set(get_api_key())
        self._base_url_var.set(s.api_base_url)
        preset = PROVIDER_PRESETS.get(current_preset, PROVIDER_PRESETS["custom"])
        self._model_combo["values"] = preset["models"]
        if current_preset == "custom":
            self._model_combo.configure(state="normal")
        self._model_var.set(s.api_model)

        # 外观
        ui_lang_name = AVAILABLE_LANGUAGES.get(s.ui_language, "中文")
        self._ui_lang_var.set(ui_lang_name)
        self._theme_var.set(s.theme)
        self._font_size_var.set(s.font_size)

        # 翻译
        src_name = TranslationEngine.get_display_name(s.default_source_lang)
        tgt_name = TranslationEngine.get_display_name(s.default_target_lang)
        self._src_lang_var.set(src_name if src_name in lang_map.values() else "自动检测")
        self._tgt_lang_var.set(tgt_name if tgt_name in lang_map.values() else "中文")
        self._temp_var.set(s.temperature)
        self._temp_label.configure(text=f"{s.temperature:.1f}")

        # 行为
        self._auto_copy_var.set(s.auto_copy)

    def _save(self):
        lang_map = {name: code for code, name in TranslationEngine.supported_languages().items()}
        preset_name = self._preset_var.get()
        preset_key = self._preset_key_map.get(preset_name, "custom")
        ui_lang_display = self._ui_lang_var.get()
        ui_lang_code = self._ui_lang_key_map.get(ui_lang_display, "zh")

        # API Key
        key = self._api_key_var.get().strip()
        if key:
            save_api_key(key)
            import os
            os.environ["API_KEY"] = key
            os.environ["DEEPSEEK_API_KEY"] = key

        # 保存
        self._sm.update(
            provider_preset=preset_key,
            api_base_url=self._base_url_var.get().strip(),
            api_model=self._model_var.get().strip(),
            ui_language=ui_lang_code,
            theme=self._theme_var.get(),
            font_size=self._font_size_var.get(),
            default_source_lang=lang_map.get(self._src_lang_var.get(), "auto"),
            default_target_lang=lang_map.get(self._tgt_lang_var.get(), "zh"),
            temperature=round(self._temp_var.get(), 1),
            auto_copy=self._auto_copy_var.get(),
        )

        if self._on_save:
            self._on_save()

        self.destroy()
