"""
החיים המסחריים של שחקן: חסויות, תקשורת וסוכנים.

הרעיון: ההצעות שמגיעות אליך הן פונקציה של מי שאתה — מוניטין, גיל,
שערים, כריזמה תקשורתית והמועדון שאתה משחק בו. שחקן בן 19 בליגה
הלאומית מקבל מוסך מקומי; אותו שחקן בגיל 26 אחרי עונה של 24 שערים
בליגת האלופות מקבל טלפון מנייקי, ולא באותו סכום.

וגם: לא כל הצעה חייבת לנחות בשבוע של משחק.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

from . import data as D
from .models import Player, clamp


# ---------------------------------------------------------------------------
# מדד הערך המסחרי
# ---------------------------------------------------------------------------

def marketability(player: Player, club_reputation: float = 40.0) -> float:
    """0-100. כמה מותג היה רוצה את הפנים שלך על שלט חוצות."""
    goals = player.career.goals + player.season.goals * 2
    score = player.reputation * 0.62
    score += player.media_skill * 0.20
    score += min(22.0, goals * 0.16)
    score += club_reputation * 0.12
    if player.age <= 23:
        score += 5.0                      # סיפור של כישרון צעיר נמכר טוב
    elif player.age >= 33:
        score -= 6.0
    if player.has_trait("media_darling"):
        score += 9.0
    if player.has_trait("hothead"):
        score -= 4.0
    if player.has_trait("loyal"):
        score += 2.0
    return clamp(score, 0.0, 100.0)


def open_tiers(market: float) -> List[tuple]:
    """אילו דרגי מותגים בכלל מסתכלים עליך."""
    return [tier for tier in D.SPONSOR_TIERS if market >= tier[2]]


# ---------------------------------------------------------------------------
# הצעת חסות
# ---------------------------------------------------------------------------

def sponsor_offer(player: Player, rng: random.Random,
                  club_reputation: float = 40.0,
                  match_week: bool = False,
                  honours: int = 0) -> Optional[Dict[str, Any]]:
    """בונה הצעת חסות שמתאימה לשחקן הזה עכשיו. None אם אף אחד לא מתעניין.

    ההצעה איננה סכום חד־פעמי: זה חוזה שנתי לכמה שנים, עם סעיפי בונוס
    שמשלמים לפי מה שתעשה בפועל. חוזה של כוכב באמת נראה אחרת מחוזה
    של נער — גם בסכום, גם באורך וגם במה שכתוב בו.
    """
    market = marketability(player, club_reputation)
    tiers = open_tiers(market)
    if not tiers:
        return None

    # ככל שהערך המסחרי גבוה, סביר יותר שיתקשר מותג מהדרג העליון
    weights = []
    for index, tier in enumerate(tiers):
        over_min = max(0.0, market - tier[2]) / 30.0
        weights.append(((index + 1) ** 2) * (0.4 + over_min))
    total = sum(weights)
    roll = rng.random() * total
    chosen = tiers[-1]
    for tier, weight in zip(tiers, weights):
        roll -= weight
        if roll <= 0:
            chosen = tier
            break

    key, tier_he, min_rep, base, media_mult, brands = chosen
    kind_key = rng.choice(list(D.DEAL_KINDS))
    kind = D.DEAL_KINDS[kind_key]

    # התשלום נגזר מהדרג, מהערך המסחרי, מהתארים ומסוג החוזה
    over = max(0.0, market - min_rep) / 40.0
    annual = base * kind["pay"] * (0.75 + over * 1.9) * rng.uniform(0.88, 1.22)
    annual *= 1.0 + min(0.45, honours * 0.06)
    years = 1
    if key == "national":
        years = rng.randint(1, 2)
    elif key in ("continental", "global"):
        years = rng.randint(2, 4)
    shoot_days = max(1, round(kind["days"] * media_mult))

    # סעיפי בונוס — כמה שהמותג גדול יותר, כך יש בהם יותר בשר
    clause_count = {"local": 1, "national": 1, "continental": 2, "global": 3}[key]
    pool = list(D.BONUS_CLAUSES)
    rng.shuffle(pool)
    clauses = [c[0] for c in pool[:clause_count]]

    return {
        "brand": rng.choice(brands),
        "tier": key,
        "tier_he": tier_he,
        "kind": kind_key,
        "kind_he": kind["name"],
        "annual": int(round(annual / 1000) * 1000),
        "amount": int(round(annual / 1000) * 1000),   # תאימות לשמורות ישנות
        "years": years,
        "days": shoot_days,
        "media_gain": kind["media"],
        "clauses": clauses,
        # ימי צילום נופלים בשבוע משחק רק לפעמים — ותמיד אפשר לדחות אותם
        "clashes": match_week and rng.random() < 0.30,
        "market": round(market, 1),
    }


CLAUSE_BY_KEY = {row[0]: row for row in D.BONUS_CLAUSES}


def clause_text(key: str, annual: int) -> str:
    row = CLAUSE_BY_KEY.get(key)
    if not row:
        return ""
    unit = int(round(annual * row[3] / 100) * 100)
    return f"{row[1]}: ₪{unit:,}"


def deal_summary(offer: Dict[str, Any]) -> str:
    """תיאור ההצעה בשורה אחת."""
    annual = offer.get("annual", offer.get("amount", 0))
    span = "לשנה" if offer["years"] == 1 else f"× {offer['years']} שנים"
    return (f"{offer['brand']} · {offer['kind_he']} · "
            f"₪{annual:,} לעונה {span} · {offer['days']} ימי צילומים")


def deal_lines(offer: Dict[str, Any]) -> List[str]:
    """פירוט מלא של החוזה, כולל מה שכתוב בסעיפים."""
    annual = offer.get("annual", offer.get("amount", 0))
    lines = [deal_summary(offer),
             f"סך הכל מובטח: ₪{annual * offer['years']:,}"]
    for key in offer.get("clauses", ()):
        text = clause_text(key, annual)
        if text:
            lines.append("• " + text)
    return lines


# ---------------------------------------------------------------------------
# תיק החסויות
# ---------------------------------------------------------------------------

def sign_deal(portfolio: List[Dict[str, Any]], offer: Dict[str, Any],
              year: int) -> Dict[str, Any]:
    """מוסיף חוזה חתום לתיק. מותג שכבר איתך פשוט מתחדש."""
    annual = offer.get("annual", offer.get("amount", 0))
    deal = {
        "brand": offer["brand"], "tier": offer["tier"],
        "tier_he": offer["tier_he"], "kind_he": offer["kind_he"],
        "annual": annual, "years_left": offer["years"],
        "clauses": list(offer.get("clauses", ())),
        "signed": year, "earned": 0,
    }
    portfolio[:] = [d for d in portfolio if d["brand"] != offer["brand"]]
    portfolio.append(deal)
    return deal


def weekly_retainer(portfolio: List[Dict[str, Any]], season_weeks: int) -> int:
    """מה שהחסויות משלמות לך כל שבוע. זה ההבדל בין תשלום חד־פעמי
    לבין הכנסה שממשיכה לזרום כל עוד החוזה בתוקף."""
    if not portfolio:
        return 0
    return int(sum(d["annual"] for d in portfolio) / max(1, season_weeks))


def season_bonuses(portfolio: List[Dict[str, Any]], player: Player,
                   trophies: int, caps: int) -> List[Tuple[str, int]]:
    """תשלומי הסעיפים בסוף עונה, לפי מה שבאמת עשית."""
    payouts: List[Tuple[str, int]] = []
    measures = {
        "goals": player.season.goals,
        "assists": player.season.assists,
        "trophies": trophies,
        "caps": caps,
        "rating": 1 if player.season.apps >= 10 and player.season.avg_rating >= 7.0 else 0,
    }
    for deal in portfolio:
        for key in deal.get("clauses", ()):
            row = CLAUSE_BY_KEY.get(key)
            if not row:
                continue
            units = measures.get(row[2], 0)
            if units <= 0:
                continue
            amount = int(round(deal["annual"] * row[3] * units / 100) * 100)
            if amount:
                deal["earned"] = deal.get("earned", 0) + amount
                payouts.append((f"{deal['brand']} · {row[1]}", amount))
    return payouts


def tick_portfolio(portfolio: List[Dict[str, Any]]) -> List[str]:
    """מקדם שנה בכל החוזים ומוציא את מה שנגמר."""
    lines: List[str] = []
    for deal in list(portfolio):
        deal["years_left"] -= 1
        if deal["years_left"] <= 0:
            portfolio.remove(deal)
            lines.append(f"📄 החוזה עם {deal['brand']} הסתיים.")
    return lines


def renewal_offer(deal: Dict[str, Any], player: Player, rng: random.Random,
                  club_reputation: float = 40.0) -> Dict[str, Any]:
    """הצעת חידוש. הסכום החדש משקף את מי שנעשית מאז שחתמת."""
    market = marketability(player, club_reputation)
    factor = clamp(0.55 + market / 55.0, 0.5, 2.6) * rng.uniform(0.9, 1.15)
    annual = int(round(deal["annual"] * factor / 1000) * 1000)
    return {
        "brand": deal["brand"], "tier": deal["tier"], "tier_he": deal["tier_he"],
        "kind_he": deal["kind_he"], "annual": annual, "amount": annual,
        "years": rng.randint(2, 4), "days": 2,
        "media_gain": 4, "clauses": list(deal.get("clauses", ())),
        "clashes": False, "market": round(market, 1), "renewal": True,
    }


def portfolio_total(portfolio: List[Dict[str, Any]]) -> int:
    return int(sum(d["annual"] for d in portfolio))


# ---------------------------------------------------------------------------
# עבודות תקשורת
# ---------------------------------------------------------------------------

def media_offer(player: Player, rng: random.Random) -> Optional[Dict[str, Any]]:
    """הצעת עבודה תקשורתית שמתאימה לכריזמה ולמוניטין הנוכחיים."""
    options = [job for job in D.MEDIA_JOBS
               if player.media_skill >= job[2] and player.reputation >= job[3]]
    if not options:
        return None
    key, name, _, _, base = rng.choice(options)
    factor = 0.7 + (player.reputation / 100.0) * 0.9 + (player.media_skill / 100.0) * 0.6
    return {
        "key": key,
        "name": name,
        "amount": int(round(base * factor * rng.uniform(0.9, 1.2) / 1000) * 1000),
    }


# ---------------------------------------------------------------------------
# סוכנים
# ---------------------------------------------------------------------------

def agent_pitch(player: Player, rng: random.Random,
                clubs: List[Any], current_club: Optional[Any]) -> Optional[Dict[str, Any]]:
    """סוכן שמזהה שאתה שווה יותר ממה שאתה מקבל, ומביא יעד קונקרטי."""
    current_rep = current_club.reputation if current_club else 20
    targets = [c for c in clubs
               if (not current_club or c.cid != current_club.cid)
               and c.reputation > current_rep + 6
               and c.reputation <= player.reputation + 26]
    if not targets:
        return None
    target = rng.choice(targets)
    raise_factor = rng.uniform(1.25, 2.1) * (1 + (target.reputation - current_rep) / 130.0)
    return {
        "agent": rng.choice(D.AGENT_NAMES),
        "club": target.cid,
        "club_name": target.name,
        "wage": int(round(player.contract.wage * raise_factor / 500) * 500),
        "fee": int(round(player.contract.wage * raise_factor * 0.12 / 500) * 500),
    }
