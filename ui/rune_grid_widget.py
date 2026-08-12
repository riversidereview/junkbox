# -*- coding: utf-8 -*-
"""
D2R 自动宝石/符文合成工具 - 33 种符文可视化组件
结构：顶部 44x44 符文石图标 + 符文名称 + 独立居中数字栏 + 专属【合成10个】按钮 (无遮挡纯净暗黑质感)
"""

import os
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QInputDialog, QToolTip
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QCursor
from core.config import get_resource_path
from core.rune_config import RUNES_DATA, RUNES_BY_ID, get_rune_recipe_text


class RuneCellWidget(QFrame):
    """单个符文卡片 (完整图标 + 编号名称 + 独立居中数字栏 + 专属【合成10个】按钮)"""
    craft10_requested = Signal(int)     # (rune_id)
    valueChanged = Signal(int, int)      # (rune_id, new_val)

    def __init__(self, rune_info: dict):
        super().__init__()
        self.rune_info = rune_info
        self.rune_id = rune_info["id"]
        self.count = 0
        self.setProperty("class", "GemCell")
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(68, 106)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(2)

        # 1. 顶部符文图标 (38px 独立视区，等比居中，清晰完整)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(62, 38)
        self.icon_label.setAlignment(Qt.AlignCenter)

        rel_icon_path = os.path.join("assets", "runes", f"r{self.rune_id:02d}.png")
        icon_path = get_resource_path(rel_icon_path)
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(pix)
        else:
            self.icon_label.setText(f"{self.rune_id}#")
            self.icon_label.setStyleSheet("color: #d1b88a; font-size: 13px; font-weight: bold;")
        layout.addWidget(self.icon_label)

        # 2. 符文编号与名称 (如 "10# 书尔")
        self.name_label = QLabel(f"{self.rune_id}# {self.rune_info['name_zh']}")
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setFixedHeight(14)
        self.name_label.setStyleSheet("color: #c79c5e; font-size: 10px; font-weight: bold;")
        layout.addWidget(self.name_label)

        # 3. 独立居中数量栏位 (GemCountBar)
        self.count_label = QLabel("0")
        self.count_label.setProperty("class", "GemCountBar")
        self.count_label.setAlignment(Qt.AlignCenter)
        self.count_label.setFixedHeight(18)
        layout.addWidget(self.count_label)

        # 4. 专属【合成10个】按钮 (33# Zod 无合成按钮)
        if self.rune_id < 33:
            self.btn_craft10 = QPushButton("合成10个")
            self.btn_craft10.setProperty("class", "QuickCraftBtn")
            self.btn_craft10.setFixedHeight(24)
            self.btn_craft10.setStyleSheet(
                "QPushButton { font-size: 10px; font-weight: bold; padding: 2px 4px; "
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2c2518, stop:1 #1a160e); "
                "border: 1px solid #8d6e3c; border-radius: 3px; color: #f1c40f; } "
                "QPushButton:hover { background: #42361e; border-color: #f39c12; color: #ffffff; } "
                "QPushButton:pressed { background: #15120a; border-color: #634d28; }"
            )
            recipe_text = get_rune_recipe_text(self.rune_id)
            self.btn_craft10.setToolTip(f"配方: {recipe_text}\n点击尝试循环合成 10 次")
            self.btn_craft10.clicked.connect(lambda: self.craft10_requested.emit(self.rune_id))
            layout.addWidget(self.btn_craft10)
        else:
            spacer = QLabel("最高阶")
            spacer.setAlignment(Qt.AlignCenter)
            spacer.setFixedHeight(24)
            spacer.setStyleSheet("color: #777; font-size: 10px; font-weight: bold;")
            layout.addWidget(spacer)

        # 整体卡片 Tooltip 提示配方
        self.setToolTip(f"【{self.rune_id}# {self.rune_info['name_en']} {self.rune_info['name_zh']}】\n{get_rune_recipe_text(self.rune_id)}")

    def set_count(self, count: int):
        self.count = count
        self.count_label.setText(str(count))

        req = self.rune_info.get("req_runes", 3)
        if req > 0 and self.count >= req:
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
            self, "修改符文数量",
            f"设置 [{self.rune_id}# {self.rune_info['name_zh']}] 数量:",
            self.count, 0, 999
        )
        if ok:
            self.set_count(val)
            self.valueChanged.emit(self.rune_id, val)


class RuneGridWidget(QWidget):
    """33 种符文展示面板 (5行矩阵，1#~28# 4行各7个，29#~33# 第5行5个)"""
    craft10_requested = Signal(int)     # (rune_id)
    runes_changed = Signal(object)      # {rune_id: count}

    def __init__(self):
        super().__init__()
        self.cell_map = {} # rune_id -> RuneCellWidget
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        grid = QGridLayout()
        grid.setSpacing(6)

        # 遍历 33 种符文进行排版
        for rune in RUNES_DATA:
            r = rune["row"]
            c = rune["col"]
            cell = RuneCellWidget(rune)
            cell.craft10_requested.connect(self.craft10_requested.emit)
            cell.valueChanged.connect(self._on_cell_val_changed)
            self.cell_map[rune["id"]] = cell
            grid.addWidget(cell, r, c)

        main_layout.addLayout(grid)

    def _on_cell_val_changed(self, rune_id, val):
        self.runes_changed.emit(self.get_counts())

    def set_counts(self, counts_dict: dict):
        """设置 33 种符文数量 {rune_id: count} 或 {'r01': count}"""
        if not counts_dict:
            return
        for k, v in counts_dict.items():
            if isinstance(k, int) and k in self.cell_map:
                self.cell_map[k].set_count(v)
            elif isinstance(k, str):
                if k.startswith('r') and k[1:].isdigit():
                    rid = int(k[1:])
                    if rid in self.cell_map:
                        self.cell_map[rid].set_count(v)

    def update_counts(self, counts_dict: dict):
        """兼容别名"""
        self.set_counts(counts_dict)

    def get_counts(self) -> dict:
        """获取当前 33 种符文数量字典 {rune_id: count}"""
        return {rid: cell.count for rid, cell in self.cell_map.items()}
