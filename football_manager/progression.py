# -*- coding: utf-8 -*-
"""
football_manager.progression
============================
התפתחות השחקן: אימונים שבועיים, התאוששות, פציעות, הזדקנות בסוף עונה,
ולמידת מקצועות לקראת הקריירה שאחרי הפרישה.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional

from . import data as D
from .models import Club, Player, clamp

# מקדם התפתחות לפי גיל — צעירים גדלים מהר, ותיקים דועכים
AGE_CURVE = {
    16: 1.70, 17: 1.60, 18: 1.50, 19: 1.40, 20: 1.30, 21: 1.18, 22: 1.05,
    23: 0.92, 24: 0.78, 25: 0.62, 26: 0.48, 27: 0.34, 28: 0.22, 29: 0.12,
    30: 0.05, 31: -0.05, 32: -0.14, 33: -0.26, 34: -0.40, 35: -0.55,
    36: -0.70, 37: -0.85, 38: -1.00,
}

# תכונות שדועכות מוקדם מול כאלה שנשמרות
DECLINE_SENSITIVITY = {
    "pace": 1.7, "physical": 1.4, "dribbling": 1.1, "shooting": 0.7,
    "passing": 0.4, "defending": 0.5, "mental": -0.5,  # שלילי = ממשיך לעלות
}

OFF_PITCH_FOCUS = {"badges", "media", "business", "rest"}


def age_factor(age: int) -> float:
    """מחזיר את מקדם ההתפתחות לגיל נתון."""
    if age < 16:
        return 1.7
    if age > 38:
        return -1.1
    return AGE_CURVE[age]


# ---------------------------------------------------------------------------
# אימון שבועי
# ---------------------------------------------------------------------------

def weekly_training(player: Player, focus: str, club: Optional[Club],
                    rng: random.Random, intensity: float = 1.0) -> List[str]:
    """מבצע שבוע אימונים אחד ומחזיר הודעות למשתמש."""
    messages: List[str] = []
    facilities = club.training_facilities if club else 45

    # מנוחה
    if focus == "rest":
        player.fitness = clamp(player.fitness + 26, 0, 100)
        player.morale = clamp(player.morale + 1.5, 0, 100)
        if player.injury_weeks > 0:
            player.injury_weeks = max(0, player.injury_weeks - 1)
            if rng.random() < 0.3:
                player.injury_weeks = max(0, player.injury_weeks - 1)
                messages.append("🏥 השיקום מתקדם מהר מהצפוי.")
        return messages

    # לימודים מחוץ למגרש
    if focus == "badges":
        gain = (0.55 + player.attributes.get("mental", 50) / 200.0) * intensity
        if player.has_trait("student"):
            gain *= 1.4
        player.coaching = clamp(player.coaching + gain, 0, 100)
        player.fitness = clamp(player.fitness + 10, 0, 100)
        new_badges = min(4, int(player.coaching // 22))
        if new_badges > player.badges:
            player.badges = new_badges
            messages.append(f"🎓 השלמת תעודת אימון רמה {player.badges}!")
        return messages

    if focus == "media":
        player.media_skill = clamp(player.media_skill + 0.9 * intensity, 0, 100)
        player.reputation = clamp(player.reputation + 0.25, 0, 100)
        player.fitness = clamp(player.fitness + 9, 0, 100)
        return messages

    if focus == "business":
        player.business = clamp(player.business + 0.85 * intensity, 0, 100)
        player.fitness = clamp(player.fitness + 9, 0, 100)
        return messages

    # אימון תכונה
    player.fitness = clamp(player.fitness + 12 - 6 * intensity, 0, 100)
    if player.injury_weeks > 0:
        player.injury_weeks = max(0, player.injury_weeks - 1)
        return ["🩹 אתה בשיקום — האימון היה קל בהרבה."]

    gap = player.potential - player.overall
    curve = age_factor(player.age)
    base = 0.30 * intensity
    base *= 0.55 + facilities / 110.0
    base *= max(0.15, curve)
    base *= 1.0 + clamp(gap, -10, 25) * 0.05
    if player.has_trait("workhorse"):
        base *= 1.30
    base *= 0.75 + player.morale / 200.0
    base *= rng.uniform(0.7, 1.35)

    # ככל שמתקרבים לתקרת הפוטנציאל, ההתקדמות נעצרת כמעט לגמרי
    headroom = player.potential - player.overall
    if headroom <= 0:
        base *= 0.08
    elif headroom < 4:
        base *= 0.25 + headroom * 0.18

    current = player.growth.get(focus, 0.0) + base
    gained = 0
    while current >= 1.0 and player.attributes.get(focus, 50) < 97:
        player.attributes[focus] = player.attributes.get(focus, 50) + 1
        current -= 1.0
        gained += 1
    player.growth[focus] = current

    if gained:
        messages.append(f"📈 {D.ATTRIBUTE_NAMES_HE[focus]} עלתה ב-{gained} "
                        f"(עכשיו {player.attributes[focus]}).")

    # אימון אינטנסיבי מסוכן
    if intensity > 1.15 and rng.random() < 0.035 * intensity:
        weeks = rng.randint(1, 3)
        player.injury_weeks = weeks
        player.injury_name = "עומס יתר באימון"
        messages.append(f"🚑 נמתחת באימון — {weeks} שבועות בחוץ.")
    return messages


def weekly_recovery(player: Player, played: bool, rng: random.Random) -> None:
    """התאוששות טבעית בסוף שבוע."""
    if player.injury_weeks > 0:
        player.injury_weeks -= 1
        if player.injury_weeks == 0:
            player.injury_name = ""
            player.fitness = clamp(player.fitness + 15, 0, 100)
    if not played:
        player.fitness = clamp(player.fitness + 9, 0, 100)
    player.form = clamp(player.form + (0 if played else rng.uniform(-1.5, 1.5)), 5, 99)


def simulate_ai_week(players: Dict[str, Player], rng: random.Random,
                     clubs: Dict[str, Club], skip: Optional[str] = None) -> None:
    """מריץ שבוע אימונים/התאוששות לכל שחקני המחשב."""
    for pid, player in players.items():
        if pid == skip or player.retired:
            continue
        club = clubs.get(player.club_id) if player.club_id else None
        if player.injury_weeks > 0:
            player.injury_weeks -= 1
            if player.injury_weeks == 0:
                player.injury_name = ""
            continue
        player.fitness = clamp(player.fitness + rng.uniform(6, 16), 0, 100)
        if rng.random() < 0.55:
            focus = rng.choice(D.ATTRIBUTES)
            weekly_training(player, focus, club, rng, intensity=0.85)


# ---------------------------------------------------------------------------
# סוף עונה
# ---------------------------------------------------------------------------

def end_of_season_development(player: Player, rng: random.Random,
                              minutes_share: float = 0.5) -> List[str]:
    """הזדקנות וקפיצת/דעיכת מדרגה שנתית."""
    messages: List[str] = []
    player.age += 1
    curve = age_factor(player.age)

    # דקות משחק מאיצות התפתחות של צעירים
    exposure = 0.45 + minutes_share * 1.1
    for attr in D.ATTRIBUTES:
        sensitivity = DECLINE_SENSITIVITY[attr]
        if curve > 0:
            delta = curve * exposure * rng.uniform(0.4, 1.5)
            if player.overall >= player.potential:
                delta *= 0.08
        else:
            delta = curve * max(0.2, sensitivity) * rng.uniform(0.5, 1.5)
        player.growth[attr] = player.growth.get(attr, 0.0) + delta
        whole = int(player.growth[attr])
        if whole:
            player.attributes[attr] = int(clamp(
                player.attributes.get(attr, 50) + whole, 10, 97))
            player.growth[attr] -= whole

    # מוניטין נגזר מהעונה
    season = player.season
    if season.apps:
        contribution = (season.goals + season.assists) / max(1, season.apps)
        player.reputation = clamp(
            player.reputation + (season.avg_rating - 6.6) * 4 + contribution * 6, 1, 99)

    player.career.merge(season)
    player.season = type(season)()
    player.fitness = 100.0
    player.form = 50.0
    if player.contract.years_left > 0:
        player.contract.years_left -= 1
    return messages


def should_retire(player: Player, rng: random.Random) -> bool:
    """האם שחקן מחשב פורש בסוף העונה."""
    if player.age < 32:
        return False
    chance = (player.age - 31) * 0.16
    if player.overall < 55:
        chance += 0.18
    if player.injury_weeks > 12:
        chance += 0.25
    return rng.random() < clamp(chance, 0, 0.95)


def retirement_pressure(player: Player) -> float:
    """0-1: כמה העולם דוחף את השחקן האנושי לפרוש."""
    pressure = 0.0
    pressure += max(0, player.age - 31) * 0.13
    pressure += max(0, 62 - player.overall) * 0.012
    if player.injury_weeks >= 10:
        pressure += 0.25
    if player.contract.years_left == 0 and player.age > 33:
        pressure += 0.15
    return clamp(pressure, 0.0, 1.0)
