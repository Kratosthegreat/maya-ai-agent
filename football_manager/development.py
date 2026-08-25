# -*- coding: utf-8 -*-
"""
football_manager.development
============================
מסלול הפיתוח — איך הופכים ילד ליהלום.

התלונה הייתה מדויקת: אפשר היה להתאמן שנים בלי לדעת לאן. כאן בוחרים
דגם שחקן (ארכיטיפ), והמסלול אומר בדיוק מה צריך להיות לך ומתי —
"בעיטה 72 עד גיל 19" — ומה תקבל אם תגיע לשם בזמן.

עמידה באבן דרך בזמן היא לא נקודה בטבלה: היא דוחפת את הערכת
הפוטנציאל למעלה, מרימה מוניטין, ומי שמשלים את כל המסלול עובר
פריצה אמיתית — הרגע שבו העולם מפסיק לקרוא לך "כישרון".
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from . import data as D
from .models import Player, clamp, gain_reputation

ARCHETYPE_BY_KEY = {row[0]: row for row in D.ARCHETYPES}


def options_for(position: str) -> List[tuple]:
    """המסלולים שפתוחים לעמדה. תמיד יש לפחות אחד."""
    fits = [row for row in D.ARCHETYPES if position in row[2]]
    return fits or list(D.ARCHETYPES)


def plan_key(game) -> Optional[str]:
    return game.flags.get("plan")


def plan_row(game) -> Optional[tuple]:
    key = plan_key(game)
    return ARCHETYPE_BY_KEY.get(key) if key else None


def set_plan(game, key: str) -> str:
    """בוחר מסלול. החלפה באמצע הדרך מאפסת את מה שכבר נצבר."""
    row = ARCHETYPE_BY_KEY.get(key)
    if not row:
        return "אין מסלול כזה."
    previous = plan_key(game)
    game.flags["plan"] = key
    if previous and previous != key:
        game.flags["plan_done"] = []
        return (f"עברת למסלול \"{row[1]}\". מה שהספקת במסלול הקודם "
                "לא נספר לך כאן — מתחילים מהתחלה.")
    game.flags.setdefault("plan_done", [])
    return f"המסלול שלך: {row[1]}. {row[6]}"


def done_list(game) -> List[int]:
    done = game.flags.get("plan_done")
    if not isinstance(done, list):
        done = []
        game.flags["plan_done"] = done
    return done


# ---------------------------------------------------------------------------
# איפה אתה עומד
# ---------------------------------------------------------------------------

def milestone_rows(game) -> List[Dict[str, Any]]:
    """כל אבני הדרך במסלול, עם המצב הנוכחי מול הדרישה."""
    row = plan_row(game)
    if not row:
        return []
    me = game.me
    done = done_list(game)
    out = []
    for index, (age, needs) in enumerate(row[4]):
        parts = []
        met = True
        for attr, target in sorted(needs.items()):
            have = me.attributes.get(attr, 50)
            if have < target:
                met = False
            parts.append({"attr": attr, "name": D.ATTRIBUTE_NAMES_HE[attr],
                          "have": have, "need": target})
        out.append({
            "index": index, "age": age, "needs": parts,
            "met": met, "claimed": index in done,
            "late": me.age > age and not met,
        })
    return out


def next_target(game) -> Optional[str]:
    """המשפט שאומר לך מה לעשות עכשיו. זו ההכוונה שהייתה חסרה."""
    rows = milestone_rows(game)
    row = plan_row(game)
    if not row or not rows:
        return None
    me = game.me
    for entry in rows:
        if entry["claimed"]:
            continue
        gaps = [p for p in entry["needs"] if p["have"] < p["need"]]
        if not gaps:
            return f"🎯 עמדת בדרישות של גיל {entry['age']} — זה ייחתם בסוף העונה."
        worst = min(gaps, key=lambda p: p["have"] - p["need"])
        left = worst["need"] - worst["have"]
        when = (f"עד גיל {entry['age']}" if me.age <= entry["age"]
                else f"(היעד של גיל {entry['age']} כבר מאחוריך)")
        return (f"🎯 {row[1]}: {worst['name']} {worst['have']} → {worst['need']} "
                f"{when}. חסרות {left} נקודות.")
    return f"🎯 השלמת את כל מסלול \"{row[1]}\"."


def recommended_focus(game) -> Optional[str]:
    """על מה כדאי להתאמן השבוע כדי להתקדם במסלול."""
    rows = milestone_rows(game)
    for entry in rows:
        if entry["claimed"]:
            continue
        gaps = [p for p in entry["needs"] if p["have"] < p["need"]]
        if gaps:
            return min(gaps, key=lambda p: p["have"] - p["need"])["attr"]
    row = plan_row(game)
    return row[3][0][0] if row else None


# ---------------------------------------------------------------------------
# חתימה על אבני דרך
# ---------------------------------------------------------------------------

def claim_milestones(game) -> List[str]:
    """נקרא בסוף עונה: חותם על מה שהושג ומחלק את הפרסים."""
    row = plan_row(game)
    if not row:
        return []
    me = game.me
    done = done_list(game)
    lines: List[str] = []
    reward = D.MILESTONE_REWARD

    for entry in milestone_rows(game):
        if entry["claimed"] or not entry["met"]:
            continue
        on_time = me.age <= entry["age"]
        done.append(entry["index"])
        scale = 1.0 if on_time else 0.45
        me.potential = clamp(me.potential + reward["potential"] * scale,
                             0, me.ceiling)
        gain_reputation(me, reward["rep"] * scale)
        me.morale = clamp(me.morale + reward["morale"] * scale, 5, 99)
        club = game.my_club
        if club:
            club.manager_trust = clamp(club.manager_trust + reward["trust"] * scale,
                                       0, 100)
        stamp = "בזמן" if on_time else "באיחור"
        lines.append(f"✅ אבן דרך במסלול \"{row[1]}\" (גיל {entry['age']}) — {stamp}.")

    # פריצה: כל המסלול הושלם
    if len(done) >= len(row[4]) and not game.flag("breakthrough"):
        lines.extend(_breakthrough(game, row))
    return lines


def _breakthrough(game, row: tuple) -> List[str]:
    """הרגע שבו מפסיקים לקרוא לך כישרון."""
    me = game.me
    game.set_flag("breakthrough", True)
    me.potential = clamp(me.potential + 6.0, 0, me.ceiling)
    gain_reputation(me, 7.0)
    me.morale = clamp(me.morale + 14, 5, 99)
    trait = row[5]
    lines = [f"💎 פריצה. השלמת את מסלול \"{row[1]}\" במלואו.",
             f"   {row[6]}"]
    if trait and not me.has_trait(trait):
        me.traits.append(trait)
        lines.append(f"   נוספה לך תכונת אופי: {D.TRAITS[trait]['name']}.")
    lines.append("   מהיום מסתכלים עליך אחרת — בתוך המועדון וגם מחוצה לו.")
    club = game.my_club
    if club:
        club.manager_trust = clamp(club.manager_trust + 12, 0, 100)
        club.fan_support = clamp(club.fan_support + 6, 0, 100)
    return lines


def plan_summary(game) -> Dict[str, Any]:
    """תמונת מצב למסך המסלול."""
    row = plan_row(game)
    if not row:
        return {"chosen": False, "options": [
            {"key": r[0], "name": r[1], "desc": r[6],
             "attrs": [D.ATTRIBUTE_NAMES_HE[a] for a, _ in r[3]]}
            for r in options_for(game.me.position)]}
    rows = milestone_rows(game)
    return {
        "chosen": True, "key": row[0], "name": row[1], "desc": row[6],
        "trait": D.TRAITS[row[5]]["name"],
        "milestones": rows,
        "done": sum(1 for r in rows if r["claimed"]),
        "total": len(rows),
        "next": next_target(game),
        "focus": recommended_focus(game),
        "breakthrough": bool(game.flag("breakthrough")),
    }
