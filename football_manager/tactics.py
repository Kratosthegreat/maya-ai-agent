# -*- coding: utf-8 -*-
"""
football_manager.tactics
========================
הטקטיקה של המאמן, ומה היא עושה לך.

עד עכשיו הטקטיקה הייתה משהו שקרה מעליך: מערך ומנטליות שנכנסו
לסימולציה ונעלמו. במקור זה מה שקובע איך נראות תשעים הדקות שלך —
כמה תיגע בכדור, כמה תרוץ, כמה תאבד, וכמה פעמים תגיע למצב.

לכל מאמן סגנון שנגזר משמו, ולכן קבוע לכל אורך כהונתו. אתה יכול
לקרוא אותו במסך הטקטיקה, ולהבין למה השבוע אתה מרגיש אחרת.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

from . import data as D
from .models import Club, Player, clamp, role_row


def _hash(text: str) -> int:
    value = 2166136261
    for ch in text:
        value ^= ord(ch)
        value = (value * 16777619) & 0xFFFFFFFF
    return value


def style_of(club: Optional[Club]) -> tuple:
    """הסגנון הטקטי של המועדון — נגזר משם המאמן, ולכן קבוע."""
    if not club or not club.manager_name:
        return D.STYLE_BY_KEY["balanced_style"]
    index = (_hash(club.manager_name + "tactics") % len(D.TACTICAL_STYLES))
    return D.TACTICAL_STYLES[index]


def instructions(club: Optional[Club]) -> Dict[str, int]:
    """שבע ההוראות שהמאמן משחק איתן השבוע.

    בסיס הסגנון, ועליו התאמות למצב: קבוצה שמפחדת יורדת אחורה, קבוצה
    בטוחה בעצמה עולה. זה גם מה שגורם לאותו מאמן להרגיש אחרת בינואר.
    """
    style = style_of(club)
    values = dict(style[2])
    if club:
        if club.board_confidence < 35:
            values["mentality"] = int(clamp(values["mentality"] - 1, -2, 2))
            values["d_line"] = int(clamp(values["d_line"] - 1, -2, 2))
        elif club.board_confidence > 75:
            values["mentality"] = int(clamp(values["mentality"] + 1, -2, 2))
        if club.reputation < 40:
            values["passing"] = int(clamp(values["passing"] + 1, -2, 2))
            values["pressing"] = int(clamp(values["pressing"] - 1, -2, 2))
    return values


def describe(club: Optional[Club]) -> List[str]:
    """איך נראית הטקטיקה, בשורות שאפשר לקרוא."""
    style = style_of(club)
    values = instructions(club)
    lines = [f"{style[1]} — {style[3]}"]
    for key in D.INSTRUCTION_KEYS:
        label = D.TEAM_INSTRUCTIONS[key][0]
        lines.append(f"{label}: {D.instruction_label(key, values[key])}")
    return lines


# ---------------------------------------------------------------------------
# מה זה עושה לך במגרש
# ---------------------------------------------------------------------------

def match_modifiers(club: Optional[Club], player: Player) -> Dict[str, float]:
    """מכפילים לשורת הסטטיסטיקה שלך, לפי הטקטיקה של המועדון והתפקיד."""
    return modifiers_from(instructions(club), player)


def modifiers_from(values: Dict[str, int], player: Player) -> Dict[str, float]:
    """מכפילים לשורת הסטטיסטיקה, מתוך ערכי הוראות מפורשים.

    זה הלב: קבוצה שמשחקת קצר תיתן לך יותר נגיעות ואחוז מסירה גבוה
    יותר; קבוצה ישירה תיתן לך פחות מסירות אבל יותר מצבים; לחיצה
    גבוהה תעלה לך בריצה ותוסיף חטיפות. אתה מרגיש את הטקטיקה בגוף.
    """
    row = role_row(player.role)
    duty_def, duty_att, duty_run = D.DUTY_SHIFT.get(player.duty, (0.0, 0.0, 0.0))

    tempo = values["tempo"] / 2.0
    width = values["width"] / 2.0
    directness = values["passing"] / 2.0
    press = values["pressing"] / 2.0
    line = values["d_line"] / 2.0
    mentality = values["mentality"] / 2.0

    mods = {
        # קצב גבוה ומשחק ישיר = פחות מסירות, יותר איבודים, יותר ריצה
        "passes": 1.0 - directness * 0.26 - tempo * 0.10,
        "pass_pct": 1.0 - directness * 0.09 - tempo * 0.04,
        "losses": 1.0 + directness * 0.22 + tempo * 0.14 - press * 0.05,
        # התקפיות ורוחב פותחים מצבים
        "shots": 1.0 + mentality * 0.20 + duty_att * 0.9,
        "key_passes": 1.0 + mentality * 0.14 + width * 0.10 + duty_att * 0.6,
        "dribbles": 1.0 + width * 0.12 - directness * 0.14,
        # לחיצה וקו גבוה = חטיפות וריצה
        "tackles": 1.0 + press * 0.30 + line * 0.10 + duty_def * 1.0,
        "duels": 1.0 + press * 0.18 + directness * 0.12,
        "sprints": 1.0 + tempo * 0.22 + press * 0.24 + duty_run * 1.2,
        "distance": 1.0 + tempo * 0.09 + press * 0.13 + duty_run * 0.5,
        "reads": 1.0 + (1.0 - abs(mentality)) * 0.05 - press * 0.04,
    }
    if row:
        # התפקיד עצמו מטה את הפרופיל — כנף מרימה, חלוץ בור בועט
        key_attrs = set(row[4])
        if "crossing" in key_attrs:
            mods["key_passes"] *= 1.25
        if "finishing" in key_attrs:
            mods["shots"] *= 1.30
        if "tackling" in key_attrs or "marking" in key_attrs:
            mods["tackles"] *= 1.28
        if "passing" in key_attrs or "vision" in key_attrs:
            mods["passes"] *= 1.22
            mods["key_passes"] *= 1.15
        if "dribbling" in key_attrs:
            mods["dribbles"] *= 1.30
        if "stamina" in key_attrs or "work_rate" in key_attrs:
            mods["distance"] *= 1.12
            mods["sprints"] *= 1.12
        if "off_the_ball" in key_attrs:
            mods["shots"] *= 1.12
            mods["sprints"] *= 1.08
    for key in mods:
        mods[key] = clamp(mods[key], 0.35, 2.4)
    return mods


def fitness_cost(club: Optional[Club], player: Player) -> float:
    """כמה הטקטיקה הזאת שוחקת אותך. גגנפרסינג עולה בגוף."""
    values = instructions(club)
    _def, _att, run = D.DUTY_SHIFT.get(player.duty, (0.0, 0.0, 0.0))
    load = 1.0 + values["pressing"] * 0.09 + values["tempo"] * 0.06 + run * 0.8
    stamina = player.detail.get("stamina", 10)
    natural = player.detail.get("natural_fitness", 10)
    load *= 1.24 - (stamina + natural) / 2.0 * 0.024
    return clamp(load, 0.6, 1.7)


def suits_player(club: Optional[Club], player: Player) -> Tuple[float, str]:
    """כמה הסגנון של המועדון מתאים לך, ולמה."""
    return suits_values(instructions(club), player)


def suits_values(values: Dict[str, int], player: Player) -> Tuple[float, str]:
    """כמה סגנון נתון מתאים לשחקן.

    זה מה שהופך מעבר מועדון להחלטה: אותו שחקן בדיוק יזרח אצל מאמן
    אחד וייעלם אצל אחר.
    """
    detail = player.detail
    score = 50.0
    notes: List[str] = []

    pace = (detail.get("acceleration", 10) + detail.get("pace", 10)) / 2.0
    tech = (detail.get("technique", 10) + detail.get("first_touch", 10)) / 2.0
    engine = (detail.get("stamina", 10) + detail.get("work_rate", 10)) / 2.0
    brain = (detail.get("decisions", 10) + detail.get("vision", 10)) / 2.0

    if values["tempo"] >= 1 or values["pressing"] >= 1:
        score += (engine - 11) * 4.4
        notes.append("קצב ולחיצה — צריך ריאות" if engine < 11
                     else "הקצב הזה בנוי בשבילך")
    if values["passing"] <= -1:
        score += (tech - 11) * 4.2
        notes.append("משחק קצר — הכול עובר בנגיעה" if tech >= 11
                     else "משחק קצר, והנגיעה שלך עוד לא שם")
    if values["passing"] >= 1:
        score += (pace - 11) * 3.8
        notes.append("כדורים לעומק — בשביל זה צריך רגליים" if pace >= 11
                     else "הם משחקים ארוך, ואתה לא הכי מהיר")
    if values["mentality"] <= -1:
        score += (brain - 11) * 3.0
        notes.append("קבוצה שמחכה — הסבלנות שלך נמדדת")
    return clamp(score, 0, 100), (notes[0] if notes else "סגנון שלא מושך לשום קיצון")


def role_fit_note(player: Player) -> Optional[str]:
    """האם התפקיד שנתנו לך הוא באמת שלך."""
    from .models import best_role, role_suitability
    if not player.role:
        return None
    mine = role_suitability(player, player.role)
    best_key, best_score = best_role(player)
    row = role_row(player.role)
    if not row:
        return None
    if best_key == player.role or best_score - mine < 5:
        return f"✅ {row[1]} — זה התפקיד שמוציא ממך את המקסימום."
    best_row = role_row(best_key)
    return (f"↔️ אתה משחק {row[1]} ({mine:.0f}), אבל התכונות שלך אומרות "
            f"{best_row[1]} ({best_score:.0f}).")


# ---------------------------------------------------------------------------
# מי מחלק את התפקידים
# ---------------------------------------------------------------------------

def assign_role(player: Player, club: Optional[Club], rng: random.Random) -> str:
    """המאמן נותן לך תפקיד. לרוב הנכון — לא תמיד.

    מאמן טוב קורא את התכונות שלך; מאמן שהמערכת שלו קודמת לך ישים
    אותך במה שהוא צריך. זה מקור אמיתי לתסכול, ולכן גם לסיפור.
    """
    from .models import best_role, role_suitability
    options = D.roles_for(player.position)
    if not options:
        return ""
    style = style_of(club)
    scored = []
    for row in options:
        score = role_suitability(player, row[0])
        # מאמן משבץ לפי הסגנון שלו, לא רק לפי מי שאתה
        key_attrs = set(row[4])
        if style[0] == "gegenpress" and ("work_rate" in key_attrs
                                         or "stamina" in key_attrs
                                         or "aggression" in key_attrs):
            score += 9
        if style[0] == "tiki_taka" and ("passing" in key_attrs
                                        or "vision" in key_attrs
                                        or "technique" in key_attrs):
            score += 9
        if style[0] == "counter" and ("acceleration" in key_attrs
                                      or "pace" in key_attrs
                                      or "off_the_ball" in key_attrs):
            score += 9
        if style[0] == "wing_play" and ("crossing" in key_attrs
                                        or "heading" in key_attrs):
            score += 9
        if style[0] == "catenaccio" and ("marking" in key_attrs
                                         or "positioning" in key_attrs
                                         or "tackling" in key_attrs):
            score += 9
        scored.append((score + rng.uniform(-4, 4), row))
    scored.sort(key=lambda pair: -pair[0])
    chosen = scored[0][1]
    return chosen[0]


def duty_for(role_key: str, club: Optional[Club], rng: random.Random) -> str:
    """החובה נגזרת מהתפקיד ומהמנטליות של הקבוצה."""
    row = D.ROLE_BY_KEY.get(role_key)
    if not row:
        return "support"
    duties = row[3]
    if len(duties) == 1:
        return duties[0]
    mentality = instructions(club)["mentality"]
    order = {"attack": 2, "support": 0, "automatic": 0,
             "defend": -2, "cover": -2, "stopper": -1}
    wanted = clamp(mentality, -2, 2)
    ranked = sorted(duties, key=lambda d: abs(order.get(d, 0) - wanted))
    return ranked[0] if rng.random() < 0.75 else rng.choice(duties)


def request_role(game, role_key: str) -> str:
    """לבקש מהמאמן תפקיד אחר. הוא לא חייב להסכים."""
    from .models import role_suitability
    me = game.me
    club = game.my_club
    row = D.ROLE_BY_KEY.get(role_key)
    if not row or me.position not in row[2]:
        return "זה לא תפקיד שאפשר למלא בעמדה שלך."
    if role_key == me.role:
        return f"אתה כבר משחק {row[1]}."
    if not club:
        me.role = role_key
        return f"מהיום אתה {row[1]}."

    fit = role_suitability(me, role_key)
    current = role_suitability(me, me.role) if me.role else 0.0
    trust = club.manager_trust
    chance = 0.16 + trust / 190.0 + max(0.0, fit - current) / 90.0
    if game.rng.random() < clamp(chance, 0.05, 0.9):
        me.role = role_key
        me.duty = duty_for(role_key, club, game.rng)
        club.manager_trust = clamp(trust - 3, 0, 100)
        return (f"✅ {club.manager_name} הסכים. מהשבוע אתה {row[1]} "
                f"({D.DUTY_NAMES_HE.get(me.duty, '')}).")
    club.manager_trust = clamp(trust - 5, 0, 100)
    return (f"⛔ {club.manager_name} שמע ואמר שהוא לא משנה מערכת בשביל "
            "שחקן אחד. השיחה הזאת לא עזרה לך.")
