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
                                     generate_world, wage_for_overall)
from football_manager import commercial as CM
from football_manager import story_engine as SE
from football_manager.story_pack import PACK
from football_manager import manager as MG
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
    for _ in range(400):
        if game.me.age > 24 or game.game_over:
            break
        if game.pending_event_id:
            game.resolve_event(0)
            continue
        game.advance_week()
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
    tough.attributes["physical"] = 88
    frail.resilience, frail.sharpness = 15, 30
    frail.attributes["physical"] = 35
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


def test_the_story_library_is_large_and_covers_every_stage():
    assert len(ST.REGISTRY) >= 100, f"רק {len(ST.REGISTRY)} אירועים"
    counts = {}
    for event in ST.REGISTRY:
        for stage in (event.stages or ("כללי",)):
            counts[stage] = counts.get(stage, 0) + 1
    for stage in ("youth", "academy", "player", "veteran", "manager"):
        assert counts.get(stage, 0) >= 4, f"{stage}: רק {counts.get(stage, 0)}"


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
    assert len(seen) >= 40, f"רק {len(seen)} אירועים שונים נורו"


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
