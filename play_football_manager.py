#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚽ קריירה — משחק ניהול כדורגל
=============================
נקודת הכניסה למשחק. אין תלויות חיצוניות — רק פייתון.

    python3 play_football_manager.py              # משחק רגיל
    python3 play_football_manager.py --demo       # הדגמה אוטומטית
    python3 play_football_manager.py --demo --seasons=5
"""

import sys

from football_manager.cli import main

if __name__ == "__main__":
    sys.exit(main())
