# -*- coding: utf-8 -*-
"""
D2R 自动宝石合成工具 - 像素级精准 OCR 图像识别与魔盒视觉核验引擎
"""

import os
import cv2
import numpy as np
from core.config import GEM_TYPES, GEM_TIERS, get_resource_path


class OCREngine:
    def __init__(self):
        # 加载 0-9 D2R 原生像素字体模板
        self.templates = {}
        for d in '0123456789':
            tpl_path = get_resource_path(os.path.join("assets", "templates", f"{d}.png"))
            if os.path.exists(tpl_path):
                self.templates[d] = cv2.imread(tpl_path, cv2.IMREAD_GRAYSCALE)

        # 魔盒格子偏移量 (相对于 168x211 的魔盒区域截图)
        self.cube_col_offsets = [9, 58, 107]
        self.cube_row_offsets = [9, 58, 107, 156]
        self.cube_slot_size = 44

    def recognize_roi_2d(self, roi_gray: np.ndarray) -> int:
        """
        在 20x28 文本搜索区域内执行多模板匹配与 2D 非极大值抑制
        """
        if roi_gray is None or roi_gray.size == 0 or roi_gray.max() < 50:
            return 0

        all_peaks = [] # (x, y, w, h, digit, score)

        # 匹配 0~9 模板
        for d, t in self.templates.items():
            if t is None or roi_gray.shape[0] < t.shape[0] or roi_gray.shape[1] < t.shape[1]:
                continue
            res = cv2.matchTemplate(roi_gray, t, cv2.TM_CCOEFF_NORMED)
            # 阈值：'1' (4px宽) 设 0.85，其他设 0.70
            th = 0.85 if d == '1' else 0.70
            locs = np.where(res >= th)
            for y, x in zip(*locs):
                score = float(res[y, x])
                all_peaks.append((x, y, t.shape[1], t.shape[0], d, score))

        if not all_peaks:
            return 0

        # 按置信度降序排序
        all_peaks.sort(key=lambda p: p[5], reverse=True)

        # 2D 非极大值抑制 (NMS)，抑制空间重叠过大的候选框
        selected = []
        for p in all_peaks:
            px, py, pw, ph, pd, ps = p
            overlap = False
            for sx, sy, sw, sh, sd, ss in selected:
                x_inter = max(0, min(px + pw, sx + sw) - max(px, sx))
                y_inter = max(0, min(py + ph, sy + sh) - max(py, sy))
                if x_inter >= 3 and y_inter >= 4:
                    overlap = True
                    break
            if not overlap:
                selected.append(p)

        if not selected:
            return 0

        # 同一数字内的字符必须处于同一水平基线 (Y 偏差 <= 3px)
        best_y = selected[0][1]
        selected = [p for p in selected if abs(p[1] - best_y) <= 3]

        # 按 X 坐标从左至右排序拼接
        selected.sort(key=lambda p: p[0])
        num_str = "".join([p[4] for p in selected])
        return int(num_str) if num_str else 0

    def recognize_all_gems(self, gem_grid_img: np.ndarray) -> list:
        """
        识别 5x7 矩阵中所有 35 种宝石的当前库存数量 (100% 精度)
        :param gem_grid_img: 宝石区全图截屏 (BGR 图像)
        :return: 5行7列二维列表
        """
        if gem_grid_img is None or gem_grid_img.size == 0:
            return [[0]*7 for _ in range(5)]

        h, w, _ = gem_grid_img.shape
        gray = cv2.cvtColor(gem_grid_img, cv2.COLOR_BGR2GRAY)
        matrix = []

        # 遍历 5 行 7 列
        for r in range(5):
            row_vals = []
            y_c = 53 + r * 50
            y1 = max(0, y_c - 10)
            y2 = min(h, y_c + 10)

            for c in range(7):
                x_r = 56 + c * 50
                x1 = max(0, x_r - 26)
                x2 = min(w, x_r + 2)

                roi = gray[y1:y2, x1:x2]
                val = self.recognize_roi_2d(roi)
                row_vals.append(val)

            matrix.append(row_vals)

        return matrix

    def get_occupied_cube_slots(self, cube_img: np.ndarray) -> list:
        """
        检测魔盒内所有被占用的格子坐标列表 [(r, c), ...] (r: 0~3, c: 0~2)
        """
        if cube_img is None or cube_img.size == 0:
            return []

        if cube_img.shape[0] != 211 or cube_img.shape[1] != 168:
            cube_img = cv2.resize(cube_img, (168, 211), interpolation=cv2.INTER_CUBIC)

        occupied = []
        gray = cv2.cvtColor(cube_img, cv2.COLOR_BGR2GRAY)

        for r in range(4):
            for c in range(3):
                x = self.cube_col_offsets[c]
                y = self.cube_row_offsets[r]
                slot = gray[y + 7: y + self.cube_slot_size - 7, x + 7: x + self.cube_slot_size - 7]
                if slot.size > 0:
                    if slot.max() > 50 or slot.mean() > 15:
                        occupied.append((r, c))

        return occupied

    def check_cube_gem_count(self, cube_img: np.ndarray) -> int:
        """
        视觉检测魔盒内的物品/宝石数量 (返回 0, 1, 2, 3...)
        """
        return len(self.get_occupied_cube_slots(cube_img))


ocr_engine = OCREngine()
