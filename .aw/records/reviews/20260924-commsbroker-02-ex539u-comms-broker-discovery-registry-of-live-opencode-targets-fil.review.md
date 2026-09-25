# Review: Comms broker discovery registry of live OpenCode targets (filesystem descriptor, mDNS optional)

- Subject-Id: ex539u
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims re-derived at HEAD `6d61a387`. The target plan was committed and unchanged, so the
pre-review snapshot was correctly skipped per Step 1. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE review and again at
`--phase review-finalize` after every revision.

A NOTE ON SCOPE, because the invocation was ambiguous. The lane-input file attached to this turn was
`plan-20260924-verdictread-01-xpta5g-...ipd.md`, a plan reviewed in the previous turn, while the
`/plan-review` command named `ex539u`. I reviewed the plan the COMMAND names, on the reasoning that the
explicit argument is the request and the attachment is a stale carry-over; `xpta5g` was already
reviewed and committed at `6d61a387` and re-reviewing it would produce a duplicate round. The ledger
therefore contains exactly one candidate, `ex539u`, and `xpta5g` is an incidental file rather than a
skipped candidate.

THIS PLAN'S MODULE DOES NOT EXIST YET, which shapes what review can and cannot verify.
`agent_workflows/comms_broker.py` is created by sibling `nomhl1` (Order 01, `reviewed`,
`go-pending-approval`), and `ex539u` correctly declares `- Item-Dependencies: executed:nomhl1`.
So every claim about the broker's internals is a claim about child 01's REVIEWED TEXT, and I checked
them there rather than against code. What I could verify directly, I did: `comms.is_filename_safe`
exists and rejects separators and traversal; `comms.BROKER_ACK_STATES` contains both
`agent-not-running` and `agent-not-responding`, and `comms.ack_writer_for` returns `broker` for each,
so E-03's two failure states are legitimately broker-authored under the spec's closed enum;
`import zeroconf` raises `ModuleNotFoundError`; `pyproject.toml` declares `dependencies =
["filelock>=3"]`; and the spec's Deferred bullet and Gitignore paragraph read exactly as the plan
quotes them. F-1, F-2 and F-3 all hold.

THE DOMINANT FINDING IS PR-901, AND IT IS A TRUST BOUNDARY THE PLAN CROSSED WITHOUT NAMING IT. This
plan introduces a SECOND way a URL enters the broker: not from the operator's command line, but from a
JSON file in `untracked/registry/`. That directory is gitignored and locally writable, so any local
process may drop an `<agent>.json` naming any loopback host and port, including an agent that has just
processed a hostile inbox message, and the spec's own "Untrusted-input stance (mandatory)" already
rules that locally-dropped content is unvetted with self-asserted identity. E-03 then makes TWO NEW
outbound HTTP calls from that value. Child 01 guards its single outbound call with
`url_policy_refusal` AND a `RefusingRedirectHandler` that re-checks every redirect target, and
`nomhl1`'s own review recorded the reason: "a redirect to a non-loopback target refused ... is the one
a bare entry check misses". E-03 named neither symbol. E-01 gestured at "the same check child 01
added" without naming it, which is not a citation an executor can implement against, and E-03 said
nothing at all. It also trusted registration-time validation for a file that may have been replaced
since. The fix needs no new mechanism, only the discipline of routing both calls through the shipped
predicate and opener and re-validating on read; what the plan lacked was the statement that this is
the whole safety story.

PR-902 IS SMALL IN CODE AND LARGE IN CONSEQUENCE, AND THIS REPOSITORY IS THE EXACT PLACE IT BITES.
F-1 records that `/path`'s 200 schema has required `directory` AND `worktree`; E-03 then compared
`directory` alone with no stated reason. I measured what that means here: `git worktree list` shows
THREE live worktrees of this repository running simultaneously, all sharing one `--git-common-dir`,
and each carries its own `.aw/records/comms` lane. So `worktree` is not a discriminator between two
lanes of one repo while `directory` is. Comparing the wrong key would let a broker running in one lane
nudge the OpenCode instance of another lane, which is precisely the cross-tree confusion the check
exists to prevent, and a reader who later "simplifies" the comparison to whichever key is handy
reintroduces it. The plan's choice is correct; its silence about why is the defect.

PR-903 IS AN UNDERSPECIFIED WRITE. E-04 says the broker "writes the resulting failure state as the
broker ack" and specifies neither what it attaches to nor how often. `comms.ack_filename(msg_id,
from_agent, state)` REQUIRES a msg-id, and a resolution failure is a property of the target rather than
of any one message, so the item as written does not determine what file to create. And child 01's
`--interval` defaults to 10 seconds, so a target down for an hour would rewrite the same ack about 360
times, against an invariant a SIBLING plan already pins ("a second `scan_once` on the same not-yet-due
message does NOT rewrite the `scheduled` ack (compare `st_mtime_ns`)"). Writing one ack per eligible
message with no rewrite reuses child 01's existing already-acked skip and adds no mechanism.

PR-904 IS A STALE DESCRIPTION OF A SIBLING'S CONTRACT. The plan's conventions bullet says the comms
directory is chosen by `".aw/records/comms"` for the aw layout and `".agents/comms"` for legacy, which
reads as a path fallback. Child 01's review explicitly corrected that formulation: `engine` selects on
LAYOUT via `engine.resolve_target_layout` and `engine._record_scaffold_dirs`, because a bare existence
probe picks the wrong lane in a repo carrying both trees, which is why `engine.detect_split_brain_layout`
exists. Carrying the superseded formulation into a dependent plan is how a corrected premise
propagates.

PR-905 IS AN UNSTATED RESIDUAL RISK, and I record it as a finding rather than fixing it because the fix
is out of proportion. Nothing in this plan establishes WHO wrote a descriptor; it establishes only that
the URL is loopback, reachable, healthy and serving this tree. That is a real limit and it deserves to
be named with its bound: a hostile descriptor can at most misdirect a CONTENT-FREE `NUDGE` to another
loopback server also serving this exact repo root, which is a lost or misdirected nudge and never a
payload disclosure, because child 01's payload-blind invariant means the broker never reads a payload.
Closing it properly would need a signature scheme or an OS permission model, neither of which a v1
registry should carry.

PR-906 IS RIGHT-SIZING AND THE GATE. The count lint passed at seven items and measures only structural
count. Three of the review's fixes have their own independent test surfaces and their own failure
modes, so they are now their own items rather than clauses bolted onto existing ones. The gate was one
paragraph with `Cohesion rationale: not required`; it said nothing about what a human is approving,
which matters here because the non-obvious part is that this plan adds an untrusted input to a
security-sensitive module, and it had no scope fence over a module where the difference between calling
child 01's policy and re-encoding it is the whole safety argument.

WHAT I VERIFIED AND LEFT ALONE, stated because most of this plan is sound. The filesystem-over-mDNS
choice is correct and well evidenced (F-2's two independent reasons: no stdlib client, and `--mdns`
binds 0.0.0.0 against child 01's loopback rule). The never-delete-a-stale-descriptor rule is right and
its Deferred row gives the right reason (the broker must not delete another party's files). The
gitignore claim is true in BOTH layouts and I probed it rather than assuming. The per-repo-root
registry bounds the flat `<agent>.json` naming, so no keying change is needed, and I recorded that so a
later reader does not "fix" it. The `directory`-mismatch mutation in V-05 was already a well designed
falsifiability proof. And the Set's orchestration is coherent: `u8tabj`'s child table maps `ssmov3`'s
IPD 4 to this plan explicitly and warns against reading the mapping from position.

CONTRACT CHECKS. `aw check release-gates --agent` reports `findings:0`. This plan carries NO
`- Blocks-Release:` and neither does backlog `lbhmi3`, and its `- Work-Kind:` is `feature`, so the
every-live-bug rule does not apply and no gate is owed or inherited; the gate now says so explicitly.
`- From-Backlog: lbhmi3` resolves to a `graduated` item and `- Item-Dependencies: executed:nomhl1`
resolves to the `reviewed` sibling. The spec amendment is legitimate per AGENTS.md and is declared in
`- Scope-Paths:`; the narrower constraint applies (`.aw/records/specs/README.md` forbids hand-editing a
spec's status or history), so E-09 is now body-only with the history line routed through
`aw specs note`. One finding this review INTRODUCED and then fixed: the new Deferred rows and OQ-01
owed durable carriers, which `evaluate_durable_carrier` reported at `error` severity; each now carries
a substantive `Carrier-Declined` and the predicate returns zero findings on this plan.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | HIGH | UNDER-SCOPE | B. Security and privacy / A. Correctness | E-03 as authored: "load the descriptor, then `GET <url>/global/health` ... and `GET <url>/path`" with no policy named; E-01 said only "loopback http(s) using the same check child 01 added"; `nomhl1` E-09 ships `comms_broker.url_policy_refusal` and a `RefusingRedirectHandler` and its review records "a redirect to a non-loopback target refused ... is the one a bare entry check misses"; `untracked/registry/` is gitignored (probed: `.aw/.gitignore:6 records/*/untracked/`) and locally writable; the spec's "Untrusted-input stance (mandatory)" rules locally-dropped content unvetted with self-asserted identity | A DESCRIPTOR IS UNTRUSTED INPUT AND E-03 OPENED TWO UNGUARDED SOCKETS TO IT. This plan introduces a second path by which a URL enters the broker: not the operator's command line but a JSON file any local process may write, including an agent that just processed a hostile inbox message. E-03 then makes TWO NEW outbound calls from that value while naming neither the loopback predicate nor the redirect-refusing opener child 01 exists to provide, so the registry path would sit OUTSIDE the policy that guards child 01's single call, and the redirect half is the one a bare entry check provably misses. It also trusted registration-time validation for a file that may have been replaced between `register` and `resolve_target`. | C:Low; U:Low; S:High; F:Low; Overall:Medium (the remedy is reuse plus re-validation; no new mechanism is designed) | FIXED | Added F-4 with the full trust analysis. Added a `## Goal` paragraph and a "ONE URL POLICY, TWO CALL SITES" paragraph in Proposed changes stating the rule once. E-01 now cites `url_policy_refusal` BY SYMBOL and forbids re-encoding the loopback set; E-03 calls it before any socket, uses child 01's redirect-refusing opener for both GETs, and RE-VALIDATES the descriptor on read. New E-08 adds four cases: non-loopback refused, redirect-to-non-loopback refused, on-disk replacement refused, plus the idempotence case; V-03 and V-08 require the fixture's ZERO-request count, because an unguarded resolver that connects then fails returns the same ack state as a guarded one that never connects. A Deferred row records the unclosed writer-authentication question with its bounded consequence. |
| PR-902 | MEDIUM | IN-SCOPE | A. Correctness / D. Anti-regression | F-1 records `/path`'s 200 schema as having required `directory` AND `worktree`; E-03 compared `directory` only, with no reason stated; measured at review: `git worktree list` shows THREE live worktrees of this repo, all sharing one `--git-common-dir`, each with its own `.aw/records/comms` lane | THE PLAN PICKED ONE OF TWO KEYS SILENTLY, IN THE ONE ENVIRONMENT WHERE THE CHOICE MATTERS MOST. `worktree` is identical across every lane of a repo while `directory` is per-lane, so comparing `worktree` would let a broker in one lane nudge another lane's OpenCode instance, which is exactly the cross-tree misdelivery the check exists to prevent. The plan's choice is right, but an unexplained choice between two required keys is one a later reader "simplifies" in either direction, and the mismatch test as specified (vary `directory`) would still pass under an implementation that wrongly compares `worktree`. | C:Low; U:Low; S:Medium; F:Low; Overall:Low | FIXED | Added F-5 with the three-worktree measurement. New E-04 fixes `directory` as authoritative, requires the reason in `resolve_target`'s docstring (two lanes share `worktree`, so matching on it would cross lanes), and records `worktree` as not-compared. V-04 requires a SIBLING fixture that serves a different `directory` with the SAME `worktree`, and states why a test varying only `directory` proves nothing. Added a "WHICH `/path` KEY DECIDES" paragraph to Proposed changes. |
| PR-903 | MEDIUM | IN-SCOPE | A. Correctness (idempotence) / C. Architecture | E-04: "writes the resulting failure state as the broker ack", with no msg-id and no frequency rule; `comms.ack_filename(msg_id, from_agent, state)` requires a msg-id and its docstring says "The caller is responsible for validating"; child 01's `--interval` default is 10 seconds; `nomhl1` E-06 pins "a second `scan_once` on the same not-yet-due message does NOT rewrite the `scheduled` ack (compare `st_mtime_ns`)" | THE NEW ACK WRITE IS UNDERSPECIFIED IN TWO WAYS, ONE OF WHICH IS NOT IMPLEMENTABLE AS WRITTEN. An ack is keyed on a MESSAGE, while a resolution failure is a property of the TARGET, so the item does not determine what file to create; an executor would have to invent a msg-id or synthesize one, and a synthesized id in a filename is the class of problem child 01's `--broker-id` fix exists to avoid. Separately, "on every scan" with a 10-second interval means a target down for an hour rewrites one ack about 360 times, which regresses an invariant a sibling plan in the same Set already pins for its own ack. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added F-6. New E-06 rules that a failure ack is written once per ELIGIBLE message the scan would have nudged (so it lands on a real msg-id and an unsent message gets no ack) and is never rewritten while in the same state, reusing child 01's existing already-acked skip rather than adding a second mechanism. V-06 requires both `st_mtime_ns` values, an `ls untracked/acks/` showing one file per message rather than per scan, and the ack filename showing a real message stem. Added a "WHAT A FAILURE ACK ATTACHES TO" paragraph. |
| PR-904 | LOW | IN-SCOPE | F. Honest documentation | Plan conventions bullet: "The comms directory is chosen per layout in `engine` (`comms_dir = \".aw/records/comms\"` for the aw layout, `\".agents/comms\"` for legacy)"; `nomhl1` E-05's review correction: `engine` selects on layout via `engine.resolve_target_layout` and `engine._record_scaffold_dirs`, and "a bare existence fallback picks the WRONG lane in a repo that has both trees (`engine.detect_split_brain_layout` exists precisely because that state occurs)" | A DEPENDENT PLAN CARRIES A FORMULATION ITS OWN DEPENDENCY'S REVIEW ALREADY CORRECTED. As written the bullet reads as a path fallback, which is the implementation child 01's review rejected by name. The consequence is not hypothetical: a repo carrying both `.aw/` and `.agents/` trees exists often enough that the toolkit ships a detector for it, and a fallback probe would pick the wrong comms lane, so the registry would be written to or read from a directory the broker does not scan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the conventions bullet to state the layout-selection rule with both symbols and the split-brain reason, and added two further bullets: one naming the four child 01 symbols this plan must reuse (so E-01/E-03 cite symbols rather than prose), and one stating the untrusted-descriptor stance. Added F-9 recording that child 01's contract is richer than the plan's references suggested, and a Scope-check note that a rename during child 01's execution would leave these citations stale. |
| PR-905 | LOW | IN-SCOPE | B. Security (an honest limit) | Nothing in E-01..E-04 establishes who wrote a descriptor; the defenses are `is_filename_safe(agent)`, the loopback URL policy, `/global/health` and the `/path` `directory` match; child 01's payload-blind invariant means the broker sends only a fixed `NUDGE` constant and never reads a payload | THE PLAN'S RESIDUAL RISK IS REAL, BOUNDED, AND UNSTATED. A reader cannot tell from the plan whether descriptor-writer authentication was considered and declined or simply not thought about, and the two read very differently to anyone assessing whether to enable the feature. The bound is what makes the decision defensible and it belongs on the record: a hostile descriptor can at most misdirect a CONTENT-FREE nudge to another loopback server that is also serving this exact repo root, so the worst outcome is a lost or misdirected interruption, never a payload disclosure. Closing it properly needs a signature scheme or an OS permission model, both far larger than a v1 registry. | C:Low; U:Low; S:Low; F:Low; Overall:Low (a disclosure, not a build) | FIXED | Added a Deferred row for descriptor-writer authentication stating why it is not attempted, the bounded consequence, and a substantive `Carrier-Declined` (the same trust level already governs every file in `untracked/`, and a signature scheme would be a new spec decision rather than deferred work from this plan). The gate's approval paragraph names it as the second of four things to weigh. |
| PR-906 | LOW | UNDER-SCOPE | G. Plan executability (right-sizing + execution contract) | Gate as authored: one paragraph plus `Cohesion rationale: not required`; original E-03 carried the resolver, the two verification calls, the key comparison and four failure mappings; original E-04 carried the `run` wiring and the ack write; original E-05 carried six test cases | THE GATE WAS MISSING MOST OF ITS REQUIRED ELEMENTS AND TWO ITEMS BUNDLED INDEPENDENT TEST SURFACES. The gate said nothing about what a human is approving, and the non-obvious part here is that the plan adds an UNTRUSTED INPUT to a security-sensitive module; it had no scope fence, which matters unusually much because the difference between calling child 01's URL policy and re-encoding it is the entire safety argument and a fence is what makes that reconcilable afterwards; no stop conditions, although this plan cannot even start without a module a sibling creates; and an unconditional finalize instruction. The bundling is the ordinary kind: the key decision needs a same-`worktree` sibling fixture, the ack rule needs an `st_mtime_ns` pair, and the trust cases need a request count, and none of those three evidences the others. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into ten items (new E-04, E-06, E-08), each with its own `V-*` for a 10:10 bijection; `Highest E allocated: 10`; E-10's dependency list completed. Substantive cohesion rationale explaining each split by its distinct evidence. Gate rewritten: a what-a-human-is-approving paragraph ranking four consequences; a per-symbol scope fence cross-referencing a new EXPLICITLY NOT IN SCOPE list; the honesty rule naming V-03/V-08, V-04 and V-06 with WHY each is fakeable; three stop conditions (`nomhl1` not executed, the URL policy absent, the ack states no longer broker-authored); the no-release-gate statement; and conditional runner/executor finalize ownership. E-09 made body-only with the `aw specs note` route. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The invocation attached `xpta5g` (already reviewed last turn) while the command named `ex539u`. Which is in scope? | `ex539u`, the plan the command names. | (a) Review `xpta5g` again - rejected: it was reviewed and committed at `6d61a387` in the previous turn, so a second round would duplicate a round and the gate reads only the CURRENT round, discarding nothing but adding nothing. (b) Review both - rejected: the attachment is a stale carry-over rather than a second request, and enumerating a plan that was never a candidate would violate the ledger rule. (c) Ask - rejected: the explicit command argument is unambiguous about intent. | The `/plan-review` command's literal argument; `xpta5g`'s committed review record and `- Status: reviewed` at this HEAD; plan-review Step 0.1 on ledger candidates | yes |
| D-2 | The descriptor's URL reaches two new outbound calls. Reuse child 01's policy, or write a registry-local check? | Reuse `url_policy_refusal` and the redirect-refusing opener, by symbol, at both call sites. | (a) Re-encode the loopback set inside `validate_descriptor` - rejected: two encodings of one policy is how they drift, and the repository already records the cost of a policy that existed in one place and not another (child 01's own redirect finding). (b) Validate only at `register` time - rejected: the descriptor lives in a locally-writable directory and may be replaced between registration and resolution, so registration-time validation proves nothing about the value actually used. (c) Skip the policy because the URL was validated once - the same rejection. | `nomhl1` E-09's symbol and its review's redirect finding; `untracked/registry/` gitignored and locally writable (probed); the spec's "Untrusted-input stance (mandatory)" | yes |
| D-3 | `/path` returns `directory` and `worktree`. Which decides? | `directory` is authoritative; `worktree` recorded and not compared, with the reason in the docstring. | (a) Compare `worktree` - rejected on measurement: three live worktrees of this repo share one `worktree` value, so it cannot distinguish two lanes and matching on it would permit cross-lane nudges. (b) Require BOTH to match - rejected: it adds no discrimination over `directory` alone (a matching `directory` implies the same lane) while making the check fail for any future OpenCode that reports `worktree` differently, so it is strictly more brittle for no gain. (c) Leave the choice unstated - rejected: an unexplained pick between two required keys is one a later reader reverses. | `git worktree list` showing three lanes sharing `--git-common-dir`, each with its own `.aw/records/comms`; F-1's record of both required keys | yes |
| D-4 | A resolution failure is not per-message but an ack requires a msg-id. What does the failure ack attach to? | One ack per ELIGIBLE message the scan would have nudged, never rewritten while in the same state. | (a) Synthesize a target-scoped pseudo msg-id - rejected: it puts a non-message identifier into a filename the ack layer treats as a message reference, which is the same category of problem child 01's `--broker-id` fix exists to prevent. (b) Write no ack on resolution failure - rejected: the sender then sees silence where the closed enum has exactly the right tokens (`agent-not-running`, `agent-not-responding`), both broker-authored, and the spec's whole point is that delivery observations are recorded. (c) Write on every scan - rejected: 360 rewrites per down hour at the default interval, against a sibling plan's already-pinned non-rewrite invariant. | `comms.ack_filename`'s required msg-id and its "caller is responsible" docstring; `comms.ack_writer_for` returning `broker` for both states; `nomhl1` E-06's `st_mtime_ns` invariant; child 01's 10-second default interval | yes |
| D-5 | Descriptor-writer authentication is not established. Build it, file it, or disclose it? | Disclose it as a Deferred row with its bounded consequence and a declined carrier. | (a) Build a signature scheme - rejected as disproportionate to a v1 registry and outside anything the spec or child 01 contemplates; it would also need a key-distribution story this repository has no place for. (b) File a backlog item - rejected: it would record an intent nobody holds, and the same trust level already governs every other file in `untracked/` by the spec's design, so the item would surface in `aw attention` as work awaiting somebody forever. (c) Say nothing - rejected: a reader cannot distinguish "considered and declined" from "not thought about", and those differ for anyone deciding whether to enable the feature. | The spec's "Untrusted-input stance (mandatory)"; child 01's payload-blind invariant bounding the consequence to a misdirected content-free nudge; `evaluate_durable_carrier`'s three legitimate dispositions | yes |
