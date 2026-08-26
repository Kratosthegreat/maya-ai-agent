# -*- coding: utf-8 -*-
"""
football_manager.mentor
=======================
מישהו שמלווה אותך, ולא חוזר על עצמו.

התלונה הייתה כפולה: אין מי שיכוון, וכשיש טיפ הוא אותו טיפ. לכן
המנטור כאן בנוי אחרת מכל שאר הטקסטים במשחק: הוא לא מגריל שורה
מרשימה. הוא **קורא את המצב** — התפקיד שלך, מה חוסם אבן דרך, כמה
דקות אתה מקבל, מה הרעננות שלך, על מה התאמנת בחודשיים האחרונים,
מי עוקב אחריך, מה קורה בחוזה — נותן ציון דחיפות לכל דבר שראה,
ומדבר על **הדחוף ביותר שעוד לא דיבר עליו**.

כל טיפ נרשם, ולכל טיפ יש זמן צינון משלו. טיפ שהמצב שלו נפתר —
משתחרר. טיפ שכבר נאמר לא יחזור עד שהמצב ישתנה באמת.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

from . import coaching as CO
from . import data as D
from . import development as DEV
from . import scouting as SC
from . import tactics as TA
from .models import Player, best_role, clamp, role_suitability

# (מפתח, שם, סגנון דיבור) — מי המנטור שלך נקבע פעם אחת ולתמיד
MENTORS = [
    ("veteran", "יעקב אזולאי", "ותיק שסיים בגיל 38 ויודע בדיוק איפה כואב",
     ["תשמע,", "אני אגיד לך את זה פעם אחת.", "אני הייתי שם."]),
    ("coach", "רונית שגב", "מאמנת כושר שראתה מאתיים נערים נשרפים",
     ["בוא נדבר תכל'ס.", "אני מסתכלת על המספרים שלך.", "שב רגע."]),
    ("scout", "מוני ברזילי", "צופה ותיק שקורא שחקנים לפני שהם קוראים את עצמם",
     ["רשמתי לעצמי משהו.", "אני עוקב אחריך.", "משהו קטן."]),
    ("agent", "דנה פרץ", "סוכנת שמדברת ישר וחוסכת לך שנים",
     ["אני לא אעטוף את זה.", "בינינו.", "תקשיב טוב."]),
]

COOLDOWN = 26          # שבועות לפני שטיפ מאותו סוג יכול לחזור


def _hash(text: str) -> int:
    value = 2166136261
    for ch in text:
        value ^= ord(ch)
        value = (value * 16777619) & 0xFFFFFFFF
    return value


def mentor_of(game) -> tuple:
    """המנטור שלך — נקבע מהשם שלך, ולכן קבוע לכל הקריירה."""
    return MENTORS[_hash(game.me.name + "mentor") % len(MENTORS)]


def _log(game) -> Dict[str, int]:
    data = game.flags.get("mentor_log")
    if not isinstance(data, dict):
        data = {}
        game.flags["mentor_log"] = data
    return data


def _counts(game) -> Dict[str, int]:
    """כמה פעמים כבר אמר לך כל דבר. זה מה שמונע ממנו לחזור על עצמו."""
    data = game.flags.get("mentor_count")
    if not isinstance(data, dict):
        data = {}
        game.flags["mentor_count"] = data
    return data


def _weeks_now(game) -> int:
    return game.year * 100 + game.week


def _said_recently(game, key: str, cooldown: int = COOLDOWN) -> bool:
    stamp = _log(game).get(key)
    if stamp is None:
        return False
    year, week = divmod(int(stamp), 100)
    weeks = (game.year - year) * 43 + (game.week - week)
    return weeks < cooldown


def _mark(game, key: str) -> None:
    _log(game)[key] = _weeks_now(game)
    counts = _counts(game)
    counts[key] = counts.get(key, 0) + 1


def _times(game, key: str) -> int:
    return _counts(game).get(key, 0)


# ---------------------------------------------------------------------------
# מה הוא רואה
# ---------------------------------------------------------------------------

def observations(game) -> List[Dict[str, Any]]:
    """כל מה שהמנטור מזהה עכשיו, עם ציון דחיפות.

    כל תצפית היא מצב אמיתי במשחק ולא טקסט אקראי — ולכן היא נעלמת
    מעצמה כשהמצב משתנה.
    """
    me = game.me
    club = game.my_club
    out: List[Dict[str, Any]] = []

    def see(key: str, urgency: float, title, body,
            action: Optional[str] = None, cooldown: int = COOLDOWN):
        """רושם תצפית.

        ``title`` ו-``body`` יכולים להיות רשימה: הגרסה נבחרת לפי כמה
        פעמים הוא כבר אמר לך את זה. מצב שנמשך לא מקבל את אותו משפט
        שוב ושוב — הוא מקבל משפט חריף יותר.
        """
        times = _times(game, key)
        titles = title if isinstance(title, list) else [title]
        bodies = body if isinstance(body, list) else [body]
        out.append({"key": key, "urgency": urgency + times * 6,
                    "title": titles[min(times, len(titles) - 1)],
                    "body": bodies[min(times, len(bodies) - 1)],
                    "action": action, "times": times,
                    # ככל שהוא חוזר על עצמו, הוא נותן לזה יותר זמן לנוח
                    "cooldown": cooldown + times * 10,
                    "exhausted": times >= max(len(titles), len(bodies)) + 1})

    # --- מה הכי חסר לך, ולמה ---
    needs = CO.ranked_needs(game, 3)
    if needs:
        top = needs[0]
        name = D.DETAIL_NAMES_HE[top["attr"]]
        why = top["reasons"][0] if top["reasons"] else "זו החולשה הבולטת שלך"
        line = CO.forecast_line(game, top["attr"])
        see(f"need_{top['attr']}", 62 + top["score"] * 0.25,
            f"תתאמן על {name}",
            f"{why}. {line}", action=top["attr"], cooldown=18)

    # --- תפקיד שלא מתאים לך ---
    if me.role:
        mine = role_suitability(me, me.role)
        best_key, best_score = best_role(me)
        if best_key != me.role and best_score - mine >= 8:
            row = D.ROLE_BY_KEY[best_key]
            current = D.ROLE_BY_KEY[me.role]
            see("role_mismatch", 74,
                [f"אתה לא {current[1]}", f"עדיין משחקים אותך כ{current[1]}"],
                [f"התכונות שלך אומרות {row[1]} ({best_score:.0f}) ולא "
                 f"{current[1]} ({mine:.0f}). {row[6]} לך תדבר איתו — "
                 "או תתאמן על מה שהתפקיד הנוכחי דורש, ותפסיק להילחם בזה.",
                 f"אמרתי לך שאתה {row[1]}. אתה עדיין {current[1]}. "
                 "שתי אפשרויות נשארו: או שאתה מקבל את התפקיד ובונה את "
                 f"התכונות שהוא דורש, או שאתה מוצא מאמן שרואה בך {row[1]}. "
                 "מה שאתה עושה עכשיו — לא עובד."])

    # --- הסגנון של המאמן לא בנוי לך ---
    if club:
        fit, note = TA.suits_player(club, me)
        if fit < 35:
            style_name = TA.style_of(club)[1]
            see("style_mismatch", 58,
                [f"אתה לא בנוי ל{style_name}", f"{style_name} עדיין חונק אותך"],
                [f"{note}. אצל מאמן אחר אותן תשעים דקות היו נראות אחרת. "
                 "אם זה נמשך עונה שלמה — תתחיל לחשוב על מעבר.",
                 f"{note}. עברה עונה ולא השתנה כלום. יש שחקנים שנשברים "
                 "בניסיון להתאים את עצמם למערכת, ויש כאלה שמוצאים מערכת "
                 "שמתאימה להם. השנייה מהירה יותר."])

    # --- דקות משחק ---
    if game.no_start_streak >= 5:
        see("no_minutes", 80,
            ["אתה לא משחק", "עדיין לא משחק", "זה כבר לא מקרי"],
            [f"{game.no_start_streak} משחקים ברצף בלי הרכב. בגיל שלך "
             "ספסל זה לא מנוחה — זה קיפאון. או שאתה משנה משהו באימונים, "
             "או שאתה מחפש מקום שבו תשחק.",
             f"{game.no_start_streak} משחקים. דיברנו על זה, ושום דבר לא זז. "
             "המאמן החליט מה הוא חושב עליך, וזה לא ישתנה מאימון טוב אחד. "
             "או שאתה מוכיח לו במשהו קונקרטי, או שאתה מרים טלפון לסוכן.",
             f"{game.no_start_streak} משחקים. אני לא אחזור על זה יותר. "
             "עונה שלמה על הספסל בגיל הזה עולה לך שנתיים של קריירה. "
             "תחליט."],
            cooldown=14)

    # --- רעננות ---
    if me.fitness < 45:
        see("fitness", 88,
            ["הגוף שלך על הקצה", "שוב הגעת לאדום", "אתה מתעלם ממני"],
            [f"רעננות {me.fitness:.0f}. ככה נכנסים למשחק ויוצאים פצועים, "
             "וגם הציון נענש. שבוע מנוחה עכשיו שווה יותר משלושה אימונים.",
             f"רעננות {me.fitness:.0f}, ושוב. זה כבר לא מקרה — זה איך שאתה "
             "מנהל את השבוע. תוריד עצימות, או תיקח שבוע.",
             f"רעננות {me.fitness:.0f}. אני אומר לך את זה בפעם השלישית. "
             "הפציעה הבאה שלך כבר נקבעה, השאלה היא רק מתי."],
            action="rest", cooldown=10)
    elif me.sharpness < 45 and me.available:
        see("sharpness", 52, "אין לך דקות ברגליים",
            f"חדות {me.sharpness:.0f}. אתה יכול להיות בכושר מצוין ועדיין "
            "להיכנס למשחק חלוד. חדות נבנית רק ממשחקים.", cooldown=16)

    # --- פציעות חוזרות ---
    if me.resilience < 38:
        see("fragile", 66, "אתה נשבר יותר מדי",
            f"עמידות {me.resilience:.0f}. עבודת כוח וסיבולת בונה גוף "
            "שמחזיק. זה משעמם, וזה מה שיקבע כמה עונות תשחק.",
            action="strength")

    # --- אבן דרך קרובה ---
    plan = DEV.plan_summary(game)
    if plan.get("chosen"):
        for entry in plan["milestones"]:
            if entry["claimed"]:
                continue
            gaps = [p for p in entry["needs"] if p["have"] < p["need"]]
            missing = sum(p["need"] - p["have"] for p in gaps)
            if gaps and missing <= 3:
                names = ", ".join(f"{p['name']} {p['have']}/{p['need']}" for p in gaps)
                see(f"milestone_{entry['index']}", 76,
                    f"אתה על סף אבן הדרך של גיל {entry['age']}",
                    f"חסרות {missing} נקודות: {names}. תסגור את זה עכשיו — "
                    "אבן דרך בזמן שווה כפול מאבן דרך באיחור.",
                    action=gaps[0]["attr"], cooldown=12)
            break
    elif game.stage in ("youth", "academy", "player", "veteran"):
        see("no_plan", 70,
            ["אין לך מסלול", "עדיין בלי מסלול"],
            ["אתה מתאמן בלי יעד. תבחר תפקיד שאתה רוצה להיות, ותקבל "
             "יעדים לפי גיל במקום לנחש כל שבוע.",
             "עוד לא בחרת. כל שבוע בלי מסלול הוא שבוע שבו אתה מפזר "
             "עבודה על שלושים ושש תכונות במקום על ארבע שחשובות."])

    # --- שגרת אימונים ---
    history = game.flags.get("focus_log") or []
    if len(history) >= 12:
        recent = history[-12:]
        if len(set(recent)) <= 2 and recent[-1] in D.DETAIL_NAMES_HE:
            name = D.DETAIL_NAMES_HE[recent[-1]]
            see("training_rut", 64, "נתקעת על אותו אימון",
                f"שלושה חודשים של {name}. ככל שתכונה מתרחקת מהשאר, כל "
                "נקודה נעשית יקרה יותר — ובמקביל חורים נפערים במקום אחר. "
                "תחליף מיקוד לכמה שבועות.", cooldown=20)

    # --- חוזה ---
    if me.contract.years_left <= 1 and club and game.stage in ("player", "veteran"):
        see("contract", 68, "החוזה שלך נגמר",
            "שנה אחת נשארה. מכאן והלאה כל מועדון יכול לדבר איתך בחינם, "
            "וגם המועדון שלך יודע את זה. או שאתה מחדש עכשיו מעמדת כוח, "
            "או שאתה מחכה ומהמר.", cooldown=30)

    # --- מי עוקב ---
    chasers = SC.watchers(game, SC.COURTED)
    if chasers:
        club_name = chasers[0][0].name
        country = D.club_country(chasers[0][0].cid, chasers[0][0].league_id)
        see("suitor", 60, f"{club_name} רציניים לגביך",
            f"הם עוקבים אחריך כבר תקופה{' מ' + country if country != 'ישראל' else ''}. "
            "זה לא אומר לעזוב — זה אומר שיש לך קלף. תמשיך לשחק ככה, "
            "והם יגיעו עם הצעה בחלון.", cooldown=22)

    # --- גיל ---
    if me.age >= 31 and me.badges == 0:
        see("after", 50, "תתחיל לחשוב על מה שאחרי",
            "בגיל שלך כל עונה היא בונוס. תעודות אימון היום שוות שנים "
            "של קריירה שנייה. זה לא במקום לשחק — זה במקביל.",
            action="badges", cooldown=40)

    # --- מורל ---
    if me.morale < 35:
        see("morale", 72,
            ["הראש שלך לא שם", "אתה עדיין למטה"],
            [f"מורל {me.morale:.0f}. זה לא רק הרגשה — זה מוריד לך את קצב "
             "ההתפתחות באימונים בעשרות אחוזים. משחק אחד טוב הופך את זה.",
             f"מורל {me.morale:.0f} כבר תקופה. אתה מפסיד התפתחות בכל שבוע "
             "שאתה נשאר שם. תתחיל ממשהו קטן שאתה יודע לעשות טוב."],
            cooldown=16)

    return out


# ---------------------------------------------------------------------------
# מה הוא אומר
# ---------------------------------------------------------------------------

def advise(game, rng: Optional[random.Random] = None) -> Optional[Dict[str, Any]]:
    """הטיפ הבא — הדחוף ביותר שעוד לא נאמר לאחרונה.

    מחזיר None כשאין לו מה לחדש, וזה בסדר גמור: מנטור שמדבר כל שבוע
    הוא רעש, לא ליווי.
    """
    rng = rng or game.rng
    fresh = [row for row in observations(game)
             if not row.get("exhausted")
             and not _said_recently(game, row["key"], row["cooldown"])]
    if not fresh:
        return None
    fresh.sort(key=lambda row: -row["urgency"])
    # מבין הדחופים באמת — אחד אקראי, כדי שלא יהיה צפוי לחלוטין
    top = fresh[0]["urgency"]
    pool = [row for row in fresh if row["urgency"] >= top - 8]
    chosen = rng.choice(pool)
    _mark(game, chosen["key"])

    key, name, blurb, openers = mentor_of(game)
    opener = openers[_hash(chosen["key"]) % len(openers)]
    return {
        "mentor": name, "blurb": blurb,
        "opener": opener,
        "title": chosen["title"],
        "body": chosen["body"],
        "action": chosen.get("action"),
        "urgency": chosen["urgency"],
    }


def advice_lines(game, rng: Optional[random.Random] = None) -> List[str]:
    """הטיפ כשורות מוכנות לדוח השבועי."""
    tip = advise(game, rng)
    if not tip:
        return []
    lines = [f"🧭 {tip['mentor']}: \"{tip['opener']} {tip['title']}.\"",
             f"   {tip['body']}"]
    if tip["action"] and tip["action"] in D.DETAIL_NAMES_HE:
        lines.append(f"   → מומלץ להתאמן השבוע על "
                     f"{D.DETAIL_NAMES_HE[tip['action']]}.")
    return lines


def board(game) -> Dict[str, Any]:
    """כל מה שהמנטור רואה עכשיו — למסך שלו."""
    key, name, blurb, _openers = mentor_of(game)
    rows = sorted(observations(game), key=lambda row: -row["urgency"])
    return {
        "name": name, "blurb": blurb,
        "items": [{
            "title": row["title"], "body": row["body"],
            "action": row.get("action"),
            "urgency": round(row["urgency"]),
            "said": _said_recently(game, row["key"], row["cooldown"]),
        } for row in rows],
        "needs": CO.ranked_needs(game, 5),
    }
