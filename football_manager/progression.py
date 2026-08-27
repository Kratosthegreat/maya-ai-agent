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
from .models import (Club, Player, add_detail, add_group, clamp,
                     gain_reputation, grow_body, personality_effect,
                     recompute_groups)

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

# אותו רעיון, ברזולוציה של התכונות המפורטות: הרגליים הולכות ראשונות,
# הראש נשאר — ולכן ותיק מפצה בקריאת משחק על מה שאיבד במהירות.
DETAIL_DECLINE = {
    "acceleration": 1.9, "pace": 1.9, "agility": 1.5, "balance": 1.0,
    "stamina": 1.4, "jumping_reach": 1.3, "strength": 0.9, "natural_fitness": 1.1,
    "dribbling": 1.1, "flair": 0.6, "work_rate": 0.9, "aggression": 0.4,
    "finishing": 0.6, "long_shots": 0.5, "heading": 0.7, "crossing": 0.4,
    "first_touch": 0.2, "technique": 0.1, "passing": 0.2, "corners": 0.0,
    "free_kick": 0.0, "penalty_taking": 0.0, "long_throws": 0.5,
    "tackling": 0.8, "marking": 0.4,
    "anticipation": -0.6, "composure": -0.6, "concentration": -0.4,
    "decisions": -0.7, "determination": -0.2, "leadership": -0.9,
    "off_the_ball": -0.2, "positioning": -0.7, "teamwork": -0.4,
    "vision": -0.5, "bravery": 0.0,
    "reflexes": 1.0, "handling": 0.3, "one_on_ones": 0.2, "aerial_reach": 1.1,
    "command_of_area": -0.4, "communication": -0.6, "kicking": 0.3,
    "throwing": 0.3, "rushing_out": 0.8, "eccentricity": 0.0,
    "tendency_to_punch": 0.0,
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
        player.fitness = clamp(player.fitness + 20 + fitness_coach / 14.0, 0, 100)
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
        player.fitness = clamp(player.fitness + 4, 0, 100)
        new_badges = min(4, int(player.coaching // 22))
        if new_badges > player.badges:
            player.badges = new_badges
            messages.append(f"🎓 השלמת תעודת אימון רמה {player.badges}!")
        return messages

    if focus == "media":
        player.media_skill = clamp(player.media_skill + 0.9 * intensity, 0, 100)
        gain_reputation(player, 0.25)
        player.fitness = clamp(player.fitness + 3, 0, 100)
        return messages

    if focus == "business":
        player.business = clamp(player.business + 0.85 * intensity, 0, 100)
        player.fitness = clamp(player.fitness + 3, 0, 100)
        return messages

    # אימון תכונה. האימון עולה כושר — הוא לא מחזיר אותו.
    # ההתאוששות עצמה קורית ב-weekly_recovery, פעם אחת בשבוע, לכולם.
    player.fitness = clamp(player.fitness - (2.5 + 5.0 * intensity), 0, 100)
    if player.injury_weeks > 0:
        player.injury_weeks = max(0, player.injury_weeks - 1)
        return ["🩹 אתה בשיקום — האימון היה קל בהרבה."]

    gap = player.potential - player.overall
    curve = age_factor(player.age)
    base = 0.178 * intensity
    base *= 0.55 + facilities / 110.0
    base *= 1.0 + assistant / 420.0          # עוזר מאמן — עד 23% יותר
    base *= max(0.15, curve)
    base *= 1.0 + clamp(gap, -10, 18) * 0.032
    if player.has_trait("workhorse"):
        base *= 1.30
    base *= 0.75 + player.morale / 200.0
    # אישיות: מקצוענות ונחישות הן ההבדל בין כישרון שהתממש לכזה שלא
    base *= personality_effect(player)[0]
    base *= 0.55 + player.detail.get("determination", 10) / 22.0
    base *= rng.uniform(0.7, 1.35)

    # ככל שמתקרבים לתקרת הפוטנציאל, ההתקדמות נעצרת כמעט לגמרי
    headroom = player.potential - player.overall
    if headroom <= 0:
        base *= 0.06
    elif headroom < 6:
        base *= 0.20 + headroom * 0.13

    messages.extend(_train_detail(player, focus, base, rng,
                                  full=player.is_human))

    # עבודת כוח בונה גוף שנשבר פחות. זו הידית שמאפשרת לחזק שחקן פציע.
    if focus in ("physical", "strength", "stamina", "natural_fitness", "balance"):
        player.resilience = clamp(player.resilience + 0.22 * intensity, 0, 96)
    elif focus in ("pace", "acceleration", "agility"):
        player.resilience = clamp(player.resilience + 0.07 * intensity, 0, 96)
    player.sharpness = clamp(player.sharpness - 0.5, 0, 100)

    # אימון אינטנסיבי מסוכן
    injury_chance = (0.022 * intensity * player.injury_risk
                     * (1.0 - fitness_coach / 260.0))
    if intensity > 1.15 and rng.random() < injury_chance:
        weeks = rng.randint(1, 3)
        player.injury_weeks = weeks
        player.injury_name = "עומס יתר באימון"
        messages.append(f"🚑 נמתחת באימון — {weeks} שבועות בחוץ.")
    return messages


# תכונות מומחיות: משתפרות רק כשמתאמנים עליהן ישירות. אף אחד לא נעשה
# בועט חופשיות טוב יותר מזה שהוא רץ ספרינטים.
SET_PIECE_ATTRS = {"corners", "free_kick", "penalty_taking", "long_throws",
                   "eccentricity", "tendency_to_punch"}

_SHARES_CACHE: Dict[tuple, Dict[str, float]] = {}


def training_shares(player: Player, focus: str) -> Dict[str, float]:
    """כמה מהאימון הולך לכל תכונה מפורטת.

    שלוש שכבות, בדיוק כמו לוח אימונים אמיתי: מה שביקשת לעבוד עליו,
    מה שנמצא לידו (אותה קבוצה, ובעיקר מה שהתפקיד שלך דורש), וכל השאר —
    כי גוף של בן שבע־עשרה מתפתח גם בלי שתכוון אליו.
    """
    cached = _SHARES_CACHE.get((player.position, player.role, focus))
    if cached is not None:
        return cached

    allowed = [a for a in D.attrs_for(player.position)]
    shares: Dict[str, float] = {}
    row = D.ROLE_BY_KEY.get(player.role)
    role_attrs = set(row[4]) | set(row[5]) if row else set()

    for attr in allowed:
        weight = D.GENERAL_SHARE
        if attr in role_attrs:
            weight *= 2.1        # התפקיד מכתיב על מה עובדים גם באימון כללי
        if attr in SET_PIECE_ATTRS:
            weight *= 0.18       # בעיטות חופשיות לא משתפרות מריצות
        shares[attr] = weight

    if focus in D.DETAIL_NAMES_HE:
        # מיקוד בתכונה אחת: היא מקבלת את רוב העבודה, שכנותיה בקבוצה חלק
        group = D.DETAIL_GROUP.get(focus)
        for attr in allowed:
            if attr != focus and D.DETAIL_GROUP.get(attr) == group:
                spill = 0.9 if attr in role_attrs else 0.28
                if attr in SET_PIECE_ATTRS:
                    spill = 0.08
                shares[attr] += D.SPILL_SHARE * spill
        shares[focus] = shares.get(focus, 0.0) + 3.4
        _SHARES_CACHE[(player.position, player.role, focus)] = shares
        return shares

    # מיקוד בקבוצה מהשבע הישנות — מתפזר על כל מרכיביה לפי משקלן
    members = (D.GROUP_MAP_GK if player.position == "GK" else D.GROUP_MAP).get(focus)
    if members:
        total = sum(members.values()) or 1.0
        for attr, share in members.items():
            if attr in shares:
                shares[attr] += 1.6 * (share / total) * len(members) / 2.0
    _SHARES_CACHE[(player.position, player.role, focus)] = shares
    return shares


def _train_detail(player: Player, focus: str, base: float,
                  rng: random.Random, full: bool = True) -> List[str]:
    """מריץ שבוע אימון על התכונות המפורטות ומחזיר את מה שהשתפר.

    ``full=False`` מריץ רק את התכונות שבאמת נושאות משקל — מסלול
    לשחקני המחשב, שרצים 1,400 בשבוע ולא צריכים את הרזולוציה המלאה.
    """
    shares = training_shares(player, focus)
    if not full:
        shares = dict(sorted(shares.items(), key=lambda kv: -kv[1])[:10])
    # נקודת הייחוס לבלם ההתמחות היא הרמה הממוצעת שלך בפועל
    levels = [player.detail.get(a, 10) for a in shares]
    average = sum(levels) / len(levels) if levels else 10.0

    # עבודה שמכוונת לתכונה שכבר בתקרה לא מתאדה — היא עוברת הלאה.
    # שחקן שהסיום שלו 20 לא מפסיק להשתפר, הוא פשוט משתפר בדברים
    # אחרים; בלי זה שבוע אימון של שחקן בוגר פשוט לא עושה כלום.
    shares = _spill_from_capped(player, shares)

    gains: Dict[str, int] = {}
    for attr, share in shares.items():
        level = player.detail.get(attr, 10)
        # base מכויל בסולם 1-100 של הקבוצות; התכונות הן 1-20
        step = (base * share * detail_damper(level, average)
                * ceiling_damper(level) / 5.0)
        got = add_detail(player, attr, step)
        if got:
            gains[attr] = gains.get(attr, 0) + got
    if not gains:
        return []
    parts = [f"{D.DETAIL_NAMES_HE[a]} ל-{player.detail[a]}" for a in gains]
    return ["📈 " + ", ".join(parts) + "."]


def _spill_from_capped(player: Player, shares: Dict[str, float]) -> Dict[str, float]:
    """מעביר את חלקן של תכונות שבתקרה לשכנותיהן באותה קבוצה.

    בלי זה, שחקן שמיצה את התכונות שהאימון שלו מכוון אליהן מגלה
    שהאימון הפסיק לעשות משהו — בלי הסבר ובלי דרך לצאת מזה.
    """
    capped = {a: w for a, w in shares.items()
              if player.detail.get(a, 10) >= D.MAX_DETAIL and w > 0}
    if not capped:
        return shares
    out = {a: w for a, w in shares.items() if a not in capped}
    for attr, weight in capped.items():
        group = D.DETAIL_GROUP.get(attr)
        targets = [a for a in out
                   if D.DETAIL_GROUP.get(a) == group
                   and player.detail.get(a, 10) < D.MAX_DETAIL]
        if not targets:                       # כל הקבוצה מיצתה — לכל השאר
            targets = [a for a in out if player.detail.get(a, 10) < D.MAX_DETAIL]
        if not targets:
            continue
        # לא במלואו: אימון מוסט הוא פחות יעיל מאימון מכוון
        share = weight * 0.6 / len(targets)
        for target in targets:
            out[target] = out.get(target, 0.0) + share
    return out


def capped_attrs(player: Player) -> List[str]:
    """התכונות שכבר אי אפשר לשפר. מה שהמסך צריך כדי להגיד את זה."""
    return [a for a, v in player.detail.items() if v >= D.MAX_DETAIL]


def ceiling_damper(level: float) -> float:
    """בולם ככל שמתקרבים ל-20.

    זה מה שהיה חסר: בלי הבלם הזה תכונה עולה בקצב אחיד עד שהיא נתקעת
    בקיר של 20 — ואז נעצרת בבת אחת, בלי אזהרה. בכדורגל אמיתי ההפך
    נכון: ככל שאתה טוב יותר, כל שיפור נוסף יקר יותר. 20 הוא הישג של
    קריירה בתכונה אחת או שתיים, לא מצב שמגיעים אליו בעשר תכונות בגיל
    עשרים ושש.
    """
    if level < 16.0:
        return 1.0
    # 16 → 1.0,  17 → 0.64,  18 → 0.35,  19 → 0.14,  20 → 0.02
    # מתחת ל-16 אין בלם בכלל: זו עדיין רמה שאפשר להגיע אליה באימון
    # רגיל, ובלימה שם רק מאטה קריירה שלמה בלי לפתור כלום.
    return max(0.05, 1.0 - (level - 16.0) * 0.22) ** 1.8


def detail_damper(level: float, average: float) -> float:
    """בולם תכונה מפורטת שרצה הרחק מכל השאר.

    אפשר להיות מצוין בדבר אחד, אבל לא לפתח סיום 20 עם גוף של ילד:
    ככל שהפער מהרמה הכללית גדל, כל נקודה נוספת נעשית יקרה יותר.
    """
    gap = level - average
    if gap <= 4.0:
        return 1.0
    return max(0.25, 1.0 - (gap - 4.0) * 0.14)


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
    """התאוששות טבעית בסוף שבוע. מרכז רפואי וצוות מקצרים שיקום.

    זו נקודת ההתאוששות היחידה, והיא רצה גם בשבוע שבו שיחקת: גוף של
    מקצוען חוזר לעצמו בין משחק למשחק. בלי זה הכושר נשחק לאורך העונה
    עד שהמאמן לא מבקש ממך יותר כלום חוץ ממנוחה.
    """
    care = medical_care(club)
    fitness_coach = club.staff_quality("fitness") if club else 0
    if player.injury_weeks > 0:
        player.injury_weeks -= 1
        if player.injury_weeks > 0 and rng.random() < (care - 0.45) * 0.55:
            player.injury_weeks -= 1        # טיפול טוב חוסך עוד שבוע
        if player.injury_weeks == 0:
            player.injury_name = ""
            player.fitness = clamp(player.fitness + 15, 0, 100)

    recover = 11.0 + fitness_coach / 12.0 + care * 5.0
    recover *= 1.06 - min(0.30, max(0, player.age - 29) * 0.028)   # ותיקים חוזרים לאט
    if played:
        player.sharpness = clamp(player.sharpness + 5.5, 0, 100)
    else:
        recover += 4.0
        player.sharpness = clamp(player.sharpness - 1.1, 0, 100)
    player.fitness = clamp(player.fitness + recover, 0, 100)
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
        player.fitness = clamp(player.fitness + rng.uniform(13, 24), 0, 100)
        # חדות משחק אצל שחקני מחשב מתכנסת לרמת "בתוך סגל" — בלי זה
        # כל הליגה הייתה נכנסת למשחקים בלי דקות ברגליים, ושילמה על כך
        target = 92.0 if player.club_id else 45.0
        player.sharpness = clamp(player.sharpness + (target - player.sharpness) * 0.22
                                 + rng.uniform(-2.0, 2.0), 0, 100)
        if rng.random() < 0.55:
            focus = rng.choice(D.ATTRIBUTES)
            weekly_training(player, focus, club, rng, intensity=0.85)


# ---------------------------------------------------------------------------
# הערכה מחדש באמצע עונה — רק לצעירים
# ---------------------------------------------------------------------------

REASSESS_EVERY = 10      # שבועות
REASSESS_UNTIL = 18      # גיל


def reassess_youngster(player: Player, rng: random.Random,
                       club: Optional[Club] = None) -> Optional[str]:
    """מרענן את הערכת הפוטנציאל של נער באמצע העונה.

    למה זה קיים: הערכת הפוטנציאל התעדכנה פעם בשנה, ונער מוכשר גדל
    תשע נקודות דירוג באותה שנה. התוצאה הייתה שהדירוג עוקף את ההערכה,
    המרווח ביניהם מתאפס, והבלם שמאט ליד תקרת הפוטנציאל חונק את
    ההתפתחות — בדיוק בגיל 16-17. נמדד: המרווח נפל מ-8.2 ל-2.0 והבלם
    מ-0.90 ל-0.37, בזמן שעקומת הגיל ירדה ב-8% בלבד.

    בעולם האמיתי אף אחד לא מחכה לסוף העונה כדי לעדכן דעה על ילד בן
    ארבע־עשרה. מרימים את ההערכה תוך כדי, בצעדים קטנים.

    רק מעלה, לעולם לא מוריד: ירידה היא החלטה של סוף עונה, עם עונה
    שלמה מאחוריה.
    """
    if player.age > REASSESS_UNTIL:
        return None
    room = player.ceiling - player.potential
    if room <= 0:
        return None
    # כמה קרוב הדירוג לנשוך את ההערכה
    headroom = player.potential - player.overall
    if headroom > 7:
        return None                     # יש עוד מרווח — אין מה למהר

    grow = max(0.0, 7 - headroom) * 0.42
    grow *= 0.55 + (club.training_facilities if club else 50) / 145.0
    grow *= 0.75 + player.detail.get("determination", 10) / 26.0
    grow *= rng.uniform(0.7, 1.3)
    gained = int(round(grow))
    if gained <= 0:
        return None
    before = player.potential
    player.potential = int(clamp(player.potential + gained,
                                 player.overall, player.ceiling))
    if player.potential <= before:
        return None
    return (f"📋 בדוח האמצע כתבו עליך אחרת. ההערכה עלתה "
            f"ל-{player.potential}.")


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
        return _push_ceiling(player, rng, quality)

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


# התקרה המוחלטת. 95 נקבע בלידה; מעבר לזה מגיעים רק בהוכחה על הדשא.
ABSOLUTE_CEILING = 99


def _push_ceiling(player: Player, rng: random.Random,
                  quality: float) -> Optional[str]:
    """עונה יוצאת דופן דוחפת את התקרה עצמה, לא רק את ההערכה.

    בלי זה, שחקן שמיצה את התקרה שנקבעה לו בהגרלה בגיל שבע־עשרה מגלה
    שנשארו לו עשרים שנות קריירה שבהן שום דבר לא זז — לא משנה כמה טוב
    הוא משחק. תקרה היא הערכה של העולם, ומי שמנפץ אותה עונה אחרי עונה
    אמור לגרום לעולם לעדכן אותה.

    זה יקר בכוונה: צריך עונה מצוינת ממש, וזה מזיז נקודה אחת.
    """
    if player.ceiling >= ABSOLUTE_CEILING or player.age > 32:
        return None
    if quality < 0.42:                # עונה טובה לא מספיקה — צריך יוצאת דופן
        return None
    chance = 0.55 if player.age <= 24 else 0.30
    if player.has_trait("workhorse"):
        chance += 0.12
    chance *= personality_effect(player)[0]
    if rng.random() > chance:
        return None
    player.ceiling = int(min(ABSOLUTE_CEILING, player.ceiling + 1))
    player.potential = int(clamp(player.potential + 1, player.overall,
                                 player.ceiling))
    return (f"🌟 עברת את מה שחשבו שאתה מסוגל לו. התקרה שלך עלתה "
            f"ל-{player.ceiling}.")


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
    # הגוף גדל באמת, ולא רק "כאילו"
    body = grow_body(player, rng)
    if body and player.is_human:
        messages.append(body)
    curve = age_factor(player.age)

    # דקות משחק מאיצות התפתחות של צעירים
    exposure = 0.45 + minutes_share * 1.1
    for attr in D.attrs_for(player.position):
        sensitivity = DETAIL_DECLINE.get(attr, 0.6)
        if curve > 0:
            # קפיצת הקיץ אמיתית אבל לא דרמטית — רוב ההתפתחות היא באימונים
            delta = curve * exposure * rng.uniform(0.4, 1.5) * 0.45
            if player.overall >= player.potential:
                delta *= 0.08
        else:
            delta = curve * max(0.2, sensitivity) * rng.uniform(0.5, 1.5)
        add_detail(player, attr, delta / 5.0)

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
