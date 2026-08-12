# -*- coding: utf-8 -*-
"""
D2R 自动宝石/符文合成工具 - 主界面窗口 (支持【宝石合成】与【符文合成】独立选项卡)
"""

import time
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QTextEdit,
    QFrame, QCheckBox, QStatusBar, QMessageBox, QTabWidget, QSizePolicy,
    QDialog, QComboBox, QDialogButtonBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QTextCursor

from core.config import config, GEM_TYPES, GEM_TIERS
from core.rune_config import RUNES_DATA, RUNES_BY_ID, get_rune_recipe_text
from core.screen_capture import screen_cap
from core.ocr_engine import ocr_engine
from core.synthesizer import SynthesizerWorker
from core.rune_synthesizer import RuneSynthesizerWorker
from core.hotkey_listener import hotkey_listener, AVAILABLE_HOTKEYS
from ui.gem_grid_widget import GemGridWidget
from ui.rune_grid_widget import RuneGridWidget


class HotkeySettingDialog(QDialog):
    """自定义全局紧急停止热键设置弹窗"""
    def __init__(self, current_key: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("自定义紧急停止热键")
        self.setFixedSize(360, 180)
        self.setStyleSheet(
            "QDialog { background-color: #1a1b1e; color: #dedede; } "
            "QLabel { color: #dedede; font-size: 13px; } "
            "QComboBox { background-color: #282a30; color: #f1c40f; border: 1px solid #7c6237; border-radius: 4px; padding: 6px 12px; font-weight: bold; font-size: 13px; } "
            "QComboBox::drop-down { border: none; } "
            "QComboBox QAbstractItemView { background-color: #222328; color: #dedede; selection-background-color: #7c6237; selection-color: #fff; } "
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2c2518, stop:1 #1a160e); border: 1px solid #7c6237; border-radius: 4px; color: #f1c40f; padding: 6px 16px; font-weight: bold; } "
            "QPushButton:hover { background: #3d3422; color: #fff; border-color: #f1c40f; }"
        )
        self.selected_key = current_key

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        tip_label = QLabel("请选择全局紧急停止热键 (物理原生无冲突监听):")
        layout.addWidget(tip_label)

        self.combo = QComboBox()
        for key_name, (vk, display_name) in AVAILABLE_HOTKEYS.items():
            self.combo.addItem(f"{key_name}  ({display_name})", key_name)

        # 选中当前热键
        idx = self.combo.findData(current_key)
        if idx >= 0:
            self.combo.setCurrentIndex(idx)
        layout.addWidget(self.combo)

        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_ok = QPushButton("保存生效")
        btn_ok.clicked.connect(self._on_confirm)
        btn_box.addWidget(btn_ok)

        layout.addLayout(btn_box)

    def _on_confirm(self):
        self.selected_key = self.combo.currentData()
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("暗黑破坏神2:重制版 - 自动宝石/符文合成工具 v1.2.0")
        self.setMinimumSize(1100, 830)
        self.resize(1120, 840)
        self.worker = None
        
        self.init_ui()
        self.init_hotkeys()

        # 启动后添加欢迎日志
        self.add_log("[系统] 欢迎使用《暗黑2:重制版》自动宝石与符文合成工具 v1.2.0！", "success")
        hotkey_name = self._get_hotkey_display_name()
        self.add_log(f"[提示] 快捷操作: 按下 [{hotkey_name}] 可在任何合成中随时无条件紧急停止！", "info")
        self.add_log("[就绪] 支持【宝石合成】与【符文合成】独立面板，点击下方选项卡自由切换。", "info")

    def _get_hotkey_display_name(self) -> str:
        key = getattr(config, 'hotkey_stop', 'Num 1')
        if key in AVAILABLE_HOTKEYS:
            return AVAILABLE_HOTKEYS[key][1]
        return key

    def _get_hotkey_short_name(self) -> str:
        return getattr(config, 'hotkey_stop', 'Num 1')

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # 1. 顶部标题栏与全局热键自定义按钮
        header_layout = QHBoxLayout()
        
        title_box = QVBoxLayout()
        title_label = QLabel("暗黑破坏神 II: 重制版 自动合成系统 v1.2.0")
        title_label.setProperty("class", "AppTitle")
        title_box.addWidget(title_label)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # 可点击自定义的紧急停止热键徽标按钮
        self.btn_hotkey_setting = QPushButton(f"紧急停止热键: [{self._get_hotkey_display_name()}]  (点击设置)")
        self.btn_hotkey_setting.setCursor(Qt.PointingHandCursor)
        self.btn_hotkey_setting.setToolTip("点击自定义或更换全局紧急停止热键")
        self.btn_hotkey_setting.setStyleSheet(
            "QPushButton { background-color: #2b1716; color: #ff7675; border: 1px solid #882b26; "
            "border-radius: 6px; padding: 7px 16px; font-weight: bold; font-size: 13px; } "
            "QPushButton:hover { background-color: #4a1f1d; border-color: #ff5252; color: #ffffff; } "
            "QPushButton:pressed { background-color: #1a0f0e; }"
        )
        self.btn_hotkey_setting.clicked.connect(self.on_change_hotkey_clicked)
        header_layout.addWidget(self.btn_hotkey_setting)

        main_layout.addLayout(header_layout)

        # 2. 全局通用设置栏 (魔盒核验 / 紧急停止)
        global_bar = QFrame()
        global_bar.setProperty("class", "CardFrame")
        global_layout = QHBoxLayout(global_bar)
        global_layout.setContentsMargins(12, 8, 12, 8)
        global_layout.setSpacing(12)

        # 【紧急停止】
        self.btn_stop = QPushButton(f"紧急停止 ({self._get_hotkey_short_name()})")
        self.btn_stop.setProperty("class", "DangerBtn")
        self.btn_stop.setToolTip("立即中断所有自动化动作并释放鼠标按键")
        self.btn_stop.clicked.connect(self.on_emergency_stop)
        self.btn_stop.setEnabled(False)
        global_layout.addWidget(self.btn_stop)

        # 【魔盒核验】
        self.chk_verify = QCheckBox("魔盒核验")
        self.chk_verify.setChecked(config.enable_verification)
        self.chk_verify.setToolTip("在投入与产出时视觉校验魔盒，保障绝对安全")
        self.chk_verify.toggled.connect(self._on_verify_toggled)
        global_layout.addWidget(self.chk_verify)

        global_layout.addStretch()

        # 状态指示
        self.status_indicator = QLabel("就绪")
        self.status_indicator.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 14px;")
        global_layout.addWidget(self.status_indicator)

        main_layout.addWidget(global_bar)

        # 3. 中间主体区 (左侧 Tab选项卡：宝石合成 / 符文合成，右侧 实时日志与进度)
        body_layout = QHBoxLayout()
        body_layout.setSpacing(12)

        # 左侧：Tab 选项卡容器
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(
            "QTabWidget::pane { border: 1px solid #332d20; background-color: #141416; border-radius: 6px; } "
            "QTabBar::tab { background: #1a1b1e; color: #a0a0aa; font-weight: bold; font-size: 13px; "
            "padding: 8px 20px; border: 1px solid #282a30; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 4px; } "
            "QTabBar::tab:selected { background: #252219; color: #e5c158; border-color: #7c6237; } "
            "QTabBar::tab:hover { color: #f1c40f; }"
        )

        # --- Tab 1: 宝石合成面板 ---
        gem_tab = QWidget()
        gem_tab_layout = QVBoxLayout(gem_tab)
        gem_tab_layout.setContentsMargins(10, 10, 10, 10)
        gem_tab_layout.setSpacing(10)

        gem_action_bar = QHBoxLayout()
        self.btn_read_gems = QPushButton("读取宝石数量")
        self.btn_read_gems.setToolTip("从游戏画面中抓取材料页，更新 5x7 宝石当前数量")
        self.btn_read_gems.clicked.connect(self.on_read_gems_clicked)
        gem_action_bar.addWidget(self.btn_read_gems)

        self.btn_start_all_gems = QPushButton("一键合成全部宝石")
        self.btn_start_all_gems.setProperty("class", "PrimaryBtn")
        self.btn_start_all_gems.setToolTip("全自动将所有可合成的宝石从碎裂层层升至完美！(满99自动向上级联)")
        self.btn_start_all_gems.clicked.connect(self.on_start_all_synthesis)
        gem_action_bar.addWidget(self.btn_start_all_gems)

        self.chk_keep_twenty = QCheckBox("保留 20 颗宝石")
        self.chk_keep_twenty.setChecked(config.keep_twenty)
        self.chk_keep_twenty.setToolTip("勾选后，当前宝石数量少于或等于 20 颗时，会自动跳过该阶并合成下一级宝石")
        self.chk_keep_twenty.toggled.connect(self._on_keep_twenty_toggled)
        gem_action_bar.addWidget(self.chk_keep_twenty)

        gem_action_bar.addStretch()
        gem_tab_layout.addLayout(gem_action_bar)

        self.gem_grid = GemGridWidget()
        self.gem_grid.quick_craft_requested.connect(self.on_quick_synthesis)
        gem_tab_layout.addWidget(self.gem_grid)
        gem_tab_layout.addStretch()

        self.tab_widget.addTab(gem_tab, "宝石合成 (5x7)")

        # --- Tab 2: 符文合成面板 ---
        rune_tab = QWidget()
        rune_tab_layout = QVBoxLayout(rune_tab)
        rune_tab_layout.setContentsMargins(10, 10, 10, 10)
        rune_tab_layout.setSpacing(8)

        rune_action_bar = QHBoxLayout()
        self.btn_read_runes = QPushButton("读取符文数量")
        self.btn_read_runes.setToolTip("从游戏画面中抓取材料页，更新 33 种符文当前数量")
        self.btn_read_runes.clicked.connect(self.on_read_runes_clicked)
        rune_action_bar.addWidget(self.btn_read_runes)

        rune_info_label = QLabel("符文合成系统 (点击各符文下方【合成10个】按钮，自动放入符文及对应所需宝石)")
        rune_info_label.setStyleSheet("color: #e5c158; font-size: 12px; font-weight: bold; margin-left: 10px;")
        rune_action_bar.addWidget(rune_info_label)
        rune_action_bar.addStretch()

        rune_tab_layout.addLayout(rune_action_bar)

        self.rune_grid = RuneGridWidget()
        self.rune_grid.craft10_requested.connect(self.on_craft_rune_10_requested)
        rune_tab_layout.addWidget(self.rune_grid)
        rune_tab_layout.addStretch()

        self.tab_widget.addTab(rune_tab, "符文合成 (1#~33#)")

        body_layout.addWidget(self.tab_widget, stretch=6)

        # 右侧：状态面板与实时日志
        right_panel = QFrame()
        right_panel.setProperty("class", "CardFrame")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)

        log_top_box = QHBoxLayout()
        log_label = QLabel("实时执行控制台:")
        log_label.setStyleSheet("color: #a0a0aa; font-size: 12px; font-weight: bold;")
        log_top_box.addWidget(log_label)

        log_top_box.addStretch()

        self.btn_clear_log = QPushButton("清空日志")
        self.btn_clear_log.setStyleSheet("padding: 3px 8px; font-size: 11px;")
        self.btn_clear_log.clicked.connect(self.clear_log)
        log_top_box.addWidget(self.btn_clear_log)
        right_layout.addLayout(log_top_box)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("进度: 0 / 0")
        right_layout.addWidget(self.progress_bar)

        # 日志文本终端
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
        """初始化全局热键监听"""
        hotkey_listener.bridge.hotkey_pressed.connect(self.on_emergency_stop, Qt.QueuedConnection)
        hotkey_listener.set_hotkey(config.hotkey_stop)
        hotkey_listener.start()

    def on_change_hotkey_clicked(self):
        """弹出自定义热键对话框"""
        dlg = HotkeySettingDialog(config.hotkey_stop, self)
        if dlg.exec():
            new_key = dlg.selected_key
            config.hotkey_stop = new_key
            config.save()
            hotkey_listener.set_hotkey(new_key)

            display_name = self._get_hotkey_display_name()
            short_name = self._get_hotkey_short_name()
            self.btn_hotkey_setting.setText(f"紧急停止热键: [{display_name}]  (点击设置)")
            self.btn_stop.setText(f"紧急停止 ({short_name})")
            self.add_log(f"[配置] 全局紧急停止热键已修改为: [{display_name}]", "success")

    def add_log(self, text: str, level: str = "info"):
        """向日志终端追加带色彩的时间戳消息"""
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

    # ---- 宝石合成调度 ----
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
        """启动一键全量宝石合成"""
        self._start_gem_worker(mode="all")

    def on_quick_synthesis(self, col: int):
        """单种宝石快速合成"""
        gem_name = GEM_TYPES[col]["name"]
        self.add_log(f"[指令] 请求快速合成【{gem_name}】...", "info")
        self._start_gem_worker(mode="single", target_col=col)

    def _start_gem_worker(self, mode: str = "all", target_col: int = None):
        """启动宝石合成工作线程"""
        if self.worker and self.worker.isRunning():
            return

        self._set_ui_busy(True)
        current_matrix = self.gem_grid.get_matrix()
        self.worker = SynthesizerWorker(mode=mode, target_col=target_col, current_matrix=current_matrix)
        
        self.worker.log_message.connect(self.add_log)
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.gem_matrix_updated.connect(self.gem_grid.set_matrix)
        self.worker.status_changed.connect(self.status_bar.showMessage)
        self.worker.finished_synthesis.connect(self._on_synthesis_finished)
        self.worker.start()

    # ---- 符文合成调度 ----
    def on_read_runes_clicked(self):
        """点击读取符文数量"""
        self.add_log("[OCR] 正在抓取屏幕材料页 33 种符文数量...", "info")
        self.status_bar.showMessage("正在抓取材料页符文库存...")

        try:
            rune_crop = screen_cap.capture_rune_grid()
            counts = ocr_engine.recognize_all_runes(rune_crop)
            if counts and sum(counts.values()) > 0:
                self.rune_grid.set_counts(counts)
                total_count = sum(counts.values())
                self.add_log(f"[OCR] 符文识别成功！当前已记录 33 种符文共 {total_count} 颗", "success")
                self.status_bar.showMessage(f"读取完成 · 共检测到 {total_count} 颗符文")
            else:
                self.add_log("[警告] 截屏未能识别到符文，请确认已在游戏中打开大箱子【材料】页！", "warning")
        except Exception as e:
            self.add_log(f"[错误] 符文识别过程出错: {e}", "error")

    def on_craft_rune_10_requested(self, rune_id: int):
        """用户点击某符文卡片上的【合成10个】"""
        if self.worker and self.worker.isRunning():
            return

        rune_info = RUNES_BY_ID.get(rune_id)
        if not rune_info:
            return

        recipe_desc = get_rune_recipe_text(rune_id)
        self.add_log(f"[指令] 请求合成【{rune_id}# {rune_info['name_zh']}】10次 (配方: {recipe_desc})", "info")

        self._set_ui_busy(True)
        current_runes = self.rune_grid.get_counts()
        current_gems = self.gem_grid.get_matrix()

        self.worker = RuneSynthesizerWorker(
            target_rune_id=rune_id,
            current_runes=current_runes,
            current_gems=current_gems,
            repeat_count=10
        )

        self.worker.log_message.connect(self.add_log)
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.runes_updated.connect(self.rune_grid.set_counts)
        self.worker.gem_matrix_updated.connect(self.gem_grid.set_matrix)
        self.worker.status_changed.connect(self.status_bar.showMessage)
        self.worker.finished_synthesis.connect(self._on_synthesis_finished)
        self.worker.start()

    def _set_ui_busy(self, busy: bool):
        self.btn_read_gems.setEnabled(not busy)
        self.btn_start_all_gems.setEnabled(not busy)
        if hasattr(self, 'btn_read_runes'):
            self.btn_read_runes.setEnabled(not busy)
        self.btn_stop.setEnabled(busy)
        if busy:
            self.status_indicator.setText("正在合成中...")
            self.status_indicator.setStyleSheet("color: #f1c40f; font-weight: bold; font-size: 14px;")

    def _on_progress_updated(self, cur, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(cur)
        self.progress_bar.setFormat(f"合成进度: {cur} / {total}")

    def _on_synthesis_finished(self, success, message):
        self._set_ui_busy(False)
        if success:
            self.status_indicator.setText("已就绪")
            self.status_indicator.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 14px;")
        else:
            self.status_indicator.setText("已停止")
            self.status_indicator.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 14px;")

    def on_emergency_stop(self):
        """紧急停止触发"""
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
