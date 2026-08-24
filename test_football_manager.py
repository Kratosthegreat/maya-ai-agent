# -*- coding: utf-8 -*-
"""בדיקות למשחק ניהול הכדורגל (football_manager)."""

import json
import os
import random

import pytest

from football_manager import data as D
from football_manager import story as ST
from football_manager.engine import (pick_lineup, position_fit, simulate_match,
                                     team_strength)
from football_manager.game import SEASON_WEEKS, GameState, round_robin
from football_manager.models import (generate_player, generate_world,
                                     wage_for_overall)
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
    assert len(moved) == 4                    # שתיים עולות, שתיים יורדות
    for league_id in ("top", "national"):
        count = sum(1 for c in game.clubs.values() if c.league_id == league_id)
        assert count == 12


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
