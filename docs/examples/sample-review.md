# Example: xreview in action

## The plan

A developer working in Claude Code has just planned a rate-limiting middleware for their Express API. They run:

```
/xreview
```

No flags needed — it defaults to reviewing with a fresh instance of the same model (`self`).

## What the reviewer returns

```
### Critical Issues (must fix)

1. The plan stores rate-limit counters in application memory. This breaks
   immediately with multiple server instances behind a load balancer — each
   instance tracks its own counts independently. Use Redis or another shared
   store.

2. The sliding window implementation resets the full window on every request
   instead of sliding. A user who hits the limit at 11:59 can send another
   burst at 12:00. Use a proper sliding log or token bucket algorithm.

### Risks (should address)

3. No mention of how rate limits apply to authenticated vs. unauthenticated
   requests. The current plan applies the same limit to both using IP-based
   tracking, which means a legitimate user behind a corporate NAT could get
   throttled by other users sharing their IP.

4. The plan doesn't address what happens when Redis is unreachable. Fail-open
   (allow all traffic) or fail-closed (reject all)? Both have consequences.

### Suggestions (consider)

5. Consider returning standard rate-limit headers (X-RateLimit-Limit,
   X-RateLimit-Remaining, X-RateLimit-Reset) so API consumers can
   self-throttle.

6. The 429 response body is just "Too Many Requests". Include a
   Retry-After header and a JSON body with the reset timestamp.

### What's Good (keep)

- Clean middleware pattern — wrapping as Express middleware that can be
  applied per-route or globally is the right design.
- The plan correctly identifies that rate limiting should happen before
  authentication middleware in the chain.
- Test plan covers the key scenarios.

### Verdict: REVISE

Good direction on the middleware architecture, but the in-memory storage is
a showstopper for any production deployment, and the sliding window logic
has a concrete bug.
```

## How the digest processes it

The developer's agent doesn't blindly accept everything. It reads `.xreview/prompts/digest.md` and classifies each point:

| # | Feedback | Classification | Reasoning |
|---|----------|---------------|-----------|
| 1 | In-memory counters break with multiple instances | **Accept** | Verified — plan uses a plain JS `Map`. Switching to Redis. |
| 2 | Sliding window resets incorrectly | **Accept** | Read the pseudocode — reviewer is right, it's a fixed window labeled "sliding." |
| 3 | Auth vs unauth rate limits | **Partially accept** | Real concern, but the fix is simpler than suggested: use user ID when authenticated, IP when not. |
| 4 | Redis failure mode | **Accept** | Genuine gap. Will add fail-open with logging. |
| 5 | Standard rate-limit headers | **Accept** | Low effort, high value for API consumers. |
| 6 | Retry-After header | **Reject** | Already in the plan (Section 4.2). Reviewer missed it. |

The agent then produces an updated plan incorporating the accepted changes, and flags one open question for the developer: "Should authenticated users get a higher rate limit, or the same limit keyed differently?"
