from src.dice import DiceBag


def sort_hand(hand):
    hand.sort(key=lambda d: d.color)


class RoundState:
    """
    Pure game logic for one round — no I/O.
    Driven by game.py (human CLI) or simulator.py (automated).
    """

    REDRAWS = 3
    REROLLS = 3

    def __init__(self, goal):
        self.goal = goal
        self.bag = DiceBag()
        self.hand = []
        self._locked = set()          # set of id(die)
        self.redraws_left = self.REDRAWS
        self.rerolls_left = self.REROLLS

    # ── Lock helpers ──────────────────────────────────────────────────────────

    def toggle_lock(self, indices):
        for i in indices:
            die_id = id(self.hand[i])
            if die_id in self._locked:
                self._locked.remove(die_id)
            else:
                self._locked.add(die_id)

    def locked_indices(self):
        return {i for i, d in enumerate(self.hand) if id(d) in self._locked}

    def reset_locks(self):
        self._locked = set()

    # ── Draw phase ────────────────────────────────────────────────────────────

    def draw_initial(self):
        self.hand = self.bag.draw(6)
        sort_hand(self.hand)

    def execute_redraw(self):
        unlocked = [d for d in self.hand if id(d) not in self._locked]
        if unlocked:
            self.bag.return_dice(unlocked)
            new_dice = self.bag.draw(len(unlocked))
            for i, die in enumerate(self.hand):
                if id(die) not in self._locked:
                    self.hand[i] = new_dice.pop(0)
        self.redraws_left -= 1
        sort_hand(self.hand)

    def evaluate_color(self):
        if self.goal.color_check:
            return self.goal.color_check(self.hand)
        return True

    # ── Roll phase ────────────────────────────────────────────────────────────

    def roll_all(self):
        for die in self.hand:
            die.roll()
        self.reset_locks()

    def execute_reroll(self):
        for die in self.hand:
            if id(die) not in self._locked:
                die.roll()
        self.rerolls_left -= 1

    def evaluate_number(self):
        if self.goal.number_check:
            return self.goal.number_check(self.hand)
        return True, None
