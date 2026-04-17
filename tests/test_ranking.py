import pytest
from cropwatch.ranking import rank_states, format_ranking, RankingError, StateRank


def _make_record(state, value, week="2024-05-05", commodity="Corn", cat="planted"):
    return {
        "state_alpha": state,
        "week_ending": week,
        "commodity_desc": commodity,
        "short_desc": f"Corn - {cat.upper()}, PCT",
        "Value": str(value),
    }


SAMPLE = [
    _make_record("IA", 72),
    _make_record("IL", 55),
    _make_record("MN", 88),
    _make_record("US", 70),  # should be excluded
]


def test_rank_states_basic():
    ranks = rank_states(SAMPLE, "2024-05-05", "Corn", "planted")
    assert len(ranks) == 3
    assert ranks[0].state == "MN"
    assert ranks[0].rank == 1


def test_rank_states_ascending():
    ranks = rank_states(SAMPLE, "2024-05-05", "Corn", "planted", ascending=True)
    assert ranks[0].state == "IL"
    assert ranks[0].value == 55.0


def test_rank_states_excludes_us():
    states = [r.state for r in rank_states(SAMPLE, "2024-05-05", "Corn", "planted")]
    assert "US" not in states


def test_rank_states_empty_raises():
    with pytest.raises(RankingError, match="No records"):
        rank_states([], "2024-05-05", "Corn", "planted")


def test_rank_states_no_match_raises():
    with pytest.raises(RankingError, match="No numeric"):
        rank_states(SAMPLE, "2024-01-01", "Corn", "planted")


def test_rank_states_skips_bad_values():
    records = SAMPLE + [_make_record("OH", "N/A")]
    ranks = rank_states(records, "2024-05-05", "Corn", "planted")
    states = [r.state for r in ranks]
    assert "OH" not in states


def test_format_ranking_contains_title():
    ranks = rank_states(SAMPLE, "2024-05-05", "Corn", "planted")
    output = format_ranking(ranks, title="Test Ranking")
    assert "Test Ranking" in output


def test_format_ranking_contains_states():
    ranks = rank_states(SAMPLE, "2024-05-05", "Corn", "planted")
    output = format_ranking(ranks)
    assert "MN" in output
    assert "IA" in output
    assert "IL" in output
