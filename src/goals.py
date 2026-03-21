import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable
from collections import Counter
from itertools import combinations


@dataclass
class Goal:
    name: str
    description: str
    points: int
    color_check: Optional[Callable]   # (hand) -> bool          | None = no draw phase
    number_check: Optional[Callable]  # (hand) -> (bool, info)  | None = no roll phase


# ─────────────────────────────────────────────────────────────────────────────
# Color check functions  (hand) → bool
# ─────────────────────────────────────────────────────────────────────────────

def _two_color_pairs(hand):
    counts = Counter(d.color for d in hand)
    return len([c for c, n in counts.items() if n >= 2]) >= 2

def _color_two_same(hand):
    return max(Counter(d.color for d in hand).values()) >= 2

def _color_three_same(hand):
    return max(Counter(d.color for d in hand).values()) >= 3

def _color_four_same(hand):
    return max(Counter(d.color for d in hand).values()) >= 4

def _color_six_same(hand):
    return len(set(d.color for d in hand)) == 1

def _color_two_three_same(hand):
    counts = Counter(d.color for d in hand)
    return len([n for n in counts.values() if n >= 3]) >= 2

def _color_three_unique(hand):
    return len(set(d.color for d in hand)) >= 3

def _color_four_unique(hand):
    return len(set(d.color for d in hand)) >= 4

def _color_five_unique(hand):
    return len(set(d.color for d in hand)) >= 5

def _color_six_unique(hand):
    return len(set(d.color for d in hand)) == 6

def _color_only_red_yellow(hand):
    return all(d.color in ("Red", "Yellow") for d in hand)

def _color_only_blue_orange(hand):
    return all(d.color in ("Blue", "Orange") for d in hand)

def _color_only_purple_green(hand):
    return all(d.color in ("Purple", "Green") for d in hand)

def _color_two_colors_five_plus(hand):
    counts = Counter(d.color for d in hand)
    top_two = sorted(counts.values(), reverse=True)[:2]
    return sum(top_two) >= 5


# ─────────────────────────────────────────────────────────────────────────────
# Number check functions  (hand) → (bool, info)
# ─────────────────────────────────────────────────────────────────────────────

def _two_number_pairs(hand):
    groups = Counter((d.color, d.value) for d in hand)
    pairs = [(color, val) for (color, val), cnt in groups.items() if cnt >= 2]
    for i in range(len(pairs)):
        for j in range(i + 1, len(pairs)):
            c1, v1 = pairs[i]
            c2, v2 = pairs[j]
            if c1 != c2 and v1 != v2:
                return True, [pairs[i], pairs[j]]
    return False, None

def _number_two_same(hand):
    return max(Counter(d.value for d in hand).values()) >= 2, None

def _number_three_same(hand):
    return max(Counter(d.value for d in hand).values()) >= 3, None

def _number_four_same(hand):
    return max(Counter(d.value for d in hand).values()) >= 4, None

def _number_five_same(hand):
    return max(Counter(d.value for d in hand).values()) >= 5, None

def _number_six_same(hand):
    return len(set(d.value for d in hand)) == 1, None

def _has_n_straight(values_set, n):
    for start in range(1, 7 - n + 1):
        if all(start + i in values_set for i in range(n)):
            return True
    return False

def _number_two_straight(hand):
    return _has_n_straight(set(d.value for d in hand), 2), None

def _number_three_straight(hand):
    return _has_n_straight(set(d.value for d in hand), 3), None

def _number_four_straight(hand):
    return _has_n_straight(set(d.value for d in hand), 4), None

def _number_five_straight(hand):
    return _has_n_straight(set(d.value for d in hand), 5), None

def _number_six_straight(hand):
    return set(d.value for d in hand) == {1, 2, 3, 4, 5, 6}, None

def _number_four_straight_no_6(hand):
    if any(d.value == 6 for d in hand):
        return False, None
    return _has_n_straight(set(d.value for d in hand), 4), None

def _sum_without(hand, min_sum, exclude):
    if any(d.value in exclude for d in hand):
        return False, None
    return sum(d.value for d in hand) >= min_sum, None

def _number_sum_without_1_ge11(hand):  return _sum_without(hand, 11, {1})
def _number_sum_without_2_ge12(hand):  return _sum_without(hand, 12, {2})
def _number_sum_without_34_ge17(hand): return _sum_without(hand, 17, {3, 4})
def _number_sum_without_46_ge14(hand): return _sum_without(hand, 14, {4, 6})
def _number_sum_without_4_ge20(hand):  return _sum_without(hand, 20, {4})
def _number_sum_without_5_ge23(hand):  return _sum_without(hand, 23, {5})
def _number_sum_without_6_ge29(hand):  return _sum_without(hand, 29, {6})

def _number_sum_with_5_ge15(hand):
    if not any(d.value == 5 for d in hand):
        return False, None
    return sum(d.value for d in hand) >= 15, None

def _number_sum_ge18(hand):
    return sum(d.value for d in hand) >= 18, None

def _number_sum_ge36(hand):
    return sum(d.value for d in hand) >= 36, None

def _number_exact_25(hand):
    return sum(d.value for d in hand) == 25, None

def _number_odd_even_even(hand):
    values = [d.value for d in hand]
    odds  = sum(v % 2     for v in values)
    evens = sum(1 - v % 2 for v in values)
    return odds >= 1 and evens >= 2, None

def _number_even_odd_odd_odd(hand):
    values = [d.value for d in hand]
    odds  = sum(v % 2     for v in values)
    evens = sum(1 - v % 2 for v in values)
    return evens >= 1 and odds >= 3, None

def _number_full_house(hand):
    vals = sorted(Counter(d.value for d in hand).values(), reverse=True)
    return len(vals) >= 2 and vals[0] >= 3 and vals[1] >= 2, None

def _number_four_of_a_kind_plus_pair(hand):
    vals = sorted(Counter(d.value for d in hand).values(), reverse=True)
    return len(vals) >= 2 and vals[0] >= 4 and vals[1] >= 2, None

def _number_three_straight_two_doubles(hand):
    counts = Counter(d.value for d in hand)
    values = set(d.value for d in hand)
    for start in range(1, 5):
        a, c = start, start + 2
        if a in values and (start + 1) in values and c in values:
            if counts[a] >= 2 and counts[c] >= 2:
                return True, None
    return False, None

def _number_two_same_same_color(hand):
    groups = Counter((d.color, d.value) for d in hand)
    return any(cnt >= 2 for cnt in groups.values()), None

def _number_three_same_same_color(hand):
    groups = Counter((d.color, d.value) for d in hand)
    return any(cnt >= 3 for cnt in groups.values()), None

def _number_three_straight_three_colors(hand):
    for combo in combinations(hand, 3):
        values = sorted(d.value for d in combo)
        if values[1] == values[0] + 1 and values[2] == values[1] + 1:
            if len(set(d.color for d in combo)) == 3:
                return True, None
    return False, None

def _number_two_three_of_a_kind_diff_colors(hand):
    groups = Counter((d.color, d.value) for d in hand)
    eligible = [(color, val) for (color, val), cnt in groups.items() if cnt >= 3]
    for i in range(len(eligible)):
        for j in range(i + 1, len(eligible)):
            if eligible[i][0] != eligible[j][0]:
                return True, None
    return False, None


# ─────────────────────────────────────────────────────────────────────────────
# Registry and loader
# ─────────────────────────────────────────────────────────────────────────────

CHECK_REGISTRY = {
    # color
    "two_color_pairs":              _two_color_pairs,
    "color_two_same":               _color_two_same,
    "color_three_same":             _color_three_same,
    "color_four_same":              _color_four_same,
    "color_six_same":               _color_six_same,
    "color_two_three_same":         _color_two_three_same,
    "color_three_unique":           _color_three_unique,
    "color_four_unique":            _color_four_unique,
    "color_five_unique":            _color_five_unique,
    "color_six_unique":             _color_six_unique,
    "color_only_red_yellow":        _color_only_red_yellow,
    "color_only_blue_orange":       _color_only_blue_orange,
    "color_only_purple_green":      _color_only_purple_green,
    "color_two_colors_five_plus":   _color_two_colors_five_plus,
    # number
    "two_number_pairs":                       _two_number_pairs,
    "number_two_same":                        _number_two_same,
    "number_three_same":                      _number_three_same,
    "number_four_same":                       _number_four_same,
    "number_five_same":                       _number_five_same,
    "number_six_same":                        _number_six_same,
    "number_two_straight":                    _number_two_straight,
    "number_three_straight":                  _number_three_straight,
    "number_four_straight":                   _number_four_straight,
    "number_five_straight":                   _number_five_straight,
    "number_six_straight":                    _number_six_straight,
    "number_four_straight_no_6":              _number_four_straight_no_6,
    "number_sum_without_1_ge11":              _number_sum_without_1_ge11,
    "number_sum_without_2_ge12":              _number_sum_without_2_ge12,
    "number_sum_without_34_ge17":             _number_sum_without_34_ge17,
    "number_sum_without_46_ge14":             _number_sum_without_46_ge14,
    "number_sum_without_4_ge20":              _number_sum_without_4_ge20,
    "number_sum_without_5_ge23":              _number_sum_without_5_ge23,
    "number_sum_without_6_ge29":              _number_sum_without_6_ge29,
    "number_sum_with_5_ge15":                 _number_sum_with_5_ge15,
    "number_sum_ge18":                        _number_sum_ge18,
    "number_sum_ge36":                        _number_sum_ge36,
    "number_exact_25":                        _number_exact_25,
    "number_odd_even_even":                   _number_odd_even_even,
    "number_even_odd_odd_odd":                _number_even_odd_odd_odd,
    "number_full_house":                      _number_full_house,
    "number_four_of_a_kind_plus_pair":        _number_four_of_a_kind_plus_pair,
    "number_three_straight_two_doubles":      _number_three_straight_two_doubles,
    "number_two_same_same_color":             _number_two_same_same_color,
    "number_three_same_same_color":           _number_three_same_same_color,
    "number_three_straight_three_colors":     _number_three_straight_three_colors,
    "number_two_three_of_a_kind_diff_colors": _number_two_three_of_a_kind_diff_colors,
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
