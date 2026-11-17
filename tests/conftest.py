# -*- coding: utf-8 -*-
"""测试路径引导：确保项目根目录在 sys.path 中。

pytest.ini 已声明 pythonpath = .（需要 pytest>=7）；本文件作为旧版 pytest
的兜底，保证 `python -m pytest tests -q` 在任何环境下都能 import 顶层模块。
全程不导入 main.py / automation.py，不依赖 GUI / Win32 / 网络。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
