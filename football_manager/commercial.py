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
from typing import Any, Dict, List, Optional

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
                  match_week: bool = False) -> Optional[Dict[str, Any]]:
    """בונה הצעת חסות שמתאימה לשחקן הזה עכשיו. None אם אף אחד לא מתעניין."""
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

    # התשלום נגזר מהדרג, מהערך המסחרי ומסוג החוזה
    over = max(0.0, market - min_rep) / 40.0
    amount = base * kind["pay"] * (0.75 + over * 1.5) * rng.uniform(0.85, 1.25)
    years = rng.randint(1, 3) if key in ("continental", "global") else 1
    shoot_days = max(1, round(kind["days"] * media_mult))

    return {
        "brand": rng.choice(brands),
        "tier": key,
        "tier_he": tier_he,
        "kind": kind_key,
        "kind_he": kind["name"],
        "amount": int(round(amount / 1000) * 1000),
        "years": years,
        "days": shoot_days,
        "media_gain": kind["media"],
        # רק חלק מההצעות דורשות ימי צילום בשבוע משחק
        "clashes": match_week and rng.random() < 0.35,
        "market": round(market, 1),
    }


def deal_summary(offer: Dict[str, Any]) -> str:
    """תיאור ההצעה בשורה אחת."""
    span = "לשנה" if offer["years"] == 1 else f"ל-{offer['years']} שנים"
    return (f"{offer['brand']} · {offer['kind_he']} · "
            f"₪{offer['amount']:,} {span} · {offer['days']} ימי צילומים")


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
