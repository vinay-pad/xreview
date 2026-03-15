Send a plan or file to another AI coding agent for independent review, then critically analyze their feedback.

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
- `--reviewer <list>` — comma-separated: `codex`, `claude`, `self`, `inline`. Defaults to `self` if omitted.
  - `self` = fresh instance of current model via subprocess (genuine independence, no sunk cost)
  - `codex` / `claude` = cross-model review via subprocess
  - `inline` = in-session review (fast, retains context, but less independent — use when speed matters more than rigor)
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
3. **Inline referenced code:** Scan the plan content for file paths (e.g., `src/foo.ts`, `lib/bar.py`, `path/to/file:123`). For each referenced file that exists, read it and include it in a `## Referenced Source Code` section with the file path as a heading and the contents in a fenced code block. This ensures the reviewer has the actual code without needing to browse the filesystem.

## Step 3: Build and send the review prompt

1. Read the reviewer prompt template: check `.xreview/prompts/reviewer.md` first (project-local), fall back to `~/.xreview/prompts/reviewer.md` (global).
2. Construct the full prompt in memory by combining:
   - The reviewer prompt template
   - A `## Codebase Context` section with the project structure, README excerpt, and package metadata from Step 2
   - A `## Plan Under Review` section with the full plan contents from Step 1
3. Resolve `self` to `claude` (since you are Claude).
4. For each reviewer:

   - **inline**: Perform the review directly in the current session. Read the reviewer prompt template, then adopt the independent reviewer role and produce the review yourself. This is fast and retains full conversation context, but less independent since you wrote the plan. After producing the review, continue to Step 4 as normal.

   - **codex**: Shell out via subprocess:
     ```bash
     codex exec -C "$PWD" --skip-git-repo-check - 2>/tmp/xreview-stderr.log <<'XREVIEW_EOF'
     [full prompt here]
     XREVIEW_EOF
     ```

   - **claude**: Shell out via subprocess:
     ```bash
     claude -p - --print 2>/tmp/xreview-stderr.log <<'XREVIEW_EOF'
     [full prompt here]
     XREVIEW_EOF
     ```

   If a subprocess produces no stdout, check `/tmp/xreview-stderr.log` for errors and report them to the user. If a CLI is not installed, report it and continue with the others.

## Step 4: Analyze the feedback

Read the digest prompt: check `.xreview/prompts/digest.md` first (project-local), fall back to `~/.xreview/prompts/digest.md` (global). Follow those instructions to process each reviewer's feedback.

In summary: do not blindly accept feedback. For each point, accept, reject with reasoning, or partially accept. Verify factual claims by reading actual code. Watch for hallucinated concerns, scope creep, preference-vs-problem, and over-engineering.

Present:
1. **Feedback analysis** — each point classified with reasoning
2. **Updated plan** — incorporating accepted feedback, marking what changed
3. **Open questions** — anything needing developer input

## Follow-up rounds

If the developer asks to send the updated plan back for another round:

1. Read the round2 prompt: check `.xreview/prompts/round2.md` first (project-local), fall back to `~/.xreview/prompts/round2.md` (global). Use it instead of the standard `reviewer.md`.
2. For **inline** reviewers: just proceed — the full history is already in the session.
3. For **cross-model subprocess** reviewers (`codex`, `claude`): construct the prompt with the round2 template plus:
   - `## Previous Review` — the reviewer's prior output
   - `## Author Response` — your Step 4 feedback analysis (accepted/rejected/partial with reasoning)
   - `## Updated Plan Under Review` — the revised plan
   - The same codebase context and referenced source code from Step 2
   This gives the fresh instance the full review history so it can track what was addressed and what wasn't.
4. Then repeat Steps 2-4.
