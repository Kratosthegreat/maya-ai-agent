# -*- coding: utf-8 -*-
"""
football_manager.models
=======================
מודלי הליבה: שחקן, מועדון, חוזה וטבלת ליגה — כולל ייצור עולם אקראי.
כל המודלים ניתנים לסריאליזציה ל-JSON (to_dict/from_dict) לצורך שמירת משחק.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from . import data as D


# ---------------------------------------------------------------------------
# עזר
# ---------------------------------------------------------------------------

def clamp(value: float, low: float, high: float) -> float:
    """מגביל ערך לטווח."""
    return max(low, min(high, value))


def weighted_choice(rng: random.Random, options):
    """בוחר פריט מרשימת (ערך, משקל)."""
    total = sum(w for _, w in options)
    roll = rng.random() * total
    upto = 0.0
    for value, weight in options:
        upto += weight
        if roll <= upto:
            return value
    return options[-1][0]


# ---------------------------------------------------------------------------
# חוזה
# ---------------------------------------------------------------------------

@dataclass
class Contract:
    """חוזה של שחקן במועדון."""
    wage: int = 0            # שכר שבועי בש"ח
    years_left: int = 0      # עונות שנותרו
    release_clause: int = 0  # סעיף שחרור (0 = אין)
    bonus_goal: int = 0      # בונוס לשער

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict) -> "Contract":
        return cls(**raw)


# ---------------------------------------------------------------------------
# סטטיסטיקה
# ---------------------------------------------------------------------------

@dataclass
class Stats:
    """סטטיסטיקת שחקן (עונתית או קריירה)."""
    apps: int = 0
    goals: int = 0
    assists: int = 0
    clean_sheets: int = 0
    yellow: int = 0
    red: int = 0
    minutes: int = 0
    rating_sum: float = 0.0
    motm: int = 0
    trophies: int = 0

    @property
    def avg_rating(self) -> float:
        if self.apps == 0:
            return 0.0
        return round(self.rating_sum / self.apps, 2)

    def add_match(self, rating: float, minutes: int) -> None:
        self.apps += 1
        self.minutes += minutes
        self.rating_sum += rating

    def merge(self, other: "Stats") -> None:
        """מצרף סטטיסטיקה של עונה לסך הקריירה."""
        self.apps += other.apps
        self.goals += other.goals
        self.assists += other.assists
        self.clean_sheets += other.clean_sheets
        self.yellow += other.yellow
        self.red += other.red
        self.minutes += other.minutes
        self.rating_sum += other.rating_sum
        self.motm += other.motm

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict) -> "Stats":
        return cls(**raw)


# ---------------------------------------------------------------------------
# שחקן
# ---------------------------------------------------------------------------

@dataclass
class Player:
    """שחקן כדורגל — אנושי או מנוהל־מחשב."""
    pid: str
    name: str
    age: int
    position: str
    nationality: str = "ישראל"
    attributes: Dict[str, int] = field(default_factory=dict)
    growth: Dict[str, float] = field(default_factory=dict)  # שברי התקדמות באימונים
    potential: int = 70          # תקרת הדירוג הנוכחית — זזה עם ההתפתחות
    ceiling: int = 70            # התקרה המוחלטת שאי אפשר לעבור
    club_id: Optional[str] = None
    contract: Contract = field(default_factory=Contract)

    form: float = 50.0           # 0-100, כושר נוכחי (משפיע על ביצועים)
    morale: float = 60.0         # 0-100, מצב רוח
    fitness: float = 100.0       # 0-100, רעננות פיזית
    injury_weeks: int = 0        # שבועות עד חזרה מפציעה
    injury_name: str = ""
    reputation: float = 20.0     # 0-100, מוניטין עולמי

    traits: List[str] = field(default_factory=list)
    foot: str = "right"
    number: int = 0             # מספר חולצה במועדון הנוכחי
    height: int = 178            # ס"מ
    weight: int = 74             # ק"ג
    resilience: float = 50.0     # 0-100, עמידות לפציעות
    sharpness: float = 60.0      # 0-100, חדות משחק — נבנית מדקות במגרש
    is_human: bool = False

    # כישורים לקריירה שאחרי הפרישה
    coaching: float = 0.0        # ידע אימון
    media_skill: float = 0.0     # כריזמה תקשורתית
    business: float = 0.0        # ראש עסקי
    badges: int = 0              # תעודות אימון שהושלמו (0-4)

    season: Stats = field(default_factory=Stats)
    career: Stats = field(default_factory=Stats)
    retired: bool = False

    # -- דירוגים -----------------------------------------------------------

    @property
    def overall(self) -> int:
        """דירוג כללי משוקלל לפי עמדה."""
        weights = D.POSITION_WEIGHTS[self.position]
        total = sum(self.attributes.get(attr, 50) * w for attr, w in weights.items())
        return int(round(total))

    @property
    def effective(self) -> float:
        """דירוג אפקטיבי במשחק — כולל כושר, מורל וכשירות."""
        base = float(self.overall)
        base += (self.form - 50) * 0.12
        base += (self.morale - 50) * 0.05
        base *= 0.85 + 0.15 * (self.fitness / 100.0)
        return clamp(base, 20.0, 99.0)

    @property
    def position_he(self) -> str:
        return D.POSITION_NAMES_HE[self.position]

    @property
    def bmi(self) -> float:
        return self.weight / ((self.height / 100.0) ** 2)

    @property
    def injury_risk(self) -> float:
        """מכפיל סיכון לפציעה, סביב 1.0. נמוך = חסין יותר.

        עמידות, כוח פיזי, חדות משחק וגיל — כל אחד מושך לכיוון אחר,
        וכולם ניתנים להשפעה: אימון כוח, מנוחה, ודקות משחק סדירות.
        """
        physical = self.attributes.get("physical", 50)
        risk = 1.0
        risk *= 1.35 - (self.resilience / 100.0) * 0.70      # 1.35 עד 0.65
        risk *= 1.20 - (physical / 100.0) * 0.45             # 1.20 עד 0.75
        risk *= 1.0 + max(0.0, (60.0 - self.sharpness)) / 190.0
        risk *= 1.0 + max(0, self.age - 30) * 0.07
        risk *= 1.0 + max(0.0, 70.0 - self.fitness) / 130.0
        if self.has_trait("glass"):
            risk *= 1.7
        if self.has_trait("workhorse"):
            risk *= 0.92
        return clamp(risk, 0.30, 3.2)

    @property
    def available(self) -> bool:
        return self.injury_weeks <= 0 and not self.retired

    @property
    def value(self) -> int:
        """שווי שוק מוערך בש\"ח."""
        ovr = self.overall
        base = (max(0, ovr - 40) ** 3) * 55
        # שיא הערך סביב גיל 24-27
        if self.age <= 20:
            age_mod = 1.35
        elif self.age <= 23:
            age_mod = 1.25
        elif self.age <= 27:
            age_mod = 1.0
        elif self.age <= 30:
            age_mod = 0.7
        elif self.age <= 33:
            age_mod = 0.4
        else:
            age_mod = 0.18
        pot_mod = 1.0 + max(0, self.potential - ovr) * 0.02
        rep_mod = 0.8 + self.reputation / 250.0
        return int(base * age_mod * pot_mod * rep_mod)

    @property
    def peak_years_left(self) -> int:
        """כמה עונות נותרו בשיא — עוזר להחלטות פרישה."""
        return max(0, 33 - self.age)

    def has_trait(self, trait: str) -> bool:
        return trait in self.traits

    def describe(self) -> str:
        stars = "★" * max(1, min(5, round(self.potential / 20)))
        return (f"{self.name} ({self.age}) — {self.position_he} | "
                f"כללי {self.overall} | פוטנציאל {stars} | {self.nationality}")

    # -- סריאליזציה --------------------------------------------------------

    def to_dict(self) -> dict:
        raw = asdict(self)
        raw["contract"] = self.contract.to_dict()
        raw["season"] = self.season.to_dict()
        raw["career"] = self.career.to_dict()
        return raw

    @classmethod
    def from_dict(cls, raw: dict) -> "Player":
        raw = dict(raw)
        raw["contract"] = Contract.from_dict(raw.get("contract", {}))
        raw["season"] = Stats.from_dict(raw.get("season", {}))
        raw["career"] = Stats.from_dict(raw.get("career", {}))
        return cls(**raw)


# ---------------------------------------------------------------------------
# מועדון
# ---------------------------------------------------------------------------

@dataclass
class Club:
    """מועדון כדורגל."""
    cid: str
    name: str
    nickname: str
    league_id: str
    reputation: int = 50
    budget: float = 5.0             # תקציב העברות במיליונים
    wage_budget: int = 200_000      # תקציב שכר שבועי
    training_facilities: int = 50   # 1-100, משפיע על קצב התפתחות
    youth_academy: int = 50         # 1-100, איכות הנוער
    medical_centre: int = 50        # 1-100, מקצר משך פציעות
    stadium_name: str = ""
    capacity: int = 12_000          # מקומות ישיבה
    balance: float = 0.0            # מזומן בקופת המועדון (₪)
    last_attendance: int = 0        # קהל במשחק הבית האחרון
    staff: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    works: List[Dict[str, Any]] = field(default_factory=list)  # פרויקטי בנייה בתהליך
    manager_name: str = ""
    manager_trust: float = 50.0     # אמון המאמן בשחקן האנושי
    board_confidence: float = 60.0  # אמון ההנהלה במאמן האנושי
    fan_support: float = 60.0       # אהדת הקהל
    formation: str = "4-3-3"
    squad: List[str] = field(default_factory=list)  # מזהי שחקנים
    season_expectation: str = "אמצע טבלה"
    trophies: List[str] = field(default_factory=list)

    # -- כלכלה ומתקנים -------------------------------------------------

    def facility(self, kind: str) -> float:
        """הערך הנוכחי של מתקן, לפי המפתח ב-D.FACILITIES."""
        return float(getattr(self, D.FACILITIES[kind]["field"]))

    def staff_quality(self, role: str) -> int:
        """איכות בעל התפקיד, או 0 אם המשרה פנויה."""
        member = self.staff.get(role)
        return int(member["quality"]) if member else 0

    @property
    def staff_wage_bill(self) -> int:
        return sum(int(m["wage"]) for m in self.staff.values())

    @property
    def ticket_price(self) -> int:
        tier = next((l["tier"] for l in D.LEAGUES if l["id"] == self.league_id), 2)
        return int(D.TICKET_BASE.get(tier, 40) * (0.55 + self.reputation / 90.0))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict) -> "Club":
        return cls(**raw)


# ---------------------------------------------------------------------------
# טבלת ליגה
# ---------------------------------------------------------------------------

@dataclass
class TableRow:
    """שורה בטבלת הליגה."""
    club_id: str
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    gf: int = 0
    ga: int = 0

    @property
    def points(self) -> int:
        return self.won * 3 + self.drawn

    @property
    def gd(self) -> int:
        return self.gf - self.ga

    def register(self, scored: int, conceded: int) -> None:
        self.played += 1
        self.gf += scored
        self.ga += conceded
        if scored > conceded:
            self.won += 1
        elif scored == conceded:
            self.drawn += 1
        else:
            self.lost += 1

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict) -> "TableRow":
        return cls(**raw)


# ---------------------------------------------------------------------------
# ייצור עולם
# ---------------------------------------------------------------------------

def _rand_name(rng: random.Random, used: set) -> str:
    for _ in range(60):
        name = f"{rng.choice(D.FIRST_NAMES)} {rng.choice(D.LAST_NAMES)}"
        if name not in used:
            used.add(name)
            return name
    return f"{rng.choice(D.FIRST_NAMES)} {rng.choice(D.LAST_NAMES)} {rng.randint(2, 99)}"


def generate_attributes(rng: random.Random, position: str, target_overall: int) -> Dict[str, int]:
    """מייצר תכונות שמתכנסות לדירוג כללי מבוקש לפי העמדה."""
    weights = D.POSITION_WEIGHTS[position]
    attrs = {}
    for attr in D.ATTRIBUTES:
        # תכונות חשובות לעמדה מקבלות ערך גבוה יותר
        importance = weights[attr]
        spread = rng.gauss(0, 7)
        base = target_overall + (importance - 0.15) * 45 + spread
        attrs[attr] = int(clamp(base, 15, 96))
    # כיול עדין כדי לקלוע לדירוג המבוקש
    for _ in range(40):
        current = sum(attrs[a] * weights[a] for a in D.ATTRIBUTES)
        diff = target_overall - current
        if abs(diff) < 0.6:
            break
        key = max(D.ATTRIBUTES, key=lambda a: weights[a])
        attrs[key] = int(clamp(attrs[key] + (1 if diff > 0 else -1), 15, 96))
    return attrs


def generate_player(rng: random.Random, club: Optional[Club], position: str,
                    age: Optional[int] = None, quality: Optional[int] = None,
                    used_names: Optional[set] = None) -> Player:
    """מייצר שחקן מחשב שמתאים לרמת המועדון."""
    used_names = used_names if used_names is not None else set()
    age = age if age is not None else rng.randint(17, 35)
    rep = club.reputation if club else 40
    if quality is None:
        quality = int(clamp(rng.gauss(rep * 0.70 + 20, 6), 28, 92))
    # צעירים עדיין לא במיטבם
    if age < 21:
        quality = int(quality - (21 - age) * 2.5)
    # תקרה מוחלטת: מה שהשחקן הזה יכול להיות במקרה הטוב ביותר.
    # אצל צעירים הפיזור רחב בכוונה — יש כישרונות דור ויש מי שייתקע.
    youth_room = max(0, 25 - age)
    ceiling = int(clamp(quality + youth_room * rng.uniform(0.5, 2.1)
                        + rng.gauss(2, 6), quality + 1, 96))
    # הערכת הפוטנציאל שרואים היום — שמרנית, ותזוז עם ההתפתחות בפועל
    potential = int(clamp(quality + (ceiling - quality) * rng.uniform(0.35, 0.75),
                          quality, ceiling))

    player = Player(
        pid=f"p{rng.randrange(10 ** 9):09d}",
        name=_rand_name(rng, used_names),
        age=age,
        position=position,
        nationality=weighted_choice(rng, D.NATIONALITIES),
        attributes=generate_attributes(rng, position, quality),
        potential=potential,
        ceiling=ceiling,
        club_id=club.cid if club else None,
        reputation=clamp(quality - 25 + rng.gauss(0, 6), 1, 95),
        form=rng.uniform(40, 60),
        morale=rng.uniform(45, 75),
    )
    wage = wage_for_overall(player.overall)
    player.contract = Contract(wage=wage, years_left=rng.randint(1, 4))
    player.foot = "right" if rng.random() < 0.72 else ("left" if rng.random() < 0.78 else "both")
    apply_physique(player, rng)
    if rng.random() < 0.35:
        player.traits.append(rng.choice(list(D.TRAITS.keys())))
    player.coaching = clamp(rng.gauss(10, 6), 0, 40)
    player.media_skill = clamp(rng.gauss(10, 6), 0, 40)
    player.business = clamp(rng.gauss(8, 5), 0, 40)
    return player


def wage_for_overall(overall: int) -> int:
    """שכר שבועי מקובל לדירוג נתון."""
    return int(clamp(8000 * (max(20, overall) / 50.0) ** 6.85, 700, 1_200_000))


SQUAD_TEMPLATE = ["GK", "GK", "GK", "CB", "CB", "CB", "CB", "LB", "LB", "RB", "RB",
                  "DM", "DM", "CM", "CM", "CM", "AM", "AM", "LW", "LW", "RW", "RW",
                  "ST", "ST", "ST"]


def gain_reputation(player: Player, delta: float) -> None:
    """נקודת החנק היחידה לשינוי מוניטין.

    שם עולמי הוא לא סכום של אירועים: ככל שכבר מכירים אותך, כל צעד
    נוסף עולה יותר. ירידות עוברות במלואן — מוניטין נשבר מהר.
    """
    if delta > 0:
        delta *= max(0.10, 1.0 - max(0.0, player.reputation - 40) / 58.0)
    player.reputation = clamp(player.reputation + delta, 1, 99)


def apply_physique(player: Player, rng: random.Random) -> None:
    """גובה, משקל ועמידות — לפי העמדה, עם רעש אישי.

    ילדים עדיין לא גמרו לגדול, ולכן הגובה נקבע כיעד בוגר וההווה נגזר ממנו.
    """
    mean, spread = D.PHYSIQUE.get(player.position, (180, 5.0))
    adult_height = int(round(clamp(rng.gauss(mean, spread), 158, 205)))
    player.height = grown_height(adult_height, player.age)
    bmi = rng.uniform(*D.BMI_RANGE)
    player.weight = int(round(bmi * (player.height / 100.0) ** 2))
    # עמידות: קשורה למבנה אבל לא נגזרת ממנו — יש שברירים חסונים
    player.resilience = clamp(rng.gauss(52, 17)
                              + (player.attributes.get("physical", 50) - 50) * 0.22,
                              5, 96)
    player.sharpness = clamp(rng.gauss(62, 12), 20, 95)


def grown_height(adult_height: int, age: int) -> int:
    """כמה מהגובה הבוגר כבר הושג בגיל הנתון."""
    if age >= 19:
        return adult_height
    share = {13: 0.895, 14: 0.925, 15: 0.952, 16: 0.973, 17: 0.988, 18: 0.996}
    return int(round(adult_height * share.get(age, 1.0)))


# המספרים המסורתיים של כל עמדה
NUMBER_PREF = {
    "GK": [1, 12, 23], "CB": [4, 5, 2, 3, 6], "LB": [3, 15], "RB": [2, 14],
    "DM": [6, 16, 4], "CM": [8, 18, 20], "AM": [10, 7, 21],
    "LW": [11, 17], "RW": [7, 17, 22], "ST": [9, 19, 29],
}
SQUAD_NUMBER_MAX = 45


def taken_numbers(club: Club, players: Dict[str, Player],
                  except_pid: Optional[str] = None) -> set:
    """המספרים שתפוסים בסגל כרגע."""
    out = set()
    for pid in club.squad:
        player = players.get(pid)
        if player and player.pid != except_pid and player.number:
            out.add(player.number)
    return out


def available_numbers(club: Club, players: Dict[str, Player],
                      except_pid: Optional[str] = None) -> List[int]:
    """כל המספרים הפנויים במועדון, 1 עד 45."""
    taken = taken_numbers(club, players, except_pid)
    return [n for n in range(1, SQUAD_NUMBER_MAX + 1) if n not in taken]


def assign_number(club: Club, players: Dict[str, Player], player: Player,
                  wanted: Optional[int] = None) -> int:
    """נותן מספר חולצה. wanted מנסה מספר מבוקש; אחרת לפי מסורת העמדה."""
    taken = taken_numbers(club, players, player.pid)
    if wanted and wanted not in taken and 1 <= wanted <= SQUAD_NUMBER_MAX:
        player.number = wanted
        return wanted
    for number in NUMBER_PREF.get(player.position, []):
        if number not in taken:
            player.number = number
            return number
    for number in range(2, SQUAD_NUMBER_MAX + 1):
        if number not in taken:
            player.number = number
            return number
    player.number = 0
    return 0


def stadium_name_for(cid: str, nickname: str, rng: random.Random) -> str:
    """שם אצטדיון קבוע למועדון."""
    word = rng.choice(D.STADIUM_WORDS)
    if rng.random() < 0.45:
        return f"{word} {rng.choice(D.STADIUM_SUFFIX)}"
    return f"{word} {nickname}"


def capacity_for(reputation: int, rng: random.Random) -> int:
    """קיבולת שמתאימה לגודל המועדון, מעוגלת ל-500 הקרובים."""
    base = 900 + (reputation / 10.0) ** 3.05 * 55
    raw = base * rng.uniform(0.84, 1.16)
    return int(round(clamp(raw, 1_500, 42_000) / 500) * 500)


def staff_member(rng: random.Random, role: str, quality: int) -> Dict[str, Any]:
    quality = int(clamp(quality, 8, 96))
    wage = int(quality * D.STAFF_ROLES[role]["wage_per_point"] * rng.uniform(0.85, 1.2))
    return {"name": rng.choice(D.STAFF_NAMES), "quality": quality, "wage": wage}


def generate_staff(rng: random.Random, reputation: int) -> Dict[str, Dict[str, Any]]:
    """צוות מקצועי שמתאים לגודל המועדון. מועדונים קטנים משאירים משרות פנויות."""
    staff: Dict[str, Dict[str, Any]] = {}
    for role in D.STAFF_ROLES:
        if reputation < 35 and rng.random() < 0.45:
            continue                      # אין תקציב לתפקיד הזה
        staff[role] = staff_member(rng, role, int(reputation + rng.gauss(0, 11)))
    return staff


def generate_world(seed: int = 0):
    """מייצר את כל המועדונים והשחקנים במשחק."""
    rng = random.Random(seed)
    clubs: Dict[str, Club] = {}
    players: Dict[str, Player] = {}
    used_names: set = set()

    for cid, name, nickname, league_id, rep, budget in D.CLUBS:
        club = Club(
            cid=cid, name=name, nickname=nickname, league_id=league_id,
            reputation=rep, budget=budget,
            wage_budget=int(budget * 1_000_000 / 10),
            training_facilities=int(clamp(rep + rng.gauss(0, 8), 15, 99)),
            youth_academy=int(clamp(rep + rng.gauss(0, 12), 15, 99)),
            medical_centre=int(clamp(rep + rng.gauss(0, 10), 15, 99)),
            manager_name=rng.choice(D.MANAGER_NAMES),
            fan_support=clamp(rep + rng.gauss(0, 10), 20, 99),
            formation=rng.choice(list(D.FORMATIONS.keys())),
        )
        club.stadium_name = stadium_name_for(cid, nickname, rng)
        club.capacity = capacity_for(rep, rng)
        club.balance = round(budget * 1_000_000 * rng.uniform(0.18, 0.42))
        club.staff = generate_staff(rng, rep)
        for position in SQUAD_TEMPLATE:
            player = generate_player(rng, club, position, used_names=used_names)
            players[player.pid] = player
            club.squad.append(player.pid)
            assign_number(club, players, player)
        clubs[cid] = club

    return clubs, players
