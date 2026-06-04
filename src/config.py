"""应用配置管理。

- API Key 等敏感信息 → .env 文件
- 其余设置 → settings.json（首次运行自动生成默认值）
"""

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

import sys

# 开发环境：项目根目录。打包后：EXE 所在目录（.env / settings.json 放这）
if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys.executable).parent
else:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]

ENV_FILE = PROJECT_ROOT / ".env"
SETTINGS_FILE = PROJECT_ROOT / "settings.json"

load_dotenv(ENV_FILE)


# ═══════════════════════════════════════════════════════════════
# Provider 预设 — 选服务商，自动填好地址和模型列表
# ═══════════════════════════════════════════════════════════════

PROVIDER_PRESETS = {
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "models": ["deepseek-chat", "deepseek-reasoner"],
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    },
    "custom": {
        "name": "自定义",
        "base_url": "",
        "models": [],
    },
}

# ═══════════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════════


@dataclass
class AppSettings:
    """可持久化的应用设置（存于 settings.json）。"""

    # ── 外观 ────────────────────────────────────────────────
    ui_language: str = "zh"      # "zh" | "en" | "ja"
    theme: str = "light"         # "light" | "dark"
    font_size: int = 11          # 8 ~ 20

    # ── 翻译 ────────────────────────────────────────────────
    default_source_lang: str = "auto"
    default_target_lang: str = "zh"
    temperature: float = 0.3     # 0.0 ~ 2.0

    # ── 行为 ────────────────────────────────────────────────
    auto_copy: bool = False      # 翻译后自动复制译文

    # ── API ─────────────────────────────────────────────────
    provider_preset: str = "deepseek"   # 对应 PROVIDER_PRESETS 的 key
    api_base_url: str = "https://api.deepseek.com"
    api_model: str = "deepseek-chat"

    # 兼容旧版 settings.json 字段名
    def __post_init__(self):
        pass  # 迁移逻辑在 SettingsManager._load() 中处理


# ═══════════════════════════════════════════════════════════════
# 设置管理器（单例）
# ═══════════════════════════════════════════════════════════════


class SettingsManager:
    """单例设置管理器，读写 settings.json。"""

    _instance: "SettingsManager | None" = None

    def __init__(self) -> None:
        self._settings = AppSettings()
        self._load()

    @classmethod
    def instance(cls) -> "SettingsManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── 持久化 ──────────────────────────────────────────────

    def _load(self) -> None:
        if not SETTINGS_FILE.exists():
            return

        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, TypeError):
            return

        # 兼容旧字段名（迁移 deepseek_xxx → api_xxx）
        _migrate = {
            "deepseek_base_url": "api_base_url",
            "deepseek_model": "api_model",
        }
        for old, new in _migrate.items():
            if old in data and new not in data:
                data[new] = data.pop(old)

        fields = AppSettings.__dataclass_fields__
        for k, v in data.items():
            if k in fields:
                setattr(self._settings, k, v)

    def save(self) -> None:
        SETTINGS_FILE.write_text(
            json.dumps(asdict(self._settings), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # ── 访问 ────────────────────────────────────────────────

    @property
    def s(self) -> AppSettings:
        """快捷访问: SettingsManager.instance().s.theme"""
        return self._settings

    def update(self, **kwargs: Any) -> None:
        """批量更新并自动保存。"""
        for k, v in kwargs.items():
            if hasattr(self._settings, k):
                setattr(self._settings, k, v)
        self.save()

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self._settings, key, default)


# ═══════════════════════════════════════════════════════════════
# API Key（敏感信息，只存 .env）
# ═══════════════════════════════════════════════════════════════


def get_api_key() -> str:
    """读取 API Key。优先读 API_KEY，向下兼容 DEEPSEEK_API_KEY。"""
    return os.getenv("API_KEY") or os.getenv("DEEPSEEK_API_KEY", "")


def save_api_key(key: str) -> None:
    """写入 .env 文件，存储为 API_KEY 并为兼容保留 DEEPSEEK_API_KEY。"""
    env_path = Path(ENV_FILE)
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    found_api = found_ds = False
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("API_KEY="):
            new_lines.append(f"API_KEY={key}")
            found_api = True
        elif stripped.startswith("DEEPSEEK_API_KEY="):
            new_lines.append(f"DEEPSEEK_API_KEY={key}")
            found_ds = True
        else:
            new_lines.append(line)

    if not found_api:
        new_lines.append(f"API_KEY={key}")
    if not found_ds:
        new_lines.append(f"DEEPSEEK_API_KEY={key}")

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
