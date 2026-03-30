"""Python port of the legacy USCF JavaScript rating helper functions.

The original fixture in ``tests/testdata/uscf_functions.js`` was written for a
browser page published by US Chess. This module extracts the rating math into a
plain-Python form that tests can import directly.

The goal here is compatibility rather than cleanup. Function names, positional
signatures, sentinel values such as ``""`` and ``"N/A"``, and JavaScript-style
rounding behavior are preserved so test code can compare Python results with
the legacy implementation as closely as possible.
"""

from __future__ import annotations

import math


isDual = "N"


def check(dual_checked: bool = False) -> None:
    """Set the module-level dual-rating flag.

    The browser version read the state of a checkbox named ``DUALK`` and stored
    the result in the global variable ``isDual``. In Python we expose the same
    behavior through an explicit argument so tests can toggle the flag without a
    DOM.

    Args:
        dual_checked: When true, store ``"Y"`` in :data:`isDual`; otherwise
            store ``"N"``.
    """
    global isDual
    isDual = "Y" if dual_checked else "N"


def _js_round(value: float) -> int:
    """Return a value rounded with JavaScript ``Math.round`` semantics.

    Python's built-in :func:`round` uses bankers rounding for ties, which does
    not match JavaScript. The original fixture relied on JavaScript rounding, so
    this helper preserves those results for translated tests.
    """
    return math.floor(value + 0.5)


def _ratings(*values: object) -> list[int]:
    """Convert the fixture's rating inputs into a compact integer list.

    The JavaScript functions accept up to twelve positional rating arguments and
    ignore empty-string placeholders. This helper mirrors that behavior and
    returns only the populated rating values as integers.
    """
    ratings: list[int] = []
    for value in values:
        if value != "":
            ratings.append(int(value))
    return ratings


def _dual_enabled(dual_k: object) -> bool:
    """Determine whether dual-rating K-factor adjustments should be applied.

    The legacy script accepted a ``DualK`` argument in some functions but also
    referenced the global ``isDual`` flag set by :func:`check`. This helper
    keeps that precedence:

    - if ``dual_k`` is provided and not ``""``, it wins
    - otherwise the module-level :data:`isDual` flag is used
    """
    if dual_k != "":
        return str(dual_k).upper() == "Y"
    return isDual == "Y"


def computeBonus(score, myExp, myK, myCurrentGames):
    """Compute the US Chess bonus term for an established player event.

    Args:
        score: Actual score earned in the event.
        myExp: Expected score against the event field.
        myK: K-factor already computed for the player and event.
        myCurrentGames: Number of games in the current event.

    Returns:
        The raw bonus amount as a float. The value is floored at zero, and the
        original fixture also suppresses bonus entirely for events with fewer
        than three games.
    """
    myConstant = 10

    if myCurrentGames < 4:
        myBonusGameCount = 4
    else:
        myBonusGameCount = myCurrentGames

    myBonus = myK * (score - myExp) - myConstant * math.sqrt(myBonusGameCount)
    if myBonus < 0:
        myBonus = 0
    if myCurrentGames < 3:
        myBonus = 0
    return myBonus


def computeK(oldRating, myGameCount, myCurrentGames, DualK=""):
    """Compute the effective K-factor used by the legacy US Chess formula.

    Args:
        oldRating: The player's pre-event rating.
        myGameCount: The number of rated games already on record before the
            current event.
        myCurrentGames: The number of games in the current event.
        DualK: Optional ``"Y"``/``"N"`` override for dual-rating handling. If
            left as ``""``, the module-level :data:`isDual` flag is consulted.

    Returns:
        The floating-point K-factor before any presentation rounding.

    Notes:
        The implementation intentionally follows the structure of the JavaScript
        source, including the dual-rating adjustment branch for higher ratings.
    """
    if oldRating < 2355:
        myPriorGames = 50.0 / math.sqrt(
            0.662 + (2569 - oldRating) * (2569 - oldRating) * 0.000007390
        )
    else:
        myPriorGames = 50

    if myPriorGames > myGameCount:
        myPriorGames = myGameCount

    myK = 800.0 / (myPriorGames + myCurrentGames)

    if _dual_enabled(DualK):
        if oldRating < 2200:
            myK = myK
        elif oldRating >= 2500:
            myK = myK / 4.0
        else:
            myK = (6.5 - 0.0025 * oldRating) * myK

    return myK


def performanceRating(
    Established,
    fScore,
    r1="",
    r2="",
    r3="",
    r4="",
    r5="",
    r6="",
    r7="",
    r8="",
    r9="",
    r10="",
    r11="",
    r12="",
):
    """Estimate a performance rating from a score and up to twelve opponents.

    Args:
        Established: Legacy truthy flag indicating whether the player should be
            treated as established. The original script used ``-1`` for true and
            ``0`` for false.
        fScore: The player's actual score in the event.
        r1-r12: Opponent ratings. Empty strings are ignored so callers can pass
            a fixed-width positional argument list.

    Returns:
        The estimated performance rating rounded with JavaScript semantics.

    Notes:
        For non-established calculations, the fixture uses a piecewise-linear
        expectation capped at +/- 400 points. For established calculations, it
        uses the logistic expectation formula. Extreme perfect-score and
        zero-score cases are handled with the same floor and ceiling logic as
        the browser script.
    """
    ratings = _ratings(r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12)

    myExp = 0.0
    pvEst = 0.0
    myEst = 4000.0
    myLow = 0.0
    myHigh = 4000.0
    iCount = len(ratings)
    totalRating = sum(ratings)
    _ = totalRating  # kept for parity with the source fixture

    TRUE = -1
    FALSE = 0
    bEstablished = Established
    if bEstablished == TRUE:
        if abs(fScore) < 0.001 or abs(iCount - fScore) < 0.001:
            bEstablished = FALSE

    while abs(myEst - pvEst) > 0.1:
        myExp = 0.0

        for iRating in ratings:
            if bEstablished == FALSE:
                ratingDiff = myEst - iRating
                if ratingDiff > 400:
                    myExp += 1.0
                elif ratingDiff < -400:
                    myExp += 0.0
                else:
                    myExp += 0.5 + ratingDiff / 800
            else:
                myExp += 1.0 / (math.exp(math.log(10) * ((iRating - myEst) / 400.0)) + 1.0)

        fDiff = myExp - fScore
        pvEst = myEst
        if fDiff > 0.0:
            myHigh = myEst
            myEst = (myEst + myLow) / 2.0
        else:
            myLow = myEst
            myEst = (myEst + myHigh) / 2.0

    if bEstablished == FALSE:
        if abs(fScore) < 0.001:
            myEst = 4000.0
            for iRating in ratings:
                if iRating < myEst:
                    myEst = iRating
            myEst = max(100, myEst - 400)
        elif abs(iCount - fScore) < 0.001:
            myEst = 0.0
            for iRating in ratings:
                if iRating > myEst:
                    myEst = iRating
            myEst = min(2700, myEst + 400)

    return _js_round(myEst)


def newRating(
    GameCount,
    myOldRating,
    DualK,
    score,
    age,
    r1="",
    r2="",
    r3="",
    r4="",
    r5="",
    r6="",
    r7="",
    r8="",
    r9="",
    r10="",
    r11="",
    r12="",
):
    """Compute a new rating using the legacy US Chess helper logic.

    Args:
        GameCount: Number of rated games on record before the current event.
        myOldRating: Existing rating, or ``""`` when the player is unrated.
        DualK: Optional dual-rating override passed through to :func:`computeK`.
        score: Event score earned by the player.
        age: Player age, used only when the player is unrated and has no
            ``myOldRating``.
        r1-r12: Opponent ratings for the current event.

    Returns:
        The new rating as an integer, or ``""`` when the legacy script would
        leave the result blank.

    Notes:
        Players with eight or fewer prior games use the performance-rating path.
        More established players use the expected-score, K-factor, and bonus
        formula path. The final rounding mirrors the original script, including
        the ``roundAway`` adjustment used before applying ``Math.round``.
    """
    # The legacy script treats the pre-event game count as the switch that
    # decides both how to interpret missing inputs and which rating formula to
    # use later.
    myGameCount = int(GameCount)

    if myGameCount > 0:
        # Once a player has prior rated games, an empty old rating is treated as
        # invalid input and the function returns the blank sentinel unchanged.
        if myOldRating == "":
            return ""
        oldRating = int(myOldRating)
    else:
        # For unrated players, the fixture synthesizes a starting rating. If no
        # age is supplied it uses 750; otherwise it clamps age into [4, 20] and
        # maps that age to the historical seed formula used by the USCF page.
        if myOldRating == "":
            if age == "":
                oldRating = 750
            else:
                oldRating = 300 + 50.0 * max(min(age, 20), 4)
        else:
            # Even with zero recorded games, callers may still supply an old
            # rating explicitly; in that case the fixture trusts that value.
            oldRating = int(myOldRating)

    # Collapse the fixed-width rating arguments into only the opponents that
    # were actually supplied for this event.
    ratings = _ratings(r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12)
    myCurrentGames = len(ratings)
    myExp = 0.0
    sumRatings = 0
    iCount = 0

    # Compute the expected score against the event field using the logistic
    # formula. This value is only needed on the established-player branch, but
    # the original script computes it up front for all callers.
    for iRating in ratings:
        myExp += 1.0 / (math.exp(math.log(10) * ((iRating - oldRating) / 400.0)) + 1.0)
        sumRatings += iRating
        iCount += 1

    _ = sumRatings  # kept for parity with the source fixture

    if myGameCount <= 8:
        # Provisional players do not use K-factor and bonus. Instead, the
        # helper estimates a performance rating for the event and blends it with
        # the pre-event rating based on how many prior games already existed.
        FALSE = 0
        rating = performanceRating(
            FALSE, score, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12
        )
        if myGameCount == 0 and (
            (score == 0 and oldRating < rating)
            or (score == iCount and oldRating > rating)
        ):
            # Brand-new players keep the seeded old rating when a perfect score
            # or zero score would otherwise push the provisional performance
            # estimate past that starting point in the "wrong" direction.
            rating = oldRating
        else:
            # Blend the old rating and the event performance rating, weighted by
            # prior games and games from the current event.
            rating = (myGameCount * oldRating + myCurrentGames * rating) / (
                myGameCount + myCurrentGames
            )
        # The provisional branch rounds directly with JavaScript semantics.
        roundAway = 0.0
    else:
        # Established players use the expected-score update formula with a
        # computed K-factor plus any earned bonus points.
        myK = computeK(oldRating, myGameCount, myCurrentGames, DualK)
        myBonus = computeBonus(score, myExp, myK, myCurrentGames)
        rating = oldRating + myK * (score - myExp) + myBonus
        if oldRating < rating:
            # The JavaScript fixture nudges values slightly away from the old
            # rating before rounding so upward and downward changes round away
            # from the starting rating instead of to nearest-even.
            roundAway = 0.4999
        else:
            roundAway = -0.4999

    # Final presentation uses JavaScript-compatible rounding rather than
    # Python's built-in round().
    return _js_round(rating + roundAway)


def getK(
    GameCount,
    myOldRating,
    DualK,
    score,
    r1="",
    r2="",
    r3="",
    r4="",
    r5="",
    r6="",
    r7="",
    r8="",
    r9="",
    r10="",
    r11="",
    r12="",
):
    """Return the event K-factor in display form.

    Args:
        GameCount: Number of rated games before the event.
        myOldRating: Existing rating, or ``""`` to propagate a blank result.
        DualK: Optional dual-rating override.
        score: Unused here, but preserved in the public signature for parity
            with the JavaScript fixture.
        r1-r12: Opponent ratings for the event.

    Returns:
        ``""`` if no prior rating is supplied, ``"N/A"`` for provisional
        players with eight or fewer prior games, otherwise the K-factor rounded
        to two decimal places using JavaScript rounding semantics.
    """
    if myOldRating == "":
        return ""

    oldRating = int(myOldRating)
    myGameCount = int(GameCount)
    if myGameCount <= 8:
        return "N/A"

    myCurrentGames = len(_ratings(r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12))
    myK = computeK(oldRating, myGameCount, myCurrentGames, DualK)
    return _js_round(100 * myK) / 100


def getBonus(
    GameCount,
    myOldRating,
    DualK,
    score,
    r1="",
    r2="",
    r3="",
    r4="",
    r5="",
    r6="",
    r7="",
    r8="",
    r9="",
    r10="",
    r11="",
    r12="",
):
    """Return the event bonus in display form.

    Args:
        GameCount: Number of rated games before the event.
        myOldRating: Existing rating, or ``""`` to propagate a blank result.
        DualK: Optional dual-rating override.
        score: Event score earned by the player.
        r1-r12: Opponent ratings for the event.

    Returns:
        ``""`` if no prior rating is supplied, ``"N/A"`` when the player is
        provisional or the event has fewer than three games, otherwise the bonus
        rounded to two decimal places with JavaScript semantics.
    """
    if myOldRating == "":
        return ""

    oldRating = int(myOldRating)
    myGameCount = int(GameCount)
    if myGameCount <= 8:
        return "N/A"

    ratings = _ratings(r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12)
    myCurrentGames = len(ratings)
    myExp = 0.0

    for iRating in ratings:
        myExp += 1.0 / (math.exp(math.log(10) * ((iRating - oldRating) / 400.0)) + 1.0)

    if myCurrentGames < 3:
        return "N/A"

    myK = computeK(oldRating, myGameCount, myCurrentGames, DualK)
    myBonus = computeBonus(score, myExp, myK, myCurrentGames)
    return _js_round(100 * myBonus) / 100
