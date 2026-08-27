"""
מנוע אירועים מונחה-נתונים.

אירוע עלילה הוא ברובו טבלה: מתי הוא רלוונטי, מה כתוב, ומה כל בחירה
עושה. כתיבת מאות אירועים כקוד — פעמיים, גם בפייתון וגם ב-JS — היא
דרך בטוחה לסטייה בין המנועים. לכן האירועים נכתבים פעם אחת כנתונים
(story_pack.py), ושני המנועים מריצים את אותו מפרש.

מפרט שורה:

    {
      "eid": "מזהה ייחודי",
      "title": "כותרת",
      "stages": ["player", "veteran"],
      "weight": 1.4, "cooldown": 30, "once": False,
      "when": {"age_min": 18, "rep_min": 20, "needs_club": True},
      "body": "טקסט עם {club} ו-{manager}",
      "choices": [
        {"label": "...", "hint": "...", "text": "מה קרה",
         "fx": {"morale": 5, "trust": -3, "attr": ["mental", 0.8]}}
      ],
    }
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from . import data as D
from .models import add_detail, add_group, clamp, gain_reputation


# ---------------------------------------------------------------------------
# מילוי מקומות בטקסט
# ---------------------------------------------------------------------------

def _squad_mate(game, predicate=None):
    """שחקן אחר מהסגל שלי, לפי תנאי אופציונלי."""
    club = game.my_club
    if not club:
        return None
    pool = [game.players[p] for p in club.squad
            if p in game.players and p != game.me_id]
    if predicate:
        pool = [p for p in pool if predicate(p)]
    return game.rng.choice(pool) if pool else None


def tokens(game) -> Dict[str, str]:
    """כל מה שאפשר לשתול בטקסט של אירוע."""
    me = game.me
    club = game.my_club
    mate = _squad_mate(game)
    rival = _squad_mate(game, lambda p: p.position == me.position)
    fixture = game.my_fixture()
    opponent = None
    if fixture and club:
        other = fixture[1] if fixture[0] == club.cid else fixture[0]
        opponent = game.clubs.get(other)
    league = next((l for l in D.LEAGUES
                   if club and l["id"] == club.league_id), None)
    return {
        "me": me.name,
        "age": str(me.age),
        "position": me.position_he,
        "club": club.name if club else "המועדון",
        "nickname": club.nickname if club else "",
        "manager": club.manager_name if club else "המאמן",
        "stadium": club.stadium_name if club else "האצטדיון",
        "mate": mate.name if mate else "אחד השחקנים",
        "rival": rival.name if rival else (mate.name if mate else "המתחרה שלך"),
        "opponent": opponent.name if opponent else "היריבה",
        "league": league["name"] if league else "הליגה",
        "wage": f"{int(me.contract.wage):,}",
        "money": f"{int(game.money):,}",
        "number": str(me.number or 0),
    }


def fill(text: str, game) -> str:
    """מחליף {placeholders} בערכים אמיתיים. חסר → נשאר כפי שהוא."""
    if "{" not in text:
        return text
    values = tokens(game)
    out = text
    for key, value in values.items():
        out = out.replace("{" + key + "}", value)
    return out


# ---------------------------------------------------------------------------
# תנאים
# ---------------------------------------------------------------------------

def _position(game) -> int:
    try:
        return game.league_position()
    except Exception:
        return 10


CONDITIONS = {
    "age_min": lambda g, v: g.me.age >= v,
    "age_max": lambda g, v: g.me.age <= v,
    "rep_min": lambda g, v: g.me.reputation >= v,
    "rep_max": lambda g, v: g.me.reputation <= v,
    "overall_min": lambda g, v: g.me.overall >= v,
    "overall_max": lambda g, v: g.me.overall <= v,
    "morale_max": lambda g, v: g.me.morale <= v,
    "morale_min": lambda g, v: g.me.morale >= v,
    "form_max": lambda g, v: g.me.form <= v,
    "form_min": lambda g, v: g.me.form >= v,
    "fitness_max": lambda g, v: g.me.fitness <= v,
    "trust_max": lambda g, v: (g.my_club.manager_trust if g.my_club else 50) <= v,
    "trust_min": lambda g, v: (g.my_club.manager_trust if g.my_club else 50) >= v,
    "needs_club": lambda g, v: (g.my_club is not None) == bool(v),
    "injured": lambda g, v: (g.me.injury_weeks > 0) == bool(v),
    "week_min": lambda g, v: g.week >= v,
    "week_max": lambda g, v: g.week <= v,
    "contract_max": lambda g, v: g.me.contract.years_left <= v,
    "apps_min": lambda g, v: g.me.season.apps >= v,
    "apps_max": lambda g, v: g.me.season.apps <= v,
    "career_goals_min": lambda g, v: g.me.career.goals >= v,
    "position_in": lambda g, v: g.me.position in v,
    "table_top": lambda g, v: _position(g) <= v,
    "table_bottom": lambda g, v: _position(g) >= v,
    "flag": lambda g, v: bool(g.flag(v)),
    "not_flag": lambda g, v: not g.flag(v),
    "has_mate": lambda g, v: (_squad_mate(g) is not None) == bool(v),
}


def matches(game, when: Optional[Dict[str, Any]]) -> bool:
    if not when:
        return True
    for key, value in when.items():
        check = CONDITIONS.get(key)
        if check is None:
            continue
        try:
            if not check(game, value):
                return False
        except Exception:
            return False
    return True


# ---------------------------------------------------------------------------
# אפקטים
# ---------------------------------------------------------------------------

# כל מה ש-apply_effects יודע לעשות. בדיקות מוודאות שאין בספרייה
# מפתח שלא ברשימה הזאת — טעות הקלדה באפקט נבלעת אחרת בשקט.
EFFECT_KEYS = {
    "morale", "trust", "fans", "board", "rep", "money", "form", "fitness",
    "resilience", "sharpness", "coaching", "media", "business", "potential",
    "attr", "attrs", "injury", "flag", "clear_flag", "trait", "drop_trait",
    "honour",
    # מה שהפגישות (encounter_pack) צריכות: העולם מגיב, לא רק השחקן
    "interest", "open_offer", "hype", "press", "agent_market", "agent_cut",
    "agent_trust", "meet_partner", "pride", "mood", "promise",
}


# ---------------------------------------------------------------------------
# העולם מגיב
#
# אירוע שמשנה רק את השחקן הוא בסוף עוד שורת מספרים. מה שהופך פגישה
# לאירוע הוא שהיא **מזיזה משהו בחוץ**: מועדון מתחיל להסתכל, הצעה
# נוחתת על השולחן, עיתון כותב. הפונקציות כאן הן הידיות האלה.
# ---------------------------------------------------------------------------

# כמה מוניטין צריך מועדון כדי להיחשב "עילית"
ELITE_REPUTATION = 84


def _club_pool(game, tier: str):
    """מועדונים לפי דרגה, בלי זה שאתה כבר בו."""
    mine = game.me.club_id
    clubs = [c for c in game.clubs.values() if c.cid != mine]
    if tier == "elite":
        pool = [c for c in clubs if c.reputation >= ELITE_REPUTATION]
    elif tier == "foreign":
        pool = [c for c in clubs if D.is_foreign(c.cid)]
    elif tier == "rich":
        pool = sorted(clubs, key=lambda c: -c.wage_budget)[:6]
    else:
        pool = clubs
    return pool or clubs


def _add_interest(game, tier: str, amount: float) -> None:
    pool = _club_pool(game, tier)
    if not pool:
        return
    club = game.rng.choice(pool)
    book = game.flags.setdefault("scout_interest", {})
    book[club.cid] = clamp(float(book.get(club.cid, 0.0)) + amount, 0, 100)


def _open_offer(game, tier: str) -> None:
    """הצעה על השולחן עכשיו — גם באמצע העונה.

    זה הרגע שהמשתמש ביקש: מועדון שרוצה אותך לא מחכה לקיץ, הוא מרים
    טלפון היום. ההצעה נכנסת לאותה רשימה שהחלון מייצר, ולכן אפשר
    לנהל עליה משא ומתן בדיוק כמו על כל אחת אחרת.
    """
    from . import transfers as TR          # מיובא כאן כדי לא לסגור מעגל
    pool = [c for c in _club_pool(game, tier)
            if not TR.offer_for(game, c.cid)]
    if not pool:
        return
    club = max(pool, key=lambda c: c.reputation)
    offers = TR.open_offers(game)
    offers.append(TR.build_offer(game, club, game.rng,
                                 eagerness=game.rng.uniform(0.72, 0.98)))
    TR.set_offers(game, offers)


def _push_press(game, text: str) -> None:
    from . import press as PR          # מיובא כאן כדי לא לסגור מעגל
    PR.push(game, {"key": "encounter", "source": "insider",
                   "true": True, "text": text})


def apply_attr(me, attr: str, delta: float) -> None:
    """שינוי תכונה, בשפת הקבוצות או בשפת התכונות המפורטות.

    אירועי העלילה נכתבו בשפת שבע הקבוצות ("shooting"), והם ממשיכים
    לעבוד: הכתיבה מתפזרת על התכונות שמרכיבות את הקבוצה. אירוע שכתוב
    בשפה המפורטת ("finishing") פוגע ישירות.
    """
    if attr in D.DETAIL_NAMES_HE:
        add_detail(me, attr, delta / 5.0)
    else:
        add_group(me, attr, delta)


def apply_effects(game, fx: Optional[Dict[str, Any]]) -> None:
    """מפעיל את כל האפקטים של בחירה. מפתח לא מוכר — מדולג בשקט."""
    if not fx:
        return
    me = game.me
    club = game.my_club
    for key, value in fx.items():
        if key == "morale":
            me.morale = clamp(me.morale + value, 5, 99)
        elif key == "trust" and club:
            club.manager_trust = clamp(club.manager_trust + value, 0, 100)
        elif key == "fans" and club:
            club.fan_support = clamp(club.fan_support + value, 0, 100)
        elif key == "board" and club:
            club.board_confidence = clamp(club.board_confidence + value, 0, 100)
        elif key == "rep":
            gain_reputation(me, value)
        elif key == "money":
            game.earn_money(value) if value >= 0 else game.spend_money(-value)
        elif key == "form":
            me.form = clamp(me.form + value, 5, 99)
        elif key == "fitness":
            me.fitness = clamp(me.fitness + value, 0, 100)
        elif key == "resilience":
            me.resilience = clamp(me.resilience + value, 0, 96)
        elif key == "sharpness":
            me.sharpness = clamp(me.sharpness + value, 0, 100)
        elif key == "coaching":
            me.coaching = clamp(me.coaching + value, 0, 100)
        elif key == "media":
            me.media_skill = clamp(me.media_skill + value, 0, 100)
        elif key == "business":
            me.business = clamp(me.business + value, 0, 100)
        elif key == "potential":
            me.potential = int(clamp(me.potential + value, me.overall, me.ceiling))
        elif key == "attr":
            attr, delta = value
            apply_attr(me, attr, delta)
        elif key == "attrs":
            for attr, delta in value:
                apply_effects(game, {"attr": [attr, delta]})
        elif key == "injury":
            weeks, name = value
            me.injury_weeks = max(me.injury_weeks, int(weeks))
            me.injury_name = name
        elif key == "flag":
            game.set_flag(value, True)
        elif key == "clear_flag":
            game.set_flag(value, False)
        elif key == "trait":
            if value not in me.traits:
                me.traits.append(value)
        elif key == "drop_trait":
            me.traits = [t for t in me.traits if t != value]
        elif key == "honour":
            game.record_honour(fill(value, game))
        elif key == "interest":
            tier, amount = value
            _add_interest(game, tier, amount)
        elif key == "open_offer":
            _open_offer(game, value[0] if isinstance(value, (list, tuple)) else value)
        elif key == "hype":
            game.flags["hype"] = clamp(float(game.flags.get("hype", 0)) + value, 0, 100)
        elif key == "press":
            _push_press(game, fill(value, game))
        elif key == "agent_market":
            from . import agents as AG
            game.flags["agent_offers"] = AG.market(game, game.rng)
        elif key == "agent_cut":
            row = game.flags.get("agent")
            if isinstance(row, dict):
                row["cut"] = round(float(row.get("cut", 5)) + value, 1)
        elif key == "agent_trust":
            row = game.flags.get("agent")
            if isinstance(row, dict):
                row["trust"] = clamp(float(row.get("trust", 60)) + value, 0, 100)
        elif key == "meet_partner":
            from . import life as LF
            kind = value[0] if isinstance(value, (list, tuple)) else value
            if kind in ("any", "", None):
                kind = game.rng.choice([k for k, *_ in LF.PARTNER_KINDS])
            game.flags["partner"] = LF.make_partner(kind, game.rng)
        elif key == "pride":
            from . import life as LF
            par = LF.parents(game)
            par["pride"] = clamp(par["pride"] + value, 0, 100)
        elif key == "mood":
            from . import life as LF
            row = LF.partner(game)
            if row:
                row["mood"] = clamp(row["mood"] + value, 0, 100)
        elif key == "promise":
            from . import manager as MG
            MG.give_promise(game, value[0] if isinstance(value, (list, tuple)) else value)


def choice_result(game, choice: Dict[str, Any]) -> str:
    apply_effects(game, choice.get("fx"))
    return fill(choice.get("text", ""), game)
