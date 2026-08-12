# -*- coding: utf-8 -*-
"""
D2R 自动宝石合成工具 - 合成执行引擎与状态机 (纯净无 Emoji 专业日志版)
支持 99 颗上限自动级联合成、保留 20 颗底仓宝石 与 异常即刻绝对中止保护
"""

import time
import pyautogui
from PySide6.QtCore import QThread, Signal
from core.config import config, GEM_TYPES, GEM_TIERS
from core.screen_capture import screen_cap
from core.ocr_engine import ocr_engine
from core.hotkey_listener import hotkey_listener

# 禁用 PyAutoGUI 默认的极端慢速 pause
pyautogui.PAUSE = 0.02


class SynthesizerWorker(QThread):
    # 信号定义
    log_message = Signal(str, str)             # (消息内容, 级别: 'info'/'success'/'warning'/'error')
    progress_updated = Signal(int, int)        # (当前完成轮次, 总预计轮次)
    gem_matrix_updated = Signal(list)          # (更新后的 5x7 宝石数据)
    status_changed = Signal(str)               # (状态栏简报)
    finished_synthesis = Signal(bool, str)     # (是否成功, 总结消息)

    def __init__(self, mode: str = "all", target_col: int = None, current_matrix: list = None):
        """
        :param mode: "all" (全量一键合成) 或 "single" (单种宝石快速合成)
        :param target_col: 当 mode="single" 时指定的宝石列索引 (0~6)
        :param current_matrix: 当前 5x7 宝石数量矩阵
        """
        super().__init__()
        self.mode = mode
        self.target_col = target_col
        self.matrix = [row[:] for row in current_matrix] if current_matrix else [[0]*7 for _ in range(5)]
        self._stop_requested = False
        self._is_paused = False
        self.cube_gem = None # 跟踪魔盒内是否有残留宝石: {"col": int, "tier": int, "count": 1}

    def request_stop(self):
        """请求立即中止当前自动化操作"""
        self._stop_requested = True
        hotkey_listener.emergency_release_keys()

    def _safe_ctrl_shift_click(self, x: int, y: int, count: int = 1):
        """
        安全且可靠地向目标坐标发送 count 次 Ctrl + Shift + 左键点击
        确保修饰键有充足的物理按下延时，避免 D2R/DirectX 引擎误判为普通左键抓取物品
        """
        if self._stop_requested:
            return

        pyautogui.moveTo(x, y, duration=0.06)
        time.sleep(0.04)

        for _ in range(count):
            if self._stop_requested:
                break
            # 按下修饰键并等待游戏轮询捕获
            pyautogui.keyDown('ctrl')
            time.sleep(0.02)
            pyautogui.keyDown('shift')
            time.sleep(0.04)

            # 按下鼠标左键并保持 60ms，确保游戏完成物品转移
            pyautogui.mouseDown(button='left')
            time.sleep(0.06)
            pyautogui.mouseUp(button='left')
            time.sleep(0.04)

            # 释放修饰键
            pyautogui.keyUp('shift')
            time.sleep(0.02)
            pyautogui.keyUp('ctrl')
            time.sleep(config.click_delay)

    def _execute_single_craft(self, gem_col: int, from_tier: int, gems_already_in_cube: int = 0) -> tuple:
        """
        执行一轮单次合成操作
        :return: (status_code, message)
        """
        if self._stop_requested:
            return ("ERROR", "用户已请求中止")

        if from_tier >= 4:
            return ("STOP", "已达最高完美等级")

        gem_name = GEM_TYPES[gem_col]["name"]
        tier_name = GEM_TIERS[from_tier]["name"]
        next_tier_name = GEM_TIERS[from_tier + 1]["name"]

        # 计算本次需要从仓库转移到魔盒的宝石数量 (通常为 3 颗；若盒内已有 1 颗则只需 2 颗)
        needed = 3 - gems_already_in_cube
        threshold = 20 if config.keep_twenty else 0

        # 保留 20 颗底仓判断
        if config.keep_twenty:
            if self.matrix[from_tier][gem_col] - needed < threshold:
                self.log_message.emit(
                    f"[跳过] [{tier_name}{gem_name}] 现有 {self.matrix[from_tier][gem_col]} 颗 (合成后不足保留 20 颗)，跳至下一级",
                    "info"
                )
                return ("STOP", "达到保留20颗底线")
        else:
            if self.matrix[from_tier][gem_col] < needed:
                return ("STOP", "库存数量不足")

        gx, gy = config.get_gem_screen_pos(from_tier, gem_col)
        tx, ty = config.get_transmute_btn_screen_pos()

        if gems_already_in_cube > 0:
            self.log_message.emit(
                f"[级联合成] 魔盒已有 1 颗 [{tier_name}{gem_name}]，存入 {needed} 颗 -> [{next_tier_name}{gem_name}]",
                "info"
            )
        else:
            self.log_message.emit(f"[合成] [{tier_name}{gem_name}] × {needed} -> [{next_tier_name}{gem_name}]", "info")

        if config.dry_run:
            cx, cy = config.get_cube_slot_screen_pos(0, 0)
            self.log_message.emit(f"  [测试模式] 移动鼠标至 ({gx}, {gy})，模拟 {needed} 次 Ctrl+Shift+左键", "info")
            time.sleep(config.step_delay)
            self.log_message.emit(f"  [测试模式] 模拟魔盒核验 (3颗)... 通过", "success")
            time.sleep(config.step_delay)
            self.log_message.emit(f"  [测试模式] 移动至合成按钮 ({tx}, {ty}) 点击", "info")
            time.sleep(config.step_delay)
            self.log_message.emit(f"  [测试模式] 模拟产物核验 (1颗)... 通过", "success")
            time.sleep(config.step_delay)
            self.log_message.emit(f"  [测试模式] 移动至魔盒 ({cx}, {cy})，1 次 Ctrl+Shift+左键收回", "info")
            
            # 本地测试数据同步
            self.matrix[from_tier][gem_col] -= needed
            self.matrix[from_tier + 1][gem_col] += 1
            self.gem_matrix_updated.emit(self.matrix)
            return ("OK", "测试模式成功")

        # ---- Step 1 & 2: 鼠标移动至源宝石，存入 needed 颗 ----
        self._safe_ctrl_shift_click(gx, gy, count=needed)
        if self._stop_requested:
            return ("ERROR", "用户已请求中止")
        time.sleep(config.step_delay)

        # ---- Step 3: 视觉核验魔盒内是否有 3 颗宝石 ----
        if config.enable_verification:
            cube_crop = screen_cap.capture_cube_area()
            cube_count = ocr_engine.check_cube_gem_count(cube_crop)
            if cube_count < 3 and not self._stop_requested:
                time.sleep(0.15)
                cube_crop = screen_cap.capture_cube_area()
                cube_count = ocr_engine.check_cube_gem_count(cube_crop)

            if cube_count < 3 and not self._stop_requested:
                err = f"魔盒存入核验失败: 检测到 {cube_count} 颗宝石 (预期为 3 颗)，可能库存已不足或点击未响应！"
                self.log_message.emit(f"[核验警告] {err}", "error")
                return ("ERROR", err)
            else:
                self.log_message.emit("  [核验] 魔盒存入成功 (3颗)", "success")

        # ---- Step 4: 点击合成按钮 (Transmute) ----
        if self._stop_requested:
            return ("ERROR", "用户已请求中止")
        pyautogui.moveTo(tx, ty, duration=0.06)
        time.sleep(0.04)
        pyautogui.mouseDown(button='left')
        time.sleep(0.06)
        pyautogui.mouseUp(button='left')
        time.sleep(config.step_delay + 0.05)

        # ---- Step 5: 视觉核验是否已合成为 1 颗高级宝石 ----
        occupied_slots = [(0, 0)]
        if config.enable_verification:
            cube_crop = screen_cap.capture_cube_area()
            occupied_slots = ocr_engine.get_occupied_cube_slots(cube_crop)
            if len(occupied_slots) != 1 and not self._stop_requested:
                time.sleep(0.15)
                cube_crop = screen_cap.capture_cube_area()
                occupied_slots = ocr_engine.get_occupied_cube_slots(cube_crop)

            if len(occupied_slots) != 1 and not self._stop_requested:
                err = f"产物合成核验失败: 魔盒内有 {len(occupied_slots)} 个物品 (预期为 1 颗产物)！"
                self.log_message.emit(f"[核验警告] {err}", "error")
                return ("ERROR", err)
            else:
                self.log_message.emit(f"  [核验] 产物合成成功 (1颗 {next_tier_name}{gem_name})", "success")

        # ---- Step 6 & 7: 移动到魔盒内产物宝石所在格子，尝试收回仓库 ----
        if self._stop_requested:
            return ("ERROR", "用户已请求中止")

        target_slots = occupied_slots if occupied_slots else [(0, 0)]
        for (sr, sc) in target_slots:
            cx, cy = config.get_cube_slot_screen_pos(sr, sc)
            self._safe_ctrl_shift_click(cx, cy, count=1)
            time.sleep(config.step_delay)

        # 检查是否因为 99 满仓导致宝石滞留在魔盒
        time.sleep(0.10)
        cube_crop = screen_cap.capture_cube_area()
        is_empty = (ocr_engine.check_cube_gem_count(cube_crop) == 0)

        # 更新扣减
        self.matrix[from_tier][gem_col] -= needed

        if is_empty:
            # 正常收回成功
            self.matrix[from_tier + 1][gem_col] += 1
            self.gem_matrix_updated.emit(self.matrix)
            self.cube_gem = None
            self.log_message.emit(f"[产出] 成功产出: 1 × [{next_tier_name}{gem_name}] 并已存入仓库！", "success")
            return ("OK", "合成并存入成功")
        else:
            # 魔盒内仍有 1 颗产物 (说明上级宝石仓库已满 99 颗)
            self.matrix[from_tier + 1][gem_col] = 99 # 修正为上限
            self.gem_matrix_updated.emit(self.matrix)
            self.cube_gem = {"col": gem_col, "tier": from_tier + 1, "count": 1}

            if from_tier + 1 < 4:
                self.log_message.emit(
                    f"[满仓级联] 【{next_tier_name}{gem_name}】仓库已满(99颗)，魔盒内保留 1 颗，自动向上级联触发更高阶合成！",
                    "warning"
                )
                # 递归向上合成更高一级 (魔盒内已有 1 颗，只需存入 2 颗)
                cascade_status, cascade_msg = self._execute_single_craft(gem_col, from_tier + 1, gems_already_in_cube=1)
                return (cascade_status, cascade_msg)
            else:
                self.log_message.emit(f"[完成] 最高等级【完美{gem_name}】也已满仓，流程安全结束", "warning")
                return ("OK", "已达完美宝石上限")

    def run(self):
        """执行主工作线程"""
        self._stop_requested = False
        hotkey_listener.register_stop_callback(self.request_stop)

        # 1. 自动截屏更新当前最新的宝石数量
        self.status_changed.emit("正在扫描游戏材料页宝石数量...")
        self.log_message.emit("[扫描] 正在抓取屏幕材料页，更新当前宝石库存...", "info")

        try:
            gem_crop = screen_cap.capture_gem_grid()
            fresh_matrix = ocr_engine.recognize_all_gems(gem_crop)
            if fresh_matrix and sum(sum(r) for r in fresh_matrix) > 0:
                self.matrix = fresh_matrix
                self.gem_matrix_updated.emit(self.matrix)
                self.log_message.emit("[扫描] 宝石数量更新完成，准备开始合成...", "success")
            else:
                self.log_message.emit("[扫描] 未检测到材料页截屏变化，使用当前界面填入的宝石数量执行...", "info")
        except Exception as e:
            self.log_message.emit(f"[警告] 实时截屏识别失败，使用界面当前填入数量: {e}", "warning")

        # 检查初始魔盒内是否已有残留的 1 颗宝石
        initial_cube_gem_count = 0
        try:
            cube_crop = screen_cap.capture_cube_area()
            initial_cube_gem_count = ocr_engine.check_cube_gem_count(cube_crop)
            if initial_cube_gem_count == 1:
                self.log_message.emit("[状态] 检测到魔盒内已有 1 颗宝石，首轮将自动按 2 颗投入！", "info")
        except Exception:
            pass

        # 2. 规划合成队列
        cols_to_process = [self.target_col] if (self.mode == "single" and self.target_col is not None) else list(range(7))
        threshold = 20 if config.keep_twenty else 0

        # 估算总轮次
        sim_matrix = [row[:] for row in self.matrix]
        total_rounds = 0
        for col in cols_to_process:
            for tier in range(4): # 0:碎裂 -> 3:无瑕
                while sim_matrix[tier][col] - 3 >= threshold:
                    crafts = (sim_matrix[tier][col] - threshold) // 3
                    sim_matrix[tier][col] -= crafts * 3
                    sim_matrix[tier + 1][col] += crafts
                    total_rounds += crafts

        if total_rounds == 0 and initial_cube_gem_count == 0:
            if config.keep_twenty:
                self.log_message.emit("[提示] 当前所选宝石均已在 20 颗底仓范围内，无需合成！", "warning")
            else:
                self.log_message.emit("[提示] 当前所选宝石数量不足 3 颗，无可合成项！", "warning")
            self.status_changed.emit("就绪 (无可合成项)")
            self.finished_synthesis.emit(True, "无需合成")
            hotkey_listener.unregister_stop_callback(self.request_stop)
            return

        total_rounds = max(1, total_rounds)
        mode_str = "保留20颗宝石" if config.keep_twenty else "完全合成"
        self.log_message.emit(f"[计划] 开始执行合成任务 (预计 {total_rounds} 轮，模式: {mode_str})", "info")
        self.progress_updated.emit(0, total_rounds)

        # 3. 逐列自底向上级联合成
        completed_rounds = 0
        success = True
        abort_reason = ""

        for col in cols_to_process:
            if not success or self._stop_requested:
                break

            gem_name = GEM_TYPES[col]["name"]
            
            # 多轮迭代循环，直到该列所有阶均无法继续合成为止
            has_more = True
            while has_more and not self._stop_requested and success:
                has_more = False
                for tier in range(4):
                    if self._stop_requested or not success:
                        break

                    # 检查是否有预存在魔盒内的宝石
                    gems_in_cube = 1 if (self.cube_gem and self.cube_gem.get("col") == col and self.cube_gem.get("tier") == tier) else 0
                    if initial_cube_gem_count == 1 and completed_rounds == 0:
                        gems_in_cube = 1

                    needed = 3 - gems_in_cube
                    
                    # 检查当前阶是否满足合成条件 (若不满足，直接顺畅跳入下一个 tier)
                    while (self.matrix[tier][col] - needed >= threshold) and not self._stop_requested and success:
                        self.status_changed.emit(f"正在合成: {gem_name} ({GEM_TIERS[tier]['name']})")
                        
                        status_code, msg = self._execute_single_craft(col, tier, gems_already_in_cube=gems_in_cube)
                        gems_in_cube = 0 # 首次使用后重置
                        initial_cube_gem_count = 0
                        
                        if status_code == "STOP":
                            # 正常由于条件限制（如保留20颗或不足投入）而停止当前阶，顺畅进入下一阶
                            break
                        elif status_code == "ERROR":
                            # 属于核验失败、点击未响应等异常，必须立即全量中止！
                            success = False
                            abort_reason = msg
                            self.log_message.emit(f"[安全中止] 检测到合成异常: {msg}，流程已立即全面暂停！", "error")
                            break
                        elif status_code == "OK":
                            has_more = True
                            completed_rounds += 1
                            self.progress_updated.emit(min(completed_rounds, total_rounds), max(completed_rounds, total_rounds))
                            time.sleep(config.step_delay)

                if not success or self._stop_requested:
                    break

            if not success or self._stop_requested:
                break

        # 4. 结束处理
        hotkey_listener.unregister_stop_callback(self.request_stop)

        if self._stop_requested:
            self.status_changed.emit("已手动紧急停止")
            self.finished_synthesis.emit(False, f"用户中止 (已完成 {completed_rounds} 轮)")
        elif not success:
            self.status_changed.emit("合成核验异常已中止")
            self.finished_synthesis.emit(False, f"异常中止: {abort_reason}")
        else:
            self.status_changed.emit("全部合成完成！")
            self.log_message.emit(f"[完成] 所有合成任务已圆满完成 (共执行 {completed_rounds} 轮)！", "success")
            self.finished_synthesis.emit(True, f"合成完成 (共 {completed_rounds} 轮)")
