# -*- coding: utf-8 -*-
"""
football_manager.engine
=======================
מנוע הסימולציה: בחירת הרכב, חישוב עוצמות, הגרלת שערים, דירוגים,
כרטיסים, פציעות ופרשנות בעברית.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from . import data as D
from . import matchstats as MS
from .models import Club, Player, clamp

# מנטליות טקטית: (מכפיל התקפה, מכפיל הגנה, תוספת סיכון)
MENTALITIES = {
    "ultra_defensive": ("בטון מזוין", 0.72, 1.30, -0.15),
    "defensive": ("הגנתי", 0.86, 1.15, -0.07),
    "balanced": ("מאוזן", 1.00, 1.00, 0.00),
    "attacking": ("התקפי", 1.16, 0.88, 0.08),
    "all_out": ("הכל קדימה", 1.34, 0.70, 0.18),
}

PRESSING = {
    "low": ("בלוק נמוך", -0.05, 0.06, 0.6),
    "medium": ("לחץ מדוד", 0.0, 0.0, 1.0),
    "high": ("לחץ גבוה", 0.09, -0.06, 1.5),
}

INJURY_TYPES = [
    ("מתיחה בשריר הירך", 1, 3),
    ("נקע בקרסול", 2, 5),
    ("חבלה בברך", 4, 10),
    ("שבר בכף הרגל", 8, 18),
    ("קרע ברצועה הצולבת", 24, 40),
    ("זעזוע מוח", 1, 2),
    ("פציעת גב", 2, 6),
]


# ---------------------------------------------------------------------------
# תוצאות
# ---------------------------------------------------------------------------

@dataclass
class MatchEvent:
    """אירוע בודד במשחק (שער, כרטיס, פציעה)."""
    minute: int
    kind: str            # goal | assist | yellow | red | injury | miss
    club_id: str
    player_id: str
    text: str = ""


@dataclass
class MatchResult:
    """תוצאת משחק מלאה."""
    home_id: str
    away_id: str
    home_goals: int = 0
    away_goals: int = 0
    events: List[MatchEvent] = field(default_factory=list)
    ratings: Dict[str, float] = field(default_factory=dict)
    motm: Optional[str] = None
    home_lineup: List[str] = field(default_factory=list)
    away_lineup: List[str] = field(default_factory=list)
    commentary: List[str] = field(default_factory=list)
    competition: str = "ליגה"
    # שורת סטטיסטיקה אישית — נבנית רק לשחקן שאתה משחק בו
    stat_lines: Dict[str, dict] = field(default_factory=dict)

    @property
    def score(self) -> str:
        return f"{self.home_goals}:{self.away_goals}"

    def result_for(self, club_id: str) -> str:
        """W / D / L מנקודת מבט מועדון."""
        if self.home_goals == self.away_goals:
            return "D"
        if club_id == self.home_id:
            return "W" if self.home_goals > self.away_goals else "L"
        return "W" if self.away_goals > self.home_goals else "L"

    def goals_for(self, club_id: str) -> int:
        return self.home_goals if club_id == self.home_id else self.away_goals

    def goals_against(self, club_id: str) -> int:
        return self.away_goals if club_id == self.home_id else self.home_goals


# ---------------------------------------------------------------------------
# הרכב
# ---------------------------------------------------------------------------

def position_fit(player_pos: str, slot: str) -> float:
    """כמה שחקן מתאים למשבצת בהרכב (1.0 = התאמה מלאה)."""
    if player_pos == slot:
        return 1.0
    if (player_pos == "GK") != (slot == "GK"):
        return 0.35
    groups = [
        {"CB"}, {"LB", "RB"}, {"DM", "CM"}, {"CM", "AM"},
        {"LW", "RW", "AM"}, {"ST", "LW", "RW"},
    ]
    for group in groups:
        if player_pos in group and slot in group:
            return 0.90
    return 0.72


def pick_lineup(club: Club, players: Dict[str, Player],
                formation: Optional[str] = None,
                forced: Optional[List[str]] = None) -> List[str]:
    """בוחר את ההרכב הפותח.

    קודם מוצבים שחקנים שנכפו על ידי המנג'ר, כל אחד במשבצת הכי מתאימה לו.
    אחר כך ממלאים משבצות בשחקנים בעמדתם הטבעית בלבד, ורק בסוף — במי שנשאר.
    שני המעברים מונעים מצב שבו הקשר הכי טוב תופס את מקום המגן הימני
    ומשאיר את משבצת הקישור למישהו גרוע יותר.
    """
    formation = formation or club.formation
    slots = D.FORMATIONS.get(formation, D.FORMATIONS["4-3-3"])
    available = [players[pid] for pid in club.squad
                 if pid in players and players[pid].available]
    lineup: List[Optional[str]] = [None] * len(slots)
    used: set = set()

    def claim(index: int, player: Player) -> None:
        lineup[index] = player.pid
        used.add(player.pid)

    for pid in (forced or []):
        player = players.get(pid)
        if not player or pid in used or player not in available:
            continue
        best_index, best_fit = -1, 0.0
        for index, slot in enumerate(slots):
            if lineup[index]:
                continue
            fit = position_fit(player.position, slot)
            if fit > best_fit:
                best_index, best_fit = index, fit
        if best_index >= 0:
            claim(best_index, player)

    for min_fit in (0.9, 0.0):
        for index, slot in enumerate(slots):
            if lineup[index]:
                continue
            candidates = [p for p in available
                          if p.pid not in used
                          and position_fit(p.position, slot) >= min_fit]
            if not candidates:
                continue
            claim(index, max(candidates,
                             key=lambda p: p.effective * position_fit(p.position, slot)))

    return [pid for pid in lineup if pid]


def team_strength(lineup: List[str], players: Dict[str, Player],
                  formation: str) -> Tuple[float, float, float]:
    """מחזיר (הגנה, קישור, התקפה) לקבוצה, בסולם אחיד של דירוגי שחקנים.

    כל קו מקבל את הממוצע המשוקלל של השחקנים שתורמים לו, ובונוס קטן
    על כמות (מערך עם חמישה מגנים באמת מגן טוב יותר).
    """
    slots = D.FORMATIONS.get(formation, D.FORMATIONS["4-3-3"])
    sums = {"def": 0.0, "mid": 0.0, "att": 0.0}
    shares = {"def": 0.0, "mid": 0.0, "att": 0.0}
    for idx, pid in enumerate(lineup):
        player = players.get(pid)
        if not player:
            continue
        slot = slots[idx] if idx < len(slots) else player.position
        fit = position_fit(player.position, slot)
        power = player.effective * (0.62 + 0.38 * fit)
        share = D.POSITION_ROLE_SHARE[slot]
        for line in sums:
            sums[line] += power * share[line]
            shares[line] += share[line]

    baselines = {"def": 5.05, "mid": 3.10, "att": 2.85}
    out = []
    for line in ("def", "mid", "att"):
        total_share = shares[line]
        average = sums[line] / total_share if total_share > 0.01 else 40.0
        quantity = (max(0.4, total_share) / baselines[line]) ** 0.4
        out.append(average * quantity)
    return out[0], out[1], out[2]


def medical_care(club: Optional[Club]) -> float:
    """איכות הטיפול הרפואי במועדון, 0..1 — מרכז רפואי ופיזיותרפיסט."""
    if club is None:
        return 0.45
    return clamp((club.medical_centre + club.staff_quality("physio")) / 200.0, 0.0, 1.0)


def _poisson(rng: random.Random, lam: float) -> int:
    """הגרלת מספר שערים מהתפלגות פואסון."""
    lam = max(0.02, lam)
    limit = math.exp(-lam)
    k, prod = 0, rng.random()
    while prod > limit and k < 12:
        k += 1
        prod *= rng.random()
    return k


# ---------------------------------------------------------------------------
# סימולציה
# ---------------------------------------------------------------------------

def simulate_match(home: Club, away: Club, players: Dict[str, Player],
                   rng: random.Random,
                   home_tactics: Optional[dict] = None,
                   away_tactics: Optional[dict] = None,
                   competition: str = "ליגה",
                   neutral: bool = False,
                   focus_pid: Optional[str] = None) -> MatchResult:
    """מדמה משחק שלם בין שתי קבוצות ומחזיר תוצאה מלאה."""
    home_tactics = home_tactics or {}
    away_tactics = away_tactics or {}

    home_form = home_tactics.get("formation", home.formation)
    away_form = away_tactics.get("formation", away.formation)
    home_lineup = pick_lineup(home, players, home_form, home_tactics.get("forced"))
    away_lineup = pick_lineup(away, players, away_form, away_tactics.get("forced"))

    hd, hm, ha = team_strength(home_lineup, players, home_form)
    ad, am, aa = team_strength(away_lineup, players, away_form)

    h_ment = MENTALITIES.get(home_tactics.get("mentality", "balanced"), MENTALITIES["balanced"])
    a_ment = MENTALITIES.get(away_tactics.get("mentality", "balanced"), MENTALITIES["balanced"])
    h_press = PRESSING.get(home_tactics.get("pressing", "medium"), PRESSING["medium"])
    a_press = PRESSING.get(away_tactics.get("pressing", "medium"), PRESSING["medium"])

    ha *= h_ment[1] * (1 + h_press[1])
    hd *= h_ment[2] * (1 + h_press[2])
    aa *= a_ment[1] * (1 + a_press[1])
    ad *= a_ment[2] * (1 + a_press[2])

    # אנליסט: קריאת היריבה מתורגמת ליתרון קטן בשני הקווים (עד 4%)
    h_edge = 1.0 + home.staff_quality("analyst") / 2400.0
    a_edge = 1.0 + away.staff_quality("analyst") / 2400.0
    ha *= h_edge; hd *= h_edge; hm *= h_edge
    aa *= a_edge; ad *= a_edge; am *= a_edge

    # יתרון ביתיות
    if not neutral:
        ha *= 1.0 + home.fan_support / 640.0
        hd *= 1.02
        hm *= 1.03

    # שליטה בקישור מתרגמת להזדמנויות
    total_mid = hm + am
    h_control = hm / total_mid if total_mid else 0.5
    a_control = 1.0 - h_control

    def expected_goals(attack: float, defence: float, control: float,
                       team_talk: float) -> float:
        edge = (attack - defence) / 11.0
        base = 1.30 * math.exp(edge * 0.36)
        base *= 0.55 + 0.9 * control
        base *= 0.9 + team_talk * 0.2
        return clamp(base, 0.12, 4.6)

    h_xg = expected_goals(ha, ad, h_control, home_tactics.get("talk_boost", 0.0))
    a_xg = expected_goals(aa, hd, a_control, away_tactics.get("talk_boost", 0.0))

    home_goals = _poisson(rng, h_xg)
    away_goals = _poisson(rng, a_xg)

    result = MatchResult(home_id=home.cid, away_id=away.cid,
                         home_goals=home_goals, away_goals=away_goals,
                         home_lineup=home_lineup, away_lineup=away_lineup,
                         competition=competition)

    minutes = sorted(rng.sample(range(1, 94), min(90, home_goals + away_goals))) \
        if (home_goals + away_goals) else []
    side_queue = ([home.cid] * home_goals) + ([away.cid] * away_goals)
    rng.shuffle(side_queue)

    for idx, club_id in enumerate(side_queue):
        minute = minutes[idx] if idx < len(minutes) else rng.randint(1, 93)
        lineup = home_lineup if club_id == home.cid else away_lineup
        scorer = _pick_scorer(lineup, players, rng)
        if scorer is None:
            continue
        players[scorer].season.goals += 1
        result.events.append(MatchEvent(minute, "goal", club_id, scorer,
                                        f"⚽ {minute}' {players[scorer].name}"))
        assister = _pick_assister(lineup, players, rng, scorer)
        if assister:
            players[assister].season.assists += 1
            result.events.append(MatchEvent(minute, "assist", club_id, assister,
                                            f"👟 בישול: {players[assister].name}"))

    _apply_discipline(result, home_lineup, home.cid, players, rng, h_press[3])
    _apply_discipline(result, away_lineup, away.cid, players, rng, a_press[3])
    _apply_injuries(result, home_lineup, home.cid, players, rng, home)
    _apply_injuries(result, away_lineup, away.cid, players, rng, away)

    _rate_players(result, home_lineup, home.cid, players, rng,
                  focus_pid=focus_pid, possession=h_control)
    _rate_players(result, away_lineup, away.cid, players, rng,
                  focus_pid=focus_pid, possession=a_control)

    if result.ratings:
        result.motm = max(result.ratings, key=lambda pid: result.ratings[pid])
        players[result.motm].season.motm += 1

    # שער נקי
    if away_goals == 0 and home_lineup:
        players[home_lineup[0]].season.clean_sheets += 1
    if home_goals == 0 and away_lineup:
        players[away_lineup[0]].season.clean_sheets += 1

    result.commentary = build_commentary(result, home, away, players, rng)
    return result


def _pick_scorer(lineup: List[str], players: Dict[str, Player],
                 rng: random.Random) -> Optional[str]:
    """בוחר כובש לפי נטייה התקפית ובעיטה."""
    weights = []
    for pid in lineup:
        p = players.get(pid)
        if not p:
            continue
        share = D.POSITION_ROLE_SHARE[p.position]
        weight = (share["att"] * 3.0 + share["mid"] * 0.7 + share["def"] * 0.12)
        weight *= (p.attributes.get("shooting", 40) / 55.0) ** 1.5
        weight *= 0.7 + p.form / 140.0
        weights.append((pid, max(0.001, weight)))
    if not weights:
        return None
    total = sum(w for _, w in weights)
    roll = rng.random() * total
    upto = 0.0
    for pid, weight in weights:
        upto += weight
        if roll <= upto:
            return pid
    return weights[-1][0]


def _pick_assister(lineup: List[str], players: Dict[str, Player],
                   rng: random.Random, scorer: str) -> Optional[str]:
    """בוחר מבשל (או כלום — שער סולו)."""
    if rng.random() < 0.26:
        return None
    weights = []
    for pid in lineup:
        if pid == scorer:
            continue
        p = players.get(pid)
        if not p:
            continue
        share = D.POSITION_ROLE_SHARE[p.position]
        weight = (share["att"] * 1.6 + share["mid"] * 1.8 + share["def"] * 0.2)
        weight *= (p.attributes.get("passing", 40) / 55.0) ** 1.4
        weights.append((pid, max(0.001, weight)))
    if not weights:
        return None
    total = sum(w for _, w in weights)
    roll = rng.random() * total
    upto = 0.0
    for pid, weight in weights:
        upto += weight
        if roll <= upto:
            return pid
    return weights[-1][0]


def _apply_discipline(result: MatchResult, lineup: List[str], club_id: str,
                      players: Dict[str, Player], rng: random.Random,
                      press_factor: float) -> None:
    """כרטיסים צהובים ואדומים."""
    for pid in lineup:
        p = players.get(pid)
        if not p:
            continue
        chance = 0.055 * press_factor
        if p.has_trait("hothead"):
            chance *= 2.4
        chance *= 1.0 + D.POSITION_ROLE_SHARE[p.position]["def"] * 0.6
        if rng.random() < chance:
            minute = rng.randint(5, 92)
            if rng.random() < 0.09:
                p.season.red += 1
                result.events.append(MatchEvent(minute, "red", club_id, pid,
                                                f"🟥 {minute}' {p.name}"))
            else:
                p.season.yellow += 1
                result.events.append(MatchEvent(minute, "yellow", club_id, pid,
                                                f"🟨 {minute}' {p.name}"))


def _apply_injuries(result: MatchResult, lineup: List[str], club_id: str,
                    players: Dict[str, Player], rng: random.Random,
                    club: Optional[Club] = None) -> None:
    """פציעות במהלך המשחק. מרכז רפואי וצוות טוב מקצרים את השיקום."""
    care = medical_care(club)
    for pid in lineup:
        p = players.get(pid)
        if not p:
            continue
        # injury_risk מרכז את כל מה שמשפיע: עמידות, כוח פיזי, חדות
        # משחק, גיל, כושר ותכונות אופי — וכולם ניתנים להשפעה
        chance = 0.0115 * p.injury_risk
        if rng.random() < chance:
            name, low, high = rng.choice(INJURY_TYPES)
            weeks = rng.randint(low, high)
            if care > 0.5 and weeks > 1 and rng.random() < (care - 0.5) * 1.6:
                weeks -= 1                      # טיפול טוב חוסך שבוע
            p.injury_weeks = weeks
            p.injury_name = name
            p.fitness = min(p.fitness, 55.0)
            result.events.append(MatchEvent(rng.randint(3, 90), "injury", club_id, pid,
                                            f"🚑 {p.name} — {name} ({weeks} שבועות)"))


def _rate_players(result: MatchResult, lineup: List[str], club_id: str,
                  players: Dict[str, Player], rng: random.Random,
                  focus_pid: Optional[str] = None,
                  possession: float = 0.5) -> None:
    """נותן ציון לכל שחקן בהרכב ומעדכן סטטיסטיקה.

    לשחקן שאתה משחק בו נבנית גם שורת סטטיסטיקה מלאה, והציון שלו נגזר
    ממה שקרה בשורה הזאת — לא מדירוג כללי. ככה שבוע של אימון סיומות
    מגיע עד לציון של יום ראשון.
    """
    conceded = result.goals_against(club_id)
    outcome = result.result_for(club_id)
    team_mod = {"W": 0.45, "D": 0.0, "L": -0.35}[outcome]

    goals_by = {}
    assists_by = {}
    cards = {}
    for ev in result.events:
        if ev.club_id != club_id:
            continue
        if ev.kind == "goal":
            goals_by[ev.player_id] = goals_by.get(ev.player_id, 0) + 1
        elif ev.kind == "assist":
            assists_by[ev.player_id] = assists_by.get(ev.player_id, 0) + 1
        elif ev.kind in ("yellow", "red"):
            cards[ev.player_id] = cards.get(ev.player_id, 0) + (1 if ev.kind == "yellow" else 3)

    for pid in lineup:
        p = players.get(pid)
        if not p:
            continue
        minutes = 90 if rng.random() > 0.18 else rng.randint(55, 89)
        goals = goals_by.get(pid, 0)
        assists = assists_by.get(pid, 0)

        rating = 5.80 + team_mod + rng.gauss(0, 0.44)
        rating += (p.overall - 58) * 0.026
        rating += (p.form - 50) * 0.003
        # חדות וכושר הם קנס, לא בונוס: שחקן רענן הוא הבסיס, ומי שנכנס
        # שרוף או בלי דקות ברגליים משלם על זה בציון. זה מה שהמאמן
        # מתכוון אליו כשהוא שולח אותך לנוח.
        rating -= max(0.0, 92.0 - p.sharpness) * 0.010
        rating -= max(0.0, 90.0 - p.fitness) * 0.009

        if pid == focus_pid:
            stats = MS.match_stat_line(p, minutes, goals, assists, rng,
                                       possession=possession)
            result.stat_lines[pid] = stats
            # הציון שלך נגזר ממה שבאמת עשית במגרש הערב, ולא רק ממי שאתה:
            # 65 זה ערב ממוצע שלך, ומשם למעלה או למטה
            rating += (MS.performance(stats, p.position) - 65) * 0.022

        rating += goals * 1.05
        rating += assists * 0.65
        rating -= cards.get(pid, 0) * 0.28
        share = D.POSITION_ROLE_SHARE[p.position]
        rating -= conceded * 0.24 * share["def"]
        if conceded == 0:
            rating += 0.45 * share["def"]
        if p.has_trait("clutch") and rng.random() < 0.4:
            rating += 0.4
        rating = round(clamp(rating, 3.0, 10.0), 1)
        result.ratings[pid] = rating

        p.season.add_match(rating, minutes)
        p.fitness = clamp(p.fitness - minutes * 0.13 - rng.uniform(0, 6), 8, 100)
        # כושר ומורל מגיבים לביצוע
        p.form = clamp(p.form * 0.82 + (rating - 6.0) * 14 + 50 * 0.18, 5, 99)
        p.morale = clamp(p.morale + (2.5 if outcome == "W" else -2.0 if outcome == "L" else 0.3)
                         + (rating - 6.5) * 1.6, 5, 99)


def build_commentary(result: MatchResult, home: Club, away: Club,
                     players: Dict[str, Player], rng: random.Random) -> List[str]:
    """מייצר פרשנות קצרה בעברית למשחק."""
    lines = [f"🏟️ {home.name} {result.home_goals} - {result.away_goals} {away.name}"
             f"  ({result.competition})"]
    diff = result.home_goals - result.away_goals
    total = result.home_goals + result.away_goals

    if total == 0:
        lines.append("שני שוערים מצוינים, אפס דרמה. 0:0 שאף אחד לא יזכור.")
    elif abs(diff) >= 3:
        winner = home.name if diff > 0 else away.name
        lines.append(f"{winner} פשוט דרסו. הקהל התחיל לצאת ברבע שעה האחרונה.")
    elif diff == 0:
        lines.append("תיקו שמשאיר את שתי הקבוצות עם טעם מריר.")
    else:
        winner = home.name if diff > 0 else away.name
        lines.append(f"{winner} לקחו את זה בשיניים. משחק צמוד עד השריקה האחרונה.")

    for ev in sorted([e for e in result.events if e.kind in ("goal", "red", "injury")],
                     key=lambda e: e.minute):
        lines.append(ev.text)

    if result.motm and result.motm in players:
        lines.append(f"⭐ מצטיין המשחק: {players[result.motm].name} "
                     f"({result.ratings.get(result.motm, 0)})")
    return lines
