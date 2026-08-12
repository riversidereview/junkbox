# -*- coding: utf-8 -*-
"""
D2R 自动宝石合成工具 - 配置文件与坐标定义
目标分辨率: 1920x1080 (1080p)
"""

import os
import sys
import json


def get_resource_path(relative_path: str) -> str:
    """获取资源文件的绝对路径 (兼顾源码运行与 PyInstaller 打包运行)"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, relative_path)


# 7 种宝石定义 (从左到右 7 列)
GEM_TYPES = [
    {"id": "diamond",  "name": "钻石",   "color": "#e0e6ed", "col": 0},
    {"id": "emerald",  "name": "绿宝石", "color": "#2ecc71", "col": 1},
    {"id": "ruby",     "name": "红宝石", "color": "#e74c3c", "col": 2},
    {"id": "topaz",    "name": "黄宝石", "color": "#f1c40f", "col": 3},
    {"id": "amethyst", "name": "紫宝石", "color": "#9b59b6", "col": 4},
    {"id": "sapphire", "name": "蓝宝石", "color": "#3498db", "col": 5},
    {"id": "skull",    "name": "骷髅",   "color": "#ecf0f1", "col": 6},
]

# 5 个等级定义 (从上到下 5 行)
GEM_TIERS = [
    {"id": "chipped",  "name": "碎裂",    "row": 0, "next_tier": 1},
    {"id": "flawed",   "name": "有瑕疵",  "row": 1, "next_tier": 2},
    {"id": "normal",   "name": "普通",    "row": 2, "next_tier": 3},
    {"id": "flawless", "name": "无瑕",    "row": 3, "next_tier": 4},
    {"id": "perfect",  "name": "完美",    "row": 4, "next_tier": None},
]

# 1080p (1920x1080) 标准坐标系 (相对于仓库 Stash 左上角原点)
DEFAULT_STASH_ORIGIN = {"x": 105, "y": 85}

# 材料页 5x7 宝石格子的相对中心坐标 (相对于仓库左上角)
GEM_COL_X = [82, 135, 189, 242, 296, 349, 402]
GEM_ROW_Y = [486, 541, 596, 651, 707]
GEM_GRID_RECT = {"x": 56, "y": 459, "w": 373, "h": 277}

# 魔盒区域 (Cube) 相对坐标
CUBE_COL_X = [315, 364, 413]
CUBE_ROW_Y = [268, 317, 366, 415]
CUBE_RECT = {"x": 283, "y": 236, "w": 168, "h": 211}

# 合成按钮 (Transmute) 中心相对坐标
TRANSMUTE_BTN = {"x": 236, "y": 340}

# 材料 Tab 相对坐标
MATERIAL_TAB = {"x": 310, "y": 115}

CONFIG_FILE_PATH = "config_custom.json"


class ConfigManager:
    """管理并持久化用户自定义配置与延迟"""
    def __init__(self):
        self.stash_x = DEFAULT_STASH_ORIGIN["x"]
        self.stash_y = DEFAULT_STASH_ORIGIN["y"]
        self.click_delay = 0.08          # 单次点击间隙 (秒)
        self.step_delay = 0.15           # 步骤间隙 (秒)
        self.verify_timeout = 1.0        # 视觉校验超时 (秒)
        self.hotkey_stop = "1"           # 停止热键 (小键盘1 / Num 1)
        self.dry_run = False             # 模拟测试模式 (只打印动作，不真实触发鼠标)
        self.enable_verification = True  # 是否启用魔盒状态机器视觉核验
        self.keep_twenty = False         # 保留20颗宝石选项 (少于或等于20颗时自动合成下一级)
        self.load()

    def get_gem_screen_pos(self, row: int, col: int):
        """获取指定行列宝石格子的绝对屏幕坐标"""
        return (self.stash_x + GEM_COL_X[col], self.stash_y + GEM_ROW_Y[row])

    def get_cube_slot_screen_pos(self, row: int = 0, col: int = 0):
        """获取魔盒指定槽位绝对屏幕坐标"""
        return (self.stash_x + CUBE_COL_X[col], self.stash_y + CUBE_ROW_Y[row])

    def get_transmute_btn_screen_pos(self):
        """获取合成按钮绝对屏幕坐标"""
        return (self.stash_x + TRANSMUTE_BTN["x"], self.stash_y + TRANSMUTE_BTN["y"])

    def get_gem_grid_screen_rect(self):
        """获取宝石矩阵的绝对屏幕截屏区域"""
        return (
            self.stash_x + GEM_GRID_RECT["x"],
            self.stash_y + GEM_GRID_RECT["y"],
            GEM_GRID_RECT["w"],
            GEM_GRID_RECT["h"]
        )

    def get_cube_screen_rect(self):
        """获取魔盒区域绝对屏幕截屏区域"""
        return (
            self.stash_x + CUBE_RECT["x"],
            self.stash_y + CUBE_RECT["y"],
            CUBE_RECT["w"],
            CUBE_RECT["h"]
        )

    def load(self):
        if os.path.exists(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.stash_x = data.get("stash_x", self.stash_x)
                    self.stash_y = data.get("stash_y", self.stash_y)
                    self.click_delay = data.get("click_delay", self.click_delay)
                    self.step_delay = data.get("step_delay", self.step_delay)
                    self.hotkey_stop = data.get("hotkey_stop", self.hotkey_stop)
                    self.enable_verification = data.get("enable_verification", self.enable_verification)
                    self.keep_twenty = data.get("keep_twenty", self.keep_twenty)
            except Exception as e:
                print(f"加载配置文件失败: {e}")

    def save(self):
        data = {
            "stash_x": self.stash_x,
            "stash_y": self.stash_y,
            "click_delay": self.click_delay,
            "step_delay": self.step_delay,
            "hotkey_stop": self.hotkey_stop,
            "enable_verification": self.enable_verification,
            "keep_twenty": self.keep_twenty,
        }
        try:
            with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")


# 全局单例配置
config = ConfigManager()
