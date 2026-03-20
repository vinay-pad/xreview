# xreview

Get a fresh, independent review of your plan from another AI coding agent — without leaving your session.

Working in Claude Code? Run `/xreview`. In Codex? Type `$xreview`. The file is optional — if you omit it, xreview reviews the most recent in-session plan.

## Why

After an hour in a session, your AI agent is anchored. It committed to decisions early, explored certain paths, and won't catch its own blind spots. A fresh reviewer sees the plan like a new engineer reading it for the first time.

xreview makes this one command instead of copy-pasting between tools.

## Install

**Prerequisites:** At least one of [Claude Code](https://claude.ai/download) or [Codex](https://github.com/openai/codex) installed and authenticated.

```bash
curl -fsSL https://raw.githubusercontent.com/vinay-pad/xreview/main/install.sh | bash
```

That's it. No pip, no npm, no dependencies. Restart your CLI session to load the new commands.

To update, re-run the same command.

## Usage

### Claude Code

```
/xreview                                    # review latest in-session plan with a fresh Claude instance
/xreview plan.md --reviewer codex           # send plan.md to Codex for review
/xreview --reviewer codex,self              # get reviews from both Codex and a fresh Claude
/xreview plan.md --context prd.md           # include extra files as context
/xreview --no-codebase                      # skip sending project structure
```

### Codex

```
$xreview                                    # review latest in-session plan with a fresh Codex instance
$xreview plan.md --reviewer claude          # send plan.md to Claude for review
$xreview --reviewer claude,self             # get reviews from both Claude and a fresh Codex
$xreview plan.md --context prd.md           # include extra files as context
```

### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `<file>` | Plan, spec, or code file to review | Most recent plan in session |
| `--reviewer` | `codex`, `claude`, `self`, `inline` (comma-separated) | `self` |
| `--context` | Extra files to include | none |
| `--no-codebase` | Skip project structure in prompt | off |

**`self`** = a fresh instance of the model you're currently using, with zero session context. Often catches more than a different model because it has the same capabilities but none of your accumulated assumptions.

**`inline`** = in-session review (fast, but less independent since the same agent wrote the plan).

## How it works

1. Your agent extracts the plan (from file or conversation)
2. `xreview-build-prompt` assembles the review prompt (reviewer instructions + project structure + plan) in <1s
3. The prompt is piped to the reviewer CLI (`codex exec` or `claude -p`), which has full filesystem access to verify claims
4. The reviewer produces an independent review (READY / REVISE / RETHINK)
5. Your agent critically digests the feedback — accepts, rejects with reasoning, or partially accepts each point

### Multi-round reviews

Ask your agent to send the updated plan back for another round. The reviewer gets the full history (previous review + your responses) so it can verify fixes were actually made.

## Customizing prompts

Global defaults live in `~/.xreview/prompts/`. To customize per-project:

```bash
cp -r ~/.xreview/prompts .xreview/prompts
# edit to taste — project-local prompts take priority
```

| File | Controls |
|------|----------|
| `reviewer.md` | What the reviewer focuses on and how it formats feedback |
| `digest.md` | How your agent processes feedback — guardrails against blind acceptance |
| `round2.md` | Follow-up round instructions — verify fixes, find new issues |

## What gets installed

```
~/.xreview/
  prompts/                          # reviewer, digest, round2 prompt templates
  bin/xreview-build-prompt          # assembles review prompt (<1s)
~/.claude/commands/xreview.md       # /xreview slash command (if Claude Code found)
~/.agents/skills/xreview/SKILL.md   # $xreview skill (if Codex found)
```

Project-local overrides go in `your-project/.xreview/prompts/`.

## FAQ

**Does this cost money?**
Each review is an API call via the reviewer's CLI. Same cost as using that CLI directly.

**Can I review with the same model?**
Yes — `self` spawns a fresh instance with zero session context.

**What if a reviewer CLI isn't installed?**
The agent reports it and continues with the others.

## Architecture Decisions

See [docs/architecture-decisions.md](docs/architecture-decisions.md).

## License

MIT
