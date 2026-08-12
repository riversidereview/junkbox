# -*- coding: utf-8 -*-
"""
D2R 自动宝石合成工具 - 5x7 宝石矩阵可视化组件 (宝石与下方独立居中数字栏)
"""

import os
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QInputDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QColor
from core.config import GEM_TYPES, GEM_TIERS, get_resource_path


class GemCellWidget(QFrame):
    """单个宝石槽位卡片 (上方完整宝石图标 + 下方独立居中数字栏)"""
    valueChanged = Signal(int, int, int) # (row, col, new_val)

    def __init__(self, row: int, col: int, gem_info: dict, tier_info: dict):
        super().__init__()
        self.row = row
        self.col = col
        self.gem_info = gem_info
        self.tier_info = tier_info
        self.count = 0
        self.setProperty("class", "GemCell")
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(66, 86)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)

        # 1. 顶部宝石图标 (独立容器，48x48 等比居中，完全不被遮挡)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(58, 50)
        self.icon_label.setAlignment(Qt.AlignCenter)

        rel_icon_path = os.path.join("assets", "gems", f"{self.gem_info['id']}_{self.tier_info['id']}.png")
        icon_path = get_resource_path(rel_icon_path)
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(44, 44, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(pix)
        else:
            self.icon_label.setText(self.gem_info['name'][:1])
            self.icon_label.setStyleSheet(f"color: {self.gem_info['color']}; font-size: 16px; font-weight: bold;")
        layout.addWidget(self.icon_label)

        # 2. 下方独立数字栏位 (单独区域，数字严格水平垂直居中)
        self.count_label = QLabel("0")
        self.count_label.setProperty("class", "GemCountBar")
        self.count_label.setAlignment(Qt.AlignCenter)
        self.count_label.setFixedHeight(18)
        layout.addWidget(self.count_label)

    def set_count(self, count: int):
        self.count = count
        self.count_label.setText(str(count))

        # 如果可合成 (数量 >= 3 且不是完美宝石)，卡片金色微光
        if self.count >= 3 and self.row < 4:
            self.setStyleSheet("QFrame.GemCell { background-color: #221e16; border: 1px solid #c79c5e; border-radius: 6px; }")
            self.count_label.setStyleSheet(
                "QLabel.GemCountBar { color: #2ecc71; font-weight: bold; background-color: #101114; "
                "border: 1px solid #4a3d24; border-radius: 3px; font-size: 12px; }"
            )
        else:
            self.setStyleSheet("")
            self.count_label.setStyleSheet(
                "QLabel.GemCountBar { color: #dedede; font-weight: bold; background-color: #101114; "
                "border: 1px solid #282a30; border-radius: 3px; font-size: 12px; }"
            )

    def mouseDoubleClickEvent(self, event):
        """双击手动修改数量 (便于离线测试)"""
        val, ok = QInputDialog.getInt(
            self, "修改宝石数量",
            f"设置 [{self.tier_info['name']} {self.gem_info['name']}] 数量:",
            self.count, 0, 999
        )
        if ok:
            self.set_count(val)
            self.valueChanged.emit(self.row, self.col, val)


class GemGridWidget(QWidget):
    """5行 x 7列 完整宝石矩阵展示面板 (无 Emoji 纯净暗黑版)"""
    quick_craft_requested = Signal(int) # (col_idx)
    matrix_changed = Signal(list)

    def __init__(self):
        super().__init__()
        self.cells = [[None for _ in range(7)] for _ in range(5)]
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        grid = QGridLayout()
        grid.setSpacing(6)

        # 1. 顶部列头 (7 种宝石名称与颜色指示)
        grid.addWidget(QLabel(""), 0, 0)
        for c, gem in enumerate(GEM_TYPES):
            header = QLabel(gem["name"])
            header.setAlignment(Qt.AlignCenter)
            header.setStyleSheet(f"color: {gem['color']}; font-weight: bold; font-size: 13px; padding-bottom: 4px;")
            grid.addWidget(header, 0, c + 1)

        # 2. 5 行宝石卡片
        for r, tier in enumerate(GEM_TIERS):
            row_label = QLabel(tier["name"])
            row_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row_label.setStyleSheet("color: #a0a0aa; font-weight: 500; font-size: 12px; padding-right: 6px;")
            grid.addWidget(row_label, r + 1, 0)

            for c, gem in enumerate(GEM_TYPES):
                cell = GemCellWidget(r, c, gem, tier)
                cell.valueChanged.connect(self._on_cell_val_changed)
                self.cells[r][c] = cell
                grid.addWidget(cell, r + 1, c + 1)

        # 3. 底部 7 个快速合成按钮
        quick_label = QLabel("快速合成:")
        quick_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        quick_label.setStyleSheet("color: #e5c158; font-size: 11px; font-weight: bold; padding-right: 6px;")
        grid.addWidget(quick_label, 6, 0)

        for c, gem in enumerate(GEM_TYPES):
            btn = QPushButton("合成")
            btn.setProperty("class", "QuickCraftBtn")
            btn.setFixedHeight(24)
            btn.setToolTip(f"只合成该列全部【{gem['name']}】至完美等级")
            btn.clicked.connect(lambda checked=False, col=c: self.quick_craft_requested.emit(col))
            grid.addWidget(btn, 6, c + 1)

        main_layout.addLayout(grid)

    def _on_cell_val_changed(self, r, c, val):
        self.matrix_changed.emit(self.get_matrix())

    def set_matrix(self, matrix: list):
        """设置 5x7 矩阵数据"""
        if not matrix:
            return
        for r in range(min(5, len(matrix))):
            for c in range(min(7, len(matrix[r]))):
                if self.cells[r][c]:
                    self.cells[r][c].set_count(matrix[r][c])

    def get_matrix(self) -> list:
        """获取当前界面的 5x7 矩阵数据"""
        res = []
        for r in range(5):
            row_vals = []
            for c in range(7):
                row_vals.append(self.cells[r][c].count if self.cells[r][c] else 0)
            res.append(row_vals)
        return res
