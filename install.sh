#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/vinay-pad/xreview.git"
INSTALLED=0

echo ""
echo "  xreview — cross-review your plans with other AI agents"
echo ""

# If run from a clone (e.g., bash install.sh), use that directory.
# If run via curl | bash, clone the repo to a temp dir.
if [ -f "${BASH_SOURCE[0]:-}" ] && [ -d "$(dirname "${BASH_SOURCE[0]}")/prompts" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    SCRIPT_DIR="$(mktemp -d)"
    echo "  Downloading xreview..."
    git clone --depth=1 --quiet "$REPO_URL" "$SCRIPT_DIR"
    CLEANUP_DIR="$SCRIPT_DIR"
    echo ""
fi

cleanup() {
    if [ -n "${CLEANUP_DIR:-}" ]; then
        rm -rf "$CLEANUP_DIR"
    fi
}
trap cleanup EXIT

# Install prompts globally
mkdir -p "$HOME/.xreview/prompts"
cp "$SCRIPT_DIR/prompts/reviewer.md" "$HOME/.xreview/prompts/reviewer.md"
cp "$SCRIPT_DIR/prompts/digest.md" "$HOME/.xreview/prompts/digest.md"
cp "$SCRIPT_DIR/prompts/round2.md" "$HOME/.xreview/prompts/round2.md"
echo "  ✓ Prompts  →  ~/.xreview/prompts/"

mkdir -p "$HOME/.xreview/lib"
rm -rf "$HOME/.xreview/lib/xreviewd"
cp -R "$SCRIPT_DIR/xreviewd" "$HOME/.xreview/lib/xreviewd"
mkdir -p "$HOME/.xreview/bin" "$HOME/.xreview/logs"
cp "$SCRIPT_DIR/bin/xreview-build-prompt" "$HOME/.xreview/bin/xreview-build-prompt"
cp "$SCRIPT_DIR/bin/xreviewd" "$HOME/.xreview/bin/xreviewd"
cp "$SCRIPT_DIR/bin/xreviewctl" "$HOME/.xreview/bin/xreviewctl"
chmod +x "$HOME/.xreview/bin/xreview-build-prompt" "$HOME/.xreview/bin/xreviewd" "$HOME/.xreview/bin/xreviewctl"
echo "  ✓ Tools    →  ~/.xreview/bin/ (prompt builder, daemon, client)"

echo ""

# Claude Code: global slash command
if command -v claude &> /dev/null; then
    mkdir -p "$HOME/.claude/commands"
    cp "$SCRIPT_DIR/claude-code/xreview.md" "$HOME/.claude/commands/xreview.md"
    echo "  ✓ Claude Code  →  /xreview (global)"
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
    INSTALLED=$((INSTALLED + 1))
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
    echo "  Prompt assembly uses ~/.xreview/bin/xreview-build-prompt (<1s)."
    echo ""
    echo "  Usage:"
    [ -f "$HOME/.claude/commands/xreview.md" ] && echo "    Claude Code:  /xreview --reviewer codex"
    [ -f "$HOME/.agents/skills/xreview/SKILL.md" ] && echo "    Codex:        /skills -> xreview or \$xreview --reviewer claude"
    echo ""
    echo "  Quick test: printf 'Say OK only' | claude -p - --print"
    echo "  Restart your CLI session to load the new commands."
else
    echo "  No supported CLIs found. Install at least one:"
    echo "    Claude Code:  npm i -g @anthropic-ai/claude-code"
    echo "    Codex:        npm i -g @openai/codex"
fi
echo ""
