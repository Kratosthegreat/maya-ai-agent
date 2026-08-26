# -*- coding: utf-8 -*-
"""
football_manager.knowledge
==========================
מה אתה באמת יודע על שחקן אחר.

זו הייתה הבעיה שהכי קשה להסביר: "אתה מקבל את מה שאתה רואה". במשחק
היה אפשר לפתוח כל שחקן בעולם ולראות את כל המספרים שלו במדויק. בשביל
מי שמכיר את המקור זה הורג את המשחק — כי שם ידע הוא משאב.

כאן: את עצמך אתה מכיר. את חבר לקבוצה אתה מכיר טוב. יריב שראית מולו
שלושה משחקים אתה מכיר קצת. שחקן בליגה אחרת אתה לא מכיר בכלל — אלא
אם הצוות סרק אותו.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from . import data as D
from .models import Player, clamp

# רמות ידע: 0 = שמועה, 1 = דוח בסיסי, 2 = דוח מלא, 3 = ידיעה מוחלטת
LEVEL_NAMES = {
    0: "שמועות בלבד",
    1: "דוח ראשוני",
    2: "דוח מלא",
    3: "ידיעה מוחלטת",
}


def knowledge_level(game, player: Player) -> int:
    """כמה אתה יודע על השחקן הזה."""
    if player.pid == game.me_id:
        return 3
    me_club = game.my_club
    if me_club and player.club_id == me_club.cid:
        return 3                                   # חבר לקבוצה, כל יום באימון
    if game.flag(f"scouted_{player.pid}"):
        return 2
    scouted = game.flag("scouted")                 # הצוות סרק לפני החלון
    if not player.club_id:
        return 1 if scouted else 0
    club = game.clubs.get(player.club_id)
    if not club:
        return 0

    level = 0
    if me_club and club.league_id == me_club.league_id:
        level = 1                                  # אותה ליגה — משחקים מולו
    if player.reputation >= 62:
        level = max(level, 1)                      # כוכב שכולם מכירים
    if player.reputation >= 80:
        level = max(level, 2)
    if scouted:
        level = min(3, level + 1)
    if me_club and club.reputation >= 70 and me_club.reputation >= 70:
        level = max(level, 1)
    return level


def _band(value: int, width: int) -> Tuple[int, int]:
    low = max(1, value - width)
    high = min(20, value + width)
    return low, high


def shown_detail(game, player: Player) -> Dict[str, Any]:
    """התכונות כפי שאתה רואה אותן — מדויקות, בטווח, או בכלל לא.

    מחזיר לכל תכונה: {"value": מדויק או None, "low", "high", "exact"}.
    """
    level = knowledge_level(game, player)
    width = {3: 0, 2: 1, 1: 3, 0: 5}[level]
    out: Dict[str, Any] = {}
    for attr in D.attrs_for(player.position):
        value = player.detail.get(attr, 10)
        if level >= 3:
            out[attr] = {"value": value, "low": value, "high": value, "exact": True}
        elif level == 0:
            out[attr] = {"value": None, "low": 0, "high": 0, "exact": False}
        else:
            low, high = _band(value, width)
            out[attr] = {"value": None, "low": low, "high": high, "exact": False}
    return out


def _stable_hash(text: str) -> int:
    """FNV-1a — אותו מספר בפייתון וב-JS, ואותו מספר בכל הרצה."""
    value = 2166136261
    for ch in text:
        value ^= ord(ch)
        value = (value * 16777619) & 0xFFFFFFFF
    return value


def stars(value: float, scale: float = 100.0) -> float:
    """המרה לכוכבים בחצאים — ככה מציגים הערכה שאינה מספר."""
    return round(clamp(value / scale * 5.0, 0.0, 5.0) * 2) / 2.0


def star_text(count: float) -> str:
    full = int(count)
    half = 1 if count - full >= 0.5 else 0
    return "★" * full + ("½" if half else "") + "☆" * (5 - full - half)


def ability_stars(game, player: Player) -> float:
    """הערכת היכולת הנוכחית בכוכבים, ביחס לרמת הליגה שאתה מכיר."""
    level = knowledge_level(game, player)
    value = float(player.overall)
    if level < 3:
        # ככל שאתה יודע פחות, ההערכה גסה יותר — ולפעמים פשוט לא נכונה.
        # הרעש קבוע לשחקן ולא מוגרל מחדש בכל צפייה, אחרת המסך היה
        # מהבהב; ולכן גם חייב להיות דטרמיניסטי ולא תלוי הרצה.
        noise = (_stable_hash(player.pid) % 11 - 5) * (3 - level) * 0.9
        value = clamp(value + noise, 1, 99)
    return stars(value)


def potential_stars(game, player: Player) -> Tuple[float, float]:
    """טווח הפוטנציאל בכוכבים. אף אחד לא באמת יודע — גם לא אתה."""
    level = knowledge_level(game, player)
    if player.pid == game.me_id:
        return stars(player.potential), stars(player.potential)
    spread = {3: 6.0, 2: 11.0, 1: 18.0, 0: 26.0}[level]
    low = clamp(player.potential - spread, 1, 99)
    high = clamp(player.potential + spread * 0.6, 1, 99)
    return stars(low), stars(high)


def summary(game, player: Player) -> Dict[str, Any]:
    """כל מה שמסך של שחקן אחר צריך."""
    level = knowledge_level(game, player)
    low, high = potential_stars(game, player)
    return {
        "level": level,
        "level_he": LEVEL_NAMES[level],
        "ability": ability_stars(game, player),
        "potential_low": low,
        "potential_high": high,
        "exact": level >= 3,
        "detail": shown_detail(game, player),
        "role": player.role,
        "personality": level >= 2,
    }


def scout_player(game, player: Player) -> str:
    """לשלוח את הצוות לבדוק שחקן מסוים. עולה כסף למועדון."""
    club = game.my_club
    if not club:
        return "אין לך מועדון שישלח צופה."
    if game.flag(f"scouted_{player.pid}"):
        return f"כבר יש לך דוח מלא על {player.name}."
    cost = int(18_000 + player.reputation * 900)
    if club.balance < cost:
        return f"הסריקה עולה ₪{cost:,} והקופה לא עומדת בזה."
    club.balance -= cost
    game.set_flag(f"scouted_{player.pid}", True)
    return (f"🔍 הצוות נסע לראות את {player.name}. "
            f"₪{cost:,} מהקופה — ועכשיו יש עליו דוח מלא.")
