# Automatic recipe generation

The purpose of this repository is to generate standardized recipes for printing and use in the kitchen, processing recipes from several different books into a common standard. The recipes are provided in image form; converted to markdown; edited by the user; then converted into PDF format via the script `recipe-pdf-generator.sh`.

## Markdown format

Past markdown files are visible in the `md` folder; read these and copy the standard patterns used. Give more weight to more recent files that may reflect graduate adjustment of the standard. Some general guidance:

- Recipes are divided into title; frontmatter; ingredients; and a two-part recipe text section (Preparation and Cooking).
- The frontmatter should define the source and page number; the star rating; and various other information about the dish. In the absence of specific instructions from the user, give a standard rating of 3 stars; this provides the user with both full and empty star characters to use to modify the rating.
- Next to the rating, provide a "Complexity:" heading with black and white circles in place of stars (this is not present in all markdown files as it was only added recently); the user can use this to assess the time and complexity of the dish.
- The ingredients block of the recipe should not contain any preparation instructions; these should be moved to the main recipe text, usually to the Preparation section. For example, if the ingredients included "ginger, finely chopped or crushed", you should just include "ginger" in the recipe and then add "crush or finely chop the ginger" to the preparation instructions.
- If multiple ingredients can be immediately combined without separate preparation *and* are used at the same point in the recipe, combine them into a single ingredient entry with a bold header (e.g. **Spice mix:**) and add a shared step in the preparation instructions to prepare them. Never collapse ingredients that need separate preparation in this way.

Markdown file names you write should follow the standard pattern `md/draft/[book-id]_[recipe-name].md`. The user will review and edit these before moving them to the main directory and converting them to PDF.

## Other guidance

- Prefer efficiency: proceed with formatting and flag decisions made, rather than asking extensive clarifying questions upfront.
- Transparently note formatting decisions in your response.
- Source attribution records the start page of multi-page spreads.
- Prefer metric units; add Imperial/US conversions in parentheses where appropriate.