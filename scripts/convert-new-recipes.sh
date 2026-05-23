#!/bin/bash

# Convert all md files in md/ that don't yet have a corresponding PDF in pdf/

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

count=0

for md_file in "$REPO_ROOT"/md/*.md; do
    [ -f "$md_file" ] || continue
    pdf_file="$REPO_ROOT/pdf/$(basename "${md_file%.md}").pdf"
    if [ ! -f "$pdf_file" ]; then
        echo "Converting: $md_file"
        "$SCRIPT_DIR/recipe-pdf-generator.sh" "$md_file"
        count=$((count + 1))
    fi
done

if [ "$count" -eq 0 ]; then
    echo "All recipes are up to date."
else
    echo "Converted $count new recipe(s)."
fi
