#!/bin/bash

# Default values
DEFAULT_OUTPUT_DIR="./pdf"
DEFAULT_CSS="recipe-style-css.css"

# Function to display usage information
usage() {
    echo "Usage: $0 <markdown_file> [output_directory] [css_file]"
    echo "  <markdown_file>    : Path to the input Markdown file (required)"
    echo "  [output_directory] : Directory to save the output PDF (default: $DEFAULT_OUTPUT_DIR)"
    echo "  [css_file]         : Path to the CSS file (default: $DEFAULT_CSS)"
    exit 1
}

# Check if at least one argument (markdown file) is provided
if [ $# -lt 1 ]; then
    usage
fi

# Assign arguments to variables
MARKDOWN_FILE="$1"
OUTPUT_DIR="${2:-$DEFAULT_OUTPUT_DIR}"
CSS_FILE="${3:-$DEFAULT_CSS}"

# Check if the input Markdown file exists
if [ ! -f "$MARKDOWN_FILE" ]; then
    echo "Error: Input Markdown file '$MARKDOWN_FILE' not found."
    exit 1
fi

# Create the output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Extract the filename without extension and add .pdf
OUTPUT_FILENAME=$(basename "${MARKDOWN_FILE%.*}").pdf

# Full path for the output PDF
OUTPUT_PATH="$OUTPUT_DIR/$OUTPUT_FILENAME"

# Run pandoc command
pandoc "$MARKDOWN_FILE" -o "$OUTPUT_PATH" --pdf-engine=weasyprint --css="$CSS_FILE"

# Check if the PDF was successfully created
if [ $? -eq 0 ]; then
    echo "PDF successfully created: $OUTPUT_PATH"
else
    echo "Error: PDF creation failed."
    exit 1
fi
