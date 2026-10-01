# Review findings: plan mc6r92

- Subject-Id: mc6r92
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-1101 (HIGH, fixed), PR-1102 (HIGH, fixed), PR-1103 (MEDIUM, fixed), PR-1104 (MEDIUM, fixed), PR-1105 (MEDIUM, fixed), PR-1106 (LOW, fixed)

## Round 1

Reviewed at HEAD `87803e1fc` in an isolated review lane. The plan file was committed and byte-identical
to the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author --agent` reported `{"outcome":"clean","exit":0,"findings":0}`
BEFORE semantic review, and `--phase review-finalize --agent` reports `clean` after revision. The plan
is `- Kind: child`, so the `IPD-S407` orchestrator child-row check does not apply.

THIS IS AN UNUSUALLY WELL EVIDENCED PLAN AND ALMOST EVERY FIGURE IN IT REPRODUCED TO THE CHARACTER.
Driven at review: `stranded_lane_drift` returns 5 rows, the over-bound one is `aw/lane/3brgb6` at 415
characters with `is_safe_descriptive` False against `MAX_DESCRIPTIVE_LEN` 300; the decomposition is
prefix 147, `why` 223, hint 41, plus 4 separators, summing exactly to 415; the five prefixes measure
147/125/116/116/116 so F-07's 116-to-147 range and the `300 - 147 - 41 - 4 = 108` arithmetic are exact;
the four `why` branches measure 223 and 51 as F-08 states; `lane_drift_severity(LANE_SUPERSEDED)` is
`info` while STRANDED is `error`; `attention.unsafe-field` is absent from `RULE_REGISTRY` and
`rule_spec` returns the default `error`, so F-04's double-count-and-red argument holds entirely; the
`--agent` diagnostics carry only `location` and `rule`; `record["why"]` is written in exactly one place
and read in exactly one; no test in `tests/` asserts the sentence text or bounds a drift detail length;
and all three spec quotations (Section 8.8's "Over-length values are a contract violation, not silently
truncated", F3a's "ONE LANE IS AT MOST ONE ROW", F10's output-safety clause) are verbatim in the
implemented attention spec. All four deferred carriers (`7stpjm`, `0livgf`, `ynhst5`, `8njbv5`) resolve
and are live. The plan's refusal of truncation and of a new `unsafe-field` finding is correct on the
evidence it cites, and its instruction to treat every count as a live population is exactly right.

THE DECISIVE FINDING IS PR-1102, AND IT MAKES TWO OF THE PLAN'S OWN ITEMS MUTUALLY UNSATISFIABLE. E-02
must bring the `why` to 108 characters; E-03 case (c) must then assert the bound on "the WORST-CASE
prefix shape reachable through the assembly". I measured the worst REACHABLE prefix using only shapes
present in this tree right now, and it is not 147. The longest live `run_id` is 28 characters
(`run-20260824T140112Z-2227235`), and three of the 30 live `.aw/worktrees/` directory names are 39 to 40
characters (`review-sweep-run-20260930T233654Z-235565`), which alone makes that one bit 63 characters.
Composed, that is a 181-character prefix, leaving `300 - 181 - 41 - 4 = 74` for the sentence. Adding
`uncommitted changes` and the `newest run X of N runs` collapse, both real code paths, reaches 219 and
leaves 36. A sentence carrying E-02's four required facts measures 102 to 110 characters at best; the
best 74-character attempt I could write ("not in HEAD; plan TERMINAL; redone later; husk to prune, not
at risk", 68 characters) loses the prune-versus-recover distinction, which is the row's entire operator
value. So a correct E-02 produces a test that fails on its own case (c), and the only way to pass it is
to gut the message. I resolved this by RESCOPING case (c) to record the composed length as an
observation while asserting only the single-line and control-character halves of the contract, and by
correcting the plan's guarantee from "every shape reachable through the assembly" to "every prefix shape
the live corpus exhibits". The plan's own F-07 already said the prefix was unbounded; what it had not
done was put a number on it and notice that the number contradicted an acceptance bar three items later.

PR-1101 is the one that would have failed at commit time. The plan's own `- Scope-Paths:` declared the
backlog item under `open/` while it sits in `graduated/`: `stale_record_scope_paths` returns
`classification='moved'` and `aw check all` reports `check.scope-path-target-stale` against this plan at
`error`. E-05's whole deliverable is a history note appended to that file, so `aw commit <plan> -- <real
path>` would have refused it as out of scope while the declared path sat unmodified, and finalize would
have demanded both a `--scope-reason` and a `--scope-ack` from a correctly executed plan. This is the
third instance of this exact class I have seen in this review sweep (`aisk5z` PR-001 and `dta75n`
PR-D02 were the others), all caused by the runner's own correct `open -> graduated` transition landing
after the plan was authored. Retargeted, re-measured clean, and E-05 now selects by id6 so a further
move does not re-break it.

PR-1103 corrects a symbol that does not exist where the plan says it does: `lane_remedy_hint` is
`attention.lane_remedy_hint`, and `runner_shared.lane_remedy_hint` raises `AttributeError`. That matters
beyond the citation, because the entire composition lives in `attention.stranded_lane_drift`, which
`- Scope:` fences out. The fence is right and stays, but E-03's test must import and call that module to
observe what production composes, so the plan now says explicitly that reading it is not a scope breach.
PR-1105 supplies a missing baseline (the suite is not green: one pre-existing date bomb in
`tests/test_backlog.py`, which is precisely the module E-05's backlog edit would make an executor
suspect). PR-1106 strengthens the fixture warning, which I reproduced: an in-checkout fixture resolves
to the MAIN checkout and returns the five REAL lanes, and after E-02 that row is in bound, so such a
test would pass for the wrong reason AND keep passing under E-04's revert, defeating the demonstration.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-1101 | HIGH | IN-SCOPE | G. Plan executability (a declared path that does not exist) | `check_engine.stale_record_scope_paths` on this plan returns `StaleScopePath(path='.aw/records/backlog/open/20260928-hv8zlg-...backlog.md', classification='moved', resolved=('.aw/records/backlog/graduated/...',))`; `aw find backlog hv8zlg` -> `graduated`; `aw check all` reports `check.scope-path-target-stale` against this plan at `error` | **The plan's own declared backlog `Scope-Paths` entry points at `open/` while the item sits in `graduated/`, and E-05's only deliverable is a history note appended to that file.** `aw commit <plan> -- <real path>` would have refused the real path as out of scope while the declared one went unmodified, so finalize would demand both a `--scope-reason` and a `--scope-ack` from a correctly executed plan, and the repository's own checker reports it at error severity before execution | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Entry retargeted to `graduated/`; `stale_record_scope_paths` now returns nothing for this plan. New finding row F-11 records the move and the mechanism; a Scope-check bullet tells the executor to re-derive by id6 rather than trust the declaration, since the item can advance again before execution |
| PR-1102 | HIGH | IN-SCOPE | E. Testing and verification (two acceptance bars that cannot both be met) | Longest live `run_id` 28 chars (`run-20260824T140112Z-2227235`); 3 of 30 live `.aw/worktrees/` dir names are 39 to 40 chars, making that bit 63 chars; composed prefix from those = 181, residual `300-181-41-4 = 74`; with `uncommitted changes` + `newest run X of N runs` = 219, residual 36. Four-fact candidate sentences measure 102/104/108/110; best 74-char attempt is 68 chars and drops a fact | **E-02's 108-character budget and E-03's "assert the bound on the WORST-CASE prefix shape reachable through the assembly" are mutually unsatisfiable, using shapes present in this tree today.** A correct E-02 yields a test that fails its own case (c), and the only way to pass is to shorten the sentence until it no longer distinguishes pruning a husk from recovering work, which destroys the row's purpose. F-07 noted the prefix was unbounded but never quantified it or noticed the contradiction | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | E-03 case (c) rescoped to RECORD the composed length and assert only the single-line/control-character halves of the contract, with an explicit prohibition on asserting the 300 bound there and on chasing it by shortening the sentence; E-02's budget note now carries the 181/74 and 219/36 measurements and states the resolution as binding; the Goal, Scope-check under-scope limit, Deferred row and approval paragraph all corrected from "every shape reachable through the assembly" to "every prefix shape the live corpus exhibits"; E-01 gains a worst-reachable-prefix measurement and V-01 requires it pasted with the instruction not to treat a sub-108 residual as a contradiction to fix; new finding row F-10 |
| PR-1103 | MEDIUM | IN-SCOPE | Evidence accuracy (a symbol cited in the wrong module) | `attention.lane_remedy_hint` exists at `agent_workflows/attention.py`; `runner_shared.lane_remedy_hint` raises `AttributeError: module 'agent_workflows.runner_shared' has no attribute 'lane_remedy_hint'`. The composition `"{0}: {1}. {2}".format("; ".join(bits), rec.get("why"), lane_remedy_hint(...))` is in `attention.stranded_lane_drift` | E-01 and F-03 both cite `lane_remedy_hint` as if it were in `runner_shared`, the module this plan edits. An executor following E-01 literally gets an `AttributeError`. The deeper point is that the whole composition lives in `attention.py`, which `- Scope:` fences out, so E-03's test must import that module to observe what production composes, and nothing said whether that was permitted | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 and F-03 both corrected to `attention.lane_remedy_hint` with the `AttributeError` recorded; a new E-01 note states that the composition lives in the fenced module, that the fence covers EDITS only, and that the test's import is reading rather than editing; a Scope-check bullet and V-03 both say so, with V-02's diff check confined to `runner_shared.py` |
| PR-1104 | MEDIUM | IN-SCOPE | Evidence accuracy (a one-character arithmetic error with a real consequence) | Rendered with a 4-character target, the SUPERSEDED `why` measures 223, not 224; prefix 147 + why 223 + hint 41 + separators 4 = 415, which matches the measured detail exactly | F-03 states the `why` is 224 while F-08 states 223, and 147+224+41+4 = 416, one more than the measured 415. Trivial alone, but the plan's whole budget derivation is this sum, so an inconsistent addend makes the 108 figure unverifiable by a reader checking the arithmetic, which is exactly what PR-1102 required me to do | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-03 corrected to 223 with the correction noted and the full sum shown to close at 415; E-02's budget note re-states the five re-measured prefixes so the derivation is checkable end to end |
| PR-1105 | MEDIUM | IN-SCOPE | E. Testing and verification (no baseline against a non-green suite) | Bare `python3 -m pytest` at HEAD `87803e1fc`: `1 failed, 3487 passed, 2 skipped, 3 warnings in 122.37s`; failure is `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, expecting a `2026-09-30` history line against a setter writing `2026-10-01` | V-04 correctly asks for a comparison "by FAILING NODE IDS rather than totals" but never states that the base is RED or which node id to expect. The live failure is a date bomb in `tests/test_backlog.py`, and E-05 edits a backlog item, so that module is the first thing an executor would suspect and the misattribution is near-certain | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | A baseline paragraph added to Required tests naming the node id, its date-bomb cause and the instruction to capture the failing set BEFORE any edit and compare as a set, never as totals; V-04 restated to require the failing node-id list and to forbid attributing that specific node id to E-05; new finding row F-12 |
| PR-1106 | LOW | IN-SCOPE | E. Testing and verification (a correct warning whose consequence was understated) | A `tempfile.TemporaryDirectory` outside the checkout resolves `_resolve_runs_repo_root` to itself and `stranded_lane_drift` returns 0 rows; a directory created inside this lane resolves to the OWNING MAIN CHECKOUT and returns the 5 REAL rows, via the `".aw/worktrees" in str(repo_root.resolve())` parent walk | E-03's fixture warning is right and I reproduced it, but it describes the failure as a fixture "reading the live tree". The sharper consequence is worse: after E-02 the live SUPERSEDED row IS in bound, so an in-checkout fixture would pass for the wrong reason AND keep passing when E-04 reverts the sentence, which silently destroys E-04's entire demonstration rather than merely weakening the fixture | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The E-03 fixture note now carries the independent reproduction and states the keep-passing-under-revert consequence, with the instruction that a non-reddening E-04 proves the fixture is leaking; V-03 requires the resolved root be pasted and asserted equal to the fixture; new finding row F-13 |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | E-02's 108-character budget and E-03's worst-case bound assertion cannot both be met. Weaken the sentence, weaken the test, or mark the plan REPLAN? | Weaken the TEST's case (c) to a recorded observation, keep E-02's 108, and correct the plan's stated guarantee | Shortening the `why` to 74 or 36 characters so case (c) passes. REJECTED on measurement: no four-fact sentence fits, and the best 74-character attempt loses the prune-versus-recover distinction that is the row's whole operator value, so the test would be satisfied by destroying the thing being protected. REPLAN. REJECTED: the plan's approach (shorten the one long segment, pin with a test) is sound and delivers a real improvement for the shapes that occur; only one acceptance bar was overreaching, which is a bounded edit. Bounding the prefix in this plan. REJECTED: that changes what every lane row prints, is a contract decision about row content, and is already deferred with carrier `0livgf` | 181-character prefix composed from the longest live `run_id` and a 40-character live worktree name; residual budgets of 74 and 36; four-fact sentences measured at 102 to 110; the plan's own F-07 already conceding the prefix is unbounded | yes |
| D-2 | The declared backlog Scope-Path is stale. Retarget it, or drop the entry and let E-05 reconcile at finalize? | Retarget to `graduated/` and additionally instruct E-05 to select by id6 | Dropping the entry. REJECTED: E-05 genuinely writes that file, so an undeclared edit would trip the finalize scope gate from the other direction. Leaving it and relying on `--scope-ack` plus `--scope-reason`. REJECTED: that is the sanctioned path for a move discovered DURING execution, not for one visible at review; the rule is `error` severity and knowingly shipping it guarantees a reconciliation prompt for a move nobody made during the run | `stale_record_scope_paths` before and after; `aw find backlog hv8zlg` showing `graduated`; the identical decision taken in the review records of `aisk5z` (D-4) and `dta75n` (PR-D02) | yes |
| D-3 | Should this review file a backlog item for the prefix-unboundedness that PR-1102 quantified? | No. The existing carrier `0livgf` already holds it; record the quantification in the plan instead | Filing a new item. REJECTED: `0livgf` is already the declared carrier for exactly this residue ("enforce drift detail ..."), verified `open`, so a second item would duplicate it and split the evidence. Leaving the quantification out of the plan. REJECTED: the number is what turns a vague "not bounded by construction" into a decidable scoping question, and it is the reason case (c) had to change | `aw find backlog 0livgf` -> `open`; the plan's existing Deferred row naming that carrier for this exact gap | yes |
| D-4 | The base suite carries a pre-existing date-dependent failure. Fix it here? | No. Record it as the baseline the executor must capture, and change no test | Fixing `test_release_exempt_setter_roundtrip_and_parity`. REJECTED: plan-review reviews planning documents only and must not change code or tests, and that file is outside this plan's `- Scope-Paths:`. Ignoring it. REJECTED: E-05 edits a backlog item and the failure is in `tests/test_backlog.py`, so an executor would misattribute it, which is PR-1105 | plan-review's opening constraint; the reproduced failure and its date diff; the plan's own `- Scope-Paths:` | yes |
