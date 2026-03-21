# Product Requirements Document (PRD)

## Chromatic Yahtzee – Core MVP

---

## 1. Objective

Build a minimal, playable command-line version of **Chromatic Yahtzee** focused on a single scoring goal:

> **Achieve Two Pairs of Numbers on Two Pairs of Colors using 6 drawn dice within limited redraws and rerolls.**

The game uses **step-based evaluation**, where progress is validated after every draw and roll action.

---

## 2. Core Game Concept

Each round is split into two distinct phases:

1. **Draw Phase (Color Validation)**
2. **Roll Phase (Number Validation)**

Each phase has its own success criteria. Failure in the Draw Phase ends the round immediately.

---

## 3. Components

### 3.1 Dice Bag

* Total dice: **36**
* Structure:
  * 6 colors × 6 dice per color
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

## 4. Round Flow

---

### 4.1 Draw Phase (Color Phase)

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

---

### 4.1.1 Draw Phase Evaluation (Color Check)

Evaluated after the initial draw and after each redraw.

#### Requirement

* At least **two distinct colors** must each appear **at least twice** in the hand

#### Outcomes

* **Passed** — color condition met; player proceeds to Roll Phase
* **Failed** — all 3 redraws used without meeting condition; round ends immediately

---

### 4.2 Roll Phase (Number Phase)

> Only begins if the Draw Phase passes.

#### Initial Roll

* All 6 dice are rolled; all locks are **reset** (everything starts unlocked)

#### Lock / Reroll Rules

* Up to **3 rerolls allowed**
* Player **locks** dice they want to keep
* On execute (Enter): all **unlocked** dice are rerolled (values change, colors stay fixed)
* Player may end the phase early at any time by typing `q`

---

### 4.2.1 Roll Phase Evaluation (Number Check)

Evaluated after the initial roll and after each reroll.

#### Requirement

* Two valid pairs where:
  * Each pair: same **color** + same **number**
  * The two pairs: different **colors** and different **numbers**

#### Outcomes

* **Success** — goal achieved; round ends
* **Failed** — all 3 rerolls used without meeting condition; round ends

---

## 5. Data Model

### 5.1 Die

```
Die:
  color: string
  value: integer (1–6, or null before rolling)
```

### 5.2 Dice Bag

```
DiceBag:
  dice: list of Die (36 total at start)
```

### 5.3 Hand

```
Hand:
  dice: list of Die (exactly 6)
  sorted by color after every draw/redraw
```

---

## 6. Functional Requirements

### 6.1 Bag Initialization

* Create 36 dice: 6 per color
* Dice have no value until rolled

### 6.2 Draw Logic

* Randomly draw N dice from bag (remove from bag)
* Return selected dice to bag during redraw (bag is reshuffled)

### 6.3 Lock Logic

* Player toggles locks by typing die indices (e.g. `0,2`)
* Toggling an unlocked die locks it; toggling a locked die unlocks it
* Updated hand is displayed immediately after each toggle
* Locks persist between actions within a phase
* All locks reset when transitioning from Draw Phase to Roll Phase

### 6.4 Roll Logic

* Assign random value (1–6) to each die in hand on initial roll

### 6.5 Reroll Logic

* Re-assign random value (1–6) to all **unlocked** dice only
* Colors are never changed

### 6.6 Evaluation Logic

#### 6.6.1 Color Evaluation (Draw Phase)

1. Count occurrences of each color in hand
2. Identify colors with count ≥ 2
3. Return TRUE if at least **two distinct colors** meet this condition

#### 6.6.2 Number Evaluation (Roll Phase)

1. Group dice by (color, value)
2. Identify groups where count ≥ 2
3. Find two such groups where colors differ **and** values differ
4. Return TRUE if such a pair of pairs exists

---

## 7. CLI Requirements

### 7.1 Display

Each step shows:

* Indexed dice list with color (draw phase) or color + value (roll phase)
* Lock indicator (🔒) on locked dice
* Color condition status: met / not met
* Number condition status: met / not met (roll phase)
* Remaining redraws / rerolls
* Winning pairs when number condition is met

Hand is displayed in **color-sorted order** (matching colors grouped together) throughout the Draw Phase.

### 7.2 Input

| Input | Action |
|---|---|
| `0,2,4` | Toggle lock on dice at those indices |
| Enter (empty) | Execute redraw (Draw Phase) or reroll (Roll Phase) |
| `q` | End current phase early |

---

## 8. Constraints

* Single round only
* Single player only
* No scoring beyond success/failure
* No persistence
* Terminal only — ANSI color output
* No AI or automation

---

## 9. Success Criteria

MVP is complete when:

* Draw phase correctly gates entry into roll phase
* Color evaluation runs after every draw/redraw
* Number evaluation runs after every roll/reroll
* Round ends immediately on draw-phase failure
* Final output clearly states SUCCESS or FAILURE with winning pairs shown on success

---

## 10. Design Principles

* **Draw Phase = Resource Qualification (Colors)**
* **Roll Phase = Value Resolution (Numbers)**
* **Lock model** replaces select-to-discard: players protect what they want, not discard what they don't
* Separation of phases reduces branching logic and makes evaluation deterministic

---

## 11. Summary

Core loop:

> Draw → Sort → Evaluate (Color) →
> Pass → Roll → Evaluate (Number) → Result
> Fail → End Round

Controls:

> Type indices to lock/unlock → Enter to execute → q to end phase early
