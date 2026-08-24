# -*- coding: utf-8 -*-
"""
football_manager.game
=====================
מצב המשחק המלא: לוח משחקים, טבלאות, גביע, שבוע אימונים, עונה,
מעבר בין שלבי קריירה, כסף, שמירה וטעינה.

כל הלוגיקה כאן חסינה לממשק — ה-CLI הוא רק עטיפה דקה מסביב.
"""

from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from . import data as D
from . import story as ST
from .engine import (MENTALITIES, MatchEvent, MatchResult, _poisson,
                     build_commentary, simulate_match)
from .models import (Club, Contract, Player, TableRow, clamp,
                     generate_player, generate_world, wage_for_overall)
from .progression import (end_of_season_development, retirement_pressure,
                          should_retire, simulate_ai_week, weekly_recovery,
                          weekly_training)

SEASON_WEEKS = 43
CUP_WEEKS = {6: "שלב 32 האחרונות", 13: "שמינית הגמר", 21: "רבע הגמר",
             29: "חצי הגמר", 37: "גמר הגביע"}
SAVE_DIR = os.path.join(os.path.expanduser("~"), ".football_manager_saves")


# ---------------------------------------------------------------------------
# לוח משחקים
# ---------------------------------------------------------------------------

def round_robin(teams: List[str], rng: random.Random) -> List[List[Tuple[str, str]]]:
    """מייצר לוח 'כל אחד נגד כולם' הלוך ושוב בשיטת המעגל."""
    teams = list(teams)
    rng.shuffle(teams)
    if len(teams) % 2:
        teams.append("__bye__")
    n = len(teams)
    rounds = []
    for r in range(n - 1):
        pairs = []
        for i in range(n // 2):
            home, away = teams[i], teams[n - 1 - i]
            if "__bye__" in (home, away):
                continue
            pairs.append((home, away) if r % 2 == 0 else (away, home))
        rounds.append(pairs)
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
    second_leg = [[(a, h) for h, a in rnd] for rnd in rounds]
    return rounds + second_leg


def league_weeks() -> List[int]:
    """השבועות בעונה שאינם שבועות גביע."""
    return [w for w in range(1, SEASON_WEEKS + 1) if w not in CUP_WEEKS]


# ---------------------------------------------------------------------------
# דוח שבועי
# ---------------------------------------------------------------------------

@dataclass
class WeekReport:
    """סיכום מה שקרה בשבוע."""
    week: int
    lines: List[str] = field(default_factory=list)
    match: Optional[MatchResult] = None
    event_id: Optional[str] = None
    season_ended: bool = False

    def add(self, text: str) -> None:
        if text:
            self.lines.append(text)


# ---------------------------------------------------------------------------
# מצב המשחק
# ---------------------------------------------------------------------------

class GameState:
    """כל מצב המשחק במקום אחד."""

    def __init__(self) -> None:
        self.seed: int = 0
        self.clubs: Dict[str, Club] = {}
        self.players: Dict[str, Player] = {}
        self.me_id: str = ""
        self.stage: str = "academy"
        self.year: int = 2026
        self.week: int = 1
        self.fixtures: Dict[str, List[List[Tuple[str, str]]]] = {}
        self.tables: Dict[str, Dict[str, TableRow]] = {}
        self.cup: Dict[str, Any] = {}
        self.money: int = 0
        self.flags: Dict[str, Any] = {}
        self.honours: List[str] = []
        self.news: List[str] = []
        self.fired_events: List[str] = []
        self.pending_event_id: Optional[str] = None
        self.pending_event_body: Optional[str] = None
        self.managed_club_id: Optional[str] = None
        self.tactics: Dict[str, Any] = {"mentality": "balanced", "pressing": "medium",
                                        "formation": "4-3-3", "talk_boost": 0.0}
        self.training_focus: str = "shooting"
        self.intensity: float = 1.0
        self.first_club_id: Optional[str] = None
        self.last_club_id: Optional[str] = None
        self.history: List[Dict[str, Any]] = []
        self.caps: int = 0
        self.intl_goals: int = 0
        self.no_start_streak: int = 0
        self.game_over: bool = False
        self.rng = random.Random(0)

    # -- קיצורים ----------------------------------------------------------

    @property
    def me(self) -> Player:
        return self.players[self.me_id]

    @property
    def my_club(self) -> Optional[Club]:
        if self.stage in ("manager", "coach", "director", "owner") and self.managed_club_id:
            return self.clubs.get(self.managed_club_id)
        club_id = self.me.club_id
        return self.clubs.get(club_id) if club_id else None

    @property
    def my_league(self) -> Optional[str]:
        club = self.my_club
        return club.league_id if club else None

    def flag(self, name: str, default: Any = None) -> Any:
        return self.flags.get(name, default)

    def set_flag(self, name: str, value: Any = True) -> None:
        self.flags[name] = value

    def log(self, text: str) -> None:
        if text:
            self.news.append(f"[{self.year}/ש{self.week}] {text}")
            self.news = self.news[-120:]

    def record_honour(self, text: str) -> str:
        entry = f"{self.year}: {text}"
        self.honours.append(entry)
        self.me.career.trophies += 1
        self.log(f"🏆 {text}")
        return entry

    def earn_money(self, amount: int) -> int:
        self.money += int(amount)
        return self.money

    def spend_money(self, amount: int) -> int:
        self.money = max(0, self.money - int(amount))
        return self.money

    # ==================================================================
    # יצירת משחק חדש
    # ==================================================================

    @staticmethod
    def stage_for_age(age: int) -> str:
        """השלב שמתאים לגיל שבו מתחילים."""
        if age <= 15:
            return "youth"
        if age <= 17:
            return "academy"
        if age <= 30:
            return "player"
        return "veteran"

    @classmethod
    def new_game(cls, name: str, position: str, club_id: str,
                 age: int = 15, seed: Optional[int] = None,
                 stage: Optional[str] = None,
                 role: str = "player") -> "GameState":
        """פותח קריירה חדשה של שחקן צעיר."""
        state = cls()
        state.seed = seed if seed is not None else random.randrange(1, 10 ** 8)
        state.rng = random.Random(state.seed)
        state.clubs, state.players = generate_world(state.seed)
        club = state.clubs[club_id]

        if role == "manager":
            return state._start_as_manager(name, club, age)

        # ככל שמתחילים מבוגר יותר, מתחילים כשחקן מגובש יותר
        if age <= 17:
            quality = int(clamp(club.reputation * 0.55 + 24, 48, 70))
        else:
            quality = int(clamp(club.reputation * 0.66 + 12 + min(8, (age - 17) * 1.4), 42, 82))
        me = generate_player(state.rng, club, position, age=age, quality=quality)
        me.name = name
        me.is_human = True
        # מי שמתחיל צעיר יותר — יש לו יותר לאן לגדול
        me.potential = int(clamp(me.overall + state.rng.randint(6, 22)
                                 + max(0, 24 - age) * 2.2, me.overall + 2, 94))
        me.club_id = club_id
        if age <= 15:
            me.contract = Contract(wage=0, years_left=0)   # בגיל הנוער אין חוזה
        elif age <= 17:
            me.contract = Contract(wage=max(2500, wage_for_overall(me.overall) // 2),
                                   years_left=3)
        else:
            me.contract = Contract(wage=wage_for_overall(me.overall),
                                   years_left=state.rng.randint(2, 4))
        me.morale = 70.0
        me.reputation = (3.0 if age <= 15 else 8.0 if age <= 17
                         else clamp(me.overall - 28 + (age - 18) * 1.2, 5, 70))

        # מי שמתחיל אחרי גיל 18 — כבר יש לו עבר
        if age >= 19:
            seasons = min(12, age - 17)
            me.career.apps = int(seasons * state.rng.uniform(14, 26))
            share = D.POSITION_ROLE_SHARE[position]["att"]
            me.career.goals = int(me.career.apps * share * state.rng.uniform(0.10, 0.34))
            me.career.assists = int(me.career.apps * state.rng.uniform(0.04, 0.13))
            me.career.minutes = me.career.apps * 78
            me.career.rating_sum = me.career.apps * state.rng.uniform(6.3, 7.0)
            me.coaching = clamp(me.coaching + (age - 18) * 1.1, 0, 60)
        me.traits = [state.rng.choice(list(D.TRAITS.keys()))]
        state.players[me.pid] = me
        club.squad.append(me.pid)
        state.me_id = me.pid
        state.first_club_id = club_id
        state.last_club_id = club_id
        state.stage = stage or cls.stage_for_age(age)
        club.manager_trust = (45.0 if age <= 17
                              else clamp(35 + (me.overall - 55) * 1.4, 25, 78))

        state.start_season(first=True)
        state.log(f"התחלת את הדרך ב{club.name}.")
        return state

    def _start_as_manager(self, name: str, club: Club, age: int) -> "GameState":
        """קריירה שמתחילה מהספסל: מנג'ר ראשי, בלי עבר כשחקן פעיל."""
        me = generate_player(self.rng, club, "CM", age=min(age, 40), quality=55)
        me.name = name
        me.is_human = True
        me.age = age
        me.retired = True
        me.club_id = None
        me.contract = Contract(wage=0, years_left=0)
        me.coaching = clamp(28 + (age - 32) * 1.9 + self.rng.uniform(0, 12), 20, 92)
        me.badges = min(4, int(me.coaching // 22))
        me.media_skill = clamp(15 + (age - 32) * 0.9, 5, 70)
        me.business = clamp(10 + (age - 32) * 0.8, 5, 60)
        me.reputation = clamp(12 + (age - 32) * 1.1, 5, 60)
        if self.rng.random() < 0.65:          # עבר כשחקן — לא לכל מנג'ר יש
            me.career.apps = self.rng.randint(60, 380)
            me.career.goals = int(me.career.apps * self.rng.uniform(0.02, 0.22))
            me.career.assists = int(me.career.apps * self.rng.uniform(0.03, 0.12))
            me.career.rating_sum = me.career.apps * self.rng.uniform(6.2, 6.9)
        self.players[me.pid] = me
        self.me_id = me.pid

        self.stage = "manager"
        self.managed_club_id = club.cid
        self.first_club_id = club.cid
        self.last_club_id = club.cid
        club.manager_name = name
        club.board_confidence = 58.0
        self.tactics["formation"] = club.formation
        self.training_focus = "tactics"
        self.start_season(first=True)
        self.log(f"מונית למנג'ר של {club.name}.")
        return self

    # ==================================================================
    # עונה
    # ==================================================================

    def start_season(self, first: bool = False) -> None:
        """בונה לוח משחקים, טבלאות וגביע לעונה חדשה."""
        self.week = 1
        self.fixtures = {}
        self.tables = {}
        for league in D.LEAGUES:
            lid = league["id"]
            clubs = [c.cid for c in self.clubs.values() if c.league_id == lid]
            self.fixtures[lid] = round_robin(clubs, self.rng)
            self.tables[lid] = {cid: TableRow(club_id=cid) for cid in clubs}
        self._build_cup()
        for club in self.clubs.values():
            club.season_expectation = self._expectation(club)

    def _build_cup(self) -> None:
        """גביע המדינה: כל ליגת העל + 12 מהלאומית — 32 קבוצות בנוקאאוט."""
        top = [c.cid for c in self.clubs.values() if c.league_id == "top"]
        national = sorted([c for c in self.clubs.values() if c.league_id == "national"],
                          key=lambda c: -c.reputation)[:12]
        teams = top + [c.cid for c in national]
        self.rng.shuffle(teams)
        self.cup = {"teams": teams[:32], "round": "שלב 32 האחרונות",
                    "winner": None, "log": []}

    def _expectation(self, club: Club) -> str:
        peers = [c for c in self.clubs.values() if c.league_id == club.league_id]
        rank = sorted(peers, key=lambda c: -c.reputation).index(club) + 1
        if rank <= 2:
            return "אליפות"
        if rank <= 4:
            return "מקום באירופה"
        if rank <= len(peers) - 3:
            return "אמצע טבלה"
        return "הישרדות"

    def league_round_for_week(self, league_id: str, week: int) -> Optional[int]:
        """איזה מחזור ליגה משוחק בשבוע נתון."""
        if week in CUP_WEEKS:
            return None
        weeks = league_weeks()
        if week not in weeks:
            return None
        idx = weeks.index(week)
        rounds = self.fixtures.get(league_id, [])
        return idx if idx < len(rounds) else None

    def my_fixture(self, week: Optional[int] = None) -> Optional[Tuple[str, str]]:
        """המשחק שלי השבוע (בית, חוץ) או None."""
        week = week or self.week
        club = self.my_club
        if not club:
            return None
        if week in CUP_WEEKS:
            return self._cup_fixture_for(club.cid)
        rnd = self.league_round_for_week(club.league_id, week)
        if rnd is None:
            return None
        for home, away in self.fixtures[club.league_id][rnd]:
            if club.cid in (home, away):
                return (home, away)
        return None

    def _cup_fixture_for(self, cid: str) -> Optional[Tuple[str, str]]:
        teams = self.cup.get("teams", [])
        if cid not in teams:
            return None
        idx = teams.index(cid)
        pair_start = idx - (idx % 2)
        if pair_start + 1 >= len(teams):
            return None
        return (teams[pair_start], teams[pair_start + 1])

    # ==================================================================
    # התקדמות שבועית
    # ==================================================================

    def available_actions(self) -> List[Tuple[str, str]]:
        """פעולות אפשריות לשבוע, לפי שלב הקריירה."""
        if self.stage == "youth":
            keys = list(D.ATTRIBUTES) + ["street", "school", "rest"]
            return [(k, D.TRAINING_FOCUS_HE[k]) for k in keys]
        if self.stage in ("academy", "player", "veteran"):
            keys = list(D.ATTRIBUTES) + ["rest", "badges", "media", "business"]
            return [(k, D.TRAINING_FOCUS_HE[k]) for k in keys]
        if self.stage in ("coach", "manager"):
            return [("tactics", "עבודה טקטית עם הקבוצה"),
                    ("individual", "אימון אישי לשחקנים צעירים"),
                    ("scouting", "סקאוטינג ואיתור שחקנים"),
                    ("media", "עבודה מול התקשורת"),
                    ("badges", "השתלמות מקצועית"),
                    ("rest", "לתת לקבוצה לנשום")]
        if self.stage == "pundit":
            return [("studio", "אולפן שידור"), ("column", "טור בעיתון"),
                    ("badges", "לשמור על תעודות האימון"), ("rest", "חופש")]
        if self.stage == "agent":
            return [("clients", "לגייס לקוחות חדשים"), ("deals", "לסגור עסקאות"),
                    ("media", "לבנות קשרים בתקשורת"), ("rest", "חופש")]
        if self.stage in ("director", "owner"):
            return [("squad", "בניית סגל"), ("finance", "ניהול פיננסי"),
                    ("academy", "השקעה בנוער"), ("rest", "חופש")]
        return [("rest", "מנוחה")]

    def set_action(self, key: str) -> None:
        self.training_focus = key

    def advance_week(self) -> WeekReport:
        """מריץ שבוע שלם ומחזיר דוח."""
        report = WeekReport(week=self.week)
        if self.game_over:
            report.add("הקריירה הסתיימה.")
            return report
        if self.pending_event_id:
            report.add("יש החלטה שממתינה לך — צריך לבחור לפני שממשיכים.")
            report.event_id = self.pending_event_id
            return report

        # 1. פעולת השבוע
        report.lines.extend(self._do_weekly_action())

        # 2. משחקים — הליגה הבוגרת רצה גם כשאתה עוד בקבוצת הנוער
        self._simulate_week_matches(report, spectator=self.stage == "youth")
        if self.stage == "youth":
            self._youth_week(report)

        # 3. שחקני מחשב
        simulate_ai_week(self.players, self.rng, self.clubs, skip=self.me_id)

        # 4. אירוע עלילה — הטקסט נבנה ונשמר עכשיו, כשההקשר עדיין תקף
        event = ST.pick_event(self, self.rng)
        if event and self._arm_event(event):
            report.event_id = event.eid

        # 5. שכר
        self._weekly_income(report)

        # 6. קידום השבוע
        self.week += 1
        if self.week > SEASON_WEEKS:
            report.season_ended = True
            report.lines.extend(self.end_season())
        return report

    def _do_weekly_action(self) -> List[str]:
        """מפעיל את הפעולה שנבחרה לשבוע."""
        focus = self.training_focus
        me = self.me
        club = self.my_club

        if self.stage == "youth":
            if focus == "school":
                if self.rng.random() < 0.35:
                    me.attributes["mental"] = int(clamp(
                        me.attributes.get("mental", 50) + 1, 10, 97))
                self.flags["school"] = self.flag("school", 0) + 1
                me.fitness = clamp(me.fitness + 14, 0, 100)
                return ["📚 שבוע של בית ספר. ההורים מרוצים, המאמן פחות."]
            if focus == "street":
                attr = self.rng.choice(["dribbling", "shooting", "pace"])
                lines = weekly_training(me, attr, club, self.rng, 1.15)
                me.morale = clamp(me.morale + 4, 5, 99)
                return ["🧱 שיחקת עד שהחשיך במגרש השכונתי."] + lines
            return weekly_training(me, focus, club, self.rng, self.intensity)

        if self.stage in ("academy", "player", "veteran"):
            return weekly_training(me, focus, club, self.rng, self.intensity)

        lines: List[str] = []
        if self.stage in ("coach", "manager"):
            if focus == "tactics":
                self.tactics["talk_boost"] = clamp(self.tactics.get("talk_boost", 0) + 0.25,
                                                   0, 0.6)
                me.coaching = clamp(me.coaching + 0.6, 0, 100)
                lines.append("🧠 עבדתם על תבניות. הקבוצה נכנסת מוכנה יותר למשחק.")
            elif focus == "individual" and club:
                young = [self.players[p] for p in club.squad
                         if p in self.players and self.players[p].age <= 22]
                if young:
                    target = self.rng.choice(young)
                    weekly_training(target, self.rng.choice(D.ATTRIBUTES), club,
                                    self.rng, 1.2)
                    lines.append(f"🎯 עבודה אישית עם {target.name} ({target.age}).")
            elif focus == "scouting" and club:
                self.set_flag("scouted", True)
                lines.append("🔍 הצוות סרק שחקנים — בחלון ההעברות יהיו לך יעדים.")
            elif focus == "media":
                me.media_skill = clamp(me.media_skill + 1.1, 0, 100)
                if club:
                    club.fan_support = clamp(club.fan_support + 1.2, 0, 100)
                lines.append("🎤 מסיבת עיתונאים טובה. הקהל נרגע.")
            elif focus == "badges":
                me.coaching = clamp(me.coaching + 1.4, 0, 100)
                lines.append("📚 השתלמות מקצועית — ידע האימון עלה.")
            elif focus == "rest" and club:
                for pid in club.squad:
                    p = self.players.get(pid)
                    if p:
                        p.fitness = clamp(p.fitness + 14, 0, 100)
                        p.morale = clamp(p.morale + 1.5, 0, 100)
                lines.append("😌 שבוע קליל. הסגל רענן.")
            return lines

        if self.stage == "pundit":
            if focus == "studio":
                fee = int(6000 + me.media_skill * 260 + me.reputation * 190)
                self.earn_money(fee)
                me.media_skill = clamp(me.media_skill + 1.4, 0, 100)
                me.reputation = clamp(me.reputation + 0.3, 0, 99)
                lines.append(f"📺 שידור באולפן. ₪{fee:,}.")
            elif focus == "column":
                fee = int(3000 + me.media_skill * 120)
                self.earn_money(fee)
                me.media_skill = clamp(me.media_skill + 1.0, 0, 100)
                lines.append(f"📰 טור שבועי. ₪{fee:,}.")
            elif focus == "badges":
                me.coaching = clamp(me.coaching + 1.6, 0, 100)
                lines.append("📚 שמרת על הכשרת האימון שלך.")
            else:
                lines.append("🌴 שבוע חופש.")
            return lines

        if self.stage == "agent":
            if focus == "clients":
                gained = 1 if self.rng.random() < 0.35 + me.business / 220 else 0
                self.flags["clients"] = self.flag("clients", 0) + gained
                me.business = clamp(me.business + 1.2, 0, 100)
                lines.append("🤝 חתמת לקוח חדש." if gained else "📞 שיחות. בלי חתימות השבוע.")
            elif focus == "deals":
                clients = self.flag("clients", 0)
                fee = int(clients * (3000 + me.business * 220) * self.rng.uniform(0.5, 1.5))
                self.earn_money(fee)
                lines.append(f"💼 עמלות מעסקאות: ₪{fee:,}." if fee else
                             "💼 אין לקוחות — אין עמלות.")
            elif focus == "media":
                me.media_skill = clamp(me.media_skill + 1.3, 0, 100)
                lines.append("🎤 בנית קשרים. השם שלך חוזר בכתבות.")
            else:
                lines.append("🌴 שבוע חופש.")
            return lines

        if self.stage in ("director", "owner") and club:
            if focus == "squad":
                club.reputation = int(clamp(club.reputation + 0.3, 1, 99))
                lines.append("📋 עבודת סגל. המועדון נראה מסודר יותר.")
            elif focus == "finance":
                income = int(club.reputation * 9000 * self.rng.uniform(0.7, 1.4))
                club.budget += income / 1_000_000
                if self.stage == "owner":
                    self.earn_money(int(income * 0.15))
                lines.append(f"💰 הכנסות: ₪{income:,} לקופת המועדון.")
            elif focus == "academy":
                club.youth_academy = int(clamp(club.youth_academy + 1.2, 1, 99))
                lines.append("🌱 השקעה בנוער. הדור הבא יהיה טוב יותר.")
            else:
                lines.append("🌴 שבוע חופש.")
            return lines

        return lines

    # -- משחקים -----------------------------------------------------------

    def _youth_week(self, report: WeekReport) -> None:
        """שבוע בקבוצת הנוער — משחק מול קבוצת נוער אחרת, בלי טבלה ובלי קהל."""
        me = self.me
        club = self.my_club
        if self.week % 2 == 0:
            report.add("🏃 שבוע אימונים בקבוצת הנוער.")
            weekly_recovery(me, played=False, rng=self.rng)
            return
        if not me.available:
            report.add(f"🚑 פצוע — {me.injury_name} ({me.injury_weeks} שבועות).")
            return

        rivals = [c for c in self.clubs.values() if not club or c.cid != club.cid]
        rival = self.rng.choice(rivals)
        opp = clamp((club.youth_academy if club else 45) * 0.42 + 16
                    + self.rng.gauss(0, 5), 18, 72)
        edge = (me.effective - opp) / 10.0

        team_goals = _poisson(self.rng, clamp(1.3 + edge * 0.35, 0.15, 6))
        opp_goals = _poisson(self.rng, clamp(1.4 - edge * 0.30, 0.15, 6))
        goals = _poisson(self.rng, clamp(
            0.18 + max(0.0, edge) * 0.22 + me.attributes.get("shooting", 40) / 260.0, 0.02, 3))
        assists = _poisson(self.rng, clamp(
            0.12 + me.attributes.get("passing", 40) / 320.0, 0.02, 2))

        me.season.goals += goals
        me.season.assists += assists
        rating = round(clamp(6.0 + edge * 0.16 + goals * 1.0 + assists * 0.5
                             + self.rng.gauss(0, 0.5), 3, 10), 1)
        me.season.add_match(rating, 70)
        me.fitness = clamp(me.fitness - 16, 8, 100)
        me.morale = clamp(me.morale + (rating - 6.3) * 2, 5, 99)
        me.form = clamp(me.form * 0.84 + (rating - 6) * 14 + 9, 5, 99)
        if club:
            club.manager_trust = clamp(club.manager_trust + (rating - 6.4) * 0.8, 0, 100)

        outcome = "ניצחון" if team_goals > opp_goals else \
                  "תיקו" if team_goals == opp_goals else "הפסד"
        report.add(f"⚽ ליגת הנוער: {team_goals}:{opp_goals} מול {rival.name} נוער — {outcome}")
        detail = f"הציון שלך: {rating}"
        if goals:
            detail += f" | {goals} שערים"
        if assists:
            detail += f" | {assists} בישולים"
        report.add(f"👤 {detail}")

    def _simulate_week_matches(self, report: WeekReport, spectator: bool = False) -> None:
        """מדמה את כל המשחקים של השבוע.

        spectator=True: העולם ממשיך לרוץ, אבל אתה לא משחק במשחקים האלה.
        """
        if self.week in CUP_WEEKS:
            self._play_cup_round(report, spectator)
            return

        my_club = self.my_club
        for league in D.LEAGUES:
            lid = league["id"]
            rnd = self.league_round_for_week(lid, self.week)
            if rnd is None:
                continue
            for home_id, away_id in self.fixtures[lid][rnd]:
                home, away = self.clubs[home_id], self.clubs[away_id]
                involves_me = my_club is not None and my_club.cid in (home_id, away_id)
                is_mine = involves_me and not spectator
                result = self._simulate_one(home, away, is_mine, "ליגה")
                self._register_result(lid, result)
                if is_mine:
                    report.match = result
                    report.lines.extend(self._my_match_lines(result))
                elif involves_me and spectator:
                    report.add(f"📰 הקבוצה הבוגרת: {home.name} {result.score} {away.name}")

    def _simulate_one(self, home: Club, away: Club, is_mine: bool,
                      competition: str, neutral: bool = False) -> MatchResult:
        """מדמה משחק בודד, עם התחשבות בטקטיקה ובבחירת ההרכב שלי."""
        home_tac: Dict[str, Any] = {}
        away_tac: Dict[str, Any] = {}
        if is_mine:
            my_club = self.my_club
            mine = dict(self.tactics) if self.stage in ("manager", "coach") else {}
            if self.stage in ("academy", "player", "veteran") and self._selected():
                mine = {"forced": [self.me_id]}
            if my_club and my_club.cid == home.cid:
                home_tac = mine
            else:
                away_tac = mine
        result = simulate_match(home, away, self.players, self.rng,
                                home_tac, away_tac, competition, neutral)
        if self.stage in ("manager", "coach"):
            self.tactics["talk_boost"] = 0.0
        return result

    def _selected(self) -> bool:
        """האם המאמן מציב אותי בהרכב הפותח."""
        me = self.me
        club = self.my_club
        if not club or not me.available:
            return False
        rivals = [self.players[p] for p in club.squad
                  if p != self.me_id and p in self.players
                  and self.players[p].available
                  and self.players[p].position == me.position]
        my_score = me.effective + (club.manager_trust - 50) * 0.14
        if self.flag("captain"):
            my_score += 4
        best_rival = max((p.effective for p in rivals), default=0.0)
        return my_score >= best_rival - 1.0

    def _my_match_lines(self, result: MatchResult) -> List[str]:
        """שורות דוח למשחק שלי, כולל הביצוע האישי."""
        lines = list(result.commentary)
        me = self.me
        if self.stage in ("academy", "player", "veteran"):
            if me.pid in result.ratings:
                self.no_start_streak = 0
                rating = result.ratings[me.pid]
                goals = sum(1 for e in result.events
                            if e.kind == "goal" and e.player_id == me.pid)
                assists = sum(1 for e in result.events
                              if e.kind == "assist" and e.player_id == me.pid)
                detail = f"הציון שלך: {rating}"
                if goals:
                    detail += f" | {goals} שערים"
                if assists:
                    detail += f" | {assists} בישולים"
                if result.motm == me.pid:
                    detail += " | ⭐ מצטיין המשחק"
                lines.append(f"👤 {detail}")
            elif me.available:
                self.no_start_streak += 1
                if self.rng.random() < 0.4:
                    lines.extend(self._sub_appearance(result))
                else:
                    me.morale = clamp(me.morale - 2.5, 5, 99)
                    lines.append("🪑 ישבת 90 דקות על הספסל.")
            else:
                lines.append(f"🚑 פצוע — {me.injury_name} ({me.injury_weeks} שבועות).")
        else:
            club = self.my_club
            if club:
                outcome = result.result_for(club.cid)
                delta = {"W": 4.0, "D": -0.5, "L": -4.0}[outcome]
                club.board_confidence = clamp(club.board_confidence + delta, 0, 100)
                club.fan_support = clamp(club.fan_support + delta * 0.7, 0, 100)
        return lines

    def _sub_appearance(self, result: MatchResult) -> List[str]:
        """כניסה מהספסל."""
        me = self.me
        club = self.my_club
        minutes = self.rng.randint(8, 32)
        rating = round(clamp(5.9 + self.rng.gauss(0.25, 0.5) +
                             (me.effective - 60) * 0.012, 3.0, 10.0), 1)
        scored = self.rng.random() < 0.06 * (me.attributes.get("shooting", 40) / 55.0)
        lines = []
        if scored and club:
            me.season.goals += 1
            rating = round(min(10.0, rating + 1.2), 1)
            minute = 90 - self.rng.randint(1, max(1, minutes - 1))
            result.events.append(MatchEvent(minute, "goal", club.cid, me.pid,
                                            f"⚽ {minute}' {me.name}"))
            if club.cid == result.home_id:
                result.home_goals += 1
            else:
                result.away_goals += 1
            # התוצאה השתנתה — הפרשנות צריכה להיכתב מחדש
            result.commentary = build_commentary(
                result, self.clubs[result.home_id], self.clubs[result.away_id],
                self.players, self.rng)
            lines.append("⚽ נכנסת מהספסל וכבשת!")
        me.season.add_match(rating, minutes)
        result.ratings[me.pid] = rating
        me.fitness = clamp(me.fitness - minutes * 0.12, 8, 100)
        me.morale = clamp(me.morale + (rating - 6.2), 5, 99)
        lines.append(f"🔁 נכנסת בדקה {90 - minutes} — {minutes} דקות, ציון {rating}.")
        return lines

    def _register_result(self, league_id: str, result: MatchResult) -> None:
        table = self.tables.get(league_id)
        if not table:
            return
        table[result.home_id].register(result.home_goals, result.away_goals)
        table[result.away_id].register(result.away_goals, result.home_goals)

    def _play_cup_round(self, report: WeekReport, spectator: bool = False) -> None:
        """מחזור גביע נוקאאוט."""
        teams = self.cup.get("teams", [])
        if not teams or self.cup.get("winner"):
            report.add("🏆 הגביע כבר הוכרע — שבוע חופשי.")
            self._idle_week(report)
            return
        round_name = CUP_WEEKS[self.week]
        self.cup["round"] = round_name
        winners: List[str] = []
        my_club = self.my_club
        neutral = round_name == "גמר הגביע"
        for i in range(0, len(teams) - 1, 2):
            home, away = self.clubs[teams[i]], self.clubs[teams[i + 1]]
            involves_me = my_club is not None and my_club.cid in (home.cid, away.cid)
            is_mine = involves_me and not spectator
            result = self._simulate_one(home, away, is_mine, round_name, neutral)
            if result.home_goals == result.away_goals:
                # פנדלים
                pick = home.cid if self.rng.random() < 0.5 else away.cid
                winners.append(pick)
                text = f"{home.name} {result.score} {away.name} (פנדלים: " \
                       f"{self.clubs[pick].name})"
            else:
                winner = result.home_id if result.home_goals > result.away_goals \
                    else result.away_id
                winners.append(winner)
                text = f"{home.name} {result.score} {away.name}"
            self.cup.setdefault("log", []).append(f"{round_name}: {text}")
            if is_mine:
                report.match = result
                report.add(f"🏆 {round_name}")
                report.lines.extend(self._my_match_lines(result))
            elif involves_me and spectator:
                report.add(f"📰 הקבוצה הבוגרת בגביע: {home.name} {result.score} {away.name}")
        self.cup["teams"] = winners
        if len(winners) == 1:
            self.cup["winner"] = winners[0]
            champ = self.clubs[winners[0]]
            report.add(f"🏆 {champ.name} זוכים בגביע המדינה!")
            if my_club and my_club.cid == winners[0]:
                self.record_honour("גביע המדינה")
        if not spectator and my_club and my_club.cid not in winners:
            self._idle_week(report)

    def _idle_week(self, report: WeekReport) -> None:
        """שבוע בלי משחק."""
        me = self.me
        weekly_recovery(me, played=False, rng=self.rng)

    def _weekly_income(self, report: WeekReport) -> None:
        """שכר שבועי לפי שלב הקריירה."""
        me = self.me
        if self.stage == "youth":
            pass                      # בגיל הזה עוד לא משלמים לך
        elif self.stage in ("academy", "player", "veteran"):
            self.earn_money(me.contract.wage)
        elif self.stage in ("coach", "manager", "director"):
            club = self.my_club
            base = 4000 if self.stage == "coach" else 12000
            if club:
                base += int(club.reputation * (60 if self.stage == "coach" else 260))
            self.earn_money(base)
        weekly_recovery(me, played=me.pid in (report.match.ratings if report.match else {}),
                        rng=self.rng)

    # ==================================================================
    # אירועי עלילה
    # ==================================================================

    def _arm_event(self, event: ST.StoryEvent) -> bool:
        """מכין אירוע להצגה. אם הטקסט לא ניתן לבנייה — מוותרים עליו."""
        try:
            body = event.body(self)
        except Exception:
            return False
        if not body:
            return False
        self.pending_event_id = event.eid
        self.pending_event_body = body
        return True

    def pending_event(self) -> Optional[ST.StoryEvent]:
        if not self.pending_event_id:
            return None
        event = ST.find_event(self.pending_event_id)
        if event is None:
            self.pending_event_id = None
            self.pending_event_body = None
        return event

    def pending_event_text(self) -> str:
        """טקסט האירוע כפי שנבנה ברגע שהוא נורה."""
        if self.pending_event_body:
            return self.pending_event_body
        event = self.pending_event()
        if not event:
            return ""
        try:
            return event.body(self)
        except Exception:
            return ""

    def resolve_event(self, choice_index: int) -> str:
        """מבצע בחירה באירוע הממתין ומחזיר את התוצאה."""
        event = self.pending_event()
        if not event:
            return ""
        choice = event.choices[max(0, min(choice_index, len(event.choices) - 1))]
        outcome = choice.apply(self) or ""
        if event.eid not in self.fired_events:
            self.fired_events.append(event.eid)
        self.pending_event_id = None
        self.pending_event_body = None
        self.log(f"{event.title} — {choice.label}")
        return outcome

    # ==================================================================
    # שאילתות שהעלילה משתמשת בהן
    # ==================================================================

    def minutes_share(self) -> float:
        played_weeks = max(1, self.week - 1)
        return clamp(self.me.season.minutes / (played_weeks * 90.0), 0.0, 1.0)

    def weeks_without_start(self) -> int:
        return self.no_start_streak

    def league_position(self) -> int:
        club = self.my_club
        if not club:
            return 0
        table = self.standings(club.league_id)
        for idx, row in enumerate(table, start=1):
            if row.club_id == club.cid:
                return idx
        return 0

    def standings(self, league_id: str) -> List[TableRow]:
        rows = list(self.tables.get(league_id, {}).values())
        rows.sort(key=lambda r: (-r.points, -r.gd, -r.gf))
        return rows

    def youth_academy_suitor(self) -> Optional[Club]:
        """מועדון עם מחלקת נוער חזקה שמעוניין בי."""
        club = self.my_club
        if not club:
            return None
        pool = [c for c in self.clubs.values()
                if c.cid != club.cid and c.youth_academy > club.youth_academy + 12
                and c.league_id != "euro"]
        if not pool:
            return None
        return max(pool, key=lambda c: c.youth_academy)

    def join_big_academy(self) -> str:
        target = self.youth_academy_suitor()
        if not target:
            return "ההזדמנות נסגרה."
        self.transfer_me(target.cid, wage=0, years=0)
        target.manager_trust = 40.0
        self.me.morale = clamp(self.me.morale - 4, 5, 99)
        self.me.potential = int(clamp(self.me.potential + self.rng.randint(1, 5), 40, 96))
        self.set_flag("big_academy", True)
        return (f"עברת ל{target.name}. מתקנים שלא הכרת, "
                f"וילדים שכולם היו הכי טובים במועדון שלהם.")

    def show_off(self) -> str:
        if self.rng.random() < 0.5:
            self.me.reputation = clamp(self.me.reputation + 6, 1, 99)
            self.me.growth["dribbling"] = self.me.growth.get("dribbling", 0.0) + 1.0
            self.set_flag("scouted_wow", True)
            return "הורדת שניים בתנועה אחת והנחת כדור בזווית. הוא הפסיק לכתוב והסתכל."
        club = self.my_club
        if club:
            club.manager_trust = clamp(club.manager_trust - 8, 0, 100)
        self.me.morale = clamp(self.me.morale - 6, 5, 99)
        return "ניסית סובב מיותר באמצע המגרש, איבדת כדור, וספגתם. הצופה כבר לא הסתכל."

    def ask_why(self) -> str:
        club = self.my_club
        trust = club.manager_trust if club else 50.0
        if trust >= 45 or self.rng.random() < 0.4:
            if club:
                club.manager_trust = clamp(club.manager_trust + 6, 0, 100)
            self.me.growth["mental"] = self.me.growth.get("mental", 0.0) + 1.2
            return ('הוא ענה בכנות: "אתה טוב עם הכדור וגרוע בלעדיו." '
                    'זו הייתה הביקורת הכי שימושית שקיבלת.')
        self.me.morale = clamp(self.me.morale - 7, 5, 99)
        return 'הוא אמר "יש עוד טורנירים" והמשיך לסדר קונוסים. לא קיבלת תשובה.'

    def loan_target_name(self) -> str:
        options = [c for c in self.clubs.values() if c.league_id == "national"]
        return self.rng.choice(options).name if options else "מועדון מהליגה הלאומית"

    def big_club_suitor(self) -> Optional[Club]:
        """מועדון גדול שמתעניין בי — לפי מוניטין."""
        me = self.me
        candidates = [c for c in self.clubs.values()
                      if c.cid != me.club_id and c.reputation > (me.reputation + 12)
                      and c.reputation < (me.reputation + 45)]
        if not candidates:
            return None
        return max(candidates, key=lambda c: c.reputation)

    def manager_suitor(self) -> Optional[Club]:
        club = self.my_club
        if not club:
            return None
        candidates = [c for c in self.clubs.values()
                      if c.reputation > club.reputation + 10 and c.cid != club.cid]
        if not candidates or club.board_confidence < 55:
            return None
        return min(candidates, key=lambda c: c.reputation)

    def manager_job_offer_name(self) -> str:
        club = self._manager_job_target()
        return club.name if club else "מועדון מהליגה"

    def _manager_job_target(self) -> Optional[Club]:
        pool = [c for c in self.clubs.values()
                if c.league_id in ("top", "national")
                and c.reputation <= 30 + self.me.coaching * 0.7]
        if not pool:
            return None
        return max(pool, key=lambda c: c.reputation)

    def squad_star(self) -> Optional[Player]:
        club = self.my_club
        if not club:
            return None
        squad = [self.players[p] for p in club.squad if p in self.players]
        squad = [p for p in squad if p.pid != self.me_id]
        return max(squad, key=lambda p: p.overall) if squad else None

    def rival_youngster(self) -> Optional[Player]:
        club = self.my_club
        if not club:
            return None
        rivals = [self.players[p] for p in club.squad
                  if p in self.players and p != self.me_id
                  and self.players[p].position == self.me.position
                  and self.players[p].age <= 21]
        return max(rivals, key=lambda p: p.potential) if rivals else None

    def retirement_ready(self) -> bool:
        return (retirement_pressure(self.me) > 0.45
                and not self.flag("retired_announced")
                and self.week >= 18)

    def last_club_name(self) -> str:
        club = self.clubs.get(self.last_club_id or "")
        return club.name if club else "המועדון שלך"

    def first_club_name(self) -> str:
        club = self.clubs.get(self.first_club_id or "")
        return club.name if club else "מועדון הילדות"

    def renewal_offer(self) -> int:
        club = self.my_club
        me = self.me
        base = me.contract.wage
        target = wage_for_overall(me.overall)
        target = int(target * (0.85 + me.reputation / 200.0))
        if club:
            target = int(min(target, club.wage_budget * 0.30))
        return int(max(base * 0.9, target))

    def career_options_summary(self) -> str:
        me = self.me
        return (f"תעודות אימון: {me.badges}/4 · ידע אימון {int(me.coaching)}\n"
                f"כריזמה תקשורתית: {int(me.media_skill)} · ראש עסקי: {int(me.business)}\n"
                f"מוניטין: {int(me.reputation)} · בחשבון: ₪{self.money:,}")

    # ==================================================================
    # אפקטים של אירועים
    # ==================================================================

    def go_on_loan(self) -> str:
        target = min([c for c in self.clubs.values() if c.league_id == "national"],
                     key=lambda c: -c.reputation)
        self.transfer_me(target.cid, wage=int(self.me.contract.wage * 0.8),
                         years=1, loan=True)
        self.me.reputation = clamp(self.me.reputation - 2, 1, 99)
        return (f"יצאת בהשאלה ל{target.name}. שם תשחק כל שבוע — "
                f"וזה בדיוק מה שהקריירה שלך צריכה.")

    def confront_manager(self) -> str:
        club = self.my_club
        roll = self.rng.random() + (self.me.effective - 62) * 0.012
        if roll > 0.55:
            club.manager_trust = clamp(club.manager_trust + 14, 0, 100)
            self.me.morale = clamp(self.me.morale + 6, 5, 99)
            return ("צעקת. הוא צעק חזרה. ואז אמר: \"תהיה מוכן ביום ראשון.\" "
                    "אתה בהרכב.")
        club.manager_trust = clamp(club.manager_trust - 18, 0, 100)
        self.me.morale = clamp(self.me.morale - 8, 5, 99)
        self.set_flag("frozen_out", True)
        return ("הוא הקשיב בשקט ואז אמר: \"תודה שבאת.\" "
                "מאז אתה אפילו לא בסגל.")

    def deny_scandal(self) -> str:
        if self.rng.random() < 0.45:
            self.me.reputation = clamp(self.me.reputation - 12, 1, 99)
            club = self.my_club
            if club:
                club.manager_trust = clamp(club.manager_trust - 12, 0, 100)
                club.fan_support = clamp(club.fan_support - 10, 0, 100)
            self.me.morale = clamp(self.me.morale - 10, 5, 99)
            return ("יומיים אחרי ההכחשה פורסם סרטון נוסף. "
                    "עכשיו זה לא הבילוי — זה השקר.")
        self.me.reputation = clamp(self.me.reputation + 1, 1, 99)
        return "הכחשת בתוקף והסיפור דעך. הפעם יצאת מזה."

    def national_debut(self) -> str:
        self.caps += 1
        self.set_flag("national_debut", True)
        self.me.reputation = clamp(self.me.reputation + 9, 1, 99)
        self.me.morale = clamp(self.me.morale + 8, 5, 99)
        self.record_honour("בכורה בנבחרת")
        if self.rng.random() < 0.25:
            self.intl_goals += 1
            return "נכנסת בדקה 71 וכבשת בנגיעה הראשונה שלך בנבחרת. אין דבר כזה."
        return "המנון, 90 דקות, וחולצה ממוסגרת אצל ההורים."

    def become_captain(self) -> str:
        self.set_flag("captain", True)
        club = self.my_club
        if club:
            club.manager_trust = clamp(club.manager_trust + 10, 0, 100)
            club.fan_support = clamp(club.fan_support + 8, 0, 100)
        self.me.morale = clamp(self.me.morale + 6, 5, 99)
        self.me.reputation = clamp(self.me.reputation + 4, 1, 99)
        if "leader" not in self.me.traits:
            self.me.traits.append("leader")
        self.me.coaching = clamp(self.me.coaching + 6, 0, 100)
        return "אתה הקפטן. עכשיו כל הפסד הוא גם שלך."

    def rush_rehab(self) -> str:
        if self.rng.random() < 0.42:
            self.me.injury_weeks = max(1, self.me.injury_weeks // 2)
            self.me.morale = clamp(self.me.morale + 5, 5, 99)
            club = self.my_club
            if club:
                club.manager_trust = clamp(club.manager_trust + 8, 0, 100)
            return "חזרת חודש לפני הזמן והחזקת. המאמן לא שכח את זה."
        extra = self.rng.randint(6, 14)
        self.me.injury_weeks += extra
        self.me.attributes["pace"] = int(clamp(self.me.attributes.get("pace", 50) - 3, 10, 97))
        self.me.morale = clamp(self.me.morale - 12, 5, 99)
        return (f"נכנסת מוקדם מדי. הפציעה חזרה, ועוד {extra} שבועות. "
                f"המהירות שלך לא תחזור לגמרי.")

    def study_during_injury(self) -> str:
        self.me.coaching = clamp(self.me.coaching + 5, 0, 100)
        new_badges = min(4, int(self.me.coaching // 22))
        extra = ""
        if new_badges > self.me.badges:
            self.me.badges = new_badges
            extra = f" השלמת תעודת אימון רמה {self.me.badges}."
        return ("במקום להסתובב במסדרונות, ישבת עם הצוות המקצועי על ניתוחי משחק." + extra)

    def sign_renewal(self, multiplier: float) -> str:
        offer = int(self.renewal_offer() * multiplier)
        self.me.contract = Contract(wage=offer, years_left=3)
        club = self.my_club
        if club:
            club.manager_trust = clamp(club.manager_trust + 6, 0, 100)
            club.fan_support = clamp(club.fan_support + 5, 0, 100)
        self.me.morale = clamp(self.me.morale + 5, 5, 99)
        return f"חתמת לשלוש עונות על ₪{offer:,} לשבוע."

    def demand_raise(self) -> str:
        club = self.my_club
        leverage = (self.me.reputation + self.me.overall) / 2 - 50
        if self.rng.random() * 100 < 45 + leverage:
            return self.sign_renewal(1.45)
        if club:
            club.manager_trust = clamp(club.manager_trust - 10, 0, 100)
        self.set_flag("contract_stalled", True)
        self.me.morale = clamp(self.me.morale - 6, 5, 99)
        return ("ההנהלה משכה את ההצעה מהשולחן. "
                "עכשיו אתה משחק על החוזה שלך כל שבוע.")

    def join_revolt(self) -> str:
        club = self.my_club
        if not club:
            return ""
        if self.rng.random() < 0.5:
            club.manager_name = self.rng.choice(D.MANAGER_NAMES)
            club.manager_trust = 50.0
            return (f"המאמן הודח. {club.manager_name} נכנס במקומו — "
                    f"ואתה מתחיל מאפס מול מישהו שיודע בדיוק מי הדליף.")
        club.manager_trust = clamp(club.manager_trust - 25, 0, 100)
        self.set_flag("frozen_out", True)
        return "המאמן שרד. אתה הוצאת מהסגל עד סוף העונה."

    def mentor_youngster(self) -> str:
        kid = self.rival_youngster()
        self.me.coaching = clamp(self.me.coaching + 4, 0, 100)
        club = self.my_club
        if club:
            club.manager_trust = clamp(club.manager_trust + 6, 0, 100)
        if kid:
            kid.potential = int(clamp(kid.potential + 2, 40, 95))
            self.set_flag("protege", kid.pid)
            return (f"לקחת את {kid.name} תחת חסותך. הוא ייקח את המקום שלך — "
                    f"אבל הוא ייקח אותו כשאתה תלמד אותו איך.")
        return "התחלת להעביר ידע לצעירים."

    def change_position(self) -> str:
        me = self.me
        moves = {"ST": "AM", "LW": "AM", "RW": "AM", "AM": "CM", "CM": "DM",
                 "DM": "CB", "LB": "CB", "RB": "CB", "CB": "CB", "GK": "GK"}
        new_pos = moves.get(me.position, "CM")
        old = me.position_he
        me.position = new_pos
        me.attributes["mental"] = int(clamp(me.attributes.get("mental", 50) + 4, 10, 97))
        return (f"עברת מ{old} ל{me.position_he}. פחות ריצה, יותר ראש — "
                f"ועוד כמה שנים בקריירה.")

    def painkillers(self) -> str:
        if self.rng.random() < 0.55:
            self.me.form = clamp(self.me.form + 12, 5, 99)
            return "הזריקות עובדות. שיחקת עונה שלמה כאילו אתה בן 26."
        weeks = self.rng.randint(8, 16)
        self.me.injury_weeks = weeks
        self.me.attributes["physical"] = int(
            clamp(self.me.attributes.get("physical", 50) - 4, 10, 97))
        return f"הגוף אמר די. {weeks} שבועות, והפעם זה כואב גם כשאתה יושב."

    def announce_retirement(self) -> str:
        self.set_flag("retired_announced", True)
        self.me.reputation = clamp(self.me.reputation + 4, 1, 99)
        self.log("הודעת על פרישה בסוף העונה.")
        return ("עמדת מול המצלמות ואמרת את המשפט. "
                "בסוף העונה אתה תולה את הנעליים.")

    # -- מסלולים אחרי הפרישה ---------------------------------------------

    def start_coaching(self) -> str:
        if self.me.badges < 1:
            self.me.coaching = clamp(self.me.coaching + 8, 0, 100)
            return ("אין לך אפילו תעודה אחת. שלחו אותך לקורס מאמנים בסיסי — "
                    "תחזור לזה בעוד קצת.")
        club = self.clubs.get(self.last_club_id or self.first_club_id or "")
        if club is None:
            club = self.rng.choice(list(self.clubs.values()))
        self.stage = "coach"
        self.managed_club_id = club.cid
        self.me.club_id = None
        self.training_focus = "tactics"
        self.log(f"התחלת לאמן — עוזר מאמן ב{club.name}.")
        return (f"אתה עוזר מאמן ב{club.name}. שעה לפני כולם במגרש, "
                f"שעתיים אחרי כולם בחדר וידאו.")

    def start_punditry(self) -> str:
        self.stage = "pundit"
        self.managed_club_id = None
        self.me.club_id = None
        self.training_focus = "studio"
        bonus = int(200_000 + self.me.reputation * 12_000)
        self.earn_money(bonus)
        self.log("חתמת בערוץ הספורט כפרשן.")
        return (f"חתמת כפרשן. מקדמה של ₪{bonus:,}, "
                f"ואור אדום שנדלק בדיוק כשאתה באמצע משפט.")

    def start_agency(self) -> str:
        self.stage = "agent"
        self.managed_club_id = None
        self.me.club_id = None
        self.training_focus = "clients"
        self.flags["clients"] = 1
        self.log("פתחת סוכנות שחקנים.")
        return ("פתחת משרד עם שולחן אחד ולקוח אחד — "
                "ילד בן 16 שאף אחד עוד לא שמע עליו.")

    def take_manager_job(self) -> str:
        club = self._manager_job_target()
        if not club:
            return "לא נמצא מועדון מתאים כרגע."
        self.stage = "manager"
        self.managed_club_id = club.cid
        club.manager_name = self.me.name
        club.board_confidence = 55.0
        self.training_focus = "tactics"
        self.tactics["formation"] = club.formation
        self.log(f"מונית למנג'ר של {club.name}.")
        return (f"אתה המנג'ר של {club.name}. "
                f"הציפייה: {club.season_expectation}. הסבלנות: קצרה.")

    def move_manager_job(self) -> str:
        target = self.manager_suitor()
        if not target:
            return "ההצעה נעלמה."
        old = self.my_club
        if old:
            old.manager_name = self.rng.choice(D.MANAGER_NAMES)
            old.board_confidence = 55.0
        self.managed_club_id = target.cid
        target.manager_name = self.me.name
        target.board_confidence = 60.0
        self.me.reputation = clamp(self.me.reputation + 6, 1, 99)
        self.log(f"עברת לאמן את {target.name}.")
        return f"אתה המנג'ר של {target.name}. ליגה אחרת, לחץ אחר."

    def board(self, delta: float) -> str:
        club = self.my_club
        if club:
            club.board_confidence = clamp(club.board_confidence + delta, 0, 100)
        return ""

    def demand_budget(self) -> str:
        club = self.my_club
        if not club:
            return ""
        if club.board_confidence > 55:
            club.budget += 6.0
            club.board_confidence = clamp(club.board_confidence - 4, 0, 100)
            return "קיבלת ₪6,000,000 להעברות. עכשיו זה עליך."
        club.board_confidence = clamp(club.board_confidence - 12, 0, 100)
        return "היו\"ר צחק. \"תעשה קודם תוצאות.\" אמון ההנהלה ירד."

    def sell_star(self) -> str:
        star = self.squad_star()
        club = self.my_club
        if not star or not club:
            return ""
        fee = star.value
        club.budget += fee / 1_000_000
        club.squad.remove(star.pid)
        buyer = max([c for c in self.clubs.values() if c.cid != club.cid],
                    key=lambda c: c.reputation)
        buyer.squad.append(star.pid)
        star.club_id = buyer.cid
        club.board_confidence = clamp(club.board_confidence + 5, 0, 100)
        club.fan_support = clamp(club.fan_support - 12, 0, 100)
        return f"מכרת את {star.name} ל{buyer.name} תמורת ₪{fee:,}. האוהדים בטראומה."

    def keep_star(self) -> str:
        star = self.squad_star()
        club = self.my_club
        if not star or not club:
            return ""
        star.morale = clamp(star.morale - 25, 5, 99)
        club.fan_support = clamp(club.fan_support + 8, 0, 100)
        self.set_flag("unhappy_star", star.pid)
        return f"{star.name} נשאר — ומצב הרוח שלו ייראה על המגרש."

    def promote_star(self) -> str:
        star = self.squad_star()
        club = self.my_club
        if not star or not club:
            return ""
        cost = int(star.contract.wage * 0.6)
        star.contract.wage += cost
        star.morale = clamp(star.morale + 20, 5, 99)
        club.wage_budget = int(club.wage_budget)
        club.budget -= cost * 40 / 1_000_000
        return (f"נתת ל{star.name} את הסרט ותוספת של ₪{cost:,} לשבוע. "
                f"הוא נשאר, והשכר מכביד על התקציב.")

    def promote_youth(self) -> str:
        club = self.my_club
        if not club:
            return ""
        kid = generate_player(self.rng, club, self.rng.choice(D.POSITIONS), age=17,
                              quality=int(clamp(club.youth_academy * 0.5 + 20, 35, 60)))
        kid.potential = int(clamp(kid.overall + self.rng.randint(10, 32), 60, 93))
        self.players[kid.pid] = kid
        club.squad.append(kid.pid)
        self.set_flag("wonderkid", kid.pid)
        return (f"העלית את {kid.name} ({kid.age}) לסגל. "
                f"פוטנציאל מוערך: {kid.potential}. עכשיו תתפלל.")

    def radical_change(self) -> str:
        club = self.my_club
        if not club:
            return ""
        self.tactics["formation"] = self.rng.choice(list(D.FORMATIONS.keys()))
        self.tactics["mentality"] = self.rng.choice(list(MENTALITIES.keys()))
        if self.rng.random() < 0.5:
            club.board_confidence = clamp(club.board_confidence + 14, 0, 100)
            for pid in club.squad:
                p = self.players.get(pid)
                if p:
                    p.morale = clamp(p.morale + 10, 5, 99)
            return (f"שינית הכל למערך {self.tactics['formation']} "
                    f"ובמנטליות {MENTALITIES[self.tactics['mentality']][0]}. "
                    f"הקבוצה נדלקה.")
        club.board_confidence = clamp(club.board_confidence - 8, 0, 100)
        return "שינית הכל והקבוצה נראתה אבודה. לפעמים תזוזה היא הפסד."

    def resign(self) -> str:
        club = self.my_club
        if club:
            club.manager_name = self.rng.choice(D.MANAGER_NAMES)
            club.board_confidence = 55.0
        self.managed_club_id = None
        self.stage = "coach"
        self.log("התפטרת מתפקיד המנג'ר.")
        return ("התפטרת לפני שהדיחו אותך. בעולם הזה זה נחשב ניצחון קטן. "
                "עכשיו אתה מחכה לטלפון הבא.")

    def become_director(self) -> str:
        club = self.my_club
        if not club:
            return ""
        self.stage = "director"
        club.manager_name = self.rng.choice(D.MANAGER_NAMES)
        self.training_focus = "squad"
        self.log(f"מונית למנהל ספורטיבי ב{club.name}.")
        return f"אתה מנהל ספורטיבי ב{club.name}. עכשיו אתה זה שמפטר מאמנים."

    def buy_club(self) -> str:
        club = self.clubs.get(self.first_club_id or "")
        if not club:
            return ""
        self.spend_money(4_000_000)
        self.stage = "owner"
        self.managed_club_id = club.cid
        club.budget += 2.0
        self.set_flag("owner_of", club.cid)
        self.log(f"רכשת את {club.name}.")
        return (f"קנית את {club.name}. הילד שהתאמן פה בגיל 12 "
                f"מחזיק עכשיו את המפתחות.")

    def transfer_me(self, club_id: str, wage: int, years: int,
                    loan: bool = False) -> str:
        """מעביר את השחקן האנושי למועדון אחר."""
        me = self.me
        old = self.clubs.get(me.club_id or "")
        if old and me.pid in old.squad:
            old.squad.remove(me.pid)
        new = self.clubs[club_id]
        new.squad.append(me.pid)
        me.club_id = club_id
        me.contract = Contract(wage=wage, years_left=years)
        new.manager_trust = 55.0 if not loan else 65.0
        self.last_club_id = club_id
        self.no_start_streak = 0
        self.log(f"{'הושאלת ל' if loan else 'עברת ל'}{new.name}.")
        return new.name

    # ==================================================================
    # סוף עונה
    # ==================================================================

    def end_season(self) -> List[str]:
        """סוגר עונה: תארים, פרסים, התפתחות, העברות, ומעבר שלב."""
        lines: List[str] = ["", "═" * 46, f"📅 סיכום עונת {self.year}/{self.year + 1}", "═" * 46]
        my_club = self.my_club

        # אליפויות
        for league in D.LEAGUES:
            lid = league["id"]
            table = self.standings(lid)
            if not table:
                continue
            champ = self.clubs[table[0].club_id]
            champ.trophies.append(f"{league['name']} {self.year}")
            lines.append(f"🥇 אלוף {league['name']}: {champ.name} ({table[0].points} נק')")
            if my_club and my_club.cid == champ.cid:
                self.record_honour(f"אליפות {league['name']}")
                lines.append("🎉 אתה אלוף!")

        cup_winner = self.cup.get("winner")
        if cup_winner:
            lines.append(f"🏆 זוכת גביע המדינה: {self.clubs[cup_winner].name}")

        # פרסים אישיים
        lines.extend(self._season_awards())

        # סיכום אישי
        lines.extend(self._personal_summary())

        # עלייה וירידת ליגה
        lines.extend(self._promotion_relegation())

        # התפתחות שחקנים והזדקנות
        self._develop_everyone()

        # פרישות של שחקני מחשב + נוער חדש
        self._process_retirements()

        # שוק ההעברות
        lines.extend(self._transfer_window())

        # מעבר שלב קריירה
        lines.extend(self._advance_career_stage())

        self.history.append({
            "year": self.year, "stage": self.stage,
            "club": my_club.name if my_club else "-",
            "apps": self.me.career.apps, "goals": self.me.career.goals,
        })

        self.year += 1
        self.start_season()
        lines.append("")
        lines.append(f"🔄 עונת {self.year}/{self.year + 1} מתחילה.")
        return lines

    def _season_awards(self) -> List[str]:
        lines = []
        league_id = self.my_league or "top"
        club_ids = {c.cid for c in self.clubs.values() if c.league_id == league_id}
        squad = [p for p in self.players.values()
                 if p.club_id in club_ids and p.season.apps > 0
                 and not (self.stage == "youth" and p.pid == self.me_id)]
        if not squad:
            return lines
        scorer = max(squad, key=lambda p: (p.season.goals, p.season.assists))
        lines.append(f"👑 מלך השערים: {scorer.name} — {scorer.season.goals} שערים")
        best = max(squad, key=lambda p: (p.season.avg_rating, p.season.apps))
        lines.append(f"⭐ שחקן העונה: {best.name} (ציון {best.season.avg_rating})")
        if scorer.pid == self.me_id:
            self.record_honour("מלך השערים")
        if best.pid == self.me_id:
            self.record_honour("שחקן העונה")
        return lines

    def _personal_summary(self) -> List[str]:
        me = self.me
        lines = ["", "— העונה שלך —"]
        if self.stage in ("youth", "academy", "player", "veteran"):
            season = me.season
            lines.append(f"משחקים: {season.apps} | שערים: {season.goals} | "
                         f"בישולים: {season.assists} | ציון ממוצע: {season.avg_rating}")
            lines.append(f"דירוג: {me.overall} (פוטנציאל {me.potential}) | "
                         f"מוניטין: {int(me.reputation)} | שווי: ₪{me.value:,}")
        else:
            club = self.my_club
            if club:
                pos = self.league_position()
                lines.append(f"{club.name} — מקום {pos} ב{self._league_name(club.league_id)}")
                lines.append(f"אמון ההנהלה: {int(club.board_confidence)}% | "
                             f"אהדת הקהל: {int(club.fan_support)}%")
        lines.append(f"בחשבון: ₪{self.money:,}")
        return lines

    def _league_name(self, league_id: str) -> str:
        for league in D.LEAGUES:
            if league["id"] == league_id:
                return league["name"]
        return league_id

    def _promotion_relegation(self) -> List[str]:
        """שתי האחרונות בליגת העל יורדות, שתי הראשונות בלאומית עולות."""
        top_table = self.standings("top")
        nat_table = self.standings("national")
        if len(top_table) < 4 or len(nat_table) < 4:
            return []
        relegated = [row.club_id for row in top_table[-3:]]
        promoted = [row.club_id for row in nat_table[:3]]
        for cid in relegated:
            self.clubs[cid].league_id = "national"
            self.clubs[cid].reputation = int(clamp(self.clubs[cid].reputation - 6, 5, 99))
        for cid in promoted:
            self.clubs[cid].league_id = "top"
            self.clubs[cid].reputation = int(clamp(self.clubs[cid].reputation + 6, 5, 99))
        lines = [f"⬇️ יורדות: {', '.join(self.clubs[c].name for c in relegated)}",
                 f"⬆️ עולות: {', '.join(self.clubs[c].name for c in promoted)}"]
        my_club = self.my_club
        if my_club and my_club.cid in relegated:
            lines.append("💔 ירדת ליגה. העונה הבאה תיראה אחרת לגמרי.")
            self.me.morale = clamp(self.me.morale - 12, 5, 99)
        if my_club and my_club.cid in promoted:
            lines.append("🎊 עלית ליגה!")
            self.record_honour("עלייה לליגת העל")
        return lines

    def _develop_everyone(self) -> None:
        for player in list(self.players.values()):
            if player.retired:
                # פורשים לא מתפתחים — אבל הגיל שלי ממשיך לרוץ
                if player.pid == self.me_id:
                    player.age += 1
                continue
            share = clamp(player.season.minutes / (SEASON_WEEKS * 90.0), 0, 1)
            end_of_season_development(player, self.rng, share)

    def _process_retirements(self) -> None:
        """שחקני מחשב פורשים, מועדונים מגדלים נוער חדש."""
        for player in list(self.players.values()):
            if player.pid == self.me_id or player.retired:
                continue
            if should_retire(player, self.rng):
                player.retired = True
                club = self.clubs.get(player.club_id or "")
                if club and player.pid in club.squad:
                    club.squad.remove(player.pid)
                player.club_id = None
        for club in self.clubs.values():
            while len(club.squad) < 20:
                kid = generate_player(self.rng, club, self.rng.choice(D.POSITIONS),
                                      age=self.rng.randint(16, 19))
                kid.potential = int(clamp(kid.overall + self.rng.randint(6, 28), 45, 94))
                self.players[kid.pid] = kid
                club.squad.append(kid.pid)

    def _transfer_window(self) -> List[str]:
        """חלון העברות: הצעות אליי, ומעברים בין קבוצות מחשב."""
        lines: List[str] = []
        me = self.me

        # מעברים בין קבוצות מחשב
        movers = [p for p in self.players.values()
                  if p.pid != self.me_id and not p.retired
                  and p.contract.years_left <= 0 and p.club_id]
        for player in movers[:40]:
            if self.rng.random() < 0.35:
                target = self.rng.choice(list(self.clubs.values()))
                old = self.clubs.get(player.club_id or "")
                if old and player.pid in old.squad and len(old.squad) > 16:
                    old.squad.remove(player.pid)
                    target.squad.append(player.pid)
                    player.club_id = target.cid
            player.contract.years_left = self.rng.randint(1, 4)

        # הצעה עבורי
        if self.stage in ("player", "veteran"):
            suitor = self._transfer_offer_for_me()
            if suitor:
                wage = int(max(me.contract.wage * 1.25,
                               min(suitor.wage_budget * 0.28,
                                   wage_for_overall(me.overall) *
                                   (0.9 + me.reputation / 220.0))))
                self.flags["pending_offer"] = {"club": suitor.cid, "wage": wage,
                                               "years": 4}
                lines.append("")
                lines.append(f"📨 הצעה על השולחן: {suitor.name} — "
                             f"₪{wage:,} לשבוע. (בתפריט: 'הצעות')")
        return lines

    def _transfer_offer_for_me(self) -> Optional[Club]:
        """מועדון שמוכן להציע לי חוזה — לפי הרמה שלי בפועל."""
        me = self.me
        # תקרת המועדונים שאליהם אפשר לעבור נגזרת מהדירוג, מהמוניטין ומהעונה
        ceiling = (me.overall + 8 + (me.reputation - 40) * 0.25
                   + (me.season.avg_rating - 6.5) * 8)
        if self.flag("open_to_europe"):
            ceiling += 6
        if self.flag("wants_transfer") or self.flag("free_agent_soon"):
            ceiling += 4
        pool = [c for c in self.clubs.values()
                if c.cid != me.club_id and ceiling - 28 <= c.reputation <= ceiling]
        if not pool or self.rng.random() > 0.55:
            return None
        return max(pool, key=lambda c: c.reputation)

    def accept_offer(self) -> str:
        """מקבל את הצעת ההעברה הפתוחה."""
        offer = self.flag("pending_offer")
        if not offer:
            return "אין הצעה פתוחה."
        club = self.clubs[offer["club"]]
        self.transfer_me(club.cid, offer["wage"], offer["years"])
        self.flags.pop("pending_offer", None)
        self.flags.pop("wants_transfer", None)
        self.me.morale = clamp(self.me.morale + 8, 5, 99)
        return f"חתמת ב{club.name} על ₪{offer['wage']:,} לשבוע."

    def reject_offer(self) -> str:
        offer = self.flags.pop("pending_offer", None)
        if not offer:
            return "אין הצעה פתוחה."
        club = self.my_club
        if club:
            club.fan_support = clamp(club.fan_support + 6, 0, 100)
            club.manager_trust = clamp(club.manager_trust + 5, 0, 100)
        return "דחית את ההצעה ונשארת. במועדון שמעו על זה."

    def _advance_career_stage(self) -> List[str]:
        """מעבר בין שלבי הקריירה בסוף עונה."""
        lines: List[str] = []
        me = self.me
        club = self.my_club

        if self.stage == "youth":
            if me.age >= 16:
                self.stage = "academy"
                me.contract = Contract(
                    wage=max(1800, wage_for_overall(me.overall) // 3), years_left=2)
                lines.append("📈 עלית לקבוצת הנוער הבוגרת — ועם החוזה הראשון שלך.")
        elif self.stage == "academy":
            if me.age >= 18 or (club and club.manager_trust >= 55):
                self.stage = "player"
                lines.append("📈 אתה כבר לא נער — אתה שחקן בסגל הבוגרים.")
        elif self.stage == "player" and me.age >= 31:
            self.stage = "veteran"
            lines.append("🧓 עברת לשלב הוותיקים. הניסיון מחליף את הרגליים.")
        elif self.stage == "veteran":
            forced = me.age >= 40 or me.overall < 45
            if self.flag("retired_announced") or forced:
                self.stage = "retired"
                me.retired = True
                if me.club_id:
                    old = self.clubs.get(me.club_id)
                    if old and me.pid in old.squad:
                        old.squad.remove(me.pid)
                    self.last_club_id = me.club_id
                    me.club_id = None
                lines.append("")
                lines.append("🎬 תלית את הנעליים.")
                lines.append(f"סה\"כ: {me.career.apps} משחקים, {me.career.goals} שערים, "
                             f"{me.career.assists} בישולים, {len(self.honours)} הישגים.")
                self.set_flag("retired_announced", True)

        if self.stage in ("coach", "manager", "director", "pundit", "agent", "owner"):
            if me.age >= 68:
                self.stage = "legend"
                self.game_over = True
                lines.append("")
                lines.append("🕰️ הגיע הזמן לרדת מהבמה. הקריירה הושלמה.")

        # פיטורים
        if self.stage == "manager" and club and club.board_confidence <= 12:
            club.manager_name = self.rng.choice(D.MANAGER_NAMES)
            self.managed_club_id = None
            self.stage = "coach"
            lines.append("📉 פוטרת. ההנהלה איבדה סבלנות.")
        return lines

    # ==================================================================
    # שמירה וטעינה
    # ==================================================================

    def to_dict(self) -> dict:
        return {
            "seed": self.seed,
            "clubs": {cid: c.to_dict() for cid, c in self.clubs.items()},
            "players": {pid: p.to_dict() for pid, p in self.players.items()},
            "me_id": self.me_id, "stage": self.stage, "year": self.year,
            "week": self.week,
            "fixtures": {lid: [[list(pair) for pair in rnd] for rnd in rounds]
                         for lid, rounds in self.fixtures.items()},
            "tables": {lid: {cid: row.to_dict() for cid, row in rows.items()}
                       for lid, rows in self.tables.items()},
            "cup": self.cup, "money": self.money, "flags": self.flags,
            "honours": self.honours, "news": self.news[-60:],
            "fired_events": self.fired_events,
            "pending_event_id": self.pending_event_id,
            "pending_event_body": self.pending_event_body,
            "managed_club_id": self.managed_club_id, "tactics": self.tactics,
            "training_focus": self.training_focus, "intensity": self.intensity,
            "first_club_id": self.first_club_id, "last_club_id": self.last_club_id,
            "history": self.history, "caps": self.caps, "intl_goals": self.intl_goals,
            "no_start_streak": self.no_start_streak, "game_over": self.game_over,
            "rng_state": _encode_rng(self.rng),
        }

    @classmethod
    def from_dict(cls, raw: dict) -> "GameState":
        state = cls()
        state.seed = raw["seed"]
        state.clubs = {cid: Club.from_dict(c) for cid, c in raw["clubs"].items()}
        state.players = {pid: Player.from_dict(p) for pid, p in raw["players"].items()}
        state.me_id = raw["me_id"]
        state.stage = raw["stage"]
        state.year = raw["year"]
        state.week = raw["week"]
        state.fixtures = {lid: [[tuple(pair) for pair in rnd] for rnd in rounds]
                          for lid, rounds in raw["fixtures"].items()}
        state.tables = {lid: {cid: TableRow.from_dict(row) for cid, row in rows.items()}
                        for lid, rows in raw["tables"].items()}
        state.cup = raw["cup"]
        state.money = raw["money"]
        state.flags = raw["flags"]
        state.honours = raw["honours"]
        state.news = raw["news"]
        state.fired_events = raw["fired_events"]
        state.pending_event_id = raw["pending_event_id"]
        state.pending_event_body = raw.get("pending_event_body")
        state.managed_club_id = raw["managed_club_id"]
        state.tactics = raw["tactics"]
        state.training_focus = raw["training_focus"]
        state.intensity = raw.get("intensity", 1.0)
        state.first_club_id = raw["first_club_id"]
        state.last_club_id = raw["last_club_id"]
        state.history = raw["history"]
        state.caps = raw["caps"]
        state.intl_goals = raw["intl_goals"]
        state.no_start_streak = raw["no_start_streak"]
        state.game_over = raw["game_over"]
        state.rng = _decode_rng(raw["rng_state"])
        return state

    def save(self, path: Optional[str] = None) -> str:
        path = path or os.path.join(SAVE_DIR, f"{self.me.name}.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, ensure_ascii=False)
        return path

    @classmethod
    def load(cls, path: str) -> "GameState":
        with open(path, encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))


def _encode_rng(rng: random.Random) -> list:
    version, internal, gauss = rng.getstate()
    return [version, list(internal), gauss]


def _decode_rng(raw: list) -> random.Random:
    rng = random.Random()
    rng.setstate((raw[0], tuple(raw[1]), raw[2]))
    return rng
