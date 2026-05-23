#!/usr/bin/env python3
"""Lint recipe markdown files against the CLAUDE.md template spec.

Usage:
    scripts/lint_recipes.py                  # lint everything under md/ (excluding draft/)
    scripts/lint_recipes.py md/foo.md ...    # lint specific files
    scripts/lint_recipes.py --drafts         # also lint md/draft/
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MD_DIR = REPO_ROOT / "md"

MAX_FILE_CHARS = 3000
MAX_TITLE_CHARS = 35
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
        if not is_sentence_case(title):
            result.errors.append(f"H1 title is not in sentence case: {title!r}")

    if not h2_match:
        result.errors.append("Missing H2 subtitle (## ...)")
    else:
        subtitle = h2_match.group(1).strip()
        if len(subtitle) > MAX_SUBTITLE_CHARS:
            result.errors.append(
                f"H2 subtitle is {len(subtitle)} chars; max {MAX_SUBTITLE_CHARS}: {subtitle!r}"
            )
        if not is_sentence_case(subtitle):
            result.errors.append(f"H2 subtitle is not in sentence case: {subtitle!r}")

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

    # ── Forbidden cooking verbs in Preparation section ────────────────────
    prep_block = extract_section(text, "#### A. Preparation", "#### B. Cooking")
    if prep_block:
        for line_no, line in enumerate(prep_block.splitlines(), start=1):
            for m in FORBIDDEN_PREP_RE.finditer(line):
                result.errors.append(
                    f"Cooking verb {m.group(0)!r} found in Preparation section: {line.strip()!r}"
                )

    return result


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


def is_sentence_case(s: str) -> bool:
    """Permissive sentence-case check.

    Rules:
    - First letter (of first alphabetic word) must be uppercase.
    - Subsequent words must be all-lowercase OR be a recognized proper-noun-ish
      exception (acronym, contains digits, has internal capital like McX, etc.).
    Words after a colon/em-dash/period get the same treatment as a fresh sentence.
    """
    # Split into tokens, preserving punctuation boundaries
    tokens = re.findall(r"\S+", s)
    if not tokens:
        return False

    sentence_start = True
    for tok in tokens:
        # strip surrounding punctuation and markdown markers
        word = re.sub(r"^[\W_]+|[\W_]+$", "", tok)
        if not word:
            continue
        if not word[0].isalpha():
            # numbers/symbols don't reset sentence-start
            continue
        if sentence_start:
            if not word[0].isupper():
                return False
            sentence_start = False
        else:
            # Allow all-lowercase, all-uppercase (acronym), or words with no letters to check
            if word.islower():
                pass
            elif word.isupper():
                pass
            else:
                # Mixed case mid-sentence is suspect (e.g. "Mushroom" in "Kodava Mushroom Curry")
                return False
        # Reset sentence-start after sentence-ending punctuation
        if tok.endswith((".", "!", "?", ":")):
            sentence_start = True
    return True


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
