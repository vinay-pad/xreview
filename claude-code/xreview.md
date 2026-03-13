Send a plan or file to another AI coding agent for adversarial review, then critically analyze their feedback.

## Usage
```
/xreview
/xreview <file>
/xreview --reviewer <reviewers>
/xreview <file> --reviewer <reviewers>
/xreview <file> --reviewer <reviewers> --context <extra-files>
/xreview <file> --reviewer <reviewers> --no-codebase
```

## Arguments
- `<file>` — optional. The plan, spec, or code file to review. If omitted, use the most recent plan from the current conversation.
- `--reviewer <list>` — comma-separated: `codex`, `claude`, `self` (self = fresh instance of current model). Defaults to `self` if omitted.
- `--context <files>` — optional comma-separated additional context files
- `--no-codebase` — skip auto-including codebase tree

Parse $ARGUMENTS to extract these values.
If `--reviewer` is not specified in $ARGUMENTS, default to `self`.

---

## Step 1: Get the plan

**If a file is specified:** Read it in full.

**If no file is specified:** Look back through the current conversation and identify the most recent plan, spec, proposal, or technical design you produced. Extract it completely — including all sections, implementation details, and decisions. Hold it in memory as the plan content. If you cannot identify a clear plan in the conversation, ask the developer which part of the conversation to use.

## Step 2: Gather context

1. Unless `--no-codebase` is passed:
   - Run `find . -type f -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/__pycache__/*' -not -path '*/venv/*' -not -path '*/.venv/*' -not -path '*/dist/*' -not -path '*/build/*' -not -path '*/.next/*' | head -200` for project structure.
   - Read README.md if it exists (first 200 lines).
   - Read package.json, pyproject.toml, or Cargo.toml if they exist.
2. Read any files passed via `--context`.

## Step 3: Build and send the review prompt

1. Read the reviewer prompt template from `.xreview/prompts/reviewer.md`.
2. Construct the full prompt in memory by combining:
   - The reviewer prompt template
   - A `## Codebase Context` section with the project structure, README excerpt, and package metadata from Step 2
   - A `## Plan Under Review` section with the full plan contents from Step 1
3. Resolve `self` to `claude` (since you are Claude).
4. For each reviewer, pipe the prompt via stdin using your Bash tool:

   - **codex**: `codex exec -C "$PWD" --skip-git-repo-check - <<'XREVIEW_EOF' ... XREVIEW_EOF`
   - **claude**: `claude -p - --print <<'XREVIEW_EOF' ... XREVIEW_EOF`

   Use a heredoc to pass the full prompt:

   ```bash
   codex exec -C "$PWD" --skip-git-repo-check - 2>/tmp/xreview-stderr.log <<'XREVIEW_EOF'
   [full prompt here]
   XREVIEW_EOF
   ```

   If the command produces no stdout, check `/tmp/xreview-stderr.log` for errors and report them to the user.

Call reviewers one at a time. If a CLI is not installed, report it and continue with the others.

Redirect stderr to `/tmp/xreview-stderr.log` to keep output clean. If the command returns empty stdout, read the stderr log and report the error to the user.

## Step 4: Analyze the feedback

Read the digest prompt from `.xreview/prompts/digest.md`. Follow those instructions to process each reviewer's feedback.

In summary: do not blindly accept feedback. For each point, accept, reject with reasoning, or partially accept. Verify factual claims by reading actual code. Watch for hallucinated concerns, scope creep, preference-vs-problem, and over-engineering.

Present:
1. **Feedback analysis** — each point classified with reasoning
2. **Updated plan** — incorporating accepted feedback, marking what changed
3. **Open questions** — anything needing developer input

## Follow-up rounds

If the developer asks to send the updated plan back for another round, read `.xreview/prompts/round2.md` and prepend it to the reviewer prompt instead of the standard reviewer.md. Then repeat Steps 2-4.
