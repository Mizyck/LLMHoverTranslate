"""全局文本选中监听 —— 鼠标钩子 + 剪贴板零污染取词 + 进程白名单。

流程:
  用户划词 → 左键松开 → 等 200ms 让选区稳定
  → Win32 API 检查鼠标所在窗口是否属于本进程（是=浮窗操作，跳过）
  → 备份剪贴板 → 模拟 Ctrl+C → 读取 → 还原剪贴板
  → 去重 / 空文本过滤 → 回调上层
"""

import ctypes
import os
import threading
import time
from ctypes import wintypes
from typing import Callable

import pyperclip
from pynput import mouse, keyboard

# ── Win32 API ────────────────────────────────────────────────

_user32 = ctypes.windll.user32

# POINT 结构体（Win32 要求 x, y 打包传入）
_user32.WindowFromPoint.restype = wintypes.HWND
_user32.WindowFromPoint.argtypes = [wintypes.POINT]

_user32.GetWindowThreadProcessId.restype = wintypes.DWORD
_user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]


class SelectionMonitor:
    """监听全局文本选中事件。白名单：自动跳过本进程窗口（浮窗）上的鼠标操作。"""

    def __init__(self, on_selection: Callable[[str], None]):
        self._on_selection = on_selection
        self._mouse_listener: mouse.Listener | None = None
        self._running = False
        self._last_text = ""
        self._last_time = 0.0
        self._debounce_timer: threading.Timer | None = None
        self._our_pid = os.getpid()

    # ── 公开接口 ──────────────────────────────────────────────

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._mouse_listener = mouse.Listener(on_click=self._on_click)
        self._mouse_listener.start()

    def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
            self._mouse_listener = None
        self._cancel_debounce()

    # ── 白名单 ────────────────────────────────────────────────

    def _is_own_window(self, x: int, y: int) -> bool:
        """鼠标所在窗口是否属于本进程。"""
        pt = wintypes.POINT(x, y)
        hwnd = _user32.WindowFromPoint(pt)
        if hwnd is None or hwnd == 0:
            return False

        pid = wintypes.DWORD()
        _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return pid.value == self._our_pid

    # ── 内部 ──────────────────────────────────────────────────

    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool):
        if not self._running:
            return True
        if button == mouse.Button.left and not pressed:
            # 浮窗上的操作（含下拉框弹出层）→ 跳过
            if self._is_own_window(x, y):
                return True
            self._schedule_capture()
        return True

    def _schedule_capture(self):
        self._cancel_debounce()
        self._debounce_timer = threading.Timer(0.2, self._capture)
        self._debounce_timer.daemon = True
        self._debounce_timer.start()

    def _cancel_debounce(self):
        if self._debounce_timer is not None:
            self._debounce_timer.cancel()
            self._debounce_timer = None

    def _capture(self):
        try:
            backup = pyperclip.paste()
        except Exception:
            backup = ""

        kb = keyboard.Controller()
        kb.press(keyboard.Key.ctrl)
        kb.press("c")
        kb.release("c")
        kb.release(keyboard.Key.ctrl)

        time.sleep(0.05)

        try:
            text = pyperclip.paste()
        except Exception:
            text = ""

        try:
            pyperclip.copy(backup if backup else " ")
        except Exception:
            pass

        text = (text or "").strip()
        if not text or text.isspace():
            return
        if text == self._last_text and (time.time() - self._last_time) < 1.0:
            return

        self._last_text = text
        self._last_time = time.time()
        self._on_selection(text)
