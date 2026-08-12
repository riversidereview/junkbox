# -*- coding: utf-8 -*-
"""
D2R 自动宝石合成工具 - 主界面窗口 (纯净无 Emoji 专业暗黑风)
"""

import time
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QTextEdit,
    QFrame, QCheckBox, QStatusBar, QMessageBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QTextCursor

from core.config import config, GEM_TYPES, GEM_TIERS
from core.screen_capture import screen_cap
from core.ocr_engine import ocr_engine
from core.synthesizer import SynthesizerWorker
from core.hotkey_listener import hotkey_listener
from ui.gem_grid_widget import GemGridWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("暗黑破坏神2:重制版 - 自动宝石合成工具 (大箱子MOD材料页)")
        self.setMinimumSize(980, 680)
        self.worker = None
        
        self.init_ui()
        self.init_hotkeys()

        # 启动后添加欢迎日志 (无 Emoji)
        self.add_log("[系统] 欢迎使用《暗黑2:重制版》自动宝石合成工具！", "success")
        self.add_log("[提示] 快捷操作: 按下 [小键盘 1] (Num 1) 可在合成中随时无条件紧急停止！", "info")
        self.add_log("[就绪] 请在游戏中打开大箱子的【材料】页，点击【读取宝石数量】进行首次识别测试。", "info")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 1. 顶部标题栏与状态指示
        header_layout = QHBoxLayout()
        
        title_box = QVBoxLayout()
        title_label = QLabel("暗黑破坏神 II: 重制版 自动宝石合成")
        title_label.setProperty("class", "AppTitle")
        subtitle_label = QLabel("专为大箱子材料页 (Material Tab) MOD 打造 · 1920×1080 目标分辨率")
        subtitle_label.setProperty("class", "Subtitle")
        title_box.addWidget(title_label)
        title_box.addWidget(subtitle_label)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # 热键提示徽标
        hotkey_badge = QLabel("紧急停止热键: [小键盘 1]")
        hotkey_badge.setStyleSheet(
            "background-color: #2b1716; color: #ff7675; border: 1px solid #772621; "
            "border-radius: 6px; padding: 6px 12px; font-weight: bold; font-size: 13px;"
        )
        header_layout.addWidget(hotkey_badge)

        main_layout.addLayout(header_layout)

        # 2. 核心操作控制条 (已移除全部 Emoji)
        action_bar = QFrame()
        action_bar.setProperty("class", "CardFrame")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(12, 10, 12, 10)
        action_layout.setSpacing(10)

        # 【读取宝石数量】
        self.btn_read = QPushButton("读取宝石数量")
        self.btn_read.setToolTip("从游戏画面中抓取材料页，更新 5x7 宝石当前数量")
        self.btn_read.clicked.connect(self.on_read_gems_clicked)
        action_layout.addWidget(self.btn_read)

        # 【一键合成全部】
        self.btn_start_all = QPushButton("一键合成全部")
        self.btn_start_all.setProperty("class", "PrimaryBtn")
        self.btn_start_all.setToolTip("全自动将所有可合成的宝石从碎裂层层升至完美！(满99自动向上级联)")
        self.btn_start_all.clicked.connect(self.on_start_all_synthesis)
        action_layout.addWidget(self.btn_start_all)

        # 【紧急停止】
        self.btn_stop = QPushButton("紧急停止 (Num 1)")
        self.btn_stop.setProperty("class", "DangerBtn")
        self.btn_stop.setToolTip("立即中断所有自动化动作并释放鼠标按键")
        self.btn_stop.clicked.connect(self.on_emergency_stop)
        self.btn_stop.setEnabled(False)
        action_layout.addWidget(self.btn_stop)

        action_layout.addStretch()

        # 【保留 20 颗宝石】
        self.chk_keep_twenty = QCheckBox("保留 20 颗宝石")
        self.chk_keep_twenty.setChecked(config.keep_twenty)
        self.chk_keep_twenty.setToolTip("勾选后，当前宝石数量少于或等于 20 颗时，会自动跳过该阶并合成下一级宝石")
        self.chk_keep_twenty.toggled.connect(self._on_keep_twenty_toggled)
        action_layout.addWidget(self.chk_keep_twenty)

        # 选项勾选
        self.chk_verify = QCheckBox("魔盒核验")
        self.chk_verify.setChecked(config.enable_verification)
        self.chk_verify.setToolTip("在投入3颗与产出1颗时视觉校验魔盒，保障绝对安全")
        self.chk_verify.toggled.connect(self._on_verify_toggled)
        action_layout.addWidget(self.chk_verify)

        self.chk_dry_run = QCheckBox("模拟测试")
        self.chk_dry_run.setChecked(config.dry_run)
        self.chk_dry_run.setToolTip("测试模式下只在日志中打印动作流程，不真正控制鼠标点击")
        self.chk_dry_run.toggled.connect(self._on_dry_run_toggled)
        action_layout.addWidget(self.chk_dry_run)

        main_layout.addWidget(action_bar)

        # 3. 中间主体区 (左侧 5x7 宝石矩阵卡片，右侧 实时日志与状态)
        body_layout = QHBoxLayout()
        body_layout.setSpacing(12)

        # 左侧：宝石矩阵卡片
        left_panel = QFrame()
        left_panel.setProperty("class", "CardFrame")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        grid_title = QLabel("材料页宝石库存矩阵 (双击数字可手动编辑测试)")
        grid_title.setStyleSheet("font-weight: bold; color: #e5c158; font-size: 13px;")
        left_layout.addWidget(grid_title)

        self.gem_grid = GemGridWidget()
        self.gem_grid.quick_craft_requested.connect(self.on_quick_synthesis)
        left_layout.addWidget(self.gem_grid)
        left_layout.addStretch()

        body_layout.addWidget(left_panel, stretch=6)

        # 右侧：状态面板与实时日志
        right_panel = QFrame()
        right_panel.setProperty("class", "CardFrame")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)

        # 状态指示卡片
        status_box = QHBoxLayout()
        self.status_indicator = QLabel("就绪")
        self.status_indicator.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 14px;")
        status_box.addWidget(self.status_indicator)

        status_box.addStretch()

        self.btn_clear_log = QPushButton("清空日志")
        self.btn_clear_log.setStyleSheet("padding: 3px 8px; font-size: 11px;")
        self.btn_clear_log.clicked.connect(self.clear_log)
        status_box.addWidget(self.btn_clear_log)
        right_layout.addLayout(status_box)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("合成进度: 0 / 0")
        right_layout.addWidget(self.progress_bar)

        # 日志文本终端
        log_label = QLabel("实时执行控制台:")
        log_label.setStyleSheet("color: #a0a0aa; font-size: 12px; font-weight: bold;")
        right_layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setProperty("class", "LogTerminal")
        self.log_text.setReadOnly(True)
        right_layout.addWidget(self.log_text)

        body_layout.addWidget(right_panel, stretch=4)

        main_layout.addLayout(body_layout)

        # 4. 底部状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 · 等待用户指令")

    def init_hotkeys(self):
        """初始化全局热键监听 (通过 Qt.QueuedConnection 确保主线程安全)"""
        hotkey_listener.bridge.hotkey_pressed.connect(self.on_emergency_stop, Qt.QueuedConnection)
        hotkey_listener.start()

    def add_log(self, text: str, level: str = "info"):
        """向日志终端追加带色彩的时间戳消息 (主线程安全执行)"""
        now = datetime.now().strftime("%H:%M:%S")
        color_map = {
            "info": "#74b9ff",
            "success": "#55efc4",
            "warning": "#ffeaa7",
            "error": "#ff7675"
        }
        color = color_map.get(level, "#ffffff")
        html_line = f"<span style='color:#636e72;'>[{now}]</span> <span style='color:{color};'>{text}</span><br>"
        
        self.log_text.moveCursor(QTextCursor.End)
        self.log_text.insertHtml(html_line)
        self.log_text.moveCursor(QTextCursor.End)

    def clear_log(self):
        self.log_text.clear()

    def _on_keep_twenty_toggled(self, checked):
        config.keep_twenty = checked
        config.save()
        self.add_log(f"[配置] 保留 20 颗宝石选项已 {'开启 (少于等于20颗跳过)' if checked else '关闭 (完全合成)'}", "info")

    def _on_verify_toggled(self, checked):
        config.enable_verification = checked
        config.save()
        self.add_log(f"[配置] 魔盒视觉核验已 {'启用' if checked else '禁用'}", "info")

    def _on_dry_run_toggled(self, checked):
        config.dry_run = checked
        self.add_log(f"[配置] 模拟测试模式已 {'开启 (不控制鼠标)' if checked else '关闭 (实机控制)'}", "warning" if checked else "info")

    def on_read_gems_clicked(self):
        """点击读取宝石数量"""
        self.add_log("[OCR] 正在抓取屏幕材料页宝石数量...", "info")
        self.status_bar.showMessage("正在抓取屏幕材料页...")
        
        try:
            gem_crop = screen_cap.capture_gem_grid()
            matrix = ocr_engine.recognize_all_gems(gem_crop)
            if matrix and sum(sum(r) for r in matrix) > 0:
                self.gem_grid.set_matrix(matrix)
                total_count = sum(sum(row) for row in matrix)
                self.add_log(f"[OCR] 宝石识别成功！当前已记录 35 格共 {total_count} 颗宝石", "success")
                self.status_bar.showMessage(f"读取完成 · 共检测到 {total_count} 颗宝石")
            else:
                self.add_log("[警告] 截屏未能识别到宝石，请确认已在游戏中打开大箱子【材料】页！", "warning")
        except Exception as e:
            self.add_log(f"[错误] 识别过程出错: {e}", "error")

    def on_start_all_synthesis(self):
        """启动一键全量合成"""
        self._start_worker(mode="all")

    def on_quick_synthesis(self, col: int):
        """单种宝石快速合成"""
        gem_name = GEM_TYPES[col]["name"]
        self.add_log(f"[指令] 请求快速合成【{gem_name}】...", "info")
        self._start_worker(mode="single", target_col=col)

    def _start_worker(self, mode: str = "all", target_col: int = None):
        """启动后台合成工作线程"""
        if self.worker and self.worker.isRunning():
            return

        self.btn_read.setEnabled(False)
        self.btn_start_all.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.status_indicator.setText("正在合成中...")
        self.status_indicator.setStyleSheet("color: #f1c40f; font-weight: bold; font-size: 14px;")

        current_matrix = self.gem_grid.get_matrix()
        self.worker = SynthesizerWorker(mode=mode, target_col=target_col, current_matrix=current_matrix)
        
        self.worker.log_message.connect(self.add_log)
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.gem_matrix_updated.connect(self.gem_grid.set_matrix)
        self.worker.status_changed.connect(self.status_bar.showMessage)
        self.worker.finished_synthesis.connect(self._on_synthesis_finished)
        
        self.worker.start()

    def _on_progress_updated(self, cur, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(cur)
        self.progress_bar.setFormat(f"合成进度: {cur} / {total} 轮")

    def _on_synthesis_finished(self, success, message):
        self.btn_read.setEnabled(True)
        self.btn_start_all.setEnabled(True)
        self.btn_stop.setEnabled(False)
        
        if success:
            self.status_indicator.setText("已就绪")
            self.status_indicator.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 14px;")
        else:
            self.status_indicator.setText("已停止")
            self.status_indicator.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 14px;")

    def on_emergency_stop(self):
        """紧急停止触发 (仅在合成正在运行时响应与打印日志)"""
        hotkey_listener.emergency_release_keys()
        if self.worker and self.worker.isRunning():
            self.worker.request_stop()
            self.add_log("[中止] 已触发紧急停止，合成已即刻中断！", "error")

    def closeEvent(self, event):
        """退出程序时注销全局钩子"""
        if self.worker and self.worker.isRunning():
            self.worker.request_stop()
            self.worker.wait(1000)
        hotkey_listener.stop()
        event.accept()
