# -*- coding: utf-8 -*-
"""
football_manager.cli
====================
ממשק טקסט בעברית למשחק. עטיפה דקה מסביב ל-GameState.
"""

from __future__ import annotations

import os
import sys
import random
from typing import List, Optional

from . import data as D
from .game import CUP_WEEKS, SAVE_DIR, SEASON_WEEKS, GameState
from . import development as DEV
from . import scouting as SC
from . import wealth as WL
from . import tactics as TA
from . import models as MDL
from . import knowledge as KN
from . import coaching as COACH
from . import mentor as MN
from . import commercial as CM
from .engine import MENTALITIES, PRESSING

LINE = "─" * 52
DOUBLE = "═" * 52


# ---------------------------------------------------------------------------
# עזרי פלט
# ---------------------------------------------------------------------------

def out(text: str = "") -> None:
    print(text)


def header(title: str) -> None:
    out()
    out(DOUBLE)
    out(f"  {title}")
    out(DOUBLE)


def ask(prompt: str, default: str = "") -> str:
    try:
        answer = input(f"{prompt} ").strip()
    except (EOFError, KeyboardInterrupt):
        out()
        return default
    return answer or default


def choose(prompt: str, options: List[str], default: int = 0) -> int:
    """תפריט ממוספר. מחזיר אינדקס."""
    out()
    for idx, label in enumerate(options, start=1):
        out(f"  {idx}. {label}")
    while True:
        raw = ask(f"\n{prompt} [1-{len(options)}]:", str(default + 1))
        try:
            value = int(raw)
        except ValueError:
            out("מספר לא תקין.")
            continue
        if 1 <= value <= len(options):
            return value - 1
        out("מחוץ לטווח.")


# ---------------------------------------------------------------------------
# מסכי מידע
# ---------------------------------------------------------------------------

def show_profile(game: GameState) -> None:
    me = game.me
    club = game.my_club
    header(f"{me.name} — {D.CAREER_STAGES_HE.get(game.stage, game.stage)}")
    out(f"גיל {me.age} | {me.position_he} | {me.nationality}")
    if club:
        out(f"מועדון: {club.name} ({club.nickname})")
    if game.stage in ("academy", "player", "veteran"):
        out(f"דירוג כללי: {me.overall}  (פוטנציאל {me.potential})")
        out(f"תפקיד: {MDL.role_name(me)} | אישיות: {MDL.personality_name(me)}")
        out(LINE)
        # לוח התכונות המלא, בארבע קבוצות — כמו במקור
        allowed = set(D.attrs_for(me.position))
        for _key, label, rows in D.ATTR_GROUPS:
            visible = [(a, he) for a, he in rows if a in allowed]
            if not visible:
                continue
            out(f"— {label} —")
            for attr, he in visible:
                value = me.detail.get(attr, 10)
                bar = "█" * value + "░" * (20 - value)
                out(f"  {he:<16} {value:>2} {bar}")
        out(LINE)
        out(f"כושר: {int(me.form)} | מורל: {int(me.morale)} | "
            f"רעננות: {int(me.fitness)} | מוניטין: {int(me.reputation)}")
        if me.injury_weeks > 0:
            out(f"🚑 פצוע: {me.injury_name} — עוד {me.injury_weeks} שבועות")
        out(f"חוזה: ₪{me.contract.wage:,} לשבוע, {me.contract.years_left} עונות")
        out(f"שווי שוק: ₪{me.value:,}")
        if club:
            out(f"אמון המאמן: {int(club.manager_trust)}%")
        season, career = me.season, me.career
        out(LINE)
        out(f"העונה:  {season.apps} משחקים | {season.goals} שערים | "
            f"{season.assists} בישולים | ציון {season.avg_rating}")
        out(f"קריירה: {career.apps} משחקים | {career.goals} שערים | "
            f"{career.assists} בישולים | ציון {career.avg_rating}")
    else:
        out(f"ידע אימון: {int(me.coaching)} | תעודות: {me.badges}/4")
        out(f"כריזמה תקשורתית: {int(me.media_skill)} | ראש עסקי: {int(me.business)}")
        if club:
            out(f"אמון ההנהלה: {int(club.board_confidence)}% | "
                f"אהדת הקהל: {int(club.fan_support)}%")
        career = me.career
        out(f"קריירת השחקן: {career.apps} משחקים, {career.goals} שערים")
    out(f"נבחרת: {game.caps} הופעות, {game.intl_goals} שערים")
    out(f"בחשבון: ₪{game.money:,}")
    if me.traits:
        out("אופי: " + ", ".join(D.TRAITS[t]["name"] for t in me.traits if t in D.TRAITS))


def show_table(game: GameState, league_id: Optional[str] = None) -> None:
    league_id = league_id or game.my_league or "top"
    name = game._league_name(league_id)
    header(f"טבלת {name} — עונת {game.year}/{game.year + 1}")
    out(f"{'#':<3}{'קבוצה':<20}{'מש':>4}{'נצ':>4}{'תק':>4}{'הפ':>4}{'הפרש':>6}{'נק':>5}")
    out(LINE)
    my_club = game.my_club
    for idx, row in enumerate(game.standings(league_id), start=1):
        club = game.clubs[row.club_id]
        mark = "◀" if my_club and club.cid == my_club.cid else " "
        out(f"{idx:<3}{club.name:<20}{row.played:>4}{row.won:>4}{row.drawn:>4}"
            f"{row.lost:>4}{row.gd:>6}{row.points:>5} {mark}")


def show_squad(game: GameState) -> None:
    club = game.my_club
    if not club:
        out("אין לך מועדון כרגע.")
        return
    header(f"סגל {club.name}")
    squad = [game.players[p] for p in club.squad if p in game.players]
    squad.sort(key=lambda p: (-p.overall))
    for player in squad:
        mark = "👤" if player.pid == game.me_id else "  "
        status = ""
        if player.injury_weeks > 0:
            status = f"🚑{player.injury_weeks}ש"
        out(f"{mark} {player.name:<20}{player.position_he:<12}גיל {player.age:<4}"
            f"כללי {player.overall:<4}{status}")
    out(LINE)
    out(f"מערך: {club.formation} | מאמן: {club.manager_name}")


def show_news(game: GameState) -> None:
    header("יומן הקריירה")
    if game.honours:
        out("🏆 הישגים:")
        for honour in game.honours:
            out(f"   • {honour}")
        out(LINE)
    for item in game.news[-18:]:
        out(f"• {item}")


def show_history(game: GameState) -> None:
    header("סיכום עונות")
    for row in game.history:
        out(f"{row['year']}: {D.CAREER_STAGES_HE.get(row['stage'], row['stage'])} — "
            f"{row['club']} | {row['apps']} משחקים, {row['goals']} שערים")


def show_tactics(game: GameState) -> None:
    """תפריט טקטיקה למנג'ר."""
    club = game.my_club
    if not club:
        return
    formations = list(D.FORMATIONS.keys())
    mentalities = list(MENTALITIES.keys())
    pressings = list(PRESSING.keys())
    header("חדר הטקטיקה")
    out(f"מערך נוכחי: {game.tactics.get('formation', club.formation)}")
    out(f"מנטליות: {MENTALITIES[game.tactics.get('mentality', 'balanced')][0]}")
    out(f"לחץ: {PRESSING[game.tactics.get('pressing', 'medium')][0]}")

    idx = choose("בחר מערך", formations)
    game.tactics["formation"] = formations[idx]
    club.formation = formations[idx]
    idx = choose("בחר מנטליות", [MENTALITIES[m][0] for m in mentalities])
    game.tactics["mentality"] = mentalities[idx]
    idx = choose("בחר לחץ", [PRESSING[p][0] for p in pressings])
    game.tactics["pressing"] = pressings[idx]
    out("\n✅ הטקטיקה עודכנה.")


def show_offer(game: GameState) -> None:
    offer = game.flag("pending_offer")
    if not offer:
        out("אין הצעות פתוחות.")
        return
    club = game.clubs[offer["club"]]
    header("הצעת העברה")
    out(f"{club.name} ({club.nickname}) — {game._league_name(club.league_id)}")
    out(f"מוניטין המועדון: {club.reputation} | שכר מוצע: ₪{offer['wage']:,} לשבוע")
    out(f"החוזה הנוכחי שלך: ₪{game.me.contract.wage:,} לשבוע")
    idx = choose("מה תעשה?", ["לחתום ולעבור", "לדחות ולהישאר", "להשאיר פתוח"])
    if idx == 0:
        out("\n" + game.accept_offer())
    elif idx == 1:
        out("\n" + game.reject_offer())


def show_fixture(game: GameState) -> None:
    fixture = game.my_fixture()
    if not fixture:
        out("📅 השבוע אין לך משחק.")
        return
    home, away = fixture
    club = game.my_club
    comp = CUP_WEEKS.get(game.week, "ליגה")
    place = "בית" if club and club.cid == home else "חוץ"
    rival = game.clubs[away if club and club.cid == home else home]
    out(f"📅 {comp}: מול {rival.name} ({place})")


# ---------------------------------------------------------------------------
# אירועי עלילה
# ---------------------------------------------------------------------------

def play_event(game: GameState) -> None:
    event = game.pending_event()
    if not event:
        return
    header(f"📖 {event.title}")
    out(game.pending_event_text())
    out()
    labels = []
    for choice in event.choices:
        labels.append(choice.label + (f"   ({choice.hint})" if choice.hint else ""))
    idx = choose("מה אתה בוחר?", labels)
    outcome = game.resolve_event(idx)
    out()
    out(LINE)
    out(outcome)
    out(LINE)
    ask("\n[Enter להמשך]")


# ---------------------------------------------------------------------------
# שבוע
# ---------------------------------------------------------------------------

def play_week(game: GameState) -> None:
    actions = game.available_actions()
    labels = [label for _, label in actions]
    idx = choose("על מה נעבוד השבוע?", labels,
                 default=_default_action_index(game, actions))
    game.set_action(actions[idx][0])

    if game.stage in ("academy", "player", "veteran"):
        pick = choose("עצימות האימון", ["רגילה", "גבוהה (סיכון פציעה)", "קלה"])
        game.intensity = {0: 1.0, 1: 1.3, 2: 0.75}[pick]

    report = game.advance_week()
    header(f"שבוע {report.week} — עונת {game.year}/{game.year + 1}")
    for line in report.lines:
        out(line)
    ask("\n[Enter להמשך]")
    if report.event_id:
        play_event(game)


def _default_action_index(game: GameState, actions) -> int:
    keys = [key for key, _ in actions]
    me = game.me
    if me.injury_weeks > 0 and "rest" in keys:
        return keys.index("rest")
    if me.fitness < 45 and "rest" in keys:
        return keys.index("rest")
    if game.training_focus in keys:
        return keys.index(game.training_focus)
    return 0


# ---------------------------------------------------------------------------
# תפריט ראשי במשחק
# ---------------------------------------------------------------------------

def status_bar(game: GameState) -> None:
    me = game.me
    club = game.my_club
    header(f"{me.name} · {D.CAREER_STAGES_HE.get(game.stage, game.stage)} · "
           f"עונה {game.year}/{game.year + 1} · שבוע {game.week}/{SEASON_WEEKS}")
    if club:
        pos = game.league_position()
        out(f"{club.name} — מקום {pos} ב{game._league_name(club.league_id)}")
    if game.stage in ("academy", "player", "veteran"):
        out(f"כללי {me.overall} | כושר {int(me.form)} | מורל {int(me.morale)} | "
            f"רעננות {int(me.fitness)}"
            + (f" | 🚑 {me.injury_weeks}ש" if me.injury_weeks else ""))
    show_fixture(game)


def game_loop(game: GameState) -> None:
    while not game.game_over:
        if game.pending_event_id:
            play_event(game)
            continue
        status_bar(game)
        options = ["▶️  להתקדם שבוע", "👤 פרופיל", "📊 טבלה", "👥 סגל",
                   "📰 יומן והישגים", "📚 היסטוריית עונות"]
        keys = ["week", "profile", "table", "squad", "news", "history"]
        if game.stage in ("youth", "academy", "player", "veteran"):
            options.append("🧭 מסלול פיתוח")
            keys.append("plan")
            options.append("👀 מי עוקב אחריי")
            keys.append("scouts")
            options.append("🧠 המערכת והתפקיד שלי")
            keys.append("system")
            options.append("🧭 המנטור שלי")
            keys.append("mentor")
            options.append("📊 איך התפתחתי")
            keys.append("growth")
        options.append("💼 חסויות ונכסים")
        keys.append("money")
        if game.stage in ("manager", "coach"):
            options.append("🧠 טקטיקה")
            keys.append("tactics")
        if game.flag("pending_offer"):
            options.append("📨 הצעת העברה")
            keys.append("offer")
        options += ["💾 שמירה", "🚪 יציאה"]
        keys += ["save", "quit"]

        key = keys[choose("מה עכשיו?", options)]
        if key == "week":
            play_week(game)
        elif key == "profile":
            show_profile(game)
            ask("\n[Enter]")
        elif key == "table":
            show_table(game)
            ask("\n[Enter]")
        elif key == "squad":
            show_squad(game)
            ask("\n[Enter]")
        elif key == "news":
            show_news(game)
            ask("\n[Enter]")
        elif key == "history":
            show_history(game)
            ask("\n[Enter]")
        elif key == "plan":
            show_plan(game)
        elif key == "scouts":
            show_scouts(game)
            ask("\n[Enter]")
        elif key == "system":
            show_system(game)
        elif key == "mentor":
            show_mentor(game)
        elif key == "growth":
            show_growth(game)
            ask("\n[Enter]")
        elif key == "money":
            show_money(game)
        elif key == "tactics":
            show_tactics(game)
            ask("\n[Enter]")
        elif key == "offer":
            show_offer(game)
            ask("\n[Enter]")
        elif key == "save":
            path = game.save()
            out(f"💾 נשמר: {path}")
            ask("\n[Enter]")
        elif key == "quit":
            if choose("לשמור לפני יציאה?", ["כן", "לא"]) == 0:
                out(f"💾 נשמר: {game.save()}")
            return
    epilogue(game)


def epilogue(game: GameState) -> None:
    me = game.me
    header("סוף הדרך")
    out(f"{me.name}")
    out(f"{me.career.apps} משחקים · {me.career.goals} שערים · "
        f"{me.career.assists} בישולים")
    out(f"נבחרת: {game.caps} הופעות")
    out(f"הון: ₪{game.money:,}")
    out(LINE)
    if game.honours:
        for honour in game.honours:
            out(f"🏆 {honour}")
    else:
        out("בלי תארים — אבל עם קריירה.")
    out(LINE)
    out(_verdict(game))


def _verdict(game: GameState) -> str:
    score = len(game.honours) * 2 + game.me.career.apps / 100 + game.caps / 10
    if score > 18:
        return "אגדה. ילדים ייוולדו עם השם שלך על הגב."
    if score > 10:
        return "קריירה גדולה. האוהדים יזכרו כל אחד מהתארים."
    if score > 5:
        return "קריירה מכובדת מאוד. עשית את זה כמו שצריך."
    if score > 2:
        return "קריירה יפה. לא כולם מגיעים עד לשם."
    return "לא הכל הלך. אבל שיחקת כדורגל בשביל להתפרנס — וזה משהו."


# ---------------------------------------------------------------------------
# פתיחת משחק
# ---------------------------------------------------------------------------

def new_game_wizard() -> GameState:
    header("⚽ קריירה חדשה")
    role = ["player", "manager"][choose(
        "מה המסלול?", ["שחקן — מהמגרש ועד הפרישה ומה שאחריה",
                       "מנג'ר — ישר לספסל האימונים"])]
    name = ask("איך קוראים לך?", "עומר לוי" if role == "player" else "דני מנג'ר")
    if role == "player":
        positions = [f"{D.POSITION_NAMES_HE[p]} ({p})" for p in D.POSITIONS]
        position = D.POSITIONS[choose("באיזו עמדה אתה משחק?", positions, default=9)]
    else:
        position = "CM"
    low, high, default_age = (32, 62, 42) if role == "manager" else (13, 38, 15)

    starters = [c for c in _club_pool() if c[3] in ("top", "national")]
    starters.sort(key=lambda c: c[4])
    labels = [f"{c[1]} — {c[2]} (מוניטין {c[4]})" for c in starters]
    club_idx = choose("באיזה מועדון אתה מתחיל?", labels, default=len(labels) // 2)
    club_id = starters[club_idx][0]

    while True:
        raw = ask(f"בן כמה אתה מתחיל? [{low}-{high}]:", str(default_age))
        try:
            age = int(raw)
        except ValueError:
            out("מספר לא תקין.")
            continue
        if low <= age <= high:
            break
        out(f"הגיל חייב להיות בין {low} ל-{high}.")
    game = GameState.new_game(name, position, club_id, age=age, role=role)
    header("הסיפור מתחיל")
    if role == "manager":
        out(f"{game.me.name}, בן {game.me.age}, המנג'ר של {game.my_club.name}.")
        out(f"ידע אימון: {int(game.me.coaching)} · תעודות: {game.me.badges}/4")
        out(f"ציפיית ההנהלה: {game.my_club.season_expectation}.")
    else:
        out(f"{game.me.name}, בן {game.me.age}, {game.me.position_he} של "
            f"{game.my_club.name}.")
        out(f"דירוג נוכחי: {game.me.overall}. מה שיהיה — תלוי בך.")
    ask("\n[Enter כדי להתחיל]")
    return game


def _club_pool():
    return list(D.CLUBS)


def list_saves() -> List[str]:
    if not os.path.isdir(SAVE_DIR):
        return []
    return sorted(os.path.join(SAVE_DIR, f) for f in os.listdir(SAVE_DIR)
                  if f.endswith(".json"))


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if "--demo" in argv:
        return demo(argv)

    header("⚽  קריירה — משחק ניהול כדורגל")
    out("מנער בקבוצת הנוער ועד המשרד של הבעלים.")
    saves = list_saves()
    options = ["משחק חדש"]
    if saves:
        options.append("טעינת משחק")
    options.append("יציאה")
    idx = choose("בחר", options)
    if options[idx] == "יציאה":
        return 0
    if options[idx] == "טעינת משחק":
        pick = choose("איזה משחק?", [os.path.basename(s)[:-5] for s in saves])
        game = GameState.load(saves[pick])
    else:
        game = new_game_wizard()
    game_loop(game)
    return 0


def demo(argv: List[str]) -> int:
    """הרצה אוטומטית להדגמה: מספר עונות בלי קלט משתמש."""
    seasons = 3
    for arg in argv:
        if arg.startswith("--seasons="):
            seasons = int(arg.split("=")[1])
    rng = random.Random(7)
    game = GameState.new_game("דמו כהן", "ST", "hapoel_ayalon", age=17, seed=1234)
    header("הדגמה אוטומטית")
    out(f"{game.me.name} — {game.me.position_he} של {game.my_club.name}, "
        f"דירוג {game.me.overall}")
    for _ in range(seasons):
        while True:
            if game.pending_event_id:
                event = game.pending_event()
                out(f"\n📖 {event.title}")
                out(game.pending_event_text())
                pick = rng.randrange(len(event.choices))
                out(f"➡️  {event.choices[pick].label}")
                out(game.resolve_event(pick))
                continue
            actions = [key for key, _ in game.available_actions()]
            game.set_action(rng.choice(actions))
            report = game.advance_week()
            for line in report.lines:
                out(line)
            if report.season_ended or game.game_over:
                break
        if game.game_over:
            break
    show_profile(game)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# ---------------------------------------------------------------------------
# מסלול, סקאוטינג, כסף
# ---------------------------------------------------------------------------

def show_plan(game: GameState) -> None:
    """מסלול הפיתוח — מה צריך להיות לך ומתי."""
    info = DEV.plan_summary(game)
    if not info["chosen"]:
        out("\n🧭 מסלול פיתוח — בחר דגם שחקן, וקבל יעדים לפי גיל.\n")
        rows = info["options"]
        for row in rows:
            out(f"  {row['name']} — {row['desc']}")
            out(f"     מתמקד ב: {', '.join(row['attrs'])}")
        idx = choose("איזה שחקן אתה רוצה להיות?",
                     [r["name"] for r in rows] + ["עוד לא"])
        if idx < len(rows):
            out("\n" + DEV.set_plan(game, rows[idx]["key"]))
        ask("\n[Enter]")
        return
    out(f"\n🧭 {info['name']} — {info['desc']}")
    out(f"אבני דרך: {info['done']}/{info['total']}"
        + ("  · 💎 פריצה הושלמה" if info["breakthrough"] else ""))
    for row in info["milestones"]:
        mark = "✅" if row["claimed"] else ("🟡" if row["met"] else
                                           "⛔" if row["late"] else "▫️")
        needs = ", ".join(f"{p['name']} {p['have']}/{p['need']}" for p in row["needs"])
        out(f"  {mark} גיל {row['age']}: {needs}")
    if info["next"]:
        out("\n" + info["next"])
    if info["focus"]:
        out(f"מומלץ להתאמן השבוע על: {D.ATTRIBUTE_NAMES_HE[info['focus']]}")
    if choose("להחליף מסלול?", ["לא", "כן"]) == 1:
        rows = DEV.options_for(game.me.position)
        idx = choose("לאיזה מסלול?", [r[1] for r in rows] + ["ביטול"])
        if idx < len(rows):
            out("\n" + DEV.set_plan(game, rows[idx][0]))
            ask("\n[Enter]")


def show_system(game: GameState) -> None:
    """הטקטיקה של המאמן, ומה התפקיד שלך בתוכה."""
    club = game.my_club
    me = game.me
    if not club:
        out("\nאין לך מועדון.")
        return
    out("")
    for line in TA.describe(club):
        out("  " + line)
    fit, note = TA.suits_player(club, me)
    out("")
    out(f"  התאמה לסגנון: {fit:.0f}/100 — {note}")
    fit_note = TA.role_fit_note(me)
    if fit_note:
        out("  " + fit_note)
    out(f"  עומס הסגנון על הגוף: {TA.fitness_cost(club, me):.2f}×")
    options = D.roles_for(me.position)
    out("")
    out("  תפקידים אפשריים בעמדה שלך:")
    for row in options:
        mark = "★" if row[0] == me.role else " "
        out(f"   {mark} {row[1]:<18} {MDL.role_suitability(me, row[0]):>3.0f}  {row[6]}")
    idx = choose("לבקש תפקיד אחר?", [r[1] for r in options] + ["לא עכשיו"],
                 default=len(options))
    if idx < len(options):
        out("\n" + TA.request_role(game, options[idx][0]))
        ask("\n[Enter]")


def show_scouts(game: GameState) -> None:
    """מי עוקב אחריך, ומה כתוב בתיק."""
    ranked = SC.watchers(game)
    out("\n👀 מי עוקב אחריך")
    if not ranked:
        out("  אף אחד עדיין לא פתח עליך תיק. תמשיך לשחק.")
        return
    for club, score in ranked[:8]:
        country = D.club_country(club.cid, club.league_id)
        out(f"  {club.name} ({country}) — {SC.interest_label(score)} "
            f"[{score:.0f}/100]")
    out("")
    for line in SC.scout_report(game, ranked[0][0]):
        out("  " + line)


def show_money(game: GameState) -> None:
    """תיק החסויות והנכסים."""
    out(f"\n💼 מזומן: ₪{int(game.money):,}")
    if game.deals:
        out(f"\n📄 חסויות פעילות (₪{CM.portfolio_total(game.deals):,} לעונה):")
        for deal in game.deals:
            out(f"  {deal['brand']} ({deal['tier_he']}) — ₪{deal['annual']:,} "
                f"לעונה, נותרו {deal['years_left']} שנים")
            for key in deal.get("clauses", ()):
                text = CM.clause_text(key, deal["annual"])
                if text:
                    out("     • " + text)
    else:
        out("\n📄 אין לך חסויות פעילות.")

    info = WL.summary(game)
    out(f"\n🏦 שווי נטו: ₪{info['net_worth']:,} "
        f"(נכסים ₪{info['assets']:,}, תשואה צפויה ₪{info['yearly']:,} לשנה)")
    for index, item in enumerate(info["items"]):
        delta = item["value"] - item["paid"]
        sign = "+" if delta >= 0 else "-"
        out(f"  [{index}] {item['name']} — שווי ₪{item['value']:,} "
            f"({sign}₪{abs(delta):,})")
    idx = choose("מה עכשיו?", ["חזרה", "לקנות נכס", "למכור נכס"])
    if idx == 1:
        rows = WL.available(game)
        labels = []
        for row in rows:
            mark = "🔒" if row["locked"] else ("💰" if row["affordable"] else "❌")
            labels.append(f"{mark} {row['name']} — ₪{row['price']:,} "
                          f"({row['yield'] * 100:.1f}% לשנה)")
        pick = choose("מה לקנות?", labels + ["ביטול"])
        if pick < len(rows):
            out("\n" + WL.buy(game, rows[pick]["key"]))
            ask("\n[Enter]")
    elif idx == 2 and info["items"]:
        labels = [f"{i['name']} — ₪{i['value']:,}" for i in info["items"]]
        pick = choose("מה למכור?", labels + ["ביטול"])
        if pick < len(info["items"]):
            out("\n" + WL.sell(game, pick))
            ask("\n[Enter]")


def show_mentor(game: GameState) -> None:
    """המנטור — מה הוא רואה, ומה כדאי לך לעבוד עליו."""
    info = MN.board(game)
    out(f"\n🧭 {info['name']} — {info['blurb']}")
    out(LINE)
    if not info["items"]:
        out("  אין לו מה להגיד לך עכשיו. זה סימן טוב.")
    for item in info["items"]:
        mark = "·" if item["said"] else "!"
        out(f"  {mark} {item['title']}")
        out(f"     {item['body']}")
        if item["action"] and item["action"] in D.DETAIL_NAMES_HE:
            out(f"     → מומלץ להתאמן על {D.DETAIL_NAMES_HE[item['action']]}")
        out("")
    out(LINE)
    out("  מה הכי שווה לך לעבוד עליו:")
    for need in info["needs"]:
        out(f"   #{need['rank']:<2} {D.DETAIL_NAMES_HE[need['attr']]:<16} "
            f"{need['level']:>2}/20  {need['verdict']}")
        if need["reasons"]:
            out(f"        {' · '.join(need['reasons'])}")
    idx = choose("לראות הסבר מלא על תכונה?",
                 [D.DETAIL_NAMES_HE[n["attr"]] for n in info["needs"]] + ["לא"],
                 default=len(info["needs"]))
    if idx < len(info["needs"]):
        show_attr(game, info["needs"][idx]["attr"])
        ask("\n[Enter]")


def show_attr(game: GameState, attr: str) -> None:
    """מה זו התכונה הזאת, ולמה שיהיה לי אכפת."""
    what, does, who = COACH.explain(attr)
    info = COACH.relevance_of(game, attr)
    plan = COACH.forecast(game, attr)
    out(f"\n— {D.DETAIL_NAMES_HE.get(attr, attr)} —  "
        f"{game.me.detail.get(attr, 10)}/20")
    out(f"  {what}")
    out(f"  במשחק:    {does}")
    out(f"  מי צריך:  {who}")
    out(LINE)
    out(f"  ואתה?     #{info['rank']} מתוך {info['of']} — {info['verdict']}")
    if info["reasons"]:
        out(f"            {' · '.join(info['reasons'])}")
    out(f"  אם תתאמן: {COACH.forecast_line(game, attr)}")
    out(f"            עלות {plan['fitness_cost']} רעננות לשבוע"
        + (f", סיכון פציעה {plan['injury_pct']}%" if plan["injury_pct"] else ""))


def show_growth(game: GameState) -> None:
    """איך התפתחתי, ובכמה."""
    out("\n📊 ההתפתחות שלך")
    out(LINE)
    for line in COACH.growth_lines(game):
        out("  " + line)
    info = COACH.growth_summary(game)
    if info["seasons"]:
        out(LINE)
        out("  עונה אחרי עונה:")
        for row in info["seasons"]:
            delta = f"{row['d_overall']:+d}" if row["d_overall"] else "  "
            out(f"   {row['year']}  גיל {row['age']:<3} {row['club'][:16]:<17} "
                f"כללי {row['overall']:>2} {delta:<4} "
                f"{row['apps']:>2} משחקים  ציון {row['rating'] or 0:.1f}")
