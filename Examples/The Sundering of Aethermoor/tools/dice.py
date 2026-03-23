#!/usr/bin/env python3
"""
Dice roller utility for The Sundering of Aethermoor.

Usage:
    python tools/dice.py <dice_expression>

Examples:
    python tools/dice.py d20
    python tools/dice.py d20+5
    python tools/dice.py 2d6
    python tools/dice.py 3d8-2
    python tools/dice.py d20 --advantage
    python tools/dice.py d20 --disadvantage
"""

import random
import sys
import re
import argparse


def roll_dice(sides: int) -> int:
    return random.randint(1, sides)


def parse_expression(expr: str) -> tuple[int, int, int]:
    """Parse a dice expression like '2d6+3' into (num_dice, sides, modifier)."""
    expr = expr.strip().lower()
    pattern = r'^(\d*)d(\d+)([+-]\d+)?$'
    match = re.match(pattern, expr)
    if not match:
        raise ValueError(f"Invalid dice expression: '{expr}'. Use format like 'd20', '2d6', 'd8+3'")

    num_dice_str, sides_str, modifier_str = match.groups()
    num_dice = int(num_dice_str) if num_dice_str else 1
    sides = int(sides_str)
    modifier = int(modifier_str) if modifier_str else 0

    if num_dice < 1:
        raise ValueError("Number of dice must be at least 1")
    if sides < 2:
        raise ValueError("Dice must have at least 2 sides")
    if num_dice > 100:
        raise ValueError("Cannot roll more than 100 dice at once")

    return num_dice, sides, modifier


def roll(expr: str, advantage: bool = False, disadvantage: bool = False) -> dict:
    """Roll dice and return detailed results."""
    num_dice, sides, modifier = parse_expression(expr)

    if advantage and disadvantage:
        # They cancel out
        advantage = disadvantage = False

    if (advantage or disadvantage) and num_dice == 1 and sides == 20:
        # Roll twice, take higher (advantage) or lower (disadvantage)
        roll1 = roll_dice(sides)
        roll2 = roll_dice(sides)
        if advantage:
            chosen = max(roll1, roll2)
            mode = "advantage"
        else:
            chosen = min(roll1, roll2)
            mode = "disadvantage"
        rolls = [roll1, roll2]
        base_total = chosen
        total = chosen + modifier
        is_critical = (sides == 20 and chosen == 20)
        is_fumble = (sides == 20 and chosen == 1)

        result = {
            "expression": expr,
            "mode": mode,
            "rolls": rolls,
            "chosen": chosen,
            "modifier": modifier,
            "total": total,
            "is_critical": is_critical,
            "is_fumble": is_fumble,
            "summary": _format_advantage_summary(expr, rolls, chosen, modifier, total, mode, is_critical, is_fumble)
        }
    else:
        rolls = [roll_dice(sides) for _ in range(num_dice)]
        base_total = sum(rolls)
        total = base_total + modifier
        is_critical = (num_dice == 1 and sides == 20 and rolls[0] == 20)
        is_fumble = (num_dice == 1 and sides == 20 and rolls[0] == 1)

        result = {
            "expression": expr,
            "mode": "normal",
            "rolls": rolls,
            "modifier": modifier,
            "total": total,
            "is_critical": is_critical,
            "is_fumble": is_fumble,
            "summary": _format_summary(expr, rolls, modifier, total, is_critical, is_fumble)
        }

    return result


def _format_summary(expr, rolls, modifier, total, is_critical, is_fumble):
    parts = [f"Rolling {expr}:"]
    if len(rolls) == 1:
        parts.append(f"  Result: {rolls[0]}")
    else:
        parts.append(f"  Rolls: {rolls} = {sum(rolls)}")
    if modifier != 0:
        sign = "+" if modifier > 0 else ""
        parts.append(f"  Modifier: {sign}{modifier}")
    parts.append(f"  TOTAL: {total}")
    if is_critical:
        parts.append("  *** CRITICAL HIT! ***")
    elif is_fumble:
        parts.append("  *** CRITICAL FUMBLE! ***")
    return "\n".join(parts)


def _format_advantage_summary(expr, rolls, chosen, modifier, total, mode, is_critical, is_fumble):
    parts = [f"Rolling {expr} ({mode.upper()}):"]
    parts.append(f"  Rolls: {rolls[0]} and {rolls[1]}")
    parts.append(f"  Chosen: {chosen} ({'higher' if mode == 'advantage' else 'lower'})")
    if modifier != 0:
        sign = "+" if modifier > 0 else ""
        parts.append(f"  Modifier: {sign}{modifier}")
    parts.append(f"  TOTAL: {total}")
    if is_critical:
        parts.append("  *** CRITICAL HIT! ***")
    elif is_fumble:
        parts.append("  *** CRITICAL FUMBLE! ***")
    return "\n".join(parts)


def check(expr: str, dc: int, modifier: int = 0, advantage: bool = False, disadvantage: bool = False) -> dict:
    """Roll against a Difficulty Class (DC). Returns pass/fail."""
    # Add modifier to expression if provided separately
    if modifier != 0:
        sign = "+" if modifier > 0 else ""
        full_expr = f"{expr}{sign}{modifier}"
    else:
        full_expr = expr

    result = roll(full_expr, advantage=advantage, disadvantage=disadvantage)
    result["dc"] = dc
    result["passed"] = result["total"] >= dc
    outcome = "SUCCESS" if result["passed"] else "FAILURE"
    result["summary"] += f"\n  DC {dc}: {outcome}"
    return result


def main():
    parser = argparse.ArgumentParser(description="Dice roller for The Sundering of Aethermoor")
    parser.add_argument("expression", help="Dice expression (e.g., d20, 2d6+3, d8-1)")
    parser.add_argument("--advantage", action="store_true", help="Roll with advantage (roll twice, take higher)")
    parser.add_argument("--disadvantage", action="store_true", help="Roll with disadvantage (roll twice, take lower)")
    parser.add_argument("--dc", type=int, default=None, help="Difficulty Class to check against")
    parser.add_argument("--modifier", type=int, default=0, help="Additional modifier (separate from expression)")

    args = parser.parse_args()

    try:
        if args.dc is not None:
            result = check(
                args.expression,
                dc=args.dc,
                modifier=args.modifier,
                advantage=args.advantage,
                disadvantage=args.disadvantage
            )
        else:
            if args.modifier != 0:
                sign = "+" if args.modifier > 0 else ""
                expr = f"{args.expression}{sign}{args.modifier}"
            else:
                expr = args.expression
            result = roll(expr, advantage=args.advantage, disadvantage=args.disadvantage)

        print(result["summary"])
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
