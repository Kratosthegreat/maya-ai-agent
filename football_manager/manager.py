"""
המאמן של הקבוצה.

עד עכשיו הוא היה שם ושדה אמון. כאן הוא הופך לדמות שמדברת אליך אחרי
כל משחק, דורשת ממך דברים בשבוע, ומסבירה למה אתה בהרכב או מחוצה לו.

לכל מאמן יש אופי, והאופי קובע מה מרגיז אותו ומה משכנע אותו.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

from . import data as D
from .models import Club, Player, clamp

# (מפתח, שם בעברית, תיאור, רגישות אמון, סבלנות לתקשורת, נטייה לרוטציה)
STYLES = [
    ("disciplinarian", "איש משמעת",
     "אצלו מגיעים ראשונים לאימון ועונים אחרונים לתקשורת.", 1.35, 0.55, 0.9),
    ("man_manager", "מאמן של שחקנים",
     "מדבר איתך, לא עליך. סולח יותר, מצפה יותר.", 0.85, 1.25, 1.0),
    ("tactician", "טקטיקן",
     "מה שמעניין אותו זה אם עמדת נכון, לא כמה רצת.", 1.05, 0.9, 1.15),
    ("rotator", "מסובב סגל",
     "מאמין שכל אחד מקבל דקות — וגם מאבד אותן.", 0.95, 1.05, 1.6),
]


def _hash(text: str) -> int:
    value = 2166136261
    for ch in text:
        value ^= ord(ch)
        value = (value * 16777619) & 0xFFFFFFFF
    return value


def style_of(club: Optional[Club]) -> Tuple[str, str, str, float, float, float]:
    """אופי המאמן — נגזר מהשם, ולכן קבוע לכל אורך הכהונה שלו."""
    if not club or not club.manager_name:
        return STYLES[1]
    return STYLES[_hash(club.manager_name) % len(STYLES)]


# ---------------------------------------------------------------------------
# הוראה שבועית
# ---------------------------------------------------------------------------

DIRECTIVE_TEXT = {
    "pace": "רוצה אותך מהיר יותר בחמישה המטרים הראשונים.",
    "shooting": "אמר שאתה מבזבז מצבים. השבוע — סיומות.",
    "passing": "רוצה שתפסיק לאבד כדורים במסירה הראשונה.",
    "dribbling": "אמר שאתה מוסר מוקדם מדי. שיחקק אחד על אחד.",
    "defending": "דורש שתחזור אחורה. גם חלוץ מגן.",
    "physical": "שלח אותך לחדר הכושר. אמר שאתה נדחף מהכדור.",
    "mental": "רוצה אותך בחדר הווידאו. אתה קורא את המשחק לאט.",
    "rest": "אמר לך לנוח. הוא רואה שאתה שרוף.",
}


def weekly_directive(game, rng: random.Random) -> Optional[str]:
    """מה המאמן רוצה ממך השבוע. None כשאין לו מה להגיד."""
    club = game.my_club
    me = game.me
    if not club or game.stage not in ("academy", "player", "veteran"):
        return None

    # הוא מגיב למה שבאמת חסר לך, לא באקראי
    if me.fitness < 55:
        return "rest"
    weights = D.POSITION_WEIGHTS[me.position]
    gaps = sorted(D.ATTRIBUTES,
                  key=lambda a: me.attributes.get(a, 50) - weights.get(a, 0.1) * 120)
    pool = gaps[:3]
    return rng.choice(pool)


def directive_line(club: Optional[Club], focus: str) -> str:
    name = club.manager_name if club else "המאמן"
    return f"🎙️ {name} {DIRECTIVE_TEXT.get(focus, 'רוצה אותך באימון נוסף.')}"


# ---------------------------------------------------------------------------
# תגובה אחרי משחק
# ---------------------------------------------------------------------------

def post_match_line(game, rating: Optional[float], outcome: str,
                    played: bool, rng: random.Random) -> Optional[str]:
    """מה המאמן אמר לך אחרי המשחק."""
    club = game.my_club
    if not club:
        return None
    key, style_he, _, sensitivity, _, _ = style_of(club)
    name = club.manager_name
    trust = club.manager_trust

    if not played:
        if trust < 35:
            return f"🎙️ {name} עבר לידך בחדר ההלבשה ולא עצר."
        if rng.random() < 0.5:
            return f"🎙️ {name}: \"תמשיך לעבוד. אני רואה אותך.\""
        return None

    if rating is None:
        return None

    if rating >= 8.0:
        pool = [f"🎙️ {name}: \"זה מה שחיפשתי ממך. עוד כאלה.\"",
                f"🎙️ {name} תפס אותך במנהרה ואמר רק: \"מצוין.\""]
        if key == "disciplinarian":
            pool.append(f"🎙️ {name}: \"טוב. אל תתאהב בעצמך.\"")
    elif rating >= 6.8:
        pool = [f"🎙️ {name}: \"עבודה טובה. תשמור על הרמה.\"",
                f"🎙️ {name} הנהן לכיוונך. זה הרבה, ממנו."]
    elif rating >= 6.0:
        pool = [f"🎙️ {name}: \"בסדר. לא יותר מזה.\"",
                f"🎙️ {name} לא אמר כלום, וזה נשמע חזק."]
    else:
        pool = [f"🎙️ {name}: \"מה זה היה? אנחנו נדבר מחר.\"",
                f"🎙️ {name} החליף אותך והסתכל עליך כל הדרך לספסל."]
        if key == "man_manager":
            pool = [f"🎙️ {name}: \"יום קשה. קורה. מחר מתחילים מחדש.\""]

    if outcome == "L" and rating < 6.5 and key == "disciplinarian":
        pool.append(f"🎙️ {name} ביטל את יום החופש של כל הקבוצה.")
    return rng.choice(pool)


# ---------------------------------------------------------------------------
# למה אתה בהרכב, או למה לא
# ---------------------------------------------------------------------------

def selection_note(game) -> Optional[str]:
    """הסבר מה עומד בינך לבין ההרכב הפותח."""
    club = game.my_club
    me = game.me
    if not club or game.stage not in ("academy", "player", "veteran"):
        return None
    if not me.available:
        return f"🚑 {me.injury_name} — {me.injury_weeks} שבועות. לא רלוונטי להרכב."

    rivals = [game.players[p] for p in club.squad
              if p != game.me_id and p in game.players
              and game.players[p].available
              and game.players[p].position == me.position]
    best = max((p.effective for p in rivals), default=0.0)
    mine = me.effective + (club.manager_trust - 50) * 0.14
    if game.flag("captain"):
        mine += 4
    gap = mine - best
    name = club.manager_name

    if gap >= 6:
        return f"✅ אתה הבחירה הראשונה של {name} בעמדה."
    if gap >= -1:
        return f"⚖️ אתה והמתחרה שלך צמודים. כל משחק גרוע יעלה לך את המקום."
    rival = max(rivals, key=lambda p: p.effective, default=None)
    if rival is not None:
        return (f"⛔ {rival.name} ({rival.overall}) לפניך בתור. "
                f"צריך {abs(gap):.0f} נקודות של פער כדי לעקוף אותו.")
    return None


def trust_move(club: Optional[Club], delta: float) -> float:
    """שינוי אמון מותאם לאופי המאמן."""
    if not club:
        return 0.0
    sensitivity = style_of(club)[3]
    club.manager_trust = clamp(club.manager_trust + delta * sensitivity, 0, 100)
    return club.manager_trust
