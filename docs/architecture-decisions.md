# Architecture Decisions

This file tracks the major architecture decisions for `xreview`, why they were made, and what tradeoffs they created.

## 2026-03-15: Keep a local daemon for warm reviewer transports

Status: Superseded by 2026-03-17 decision below

Context:
- Cold-starting reviewer CLIs on every request was too slow for normal `xreview` use.
- The project needed a faster default path without introducing extra package dependencies or a larger service footprint.

Decision:
- Keep a local `xreviewd` daemon and route review requests through `xreviewctl`.
- For Claude, keep a warm spare worker per `cwd`.
- For Codex, keep a long-lived `codex app-server` process and create ephemeral threads per review.

Consequences:
- This reduces CLI process startup overhead, but it does not reduce the model's own review latency.
- The first review is still effectively cold.
- Fixed-port daemon startup and weak stderr/error propagation can turn ordinary startup failures into long timeouts.
- Observability is part of the architecture now; daemon logs and startup diagnostics are required, not optional.

## 2026-03-15: Track architecture decisions in-repo

Status: Accepted

Context:
- Important design choices and reversals were being explained in chat but not captured in the repository.
- That made it too easy to repeat failed experiments or forget why a redesign happened.

Decision:
- Record architecture decisions in `docs/architecture-decisions.md`.
- Add new entries when a design meaningfully changes system behavior, operability, or performance expectations.

Consequences:
- Future reviews can validate changes against written intent instead of reconstructing history from memory.
- Performance work must state which latency source it is targeting: process startup, transport/session setup, or model generation time.

## 2026-03-17: Replace daemon with prompt builder + direct CLI calls

Status: Accepted

Context:
- Instrumented timing of the full `/xreview` flow revealed the daemon saved ~0.3s on a 417s flow.
- The real bottlenecks were: host LLM spending ~116s assembling the prompt token-by-token, and the reviewer model itself (~220s).
- The daemon added a hardcoded 180s backend timeout that silently killed legitimate reviews, plus port-binding failures that masked real errors.

Decision:
- Remove the daemon from the default review path. Slash commands call `codex exec` / `claude -p` directly.
- Move prompt assembly (reviewer template + codebase context + referenced source code + plan) into a shell script (`xreview-build-prompt`) that runs in <1s.
- Keep the daemon code in the repo but do not route through it by default.

Consequences:
- Eliminates the 116s host-agent prompt-assembly overhead.
- Eliminates daemon startup failures, port conflicts, and timeout mismatches.
- Review latency is now dominated by reviewer model inference time, which we cannot reduce without changing model or prompt size.
- The prompt builder is a shell script with no dependencies, so it works on any machine with bash.
