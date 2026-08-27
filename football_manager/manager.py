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
from . import matchstats as MS
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

# מה המאמן אומר כשהוא מבקש תכונה מפורטת. הטקסט הכללי נשען על הקבוצה
# שאליה היא שייכת, והמספרים מהמשחק מגיעים מהשורה של אתמול.
def detail_directive_text(focus: str) -> str:
    name = D.DETAIL_NAMES_HE.get(focus)
    if not name:
        return DIRECTIVE_TEXT.get(focus, "רוצה אותך באימון נוסף.")
    return f"רוצה שתעבוד השבוע על {name}."


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
    """מה המאמן רוצה ממך השבוע.

    הוא לא ממציא: הוא קורא את שורת הסטטיסטיקה של המשחק האחרון שלך
    ובוחר את התחום שבו נפלת הכי הרבה יחסית למה שהעמדה שלך דורשת.
    כשאין משחק אחרון — הוא נופל חזרה לפער מול פרופיל העמדה.
    """
    club = game.my_club
    me = game.me
    if not club or game.stage not in ("academy", "player", "veteran"):
        return None

    # מנוחה נדרשת רק כשהגוף באמת על הקצה — לא כברירת מחדל
    if me.fitness < 34 or (me.fitness < 46 and me.sharpness < 45):
        return "rest"

    stats = game.flags.get("last_stats")
    if stats:
        return MS.weakest_detail(stats, me)

    weights = D.POSITION_WEIGHTS[me.position]
    gaps = sorted(D.ATTRIBUTES,
                  key=lambda a: me.attributes.get(a, 50) - weights.get(a, 0.1) * 120)
    return rng.choice(gaps[:3])


def directive_line(club: Optional[Club], focus: str, stats=None) -> str:
    """ההוראה, עם הסיבה מהמשחק האחרון וההבטחה מה זה ייתן.

    בלי הסיבה זו הייתה שורת טקסט אקראית. עם הסיבה זו שיחה: הוא מצטט
    לך את המספרים שלך מיום ראשון, ואומר מה ישתנה אם תעבוד על זה.
    """
    name = club.manager_name if club else "המאמן"
    head = f"🎙️ {name} {detail_directive_text(focus)}"
    if not stats:
        return head
    # הסיבה וההבטחה כתובות בשפת הקבוצות — מתרגמים חזרה
    group = D.DETAIL_GROUP.get(focus)
    area = focus if focus in D.DIRECTIVE_REASON else _area_of(focus)
    reason = MS.reason_line(area, stats)
    promise = MS.promise_line(area)
    parts = [head]
    if reason:
        parts.append(f"   \"{reason}\"")
    if promise:
        parts.append(f"   → {promise}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# תגובה אחרי משחק
# ---------------------------------------------------------------------------

def _area_of(detail_attr: str) -> str:
    """לאיזו מבין שבע הקבוצות שייכת תכונה מפורטת."""
    best, best_share = "physical", -1.0
    for group, members in D.GROUP_MAP.items():
        share = members.get(detail_attr, 0.0)
        if share > best_share:
            best, best_share = group, share
    for group, members in D.GROUP_MAP_GK.items():
        share = members.get(detail_attr, 0.0)
        if share > best_share:
            best, best_share = group, share
    return best


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


# ---------------------------------------------------------------------------
# למאמן יש דעה עליך, ולדעה יש משקל
#
# עד כאן `manager_trust` היה מספר שהשפיע קצת על ההרכב וזהו. מאמן
# אמיתי הוא לא מד־חום: יש לו מועדפים, יש לו כלב שלא מקבל דקות, הוא
# מבטיח דברים ולפעמים שובר אותם, ואפשר לדפוק לו על הדלת ולשאול למה.
# ---------------------------------------------------------------------------

# (מפתח, שם, סף אמון, מה זה שווה בהרכב)
#
# הבונוס נכנס ישירות ל-`effective` בבחירת ההרכב, ולכן ה"כלב" הוא לא
# תווית — הוא שמונה נקודות דירוג שנעלמות, וזה מורגש בכל שבוע.
STANDINGS = [
    ("favourite", "המועדף שלו", 78, 6.0),
    ("trusted", "בתוך התוכנית", 58, 2.5),
    ("neutral", "עוד אחד בסגל", 40, 0.0),
    ("doubted", "מסומן בשאלה", 24, -3.5),
    ("frozen", "בכלוב", 0, -8.0),
]

# מה אפשר לבקש בפגישה, ומה הסיכון
#
# ask   — כמה קשה לקבל את זה (0-1, גבוה = קשה)
# gain  — אמון אם הצליח
# cost  — אמון אם נכשל
MEETINGS = [
    ("role", "לבקש מקום קבוע בהרכב",
     "\"אני צריך לדעת אם אני משחק כאן.\"", 0.55, 6, -8),
    ("why", "לשאול למה אתה לא משחק",
     "\"תסביר לי מה חסר לי.\"", 0.30, 3, -3),
    ("promise", "להבטיח לו עונה",
     "\"תן לי שלושה משחקים ואני אראה לך.\"", 0.45, 8, -6),
    ("position", "לבקש לשחק בעמדה שלך",
     "\"אני לא שחקן שאתה מכניס לאן שחסר.\"", 0.50, 5, -6),
    ("leave", "לבקש רשות לעזוב",
     "\"אני רוצה לשמוע הצעות. בלי מלחמות.\"", 0.60, -2, -12),
]
MEETING_NAMES = {key: name for key, name, _, _, _, _ in MEETINGS}

# הבטחות של המאמן, ומה קורה כשהן נשברות
PROMISE_WEEKS = 5
PROMISE_TRUST_BREAK = -14.0

# כמה זמן צריך לעבור בין פגישה לפגישה. מאמן שסופגים לו על הדלת כל
# שבוע מפסיק לפתוח אותה.
MEETING_COOLDOWN = 6


def standing(game) -> Tuple[str, str, float]:
    """איפה אתה עומד אצלו: מפתח, שם, ומה זה שווה בהרכב."""
    club = game.my_club
    trust = club.manager_trust if club else 50.0
    if game.flag("doghouse"):
        trust -= 22
    if game.flag("captain"):
        trust += 8
    for key, name, threshold, bonus in STANDINGS:
        if trust >= threshold:
            return key, name, bonus
    return STANDINGS[-1][0], STANDINGS[-1][1], STANDINGS[-1][3]


def selection_bonus(game) -> float:
    """כמה נקודות המאמן מוסיף או מוריד לך בבחירת ההרכב.

    זה מה שהופך את היחסים איתו למשהו שמרגישים: שחקן בכלוב לא נכנס
    להרכב גם כשהוא הכי טוב בעמדה, ומועדף נכנס גם כשהוא לא.
    """
    bonus = standing(game)[2]
    promise = active_promise(game)
    if promise and promise["kind"] in ("start", "role"):
        bonus += 9.0            # הבטחה זה הבטחה, לפחות לכמה שבועות
    return bonus


def standing_line(game) -> str:
    club = game.my_club
    if not club:
        return ""
    key, name, bonus = standing(game)
    who = club.manager_name
    if key == "favourite":
        return f"⭐ {who} רואה בך את הציר. אתה משחק גם כשאתה לא בכושר."
    if key == "trusted":
        return f"✅ {who} סופר אותך. המקום שלך תלוי בך."
    if key == "neutral":
        return f"⚖️ {who} עוד לא החליט לגביך."
    if key == "doubted":
        return f"⚠️ {who} מסתכל עליך אחרת. עוד משחק חלש וזה ייסגר."
    return f"⛔ אתה מחוץ לתוכניות של {who}. גם אימון מצוין לא יזיז את זה מהר."


# ---------------------------------------------------------------------------
# הבטחות
# ---------------------------------------------------------------------------

def give_promise(game, kind: str, weeks: int = PROMISE_WEEKS) -> str:
    """המאמן מבטיח משהו. מרגע זה הוא נמדד לפיו."""
    game.flags["promise"] = {"kind": kind, "weeks": weeks, "made": game.week,
                             "starts": 0}
    club = game.my_club
    who = club.manager_name if club else "המאמן"
    text = {"start": f"{who} הבטיח לך {weeks} משחקים בהרכב.",
            "role": f"{who} הבטיח לך את העמדה שלך.",
            "minutes": f"{who} הבטיח לך דקות.",
            "leave": f"{who} הבטיח לא לחסום מעבר בקיץ."}.get(
                kind, f"{who} הבטיח לך משהו.")
    return f"🤝 {text}"


def active_promise(game) -> Optional[Dict[str, Any]]:
    row = game.flags.get("promise")
    if not isinstance(row, dict) or row.get("weeks", 0) <= 0:
        return None
    return row


def promise_tick(game, played: bool) -> Optional[str]:
    """שבוע עובר על הבטחה. שבורה — זה עולה לו, לא לך."""
    row = active_promise(game)
    if not row:
        return None
    row["weeks"] -= 1
    if played:
        row["starts"] = row.get("starts", 0) + 1
    club = game.my_club
    who = club.manager_name if club else "המאמן"

    if row["weeks"] > 0:
        return None
    kept = row.get("starts", 0) >= max(1, PROMISE_WEEKS // 2)
    game.flags.pop("promise", None)
    if kept:
        game.me.morale = clamp(game.me.morale + 8, 5, 99)
        return f"✅ {who} עמד במילה שלו."
    # הוא שבר. זה משנה איך אתה מסתכל עליו, ולא להפך.
    game.me.morale = clamp(game.me.morale - 12, 5, 99)
    if club:
        club.manager_trust = clamp(club.manager_trust + PROMISE_TRUST_BREAK, 0, 100)
    game.set_flag("broken_promise", True)
    return (f"💢 {who} הבטיח ולא קיים. אתה זוכר בדיוק מה הוא אמר "
            f"ובאיזה יום.")


# ---------------------------------------------------------------------------
# פגישה בארבע עיניים
# ---------------------------------------------------------------------------

def meeting_options(game) -> List[Dict[str, Any]]:
    """מה אפשר לבקש ממנו עכשיו."""
    club = game.my_club
    if not club or game.stage not in ("academy", "player", "veteran"):
        return []
    last = int(game.flag("meeting_week", -99) or -99)
    if game.week - last < MEETING_COOLDOWN:
        return []
    out = []
    for key, name, line, difficulty, gain, cost in MEETINGS:
        out.append({"key": key, "name": name, "line": line,
                    "odds": _meeting_odds(game, difficulty)})
    return out


def _meeting_odds(game, difficulty: float) -> float:
    """כמה סיכוי שהוא יגיד כן. גלוי לשחקן — זו החלטה, לא הימור עיוור."""
    club = game.my_club
    trust = club.manager_trust if club else 50.0
    me = game.me
    chance = 0.9 - difficulty
    chance += (trust - 50) / 145.0
    chance += (me.reputation - 40) / 320.0
    if me.season.apps >= 5:
        chance += clamp((me.season.avg_rating - 6.7) * 0.14, -0.12, 0.16)
    if game.flag("doghouse"):
        chance -= 0.22
    # מאמן שסולח יותר — האופי שלו הוא לא קישוט
    chance += (style_of(club)[4] - 1.0) * 0.18
    return clamp(chance, 0.05, 0.92)


def request(game, key: str, rng: random.Random) -> str:
    """נכנס אליו למשרד ומבקש. יוצא עם משהו, או עם פחות ממה שנכנסת."""
    club = game.my_club
    if not club:
        return "אין לך מועדון."
    row = next((r for r in MEETINGS if r[0] == key), None)
    if not row:
        return "לא ידוע."
    _, name, line, difficulty, gain, cost = row
    game.set_flag("meeting_week", game.week)
    who = club.manager_name
    odds = _meeting_odds(game, difficulty)

    if rng.random() < odds:
        club.manager_trust = clamp(club.manager_trust + gain, 0, 100)
        game.set_flag("doghouse", False)
        if key == "role":
            return give_promise(game, "start") + f"\n{who}: \"תוכיח לי שצדקתי.\""
        if key == "position":
            return give_promise(game, "role") + f"\n{who}: \"בסדר. העמדה שלך.\""
        if key == "promise":
            return give_promise(game, "minutes") + f"\n{who}: \"שלושה משחקים. לא יותר.\""
        if key == "leave":
            game.set_flag("free_to_leave", True)
            return (f"🤝 {who}: \"אני לא כולא אף אחד. תביא הצעה נורמלית "
                    f"ואני לא אעמוד בדרך.\"")
        return (f"🎙️ {who} הסביר בדיוק מה חסר לך, בלי לרכך. "
                f"יצאת עם רשימה ולא עם תירוץ.")

    club.manager_trust = clamp(club.manager_trust + cost, 0, 100)
    game.me.morale = clamp(game.me.morale - 5, 5, 99)
    if key in ("role", "leave") and rng.random() < 0.45:
        game.set_flag("doghouse", True)
        return (f"⛔ {who}: \"אתה לא במצב לבקש.\" מהשבוע הבא אתה "
                f"מתאמן עם הקבוצה השנייה.")
    return f"🚫 {who} שמע עד הסוף ואמר \"לא עכשיו\". זה לא נשמע כמו \"אחר כך\"."


# ---------------------------------------------------------------------------
# מאמנים מפוטרים
# ---------------------------------------------------------------------------

def maybe_replace(game, rng: random.Random) -> Optional[str]:
    """הנהלה מאבדת סבלנות — ומאמן חדש הוא דף חדש, לטוב ולרע.

    זה אחד הדברים שהופכים עונה ללא צפויה: כל היחסים שבנית חצי שנה
    נמחקים ברביעי בבוקר, והחדש לא חייב לך כלום.
    """
    club = game.my_club
    if not club or game.stage not in ("academy", "player", "veteran"):
        return None
    pressure = 0.0
    if club.board_confidence < 35:
        pressure += 0.05
    if club.board_confidence < 22:
        pressure += 0.07
    if club.fan_support < 30:
        pressure += 0.02
    if pressure <= 0 or rng.random() > pressure:
        return None

    old = club.manager_name
    club.manager_name = rng.choice([n for n in D.MANAGER_NAMES if n != old])
    # אמון מתאפס לאמצע, וכל מה שנצבר — הבטחות, כלוב, סרט — יורד לטמיון
    club.manager_trust = clamp(rng.uniform(38, 58), 0, 100)
    club.board_confidence = clamp(club.board_confidence + 12, 0, 100)
    game.flags.pop("promise", None)
    game.set_flag("doghouse", False)
    game.set_flag("new_manager", True)
    key, style_he, desc, _, _, _ = style_of(club)
    return (f"📣 {old} פוטר. {club.manager_name} נכנס — {style_he}. "
            f"{desc}\n   כל מה שבנית מול הקודם — מתחיל מאפס.")
