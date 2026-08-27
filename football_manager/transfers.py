# -*- coding: utf-8 -*-
"""
football_manager.transfers
==========================
שוק העברות עם משא ומתן אמיתי.

עד כאן ההעברה הייתה שורה אחת: מועדון אחד, סכום אחד, כן או לא. זה לא
מה שקורה כשקבוצה רוצה שחקן — ובעיקר זה לא מעניין, כי לשחקן אין שום
החלטה לקבל מלבד "להסכים" או "לא".

מה שיש כאן במקום:

* **כמה הצעות במקביל.** טבלה להשוות בה, לא הודעה יחידה.
* **משא ומתן על כל סעיף.** שכר, שנים, מענק חתימה, סעיף שחרור, תפקיד
  מובטח בסגל, אחוזי דימוי. כל אחד מהם ידית נפרדת.
* **סיכון.** לכל מועדון יש סבלנות ותקציב. בקשה גדולה מדי שורפת הצעה,
  ולפעמים המועדון פשוט קם מהשולחן.
* **מינוף.** שתי הצעות מתחרות שוות יותר מאחת — כשמישהו משפר, היריב
  שומע על זה ומשפר בחזרה. זה מה שהופך שוק לשוק.
* **דדליין.** חלון נסגר, והצעה שלא סגרת נעלמת.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from . import data as D
from .models import Club, Player, clamp, wage_for_overall

# תפקיד מובטח בסגל — מה שהמועדון מתחייב לו כשהוא מחתים אותך
SQUAD_ROLES = [
    ("star", "איש הקבוצה", 1.35),
    ("starter", "שחקן הרכב", 1.12),
    ("rotation", "רוטציה", 0.92),
    ("prospect", "לעתיד", 0.78),
]
ROLE_NAMES = {key: name for key, name, _ in SQUAD_ROLES}
ROLE_VALUE = {key: value for key, _, value in SQUAD_ROLES}

# הסעיפים שאפשר לבקש עליהם יותר
TERMS = [
    ("wage", "שכר שבועי"),
    ("years", "אורך חוזה"),
    ("bonus", "מענק חתימה"),
    ("clause", "סעיף שחרור"),
    ("role", "תפקיד בסגל"),
    ("image", "אחוזי דימוי"),
    ("minutes", "התחייבות לדקות"),
    ("loyalty", "מענק נאמנות"),
    ("family", "חבילה למשפחה"),
]
TERM_NAMES = dict(TERMS)

WINDOW_WEEKS = 4          # כמה שבועות הדלת פתוחה


# ---------------------------------------------------------------------------
# עילוי
#
# "שחקן שנחשב לעילוי — קופצים עליו מכל כיוון ומציעים לו עולם ומלואו."
# זה לא קורה מעצמו: מועדון עשיר לא מציע פי שלושה כי הדירוג עלה בשתיים,
# הוא מציע פי שלושה כי **כולם רוצים אותו והוא בן תשע־עשרה**. הציון כאן
# הוא בדיוק זה — גיל, מרווח לפוטנציאל, ביצועים ורעש בשוק.
# ---------------------------------------------------------------------------

WONDERKID_AGE = 23          # מעל זה כבר לא מדובר בהימור על העתיד
FRENZY_MIN = 0.50           # מאיזה ציון השוק מתחיל להתנהג אחרת


def hype(game) -> float:
    """כמה השם שלך "בוער". נבנה מפגישות, כתבות וקרבות רכש."""
    try:
        return float(game.flags.get("hype", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def wonderkid_score(game) -> float:
    """0-1: כמה השוק רואה בך עילוי ולא עוד שחקן טוב.

    המרווח לפוטנציאל הוא הרכיב הכבד: בן 19 עם 74 ותקרה 92 שווה יותר
    בעיני מועדון־על מבן 27 עם 84 ותקרה 85. זה מה שמייצר את הטירוף.
    """
    me = game.me
    if me.age > WONDERKID_AGE:
        return 0.0
    # +2 כדי שבן 19 עדיין ייחשב עילוי. בלי זה הגיל אכל את הציון
    # בדיוק בשנים שבהן השוק באמת משתגע.
    youth = clamp((WONDERKID_AGE - me.age + 2) / 8.0, 0.0, 1.0)
    headroom = clamp((me.potential - me.overall) / 18.0, 0.0, 1.0)
    quality = clamp((me.overall - 58) / 30.0, 0.0, 1.0)
    noise = clamp(hype(game) / 100.0, 0.0, 1.0)
    # בלי משחקים בעונה — ניטרלי. אפס היה מעניש על תחילת עונה.
    rating = 0.4
    if me.season.apps >= 4:
        rating = clamp((me.season.avg_rating - 6.6) / 1.4, 0.0, 1.0)
    score = (youth * 0.26 + headroom * 0.26 + quality * 0.24
             + noise * 0.14 + rating * 0.10)
    return clamp(score, 0.0, 1.0)


def frenzy(game) -> float:
    """מכפיל הטירוף. 1.0 = שוק רגיל; 2.6 = כל אירופה על הדלת."""
    score = wonderkid_score(game)
    if score < FRENZY_MIN:
        return 1.0
    return 1.0 + (score - FRENZY_MIN) / (1.0 - FRENZY_MIN) * 1.6


def frenzy_word(game) -> str:
    mult = frenzy(game)
    if mult >= 2.2:
        return "כל אירופה מדברת עליך. המספרים שהם מוכנים לשלם לא הגיוניים."
    if mult >= 1.6:
        return "אתה בשוק של העילויים. מי שרוצה אותך יודע שיש תור."
    if mult >= 1.15:
        return "מתחילים להתייחס אליך כאל השקעה, לא כאל חתימה."
    return ""


# ---------------------------------------------------------------------------
# כמה אתה שווה, וכמה כוח יש לך
# ---------------------------------------------------------------------------

def market_value(player: Player) -> int:
    """שווי העברה משוער בשקלים. הבסיס לכל מספר אחר כאן."""
    base = wage_for_overall(player.overall) * 46.0
    # גיל הוא המכפיל הגדול: בן 22 עם אותו דירוג שווה כפליים מבן 31
    if player.age <= 20:
        base *= 1.95
    elif player.age <= 23:
        base *= 1.70
    elif player.age <= 26:
        base *= 1.35
    elif player.age <= 29:
        base *= 1.0
    elif player.age <= 32:
        base *= 0.55
    else:
        base *= 0.25
    base *= 0.72 + player.reputation / 145.0
    # פוטנציאל שעוד לא מומש הוא חלק מהמחיר
    base *= 1.0 + max(0, player.potential - player.overall) * 0.020
    if player.contract.years_left <= 1:
        base *= 0.45          # שנה לסיום — כמעט חינם
    elif player.contract.years_left == 2:
        base *= 0.80
    return int(round(base / 1000.0) * 1000)


def leverage(game) -> float:
    """0-1: כמה כוח יש לך סביב השולחן.

    מינוף הוא לא "כמה אתה טוב" אלא "כמה אפשרויות יש לך". שחקן מצוין
    עם הצעה אחת וחוזה לארבע שנים חלש מול שחקן טוב עם שלוש הצעות
    וחוזה שנגמר.
    """
    me = game.me
    offers = [o for o in open_offers(game) if o["state"] != "withdrawn"]
    score = 0.20
    score += min(0.34, max(0, len(offers) - 1) * 0.17)   # מתחרים
    score += min(0.20, me.reputation / 500.0)
    if me.contract.years_left <= 1:
        score += 0.18
    elif me.contract.years_left >= 4:
        score -= 0.08
    if me.season.apps >= 6:
        score += clamp((me.season.avg_rating - 6.7) * 0.16, -0.10, 0.16)
    if me.age <= 23:
        score += 0.06
    elif me.age >= 33:
        score -= 0.14
    return clamp(score, 0.03, 0.95)


# ---------------------------------------------------------------------------
# בניית הצעה
# ---------------------------------------------------------------------------

def build_offer(game, club: Club, rng: random.Random,
                eagerness: Optional[float] = None) -> Dict[str, Any]:
    """חבילה שלמה ממועדון אחד, לא רק מספר."""
    me = game.me
    boom = frenzy(game)
    if eagerness is None:
        eagerness = rng.uniform(0.35, 0.95)
    # מועדון שרודף אחרי עילוי לא "בודק אפשרות"
    eagerness = clamp(eagerness * (0.75 + boom * 0.35), 0.05, 0.99)

    # מה הם מוכנים לשלם: מה שהשוק אומר, מוטה לפי כמה הם רוצים אותך
    par = wage_for_overall(me.overall) * (0.88 + me.reputation / 200.0)
    ceiling = max(par * 1.05, club.wage_budget * 0.34) * boom
    wage = int(min(ceiling, par * (0.80 + eagerness * 0.55) * boom))
    wage = max(wage, int(me.contract.wage * 1.08))

    value = int(market_value(me) * boom)
    role = _role_for(club, me, eagerness)
    years = 3 if me.age >= 31 else (5 if eagerness > 0.7 and me.age <= 24 else 4)

    offer = {
        "cid": club.cid,
        "wage": wage,
        "years": years,
        "bonus": int(value * rng.uniform(0.03, 0.09) * (0.5 + eagerness)),
        "clause": 0,
        "role": role,
        "image": 0,
        "minutes": 0,
        "loyalty": 0,
        "family": 0,
        "promises": [],
        "fee": value,
        "eagerness": round(eagerness, 3),
        "ceiling": int(ceiling),
        "patience": 2 + int(eagerness * 3),
        "asks": 0,
        "state": "open",
        "weeks": WINDOW_WEEKS,
        "log": [],
        "frenzy": round(boom, 2),
    }
    # בטירוף אמיתי הם לא מחכים שתבקש — הם שמים את הכול על השולחן מראש
    if boom >= 1.9:
        offer["bonus"] = int(offer["bonus"] * 2.2)
        offer["image"] = 15
        offer["minutes"] = 55
        offer["promises"] = ["מספר החולצה שתבחר",
                             "פרויקט שנבנה סביבך",
                             "לא נמכור אותך בשנתיים הראשונות"]
    elif boom >= 1.35:
        offer["bonus"] = int(offer["bonus"] * 1.5)
        offer["promises"] = ["פרויקט שנבנה סביבך"]
    return offer


def _role_for(club: Club, me: Player, eagerness: float) -> str:
    """איזה תפקיד מועדון מוכן להבטיח — לפי הפער בינך לבין הסגל שלו."""
    gap = me.overall - club.reputation
    if gap >= 10 and eagerness > 0.55:
        return "star"
    if gap >= 0:
        return "starter"
    if gap >= -9:
        return "rotation"
    return "prospect"


def offer_worth(offer: Dict[str, Any]) -> int:
    """ערך שנתי מקורב של חבילה — כדי שאפשר יהיה להשוות הצעות."""
    annual = offer["wage"] * 52
    annual += offer["bonus"] // max(1, offer["years"])
    annual = int(annual * ROLE_VALUE.get(offer["role"], 1.0))
    annual += annual * offer.get("image", 0) // 100
    annual += int(offer.get("loyalty", 0))
    annual += int(offer.get("family", 0))
    # התחייבות לדקות היא לא כסף, אבל היא שווה — קריירה נבנית מדקות
    annual = int(annual * (1.0 + offer.get("minutes", 0) / 420.0))
    return annual


# ---------------------------------------------------------------------------
# ניהול השוק
# ---------------------------------------------------------------------------

def open_offers(game) -> List[Dict[str, Any]]:
    data = game.flags.get("offers")
    return data if isinstance(data, list) else []


def set_offers(game, offers: List[Dict[str, Any]]) -> None:
    game.flags["offers"] = offers


def live_offers(game) -> List[Dict[str, Any]]:
    """מה שעדיין על השולחן, מהשווה ביותר לפחות."""
    rows = [o for o in open_offers(game) if o["state"] in ("open", "improved", "final")]
    rows.sort(key=lambda o: -offer_worth(o))
    return rows


def offer_for(game, cid: str) -> Optional[Dict[str, Any]]:
    for offer in open_offers(game):
        if offer["cid"] == cid:
            return offer
    return None


def tick_offers(game) -> List[str]:
    """שבוע עובר: הצעות מתקרבות לפקיעה, ומתחרים מגיבים זה לזה."""
    lines: List[str] = []
    offers = open_offers(game)
    if not offers:
        return lines
    live = [o for o in offers if o["state"] in ("open", "improved", "final")]
    for offer in live:
        offer["weeks"] -= 1
        club = game.clubs.get(offer["cid"])
        name = club.name if club else "מועדון"
        if offer["weeks"] <= 0:
            offer["state"] = "withdrawn"
            lines.append(f"⌛ {name} משכו את ההצעה — הדדליין עבר.")
        elif offer["weeks"] == 1:
            lines.append(f"⏳ {name} רוצים תשובה עד סוף השבוע.")

    # מרוץ: כשיש כמה מתעניינים, מישהו מרים את הרף מעצמו
    still = [o for o in offers if o["state"] in ("open", "improved", "final")]
    if len(still) >= 2 and game.rng.random() < 0.42:
        best = max(still, key=offer_worth)
        rival = game.rng.choice([o for o in still if o is not best])
        if rival["wage"] < rival["ceiling"] * 0.97:
            bump = max(1, int((best["wage"] - rival["wage"]) * 0.6))
            rival["wage"] = int(min(rival["ceiling"], rival["wage"] + max(bump, rival["wage"] // 20)))
            rival["state"] = "improved"
            club = game.clubs.get(rival["cid"])
            lines.append(f"📈 {club.name if club else 'מועדון'} שמעו על ההצעה השנייה "
                         f"והעלו ל-₪{rival['wage']:,} לשבוע.")
    set_offers(game, offers)
    return lines


def clear_offers(game) -> None:
    game.flags.pop("offers", None)


# ---------------------------------------------------------------------------
# משא ומתן
# ---------------------------------------------------------------------------

def ask_options(offer: Dict[str, Any]) -> List[Dict[str, Any]]:
    """מה אפשר לבקש מההצעה הזאת עכשיו, ומה זה יעלה."""
    out = []
    for key, name in TERMS:
        if key == "role" and offer["role"] == "star":
            continue
        if key == "years" and offer["years"] >= 6:
            continue
        if key == "image" and offer["image"] >= 25:
            continue
        if key == "clause" and offer["clause"] and offer["clause"] <= offer["fee"]:
            continue
        if key == "minutes" and offer.get("minutes", 0) >= 75:
            continue
        if key == "loyalty" and offer.get("loyalty", 0) >= offer["wage"] * 30:
            continue
        if key == "family" and offer.get("family", 0):
            continue
        out.append({"term": key, "name": name, "ask": _ask_text(offer, key)})
    return out


def _ask_text(offer: Dict[str, Any], term: str) -> str:
    if term == "wage":
        return f"₪{int(offer['wage'] * 1.22):,} במקום ₪{offer['wage']:,}"
    if term == "years":
        return f"{offer['years'] + 1} שנים במקום {offer['years']}"
    if term == "bonus":
        return f"מענק ₪{int(max(offer['bonus'] * 1.6, 120000)):,}"
    if term == "clause":
        return f"סעיף שחרור ₪{int(offer['fee'] * 1.6):,}"
    if term == "role":
        nxt = _better_role(offer["role"])
        return f"התחייבות ל{ROLE_NAMES[nxt]}"
    if term == "image":
        return f"{min(25, offer['image'] + 10)}% מזכויות הדימוי"
    if term == "minutes":
        return f"התחייבות ל-{min(75, offer.get('minutes', 0) + 25)}% מהדקות"
    if term == "loyalty":
        return f"מענק נאמנות ₪{int(max(offer['wage'] * 14, 200000)):,} לשנה"
    if term == "family":
        return "דירה, בית ספר ורילוקיישן למשפחה"
    return ""


def _better_role(role: str) -> str:
    order = [key for key, _, _ in SQUAD_ROLES]
    return order[max(0, order.index(role) - 1)]


def negotiate(game, cid: str, term: str, rng: random.Random) -> Dict[str, Any]:
    """מבקש שיפור בסעיף אחד. מחזיר מה קרה.

    זו ההחלטה האמיתית של השוק: כל בקשה שורפת סבלנות, ומועדון שנגמרה
    לו הסבלנות קם מהשולחן. מינוף הוא מה שקובע אם זה משתלם.
    """
    offer = offer_for(game, cid)
    if not offer or offer["state"] not in ("open", "improved", "final"):
        return {"ok": False, "text": "ההצעה כבר לא על השולחן.", "gone": True}

    club = game.clubs.get(cid)
    name = club.name if club else "המועדון"
    offer["asks"] += 1
    lev = leverage(game)

    # כמה סיכוי שיסכימו: רצון + מינוף, פחות מה שכבר ביקשת
    chance = 0.24 + offer["eagerness"] * 0.42 + lev * 0.38
    chance -= (offer["asks"] - 1) * 0.19
    if term == "wage" and offer["wage"] >= offer["ceiling"] * 0.95:
        chance -= 0.42                    # כבר בתקרת התקציב שלהם
    if term in ("clause", "image"):
        chance -= 0.10                    # סעיפים שמועדונים לא אוהבים
    chance = clamp(chance, 0.04, 0.93)

    roll = rng.random()
    if roll < chance:
        text = _apply_ask(offer, term, full=True)
        offer["state"] = "improved"
        offer["log"].append(f"✅ {text}")
        return {"ok": True, "text": f"{name} הסכימו: {text}", "gone": False}

    # סירוב מלא, פשרה, או קימה מהשולחן
    if offer["asks"] > offer["patience"] and rng.random() < 0.55:
        offer["state"] = "withdrawn"
        offer["log"].append("❌ ירדו מהעסקה")
        return {"ok": False, "gone": True,
                "text": f"{name} סגרו את התיק. \"ניסינו, נתראה בקיץ הבא.\""}

    if roll < chance + 0.28:
        text = _apply_ask(offer, term, full=False)
        offer["state"] = "final"
        offer["log"].append(f"🤝 {text}")
        return {"ok": True, "gone": False,
                "text": f"{name} לא הלכו על כל הדרך, אבל: {text}"}

    offer["log"].append(f"🚫 סירבו על {TERM_NAMES.get(term, term)}")
    return {"ok": False, "gone": False,
            "text": f"{name} סירבו. \"זה מה שיש, וזה לא ייפתח שוב.\""}


def _apply_ask(offer: Dict[str, Any], term: str, full: bool) -> str:
    """מזיז את הסעיף בפועל. full=False היא פשרה — כחצי ממה שביקשת."""
    share = 1.0 if full else 0.5
    if term == "wage":
        target = offer["wage"] * (1 + 0.22 * share)
        offer["wage"] = int(min(offer["ceiling"], target))
        return f"₪{offer['wage']:,} לשבוע"
    if term == "years":
        offer["years"] += 1 if full else 0
        if not full:
            offer["bonus"] = int(offer["bonus"] * 1.15)
            return f"אותן {offer['years']} שנים, אבל מענק ₪{offer['bonus']:,}"
        return f"{offer['years']} שנים"
    if term == "bonus":
        offer["bonus"] = int(max(offer["bonus"] * (1 + 0.6 * share), 120000 * share))
        return f"מענק חתימה ₪{offer['bonus']:,}"
    if term == "clause":
        offer["clause"] = int(offer["fee"] * (1.6 if full else 2.4))
        return f"סעיף שחרור ₪{offer['clause']:,}"
    if term == "role":
        if full:
            offer["role"] = _better_role(offer["role"])
            return f"התחייבות ל{ROLE_NAMES[offer['role']]}"
        offer["wage"] = int(min(offer["ceiling"], offer["wage"] * 1.08))
        return f"בלי התחייבות בכתב, אבל ₪{offer['wage']:,} לשבוע"
    if term == "image":
        offer["image"] = min(25, offer["image"] + (10 if full else 5))
        return f"{offer['image']}% מזכויות הדימוי"
    if term == "minutes":
        step = 25 if full else 12
        offer["minutes"] = min(75, offer.get("minutes", 0) + step)
        return f"התחייבות ל-{offer['minutes']}% מהדקות"
    if term == "loyalty":
        base = max(offer["wage"] * 14, 200000)
        offer["loyalty"] = int(base * (1.0 if full else 0.5))
        return f"מענק נאמנות ₪{offer['loyalty']:,} לשנה"
    if term == "family":
        offer["family"] = int(max(offer["wage"] * 8, 120000) * (1.0 if full else 0.5))
        return ("דירה, בית ספר ורילוקיישן למשפחה"
                if full else "השתתפות בדיור למשפחה")
    return ""


# ---------------------------------------------------------------------------
# תצוגה
# ---------------------------------------------------------------------------

def club_tag(game, cid: str) -> str:
    """דגל, מדינה וליגה — הזהות של המועדון במבט אחד."""
    club = game.clubs.get(cid)
    return D.club_tag(cid, club.league_id if club else "")


def is_foreign(cid: str) -> bool:
    return D.is_foreign(cid)


def offer_lines(game, offer: Dict[str, Any]) -> List[str]:
    """החבילה בשורות, כדי שאפשר יהיה להשוות בעין."""
    club = game.clubs.get(offer["cid"])
    out = [club_tag(game, offer["cid"]),
           f"₪{offer['wage']:,} לשבוע · {offer['years']} שנים"]
    if offer["bonus"]:
        out.append(f"מענק חתימה ₪{offer['bonus']:,}")
    out.append(f"תפקיד מובטח: {ROLE_NAMES.get(offer['role'], offer['role'])}")
    if offer["clause"]:
        out.append(f"סעיף שחרור ₪{offer['clause']:,}")
    if offer["image"]:
        out.append(f"{offer['image']}% זכויות דימוי")
    if offer.get("minutes"):
        out.append(f"התחייבות ל-{offer['minutes']}% מהדקות")
    if offer.get("loyalty"):
        out.append(f"מענק נאמנות ₪{offer['loyalty']:,} לשנה")
    if offer.get("family"):
        out.append(f"חבילה למשפחה ₪{offer['family']:,}")
    for promise in offer.get("promises", []):
        out.append(f"הבטחה: {promise}")
    if club:
        out.append(f"דמי העברה ₪{offer['fee']:,} ל{game.my_club.name}"
                   if game.my_club else f"דמי העברה ₪{offer['fee']:,}")
    return out


def interest_word(offer: Dict[str, Any]) -> str:
    """כמה הם רוצים אותך, בלי לחשוף את המספר."""
    eager = offer["eagerness"]
    if eager > 0.82:
        return "רוצים אותך מאוד"
    if eager > 0.62:
        return "מעוניינים ברצינות"
    if eager > 0.42:
        return "בודקים אפשרות"
    return "שומרים אופציה"
