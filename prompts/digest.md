You just received external review feedback on your plan from a separate AI agent
that reviewed it with fresh eyes and full codebase access.

DO NOT BLINDLY ACCEPT THE FEEDBACK.

The reviewer had less context than you. They reviewed the plan cold — they don't
know about constraints you discovered during this session, trade-offs you already
considered and rejected, or requirements that aren't written down.

FOR EACH PIECE OF FEEDBACK, CLASSIFY IT:

ACCEPT — The reviewer caught a genuine issue you missed. State what you'll
change and why they're right.

REJECT — The reviewer is wrong or the concern doesn't apply. Explain specifically
why — reference the codebase, a constraint they don't know about, or a trade-off
you already evaluated. Do not reject without concrete reasoning.

PARTIALLY ACCEPT — The reviewer identified a real concern but their suggested
fix isn't right. Take the signal, propose your own solution.

VERIFY EVERY FACTUAL CLAIM AGAINST THE CODEBASE.

If the reviewer says "file X doesn't handle case Y" — read the file right now.
The reviewer may have misread the code, or you may have genuinely missed something.
Do not argue from memory. Look at the actual code.

WATCH FOR THESE REVIEWER FAILURE MODES:

- Hallucinated concerns: The reviewer flags an issue that doesn't exist in the
  codebase. Always verify before acting.
- Scope creep: The reviewer suggests additions that are out of scope or
  nice-to-have. Don't let a review inflate the plan beyond its original goals.
- Preference disguised as problem: The reviewer says "I would do X instead"
  without a concrete reason why your approach is worse. That's a preference,
  not a bug. Acknowledge it but don't change the plan.
- Redundant with existing code: The reviewer suggests adding something that
  already exists. Check before adding duplicate logic.
- Over-engineering: The reviewer suggests abstractions or patterns that add
  complexity without proportional value for the current scope.

PRODUCE:

1. Feedback analysis — Each reviewer's points with your accept/reject/partial
   classification and concrete reasoning for each.
2. Updated plan — Incorporate accepted feedback. Clearly mark what changed
   and why.
3. Open questions — Anything the review surfaced that you can't resolve without
   more input from the developer.
