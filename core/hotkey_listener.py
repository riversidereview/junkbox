# -*- coding: utf-8 -*-
"""
D2R 自动宝石合成工具 - 全局热键监听器 (专注小键盘1 / Num 1，防冲突原生监听)
"""

import time
import threading
import ctypes
import pyautogui
from PySide6.QtCore import QObject, Signal

# Windows 常用无冲突虚拟键码字典 {key_name: (vk_code, display_name)}
AVAILABLE_HOTKEYS = {
    "Num 1": (0x61, "小键盘 1 (Num 1)"),
    "Num 0": (0x60, "小键盘 0 (Num 0)"),
    "Num 2": (0x62, "小键盘 2 (Num 2)"),
    "Num 3": (0x63, "小键盘 3 (Num 3)"),
    "Num 4": (0x64, "小键盘 4 (Num 4)"),
    "Num 5": (0x65, "小键盘 5 (Num 5)"),
    "F1": (0x70, "F1 键"),
    "F2": (0x71, "F2 键"),
    "F3": (0x72, "F3 键"),
    "F4": (0x73, "F4 键"),
    "F8": (0x77, "F8 键"),
    "F9": (0x78, "F9 键"),
    "F10": (0x79, "F10 键"),
    "F11": (0x7A, "F11 键"),
    "F12": (0x7B, "F12 键"),
    "Pause": (0x13, "Pause / Break 键"),
    "Esc": (0x1B, "ESC 键"),
    "~ (Tilde)": (0xC0, "~ / ` 波浪键"),
}


class HotkeyBridge(QObject):
    """Qt 线程安全信号桥接器"""
    hotkey_pressed = Signal()


class HotkeyListener:
    def __init__(self):
        self.bridge = HotkeyBridge()
        self._stop_callbacks = []
        self._is_running = False
        self._thread = None
        self._last_trigger_time = 0.0
        self.current_vk = 0x61 # 默认小键盘 1 (VK_NUMPAD1)
        self.current_key_name = "Num 1"

    def set_hotkey(self, key_name: str):
        """动态修改监听的热键"""
        if key_name in AVAILABLE_HOTKEYS:
            self.current_key_name = key_name
            self.current_vk = AVAILABLE_HOTKEYS[key_name][0]
        elif isinstance(key_name, int):
            self.current_vk = key_name

    def register_stop_callback(self, callback):
        """注册紧急停止回调函数"""
        if callback and callback not in self._stop_callbacks:
            self._stop_callbacks.append(callback)

    def unregister_stop_callback(self, callback):
        if callback in self._stop_callbacks:
            self._stop_callbacks.remove(callback)

    def _is_pressed(self, vk_code: int) -> bool:
        """原生检测物理键位是否被按下"""
        try:
            return bool(ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000)
        except Exception:
            return False

    def _listen_loop(self):
        """监听用户自定义热键，防冲突原生毫秒级监听"""
        while self._is_running:
            try:
                now = time.time()
                if self._is_pressed(self.current_vk):
                    # 防抖动 (400ms 间隔)
                    if now - self._last_trigger_time > 0.40:
                        self._last_trigger_time = now
                        self._on_hotkey_triggered()
            except Exception as e:
                print(f"热键监听线程异常: {e}")

            time.sleep(0.02) # 20ms 极低 CPU 轮询

    def _on_hotkey_triggered(self):
        """当紧急停止热键触发时"""
        # 1. 强制释放所有可能按住的键位与鼠标
        self.emergency_release_keys()

        # 2. 执行直接工作线程回调 (用于立即标记 worker._stop_requested = True)
        for cb in list(self._stop_callbacks):
            try:
                cb()
            except Exception as e:
                print(f"执行工作线程停止回调异常: {e}")

        # 3. 通过 Qt 信号安全通知 GUI 主线程
        try:
            self.bridge.hotkey_pressed.emit()
        except Exception as e:
            print(f"发射停止信号异常: {e}")

    def emergency_release_keys(self):
        """强制释放所有修饰键和鼠标按键，防止卡键"""
        try:
            pyautogui.keyUp('ctrl')
            pyautogui.keyUp('shift')
            pyautogui.keyUp('alt')
            pyautogui.mouseUp(button='left')
            pyautogui.mouseUp(button='right')
        except Exception:
            pass

    def start(self):
        """启动全局键盘监听线程"""
        if self._is_running:
            return
        self._is_running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True, name="HotkeyListenerThread")
        self._thread.start()

    def stop(self):
        """停止全局监听"""
        self._is_running = False


# 全局单例
hotkey_listener = HotkeyListener()
