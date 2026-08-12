# -*- coding: utf-8 -*-
"""
D2R 自动宝石/符文合成工具 - 符文配置与赫拉迪姆魔盒公式定义
包含全部 33 种符文的名称、品阶、合成公式 (原料符文数量、附加宝石品阶) 及坐标计算
"""

import os
from typing import Dict, List, Optional, Tuple

# 33 种符文定义表 (编号 1# ~ 33#)
# require_count: 合成下一级所需本级符文数量 (1#~20# 需 3 个, 21#~32# 需 2 个, 33# 无法合成)
# required_gem: 合成下一级所需宝石 (None 或 (gem_id, tier_id))
# 宝石颜色顺序: Topaz(黄) -> Amethyst(紫) -> Sapphire(蓝) -> Ruby(红) -> Emerald(绿) -> Diamond(钻)
RUNES_DATA = [
    # 1# ~ 9# (纯符文 3合1)
    {"id": 1, "code": "r01", "name_en": "El", "name_zh": "艾尔", "row": 0, "col": 0, "req_runes": 3, "req_gem": None},
    {"id": 2, "code": "r02", "name_en": "Eld", "name_zh": "艾德", "row": 0, "col": 1, "req_runes": 3, "req_gem": None},
    {"id": 3, "code": "r03", "name_en": "Tir", "name_zh": "特尔", "row": 0, "col": 2, "req_runes": 3, "req_gem": None},
    {"id": 4, "code": "r04", "name_en": "Nef", "name_zh": "那夫", "row": 0, "col": 3, "req_runes": 3, "req_gem": None},
    {"id": 5, "code": "r05", "name_en": "Eth", "name_zh": "爱斯", "row": 0, "col": 4, "req_runes": 3, "req_gem": None},
    {"id": 6, "code": "r06", "name_en": "Ith", "name_zh": "伊司", "row": 0, "col": 5, "req_runes": 3, "req_gem": None},
    {"id": 7, "code": "r07", "name_en": "Tal", "name_zh": "塔尔", "row": 0, "col": 6, "req_runes": 3, "req_gem": None},
    {"id": 8, "code": "r08", "name_en": "Ral", "name_zh": "拉尔", "row": 1, "col": 0, "req_runes": 3, "req_gem": None},
    {"id": 9, "code": "r09", "name_en": "Ort", "name_zh": "欧特", "row": 1, "col": 1, "req_runes": 3, "req_gem": None},

    # 10# ~ 15# (3合1 + 碎裂宝石 chipped)
    {"id": 10, "code": "r10", "name_en": "Thul", "name_zh": "书尔", "row": 1, "col": 2, "req_runes": 3, "req_gem": ("topaz", "chipped"), "gem_name": "碎裂黄宝石"},
    {"id": 11, "code": "r11", "name_en": "Amn", "name_zh": "安姆", "row": 1, "col": 3, "req_runes": 3, "req_gem": ("amethyst", "chipped"), "gem_name": "碎裂紫宝石"},
    {"id": 12, "code": "r12", "name_en": "Sol", "name_zh": "索尔", "row": 1, "col": 4, "req_runes": 3, "req_gem": ("sapphire", "chipped"), "gem_name": "碎裂蓝宝石"},
    {"id": 13, "code": "r13", "name_en": "Shael", "name_zh": "夏", "row": 1, "col": 5, "req_runes": 3, "req_gem": ("ruby", "chipped"), "gem_name": "碎裂红宝石"},
    {"id": 14, "code": "r14", "name_en": "Dol", "name_zh": "多尔", "row": 1, "col": 6, "req_runes": 3, "req_gem": ("emerald", "chipped"), "gem_name": "碎裂绿宝石"},
    {"id": 15, "code": "r15", "name_en": "Hel", "name_zh": "海尔", "row": 2, "col": 0, "req_runes": 3, "req_gem": ("diamond", "chipped"), "gem_name": "碎裂钻石"},

    # 16# ~ 20# (3合1 + 有瑕疵宝石 flawed)
    {"id": 16, "code": "r16", "name_en": "Io", "name_zh": "艾欧", "row": 2, "col": 1, "req_runes": 3, "req_gem": ("topaz", "flawed"), "gem_name": "有瑕疵黄宝石"},
    {"id": 17, "code": "r17", "name_en": "Lum", "name_zh": "卢姆", "row": 2, "col": 2, "req_runes": 3, "req_gem": ("amethyst", "flawed"), "gem_name": "有瑕疵紫宝石"},
    {"id": 18, "code": "r18", "name_en": "Ko", "name_zh": "科", "row": 2, "col": 3, "req_runes": 3, "req_gem": ("sapphire", "flawed"), "gem_name": "有瑕疵蓝宝石"},
    {"id": 19, "code": "r19", "name_en": "Fal", "name_zh": "法尔", "row": 2, "col": 4, "req_runes": 3, "req_gem": ("ruby", "flawed"), "gem_name": "有瑕疵红宝石"},
    {"id": 20, "code": "r20", "name_en": "Lem", "name_zh": "蓝姆", "row": 2, "col": 5, "req_runes": 3, "req_gem": ("emerald", "flawed"), "gem_name": "有瑕疵绿宝石"},

    # 21# ~ 27# (2合1 + 有瑕疵/普通宝石)
    {"id": 21, "code": "r21", "name_en": "Pul", "name_zh": "普尔", "row": 2, "col": 6, "req_runes": 2, "req_gem": ("diamond", "flawed"), "gem_name": "有瑕疵钻石"},
    {"id": 22, "code": "r22", "name_en": "Um", "name_zh": "乌姆", "row": 3, "col": 0, "req_runes": 2, "req_gem": ("topaz", "normal"), "gem_name": "普通黄宝石"},
    {"id": 23, "code": "r23", "name_en": "Mal", "name_zh": "马尔", "row": 3, "col": 1, "req_runes": 2, "req_gem": ("amethyst", "normal"), "gem_name": "普通紫宝石"},
    {"id": 24, "code": "r24", "name_en": "Ist", "name_zh": "伊司特", "row": 3, "col": 2, "req_runes": 2, "req_gem": ("sapphire", "normal"), "gem_name": "普通蓝宝石"},
    {"id": 25, "code": "r25", "name_en": "Gul", "name_zh": "古尔", "row": 3, "col": 3, "req_runes": 2, "req_gem": ("ruby", "normal"), "gem_name": "普通红宝石"},
    {"id": 26, "code": "r26", "name_en": "Vex", "name_zh": "伐克斯", "row": 3, "col": 4, "req_runes": 2, "req_gem": ("emerald", "normal"), "gem_name": "普通绿宝石"},
    {"id": 27, "code": "r27", "name_en": "Ohm", "name_zh": "欧姆", "row": 3, "col": 5, "req_runes": 2, "req_gem": ("diamond", "normal"), "gem_name": "普通钻石"},

    # 28# ~ 32# (2合1 + 无瑕宝石 flawless)
    {"id": 28, "code": "r28", "name_en": "Lo", "name_zh": "罗", "row": 3, "col": 6, "req_runes": 2, "req_gem": ("topaz", "flawless"), "gem_name": "无瑕黄宝石"},
    {"id": 29, "code": "r29", "name_en": "Sur", "name_zh": "瑟", "row": 4, "col": 1, "req_runes": 2, "req_gem": ("amethyst", "flawless"), "gem_name": "无瑕紫宝石"},
    {"id": 30, "code": "r30", "name_en": "Ber", "name_zh": "贝", "row": 4, "col": 2, "req_runes": 2, "req_gem": ("sapphire", "flawless"), "gem_name": "无瑕蓝宝石"},
    {"id": 31, "code": "r31", "name_en": "Jah", "name_zh": "乔", "row": 4, "col": 3, "req_runes": 2, "req_gem": ("ruby", "flawless"), "gem_name": "无瑕红宝石"},
    {"id": 32, "code": "r32", "name_en": "Cham", "name_zh": "查姆", "row": 4, "col": 4, "req_runes": 2, "req_gem": ("emerald", "flawless"), "gem_name": "无瑕绿宝石"},

    # 33# (最高级符文，不可合成)
    {"id": 33, "code": "r33", "name_en": "Zod", "name_zh": "萨德", "row": 4, "col": 5, "req_runes": 0, "req_gem": None},
]

# 快速查询字典
RUNES_BY_ID = {r["id"]: r for r in RUNES_DATA}


def get_rune_recipe_text(rune_id: int) -> str:
    """获取符文合成下一级的配方文字说明"""
    if rune_id >= 33:
        return "最高级符文 (不可合成)"
    r = RUNES_BY_ID.get(rune_id)
    if not r:
        return ""
    next_r = RUNES_BY_ID.get(rune_id + 1)
    gem_part = f" + 1 × {r['gem_name']}" if r.get("gem_name") else ""
    return f"{r['req_runes']} × {r['id']}# {r['name_zh']}{gem_part} ➔ {next_r['id']}# {next_r['name_zh']}"
