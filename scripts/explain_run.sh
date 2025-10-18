#!/bin/bash
# Display explanation artifacts from last run

OUTPUT_DIR=".helix/outputs"

if [ ! -d "$OUTPUT_DIR" ]; then
    echo "❌ No output directory found. Run Helix first."
    exit 1
fi

echo "📖 Helix Explanation"
echo "===================="
echo ""

if [ -f "$OUTPUT_DIR/explanation.md" ]; then
    echo "## Explanation"
    cat "$OUTPUT_DIR/explanation.md"
    echo ""
fi

if [ -f "$OUTPUT_DIR/run_commands.sh" ]; then
    echo "## Run Commands"
    cat "$OUTPUT_DIR/run_commands.sh"
    echo ""
fi

if [ -f "$OUTPUT_DIR/changelist.txt" ]; then
    echo "## Changes"
    cat "$OUTPUT_DIR/changelist.txt"
    echo ""
fi

if [ -f "$OUTPUT_DIR/next_steps.md" ]; then
    echo "## Next Steps"
    cat "$OUTPUT_DIR/next_steps.md"
    echo ""
fi