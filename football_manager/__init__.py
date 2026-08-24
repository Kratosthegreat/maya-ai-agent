# -*- coding: utf-8 -*-
"""
⚽ קריירה — משחק ניהול כדורגל בסגנון מנג'ר.

מסלול חיים שלם: נער בקבוצת נוער → שחקן מקצוען → ותיק → פרישה →
מאמן → מנג'ר → מנהל ספורטיבי / פרשן / סוכן / בעלים.

שימוש מהיר:

    from football_manager import GameState
    game = GameState.new_game("עומר לוי", "ST", "hapoel_carmel", age=17)
    game.set_action("shooting")
    report = game.advance_week()

או מהטרמינל:

    python3 play_football_manager.py
"""

from .game import GameState, WeekReport, SEASON_WEEKS
from .models import Club, Player, Contract, Stats, generate_world
from .engine import MatchResult, simulate_match

__version__ = "1.0.0"

__all__ = [
    "GameState", "WeekReport", "SEASON_WEEKS",
    "Club", "Player", "Contract", "Stats", "generate_world",
    "MatchResult", "simulate_match",
]
