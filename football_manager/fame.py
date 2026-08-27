# -*- coding: utf-8 -*-
"""
football_manager.fame
=====================
מה שקורה לך בגלל שאתה מפורסם, ולא בגלל שאתה טוב.

חסויות היו כל מה שהיה כאן, וזה חלק קטן מהתמונה. שחקן שהפך לשם עולמי
מקבל טלפונים מסוג אחר לגמרי: איש עסקים שרוצה אותך כשותף ולא כפרזנטור,
ליגה בחו"ל שמוכנה לשלם על עצם זה שתשחק בה, התאחדות שרוצה אותך כפנים
של קמפיין, סרט דוקו, מותג שרוצה קולקציה על שמך.

לכל פנייה כזאת יש מחיר שהוא לא כסף: זמן, אימונים שהחמצת, ולפעמים
המוניטין עצמו. פנייה גדולה שמגיעה בזמן הלא נכון היא בדיוק ההחלטה
שהופכת קריירה לסיפור.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from . import data as D
from .models import Player, clamp, gain_reputation

# סוג, כותרת, סף שם עולמי, מכפיל תשלום, מחיר בכושר/חדות
VENTURES = [
    ("tycoon", "שותפות עסקית", 62, 3.4, 6),
    ("league", "פנייה מליגה זרה", 70, 5.5, 0),
    ("ambassador", "שגריר קמפיין", 58, 2.2, 4),
    ("collection", "קולקציה על שמך", 74, 3.0, 3),
    ("documentary", "סרט דוקו", 66, 1.6, 8),
    ("academy", "אקדמיה על שמך", 78, 2.6, 5),
]

TYCOONS = [
    "קרן השקעות אטלס", "אחים ורדימון החזקות", "ליאון קפיטל",
    "משפחת דה־קסטרו", "אוליב גרופ", "נורת'סטאר ונצ'רס",
]

FOREIGN_LEAGUES = [
    ("ליגת המפרץ", 1.9), ("הליגה הצפון־אמריקאית", 1.35),
    ("הליגה היפנית", 1.15), ("הליגה הטורקית", 1.25),
    ("הליגה הסעודית", 2.1), ("הליגה הסינית", 1.6),
]

CAMPAIGNS = [
    "קמפיין תיירות", "מיזם ספורט לנוער", "קמפיין בטיחות בדרכים",
    "פסטיבל ספורט בינלאומי", "מיזם חינוך דרך כדורגל",
]


def fame_score(player: Player, club_reputation: float = 40.0,
               honours: int = 0) -> float:
    """0-100. לא "כמה אתה טוב" אלא "כמה אנשים מחוץ לכדורגל מכירים אותך"."""
    score = player.reputation * 0.70
    score += player.media_skill * 0.22
    score += min(16.0, (player.career.goals + player.career.assists) * 0.05)
    score += club_reputation * 0.10
    score += min(10.0, honours * 2.5)
    if player.has_trait("media_darling"):
        score += 8.0
    if player.has_trait("hothead"):
        score -= 3.0
    return clamp(score, 0.0, 100.0)


def open_ventures(fame: float) -> List[tuple]:
    return [v for v in VENTURES if fame >= v[2]]


def venture_offer(game, rng: random.Random) -> Optional[Dict[str, Any]]:
    """פנייה אחת, אם מישהו בכלל מתעניין השבוע."""
    me = game.me
    club = game.my_club
    fame = fame_score(me, club.reputation if club else 40.0, len(game.honours))
    available = open_ventures(fame)
    if not available:
        return None
    # ככל שאתה גדול יותר, כך הטלפון מצלצל יותר
    if rng.random() > 0.05 + fame / 900.0:
        return None

    kind, title, _, mult, cost = rng.choice(available)
    base = int(fame * fame * 24 * mult)
    payout = int(base * rng.uniform(0.75, 1.4))

    offer: Dict[str, Any] = {
        "kind": kind, "title": title, "payout": payout,
        "cost": cost, "weeks": rng.randint(1, 3),
    }

    if kind == "tycoon":
        who = rng.choice(TYCOONS)
        offer["who"] = who
        offer["equity"] = rng.randint(3, 12)
        offer["text"] = (f"{who} רוצים אותך כשותף, לא כפרזנטור. "
                         f"₪{payout:,} ו-{offer['equity']}% מהמיזם.")
    elif kind == "league":
        league, factor = rng.choice(FOREIGN_LEAGUES)
        offer["who"] = league
        offer["payout"] = int(payout * factor)
        offer["text"] = (f"{league} מוכנים לשלם ₪{offer['payout']:,} בשנה — "
                         f"על עצם זה שתשחק שם. הרמה נמוכה מהמקום שלך היום.")
        offer["rep_cost"] = 4.0
    elif kind == "ambassador":
        who = rng.choice(CAMPAIGNS)
        offer["who"] = who
        offer["text"] = (f"הוזמנת להיות הפנים של {who}. "
                         f"₪{payout:,}, וכמה ימי צילום באמצע העונה.")
    elif kind == "collection":
        offer["who"] = rng.choice(["נייקי", "אדידס", "פומה", "אמברו"])
        offer["text"] = (f"{offer['who']} רוצים קולקציה על שמך. "
                         f"₪{payout:,} מראש, ואחוזים מהמכירות.")
        offer["royalty"] = rng.randint(2, 7)
    elif kind == "documentary":
        offer["who"] = rng.choice(["נטפליקס", "אמזון", "ערוץ הספורט"])
        offer["text"] = (f"{offer['who']} רוצים לעשות עליך סדרה. "
                         f"₪{payout:,}, וצוות שילווה אותך חודשיים.")
    else:
        offer["who"] = "עיריית " + rng.choice(["באר שבע", "חיפה", "נתניה", "אשדוד"])
        offer["text"] = (f"{offer['who']} מציעים לפתוח אקדמיה על שמך. "
                         f"₪{payout:,}, ומשהו שיישאר אחרייך.")
    return offer


def accept_venture(game, offer: Dict[str, Any]) -> List[str]:
    """לוקח את העסקה. הכסף נכנס, והמחיר נגבה מהמגרש."""
    me = game.me
    out = [f"✍️ סגרת: {offer['title']} — {offer.get('who', '')}."]
    game.money += offer["payout"]
    out.append(f"   ₪{offer['payout']:,} נכנסו לחשבון.")

    if offer["cost"]:
        me.fitness = clamp(me.fitness - offer["cost"], 0, 100)
        me.sharpness = clamp(me.sharpness - offer["cost"] * 1.4, 0, 100)
        out.append(f"   ימי הצילום עלו לך בכושר ובחדות.")

    gain_reputation(me, 1.6)
    me.media_skill = clamp(me.media_skill + 2.2, 0, 100)

    if offer["kind"] == "tycoon":
        book = game.flags.setdefault("ventures", [])
        book.append({"who": offer.get("who", ""), "equity": offer["equity"],
                     "value": offer["payout"], "year": game.year})
        out.append(f"   {offer['equity']}% מהמיזם רשומים על שמך — "
                   f"זה ימשיך לעבוד גם אחרי שתפרוש.")
    elif offer["kind"] == "league":
        gain_reputation(me, -offer.get("rep_cost", 0))
        game.set_flag("open_to_europe", True)
        out.append("   בכדורגל האירופי הרימו גבה. הכסף שווה את זה?")
    elif offer["kind"] == "collection":
        book = game.flags.setdefault("royalties", [])
        book.append({"who": offer.get("who", ""), "rate": offer["royalty"]})
        out.append(f"   {offer['royalty']}% מכל פריט שנמכר.")
    elif offer["kind"] == "academy":
        game.set_flag("academy", offer.get("who", ""))
        out.append("   ילדים ילבשו את השם שלך על הגב.")
    return out


def decline_venture(game, offer: Dict[str, Any]) -> str:
    me = game.me
    if offer["kind"] == "league" and me.age >= 32:
        return ("אמרת לא. בגיל הזה לא בטוח שיצלצלו שוב "
                "— אבל אתה עוד רוצה לשחק כדורגל.")
    me.morale = clamp(me.morale + 1.5, 5, 99)
    return "אמרת לא. הראש נשאר על המגרש."


def venture_book(game) -> List[Dict[str, Any]]:
    data = game.flags.get("ventures")
    return data if isinstance(data, list) else []


def royalty_book(game) -> List[Dict[str, Any]]:
    data = game.flags.get("royalties")
    return data if isinstance(data, list) else []


def passive_income(game) -> int:
    """מה שממשיך להיכנס כל עונה מהמיזמים שסגרת."""
    total = 0
    for row in venture_book(game):
        total += int(row["value"] * row["equity"] / 100.0 * 0.22)
    fame = fame_score(game.me, game.my_club.reputation if game.my_club else 40,
                      len(game.honours))
    for row in royalty_book(game):
        total += int(fame * fame * row["rate"] * 1.4)
    return total


def fame_lines(game) -> List[str]:
    """מה השם שלך שווה עכשיו, בשורות."""
    me = game.me
    club = game.my_club
    fame = fame_score(me, club.reputation if club else 40.0, len(game.honours))
    out = [f"שם עולמי: {fame:.0f} מתוך 100"]
    tiers = open_ventures(fame)
    if tiers:
        out.append("פתוח לך: " + ", ".join(t[1] for t in tiers))
    else:
        nxt = min(VENTURES, key=lambda v: v[2])
        out.append(f"הפנייה הראשונה מסוג הזה תגיע סביב {nxt[2]} — "
                   f"{nxt[1]}.")
    income = passive_income(game)
    if income:
        out.append(f"הכנסה פסיבית מהמיזמים: ₪{income:,} לעונה")
    return out
