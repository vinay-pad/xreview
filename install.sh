#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/vinay-pad/xreview.git"
INSTALLED=0
MCP_CONFIGURED=0

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
    [ -n "${CLEANUP_DIR:-}" ] && rm -rf "$CLEANUP_DIR"
}
trap cleanup EXIT

# Install prompts globally
mkdir -p "$HOME/.xreview/prompts"
cp "$SCRIPT_DIR/prompts/reviewer.md" "$HOME/.xreview/prompts/reviewer.md"
cp "$SCRIPT_DIR/prompts/digest.md" "$HOME/.xreview/prompts/digest.md"
cp "$SCRIPT_DIR/prompts/round2.md" "$HOME/.xreview/prompts/round2.md"
echo "  ✓ Prompts  →  ~/.xreview/prompts/"

echo ""

# Claude Code: global slash command + MCP server for Codex
if command -v claude &> /dev/null; then
    mkdir -p "$HOME/.claude/commands"
    cp "$SCRIPT_DIR/claude-code/xreview.md" "$HOME/.claude/commands/xreview.md"
    echo "  ✓ Claude Code  →  /xreview (global)"
    INSTALLED=$((INSTALLED + 1))

    # Register Codex as an MCP server in Claude Code (if codex is installed)
    if command -v codex &> /dev/null; then
        claude mcp add -s user --transport stdio codex -- codex mcp-server 2>/dev/null && {
            echo "  ✓ MCP  →  Codex registered as MCP server in Claude Code"
            MCP_CONFIGURED=$((MCP_CONFIGURED + 1))
        } || echo "  ⚠  Could not register Codex MCP server (run manually: claude mcp add -s user --transport stdio codex -- codex mcp-server)"
    fi
else
    echo "  ✗ Claude Code — not found"
    echo "    Install: npm i -g @anthropic-ai/claude-code"
fi

echo ""

# Codex: global skill + MCP server for Claude
if command -v codex &> /dev/null; then
    mkdir -p "$HOME/.agents/skills/xreview"
    cp "$SCRIPT_DIR/codex/xreview/SKILL.md" "$HOME/.agents/skills/xreview/SKILL.md"
    echo "  ✓ Codex  →  /skills -> xreview or \$xreview (global)"
    INSTALLED=$((INSTALLED + 1))

    # Register Claude as an MCP server in Codex (if claude is installed)
    if command -v claude &> /dev/null; then
        codex mcp add claude-code -- claude mcp serve 2>/dev/null && {
            echo "  ✓ MCP  →  Claude registered as MCP server in Codex"
            MCP_CONFIGURED=$((MCP_CONFIGURED + 1))
        } || {
            echo "  ⚠  Could not register Claude MCP server automatically."
            echo "    Add to ~/.codex/config.toml:"
            echo "      [mcp_servers.claude-code]"
            echo "      command = \"claude\""
            echo "      args = [\"mcp\", \"serve\"]"
        }
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
    if [ $MCP_CONFIGURED -gt 0 ]; then
        echo "  $MCP_CONFIGURED MCP server(s) configured for fast cross-model review."
    fi
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
