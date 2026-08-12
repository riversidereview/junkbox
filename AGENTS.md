# D2R Gem Crafter 开发规范与基准指南 (AGENTS.md)

> **基准版本号**: `v1.1.0` (Git Tag: `v1.1.0`)  
> **项目定位**: 《暗黑破坏神 2：重制版》(Diablo II: Resurrected) 桌面自动宝石与符文合成工具。  
> **核心原则**: 后续所有功能迭代、重构与优化必须在 `v1.1.0` 稳定版本的基础之上进行，严禁破坏既有已验证的核心业务逻辑与美术规范。

---

## 1. 核心业务逻辑规范 (必须严格保持)

1. **99 满仓级联跨阶流转（宝石）**：
   - 当上一级宝石数量达到 99 个堆叠上限时，合成流程**绝不能异常中止**，而是自动平滑切换至下一级宝石的合成。
   - 跨阶切换时，魔盒内已留存 1 颗宝石，因此下一次合成循环只需要从背包/仓位置入 2 颗宝石即可继续。
2. **保留 20 颗底仓机制（宝石）**：
   - 勾选【保留 20 颗宝石】后，单次合成结束后若检测到当前品阶宝石 ≤ 20 颗，必须自动跳过并开始合成下一级宝石（保留洗超大护身符或打孔底仓）。
3. **符文合成系统 (1#~33#)**：
   - 33 种符文独立面板，1#~32# 具备专属【合成10个】循环合成流程。
   - 支持多材料与宝石合成配方（10#~21# 需要碎裂/裂开/普通/无瑕疵宝石，22#~32# 需各色无暇/完美宝石）。
4. **三态智能熔断与安全停止**：
   - **紧急停止**：必须使用 Windows 原生 `GetAsyncKeyState` 独立线程监听自定义热键（默认 `Num 1`，支持 F1~F12 等），确保任何时候按下均能毫秒级中断所有鼠标模拟并强制释放按键。
   - **合成熔断**：单次合成若材料不足或魔盒未产出新宝石/符文，必须触发熔断保护并安全退出，避免死循环。

---

## 2. UI 与美术资产规范 (严禁擅自修改破坏)

1. **官方原版素材**：
   - `assets/gems/` 下存储的 35 个 PNG（7 品类 × 5 品阶）及 `assets/runes/` 下 33 个 PNG 为 **100% 暴雪官方《暗黑破坏神 2：重制版》游戏原版提取素材**。
   - **严禁**使用任何 OpenCV 程序化绘制的几何图形或单色色相调色板生成的变体替换。
2. **零遮挡与独立居中排版**：
   - 宝石卡片 (`GemCellWidget`) 与符文卡片 (`RuneCellWidget`) 必须保持物理隔离容器：
     - **上层**：独立视区，官方原版图标等比居中缩放显示。
     - **下层**：独立数字条 (`GemCountBar`)，数字绝对水平垂直居中，严禁与宝石/符文发生任何重叠与遮挡。
   - 所有 35 种宝石与 33 种符文卡片必须保持尺寸均等与严格对称。
3. **纯净暗黑质感**：
   - 界面所有控件、标题、按钮及日志输出**严禁包含任何 Emoji 表情字符**。

---

## 3. 代码模块架构

- [`main.py`](file:///c:/Users/Patch/Documents/antigravity/excited-nobel/main.py)：程序入口与高 DPI 适配。
- [`core/config.py`](file:///c:/Users/Patch/Documents/antigravity/excited-nobel/core/config.py)：5x7 宝石数据模型、坐标体系与配置读取。
- [`core/rune_config.py`](file:///c:/Users/Patch/Documents/antigravity/excited-nobel/core/rune_config.py)：33 种符文数据、矩阵排版与合成配方定义。
- [`core/synthesizer.py`](file:///c:/Users/Patch/Documents/antigravity/excited-nobel/core/synthesizer.py)：核心宝石合成工作流（级联跨阶流转、保留底仓、魔盒置入/转化）。
- [`core/rune_synthesizer.py`](file:///c:/Users/Patch/Documents/antigravity/excited-nobel/core/rune_synthesizer.py)：核心符文合成工作流（10次循环合成、宝石材料置入与魔盒校验）。
- [`core/hotkey_listener.py`](file:///c:/Users/Patch/Documents/antigravity/excited-nobel/core/hotkey_listener.py)：Windows 原生底层热键监听器与动态切换。
- [`core/ocr_engine.py`](file:///c:/Users/Patch/Documents/antigravity/excited-nobel/core/ocr_engine.py)：材料仓数字高精度 OCR 识别引擎（多变体与笔画亮度校验，100% 精度）。
- [`ui/main_window.py`](file:///c:/Users/Patch/Documents/antigravity/excited-nobel/ui/main_window.py)：PySide6 主窗口与合成线程调度。
- [`ui/gem_grid_widget.py`](file:///c:/Users/Patch/Documents/antigravity/excited-nobel/ui/gem_grid_widget.py)：5x7 宝石矩阵组件。
- [`ui/rune_grid_widget.py`](file:///c:/Users/Patch/Documents/antigravity/excited-nobel/ui/rune_grid_widget.py)：33 种符文面板与【合成10个】卡片组件。
- [`ui/dark_theme.py`](file:///c:/Users/Patch/Documents/antigravity/excited-nobel/ui/dark_theme.py)：暗金质感暗黑主题样式表。
- [`D2R_Gem_Crafter.spec`](file:///c:/Users/Patch/Documents/antigravity/excited-nobel/D2R_Gem_Crafter.spec)：PyInstaller 单独打包配置文件。

---

## 4. 打包与发布

打包命令必须执行：
```bash
pyinstaller -y D2R_Gem_Crafter.spec
```
打包输出单个独立绿色执行文件：`dist/D2R_Gem_Crafter.exe`（单文件免安装，开箱即用）。
