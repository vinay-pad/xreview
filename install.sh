#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLED=0

echo ""
echo "  xreview — cross-review your plans with other AI agents"
echo ""

# Always install prompts into .xreview/prompts/
mkdir -p .xreview/prompts
cp "$SCRIPT_DIR/prompts/reviewer.md" .xreview/prompts/reviewer.md
cp "$SCRIPT_DIR/prompts/digest.md" .xreview/prompts/digest.md
cp "$SCRIPT_DIR/prompts/round2.md" .xreview/prompts/round2.md
echo "  ✓ Prompts  →  .xreview/prompts/"

echo ""

# Claude Code: slash command
if command -v claude &> /dev/null; then
    mkdir -p .claude/commands
    cp "$SCRIPT_DIR/claude-code/xreview.md" .claude/commands/xreview.md
    echo "  ✓ Claude Code  →  /xreview"
    echo "    Installed .claude/commands/xreview.md"
    INSTALLED=$((INSTALLED + 1))
else
    echo "  ✗ Claude Code — not found"
    echo "    Install: npm i -g @anthropic-ai/claude-code"
fi

echo ""

# Codex: skill
if command -v codex &> /dev/null; then
    mkdir -p .agents/skills/xreview
    cp "$SCRIPT_DIR/codex/xreview/SKILL.md" .agents/skills/xreview/SKILL.md
    echo "  ✓ Codex  →  /skills -> xreview or \$xreview"
    echo "    Installed .agents/skills/xreview/SKILL.md"
    INSTALLED=$((INSTALLED + 1))

    CODEX_CONFIG="$HOME/.codex/config.toml"
    if [ -f "$CODEX_CONFIG" ]; then
        if ! grep -q 'skills\s*=\s*true' "$CODEX_CONFIG" 2>/dev/null; then
            echo ""
            echo "    ⚠  Codex skills may need enabling. Add to ~/.codex/config.toml:"
            echo "      [features]"
            echo "      skills = true"
        fi
    fi
else
    echo "  ✗ Codex — not found"
    echo "    Install: npm i -g @openai/codex"
fi

echo ""
echo "─────────────────────────────────────────"
echo ""

if [ $INSTALLED -gt 0 ]; then
    echo "  $INSTALLED integration(s) installed."
    echo ""
    echo "  Prompts are in .xreview/prompts/ — edit them to tune review behavior."
    echo ""
    echo "  Usage:"
    [ -f ".claude/commands/xreview.md" ] && echo "    Claude Code:  /xreview --reviewer codex"
    [ -f ".agents/skills/xreview/SKILL.md" ] && echo "    Codex:        /skills -> xreview or \$xreview --reviewer claude"
    echo ""
    echo "  Restart your CLI session to load the new commands."
else
    echo "  No supported CLIs found. Install at least one:"
    echo "    Claude Code:  npm i -g @anthropic-ai/claude-code"
    echo "    Codex:        npm i -g @openai/codex"
fi
echo ""
