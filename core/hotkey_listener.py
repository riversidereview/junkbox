# -*- coding: utf-8 -*-
"""
D2R 自动宝石合成工具 - 全局热键监听器 (专注小键盘1 / Num 1，防冲突原生监听)
"""

import time
import threading
import ctypes
import pyautogui
from PySide6.QtCore import QObject, Signal

# Windows 虚拟键码定义
VK_NUMPAD1 = 0x61    # 小键盘 1 (Num 1, 游戏专属无冲突热键)


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
        """仅在用户按下【小键盘 1】时触发，防主键盘冲突，100% 稳定"""
        while self._is_running:
            try:
                now = time.time()
                # 仅监听小键盘 1 (VK_NUMPAD1)，避免与主键盘输入打字产生任何冲突
                if self._is_pressed(VK_NUMPAD1):
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
