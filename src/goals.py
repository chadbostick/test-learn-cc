import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable
from collections import Counter


@dataclass
class Goal:
    name: str
    description: str
    points: int
    color_check: Optional[Callable]   # (hand) -> bool          | None = no draw phase
    number_check: Optional[Callable]  # (hand) -> (bool, info)  | None = no roll phase


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

def _two_color_pairs(hand):
    """At least two distinct colors each appearing 2+ times."""
    counts = Counter(d.color for d in hand)
    qualifying = [color for color, n in counts.items() if n >= 2]
    return len(qualifying) >= 2


def _two_number_pairs(hand):
    """Two pairs (same color + same number) using different colors and different numbers."""
    groups = Counter((d.color, d.value) for d in hand)
    pairs = [(color, val) for (color, val), cnt in groups.items() if cnt >= 2]
    for i in range(len(pairs)):
        for j in range(i + 1, len(pairs)):
            c1, v1 = pairs[i]
            c2, v2 = pairs[j]
            if c1 != c2 and v1 != v2:
                return True, [pairs[i], pairs[j]]
    return False, None


# ---------------------------------------------------------------------------
# Registry and loader
# ---------------------------------------------------------------------------

CHECK_REGISTRY = {
    "two_color_pairs": _two_color_pairs,
    "two_number_pairs": _two_number_pairs,
}


def load_goals():
    path = Path(__file__).parent / "goals.json"
    with open(path) as f:
        data = json.load(f)
    return [
        Goal(
            name=d["name"],
            description=d["description"],
            points=d["points"],
            color_check=CHECK_REGISTRY.get(d.get("color_check")),
            number_check=CHECK_REGISTRY.get(d.get("number_check")),
        )
        for d in data
    ]
