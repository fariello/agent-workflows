# Review findings: plan nomhl1

- Subject-Id: nomhl1
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed Order 01 of Set `commsbroker`: the payload-blind broker. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE semantic review, and
`--phase review-finalize` conforms after the revisions. The plan file was committed and unchanged at
review start (`git status --porcelain` empty; last touched by `c41b69fb`), so no pre-review snapshot
was needed. The Set's orchestrator (`u8tabj`) was reviewed immediately before this, so the
sequencing claims are already verified and are not re-derived here.

THIS REVIEW SPENT ITS EFFORT ON MEASUREMENT RATHER THAN READING, and that is what produced its
central finding. The plan's whole design rests on three OpenCode HTTP routes, and its own E-01 was
written as a status-code spike. Running that spike at review showed the status codes are NOT
sufficient evidence for the ack the broker would write. Everything in PR-001 below is a live
measurement of `opencode serve --pure` 1.18.32 in this worktree, pasted in the measurements section.

SEVEN FINDINGS, ALL FIXED IN PLACE. One is a BLOCKER that would have produced systematically false
acks (PR-001). Two are security findings on trust boundaries the plan crossed without noticing
(PR-002 untrusted identity into a filename, PR-003 redirect policy). Two are correctness bugs against
the shipped tree (PR-004 wrong comms-dir rule, PR-005 missing-lane crash). One is an idempotence
defect that would rewrite a file every ten seconds forever (PR-006). One is the deterministic
`error`-severity repository finding the plan actually carried (PR-007).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A (correctness) / E (verification) | MEASURED live at review, OpenCode 1.18.32, throwaway `opencode serve --pure` on a free port: `POST /tui/show-toast` -> `200 true` and `POST /tui/append-prompt` -> `200 true`, repeated 3x each, against a server with NO TUI attached; `GET /tui/control/next` (whose `/doc` description is "Retrieve the next TUI request from the queue for processing") BLOCKED to timeout both before and after those posts. Contrast: `POST /session` -> `200` + id, `POST /session/{id}/prompt_async` -> `204`, bogus session -> `404 NotFoundError`. | THE SPIKE'S STOP CONDITION COULD NOT CATCH THE FAILURE IT EXISTS FOR. E-01 said "STOP if any route ... returns a status other than the ones named" and expected `200, 200, 204`. Those are exactly the statuses a HEADLESS server with no TUI returns, so the spike would PASS and the broker would be built mapping `tui` success to the broker-authored ack `delivered` for nudges no agent ever saw. That is worse than not delivering: child 03 (`ozcfjr`) derives `unread` as "a `delivered` ack with no later `read` ack", so every phantom delivery becomes a false `unread`, and the ack layer the whole Set is built to aggregate is systematically wrong. The headless path does NOT share the defect - `prompt_async` returns `204` for a real session and `404` for a bogus one, so it verifiably reaches something - which is what makes a clean re-scope available instead of a replan. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-01 rewritten: the bar is now OBSERVABILITY, not a status code; `GET /tui/control/next` with no TUI attached is added as the DISCRIMINATING probe; the stop condition says explicitly that `200 true` does not establish delivery and names the measurement; and the stop path names HEADLESS-ONLY v1 as the legitimate re-scope rather than abandonment. E-03 may not map `tui` success to `delivered` unless E-01 established observability. E-07 must describe what actually shipped (keeping a Deferred bullet for attended-TUI if it did not). V-01 now REFUSES a paste of three status codes and demands the `control/next` observation. Recorded as OQ-02 carrying `- Finding: F-1a`, because narrowing a declared scope is the maintainer's call. |
| PR-002 | HIGH | IN-SCOPE | B (security) | `comms.ack_filename` interpolates its args with no validation and says so ("The caller is responsible for validating"); the comms spec: "Sender identity is self-asserted"; E-04 as written derived the ack `by` from "the target's `To:` project part" | UNTRUSTED, SELF-ASSERTED ENVELOPE TEXT FLOWED INTO A FILENAME. The broker's own ack identity was to be taken from the `To:` header, which is written by whoever authored the message. `comms.is_filename_safe` bounds the damage to a confusing name rather than a path escape (it rejects `..`, separators, control chars, drive letters), so this is not a traversal hole, but the ack layer would carry an attacker-chosen project label and the broker would be asserting an identity it was handed rather than one it owns. | C:Low; U:Low; S:Medium; F:Low; Overall:Low | FIXED | E-04 now takes the broker identity from an OPERATOR-supplied `--broker-id <proj.agent>` (default `aw.comms-broker`), validated once at startup with `comms.is_filename_safe` and exiting 2 on failure, and NEVER read from a message. `msg_id` is also passed through `is_filename_safe` before interpolation, since it too comes from disk. E-06 adds a hostile-`To:`-label test and a refused-`--broker-id` test; V-04 demands both. Recorded as F-5. |
| PR-003 | HIGH | IN-SCOPE | B (security) | `run_analytics_submit.RefusingRedirectHandler` and its docstring ("a server answering `302 Location: file:///etc/passwd` hands the new url back through the redirect machinery"); E-03 said only "an opener with redirects disabled" | THE URL POLICY WAS AN ENTRY-POINT CHECK WITH NO REDIRECT STORY, in a repo that already learned this lesson once and wrote the fix down. "Redirects disabled" is not specific enough to verify, and a loopback server answering `302 Location: http://evil/` is precisely the case a single entry check misses. The plan also told the executor to reuse `oc_models._LOOPBACK_HOSTS`, another module's underscore-private name, where the in-repo precedent (`run_analytics_submit`) keeps its own copy. | C:Low; U:Low; S:Medium; F:Low; Overall:Low | FIXED | Split out as new E-09: a `url_policy_refusal(url)` predicate called before any socket opens, reused by the redirect handler so EVERY redirect target is re-checked, following `RefusingRedirectHandler`. The loopback set is COPIED, not imported. The docstring must record the measured limit: this is a literal-host check, so `localhost.localdomain` (resolves `::1`) and `127.1` (resolves `127.0.0.1`) are REFUSED - conservative, not permissive - and DNS rebinding is out of scope and now an explicit Deferred row. New V-09 demands the redirect case. |
| PR-004 | MEDIUM | IN-SCOPE | A (correctness) | `engine.resolve_target_layout` (`.aw/system` -> `aw`, else `.agents/workflows` -> `legacy`, else `aw`), `engine._record_scaffold_dirs`, `engine.detect_split_brain_layout` | THE COMMS-DIR RULE WAS MISDESCRIBED AS A FALLBACK. E-05 said resolve `.aw/records/comms` "falling back to `.agents/comms` exactly as `engine` chooses". `engine` does no such probe: it selects on LAYOUT, and `.aw/system` WINS when both trees exist. An existence-probe fallback would pick the wrong lane in a split-brain repo, and `detect_split_brain_layout` exists precisely because that state occurs, so the misdescription would send the broker to read an inbox nobody writes to. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now names `engine.resolve_target_layout` and `engine._record_scaffold_dirs` and says to CALL them rather than reimplement a probe, with the reason (split-brain) recorded. |
| PR-005 | MEDIUM | IN-SCOPE | A (correctness) / F (silent failure) | MEASURED: `.aw/records/comms/` in this worktree contains only `README.md` and `shared/`; `untracked/` is ABSENT. `engine` creates `COMMS_UNTRACKED_SUBDIRS` as an install side effect only, and the lane is gitignored by `records/*/untracked/`. | THE BROKER WOULD CRASH ON A FRESH CLONE. Every scan path assumed `untracked/inbox/` and `untracked/acks/` exist, but the lane is gitignored by construction, so a clone has neither - demonstrated in the very worktree this review ran in. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now treats a missing `untracked/inbox/` or `untracked/acks/` as ZERO MESSAGES (not an error), creates `untracked/acks/` on first write with `mkdir(parents=True, exist_ok=True)`, and must exit 0 having done nothing. E-06 adds the no-lane case; V-05 demands the exit code. Recorded as F-6. |
| PR-006 | MEDIUM | IN-SCOPE | A (idempotence) | `comms.ack_filename` is a pure function of `(msg_id, from_agent, state)`, so a re-scan writes the SAME path; E-05 `--interval` default is 10 seconds | A NOT-YET-DUE MESSAGE WOULD HAVE ITS `scheduled` ACK REWRITTEN EVERY TEN SECONDS FOREVER. E-04 skipped a message already acked `delivered` or `expired` but said nothing about `scheduled`, and since the filename is deterministic the write is a silent rewrite of the same file on every poll for the whole waiting period. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now skips when that exact ack path already exists, extending the idempotence `delivered`/`expired` already had. V-04 demands two consecutive `scan_once` calls leave `st_mtime_ns` UNCHANGED. The legitimate two-acks-per-delivery case (`queued` then the result) is stated so it is not later mistaken for this bug. |
| PR-007 | HIGH | IN-SCOPE | G / repository rule | `check_engine.evaluate_durable_carrier` on this file -> 1 finding `check.ipd-uncarried-obligation` severity `error`; `carrier_severity_for_plan` -> `error` (Date 2026-09-24 > `CARRIER_CUTOVER_DATE` 20260919) | OQ-01 CARRIED NO DURABLE CARRIER, so the plan failed an `error`-severity repository rule. Once it reached `executed` it would class `done` in `aw attention` and the question would vanish with no record. Identical to the defect found in the parent `u8tabj`; the two remaining children carry it too. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- Carrier-Declined:` added to OQ-01, and the newly authored OQ-02 carries one from the start. Re-measured: 1 -> 0 findings. Children 02 and 03 not touched (D-1 of the parent review). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001 shows the `tui` branch may be unbuildable on current evidence. Is that a REPLAN, or a repairable plan? | Repairable. Keep the plan, harden the spike into an observability gate, and name headless-only as the re-scope its stop path produces. | (a) `REJECT - NEEDS REPLAN`. Rejected: the plan's structure, payload-blind invariant, ack discipline and headless path are all sound, and a replan would rewrite them unchanged. (b) Narrow the plan to headless-only NOW. Rejected: that decides a scope question on one review probe, when a real attached TUI may behave differently. | The headless path verifies independently (`prompt_async` `204` real / `404` bogus), so a sound v1 exists under either spike outcome; `plan-review` Step 2.4 reserves REPLAN for an approach "fundamentally unsound and ... not repairable with bounded edits". | yes |
| D-2 | Should the review DECIDE headless-only, given it measured the TUI routes discarding nudges? | No. Record OQ-02 with the measurement, the recommendation (yes, headless-only), and `Blocking: no`. | Raising it `Blocking: yes` to force a human answer before execution. Rejected: it needs no answer before the run, because E-01 PRODUCES the deciding evidence and its stop path already names the re-scope, so nothing is silently assumed either way. | Narrowing a declared scope is a maintainer call (scope is explicitly the human's per AGENTS.md); the 2026-09-10 ruling makes a non-blocking question not-a-NO-GO; and the question is escalated as `- Finding: F-1a` so the join is machine-readable. | yes |
| D-3 | The URL policy fix could extend E-03 or become its own E-item. Which? | Its own E-item (E-09), sequenced before E-03 consumes it. | Extending E-03. Rejected: E-03 already carries mode-aware delivery plus outcome-to-ack mapping, and the plan's own right-sizing rule says to split when an item names multiple deliverables or independent test-surfaces - the URL policy has its own test surface (V-09). | The plan's stated right-sizing rule; `run_analytics_submit` keeps `url_policy_refusal` as a separate predicate reused by the redirect handler, which is the shape being copied. | yes |
| D-4 | E-09 needs an id. Reuse a letter suffix (`E-03b`) to keep it beside E-03? | No. Allocate `E-09` and raise `- Highest E allocated:` to 09. | `E-03b`. Rejected after MEASURING it: `ipd_schema.E_ID_STRICT` is `^E-[0-9]{2,}$`, so `E-03b` does not match and `aw ipd lint` refused it with `IPD-I302` at line 53. | Measured directly by running the linter on the edit, which failed; the reordering is expressed by `Depends on:` edges rather than by id order, so a high id early in the file is correct. | yes |
| D-5 | Should this review fix the same uncarriered-OQ error in children 02 and 03, which both carry it? | No. Fix it here; it stays a finding against them. | Fixing all three children. Rejected: they are not in this review's ledger, and a reviewer editing a plan it did not review leaves a diff with no findings record behind it. | `plan-review` Step 0.1 (the ledger is the named target plus documented additions; evidence-only files are out of scope); consistent with D-1 of the `u8tabj` review. | yes |

### Measurements taken at review

```text
aw ipd lint --phase author           --agent nomhl1 -> {"outcome":"clean","exit":0,"findings":0}
aw ipd lint --phase review-finalize  --agent nomhl1 -> {"outcome":"clean","exit":0,"findings":0}  (after revisions)
ipd_lint.lint_text(review-finalize)  -> conforming, 0 diagnostics, 0 advisories (no density advisory fired)

check_engine.evaluate_durable_carrier(nomhl1)  BEFORE -> 1 finding, severity error (OQ-01)
                                                AFTER -> 0 findings
carrier_severity_for_plan(nomhl1) -> error   (Date 2026-09-24 > CARRIER_CUTOVER_DATE 20260919)

--- LIVE OpenCode measurement, the basis of PR-001. opencode --version: 1.18.32
--- throwaway `opencode serve --pure --port <free>`, disposed after each probe set.

GET /global/health              -> 200 {"healthy":true,"version":"1.18.32"}
GET /path                       -> 200 {... "directory": <this worktree> ...}

WITH NO TUI ATTACHED (3 repetitions each):
POST /tui/show-toast            -> 200 true      (x3)
POST /tui/append-prompt         -> 200 true      (x3)
POST /tui/submit-prompt         -> 200 true
GET  /tui/control/next          -> BLOCKED to timeout, drainer started BEFORE the posts
GET  /tui/control/next          -> BLOCKED to timeout, drainer started AFTER the posts
   => the 200 is an accept-and-discard on this evidence; nothing queued for a TUI.

THE ROUTES DO VALIDATE (so the 200 is "well-formed", not "delivered"):
POST /tui/show-toast variant="bogus"   -> 400 BadRequest, 'Expected "info" | "success" | ...'
POST /tui/show-toast missing message   -> 400 BadRequest, 'Missing key at ["message"]'
POST /tui/append-prompt extra property -> 200 true   (despite /doc additionalProperties:false;
                                                      so /doc is not a guide to runtime strictness)

THE HEADLESS PATH IS VERIFIABLY REAL (the contrast that makes re-scope possible):
POST /session                                  -> 200 {"id":"<a real session id>","slug":...}
POST /session/<that real id>/prompt_async      -> 204 (empty)
POST /session/<a nonexistent id>/prompt_async  -> 404 {"name":"NotFoundError",...}

/doc route inventory (1.18.32): /tui/show-toast 200,400 | /tui/append-prompt 200,400 |
  /tui/submit-prompt 200,400 | /session/{sessionID}/prompt_async 204,400,404 |
  /global/health 200,400 | /path 200,400 | /session GET+POST 200,400 |
  /tui/select-session 200,400,404  (present, and returned 404 for a bogus session id)
/doc security: components.securitySchemes = null, top-level security = []   (OQ-01's evidence)
server log: "Warning: OPENCODE_SERVER_PASSWORD is not set; server is unsecured."

--- Tree facts the revisions rest on
comms.py exports            BROKER_ACK_STATES, AGENT_ACK_STATES, ACK_WRITER, ACK_STATES,
                            validate_ack, ack_filename, ack_writer_for, parse_not_before,
                            is_filename_safe, parse_envelope_header, validate_envelope_header
                            and NO writer of any kind
tests/ comms coverage       NONE (ls tests/ | grep -i comms -> empty); tests/test_comms.py was
                            deleted in 19313eed "test: trim test suite from 9,136 to under 2,000"
                            => this plan is the FIRST consumer of those helpers (F-4)
.aw/records/comms/          README.md + shared/ ONLY; untracked/ ABSENT  (PR-005)
COMMS_UNTRACKED_SUBDIRS     ("inbox","sent","archive","scheduled","acks"), created by engine as an
                            install SIDE EFFECT only
engine layout rule          resolve_target_layout: .aw/system -> "aw"; .agents/workflows -> "legacy";
                            neither -> "aw"    (PR-004; NOT an existence fallback)
detect_split_brain_layout   exists, so the both-trees state is real
oc_models._LOOPBACK_HOSTS       {"127.0.0.1","::1","[::1]","localhost"}
run_analytics_submit._LOOPBACK  {"127.0.0.1","::1","localhost"}   (keeps its OWN copy: the precedent)
urlsplit("http://[::1]:99/x").hostname == "::1"   (brackets already stripped)
localhost.localdomain -> ::1 ; 127.1 -> 127.0.0.1  (both REFUSED by a literal-host set: conservative)
ipd_schema.E_ID_STRICT      ^E-[0-9]{2,}$          (D-4: rules out "E-03b")

backlog ifeyjv              graduated, Graduated-To: commsbroker, NO Blocks-Release
                            evaluate_blocking_close(..., "done") -> legitimate=True, path=DE-GATED
review_findings._resolved_escalated_questions(nomhl1) -> {'F-1a': ('OQ-02','open')}
                            (the escalation join resolves; still open, so not stale)
```

### Verdict and readiness

APPROVE WITH REVISIONS APPLIED. PR-001 through PR-007 all FIXED, none deferred, none open. The
BLOCKER was repaired by hardening the spike's stop condition rather than by narrowing scope, so both
outcomes are now owned inside the plan. OQ-01 and OQ-02 are both `Blocking: no` with recorded
recommendations and durable carriers, which under the 2026-09-10 maintainer ruling does not make the
plan `NO-GO`.

Readiness `go-pending-approval`. Three things a human should know before approving. FIRST, there is a
real chance this plan ships HEADLESS-ONLY: on this review's measurement the attended-TUI routes accept
and discard, and E-01 is now a genuine stop on that point (OQ-02 records the recommendation). SECOND,
E-01 starts a real local `opencode serve --pure` on a free port and makes live HTTP calls to it; no
test does, and no human's instance is ever targeted. THIRD, this plan is the first and only consumer
of `comms.py`'s ack helpers, which currently have zero test coverage, so its own tests are the only
thing exercising them.
