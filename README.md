# 翻译工具

基于大模型 API 的桌面翻译工具，支持手动翻译 + 划词翻译，tkinter + sv_ttk 构建界面。

**支持 DeepSeek、OpenAI 及任何兼容 OpenAI SDK 格式的 API 服务。**

## 功能

### 手动翻译
- 输入文本，点击翻译或 `Ctrl+Enter`
- 18 种语言支持，自动检测 + 手动选择
- 暗黑模式 / 亮色主题，字体大小可调
- 多服务商一键切换（DeepSeek ↔ OpenAI ↔ 自定义）

### 划词翻译
- 点击 **"✂ 划词翻译"** 进入划词模式
- 在**任何软件**中选中文字，浮窗自动显示翻译
- 浮窗内置语言选择和开关，随时开关监听
- 最小化到系统托盘，不干扰工作流
- 剪贴板零污染（借还机制，用户无感）

### 界面多语言
- 设置 → 外观 → 界面语言：中文 / English / 日本語
- 切换即时生效，翻译目标语言名跟随界面语言变化

## 快速开始

### 环境要求

- Python 3.10+
- 任一 OpenAI 兼容 API Key

### 安装与运行

```powershell
# 1. 克隆仓库
git clone <repo-url>
cd translator

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 API Key（二选一）
#    方式 A：创建 .env 文件
copy .env.example .env
#    编辑 .env，填入 API_KEY=你的key

#    方式 B：直接启动，首次运行弹出输入框
#    输入的 Key 自动写入 .env

# 4. 运行
python main.py
```

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + Enter` | 执行翻译 |
| `Ctrl + C` | 复制译文 |

## Git 仓库说明

### 需要提交的文件

源码仓库只包含代码，**不含**构建产物和本地配置：

```
translator/
├── main.py
├── requirements.txt
├── .env.example                 # API Key 模板（不含真实 Key）
├── .gitignore
├── README.md
│
├── locales/                     # 界面翻译文件
│   ├── zh.json
│   ├── en.json
│   └── ja.json
│
└── src/
    ├── config.py                # 配置管理
    ├── core/
    │   ├── engine.py            # 翻译引擎
    │   ├── locale.py            # 多语言管理
    │   ├── selection_monitor.py # 全局划词监听
    │   └── providers/
    │       ├── base.py          # Provider 抽象基类
    │       └── deepseek.py      # OpenAI 兼容通用实现
    └── gui/
        ├── main_window.py       # 主窗口
        ├── float_window.py      # 划词翻译浮窗
        ├── tray_manager.py      # 系统托盘
        └── settings_window.py   # 设置对话框
```

### 不会提交的文件（.gitignore）

| 文件 / 目录 | 原因 |
|-------------|------|
| `.env` | 包含 API Key，敏感信息 |
| `settings.json` | 用户本地偏好，首次运行自动生成 |
| `dist/` `build/` | PyInstaller 构建产物 |
| `__pycache__/` | Python 缓存 |

## 项目结构

```
translator/
├── main.py                          # 入口
├── requirements.txt                 # 依赖
├── .env.example                     # API Key 模板
├── .gitignore
│
├── locales/                         # 界面翻译 JSON
│   ├── zh.json
│   ├── en.json
│   └── ja.json
│
└── src/
    ├── config.py                    # SettingsManager(单例) + Provider 预设
    ├── core/
    │   ├── engine.py                # TranslationEngine — 翻译编排
    │   ├── locale.py                # LocaleManager(单例) — 多语言
    │   ├── selection_monitor.py     # 全局鼠标钩子 + 剪贴板零污染取词
    │   └── providers/
    │       ├── base.py              # TranslatorProvider (ABC)
    │       └── deepseek.py          # OpenAICompatibleProvider（通用）
    └── gui/
        ├── main_window.py           # 主窗口
        ├── float_window.py          # 划词翻译浮窗
        ├── tray_manager.py          # 系统托盘
        └── settings_window.py       # 设置对话框
```

## 架构设计

### 分层架构

```
┌──────────────────────────────────────────────────┐
│  gui/                                            │  ← 展示层
│  main_window.py  float_window.py  tray_manager   │
├──────────────────────────────────────────────────┤
│  core/engine.py          core/locale.py          │  ← 业务层
│  翻译编排 / 多语言管理                             │
├──────────────────────────────────────────────────┤
│  core/selection_monitor.py                       │  ← 输入层
│  全局鼠标钩子 + Win32 进程白名单                   │
├──────────────────────────────────────────────────┤
│  core/providers/                                 │  ← API 层
│  OpenAICompatibleProvider（一个类通吃所有兼容 API） │
├──────────────────────────────────────────────────┤
│  config.py                                       │  ← 配置层
│  SettingsManager + .env / settings.json           │
└──────────────────────────────────────────────────┘
```

### 划词翻译流程

```
用户在任意软件选中文字
        │
        ▼
  全局鼠标钩子（pynput）检测左键松开
        │
        ▼
  Win32 API 检查鼠标所在窗口进程
  ── 是本进程 → 跳过（浮窗操作）
  ── 不是本进程 → 继续
        │
        ▼
  备份剪贴板 → 模拟 Ctrl+C → 读取 → 还原剪贴板
        │
        ▼
  浮窗显示原文 → 后台线程调用 API → 浮窗显示译文
```

### Provider 预设

`config.py` 中的 `PROVIDER_PRESETS`：

```python
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
    "custom": {"name": "自定义", "base_url": "", "models": []},
}
```

设置界面选择服务商，base_url 和模型列表自动填充。

## 打包为 EXE

```powershell
# 安装打包工具
pip install pyinstaller

# 构建（输出到 dist/Translator/）
pyinstaller --noconsole --name Translator \
    --add-data "locales;locales" \
    --collect-data sv_ttk \
    --exclude-module PyQt5 --exclude-module PyQt6 \
    --exclude-module numpy --exclude-module pandas \
    --exclude-module matplotlib --exclude-module notebook \
    --clean main.py
```

构建完成后将 `dist/Translator/` 整个文件夹分发给用户，双击 `Translator.exe` 运行。

> **注意**：如果使用 Anaconda 环境，建议排除无关科学计算包以减小体积。使用纯净 venv 可以省略大部分 `--exclude-module`。

## 扩展指南

### 添加新的 LLM Provider

**OpenAI 兼容协议 → 零代码**：设置 → API → 服务商选"自定义"，填入地址和模型。

**非 OpenAI 协议 → 写一个类**：
1. 在 `src/core/providers/` 建新文件，实现 `TranslatorProvider` ABC
2. 在 `main_window.py` 的 `_init_engine()` 中切换实例

### 添加新语言（翻译目标语言）

编辑 `src/core/engine.py` 的 `LANGUAGES` 字典和三个 `locales/*.json` 的 `lang.xxx` 条目。

### 添加新的界面语言

1. 复制 `locales/en.json` 为 `locales/fr.json`
2. 翻译所有条目
3. 在 `src/core/locale.py` 的 `AVAILABLE_LANGUAGES` 中添加 `"fr": "Français"`

### 添加新的设置项

1. `config.py` 的 `AppSettings` 加字段
2. `settings_window.py` 对应标签页加控件
3. `_load_values()` / `_save()` 中读写
4. `main_window.py` 的 `_on_settings_saved()` 中响应变更

## 依赖

| 包 | 用途 |
|----|------|
| `openai` | OpenAI 兼容 API 调用 |
| `python-dotenv` | 从 .env 加载 API Key |
| `sv-ttk` | Sun Valley 主题 + 暗黑模式 |
| `pynput` | 全局鼠标钩子 + 模拟键盘 |
| `pyperclip` | 剪贴板读写（借还机制） |
| `pystray` | 系统托盘 |
| `Pillow` | 托盘图标生成 |

## License

MIT
