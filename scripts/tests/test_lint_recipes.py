"""Tests for the recipe linter.

Run with: pytest scripts/tests/
"""

from __future__ import annotations

from pathlib import Path

import pytest

import lint_recipes


# A minimal, valid recipe used as the baseline for mutation in tests.
GOOD_RECIPE = """<body class="recipe-vegetable">

<div class="title-block">
# Aloo gobi
## Potato and cauliflower curry
</div>

<div class="preamble">

**Source:** *Curry Easy Vegetarian*, p. 50

**Rating:** ★★★☆☆

**Complexity:** ●●○○○

**Servings:** 4

**Calories/serving:** 300

**Dietary requirements:** Vegan, gluten-free

</div>

<div class="ingredients-container">

### Ingredients

::: {.ingredients}
* 500g potatoes
* 1 cauliflower
:::

</div>

<div class="instructions">

### Instructions

#### A. Preparation

1. Peel the **potatoes**.
2. Cut the **cauliflower** into florets.

#### B. Cooking

1. Heat a pan and cook the vegetables until tender.

</div>
</body>
"""


def write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "recipe.md"
    p.write_text(content)
    return p


# ── Baseline ─────────────────────────────────────────────────────────────


def test_good_recipe_passes(tmp_path):
    result = lint_recipes.lint_file(write(tmp_path, GOOD_RECIPE))
    assert result.errors == []


# ── Frontmatter / preamble fields ────────────────────────────────────────


@pytest.mark.parametrize("field_name", lint_recipes.REQUIRED_FIELDS)
def test_missing_required_field_is_error(tmp_path, field_name):
    text = GOOD_RECIPE.replace(f"**{field_name}:**", f"**MISSING_{field_name}:**")
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any(f"Missing required preamble field: {field_name}" in e for e in result.errors)


def test_invalid_rating_is_error(tmp_path):
    text = GOOD_RECIPE.replace("★★★☆☆", "***")
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("Rating must be exactly 5 chars" in e for e in result.errors)


def test_invalid_complexity_is_error(tmp_path):
    text = GOOD_RECIPE.replace("●●○○○", "OOO")
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("Complexity must be exactly 5 chars" in e for e in result.errors)


def test_invalid_servings_is_error(tmp_path):
    text = GOOD_RECIPE.replace("**Servings:** 4", "**Servings:** many")
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("Servings must be a number or range" in e for e in result.errors)


def test_servings_range_is_valid(tmp_path):
    text = GOOD_RECIPE.replace("**Servings:** 4", "**Servings:** 4-6")
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert not any("Servings" in e for e in result.errors)


def test_invalid_calories_is_error(tmp_path):
    text = GOOD_RECIPE.replace("**Calories/serving:** 300", "**Calories/serving:** lots")
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("Calories/serving must be an integer" in e for e in result.errors)


def test_invalid_source_is_error(tmp_path):
    text = GOOD_RECIPE.replace("*Curry Easy Vegetarian*, p. 50", "some book, page 50")
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("Source must be" in e for e in result.errors)


def test_url_source_is_valid(tmp_path):
    text = GOOD_RECIPE.replace(
        "*Curry Easy Vegetarian*, p. 50", "https://example.com/recipe"
    )
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert not any("Source must be" in e for e in result.errors)


# ── Title / subtitle sentence case ────────────────────────────────────────


def test_title_case_h1_is_error(tmp_path):
    text = GOOD_RECIPE.replace("# Aloo gobi", "# Aloo Gobi")
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("H1 title is not in sentence case" in e for e in result.errors)


def test_title_case_h2_is_error(tmp_path):
    text = GOOD_RECIPE.replace(
        "## Potato and cauliflower curry", "## Potato And Cauliflower Curry"
    )
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("H2 subtitle is not in sentence case" in e for e in result.errors)


def test_lowercase_first_letter_is_error(tmp_path):
    text = GOOD_RECIPE.replace("# Aloo gobi", "# aloo gobi")
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("H1 title is not in sentence case" in e for e in result.errors)


def test_acronym_in_subtitle_is_allowed(tmp_path):
    text = GOOD_RECIPE.replace(
        "## Potato and cauliflower curry", "## Curry from the USA region"
    )
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert not any("sentence case" in e for e in result.errors)


@pytest.mark.parametrize(
    "subtitle",
    [
        "Mixed dal, Delhi style",
        "Stir-fried aubergines, Tamil Nadu style",
        "Classic Punjabi-style kidney bean curry",
        "Spinach with fresh Indian cheese",
    ],
)
def test_proper_noun_in_subtitle_is_allowed(tmp_path, subtitle):
    text = GOOD_RECIPE.replace("## Potato and cauliflower curry", f"## {subtitle}")
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert not any("sentence case" in e for e in result.errors)


def test_proper_noun_in_h1_is_still_flagged(tmp_path):
    # H1 uses strict sentence case — proper-noun allowlist doesn't apply.
    # "Delhi" mid-sentence is mixed case and not allowed without the allowlist.
    text = GOOD_RECIPE.replace("# Aloo gobi", "# Aloo Delhi style")
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("H1 title is not in sentence case" in e for e in result.errors)


def test_unknown_proper_noun_in_subtitle_is_flagged(tmp_path):
    # Words not on the allowlist are still flagged.
    text = GOOD_RECIPE.replace(
        "## Potato and cauliflower curry", "## Aloo from the Foobar region"
    )
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("H2 subtitle is not in sentence case" in e for e in result.errors)


def test_h1_longer_than_h2_is_error(tmp_path):
    # H1 should be the short dish name; H2 the longer English description.
    text = GOOD_RECIPE.replace(
        "# Aloo gobi", "# Lal mirch aur tamatar ka soup"
    ).replace("## Potato and cauliflower curry", "## Tomato soup")
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("H1" in e and "longer than H2" in e for e in result.errors)


# ── US → UK spellings ────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "us,uk",
    [
        ("flavors", "flavours"),
        ("color", "colour"),
        ("caramelized", "caramelised"),
        ("yogurt", "yoghurt"),
        ("cilantro", "coriander"),
        ("liter", "litre"),
    ],
)
def test_us_spelling_is_flagged(tmp_path, us, uk):
    text = GOOD_RECIPE.replace(
        "1. Heat a pan and cook the vegetables until tender.",
        f"1. Heat a pan; add {us}.",
    )
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any(f"American spelling {us!r}" in e and uk in e for e in result.errors)


def test_us_spelling_capitalized_keeps_case(tmp_path):
    text = GOOD_RECIPE.replace(
        "1. Heat a pan and cook the vegetables until tender.",
        "1. Flavor the dish well.",
    )
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("'Flavour'" in e for e in result.errors)


def test_uk_spelling_is_not_flagged(tmp_path):
    text = GOOD_RECIPE.replace(
        "1. Heat a pan and cook the vegetables until tender.",
        "1. Add the flavours and colour the dish.",
    )
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert not any("American spelling" in e for e in result.errors)


# ── Indian name canonicalization ─────────────────────────────────────────


@pytest.mark.parametrize(
    "bad,good",
    [
        ("dhal", "dal"),
        ("toovar", "toor"),
        ("tuvar", "toor"),
        ("moong", "mung"),
        ("mattar", "matar"),
        ("wattana", "matar"),
        ("bataka", "aloo"),
        ("bhinda", "bhindi"),
        ("baigan", "baingan"),
        ("gobhi", "gobi"),
        ("amchoor", "amchur"),
    ],
)
def test_indian_name_is_flagged(tmp_path, bad, good):
    text = GOOD_RECIPE.replace("* 500g potatoes", f"* 500g {bad}")
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any(f"non-canonical Indian name {bad!r}" in e and good in e for e in result.errors)


def test_indian_name_capitalized_keeps_case(tmp_path):
    text = GOOD_RECIPE.replace("# Aloo gobi", "# Toovar dal")
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("'Toor'" in e for e in result.errors)


def test_canonical_indian_name_is_not_flagged(tmp_path):
    text = GOOD_RECIPE.replace(
        "* 500g potatoes", "* 500g aloo\n* 200g toor dal\n* 100g matar"
    )
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert not any("non-canonical Indian name" in e for e in result.errors)


# ── Filename checks ──────────────────────────────────────────────────────


def _write_named(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def test_filename_matching_h1_is_not_flagged(tmp_path):
    # GOOD_RECIPE has H1 "Aloo gobi" → "aloo-gobi"
    p = _write_named(tmp_path, "curry-easy_aloo-gobi.md", GOOD_RECIPE)
    result = lint_recipes.lint_file(p)
    assert not any("Filename" in e for e in result.errors)


def test_filename_mismatching_h1_is_flagged(tmp_path):
    p = _write_named(tmp_path, "curry-easy_wrong-name.md", GOOD_RECIPE)
    result = lint_recipes.lint_file(p)
    assert any(
        "Filename does not match H1" in e and "curry-easy_aloo-gobi.md" in e
        for e in result.errors
    )


def test_filename_without_underscore_is_skipped(tmp_path):
    p = _write_named(tmp_path, "aloo-gobi.md", GOOD_RECIPE)
    result = lint_recipes.lint_file(p)
    assert not any("Filename" in e for e in result.errors)


def test_unknown_book_id_is_flagged(tmp_path):
    p = _write_named(tmp_path, "made-up-book_aloo-gobi.md", GOOD_RECIPE)
    result = lint_recipes.lint_file(p)
    assert any("Unknown book ID 'made-up-book'" in e for e in result.errors)


def test_known_book_id_is_not_flagged(tmp_path):
    p = _write_named(tmp_path, "curry-easy_aloo-gobi.md", GOOD_RECIPE)
    result = lint_recipes.lint_file(p)
    assert not any("Unknown book ID" in e for e in result.errors)


@pytest.mark.parametrize(
    "h1,slug",
    [
        ("Aloo gobi", "aloo-gobi"),
        ("Soya & matar keema", "soya-matar-keema"),
        ("Saag-tamatar chana dal", "saag-tamatar-chana-dal"),
        ("Tomato kut", "tomato-kut"),
        ("Hari chutney walay chana", "hari-chutney-walay-chana"),
    ],
)
def test_h1_to_slug_conversion(h1, slug):
    assert lint_recipes._h1_to_slug(h1) == slug


def test_h1_equal_length_to_h2_is_ok(tmp_path):
    text = GOOD_RECIPE.replace("# Aloo gobi", "# Aloooo gobi").replace(
        "## Potato and cauliflower curry", "## Potato cauli"
    )
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert not any("longer than H2" in e for e in result.errors)


# ── Length limits ─────────────────────────────────────────────────────────


def test_title_too_long_is_error(tmp_path):
    long_title = "# " + "a" * (lint_recipes.MAX_TITLE_CHARS + 5)
    # Keep first letter uppercase to isolate the length failure.
    long_title = "# A" + "a" * (lint_recipes.MAX_TITLE_CHARS + 5)
    text = GOOD_RECIPE.replace("# Aloo gobi", long_title)
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("H1 title is" in e and "chars; max" in e for e in result.errors)


def test_subtitle_too_long_is_error(tmp_path):
    long_subtitle = "## P" + "a" * (lint_recipes.MAX_SUBTITLE_CHARS + 5)
    text = GOOD_RECIPE.replace("## Potato and cauliflower curry", long_subtitle)
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("H2 subtitle is" in e and "chars; max" in e for e in result.errors)


def test_file_too_long_is_error(tmp_path):
    padding = "* extra ingredient\n" * 500
    text = GOOD_RECIPE.replace(
        "* 500g potatoes",
        "* 500g potatoes\n" + padding,
    )
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("recipe must fit on one page" in e for e in result.errors)


# ── Forbidden prep-phase cooking words ────────────────────────────────────


@pytest.mark.parametrize(
    "verb",
    ["boil", "boiled", "simmer", "fry", "fried", "roast", "baked"],
)
def test_cooking_verb_in_prep_is_error(tmp_path, verb):
    bad_prep_line = f"3. {verb.capitalize()} the potatoes for 10 minutes."
    text = GOOD_RECIPE.replace(
        "2. Cut the **cauliflower** into florets.",
        "2. Cut the **cauliflower** into florets.\n" + bad_prep_line,
    )
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any(verb in e.lower() and "Preparation section" in e for e in result.errors)


def test_cooking_verb_in_cooking_section_is_ok(tmp_path):
    # "Boil" should be fine in section B
    text = GOOD_RECIPE.replace(
        "1. Heat a pan and cook the vegetables until tender.",
        "1. Boil the potatoes for 10 minutes.",
    )
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert not any("Preparation section" in e for e in result.errors)


@pytest.mark.parametrize(
    "phrase",
    [
        "place in a roasting tin",
        "use a frying pan",
        "line a baking tray",
        "put on a baking sheet",
        "place on baking paper",
        "set on a roasting rack",
        "cover with boiling water",
    ],
)
def test_cookware_phrase_in_prep_is_ok(tmp_path, phrase):
    # Gerunds used as adjectives for cookware/state nouns should not be flagged.
    text = GOOD_RECIPE.replace(
        "2. Cut the **cauliflower** into florets.",
        f"2. Cut the **cauliflower** into florets.\n3. Prepare the dish; {phrase}.",
    )
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert not any("Preparation section" in e for e in result.errors)


# ── High-level structure ──────────────────────────────────────────────────


@pytest.mark.parametrize(
    "marker",
    [
        '<div class="preamble">',
        '<div class="ingredients-container">',
        "### Ingredients",
        "::: {.ingredients}",
        '<div class="instructions">',
        "### Instructions",
    ],
)
def test_missing_structural_marker_is_error(tmp_path, marker):
    text = GOOD_RECIPE.replace(marker, "")
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any(f"Missing structural marker: {marker!r}" in e for e in result.errors)


def test_invalid_body_class_is_error(tmp_path):
    text = GOOD_RECIPE.replace("recipe-vegetable", "recipe-bogus")
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("Invalid body class" in e for e in result.errors)


def test_missing_body_tag_is_error(tmp_path):
    text = GOOD_RECIPE.replace('<body class="recipe-vegetable">', "")
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("Missing <body" in e for e in result.errors)


def test_only_one_section_header_is_error(tmp_path):
    text = GOOD_RECIPE.replace("#### B. Cooking", "#### Cooking")
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("must have both or neither" in e for e in result.errors)


@pytest.mark.parametrize("value", ["n/a", "N/A", "Na", "none", "  "])
def test_empty_other_notes_is_flagged(tmp_path, value):
    text = GOOD_RECIPE.replace(
        "**Dietary requirements:** Vegan, gluten-free",
        f"**Dietary requirements:** Vegan, gluten-free\n\n**Other notes:** {value}",
    )
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("Empty 'Other notes' field" in e for e in result.errors)


def test_nonempty_other_notes_is_ok(tmp_path):
    text = GOOD_RECIPE.replace(
        "**Dietary requirements:** Vegan, gluten-free",
        "**Dietary requirements:** Vegan, gluten-free\n\n**Other notes:** Tasty",
    )
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert not any("Other notes" in e for e in result.errors)


@pytest.mark.parametrize(
    "word,suggestion",
    [
        ("teaspoon", "tsp"),
        ("teaspoons", "tsp"),
        ("tablespoon", "ml"),
        ("tablespoons", "ml"),
    ],
)
def test_longhand_unit_in_ingredients_is_flagged(tmp_path, word, suggestion):
    text = GOOD_RECIPE.replace("* 500g potatoes", f"* 2 {word} salt")
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any(word in e and suggestion in e for e in result.errors)


def test_tbsp_is_banned_in_ingredients(tmp_path):
    text = GOOD_RECIPE.replace("* 500g potatoes", "* 2 tbsp salt")
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("'tbsp' is banned" in e for e in result.errors)


def test_tbsp_is_banned_in_instructions(tmp_path):
    # Unlike longhand `teaspoon`, `tbsp` is banned everywhere.
    text = GOOD_RECIPE.replace(
        "1. Heat a pan and cook the vegetables until tender.",
        "1. Heat a pan and add 2 tbsp water.",
    )
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("'tbsp' is banned" in e for e in result.errors)


def test_longhand_unit_in_instructions_is_ok(tmp_path):
    # Longhand `tablespoons` is fine in instructions (only banned in ingredients).
    text = GOOD_RECIPE.replace(
        "1. Heat a pan and cook the vegetables until tender.",
        "1. Heat a pan and add 2 tablespoons of water if too thick.",
    )
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert not any("ingredients block" in e for e in result.errors)


def test_tsp_in_ingredients_is_ok(tmp_path):
    text = GOOD_RECIPE.replace("* 500g potatoes", "* 2 tsp salt")
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert not any("ingredients block" in e for e in result.errors)


def test_omitted_other_notes_is_ok(tmp_path):
    # GOOD_RECIPE has no Other notes field — should pass.
    result = lint_recipes.lint_file(write(tmp_path, GOOD_RECIPE))
    assert not any("Other notes" in e for e in result.errors)


def test_duplicate_step_number_is_flagged(tmp_path):
    text = GOOD_RECIPE.replace(
        "1. Heat a pan and cook the vegetables until tender.",
        "1. Heat a pan and cook the vegetables until tender.\n1. Add salt.",
    )
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("Step numbers" in e and "not sequential" in e for e in result.errors)


def test_skipped_step_number_is_flagged(tmp_path):
    text = GOOD_RECIPE.replace(
        "2. Cut the **cauliflower** into florets.",
        "2. Cut the **cauliflower** into florets.\n4. Wash the potatoes.",
    )
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert any("Step numbers" in e for e in result.errors)


def test_sequential_step_numbers_pass(tmp_path):
    # GOOD_RECIPE already has sequential numbers in both sections.
    result = lint_recipes.lint_file(write(tmp_path, GOOD_RECIPE))
    assert not any("Step numbers" in e for e in result.errors)


def test_no_section_headers_is_allowed(tmp_path):
    # Simple recipes can omit A/B section headers.
    text = GOOD_RECIPE.replace("#### A. Preparation\n\n", "").replace(
        "#### B. Cooking\n\n", ""
    )
    result = lint_recipes.lint_file(write(tmp_path, text))
    assert not any("must have both or neither" in e for e in result.errors)
