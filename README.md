# xreview

Get a fresh, independent review of your plan from another AI coding agent — without leaving your session.

Working in Claude Code? Run `/xreview`. In Codex? Open `/skills` and choose `xreview`, or type `$xreview`. In both tools, the file is optional: if you omit it, `xreview` reviews the most recent in-session plan or spec. Or review with a **fresh instance of the same model** — no session bias, no anchoring, no sunk cost.

## Why

After an hour in a session, your AI agent is anchored. It committed to decisions early, explored certain paths, and won't catch its own blind spots. A fresh reviewer sees the plan like a new engineer reading it for the first time.

xreview makes this one command instead of copy-pasting between tools.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/vinay-pad/xreview/main/install.sh | bash
```

One install, works in every project. The script:

1. Installs prompts, commands, and skills globally
2. Registers MCP servers so cross-model review is fast (warm instance, no cold start)

| What | Where | Purpose |
|------|-------|---------|
| Prompts | `~/.xreview/prompts/` | Reviewer, digest, and follow-up prompt templates |
| Claude Code command | `~/.claude/commands/xreview.md` | `/xreview` slash command (global) |
| Codex skill | `~/.agents/skills/xreview/SKILL.md` | `/skills` -> `xreview` or `$xreview` (global) |
| MCP: Codex in Claude | `claude mcp add codex` | Codex stays warm inside Claude Code sessions |
| MCP: Claude in Codex | `codex mcp add claude-code` | Claude stays warm inside Codex sessions |

No pip, no npm, no dependencies. Just markdown files and MCP config.

To customize prompts for a specific project, copy them into that repo:

```bash
cp -r ~/.xreview/prompts .xreview/prompts
# edit .xreview/prompts/ to taste — project-local prompts take priority
```

### Update

Re-run the install command — it pulls the latest and overwrites the global files:

```bash
curl -fsSL https://raw.githubusercontent.com/vinay-pad/xreview/main/install.sh | bash
```

Project-local prompts in `.xreview/prompts/` are not touched.

**Requirements:** At least two AI coding CLIs installed and authenticated.

## Usage

### From Claude Code

```
/xreview
/xreview plan.md --reviewer codex
/xreview plan.md --reviewer codex,self
/xreview plan.md --reviewer self --context prd.md,architecture.md
```

### From Codex

```
/skills
$xreview
$xreview plan.md --reviewer claude
$xreview plan.md --reviewer codex,self
$xreview plan.md --reviewer self --context prd.md,architecture.md
```

The argument surface is intentionally the same in both tools:

```
xreview [file] --reviewer <reviewers> --context <extra-files> --no-codebase
```

If `file` is omitted, the agent should use the most recent plan or spec from the current conversation.

### What `self` means

`self` = a fresh instance of the model you're currently using. It reviews your plan cold, with zero session context. Often catches more than a different model because it has the same capabilities but none of your accumulated assumptions.

## What happens

1. Your agent reads the plan from the provided file or the current conversation and gathers codebase context
2. Reads the reviewer prompt (project-local `.xreview/prompts/reviewer.md` if it exists, otherwise global `~/.xreview/prompts/reviewer.md`)
3. Calls the reviewer via MCP (fast, warm instance) or CLI subprocess (fallback)
4. Reviewer does an independent review: validates against the codebase, finds structural problems, challenges decisions, rates the plan READY/REVISE/RETHINK
5. Response flows back into your session
6. Your agent reads the digest prompt and processes the feedback critically — doesn't blindly accept it

### The digest guardrails

Your agent classifies each piece of feedback:

- **Accept** — genuine issue, will change the plan
- **Reject** — wrong or doesn't apply, with specific reasoning
- **Partially accept** — real concern but different fix needed

And watches for: hallucinated concerns, scope creep, preferences disguised as problems, suggestions that duplicate existing code.

### Multi-round reviews

After the first review, ask your agent to send the updated plan back. It reads the round2 prompt and tells the reviewer to verify fixes were actually made, check for new issues, and call out weak rejections.

## Editing prompts

The prompts are the product. Global defaults live in `~/.xreview/prompts/`. To customize per-project, copy them to `.xreview/prompts/` in that repo — project-local always wins.

| File | Controls |
|------|----------|
| `reviewer.md` | What the external reviewer focuses on and how it formats feedback |
| `digest.md` | How your agent processes feedback — guardrails against blind acceptance |
| `round2.md` | Follow-up round instructions — verify fixes, find new issues |

Tune these to match your workflow. Make the reviewer harsher, add domain-specific review criteria, adjust the digest rules.

## File structure

```
# Installed globally
~/.xreview/
  prompts/
    reviewer.md         # Independent review prompt
    digest.md           # Feedback analysis guardrails
    round2.md           # Follow-up round prompt
~/.claude/
  commands/
    xreview.md          # /xreview slash command (works in any project)
~/.agents/
  skills/
    xreview/
      SKILL.md          # /skills -> xreview or $xreview (works in any project)

# Optional per-project override (takes priority over global)
your-project/.xreview/
  prompts/
    reviewer.md         # Project-specific review criteria
    digest.md
    round2.md
```

```
# Source repo
xreview/
├── install.sh
├── claude-code/xreview.md
├── codex/xreview/SKILL.md
├── prompts/
│   ├── reviewer.md
│   ├── digest.md
│   └── round2.md
├── README.md
└── LICENSE
```

## FAQ

**Does this cost money?**
Each review is an API call via the reviewer's CLI. Same cost as using that CLI directly.

**Can I review with the same model?**
Yes — use `self` or the model name. A fresh instance reviews without session bias. This is often the most useful mode.

**What if a reviewer CLI isn't installed?**
The agent reports it and continues with the others.

**Why not an MCP server or Python package?**
The agent already knows how to read files, run shell commands, and process output. It just needs instructions on when to call another CLI and how to think about the feedback. That's markdown files, not infrastructure.

**What if the prompt-only approach breaks?**
If you hit issues with shell escaping or inconsistent agent behavior, the next step would be extracting a small local runner script. But start simple and add that only if needed.

## License

MIT
