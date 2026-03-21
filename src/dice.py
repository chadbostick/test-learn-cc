import random
from dataclasses import dataclass
from typing import Optional

COLORS = ["Red", "Blue", "Green", "Yellow", "Purple", "Orange"]


@dataclass
class Die:
    color: str
    value: Optional[int] = None

    def roll(self):
        self.value = random.randint(1, 6)


class DiceBag:
    def __init__(self):
        self.dice = [Die(color=c) for c in COLORS for _ in range(6)]
        random.shuffle(self.dice)

    def draw(self, n: int) -> list:
        drawn, self.dice = self.dice[:n], self.dice[n:]
        return drawn

    def return_dice(self, dice: list):
        self.dice.extend(dice)
        random.shuffle(self.dice)

    def __len__(self):
        return len(self.dice)
