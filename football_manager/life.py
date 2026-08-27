# -*- coding: utf-8 -*-
"""
football_manager.life
=====================
מה שקורה כשאתה לא על המגרש.

המשפחה נכנסה למשחק בגיל שלוש־עשרה והתאדתה ברגע שחתמת חוזה ראשון.
זו טעות: **ההורים לא נעלמים כשהילד מצליח** — הם רק מתחילים לצפות
בטלוויזיה במקום ביציע. וגם, לשחקן יש חיים. יש מי שמחכה בבית, ויש מי
שנשאר ער כשהפסדתם.

מה שיש כאן:

* **הורים חיים.** גאווה שעולה ויורדת, אח או אחות עם בקשה, בית שאפשר
  לקנות להם. ההורים מבקשים דברים, וגם נותנים.
* **בת או בן זוג.** נפגשים במקרה (דרך `encounters`), והקשר עובר
  שלבים: היכרות → זוגיות → אירוסין → נישואין → ילדים.
* **תמיכה מול זרקור.** לכל בן זוג יש שני מספרים: כמה הוא מחזיק אותך
  כשקשה, וכמה הוא מביא איתו מצלמות. בת זוג מפורסמת מכפילה את השם
  שלך ואת כמות הכותרות — לטוב ולרע.
* **מצב הקשר לא סטטי.** עצימות אימונים גבוהה שבוע אחרי שבוע, מעבר
  לחו"ל בלי לשאול, וגם עונה של הפסדים — כל אלה שוחקים. חופשה, מתנה
  וזמן מחזירים.
* **פרידה קיימת.** ומרגישים אותה במורל ובחדות למשך חודשים.

הכול מיתרגם למספרים שהמנוע כבר מכיר: מורל, עמידות, חדות ומוניטין.
זו לא מערכת נפרדת שיושבת בצד — היא מזיזה את אותם ידיות.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from .models import clamp

# ---------------------------------------------------------------------------
# ההורים
# ---------------------------------------------------------------------------

# מה ההורים מבקשים ממך לאורך הקריירה. כל בקשה עולה כסף ומחזירה גאווה.
PARENT_ASKS = [
    ("house", "בית להורים", "הם עדיין בדירת השכירות שגדלת בה.", 1_400_000, 26),
    ("car", "אוטו לאבא", "האוטו שלו לא עובר טסט כבר שנתיים.", 180_000, 12),
    ("debt", "לסגור חוב", "הם לא סיפרו לך, ואתה גילית במקרה.", 320_000, 18),
    ("trip", "לקחת אותם למשחק בחו\"ל", "אמא שלך אף פעם לא טסה.", 90_000, 14),
    ("sibling", "לממן לימודים לאח", "הוא טוב בלימודים. אתה טוב בכדורגל.", 240_000, 16),
]
PARENT_ASK_NAMES = {key: name for key, name, _, _, _ in PARENT_ASKS}

PRIDE_START = 60.0


# ---------------------------------------------------------------------------
# בן/בת הזוג
# ---------------------------------------------------------------------------

# (מפתח, שם השלב, כמה שבועות עד שאפשר להתקדם)
STAGES = [
    ("dating", "בהיכרות", 10),
    ("serious", "זוגיות", 26),
    ("engaged", "מאורסים", 30),
    ("married", "נשואים", 0),
]
STAGE_NAMES = {key: name for key, name, _ in STAGES}
STAGE_ORDER = [key for key, _, _ in STAGES]

# מי שאפשר לפגוש. הזרקור הוא לא "יותר טוב" — הוא סוג אחר של חיים.
PARTNER_KINDS = [
    ("hometown", "מהשכונה", "מכירה אותך מלפני שהיית מישהו.", 82, 8),
    ("student", "סטודנטית לרפואה", "יש לה חיים משלה, והם תובעניים.", 64, 14),
    ("athlete", "ספורטאית", "מבינה בדיוק מה זה שבוע לפני דרבי.", 74, 34),
    ("model", "דוגמנית", "כל יציאה שלכם היא ידיעה.", 46, 88),
    ("singer", "זמרת", "מפורסמת יותר ממך, לפחות בינתיים.", 42, 95),
    ("agent_daughter", "עורכת דין", "קוראת את החוזה שלך לפני שאתה חותם.", 70, 26),
]
PARTNER_BY_KIND = {row[0]: row for row in PARTNER_KINDS}

# שמות. אלה דמויות במשחק, ולכן יש להן שם.
PARTNER_FIRST = ["מאיה", "נועה", "שירה", "רוני", "טל", "אביגיל", "ליהי",
                 "יערה", "דנה", "עדי", "הילה", "אלמה", "סתיו", "רותם",
                 "יסמין", "אמילי", "לוסיה", "אנה", "סופיה", "מיה"]

# כמה מהר הקשר נשחק כשלא מטפלים בו, וכמה הוא מחזיר לעצמו כשכן
DRIFT_PER_WEEK = 0.55
NEGLECT_INTENSITY = 1.3      # עצימות אימון שמעליה זה נחשב הזנחה
BREAKUP_MOOD = 22.0          # מתחת לזה הקשר בסכנה אמיתית
BREAKUP_CHANCE = 0.16

# עלות המחוות
GIFT_COST = 45_000
HOLIDAY_COST = 160_000
RING_COST = 400_000
WEDDING_COST = 900_000


# ---------------------------------------------------------------------------
# מצב
# ---------------------------------------------------------------------------

def parents(game) -> Dict[str, Any]:
    """מצב ההורים. נבנה בפעם הראשונה שמישהו שואל."""
    data = game.flags.get("parents")
    if not isinstance(data, dict):
        data = {"pride": PRIDE_START, "given": [], "ask": None, "asked": 0}
        game.flags["parents"] = data
    return data


def partner(game) -> Optional[Dict[str, Any]]:
    data = game.flags.get("partner")
    return data if isinstance(data, dict) else None


def make_partner(kind: str, rng: random.Random, name: str = "") -> Dict[str, Any]:
    key, label, desc, support, spotlight = PARTNER_BY_KIND[kind]
    return {
        "kind": key,
        "name": name or rng.choice(PARTNER_FIRST),
        "support": int(clamp(support + rng.randint(-9, 9), 10, 99)),
        "spotlight": int(clamp(spotlight + rng.randint(-8, 8), 0, 99)),
        "stage": "dating",
        "mood": 72.0,
        "weeks": 0,           # כמה זמן בשלב הנוכחי
        "kids": 0,
        "gifts": 0,
    }


def stage_name(row: Optional[Dict[str, Any]]) -> str:
    if not row:
        return ""
    return STAGE_NAMES.get(row["stage"], row["stage"])


def next_stage(stage: str) -> Optional[str]:
    idx = STAGE_ORDER.index(stage) if stage in STAGE_ORDER else -1
    if idx < 0 or idx >= len(STAGE_ORDER) - 1:
        return None
    return STAGE_ORDER[idx + 1]


# ---------------------------------------------------------------------------
# מה זה עושה לשחקן
# ---------------------------------------------------------------------------

def support_bonus(game) -> float:
    """כמה המורל מרוויח מזה שיש מישהו בבית.

    זה לא בונוס קבוע: בן זוג תומך במצב רוח טוב מרים, ובן זוג במשבר
    מוריד. זו הסיבה שהמספר יכול להיות שלילי.
    """
    row = partner(game)
    if not row:
        return 0.0
    quality = (row["support"] / 100.0) * (row["mood"] - 45.0) / 55.0
    stage_weight = {"dating": 0.7, "serious": 1.0, "engaged": 1.15,
                    "married": 1.3}.get(row["stage"], 1.0)
    return clamp(quality * 3.4 * stage_weight, -3.2, 3.6)


def spotlight_bonus(game) -> float:
    """כמה מוניטין הזוגיות מוסיפה לך בשבוע. מפורסמת = כותרות."""
    row = partner(game)
    if not row:
        return 0.0
    if row["mood"] < 30:
        return 0.0
    return (row["spotlight"] / 100.0) * 0.22


def family_line(game) -> str:
    """שורה אחת שמסכמת את הבית — למסך הראשי."""
    row = partner(game)
    par = parents(game)
    bits = [f"ההורים: {_pride_word(par['pride'])}"]
    if row:
        bits.append(f"{row['name']} — {stage_name(row)}, {_mood_word(row['mood'])}")
        if row["kids"]:
            bits.append(f"{row['kids']} ילדים")
    return " · ".join(bits)


def _pride_word(pride: float) -> str:
    if pride >= 85:
        return "לא מפסיקים לספר עליך"
    if pride >= 65:
        return "גאים בך"
    if pride >= 45:
        return "בסדר, אבל מרגישים רחוקים"
    return "נפגעו, ולא אומרים"


def _mood_word(mood: float) -> str:
    if mood >= 80:
        return "מצוין"
    if mood >= 60:
        return "טוב"
    if mood >= 40:
        return "מתוח"
    if mood >= 25:
        return "רע"
    return "על הקצה"


# ---------------------------------------------------------------------------
# השבוע
# ---------------------------------------------------------------------------

def weekly(game, rng: random.Random) -> List[str]:
    """מה קרה בבית השבוע.

    ההגרלה קודמת לבנייה: קודם מחליטים אם יש אירוע, ורק אחר כך בונים
    את הטקסט.
    """
    out: List[str] = []
    out.extend(_partner_week(game, rng))
    out.extend(_parents_week(game, rng))
    return out


def _partner_week(game, rng: random.Random) -> List[str]:
    row = partner(game)
    if not row:
        return []
    me = game.me
    row["weeks"] += 1

    # שחיקה: זמן לבד, עצימות גבוהה, והפסדים
    drift = DRIFT_PER_WEEK
    if game.intensity >= NEGLECT_INTENSITY:
        drift += 0.8
    if me.morale < 40:
        drift += 0.5
    # מי שמבין ספורט סופג פחות מהשבוע הקשה
    drift *= 1.25 - (row["support"] / 100.0) * 0.55
    row["mood"] = clamp(row["mood"] - drift, 0, 100)

    # ההשפעה עצמה — קטנה בשבוע, גדולה לאורך עונה
    bonus = support_bonus(game)
    me.morale = clamp(me.morale + bonus, 5, 99)
    if bonus > 1.4:
        me.resilience = clamp(me.resilience + 0.05, 0, 100)
    me.reputation = clamp(me.reputation + spotlight_bonus(game), 0, 100)

    if row["mood"] > BREAKUP_MOOD:
        return _partner_event(game, row, rng)

    # מתחת לסף — סכנה אמיתית, ואזהרה לפני
    if rng.random() < BREAKUP_CHANCE:
        name = row["name"]
        game.flags.pop("partner", None)
        game.flags["heartbreak"] = 8
        me.morale = clamp(me.morale - 16, 5, 99)
        return [f"💔 {name} עזבה. \"אני לא מתחרה בכדורגל, ואני לא רוצה.\""]
    return [f"⚠️ {row['name']} אמרה שאתם לא נפגשים. זה לא היה שקט."]


def _partner_event(game, row: Dict[str, Any], rng: random.Random) -> List[str]:
    """אירוע קטן מהבית. נדיר מספיק כדי שלא יהפוך לרעש."""
    if rng.random() > 0.09:
        return []
    name = row["name"]
    pool = []
    if row["spotlight"] >= 60:
        pool.append(("📸 צילמו אתכם יוצאים ממסעדה. הכותרת לא עסקה בכדורגל.",
                     {"reputation": 1.2}))
    if row["support"] >= 70:
        pool.append((f"🏠 {name} חיכתה ער עד שחזרת מהמשחק. "
                     f"זה נשמע קטן, וזה לא.", {"morale": 3.0}))
    pool.append((f"🍽️ ערב בלי טלפונים עם {name}.", {"mood": 6.0}))
    if row["stage"] in ("engaged", "married"):
        pool.append((f"👨‍👩‍👦 {name} שאלה מתי מתכננים קדימה.", {"mood": -3.0}))
    text, effect = rng.choice(pool)
    _apply(game, row, effect)
    return [text]


def _apply(game, row: Optional[Dict[str, Any]], effect: Dict[str, float]) -> None:
    me = game.me
    if "morale" in effect:
        me.morale = clamp(me.morale + effect["morale"], 5, 99)
    if "reputation" in effect:
        me.reputation = clamp(me.reputation + effect["reputation"], 0, 100)
    if "mood" in effect and row:
        row["mood"] = clamp(row["mood"] + effect["mood"], 0, 100)


def _parents_week(game, rng: random.Random) -> List[str]:
    """ההורים מבקשים משהו — לא כל שבוע, ורק כשיש מה לבקש."""
    if game.stage not in ("academy", "player", "veteran"):
        return []
    par = parents(game)
    if par.get("ask"):
        return []
    left = [row for row in PARENT_ASKS if row[0] not in par["given"]]
    if not left:
        return []
    # ככל שאתה מרוויח יותר, כך הבקשות מגיעות מוקדם יותר
    chance = 0.012 + min(0.03, game.money / 40_000_000.0)
    if rng.random() > chance:
        return []
    key, name, why, cost, pride = rng.choice(left)
    par["ask"] = {"key": key, "name": name, "why": why,
                  "cost": cost, "pride": pride}
    par["asked"] += 1
    return [f"📞 אבא שלך התקשר. {why} ({name} — בתפריט: 'חיים')"]


def grant_ask(game) -> str:
    """נותן להורים את מה שביקשו. עולה כסף ומחזיר גאווה — ולא רק."""
    par = parents(game)
    ask = par.get("ask")
    if not ask:
        return "אין בקשה פתוחה."
    if game.money < ask["cost"]:
        return f"אין לך ₪{ask['cost']:,}. עוד לא."
    game.spend_money(ask["cost"])
    par["given"] = par["given"] + [ask["key"]]
    par["pride"] = clamp(par["pride"] + ask["pride"], 0, 100)
    par["ask"] = None
    game.me.morale = clamp(game.me.morale + 6, 5, 99)
    return f"✅ {ask['name']} — ₪{ask['cost']:,}. אמא שלך בכתה בטלפון."


def decline_ask(game) -> str:
    """מסרב. זה לגיטימי, וזה עולה."""
    par = parents(game)
    ask = par.get("ask")
    if not ask:
        return "אין בקשה פתוחה."
    par["ask"] = None
    par["pride"] = clamp(par["pride"] - 9, 0, 100)
    return "אמרת שעכשיו לא. הוא אמר \"בסדר, בסדר\" וניתק מהר מדי."


# ---------------------------------------------------------------------------
# מה אתה יכול לעשות
# ---------------------------------------------------------------------------

def actions(game) -> List[Dict[str, Any]]:
    """מה פתוח לך עכשיו בחיים האישיים, ומה זה עולה."""
    out: List[Dict[str, Any]] = []
    row = partner(game)
    par = parents(game)

    if par.get("ask"):
        ask = par["ask"]
        out.append({"key": "grant", "name": f"לתת: {ask['name']}",
                    "cost": ask["cost"], "note": ask["why"]})
        out.append({"key": "decline", "name": "להגיד שעכשיו לא",
                    "cost": 0, "note": "הם יבינו. פחות ממה שהם יגידו."})

    if not row:
        return out

    out.append({"key": "gift", "name": f"מתנה ל{row['name']}",
                "cost": GIFT_COST, "note": "לא פותר, אבל עוזר."})
    out.append({"key": "holiday", "name": "לקחת חופשה ביחד",
                "cost": HOLIDAY_COST,
                "note": "שבוע בלי כדורגל. הגוף גם ירוויח."})
    nxt = next_stage(row["stage"])
    if nxt and row["weeks"] >= _stage_wait(row["stage"]) and row["mood"] >= 62:
        cost = RING_COST if nxt == "engaged" else WEDDING_COST if nxt == "married" else 0
        out.append({"key": "advance", "name": _advance_name(nxt),
                    "cost": cost, "note": "צעד גדול. אין דרך חזרה."})
    if row["stage"] == "married" and row["kids"] < 3 and row["mood"] >= 60:
        out.append({"key": "child", "name": "להביא ילד",
                    "cost": 0, "note": "החיים ישתנו. גם המשחק."})
    return out


def _stage_wait(stage: str) -> int:
    for key, _, weeks in STAGES:
        if key == stage:
            return weeks
    return 0


def _advance_name(stage: str) -> str:
    return {"serious": "להפוך את זה לרציני",
            "engaged": "להציע נישואין",
            "married": "להתחתן"}.get(stage, "להתקדם")


def do_action(game, key: str) -> str:
    """מבצע פעולה מהרשימה. מחזיר מה קרה."""
    if key == "grant":
        return grant_ask(game)
    if key == "decline":
        return decline_ask(game)

    row = partner(game)
    if not row:
        return "אין למי."

    if key == "gift":
        if game.money < GIFT_COST:
            return "אין לך מספיק."
        game.spend_money(GIFT_COST)
        row["gifts"] += 1
        # מתנה חמישית כבר לא מרגשת אף אחד
        gain = max(3.0, 12.0 - row["gifts"] * 1.5)
        row["mood"] = clamp(row["mood"] + gain, 0, 100)
        return f"🎁 {row['name']} שמחה. (+{gain:.0f} למצב הקשר)"

    if key == "holiday":
        if game.money < HOLIDAY_COST:
            return "אין לך מספיק."
        game.spend_money(HOLIDAY_COST)
        row["mood"] = clamp(row["mood"] + 22, 0, 100)
        game.me.fitness = clamp(game.me.fitness + 12, 0, 100)
        game.me.morale = clamp(game.me.morale + 8, 5, 99)
        game.me.sharpness = clamp(game.me.sharpness - 6, 0, 100)
        return (f"✈️ שבוע איתה, בלי טלפונים. חזרת רענן ופחות חד — "
                f"וזה שווה את זה.")

    if key == "advance":
        nxt = next_stage(row["stage"])
        if not nxt:
            return "אין לאן."
        cost = RING_COST if nxt == "engaged" else WEDDING_COST if nxt == "married" else 0
        if cost and game.money < cost:
            return f"זה עולה ₪{cost:,}. עוד לא."
        if cost:
            game.spend_money(cost)
        row["stage"] = nxt
        row["weeks"] = 0
        row["mood"] = clamp(row["mood"] + 14, 0, 100)
        game.me.morale = clamp(game.me.morale + 10, 5, 99)
        if row["spotlight"] >= 55:
            game.me.reputation = clamp(game.me.reputation + 2.5, 0, 100)
        return {"serious": f"אתם ביחד. {row['name']} עברה לגור אצלך.",
                "engaged": f"💍 היא אמרה כן. הטלפון שלך התפוצץ.",
                "married": f"💒 התחתנתם. חצי מהסגל היה שם."}[nxt]

    if key == "child":
        row["kids"] += 1
        row["mood"] = clamp(row["mood"] + 10, 0, 100)
        game.me.morale = clamp(game.me.morale + 12, 5, 99)
        # לילה ראשון בבית עם תינוק — הגוף יודע
        game.me.fitness = clamp(game.me.fitness - 10, 0, 100)
        return ("👶 נולד לכם ילד. חגגת את השער הבא עם אצבע באוויר, "
                "וכולם הבינו.")
    return "לא ידוע."


# ---------------------------------------------------------------------------
# פרידה שנמשכת
# ---------------------------------------------------------------------------

def heartbreak_tick(game) -> Optional[str]:
    """פרידה לא נגמרת בשבוע. זה נגרר, וזה נמדד."""
    weeks = int(game.flags.get("heartbreak", 0) or 0)
    if weeks <= 0:
        return None
    game.flags["heartbreak"] = weeks - 1
    me = game.me
    me.morale = clamp(me.morale - 1.6, 5, 99)
    me.sharpness = clamp(me.sharpness - 0.8, 0, 100)
    if weeks == 1:
        return "🙂 מתחיל להיות בסדר. הראש חזר למגרש."
    return None
