#!/bin/bash
# launch.sh — Run this to start a Claude Code agent session
# Usage:
#   First time ever:     bash launch.sh init
#   Every session after: bash launch.sh

SESSION_TYPE="${1:-coding}"
PROJECT_DIR="portfolio-advisor"

if [ "$SESSION_TYPE" = "init" ]; then
    PROMPT_FILE="INIT_PROMPT.md"
    echo "🚀 Starting INITIALIZER session (first time only)"
else
    PROMPT_FILE="CODING_AGENT_PROMPT.md"
    echo "🔄 Starting CODING AGENT session"
fi

if [ ! -f "$PROMPT_FILE" ]; then
    echo "❌ Error: $PROMPT_FILE not found. Are you in the bootstrap directory?"
    exit 1
fi

# Create project dir if init
if [ "$SESSION_TYPE" = "init" ]; then
    mkdir -p "$PROJECT_DIR"
    echo "📁 Created $PROJECT_DIR/"
fi

# Run Claude Code with the appropriate prompt
# The --print flag pipes the prompt in, --dangerously-skip-permissions for automation
echo ""
echo "Running: claude --print < $PROMPT_FILE"
echo "---"
cat "$PROMPT_FILE" | claude --print --dangerously-skip-permissions
