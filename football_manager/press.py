# -*- coding: utf-8 -*-
"""
football_manager.press
======================
עיתונות, טלוויזיה ושמועות.

במשחק ניהול אמיתי אתה לא לומד על עצמך מטבלה — אתה לומד מהעיתון. מישהו
כותב שקבוצה מתעניינת בך לפני שהיא פונה, פרשן אומר במשדר שאתה לא בכושר,
"מקורות יודעי דבר" מדליפים שהמאמן איבד בך אמון. חלק מזה נכון.

וזה העיקר כאן: **לא כל שמועה נכונה.** לכל מקור יש אמינות, ואתה רואה
אותה — אבל לא רואה את התשובה. תחקירן ותיק שכותב שיש הצעה מחו"ל צודק
כמעט תמיד; חשבון אוהדים שכותב את אותו דבר צודק במקרה. מה אתה עושה עם
זה — מכחיש, מאשר, או שותק — זו החלטה עם מחיר.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from . import data as D
from .models import Player, clamp, gain_reputation

# מקור, אמינות (0-1), ותווית תצוגה
SOURCES = [
    ("insider", "תחקירן ההעברות", 0.88, "📰"),
    ("tv", "פרשן הערוץ", 0.74, "📺"),
    ("beat", "כתב המועדון", 0.70, "🖊"),
    ("sources", "מקורות יודעי דבר", 0.52, "🕵"),
    ("radio", "תוכנית הרדיו", 0.44, "📻"),
    ("tabloid", "העיתון הצהוב", 0.26, "🗞"),
    ("fan", "חשבון אוהדים ברשת", 0.20, "📱"),
]
SOURCE_NAMES = {key: name for key, name, _, _ in SOURCES}
SOURCE_TRUST = {key: trust for key, _, trust, _ in SOURCES}
SOURCE_ICON = {key: icon for key, _, _, icon in SOURCES}

TRUST_WORDS = [
    (0.80, "מקור אמין מאוד"),
    (0.62, "בדרך כלל צודק"),
    (0.40, "לפעמים צודק"),
    (0.00, "כדאי לקחת בעירבון"),
]

REACTIONS = [
    ("deny", "להכחיש"),
    ("confirm", "לאשר"),
    ("silent", "לא להגיב"),
]

FEED_LIMIT = 30


def trust_word(trust: float) -> str:
    for floor, word in TRUST_WORDS:
        if trust >= floor:
            return word
    return TRUST_WORDS[-1][1]


# ---------------------------------------------------------------------------
# הפיד
# ---------------------------------------------------------------------------

def feed(game) -> List[Dict[str, Any]]:
    data = game.flags.get("press")
    return data if isinstance(data, list) else []


def push(game, item: Dict[str, Any]) -> None:
    items = feed(game)
    item.setdefault("year", game.year)
    item.setdefault("week", game.week)
    item.setdefault("answered", False)
    items.append(item)
    game.flags["press"] = items[-FEED_LIMIT:]


def open_question(game) -> Optional[Dict[str, Any]]:
    """הפריט האחרון שמחכה לתגובה שלך, אם יש."""
    for item in reversed(feed(game)):
        if item.get("asks") and not item.get("answered"):
            return item
    return None


def _story(game, key: str, source: str, text: str, true: bool,
           asks: bool = False, weight: float = 1.0) -> Dict[str, Any]:
    return {"key": key, "source": source, "text": text, "true": true,
            "trust": SOURCE_TRUST[source], "asks": asks, "weight": weight}


# ---------------------------------------------------------------------------
# מה נכתב עליך השבוע
# ---------------------------------------------------------------------------

def weekly_press(game, rng: random.Random) -> List[str]:
    """מייצר את מה שנכתב עליך השבוע ומחזיר שורות לדוח.

    השמועות לא נשלפות מהאוויר: כל אחת נשענת על משהו שקורה במצב המשחק
    — כושר, פציעה, חוזה, מי עוקב אחריך — ואז עוברת דרך מקור עם אמינות.
    מקור חלש מייצר גם שמועות שפשוט לא נכונות.
    """
    me = game.me
    out: List[str] = []
    if game.stage not in ("player", "veteran", "youth"):
        return out

    # קודם ההגרלה ורק אחר כך בניית הסיפורים: ברוב השבועות לא כותבים
    # עליך כלום, ואין טעם לבנות עשרה סיפורים כדי לזרוק את כולם.
    chance = 0.16 + me.reputation / 260.0
    if me.reputation > 70:
        chance += 0.12
    if rng.random() > chance:
        return out

    pool = _candidates(game)
    if not pool:
        return out

    weights = [item["weight"] for item in pool]
    item = _weighted_pick(pool, weights, rng)
    push(game, item)
    icon = SOURCE_ICON[item["source"]]
    out.append(f"{icon} {SOURCE_NAMES[item['source']]}: \"{item['text']}\"")
    if item["asks"]:
        out.append("   (אפשר להגיב — בתפריט: 'תקשורת')")
    return out


def _weighted_pick(items, weights, rng):
    total = sum(weights)
    roll = rng.random() * total
    acc = 0.0
    for item, weight in zip(items, weights):
        acc += weight
        if roll <= acc:
            return item
    return items[-1]


def _candidates(game) -> List[Dict[str, Any]]:
    """כל הסיפורים שאפשר לכתוב עליך עכשיו, לפי מצב המשחק."""
    from . import scouting as SC
    me = game.me
    club = game.my_club
    rng = game.rng
    out: List[Dict[str, Any]] = []
    club_name = club.name if club else "המועדון"

    # -- התעניינות אמיתית של מועדון --------------------------------------
    watchers = SC.watchers(game)
    if watchers:
        other, score = watchers[0]
        strong = score >= SC.CHASED
        source = "insider" if strong else rng.choice(["sources", "beat", "tv"])
        out.append(_story(
            game, "interest", source,
            f"{other.name} שולחים צופים לכל משחק של {me.name}. "
            f"בהנהלה מדברים על פנייה רשמית.",
            true=True, asks=True, weight=2.4 if strong else 1.4))

    # -- התעניינות שהיא בעיקר רעש ----------------------------------------
    pool = [c for c in SC.candidate_clubs(game)
            if not any(c.cid == w[0].cid for w in watchers)]
    if pool and me.reputation > 45:
        other = rng.choice(pool)
        out.append(_story(
            game, "rumour", rng.choice(["tabloid", "fan", "radio"]),
            f"{other.name} הניחו עין על {me.name}. מדובר בסכום דמיוני.",
            true=False, asks=True, weight=1.6))

    # -- כושר --------------------------------------------------------------
    if me.season.apps >= 4:
        rating = me.season.avg_rating
        if rating >= 7.3:
            out.append(_story(
                game, "hot", "tv",
                f"אין היום שחקן בכושר של {me.name}. ממוצע {rating:.2f} "
                f"זה לא מקרי — זה מישהו שעולה מדרגה.",
                true=True, weight=1.8))
        elif rating <= 6.3:
            out.append(_story(
                game, "cold", rng.choice(["radio", "tabloid", "beat"]),
                f"מה קרה ל{me.name}? ממוצע {rating:.2f} מתחילת העונה. "
                f"ב{club_name} מתחילים לשאול שאלות.",
                true=True, asks=True, weight=1.6))

    # -- חוזה ---------------------------------------------------------------
    if me.contract.years_left <= 1 and game.stage != "youth":
        out.append(_story(
            game, "contract", "insider",
            f"החוזה של {me.name} ב{club_name} נגמר בסוף העונה, "
            f"והמגעים לחידוש תקועים.",
            true=True, asks=True, weight=2.0))

    # -- פציעה --------------------------------------------------------------
    if me.injury_weeks > 0:
        out.append(_story(
            game, "injury", "tabloid",
            f"הפציעה של {me.name} חמורה בהרבה ממה שב{club_name} מוכנים להגיד. "
            f"מדברים על חצי עונה.",
            true=False, asks=True, weight=1.8))
    elif me.fitness < 62:
        out.append(_story(
            game, "fitness", "sources",
            f"{me.name} מגיע לאימונים על חצי מיכל. בצוות הרפואי לא רגועים.",
            true=me.fitness < 55, asks=True, weight=1.2))

    # -- יחסים במועדון ------------------------------------------------------
    if club and club.manager_trust < 42:
        out.append(_story(
            game, "manager", rng.choice(["sources", "beat"]),
            f"ב{club_name} מספרים על שיחה לא נעימה בין המאמן ל{me.name}. "
            f"הוא לא בטוח בהרכב.",
            true=True, asks=True, weight=1.9))
    elif club and club.manager_trust > 78:
        out.append(_story(
            game, "trusted", "beat",
            f"המאמן של {club_name} על {me.name}: \"הוא הראשון על הדף שלי.\"",
            true=True, weight=1.0))

    # -- שמועה מומצאת לגמרי -------------------------------------------------
    if me.reputation > 55:
        out.append(_story(
            game, "gossip", rng.choice(["tabloid", "fan"]),
            rng.choice([
                f"{me.name} נראה מחפש בתים בחו\"ל. אצלנו יודעים למה.",
                f"ב{club_name} כועסים על {me.name} אחרי שאיחר לאימון. "
                f"המקורבים מכחישים.",
                f"{me.name} החליף סוכן בשקט. זה תמיד אומר משהו.",
            ]),
            true=False, asks=True, weight=1.3))

    # -- נבחרת --------------------------------------------------------------
    if me.reputation > 62 and not game.caps:
        out.append(_story(
            game, "national", rng.choice(["tv", "sources"]),
            f"השם של {me.name} עלה בישיבת הסגל של הנבחרת. "
            f"יש מי שאומר שזה רק עניין של זמן.",
            true=me.reputation > 70, asks=True, weight=1.7))
    return out


# ---------------------------------------------------------------------------
# התגובה שלך
# ---------------------------------------------------------------------------

def react(game, choice: str, rng: random.Random) -> str:
    """מגיב לשמועה הפתוחה. לכל בחירה יש מחיר, וגם לשתיקה.

    זו הנקודה שבה תקשורת מפסיקה להיות טפט: הכחשה של דבר נכון נשברת
    בפנים שלך אחר כך, אישור של משהו נכון פוגע במועדון אבל מרים את
    השוק, ושתיקה משאירה את הסיפור לרוץ.
    """
    item = open_question(game)
    if not item:
        return "אין כרגע משהו שמחכה לתגובה."
    me = game.me
    club = game.my_club
    item["answered"] = True
    item["reaction"] = choice
    game.flags["press"] = feed(game)

    skill = me.media_skill
    smooth = skill / 100.0
    if me.has_trait("media_darling"):
        smooth += 0.18
    if me.has_trait("hothead"):
        smooth -= 0.20
    smooth = clamp(smooth, 0.0, 1.0)

    if choice == "deny":
        if item["true"]:
            # הכחשת אמת מחזיקה בדיוק עד שהיא לא
            if rng.random() < 0.45 - smooth * 0.30:
                gain_reputation(me, -2.5)
                me.morale = clamp(me.morale - 7, 5, 99)
                if club:
                    club.fan_support = clamp(club.fan_support - 5, 0, 100)
                return ("הכחשת — ותוך שבוע יצאה ההקלטה. "
                        "\"אמרתי מה שהייתי צריך להגיד\" לא עבד הפעם.")
            if club:
                club.manager_trust = clamp(club.manager_trust + 4, 0, 100)
                club.fan_support = clamp(club.fan_support + 3, 0, 100)
            return "הכחשת בתוקף. במועדון אהבו את זה; אתה יודע מה האמת."
        gain_reputation(me, 0.8 + smooth)
        if club:
            club.fan_support = clamp(club.fan_support + 5, 0, 100)
        return "הכחשת, וצדקת. הסיפור נגמר תוך יומיים והיציע זכר את זה."

    if choice == "confirm":
        if item["true"]:
            gain_reputation(me, 2.2)
            me.morale = clamp(me.morale + 4, 5, 99)
            if club:
                club.manager_trust = clamp(club.manager_trust - 7, 0, 100)
                club.fan_support = clamp(club.fan_support - 8, 0, 100)
            game.set_flag("open_to_europe", True)
            return ("אישרת. הכותרות ענקיות, הסוכן שלך מאושר, "
                    "וביציע לא סולחים על זה מהר.")
        gain_reputation(me, -3.0)
        me.morale = clamp(me.morale - 5, 5, 99)
        return ("אישרת משהו שלא היה. כשהתברר שאין שום הצעה, "
                "יצאת מי שמנסה ליצור לעצמו שוק.")

    # שתיקה
    if item["true"]:
        if club:
            club.manager_trust = clamp(club.manager_trust - 2, 0, 100)
        return "לא הגבת. הסיפור המשיך לרוץ, וכולם הבינו לבד."
    return "לא הגבת. בלי דלק הסיפור דעך מעצמו תוך שבוע."


# ---------------------------------------------------------------------------
# משדר
# ---------------------------------------------------------------------------

def broadcast(game, result, rng: random.Random) -> List[str]:
    """מה אמרו עליך באולפן אחרי המשחק. נשען על המספרים האמיתיים."""
    me = game.me
    stats = me.last_match if hasattr(me, "last_match") else None
    rating = getattr(stats, "rating", 0) if stats else 0
    if not rating:
        return []
    lines = []
    if rating >= 8.2:
        lines.append(rng.choice([
            f"📺 \"אם מישהו עוד לא ראה את {me.name} — תראו את המשחק הזה.\"",
            f"📺 \"ציון {rating:.1f}. לא צריך להוסיף מילה.\"",
        ]))
    elif rating >= 7.2:
        lines.append(rng.choice([
            f"📺 \"{me.name} היה הכי טוב על המגרש, ובלי לעשות רעש.\"",
            f"📺 \"זה שחקן שהקבוצה כבר בנויה סביבו.\"",
        ]))
    elif rating <= 5.6:
        lines.append(rng.choice([
            f"📺 \"אני אגיד את זה בזהירות — {me.name} לא היה שם היום.\"",
            f"📺 \"ציון {rating:.1f}. יש ימים כאלה, אבל לא שניים ברצף.\"",
        ]))
    return lines
