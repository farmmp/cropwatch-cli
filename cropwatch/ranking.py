"""Rank states by crop progress value for a given week."""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


class RankingError(Exception):
    pass


@dataclass
class StateRank:
    state: str
    value: float
    rank: int


def rank_states(
    records: List[dict],
    week_ending: str,
    commodity: str,
    category: str,
    ascending: bool = False,
) -> List[StateRank]:
    """Return states ranked by their progress value for a specific week."""
    if not records:
        raise RankingError("No records provided for ranking.")

    filtered = [
        r for r in records
        if r.get("week_ending") == week_ending
        and r.get("commodity_desc", "").lower() == commodity.lower()
        and r.get("short_desc", "").lower().find(category.lower()) != -1
        and r.get("state_alpha") not in (None, "", "US")
    ]

    parsed: List[tuple[str, float]] = []
    for r in filtered:
        try:
            val = float(r["Value"])
            parsed.append((r["state_alpha"], val))
        except (KeyError, ValueError, TypeError):
            continue

    if not parsed:
        raise RankingError(
            f"No numeric state data found for week={week_ending}, "
            f"commodity={commodity}, category={category}."
        )

    parsed.sort(key=lambda x: x[1], reverse=not ascending)
    return [
        StateRank(state=state, value=value, rank=i + 1)
        for i, (state, value) in enumerate(parsed)
    ]


def format_ranking(ranks: List[StateRank], title: str = "State Ranking") -> str:
    """Format ranked states as a text table."""
    lines = [title, "-" * 30]
    for sr in ranks:
        bar_len = int(sr.value / 2)  # scale 0-100 to 0-50
        bar = "#" * bar_len
        lines.append(f"{sr.rank:>3}. {sr.state:<6} {sr.value:>6.1f}%  {bar}")
    return "\n".join(lines)
