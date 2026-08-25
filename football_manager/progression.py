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
from .engine import medical_care
from .models import Club, Player, clamp, gain_reputation

# מקדם התפתחות לפי גיל — צעירים גדלים מהר, ותיקים דועכים
# העקומה שטוחה יותר ממה שנדמה: שחקן לא "נסגר" בגיל 18. השיא מגיע
# באמצע שנות העשרים, ועד אז כל עונה עוד מוסיפה — פחות ופחות, אבל מוסיפה.
AGE_CURVE = {
    13: 1.60, 14: 1.58, 15: 1.54,
    16: 1.48, 17: 1.42, 18: 1.34, 19: 1.26, 20: 1.18, 21: 1.10, 22: 1.02,
    23: 0.94, 24: 0.85, 25: 0.75, 26: 0.63, 27: 0.51, 28: 0.39, 29: 0.27,
    30: 0.14, 31: 0.02, 32: -0.14, 33: -0.28, 34: -0.42, 35: -0.56,
    36: -0.72, 37: -0.86, 38: -1.00,
}

# תכונות שדועכות מוקדם מול כאלה שנשמרות
DECLINE_SENSITIVITY = {
    "pace": 1.7, "physical": 1.4, "dribbling": 1.1, "shooting": 0.7,
    "passing": 0.4, "defending": 0.5, "mental": -0.5,  # שלילי = ממשיך לעלות
}

OFF_PITCH_FOCUS = {"badges", "media", "business", "rest"}


def age_factor(age: int) -> float:
    """מחזיר את מקדם ההתפתחות לגיל נתון."""
    if age < 13:
        return 1.65
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
    assistant = club.staff_quality("assistant") if club else 0
    fitness_coach = club.staff_quality("fitness") if club else 0
    care = medical_care(club)

    # מנוחה
    if focus == "rest":
        player.fitness = clamp(player.fitness + 26 + fitness_coach / 14.0, 0, 100)
        player.morale = clamp(player.morale + 1.5, 0, 100)
        player.resilience = clamp(player.resilience + 0.14, 0, 96)
        player.sharpness = clamp(player.sharpness - 1.6, 0, 100)
        if player.injury_weeks > 0:
            player.injury_weeks = max(0, player.injury_weeks - 1)
            if rng.random() < 0.20 + care * 0.34:
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
        gain_reputation(player, 0.25)
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
    base = 0.165 * intensity
    base *= 0.55 + facilities / 110.0
    base *= 1.0 + assistant / 420.0          # עוזר מאמן — עד 23% יותר
    base *= max(0.15, curve)
    base *= 1.0 + clamp(gap, -10, 18) * 0.032
    if player.has_trait("workhorse"):
        base *= 1.30
    base *= 0.75 + player.morale / 200.0
    base *= rng.uniform(0.7, 1.35)

    # ככל שמתקרבים לתקרת הפוטנציאל, ההתקדמות נעצרת כמעט לגמרי
    headroom = player.potential - player.overall
    if headroom <= 0:
        base *= 0.06
    elif headroom < 6:
        base *= 0.20 + headroom * 0.13

    # האימון מתפזר בשלוש שכבות: התכונה שבחרת, התכונות הקרובות לה,
    # וכל השאר — כי גוף של בן 17 מתפתח גם בלי שתכוון אליו.
    gains: Dict[str, int] = {}
    weights = D.POSITION_WEIGHTS[player.position]
    shares: Dict[str, float] = {}
    for attr in D.ATTRIBUTES:
        shares[attr] = D.GENERAL_SHARE * (0.45 + weights.get(attr, 0.1) * 2.4)
    for attr in D.TRAINING_SPILL.get(focus, ()):
        shares[attr] = shares.get(attr, 0.0) + D.SPILL_SHARE
    shares[focus] = shares.get(focus, 0.0) + 1.0

    # עבודת כוח בונה גוף שנשבר פחות. זו הידית שמאפשרת לחזק שחקן פציע.
    if focus == "physical":
        player.resilience = clamp(player.resilience + 0.22 * intensity, 0, 96)
    elif focus == "pace":
        player.resilience = clamp(player.resilience + 0.07 * intensity, 0, 96)
    player.sharpness = clamp(player.sharpness - 0.5, 0, 100)

    for attr, share in shares.items():
        level = player.attributes.get(attr, 50)
        step = base * share * specialisation_damper(level, player.overall)
        current = player.growth.get(attr, 0.0) + step
        while current >= 1.0 and player.attributes.get(attr, 50) < 97:
            player.attributes[attr] = player.attributes.get(attr, 50) + 1
            current -= 1.0
            gains[attr] = gains.get(attr, 0) + 1
        player.growth[attr] = current

    if gains:
        parts = [f"{D.ATTRIBUTE_NAMES_HE[a]} ל-{player.attributes[a]}"
                 for a in gains]
        messages.append("📈 " + ", ".join(parts) + ".")

    # אימון אינטנסיבי מסוכן
    injury_chance = (0.022 * intensity * player.injury_risk
                     * (1.0 - fitness_coach / 260.0))
    if intensity > 1.15 and rng.random() < injury_chance:
        weeks = rng.randint(1, 3)
        player.injury_weeks = weeks
        player.injury_name = "עומס יתר באימון"
        messages.append(f"🚑 נמתחת באימון — {weeks} שבועות בחוץ.")
    return messages


def specialisation_damper(level: int, overall: int) -> float:
    """בולם תכונה שרצה הרחק מכל השאר.

    אפשר להיות מצוין בדבר אחד, אבל לא לפתח בעיטה 95 עם גוף של ילד:
    ככל שהפער מהדירוג הכללי גדל, כל נקודה נוספת נעשית יקרה יותר.
    """
    gap = level - overall
    if gap <= 12:
        return 1.0
    return max(0.18, 1.0 - (gap - 12) * 0.055)


def weekly_recovery(player: Player, played: bool, rng: random.Random,
                    club: Optional[Club] = None) -> None:
    """התאוששות טבעית בסוף שבוע. מרכז רפואי וצוות מקצרים שיקום."""
    care = medical_care(club)
    if player.injury_weeks > 0:
        player.injury_weeks -= 1
        if player.injury_weeks > 0 and rng.random() < (care - 0.45) * 0.55:
            player.injury_weeks -= 1        # טיפול טוב חוסך עוד שבוע
        if player.injury_weeks == 0:
            player.injury_name = ""
            player.fitness = clamp(player.fitness + 15, 0, 100)
    if played:
        player.sharpness = clamp(player.sharpness + 5.5, 0, 100)
    else:
        fitness_coach = club.staff_quality("fitness") if club else 0
        player.fitness = clamp(player.fitness + 9 + fitness_coach / 22.0, 0, 100)
        player.sharpness = clamp(player.sharpness - 1.1, 0, 100)
    if player.injury_weeks > 0:
        player.sharpness = clamp(player.sharpness - 1.8, 0, 100)
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

def update_potential(player: Player, rng: random.Random,
                     minutes_share: float, club: Optional[Club]) -> Optional[str]:
    """מעדכן את הערכת הפוטנציאל לפי מה שהשחקן באמת עשה השנה.

    התקרה המוחלטת (ceiling) נסתרת ולא זזה. מה שזז הוא ההערכה: עונה טובה
    עם דקות משחק במועדון עם מתקנים טובים מגלה שיש כאן יותר ממה שחשבו,
    ושנה על הספסל אחרי גיל 21 מכווצת את מה שנשאר.
    """
    room = player.ceiling - player.potential
    rating = player.season.avg_rating if player.season.apps else 6.1
    quality = (rating - 6.45) * 0.85 + (minutes_share - 0.45) * 1.1

    if room <= 0:
        return None

    youth = 1.0 if player.age <= 20 else max(0.12, 1.0 - (player.age - 20) * 0.15)
    facilities = (club.training_facilities if club else 50) / 100.0
    step = room * 0.30 * youth * (0.40 + facilities * 0.55) * max(0.0, 0.45 + quality)
    if player.has_trait("workhorse"):
        step *= 1.30
    if player.has_trait("student"):
        step *= 1.10
    step *= rng.uniform(0.65, 1.4)

    if quality < -0.45 and player.age > 21:
        step = -room * 0.06          # שנה מבוזבזת עולה בתקרה
    gained = int(round(step))
    if not gained:
        return None
    before = player.potential
    player.potential = int(clamp(player.potential + gained, player.overall,
                                 player.ceiling))
    if player.potential == before:
        return None
    if player.potential > before:
        return (f"📈 ההערכה עליך עלתה: הפוטנציאל שלך עכשיו {player.potential} "
                f"(היה {before}).")
    return f"📉 עונה כזו עולה — ההערכה ירדה ל-{player.potential}."


def end_of_season_development(player: Player, rng: random.Random,
                              minutes_share: float = 0.5,
                              club: Optional[Club] = None) -> List[str]:
    """הזדקנות, עדכון הערכת הפוטנציאל וקפיצת/דעיכת מדרגה שנתית."""
    messages: List[str] = []
    if player.age >= 29:
        player.resilience = clamp(player.resilience - (player.age - 28) * 0.9, 3, 96)
    note = update_potential(player, rng, minutes_share, club)
    if note and player.is_human:
        messages.append(note)
    player.age += 1
    curve = age_factor(player.age)

    # דקות משחק מאיצות התפתחות של צעירים
    exposure = 0.45 + minutes_share * 1.1
    for attr in D.ATTRIBUTES:
        sensitivity = DECLINE_SENSITIVITY[attr]
        if curve > 0:
            # קפיצת הקיץ אמיתית אבל לא דרמטית — רוב ההתפתחות היא באימונים
            delta = curve * exposure * rng.uniform(0.4, 1.5) * 0.45
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
        gain_reputation(player,
                        (season.avg_rating - 6.6) * 3.2 + contribution * 5.0)

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
