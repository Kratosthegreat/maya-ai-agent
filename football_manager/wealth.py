# -*- coding: utf-8 -*-
"""
football_manager.wealth
=======================
מה עושים עם הכסף.

עד עכשיו הכסף רק נערם. כאן הוא יכול לעבוד: דירות להשכרה, חנויות,
מסעדה עם השם שלך על השלט, מתחם פאדל, אקדמיה לילדים, קרן מדד,
ואחזקה במועדון. כל נכס משלם תשואה בסוף עונה, שווה בסוף פחות או
יותר ממה ששילמת עליו, ולפעמים קורה לו משהו.

זה גם מה שמחזיק אותך אחרי הפרישה: מי שקנה נכון בגיל 26 לא צריך
לקחת כל עבודה באולפן בגיל 40.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

from . import data as D
from .models import clamp

ASSET_BY_KEY = {row[0]: row for row in D.ASSETS}


def holdings(game) -> List[Dict[str, Any]]:
    """הנכסים שבבעלותך. חיים בדגלים, ולכן נשמרים עם הקריירה."""
    data = game.flags.get("assets")
    if not isinstance(data, list):
        data = []
        game.flags["assets"] = data
    return data


def available(game) -> List[Dict[str, Any]]:
    """מה פתוח לרכישה עכשיו, ולמה משהו נעול."""
    me = game.me
    out = []
    for key, name, category, price, yield_pct, vol, min_rep, desc in D.ASSETS:
        locked = me.reputation < min_rep
        out.append({
            "key": key, "name": name, "category": category, "price": price,
            "yield": yield_pct, "volatility": vol, "desc": desc,
            "min_rep": min_rep, "locked": locked,
            "affordable": game.money >= price,
        })
    return out


def buy(game, key: str) -> str:
    """רוכש נכס."""
    row = ASSET_BY_KEY.get(key)
    if not row:
        return "אין נכס כזה."
    _, name, category, price, yield_pct, vol, min_rep, _ = row
    if game.me.reputation < min_rep:
        return f"{name} — לא פתוח לך עדיין. צריך מוניטין {min_rep}."
    if game.money < price:
        return f"אין מספיק. {name} עולה ₪{price:,}, ויש לך ₪{int(game.money):,}."
    game.spend_money(price)
    holdings(game).append({
        "key": key, "name": name, "category": category,
        "paid": price, "value": price, "year": game.year, "income": 0,
    })
    return f"🏠 קנית: {name} תמורת ₪{price:,}."


def sell(game, index: int) -> str:
    """מוכר נכס לפי מיקומו ברשימה."""
    items = holdings(game)
    if index < 0 or index >= len(items):
        return "אין נכס כזה."
    item = items.pop(index)
    value = int(item["value"])
    game.earn_money(value)
    profit = value - int(item["paid"])
    verdict = (f"רווח של ₪{profit:,}" if profit > 0 else
               f"הפסד של ₪{abs(profit):,}" if profit < 0 else "בדיוק מה ששילמת")
    return f"💼 מכרת את {item['name']} ב-₪{value:,} — {verdict}."


def net_worth(game) -> int:
    """מזומן ועוד שווי הנכסים."""
    return int(game.money) + int(sum(item["value"] for item in holdings(game)))


def portfolio_yield(game) -> int:
    """כמה הנכסים צפויים לשלם בעונה הקרובה."""
    total = 0.0
    for item in holdings(game):
        row = ASSET_BY_KEY.get(item["key"])
        if row:
            total += item["value"] * row[4]
    return int(total)


# ---------------------------------------------------------------------------
# מה קורה לנכסים לאורך זמן
# ---------------------------------------------------------------------------

def season_tick(game, rng: random.Random) -> List[str]:
    """סוף עונה: תשואה, שינוי שווי, ולפעמים אירוע."""
    items = holdings(game)
    if not items:
        return []
    lines: List[str] = []
    total_income = 0
    for item in items:
        row = ASSET_BY_KEY.get(item["key"])
        if not row:
            continue
        _, name, category, price, base_yield, vol, _, _ = row

        # תשואה — סביב הבסיס, עם התנודתיות של הקטגוריה
        realised = base_yield * (1.0 + rng.gauss(0, vol))
        # מסעדה ואקדמיה נשענות על השם שלך
        if item["key"] in ("restaurant", "academy", "agency_stake"):
            realised *= 0.55 + game.me.reputation / 90.0
        income = int(item["value"] * max(-0.25, realised))
        item["income"] = item.get("income", 0) + income
        total_income += income

        # שווי — נדל"ן עולה לאט, עסקים זזים עם התשואה
        drift = 0.028 if "נדל" in category else 0.012
        item["value"] = int(max(price * 0.25,
                                item["value"] * (1 + drift + rng.gauss(0, vol * 0.35))))

    if total_income:
        if total_income > 0:
            game.earn_money(total_income)
            lines.append(f"🏦 הנכסים שלך הכניסו ₪{total_income:,} העונה.")
        else:
            game.spend_money(-total_income)
            lines.append(f"🏦 הנכסים שלך עלו לך ₪{abs(total_income):,} העונה.")

    # אירוע על נכס אחד
    if items and rng.random() < 0.45:
        item = rng.choice(items)
        pool = [ev for ev in D.ASSET_EVENTS if ev[0] == item["category"]]
        if pool:
            _, text, impact = rng.choice(pool)
            shift = int(item["value"] * impact * 0.28)
            item["value"] = int(max(1, item["value"] + shift))
            if impact > 0:
                game.earn_money(max(0, int(item["value"] * impact * 0.10)))
            lines.append(f"📌 {item['name']}: {text}")
    return lines


def summary(game) -> Dict[str, Any]:
    """תמונת מצב למסך הנכסים."""
    items = holdings(game)
    return {
        "cash": int(game.money),
        "assets": int(sum(i["value"] for i in items)),
        "net_worth": net_worth(game),
        "yearly": portfolio_yield(game),
        "count": len(items),
        "items": [dict(i) for i in items],
    }
