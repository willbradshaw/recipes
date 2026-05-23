#!/usr/bin/env python3
"""Lint recipe markdown files against the CLAUDE.md template spec.

Usage:
    scripts/lint_recipes.py                  # lint everything under md/ (excluding draft/)
    scripts/lint_recipes.py md/foo.md ...    # lint specific files
    scripts/lint_recipes.py --drafts         # also lint md/draft/
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MD_DIR = REPO_ROOT / "md"
DATA_DIR = Path(__file__).resolve().parent / "data"

MAX_FILE_CHARS = 2250
MAX_TITLE_CHARS = 25
MAX_SUBTITLE_CHARS = 60

VALID_BODY_CLASSES = {
    "recipe-vegetable",
    "recipe-pulse",
    "recipe-protein",
    "recipe-soup",
    "recipe-sweet",
}

REQUIRED_FIELDS = [
    "Source",
    "Rating",
    "Complexity",
    "Servings",
    "Calories/serving",
    "Dietary requirements",
]
FIELD_ORDER = [
    "Source",
    "Rating",
    "Complexity",
    "Servings",
    "Calories/serving",
    "Dietary requirements",
    "Other notes",
]

# Words that indicate cooking, which should not appear in section A (Preparation).
# Use word-boundary regex; matches are case-insensitive.
FORBIDDEN_PREP_WORDS = [
    "boil",
    "boils",
    "boiled",
    "boiling",
    "simmer",
    "simmers",
    "simmered",
    "simmering",
    "fry",
    "fries",
    "fried",
    "frying",
    "saute",
    "sauté",
    "sauteed",
    "sautéed",
    "sautéing",
    "roast",
    "roasted",
    "roasting",
    "bake",
    "baked",
    "baking",
]
# Nouns that follow these gerunds to form cookware/state phrases ("roasting tin",
# "frying pan", "boiling water"). When a forbidden word is followed by one of
# these, treat it as an adjective rather than a cooking action.
COOKWARE_NOUNS = ("tin", "pan", "tray", "dish", "sheet", "paper", "rack", "water")

FORBIDDEN_PREP_RE = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in FORBIDDEN_PREP_WORDS) + r")\b"
    r"(?!\s+(?:" + "|".join(COOKWARE_NOUNS) + r")\b)",
    re.IGNORECASE,
)

def _load_corrections(name: str) -> tuple[dict[str, str], re.Pattern[str]]:
    mapping: dict[str, str] = json.loads((DATA_DIR / name).read_text())
    pattern = re.compile(
        r"\b(" + "|".join(re.escape(w) for w in mapping) + r")\b", re.IGNORECASE
    )
    return mapping, pattern


US_TO_UK, US_TO_UK_RE = _load_corrections("us_to_uk.json")
INDIAN_NAMES, INDIAN_NAMES_RE = _load_corrections("indian_names.json")
BOOK_IDS: dict[str, str] = json.loads((DATA_DIR / "book_ids.json").read_text())

# Proper nouns that are allowed to be capitalized mid-sentence. Extend as
# new recipes introduce new place names, languages, or culinary traditions.
PROPER_NOUNS = {
    "anya",  # potato variety
    "banarasi",
    "bihari",
    "brahmin",
    "british",
    "chitrapur",
    "coorg",
    "delhi",
    "hyderabadi",
    "indian",
    "kannada",
    "kodava",
    "konkan",
    "nadu",
    "punjabi",
    "saraswat",
    "tamil",
}

RATING_RE = re.compile(r"^[★☆]{5}$")
COMPLEXITY_RE = re.compile(r"^[●○]{5}$")
SERVINGS_RE = re.compile(r"^\d+(\s*[-–]\s*\d+)?$")
CALORIES_RE = re.compile(r"^\d+$")
SOURCE_BOOK_RE = re.compile(r"^\*[^*]+\*,\s*p\.\s*\d+$")
SOURCE_URL_RE = re.compile(r"^https?://\S+$")


@dataclass
class LintResult:
    path: Path
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def lint_file(path: Path) -> LintResult:
    result = LintResult(path=path)
    text = path.read_text()

    # ── Size ───────────────────────────────────────────────────────────────
    if len(text) > MAX_FILE_CHARS:
        result.errors.append(
            f"File is {len(text)} chars; max {MAX_FILE_CHARS} (recipe must fit on one page)"
        )

    # ── Body tag ──────────────────────────────────────────────────────────
    body_match = re.search(r'<body class="([^"]+)">', text)
    if not body_match:
        result.errors.append('Missing <body class="..."> opening tag')
    else:
        cls = body_match.group(1)
        if cls not in VALID_BODY_CLASSES:
            result.errors.append(
                f"Invalid body class {cls!r}; must be one of {sorted(VALID_BODY_CLASSES)}"
            )
    if "</body>" not in text:
        result.errors.append("Missing </body> closing tag")

    # ── Title block / H1 / H2 ─────────────────────────────────────────────
    if '<div class="title-block">' not in text:
        result.errors.append('Missing <div class="title-block">')

    h1_match = re.search(r"^# (.+)$", text, re.MULTILINE)
    h2_match = re.search(r"^## (.+)$", text, re.MULTILINE)

    if not h1_match:
        result.errors.append("Missing H1 title (# ...)")
    else:
        title = h1_match.group(1).strip()
        if len(title) > MAX_TITLE_CHARS:
            result.errors.append(
                f"H1 title is {len(title)} chars; max {MAX_TITLE_CHARS}: {title!r}"
            )
        if not is_sentence_case(title, allow_proper_nouns=False):
            result.errors.append(f"H1 title is not in sentence case: {title!r}")

    if not h2_match:
        result.errors.append("Missing H2 subtitle (## ...)")
    else:
        subtitle = h2_match.group(1).strip()
        if len(subtitle) > MAX_SUBTITLE_CHARS:
            result.errors.append(
                f"H2 subtitle is {len(subtitle)} chars; max {MAX_SUBTITLE_CHARS}: {subtitle!r}"
            )
        if not is_sentence_case(subtitle, allow_proper_nouns=True):
            result.errors.append(f"H2 subtitle is not in sentence case: {subtitle!r}")

    if h1_match and h2_match:
        title = h1_match.group(1).strip()
        subtitle = h2_match.group(1).strip()
        if len(title) > len(subtitle):
            result.errors.append(
                f"H1 ({len(title)} chars) is longer than H2 ({len(subtitle)} chars) — "
                "are they swapped?"
            )

    # ── Preamble fields ───────────────────────────────────────────────────
    fields = parse_preamble_fields(text)
    for f in REQUIRED_FIELDS:
        if f not in fields:
            result.errors.append(f"Missing required preamble field: {f}")

    # Field order
    present = [f for f in FIELD_ORDER if f in fields]
    actual_order = [name for name, _ in iter_preamble_in_order(text) if name in FIELD_ORDER]
    if actual_order != present:
        result.errors.append(
            f"Preamble fields out of order: got {actual_order}, expected {present}"
        )

    # Field-value validation
    if "Rating" in fields and not RATING_RE.match(fields["Rating"]):
        result.errors.append(
            f"Rating must be exactly 5 chars of ★/☆; got {fields['Rating']!r}"
        )
    if "Complexity" in fields and not COMPLEXITY_RE.match(fields["Complexity"]):
        result.errors.append(
            f"Complexity must be exactly 5 chars of ●/○; got {fields['Complexity']!r}"
        )
    if "Servings" in fields and not SERVINGS_RE.match(fields["Servings"]):
        result.errors.append(
            f"Servings must be a number or range (e.g. 4 or 4-6); got {fields['Servings']!r}"
        )
    if "Calories/serving" in fields and not CALORIES_RE.match(fields["Calories/serving"]):
        result.errors.append(
            f"Calories/serving must be an integer; got {fields['Calories/serving']!r}"
        )
    if "Source" in fields:
        src = fields["Source"]
        if not (SOURCE_BOOK_RE.match(src) or SOURCE_URL_RE.match(src)):
            result.errors.append(
                f"Source must be '*Book Title*, p. N' or a URL; got {src!r}"
            )

    # ── Empty "Other notes" ───────────────────────────────────────────────
    if "Other notes" in fields:
        notes = fields["Other notes"].strip().lower()
        if notes in ("", "n/a", "na", "none"):
            result.errors.append(
                f"Empty 'Other notes' field ({fields['Other notes']!r}) — omit the line entirely"
            )

    # ── Structural sections ───────────────────────────────────────────────
    expected_markers = [
        '<div class="preamble">',
        '<div class="ingredients-container">',
        "### Ingredients",
        "::: {.ingredients}",
        ":::",
        '<div class="instructions">',
        "### Instructions",
    ]
    for marker in expected_markers:
        if marker not in text:
            result.errors.append(f"Missing structural marker: {marker!r}")

    # Section A/B headers — optional (simple recipes may omit), so warn only.
    has_prep = "#### A. Preparation" in text
    has_cook = "#### B. Cooking" in text
    if has_prep != has_cook:
        result.errors.append(
            "Recipe has only one of '#### A. Preparation' / '#### B. Cooking' — must have both or neither"
        )

    # ── Unit conventions ─────────────────────────────────────────────────
    # `tbsp` is banned everywhere (too easy to misread as `tsp`): use
    # multiple `tsp` for small quantities or `ml` for larger ones.
    for m in re.finditer(r"\btbsp\b", text, re.IGNORECASE):
        result.errors.append(
            f"{m.group(0)!r} is banned (misreadable as 'tsp'); use 'tsp' (small qty) or 'ml' (larger qty)"
        )
    # Ingredients must use `tsp` (not `teaspoon[s]`), and `tablespoon[s]`
    # longhand is also disallowed there. Longhand units in instructions are
    # fine (consistent with `for 5 minutes`).
    ing_match = re.search(r":::\s*{\.ingredients}(.*?):::", text, re.DOTALL)
    if ing_match:
        for m in re.finditer(
            r"\b(teaspoons?|tablespoons?)\b", ing_match.group(1), re.IGNORECASE
        ):
            word = m.group(1)
            short = "tsp" if "teaspoon" in word.lower() else "tsp (small qty) or ml (larger qty)"
            result.errors.append(
                f"Use {short} instead of {word!r} in the ingredients block"
            )

    # ── Spelling / canonical-name checks ──────────────────────────────────
    _flag_substitutions(text, US_TO_UK, US_TO_UK_RE, "American spelling", result)
    _flag_substitutions(text, INDIAN_NAMES, INDIAN_NAMES_RE, "non-canonical Indian name", result)
    _check_filename(path, text, result)

    # ── Step numbering (each section starts at 1 and runs sequentially) ──
    for header, end_marker in (
        ("#### A. Preparation", "#### B. Cooking"),
        ("#### B. Cooking", "</div>"),
    ):
        block = extract_section(text, header, end_marker)
        if not block:
            continue
        numbers = [int(m.group(1)) for m in re.finditer(r"^(\d+)\.\s", block, re.MULTILINE)]
        if numbers and numbers != list(range(1, len(numbers) + 1)):
            result.errors.append(
                f"Step numbers in '{header}' are not sequential 1..N: got {numbers}"
            )

    # ── Forbidden cooking verbs in Preparation section ────────────────────
    prep_block = extract_section(text, "#### A. Preparation", "#### B. Cooking")
    if prep_block:
        for line_no, line in enumerate(prep_block.splitlines(), start=1):
            for m in FORBIDDEN_PREP_RE.finditer(line):
                result.errors.append(
                    f"Cooking verb {m.group(0)!r} found in Preparation section: {line.strip()!r}"
                )

    return result


def _check_filename(path: Path, text: str, result: LintResult) -> None:
    """Check that the recipe-name portion of the filename matches the H1.

    Expected format: [book-id]_[recipe-name].md, where recipe-name is the
    deterministic kebab-case form of the H1 title.
    """
    stem = path.stem  # filename without .md
    if "_" not in stem:
        return  # not a standard recipe filename; skip
    book_id, recipe_name = stem.split("_", 1)

    if book_id not in BOOK_IDS:
        result.errors.append(
            f"Unknown book ID {book_id!r}; must be one of {sorted(BOOK_IDS)}"
        )

    h1_match = re.search(r"^# (.+)$", text, re.MULTILINE)
    if not h1_match:
        return  # H1 missing; that error is already reported elsewhere

    expected = _h1_to_slug(h1_match.group(1).strip())
    if recipe_name != expected:
        suggested = f"{book_id}_{expected}.md"
        result.errors.append(
            f"Filename does not match H1; rename to {suggested!r}"
        )


def _h1_to_slug(h1: str) -> str:
    """Convert an H1 title to its canonical kebab-case filename form.

    Rules: lowercase, strip italics asterisks, drop '&' and other
    punctuation, collapse whitespace to single hyphens, preserve existing
    hyphens.
    """
    s = h1.lower()
    s = s.replace("&", " ")  # drop ampersand, gap becomes whitespace
    s = re.sub(r"[*'\".,:;!?()]", "", s)  # strip stray punctuation
    s = re.sub(r"\s+", "-", s.strip())  # spaces → hyphens
    s = re.sub(r"-+", "-", s)  # collapse repeated hyphens
    return s


def _flag_substitutions(
    text: str,
    mapping: dict[str, str],
    pattern: re.Pattern[str],
    label: str,
    result: LintResult,
) -> None:
    for m in pattern.finditer(text):
        found = m.group(0)
        replacement = mapping[found.lower()]
        if found[0].isupper():
            replacement = replacement[0].upper() + replacement[1:]
        result.errors.append(f"{label} {found!r}; use {replacement!r}")


def parse_preamble_fields(text: str) -> dict[str, str]:
    """Extract `**Label:** value` pairs from inside the preamble div."""
    fields: dict[str, str] = {}
    for name, value in iter_preamble_in_order(text):
        fields[name] = value
    return fields


def iter_preamble_in_order(text: str):
    m = re.search(
        r'<div class="preamble">(.*?)</div>', text, re.DOTALL
    )
    if not m:
        return
    for fm in re.finditer(r"\*\*([^*]+?):\*\*\s*(.+)", m.group(1)):
        yield fm.group(1).strip(), fm.group(2).strip()


def extract_section(text: str, start_marker: str, end_marker: str) -> str | None:
    si = text.find(start_marker)
    if si < 0:
        return None
    si += len(start_marker)
    ei = text.find(end_marker, si)
    return text[si:ei] if ei >= 0 else text[si:]


def is_sentence_case(s: str, *, allow_proper_nouns: bool = False) -> bool:
    """Permissive sentence-case check.

    Rules:
    - First letter (of first alphabetic word) must be uppercase.
    - Subsequent words must be all-lowercase, all-uppercase (acronym), or
      (if `allow_proper_nouns`) in PROPER_NOUNS.
    - Hyphenated words are checked component-by-component (e.g. "Punjabi-style"
      passes because "Punjabi" is a proper noun and "style" is lowercase).
    Words after sentence-ending punctuation (.!?:) get the same treatment as
    a fresh sentence.

    H1 titles use strict mode (proper nouns shouldn't appear in transliterated
    dish names). H2 subtitles allow the PROPER_NOUNS list since they're
    descriptive English where places/languages naturally occur.
    """
    tokens = re.findall(r"\S+", s)
    if not tokens:
        return False

    sentence_start = True
    for tok in tokens:
        word = re.sub(r"^[\W_]+|[\W_]+$", "", tok)
        if not word:
            continue
        if not word[0].isalpha():
            continue

        # Split hyphenated compounds (e.g. "Punjabi-style", "Stir-fried").
        # The first component follows sentence-start rules; the rest are
        # always treated as mid-sentence.
        parts = word.split("-")
        first, rest = parts[0], parts[1:]

        if sentence_start:
            if not _component_ok(first, at_start=True, allow_proper_nouns=allow_proper_nouns):
                return False
            sentence_start = False
        else:
            if not _component_ok(first, at_start=False, allow_proper_nouns=allow_proper_nouns):
                return False

        for part in rest:
            if not _component_ok(part, at_start=False, allow_proper_nouns=allow_proper_nouns):
                return False

        if tok.endswith((".", "!", "?", ":")):
            sentence_start = True
    return True


def _component_ok(word: str, *, at_start: bool, allow_proper_nouns: bool) -> bool:
    """Validate a single (possibly hyphen-split) word component."""
    if not word or not word[0].isalpha():
        return True
    if at_start:
        return word[0].isupper()
    if word.islower():
        return True
    if word.isupper():
        return True  # acronym
    if allow_proper_nouns and word.lower() in PROPER_NOUNS:
        return True
    return False


def collect_paths(args_paths: list[str], include_drafts: bool) -> list[Path]:
    if args_paths:
        return [Path(p).resolve() for p in args_paths]
    paths = sorted(MD_DIR.glob("*.md"))
    if include_drafts:
        paths += sorted((MD_DIR / "draft").glob("*.md"))
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Specific files to lint")
    parser.add_argument(
        "--drafts", action="store_true", help="Also lint md/draft/*.md"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Only print files with issues"
    )
    args = parser.parse_args()

    paths = collect_paths(args.paths, args.drafts)
    if not paths:
        print("No recipe files to lint.")
        return 0

    total_errors = 0
    files_with_issues = 0

    for p in paths:
        result = lint_file(p)
        total_errors += len(result.errors)

        if result.errors:
            files_with_issues += 1
            rel = p.relative_to(REPO_ROOT) if p.is_relative_to(REPO_ROOT) else p
            print(f"\n{rel}")
            for e in result.errors:
                print(f"  {e}")
        elif not args.quiet:
            rel = p.relative_to(REPO_ROOT) if p.is_relative_to(REPO_ROOT) else p
            print(f"OK  {rel}")

    print(
        f"\n{len(paths)} files checked, {files_with_issues} with issues "
        f"({total_errors} errors)"
    )
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
