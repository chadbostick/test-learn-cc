from collections import Counter
from src.dice import DiceBag

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


def show_hand(hand, phase="draw"):
    print()
    for i, die in enumerate(hand):
        label = c(f"{die.color:<8}", die.color)
        if phase == "roll":
            print(f"  [{i}]  {label}  →  {die.value}")
        else:
            print(f"  [{i}]  {label}")
    print()


def eval_colors(hand):
    counts = Counter(d.color for d in hand)
    qualifying = [color for color, n in counts.items() if n >= 2]
    return len(qualifying) >= 2


def eval_numbers(hand):
    groups = Counter((d.color, d.value) for d in hand)
    pairs = [(color, val) for (color, val), cnt in groups.items() if cnt >= 2]
    for i in range(len(pairs)):
        for j in range(i + 1, len(pairs)):
            c1, v1 = pairs[i]
            c2, v2 = pairs[j]
            if c1 != c2 and v1 != v2:
                return True, pairs[i], pairs[j]
    return False, None, None


def get_indices(prompt, max_idx):
    while True:
        raw = input(prompt).strip()
        if not raw:
            return []
        try:
            indices = list({int(x) for x in raw.split(",")})
            if all(0 <= i <= max_idx for i in indices):
                return indices
            print(f"  Indices must be 0–{max_idx}. Try again.")
        except ValueError:
            print("  Enter comma-separated numbers (e.g. 0,2,4) or press Enter to proceed.")


def sort_hand(hand):
    hand.sort(key=lambda d: d.color)


def draw_phase(bag):
    rule("DRAW PHASE")
    hand = bag.draw(6)
    sort_hand(hand)
    redraws_left = 3

    print("\n  Initial draw:")
    show_hand(hand, "draw")

    while True:
        met = eval_colors(hand)
        print(f"  Color condition : {'✓ MET' if met else '✗ not met'}")
        print(f"  Redraws left    : {redraws_left}")

        if redraws_left == 0:
            break

        indices = get_indices(
            "  Return dice by index (e.g. 0,3) or Enter to proceed: ", 5
        )

        if not indices:
            break

        to_return = [hand[i] for i in indices]
        bag.return_dice(to_return)
        new_dice = bag.draw(len(to_return))
        for slot, new_die in zip(sorted(indices), new_dice):
            hand[slot] = new_die
        redraws_left -= 1
        sort_hand(hand)

        print("\n  After redraw:")
        show_hand(hand, "draw")

    return hand, eval_colors(hand)


def roll_phase(hand):
    rule("ROLL PHASE")
    for die in hand:
        die.roll()
    rerolls_left = 3

    print("\n  Initial roll:")
    show_hand(hand, "roll")

    while True:
        success, p1, p2 = eval_numbers(hand)
        print(f"  Number condition: {'✓ MET' if success else '✗ not met'}")
        if success:
            print(f"  Pairs: {c(p1[0], p1[0])}:{p1[1]}  and  {c(p2[0], p2[0])}:{p2[1]}")
        print(f"  Rerolls left    : {rerolls_left}")

        if rerolls_left == 0:
            break

        indices = get_indices(
            "  Select dice to reroll (e.g. 1,4) or Enter to proceed: ", 5
        )

        if not indices:
            break

        for i in indices:
            hand[i].roll()
        rerolls_left -= 1

        print("\n  After reroll:")
        show_hand(hand, "roll")

    return eval_numbers(hand)


def run_game():
    print(f"\n{BOLD}{'═' * 44}{RESET}")
    print(f"{BOLD}         CHROMATIC YAHTZEE{RESET}")
    print(f"{BOLD}{'═' * 44}{RESET}")
    print(f"""
  Goal: Draw 6 colored dice, then roll them.
  Form two pairs where each pair is:
    • same color  +  same number
  The two pairs must use different colors
  and different numbers.

  {DIM}Draw phase : up to 3 redraws
  Roll phase : up to 3 rerolls{RESET}
""")
    input("  Press Enter to begin...\n")

    bag = DiceBag()

    # --- Draw Phase ---
    hand, color_met = draw_phase(bag)

    rule("DRAW PHASE RESULT")
    if color_met:
        print(f"\n  ✓ PASSED — two qualifying colors found\n")
    else:
        print(f"\n  ✗ FAILED — could not meet color condition\n")
        rule("FINAL RESULT")
        print(f"\n  {BOLD}*** FAILURE ***{RESET}")
        print("  Draw phase failed. Round over.\n")
        return

    # --- Roll Phase ---
    success, p1, p2 = roll_phase(hand)

    rule("ROLL PHASE RESULT")
    if success:
        print(f"\n  ✓ PASSED — two valid pairs found\n")
    else:
        print(f"\n  ✗ FAILED — could not form two valid pairs\n")

    # --- Final Result ---
    rule("FINAL RESULT")
    if success:
        print(f"\n  {BOLD}*** SUCCESS! ***{RESET}")
        print(f"\n  Winning pairs:")
        print(f"    {c(p1[0], p1[0])}  ×2  →  {p1[1]}")
        print(f"    {c(p2[0], p2[0])}  ×2  →  {p2[1]}")
    else:
        print(f"\n  {BOLD}*** FAILURE ***{RESET}")
        print("  Could not form two valid pairs.")
    print(f"\n{'═' * 44}\n")
