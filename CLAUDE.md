# Automatic recipe generation

The purpose of this repository is to generate standardized recipes for printing and use in the kitchen, processing recipes from several different books into a common standard. The recipes are provided in image form; converted to markdown; edited by the user; then converted into PDF format via the script `scripts/recipe-pdf-generator.sh`.

## General guidance

- Prefer efficiency: proceed with formatting and flag decisions made, rather than asking extensive clarifying questions upfront.
- Transparently note formatting decisions in your response.
- Source attribution records the start page of multi-page spreads.
- Prefer metric units; add Imperial/US conversions in parentheses where appropriate.
- Never substitute spices or ingredients without explicit direction from the user. Use what the source recipe specifies.
- In most cases, add MSG in a volume equal to the volume of salt.

## File naming

Markdown file names follow the pattern `[book-id]_[recipe-name].md`. Drafts go in `md/draft/` for user review, then move to `md/`.

The **book-id** prefix must be one of the known IDs listed in `scripts/data/book_ids.json` (currently: `curry-easy`, `prashad`, `prashad-home`, `instant-pot`, `online`). The linter rejects unknown book IDs.

The **recipe-name** portion is derived deterministically from the H1 title:
- Lowercase.
- `&` and other punctuation dropped.
- Spaces and existing whitespace → hyphens.
- Hyphens in the title preserved.
- Example: H1 `Soya & matar keema` → `soya-matar-keema`; H1 `Saag-tamatar chana dal` → `saag-tamatar-chana-dal`.

The linter enforces this match — if you rename the H1, rename the file too (or vice versa).

## Document structure

Every recipe file follows this exact skeleton, in order:

```
<body class="[body-class]">

<div class="title-block">
# [Main title]
## [Subtitle]
</div>

<div class="preamble">
[preamble fields]
</div>

<div class="ingredients-container">

### Ingredients

::: {.ingredients}
[ingredient list]
:::

</div>

<div class="instructions">

### Instructions

#### A. Preparation
[numbered steps]

#### B. Cooking
[numbered steps]

</div>
</body>
```

## Body class

The `<body>` tag must have exactly one of these classes (defined in the CSS):

| Class | Use for |
|---|---|
| `recipe-vegetable` | Vegetable-based mains and sides |
| `recipe-pulse` | Lentil, bean and chickpea dishes |
| `recipe-protein` | Paneer, soya, egg, and other protein-centred dishes |
| `recipe-soup` | Soups |
| `recipe-sweet` | Desserts, sweet drinks, baked goods |

## Title block

- **H1 (`#`):** The recipe's primary name in strict sentence case — use the transliterated/original name if one is given (e.g. "Baingan bharta"), otherwise an English name. Max 25 chars.
- **H2 (`##`):** A short English description of the dish in sentence case (e.g. "Simple, twice-cooked aubergine"). Max 60 chars. Recognized proper nouns (place names, languages, regional styles) may be capitalized mid-sentence — the allowlist lives in `scripts/lint_recipes.py:PROPER_NOUNS`.
- **H1 length should not exceed H2 length** — the H1 is meant to be a short dish name; if it's longer than the H2 description, they're probably swapped.

## Preamble

Fields appear in this exact order. Each field is on its own line, formatted as `**Label:** value`, with a blank line between each.

1. **Source:** — For books: `*Book Title*, p. [number]`. For online: the bare URL (no markdown link syntax).
2. **Rating:** — Exactly 5 star characters, filled (★) then empty (☆). Default to `★★★☆☆` (3 stars) unless the user specifies otherwise; this gives the user both characters to copy-paste when adjusting.
3. **Complexity:** — Exactly 5 circle characters, filled (●) then empty (○). Assess based on number of steps, techniques required, and active cooking time. Default to `●●●○○` unless you have reason to judge otherwise.
4. **Servings:** — A number or range (e.g. `4`, `4-6`).
5. **Calories/serving:** — Per-serving calorie count. Estimate using `scripts/data/calorie_values.json`.
6. **Dietary requirements:** — Comma-separated tags. Common values: `Vegan`, `Vegetarian`, `gluten-free`, `no major allergens`, `contains alliums`, `contains dairy`, `contains alliums & dairy`, `contains eggs`. List the most relevant combination.
7. **Other notes:** — Optional. Brief personal-style commentary (e.g. "Quick, easy, very tasty"). **Omit the line entirely if nothing notable** — don't write `n/a` (the linter flags this). Do not invent subjective opinions.

## Ingredients

### Structure
- Wrapped in `<div class="ingredients-container">` with an H3 `### Ingredients` header.
- The list itself is inside a Pandoc fenced div: `::: {.ingredients}` ... `:::`.
- Each ingredient is a bullet (`*`).
- List ingredients in order of first use in the recipe (preparation steps first, then cooking steps).

### Formatting rules
- **No preparation instructions in the ingredients list.** Move all prep (chopping, crushing, soaking, etc.) to section A of the instructions. E.g., list `ginger` in ingredients, then add "crush or finely chop the **ginger**" as a preparation step.
- **Ingredient groups:** If multiple ingredients are combined together at the same point in the recipe and need no separate preparation, group them under a bold header with indented sub-bullets:
  ```
  * **Spice mix:**
      * 1 tsp ground turmeric
      * 2 tsp salt
  ```
  Number groups sequentially if there are multiple (`**Spice mix 1:**`, `**Spice mix 2:**`). Use descriptive names where appropriate (`**Masala paste:**`, `**Paneer marinade:**`, `**Dal mix:**`).
  Never collapse ingredients that need separate preparation into the same group.
- **Units:** Metric primary. Use `g`, `ml`, `tsp`, `cm` for metric. Add Imperial in parentheses where helpful: `18 oz (540g)`, `475ml (16 fl oz)`. Temperatures: `200ºC/390ºF`.
- **`tbsp` is banned everywhere** (too easily misread as `tsp`). Convert to `tsp` for small quantities (≤6 tsp / 2 tbsp) or `ml` for larger ones (3 tsp = 1 tbsp = 15ml).
- **In the ingredients block, also avoid longhand `teaspoon[s]`/`tablespoon[s]`** — use `tsp`/`ml`. Longhand units are fine in instructions (consistent with `for 5 minutes`).
- **Special ingredient names:** Italicize transliterated names in parentheses: `250g red lentils (*masoor dal*)`.
- **Canonical spellings:** Use British English throughout, and use the canonical Indian-name spellings listed in `scripts/data/indian_names.json` (e.g. `toor` not `tuvar`, `matar` not `mattar`, `baingan` not `baigan`). The linter checks both maps (`us_to_uk.json` and `indian_names.json`).

### Ingredient sub-bullet markers
Use `*` for both top-level bullets and sub-bullets. Indent sub-bullets by 4 spaces.

## Instructions

### Structure
- Wrapped in `<div class="instructions">` with an H3 `### Instructions` header.
- Split into two subsections:
  - `#### A. Preparation` — mise en place: chopping, soaking, preparing spice mixes, preheating.
  - `#### B. Cooking` — actual cooking steps, including any boiling (e.g. potatoes). Boiling is cooking, not preparation.
- Both sections use numbered lists, each starting from 1.
- **Exception:** Very simple recipes with no meaningful prep (e.g. drinks, simple baking) may use a single unnumbered section with just numbered steps.

### Formatting rules
- Bold the first instance of each ingredient in each instruction subsection (once in Preparation and once in Cooking): `**oil**`, `**spice mix 1**`, `**fresh coriander**`.
- Include heat levels: "medium heat", "medium-high heat", "high heat".
- Include timing: "for 5-6 minutes", "for about 25 minutes".
- Include visual cues where helpful: "until golden brown", "until the mustard seeds start to pop".
- Omit parenthetical safety warnings (e.g. "take care as they will splutter") — they clutter the instructions.
- Common preparation step: `Prepare the **spice mixes**.` (always include this when spice mixes are defined).
- **Curry leaves** should be crushed in the hand immediately before adding to the pan (not during section A preparation), as the crushing releases volatile oils.
- Many curry recipes end with: "Remove from the heat and leave covered for at least 10 minutes to allow the flavours to infuse."
- **Potato handling standard:** when a recipe pre-boils potatoes, cut them raw (skin on) into ~2cm chunks in Section A, then boil for 25-30 minutes in Section B. Don't boil whole-with-skin then peel.
- **Step numbering:** within each section, numbered steps must run 1, 2, 3, … with no gaps or duplicates. The linter enforces this.

### Page-fit constraint

Each recipe must fit on a single printed page. The linter caps file size at 2250 characters; if a recipe overshoots, trim verbose phrasing (`for 5 minutes` → `for 5 min`, `on a low heat` → `on low`, `for about` → `for ~`) and verbose source-book wording (`1 tin peeled or chopped tomatoes` → `1 tin chopped tomatoes`). Don't drop concrete qualifiers (`chunks`, `pieces`, `florets`) or adverbs of frequency (`stirring regularly`) — those carry real cooking info.

## Calorie reference values

Per-ingredient kcal/100g and kcal/100ml values live in `scripts/data/calorie_values.json`. Use these ballparks when estimating `Calories/serving`. Add new entries to the JSON as recipes introduce other major calorie contributors.

For estimating, use `scripts/calorie_helper.py` — either as a Python import (`from calorie_helper import estimate`) or via its CLI (`scripts/calorie_helper.py "Recipe name" -s 4 -i "Potatoes:680" -i "Fats and oils:60:ml" --spice-tsp 8`). It prints a per-ingredient breakdown and returns the rounded-to-5 kcal/serving figure.

Notes:
- Always use values for ingredients in the state listed in the recipe (e.g. dry pulses, not cooked).
- Common trap: cooked dal is ~120 kcal/100g (water-diluted), but recipes specify dry weight — always use the dry value (~350 kcal/100g).
- Salt and MSG are zero calories. Other dry spices average ~100 kcal/100g, but they're used in tiny amounts (~5 kcal per tsp).
- When estimating calories, always include an aggregate "Spices (aggregate)" line in your breakdown: count cal-containing tsp in the recipe (excluding salt/MSG) and multiply by ~5 kcal.
- Scan ingredient sub-groups (masala paste, sauce mix, etc.) for hidden calorie-dense items like nuts — they're easy to miss and contribute meaningfully.
- Tamarind is treated as a spice for calorie purposes.
- Flapjack-specific ingredients (oats, golden syrup, plain flour) are calculated in that one recipe rather than added to the reference.

## Processing images into markdown

When converting recipe images to markdown:

1. Read the image carefully. Identify the recipe name, source book, page number, serving count, and full ingredient/method text.
2. Apply the markdown format described above, making formatting decisions as needed.
3. Separate preparation instructions embedded in the ingredient list into section A steps.
4. Identify opportunities to group spices/seasonings into named mixes.
5. Convert all measurements to metric-primary format.
6. Flag any decisions or ambiguities in your response to the user.
7. Run `scripts/lint_recipes.py md/draft/[the-new-file].md` and fix any errors before reporting the recipe as done. The linter catches missing fields, spelling/canonical-name issues, page-length overruns, step-numbering bugs, and filename mismatches.
