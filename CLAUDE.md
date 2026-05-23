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

Markdown file names should follow the pattern `md/draft/[book-id]_[recipe-name].md`. The user will review and edit these before moving them to the main directory and converting them to PDF.

Known book IDs and their full titles:
- `curry-easy` → *Curry Easy Vegetarian*
- `prashad` → *Prashad*
- `prashad-home` → *Prashad At Home*
- `instant-pot` → *Vegetarian Indian Cooking with Your Instant Pot*
- `online` → online sources (URLs)

Recipe names in filenames should be lowercase, hyphen-separated, and use the dish's transliterated name where one exists (e.g. `baingan-bharta`, `paneer-masala`). Use the English name only if no transliterated name is given.

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

- **H1 (`#`):** The recipe's primary name in sentence case — use the transliterated/original name if one is given (e.g. "Baingan bharta"), otherwise an English name.
- **H2 (`##`):** A short English description of the dish in sentence case (e.g. "Simple, twice-cooked aubergine").

## Preamble

Fields appear in this exact order. Each field is on its own line, formatted as `**Label:** value`, with a blank line between each.

1. **Source:** — For books: `*Book Title*, p. [number]`. For online: the bare URL (no markdown link syntax).
2. **Rating:** — Exactly 5 star characters, filled (★) then empty (☆). Default to `★★★☆☆` (3 stars) unless the user specifies otherwise; this gives the user both characters to copy-paste when adjusting.
3. **Complexity:** — Exactly 5 circle characters, filled (●) then empty (○). Assess based on number of steps, techniques required, and active cooking time. Default to `●●●○○` unless you have reason to judge otherwise. (Recently added; not present in all older files.)
4. **Servings:** — A number or range (e.g. `4`, `4-6`).
5. **Calories/serving:** — Per-serving calorie count, if known. Omit if not available. (Recently added; not present in all older files.)
6. **Dietary requirements:** — Comma-separated tags. Common values: `Vegan`, `Vegetarian`, `gluten-free`, `no major allergens`, `contains alliums`, `contains dairy`, `contains alliums & dairy`, `contains eggs`. List the most relevant combination.
7. **Other notes:** — Optional. Brief personal-style commentary (e.g. "Quick, easy, very tasty"). Write `n/a` or omit entirely if nothing notable. Do not invent subjective opinions — leave blank/`n/a` for the user to fill in.

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
- **Units:** Metric primary. Use `g`, `ml`, `tsp`, `cm` for metric. Add Imperial in parentheses where helpful: `18 oz (540g)`, `475ml (16 fl oz)`. Temperatures: `200ºC/390ºF`. In the ingredients block, use `tsp` only (not `tbsp`) to avoid misreading; convert quantities above 6 tsp (i.e. above 2 tbsp) to `ml`.
- **Special ingredient names:** Italicize transliterated names in parentheses: `250g red lentils (*masoor dal*)`.

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

## Calorie reference values

Use these ballpark figures when estimating `Calories/serving`. Always use values for ingredients in the state listed in the recipe (e.g. dry pulses, not cooked). Add new rows here as recipes introduce other major calorie contributors.

| Ingredient | kcal/100g | kcal/100ml |
|---|---|---|
| Dry pulses (dal, lentils, chickpeas) | ~350 | — |
| Fats and oils | 880 | 810 |
| Potatoes | 80 | — |
| Onion | 40 | — |
| Frozen peas | 80 | — |

Common trap: cooked dal is ~120 kcal/100g (water-diluted), but recipes specify dry weight — always use the ~350 kcal/100g figure.

## Processing images into markdown

When converting recipe images to markdown:

1. Read the image carefully. Identify the recipe name, source book, page number, serving count, and full ingredient/method text.
2. Apply the markdown format described above, making formatting decisions as needed.
3. Separate preparation instructions embedded in the ingredient list into section A steps.
4. Identify opportunities to group spices/seasonings into named mixes.
5. Convert all measurements to metric-primary format.
6. Flag any decisions or ambiguities in your response to the user.
