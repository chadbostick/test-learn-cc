"""
Automated simulator — drives RoundState without human input.
Makes smart, greedy decisions to complete each goal.
"""

import os
import random
import time
from collections import Counter
from itertools import combinations

from src.engine import RoundState
from src.goals import load_goals
from src.game import show_hand, rule, c, BOLD, DIM, RESET

DELAY = 0.4  # seconds between actions (set to 0 for instant)


# ─────────────────────────────────────────────────────────────────────────────
# Strategy helpers
# ─────────────────────────────────────────────────────────────────────────────

def _best_straight_lock(hand, exclude=None):
    """Indices forming the longest existing straight run (one die per value)."""
    exclude = exclude or set()
    val_to_idx = {}
    for i, d in enumerate(hand):
        if d.value not in exclude and d.value not in val_to_idx:
            val_to_idx[d.value] = i
    best = []
    for start in range(1, 7):
        run, v = [], start
        while v in val_to_idx:
            run.append(val_to_idx[v]); v += 1
        if len(run) > len(best):
            best = run
    return best


def _unique_val_lock(hand):
    """One die per distinct value — maximises straight coverage."""
    seen, result = set(), []
    for i, d in enumerate(hand):
        if d.value not in seen:
            seen.add(d.value); result.append(i)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Color strategy  →  which indices to lock in draw phase
# ─────────────────────────────────────────────────────────────────────────────

def _decide_color_locks(state):
    hand = state.hand
    name = state.goal.color_check.__name__

    if name == "_two_color_pairs":
        counts = Counter(d.color for d in hand)
        top2 = [col for col, _ in counts.most_common(2)]
        kept = {col: 0 for col in top2}
        indices = []
        for i, d in enumerate(hand):
            if d.color in kept and kept[d.color] < 2:
                indices.append(i); kept[d.color] += 1
        return indices

    if name in ("_color_two_same", "_color_three_same",
                "_color_four_same", "_color_six_same"):
        limit = {"_color_two_same": 2, "_color_three_same": 3,
                 "_color_four_same": 4, "_color_six_same": 6}[name]
        counts = Counter(d.color for d in hand)
        best = max(counts, key=counts.get)
        return [i for i, d in enumerate(hand) if d.color == best][:limit]

    if name == "_color_two_three_same":
        counts = Counter(d.color for d in hand)
        top2 = [col for col, _ in counts.most_common(2)]
        kept = {col: 0 for col in top2}
        indices = []
        for i, d in enumerate(hand):
            if d.color in kept and kept[d.color] < 3:
                indices.append(i); kept[d.color] += 1
        return indices

    if name in ("_color_three_unique", "_color_four_unique",
                "_color_five_unique", "_color_six_unique"):
        limit = {"_color_three_unique": 3, "_color_four_unique": 4,
                 "_color_five_unique": 5, "_color_six_unique": 6}[name]
        seen, indices = set(), []
        for i, d in enumerate(hand):
            if d.color not in seen:
                seen.add(d.color); indices.append(i)
                if len(seen) >= limit:
                    break
        return indices

    if name == "_color_only_red_yellow":
        return [i for i, d in enumerate(hand) if d.color in ("Red", "Yellow")]
    if name == "_color_only_blue_orange":
        return [i for i, d in enumerate(hand) if d.color in ("Blue", "Orange")]
    if name == "_color_only_purple_green":
        return [i for i, d in enumerate(hand) if d.color in ("Purple", "Green")]

    if name == "_color_two_colors_five_plus":
        counts = Counter(d.color for d in hand)
        top2 = {col for col, _ in counts.most_common(2)}
        return [i for i, d in enumerate(hand) if d.color in top2]

    return []


# ─────────────────────────────────────────────────────────────────────────────
# Number strategy  →  which indices to lock in roll phase
# ─────────────────────────────────────────────────────────────────────────────

def _decide_number_locks(state):
    hand = state.hand
    name = state.goal.number_check.__name__

    # Already passing — lock everything
    if state.evaluate_number()[0]:
        return list(range(len(hand)))

    if name == "_two_number_pairs":
        groups = Counter((d.color, d.value) for d in hand)
        pairs = [(col, val) for (col, val), cnt in groups.items() if cnt >= 2]
        for i in range(len(pairs)):
            for j in range(i + 1, len(pairs)):
                c1, v1 = pairs[i]; c2, v2 = pairs[j]
                if c1 != c2 and v1 != v2:
                    return [idx for idx, d in enumerate(hand)
                            if (d.color == c1 and d.value == v1) or
                               (d.color == c2 and d.value == v2)]
        if pairs:
            c1, v1 = pairs[0]
            return [idx for idx, d in enumerate(hand) if d.color == c1 and d.value == v1]
        return []

    if name in ("_number_two_same", "_number_three_same", "_number_four_same",
                "_number_five_same", "_number_six_same"):
        limit = {"_number_two_same": 2, "_number_three_same": 3,
                 "_number_four_same": 4, "_number_five_same": 5,
                 "_number_six_same": 6}[name]
        counts = Counter(d.value for d in hand)
        best = max(counts, key=counts.get)
        return [i for i, d in enumerate(hand) if d.value == best][:limit]

    if name == "_number_two_straight":   return _best_straight_lock(hand)[:2]
    if name == "_number_three_straight": return _best_straight_lock(hand)[:3]
    if name == "_number_four_straight":  return _best_straight_lock(hand)[:4]
    if name == "_number_five_straight":  return _best_straight_lock(hand)[:5]
    if name == "_number_six_straight":   return _unique_val_lock(hand)
    if name == "_number_four_straight_no_6":
        return _best_straight_lock(hand, exclude={6})[:4]

    if name == "_number_sum_without_1_ge11":
        return [i for i, d in enumerate(hand) if d.value != 1]
    if name == "_number_sum_without_2_ge12":
        return [i for i, d in enumerate(hand) if d.value != 2]
    if name == "_number_sum_without_34_ge17":
        return [i for i, d in enumerate(hand) if d.value not in (3, 4)]
    if name == "_number_sum_without_46_ge14":
        return [i for i, d in enumerate(hand) if d.value not in (4, 6)]
    if name == "_number_sum_without_4_ge20":
        return [i for i, d in enumerate(hand) if d.value != 4]
    if name == "_number_sum_without_5_ge23":
        return [i for i, d in enumerate(hand) if d.value != 5]
    if name == "_number_sum_without_6_ge29":
        return [i for i, d in enumerate(hand) if d.value != 6]

    if name == "_number_sum_with_5_ge15":
        fives = [i for i, d in enumerate(hand) if d.value == 5]
        others = sorted([i for i, d in enumerate(hand) if d.value != 5],
                        key=lambda i: -hand[i].value)
        return (fives + others)[:5]

    if name == "_number_sum_ge18":
        return [i for i, d in enumerate(hand) if d.value >= 3]

    if name == "_number_sum_ge36":
        return [i for i, d in enumerate(hand) if d.value == 6]

    if name == "_number_exact_25":
        current = sum(d.value for d in hand)
        if current < 25:
            return [i for i, d in enumerate(hand) if d.value >= 4]
        else:
            return [i for i, d in enumerate(hand) if d.value <= 4]

    if name == "_number_odd_even_even":
        odds  = [i for i, d in enumerate(hand) if d.value % 2 == 1]
        evens = sorted([i for i, d in enumerate(hand) if d.value % 2 == 0],
                       key=lambda i: -hand[i].value)
        return odds[:1] + evens[:2]

    if name == "_number_even_odd_odd_odd":
        evens = [i for i, d in enumerate(hand) if d.value % 2 == 0]
        odds  = sorted([i for i, d in enumerate(hand) if d.value % 2 == 1],
                       key=lambda i: -hand[i].value)
        return evens[:1] + odds[:3]

    if name == "_number_full_house":
        counts = Counter(d.value for d in hand)
        sv = sorted(counts, key=lambda v: -counts[v])
        locked = [i for i, d in enumerate(hand) if d.value == sv[0]][:3]
        if len(sv) > 1:
            locked += [i for i, d in enumerate(hand) if d.value == sv[1]][:2]
        return locked

    if name == "_number_four_of_a_kind_plus_pair":
        counts = Counter(d.value for d in hand)
        sv = sorted(counts, key=lambda v: -counts[v])
        locked = [i for i, d in enumerate(hand) if d.value == sv[0]][:4]
        if len(sv) > 1:
            locked += [i for i, d in enumerate(hand) if d.value == sv[1]][:2]
        return locked

    if name == "_number_three_straight_two_doubles":
        counts = Counter(d.value for d in hand)
        values = set(d.value for d in hand)
        best = []
        for start in range(1, 5):
            a, b, cc = start, start + 1, start + 2
            if a in values and b in values and cc in values:
                combo = ([i for i, d in enumerate(hand) if d.value == a][:2] +
                         [i for i, d in enumerate(hand) if d.value == b][:1] +
                         [i for i, d in enumerate(hand) if d.value == cc][:2])
                if len(combo) > len(best):
                    best = combo
        if not best:
            for start in range(1, 6):
                if start in values and start + 1 in values:
                    best = ([i for i, d in enumerate(hand) if d.value == start][:2] +
                            [i for i, d in enumerate(hand) if d.value == start + 1][:2])
                    break
        return best

    if name == "_number_two_same_same_color":
        groups = Counter((d.color, d.value) for d in hand)
        key = max(groups, key=groups.get)
        return [i for i, d in enumerate(hand) if d.color == key[0] and d.value == key[1]][:2]

    if name == "_number_three_same_same_color":
        groups = Counter((d.color, d.value) for d in hand)
        key = max(groups, key=groups.get)
        return [i for i, d in enumerate(hand) if d.color == key[0] and d.value == key[1]][:3]

    if name == "_number_three_straight_three_colors":
        for combo in combinations(range(len(hand)), 3):
            dice = [hand[i] for i in combo]
            vals = sorted(d.value for d in dice)
            if vals[1] == vals[0] + 1 and vals[2] == vals[1] + 1:
                if len(set(d.color for d in dice)) == 3:
                    return list(combo)
        best = []
        for i, j in combinations(range(len(hand)), 2):
            di, dj = hand[i], hand[j]
            if abs(di.value - dj.value) == 1 and di.color != dj.color:
                best = [i, j]; break
        return best

    if name == "_number_two_three_of_a_kind_diff_colors":
        groups = Counter((d.color, d.value) for d in hand)
        eligible = sorted(groups.items(), key=lambda x: -x[1])
        locked, colors_used = [], set()
        for (color, val), _ in eligible:
            if color not in colors_used:
                colors_used.add(color)
                locked += [i for i, d in enumerate(hand)
                           if d.color == color and d.value == val][:3]
            if len(colors_used) >= 2:
                break
        return locked

    return []


# ─────────────────────────────────────────────────────────────────────────────
# Phase runners
# ─────────────────────────────────────────────────────────────────────────────

def _apply_locks(state, indices):
    state.reset_locks()
    if indices:
        state.toggle_lock(indices)


def simulate_draw_phase(state):
    rule("DRAW PHASE")
    state.draw_initial()

    print("\n  Initial draw:")
    show_hand(state.hand, "draw", state.locked_indices())
    time.sleep(DELAY)

    while True:
        met = state.evaluate_color()
        print(f"  Color condition : {'✓ MET' if met else '✗ not met'}")
        print(f"  Redraws left    : {state.redraws_left}")

        if met or state.redraws_left == 0:
            break

        indices = _decide_color_locks(state)
        _apply_locks(state, indices)
        kept = [state.hand[i].color for i in sorted(indices)]
        print(f"  [SIM] Locking {indices}  →  keeping {kept}")
        show_hand(state.hand, "draw", state.locked_indices())
        time.sleep(DELAY)

        state.execute_redraw()
        print("\n  After redraw:")
        show_hand(state.hand, "draw", state.locked_indices())
        time.sleep(DELAY)

    return state.evaluate_color()


def simulate_roll_phase(state):
    rule("ROLL PHASE")
    state.roll_all()

    print("\n  Initial roll:")
    show_hand(state.hand, "roll", state.locked_indices())
    time.sleep(DELAY)

    while True:
        success, info = state.evaluate_number()
        print(f"  Number condition: {'✓ MET' if success else '✗ not met'}")
        if success and info:
            p1, p2 = info
            print(f"  Pairs: {c(p1[0], p1[0])}:{p1[1]}  and  {c(p2[0], p2[0])}:{p2[1]}")
        print(f"  Rerolls left    : {state.rerolls_left}")

        if success or state.rerolls_left == 0:
            break

        indices = _decide_number_locks(state)
        _apply_locks(state, indices)
        kept = [(state.hand[i].color, state.hand[i].value) for i in sorted(indices)]
        print(f"  [SIM] Locking {indices}  →  keeping {kept}")
        show_hand(state.hand, "roll", state.locked_indices())
        time.sleep(DELAY)

        state.execute_reroll()
        print("\n  After reroll:")
        show_hand(state.hand, "roll", state.locked_indices())
        time.sleep(DELAY)

    return state.evaluate_number()


# ─────────────────────────────────────────────────────────────────────────────
# Round and game runners
# ─────────────────────────────────────────────────────────────────────────────

def simulate_round(round_num, total_rounds):
    goal = random.choice(load_goals())
    state = RoundState(goal)

    rule(f"ROUND {round_num} of {total_rounds}")
    print(f"""
  Goal   : {goal.name}
  Points : {goal.points}

  {goal.description}

  {DIM}Draw phase : up to 3 redraws
  Roll phase : up to 3 rerolls{RESET}
""")
    time.sleep(DELAY * 2)

    # --- Draw Phase ---
    if goal.color_check:
        color_met = simulate_draw_phase(state)

        rule("DRAW PHASE RESULT")
        if color_met:
            print(f"\n  ✓ PASSED — color condition met\n")
        else:
            print(f"\n  ✗ FAILED — color condition not met\n")
            rule("ROUND RESULT")
            print(f"\n  {BOLD}*** FAILURE ***{RESET}  (+0 pts)\n")
            return 0
    else:
        state.draw_initial()

    # --- Roll Phase ---
    if goal.number_check:
        success, info = simulate_roll_phase(state)

        rule("ROLL PHASE RESULT")
        if success:
            print(f"\n  ✓ PASSED — number condition met\n")
        else:
            print(f"\n  ✗ FAILED — number condition not met\n")
    else:
        success, info = True, None

    # --- Round Result ---
    rule("ROUND RESULT")
    if success:
        print(f"\n  {BOLD}*** SUCCESS! ***{RESET}  +{goal.points} pts")
        if info:
            p1, p2 = info
            print(f"\n  Winning pairs:")
            print(f"    {c(p1[0], p1[0])}  ×2  →  {p1[1]}")
            print(f"    {c(p2[0], p2[0])}  ×2  →  {p2[1]}")
        print()
        return goal.points
    else:
        print(f"\n  {BOLD}*** FAILURE ***{RESET}  (+0 pts)\n")
        return 0


def simulate_game():
    os.system("clear")
    total_rounds = 6

    print(f"\n{BOLD}{'═' * 44}{RESET}")
    print(f"{BOLD}     CHROMATIC YAHTZEE  [SIMULATOR]{RESET}")
    print(f"{BOLD}{'═' * 44}{RESET}")
    print(f"\n  {total_rounds} rounds — automated smart play.\n")
    time.sleep(DELAY * 2)

    total_score = 0
    scores = []

    for round_num in range(1, total_rounds + 1):
        earned = simulate_round(round_num, total_rounds)
        total_score += earned
        scores.append(earned)
        print(f"  Score so far: {total_score} pts  "
              f"({' + '.join(str(s) for s in scores)})")
        if round_num < total_rounds:
            time.sleep(DELAY * 3)

    print(f"\n{BOLD}{'═' * 44}{RESET}")
    print(f"{BOLD}         FINAL SCORE: {total_score} pts{RESET}")
    print(f"{'═' * 44}\n")
