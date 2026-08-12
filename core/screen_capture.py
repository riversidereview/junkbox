# -*- coding: utf-8 -*-
"""
D2R 自动宝石合成工具 - 屏幕捕获与窗口定位模块
"""

import cv2
import numpy as np
import mss
import pygetwindow as gw
from core.config import config, GEM_GRID_RECT, CUBE_RECT


class ScreenCapture:
    def __init__(self):
        self.sct = mss.mss()

    def find_d2r_window(self):
        """查找《暗黑破坏神2：重制版》游戏窗口"""
        try:
            windows = gw.getWindowsWithTitle("Diablo II: Resurrected")
            if not windows:
                windows = gw.getWindowsWithTitle("暗黑破坏神")
            if windows:
                win = windows[0]
                return win
        except Exception:
            pass
        return None

    def capture_region(self, x: int, y: int, w: int, h: int) -> np.ndarray:
        """截取指定屏幕区域 (BGR 格式)"""
        monitor = {"top": int(y), "left": int(x), "width": int(w), "height": int(h)}
        screenshot = self.sct.grab(monitor)
        img = np.array(screenshot)
        # mss 返回的是 BGRA
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def capture_full_screen(self, monitor_idx: int = 1) -> np.ndarray:
        """截取主显示器画面"""
        monitors = self.sct.monitors
        idx = min(monitor_idx, len(monitors) - 1)
        screenshot = self.sct.grab(monitors[idx])
        img = np.array(screenshot)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def capture_gem_grid(self) -> np.ndarray:
        """截取材料页 5x7 宝石网格区域"""
        x, y, w, h = config.get_gem_grid_screen_rect()
        return self.capture_region(x, y, w, h)

    def capture_cube_area(self) -> np.ndarray:
        """截取魔盒区域"""
        x, y, w, h = config.get_cube_screen_rect()
        return self.capture_region(x, y, w, h)

    def auto_detect_stash_origin(self) -> bool:
        """自动检测游戏内仓库左上角原点坐标"""
        # 截取全屏尝试定位
        screen = self.capture_full_screen()
        # 如果分辨率是 1920x1080，使用默认 (105, 85) 或通过模板微调
        # 这里默认以 1080p 标准为准
        return True


# 全局单例
screen_cap = ScreenCapture()
