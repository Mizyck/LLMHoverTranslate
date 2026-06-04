"""系统托盘管理 —— 划词翻译模式下的任务栏图标。"""

import threading
import tkinter as tk
from typing import Callable

import pystray
from PIL import Image, ImageDraw, ImageFont

from ..core.locale import _


def _generate_icon() -> Image.Image:
    """生成 64x64 蓝色"译"字图标。"""
    img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=(41, 128, 185))

    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 34)
    except Exception:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/simsun.ttc", 34)
        except Exception:
            font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), "译", font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (64 - tw) / 2 - bbox[0]
    y = (64 - th) / 2 - bbox[1]
    draw.text((x, y), "译", fill="white", font=font)
    return img


class TrayManager:
    """系统托盘管理器。"""

    def __init__(
        self,
        root: tk.Tk,
        on_show_main: Callable[[], None],
        on_quit: Callable[[], None],
    ):
        self._root = root
        self._on_show_main = on_show_main
        self._on_quit = on_quit
        self._tray: pystray.Icon | None = None

    def show(self) -> None:
        if self._tray is not None:
            return

        menu = pystray.Menu(
            pystray.MenuItem(
                _("tray.show_main"), self._safe(self._on_show_main), default=True
            ),
            pystray.MenuItem(_("tray.quit"), self._safe(self._on_quit)),
        )
        self._tray = pystray.Icon(
            "translator", _generate_icon(), _("tray.tooltip"), menu
        )
        threading.Thread(target=self._tray.run, daemon=True).start()

    def hide(self) -> None:
        if self._tray is not None:
            self._tray.stop()
            self._tray = None

    def _safe(self, callback: Callable[[], None]):
        def _wrapper(icon=None, item=None):
            self._root.after(0, callback)
        return _wrapper
