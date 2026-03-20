---
name: xreview
description: >
  Use when asked to cross-review, get a second opinion, or send a plan, spec, or code file to
  another AI reviewer. Applies to requests like "xreview", "$xreview", "fresh review",
  "independent review", "cross-review", or "get Claude/Codex to review this". If no file is specified, review the
  most recent plan or spec from the current conversation.
---

# Cross-Review with External AI Agent

Send a plan or file to another AI coding agent for independent review, then critically analyze their feedback.

## Usage

```text
$xreview
$xreview <file>
$xreview --reviewer <reviewers>
$xreview <file> --reviewer <reviewers>
$xreview <file> --reviewer <reviewers> --context <extra-files>
$xreview <file> --reviewer <reviewers> --no-codebase
```

For explicit invocation in Codex, use `/skills` and choose `xreview`, or type one of the commands above directly.

Supported arguments:

| Argument | Meaning | Default |
|----------|---------|---------|
| `file` | Optional plan, spec, or code file to review | Most recent plan/spec in the current conversation |
| `--reviewer` | Comma-separated: `claude`, `codex`, `self`, `inline` | `self` |
| `--context` | Comma-separated extra files to include | none |
| `--no-codebase` | Skip auto-including repo structure and metadata | off |

`self` = fresh instance of current model via subprocess (genuine independence, no sunk cost). `inline` = in-session review (fast but less independent).

## When to Use

- User asks to cross-review, get a second opinion, or get external feedback on a plan
- User mentions sending work to Claude or a fresh Codex instance
- User says `xreview`, `$xreview`, `fresh review`, `cross-review`, or similar
- User wants to review the most recent in-session plan without saving it to a file first

## Arguments

Parse the user's request for:
- **file** — optional. The plan, spec, or code file to review. If not specified, use the most recent plan from the current conversation.
- **reviewers** — which agents: `claude`, `codex`, `self`, `inline`. `self` = fresh subprocess of current model. Defaults to `self` if not specified.
- **context files** — any additional files to include
- **no-codebase** — whether to skip codebase structure

## Timing

You MUST track wall-clock time at each step boundary so the user can see where time goes. At the start of each step, run:
```bash
python3 -c 'import time; print(f"{time.time():.3f}")'
```
Record the output as `t0` (start of step 1), `t1` (start of step 2), `t2` (end of step 2 / start of step 3), and `t3` (end of step 3). In the final output, compute and report:
- **Step 1 (plan + prompt assembly):** `t1 - t0` seconds
- **Step 2 (reviewer call):** `t2 - t1` seconds
- **Step 3 (digest):** `t3 - t2` seconds
- **Total:** `t3 - t0` seconds

This is mandatory. Do not skip timing even if the review succeeds.

## Step 1: Get the plan and build the review prompt

Run `python3 -c 'import time; print(f"{time.time():.3f}")'` and record the result as `t0`.

**If a file is specified:** Use that file path as the plan.

**If no file is specified:** Look back through the current conversation and identify the most recent plan, spec, proposal, or technical design you produced. Write it to a unique temp file:
```bash
PLAN_FILE=$(mktemp /tmp/xreview-plan.XXXXXX.md)
cat > "$PLAN_FILE" <<'PLAN_EOF'
[paste the full plan content here]
PLAN_EOF
```

Then build the review prompt using the helper script and capture the returned path:
```bash
PROMPT_FILE=$(~/.xreview/bin/xreview-build-prompt \
  --plan <file-or-$PLAN_FILE> \
  --cwd "$PWD" \
  [--context <extra-files>] \
  [--no-codebase])
```

This prints the path to a temp file containing the assembled prompt (reviewer instructions + project structure + plan). It runs in <1s. You MUST capture the output into `PROMPT_FILE` and use that variable in all subsequent commands.

Resolve `self` to `codex` (since you are Codex).

## Step 2: Send for review

Run `python3 -c 'import time; print(f"{time.time():.3f}")'` and record the result as `t1`.

For each reviewer, use `$PROMPT_FILE` (the path captured from `xreview-build-prompt`):

- **inline**: Read the reviewer prompt template (`.xreview/prompts/reviewer.md` or `~/.xreview/prompts/reviewer.md`), then adopt the independent reviewer role and produce the review yourself. This is fast and retains full conversation context, but less independent since you wrote the plan. Skip to Step 3.

- **claude**: Call the CLI directly:
  ```bash
  claude -p - --print 2>/tmp/xreview-stderr.log < "$PROMPT_FILE"
  ```

- **codex** (fresh instance): Call the CLI directly:
  ```bash
  codex exec -C "$PWD" --skip-git-repo-check - 2>/tmp/xreview-stderr.log < "$PROMPT_FILE"
  ```

If a subprocess produces no stdout, check `/tmp/xreview-stderr.log` for errors and report them to the user. If a CLI is not available, report it and continue.

Clean up temp files after use (only delete files YOU created, never the user's original plan file):
```bash
rm -f "$PROMPT_FILE"
```
If you created a temp plan file with `mktemp` in Step 1, also delete that: `rm -f "$PLAN_FILE"`. Do NOT delete a user-supplied file path.

## Step 3: Analyze the feedback

Run `python3 -c 'import time; print(f"{time.time():.3f}")'` and record the result as `t2`.

Read the digest prompt: check `.xreview/prompts/digest.md` first (project-local), fall back to `~/.xreview/prompts/digest.md` (global). Follow those instructions to process each reviewer's feedback.

In summary: do not blindly accept feedback. For each point, accept, reject with reasoning, or partially accept. Verify factual claims by reading actual code. Watch for hallucinated concerns, scope creep, preference-vs-problem, and over-engineering.

Present:
1. **Feedback analysis** — each point classified with reasoning
2. **Updated plan** — incorporating accepted feedback, marking what changed
3. **Open questions** — anything needing developer input
4. **Timing** — Run `python3 -c 'import time; print(f"{time.time():.3f}")'` and record the result as `t3`. Compute and report the full timing breakdown as described in the Timing section above. Always include this.

## Follow-up rounds

If the user asks to send the updated plan back for another round:

1. For **inline** reviewers: just proceed — the full history is already in the session.
2. For **cross-model subprocess** reviewers (`codex`, `claude`):
   - Write the updated plan to a temp file
   - Run `~/.xreview/bin/xreview-build-prompt --plan <updated-plan> --cwd "$PWD" --template round2.md` to get the base prompt with the round2 template
   - Append to that prompt file:
     - `## Previous Review` — the reviewer's prior output
     - `## Author Response` — your Step 3 feedback analysis (accepted/rejected/partial with reasoning)
   This gives the fresh instance the full review history so it can track what was addressed and what wasn't.
3. Then repeat Steps 2-3.

## Common Mistakes

- Do not require a file path if the conversation already contains a clear plan or spec.
- `self` resolves to a fresh subprocess of the current model (`codex` in Codex, `claude` in Claude). Do not resolve `self` to `inline`.
- Do not blindly accept reviewer feedback; always classify it and verify factual claims against the actual code or plan.
- Do not skip the codebase context unless the user explicitly asks for `--no-codebase`.
- Do NOT manually construct the review prompt — always use `xreview-build-prompt` to assemble it. This is critical for performance.

## Red Flags

- "I need a file before I can review this" when there is already a recent in-session plan
- "self probably means the other CLI"
- "The reviewer said it, so I'll just update the plan"
- "This is just a quick review, I can skip the digest step"
- Building the prompt by concatenating strings in your response instead of calling `xreview-build-prompt`
