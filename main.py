# -*- coding: utf-8 -*-
"""
《暗黑破坏神2:重制版》自动宝石合成工具
程序主入口
"""

import sys
import os

# 将当前目录加入 python 模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from ui.dark_theme import DARK_THEME_QSS
from ui.main_window import MainWindow


def main():
    # 支持高分屏适配
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME_QSS)

    # 设置应用图标 (如果有宝石图标)
    icon_path = os.path.join("assets", "gems", "amethyst_perfect.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
