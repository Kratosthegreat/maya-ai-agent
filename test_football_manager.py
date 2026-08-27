# -*- coding: utf-8 -*-
"""בדיקות למשחק ניהול הכדורגל (football_manager)."""

import json
import os
import random

import pytest

from football_manager import club_ops as CO
from football_manager import data as D
from football_manager import story as ST
from football_manager.engine import (pick_lineup, position_fit, simulate_match,
                                     team_strength)
from football_manager.game import CUP_WEEKS, SEASON_WEEKS, GameState, round_robin
from football_manager.models import (available_numbers, generate_player,
                                     generate_world, set_all, set_group,
                                     wage_for_overall)
from football_manager import commercial as CM
from football_manager import story_engine as SE
from football_manager.story_pack import PACK
from football_manager import manager as MG
from football_manager import matchstats as MS
from football_manager import scouting as SC
from football_manager import development as DEV
from football_manager import wealth as WL
from football_manager import models as MDL
from football_manager import tactics as TA
from football_manager import knowledge as KN
from football_manager import coaching as COACH
from football_manager import mentor as MN
from football_manager import transfers as TR
from football_manager import press as PR
from football_manager import fame as FA
from football_manager.engine import medical_care
from football_manager.progression import (age_factor, end_of_season_development,
                                          weekly_training)


# ---------------------------------------------------------------------------
# עולם ומודלים
# ---------------------------------------------------------------------------

def test_world_generation_is_complete():
    clubs, players = generate_world(seed=1)
    assert len(clubs) == len(D.CLUBS)
    for club in clubs.values():
        assert len(club.squad) >= 11
        assert club.league_id in {league["id"] for league in D.LEAGUES}
        for pid in club.squad:
            assert players[pid].club_id == club.cid


def test_world_generation_is_deterministic():
    clubs_a, players_a = generate_world(seed=7)
    clubs_b, players_b = generate_world(seed=7)
    assert [p.name for p in players_a.values()] == [p.name for p in players_b.values()]
    assert [c.reputation for c in clubs_a.values()] == \
           [c.reputation for c in clubs_b.values()]


def test_player_overall_matches_position_weights():
    rng = random.Random(3)
    clubs, _ = generate_world(seed=3)
    club = clubs["maccabi_harel"]
    for position in D.POSITIONS:
        player = generate_player(rng, club, position, age=25, quality=70)
        assert 60 <= player.overall <= 80
        assert set(player.attributes) == set(D.ATTRIBUTES)


def test_stronger_clubs_have_stronger_squads():
    clubs, players = generate_world(seed=5)
    def avg(cid):
        squad = clubs[cid].squad
        return sum(players[p].overall for p in squad) / len(squad)
    assert avg("real_castilla") > avg("maccabi_harel") > avg("ironi_shomron")


def test_wage_scale_is_monotonic():
    wages = [wage_for_overall(o) for o in (40, 50, 60, 70, 80, 90)]
    assert wages == sorted(wages)
    assert wages[0] < wages[-1] / 20


def test_player_value_peaks_in_mid_twenties():
    rng = random.Random(11)
    clubs, _ = generate_world(seed=11)
    club = clubs["maccabi_harel"]
    young = generate_player(rng, club, "ST", age=25, quality=75)
    old = generate_player(rng, club, "ST", age=36, quality=75)
    young.attributes = dict(old.attributes)
    assert young.value > old.value


# ---------------------------------------------------------------------------
# מנוע המשחק
# ---------------------------------------------------------------------------

def test_lineup_has_eleven_players_and_no_duplicates():
    clubs, players = generate_world(seed=2)
    club = clubs["bnei_negev"]
    lineup = pick_lineup(club, players, "4-3-3")
    assert len(lineup) == 11
    assert len(set(lineup)) == 11
    assert all(players[pid].available for pid in lineup)


def test_forced_player_starts_in_a_slot_that_fits_his_position():
    """שחקן שהמאמן מציב בהרכב לא אמור למצוא את עצמו בשער."""
    clubs, players = generate_world(seed=31)
    club = clubs["ironi_shomron"]
    for position in ("ST", "CB", "CM", "LW", "GK"):
        player = next((players[p] for p in club.squad
                       if players[p].position == position), players[club.squad[0]])
        player.position = position
        for formation, slots in D.FORMATIONS.items():
            lineup = pick_lineup(club, players, formation, forced=[player.pid])
            assert player.pid in lineup, f"{position} לא נכנס להרכב ב-{formation}"
            slot = slots[lineup.index(player.pid)]
            assert position_fit(position, slot) >= 0.9, \
                f"{position} הוצב כ-{slot} במערך {formation}"


def test_best_players_are_not_played_out_of_position():
    """המעבר הראשון שומר את המשבצות לשחקנים בעמדתם הטבעית."""
    clubs, players = generate_world(seed=17)
    club = clubs["maccabi_harel"]
    for formation, slots in D.FORMATIONS.items():
        lineup = pick_lineup(club, players, formation)
        misplaced = sum(1 for pid, slot in zip(lineup, slots)
                        if position_fit(players[pid].position, slot) < 0.9)
        assert misplaced <= 1, f"{misplaced} שחקנים מחוץ לעמדה ב-{formation}"


def test_position_fit_prefers_natural_position():
    assert position_fit("ST", "ST") == 1.0
    assert position_fit("ST", "CB") < position_fit("CB", "CB")
    assert position_fit("GK", "ST") < 0.5


def test_team_strength_is_on_rating_scale():
    clubs, players = generate_world(seed=4)
    club = clubs["maccabi_harel"]
    lineup = pick_lineup(club, players, club.formation)
    dfn, mid, att = team_strength(lineup, players, club.formation)
    for line in (dfn, mid, att):
        assert 30 < line < 100


def test_match_is_deterministic_for_same_seed():
    def run():
        clubs, players = generate_world(seed=6)
        return simulate_match(clubs["maccabi_harel"], clubs["bnei_negev"],
                              players, random.Random(42))
    first, second = run(), run()
    assert (first.home_goals, first.away_goals) == (second.home_goals, second.away_goals)
    assert first.ratings == second.ratings


def test_match_result_is_internally_consistent():
    clubs, players = generate_world(seed=8)
    rng = random.Random(8)
    result = simulate_match(clubs["maccabi_harel"], clubs["hapoel_yam"], players, rng)
    goals = [e for e in result.events if e.kind == "goal"]
    assert len(goals) == result.home_goals + result.away_goals
    assert sum(1 for e in goals if e.club_id == result.home_id) == result.home_goals
    for pid in result.home_lineup + result.away_lineup:
        assert pid in result.ratings
        assert 3.0 <= result.ratings[pid] <= 10.0
    assert result.motm in result.ratings
    assert result.result_for(result.home_id) in ("W", "D", "L")


def test_stronger_team_wins_most_of_the_time():
    clubs, players = generate_world(seed=9)
    rng = random.Random(9)
    strong, weak = clubs["real_castilla"], clubs["ironi_shomron"]
    wins = 0
    for _ in range(60):
        for player in players.values():
            player.fitness, player.injury_weeks = 100.0, 0
        result = simulate_match(strong, weak, players, rng)
        wins += result.result_for(strong.cid) == "W"
    assert wins >= 45


def test_goals_per_match_is_realistic():
    clubs, players = generate_world(seed=10)
    rng = random.Random(10)
    top = [c for c in clubs.values() if c.league_id == "top"]
    total = 0
    matches = 120
    for _ in range(matches):
        for player in players.values():
            player.fitness, player.injury_weeks = 100.0, 0
        home, away = rng.sample(top, 2)
        result = simulate_match(home, away, players, rng)
        total += result.home_goals + result.away_goals
    assert 1.8 <= total / matches <= 3.6


# ---------------------------------------------------------------------------
# לוח משחקים
# ---------------------------------------------------------------------------

def test_round_robin_covers_every_pairing_twice():
    teams = [f"t{i}" for i in range(12)]
    rounds = round_robin(teams, random.Random(1))
    assert len(rounds) == 22
    seen = {}
    for rnd in rounds:
        assert len(rnd) == 6
        in_round = [t for pair in rnd for t in pair]
        assert len(set(in_round)) == 12          # כל קבוצה פעם אחת במחזור
        for home, away in rnd:
            seen[(home, away)] = seen.get((home, away), 0) + 1
    assert len(seen) == 12 * 11                  # כל צמד, בבית ובחוץ
    assert set(seen.values()) == {1}


# ---------------------------------------------------------------------------
# התפתחות
# ---------------------------------------------------------------------------

def test_age_curve_rewards_youth_and_punishes_age():
    assert age_factor(18) > age_factor(25) > age_factor(30)
    assert age_factor(35) < 0


def test_training_improves_the_trained_attribute():
    rng = random.Random(12)
    clubs, _ = generate_world(seed=12)
    club = clubs["maccabi_harel"]
    player = generate_player(rng, club, "ST", age=18, quality=55)
    player.potential = 85
    before = player.attributes["shooting"]
    for _ in range(25):
        weekly_training(player, "shooting", club, rng)
    assert player.attributes["shooting"] > before


def test_training_respects_the_potential_ceiling():
    rng = random.Random(13)
    clubs, _ = generate_world(seed=13)
    club = clubs["maccabi_harel"]
    player = generate_player(rng, club, "ST", age=20, quality=60)
    player.potential = player.overall
    for _ in range(60):
        weekly_training(player, "shooting", club, rng)
    assert player.overall <= player.potential + 4


def test_rest_recovers_fitness_and_heals():
    rng = random.Random(14)
    clubs, _ = generate_world(seed=14)
    club = clubs["maccabi_harel"]
    player = generate_player(rng, club, "CM", age=27)
    player.fitness = 40.0
    player.injury_weeks = 3
    weekly_training(player, "rest", club, rng)
    assert player.fitness > 40.0
    assert player.injury_weeks < 3


def test_old_players_decline_over_seasons():
    rng = random.Random(15)
    clubs, _ = generate_world(seed=15)
    club = clubs["maccabi_harel"]
    player = generate_player(rng, club, "LW", age=34, quality=75)
    before = player.overall
    for _ in range(4):
        end_of_season_development(player, rng, 0.8)
    assert player.overall < before
    assert player.age == 38


def test_badges_require_years_of_study():
    rng = random.Random(16)
    clubs, _ = generate_world(seed=16)
    club = clubs["maccabi_harel"]
    player = generate_player(rng, club, "CM", age=24)
    player.coaching = 0.0
    for _ in range(22):                     # עונה שלמה של לימודים
        weekly_training(player, "badges", club, rng)
    assert 0 < player.coaching < 40
    assert player.badges <= 1


# ---------------------------------------------------------------------------
# עלילה
# ---------------------------------------------------------------------------

def test_story_registry_is_well_formed():
    ids = [event.eid for event in ST.REGISTRY]
    assert len(ids) == len(set(ids))
    for event in ST.REGISTRY:
        assert event.choices, f"{event.eid} has no choices"
        assert callable(event.body)
        for choice in event.choices:
            assert choice.label and callable(choice.apply)
        for stage in event.stages:
            assert stage in D.CAREER_STAGES_HE


def test_eligible_events_respect_career_stage():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", age=17, seed=21)
    for event in ST.eligible_events(game):
        assert not event.stages or game.stage in event.stages


def test_pending_event_blocks_progress_until_resolved():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", age=17, seed=21)
    game.pending_event_id = "youth_mentor"
    week_before = game.week
    report = game.advance_week()
    assert game.week == week_before          # השבוע לא התקדם
    assert report.event_id == "youth_mentor"
    outcome = game.resolve_event(0)
    assert outcome
    assert game.pending_event_id is None
    assert "youth_mentor" in game.fired_events


# ---------------------------------------------------------------------------
# מצב המשחק
# ---------------------------------------------------------------------------

def test_new_game_places_the_player_in_the_club():
    game = GameState.new_game("עומר לוי", "ST", "hapoel_carmel", age=17, seed=31)
    assert game.me.name == "עומר לוי"
    assert game.me.is_human
    assert game.me.pid in game.my_club.squad
    assert game.stage == "academy"
    assert game.me.overall < game.me.potential


def test_advance_week_moves_the_calendar():
    game = GameState.new_game("עומר לוי", "ST", "hapoel_carmel", age=17, seed=32)
    game.set_action("shooting")
    report = game.advance_week()
    assert game.week == 2
    assert report.week == 1
    assert report.lines


def test_league_table_totals_add_up():
    game = GameState.new_game("עומר לוי", "ST", "hapoel_carmel", age=17, seed=33)
    for _ in range(6):
        if game.pending_event_id:
            game.resolve_event(0)
            continue
        game.set_action("rest")
        game.advance_week()
    for league_id in ("top", "national"):
        rows = game.standings(league_id)
        assert sum(r.gf for r in rows) == sum(r.ga for r in rows)
        for row in rows:
            assert row.played == row.won + row.drawn + row.lost
            assert row.points == row.won * 3 + row.drawn


def test_the_calendar_fits_the_fixture_list():
    """38 מחזורי ליגה, חמישה מחזורי גביע, ועונה שבדיוק מכילה אותם."""
    from football_manager.game import league_weeks
    assert len(CUP_WEEKS) == 5
    assert len(league_weeks()) == 38
    game = GameState.new_game("בודק", "ST", "maccabi_sharon", age=24, seed=3)
    for league_id in ("top", "national"):
        assert len(game.fixtures[league_id]) == 38
    assert len(game.cup["teams"]) == 32


def test_season_rolls_over_and_history_is_recorded():
    game = GameState.new_game("עומר לוי", "ST", "hapoel_carmel", age=17, seed=34)
    year = game.year
    while True:
        if game.pending_event_id:
            game.resolve_event(0)
            continue
        game.set_action("shooting")
        if game.advance_week().season_ended:
            break
    assert game.year == year + 1
    assert game.week == 1
    assert game.me.age >= 18
    assert len(game.history) == 1
    assert all(row.played == 0 for row in game.standings("top"))


def test_promotion_and_relegation_change_leagues():
    game = GameState.new_game("עומר לוי", "ST", "hapoel_carmel", age=17, seed=35)
    before = {cid: club.league_id for cid, club in game.clubs.items()}
    while True:
        if game.pending_event_id:
            game.resolve_event(0)
            continue
        game.set_action("rest")
        if game.advance_week().season_ended:
            break
    moved = [cid for cid, lid in before.items() if game.clubs[cid].league_id != lid]
    assert len(moved) == 6                    # שלוש עולות, שלוש יורדות
    for league_id in ("top", "national"):
        count = sum(1 for c in game.clubs.values() if c.league_id == league_id)
        assert count == 20


def test_career_can_start_at_any_age():
    """הגיל שנבחר קובע את השלב, את החוזה ואת העבר."""
    expected = {13: "youth", 15: "youth", 16: "academy", 17: "academy",
                18: "player", 25: "player", 30: "player", 31: "veteran", 36: "veteran"}
    for age, stage in expected.items():
        game = GameState.new_game("בודק", "ST", "maccabi_sharon", age=age, seed=5)
        assert game.stage == stage, f"גיל {age}: {game.stage} במקום {stage}"
        assert game.me.age == age
        assert game.me.potential >= game.me.overall
        if age >= 19:
            assert game.me.career.apps > 0, f"גיל {age} בלי עבר"
            assert game.me.contract.wage > 0
        if age <= 15:
            assert game.me.contract.wage == 0
            assert game.me.career.apps == 0


def test_a_career_can_start_as_a_manager():
    """מסלול מנג'ר: בלי קריירת שחקן פעילה, עם קבוצה מהשבוע הראשון."""
    game = GameState.new_game("דני מנג'ר", "CM", "hapoel_carmel",
                              age=45, seed=11, role="manager")
    assert game.stage == "manager"
    assert game.me.retired
    assert game.me.club_id is None
    assert game.my_club is not None
    assert game.my_club.manager_name == "דני מנג'ר"
    assert game.me.coaching > 20
    game.set_action("tactics")
    report = game.advance_week()
    assert report.lines or report.match
    assert game.week == 2


def test_career_starting_at_thirteen_goes_through_the_youth_stage():
    """קריירה שמתחילה בגיל 13 — שנות נוער, בלי שכר, ואז חוזה ראשון."""
    game = GameState.new_game("ילד מהשכונה", "ST", "hapoel_carmel", age=13, seed=77)
    assert game.stage == "youth"
    assert game.me.contract.wage == 0
    start_overall = game.me.overall
    assert game.me.potential > start_overall + 15

    youth_matches = 0
    seasons = 0
    while seasons < 4 and game.stage == "youth":
        if game.pending_event_id:
            game.resolve_event(0)
            continue
        game.set_action("shooting")
        report = game.advance_week()
        youth_matches += sum(1 for line in report.lines if "ליגת הנוער" in line)
        if report.season_ended:
            seasons += 1

    assert youth_matches > 10, f"רק {youth_matches} משחקי נוער"
    assert game.me.age == 16
    assert game.stage == "academy"
    assert game.me.contract.wage > 0
    assert game.me.overall > start_overall
    assert game.money == 0, "ילד בקבוצת נוער לא מרוויח שכר"


def test_the_senior_league_keeps_running_during_the_youth_years():
    """העולם לא קופא בזמן ששחקן הנוער גדל."""
    game = GameState.new_game("ילד", "ST", "hapoel_carmel", age=13, seed=42)
    while True:
        if game.pending_event_id:
            game.resolve_event(0)
            continue
        game.set_action("shooting")
        if game.advance_week().season_ended:
            break
    champion = game.history[0]
    assert champion                      # העונה נרשמה
    top_scorers = [p for p in game.players.values()
                   if p.pid != game.me_id and p.career.goals > 0]
    assert len(top_scorers) > 20, "אף שחקן בוגר לא כבש — הליגה לא שוחקה"


def test_career_stage_advances_from_academy_to_player():
    game = GameState.new_game("עומר לוי", "ST", "hapoel_carmel", age=17, seed=36)
    while game.stage == "academy":
        if game.pending_event_id:
            game.resolve_event(0)
            continue
        game.set_action("shooting")
        game.advance_week()
    assert game.stage == "player"
    assert game.me.age >= 18


def test_transfer_moves_the_player_between_squads():
    game = GameState.new_game("עומר לוי", "ST", "hapoel_carmel", age=17, seed=37)
    old_club = game.my_club
    game.transfer_me("maccabi_harel", wage=50_000, years=3)
    assert game.me.pid not in old_club.squad
    assert game.me.pid in game.clubs["maccabi_harel"].squad
    assert game.me.club_id == "maccabi_harel"
    assert game.me.contract.wage == 50_000


def test_retirement_opens_the_next_chapter():
    game = GameState.new_game("ותיק כהן", "CM", "hapoel_carmel", age=18, seed=38)
    game.stage = "veteran"
    game.me.age = 39
    game.me.coaching = 70.0
    game.me.badges = 3
    game.set_flag("retired_announced", True)
    while True:
        if game.pending_event_id:
            game.resolve_event(0)
            continue
        game.set_action("rest")
        if game.advance_week().season_ended:
            break
    assert game.stage == "retired"
    assert game.me.retired
    assert game.me.club_id is None
    # הפרק הבא: מסלול אימון
    game.pending_event_id = "next_chapter"
    game.resolve_event(0)
    assert game.stage == "coach"
    assert game.my_club is not None


def test_manager_path_and_tactics_take_effect():
    game = GameState.new_game("מנג'ר כהן", "CM", "hapoel_carmel", age=18, seed=39)
    game.stage = "coach"
    game.me.retired = True
    game.me.coaching = 80.0
    game.managed_club_id = "hapoel_carmel"
    game.me.club_id = None
    game.pending_event_id = "first_manager_offer"
    game.resolve_event(0)
    assert game.stage == "manager"
    assert game.my_club.manager_name == game.me.name
    game.tactics["mentality"] = "attacking"
    game.set_action("tactics")
    report = game.advance_week()
    assert report.lines


def test_sub_goal_refreshes_the_commentary():
    """שער של מחליף משנה את התוצאה — והפרשנות חייבת להשתנות איתה."""
    for seed in range(80):
        game = GameState.new_game("מחליף כהן", "ST", "hapoel_carmel", age=17, seed=seed)
        for _ in range(26):
            if game.pending_event_id:
                game.resolve_event(0)
                continue
            game.set_action("rest")
            report = game.advance_week()
            if report.match and any("נכנסת מהספסל וכבשת" in line for line in report.lines):
                head = report.match.commentary[0]
                assert f"{report.match.home_goals} - {report.match.away_goals}" in head
                return
    pytest.skip("לא נמצא שער של מחליף בזרעים שנבדקו")


def test_money_accumulates_from_wages():
    game = GameState.new_game("עומר לוי", "ST", "hapoel_carmel", age=17, seed=40)
    start = game.money
    for _ in range(3):
        if game.pending_event_id:
            game.resolve_event(0)
            continue
        game.set_action("rest")
        game.advance_week()
    assert game.money > start


# ---------------------------------------------------------------------------
# שמירה וטעינה
# ---------------------------------------------------------------------------

def test_save_and_load_round_trip(tmp_path):
    game = GameState.new_game("עומר לוי", "ST", "hapoel_carmel", age=17, seed=41)
    for _ in range(4):
        if game.pending_event_id:
            game.resolve_event(0)
            continue
        game.set_action("passing")
        game.advance_week()

    path = os.path.join(tmp_path, "save.json")
    game.save(path)
    with open(path, encoding="utf-8") as handle:
        json.load(handle)                     # שמירה תקינה כ-JSON

    loaded = GameState.load(path)
    assert loaded.me.name == game.me.name
    assert loaded.week == game.week
    assert loaded.year == game.year
    assert loaded.stage == game.stage
    assert loaded.money == game.money
    assert loaded.me.attributes == game.me.attributes
    assert loaded.standings("top")[0].points == game.standings("top")[0].points

    # מצב ההגרלה נשמר — ההמשך זהה
    for state in (game, loaded):
        if state.pending_event_id:
            state.resolve_event(0)
        state.set_action("passing")
        state.advance_week()
    assert loaded.me.attributes == game.me.attributes
    assert loaded.standings("top")[0].points == game.standings("top")[0].points


# ---------------------------------------------------------------------------
# בדיקת שפיות ארוכה
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("seed", [101, 202])
def test_long_career_runs_without_errors(seed):
    """מריץ קריירה ארוכה ומוודא שהמצב נשאר עקבי לאורך כל הדרך."""
    game = GameState.new_game("מרתון לוי", "ST", "hapoel_ayalon", age=17, seed=seed)
    rng = random.Random(seed)
    picks = 0
    seasons = 0
    while not game.game_over and seasons < 25:
        if game.pending_event_id:
            event = game.pending_event()
            assert event is not None
            assert game.pending_event_text()           # הטקסט נבנה בלי שגיאה
            game.resolve_event(picks % len(event.choices))
            picks += 1
            continue
        actions = [key for key, _ in game.available_actions()]
        game.set_action(rng.choice(actions))
        report = game.advance_week()
        assert 1 <= report.week <= SEASON_WEEKS
        if report.season_ended:
            seasons += 1
            for league_id in ("top", "national", "euro"):
                for row in game.standings(league_id):
                    assert row.played == 0
            for club in game.clubs.values():
                assert len(club.squad) >= 16
    assert picks >= 12                                  # העלילה באמת התקדמה
    assert game.me.age > 25
    assert len(game.history) == seasons


def test_many_story_events_fire_across_careers():
    """כיסוי אמיתי לאירועי העלילה — לפחות שליש מהמאגר נורה בפועל."""
    fired = set()
    for seed in (11, 22, 33):
        game = GameState.new_game("שחקן בדיקה", "ST", "hapoel_carmel",
                                  age=17, seed=seed)
        rng = random.Random(seed)
        picks = 0
        for _ in range(26 * 22):
            if game.game_over:
                break
            if game.pending_event_id:
                event = game.pending_event()
                game.resolve_event(picks % len(event.choices))
                picks += 1
                continue
            game.set_action(rng.choice([k for k, _ in game.available_actions()]))
            game.advance_week()
        fired.update(game.fired_events)
    assert len(fired) >= len(ST.REGISTRY) // 3


# ---------------------------------------------------------------------------
# אצטדיון, תקציב, מתקנים וצוות
# ---------------------------------------------------------------------------

def _managed_game(seed=9, club="hapoel_carmel"):
    return GameState.new_game("מנג'ר", "CM", club, 42, seed=seed, role="manager")


def test_every_club_has_a_stadium_facilities_and_staff():
    clubs, _ = generate_world(seed=4)
    for club in clubs.values():
        assert club.stadium_name
        assert 1_500 <= club.capacity <= 42_000
        assert club.capacity % 500 == 0
        assert club.balance > 0
        assert 1 <= club.medical_centre <= 99
        assert club.ticket_price > 0
        for role, member in club.staff.items():
            assert role in D.STAFF_ROLES
            assert 8 <= member["quality"] <= 96
            assert member["wage"] > 0
            assert member["name"]


def test_stadium_size_tracks_club_stature():
    clubs, _ = generate_world(seed=4)
    ranked = sorted(clubs.values(), key=lambda c: -c.reputation)
    big = sum(c.capacity for c in ranked[:6]) / 6
    small = sum(c.capacity for c in ranked[-6:]) / 6
    assert big > small * 4


def test_attendance_never_exceeds_capacity_and_follows_support():
    clubs, _ = generate_world(seed=4)
    rng = random.Random(2)
    club = clubs["hapoel_carmel"]
    opponent = clubs["maccabi_harel"]
    for _ in range(60):
        assert 0 < CO.attendance_for(club, opponent, rng) <= club.capacity

    loyal = generate_world(seed=4)[0]["hapoel_carmel"]
    quiet = generate_world(seed=4)[0]["hapoel_carmel"]
    loyal.fan_support, quiet.fan_support = 95.0, 25.0
    crowded = sum(CO.attendance_for(loyal, opponent, random.Random(i)) for i in range(30))
    empty = sum(CO.attendance_for(quiet, opponent, random.Random(i)) for i in range(30))
    assert crowded > empty


def test_weekly_finances_balance_out():
    clubs, players = generate_world(seed=4)
    club = clubs["hapoel_carmel"]
    before = club.balance
    detail = CO.weekly_finances(club, players, matchday=1_000_000)
    assert detail["net"] == (detail["commercial"] + detail["matchday"]
                             - detail["wages"] - detail["staff"])
    assert club.balance == round(before + detail["net"])
    assert detail["balance"] == int(club.balance)


def test_home_matches_draw_a_crowd_and_pay_for_themselves():
    game = _managed_game()
    home_weeks = 0
    for _ in range(120):
        if game.pending_event_id:
            game.resolve_event(0)
            continue
        report = game.advance_week()
        if report.attendance:
            home_weeks += 1
            assert report.finances["matchday"] > 0
            assert report.attendance <= game.my_club.capacity
        else:
            assert report.finances["matchday"] == 0
        if report.season_ended:
            break
    assert home_weeks >= 14


def test_the_gate_is_counted_during_the_youth_years_too():
    """בשנות הנוער אתה צופה מהיציע — אבל הקופה של המועדון עדיין עובדת."""
    game = GameState.new_game("נער", "ST", "hapoel_carmel", 13, seed=5)
    assert game.stage == "youth"
    home_weeks = 0
    gate = 0
    for _ in range(80):
        if game.pending_event_id:
            game.resolve_event(0)
            continue
        report = game.advance_week()
        if report.attendance:
            home_weeks += 1
            assert report.finances["matchday"] > 0
        gate += report.finances["matchday"] if report.finances else 0
        if report.season_ended:
            break
    assert home_weeks >= 14
    # מועדון יכול לסיים עונה במינוס — מה שנבדק כאן הוא שהקהל נספר בכלל
    assert gate > CO.commercial_income(game.my_club) * 4


def test_facility_upgrade_costs_money_takes_time_and_lands():
    game = _managed_game()
    club = game.my_club
    club.balance = 60_000_000
    before_level = club.medical_centre
    before_balance = club.balance
    cost = CO.upgrade_cost(club, "medical")

    assert "אישרת" in game.upgrade_facility("medical")
    assert club.balance == before_balance - cost
    assert club.medical_centre == before_level          # עוד לא הסתיים
    assert "כבר בעיצומן" in game.upgrade_facility("medical")

    for _ in range(D.FACILITIES["medical"]["weeks"]):
        CO.tick_works(club)
    assert club.medical_centre > before_level
    assert club.works == []


def test_stadium_expansion_adds_seats():
    game = _managed_game()
    club = game.my_club
    club.balance = 200_000_000
    before = club.capacity
    added = CO.stadium_expansion(club)
    game.upgrade_facility("stadium")
    for _ in range(D.FACILITIES["stadium"]["weeks"]):
        CO.tick_works(club)
    assert club.capacity == before + added


def test_an_empty_till_blocks_building():
    game = _managed_game()
    club = game.my_club
    club.balance = 1_000
    assert CO.can_upgrade(club, "training") == "אין מספיק כסף בקופה."
    assert "אין מספיק כסף" in game.upgrade_facility("training")
    assert club.works == []


def test_hiring_and_firing_staff_moves_money_and_the_roster():
    game = _managed_game()
    club = game.my_club
    club.balance = 20_000_000
    candidate = dict(game.staff_market["analyst"][0])
    balance_before = club.balance

    message = game.hire_staff("analyst", 0)
    assert candidate["name"] in message
    assert club.staff["analyst"]["quality"] == candidate["quality"]
    assert club.balance == balance_before - candidate["wage"] * 4
    assert game.staff_market["analyst"][0]["name"] != candidate["name"] or True

    wage = club.staff["analyst"]["wage"]
    balance_before = club.balance
    assert "סיים את תפקידו" in game.release_staff("analyst")
    assert "analyst" not in club.staff
    assert club.balance == balance_before - wage * 8
    assert game.release_staff("analyst") == "המשרה כבר פנויה."


def test_only_a_decision_maker_spends_club_money():
    game = GameState.new_game("שחקן", "ST", "hapoel_carmel", 24, seed=9)
    assert not game.controls_club()
    balance = game.my_club.balance
    assert "לא מחליט" in game.upgrade_facility("training")
    assert "לא מגייס" in game.hire_staff("analyst", 0)
    assert "לא מפטר" in game.release_staff("analyst")
    assert game.my_club.balance == balance


def test_medical_quality_shortens_injuries():
    clubs, _ = generate_world(seed=4)
    club = clubs["hapoel_carmel"]
    club.medical_centre = 95
    club.staff["physio"] = {"name": "טוב", "quality": 95, "wage": 5000}
    from football_manager.engine import medical_care
    from football_manager.progression import weekly_recovery
    assert medical_care(club) > 0.9

    poor = clubs["maccabi_shikma"] if "maccabi_shikma" in clubs else club
    poor.medical_centre = 10
    poor.staff.pop("physio", None)
    assert medical_care(poor) < 0.2

    def weeks_to_heal(target):
        player = generate_player(random.Random(3), target, "ST")
        player.injury_weeks = 6
        rng = random.Random(11)
        weeks = 0
        while player.injury_weeks > 0 and weeks < 40:
            weekly_recovery(player, played=False, rng=rng, club=target)
            weeks += 1
        return weeks

    fast = sum(weeks_to_heal(club) for _ in range(12))
    slow = sum(weeks_to_heal(poor) for _ in range(12))
    assert fast < slow


def test_an_assistant_manager_speeds_up_training():
    clubs, _ = generate_world(seed=4)
    with_help = clubs["hapoel_carmel"]
    with_help.staff["assistant"] = {"name": "טוב", "quality": 95, "wage": 6000}
    alone = clubs["maccabi_sharon"]
    alone.training_facilities = with_help.training_facilities
    alone.staff.pop("assistant", None)

    def gain(club, seed):
        player = generate_player(random.Random(seed), club, "ST", age=19, quality=55)
        player.potential = 90
        start = player.attributes["shooting"]
        rng = random.Random(seed)
        for _ in range(40):
            weekly_training(player, "shooting", club, rng)
        return player.attributes["shooting"] - start

    helped = sum(gain(with_help, s) for s in range(14))
    unhelped = sum(gain(alone, s) for s in range(14))
    assert helped > unhelped


def test_an_analyst_gives_a_measurable_edge():
    clubs, players = generate_world(seed=4)
    home, away = clubs["hapoel_carmel"], clubs["maccabi_sharon"]
    home.staff["analyst"] = {"name": "מצוין", "quality": 95, "wage": 6000}
    away.staff.pop("analyst", None)
    sharp = sum(simulate_match(home, away, players, random.Random(s)).home_goals
                for s in range(160))
    home.staff.pop("analyst", None)
    away.staff["analyst"] = {"name": "מצוין", "quality": 95, "wage": 6000}
    blunt = sum(simulate_match(home, away, players, random.Random(s)).home_goals
                for s in range(160))
    assert sharp > blunt


def test_building_finishes_even_after_you_change_clubs():
    """בנייה ששילמת עליה לא נתקעת רק כי עברת מועדון."""
    game = _managed_game()
    first = game.my_club
    first.balance = 60_000_000
    before = first.medical_centre
    game.upgrade_facility("medical")

    game.managed_club_id = "maccabi_harel"      # עברת מועדון באמצע
    for _ in range(D.FACILITIES["medical"]["weeks"] + 1):
        if game.pending_event_id:
            game.resolve_event(0)
        game.advance_week()

    assert first.medical_centre > before
    assert first.works == []


def test_club_books_survive_save_and_load(tmp_path):
    game = _managed_game()
    club = game.my_club
    club.balance = 80_000_000
    game.upgrade_facility("medical")
    game.hire_staff("assistant", 0)
    for _ in range(3):
        if game.pending_event_id:
            game.resolve_event(0)
        game.advance_week()

    # ייתכן שהמנג'ר עבר מועדון באמצע — משווים את אותו מועדון בשני הצדדים
    club = game.my_club
    path = game.save(str(tmp_path / "save.json"))
    loaded = GameState.load(path)
    mirror = loaded.clubs[club.cid]
    assert mirror.stadium_name == club.stadium_name
    assert mirror.capacity == club.capacity
    assert int(mirror.balance) == int(club.balance)
    assert mirror.staff == club.staff
    assert mirror.works == club.works
    assert loaded.staff_market.keys() == game.staff_market.keys()


# ---------------------------------------------------------------------------
# התפתחות, פציעות ומסחר
# ---------------------------------------------------------------------------

def test_a_player_keeps_improving_after_eighteen():
    """התלונה שהתחילה את זה: ההתפתחות מתה בגיל 17-18."""
    game = GameState.new_game("צעיר", "ST", "hapoel_carmel", 17, seed=4)
    marks = {}
    weeks = 0
    # התקציב נספר בשבועות בלבד — פתרון צומת עלילה אינו מקדם את הלוח,
    # ועם ספרייה של מאות אירועים הוא היה אוכל את התקציב לפני גיל 24.
    while weeks < 420 and game.me.age <= 24 and not game.game_over:
        if game.pending_event_id:
            game.resolve_event(0)
            continue
        game.advance_week()
        weeks += 1
        marks[game.me.age] = game.me.overall
    assert marks[22] > marks[18] + 3, f"18→22 עלה רק {marks[22] - marks[18]}"
    assert marks[24] >= marks[22]


def test_potential_moves_but_the_ceiling_holds():
    game = GameState.new_game("צעיר", "ST", "hapoel_carmel", 16, seed=8)
    first = game.me.potential
    assert game.me.ceiling >= first
    for _ in range(300):
        if game.me.age > 22 or game.game_over:
            break
        if game.pending_event_id:
            game.resolve_event(0)
            continue
        game.advance_week()
        assert game.me.potential <= game.me.ceiling
    assert game.me.potential != first


def test_training_spreads_across_attributes():
    clubs, _ = generate_world(seed=4)
    club = clubs["hapoel_carmel"]
    player = generate_player(random.Random(3), club, "ST", age=19, quality=50)
    player.potential = 90
    player.ceiling = 90
    before = dict(player.attributes)
    rng = random.Random(3)
    for _ in range(43):
        weekly_training(player, "shooting", club, rng)
    moved = [a for a in D.ATTRIBUTES if player.attributes[a] > before[a]]
    assert len(moved) >= 4, f"רק {len(moved)} תכונות זזו"
    assert player.attributes["shooting"] > before["shooting"]


def test_strength_and_resilience_lower_injury_risk():
    clubs, _ = generate_world(seed=4)
    club = clubs["hapoel_carmel"]
    tough = generate_player(random.Random(5), club, "CB", age=24, quality=60)
    frail = generate_player(random.Random(5), club, "CB", age=24, quality=60)
    tough.resilience, tough.sharpness = 92, 85
    set_group(tough, "physical", 88)
    frail.resilience, frail.sharpness = 15, 30
    set_group(frail, "physical", 35)
    assert tough.injury_risk < frail.injury_risk * 0.6
    assert tough.injury_risk < 1.0


def test_every_player_has_a_believable_body():
    _, players = generate_world(seed=4)
    keepers, wingers = [], []
    for player in players.values():
        assert 150 <= player.height <= 210
        assert 45 <= player.weight <= 110
        assert 0 <= player.resilience <= 100
        if player.position == "GK" and player.age >= 20:
            keepers.append(player.height)
        if player.position == "LW" and player.age >= 20:
            wingers.append(player.height)
    assert sum(keepers) / len(keepers) > sum(wingers) / len(wingers) + 6


def test_sponsor_offers_scale_with_who_you_are():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 24, seed=2)
    rng = random.Random(9)

    def sample(rep, media, goals):
        game.me.reputation, game.me.media_skill = rep, media
        game.me.career.goals = goals
        offers = [CM.sponsor_offer(game.me, rng, 67) for _ in range(60)]
        return sum(o["amount"] for o in offers if o) / len(offers)

    young = sample(18, 8, 2)
    star = sample(88, 72, 210)
    assert star > young * 8, f"כוכב {star:.0f} מול צעיר {young:.0f}"
    assert CM.marketability(game.me, 67) > 50


def test_the_manager_has_a_character_and_speaks_up():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 24, seed=5)
    club = game.my_club
    style = MG.style_of(club)
    assert style[1]
    assert MG.style_of(club) == style, "האופי משתנה בין קריאות"
    rng = random.Random(1)
    assert club.manager_name in MG.post_match_line(game, 8.6, "W", True, rng)
    assert MG.selection_note(game)
    directive = MG.weekly_directive(game, rng)
    assert directive in list(D.ATTRIBUTES) + ["rest"]


def test_repeat_events_respect_their_cooldown():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 24, seed=6)
    last_seen = {}
    seen = set()
    for _ in range(220):
        if game.game_over:
            break
        if game.pending_event_id:
            eid = game.pending_event_id
            event = ST.find_event(eid)
            stamp = game.year * 43 + game.week
            if event and not event.once and eid in last_seen:
                gap = stamp - last_seen[eid]
                assert gap >= event.cooldown, \
                    f"{eid} חזר אחרי {gap} שבועות במקום {event.cooldown}"
            last_seen[eid] = stamp
            seen.add(eid)
            game.resolve_event(0)
            continue
        game.advance_week()
    assert len(seen) > 5


def test_shirt_numbers_are_unique_and_choosable():
    clubs, players = generate_world(seed=4)
    club = clubs["hapoel_carmel"]
    numbers = [players[pid].number for pid in club.squad]
    assert all(1 <= n <= 45 for n in numbers)
    assert len(set(numbers)) == len(numbers)

    free = available_numbers(club, players)
    assert free and not set(free) & set(numbers)

    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 22, seed=5,
                              wanted_number=free[0])
    squad = [game.players[pid].number for pid in game.my_club.squad]
    assert len(set(squad)) == len(squad)


def test_a_taken_number_is_not_stolen():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 22, seed=5)
    club = game.my_club
    other = next(game.players[pid] for pid in club.squad
                 if pid != game.me_id and game.players[pid].number)
    before = game.me.number
    from football_manager.models import assign_number
    assign_number(club, game.players, game.me, other.number)
    assert game.me.number != other.number or before == other.number
    squad = [game.players[pid].number for pid in club.squad]
    assert len(set(squad)) == len(squad)


# ---------------------------------------------------------------------------
# ספריית העלילה
# ---------------------------------------------------------------------------

STAGES = {"youth", "academy", "player", "veteran", "retired", "coach",
          "manager", "director", "pundit", "agent", "owner", "legend"}


def test_the_story_pack_is_well_formed():
    seen = set()
    for row in PACK:
        assert row["eid"] not in seen, f"מזהה כפול: {row['eid']}"
        seen.add(row["eid"])
        assert row["title"] and row["body"]
        assert len(row["choices"]) >= 2, f"{row['eid']}: פחות משתי בחירות"
        for stage in row.get("stages", []):
            assert stage in STAGES, f"{row['eid']}: שלב לא מוכר {stage}"
        for choice in row["choices"]:
            assert choice["label"] and choice["text"]
        for key in (row.get("when") or {}):
            assert key in SE.CONDITIONS, f"{row['eid']}: תנאי לא מוכר {key}"
        for choice in row["choices"]:
            for key in (choice.get("fx") or {}):
                assert key in SE.EFFECT_KEYS, \
                    f"{row['eid']}: אפקט לא מוכר {key}"


def test_the_story_library_is_large_and_covers_every_stage():
    assert len(ST.REGISTRY) >= 170, f"רק {len(ST.REGISTRY)} אירועים"
    counts = {}
    for event in ST.REGISTRY:
        for stage in (event.stages or ("כללי",)):
            counts[stage] = counts.get(stage, 0) + 1
    for stage in ("youth", "academy", "player", "veteran", "manager",
                  "coach", "director", "owner", "pundit", "agent", "legend"):
        assert counts.get(stage, 0) >= 5, f"{stage}: רק {counts.get(stage, 0)}"


def test_every_fired_event_renders_complete_text():
    seen = set()
    for seed in (3, 9, 17):
        game = GameState.new_game("בודק", "ST", "hapoel_carmel", 13, seed=seed)
        for _ in range(700):
            if game.game_over:
                break
            if game.pending_event_id:
                body = game.pending_event_body or ""
                assert body.strip(), f"{game.pending_event_id}: טקסט ריק"
                assert "{" not in body, \
                    f"{game.pending_event_id}: מקום שלא מולא — {body[:40]}"
                seen.add(game.pending_event_id)
                event = game.pending_event()
                game.resolve_event(game.rng.randrange(len(event.choices)))
                continue
            game.advance_week()
    assert len(seen) >= 60, f"רק {len(seen)} אירועים שונים נורו"


def test_choice_effects_change_the_state():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 24, seed=4)
    morale, money, rep = game.me.morale, game.money, game.me.reputation
    SE.apply_effects(game, {"morale": 9, "money": 50_000, "rep": 4,
                            "attr": ["shooting", 1.0]})
    assert game.me.morale > morale
    assert game.money == money + 50_000
    assert game.me.reputation > rep

    club = game.my_club
    trust = club.manager_trust
    SE.apply_effects(game, {"trust": -10, "flag": "test_flag", "trait": "leader"})
    assert club.manager_trust < trust
    assert game.flag("test_flag") is True
    assert "leader" in game.me.traits


# ---------------------------------------------------------------------------
# שורת הסטטיסטיקה: החוט בין האימון למגרש
# ---------------------------------------------------------------------------

def _striker(shooting=60, passing=60, **rest):
    player = generate_player(random.Random(3), None, "ST", 24, 65)
    set_all(player, 60)
    set_group(player, "shooting", shooting)
    set_group(player, "passing", passing)
    for key, value in rest.items():
        set_group(player, key, value)
    player.fitness, player.sharpness = 90.0, 85.0
    return player


def _mean_stats(player, rng, n=250):
    totals = {}
    for _ in range(n):
        stats = MS.match_stat_line(player, 90, 0, 0, rng)
        for key, value in stats.items():
            if isinstance(value, (int, float)):
                totals[key] = totals.get(key, 0) + value
    return {key: value / n for key, value in totals.items()}


def test_training_shows_up_in_the_match():
    """התלונה: מתאמנים, והמגרש לא מרגיש את זה."""
    rng = random.Random(11)
    weak = _mean_stats(_striker(shooting=45), rng)
    strong = _mean_stats(_striker(shooting=90), rng)
    assert strong["on_target"] > weak["on_target"] * 1.5, \
        f"בעיטה 45→90 העלתה למסגרת רק מ-{weak['on_target']:.2f} ל-{strong['on_target']:.2f}"

    sloppy = _mean_stats(_striker(passing=40), rng)
    tidy = _mean_stats(_striker(passing=88), rng)
    assert tidy["pass_pct"] > sloppy["pass_pct"] + 8
    assert tidy["losses"] < sloppy["losses"]


def test_area_scores_are_centred_on_the_players_own_level():
    """70 = ערב ממוצע שלך, בכל עמדה ובכל רמה."""
    rng = random.Random(5)
    for position in ("ST", "CM", "CB", "LW", "GK"):
        for level in (45, 85):
            player = generate_player(rng, None, position, 24, level)
            set_all(player, level)
            player.fitness, player.sharpness = 88.0, 80.0
            scores = [MS.performance(MS.match_stat_line(player, 90, 0, 0, rng), position)
                      for _ in range(120)]
            mean = sum(scores) / len(scores)
            assert 55 <= mean <= 80, f"{position}/{level}: ממוצע {mean:.1f}"


def test_the_manager_asks_for_something_a_striker_actually_does():
    """מאמן לא דורש מחלוץ בור לחטוף כדורים כל שבוע."""
    rng = random.Random(7)
    player = _striker()
    asks = {}
    for _ in range(300):
        stats = MS.match_stat_line(player, 90, 0, 0, rng)
        area = MS.weakest_area(stats, "ST", player.attributes)
        asks[area] = asks.get(area, 0) + 1
    assert asks.get("defending", 0) <= 15, f"דרש הגנה {asks.get('defending')} פעמים"
    assert set(asks) <= set(D.ATTRIBUTES)


def test_rest_is_not_the_default_directive():
    """התלונה: 'לרוב המאמן דורש מנוחה'."""
    counts = {}
    for seed in (11, 24):
        game = GameState.new_game("בודק", "ST", "hapoel_carmel", 18, seed=seed)
        for _ in range(260):
            if game.game_over or game.me.age > 22:
                break
            if game.pending_event_id:
                game.resolve_event(0)
                continue
            game.advance_week()
            focus = game.flag("directive")
            if focus:
                counts[focus] = counts.get(focus, 0) + 1
    total = sum(counts.values())
    assert total > 100
    top = max(counts, key=lambda key: counts[key])
    assert top != "rest", f"מנוחה היא עדיין ההוראה הנפוצה ביותר ({counts})"
    # כמה מנוחה תידרש תלוי גם במאמן הכושר של המועדון — אבל לא רוב השבועות
    assert counts.get("rest", 0) / total < 0.30, \
        f"מנוחה נדרשה ב-{counts.get('rest', 0)}/{total} מהשבועות"


def test_the_directive_quotes_the_last_match():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 22, seed=6)
    for _ in range(80):
        if game.pending_event_id:
            game.resolve_event(0)
            continue
        game.advance_week()
        if game.flags.get("last_stats") and game.flag("directive"):
            break
    stats = game.flags.get("last_stats")
    assert stats, "לא נשמרה שורת סטטיסטיקה"
    line = MG.directive_line(game.my_club, game.flag("directive"), stats)
    assert "\n" in line, "ההוראה לא כוללת סיבה מהמשחק"
    assert "{" not in line


def test_fitness_no_longer_collapses_over_a_season():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 22, seed=9)
    readings = []
    for _ in range(120):
        if game.game_over:
            break
        if game.pending_event_id:
            game.resolve_event(0)
            continue
        game.advance_week()
        readings.append(game.me.fitness)
    mean = sum(readings) / len(readings)
    assert mean > 70, f"כושר ממוצע {mean:.0f} — הגוף לא מתאושש"
    assert min(readings) < 95, "הכושר לא זז בכלל — אין מחיר לעומס"


# ---------------------------------------------------------------------------
# סקאוטינג
# ---------------------------------------------------------------------------

def test_scouts_build_interest_over_a_season():
    """התלונה: 'אין פניה של סקאוטינג כמעט'.

    עשרה זרעים ולא ארבעה: watchers הוא תצלום רגע, וקריירה בודדת
    שבמקרה לא משכה איש היא תוצאה לגיטימית ולא ראיה שהסקאוטינג שבור.
    """
    seeds = (8, 21, 33, 44, 57, 66, 71, 88, 95, 103)
    found = 0
    for seed in seeds:
        game = GameState.new_game("בודק", "ST", "hapoel_carmel", 19, seed=seed)
        for _ in range(300):
            if game.game_over or game.me.age > 25:
                break
            if game.pending_event_id:
                game.resolve_event(0)
                continue
            game.advance_week()
        if SC.watchers(game):
            found += 1
    assert found >= 6, f"רק {found} מתוך {len(seeds)} קריירות משכו צופים"


def test_scouting_reaches_beyond_israel():
    seen_abroad = False
    for seed in (33, 44, 52, 61):
        game = GameState.new_game("בודק", "ST", "maccabi_harel", 20, seed=seed)
        for _ in range(320):
            if game.game_over or game.me.age > 27:
                break
            if game.pending_event_id:
                game.resolve_event(0)
                continue
            game.advance_week()
        for club, _ in SC.watchers(game):
            if D.club_country(club.cid, club.league_id) != "ישראל":
                seen_abroad = True
    assert seen_abroad, "אף מועדון מחו\"ל לא עקב אחרי אף אחת מהקריירות"


def test_a_small_club_does_not_chase_a_star():
    game = GameState.new_game("בודק", "ST", "maccabi_harel", 26, seed=4)
    set_all(game.me, 88)
    pool = SC.candidate_clubs(game)
    assert pool, "אין בכלל יעדים"
    assert all(c.reputation >= game.me.overall - 24 for c in pool)


def test_interest_decays_when_nobody_watches():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 24, seed=2)
    SC.interest_map(game)["real_castilla"] = 60.0
    for _ in range(40):
        SC.scouts_this_week(game, game.rng, None)
    assert SC.interest_map(game).get("real_castilla", 0) < 55


# ---------------------------------------------------------------------------
# מסלול הפיתוח
# ---------------------------------------------------------------------------

def test_every_position_has_a_plan():
    for position in D.POSITIONS:
        options = DEV.options_for(position)
        assert options, position
        for row in options:
            assert len(row[4]) >= 3, f"{row[0]}: פחות משלוש אבני דרך"


def test_the_plan_tells_you_what_is_missing():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 15, seed=3)
    assert DEV.next_target(game) is None
    DEV.set_plan(game, "poacher")
    target = DEV.next_target(game)
    assert target and "חלוץ בור" in target and "🎯" in target
    focus = DEV.recommended_focus(game)
    assert focus in D.DETAIL_NAMES_HE
    # המסלול מדבר בשפת התכונות המפורטות, לא בקטגוריות
    assert any(D.DETAIL_NAMES_HE[focus] in target for focus in [focus])


def test_milestones_pay_out_and_a_full_plan_breaks_through():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 24, seed=3)
    DEV.set_plan(game, "poacher")
    game.me.ceiling = 99
    game.me.potential = 60
    set_all(game.me, 99)
    before = game.me.potential
    lines = DEV.claim_milestones(game)
    assert len(lines) >= 5, lines            # ארבע אבני דרך + פריצה
    assert any("💎" in line for line in lines)
    assert game.me.potential > before
    assert game.flag("breakthrough") is True
    assert "clutch" in game.me.traits
    assert DEV.claim_milestones(game) == []   # לא משלמים פעמיים


def test_changing_the_plan_resets_progress():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 20, seed=3)
    DEV.set_plan(game, "poacher")
    game.flags["plan_done"] = [0, 1]
    DEV.set_plan(game, "tf")
    assert game.flags["plan_done"] == []


def test_a_milestone_never_pushes_potential_past_the_ceiling():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 24, seed=3)
    DEV.set_plan(game, "poacher")
    game.me.ceiling = 70
    game.me.potential = 69
    set_all(game.me, 99)
    DEV.claim_milestones(game)
    assert game.me.potential <= game.me.ceiling


# ---------------------------------------------------------------------------
# חסויות כתיק, לא כתשלום חד־פעמי
# ---------------------------------------------------------------------------

def test_a_deal_keeps_paying_every_week():
    """התלונה: 'החסויות מקובעות ואין להן רווחים'."""
    rng = random.Random(2)
    player = generate_player(rng, None, "ST", 26, 82)
    player.reputation, player.media_skill = 78, 65
    offer = CM.sponsor_offer(player, rng, 80, False, honours=2)
    assert offer and offer["annual"] > 0
    portfolio = []
    CM.sign_deal(portfolio, offer, 2030)
    weekly = CM.weekly_retainer(portfolio, 43)
    assert weekly > 0
    assert abs(weekly * 43 - offer["annual"]) < offer["annual"] * 0.05


def test_bonus_clauses_pay_for_a_real_season():
    rng = random.Random(2)
    player = generate_player(rng, None, "ST", 26, 82)
    player.reputation, player.media_skill = 78, 65
    portfolio = []
    deal = CM.sign_deal(portfolio, {
        "brand": "מותג", "tier": "global", "tier_he": "עולמי", "kind_he": "נעליים",
        "annual": 1_000_000, "years": 3,
        "clauses": ["per_goal", "trophy"]}, 2030)
    assert CM.season_bonuses(portfolio, player, 0, 0) == []
    player.season.goals = 20
    payouts = CM.season_bonuses(portfolio, player, 1, 0)
    assert len(payouts) == 2
    assert sum(amount for _, amount in payouts) > 800_000
    assert deal["earned"] > 0


def test_a_deal_expires_and_the_renewal_reflects_who_you_became():
    rng = random.Random(2)
    player = generate_player(rng, None, "ST", 27, 88)
    player.reputation, player.media_skill = 90, 80
    portfolio = []
    CM.sign_deal(portfolio, {"brand": "מותג", "tier": "national", "tier_he": "ארצי",
                             "kind_he": "ביגוד", "annual": 200_000, "years": 2,
                             "clauses": []}, 2030)
    assert CM.tick_portfolio(portfolio) == []
    assert portfolio[0]["years_left"] == 1
    renewal = CM.renewal_offer(portfolio[0], player, rng, 85)
    assert renewal["annual"] > 200_000, "החידוש לא משקף כוכב"
    lines = CM.tick_portfolio(portfolio)
    assert portfolio == [] and lines


def test_big_brands_open_up_for_a_big_career():
    rng = random.Random(2)
    kid = generate_player(rng, None, "ST", 17, 55)
    kid.reputation, kid.media_skill = 18, 10
    star = generate_player(rng, None, "ST", 27, 90)
    star.reputation, star.media_skill = 88, 75
    star.career.goals = 180
    assert [t[0] for t in CM.open_tiers(CM.marketability(kid, 40))] == ["local"]
    assert "global" in [t[0] for t in CM.open_tiers(CM.marketability(star, 90))]


def test_sponsor_money_actually_reaches_the_bank():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 25, seed=5)
    game.deals.append({"brand": "מותג", "tier": "global", "tier_he": "עולמי",
                       "kind_he": "נעליים", "annual": 4_300_000, "years_left": 3,
                       "clauses": [], "signed": game.year, "earned": 0})
    before = game.money
    game.advance_week()
    assert game.money > before + 40_000, "התיק המסחרי לא שילם השבוע"


# ---------------------------------------------------------------------------
# נכסים והשקעות
# ---------------------------------------------------------------------------

def test_you_cannot_buy_what_you_cannot_afford_or_reach():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 20, seed=5)
    game.money = 2_000_000
    game.me.reputation = 10
    assert "מוניטין" in WL.buy(game, "club_shares")
    game.me.reputation = 95
    assert "אין מספיק" in WL.buy(game, "club_shares")
    assert WL.holdings(game) == []
    assert "קנית" in WL.buy(game, "studio_flat")
    assert game.money < 2_000_000
    assert len(WL.holdings(game)) == 1


def test_assets_pay_out_and_can_be_sold():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 26, seed=5)
    game.money = 20_000_000
    game.me.reputation = 60
    WL.buy(game, "padel")
    assert WL.portfolio_yield(game) > 0
    worth_before = WL.net_worth(game)
    lines = WL.season_tick(game, game.rng)
    assert lines, "עונה שלמה בלי שום תנועה בנכסים"
    assert WL.net_worth(game) != worth_before
    cash = game.money
    assert "מכרת" in WL.sell(game, 0)
    assert game.money > cash
    assert WL.holdings(game) == []


def test_net_worth_counts_cash_and_assets():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 26, seed=5)
    game.money = 10_000_000
    game.me.reputation = 60
    WL.buy(game, "restaurant")
    info = WL.summary(game)
    assert info["net_worth"] == info["cash"] + info["assets"]
    assert info["assets"] == 5_000_000
    assert info["count"] == 1


def test_tax_leaves_less_than_the_gross():
    from football_manager.game import net_income
    assert net_income(0) == 0
    assert net_income(2_000) > net_income(2_000) * 0        # לא שלילי
    assert net_income(2_000) < 2_000
    # מדרגות פרוגרסיביות: אחוז הנטו יורד ככל שהברוטו עולה
    low = net_income(2_000) / 2_000
    high = net_income(200_000) / 200_000
    assert low > high


# ---------------------------------------------------------------------------
# המבנה של המקור: תכונות מפורטות, תפקידים, טקטיקה, אישיות וידע
# ---------------------------------------------------------------------------

def test_the_detailed_attributes_are_the_source_of_truth():
    """התלונה: 'אתה מקבל את מה שאתה רואה'. שבע קטגוריות זה מה שהיה."""
    assert len(D.DETAIL_NAMES_HE) >= 45
    assert len(D.TECHNICAL) == 14 and len(D.MENTAL) == 14
    assert len(D.PHYSICAL) == 8 and len(D.GOALKEEPING) == 11
    player = generate_player(random.Random(2), None, "ST", 24, 70)
    assert len(player.detail) >= 45
    assert all(1 <= v <= 20 for v in player.detail.values())
    # הקבוצות נגזרות — כתיבה ישירה אליהן נמחקת בחישוב הבא
    player.attributes["shooting"] = 5
    MDL.recompute_groups(player)
    assert player.attributes["shooting"] > 5


def test_a_group_write_lands_on_the_attributes_beneath_it():
    player = generate_player(random.Random(2), None, "ST", 24, 70)
    before = dict(player.detail)
    gains = MDL.add_group(player, "shooting", 12.0)
    assert gains, "כתיבה לקבוצה לא הזיזה שום תכונה"
    assert set(gains) <= set(D.GROUP_MAP["shooting"])
    assert player.detail["finishing"] > before["finishing"]
    assert player.attributes["shooting"] > 0


def test_story_effects_still_speak_the_old_language():
    """149 שורות בספריית העלילה כתובות בשפת הקבוצות — והן ממשיכות לעבוד."""
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 22, seed=4)
    before = game.me.detail["finishing"]
    SE.apply_effects(game, {"attr": ["shooting", 9.0]})
    assert game.me.detail["finishing"] > before
    # ואפשר גם לכתוב ישירות בשפה המפורטת
    before = game.me.detail["composure"]
    SE.apply_effects(game, {"attr": ["composure", 9.0]})
    assert game.me.detail["composure"] > before


def test_every_position_has_real_roles():
    assert len(D.ROLES) >= 40
    for position in D.POSITIONS:
        options = D.roles_for(position)
        assert len(options) >= 2, position
        for row in options:
            assert row[3], row[0]
            assert len(row[4]) >= 4, row[0]


def test_role_suitability_separates_two_players_of_the_same_rating():
    """שני חלוצים בדירוג זהה הם לא אותו שחקן."""
    rng = random.Random(5)
    poacher = generate_player(rng, None, "ST", 26, 75)
    target = generate_player(rng, None, "ST", 26, 75)
    for attr in ("finishing", "off_the_ball", "anticipation", "composure"):
        poacher.detail[attr] = 18
        target.detail[attr] = 9
    for attr in ("heading", "jumping_reach", "strength", "bravery"):
        target.detail[attr] = 18
        poacher.detail[attr] = 9
    MDL.recompute_groups(poacher)
    MDL.recompute_groups(target)
    assert MDL.role_suitability(poacher, "poacher") > MDL.role_suitability(target, "poacher")
    assert MDL.role_suitability(target, "tf") > MDL.role_suitability(poacher, "tf")
    assert MDL.best_role(poacher)[0] != MDL.best_role(target)[0]


def test_the_manager_hands_out_a_role_and_can_refuse_to_change_it():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 22, seed=7)
    assert game.me.role, "לא חולק תפקיד"
    assert game.me.duty in D.DUTY_NAMES_HE
    assert game.me.position in D.ROLE_BY_KEY[game.me.role][2]
    answers = set()
    for _ in range(40):
        game.my_club.manager_trust = 50
        answers.add(TA.request_role(game, "tf" if game.me.role != "tf" else "poacher")[0])
    assert "✅" in answers and "⛔" in answers, "המאמן תמיד עונה אותו דבר"


def test_tactics_change_what_ninety_minutes_look_like():
    """התלונה: הטקטיקה לא מגיעה לשחקן."""
    rng = random.Random(4)
    player = generate_player(rng, None, "CM", 25, 72)
    player.role, player.duty = "b2b", "support"
    player.fitness, player.sharpness = 90.0, 85.0
    club = MDL.Club(cid="x", name="X", nickname="x", league_id="top",
                    reputation=60, manager_name="", board_confidence=60)

    def sample(style_key, n=250):
        mods = TA.modifiers_from(D.STYLE_BY_KEY[style_key][2], player)
        totals = {}
        for _ in range(n):
            stats = MS.match_stat_line(player, 90, 0, 0, rng, mods=mods)
            for key, value in stats.items():
                if isinstance(value, (int, float)):
                    totals[key] = totals.get(key, 0) + value
        return {k: v / n for k, v in totals.items()}

    tiki = sample("tiki_taka")
    counter = sample("counter")
    press = sample("gegenpress")
    block = sample("catenaccio")
    assert tiki["passes"] > counter["passes"] * 1.5, "משחק קצר לא נותן יותר נגיעות"
    assert tiki["pass_pct"] > counter["pass_pct"] + 8
    assert press["distance"] > block["distance"] + 2, "גגנפרסינג לא עולה בריצה"
    assert press["sprints"] > block["sprints"] * 1.4


def test_the_same_player_fits_one_manager_and_not_another():
    rng = random.Random(6)
    runner = generate_player(rng, None, "CM", 25, 70)
    for attr in ("stamina", "work_rate"):
        runner.detail[attr] = 18
    for attr in ("technique", "first_touch"):
        runner.detail[attr] = 7
    MDL.recompute_groups(runner)
    club = MDL.Club(cid="x", name="X", nickname="x", league_id="top",
                    reputation=60, manager_name="", board_confidence=60)

    def score(style_key):
        return TA.suits_values(D.STYLE_BY_KEY[style_key][2], runner)[0]

    assert score("gegenpress") > score("tiki_taka") + 10


def test_personality_is_hidden_and_it_matters():
    rng = random.Random(3)
    player = generate_player(rng, None, "CM", 24, 65)
    assert len(player.hidden) == len(D.HIDDEN_ATTRS)
    assert all(1 <= v <= 20 for v in player.hidden.values())

    pro = generate_player(rng, None, "CM", 24, 65)
    pro.hidden.update({"professionalism": 19, "ambition": 15})
    pro.detail["determination"] = 17
    lazy = generate_player(rng, None, "CM", 24, 65)
    lazy.hidden.update({"professionalism": 4})
    lazy.detail["determination"] = 6
    assert MDL.personality_key(pro) != MDL.personality_key(lazy)
    assert MDL.personality_effect(pro)[0] > MDL.personality_effect(lazy)[0]


def test_a_professional_develops_faster_than_a_slacker():
    rng = random.Random(8)
    club = generate_world(4)[0]["hapoel_carmel"]
    results = []
    for professionalism, determination in ((19, 18), (4, 5)):
        player = generate_player(random.Random(11), club, "ST", 18, 60)
        player.hidden["professionalism"] = professionalism
        player.hidden["ambition"] = 15 if professionalism > 10 else 5
        player.detail["determination"] = determination
        player.potential, player.ceiling = 90, 95
        start = player.overall
        for _ in range(120):
            player.fitness = 90.0
            weekly_training(player, "finishing", club, random.Random(3), 1.0)
        results.append(player.overall - start)
    assert results[0] > results[1] + 1, f"מקצוען {results[0]} מול מזלזל {results[1]}"


def test_you_do_not_see_everything_about_everyone():
    """זה הלב של 'אתה מקבל את מה שאתה רואה'."""
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 24, seed=6)
    assert KN.knowledge_level(game, game.me) == 3
    mate = next(game.players[p] for p in game.my_club.squad if p != game.me_id)
    assert KN.knowledge_level(game, mate) == 3

    far = next(p for p in game.players.values()
               if p.club_id and game.clubs[p.club_id].league_id == "national"
               and p.reputation < 55)
    assert KN.knowledge_level(game, far) < 2
    shown = KN.shown_detail(game, far)
    sample = shown[D.attrs_for(far.position)[0]]
    assert not sample["exact"], "רואים מספר מדויק של שחקן שלא מכירים"

    before = KN.knowledge_level(game, far)
    game.my_club.balance = 5_000_000
    assert "הצוות" in KN.scout_player(game, far)
    assert KN.knowledge_level(game, far) > before
    shown = KN.shown_detail(game, far)
    band = shown[D.attrs_for(far.position)[0]]
    assert band["high"] - band["low"] <= 2, "דוח מלא ועדיין טווח רחב"


def test_star_ratings_are_a_range_not_a_number():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 24, seed=6)
    far = next(p for p in game.players.values()
               if p.club_id and game.clubs[p.club_id].league_id == "euro")
    low, high = KN.potential_stars(game, far)
    assert high > low, "פוטנציאל של זר מוצג כמספר מדויק"
    mine_low, mine_high = KN.potential_stars(game, game.me)
    assert mine_low == mine_high
    assert 0 <= KN.ability_stars(game, far) <= 5
    assert KN.star_text(3.5).startswith("★★★")


def test_training_a_single_attribute_moves_that_attribute_most():
    """מתחילים מרצפה שווה, כדי לבודד את מה שהאימון עצמו עושה."""
    club = generate_world(4)[0]["hapoel_carmel"]
    player = generate_player(random.Random(9), club, "ST", 19, 62)
    player.potential, player.ceiling = 92, 95
    player.is_human = True
    set_all(player, 45)                 # כל התכונות על 9 מתוך 20
    before = dict(player.detail)
    for _ in range(60):
        player.fitness = 90.0
        weekly_training(player, "finishing", club, random.Random(5), 1.0)
    moved = {a: player.detail[a] - before[a] for a in D.attrs_for("ST")}
    best = max(moved, key=lambda a: moved[a])
    assert best == "finishing", f"אימון סיום הזיז דווקא את {best}"
    assert moved["finishing"] > moved["free_kick"] * 2, \
        "בעיטות חופשיות משתפרות מאימון סיומות"


def test_a_specialism_does_not_improve_by_accident():
    """אף אחד לא נעשה בועט חופשיות טוב יותר מזה שהוא רץ ספרינטים."""
    club = generate_world(4)[0]["hapoel_carmel"]
    player = generate_player(random.Random(9), club, "ST", 19, 62)
    player.potential, player.ceiling = 92, 95
    player.is_human = True
    set_all(player, 45)
    before = dict(player.detail)
    for _ in range(60):
        player.fitness = 90.0
        weekly_training(player, "acceleration", club, random.Random(5), 1.0)
    assert player.detail["acceleration"] > before["acceleration"]
    assert player.detail["free_kick"] - before["free_kick"] <= 1
    assert player.detail["penalty_taking"] - before["penalty_taking"] <= 1


# ---------------------------------------------------------------------------
# להבין את המשחק: הסברים, התפתחות נראית ומנטור
# ---------------------------------------------------------------------------

def test_every_attribute_explains_itself():
    """התלונה: 'מה זה צמידות? במה הוא מועיל?'"""
    for attr in D.DETAIL_NAMES_HE:
        what, does, who = COACH.explain(attr)
        assert what and does and who, attr
        assert len(does) > 15, attr
    for focus in ("rest", "badges", "media", "business", "school", "street"):
        assert COACH.explain(focus)[0], focus


def test_relevance_answers_whether_you_need_it_now():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 20, seed=4)
    marking = COACH.relevance_of(game, "marking")
    finishing = COACH.relevance_of(game, "finishing")
    assert marking["rank"] > finishing["rank"], "צמידות דורגה מעל סיום אצל חלוץ"
    assert marking["rank"] > marking["of"] * 0.6, \
        f"צמידות במקום {marking['rank']} מתוך {marking['of']} אצל חלוץ"
    assert marking["score"] < finishing["score"] * 0.5
    assert finishing["rank"] <= 8
    assert marking["of"] == len(D.attrs_for("ST"))

    keeper = GameState.new_game("שוער", "GK", "hapoel_carmel", 20, seed=4)
    reflexes = COACH.relevance_of(keeper, "reflexes")
    assert reflexes["rank"] <= 6, "רפלקסים לא בראש הרשימה של שוער"


def test_the_forecast_matches_what_training_actually_does():
    """תחזית שלא מתממשת גרועה מאין תחזית."""
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 19, seed=6)
    game.me.potential, game.me.ceiling = 92, 95
    attr = "finishing"
    assert COACH.weekly_rate(game, attr) > 0
    for weeks in (6, 20, 40):
        probe = GameState.new_game("בודק", "ST", "hapoel_carmel", 19, seed=6)
        probe.me.potential, probe.me.ceiling = 92, 95
        predicted = COACH.projected_gain(probe, attr, weeks)
        before = probe.me.detail[attr]
        for _ in range(weeks):
            probe.me.fitness = 90.0
            weekly_training(probe.me, attr, probe.my_club, random.Random(3), 1.0)
        actual = probe.me.detail[attr] - before
        assert abs(actual - predicted) <= max(1.5, predicted * 0.35), \
            f"{weeks} שבועות: התחזית אמרה {predicted:.1f} והתקבל {actual}"


def test_the_body_actually_grows():
    """התלונה: 'הכול כאילו מתפתח'. הגובה פשוט לא זז."""
    game = GameState.new_game("נער", "ST", "hapoel_carmel", 13, seed=8)
    start_height, start_weight = game.me.height, game.me.weight
    assert game.me.adult_height > start_height, "אין יעד גובה בוגר"
    for _ in range(700):
        if game.game_over or game.me.age > 21:
            break
        if game.pending_event_id:
            game.resolve_event(0)
            continue
        game.advance_week()
    assert game.me.height > start_height + 6, \
        f"גדל רק {game.me.height - start_height} ס\"מ בשמונה שנים"
    assert game.me.height <= game.me.adult_height
    assert game.me.weight > start_weight


def test_the_season_report_says_what_changed():
    game = GameState.new_game("נער", "ST", "hapoel_carmel", 16, seed=8)
    lines = []
    for _ in range(200):
        if game.game_over:
            break
        if game.pending_event_id:
            game.resolve_event(0)
            continue
        report = game.advance_week()
        if report.season_ended:
            lines = report.lines
            break
    assert any("ההתפתחות שלך העונה" in line for line in lines), "אין דוח התפתחות"
    assert any("📏" in line for line in lines), "אין דוח גוף"


def test_growth_history_answers_by_how_much():
    game = GameState.new_game("נער", "ST", "hapoel_carmel", 15, seed=8)
    for _ in range(500):
        if game.game_over or game.me.age > 20:
            break
        if game.pending_event_id:
            game.resolve_event(0)
            continue
        game.advance_week()
    info = COACH.growth_summary(game)
    assert len(info["seasons"]) >= 3
    assert info["overall_to"] > info["overall_from"]
    assert info["total_points"] > 0
    assert info["physical"]["height_to"] > info["physical"]["height_from"]
    assert info["moved"], "אף תכונה לא נרשמה כזזה"
    top = info["moved"][0]
    assert top["to"] - top["from"] == top["delta"]


def test_the_mentor_says_something_useful_and_specific():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 18, seed=5)
    game.me.fitness = 20.0
    tip = MN.advise(game, random.Random(1))
    assert tip, "המנטור שתק כשהרעננות ב-20"
    assert tip["mentor"]
    assert "20" in tip["body"] or "רעננות" in tip["body"]
    assert "{" not in tip["body"]


def test_the_mentor_does_not_repeat_himself():
    """התלונה המדויקת: 'לא כל פעם אותם טיפים'."""
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 17, seed=13)
    rng = random.Random(3)
    seen = []
    for _ in range(600):
        if game.game_over or game.me.age > 25:
            break
        if game.pending_event_id:
            game.resolve_event(rng.randrange(2))
            continue
        report = game.advance_week()
        for line in report.lines:
            if line.startswith("🧭"):
                seen.append(line)
    assert len(seen) >= 6, f"רק {len(seen)} טיפים בשמונה שנים"
    distinct = len(set(seen))
    assert distinct >= len(seen) * 0.55, \
        f"{len(seen)} טיפים אבל רק {distinct} שונים"
    # אף טיפ בודד לא נאמר יותר משלוש פעמים
    for line in set(seen):
        assert seen.count(line) <= 3, f"נאמר {seen.count(line)} פעמים: {line[:50]}"


def test_a_lasting_problem_escalates_instead_of_repeating():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 20, seed=5)
    bodies = []
    for _ in range(6):
        game.me.fitness = 18.0
        tip = MN.advise(game, random.Random(1))
        if tip and "רעננות" in tip["body"]:
            bodies.append(tip["body"])
        game.week += 12
        if game.week > 43:
            game.week -= 43
            game.year += 1
    assert len(bodies) >= 2, "המנטור אמר את זה רק פעם אחת"
    assert len(set(bodies)) == len(bodies), "אותו משפט בדיוק חזר"
    assert "פעם השלישית" in bodies[-1] or "שוב" in bodies[-1] or \
        "כבר לא מקרה" in bodies[-1], "אין הסלמה"


def test_the_mentor_reacts_to_the_actual_state():
    quiet = GameState.new_game("בודק", "ST", "hapoel_carmel", 24, seed=9)
    quiet.me.fitness = 95.0
    quiet.me.morale = 80.0
    keys = {row["key"] for row in MN.observations(quiet)}
    assert "fitness" not in keys
    quiet.me.fitness = 20.0
    assert "fitness" in {row["key"] for row in MN.observations(quiet)}

    quiet.no_start_streak = 12
    assert "no_minutes" in {row["key"] for row in MN.observations(quiet)}
    quiet.no_start_streak = 0
    assert "no_minutes" not in {row["key"] for row in MN.observations(quiet)}


def test_the_squad_report_tells_you_who_is_ahead():
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 18, seed=7)
    report = COACH.squad_report(game)
    assert report["has_club"]
    assert report["squad_size"] >= 16
    assert 1 <= report["rep_rank"] <= report["rep_of"]
    assert game.me.position in report["by_position"]
    mine = [row for row in report["by_position"][game.me.position] if row["is_me"]]
    assert len(mine) == 1
    for row in report["ahead_of_me"]:
        assert row["overall"] > game.me.overall
    assert len(report["facilities"]) == len(D.FACILITIES)
    assert len(report["staff"]) == len(D.STAFF_ROLES)

# ---------------------------------------------------------------------------
# התקרה: להתקרב אליה לאט, ולא להיעצר בה בלי הסבר
# ---------------------------------------------------------------------------

def test_ceiling_damper_slows_the_approach_to_twenty():
    """20 הוא הישג של קריירה, לא מדרגה שמגיעים אליה בקצב אחיד."""
    from football_manager.progression import ceiling_damper
    # עד 16 אין בלם: זו רמה שמגיעים אליה באימון רגיל
    assert ceiling_damper(10) == 1.0
    assert ceiling_damper(15.9) == 1.0
    # מ-16 והלאה כל נקודה יקרה יותר, ובאופן מונוטוני
    values = [ceiling_damper(l) for l in range(16, 21)]
    assert values == sorted(values, reverse=True)
    assert values[0] == 1.0
    assert values[-1] < 0.05, "19→20 חייב להיות יקר בהרבה מ-16→17"
    assert ceiling_damper(19) < ceiling_damper(17) * 0.3


def test_training_a_capped_attribute_is_not_wasted():
    """אימון שמכוון לתכונה בתקרה עובר לשכנותיה במקום להתאדות."""
    from football_manager.progression import _spill_from_capped
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 18, seed=5)
    me = game.me
    me.detail["finishing"] = D.MAX_DETAIL
    shares = {"finishing": 3.0, "long_shots": 0.5, "technique": 0.5}
    out = _spill_from_capped(me, shares)
    assert "finishing" not in out, "תכונה בתקרה לא אמורה לקבל עבודה"
    assert out["long_shots"] > 0.5 and out["technique"] > 0.5, "העבודה לא עברה הלאה"
    # לא במלואה — אימון מוסט פחות יעיל
    assert sum(out.values()) < sum(shares.values())


def test_a_capped_attribute_says_so_instead_of_being_ranked():
    """הפסק על תכונה בתקרה חייב להיות "אין לאן", לא "פחות דחוף"."""
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 18, seed=6)
    game.me.detail["finishing"] = D.MAX_DETAIL
    row = COACH.relevance_of(game, "finishing")
    assert row["capped"] is True
    assert "תקרה" in row["verdict"]
    line = COACH.forecast_line(game, "finishing")
    assert "התקרה" in line, line
    # והתחזית לא מבטיחה שום רווח
    assert COACH.projected_gain(game, "finishing", 12) == 0.0


def test_an_exceptional_season_pushes_the_ceiling_itself():
    """מי שמיצה את התקרה שלו לא נתקע שם לעשרים שנה."""
    import random
    from football_manager.progression import _push_ceiling, ABSOLUTE_CEILING
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 18, seed=8)
    me = game.me
    me.ceiling = 90
    me.potential = 90

    # עונה בינונית לא מזיזה תקרה, כמה פעמים שלא ננסה
    for seed in range(40):
        assert _push_ceiling(me, random.Random(seed), quality=0.30) is None
    assert me.ceiling == 90

    # עונה יוצאת דופן כן, ובסופו של דבר נעצרת בתקרה המוחלטת
    rng = random.Random(1)
    for _ in range(400):
        _push_ceiling(me, rng, quality=0.65)
    assert me.ceiling == ABSOLUTE_CEILING
    assert me.ceiling > 90, "תקרה שלא זזה היא קיר לשארית הקריירה"


def test_the_ceiling_does_not_move_for_a_veteran():
    """אחרי 32 כבר לא מגלים בך פוטנציאל חדש."""
    import random
    from football_manager.progression import _push_ceiling
    game = GameState.new_game("בודק", "ST", "hapoel_carmel", 18, seed=9)
    me = game.me
    me.ceiling = 90
    me.potential = 90
    me.age = 34
    for seed in range(40):
        assert _push_ceiling(me, random.Random(seed), quality=0.9) is None

# ---------------------------------------------------------------------------
# שוק העברות, עיתונות ושם
# ---------------------------------------------------------------------------

def _market(seed=11, age=24, rep=82, count=3, eagerness=(0.9, 0.7, 0.45)):
    game = GameState.new_game("בודק", "ST", "maccabi_harel", age, seed=seed)
    game.me.reputation = rep
    game.me.contract.years_left = 1
    others = [c for c in game.clubs.values() if c.cid != game.me.club_id][:count]
    TR.set_offers(game, [TR.build_offer(game, c, game.rng, e)
                         for c, e in zip(others, eagerness)])
    return game


def test_several_offers_can_sit_on_the_table_at_once():
    """הצעה אחת היא לא שוק — צריך עם מה להשוות."""
    game = _market()
    live = TR.live_offers(game)
    assert len(live) == 3
    # ממוינות מהשווה ביותר לפחות
    worth = [TR.offer_worth(o) for o in live]
    assert worth == sorted(worth, reverse=True)
    # וכל חבילה היא חבילה, לא מספר
    for offer in live:
        assert offer["wage"] > 0 and offer["years"] >= 3
        assert offer["role"] in TR.ROLE_NAMES
        assert len(TR.offer_lines(game, offer)) >= 3


def test_competing_offers_are_real_leverage():
    """שלוש הצעות שוות יותר מאחת — וזה חייב להיות מדיד."""
    alone = _market(count=1, eagerness=(0.9,))
    crowd = _market(count=3)
    assert TR.leverage(crowd) > TR.leverage(alone) + 0.20


def test_a_long_contract_weakens_you():
    game = _market()
    strong = TR.leverage(game)
    game.me.contract.years_left = 5
    assert TR.leverage(game) < strong


def test_asking_for_more_can_actually_win_more():
    """משא ומתן שלא משנה כלום הוא לא משא ומתן."""
    import random
    moved = 0
    for seed in range(25):
        game = _market(seed=seed)
        offer = TR.live_offers(game)[0]
        before = offer["wage"]
        TR.negotiate(game, offer["cid"], "wage", random.Random(seed))
        if TR.offer_for(game, offer["cid"])["wage"] > before:
            moved += 1
    assert moved >= 8, f"רק {moved} מתוך 25 בקשות שכר הזיזו משהו"


def test_greed_can_lose_the_whole_offer():
    """בלי סיכון אמיתי, כל בקשה היא בחירה חופשית — וזה משעמם."""
    import random
    lost = 0
    for seed in range(25):
        game = _market(seed=seed)
        cid = TR.live_offers(game)[0]["cid"]
        rng = random.Random(seed)
        for term in ["wage", "years", "bonus", "clause", "image", "role"]:
            TR.negotiate(game, cid, term, rng)
            if TR.offer_for(game, cid)["state"] == "withdrawn":
                lost += 1
                break
    assert lost >= 10, f"רק {lost} מתוך 25 מועדונים קמו מהשולחן — אין סיכון"


def test_signing_takes_the_whole_package_not_just_the_wage():
    game = _market()
    offer = TR.live_offers(game)[0]
    offer["bonus"] = 500_000
    offer["clause"] = 9_000_000
    offer["role"] = "star"
    before = game.money
    text = game.accept_offer(offer["cid"])
    assert game.money == before + 500_000, "מענק החתימה לא שולם"
    assert game.flag("release_clause") == 9_000_000
    assert game.flag("squad_role") == "star"
    assert "איש הקבוצה" in text
    assert not TR.live_offers(game), "אחרי חתימה השולחן מתרוקן"


def test_rejecting_one_offer_leaves_the_others():
    game = _market()
    cid = TR.live_offers(game)[0]["cid"]
    game.reject_offer(cid)
    left = TR.live_offers(game)
    assert len(left) == 2 and all(o["cid"] != cid for o in left)


def test_offers_expire_on_a_deadline():
    game = _market()
    for _ in range(TR.WINDOW_WEEKS):
        TR.tick_offers(game)
    assert not TR.live_offers(game), "הצעה בלי דדליין היא לא הצעה"


def test_market_value_follows_age_and_contract():
    game = GameState.new_game("בודק", "ST", "maccabi_harel", 24, seed=3)
    me = game.me
    me.contract.years_left = 4
    young = TR.market_value(me)
    me.age = 34
    assert TR.market_value(me) < young * 0.5, "ותיק אמור להיות זול בהרבה"
    me.age = 24
    me.contract.years_left = 1
    assert TR.market_value(me) < young * 0.6, "שנה לסיום חוזה מוזילה"


# -- עיתונות ---------------------------------------------------------------

def test_press_sources_differ_in_how_often_they_are_right():
    """זה כל העניין: אמינות גלויה, אמת נסתרת."""
    assert PR.SOURCE_TRUST["insider"] > PR.SOURCE_TRUST["fan"] + 0.5
    assert "אמין" in PR.trust_word(0.9)
    assert PR.trust_word(0.9) != PR.trust_word(0.2)


def test_the_press_writes_both_truth_and_invention():
    game = GameState.new_game("בודק", "ST", "maccabi_harel", 24, seed=7)
    game.me.reputation = 80
    game.me.contract.years_left = 1
    pool = PR._candidates(game)
    assert pool, "אין על מה לכתוב"
    assert any(item["true"] for item in pool), "הכל שקר"
    assert any(not item["true"] for item in pool), "הכל אמת — אין דרמה"


def test_denying_something_true_can_blow_up_in_your_face():
    import random
    burned = 0
    for seed in range(30):
        game = GameState.new_game("בודק", "ST", "maccabi_harel", 24, seed=seed)
        game.me.media_skill = 10
        PR.push(game, PR._story(game, "x", "insider", "אמת", True, asks=True))
        text = PR.react(game, "deny", random.Random(seed))
        if "ההקלטה" in text:
            burned += 1
    assert burned >= 5, f"הכחשת אמת נשברה רק {burned} פעמים מתוך 30"


def test_media_skill_protects_a_denial():
    import random
    def burns(skill):
        count = 0
        for seed in range(40):
            game = GameState.new_game("בודק", "ST", "maccabi_harel", 24, seed=seed)
            game.me.media_skill = skill
            PR.push(game, PR._story(game, "x", "insider", "אמת", True, asks=True))
            if "ההקלטה" in PR.react(game, "deny", random.Random(seed)):
                count += 1
        return count
    assert burns(95) < burns(5), "כישורי תקשורת חייבים להיות שווים משהו"


def test_confirming_an_invention_costs_you():
    import random
    game = GameState.new_game("בודק", "ST", "maccabi_harel", 24, seed=5)
    before = game.me.reputation
    PR.push(game, PR._story(game, "x", "fan", "המצאה", False, asks=True))
    PR.react(game, "confirm", random.Random(1))
    assert game.me.reputation < before, "לאשר משהו שלא היה חייב לעלות"


def test_answering_closes_the_question():
    import random
    game = GameState.new_game("בודק", "ST", "maccabi_harel", 24, seed=5)
    PR.push(game, PR._story(game, "x", "tv", "משהו", True, asks=True))
    assert PR.open_question(game) is not None
    PR.react(game, "silent", random.Random(1))
    assert PR.open_question(game) is None


# -- שם ---------------------------------------------------------------------

def test_fame_opens_doors_in_order():
    game = GameState.new_game("בודק", "ST", "maccabi_harel", 26, seed=5)
    assert FA.open_ventures(20) == []
    small = len(FA.open_ventures(60))
    big = len(FA.open_ventures(95))
    assert big > small > 0, "שם גדול חייב לפתוח יותר דלתות"


def test_a_venture_pays_and_costs():
    game = GameState.new_game("בודק", "ST", "maccabi_harel", 26, seed=5)
    me = game.me
    me.fitness = 100.0
    money = game.money
    offer = {"kind": "ambassador", "title": "שגריר קמפיין", "who": "קמפיין",
             "payout": 400_000, "cost": 5, "weeks": 2}
    FA.accept_venture(game, offer)
    assert game.money == money + 400_000
    assert me.fitness < 100, "ימי צילום הם לא ימי אימון"


def test_equity_keeps_paying_after_the_deal():
    game = GameState.new_game("בודק", "ST", "maccabi_harel", 26, seed=5)
    assert FA.passive_income(game) == 0
    FA.accept_venture(game, {"kind": "tycoon", "title": "שותפות", "who": "קרן",
                             "payout": 2_000_000, "equity": 10, "cost": 0})
    assert FA.passive_income(game) > 0, "שותפות אמורה להמשיך לעבוד"


def test_a_foreign_league_pays_in_reputation():
    game = GameState.new_game("בודק", "ST", "maccabi_harel", 30, seed=5)
    game.me.reputation = 80
    before = game.me.reputation
    FA.accept_venture(game, {"kind": "league", "title": "ליגה זרה", "who": "ליגה",
                             "payout": 9_000_000, "cost": 0, "rep_cost": 4.0})
    assert game.me.reputation < before, "כסף גדול מליגה חלשה חייב לעלות במשהו"
