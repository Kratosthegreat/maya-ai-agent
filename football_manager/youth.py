# -*- coding: utf-8 -*-
"""
football_manager.youth
======================
איך צדים ילד בן שלוש־עשרה.

מועדונים גדולים לא מחכים שתגיע לבוגרים. יש להם מערך צופים שמסתובב
בטורנירי נוער בכל העולם ומחפש את מי שיהיה שווה משהו בעוד עשר שנים —
וברגע שמישהו מצא אותך, השאר שומעים ובאים לראות בעצמם.

שני דברים מבדילים את השוק הזה מזה של הבוגרים:

**זו לא עסקה של כסף.** אף אחד לא מציע לילד שכר. מציעים לו מעונות,
בית ספר, נסיעות, מאמן אישי, הבטחת דקות בקבוצת הנוער, ומסלול מוגדר
לסגל הבוגרים. ולמשפחה — סיוע במעבר.

**ההחלטה היא לא רק שלך.** יש הורים, ולהורים יש דעה משלהם: הם רוצים
שתסיים בית ספר, שתהיה קרוב לבית, ושלא תיסע לחו"ל בגיל שלוש־עשרה.
כשהם לא מסכימים איתך אפשר לנסות לשכנע — וזה לא תמיד עובד.

והדבר החשוב באמת: **מרוץ מעלה את הערך שלך.** ילד ששלוש קבוצות רבות
עליו נהיה שווה יותר מילד שאחת בדקה אותו, עוד לפני שהוכיח משהו.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from . import data as D
from .models import Club, Player, clamp, gain_reputation

# מה חשוב להורים שלך. נקבע פעם אחת בתחילת הקריירה.
FAMILY_VALUES = [
    ("schooling", "לימודים", "רוצים שתסיים בית ספר כמו כל ילד"),
    ("home", "קרבה לבית", "לא מוכנים שתגור רחוק בגיל הזה"),
    ("money", "ביטחון כלכלי", "המשפחה צריכה את זה, ואין טעם להתבייש"),
    ("football", "כדורגל קודם", "מאמינים בך, ומוכנים לשלם את המחיר"),
]
FAMILY_NAMES = {key: name for key, name, _ in FAMILY_VALUES}
FAMILY_WHY = {key: why for key, _, why in FAMILY_VALUES}

# כמה רחוק זה, ומה זה עושה למשפחה
DISTANCES = [
    ("local", "בעיר שלך", 0),
    ("national", "בארץ, נסיעה ארוכה", 1),
    ("abroad", "בחו\"ל", 2),
]
DISTANCE_NAMES = {key: name for key, name, _ in DISTANCES}

SCOUT_POOL_LIMIT = 12    # כמה אקדמיות בכלל מסתובבות בטורנירי הנוער
YOUTH_NOTICED = 20.0     # מופיע ברשימת "מי מסתכל עליי"
YOUTH_CHASED = 50.0      # מוכן להניח הצעה על השולחן
YOUTH_JOINS = 30.0       # מצטרף למרוץ ברגע שמישהו אחר פנה
WINDOW_WEEKS = 6         # לילד נותנים יותר זמן להחליט


# ---------------------------------------------------------------------------
# המשפחה
# ---------------------------------------------------------------------------

def make_family(rng: random.Random) -> Dict[str, Any]:
    """פרופיל ההורים. נקבע בלידת הקריירה ולא משתנה."""
    values = [key for key, _, _ in FAMILY_VALUES]
    first = rng.choice(values)
    second = rng.choice([v for v in values if v != first])
    return {
        "first": first,
        "second": second,
        "trust": rng.randint(45, 75),     # כמה הם סומכים על השיפוט שלך
    }


def family(game) -> Dict[str, Any]:
    data = game.flags.get("family")
    if not isinstance(data, dict):
        data = make_family(game.rng)
        game.flags["family"] = data
    return data


def family_line(game) -> str:
    fam = family(game)
    return (f"ההורים שלך: {FAMILY_NAMES[fam['first']]} לפני הכול, "
            f"ואחר כך {FAMILY_NAMES[fam['second']]}. "
            f"{FAMILY_WHY[fam['first']]}.")


# ---------------------------------------------------------------------------
# מי מסתכל עליך
# ---------------------------------------------------------------------------

def interest(game) -> Dict[str, float]:
    data = game.flags.get("youth_interest")
    if not isinstance(data, dict):
        data = {}
        game.flags["youth_interest"] = data
    return data


def watchers(game, minimum: float = YOUTH_NOTICED) -> List[tuple]:
    """מי עוקב אחריך עכשיו, מהחזק לחלש."""
    table = interest(game)
    rows = [(game.clubs[cid], float(score)) for cid, score in table.items()
            if cid in game.clubs and float(score) >= minimum]
    rows.sort(key=lambda row: -row[1])
    return rows


def scout_pool(game) -> List[Club]:
    """אילו אקדמיות בכלל מחפשות ילדים כמוך.

    אקדמיה גדולה מסתכלת רחוק יותר: היא מוכנה להמר על ילד שעוד לא
    בולט, כי היא מגדלת אותו שש שנים. אקדמיה קטנה צריכה מישהו שיעזור
    כבר עכשיו.
    """
    me = game.me
    out = []
    for club in game.clubs.values():
        if club.cid == me.club_id:
            continue
        reach = club.reputation * 0.55 + club.training_facilities * 0.30
        if me.potential + 6 >= reach:
            out.append(club)
    # ילד אחד לא נמצא על הרדאר של ארבעים מועדונים. מי שבאמת שולח
    # צופה לטורניר נוער הוא מי שיש לו מחלקת נוער רצינית — ואם כל
    # הביקורים מתפזרים על כולם, אף אחד לא בונה תיק ואף אחד לא פונה.
    out.sort(key=lambda c: -(c.reputation * 0.6 + c.training_facilities * 0.4))
    return out[:SCOUT_POOL_LIMIT]


def scouts_this_week(game, rng: random.Random) -> List[str]:
    """שבוע של צופי נוער. אין ציוני משחק בגיל הזה — יש עין.

    מה שצופה נוער רואה זה לא תוצאה אלא כיוון: כמה הילד גדל מאז הפעם
    שעברה, כמה הוא רוצה, ומה הגוף שלו יעשה עוד שלוש שנים.
    """
    me = game.me
    lines: List[str] = []
    table = interest(game)

    # דעיכה — צופה שלא חזר לראות אותך מתחיל לשכוח
    for cid in list(table):
        table[cid] = round(float(table[cid]) * 0.985 - 0.15, 2)
        if table[cid] <= 1.0:
            del table[cid]

    if me.age < 12:
        return lines
    pool = scout_pool(game)
    if not pool:
        return lines

    visits = 1 if rng.random() < 0.42 + me.potential / 220.0 else 0
    if me.potential >= 70 and rng.random() < 0.24:
        visits += 1
    for _ in range(visits):
        weights = []
        for club in pool:
            weight = (club.reputation / 30.0) ** 1.25
            weight *= 1.0 + club.training_facilities / 90.0
            # מי שכבר פתח עליך תיק חוזר לראות אותך שוב — וזה מה
            # שבונה עניין אמיתי במקום ביקור חד־פעמי שנשכח
            weight *= 1.0 + float(table.get(club.cid, 0.0)) / 9.0
            weights.append((club, weight))
        total = sum(w for _, w in weights) or 1.0
        roll = rng.random() * total
        club = weights[-1][0]
        for candidate, weight in weights:
            roll -= weight
            if roll <= 0:
                club = candidate
                break

        # מה שהוא רואה: פוטנציאל מול מה שהאקדמיה שלו רגילה אליו
        move = (me.potential - club.reputation * 0.78) * 0.42
        move += (me.detail.get("determination", 10) - 10) * 0.55
        move += (me.detail.get("natural_fitness", 10) - 10) * 0.25
        move += rng.uniform(-2.0, 2.0)
        if me.age <= 14:
            move = move * 1.2 + 1.0        # על ילד קטן מהמרים בקלות
        before = float(table.get(club.cid, 0.0))
        after = round(clamp(before + move, 0, 100), 2)
        table[club.cid] = after

        if before < YOUTH_NOTICED <= after:
            lines.append(f"👀 צופה של {club.name} עמד בצד המגרש כל האימון.")
        elif before < YOUTH_CHASED <= after:
            lines.append(f"🔥 {club.name} שלחו את ראש מחלקת הנוער. "
                         f"זה כבר לא סתם מבט.")
            # וזה בדיוק הרגע שבו כל השאר שומעים. עולם הצופים קטן,
            # ואקדמיה שמגלה שמתחרה שלה פתחה תיק על ילד לא ממתינה
            # לטורניר הבא — היא שולחת מישהו בשבוע שאחרי.
            lines.extend(_rivals_hear(game, club, table, rng))
    game.flags["youth_interest"] = table
    return lines


def _rivals_hear(game, club: Club, table: Dict[str, float],
                 rng: random.Random) -> List[str]:
    """כשאקדמיה אחת נכנסת ברצינות, המתחרות מתעוררות.

    בלי זה כל ילד נחטף על ידי המועדון הראשון שראה אותו, ואין מרוץ —
    וזה בדיוק מה שמעלה את הערך של נער בן שלוש־עשרה.
    """
    out: List[str] = []
    rivals = [c for c in scout_pool(game)
              if c.cid != club.cid and float(table.get(c.cid, 0.0)) < YOUTH_CHASED]
    rng.shuffle(rivals)
    for rival in rivals[:2]:
        if rng.random() > 0.55:
            continue
        before = float(table.get(rival.cid, 0.0))
        table[rival.cid] = round(clamp(before + rng.uniform(14, 26), 0, 100), 2)
        if before < YOUTH_NOTICED <= table[rival.cid]:
            out.append(f"👀 גם {rival.name} שלחו מישהו. השמועה עברה.")
    return out


# ---------------------------------------------------------------------------
# הצעת אקדמיה
# ---------------------------------------------------------------------------

def build_offer(game, club: Club, rng: random.Random,
                eagerness: Optional[float] = None) -> Dict[str, Any]:
    """חבילה לילד ולמשפחה שלו. אין כאן שכר — יש כאן חיים."""
    me = game.me
    my_club = game.my_club
    if eagerness is None:
        eagerness = rng.uniform(0.4, 1.0)

    country = D.CLUB_COUNTRY.get(club.cid, "ישראל")
    home = D.CLUB_COUNTRY.get(my_club.cid, "ישראל") if my_club else "ישראל"
    if country != home:
        distance = "abroad"
    elif club.reputation > 55:
        distance = "national"
    else:
        distance = rng.choice(["local", "national"])

    # ההשקעה עולה עם כמה שהם רוצים אותך ועם גודל האקדמיה
    grade = club.training_facilities / 100.0
    return {
        "cid": club.cid,
        "distance": distance,
        "boarding": distance != "local" and rng.random() < 0.55 + eagerness * 0.4,
        "schooling": int(clamp(35 + grade * 55 + eagerness * 18, 20, 99)),
        "family_help": int(club.reputation * 900 * (0.5 + eagerness) * grade),
        "minutes": eagerness > 0.55,
        "pathway": eagerness > 0.72 and club.reputation > 45,
        "coach": eagerness > 0.62,
        "fee": int(club.reputation * 1400 * (0.4 + eagerness)),
        "eagerness": round(eagerness, 3),
        "weeks": WINDOW_WEEKS,
        "state": "open",
    }


def offer_lines(game, offer: Dict[str, Any]) -> List[str]:
    out = [f"מיקום: {DISTANCE_NAMES[offer['distance']]}"]
    out.append("מעונות ופנימייה" if offer["boarding"] else "גר בבית, נוסע לאימונים")
    out.append(f"בית ספר במסגרת האקדמיה: {offer['schooling']}/100")
    if offer["family_help"]:
        out.append(f"סיוע למשפחה: ₪{offer['family_help']:,} לשנה")
    if offer["minutes"]:
        out.append("הבטחת דקות בקבוצת הנוער")
    if offer["pathway"]:
        out.append("מסלול מוגדר לסגל הבוגרים")
    if offer["coach"]:
        out.append("מאמן אישי צמוד")
    return out


def football_score(game, offer: Dict[str, Any]) -> float:
    """כמה זה טוב לכדורגל שלך. 0-100."""
    club = game.clubs.get(offer["cid"])
    if not club:
        return 0.0
    score = club.reputation * 0.55 + club.training_facilities * 0.30
    if offer["minutes"]:
        score += 8
    if offer["pathway"]:
        score += 10
    if offer["coach"]:
        score += 6
    return clamp(score, 0, 100)


def family_score(game, offer: Dict[str, Any]) -> float:
    """כמה זה טוב בעיני ההורים. 0-100. לא אותו דבר בכלל."""
    fam = family(game)
    club = game.clubs.get(offer["cid"])
    if not club:
        return 0.0
    parts = {
        "schooling": offer["schooling"],
        "home": {"local": 92.0, "national": 55.0, "abroad": 18.0}[offer["distance"]],
        "money": clamp(offer["family_help"] / 900.0, 0, 100),
        "football": football_score(game, offer),
    }
    # הערך הראשון חייב באמת להכריע. אחרת בית ספר טוב וכסף גדול
    # מצליחים "לפצות" על ילד בן שלוש־עשרה שעובר לגור בחו"ל, וזה בדיוק
    # מה שההורים האלה לא מוכנים לשמוע.
    score = 0.0
    for key, value in parts.items():
        weight = 4.5 if key == fam["first"] else 1.8 if key == fam["second"] else 0.8
        score += value * weight
    score /= (4.5 + 1.8 + 0.8 + 0.8)
    if offer["boarding"] and fam["first"] == "home":
        score -= 18
    return clamp(score, 0, 100)


def family_verdict(game, offer: Dict[str, Any]) -> Dict[str, Any]:
    """מה ההורים אומרים, ולמה. זה החלק שהופך את זה להחלטה משפחתית."""
    fam = family(game)
    mine = football_score(game, offer)
    theirs = family_score(game, offer)
    club = game.clubs.get(offer["cid"])
    name = club.name if club else "המועדון"

    if theirs >= 68:
        mood, text = "happy", f"\"{name} זה מקום טוב. אנחנו איתך.\""
    elif theirs >= 48:
        mood, text = "unsure", f"\"אנחנו לא בטוחים לגבי {name}, אבל נקשיב לך.\""
    else:
        why = {
            "schooling": "\"ומה עם בית הספר? זה לא נגמר בכדורגל.\"",
            "home": "\"אתה בן {age}. לא נותנים לך לגור לבד.\"",
            "money": "\"אנחנו לא יכולים לממן את זה. פשוט לא.\"",
            "football": "\"זה לא המקום שיוציא ממך את המקסימום.\"",
        }[fam["first"]].format(age=game.me.age)
        mood, text = "against", why

    return {
        "mood": mood, "text": text,
        "family": round(theirs, 1), "football": round(mine, 1),
        "conflict": mood == "against" and mine >= theirs + 12,
    }


# ---------------------------------------------------------------------------
# השוק
# ---------------------------------------------------------------------------

def open_offers(game) -> List[Dict[str, Any]]:
    data = game.flags.get("youth_offers")
    return data if isinstance(data, list) else []


def set_offers(game, offers: List[Dict[str, Any]]) -> None:
    game.flags["youth_offers"] = offers


def live_offers(game) -> List[Dict[str, Any]]:
    rows = [o for o in open_offers(game) if o["state"] == "open"]
    rows.sort(key=lambda o: -football_score(game, o))
    return rows


def offer_for(game, cid: str) -> Optional[Dict[str, Any]]:
    for offer in open_offers(game):
        if offer["cid"] == cid:
            return offer
    return None


def clear_offers(game) -> None:
    game.flags.pop("youth_offers", None)


def maybe_open_market(game, rng: random.Random) -> List[str]:
    """אם מספיק אקדמיות רוצות אותך — הן מניחות הצעות.

    זה קורה באמצע העונה ולא רק בסופה: אקדמיה שמצאה ילד לא מחכה
    לקיץ, היא מתקשרת להורים בשבוע שאחרי הטורניר.
    """
    me = game.me
    if game.stage != "youth" or open_offers(game):
        return []
    chasing = watchers(game, YOUTH_CHASED)
    if not chasing:
        return []
    if rng.random() > 0.30:
        return []

    # ברגע שאחת פונה רשמית, כל מי שיש לו תיק פתוח מניח משהו על השולחן
    # גם הוא — אף אקדמיה לא רוצה לגלות בעיתון שהילד שהיא עקבה אחריו
    # שנתיים חתם אצל השכנה. זה מה שיוצר מרוץ ולא פנייה בודדת.
    joining = watchers(game, YOUTH_JOINS)
    offers = []
    for club, score in joining[:4]:
        eagerness = clamp(0.35 + (score - YOUTH_JOINS) / 48.0, 0.35, 1.0)
        offers.append(build_offer(game, club, rng, eagerness))
    set_offers(game, offers)

    lines = ["", f"📞 טלפון הביתה. {len(offers)} "
                 f"{'אקדמיות' if len(offers) > 1 else 'אקדמיה'} רוצות אותך:"]
    for offer in live_offers(game):
        club = game.clubs[offer["cid"]]
        lines.append(f"   • {club.name} — {DISTANCE_NAMES[offer['distance']]}")
    lines.append("   ההחלטה היא שלך ושל ההורים. (בתפריט: 'אקדמיות')")
    lines.extend(chase_bonus(game))
    return lines


def tick_offers(game) -> List[str]:
    lines: List[str] = []
    offers = open_offers(game)
    if not offers:
        return lines
    for offer in [o for o in offers if o["state"] == "open"]:
        offer["weeks"] -= 1
        club = game.clubs.get(offer["cid"])
        name = club.name if club else "אקדמיה"
        if offer["weeks"] <= 0:
            offer["state"] = "gone"
            lines.append(f"⌛ {name} סגרו את הרשימה שלהם לעונה הזאת.")
        elif offer["weeks"] == 1:
            lines.append(f"⏳ {name} מבקשים תשובה השבוע.")
    set_offers(game, offers)
    return lines


def chase_bonus(game) -> List[str]:
    """מרוץ על ילד מעלה את הערך שלו — עוד לפני שהוכיח משהו.

    ככה זה עובד באמת: ברגע שנודע ששלוש אקדמיות רוצות את אותו נער,
    הוא מפסיק להיות "עוד ילד מהשכונה" ומתחיל להיות נכס. הציפייה
    עצמה מייצרת שווי, וגם לחץ.
    """
    me = game.me
    count = len(live_offers(game))
    if count < 2:
        return []
    gain_reputation(me, 1.6 * count)
    before = me.potential
    me.potential = int(clamp(me.potential + count, 0, me.ceiling))
    if count >= 3 and me.ceiling < 95:
        me.ceiling = int(min(95, me.ceiling + 1))
    me.morale = clamp(me.morale + 4, 5, 99)
    out = [f"💎 {count} אקדמיות רבות עליך. בגיל {me.age} זה כבר סיפור."]
    if me.potential > before:
        out.append(f"   ההערכה עליך עלתה ל-{me.potential}.")
    return out


# ---------------------------------------------------------------------------
# ההחלטה
# ---------------------------------------------------------------------------

def persuade(game, cid: str, rng: random.Random) -> str:
    """מנסה לשכנע את ההורים. פעם אחת לכל הצעה."""
    offer = offer_for(game, cid)
    if not offer or offer["state"] != "open":
        return "ההצעה כבר לא על השולחן."
    if offer.get("persuaded"):
        return "כבר דיברת איתם על זה. יותר מזה רק יזיק."
    me = game.me
    fam = family(game)
    offer["persuaded"] = True

    chance = 0.20 + fam["trust"] / 260.0
    chance += (me.detail.get("determination", 10) - 10) * 0.030
    chance += (game.flag("school", 0) >= 6) * 0.12      # למדת — יש לך קרדיט
    chance -= (family_score(game, offer) < 35) * 0.18
    chance = clamp(chance, 0.05, 0.88)

    if rng.random() < chance:
        offer["blessing"] = True
        fam["trust"] = int(clamp(fam["trust"] + 6, 0, 100))
        game.flags["family"] = fam
        return ("ישבתם במטבח שעתיים. בסוף אבא אמר \"אם אתה בטוח — "
                "אנחנו מאחוריך.\"")
    fam["trust"] = int(clamp(fam["trust"] - 4, 0, 100))
    game.flags["family"] = fam
    me.morale = clamp(me.morale - 5, 5, 99)
    return ("הם לא השתכנעו. \"אנחנו לא אומרים לא לכדורגל, "
            "אנחנו אומרים לא עכשיו.\"")


def accept(game, cid: str) -> List[str]:
    """חותם באקדמיה. אם ההורים נגד — זה עולה במשהו."""
    offer = offer_for(game, cid)
    if not offer or offer["state"] != "open":
        return ["ההצעה כבר לא על השולחן."]
    club = game.clubs[offer["cid"]]
    me = game.me
    verdict = family_verdict(game, offer)
    against = verdict["mood"] == "against" and not offer.get("blessing")

    out = [f"✍️ עברת לאקדמיה של {club.name}."]
    game.transfer_me(club.cid, 0, 3)
    if offer["family_help"]:
        game.money += offer["family_help"]
        out.append(f"   המשפחה קיבלה ₪{offer['family_help']:,} סיוע.")
    game.flags["academy_deal"] = {
        "cid": club.cid, "minutes": offer["minutes"],
        "pathway": offer["pathway"], "coach": offer["coach"],
        "schooling": offer["schooling"], "boarding": offer["boarding"],
    }
    if offer["pathway"]:
        out.append("   יש לך מסלול כתוב לסגל הבוגרים.")
    if offer["coach"]:
        out.append("   הצמידו לך מאמן אישי.")
    if offer["boarding"]:
        out.append("   ארזת תיק. בן כמה היית כשעזבת את הבית?")

    if against:
        me.morale = clamp(me.morale - 12, 5, 99)
        fam = family(game)
        fam["trust"] = int(clamp(fam["trust"] - 14, 0, 100))
        game.flags["family"] = fam
        out.append("   ההורים לא הסכימו, והלכת בכל זאת. "
                   "בבית לא מדברים על זה.")
    else:
        me.morale = clamp(me.morale + 9, 5, 99)

    clear_offers(game)
    game.flags["youth_interest"] = {}
    return out


def decline(game, cid: str) -> str:
    offer = offer_for(game, cid)
    if not offer:
        return "אין הצעה כזאת."
    offer["state"] = "gone"
    set_offers(game, open_offers(game))
    club = game.clubs.get(cid)
    left = live_offers(game)
    if left:
        return f"אמרת לא ל{club.name if club else 'אקדמיה'}. נשארו אחרות."
    clear_offers(game)
    game.me.morale = clamp(game.me.morale + 2, 5, 99)
    return "נשארת איפה שאתה. יש עוד זמן."
