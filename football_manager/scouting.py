# -*- coding: utf-8 -*-
"""
football_manager.scouting
=========================
מי צופה בך, ומאיפה.

עד עכשיו הצעת העברה הייתה הטלת מטבע אחת בשנה: או שקבוצה מופיעה, או
שלא, ובלי שום דבר לפני. כאן זה תהליך: קבוצות שולחות צופים למשחקים
מסוימים, הצופה כותב דוח לפי מה שראה, והעניין נבנה או נשחק לאורך
העונה. אתה רואה את זה קורה — מי היה ביציע, מה הוא כתב, ואיפה אתה
עומד ברשימה שלו.

וזה לא נשאר מקומי: ככל שהמוניטין עולה, נפתחות עיניים בליגות אחרות.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

from . import data as D
from .models import Club, Player, clamp

# כמה עניין נשחק בשבוע שבו לא קרה כלום. הדעיכה יחסית ולא קבועה:
# מועדון ששם עליך עין לא שוכח אותך תוך חודש, אבל גם לא זוכר לנצח.
DECAY = 0.985
DECAY_FLOOR = 0.10

# ספים
NOTICED = 25.0      # מופיע ברשימת "מי עוקב אחריי"
COURTED = 55.0      # סוכן עשוי לפנות אליך באמצע העונה
CHASED = 74.0       # הצעה רשמית בחלון


def interest_map(game) -> Dict[str, float]:
    """טבלת העניין הנוכחית. חיה בדגלים, ולכן נשמרת עם הקריירה."""
    data = game.flags.get("scout_interest")
    if not isinstance(data, dict):
        data = {}
        game.flags["scout_interest"] = data
    return data


def watchers(game, minimum: float = NOTICED) -> List[Tuple[Club, float]]:
    """הקבוצות שעוקבות אחריך, מהחזקה לחלשה."""
    out = []
    for cid, score in interest_map(game).items():
        club = game.clubs.get(cid)
        if club and score >= minimum:
            out.append((club, round(float(score), 1)))
    out.sort(key=lambda pair: -pair[1])
    return out


def interest_label(score: float) -> str:
    if score >= CHASED:
        return "רודפים אחריך"
    if score >= COURTED:
        return "מחזרים"
    if score >= 40:
        return "עוקבים מקרוב"
    return "רשומים אצלם"


# ---------------------------------------------------------------------------
# מי בכלל מסתכל
# ---------------------------------------------------------------------------

def candidate_clubs(game) -> List[Club]:
    """קבוצות שרמת השחקן שלך רלוונטית להן היום.

    התקרה נגזרת מהדירוג ומהמוניטין, אבל לא רק: עונה טובה פותחת דלתות
    שלא היו פתוחות בקיץ. חוזה שנגמר מרחיב את המעגל עוד.
    """
    me = game.me
    my_club = game.my_club
    current = my_club.reputation if my_club else 15
    ceiling = me.overall + 6 + (me.reputation - 40) * 0.30
    if me.season.apps >= 6:
        ceiling += (me.season.avg_rating - 6.6) * 9
    if me.age <= 21:
        ceiling += 5                       # על כישרון צעיר מהמרים
    if me.contract.years_left <= 1:
        ceiling += 5
    if game.flag("open_to_europe"):
        ceiling += 6
    # מי שקטן מדי לא באמת יילך על שחקן ברמה שלך — הוא לא יעמוד בשכר
    floor = max(current - 12, me.overall - 24)
    out = []
    for club in game.clubs.values():
        if my_club and club.cid == my_club.cid:
            continue
        if club.reputation > ceiling or club.reputation < floor:
            continue
        out.append(club)
    return out


def scouts_this_week(game, rng: random.Random, rating: Optional[float]) -> List[str]:
    """מריץ שבוע של סקאוטינג ומחזיר שורות לדוח.

    ``rating`` הוא הציון שלך במשחק השבוע, או None אם לא שיחקת.
    """
    me = game.me
    table = interest_map(game)
    lines: List[str] = []

    # דעיכה — מי שלא ראה אותך שוב מתחיל לשכוח
    for cid in list(table):
        table[cid] = round(float(table[cid]) * DECAY - DECAY_FLOOR, 2)
        if table[cid] <= 1.0:
            del table[cid]

    if rating is None or game.stage not in ("academy", "player", "veteran"):
        return lines

    pool = candidate_clubs(game)
    if not pool:
        return lines

    # כמה צופים בכלל מגיעים השבוע
    visits = 1 if rng.random() < 0.34 + me.reputation / 260.0 else 0
    if me.reputation >= 55 and rng.random() < 0.22:
        visits += 1
    for _ in range(visits):
        # מועדונים גדולים שולחים צופים לעיתים קרובות יותר — ומי שכבר
        # פתח עליך תיק חוזר לראות אותך שוב, וזה מה שבונה עניין אמיתי
        weights = []
        for club in pool:
            weight = (club.reputation / 30.0) ** 1.4
            weight *= 1.0 + float(table.get(club.cid, 0.0)) / 14.0
            weights.append((club, weight))
        total = sum(w for _, w in weights)
        roll = rng.random() * total
        club = weights[-1][0]
        for candidate, weight in weights:
            roll -= weight
            if roll <= 0:
                club = candidate
                break

        # הצופה לא שופט אותך במוחלט — הוא שואל אם אתה מספיק *לו*.
        # ערב טוב מול קבוצה קטנה שווה יותר מערב סביר מול ענקית.
        move = (rating - 6.5) * 4.5
        move += (me.overall - club.reputation * 0.92) * 0.38
        move += rng.uniform(-1.5, 1.5)
        if me.age <= 20:
            move = move * 1.15 + 0.8       # על גיל צעיר מוכנים להמר
        before = float(table.get(club.cid, 0.0))
        table[club.cid] = round(clamp(before + move, 0, 100), 2)
        country = D.club_country(club.cid, club.league_id)
        where = f" ({country})" if country != "ישראל" else ""
        lines.append(f"👀 צופה מ{club.name}{where} היה ביציע. {_verdict(move)}")
        if before < NOTICED <= table[club.cid]:
            lines.append(f"📋 {club.name} פתחו עליך תיק.")
    return lines


def _verdict(move: float) -> str:
    if move >= 6:
        return "הוא לא הוריד ממך עיניים."
    if move >= 2:
        return "הוא רשם משהו וסימן וי."
    if move >= -2:
        return "ערב שגרתי. הוא ראה מה שהוא ראה."
    return "הוא סגר את המחברת בהפסקה."


def top_suitor(game, minimum: float = CHASED) -> Optional[Club]:
    """הקבוצה שהכי רוצה אותך — אם מישהי הגיעה לרף."""
    ranked = watchers(game, minimum)
    return ranked[0][0] if ranked else None


def foreign_agent(game, rng: random.Random) -> Optional[Dict[str, Any]]:
    """סוכן מחו\"ל שמתקשר בעקבות מה שהצופים שלו כתבו.

    הוא לא מגיע יש מאין: הוא מייצג בדיוק את המועדון שכבר עוקב אחריך.
    """
    ranked = [(club, score) for club, score in watchers(game, COURTED)
              if D.club_country(club.cid, club.league_id) != "ישראל"]
    if not ranked:
        return None
    club, score = ranked[0]
    me = game.me
    country = D.club_country(club.cid, club.league_id)
    raise_factor = 1.6 + (club.reputation - (game.my_club.reputation if game.my_club else 20)) / 90.0
    wage = int(round(max(me.contract.wage * 1.4,
                         club.wage_budget * 0.16) * rng.uniform(0.85, 1.2) / 500) * 500)
    return {
        "agent": rng.choice(D.AGENT_NAMES),
        "club": club.cid,
        "club_name": club.name,
        "country": country,
        "score": round(score, 1),
        "wage": wage,
        "fee": int(round(wage * 0.18 / 500) * 500),
        "raise_factor": round(raise_factor, 2),
    }


def scout_report(game, club: Club) -> List[str]:
    """מה כתוב בתיק שיש עליך אצל מועדון מסוים."""
    me = game.me
    score = float(interest_map(game).get(club.cid, 0.0))
    country = D.club_country(club.cid, club.league_id)
    lines = [f"{club.name} · {country} · מוניטין {club.reputation}",
             f"רמת עניין: {interest_label(score)} ({score:.0f}/100)"]
    weights = D.POSITION_WEIGHTS[me.position]
    ranked = sorted(D.ATTRIBUTES,
                    key=lambda a: -(me.attributes.get(a, 50) * weights.get(a, 0.1)))
    best, worst = ranked[0], ranked[-1]
    lines.append(f'"{D.ATTRIBUTE_NAMES_HE[best]} ברמה שאנחנו מחפשים '
                 f'({me.attributes.get(best, 50)}). '
                 f'{D.ATTRIBUTE_NAMES_HE[worst]} — עוד לא."')
    if me.age <= 21:
        lines.append('"בגיל הזה, מה שחסר עוד אפשר ללמד."')
    elif me.age >= 30:
        lines.append('"הגיל אצלנו הוא שיקול. חוזה קצר, לא יותר."')
    if score < NOTICED:
        lines.append("עוד לא פתחו עליך תיק אמיתי.")
    return lines
