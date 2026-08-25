# -*- coding: utf-8 -*-
"""
football_manager.matchstats
===========================
שורת הסטטיסטיקה האישית שלך אחרי משחק.

זה החוט שהיה חסר. עד עכשיו התאמנת על בעיטות, המספר בתפריט עלה,
ובמשחק לא ראית כלום — כי הדירוג נגזר מדירוג כללי אחד שהרעש בלע אותו.
כאן כל תכונה מייצרת מספר שאתה רואה: בעיטות למסגרת, אחוז מסירה,
דו־קרבים, חטיפות, ספרינטים, איבודי כדור.

המאמן קורא בדיוק את המספרים האלה כשהוא מחליט מה לדרוש ממך בשבוע הבא,
והשבוע שתעשה בעקבות זה יזוז את אותם מספרים במשחק הבא. זה המעגל.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from . import data as D
from .models import Player, clamp


def _rate(value: float, low: float, high: float) -> float:
    """ממפה תכונה 0-100 לטווח שימושי."""
    return low + (high - low) * clamp(value, 0.0, 100.0) / 100.0


def match_stat_line(player: Player, minutes: int, goals: int, assists: int,
                    rng: random.Random, possession: float = 0.5,
                    fitness_at_kickoff: Optional[float] = None) -> Dict[str, Any]:
    """מייצר שורת סטטיסטיקה למשחק אחד, נגזרת מהתכונות בפועל.

    ``possession`` הוא נתח השליטה של הקבוצה שלך — שחקן בקבוצה ששולטת
    בכדור נוגע בו יותר, ולכן גם מייצר יותר מהכול, טוב כרע.

    לצד המספרים נשמרות גם התוחלות שמהן הם הוגרלו (``exp``). זה מה
    שמאפשר אחר כך לומר לא רק "כמה", אלא "האם זה היה ערב טוב שלך" —
    אותה שורה בדיוק נקראת אחרת אצל בן 16 ואצל כוכב.
    """
    attrs = player.attributes
    share = D.POSITION_ROLE_SHARE[player.position]
    load = (minutes / 90.0) * (0.72 + possession * 0.56)
    fit = fitness_at_kickoff if fitness_at_kickoff is not None else player.fitness
    stamina = 0.80 + 0.20 * clamp(fit, 0, 100) / 100.0
    sharp = 0.86 + 0.28 * clamp(player.sharpness, 0, 100) / 100.0

    shooting = attrs.get("shooting", 50)
    passing = attrs.get("passing", 50)
    dribbling = attrs.get("dribbling", 50)
    defending = attrs.get("defending", 50)
    physical = attrs.get("physical", 50)
    pace = attrs.get("pace", 50)
    mental = attrs.get("mental", 50)

    exp: Dict[str, float] = {}

    # בעיטות — כמה אתה בכלל מגיע למצב, וכמה מזה נוגע במסגרת
    shot_rate = (share["att"] * 3.4 + share["mid"] * 1.0 + share["def"] * 0.25)
    shot_rate *= _rate(shooting, 0.45, 1.5) * _rate(mental, 0.7, 1.25)
    exp["shots"] = shot_rate * load * sharp
    shots = _draw(rng, exp["shots"])
    accuracy = _rate(shooting, 0.22, 0.66) * sharp
    exp["on_target"] = exp["shots"] * accuracy
    on_target = sum(1 for _ in range(shots) if rng.random() < accuracy)
    on_target = max(on_target, min(shots, goals))

    # מסירות — הנפח נקבע בעמדה, האחוז נקבע בתכונה
    pass_volume = (share["mid"] * 62 + share["def"] * 46 + share["att"] * 26)
    exp["passes"] = pass_volume * load * (0.75 + passing / 260.0)
    passes = max(3, _draw(rng, exp["passes"]))
    exp["pass_pct"] = clamp(58 + passing * 0.30 - (1 - stamina) * 22, 35, 96)
    pass_pct = clamp(exp["pass_pct"] + rng.gauss(0, 3.4), 35, 96)
    completed = int(round(passes * pass_pct / 100.0))
    key_rate = (share["att"] * 1.5 + share["mid"] * 1.3 + share["def"] * 0.3)
    exp["key_passes"] = key_rate * _rate(passing, 0.25, 1.35) * load
    key_passes = _draw(rng, exp["key_passes"])
    key_passes = max(key_passes, assists)

    # כדרור
    exp["dribble_tries"] = ((share["att"] * 2.6 + share["mid"] * 1.4 +
                             share["def"] * 0.5) * _rate(dribbling, 0.4, 1.5) * load)
    dribble_tries = _draw(rng, exp["dribble_tries"])
    exp["dribble_pct"] = clamp(24 + dribbling * 0.44, 8, 92)
    dribble_pct = clamp(exp["dribble_pct"] + rng.gauss(0, 5), 8, 92)
    exp["dribbles"] = exp["dribble_tries"] * exp["dribble_pct"] / 100.0
    dribbles = sum(1 for _ in range(dribble_tries) if rng.random() * 100 < dribble_pct)

    # דו־קרבים וחטיפות
    exp["duels"] = (5.5 + share["def"] * 5.0 + share["mid"] * 2.5) * load
    duels = max(2, _draw(rng, exp["duels"]))
    exp["duels_pct"] = clamp(28 + physical * 0.34 + mental * 0.10
                             - (1 - stamina) * 26, 10, 92)
    duels_pct = clamp(exp["duels_pct"] + rng.gauss(0, 4.5), 10, 92)
    duels_won = int(round(duels * duels_pct / 100.0))
    tackle_rate = (share["def"] * 4.6 + share["mid"] * 2.4 + share["att"] * 0.6)
    exp["tackles"] = tackle_rate * _rate(defending, 0.35, 1.4) * load
    tackles = _draw(rng, exp["tackles"])

    # איבודי כדור — הדבר היחיד שבו נמוך זה טוב
    exp["losses"] = (exp["passes"] * (1 - exp["pass_pct"] / 100.0) * 0.55 +
                     (exp["dribble_tries"] - exp["dribbles"]) * 0.7)
    loss_base = (passes * (1 - pass_pct / 100.0) * 0.55 +
                 (dribble_tries - dribbles) * 0.7)
    losses = max(0, int(round(loss_base + rng.gauss(0, 1.1))))

    # ריצה
    exp["sprints"] = ((11 + share["att"] * 9 + share["mid"] * 7) *
                      _rate(pace, 0.45, 1.4) * load * stamina)
    sprints = _draw(rng, exp["sprints"])
    distance = round(clamp((7.4 + share["mid"] * 3.4 + share["def"] * 1.2 +
                            physical * 0.022) * (minutes / 90.0) * stamina
                           + rng.gauss(0, 0.35), 2.0, 14.5), 1)

    # קריאת משחק — כמה פעמים היית במקום הנכון
    exp["reads"] = ((4.0 + share["def"] * 2.4 + share["mid"] * 2.0) *
                    _rate(mental, 0.4, 1.55) * load)
    reads = _draw(rng, exp["reads"])

    return {
        "minutes": minutes, "goals": goals, "assists": assists,
        "shots": shots, "on_target": on_target,
        "passes": passes, "completed": completed, "pass_pct": int(round(pass_pct)),
        "key_passes": key_passes,
        "dribble_tries": dribble_tries, "dribbles": dribbles,
        "duels": duels, "duels_won": duels_won, "duels_pct": int(round(duels_pct)),
        "tackles": tackles, "losses": losses,
        "sprints": sprints, "distance": distance, "reads": reads,
        "fitness": int(round(fit)),
        "exp": {k: round(v, 3) for k, v in exp.items()},
    }


def _draw(rng: random.Random, mean: float) -> int:
    """הגרלה שלמה סביב ממוצע — עם שארית הסתברותית, כדי ש-0.4 יהיה 0.4."""
    if mean <= 0:
        return 0
    whole = int(mean)
    if rng.random() < mean - whole:
        whole += 1
    spread = max(1, int(whole * 0.45))
    return max(0, whole + rng.randint(-spread, spread))


# ---------------------------------------------------------------------------
# מה זה אומר
# ---------------------------------------------------------------------------

def stat_summary(stats: Dict[str, Any], position: str) -> List[str]:
    """שלוש-ארבע שורות שמסבירות איך שיחקת, בשפה של מגרש."""
    share = D.POSITION_ROLE_SHARE[position]
    lines: List[str] = []
    if stats["shots"]:
        lines.append(f"⚽ {stats['shots']} בעיטות, {stats['on_target']} למסגרת"
                     + (f", {stats['goals']} נכנסו" if stats["goals"] else ""))
    lines.append(f"🎯 {stats['completed']}/{stats['passes']} מסירות "
                 f"({stats['pass_pct']}%)"
                 + (f" · {stats['key_passes']} מסירות מפתח" if stats["key_passes"] else ""))
    if share["def"] >= 0.2 or stats["tackles"]:
        lines.append(f"🛡️ {stats['tackles']} חטיפות · "
                     f"{stats['duels_won']}/{stats['duels']} דו־קרבים "
                     f"({stats['duels_pct']}%)")
    else:
        lines.append(f"💪 {stats['duels_won']}/{stats['duels']} דו־קרבים "
                     f"({stats['duels_pct']}%)")
    if stats["dribble_tries"]:
        lines.append(f"🌀 {stats['dribbles']}/{stats['dribble_tries']} כדרורים")
    lines.append(f"🏃 {stats['distance']} ק\"מ · {stats['sprints']} ספרינטים · "
                 f"{stats['losses']} איבודי כדור")
    return lines


# ---------------------------------------------------------------------------
# איך קוראים את השורה הזאת
# ---------------------------------------------------------------------------

def area_scores(stats: Dict[str, Any], position: str) -> Dict[str, float]:
    """כמה טוב היית בכל תחום, ביחס למה שהתכונות שלך מבטיחות.

    70 פירושו "בדיוק כמו שאתה" — ערב ממוצע. מעל זה ערב טוב, מתחת
    ערב רע. זו הסיבה שהסולם אחיד: אותה שורה בדיוק נקראת אחרת אצל
    בן 16 בליגה הלאומית ואצל חלוץ ליגת האלופות.
    """
    exp = stats.get("exp") or {}
    share = D.POSITION_ROLE_SHARE[position]
    scores: Dict[str, float] = {}

    def ratio(actual: float, expected: float, floor: float) -> Optional[float]:
        if expected < floor:
            return None
        return clamp(70.0 * (actual / expected), 0.0, 100.0)

    shot_value = stats["on_target"] + stats["goals"] * 1.4
    shot_exp = exp.get("on_target", 0.0) * 1.25
    got = ratio(shot_value, shot_exp, 0.35)
    if got is not None:
        scores["shooting"] = got

    pass_parts = []
    if exp.get("pass_pct"):
        pass_parts.append(clamp(70.0 * stats["pass_pct"] / exp["pass_pct"], 0, 100))
    if exp.get("key_passes", 0) >= 0.25:
        pass_parts.append(clamp(70.0 * (stats["key_passes"] + stats["assists"] * 1.2)
                                / (exp["key_passes"] * 1.2), 0, 100))
    if exp.get("losses", 0) >= 1.0:
        pass_parts.append(clamp(140.0 - 70.0 * stats["losses"] / exp["losses"], 0, 100))
    if pass_parts:
        scores["passing"] = sum(pass_parts) / len(pass_parts)

    got = ratio(stats["dribbles"], exp.get("dribbles", 0.0), 0.30)
    if got is not None:
        scores["dribbling"] = got

    got = ratio(stats["tackles"], exp.get("tackles", 0.0), 0.35)
    if got is not None:
        scores["defending"] = got

    if exp.get("duels_pct"):
        scores["physical"] = clamp(70.0 * stats["duels_pct"] / exp["duels_pct"], 0, 100)

    got = ratio(stats["sprints"], exp.get("sprints", 0.0), 1.0)
    if got is not None:
        scores["pace"] = got

    got = ratio(stats["reads"], exp.get("reads", 0.0), 0.5)
    if got is not None:
        scores["mental"] = got

    if not scores:      # שמורה ישנה בלי תוחלות — אין על מה לדבר
        scores["physical"] = 70.0
    return scores


def performance(stats: Dict[str, Any], position: str) -> float:
    """ציון כולל למשחק, 0-100, כשהעמדה קובעת על מה מסתכלים. 70 = ערב ממוצע."""
    scores = area_scores(stats, position)
    weights = D.POSITION_WEIGHTS[position]
    total = sum(weights.get(area, 0.0) for area in scores)
    if total <= 0:
        return 70.0
    return sum(scores[a] * weights.get(a, 0.0) for a in scores) / total


def weakest_area(stats: Dict[str, Any], position: str,
                 attributes: Optional[Dict[str, int]] = None) -> str:
    """מה המאמן יבקש ממך לעבוד עליו.

    שני דברים נשקלים: הפער הקבוע בין התכונה שלך לבין מה שהעמדה
    דורשת, ומה שקרה במשחק האחרון בפועל. בלי הראשון הוא היה דורש
    מחלוץ בור לחטוף כדורים; בלי השני הוא היה חוזר על עצמו לנצח.
    תחום שהעמדה כמעט לא נוגעת בו פשוט לא עולה לדיון.
    """
    scores = area_scores(stats, position)
    weights = D.POSITION_WEIGHTS[position]
    top = max(weights.values()) or 1.0
    attrs = attributes or {}
    ranked = []
    for area, weight in weights.items():
        relevance = weight / top
        if relevance < 0.18:
            continue
        need = 45.0 + relevance * 48.0
        gap = attrs.get(area, 60) - need if attrs else 0.0
        match_gap = (scores.get(area, 70.0) - 70.0) * 0.30
        ranked.append((gap + match_gap, area))
    if not ranked:
        return "physical"
    return min(ranked)[1]


def reason_line(area: str, stats: Dict[str, Any]) -> str:
    """המשפט שהמאמן אומר — עם המספרים האמיתיים של המשחק שלך."""
    pair = D.DIRECTIVE_REASON.get(area)
    if not pair:
        return ""
    try:
        return pair[0].format(**stats)
    except (KeyError, IndexError):
        return ""


def promise_line(area: str) -> str:
    """מה המאמן מבטיח שיקרה אם תעבוד על זה."""
    pair = D.DIRECTIVE_REASON.get(area)
    return pair[1] if pair else ""
