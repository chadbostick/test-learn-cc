# Product Requirements Document (PRD)

## Chromatic Yahtzee – Core MVP (Revised Evaluation Flow)

---

## 1. Objective

Build a minimal, playable command-line version of **Chromatic Yahtzee** focused on a single scoring goal:

> **Achieve Two Pairs of Numbers on Two Pairs of Colors using 6 drawn dice within limited redraws and rerolls.**

This version introduces **step-based evaluation**, where progress is validated during both phases of play.

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

  * 6 colors
  * 6 dice per color
* Each die:

  * Has a **color**
  * Rolls a value from **1–6**

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

#### Redraw Rules

* Up to **3 redraws allowed**
* Each redraw:

  * Player selects any number of dice to return
  * Returned dice go back into the bag
  * New dice drawn to return total to 6

---

### 4.1.1 Draw Phase Evaluation (Color Check)

After:

* Initial draw
* Each redraw

Run evaluation:

#### Requirement:

* Player must have **at least two distinct colors**
* Each of those colors must appear **at least twice**

#### Interpretation:

* Identify colors with count ≥ 2
* There must be **at least two different colors** meeting this condition

---

#### Outcomes:

* **Success (Color Condition Met)**

  * Player may proceed or continue optimizing via redraws

* **Continue**

  * Player has redraws remaining and has not yet met condition

* **Failure (End Round)**

  * Player uses all redraws and does NOT meet condition
  * Round ends immediately
  * No roll phase occurs

---

### 4.2 Roll Phase (Number Phase)

> This phase only begins if the Draw Phase succeeds.

#### Initial Roll

* All 6 dice are rolled

#### Reroll Rules

* Up to **3 rerolls allowed**
* Each reroll:

  * Player selects any number of dice to reroll
  * Values change, colors remain fixed

---

### 4.2.1 Roll Phase Evaluation (Number Check)

After:

* Initial roll
* Each reroll

Run evaluation:

#### Requirement:

* Player must form **two valid pairs**, where:

  * Each pair:

    * Same **color**
    * Same **number**
  * The two pairs:

    * Must use **different colors**
    * Must use **different numbers**

---

#### Outcomes:

* **Success**

  * Goal achieved
  * Round ends

* **Continue**

  * Player has rerolls remaining and has not yet met condition

* **Failure**

  * Player uses all rerolls and does NOT meet condition
  * Round ends

---

## 5. Data Model

### 5.1 Die

```id="die-model"
Die:
  color: string
  value: integer (1–6 or null before rolling)
```

---

### 5.2 Dice Bag

```id="bag-model"
DiceBag:
  dice: list of Die (36 total at start)
```

---

### 5.3 Hand

```id="hand-model"
Hand:
  dice: list of Die (max 6)
```

---

## 6. Functional Requirements

---

### 6.1 Bag Initialization

* Create 36 dice:

  * 6 per color
* Dice do not have values until rolled

---

### 6.2 Draw Logic

* Randomly select dice from bag
* Remove selected dice from bag
* Returned dice go back into bag during redraw

---

### 6.3 Redraw Logic

* Allow selection of dice indices
* Replace selected dice from bag

---

### 6.4 Roll Logic

* Assign random value (1–6) to each die rolled

---

### 6.5 Reroll Logic

* Allow selection of dice indices
* Reassign values only

---

### 6.6 Evaluation Logic

---

#### 6.6.1 Color Evaluation (Draw Phase)

Steps:

1. Count occurrences of each color in hand
2. Identify colors with count ≥ 2
3. Check if at least **two distinct colors** meet this condition

Return:

* TRUE (pass)
* FALSE (fail or continue)

---

#### 6.6.2 Number Evaluation (Roll Phase)

Steps:

1. Group dice by (color, value)
2. Identify groups where count ≥ 2
3. From those groups:

   * Find two groups where:

     * Colors are different
     * Values are different

Return:

* TRUE (success)
* FALSE (fail or continue)

---

## 7. CLI Requirements

---

### 7.1 Output

Display:

* Dice (color + value or color only in draw phase)
* Remaining redraws
* Remaining rerolls
* Current phase (DRAW or ROLL)
* Evaluation status:

  * Color condition: met / not met
  * Number condition: met / not met

---

### 7.2 Input

Player can:

* Select dice indices to redraw
* Select dice indices to reroll
* Skip remaining actions early

---

## 8. Constraints

* Single round only
* No scoring beyond success/failure
* No persistence
* No UI beyond terminal
* No automation or AI player
* No additional goal types (yet)

---

## 9. Success Criteria

MVP is complete when:

* Draw phase correctly gates entry into roll phase
* Color evaluation runs after every draw/redraw
* Number evaluation runs after every roll/reroll
* Round ends immediately on draw-phase failure
* Final output clearly states SUCCESS or FAILURE

---

## 10. Design Principle

This system is intentionally split:

* **Draw Phase = Resource Qualification (Colors)**
* **Roll Phase = Value Resolution (Numbers)**

This separation:

* Reduces branching logic
* Makes evaluation deterministic
* Prepares system for future modular goal types

---

## 11. Summary

Core loop:

> Draw → Evaluate (Color) →
> Pass → Roll → Evaluate (Number) → Result
> Fail → End Round

The system enforces:

* Early failure
* Clear phase boundaries
* Minimal logic with high clarity
