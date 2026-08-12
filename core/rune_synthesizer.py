# -*- coding: utf-8 -*-
"""
D2R 自动宝石/符文合成工具 - 符文合成执行引擎 (RuneSynthesizerWorker)
支持 33 种符文专属【合成10个】功能、附加宝石自动投放、魔盒转化与即刻安全熔断
"""

import time
import pyautogui
from PySide6.QtCore import QThread, Signal
from core.config import config, GEM_TYPES, GEM_TIERS
from core.rune_config import RUNES_DATA, RUNES_BY_ID, get_rune_recipe_text
from core.screen_capture import screen_cap
from core.ocr_engine import ocr_engine
from core.hotkey_listener import hotkey_listener

# 禁用 PyAutoGUI 默认的极端慢速 pause
pyautogui.PAUSE = 0.02


class RuneSynthesizerWorker(QThread):
    # 信号定义
    log_message = Signal(str, str)             # (消息内容, 级别: 'info'/'success'/'warning'/'error')
    progress_updated = Signal(int, int)        # (当前完成轮次, 总预计轮次 10)
    runes_updated = Signal(object)             # (更新后的 33 种符文数量字典 {rune_id: count})
    gem_matrix_updated = Signal(list)          # (若消耗宝石，更新 5x7 宝石数据)
    status_changed = Signal(str)               # (状态栏简报)
    finished_synthesis = Signal(bool, str)     # (是否成功, 总结消息)

    def __init__(self, target_rune_id: int, current_runes: dict = None, current_gems: list = None, repeat_count: int = 10):
        """
        :param target_rune_id: 要合成的目标符文编号 (1 ~ 32)
        :param current_runes: 当前 33 种符文数量字典 {1: count, 2: count, ...}
        :param current_gems: 当前 5x7 宝石数量矩阵
        :param repeat_count: 重复合成次数 (默认 10 次)
        """
        super().__init__()
        self.target_rune_id = target_rune_id
        self.repeat_count = repeat_count
        self.runes_map = dict(current_runes) if current_runes else {r["id"]: 0 for r in RUNES_DATA}
        self.gem_matrix = [row[:] for row in current_gems] if current_gems else [[0]*7 for _ in range(5)]
        self._stop_requested = False

    def request_stop(self):
        """请求立即中止当前自动化操作"""
        self._stop_requested = True
        hotkey_listener.emergency_release_keys()

    def _safe_ctrl_shift_click(self, x: int, y: int, count: int = 1):
        """安全且可靠地向目标坐标发送 count 次 Ctrl + Shift + 左键点击"""
        if self._stop_requested:
            return

        pyautogui.moveTo(x, y, duration=0.06)
        time.sleep(0.04)

        for _ in range(count):
            if self._stop_requested:
                break
            pyautogui.keyDown('ctrl')
            time.sleep(0.02)
            pyautogui.keyDown('shift')
            time.sleep(0.04)

            pyautogui.mouseDown(button='left')
            time.sleep(0.06)
            pyautogui.mouseUp(button='left')
            time.sleep(0.04)

            pyautogui.keyUp('shift')
            time.sleep(0.02)
            pyautogui.keyUp('ctrl')
            time.sleep(config.click_delay)

    def _get_gem_col_row(self, gem_id: str, tier_id: str) -> tuple:
        """根据 gem_id ('topaz') 和 tier_id ('chipped') 查找 5x7 矩阵的 (row, col)"""
        col_idx = 0
        for idx, g in enumerate(GEM_TYPES):
            if g["id"] == gem_id:
                col_idx = idx
                break
        row_idx = 0
        for idx, t in enumerate(GEM_TIERS):
            if t["id"] == tier_id:
                row_idx = idx
                break
        return row_idx, col_idx

    def _execute_single_rune_craft(self, rune_id: int) -> tuple:
        """
        执行一轮单次符文合成操作
        :return: (status_code, message)
        """
        if self._stop_requested:
            return ("ERROR", "用户已请求中止")

        if rune_id >= 33:
            return ("STOP", "已达最高级符文 33# 萨德")

        rune_info = RUNES_BY_ID.get(rune_id)
        next_rune = RUNES_BY_ID.get(rune_id + 1)
        req_runes = rune_info["req_runes"]
        req_gem = rune_info.get("req_gem")

        # 1. 检查符文材料是否充足
        curr_rune_count = self.runes_map.get(rune_id, 0)
        if curr_rune_count < req_runes:
            msg = f"符文材料不足: 当前 [{rune_id}# {rune_info['name_zh']}] 仅有 {curr_rune_count} 颗 (需要 {req_runes} 颗)"
            self.log_message.emit(f"[材料提示] {msg}", "warning")
            return ("STOP", msg)

        # 2. 检查所需附加宝石材料是否充足
        gem_row, gem_col = (0, 0)
        if req_gem is not None:
            gem_id, tier_id = req_gem
            gem_row, gem_col = self._get_gem_col_row(gem_id, tier_id)
            gem_avail = self.gem_matrix[gem_row][gem_col]
            if gem_avail < 1:
                msg = f"宝石材料不足: 合成需要 1 × 【{rune_info.get('gem_name')}】，当前库存为 0"
                self.log_message.emit(f"[材料提示] {msg}", "warning")
                return ("STOP", msg)

        rx, ry = config.get_rune_screen_pos(rune_info["row"], rune_info["col"])
        tx, ty = config.get_transmute_btn_screen_pos()
        recipe_desc = get_rune_recipe_text(rune_id)

        self.log_message.emit(f"[合成开始] {recipe_desc}", "info")

        if config.dry_run:
            self.log_message.emit(f"  [测试模式] 模拟放入符文与宝石并点击合成...", "info")
            time.sleep(config.step_delay * 2)
            self.runes_map[rune_id] -= req_runes
            self.runes_map[rune_id + 1] = self.runes_map.get(rune_id + 1, 0) + 1
            if req_gem is not None:
                self.gem_matrix[gem_row][gem_col] -= 1
                self.gem_matrix_updated.emit(self.gem_matrix)
            self.runes_updated.emit(self.runes_map)
            return ("OK", "测试模式合成成功")

        # ---- Step 1: 若需要宝石，先将 1 颗宝石存入魔盒 ----
        if req_gem is not None:
            gx, gy = config.get_gem_screen_pos(gem_row, gem_col)
            self.log_message.emit(f"  [置入] 存入 1 × 【{rune_info.get('gem_name')}】至魔盒", "info")
            self._safe_ctrl_shift_click(gx, gy, count=1)
            if self._stop_requested:
                return ("ERROR", "用户已请求中止")
            time.sleep(config.step_delay)

        # ---- Step 2: 存入 req_runes 颗符文至魔盒 ----
        self.log_message.emit(f"  [置入] 存入 {req_runes} × [{rune_id}# {rune_info['name_zh']}] 至魔盒", "info")
        self._safe_ctrl_shift_click(rx, ry, count=req_runes)
        if self._stop_requested:
            return ("ERROR", "用户已请求中止")
        time.sleep(config.step_delay)

        # ---- Step 3: 点击合成按钮 (Transmute) ----
        pyautogui.moveTo(tx, ty, duration=0.06)
        time.sleep(0.04)
        pyautogui.mouseDown(button='left')
        time.sleep(0.06)
        pyautogui.mouseUp(button='left')
        time.sleep(config.step_delay + 0.05)

        # ---- Step 4: 视觉核验产物并收回仓库 ----
        occupied_slots = [(0, 0)]
        if config.enable_verification:
            cube_crop = screen_cap.capture_cube_area()
            occupied_slots = ocr_engine.get_occupied_cube_slots(cube_crop)
            if len(occupied_slots) != 1 and not self._stop_requested:
                time.sleep(0.15)
                cube_crop = screen_cap.capture_cube_area()
                occupied_slots = ocr_engine.get_occupied_cube_slots(cube_crop)

            if len(occupied_slots) != 1 and not self._stop_requested:
                err = f"魔盒产物核验失败: 预期产物为 1 个，实际魔盒内有 {len(occupied_slots)} 个物品 (可能公式不匹配或点击未响应)！"
                self.log_message.emit(f"[核验警告] {err}", "error")
                return ("ERROR", err)

        # ---- Step 5: 移动到魔盒产物槽位，按 1 次 Ctrl+Shift+左键 收回材料仓 ----
        target_slots = occupied_slots if occupied_slots else [(0, 0)]
        for (sr, sc) in target_slots:
            cx, cy = config.get_cube_slot_screen_pos(sr, sc)
            self._safe_ctrl_shift_click(cx, cy, count=1)
            time.sleep(config.step_delay)

        # ---- Step 6: 检查魔盒是否已成功清空 ----
        time.sleep(0.08)
        cube_crop = screen_cap.capture_cube_area()
        is_empty = (ocr_engine.check_cube_gem_count(cube_crop) == 0)

        # 更新扣减与产出
        self.runes_map[rune_id] -= req_runes
        self.runes_map[rune_id + 1] = self.runes_map.get(rune_id + 1, 0) + 1
        if req_gem is not None:
            self.gem_matrix[gem_row][gem_col] -= 1
            self.gem_matrix_updated.emit(self.gem_matrix)
        self.runes_updated.emit(self.runes_map)

        if is_empty:
            self.log_message.emit(f"[产出成功] 获得 1 × [{next_rune['id']}# {next_rune['name_zh']}] 并已存入材料仓！", "success")
            return ("OK", "合成并存入成功")
        else:
            self.log_message.emit(f"[警告] 魔盒产物未成功收回材料仓 (请检查背包/材料页是否已满)", "warning")
            return ("ERROR", "魔盒产物收回失败")

    def run(self):
        """执行符文合成工作线程 (最多尝试 repeat_count 次)"""
        self._stop_requested = False
        hotkey_listener.register_stop_callback(self.request_stop)

        rune_info = RUNES_BY_ID.get(self.target_rune_id)
        if not rune_info or self.target_rune_id >= 33:
            self.finished_synthesis.emit(False, "无法合成最高级符文")
            hotkey_listener.unregister_stop_callback(self.request_stop)
            return

        self.status_changed.emit(f"开始合成 [{self.target_rune_id}# {rune_info['name_zh']}] (最多10次)...")
        self.log_message.emit(
            f"[任务] 启动【{self.target_rune_id}# {rune_info['name_zh']}】合成 10 个流程 (目标 ➔ {self.target_rune_id+1}#)",
            "info"
        )
        self.progress_updated.emit(0, self.repeat_count)

        completed_rounds = 0
        success = True
        abort_reason = ""

        for i in range(self.repeat_count):
            if self._stop_requested:
                break

            self.status_changed.emit(f"正在执行第 {i + 1}/{self.repeat_count} 次合成...")
            status_code, msg = self._execute_single_rune_craft(self.target_rune_id)

            if status_code == "STOP":
                # 材料不足正常结束循环
                abort_reason = msg
                break
            elif status_code == "ERROR":
                # 异常中断
                success = False
                abort_reason = msg
                self.log_message.emit(f"[安全熔断] 符文合成中止: {msg}", "error")
                break
            elif status_code == "OK":
                completed_rounds += 1
                self.progress_updated.emit(completed_rounds, self.repeat_count)
                time.sleep(config.step_delay)

        hotkey_listener.unregister_stop_callback(self.request_stop)

        if self._stop_requested:
            self.status_changed.emit("已手动紧急停止")
            self.finished_synthesis.emit(False, f"用户中止 (已完成 {completed_rounds} 次)")
        elif not success:
            self.status_changed.emit("合成异常已中止")
            self.finished_synthesis.emit(False, f"异常中止: {abort_reason} (已完成 {completed_rounds} 次)")
        else:
            if completed_rounds == self.repeat_count:
                self.status_changed.emit(f"已完成全部 {self.repeat_count} 次合成！")
                self.log_message.emit(f"[完成] 已顺利完成全部 {self.repeat_count} 次合成目标！", "success")
                self.finished_synthesis.emit(True, f"全部完成 (共 {completed_rounds} 次)")
            else:
                self.status_changed.emit(f"合成结束 (已完成 {completed_rounds} 次)")
                self.log_message.emit(f"[结束] 合成结束: {abort_reason} (共完成 {completed_rounds} 次)", "info")
                self.finished_synthesis.emit(True, f"已完成 {completed_rounds} 次 ({abort_reason})")
