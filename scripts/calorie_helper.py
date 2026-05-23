#!/usr/bin/env python3
"""Calorie estimation helper.

Loads `scripts/data/calorie_values.json` and exposes lookup + breakdown.

Python usage:
    from calorie_helper import estimate
    estimate("Aloo gobi", 4, [
        ("Potatoes", 680),
        ("Onion", 150),
        ("Fats and oils", 60, "ml"),
    ])

CLI usage:
    scripts/calorie_helper.py "Aloo gobi" --servings 4 \\
        --item "Potatoes:680" --item "Onion:150" --item "Fats and oils:60:ml"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent / "data" / "calorie_values.json"
CALS: dict = json.loads(DATA_PATH.read_text())


def lookup(name: str) -> str:
    """Find an entry by partial match against the keys."""
    name_l = name.lower()
    matches = [k for k in CALS if name_l in k.lower()]
    if not matches:
        raise KeyError(f"No match for {name!r} — keys: {list(CALS)}")
    if len(matches) > 1:
        exact = [k for k in matches if k.lower() == name_l]
        if exact:
            return exact[0]
        raise KeyError(f"Ambiguous {name!r}: matches {matches}")
    return matches[0]


def kcal(name: str, amount: float, unit: str = "g") -> float:
    """Return total kcal for `amount` (g or ml) of an ingredient."""
    key = lookup(name)
    info = CALS[key]
    per = info.get(f"per_100{unit}")
    if per is None:
        # Fall back to the other unit (assume density ≈ 1)
        per = info.get("per_100g") or info.get("per_100ml")
    return amount * per / 100


def estimate(
    name: str,
    servings: int,
    ingredients: list,
    spice_tsp: int = 0,
    verbose: bool = True,
) -> int:
    """Compute total calories and rounded kcal/serving.

    ingredients: list of (ingredient_name, amount_g) or (name, amount, unit)
    spice_tsp:   count of cal-containing spice tsp (excludes salt/MSG); each ≈ 5 kcal
    """
    total = 0.0
    rows = []
    for item in ingredients:
        if len(item) == 2:
            ing, amt = item
            unit = "g"
        else:
            ing, amt, unit = item
        c = kcal(ing, amt, unit)
        rows.append((ing, amt, unit, c))
        total += c
    spice_kcal = spice_tsp * 5
    total += spice_kcal
    per_serving = total / servings
    rounded = round(per_serving / 5) * 5
    if verbose:
        print(f"=== {name} (serves {servings}) ===")
        for ing, amt, unit, c in rows:
            print(f"  {amt:>6.0f} {unit:<2} {ing:<40} {c:>6.0f} kcal")
        if spice_tsp:
            print(f"  {'':>9} {f'Spices (aggregate, {spice_tsp} tsp)':<40} {spice_kcal:>6.0f} kcal")
        print(f"  {'':>9} {'TOTAL':<40} {total:>6.0f} kcal")
        print(f"  {'':>9} {'PER SERVING':<40} {per_serving:>6.0f} kcal")
        print(f"  → round to: {rounded}")
    return rounded


def _parse_item(spec: str) -> tuple:
    """Parse a CLI --item spec like 'Potatoes:680' or 'Fats and oils:60:ml'."""
    parts = spec.split(":")
    if len(parts) == 2:
        return (parts[0], float(parts[1]))
    elif len(parts) == 3:
        return (parts[0], float(parts[1]), parts[2])
    raise argparse.ArgumentTypeError(
        f"Bad --item spec {spec!r}; expected 'name:amount' or 'name:amount:unit'"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("name", help="Recipe name (for display)")
    parser.add_argument("--servings", "-s", type=int, required=True)
    parser.add_argument(
        "--item",
        "-i",
        action="append",
        type=_parse_item,
        required=True,
        help="Ingredient as 'name:amount[:unit]' (unit defaults to g)",
    )
    parser.add_argument(
        "--spice-tsp",
        type=int,
        default=0,
        help="Count of cal-containing spice tsp (excludes salt/MSG)",
    )
    args = parser.parse_args()
    estimate(args.name, args.servings, args.item, spice_tsp=args.spice_tsp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
