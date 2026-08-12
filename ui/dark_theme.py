# -*- coding: utf-8 -*-
"""
D2R 自动宝石合成工具 - 暗黑破坏神黑金风格 UI 主题
"""

DARK_THEME_QSS = """
/* 全局基础设置 */
QWidget {
    background-color: #121316;
    color: #dedede;
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 13px;
    selection-background-color: #8c733e;
    selection-color: #ffffff;
}

/* 主窗口 */
QMainWindow {
    background-color: #0f1012;
}

/* 面板与卡片容器 */
QFrame.CardFrame {
    background-color: #1a1b20;
    border: 1px solid #363228;
    border-radius: 8px;
}

QFrame.CardFrame:hover {
    border: 1px solid #6b5731;
}

/* 顶部标题栏 */
QLabel.AppTitle {
    font-size: 19px;
    font-weight: bold;
    color: #e5c158;
    letter-spacing: 1px;
}

QLabel.Subtitle {
    font-size: 12px;
    color: #8a8d9b;
}

/* 按钮通用风格 */
QPushButton {
    background-color: #262730;
    color: #f0f0f0;
    border: 1px solid #4a4536;
    border-radius: 6px;
    padding: 7px 15px;
    font-weight: 500;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #353644;
    border: 1px solid #bfa15f;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #1e1f26;
    border: 1px solid #8c733e;
}

QPushButton:disabled {
    background-color: #16171b;
    color: #555863;
    border: 1px solid #22242a;
}

/* 金色高亮主按钮 (一键合成) */
QPushButton.PrimaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #a88434, stop:1 #6b4e18);
    color: #ffffff;
    border: 1px solid #d4af37;
    font-size: 14px;
    font-weight: bold;
    border-radius: 6px;
    padding: 9px 20px;
}

QPushButton.PrimaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #c49d42, stop:1 #876420);
    border: 1px solid #ffe082;
    box-shadow: 0 0 10px rgba(212, 175, 55, 0.5);
}

QPushButton.PrimaryBtn:pressed {
    background: #543d12;
}

/* 红色紧急停止按钮 */
QPushButton.DangerBtn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #96281b, stop:1 #69170e);
    color: #ffffff;
    border: 1px solid #e74c3c;
    font-size: 14px;
    font-weight: bold;
    border-radius: 6px;
    padding: 9px 20px;
}

QPushButton.DangerBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #b83424, stop:1 #801e13);
    border: 1px solid #ff7675;
}

QPushButton.DangerBtn:pressed {
    background: #4a100a;
}

/* 快速合成小按钮 */
QPushButton.QuickCraftBtn {
    background-color: #21222b;
    color: #e5c158;
    border: 1px solid #52472d;
    border-radius: 4px;
    padding: 4px 6px;
    font-size: 12px;
    font-weight: 500;
}

QPushButton.QuickCraftBtn:hover {
    background-color: #3d351e;
    border: 1px solid #d4af37;
    color: #ffffff;
}

/* 宝石卡片与独立数字栏 */
QFrame.GemCell {
    background-color: #16171c;
    border: 1px solid #282a30;
    border-radius: 6px;
}

QFrame.GemCell:hover {
    background-color: #20222a;
    border: 1px solid #bfa15f;
}

QLabel.GemCountBar {
    font-size: 12px;
    font-weight: bold;
    color: #dedede;
    background-color: #101114;
    border: 1px solid #282a30;
    border-radius: 3px;
    padding: 1px 0px;
}

/* 进度条 */
QProgressBar {
    background-color: #1a1b20;
    border: 1px solid #363228;
    border-radius: 5px;
    text-align: center;
    color: #ffffff;
    font-weight: bold;
    height: 18px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a88434, stop:1 #2ecc71);
    border-radius: 4px;
}

/* 日志文本框 */
QTextEdit.LogTerminal {
    background-color: #0b0c0e;
    color: #c8c8cf;
    border: 1px solid #2a2926;
    border-radius: 6px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
    padding: 8px;
}

/* 滚动条 */
QScrollBar:vertical {
    background: #121316;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #363842;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #bfa15f;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* 状态栏 */
QStatusBar {
    background-color: #0b0c0e;
    color: #8a8d9b;
    border-top: 1px solid #22242a;
}
"""
