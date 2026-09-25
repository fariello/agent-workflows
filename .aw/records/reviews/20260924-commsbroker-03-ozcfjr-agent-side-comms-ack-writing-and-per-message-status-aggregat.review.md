# Review findings: plan ozcfjr

- Subject-Id: ozcfjr
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed Order 03 of Set `commsbroker`: agent-side ack writing plus per-message status aggregation.
Structural preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE
semantic review, and `--phase review-finalize` conforms after the revisions. The plan file was
committed and unchanged at review start (`git status --porcelain` on the file was empty; last touched
by `c41b69fb`), so no pre-review snapshot was needed. The Set's orchestrator (`u8tabj`) and child 01
(`nomhl1`) were reviewed earlier in this sweep, so their sequencing and broker-side claims are not
re-derived here.

THIS REVIEW SPENT ITS EFFORT RUNNING THE SHIPPED HELPERS THIS PLAN CONSUMES, and that is what
produced its findings. The plan's design rests on four `comms` functions (`validate_ack`,
`ack_filename`, `ack_writer_for`, `AGENT_ACK_STATES`), and three of the four turned out to have
properties the plan's prose assumed away. Every measurement below was run against HEAD in this
worktree and is pasted in the measurements section.

EIGHT FINDINGS, ALL FIXED IN PLACE. Two would have crashed or silently mis-answered the status view
that is half the plan's deliverable (PR-002 a `TypeError` on a legitimately mixed acks dir, PR-003 an
ack selector that cannot work on a realistic msg-id). Two were claims the plan made that the code
cannot support, so the plan was promising a guarantee it could not deliver (PR-004 detecting a forged
writer, PR-005 a `read`-or-later ordering the enum does not define). The rest are a repository-rule
error (PR-001), a contract miss the plan half-found (PR-006), a fresh-clone crash inherited from the
same defect class as child 01's PR-005 (PR-007), and a thin gate (PR-008).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G / repository rule | `check_engine.evaluate_durable_carrier` on this file -> 1 finding `check.ipd-uncarried-obligation`, severity `error`; the rule's own RuleSpec is `("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07")`; also reported by `aw check plans` | OQ-01 CARRIED NO DURABLE CARRIER, so the plan failed a deterministic `error`-severity repository rule. The rule's own detail states the consequence: once the plan reaches `executed` it classes `done` in `aw attention` and the question vanishes with no record. Identical to the defect found in the parent `u8tabj` and in child 01 `nomhl1`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- Carrier-Declined:` added to OQ-01, stating that "permitted" is the shipped behavior E-04 builds so nothing is owed unless the maintainer chooses to make acks mandatory. Re-measured: 1 -> 0 findings. |
| PR-002 | BLOCKER | IN-SCOPE | A (correctness) | MEASURED: `comms.validate_ack({... 'at':'2026-09-24T11:00:00'})` -> `[]` and `comms.validate_ack({... 'at':'2026-09-24T10:00:00Z'})` -> `[]` (BOTH valid); `sorted([{'at':'...10:00:00Z'},{'at':'...11:00:00'}], key=lambda a: comms.parse_not_before(a['at']))` -> `TypeError: can't compare offset-naive and offset-aware datetimes` | THE "NEWEST BY `at`" RULE RAISES ON A LEGITIMATE ACKS DIR. E-02's whole contract is `delivery` = newest broker ack and `work` = newest agent ack, ordered by `at`. But `comms.validate_ack` accepts any value `parse_not_before` parses, and that returns a NAIVE datetime for an offsetless timestamp and an AWARE one otherwise. So an acks dir holding one broker ack written with a `Z` and one agent ack written without is entirely valid per the shipped validator, and comparing them raises. This is not an edge case the plan could dismiss: the two acks come from two DIFFERENT writers (child 01's broker and this plan's agent writer), so mixed spellings are the expected steady state unless something forces one, and nothing did. A read-only status view crashing is worse than a wrong answer because it takes out the `status` subcommand entirely. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-02 now MUST normalize before comparing (naive parse treated as UTC via `replace(tzinfo=timezone.utc)`), must never sort raw parse results, and must not raise on an unparseable or tied `at` (stable filename fallback). E-01 pins the write half: `now` defaults to `datetime.now(timezone.utc)` so every ack this module writes is offset-aware, while E-02 still normalizes because the broker and hand-written acks are not bound by that. E-05 case (a) plants exactly the two measured values; V-02 demands the pasted `TypeError` from the pre-revision sort, so the fix is proven non-vacuous. Recorded as F-5. |
| PR-003 | HIGH | IN-SCOPE | A (correctness) | MEASURED: `comms.ack_filename("m.a","b","read")` and `comms.ack_filename("m","a.b","read")` BOTH -> `m.a.b.read.json`; `ack_filename("20260924-1200-01-a.b--to--c.d-ask-x","aw.comms-broker","delivered").split(".")` -> 7 parts; `comms.is_filename_safe` -> True for `a[b`, `a*b`, `a?b` | AN ACK FILENAME CANNOT BE PARSED BACK, AND GLOBBING IT IS UNSAFE, yet E-02 had to find "a message's acks" and said nothing about how. `ack_filename` joins three dot-bearing parts with `.`, so the mapping is not injective (measured: two different inputs produce one name) and a real msg-id splits into 7 parts, so any name-splitting selector is wrong on the FIRST realistic message rather than on a contrived one. The obvious alternative, `Path.glob(f"{msg_id}.*")`, is also unsafe because `is_filename_safe` PERMITS glob metacharacters, so a msg-id containing `[` silently matches the wrong file or nothing at all. The plan would have been implemented one of these two ways and appeared to work in a test using a short dot-free msg-id. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 now selects by the `re` FIELD of each parsed ack, not by the name: read every `*.json`, parse, keep those whose `re` equals `msg_id`, with the filename explicitly demoted to a human convenience and the JSON body named as the authority. An unparseable or non-object file becomes an `acks` row with a `problem` rather than an exception. E-05 adds a dot-bearing msg-id case (b) and a glob-metachar case (c), each of which fails under the respective wrong approach. Recorded as F-6. |
| PR-004 | HIGH | IN-SCOPE | B (security) / F (honest documentation) | `engine.COMMS_UNTRACKED_SUBDIRS` -> `('inbox','sent','archive','scheduled','acks')` with ONE `acks` entry; `engine.COMMS_SHARED_SUBDIRS` -> `('inbox','sent','archive')`, no `acks` (measured); the plan's own Deferred list: "Authenticating the `by` field: it is self-asserted" | THE PLAN PROMISED TO DETECT A FORGERY IT CANNOT SEE. E-02 said any ack "whose state's writer does not match its layer" is reported with a problem, and its Expected outcome claimed "a forged broker-layer `read` is reported, not counted". There is no per-file layer to compare against: every ack lands in the SAME `untracked/acks/` directory (measured: one `acks` lane exists, and the shared tree has none), and `by` is self-asserted, which the plan's own Deferred list concedes two sections later. So a broker-written `read` is byte-indistinguishable from an agent-written one. This matters beyond tidiness: the spec ships an authorized-writer table, and a status view claiming to enforce it would let a reader trust `work` as attested when it is not, which is the exact "treat an ack as proof" failure the spec forbids and the plan's own Scope says is OUT. | C:Low; U:Low; S:Medium; F:Low; Overall:Low | FIXED | E-02 no longer claims detection. It classifies each ack by `comms.ack_writer_for(state)` so a state is never counted in the wrong bucket (`delivery` from broker states, `work` from agent states), and its docstring MUST state plainly that the writer of a given file is unverified. The Expected outcome was rewritten to drop the forgery claim. E-06 carries the limit into the spec amendment, since the spec's writer table is what a reader would otherwise take as enforced. Recorded as F-8. |
| PR-005 | MEDIUM | IN-SCOPE | A (correctness) | MEASURED: `comms.AGENT_ACK_STATES` -> `('read','in-progress','done','not-done','executed','not-executed')`, so `index('not-done')` is 3 and `index('executed')` is 4; `[n for n in dir(comms) if 'ORDER' or 'RANK' or 'LATTICE' in n]` -> `[]` | `read`-OR-LATER WAS NOT DERIVABLE, AND THE OBVIOUS IMPLEMENTATION IS BACKWARDS. E-02 defined `unread` as True when no "`read`-or-later agent ack" exists, but `comms` defines no state ordering and the tuple order is not one: a tuple-index rank would place the terminal refusal `not-done` BELOW `executed`, so an agent that finished and wrote `not-done` would still read as unread while one that wrote `executed` would not. The spec's own wording is simpler and is the one guarantee available ("the ABSENCE of a `read` ack after `delivered`"), and since membership in `AGENT_ACK_STATES` already means the target asserted something, any agent ack is evidence it read the message. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 now derives `unread` as "a `delivered` ack exists and NO valid agent-state ack exists", with an explicit instruction not to write a rank comparison and the measured reason why. E-05 case (e) pins it by asserting `unread` is False after a `not-done` ack, so a later rank-based rewrite fails a test. Recorded as F-7. |
| PR-006 | MEDIUM | IN-SCOPE | A (correctness) / spec sync | MEASURED: `grep -n "local/"` on the spec returns THREE lines (82 the ack path, 110 "`local/inbox/`", 28 the historical "(was `local/`)"); `engine`'s installed AGENTS.md block says "check `{comms_dir}/untracked/inbox/`" | THE PLAN FOUND ONE STALE PATH AND MISSED ITS TWIN. F-2 correctly identified the ack path `.agents/comms/local/acks/`, but the spec's "Cooperative check-in" section still tells agents to check `local/inbox/`, directly contradicting the AGENTS.md block `engine` actually installs (which says `untracked/inbox/`). That is the same rename miss with the same consequence, and it is arguably worse: it is the instruction a target agent follows to find its mail at all. The plan's own V-06 would not have caught it, because `grep local/acks` returns nothing while `local/inbox/` survives. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06 now fixes BOTH stale references and explicitly preserves the third (the layout block's "(was `local/`)", which is history). V-06's required grep was widened from `local/acks` to `local/` and must return EXACTLY ONE line. E-06 also gained the prohibition on hand-editing `- Status:`/`## Workflow history` (`.aw/records/specs/README.md`: "Do NOT hand-edit the status or history"), which the original E-06 violated by instructing "append a `## Workflow history` note line"; verified at review that `aw specs note` accepts this spec unchanged. Recorded as F-9. |
| PR-007 | MEDIUM | IN-SCOPE | A (correctness) / F (silent failure) | MEASURED in this worktree: `.aw/records/comms/untracked/` exists but is EMPTY (`ls -a` shows only `.` and `..`); `ls untracked/inbox` and `ls untracked/acks` both -> No such file or directory; `git check-ignore -v` -> `.aw/.gitignore:6:records/*/untracked/`; `engine` creates `COMMS_UNTRACKED_SUBDIRS` as an install side effect only | THE WRITER WOULD CRASH ON A FRESH CLONE, and this is measured in the very worktree the review ran in. E-01 writes to `untracked/acks/` and checks for the message in `untracked/inbox/`, but both are gitignored by construction, so a clone has neither. Child 01's PR-005 found exactly this defect in the broker half; the same defect class was still present in this plan's writer and status reader. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now `mkdir(parents=True, exist_ok=True)` the acks dir before writing and treats a missing `inbox/` as a clean "message not found" refusal rather than letting `FileNotFoundError` escape. E-03's `status` treats a missing lane as zero messages and exits 0. E-05 case (d) covers the no-lane repo; V-01 and V-03 demand it. Recorded as F-11. |
| PR-008 | MEDIUM | IN-SCOPE | G (plan executability) | The gate as written was four sentences (OQ status, dependency, commit rule, lint); compare child 01's and child 02's gates, which carry an honesty rule naming the faking-exposed items, stop conditions, and a scope fence | THE GATE CARRIED ALMOST NO EXECUTION CONTRACT, and this plan needs one more than its siblings do, because four of its five newly added test cases are defects whose WRONG implementation still returns a plausible object rather than an error: a mixed-offset dir raises only when both spellings are present, a name-splitting selector is correct for a dot-free msg-id, a glob selector works until a metacharacter appears, and a rank-based `unread` agrees with the correct rule on every state except `not-done`. A generic "paste the output" instruction does not defend against that; a green `-k status` summary is consistent with all four bugs. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate rewritten with: an honesty rule naming V-02 and V-06 as the faking-exposed items AND why each is (four indistinguishable wrong implementations; `grep local/acks` passing while `local/inbox/` survives); STOP CONDITIONS for `nomhl1` not executed (noting the writer half stands alone per F-4, so writer-only is the sensible re-scope report) and for the `comms` helpers changing shape; a SCOPE FENCE stated as a declaration reconciled by `aw ipd finalize`'s `--scope-reason`/`--scope-ack` and NOT as a stop directive (per the 2026-09-01 maintainer ruling); the `aw commit ozcfjr` path-scoped never-push rule; the verified absence of a release gate on both this plan and backlog `0gd5w6`; and the conditional runner-versus-`aw ipd finalize` transition ownership. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-004 shows E-02 promised a forgery detection that is impossible. Is that a REPLAN of the status half, or a repairable claim? | Repairable claim. Keep the aggregation, delete the detection promise, and write the unverifiable-writer limit into both the docstring and the spec. | (a) `REJECT - NEEDS REPLAN`. Rejected: the aggregation itself is sound and useful without the detection; only one sentence and one Expected outcome asserted the impossible thing. (b) Add a real authorization mechanism (signing, a broker-owned lane). Rejected as over-scope: the plan's Deferred list already declines to authenticate `by`, and inventing a trust mechanism is a separate design. | The plan's own Scope says treating an ack as proof is OUT and its Deferred list concedes `by` is self-asserted, so removing the claim makes the plan internally consistent rather than weaker; `plan-review` Step 2.4 reserves REPLAN for an approach not repairable with bounded edits. | yes |
| D-2 | PR-005: with no ordering defined, should the review DEFINE a progress lattice for `AGENT_ACK_STATES` so "`read`-or-later" becomes meaningful? | No. Use the spec's literal rule (any agent ack clears `unread`) and forbid a rank comparison. | Defining an ordering in `comms.py` and ranking against it. Rejected: `comms.py` is not in this plan's `- Scope-Paths:`, a state lattice is a public contract other consumers would inherit, and the measured tuple order shows the naive version is wrong in a way a reviewer-invented ordering could easily repeat. | The spec states the rule literally ("`unread` is NOT a token: it is the ABSENCE of a `read` ack after `delivered`"); measured that no ordering constant exists in `comms`; AGENTS.md makes a public-contract widening a maintainer call. | yes |
| D-3 | PR-002 could be fixed by normalizing on read, by pinning the write spelling, or by tightening `comms.validate_ack` to require an offset. Which? | Both normalize on read (E-02) and pin the write spelling (E-01); do NOT tighten the validator. | Tightening `validate_ack` to reject a naive `at`. Rejected: `comms.py` is out of this plan's declared scope, the validator is a shipped public contract whose behavior child 01 also depends on, and tightening it would retroactively invalidate any ack already on disk. | `comms.py` is absent from `- Scope-Paths:`; AGENTS.md requires a spec/contract change to be declared and justified, which a reader-side fix does not need; normalizing on read is required anyway because the broker and hand-written acks are not bound by this module's write rule. | yes |
| D-4 | Should this review fix the same stale-`local/inbox/` spec reference (PR-006) itself, since it is a one-line contract error in a tracked spec? | No. Route it through E-06, which already amends that spec and is declared in `- Scope-Paths:`. | Editing the spec now. Rejected: `plan-review` may not change code, tests, or runtime configuration, and a spec is a tracked contract another plan is mid-flight on; a reviewer editing it leaves a diff with no execution record. Also child 02 declares the same spec, so an out-of-band edit could collide. | `plan-review` Step 0 ("Review planning documents only ... Editing a plan is not executing it"); the plan already declares the spec, so the fix has a legitimate owner. | yes |
| D-5 | Should this review also fix PR-001 (the uncarriered OQ) in child 02 `ex539u`, which the child-01 review recorded as still carrying it? | No. Fix it here only; it remains a finding against `ex539u` if that plan is not separately reviewed. | Fixing both children. Rejected: `ex539u` is not in this review's ledger, and a reviewer editing a plan it did not review leaves a diff with no findings record behind it. (Noted: `ex539u` was in fact hardened separately in this sweep, per commit `1e613bbe`.) | `plan-review` Step 0.1 (the ledger is the named target plus documented additions); consistent with D-5 of the `nomhl1` review and D-1 of the `u8tabj` review. | yes |
| D-6 | E-03 said to resolve the comms dir "the same way `comms_broker` does", a module that does not exist yet. Cite it anyway, or name the shipped rule? | Name the shipped rule: call `engine.resolve_target_layout` and `engine._record_scaffold_dirs`. | Keeping the citation to `comms_broker`. Rejected: it is not checkable at authoring time, and if child 01 stops at its E-01 spike the named shape may never exist in the form assumed. | The plan's own Step-0 convention requires citing by symbol rather than by an expiring reference; child 01's E-05 was corrected in its own review to call these two functions, so this is the same rule, not a new one. | yes |

### Measurements taken at review

```text
aw ipd lint --phase author           --agent ozcfjr -> {"outcome":"clean","exit":0,"findings":0}
aw ipd lint --phase review-finalize  --agent ozcfjr -> {"outcome":"clean","exit":0,"findings":0}  (after revisions)

check_engine.evaluate_durable_carrier(ozcfjr)  BEFORE -> 1 finding, severity error (OQ-01)
                                                AFTER -> 0 findings

# PR-002: both spellings valid, comparing them raises
comms.validate_ack({'re':'m','state':'read','by':'x.y','at':'2026-09-24T11:00:00'})   -> []
comms.validate_ack({'re':'m','state':'read','by':'x.y','at':'2026-09-24T10:00:00Z'})  -> []
sorted([{'at':'2026-09-24T10:00:00Z'},{'at':'2026-09-24T11:00:00'}],
       key=lambda a: comms.parse_not_before(a['at']))
  -> TypeError: can't compare offset-naive and offset-aware datetimes

# PR-003: ack_filename is not injective, and is_filename_safe permits glob metachars
comms.ack_filename('m.a','b','read')   -> 'm.a.b.read.json'
comms.ack_filename('m','a.b','read')   -> 'm.a.b.read.json'      # SAME name, different inputs
comms.ack_filename('20260924-1200-01-a.b--to--c.d-ask-x','aw.comms-broker','delivered').split('.')
  -> ['20260924-1200-01-a','b--to--c','d-ask-x','aw','comms-broker','delivered','json']   # 7 parts
comms.is_filename_safe('a[b') / ('a*b') / ('a?b')  -> True / True / True

# PR-004: one acks lane, so no per-file "layer" exists
engine.COMMS_UNTRACKED_SUBDIRS -> ('inbox','sent','archive','scheduled','acks')
engine.COMMS_SHARED_SUBDIRS    -> ('inbox','sent','archive')      # no acks

# PR-005: the enum order is not a progress lattice
comms.AGENT_ACK_STATES -> ('read','in-progress','done','not-done','executed','not-executed')
  index('not-done') == 3 < index('executed') == 4
no ORDER/RANK/LATTICE name in dir(comms)

# PR-006: three `local/` lines in the spec, only one is the ack path
grep -n "local/" <spec> -> 28 "(was `local/`)"  [history, keep]
                           82 ".agents/comms/local/acks/..."     [F-2, fix]
                          110 "`local/inbox/` (and `shared/inbox/`)"  [MISSED, fix]
engine installed AGENTS.md block -> "check `{comms_dir}/untracked/inbox/`"

aw specs note <copy of spec in scratch repo> --message "probe..."  -> exit 0, record prepended
  (so the tooled history route accepts this spec unchanged; no hand edit needed)

# PR-007: the untracked lane does not exist here
ls -a .aw/records/comms/untracked/  -> only `.` and `..`
ls .aw/records/comms/untracked/inbox -> No such file or directory
ls .aw/records/comms/untracked/acks  -> No such file or directory
git check-ignore -v .aw/records/comms/untracked/acks/x.json
  -> .aw/.gitignore:6:records/*/untracked/

# F-10: the README drift is two deliberate layout substitutions, not noise
difflib(engine._COMMS_README_TEMPLATE, .aw/records/comms/README.md)
  -> H1:  "# .agents/comms/"          vs "# .aw/records/comms/"
  -> tail: ".agents/docs/specs/"      vs ".aw/records/specs/"
  (2220 vs 2223 chars; no test compares the content)
```

### Verdict and readiness

Verdict `APPROVE WITH REVISIONS APPLIED`. Eight findings, all FIXED in place; none DEFERRED, none
OPEN, none REPLAN, so nothing required escalation as a `- Blocking: yes` question. OQ-01 remains
`Blocking: no` with a stated default and now a declined carrier, which per the 2026-09-10 maintainer
ruling does not make the plan `NO-GO`. Readiness `go-pending-approval`: the plan is clean and awaits
human sign-off, and it additionally carries `- Item-Dependencies: executed:nomhl1`, which the runner
re-checks at dispatch.
