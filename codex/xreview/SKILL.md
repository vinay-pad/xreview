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

## Step 1: Get the plan

**If a file is specified:** Read it in full.

**If no file is specified:** Look back through the current conversation and identify the most recent plan, spec, proposal, or technical design you produced. Extract it completely — including all sections, implementation details, and decisions. Hold it in memory as the plan content. If you cannot identify a clear plan in the conversation, ask the user which part of the conversation to use.

## Step 2: Gather context

1. Unless `--no-codebase` is requested:
   - Run `find . -type f -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/__pycache__/*' -not -path '*/venv/*' -not -path '*/.venv/*' -not -path '*/dist/*' -not -path '*/build/*' -not -path '*/.next/*' | head -200` for project structure.
   - Read README.md if it exists (first 200 lines).
   - Read package.json, pyproject.toml, or Cargo.toml if they exist.
2. Read any files passed via `--context`.
3. **Inline referenced code:** Scan the plan content for file paths (e.g., `src/foo.ts`, `lib/bar.py`, `path/to/file:123`). For each referenced file that exists, read it and include it in a `## Referenced Source Code` section with the file path as a heading and the contents in a fenced code block. This ensures the reviewer has the actual code without needing to browse the filesystem.

## Step 3: Build and send the review prompt

1. Read the reviewer prompt template: check `.xreview/prompts/reviewer.md` first (project-local), fall back to `~/.xreview/prompts/reviewer.md` (global).
2. Construct the full prompt in memory by combining:
   - The reviewer prompt template
   - A `## Codebase Context` section with structure, README, and package metadata from Step 2
   - A `## Plan Under Review` section with the full plan contents from Step 1
3. Resolve `self` to `codex` (since you are Codex).
4. For each reviewer:

   - **inline**: Perform the review directly in the current session. Read the reviewer prompt template, then adopt the independent reviewer role and produce the review yourself. This is fast and retains full conversation context, but less independent since you wrote the plan. After producing the review, continue to Step 4 as normal.

   - **claude**: Use the `claude-code` MCP tool (preferred) or fall back to subprocess.
     - **MCP (fast):** Call the `claude-code` MCP tool with the full review prompt. This uses a warm Claude instance — no cold start.
     - **Subprocess (fallback):** If the MCP tool is not available, shell out:
       ```bash
       claude -p - --print 2>/tmp/xreview-stderr.log <<'XREVIEW_EOF'
       [full prompt here]
       XREVIEW_EOF
       ```

   - **codex** (fresh instance): Shell out via subprocess:
     ```bash
     codex exec -C "$PWD" --skip-git-repo-check - 2>/tmp/xreview-stderr.log <<'XREVIEW_EOF'
     [full prompt here]
     XREVIEW_EOF
     ```

   If a subprocess produces no stdout, check `/tmp/xreview-stderr.log` for errors and report them to the user. If a CLI or MCP tool is not available, report it and continue.

## Step 4: Analyze the feedback

Read the digest prompt: check `.xreview/prompts/digest.md` first (project-local), fall back to `~/.xreview/prompts/digest.md` (global). Follow those instructions to process each reviewer's feedback.

In summary: do not blindly accept feedback. For each point, accept, reject with reasoning, or partially accept. Verify factual claims by reading actual code. Watch for hallucinated concerns, scope creep, preference-vs-problem, and over-engineering.

Present:
1. **Feedback analysis** — each point classified with reasoning
2. **Updated plan** — incorporating accepted feedback, marking what changed
3. **Open questions** — anything needing developer input

## Follow-up rounds

If the user asks to send the updated plan back for another round:

1. Read the round2 prompt: check `.xreview/prompts/round2.md` first (project-local), fall back to `~/.xreview/prompts/round2.md` (global). Use it instead of the standard `reviewer.md`.
2. For **inline** reviewers: just proceed — the full history is already in the session.
3. For **cross-model subprocess** reviewers (`codex`, `claude`): construct the prompt with the round2 template plus:
   - `## Previous Review` — the reviewer's prior output
   - `## Author Response` — your Step 4 feedback analysis (accepted/rejected/partial with reasoning)
   - `## Updated Plan Under Review` — the revised plan
   - The same codebase context and referenced source code from Step 2
   This gives the fresh instance the full review history so it can track what was addressed and what wasn't.
4. Then repeat Steps 2-4.

## Common Mistakes

- Do not require a file path if the conversation already contains a clear plan or spec.
- `self` resolves to a fresh subprocess of the current model (`codex` in Codex, `claude` in Claude). Do not resolve `self` to `inline`.
- Do not blindly accept reviewer feedback; always classify it and verify factual claims against the actual code or plan.
- Do not skip the codebase context unless the user explicitly asks for `--no-codebase`.

## Red Flags

- "I need a file before I can review this" when there is already a recent in-session plan
- "self probably means the other CLI"
- "The reviewer said it, so I'll just update the plan"
- "This is just a quick review, I can skip the digest step"
