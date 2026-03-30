# `tests/uscf_functions.py` Call Tree

This document describes the function call tree for [`tests/uscf_functions.py`](/home/saspeh/dev/python/chess-rating/tests/uscf_functions.py), including which functions are public entry points, which helpers they rely on, and how the major rating paths branch.

## Function Inventory

Public-facing functions:

- `check`
- `computeBonus`
- `computeK`
- `performanceRating`
- `newRating`
- `getK`
- `getBonus`

Private helpers:

- `_js_round`
- `_ratings`
- `_dual_enabled`

## High-Level Call Tree

```text
check
  └─ sets global isDual

_js_round
  └─ math.floor

_ratings
  └─ int

_dual_enabled
  └─ reads dual_k or global isDual

computeBonus
  └─ math.sqrt

computeK
  ├─ math.sqrt
  └─ _dual_enabled

performanceRating
  ├─ _ratings
  ├─ math.exp
  ├─ math.log
  └─ _js_round

newRating
  ├─ _ratings
  ├─ math.exp
  ├─ math.log
  ├─ provisional path:
  │   └─ performanceRating
  ├─ established path:
  │   ├─ computeK
  │   └─ computeBonus
  └─ _js_round

getK
  ├─ _ratings
  ├─ computeK
  └─ _js_round

getBonus
  ├─ _ratings
  ├─ math.exp
  ├─ math.log
  ├─ computeK
  ├─ computeBonus
  └─ _js_round
```

## Public Entry Points

### `check(dual_checked=False)`

Purpose:
Sets the module-global `isDual` flag to `"Y"` or `"N"`.

Calls:

- No other functions in this module

Used by:

- Indirectly affects `_dual_enabled`
- Therefore indirectly affects `computeK`, `newRating`, `getK`, and `getBonus` when `DualK == ""`

### `computeBonus(score, myExp, myK, myCurrentGames)`

Purpose:
Computes the event bonus for established-player rating updates.

Calls:

- `math.sqrt`

Used by:

- `newRating` on the established-player path
- `getBonus`

### `computeK(oldRating, myGameCount, myCurrentGames, DualK="")`

Purpose:
Computes the effective K-factor.

Calls:

- `_dual_enabled`
- `math.sqrt`

Used by:

- `newRating` on the established-player path
- `getK`
- `getBonus`

### `performanceRating(Established, fScore, r1, ..., r12)`

Purpose:
Estimates a performance rating from score plus opponent ratings.

Calls:

- `_ratings`
- `_js_round`
- `math.exp`
- `math.log`

Used by:

- `newRating` on the provisional-player path

### `newRating(GameCount, myOldRating, DualK, score, age, r1, ..., r12)`

Purpose:
Main rating-update function. This is the central orchestration function in the file.

Calls:

- `_ratings`
- `performanceRating` when `myGameCount <= 8`
- `computeK` when `myGameCount > 8`
- `computeBonus` when `myGameCount > 8`
- `_js_round`
- `math.exp`
- `math.log`

Used by:

- External callers and tests

### `getK(GameCount, myOldRating, DualK, score, r1, ..., r12)`

Purpose:
Returns the display-form K-factor for an event.

Calls:

- `_ratings`
- `computeK`
- `_js_round`

Used by:

- External callers and tests

### `getBonus(GameCount, myOldRating, DualK, score, r1, ..., r12)`

Purpose:
Returns the display-form bonus for an event.

Calls:

- `_ratings`
- `computeK`
- `computeBonus`
- `_js_round`
- `math.exp`
- `math.log`

Used by:

- External callers and tests

## Private Helpers

### `_js_round(value)`

Purpose:
Implements JavaScript `Math.round` behavior instead of Python's bankers rounding.

Called by:

- `performanceRating`
- `newRating`
- `getK`
- `getBonus`

### `_ratings(*values)`

Purpose:
Filters out empty-string placeholders and converts the remaining rating arguments to integers.

Called by:

- `performanceRating`
- `newRating`
- `getK`
- `getBonus`

### `_dual_enabled(dual_k)`

Purpose:
Determines whether dual-rating K-factor adjustments apply. Prefers the explicit `DualK` argument; otherwise falls back to the global `isDual`.

Called by:

- `computeK`

## Main Execution Paths

### 1. Provisional rating path

This path is taken inside `newRating` when `myGameCount <= 8`.

```text
newRating
  ├─ _ratings
  ├─ compute expected score locally
  ├─ performanceRating
  │   ├─ _ratings
  │   └─ _js_round
  └─ _js_round
```

Notes:

- `newRating` computes opponent expectations itself before branching.
- For provisional players, the result is based on a blend of old rating and performance rating.
- `computeK` and `computeBonus` are not used on this branch.

### 2. Established rating path

This path is taken inside `newRating` when `myGameCount > 8`.

```text
newRating
  ├─ _ratings
  ├─ compute expected score locally
  ├─ computeK
  │   └─ _dual_enabled
  ├─ computeBonus
  └─ _js_round
```

Notes:

- This is the classic expected-score plus K-factor plus bonus formula path.
- The global `isDual` can influence this branch if `DualK` is passed as `""`.

### 3. Display-only K-factor path

```text
getK
  ├─ _ratings
  ├─ computeK
  │   └─ _dual_enabled
  └─ _js_round
```

Notes:

- Returns `""` if there is no old rating.
- Returns `"N/A"` for players with eight or fewer prior games.

### 4. Display-only bonus path

```text
getBonus
  ├─ _ratings
  ├─ compute expected score locally
  ├─ computeK
  │   └─ _dual_enabled
  ├─ computeBonus
  └─ _js_round
```

Notes:

- Returns `""` if there is no old rating.
- Returns `"N/A"` for provisional players or events with fewer than three games.

## Reverse Dependency View

This is the same information inverted, showing which functions depend on each helper.

```text
_dual_enabled
  └─ computeK
      ├─ newRating
      ├─ getK
      └─ getBonus

computeBonus
  ├─ newRating
  └─ getBonus

performanceRating
  └─ newRating

_ratings
  ├─ performanceRating
  ├─ newRating
  ├─ getK
  └─ getBonus

_js_round
  ├─ performanceRating
  ├─ newRating
  ├─ getK
  └─ getBonus
```

## Summary

The core orchestrator is `newRating`.

- For provisional players, `newRating` delegates to `performanceRating`.
- For established players, `newRating` delegates to `computeK` and `computeBonus`.
- `getK` and `getBonus` are display helpers that reuse the same lower-level math functions without performing a full rating update.
- `_ratings`, `_js_round`, and `_dual_enabled` are the shared internal utilities that support nearly all of the public API.
