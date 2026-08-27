# -*- coding: utf-8 -*-
"""
football_manager.agents
=======================
סוכנים — מי שמזיז את השוק כשאתה ישן.

עד כאן השוק היה הוגן: מועדונים ראו אותך, שקלו, והציעו. זה נקי, וזו
בדיוק הבעיה — **הכול צפוי**. במציאות יש בין השחקן למועדון אדם שלישי
שהאינטרס שלו לא זהה לשלך, ומה שהוא עושה בין שני טלפונים משנה קריירות.

מה שיש כאן:

* **ארבעה טיפוסים, וכל אחד משחק אחרת.** לכריש יש טווח עצום ואפס
  בושה; לסוכן המשפחה יש עמלה נמוכה ואין לו קשרים; המקושר פותח דלתות
  בחו"ל; הטירון לומד איתך וגדל איתך.
* **הסוכן פועל לבד.** כל שבוע הוא בוחר מהלך — לייצר עניין יש מאין,
  לדלוף לעיתונות כדי ללחוץ, לדחוף הצעה קיימת, או **לחבל** אצל מועדון
  יריב כדי לפנות מקום.
* **לחבל זה להסתכן.** חבלה שנחשפת עולה במוניטין, באמון המאמן,
  ולפעמים בהצעה עצמה. הסוכן לא מספר לך מראש.
* **הוא גובה.** אחוז מהשכר ואחוז מהמענק, כל שבוע, בלי לשאול.
* **גם לו יש דעה עליך.** סוכן שלא סוגר עסקאות מאבד עניין ועוזב.

הכלל שמנחה את הקובץ: **הגרלה קודם, בנייה אחר כך.** אל תבנה מהלך ואז
תזרוק אותו — זה מבזבז זמן ומזיז את זרם המספרים האקראיים בלי סיבה.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from . import data as D
from . import press as PR
from . import transfers as TR
from .models import Club, clamp

# (מפתח, שם, תיאור, עמלה%, טווח, תוקפנות, נאמנות)
#
# טווח   — כמה גבוה הוא מגיע. 1.0 = מועדוני צמרת אירופה בהישג יד.
# תוקפנות — כמה הוא מוכן ללכת רחוק: דליפות, חבלה, לשרוף גשרים.
# נאמנות  — כמה הוא נשאר איתך כשאתה לא מוכר.
AGENT_TYPES = [
    ("family", "סוכן המשפחה", "עורך דין שהאבא שלך מכיר. לא יעשה לך נזק, וגם לא נס.",
     3.0, 0.28, 0.10, 0.95),
    ("rookie", "הטירון", "התיק הראשון שלו זה אתה. רעב, לומד מהר, עוד לא מכיר אף אחד.",
     4.0, 0.34, 0.35, 0.80),
    ("connected", "המקושר", "מכיר מנהלים ספורטיביים בשם הפרטי. שיחה אחת פותחת דלת.",
     7.0, 0.82, 0.45, 0.55),
    ("shark", "הכריש", "יוציא לך חוזה חלומות ויעשה את זה על גופות. גם על שלך, אם צריך.",
     11.0, 0.95, 0.90, 0.30),
    ("super", "הסופר־סוכן", "מנהל תיק של ארבעים כוכבים. אתה מספר ארבעים ואחת — עד שלא.",
     9.0, 1.00, 0.70, 0.45),
]
AGENT_NAMES = {key: name for key, name, _, _, _, _, _ in AGENT_TYPES}
AGENT_BY_KEY = {row[0]: row for row in AGENT_TYPES}

# הסופר־סוכן לא לוקח כל אחד. מתחת לזה הוא לא מחזיר טלפון.
SUPER_AGENT_FAME = 72.0

# שמות פרטיים לסוכנים. הם דמויות, ולכן יש להם שם ולא רק תפקיד.
AGENT_FIRST = ["רוני", "איציק", "ז'אן", "מרקו", "דודו", "אבי", "פאולו",
               "שרון", "ליאור", "ז'ילבר", "אמיר", "טוני", "ניר", "סמי"]
AGENT_LAST = ["ברזילי", "מנשה", "לוינסון", "דה סילבה", "אזולאי", "קרן",
              "מורנו", "שגב", "בן־חיים", "רוסו", "אלמליח", "פישר"]

# כמה מהלכים הסוכן עושה לפני שהוא מתעייף מהשבוע
MOVE_CHANCE = 0.30        # הסיכוי הבסיסי שבכלל קורה משהו בשבוע
SABOTAGE_EXPOSURE = 0.32  # כמה מהחבלות נחשפות בסוף

CANDIDATES = 3            # כמה סוכנים מציעים לך את עצמם בכל פנייה


# ---------------------------------------------------------------------------
# מי הסוכן שלך
# ---------------------------------------------------------------------------

def agent(game) -> Optional[Dict[str, Any]]:
    data = game.flags.get("agent")
    return data if isinstance(data, dict) else None


def has_agent(game) -> bool:
    return agent(game) is not None


def agent_type(row: Optional[Dict[str, Any]]):
    if not row:
        return None
    return AGENT_BY_KEY.get(row.get("kind"), AGENT_BY_KEY["family"])


def cut_percent(game) -> float:
    """כמה אחוז מהשכר הסוכן לוקח."""
    row = agent(game)
    if not row:
        return 0.0
    return float(row.get("cut", agent_type(row)[3]))


def agent_cut(game, gross: int) -> int:
    """העמלה על סכום. נקראת גם על שכר שבועי וגם על מענק חתימה."""
    return int(gross * cut_percent(game) / 100.0)


def reach(game) -> float:
    row = agent(game)
    if not row:
        return 0.20          # בלי סוכן מגיעים רק למי שראה אותך במגרש
    return float(agent_type(row)[4])


def make_agent(kind: str, rng: random.Random) -> Dict[str, Any]:
    """סוכן חדש. העמלה מתנדנדת סביב הבסיס — אין שני סוכנים זהים."""
    key, name, desc, cut, span, aggression, loyalty = AGENT_BY_KEY[kind]
    return {
        "kind": key,
        "name": f"{rng.choice(AGENT_FIRST)} {rng.choice(AGENT_LAST)}",
        "cut": round(cut * rng.uniform(0.85, 1.2), 1),
        "trust": rng.randint(50, 70),   # מה הוא חושב עליך
        "deals": 0,                     # כמה עסקאות סגר בשבילך
        "burned": [],                   # מועדונים שהוא שרף
        "moves": [],                    # יומן קצר של המהלכים האחרונים
        "since": 0,
    }


def market(game, rng: random.Random) -> List[Dict[str, Any]]:
    """מי מוכן לייצג אותך עכשיו. שלושה, ולא אותם שלושה תמיד."""
    fame = _fame(game)
    pool = [key for key, *_ in AGENT_TYPES if key != "super"]
    if fame >= SUPER_AGENT_FAME:
        pool.append("super")
    # שחקן אלמוני לא מעניין את המקושר, ובטח לא את הכריש
    if fame < 18:
        pool = [k for k in pool if k in ("family", "rookie")]
    elif fame < 34:
        pool = [k for k in pool if k != "shark"]
    rng.shuffle(pool)
    return [make_agent(kind, rng) for kind in pool[:CANDIDATES]]


def _fame(game) -> float:
    """כמה גדול השם שלך — הסולם שמחליט מי בכלל מחזיר לך טלפון."""
    me = game.me
    club = game.my_club
    score = me.reputation
    if club:
        # המועדון עוזר, אבל השם הוא שלך. במשקל 0.25 שחקן בינוני
        # במועדון גדול קיבל סופר־סוכן, וזה עשה את הסולם חסר משמעות.
        score += club.reputation * 0.14
    score += len(game.honours) * 4
    return score


def sign(game, row: Dict[str, Any]) -> str:
    """חותם עם סוכן. אם היה קודם — הוא לא לוחץ ידיים בדרך החוצה."""
    old = agent(game)
    row = dict(row)
    row["since"] = game.year
    game.flags["agent"] = row
    kind = agent_type(row)
    if old:
        return (f"🤝 {row['name']} מחליף את {old['name']}. "
                f"{kind[1]} — {row['cut']}% מהשכר.")
    return f"🤝 חתמת עם {row['name']}. {kind[1]}, {row['cut']}% מהשכר."


def leave(game, reason: str = "") -> str:
    row = agent(game)
    game.flags.pop("agent", None)
    if not row:
        return ""
    return f"👋 {row['name']} כבר לא מייצג אותך. {reason}".strip()


def describe(game) -> List[str]:
    """הסוכן בשורות, למסך."""
    row = agent(game)
    if not row:
        return ["אין לך סוכן. אתה מנהל את הקריירה שלך לבד — "
                "וזה נראה בכמות ההצעות."]
    kind = agent_type(row)
    out = [f"{row['name']} · {kind[1]}",
           kind[2],
           f"עמלה {row['cut']}% מהשכר ומהמענקים",
           f"טווח: {_reach_word(kind[4])}",
           f"מה הוא חושב עליך: {_trust_word(row['trust'])}"]
    if row["deals"]:
        out.append(f"סגר בשבילך {row['deals']} עסקאות")
    if row["burned"]:
        names = ", ".join(game.clubs[c].name for c in row["burned"]
                          if c in game.clubs)
        if names:
            out.append(f"שרוף מולם: {names}")
    return out


def _reach_word(span: float) -> str:
    if span >= 0.9:
        return "כל מועדון באירופה"
    if span >= 0.7:
        return "צמרת אירופה בהישג יד"
    if span >= 0.32:
        return "הליגה המקומית, ולפעמים מעבר"
    return "מה שמסביב"


def _trust_word(trust: float) -> str:
    if trust >= 78:
        return "אתה התיק הכי חשוב שלו"
    if trust >= 58:
        return "מרוצה, עובד בשבילך"
    if trust >= 38:
        return "מתחיל לאבד עניין"
    return "מחזיק בך מהרגל"


# ---------------------------------------------------------------------------
# מה הסוכן עושה השבוע
#
# הכלל שנלמד בדם: **סוכן שעושה כל שבוע את אותו מהלך הוא רעש, לא דמות.**
# לכן הוא לא "מייצר עניין" בכל פעם מחדש אצל מועדון אקראי — הוא מנהל
# קמפיין: בוחר יעד אחד, עובד עליו לאורך שבועות, ומספר לך בכל פעם על
# שלב אחר בתהליך. כשהיעד בשל — הוא עובר ליעד הבא.
# ---------------------------------------------------------------------------

CAMPAIGN_READY = 74.0     # מעל זה המועדון כבר מוכן להניח הצעה
CAMPAIGN_MAX_WEEKS = 9    # אחרי זה הוא מוותר על היעד ועובר הלאה

# שלבי הקמפיין. כל שלב הוא משפט אחר, כדי שאותו מהלך לא ייקרא אותו דבר.
# תשעה שלבים ולא חמישה, כי `CAMPAIGN_MAX_WEEKS` הוא 9 — ברשימה קצרה
# יותר הקמפיין מתחיל להתחיל מהתחלה מול אותו מועדון, וזה נשמע כמו תקלה.
CAMPAIGN_STEPS = [
    ("שלח להם קלטת של שלושה משחקים.", 9),
    ("דיבר עם המנהל הספורטיבי שלהם. הם שאלו על החוזה.", 11),
    ("סידר שיבואו לראות אותך חי.", 13),
    ("ישב איתם ארוחת צהריים ארוכה מדי מכדי שתהיה נימוסית.", 12),
    ("אמר להם שיש עוד מישהו בתמונה. זה לא היה מדויק.", 15),
    ("העביר להם נתונים שהוא הזמין מחברת אנליזה.", 10),
    ("דאג שהשם שלך יעלה בישיבת הרכש שלהם.", 14),
    ("הביא את המאמן שלהם לשיחת טלפון של שתי דקות.", 16),
    ("אמר להם שהחלון נסגר, וששאלו עליך גם ממקום אחר.", 13),
]


def weekly(game, rng: random.Random) -> List[str]:
    """המהלך של הסוכן, אם בכלל.

    ההגרלה קודמת לבנייה: קודם מחליטים אם קורה משהו ואיזה מהלך, ורק
    אחר כך בונים אותו.
    """
    row = agent(game)
    if not row or game.stage not in ("academy", "player", "veteran"):
        return []

    kind = agent_type(row)
    live = TR.live_offers(game)
    chance = MOVE_CHANCE * (0.55 + kind[5])
    if live:
        chance *= 1.8                            # יש עסקה על השולחן — הוא ער
    if rng.random() > min(0.55, chance):
        return _idle(game, row, rng)

    moves: List[str] = []
    if live:
        moves += ["push", "push"]
        if len(live) >= 2 and kind[5] >= 0.45:
            moves += ["sabotage", "sabotage"]
    else:
        moves += ["campaign", "campaign", "campaign"]
    if kind[5] >= 0.35:
        moves.append("leak")

    move = rng.choice(moves)
    if move == "campaign":
        return _campaign(game, row, rng)
    if move == "push":
        return _push(game, row, rng, live)
    if move == "leak":
        return _leak(game, row, rng)
    return _sabotage(game, row, rng, live)


def _idle(game, row: Dict[str, Any], rng: random.Random) -> List[str]:
    """שבוע שקט. סוכן שלא רואה תנועה מתחיל להתקרר — לאט."""
    kind = agent_type(row)
    row["trust"] = clamp(row["trust"] - 0.10 * (1.4 - kind[6]), 0, 100)
    if row["trust"] > 20 or row["deals"] > 0 or rng.random() > 0.05:
        return []
    return [leave(game, "\"תתקשר כשיהיה מה למכור.\"")]


# ---------------------------------------------------------------------------
# קמפיין: יעד אחד, כמה שבועות
# ---------------------------------------------------------------------------

def _candidate_clubs(game, span: float) -> List[Club]:
    """מי בטווח של הסוכן ועוד לא על השולחן."""
    me = game.me
    taken = {o["cid"] for o in TR.open_offers(game)}
    mine = me.club_id
    out = []
    for club in game.clubs.values():
        if club.cid in taken or club.cid == mine:
            continue
        # טווח הסוכן חוסם למעלה: מועדון עשיר מדי לא עונה לטלפון
        if club.reputation > 55 + span * 48:
            continue
        if club.reputation < me.overall - 26:
            continue                       # קטן מכדי שיהיה מעניין
        out.append(club)
    return out


def _pick_target(game, row: Dict[str, Any], rng: random.Random) -> Optional[Club]:
    kind = agent_type(row)
    pool = [c for c in _candidate_clubs(game, kind[4])
            if c.cid not in row["burned"] and c.cid != row.get("target")]
    if not pool:
        return None
    # ככל שהטווח גדול יותר, כך הוא מכוון גבוה יותר
    pool.sort(key=lambda c: -c.reputation)
    top = pool[:max(2, int(len(pool) * (0.15 + kind[4] * 0.4)))]
    return rng.choice(top)


def _campaign(game, row: Dict[str, Any], rng: random.Random) -> List[str]:
    """עובד על יעד אחד לאורך שבועות, ומדווח בכל פעם על שלב אחר."""
    book = game.flags.setdefault("scout_interest", {})
    target = row.get("target")
    heat = float(book.get(target, 0.0)) if target else 0.0
    stale = row.get("target_weeks", 0) >= CAMPAIGN_MAX_WEEKS
    # "הם מוכנים" נאמר פעם אחת. בלי הדגל הזה ההתעניינות דועכת שבוע
    # אחרי, הקמפיין מרים אותה חזרה, והשורה חוזרת על עצמה.
    ready = row.get("target_done") or heat >= CAMPAIGN_READY

    if target not in game.clubs or ready or stale:
        done = target in game.clubs and ready
        row["target_done"] = False
        club = _pick_target(game, row, rng)
        if not club:
            return []
        row["target"] = club.cid
        row["target_weeks"] = 0
        row["moves"] = (row.get("moves", []) + [f"פתח תיק: {club.name}"])[-5:]
        tag = D.club_tag(club.cid, club.league_id)
        opener = (f"📞 {row['name']}: \"סגרנו את {game.clubs[target].name}. "
                  f"עכשיו {club.name}.\"" if done else
                  f"📞 {row['name']} התחיל לעבוד על {club.name}. {tag}")
        return [opener]

    club = game.clubs[target]
    step = row.get("target_weeks", 0)
    text, gain = CAMPAIGN_STEPS[step % len(CAMPAIGN_STEPS)]
    row["target_weeks"] = step + 1
    book[target] = clamp(heat + gain * (0.7 + agent_type(row)[4] * 0.5), 0, 100)
    if book[target] >= CAMPAIGN_READY:
        row["target_done"] = True
        return [f"📞 {row['name']}: \"{club.name} מוכנים. הם יניחו הצעה.\""]
    return [f"📞 {row['name']} {text} ({club.name})"]


def _push(game, row: Dict[str, Any], rng: random.Random,
          live: List[Dict[str, Any]]) -> List[str]:
    """דוחף הצעה קיימת למעלה בלי שביקשת. לפעמים זה עובד."""
    if not live:
        return _manufacture(game, row, rng)
    kind = agent_type(row)
    offer = rng.choice(live)
    club = game.clubs.get(offer["cid"])
    name = club.name if club else "המועדון"
    # הצלחה תלויה בטווח ובתוקפנות, ובכמה כבר לחצו עליהם
    chance = clamp(0.24 + kind[4] * 0.30 + kind[5] * 0.18
                   - offer["asks"] * 0.09, 0.05, 0.82)
    if rng.random() < chance:
        before = offer["wage"]
        offer["wage"] = int(min(offer["ceiling"], offer["wage"] * 1.11))
        offer["state"] = "improved"
        if offer["wage"] <= before:
            offer["bonus"] = int(offer["bonus"] * 1.25)
            return [f"📈 {row['name']} סחט מ{name} מענק גדול יותר: "
                    f"₪{offer['bonus']:,}."]
        return [f"📈 {row['name']} טלפן ל{name} בלי לשאול אותך. "
                f"₪{offer['wage']:,} לשבוע במקום ₪{before:,}."]
    offer["patience"] -= 1
    if offer["patience"] <= 0:
        offer["state"] = "withdrawn"
        row["trust"] = clamp(row["trust"] - 6, 0, 100)
        return [f"❌ {row['name']} לחץ יותר מדי. {name} ירדו מהעסקה."]
    return [f"😐 {row['name']} ניסה על {name} ונענה \"זה מה שיש\"."]


def _leak(game, row: Dict[str, Any], rng: random.Random) -> List[str]:
    """דליפה לעיתונות — לוחצת על המועדון, ומרגיזה אותו."""
    kind = agent_type(row)
    club = game.my_club
    live = TR.live_offers(game)
    interest = game.flags.get("scout_interest") or {}
    target = None
    if live:
        target = game.clubs.get(live[0]["cid"])
    elif interest:
        best = max(interest.items(), key=lambda kv: kv[1])
        target = game.clubs.get(best[0])
    if not target:
        return []

    # דרך `PR.push` ולא ביד: הוא זה שיודע מה הצורה של פריט בפיד
    # (מפתח, שנה, שבוע, האם נענה) ומה אורך הפיד.
    PR.push(game, {"key": "agent_leak", "source": "insider", "true": True,
                   "text": f"מקורב לשחקן: \"יש קשר עם {target.name}, "
                           f"והשחקן פתוח לשמוע.\""})

    out = [f"📰 {row['name']} דלף לעיתונות. הכותרת יצאה: \"{target.name} "
           f"בודקים אותך.\""]
    # המועדון שלך קורא עיתונים
    if club and rng.random() < 0.55 + kind[5] * 0.25:
        club.manager_trust = clamp(club.manager_trust - 4.5, 0, 100)
        out.append(f"😠 ב{club.name} לא אהבו את הכותרת.")
    # אבל הלחץ עובד: המתעניין מרגיש שהוא חייב לזוז
    cur = game.flags.setdefault("scout_interest", {})
    cur[target.cid] = clamp(float(cur.get(target.cid, 0.0)) + 9, 0, 100)
    return out


def _sabotage(game, row: Dict[str, Any], rng: random.Random,
              live: List[Dict[str, Any]]) -> List[str]:
    """מחסל הצעה מתחרה כדי לפנות מקום לזו שמשלמת לו יותר.

    זה המהלך שהופך סוכן לדמות ולא לצינור: הוא עושה את זה בלי לשאול,
    זה מיטיב איתך בטווח הקצר, וכשזה נחשף אתה משלם — לא הוא.
    """
    if len(live) < 2:
        return _push(game, row, rng, live)
    kind = agent_type(row)
    if kind[5] < 0.25:
        return _push(game, row, rng, live)      # סוכן המשפחה לא עושה כאלה

    best = live[0]
    victim = rng.choice(live[1:])
    vclub = game.clubs.get(victim["cid"])
    bclub = game.clubs.get(best["cid"])
    if not vclub or not bclub:
        return []

    victim["state"] = "withdrawn"
    victim["log"].append("🕳️ נעלמו בלי הסבר")
    best["wage"] = int(min(best["ceiling"], best["wage"] * 1.07))
    best["state"] = "improved"
    row["burned"] = (row["burned"] + [vclub.cid])[-6:]
    row["moves"] = (row["moves"] + [f"חיסל את {vclub.name}"])[-5:]

    out = [f"🕳️ {vclub.name} ירדו מהעסקה בלי הסבר. "
           f"{row['name']} לא נראה מופתע."]

    if rng.random() < SABOTAGE_EXPOSURE + kind[5] * 0.12:
        game.me.reputation = clamp(game.me.reputation - 3.5, 0, 100)
        club = game.my_club
        if club:
            club.manager_trust = clamp(club.manager_trust - 6, 0, 100)
        PR.push(game, {"key": "agent_exposed", "source": "insider", "true": True,
                       "text": f"\"הסוכן של השחקן טרפד את המהלך של "
                               f"{vclub.name}.\" בחדרי חדרים כועסים."})
        out.append("🔥 זה יצא החוצה. \"ככה לא עובדים\" — וזה נדבק בך, לא בו.")
    return out


# ---------------------------------------------------------------------------
# מה קורה כשנסגרת עסקה
# ---------------------------------------------------------------------------

def on_deal(game, offer: Dict[str, Any]) -> List[str]:
    """הסוכן גובה את שלו ברגע החתימה, ומרוצה בהתאם."""
    row = agent(game)
    if not row:
        return []
    row["deals"] += 1
    row["trust"] = clamp(row["trust"] + 9, 0, 100)
    fee = agent_cut(game, offer.get("bonus", 0))
    if fee <= 0:
        return [f"🤝 {row['name']} סגר. \"אמרתי לך שאני עובד.\""]
    game.spend_money(fee)
    return [f"🤝 {row['name']} סגר את העסקה ולקח ₪{fee:,} מהמענק."]
