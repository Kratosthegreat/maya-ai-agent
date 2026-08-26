# -*- coding: utf-8 -*-
"""
football_manager.coaching
=========================
מה כל תכונה עושה, כמה היא שווה *לך*, ומה יקרה אם תתאמן עליה.

"מה זה צמידות? במה הוא מועיל? האם השחקן צריך אותו ברגע זה?" — שלוש
שאלות שלא הייתה להן תשובה בשום מקום במשחק. כאן יש: הסבר, השפעה
במגרש, וציון רלוונטיות אישי שנגזר מהתפקיד שלך, מהעמדה, מהמסלול
שבחרת ומכמה אתה נמוך בה ביחס לרמה שלך.

וגם: תחזית. כמה תרוויח אם תתאמן על זה חודש, ומה זה יעלה לך.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

from . import data as D
from .models import Player, clamp
from .progression import (SET_PIECE_ATTRS, age_factor, detail_damper,
                          training_shares)

# כמה כל מקור תורם לציון הרלוונטיות
WEIGHT_ROLE_KEY = 34.0
WEIGHT_ROLE_EXTRA = 18.0
WEIGHT_POSITION = 26.0
WEIGHT_PLAN = 22.0
WEIGHT_GAP = 30.0


def explain(attr: str) -> Tuple[str, str, str]:
    """(מה זה, מה זה עושה במשחק, מי צריך את זה)."""
    return D.ATTR_INFO.get(attr) or D.FOCUS_INFO.get(attr) or ("", "", "")


_DEMAND_CACHE: Dict[str, Dict[str, float]] = {}


def _demand_table(position: str) -> Dict[str, float]:
    """כמה כל תכונה נדרשת בעמדה, מנורמל כך שהחשובה ביותר היא 1.0."""
    cached = _DEMAND_CACHE.get(position)
    if cached is not None:
        return cached
    weights = D.POSITION_WEIGHTS[position]
    mapping = D.GROUP_MAP_GK if position == "GK" else D.GROUP_MAP
    raw: Dict[str, float] = {}
    for attr in D.attrs_for(position):
        total = 0.0
        for group, members in mapping.items():
            share = members.get(attr)
            if share:
                total += share * weights.get(group, 0.0)
        raw[attr] = total
    top = max(raw.values()) or 1.0
    table = {attr: value / top for attr, value in raw.items()}
    _DEMAND_CACHE[position] = table
    return table


def position_demand(attr: str, position: str) -> float:
    """0-1: כמה העמדה דורשת את התכונה, ביחס לתכונה החשובה בה ביותר."""
    return _demand_table(position).get(attr, 0.0)


def relevance(game, attr: str) -> Dict[str, Any]:
    """כמה התכונה הזאת שווה לך *עכשיו*, ולמה.

    זו התשובה ל"האם השחקן צריך אותו ברגע זה": לא ציון מוחלט, אלא
    שילוב של מה שהתפקיד דורש, מה שהמסלול צריך, ומה שחסר לך בפועל.
    """
    me = game.me
    row = D.ROLE_BY_KEY.get(me.role)
    reasons: List[str] = []
    score = 0.0
    wanted = 0.0            # 0-1: כמה בכלל צריך ממך את התכונה הזאת

    if row and attr in row[4]:
        score += WEIGHT_ROLE_KEY
        wanted = 1.0
        reasons.append(f"תכונת מפתח ב{row[1]}")
    elif row and attr in row[5]:
        score += WEIGHT_ROLE_EXTRA
        wanted = 0.65
        reasons.append(f"נדרשת ב{row[1]}")

    demand = position_demand(attr, me.position)
    score += demand * WEIGHT_POSITION
    wanted = max(wanted, demand)
    if demand >= 0.55 and not reasons:
        reasons.append(f"חשובה ל{D.POSITION_NAMES_HE[me.position]}")

    # המסלול שבחרת — אם התכונה חוסמת אבן דרך, היא קופצת לראש
    from . import development as DEV
    for entry in DEV.milestone_rows(game):
        if entry["claimed"]:
            continue
        for part in entry["needs"]:
            if part["attr"] == attr and part["have"] < part["need"]:
                score += WEIGHT_PLAN
                wanted = max(wanted, 1.0)
                reasons.append(f"חוסמת אבן דרך של גיל {entry['age']}")
                break
        break

    # כמה אתה נמוך בה ביחס לעצמך — אבל רק במידה שבכלל צריך אותה.
    # חלוץ עם צמידות 5 הוא לא בעיה: זה בדיוק מה שאמור להיות.
    allowed = D.attrs_for(me.position)
    average = sum(me.detail.get(a, 10) for a in allowed) / max(1, len(allowed))
    level = me.detail.get(attr, 10)
    gap = average - level
    if gap > 0:
        score += min(WEIGHT_GAP, gap * 7.0) * wanted
        if gap >= 2.5 and wanted >= 0.4:
            reasons.append("נמוכה ביחס לשאר התכונות שלך")
    elif level >= 17:
        reasons.append("כבר ברמה גבוהה")

    if attr in SET_PIECE_ATTRS:
        score *= 0.55
        reasons.append("מומחיות — משתפרת רק באימון ישיר")

    return {"attr": attr, "score": round(clamp(score, 0, 100)),
            "reasons": reasons[:3], "level": level, "average": round(average, 1)}


def needs_table(game) -> List[Dict[str, Any]]:
    """כל התכונות שלך, מסודרות לפי כמה הן שוות לך עכשיו.

    הפסק ניתן ביחס לעצמך ולא בסולם מוחלט: "מקום 1 מתוך 36" אומר לך
    יותר מ-"45 מתוך 100", כי מה שחשוב הוא במה לבחור עכשיו.
    """
    rows = [relevance(game, attr) for attr in D.attrs_for(game.me.position)]
    rows.sort(key=lambda row: -row["score"])
    total = len(rows)
    top = rows[0]["score"] if rows else 1
    for index, row in enumerate(rows):
        row["rank"] = index + 1
        row["of"] = total
        share = row["score"] / top if top else 0.0
        if index < 3 and share >= 0.75:
            row["verdict"] = "כן — זה מה שחסר לך עכשיו"
        elif share >= 0.62:
            row["verdict"] = "שווה, אבל לא הכי דחוף"
        elif share >= 0.35:
            row["verdict"] = "לא בראש סדר העדיפויות"
        else:
            row["verdict"] = "לא רלוונטי אליך"
    return rows


def relevance_of(game, attr: str) -> Dict[str, Any]:
    """הרלוונטיות של תכונה אחת, כולל הדירוג שלה מול כל השאר."""
    for row in needs_table(game):
        if row["attr"] == attr:
            return row
    row = relevance(game, attr)
    row.update({"rank": 0, "of": 0, "verdict": "לא רלוונטי אליך"})
    return row


def ranked_needs(game, limit: int = 6) -> List[Dict[str, Any]]:
    """מה הכי כדאי לך לעבוד עליו, מסודר."""
    return needs_table(game)[:limit]


# ---------------------------------------------------------------------------
# תחזית: מה יקרה אם אתאמן על זה
# ---------------------------------------------------------------------------

def weekly_rate(game, attr: str, intensity: Optional[float] = None) -> float:
    """כמה נקודות (1-20) תרוויח בשבוע בממוצע, אם תתאמן על התכונה הזאת.

    זו הנוסחה האמיתית מ-weekly_training, בלי ההגרלה — ולכן זו תחזית
    ולא הבטחה. אבל היא נכונה בממוצע, וזה מה שחסר כדי לבחור.
    """
    me = game.me
    club = game.my_club
    intensity = game.intensity if intensity is None else intensity
    from .models import personality_effect

    facilities = club.training_facilities if club else 45
    assistant = club.staff_quality("assistant") if club else 0

    base = 0.165 * intensity
    base *= 0.55 + facilities / 110.0
    base *= 1.0 + assistant / 420.0
    base *= max(0.15, age_factor(me.age))
    base *= 1.0 + clamp(me.potential - me.overall, -10, 18) * 0.032
    if me.has_trait("workhorse"):
        base *= 1.30
    base *= 0.75 + me.morale / 200.0
    base *= personality_effect(me)[0]
    base *= 0.55 + me.detail.get("determination", 10) / 22.0
    base *= 1.025                              # תוחלת ההגרלה 0.7-1.35

    headroom = me.potential - me.overall
    if headroom <= 0:
        base *= 0.06
    elif headroom < 6:
        base *= 0.20 + headroom * 0.13

    shares = training_shares(me, attr)
    share = shares.get(attr, 0.0)
    allowed = list(shares)
    average = (sum(me.detail.get(a, 10) for a in allowed) / len(allowed)
               if allowed else 10.0)
    level = me.detail.get(attr, 10)
    return base * share * detail_damper(level, average) / 5.0


def projected_gain(game, attr: str, weeks: int,
                   intensity: Optional[float] = None) -> float:
    """כמה תעלה התכונה בפועל ב-N שבועות.

    לא הכפלה של הקצב הנוכחי במספר השבועות: ככל שהתכונה עולה, הבלם
    מאט אותה, והתקרה 20 עוצרת אותה. תחזית קווית הייתה מבטיחה כפול
    ממה שיקרה — וזה גרוע יותר מאין תחזית.
    """
    me = game.me
    level = float(me.detail.get(attr, 10))
    if level >= 20:
        return 0.0
    allowed = D.attrs_for(me.position)
    others = sum(me.detail.get(a, 10) for a in allowed if a != attr)
    count = max(1, len(allowed))
    rate = weekly_rate(game, attr, intensity)
    base_level = float(me.detail.get(attr, 10))
    if rate <= 0:
        return 0.0
    total = 0.0
    for _ in range(weeks):
        if level >= 20:
            break
        average = (others + level) / count
        # מנרמלים מול הבלם שכבר נכלל ב-rate, ומחילים את הבלם העדכני
        base = detail_damper(base_level, average)
        now = detail_damper(level, average)
        step = rate * (now / base if base > 0 else 1.0)
        level = min(20.0, level + step)
        total += step
    return min(total, 20.0 - me.detail.get(attr, 10))


def forecast(game, attr: str, weeks: int = 6,
             intensity: Optional[float] = None) -> Dict[str, Any]:
    """תחזית לחודש וחצי של אימון על התכונה הזאת."""
    me = game.me
    rate = weekly_rate(game, attr, intensity)
    level = me.detail.get(attr, 10)
    gain = projected_gain(game, attr, weeks, intensity)
    intensity = game.intensity if intensity is None else intensity
    fitness_cost = 2.5 + 5.0 * intensity
    injury = (0.022 * intensity * me.injury_risk) if intensity > 1.15 else 0.0

    # מה עוד יזוז אגב
    shares = training_shares(me, attr)
    side = sorted(((v, a) for a, v in shares.items() if a != attr),
                  reverse=True)[:3]
    return {
        "attr": attr,
        "rate": round(rate, 3),
        "weeks_per_point": (round(1.0 / rate, 1) if rate > 0.001 else None),
        "gain": round(gain, 1),
        "level": level,
        "target": min(20, int(round(level + gain))),
        "fitness_cost": round(fitness_cost, 1),
        "injury_pct": round(injury * 100, 1),
        "side": [a for _, a in side],
    }


def forecast_line(game, attr: str) -> str:
    """שורה אחת שאומרת מה יקרה. זה מה שהיה חסר כדי לבחור אימון."""
    data = forecast(game, attr)
    name = D.DETAIL_NAMES_HE.get(attr, attr)
    if data["weeks_per_point"] is None:
        return f"{name}: כרגע לא תתקדם בזה — הגעת לתקרת הפוטנציאל."
    weeks = data["weeks_per_point"]
    pace = (f"נקודה כל {weeks:.0f} שבועות" if weeks >= 1.5
            else f"כ-{1 / weeks:.1f} נקודות בשבוע")
    side = ", ".join(D.DETAIL_NAMES_HE[a] for a in data["side"])
    return (f"{name} {data['level']} → {data['target']} בשישה שבועות "
            f"({pace}). אגב זה יעלו גם {side}.")


# ---------------------------------------------------------------------------
# איך התפתחתי, ובכמה
# ---------------------------------------------------------------------------

def growth_log(game) -> List[Dict[str, Any]]:
    data = game.flags.get("growth_log")
    return data if isinstance(data, list) else []


def growth_summary(game) -> Dict[str, Any]:
    """כל מה שצריך כדי לענות על "עד כמה התפתחתי, ובמה".

    לא "כאילו מתפתח": מספרים מדויקים מהעונה הראשונה שנרשמה ועד היום,
    כולל גובה, משקל, כל תכונה, והעונות שבהן זה קרה.
    """
    me = game.me
    log = growth_log(game)
    if not log:
        return {"seasons": [], "since": None, "moved": [], "physical": None}

    first = log[0]
    rows = []
    previous = None
    for shot in log:
        row = dict(shot)
        if previous:
            row["d_overall"] = shot["overall"] - previous["overall"]
            row["d_height"] = shot["height"] - previous["height"]
            row["d_weight"] = shot["weight"] - previous["weight"]
            gained = sum(max(0, shot["detail"].get(a, 10) - previous["detail"].get(a, 10))
                         for a in shot["detail"])
            row["d_points"] = gained
        else:
            row["d_overall"] = row["d_height"] = row["d_weight"] = 0
            row["d_points"] = 0
        row.pop("detail", None)
        rows.append(row)
        previous = shot

    moved = []
    for attr in D.attrs_for(me.position):
        start = first["detail"].get(attr, 10)
        delta = me.detail.get(attr, 10) - start
        if delta:
            moved.append({"attr": attr, "name": D.DETAIL_NAMES_HE[attr],
                          "from": start, "to": me.detail.get(attr, 10),
                          "delta": delta})
    moved.sort(key=lambda row: -row["delta"])

    return {
        "seasons": rows,
        "since": first["year"],
        "since_age": first["age"],
        "moved": moved,
        "total_points": sum(row["delta"] for row in moved if row["delta"] > 0),
        "overall_from": first["overall"], "overall_to": me.overall,
        "physical": {
            "height_from": first["height"], "height_to": me.height,
            "weight_from": first["weight"], "weight_to": me.weight,
            "adult_height": me.adult_height,
            "left": max(0, me.adult_height - me.height),
        },
    }


def growth_lines(game) -> List[str]:
    """סיכום ההתפתחות בשורות, לטרמינל."""
    info = growth_summary(game)
    if not info["seasons"]:
        return ["עוד לא נרשמה עונה שלמה — התמונה תיבנה בסוף העונה."]
    phys = info["physical"]
    out = [f"מאז {info['since']} (גיל {info['since_age']}): "
           f"כללי {info['overall_from']} → {info['overall_to']}, "
           f"{info['total_points']} נקודות תכונה.",
           f"גוף: {phys['height_from']} → {phys['height_to']} ס\"מ, "
           f"{phys['weight_from']} → {phys['weight_to']} ק\"ג"
           + (f" (נותרו {phys['left']} ס\"מ לגדול)" if phys["left"] else " — סיימת לגדול"),
           ""]
    for row in info["moved"][:10]:
        arrow = "▲" if row["delta"] > 0 else "▼"
        out.append(f"  {arrow} {row['name']:<16} {row['from']:>2} → {row['to']:<2} "
                   f"({row['delta']:+d})")
    return out


# ---------------------------------------------------------------------------
# מה יש בקבוצה שלי
# ---------------------------------------------------------------------------

def squad_report(game) -> Dict[str, Any]:
    """פרטי הקבוצה שהיו חסרים: עומק לפי עמדה, מי לפניך, ואיפה אתה עומד."""
    club = game.my_club
    me = game.me
    if not club:
        return {"has_club": False}

    squad = [game.players[pid] for pid in club.squad if pid in game.players]
    by_position: Dict[str, List[Dict[str, Any]]] = {}
    for player in squad:
        row = by_position.setdefault(player.position, [])
        row.append({
            "pid": player.pid, "name": player.name, "age": player.age,
            "overall": player.overall, "role": player.role,
            "number": player.number, "available": player.available,
            "is_me": player.pid == me.pid,
        })
    for rows in by_position.values():
        rows.sort(key=lambda row: -row["overall"])

    rivals = [row for row in by_position.get(me.position, []) if not row["is_me"]]
    ahead = [row for row in rivals if row["overall"] > me.overall]

    ages = [p.age for p in squad] or [25]
    league_clubs = [c for c in game.clubs.values() if c.league_id == club.league_id]
    ranked = sorted(league_clubs, key=lambda c: -c.reputation)
    rank = next((i + 1 for i, c in enumerate(ranked) if c.cid == club.cid), 0)

    return {
        "has_club": True,
        "name": club.name, "nickname": club.nickname,
        "reputation": club.reputation, "rep_rank": rank, "rep_of": len(ranked),
        "manager": club.manager_name,
        "squad_size": len(squad),
        "average_age": round(sum(ages) / len(ages), 1),
        "average_overall": round(sum(p.overall for p in squad) / max(1, len(squad))),
        "by_position": by_position,
        "ahead_of_me": ahead,
        "depth_here": len(by_position.get(me.position, [])),
        "facilities": [
            {"key": key, "name": info["name"],
             "value": int(club.facility(key)),
             "desc": info.get("desc", "")}
            for key, info in D.FACILITIES.items()
        ],
        "staff": [
            {"role": key, "name": info["name"],
             "member": club.staff.get(key), "quality": club.staff_quality(key)}
            for key, info in D.STAFF_ROLES.items()
        ],
    }
