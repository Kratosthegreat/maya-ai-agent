"""
כלכלת מועדון: אצטדיון, קהל, תקציב, שדרוג מתקנים וגיוס בעלי תפקיד.

כל מספר כאן מזין את הסימולציה עצמה — הקהל קובע הכנסה, ההכנסה מממנת
מתקנים וצוות, והמתקנים והצוות משפיעים בחזרה על ההתפתחות, הפציעות
והביצועים במגרש.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from . import data as D
from .models import Club, Player, clamp, staff_member

# כפל ההכנסה המסחרית לפי דרג הליגה
COMMERCIAL_POWER = 3.1
TIER_COMMERCIAL = {0: 3.0, 1: 2.18, 2: 1.5, 3: 1.0}


# ---------------------------------------------------------------------------
# קהל והכנסות משחק בית
# ---------------------------------------------------------------------------

def attendance_for(club: Club, opponent: Club, rng: random.Random,
                   position: int = 10, size: int = 20,
                   form: float = 0.5) -> int:
    """כמה אנשים באו. תפוסה נגזרת מאהדה, מיקום בטבלה, היריבה והכושר."""
    standing = 1.0 - (position - 1) / max(1, size - 1)     # 1.0 = ראשונה
    occupancy = (0.24
                 + club.fan_support / 100.0 * 0.34
                 + standing * 0.17
                 + opponent.reputation / 100.0 * 0.14
                 + (form - 0.5) * 0.16)
    occupancy *= rng.uniform(0.93, 1.07)
    occupancy = clamp(occupancy, 0.22, 1.0)
    return int(round(club.capacity * occupancy))


def matchday_income(club: Club, attendance: int) -> int:
    """כרטיסים ועוד 24% מזון, חנות וחניה."""
    return int(attendance * club.ticket_price * 1.24)


# ---------------------------------------------------------------------------
# מאזן שבועי
# ---------------------------------------------------------------------------

def wage_bill(club: Club, players: Dict[str, Player]) -> int:
    """שכר שבועי לכל הסגל."""
    total = 0
    for pid in club.squad:
        player = players.get(pid)
        if player and not player.retired:
            total += int(player.contract.wage)
    return total


def commercial_income(club: Club) -> int:
    """שידורים, חסויות ומרצ'נדייז — הכנסה קבועה בכל שבוע."""
    tier = next((l["tier"] for l in D.LEAGUES if l["id"] == club.league_id), 2)
    return int((club.reputation ** COMMERCIAL_POWER) * TIER_COMMERCIAL.get(tier, 1.2))


def weekly_finances(club: Club, players: Dict[str, Player],
                    matchday: int = 0) -> Dict[str, int]:
    """מריץ שבוע כספי אחד על קופת המועדון ומחזיר פירוט."""
    wages = wage_bill(club, players)
    staff = club.staff_wage_bill
    commercial = commercial_income(club)
    net = commercial + matchday - wages - staff
    club.balance = round(club.balance + net)
    return {"commercial": commercial, "matchday": matchday,
            "wages": wages, "staff": staff, "net": net,
            "balance": int(club.balance)}


# ---------------------------------------------------------------------------
# שדרוג מתקנים
# ---------------------------------------------------------------------------

def upgrade_cost(club: Club, kind: str) -> int:
    """מחיר השדרוג הבא. ככל שהמתקן טוב יותר, כל נקודה יקרה יותר."""
    spec = D.FACILITIES[kind]
    if kind == "stadium":
        added = stadium_expansion(club)
        return int(spec["cost"] * added / 1000.0)
    level = club.facility(kind)
    return int(spec["cost"] * (0.55 + (level / 100.0) ** 1.7 * 2.6))


def stadium_expansion(club: Club) -> int:
    """כמה מקומות נוספים בהרחבה הבאה, מעוגל ל-500."""
    added = club.capacity * D.FACILITIES["stadium"]["unit"]
    return int(round(max(1_000, min(added, 9_000)) / 500) * 500)


def work_in_progress(club: Club, kind: str) -> Optional[Dict[str, Any]]:
    return next((w for w in club.works if w["kind"] == kind), None)


def can_upgrade(club: Club, kind: str) -> Optional[str]:
    """מחזיר סיבה למה אי אפשר, או None אם אפשר."""
    if work_in_progress(club, kind):
        return "העבודות כבר בעיצומן."
    if kind != "stadium" and club.facility(kind) >= 95:
        return "המתקן כבר ברמה הגבוהה ביותר."
    if kind == "stadium" and club.capacity >= 75_000:
        return "אין לאן להרחיב יותר."
    if club.balance < upgrade_cost(club, kind):
        return "אין מספיק כסף בקופה."
    return None


def start_upgrade(club: Club, kind: str) -> str:
    """מתחיל פרויקט בנייה. הכסף יורד מיד, התוצאה מגיעה בעוד כמה שבועות."""
    blocked = can_upgrade(club, kind)
    if blocked:
        return blocked
    spec = D.FACILITIES[kind]
    cost = upgrade_cost(club, kind)
    club.balance = round(club.balance - cost)
    club.works.append({
        "kind": kind,
        "weeks_left": int(spec["weeks"]),
        "cost": cost,
        "added": stadium_expansion(club) if kind == "stadium" else 0,
    })
    if kind == "stadium":
        return (f"אישרת הרחבה של {club.works[-1]['added']:,} מקומות ב{club.stadium_name}. "
                f"{spec['weeks']} שבועות עבודה.")
    return f"אישרת שדרוג של {spec['name']}. {spec['weeks']} שבועות עבודה."


def tick_works(club: Club) -> List[str]:
    """מקדם את הבנייה בשבוע. מחזיר הודעות על פרויקטים שהסתיימו."""
    messages: List[str] = []
    remaining: List[Dict[str, Any]] = []
    for work in club.works:
        work["weeks_left"] = int(work["weeks_left"]) - 1
        if work["weeks_left"] > 0:
            remaining.append(work)
            continue
        spec = D.FACILITIES[work["kind"]]
        if work["kind"] == "stadium":
            club.capacity += int(work["added"])
            messages.append(f"🏟️ ההרחבה הושלמה — {club.stadium_name} מכיל עכשיו "
                            f"{club.capacity:,} מקומות.")
        else:
            field = spec["field"]
            before = getattr(club, field)
            setattr(club, field, int(clamp(before + spec["unit"], 1, 99)))
            messages.append(f"🏗️ {spec['name']} שודרגו: {int(before)} → "
                            f"{getattr(club, field)}.")
    club.works = remaining
    return messages


# ---------------------------------------------------------------------------
# שוק בעלי התפקיד
# ---------------------------------------------------------------------------

def staff_candidates(rng: random.Random, club: Club, role: str,
                     count: int = 3) -> List[Dict[str, Any]]:
    """מועמדים לתפקיד. מועדון גדול מושך מועמדים טובים יותר."""
    out = []
    for _ in range(count):
        quality = int(clamp(club.reputation + rng.gauss(4, 16), 12, 95))
        out.append(staff_member(rng, role, quality))
    return sorted(out, key=lambda c: -c["quality"])


def hire_staff(club: Club, role: str, candidate: Dict[str, Any]) -> str:
    """מגייס בעל תפקיד. דמי חתימה = שכר של ארבעה שבועות."""
    fee = int(candidate["wage"]) * 4
    if club.balance < fee:
        return "אין מספיק כסף בקופה לדמי החתימה."
    club.balance = round(club.balance - fee)
    outgoing = club.staff.get(role)
    club.staff[role] = dict(candidate)
    name = D.STAFF_ROLES[role]["name"]
    if outgoing:
        return (f"{candidate['name']} מחליף את {outgoing['name']} בתפקיד {name} "
                f"(איכות {candidate['quality']}).")
    return f"{candidate['name']} נכנס לתפקיד {name} (איכות {candidate['quality']})."


def fire_staff(club: Club, role: str) -> str:
    """מפטר בעל תפקיד. פיצויים = שכר של שמונה שבועות."""
    member = club.staff.get(role)
    if not member:
        return "המשרה כבר פנויה."
    severance = int(member["wage"]) * 8
    club.balance = round(club.balance - severance)
    del club.staff[role]
    return (f"{member['name']} סיים את תפקידו. פיצויים: ₪{severance:,}.")
