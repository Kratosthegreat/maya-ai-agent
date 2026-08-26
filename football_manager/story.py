# -*- coding: utf-8 -*-
"""
football_manager.story
======================
מנוע העלילה. כל אירוע הוא צומת החלטה עם השלכות אמיתיות על המשחק:
יחסים במועדון, מוניטין, כסף, פציעות, מעברים — ולפעמים על כל הקריירה.

האירועים מסודרים לפי שלב הקריירה: נוער → שחקן → ותיק → פרישה →
מאמן → מנג'ר → ומה שבא אחרי.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple

from . import data as D
from . import commercial as CM
from . import scouting as SC
from . import story_engine as SE
from .story_pack import PACK
from .models import clamp, gain_reputation


@dataclass
class Choice:
    """אפשרות בחירה בתוך אירוע עלילה."""
    label: str
    apply: Callable[[Any], str]
    hint: str = ""


@dataclass
class StoryEvent:
    """צומת עלילה."""
    eid: str
    title: str
    body: Callable[[Any], str]
    choices: List[Choice]
    condition: Callable[[Any], bool] = lambda g: True
    stages: Tuple[str, ...] = ()
    weight: float = 1.0
    once: bool = True
    # אירוע חוזר לא אמור לקרות שוב מיד. ברירת המחדל: פעם בעונה בערך.
    cooldown: int = 30


REGISTRY: List[StoryEvent] = []


def register(event: StoryEvent) -> StoryEvent:
    REGISTRY.append(event)
    return event


# ---------------------------------------------------------------------------
# קיצורי דרך לאפקטים
# ---------------------------------------------------------------------------

def _morale(game, delta: float) -> None:
    game.me.morale = clamp(game.me.morale + delta, 5, 99)


def _trust(game, delta: float) -> None:
    club = game.my_club
    if club:
        club.manager_trust = clamp(club.manager_trust + delta, 0, 100)


def _fans(game, delta: float) -> None:
    club = game.my_club
    if club:
        club.fan_support = clamp(club.fan_support + delta, 0, 100)


def _rep(game, delta: float) -> None:
    gain_reputation(game.me, delta)


def _attr(game, attr: str, delta: float) -> None:
    """שינוי תכונה מאירוע עלילה.

    האירועים כתובים בשפת שבע הקבוצות, וזה נשאר נכון: הכתיבה מתפזרת
    על התכונות המפורטות שמרכיבות את הקבוצה. אירוע שאומר "בעיטה +1.6"
    מזיז בפועל סיום, בעיטות מרחוק, טכניקה וקור רוח.
    """
    SE.apply_attr(game.me, attr, delta)


# ===========================================================================
# שלב 0 — כדורגל נוער (13-15)
# ===========================================================================

register(StoryEvent(
    eid="first_boots",
    title="הנעליים הראשונות",
    stages=("youth",),
    weight=7.0,
    condition=lambda g: g.week >= 2,
    body=lambda g: (
        "אבא שלך שם על השולחן קופסה.\n"
        "נעלי כדורגל אמיתיות — לא של אח גדול, לא מהשוק.\n\n"
        "\"אני לא מבין בזה,\" הוא אומר, \"אבל אמרו לי שאתה טוב. תוכיח.\""
    ),
    choices=[
        Choice("לשמור אותן רק למשחקים",
               lambda g: (_attr(g, "mental", 1.2), _morale(g, 5),
                          "נעלת אותן רק בימי משחק. באימונים המשכת עם הישנות, עד שנקרעו.")[-1],
               hint="משמעת"),
        Choice("לשחק בהן בכל יום עד שיתפרקו",
               lambda g: (_attr(g, "dribbling", 1.6), _attr(g, "physical", 0.4),
                          "שחקת בהן בבית ספר, ברחוב, בחצר. "
                          "תוך חודשיים הן נראו כמו סמרטוט — ואתה נראית אחרת.")[-1],
               hint="כדרור ↑↑"),
    ],
))

register(StoryEvent(
    eid="school_or_football",
    title="מבחן ביום משחק",
    stages=("youth",),
    weight=4.0,
    once=False,
    cooldown=24,
    condition=lambda g: g.me.age <= 15,
    body=lambda g: (
        "מחר גמר מחוזי. מחר גם מבחן במתמטיקה.\n"
        "המחנכת אמרה שאם תיעדר שוב — היא מזמינה את ההורים."
    ),
    choices=[
        Choice("לשחק. המבחן יחכה.",
               lambda g: (_trust(g, 8), _attr(g, "shooting", 0.8),
                          g.set_flag("school_trouble", True),
                          "כבשת שניים. בבית חיכתה שיחה ארוכה, "
                          "אבל אף אחד לא הזכיר את זה יותר אחרי הגמר.")[-1],
               hint="המאמן ↑, בית הספר ↓"),
        Choice("מבחן. אני לא זורק את הלימודים.",
               lambda g: (_attr(g, "mental", 1.4), _trust(g, -5),
                          "עברת את המבחן. הקבוצה הפסידה 1:0 "
                          "והמאמן הסתכל עליך אחרת שבועיים.")[-1],
               hint="ראש ↑"),
        Choice("לנסות את שניהם — מבחן בבוקר, משחק בערב",
               lambda g: (_attr(g, "mental", 0.6), _morale(g, -3),
                          g.me.__setattr__("fitness", clamp(g.me.fitness - 20, 5, 100)),
                          "הגעת למשחק שרוף. שיחקת חצי שעה ולא זכרת ממנה כלום.")[-1]),
    ],
))

register(StoryEvent(
    eid="growth_spurt",
    title="פתאום הכל ארוך",
    stages=("youth",),
    weight=5.0,
    condition=lambda g: g.me.age >= 14,
    body=lambda g: (
        "גדלת שמונה סנטימטרים בחצי שנה.\n"
        "הרגליים לא במקום שהן היו, הכדור לא מגיע לאן שכיוונת,\n"
        "וכל מי שהיה נמוך ממך פתאום עוקף אותך בכדרור."
    ),
    choices=[
        Choice("לעבוד על תיאום ושליטה",
               lambda g: (_attr(g, "dribbling", 1.3), _attr(g, "passing", 1.0),
                          _attr(g, "pace", -0.4),
                          "חודשיים של תרגילי קונוסים משעממים. "
                          "חזרת לשלוט בגוף החדש שלך.")[-1],
               hint="כדרור ומסירה ↑"),
        Choice("לנצל את הגובה ולהתחזק",
               lambda g: (_attr(g, "physical", 2.0), _attr(g, "dribbling", -0.5),
                          "הפכת לילד הכי חזק במגרש. גם הכי מגושם, "
                          "אבל אף אחד לא הזיז אותך מהכדור.")[-1],
               hint="כוח פיזי ↑↑"),
    ],
))

register(StoryEvent(
    eid="scout_in_stands",
    title="האיש עם המחברת",
    stages=("youth",),
    weight=4.5,
    condition=lambda g: g.me.age >= 14 and g.me.season.apps >= 3,
    body=lambda g: (
        "מאחורי השער עומד גבר עם מעיל ומחברת.\n"
        "כולם יודעים מי זה. הקבוצה משחקת אחרת כשהוא שם — כולם רוצים להיראות."
    ),
    choices=[
        Choice("לשחק בדיוק כמו תמיד",
               lambda g: (_attr(g, "mental", 1.0), _rep(g, 2),
                          "לא ניסית להרשים. הוא רשם משהו קצר והלך. "
                          "שבוע אחרי זה שאלו עליך.")[-1],
               hint="בטוח"),
        Choice("לנסות משהו מיוחד", lambda g: g.show_off(), hint="הימור"),
    ],
))

register(StoryEvent(
    eid="left_out",
    title="הרשימה על הדלת",
    stages=("youth",),
    weight=3.5,
    once=False,
    cooldown=10,
    condition=lambda g: g.me.age <= 15 and g.week >= 6,
    body=lambda g: (
        "רשימת הנוסעים לטורניר תלויה על דלת חדר ההלבשה.\n"
        "קראת אותה שלוש פעמים. השם שלך לא שם."
    ),
    choices=[
        Choice("לשאול את המאמן למה", lambda g: g.ask_why(), hint="אמת בפנים"),
        Choice("להתאמן לבד כל השבוע",
               lambda g: (_attr(g, "physical", 1.4), _attr(g, "shooting", 0.6),
                          _morale(g, -8),
                          "כל בוקר, מגרש ריק, אתה והכדור. "
                          "בטורניר הבא לא היה מה לשאול.")[-1],
               hint="כוח פיזי ↑, מורל ↓"),
        Choice("לא להגיע לאימונים שבוע",
               lambda g: (_trust(g, -14), _morale(g, 3),
                          "נעלמת שבוע. כשחזרת, המאמן אמר רק: "
                          "\"נחמד שהצטרפת.\" זה עלה לך.")[-1],
               hint="מסוכן"),
    ],
))

register(StoryEvent(
    eid="academy_offer",
    title="מכתב ממועדון גדול",
    stages=("youth",),
    weight=6.0,
    condition=lambda g: g.me.age >= 14 and g.youth_academy_suitor() is not None,
    body=lambda g: (
        f"{g.youth_academy_suitor().name} מזמינים אותך למחלקת הנוער שלהם.\n"
        f"מתקנים אחרים, מאמנים אחרים, ילדים טובים יותר.\n\n"
        f"זה גם שעה נסיעה לכל כיוון, וחברים שלא תראה יותר."
    ),
    choices=[
        Choice("לעבור למועדון הגדול", lambda g: g.join_big_academy(),
               hint="מתקנים ↑↑, תחרות קשה"),
        Choice("להישאר בבית",
               lambda g: (_trust(g, 12), _morale(g, 6), g.set_flag("stayed_home", True),
                          "נשארת. במועדון שלך הפכת לילד שכולם מדברים עליו — "
                          "וזה בדיוק מה שהיה צריך.")[-1],
               hint="דקות משחק, אמון"),
    ],
))


# ===========================================================================
# שלב 1 — נוער ופריצה
# ===========================================================================

register(StoryEvent(
    eid="first_call_up",
    title="קריאה מהמשרד",
    stages=("academy",),
    weight=6.0,
    condition=lambda g: g.week >= 2,
    body=lambda g: (
        f"עוזר המאמן עוצר אותך במסדרון של {g.my_club.name}.\n"
        f"\"{g.my_club.manager_name} רוצה אותך באימון של הבוגרים ביום חמישי. "
        f"אל תדפוק את זה.\"\n\n"
        f"אתה בן {g.me.age}. חצי מהחדר הזה הם אנשים שראית בטלוויזיה."
    ),
    choices=[
        Choice("להיכנס חזק — שיזכרו את השם שלך",
               lambda g: (_trust(g, 9), _morale(g, 6), _attr(g, "physical", 0.7),
                          g.set_flag("bold_debut", True),
                          "נכנסת לקפטן בכניסה קשה. חצי מהקבוצה צחקה, המאמן רשם משהו במחברת. "
                          "אתה בפנים.")[-1],
               hint="אמון המאמן ↑↑"),
        Choice("לשחק פשוט, בלי סיכונים",
               lambda g: (_trust(g, 4), _attr(g, "passing", 0.6),
                          "94% מסירות מדויקות ואפס טעויות. לא הרשמת אף אחד, "
                          "אבל גם לא נתת סיבה להוריד אותך.")[-1],
               hint="בטוח"),
        Choice("להישאר בנוער עוד קצת",
               lambda g: (_morale(g, -4), _trust(g, -6), g.set_flag("declined_first", True),
                          "אמרת שאתה עוד לא מוכן. המאמן הנהן. "
                          "לפעמים הנהון כזה עולה שנתיים.")[-1],
               hint="מסוכן"),
    ],
))

register(StoryEvent(
    eid="youth_mentor",
    title="הוותיק שבפינת ההלבשה",
    stages=("academy", "player"),
    weight=2.5,
    condition=lambda g: g.me.age <= 22,
    body=lambda g: (
        "הוותיק של הקבוצה מתיישב לידך אחרי אימון.\n"
        "\"אני רואה אותך. יש לך רגליים. מה שאין לך זה ראש.\n"
        "בוא נשב על וידאו פעמיים בשבוע — בחינם. רק תבוא בזמן.\""
    ),
    choices=[
        Choice("לבוא לכל מפגש",
               lambda g: (_attr(g, "mental", 2.0), _morale(g, 3),
                          g.set_flag("has_mentor", True),
                          "שלושה חודשים של וידאו. פתאום אתה רואה מסירות שלפני חודש לא היו קיימות.")[-1],
               hint="קריאת משחק ↑↑"),
        Choice("תודה, אני מסתדר",
               lambda g: (_attr(g, "dribbling", 0.8),
                          "המשכת לעבוד לבד על הכדור. הוא לא הציע שוב.")[-1]),
    ],
))

register(StoryEvent(
    eid="loan_offer",
    title="הצעת השאלה",
    stages=("player",),
    weight=3.0,
    condition=lambda g: g.me.age <= 23 and g.minutes_share() < 0.35,
    body=lambda g: (
        f"אתה לא משחק. {g.loan_target_name()} מהליגה הלאומית רוצים אותך בהשאלה לעונה.\n"
        f"\"אצלנו אתה משחק 90 דקות כל שבוע. אצלם אתה מחמם ספסל ומזדקן.\""
    ),
    choices=[
        Choice("לצאת להשאלה ולשחק",
               lambda g: g.go_on_loan(),
               hint="דקות משחק ↑↑, מוניטין ↓"),
        Choice("להישאר ולהילחם על מקום",
               lambda g: (_trust(g, 5), _morale(g, -2),
                          "נשארת. המאמן העריך את זה — עכשיו תוכיח שהוא צדק.")[-1]),
    ],
))

# ===========================================================================
# שלב 2 — חיי שחקן מקצוען
# ===========================================================================

register(StoryEvent(
    eid="bench_frustration",
    title="שבוע חמישי על הספסל",
    stages=("player", "veteran"),
    weight=3.0,
    once=False,
    cooldown=12,
    condition=lambda g: g.weeks_without_start() >= 4 and g.me.age >= 19,
    body=lambda g: (
        f"חמישה משחקים. אפס דקות.\n"
        f"אתה עומד מול הדלת של {g.my_club.manager_name} ומחזיק את הידית."
    ),
    choices=[
        Choice("להיכנס ולהתעמת",
               lambda g: g.confront_manager(),
               hint="מר-רווח: או שתשחק או שתיגמר"),
        Choice("לשתוק ולהתאמן כפול",
               lambda g: (_attr(g, "physical", 1.0), _trust(g, 6), _morale(g, -5),
                          "נשארת אחרי כל אימון. הצוות שם לב. הסבלנות עולה לך במצב רוח.")[-1],
               hint="אמון ↑, מורל ↓"),
        Choice("לבקש מהסוכן למצוא מועדון אחר",
               lambda g: (g.set_flag("wants_transfer", True), _trust(g, -10),
                          "הסוכן התחיל לעבוד. בחלון הקרוב יגיעו הצעות — "
                          "והמאמן כבר יודע שאתה בדרך החוצה.")[-1],
               hint="פותח שוק העברות"),
    ],
))

register(StoryEvent(
    eid="derby_week",
    title="שבוע דרבי",
    stages=("player", "veteran"),
    weight=2.0,
    once=False,
    cooldown=20,
    condition=lambda g: g.week >= 3,
    body=lambda g: (
        f"העיר לא ישנה. שלטי חוצות, אוהדים מחוץ למתחם האימונים,\n"
        f"וכתבה שמצטטת שחקן מהיריבה: \"{g.me.name}? לא מכיר.\""
    ),
    choices=[
        Choice("לענות לו בתקשורת",
               lambda g: (_rep(g, 4), _fans(g, 6), g.set_flag("derby_beef", True),
                          "הכותרת שלך פתחה את המהדורה. עכשיו אסור לך לככב פחות מהמצוין.")[-1],
               hint="מוניטין ↑, לחץ ↑"),
        Choice("לשתוק ולעלות על המגרש",
               lambda g: (_morale(g, 4), _attr(g, "mental", 0.8),
                          "לא אמרת מילה כל השבוע. בחדר ההלבשה זה נשמע חזק יותר מכל ציטוט.")[-1]),
        Choice("להזמין את המשפחה ליציע ולנשום",
               lambda g: (_morale(g, 7),
                          "ראית אותם ביציע בחימום. פתאום זה שוב רק כדורגל.")[-1]),
    ],
))

register(StoryEvent(
    eid="scandal_night",
    title="צילום מהמועדון",
    stages=("player", "veteran"),
    weight=1.6,
    condition=lambda g: g.me.age >= 19 and g.me.reputation >= 30,
    body=lambda g: (
        "3:40 לפנות בוקר. מישהו צילם אותך יוצא ממועדון לילה\n"
        "שני ימים לפני משחק. הסרטון כבר ברשת.\n"
        "הדובר מחכה לתשובה שלך עוד עשר דקות."
    ),
    choices=[
        Choice("להתנצל בפומבי ולקחת אחריות",
               lambda g: (_rep(g, -3), _trust(g, 4), _fans(g, 2), _morale(g, -2),
                          "התנצלת בלי תירוצים. התקשורת התייבשה תוך יומיים. "
                          "המאמן העריך את זה יותר ממה שהודה.")[-1]),
        Choice("להכחיש הכל",
               lambda g: g.deny_scandal(),
               hint="הימור"),
        Choice("לתרום את שכר השבוע ולא לומר מילה",
               lambda g: (g.spend_money(int(g.me.contract.wage)), _fans(g, 9), _rep(g, 2),
                          "העברת את שכר השבוע למועדון ילדים בשכונה. "
                          "מישהו הדליף את זה. האוהדים אימצו אותך.")[-1],
               hint="עולה כסף"),
    ],
))

register(StoryEvent(
    eid="national_call",
    title="המעטפה מהנבחרת",
    stages=("player", "veteran"),
    weight=5.0,
    condition=lambda g: g.me.reputation >= 52 and not g.flag("national_debut"),
    body=lambda g: (
        "סגל הנבחרת פורסם. השם שלך שם, בשורה התחתונה, מודפס קטן.\n"
        "אמא שלך שלחה צילום מסך עם אחת עשרה נקודות קריאה."
    ),
    choices=[
        Choice("לנסוע ולתת הכל",
               lambda g: g.national_debut(),
               hint="מוניטין ↑↑"),
        Choice("להתנצל — הגוף צריך מנוחה",
               lambda g: (_rep(g, -5), g.me.__setattr__("fitness", 100.0), _morale(g, -3),
                          "ויתרת על הקריאה הראשונה. הסלקטור לא שכח.")[-1]),
    ],
))

register(StoryEvent(
    eid="big_club_interest",
    title="שיחה מאירופה",
    stages=("player", "veteran"),
    weight=4.5,
    once=False,
    cooldown=34,
    condition=lambda g: g.big_club_suitor() is not None and g.week in (11, 12, 13),
    body=lambda g: (
        f"הסוכן שלך מתקשר בשתיים בלילה.\n"
        f"\"{g.big_club_suitor().name} שאלו עליך. לא סתם שאלו — הם שלחו צופה לשלושה משחקים.\n"
        f"תגיד לי עכשיו: אם תגיע הצעה, אתה בפנים?\""
    ),
    choices=[
        Choice("תגיד להם שאני מוכן",
               lambda g: (g.set_flag("open_to_europe", True), _morale(g, 5),
                          "המילה עברה. עכשיו כל משחק הוא מבחן קבלה.")[-1],
               hint="מגדיל סיכוי להצעה"),
        Choice("אני מרוכז במועדון שלי",
               lambda g: (_trust(g, 8), _fans(g, 7), _morale(g, 2),
                          "הצהרת נאמנות. המועדון הרים לך את השכר בלי שביקשת.")[-1]),
    ],
))

register(StoryEvent(
    eid="captain_armband",
    title="הסרט",
    stages=("player", "veteran"),
    weight=4.0,
    condition=lambda g: (g.me.age >= 25 and g.my_club is not None
                         and g.my_club.manager_trust >= 65),
    body=lambda g: (
        f"{g.my_club.manager_name} סוגר את הדלת.\n"
        f"\"הקפטן הולך בסוף העונה. אני רוצה שאתה תיקח את הסרט.\n"
        f"זה אומר גם את הפעמים שצריך לצעוק על מישהו שאתה אוהב.\""
    ),
    choices=[
        Choice("לקחת את הסרט",
               lambda g: g.become_captain(),
               hint="מנהיגות, אחריות, לחץ"),
        Choice("להציע במקומי את הוותיק",
               lambda g: (_trust(g, 3), _morale(g, 2),
                          "ויתרת לטובת מישהו אחר. חדר ההלבשה זכר לך את זה שנים.")[-1]),
    ],
))

register(StoryEvent(
    eid="serious_injury",
    title="הרגל נתקעה בדשא",
    stages=("player", "veteran"),
    weight=3.0,
    once=False,
    cooldown=40,
    condition=lambda g: g.me.injury_weeks >= 8,
    body=lambda g: (
        f"{g.me.injury_name}. {g.me.injury_weeks} שבועות, אם הכל ילך טוב.\n"
        f"הרופא מדבר, אתה שומע רק את המילה \"אם\"."
    ),
    choices=[
        Choice("שיקום לפי הספר, בלי קיצורי דרך",
               lambda g: (_attr(g, "mental", 1.2), _morale(g, -4),
                          g.set_flag("clean_rehab", True),
                          "חזרת בזמן, בלי הישנות. איבדת חצי עונה והרווחת גוף שמחזיק.")[-1],
               hint="בטוח"),
        Choice("לדחוף חזרה מוקדם — הקבוצה צריכה אותי",
               lambda g: g.rush_rehab(),
               hint="הימור מסוכן"),
        Choice("לנצל את הזמן ללימודי אימון",
               lambda g: g.study_during_injury(),
               hint="פותח דלתות לעתיד"),
    ],
))

# --- החיים המסחריים -------------------------------------------------------
#
# ההצעות נבנות בזמן אמת מ-commercial.py לפי מי שאתה עכשיו: מוניטין,
# שערים, כריזמה והמועדון. לכן אותו אירוע נראה אחרת בגיל 18 ובגיל 27.

def _cool(game, key: str, weeks: int) -> bool:
    """האם עבר מספיק זמן מאז הפעם הקודמת של האירוע הזה."""
    last = game.flags.get(f"cool_{key}")
    now = game.year * 100 + game.week
    if last is None:
        return True
    gap = (now // 100 - last // 100) * 43 + (now % 100 - last % 100)
    return gap >= weeks


def _mark(game, key: str) -> None:
    game.flags[f"cool_{key}"] = game.year * 100 + game.week


def _pending_deal(game):
    """ההצעה שנבנתה כשהאירוע נדרך. נשמרת כדי שהטקסט והתוצאה יתאימו."""
    return game.flags.get("pending_deal")


def _build_deal(game):
    club = game.my_club
    match_week = game.my_fixture() is not None
    # חידוש שממתין קודם — מותג שכבר עבד איתך חוזר לפני שמחפשים חדש
    pending = game.flags.get("pending_renewal")
    if pending:
        game.flags["pending_renewal"] = None
        game.flags["pending_deal"] = pending
        return pending
    offer = CM.sponsor_offer(game.me, game.rng,
                             club.reputation if club else 30, match_week,
                             honours=len(game.honours))
    if offer:
        game.flags["pending_deal"] = offer
    return offer


register(StoryEvent(
    eid="sponsor_deal",
    title="טלפון ממחלקת השיווק",
    stages=("academy", "player", "veteran"),
    weight=2.4,
    once=False,
    cooldown=9,
    condition=lambda g: (_cool(g, "sponsor", 8) and CM.marketability(
        g.me, g.my_club.reputation if g.my_club else 30) >= 12),
    body=lambda g: _sponsor_body(g),
    choices=[
        Choice("לחתום", lambda g: _sponsor_sign(g), hint="כסף וכריזמה"),
        Choice("לסרב", lambda g: _sponsor_decline(g)),
    ],
))


def _sponsor_body(game) -> str:
    offer = _build_deal(game)
    if not offer:
        return ""
    head = (f"{offer['brand']} ({offer['tier_he']}) רוצים לחדש איתך."
            if offer.get("renewal") else
            f"{offer['brand']} ({offer['tier_he']}) רוצים אותך על {offer['kind_he']}.")
    lines = [head, ""] + CM.deal_lines(offer) + [""]
    if offer["clashes"]:
        lines.append("אחד מימי הצילומים נופל בשבוע של משחק.")
    else:
        lines.append("הצילומים בהפסקת הליגה — לא פוגע בשום דבר.")
    return "\n".join(lines)


def _sponsor_sign(game) -> str:
    _mark(game, "sponsor")
    offer = _pending_deal(game)
    if not offer:
        return "ההצעה ירדה מהשולחן."
    annual = offer.get("annual", offer.get("amount", 0))
    CM.sign_deal(game.deals, offer, game.year)
    # מקדמה בחתימה, ומכאן והלאה זה משלם כל שבוע לאורך כל החוזה
    signing = int(annual * 0.35)
    game.earn_money(signing)
    game.me.media_skill = clamp(game.me.media_skill + offer["media_gain"], 0, 100)
    gain_reputation(game.me, offer["media_gain"] * 0.25)
    game.flags["pending_deal"] = None
    weekly = CM.weekly_retainer(game.deals, 43)
    tail = (f"מקדמה של ₪{signing:,} נכנסה, ומעכשיו התיק המסחרי שלך "
            f"משלם ₪{weekly:,} בשבוע.")
    if offer["clashes"]:
        _trust(game, -3)
        return (f"חתמת עם {offer['brand']} על ₪{annual:,} לעונה. {tail} "
                "יום הצילומים בשבוע המשחק לא עבר בשקט אצל המאמן.")
    return (f"חתמת עם {offer['brand']} על ₪{annual:,} לעונה. {tail} "
            "הצילומים בהפסקה — אף אחד במועדון לא הרים גבה.")


def _sponsor_decline(game) -> str:
    _mark(game, "sponsor")
    offer = _pending_deal(game)
    game.flags["pending_deal"] = None
    if offer and offer["clashes"]:
        _trust(game, 4)
        _attr(game, "mental", 0.4)
        return "סירבת בגלל השבוע של המשחק. הצוות המקצועי שמע, וזכר."
    return "סירבת. הסוכן שלך לא הבין למה, אבל זה הכסף שלך."


register(StoryEvent(
    eid="sponsor_global",
    title="הפגישה בקומה העליונה",
    stages=("player", "veteran"),
    weight=3.0,
    once=False,
    cooldown=40,
    condition=lambda g: (_cool(g, "global", 38) and g.my_club is not None
                         and CM.marketability(
                             g.me, g.my_club.reputation) >= 74),
    body=lambda g: _global_body(g),
    choices=[
        Choice("לחתום", lambda g: _sponsor_sign(g), hint="חוזה רב־שנתי"),
        Choice("לבקש מהסוכן לשפר", lambda g: _global_push(g), hint="הימור"),
        Choice("לא עכשיו", lambda g: _sponsor_decline(g)),
    ],
))


def _global_body(game) -> str:
    """מותג עולמי לא מתקשר — הוא מזמין אותך למשרד."""
    club = game.my_club
    tiers = [t for t in D.SPONSOR_TIERS if t[0] in ("continental", "global")]
    market = CM.marketability(game.me, club.reputation if club else 40)
    tier = tiers[-1] if market >= 80 and game.rng.random() < 0.6 else tiers[0]
    offer = CM.sponsor_offer(game.me, game.rng,
                             club.reputation if club else 40, False,
                             honours=len(game.honours))
    if not offer:
        return ""
    # ההצעה הזאת מגיעה מהדרג הגבוה, לא מהגרלה רגילה
    key, tier_he, min_rep, base, media_mult, brands = tier
    over = max(0.0, market - min_rep) / 40.0
    annual = int(round(base * (1.05 + over * 2.1) *
                       game.rng.uniform(0.92, 1.3) / 1000) * 1000)
    offer.update({"brand": game.rng.choice(brands), "tier": key,
                  "tier_he": tier_he, "annual": annual, "amount": annual,
                  "years": game.rng.randint(3, 5), "media_gain": 9,
                  "clashes": False, "market": round(market, 1),
                  "clauses": [c[0] for c in D.BONUS_CLAUSES[:3]]})
    game.flags["pending_deal"] = offer
    lines = [f"טסת לפגישה. {offer['brand']} — הדרג ה{tier_he}.", "",
             f"\"עקבנו אחריך שנתיים. אנחנו לא מחפשים פרצוף לעונה, "
             f"אנחנו מחפשים מישהו לבנות סביבו.\"", ""]
    lines.extend(CM.deal_lines(offer))
    return "\n".join(lines)


def _global_push(game) -> str:
    """לבקש יותר ממותג עולמי — או שמכבדים אותך, או שמצטננים."""
    _mark(game, "global")
    offer = _pending_deal(game)
    if not offer:
        return "ההצעה ירדה מהשולחן."
    if game.rng.random() < 0.45 + game.me.business / 300.0:
        offer["annual"] = int(offer["annual"] * game.rng.uniform(1.2, 1.5))
        offer["amount"] = offer["annual"]
        CM.sign_deal(game.deals, offer, game.year)
        game.earn_money(int(offer["annual"] * 0.35))
        gain_reputation(game.me, 3)
        game.me.business = clamp(game.me.business + 3, 0, 100)
        game.flags["pending_deal"] = None
        return (f"הסוכן שלך עמד על שלו. {offer['brand']} עלו ל-"
                f"₪{offer['annual']:,} לעונה. חתמת.")
    game.flags["pending_deal"] = None
    game.me.business = clamp(game.me.business + 1, 0, 100)
    return (f"{offer['brand']} אמרו שיחזרו אליך. הם לא חזרו העונה. "
            "לפעמים ההימור לא עובד.")


register(StoryEvent(
    eid="media_job",
    title="הצעה מהתקשורת",
    stages=("player", "veteran"),
    weight=0.9,
    once=False,
    cooldown=22,
    condition=lambda g: (_cool(g, "media", 20) and CM.media_offer(
        g.me, random.Random(g.week * 31 + g.year)) is not None),
    body=lambda g: _media_body(g),
    choices=[
        Choice("לקחת את זה", lambda g: _media_accept(g), hint="כסף וחשיפה"),
        Choice("להישאר מחוץ לאור הזרקורים", lambda g: _media_decline(g)),
    ],
))


def _media_body(game) -> str:
    offer = CM.media_offer(game.me, game.rng)
    if not offer:
        return ""
    game.flags["pending_media"] = offer
    return (f"{offer['name']}.\n\n"
            f"₪{offer['amount']:,}. זה גם אומר שהפנים שלך יהיו בכל מקום, "
            "וזה חרב פיפיות: העיתונות אוהבת את מי שמדבר, עד שהיא לא.")


def _media_accept(game) -> str:
    _mark(game, "media")
    offer = game.flags.get("pending_media")
    if not offer:
        return "ההצעה ירדה."
    game.earn_money(offer["amount"])
    game.me.media_skill = clamp(game.me.media_skill + 7, 0, 100)
    gain_reputation(game.me, 2)
    game.flags["pending_media"] = None
    if game.rng.random() < 0.3:
        _trust(game, -2)
        return (f"לקחת. ₪{offer['amount']:,} בכיס, והמאמן שאל אותך "
                "אם אתה שחקן או פרשן.")
    return f"לקחת. ₪{offer['amount']:,}, וכולם ראו אותך."


def _media_decline(game) -> str:
    _mark(game, "media")
    game.flags["pending_media"] = None
    _trust(game, 2)
    _attr(game, "mental", 0.3)
    return "ויתרת. פחות רעש, יותר אימונים."


register(StoryEvent(
    eid="agent_pitch",
    title="סוכן עם הצעה",
    stages=("player", "veteran"),
    weight=1.1,
    once=False,
    cooldown=26,
    condition=lambda g: (_cool(g, "agent", 24) and g.my_club is not None
                         and g.me.reputation >= 30
                         and g.me.contract.years_left <= 2),
    body=lambda g: _agent_body(g),
    choices=[
        Choice("לתת לו לעבוד", lambda g: _agent_accept(g), hint="פותח דלת למעבר"),
        Choice("אני מסודר איפה שאני", lambda g: _agent_decline(g)),
    ],
))


def _agent_body(game) -> str:
    pitch = CM.agent_pitch(game.me, game.rng, list(game.clubs.values()), game.my_club)
    if not pitch:
        return ""
    game.flags["pending_agent"] = pitch
    return (f"{pitch['agent']} תפס אותך אחרי אימון.\n\n"
            f"\"יש לי קשר ב{pitch['club_name']}. אתה מקבל היום "
            f"₪{game.me.contract.wage:,} לשבוע — שם מדברים על "
            f"₪{pitch['wage']:,}. תן לי לעבוד.\"\n\n"
            f"העמלה שלו: ₪{pitch['fee']:,}.")


def _agent_accept(game) -> str:
    _mark(game, "agent")
    pitch = game.flags.get("pending_agent")
    if not pitch:
        return "הסוכן נעלם."
    game.spend_money(pitch["fee"])
    game.set_flag("agent_target", pitch["club"])
    game.flags["pending_agent"] = None
    _morale(game, 3)
    return (f"שילמת לו מקדמה. הוא כבר מדבר עם {pitch['club_name']} — "
            "בחלון ההעברות זה יהיה על השולחן.")


def _agent_decline(game) -> str:
    _mark(game, "agent")
    game.flags["pending_agent"] = None
    _trust(game, 3)
    return "אמרת לו שאתה מסודר. הידיעה הזו הגיעה למאמן, והוא חייך."


register(StoryEvent(
    eid="foreign_agent",
    title="שיחה מחו\"ל",
    stages=("player", "veteran"),
    weight=1.4,
    once=False,
    cooldown=20,
    condition=lambda g: (_cool(g, "foreign", 18) and g.my_club is not None
                         and SC.foreign_agent(g, random.Random(g.week * 17 + g.year))
                         is not None),
    body=lambda g: _foreign_body(g),
    choices=[
        Choice("להקשיב לו", lambda g: _foreign_accept(g), hint="פותח דלת לחו\"ל"),
        Choice("עוד לא", lambda g: _foreign_decline(g)),
    ],
))


def _foreign_body(game) -> str:
    pitch = SC.foreign_agent(game, game.rng)
    if not pitch:
        return ""
    game.flags["pending_foreign"] = pitch
    return (f"{pitch['agent']} התקשר מ{pitch['country']}.\n\n"
            f"\"אני עובד מול {pitch['club_name']}. הם שולחים אליך צופים "
            f"כבר תקופה — התיק שלך אצלם פתוח ({pitch['score']:.0f} מתוך 100). "
            f"אתה מקבל היום ₪{game.me.contract.wage:,} לשבוע; שם מדברים על "
            f"₪{pitch['wage']:,}.\"\n\n"
            f"העמלה שלו: ₪{pitch['fee']:,}. זה לא אומר שאתה עובר — "
            "זה אומר שיש מי שיפתח את הדלת.")


def _foreign_accept(game) -> str:
    _mark(game, "foreign")
    pitch = game.flags.get("pending_foreign")
    if not pitch:
        return "הקו התנתק."
    game.spend_money(pitch["fee"])
    game.set_flag("agent_target", pitch["club"])
    game.set_flag("open_to_europe", True)
    # עצם זה שיש נציג בשטח מחמם את העניין
    table = SC.interest_map(game)
    table[pitch["club"]] = min(100.0, float(table.get(pitch["club"], 0)) + 9.0)
    game.flags["pending_foreign"] = None
    _morale(game, 4)
    return (f"שילמת לו מקדמה. {pitch['club_name']} יודעים עכשיו שאתה פתוח "
            "לשמוע — ובחלון ההעברות זה יהיה על השולחן.")


def _foreign_decline(game) -> str:
    _mark(game, "foreign")
    game.flags["pending_foreign"] = None
    _trust(game, 3)
    return "אמרת לו שאתה באמצע משהו כאן. הוא השאיר מספר."


register(StoryEvent(
    eid="scout_report",
    title="מה כתבו עליך",
    stages=("academy", "player", "veteran"),
    weight=0.9,
    once=False,
    cooldown=24,
    condition=lambda g: len(SC.watchers(g, SC.NOTICED)) >= 2,
    body=lambda g: _scout_body(g),
    choices=[
        Choice("לעבוד על מה שחסר", lambda g: _scout_work(g), hint="מקצועי"),
        Choice("לא לתת לזה להיכנס לראש", lambda g: _scout_ignore(g)),
    ],
))


def _scout_body(game) -> str:
    ranked = SC.watchers(game, SC.NOTICED)
    if not ranked:
        return ""
    lines = ["הסוכן שלך שלח לך צילום מסך של דוח שדלף.", ""]
    for club, score in ranked[:3]:
        lines.append(f"• {club.name} — {SC.interest_label(score)} ({score:.0f}/100)")
    lines.append("")
    lines.extend(SC.scout_report(game, ranked[0][0]))
    return "\n".join(lines)


def _scout_work(game) -> str:
    ranked = SC.watchers(game, SC.NOTICED)
    row = D.ROLE_BY_KEY.get(game.me.role)
    watched = (list(row[4]) + list(row[5])) if row else list(D.attrs_for(game.me.position))
    worst = min(watched, key=lambda a: game.me.detail.get(a, 10))
    SE.apply_attr(game.me, worst, 0.9)
    _morale(game, 3)
    club = ranked[0][0].name if ranked else "מי שעוקב אחריך"
    return (f"לקחת את זה לאימון. {D.DETAIL_NAMES_HE[worst]} — "
            f"בדיוק מה ש{club} סימנו לך. הצופה הבא יראה משהו אחר.")


def _scout_ignore(game) -> str:
    _morale(game, 5)
    game.me.sharpness = clamp(game.me.sharpness + 4, 0, 100)
    return "סגרת את הטלפון. יש שחקנים שנשברים מזה, ואתה לא אחד מהם."


register(StoryEvent(
    eid="contract_talks",
    title="שולחן המשא ומתן",
    stages=("player", "veteran"),
    weight=8.0,
    once=False,
    cooldown=8,
    condition=lambda g: g.me.contract.years_left <= 0 and g.my_club is not None,
    body=lambda g: (
        f"החוזה שלך נגמר בסוף העונה.\n"
        f"{g.my_club.name} הניחו הצעה על השולחן: "
        f"₪{g.renewal_offer():,} לשבוע."
    ),
    choices=[
        Choice("לחתום מיד",
               lambda g: g.sign_renewal(1.0),
               hint="ביטחון"),
        Choice("לדרוש יותר",
               lambda g: g.demand_raise(),
               hint="הימור על היחסים"),
        Choice("לא לחתום — לצאת חופשי בקיץ",
               lambda g: (g.set_flag("free_agent_soon", True), _trust(g, -14), _fans(g, -8),
                          "לא חתמת. בקיץ תהיה חופשי — ועד אז אתה זר במועדון שלך.")[-1],
               hint="מסוכן, אבל משתלם"),
    ],
))

register(StoryEvent(
    eid="dressing_room_split",
    title="חדר הלבשה מפוצל",
    stages=("player", "veteran"),
    weight=2.0,
    once=False,
    cooldown=30,
    condition=lambda g: g.my_club is not None and g.my_club.manager_trust <= 40,
    body=lambda g: (
        f"חצי מהקבוצה רוצה ש{g.my_club.manager_name} ילך.\n"
        f"מישהו כבר דיבר עם עיתונאי. עכשיו מסתכלים עליך — אתה בין הבכירים."
    ),
    choices=[
        Choice("לתמוך במאמן בפומבי",
               lambda g: (_trust(g, 16), _morale(g, -3), g.set_flag("manager_ally", True),
                          "עמדת מולו והצהרת. חלק מהחבר'ה הפסיקו לדבר איתך. "
                          "המאמן לא יוריד אותך יותר לעולם.")[-1]),
        Choice("להצטרף למרד",
               lambda g: g.join_revolt(),
               hint="עלול לפוצץ את העונה"),
        Choice("לכנס את הקבוצה בלי המאמן",
               lambda g: (_attr(g, "mental", 1.5), _morale(g, 5),
                          g.set_flag("leader_moment", True),
                          "כינסת את כולם. שעה של אמת בלי צוות מקצועי. "
                          "מאותו יום אתה המנהיג של החדר.")[-1],
               hint="מנהיגות"),
    ],
))

register(StoryEvent(
    eid="youngster_threat",
    title="הילד שהגיע לתפוס את המקום",
    stages=("player", "veteran"),
    weight=2.0,
    once=False,
    cooldown=34,
    condition=lambda g: g.me.age >= 26 and g.rival_youngster() is not None,
    body=lambda g: (
        f"{g.rival_youngster().name}, בן {g.rival_youngster().age}, נכנס לקבוצה.\n"
        f"אותה עמדה. אותן רגליים שהיו לך פעם. הצוות מדבר עליו בהתלהבות שכבר לא מדברים עליך."
    ),
    choices=[
        Choice("לקחת אותו תחת חסותך",
               lambda g: g.mentor_youngster(),
               hint="פותח דלת לאימון בעתיד"),
        Choice("להילחם בו על כל דקה",
               lambda g: (_attr(g, "physical", 1.2), _morale(g, -3), _trust(g, 4),
                          "הפכת כל אימון לקרב. שנית בחזרה את הכיסא — לעונה אחת לפחות.")[-1]),
        Choice("לבקש מהמאמן לשחק במקום אחר במגרש",
               lambda g: g.change_position(),
               hint="מאריך קריירה"),
    ],
))

# ===========================================================================
# שלב 3 — ותיק ופרישה
# ===========================================================================

register(StoryEvent(
    eid="body_signals",
    title="הגוף מדבר",
    stages=("veteran",),
    weight=3.0,
    once=False,
    cooldown=30,
    condition=lambda g: g.me.age >= 32,
    body=lambda g: (
        f"אתה בן {g.me.age}. הבוקר לקח לך עשרים דקות לרדת מהמיטה.\n"
        f"הפיזיותרפיסט אומר שאפשר להמשיך — עם מחיר."
    ),
    choices=[
        Choice("להוריד עומסים ולשחק חכם",
               lambda g: (_attr(g, "mental", 1.4), _attr(g, "pace", -0.6),
                          g.me.__setattr__("fitness", 100.0),
                          "התחלת לשחק בראש במקום ברגליים. פחות ספרינטים, יותר מסירות נכונות.")[-1]),
        Choice("זריקות ולהמשיך כרגיל",
               lambda g: g.painkillers(),
               hint="מסוכן"),
        Choice("להתחיל לתכנן את היום שאחרי",
               lambda g: (_morale(g, 2), g.study_during_injury())[-1],
               hint="מכין את הקריירה הבאה"),
    ],
))

register(StoryEvent(
    eid="retirement_call",
    title="ההחלטה",
    stages=("veteran",),
    weight=9.0,
    once=False,
    cooldown=20,
    condition=lambda g: g.retirement_ready(),
    body=lambda g: (
        f"{g.me.age}. {g.me.career.apps + g.me.season.apps} משחקים בקריירה.\n"
        f"{g.me.career.goals + g.me.season.goals} שערים.\n"
        f"הסוכן שואל את השאלה שאתה מתחמק ממנה חודשים:\n"
        f"\"עוד עונה, או שאנחנו מתחילים לדבר על מה שאחרי?\""
    ),
    choices=[
        Choice("עוד עונה אחת. אני עוד מסוגל.",
               lambda g: (_morale(g, 5), g.set_flag("one_more_year", True),
                          "עוד עונה. הגוף ישלם, אבל אתה עוד לא מוכן להוריד את הנעליים.")[-1]),
        Choice("להכריז על פרישה בסוף העונה",
               lambda g: g.announce_retirement(),
               hint="פותח את הפרק הבא"),
    ],
))

register(StoryEvent(
    eid="farewell_match",
    title="משחק הפרידה",
    stages=("retired",),
    weight=10.0,
    condition=lambda g: g.flag("retired_announced"),
    body=lambda g: (
        f"{g.last_club_name()} מארגנים לך משחק פרידה.\n"
        f"האצטדיון מלא. הילדים ביציע לובשים את החולצה עם השם שלך."
    ),
    choices=[
        Choice("לשחק 20 דקות ולצאת לתשואות",
               lambda g: (_rep(g, 6), g.record_honour("משחק פרידה מול אצטדיון מלא"),
                          g.earn_money(700_000),
                          "עשרים דקות, נגיעה אחת שהזכירה לכולם למה. "
                          "יצאת כשכל האצטדיון עומד.")[-1]),
        Choice("לוותר על הטקס ולהיעלם בשקט",
               lambda g: (_rep(g, -2), g.set_flag("quiet_exit", True),
                          "לא הגעת. חלק כיבדו את זה, רובם לא הבינו.")[-1]),
    ],
))

register(StoryEvent(
    eid="next_chapter",
    title="הפרק הבא",
    stages=("retired",),
    weight=12.0,
    condition=lambda g: True,
    body=lambda g: (
        f"עברו שלושה חודשים מאז המשחק האחרון.\n"
        f"הטלפון עדיין מצלצל — אבל עכשיו מציעים לך דברים אחרים.\n\n"
        f"{g.career_options_summary()}"
    ),
    choices=[
        Choice("מסלול אימון — מאמן עוזר במועדון",
               lambda g: g.start_coaching(),
               hint="דורש תעודות אימון"),
        Choice("אולפן — פרשן טלוויזיה",
               lambda g: g.start_punditry(),
               hint="דורש כריזמה תקשורתית"),
        Choice("סוכנות שחקנים",
               lambda g: g.start_agency(),
               hint="דורש ראש עסקי"),
        Choice("לקחת שנה חופש",
               lambda g: (g.set_flag("gap_year", True), _morale(g, 8),
                          "שנה של כלום. משפחה, ים, שינה. "
                          "כשחזרת, הטלפון עדיין צלצל.")[-1]),
    ],
))

# ===========================================================================
# שלב 4 — מאמן ומנג'ר
# ===========================================================================

register(StoryEvent(
    eid="first_manager_offer",
    title="הצעה לשבת בכיסא הגדול",
    stages=("coach",),
    weight=8.0,
    condition=lambda g: g.me.coaching >= 45,
    body=lambda g: (
        f"{g.manager_job_offer_name()} מחפשים מנג'ר.\n"
        f"הם רוצים מישהו שמכיר את המועדון מבפנים. הם רוצים אותך.\n"
        f"התנאי: אתה לוקח את זה עכשיו, באמצע משבר."
    ),
    choices=[
        Choice("לקחת את התפקיד",
               lambda g: g.take_manager_job(),
               hint="הופך אותך למנג'ר ראשי"),
        Choice("עוד שנה כעוזר, ללמוד עוד",
               lambda g: (g.me.__setattr__("coaching", clamp(g.me.coaching + 10, 0, 100)),
                          "נשארת ללמוד. ידע האימון שלך קפץ — וההצעה הבאה תהיה טובה יותר.")[-1]),
    ],
))

register(StoryEvent(
    eid="board_meeting",
    title="ישיבת הנהלה",
    stages=("manager",),
    weight=4.0,
    once=False,
    cooldown=12,
    condition=lambda g: g.week in (6, 13, 20),
    body=lambda g: (
        f"היו\"ר פורש טבלה על השולחן.\n"
        f"\"ציפינו ל{g.my_club.season_expectation}. אנחנו במקום {g.league_position()}.\n"
        f"תסביר לי מה קורה — ובלי סיסמאות.\""
    ),
    choices=[
        Choice("לקחת אחריות מלאה",
               lambda g: (g.board(6), "לקחת הכל על עצמך. ההנהלה נתנה לך עוד זמן.")[-1]),
        Choice("לדרוש תקציב להעברות",
               lambda g: g.demand_budget(),
               hint="הימור על היחסים"),
        Choice("להאשים את השופטים ואת הפציעות",
               lambda g: (g.board(-9), _fans(g, 4),
                          "האוהדים אהבו את זה. ההנהלה ספרה את המילים ולא התרשמה.")[-1]),
    ],
))

register(StoryEvent(
    eid="star_wants_out",
    title="הכוכב רוצה ללכת",
    stages=("manager",),
    weight=3.0,
    once=False,
    cooldown=34,
    condition=lambda g: g.squad_star() is not None,
    body=lambda g: (
        f"{g.squad_star().name} ({g.squad_star().overall}) נכנס למשרד עם הסוכן.\n"
        f"\"יש הצעה מבחוץ. אני רוצה שתשחרר אותי.\""
    ),
    choices=[
        Choice("למכור ולהשקיע בסגל",
               lambda g: g.sell_star(),
               hint="תקציב ↑, איכות ↓"),
        Choice("לסרב ולהחזיק אותו בכוח",
               lambda g: g.keep_star(),
               hint="מורל הקבוצה בסיכון"),
        Choice("להציע לו את הקפטן והעלאה",
               lambda g: g.promote_star(),
               hint="עולה כסף"),
    ],
))

register(StoryEvent(
    eid="wonderkid",
    title="ילד מהנוער",
    stages=("manager",),
    weight=3.0,
    once=False,
    cooldown=40,
    condition=lambda g: g.my_club is not None,
    body=lambda g: (
        "מאמן הנוער מביא לך שם.\n"
        "בן 17. באימון הבוגרים הוריד שני בלמים בתנועה אחת."
    ),
    choices=[
        Choice("להעלות אותו לסגל הבוגרים",
               lambda g: g.promote_youth(),
               hint="הימור ארוך טווח"),
        Choice("להשאיר אותו בנוער עוד שנה",
               lambda g: (g.board(2), "השארת אותו למטה. בטוח, אבל שקט מדי.")[-1]),
    ],
))

register(StoryEvent(
    eid="sack_race",
    title="השם שלך בעיתון",
    stages=("manager",),
    weight=6.0,
    once=False,
    cooldown=22,
    condition=lambda g: g.my_club is not None and g.my_club.board_confidence <= 32,
    body=lambda g: (
        f"\"{g.me.name} על הכוונת\" — כותרת ראשית.\n"
        f"אמון ההנהלה: {int(g.my_club.board_confidence)}%. שלושה משחקים להוכיח."
    ),
    choices=[
        Choice("לשנות הכל — טקטיקה, הרכב, הכל",
               lambda g: g.radical_change(),
               hint="הימור גדול"),
        Choice("להמשיך בדרך שלי",
               lambda g: (g.board(-2), g.set_flag("stubborn", True),
                          "לא זזת מילימטר. אם זה יעבוד — אתה גאון. אם לא — אתה מובטל.")[-1]),
        Choice("להתפטר בכבוד",
               lambda g: g.resign(),
               hint="יוצא בתנאים שלך"),
    ],
))

register(StoryEvent(
    eid="bigger_job",
    title="מועדון גדול מתקשר",
    stages=("manager",),
    weight=4.0,
    once=False,
    cooldown=34,
    condition=lambda g: g.manager_suitor() is not None,
    body=lambda g: (
        f"{g.manager_suitor().name} רוצים אותך.\n"
        f"תקציב אחר, לחץ אחר, אצטדיון אחר.\n"
        f"ובמועדון שלך יש חוזה ואוהדים שקראו לך בשם."
    ),
    choices=[
        Choice("לעבור למועדון הגדול",
               lambda g: g.move_manager_job(),
               hint="מוניטין ↑↑"),
        Choice("להישאר ולסיים את הפרויקט",
               lambda g: (g.board(10), _fans(g, 12), _rep(g, 3),
                          "נשארת. בעיר הזאת לא ישכחו לך את זה.")[-1]),
    ],
))

# ===========================================================================
# שלב 5 — אחרי הכל
# ===========================================================================

register(StoryEvent(
    eid="director_offer",
    title="מהספסל למשרד",
    stages=("manager",),
    weight=3.0,
    condition=lambda g: g.me.age >= 50 and g.me.business >= 30,
    body=lambda g: (
        "הבעלים מציע לך לעלות קומה: מנהל ספורטיבי.\n"
        "בלי אימונים בגשם, בלי שריקות. רק החלטות — ואחריות על כולן."
    ),
    choices=[
        Choice("לעלות למשרד",
               lambda g: g.become_director(),
               hint="שלב קריירה חדש"),
        Choice("אני שייך לקו הצדדי",
               lambda g: (_morale(g, 4), "סירבת. הדשא עוד קורא לך.")[-1]),
    ],
))

register(StoryEvent(
    eid="buy_childhood_club",
    title="המועדון שבו התחלת",
    stages=("pundit", "agent", "director", "manager", "retired"),
    weight=2.5,
    condition=lambda g: g.money >= 4_000_000,
    body=lambda g: (
        f"{g.first_club_name()} — המועדון שבו התחלת — בקשיים.\n"
        f"מציעים לך לרכוש שליטה. המחיר: ₪4,000,000 והרבה כאב ראש."
    ),
    choices=[
        Choice("לקנות את המועדון",
               lambda g: g.buy_club(),
               hint="₪4,000,000 — הופך אותך לבעלים"),
        Choice("לתרום ולהישאר בחוץ",
               lambda g: (g.spend_money(500_000), _rep(g, 3),
                          "תרמת חצי מיליון. שם המגרש הפך לשם שלך.")[-1]),
    ],
))

register(StoryEvent(
    eid="hall_of_fame",
    title="היכל התהילה",
    stages=("retired", "coach", "manager", "pundit", "agent", "director", "owner"),
    weight=4.0,
    condition=lambda g: g.me.career.apps >= 250 or len(g.honours) >= 3,
    body=lambda g: (
        f"מכתב רשמי: אתה נכנס להיכל התהילה.\n"
        f"{g.me.career.apps} משחקים. {g.me.career.goals} שערים. "
        f"{len(g.honours)} הישגים."
    ),
    choices=[
        Choice("לנאום ולהודות לכולם",
               lambda g: (_rep(g, 8), g.record_honour("היכל התהילה"),
                          "עמדת שם עם הנאום ביד ולא הסתכלת בו אפילו פעם אחת.")[-1]),
    ],
))

register(StoryEvent(
    eid="child_debut",
    title="הדור הבא",
    stages=("coach", "manager", "pundit", "agent", "director", "owner", "legend"),
    weight=2.0,
    condition=lambda g: g.me.age >= 45,
    body=lambda g: (
        "הבן שלך חתם חוזה נעורים.\n"
        "מאמן הנוער אומר שהוא טוב יותר ממה שאתה היית בגיל הזה.\n"
        "העיתונות כבר כותבת את השם המשפחה בכותרות."
    ),
    choices=[
        Choice("להגן עליו מהתקשורת",
               lambda g: (_rep(g, 2), g.set_flag("protective_parent", True),
                          "סגרת את הדלת בפני כולם. הוא גדל בשקט.")[-1]),
        Choice("לאמן אותו בעצמך",
               lambda g: (g.me.__setattr__("coaching", clamp(g.me.coaching + 5, 0, 100)),
                          g.set_flag("coaching_child", True),
                          "כל בוקר, שעה לפני כולם, במגרש הריק. "
                          "זה הדבר הכי טוב שעשית מאז שפרשת.")[-1]),
    ],
))


# ---------------------------------------------------------------------------
# בחירת אירוע
# ---------------------------------------------------------------------------

def weeks_since(game, eid: str) -> Optional[int]:
    """כמה שבועות עברו מאז שהאירוע הזה נורה. None אם מעולם לא."""
    stamp = game.flags.get("last_fired", {}).get(eid)
    if stamp is None:
        return None
    return (game.year - stamp[0]) * 43 + (game.week - stamp[1])


def note_fired(game, eid: str) -> None:
    """מסמן מתי אירוע נורה, כדי שלא יחזור על עצמו בשבוע הבא."""
    log = game.flags.setdefault("last_fired", {})
    log[eid] = [game.year, game.week]


def eligible_events(game) -> List[StoryEvent]:
    """מחזיר את כל האירועים שיכולים לקרות עכשיו."""
    out = []
    for event in REGISTRY:
        if event.stages and game.stage not in event.stages:
            continue
        if event.once and event.eid in game.fired_events:
            continue
        if not event.once:
            gap = weeks_since(game, event.eid)
            if gap is not None and gap < event.cooldown:
                continue
        try:
            if not event.condition(game):
                continue
        except Exception:
            continue
        out.append(event)
    return out


def pick_event(game, rng: random.Random, chance: float = 0.34) -> Optional[StoryEvent]:
    """בוחר אירוע עלילה לשבוע הנוכחי (או None)."""
    candidates = eligible_events(game)
    if not candidates:
        return None
    forced = [e for e in candidates if e.weight >= 8.0]
    if not forced and rng.random() > chance:
        return None
    pool = forced or candidates
    total = sum(e.weight for e in pool)
    roll = rng.random() * total
    upto = 0.0
    for event in pool:
        upto += event.weight
        if roll <= upto:
            return event
    return pool[-1]


def find_event(eid: str) -> Optional[StoryEvent]:
    for event in REGISTRY:
        if event.eid == eid:
            return event
    return None


# ---------------------------------------------------------------------------
# רישום החבילה מונחת-הנתונים
# ---------------------------------------------------------------------------

def _pack_choice(row: dict):
    """הופך שורת בחירה מהטבלה ל-Choice אמיתי."""
    return Choice(row["label"],
                  lambda game, row=row: SE.choice_result(game, row),
                  row.get("hint", ""))


def register_pack(pack=PACK) -> int:
    """מרשם את כל האירועים שנכתבו כנתונים. מחזיר כמה נוספו."""
    added = 0
    for row in pack:
        when = row.get("when")
        register(StoryEvent(
            eid=row["eid"],
            title=row["title"],
            stages=tuple(row.get("stages", ())),
            weight=float(row.get("weight", 1.0)),
            once=bool(row.get("once", False)),
            cooldown=int(row.get("cooldown", 30)),
            condition=lambda g, when=when: SE.matches(g, when),
            body=lambda g, text=row["body"]: SE.fill(text, g),
            choices=[_pack_choice(c) for c in row["choices"]],
        ))
        added += 1
    return added


PACK_COUNT = register_pack()
