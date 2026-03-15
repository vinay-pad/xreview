#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLED=0

echo ""
echo "  xreview — cross-review your plans with other AI agents"
echo ""

# Install prompts globally into ~/.xreview/prompts/
mkdir -p "$HOME/.xreview/prompts"
cp "$SCRIPT_DIR/prompts/reviewer.md" "$HOME/.xreview/prompts/reviewer.md"
cp "$SCRIPT_DIR/prompts/digest.md" "$HOME/.xreview/prompts/digest.md"
cp "$SCRIPT_DIR/prompts/round2.md" "$HOME/.xreview/prompts/round2.md"
echo "  ✓ Prompts  →  ~/.xreview/prompts/"

echo ""

# Claude Code: global slash command
if command -v claude &> /dev/null; then
    mkdir -p "$HOME/.claude/commands"
    cp "$SCRIPT_DIR/claude-code/xreview.md" "$HOME/.claude/commands/xreview.md"
    echo "  ✓ Claude Code  →  /xreview (global)"
    echo "    Installed ~/.claude/commands/xreview.md"
    INSTALLED=$((INSTALLED + 1))
else
    echo "  ✗ Claude Code — not found"
    echo "    Install: npm i -g @anthropic-ai/claude-code"
fi

echo ""

# Codex: global skill
if command -v codex &> /dev/null; then
    mkdir -p "$HOME/.agents/skills/xreview"
    cp "$SCRIPT_DIR/codex/xreview/SKILL.md" "$HOME/.agents/skills/xreview/SKILL.md"
    echo "  ✓ Codex  →  /skills -> xreview or \$xreview (global)"
    echo "    Installed ~/.agents/skills/xreview/SKILL.md"
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
    echo "  $INSTALLED integration(s) installed globally."
    echo ""
    echo "  /xreview now works in any project."
    echo ""
    echo "  Default prompts are in ~/.xreview/prompts/"
    echo "  To customize per-project, copy them to .xreview/prompts/ in that repo."
    echo ""
    echo "  Usage:"
    [ -f "$HOME/.claude/commands/xreview.md" ] && echo "    Claude Code:  /xreview --reviewer codex"
    [ -f "$HOME/.agents/skills/xreview/SKILL.md" ] && echo "    Codex:        /skills -> xreview or \$xreview --reviewer claude"
    echo ""
    echo "  Restart your CLI session to load the new commands."
else
    echo "  No supported CLIs found. Install at least one:"
    echo "    Claude Code:  npm i -g @anthropic-ai/claude-code"
    echo "    Codex:        npm i -g @openai/codex"
fi
echo ""
