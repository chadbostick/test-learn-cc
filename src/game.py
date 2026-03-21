from src.dice import DiceBag
from src.goals import GOALS

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


def show_hand(hand, phase="draw", locked=None):
    if locked is None:
        locked = set()
    locked_indices = {i for i, d in enumerate(hand) if id(d) in locked}
    print()
    for i, die in enumerate(hand):
        label = c(f"{die.color:<8}", die.color)
        lock = " 🔒" if i in locked_indices else "   "
        if phase == "roll":
            print(f"  [{i}]  {label}  →  {die.value}{lock}")
        else:
            print(f"  [{i}]  {label}{lock}")
    print()


def sort_hand(hand):
    hand.sort(key=lambda d: d.color)


def phase_input(hand, phase, locked):
    """Input loop for toggling locks. Returns 'execute' or 'done'."""
    print(f"  {DIM}Lock/unlock: type indices (e.g. 0,2)  |  Execute: Enter  |  End phase: q{RESET}")
    while True:
        raw = input("  > ").strip().lower()

        if not raw:
            return "execute"

        if raw == "q":
            return "done"

        try:
            indices = list({int(x) for x in raw.split(",")})
            if not all(0 <= i <= 5 for i in indices):
                print("  Indices must be 0–5.")
                continue
            for i in indices:
                die_id = id(hand[i])
                if die_id in locked:
                    locked.remove(die_id)
                else:
                    locked.add(die_id)
            show_hand(hand, phase, locked)
        except ValueError:
            print("  Type indices (e.g. 0,2), Enter to execute, or q to end phase.")


def draw_phase(bag, goal):
    rule("DRAW PHASE")
    hand = bag.draw(6)
    sort_hand(hand)
    redraws_left = 3
    locked = set()

    print("\n  Initial draw:")
    show_hand(hand, "draw", locked)

    while True:
        met = goal.color_check(hand)
        print(f"  Color condition : {'✓ MET' if met else '✗ not met'}")
        print(f"  Redraws left    : {redraws_left}")

        if redraws_left == 0:
            break

        action = phase_input(hand, "draw", locked)

        if action == "done":
            break

        unlocked = [d for d in hand if id(d) not in locked]
        if unlocked:
            bag.return_dice(unlocked)
            new_dice = bag.draw(len(unlocked))
            for i, die in enumerate(hand):
                if id(die) not in locked:
                    hand[i] = new_dice.pop(0)
        redraws_left -= 1
        sort_hand(hand)

        print("\n  After redraw:")
        show_hand(hand, "draw", locked)

    return hand, goal.color_check(hand)


def roll_phase(hand, goal):
    rule("ROLL PHASE")
    for die in hand:
        die.roll()
    rerolls_left = 3
    locked = set()

    print("\n  Initial roll:")
    show_hand(hand, "roll", locked)

    while True:
        success, info = goal.number_check(hand)
        print(f"  Number condition: {'✓ MET' if success else '✗ not met'}")
        if success and info:
            p1, p2 = info
            print(f"  Pairs: {c(p1[0], p1[0])}:{p1[1]}  and  {c(p2[0], p2[0])}:{p2[1]}")
        print(f"  Rerolls left    : {rerolls_left}")

        if rerolls_left == 0:
            break

        action = phase_input(hand, "roll", locked)

        if action == "done":
            break

        for die in hand:
            if id(die) not in locked:
                die.roll()
        rerolls_left -= 1

        print("\n  After reroll:")
        show_hand(hand, "roll", locked)

    return goal.number_check(hand)


def run_game():
    goal = GOALS[0]

    print(f"\n{BOLD}{'═' * 44}{RESET}")
    print(f"{BOLD}         CHROMATIC YAHTZEE{RESET}")
    print(f"{BOLD}{'═' * 44}{RESET}")
    print(f"""
  Goal   : {goal.name}
  Points : {goal.points}

  {goal.description}

  {DIM}Draw phase : up to 3 redraws
  Roll phase : up to 3 rerolls{RESET}
""")
    input("  Press Enter to begin...\n")

    bag = DiceBag()

    # --- Draw Phase (if goal has a color component) ---
    if goal.color_check:
        hand, color_met = draw_phase(bag, goal)

        rule("DRAW PHASE RESULT")
        if color_met:
            print(f"\n  ✓ PASSED — color condition met\n")
        else:
            print(f"\n  ✗ FAILED — color condition not met\n")
            rule("FINAL RESULT")
            print(f"\n  {BOLD}*** FAILURE ***{RESET}  ({goal.points} pts lost)")
            print("  Draw phase failed. Round over.\n")
            return
    else:
        hand = bag.draw(6)
        sort_hand(hand)

    # --- Roll Phase (if goal has a number component) ---
    if goal.number_check:
        success, info = roll_phase(hand, goal)

        rule("ROLL PHASE RESULT")
        if success:
            print(f"\n  ✓ PASSED — number condition met\n")
        else:
            print(f"\n  ✗ FAILED — number condition not met\n")
    else:
        success, info = True, None

    # --- Final Result ---
    rule("FINAL RESULT")
    if success:
        print(f"\n  {BOLD}*** SUCCESS! ***{RESET}  +{goal.points} pts")
        if info:
            p1, p2 = info
            print(f"\n  Winning pairs:")
            print(f"    {c(p1[0], p1[0])}  ×2  →  {p1[1]}")
            print(f"    {c(p2[0], p2[0])}  ×2  →  {p2[1]}")
    else:
        print(f"\n  {BOLD}*** FAILURE ***{RESET}  ({goal.points} pts lost)")
        print("  Could not form two valid pairs.")
    print(f"\n{'═' * 44}\n")
