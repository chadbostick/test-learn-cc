import os
import random
from src.goals import load_goals
from src.engine import RoundState

# ANSI formatting
COLOR_CODES = {
    "Red":    "\033[91m",
    "Blue":   "\033[94m",
    "Green":  "\033[92m",
    "Yellow": "\033[93m",
    "Purple": "\033[95m",
    "Orange": "\033[38;5;208m",
}
RESET = "\033[0m"
BOLD  = "\033[1m"
DIM   = "\033[2m"


def c(text, color):
    return f"{COLOR_CODES.get(color, '')}{BOLD}{text}{RESET}"


def rule(title=""):
    if title:
        print(f"\n{'─' * 44}")
        print(f"  {BOLD}{title}{RESET}")
        print(f"{'─' * 44}")
    else:
        print(f"{'─' * 44}")


def show_hand(hand, phase="draw", locked_indices=None):
    if locked_indices is None:
        locked_indices = set()
    print()
    for i, die in enumerate(hand):
        label = c(f"{die.color:<8}", die.color)
        lock = " 🔒" if i in locked_indices else "   "
        if phase == "roll":
            print(f"  [{i}]  {label}  →  {die.value}{lock}")
        else:
            print(f"  [{i}]  {label}{lock}")
    print()


def phase_input():
    """Read one line of input. Returns ('execute', []), ('done', []), or ('toggle', [indices])."""
    print(f"  {DIM}Lock/unlock: type indices (e.g. 0,2)  |  Execute: Enter  |  End phase: q{RESET}")
    while True:
        raw = input("  > ").strip().lower()
        if not raw:
            return "execute", []
        if raw == "q":
            return "done", []
        try:
            indices = list({int(x) for x in raw.split(",")})
            if not all(0 <= i <= 5 for i in indices):
                print("  Indices must be 0–5.")
                continue
            return "toggle", indices
        except ValueError:
            print("  Type indices (e.g. 0,2), Enter to execute, or q to end phase.")


def draw_phase(state):
    rule("DRAW PHASE")
    state.draw_initial()

    print("\n  Initial draw:")
    show_hand(state.hand, "draw", state.locked_indices())

    while True:
        met = state.evaluate_color()
        print(f"  Color condition : {'✓ MET' if met else '✗ not met'}")
        print(f"  Redraws left    : {state.redraws_left}")

        if state.redraws_left == 0:
            break

        action, indices = phase_input()

        if action == "done":
            break
        if action == "toggle":
            state.toggle_lock(indices)
            show_hand(state.hand, "draw", state.locked_indices())
            continue

        # execute redraw
        state.execute_redraw()
        print("\n  After redraw:")
        show_hand(state.hand, "draw", state.locked_indices())

    return state.evaluate_color()


def roll_phase(state):
    rule("ROLL PHASE")
    state.roll_all()

    print("\n  Initial roll:")
    show_hand(state.hand, "roll", state.locked_indices())

    while True:
        success, info = state.evaluate_number()
        print(f"  Number condition: {'✓ MET' if success else '✗ not met'}")
        if success and info:
            p1, p2 = info
            print(f"  Pairs: {c(p1[0], p1[0])}:{p1[1]}  and  {c(p2[0], p2[0])}:{p2[1]}")
        print(f"  Rerolls left    : {state.rerolls_left}")

        if state.rerolls_left == 0:
            break

        action, indices = phase_input()

        if action == "done":
            break
        if action == "toggle":
            state.toggle_lock(indices)
            show_hand(state.hand, "roll", state.locked_indices())
            continue

        # execute reroll
        state.execute_reroll()
        print("\n  After reroll:")
        show_hand(state.hand, "roll", state.locked_indices())

    return state.evaluate_number()


def play_round(round_num, total_rounds):
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
    input("  Press Enter to begin...\n")

    # --- Draw Phase ---
    if goal.color_check:
        color_met = draw_phase(state)

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
        success, info = roll_phase(state)

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


def run_game():
    os.system("clear")
    total_rounds = 6

    print(f"\n{BOLD}{'═' * 44}{RESET}")
    print(f"{BOLD}         CHROMATIC YAHTZEE{RESET}")
    print(f"{BOLD}{'═' * 44}{RESET}")
    print(f"\n  {total_rounds} rounds — a new goal each round.\n")
    input("  Press Enter to begin...\n")

    total_score = 0
    scores = []

    for round_num in range(1, total_rounds + 1):
        earned = play_round(round_num, total_rounds)
        total_score += earned
        scores.append(earned)
        print(f"  Score so far: {total_score} pts  "
              f"({' + '.join(str(s) for s in scores)})")
        if round_num < total_rounds:
            input(f"\n  Press Enter for round {round_num + 1}...\n")

    print(f"\n{BOLD}{'═' * 44}{RESET}")
    print(f"{BOLD}         FINAL SCORE: {total_score} pts{RESET}")
    print(f"{'═' * 44}\n")
