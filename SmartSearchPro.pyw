#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smart Search Pro - No-console launcher"""
import sys
import os
from pathlib import Path

# Setup path
app_dir = Path(__file__).parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

os.chdir(app_dir)

# Suppress console output
if sys.platform == 'win32':
    import warnings
    warnings.filterwarnings('ignore')

# Launch app
from app import main
sys.exit(main())
