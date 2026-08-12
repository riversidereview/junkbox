# -*- coding: utf-8 -*-
"""
PyInstaller 打包脚本 (安全构建版)
"""

import os
import sys
import subprocess
import shutil

def build():
    print("========================================")
    print("  开始打包 D2R 自动宝石合成工具...")
    print("========================================")

    # 包含 rapidocr onnx 模型的必要数据目录
    import rapidocr_onnxruntime
    rapidocr_dir = os.path.dirname(rapidocr_onnxruntime.__file__)
    print(f"RapidOCR 路径: {rapidocr_dir}")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name", "D2R_Gem_Crafter",
        "--icon", "app.ico",
        "--add-data", "assets;assets",
        "--add-data", f"{rapidocr_dir};rapidocr_onnxruntime",
        "--hidden-import", "PySide6",
        "--hidden-import", "PySide6.QtCore",
        "--hidden-import", "PySide6.QtGui",
        "--hidden-import", "PySide6.QtWidgets",
        "--hidden-import", "keyboard",
        "--hidden-import", "mss",
        "--hidden-import", "pygetwindow",
        "--hidden-import", "cv2",
        "--hidden-import", "numpy",
        "--hidden-import", "pyautogui",
        "--hidden-import", "onnxruntime",
        "--hidden-import", "shapely",
        "--hidden-import", "pyclipper",
        "main.py"
    ]

    print("执行命令:", " ".join(cmd))
    res = subprocess.run(cmd)
    if res.returncode == 0:
        print("\n========================================")
        print("🎉 打包成功！")
        exe_path = os.path.abspath("dist/D2R_Gem_Crafter/D2R_Gem_Crafter.exe")
        print(f"可执行文件: {exe_path}")
        print("========================================")
    else:
        print(f"\n❌ 打包失败，错误码: {res.returncode}")

if __name__ == "__main__":
    build()
