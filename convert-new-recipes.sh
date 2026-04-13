#!/bin/bash

# Convert all md files in md/ that don't yet have a corresponding PDF in pdf/

count=0

for md_file in md/*.md; do
    [ -f "$md_file" ] || continue
    pdf_file="pdf/$(basename "${md_file%.md}").pdf"
    if [ ! -f "$pdf_file" ]; then
        echo "Converting: $md_file"
        ./recipe-pdf-generator.sh "$md_file"
        count=$((count + 1))
    fi
done

if [ "$count" -eq 0 ]; then
    echo "All recipes are up to date."
else
    echo "Converted $count new recipe(s)."
fi
