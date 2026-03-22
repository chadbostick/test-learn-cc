# Product Requirements Document (PRD)

## Chromatic Yahtzee – Core MVP

---

## 1. Objective

Build a minimal, playable command-line version of **Chromatic Yahtzee** where the player completes **6 rounds**, each with a randomly assigned goal. Points are earned per round and summed into a final score.

The game uses **step-based evaluation**, where progress is validated after every draw and roll action.

---

## 2. Core Game Concept

A game consists of **6 rounds**. Each round:

1. A goal is randomly selected from the goal library
2. The player attempts to achieve it using 6 dice across two phases
3. Points are awarded on success; no points are deducted on failure

Each round is split into two distinct phases:

1. **Draw Phase (Color Validation)** — only if the goal has a color component
2. **Roll Phase (Number Validation)** — only if the goal has a number component

Failure in the Draw Phase ends the round immediately with no roll phase.

---

## 3. Components

### 3.1 Dice Bag

* Total dice: **36**
* Structure: 6 colors × 6 dice per color
* Each die:
  * Has a **color**
  * Rolls a value from **1–6** (null before rolling)

### 3.2 Colors

* Red
* Blue
* Green
* Yellow
* Purple
* Orange

---

## 4. Goal System

### 4.1 Goal Structure

Each goal defines:

| Field | Description |
|---|---|
| `name` | Display name |
| `description` | Human-readable objective |
| `points` | Stars awarded on success (1–36) |
| `color_check` | Function name for draw phase evaluation, or null |
| `number_check` | Function name for roll phase evaluation, or null |

Goals with only a `color_check` end after the draw phase.
Goals with only a `number_check` skip the draw phase.
Goals with both require passing the draw phase before entering the roll phase.

### 4.2 Goal Files

* **`src/goals.json`** — goal definitions (name, description, points, check function names)
* **`src/goals.py`** — check function implementations + `CHECK_REGISTRY` + `load_goals()` loader

Adding a new goal requires only editing `goals.json` and referencing an existing check function name. New check types require a new function in `goals.py` registered in `CHECK_REGISTRY`.

### 4.3 Goal Selection

At the start of each round, one goal is selected at random from the full goal library.

### 4.4 Point Tiers

| Stars | Example Goals |
|---|---|
| 1 | Two of the Same Color, Two Adjacent Numbers |
| 2 | Two Pairs of Colors, Three Straight Numbers |
| 3 | Three of the Same Color, Four Different Colors |
| 4 | Full House, Five Straight Numbers |
| 5 | Six Different Colors, Exact Sum 25 |
| 36 | Six Straight on Six Colors, Six of the Same Number |

---

## 5. Round Flow

### 5.1 Draw Phase (Color Phase)

> Skipped if goal has no `color_check`.

#### Initial Draw

* Player draws **6 dice randomly** from the bag
* Hand is sorted by color so matching colors are grouped together

#### Lock / Redraw Rules

* Up to **3 redraws allowed**
* Player **locks** dice they want to keep
* On execute (Enter): all **unlocked** dice are returned to the bag and replaced with new draws
* Locked dice remain in place; newly drawn dice are unlocked by default
* Hand is re-sorted by color after every redraw
* Player may end the phase early at any time by typing `q`

#### Outcomes

* **Passed** — color condition met; player proceeds to Roll Phase
* **Failed** — all 3 redraws used without meeting condition; round ends, +0 pts

---

### 5.2 Roll Phase (Number Phase)

> Skipped if goal has no `number_check`.
> Only begins if Draw Phase passed (when applicable).

#### Initial Roll

* All 6 dice are rolled; all locks are **reset** (everything starts unlocked)

#### Lock / Reroll Rules

* Up to **3 rerolls allowed**
* Player **locks** dice they want to keep
* On execute (Enter): all **unlocked** dice are rerolled (values change, colors stay fixed)
* Player may end the phase early at any time by typing `q`

#### Outcomes

* **Success** — number condition met; player earns goal's point value
* **Failed** — all 3 rerolls used without meeting condition; round ends, +0 pts

---

## 6. Scoring

* **Success**: player earns the goal's point value for that round
* **Failure**: player earns 0 points — no deductions
* **Final score**: sum of points earned across all 6 rounds
* Running score is displayed after each round as a breakdown (e.g. `2 + 0 + 4 + ...`)

---

## 7. Data Model

### 7.1 Die

```
Die:
  color: string
  value: integer (1–6, or null before rolling)
```

### 7.2 Dice Bag

```
DiceBag:
  dice: list of Die (36 total at start)
```

### 7.3 Hand

```
Hand:
  dice: list of Die (exactly 6)
  sorted by color after every draw/redraw
```

### 7.4 Goal

```
Goal:
  name: string
  description: string
  points: integer
  color_check: callable | None
  number_check: callable | None
```

---

## 8. Functional Requirements

### 8.1 Bag Initialization

* Create 36 dice: 6 per color
* Dice have no value until rolled

### 8.2 Draw Logic

* Randomly draw N dice from bag (removed from bag)
* Returned dice go back into bag and bag is reshuffled

### 8.3 Lock Logic

* Player toggles locks by typing die indices (e.g. `0,2`)
* Toggling an unlocked die locks it; toggling a locked die unlocks it
* Updated hand is displayed immediately after each toggle
* Locks persist between actions within a phase
* All locks reset when transitioning from Draw Phase to Roll Phase

### 8.4 Roll Logic

* Assign random value (1–6) to each die on initial roll

### 8.5 Reroll Logic

* Re-assign random value (1–6) to all **unlocked** dice only
* Colors are never changed

### 8.6 Evaluation Logic

Each goal's check functions receive the full hand and return:
* Color check: `bool`
* Number check: `(bool, info)` where info may contain display metadata (e.g. winning pairs)

---

## 9. CLI Requirements

### 9.1 Display

Each round shows:

* Round number (e.g. ROUND 2 of 6)
* Goal name, point value, and description
* Indexed dice list with color (draw phase) or color + value (roll phase)
* Lock indicator (🔒) on locked dice
* Color / number condition status: met / not met
* Remaining redraws / rerolls
* Round result: SUCCESS (+N pts) or FAILURE (+0 pts)
* Running score breakdown after each round

Final screen shows the total score across all 6 rounds.

### 9.2 Input

| Input | Action |
|---|---|
| `0,2,4` | Toggle lock on dice at those indices |
| Enter (empty) | Execute redraw (Draw Phase) or reroll (Roll Phase) |
| `q` | End current phase early |

---

## 10. Constraints

* 6 rounds per game
* Single player only
* No persistence between games
* Terminal only — ANSI color output
* No AI or automation

---

## 11. Design Principles

* **Draw Phase = Resource Qualification (Colors)**
* **Roll Phase = Value Resolution (Numbers)**
* **Lock model** — players protect what they want, not discard what they don't
* **Goal-driven** — each round's objective is data-defined in `goals.json`, not hardcoded
* Failure is forgiving — no point deductions, only missed opportunities

---

## 12. Summary

Core loop (per round):

> Select Goal → Draw → Sort → Evaluate (Color) →
> Pass → Roll → Evaluate (Number) → Award Points
> Fail → +0 pts → Next Round

After 6 rounds → display final score.

Controls:

> Type indices to lock/unlock → Enter to execute → q to end phase early
