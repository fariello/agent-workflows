# Review findings: plan pi3bk8

- Subject-Id: pi3bk8
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-801 (BLOCKER, fixed), PR-802 (HIGH, fixed), PR-803 (HIGH, fixed), PR-804 (MEDIUM, fixed), PR-805 (MEDIUM, fixed), PR-806 (MEDIUM, fixed), PR-807 (MEDIUM, fixed), PR-808 (LOW, fixed), PR-809 (LOW, fixed), PR-810 (LOW, fixed), PR-811 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file was committed and byte-identical to the lane input,
so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author --agent`
reported `conforming` (exit 0, zero findings) BEFORE semantic review; `--phase review-finalize` reports
`conforming` with zero findings after revision. This plan's own first `- Kind:` bullet reads `child`,
so the `IPD-S407` orchestrator child-row check does NOT apply and the bounded repair loop was never
entered.

I BUILT THE PROBE THIS PLAN SPECIFIES rather than reading research `uq4y6q`, because the plan's
deliverable is a mechanism and a review that reads a prose description of a mechanism reviews nothing.
That is what produced the blocker: the authored design cannot work, and it fails in the direction that
survives review.

FIRST, the technical premise holds. On this host: `abi: 4`, a `CONNECT_TCP` ruleset with one
`LANDLOCK_RULE_NET_PORT` rule gives `allowed connect ok: True` and `denied connect refused: True
[Errno 13] Permission denied`, `RESULT: ENFORCED`, with `rule struct size: 16`. So F-1, F-2 and F-3
are sound and the naming decision resting on them is correct.

### THE BLOCKER: the probe as authored can never report True (PR-801)

E-02 said the child "binds a loopback listener, applies a ruleset allowing only that listener's port".
`landlock_bootstrap_source` applies the ruleset and THEN `execv`s, so every allowed port must be chosen
while the child does not yet exist. Measured: with only port `40001` allowed and `restrict_self`
applied, the process bound `127.0.0.1:56659` successfully (bind is unaffected, since only `CONNECT_TCP`
is handled) and connecting to that very socket returned `[Errno 13] Permission denied`.

Why this matters more than an ordinary design error: the failure is FAIL-CLOSED. The probe returns
False on a fully capable host, the capability reads not-supported, nothing breaks, no test goes red,
and the False gets pasted into V-02 as "whatever the real host reports" because V-02 explicitly
accepted that. The capability would have been permanently unreachable and the plan would have looked
executed correctly. This is the same class of defect as the one-sided measurement trap the
orchestrator `l4vw9o` records, inverted: there a total denial read like enforcement, here a total
denial reads like an honest negative.

I then DEMONSTRATED the alternative rather than describing it, per Step 3.1's HOW-question standard:
parent binds both listeners, passes the allowed port into the network-extended bootstrap, bootstrap
restricts and `execv`s the checker. Result: parent listeners `46623` (allowed) and `46745` (denied),
`probe rc: 0`, stderr `denied connect refused: [Errno 13] Permission denied`. Both sides proven in one
run. E-02 now specifies parent-binds with the measured refutation inline, notes that the parent must
hold the sockets open (a closed listener yields `ECONNREFUSED`, not the `EPERM` that distinguishes a
kernel denial from a dead port), and E-02's Expected outcome plus V-02 now REQUIRE a True on an
ABI >= 4 host so the impossibility cannot pass as a fail-closed result.

### The second dead end: a test that cannot fail (PR-802)

E-06 proposed adding a row to `PRESENCE_VS_OBSERVATION`. That table has had no consumer since commit
`80db6750` ("test: delete 366 tests that pinned code structure instead of behaviour") deleted
`test_no_runner_safety_probe_infers_support_from_helper_presence`. An `ast` walk of
`tests/test_host_capability_extension.py` for every `Name`/`Attribute` reference returns exactly
`[('name', 235)]`, the assignment itself; the table's own comment still asserts "`_helper_exists` is
asserted per row" and no such symbol exists anywhere in the repository. So the authored E-06 would
have written a row into data nothing reads, and V-06 would have pasted a green suite line as proof.
E-06 now restores the consuming test first (behavioral, driving `probe_runner_safety_capabilities`,
with an explicit prohibition on reviving the deleted source-reading parts), E-08 adds the row, and
V-06/V-08 each demand an induced FAILURE.

PR-801 and PR-802 share one shape, which is now stated in the plan's gate: an artifact that cannot
produce the answer which would reveal a problem. A probe that can only say False, and a test that can
only say pass.

### The sequencing defect (PR-803)

I applied E-03's edits and nothing else, then ran the affected files: `1 failed, 73 passed`, with
`AssertionError: 'supports_deny_tcp_port' not found in ('supports_inline_permissions', ...)`.
`test_new_contract_fields_and_defaults` iterates `RUNNER_SAFETY_CAPABILITIES` and asserts every member
appears in `CONTRACT_FIELDS`, which it imports from the other test module, so registering the
capability in E-03 while the tuple append waited for E-05 leaves the suite red across two items. Adding
the tuple entry gives `74 passed`. The one-line append moved into E-03; E-05 keeps the rest.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | BLOCKER | IN-SCOPE | A. Correctness / E. Testing | `agent_workflows/host_sandbox_profile.py` `landlock_bootstrap_source` (restrict-then-`execv` order); plan E-02 "The child binds a loopback listener, applies a ruleset allowing only that listener's port" | THE PROBE AS AUTHORED CAN NEVER RETURN True. Every allowed port is fixed before the child exists, so a child that binds afterwards cannot reach its own listener. Measured: allowed port `40001`, child bound `127.0.0.1:56659`, connect to own socket `[Errno 13] Permission denied`. The failure is fail-CLOSED, so it breaks no test and would have been pasted as the host's honest measurement, leaving the capability permanently unreachable. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-02 rewritten to PARENT-BINDS both listeners, with the measured refutation and the `ECONNREFUSED`-vs-`EPERM` requirement inline. The replacement was DEMONSTRATED at review (`rc: 0`, `denied connect refused: [Errno 13] Permission denied`, parent listeners 46623/46745). E-02's Expected outcome and V-02 now require True on an ABI >= 4 host, so a False there fails the item instead of being recorded as the measurement. |
| PR-802 | HIGH | IN-SCOPE | E. Testing | `tests/test_host_capability_extension.py` `PRESENCE_VS_OBSERVATION`; `ast` walk for every `Name`/`Attribute` reference returns `[('name', 235)]`; commit `80db6750` deleted `test_no_runner_safety_probe_infers_support_from_helper_presence` | THE TARGETED TABLE IS DEAD DATA. Its only reference is its own assignment, so a row added to it asserts nothing, and the comment claiming "`_helper_exists` is asserted per row" names a symbol that exists nowhere. E-06's deliverable plus V-06's green-suite evidence would both have been vacuous, which is precisely what V-06's own inversion check exists to catch. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06 now restores the CONSUMER first (iterate the table, assert helper importable+callable, run the prober under each row's `arrange`, assert the verdict), explicitly behavioral and explicitly forbidden from reviving the deleted source-reading parts. E-08 adds the new row second. V-06 demands an `ast` reference count above 1 and an induced failure; V-08 demands the same for the row. |
| PR-803 | HIGH | IN-SCOPE | A. Correctness / G. Plan executability | Applied E-03's edits alone: `1 failed, 73 passed`, `AssertionError: 'supports_deny_tcp_port' not found in (...)`; `tests/test_host_capability_extension.py` `test_new_contract_fields_and_defaults` asserts every `RUNNER_SAFETY_CAPABILITIES` member is in `CONTRACT_FIELDS` | E-03 LEAVES THE SUITE RED until E-05, across two intervening items. A plan whose own gate is the bare suite cannot have a middle state where the suite fails, and an executor hitting the red would either debug a non-defect or reorder the plan silently. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | The one-line `CONTRACT_FIELDS` append moved into E-03 with the measurement recorded (`1 failed, 73 passed` -> `74 passed`). E-05 retains the rest of that file's coverage and its Expected outcome now states the suite is green at the end of E-03, not merely at the end of the plan. |
| PR-804 | MEDIUM | IN-SCOPE | B. Security / D. Invariants | Plan Deferred row "WITHHOLDING remote credentials ... Already built and shipped"; `runner_shared.pinned_child_env` is `os.environ.copy()` plus a PYTHONPATH pin; `oc_runipd._apply_execution_profile` returns `argv` unchanged outside `hardened`; Order 01's review PR-701 corrected the identical sentence | REPEATS A SECURITY OVERCLAIM THE SIBLING PLAN WAS ALREADY CORRECTED FOR. No environment-carried credential is withheld (a `GH_TOKEN` or forwarded `SSH_AUTH_SOCK` reaches the worker), hardened mode is opt-in and Linux-only, and the path list is a fixed enumeration. An environment token is push-capable, so the unqualified claim asserts a boundary that does not exist, in a plan whose whole purpose is refusing that shape. | C:Low; U:Low; S:Medium; F:Low; Overall:Low | FIXED | Row rewritten with the three measured bounds and a Carrier-Declined that says nothing is owed BY THIS PLAN while naming what is incomplete, so a reader of this plan alone cannot infer the credential half is done. |
| PR-805 | MEDIUM | UNDER-SCOPE | G. Plan executability | Plan "Spec / documentation sync": "an entry IS warranted here ... it is not in `Scope-Paths` ... If the reviewer prefers the CHANGELOG edit be declared, add the path at review time"; `ipd_schema.scope_paths_implicit_allowances()` returns `('.aw/records/plans/**', '.aw/records/plans/INDEX.md', '.aw/records/**/index.md')` | A DECLARED-NECESSARY EDIT LEFT OUT OF THE FENCE. `CHANGELOG.md` is not implicitly allowed, so the plan committed itself to an edit the finalize scope gate would then demand a `--scope-reason` for, over work the plan already knew it would do. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `CHANGELOG.md` added to `Scope-Paths`; the sync section now records why (with the measured allowance list) and the gate's scope fence says to write the entry rather than ack it. |
| PR-806 | MEDIUM | IN-SCOPE | C. Architecture | Plan OQ-03: "that work is carried by `wzhe4n`"; `wzhe4n` is Order 03 of this Set, whose Scope reads "Records and verification only; no product code"; backlog `sv9ce4` Summary: "Build host-granular outbound network filtering (netns plus filtering proxy)" | A CARRIER POINTING AT A PLAN THAT FORBIDS THE WORK. OQ-03 assigned the network-policy deliverable to a sibling records-only plan, while every other deferral row in this plan correctly names `sv9ce4`. An obligation routed to a plan that cannot accept it is an obligation lost, which is the failure the carrier convention exists to prevent. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | OQ-03 now names backlog `sv9ce4` (verified `open`), with the correction and its reason recorded inline so the outlier is visible rather than silently swapped. |
| PR-807 | MEDIUM | IN-SCOPE | E. Testing | Plan E-05: "with the real probe, assert the reported verdict equals a forced re-run of the probe" | A VACUOUS ASSERTION. `probe_runner_safety_capabilities` is uncached, so it re-runs the same function and the assertion reduces to `probe() == probe()`, which passes for a probe returning a constant. That is the exact fail-open shape this area's test discipline exists to reject, and it was being written into the item that is supposed to pin the probe. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now forbids that wording explicitly, requires assertion against an arranged kernel outcome or the probe's own evidence-naming note, and V-05 demands a paste showing the test FAILS against `lambda: (True, "constant")`. |
| PR-808 | LOW | IN-SCOPE | E. Testing | Plan V-07's piped `aw host capabilities opencode` grep for `deny_push` and the `REFUSED` check; measured on the current tree: bare `grep -c REFUSED` returns 1 (the fresh-verifier note reads "a reused-identity run was REFUSED"), `grep -c 'REFUSED  '` returns 0; `DenyPushRemovedTests` asserts `assertNotIn("REFUSED  ", out)` | THE PRESCRIBED GREP REPORTS A FALSE POSITIVE. An executor greping the bare word sees a hit and concludes the guard's premise broke, then either "fixes" a passing test or reports a regression that does not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-07 now prescribes the two-space form, states both measured counts, and names the assertion it mirrors. |
| PR-809 | LOW | IN-SCOPE | G. Plan executability | Plan F-9 attributed both quoted strings to "the bwrap stub's rationale"; `tests/test_host_sandbox_profile.py` module docstring holds "leaves the guarantee UNVERIFIED on that machine" while the `BWRAP_STUB_MODES` comment holds "would SKIP everywhere and guard nothing" | TWO QUOTES ATTRIBUTED TO ONE PLACE. Minor, but an executor greping the stub comment for the UNVERIFIED sentence will not find it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-9 now cites each string to its own location and records the correction. |
| PR-810 | LOW | UNDER-SCOPE | C. Architecture / F. KISS | `probe_runner_safety_capabilities` is deliberately uncached; measured: extended bootstrap probe mean `0.047s` over 5 runs, warm `detect_host_capabilities('opencode')` `0.305s`, projected `0.352s` (~1.2x) | OQ-02 CHOSE THE UNCACHED GROUP WITHOUT PRICING IT. The choice is right, but membership means paying a subprocess per call, and AGENTS.md makes user-perceptible slowness a `bug`-class defect, so the number belongs in the record rather than being discovered later. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-12 records the measurement and the judgement (once per report invocation, not per queue item; 47ms on 305ms is not perceptible), and OQ-02 now carries the figure plus the observation that `RUNNER_SAFETY_CAPABILITIES` membership gates nothing because `read_only` has `required=()`. |
| PR-811 | LOW | IN-SCOPE | G. Plan executability (right-sizing) | `aw ipd lint` `IPD-Z602` on my own PR-802 rewrite: "E-06: action text may bundle multiple concerns (3 clauses)" | MY OWN REVISION WAS MULTI-CONCERN, bundling the consumer restoration, the new row, and the ABI-gate test into one item with three independent test surfaces. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into E-06 (restore the consumer), E-08 (add the row, depends on E-06), E-09 (ABI gate), each with its own `V-*`. `Highest E allocated` raised to 09; `aw ipd lint --phase review-finalize` conforming with zero findings. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01: is `supports_deny_tcp_port` the right name, or should it be `supports_deny_outbound_tcp_port`? | Keep the short name; carry the direction in the `probe_notes` entry, and make that a requirement of E-02 rather than a nicety. | The longer name. Its case is real and I confirmed the ambiguity by measurement rather than dismissing it: at ABI 4 this kernel accepts a ruleset handling `LANDLOCK_ACCESS_NET_BIND_TCP` (`1 << 0`) exactly as readily as `CONNECT_TCP` (`1 << 1`), both returning a valid fd, so the two rights genuinely are separate and a bare "tcp_port" does not say which was proven. | `host_cmd._capability_rows` plus the human renderer emit each capability's note directly beneath its verdict row, verified by running `aw host capabilities opencode` (every row is followed by its own `why:` line). Direction is therefore read at the same instant as the verdict, never separately, so the longer name spends 8 characters on information already present at the point of use. | yes |
| D-2 | PR-801: which probe architecture replaces the impossible child-binds design? | Parent binds both listeners and passes the allowed port into the bootstrap. | Having the child bind and then applying a second ruleset post-`exec` (Landlock domains cannot be relaxed and a second restriction only narrows, so the allowed port still could not be added); using a fixed well-known port (collision-prone and not hermetic). | DEMONSTRATED, not argued: parent listeners `46623`/`46745`, network-extended bootstrap plus checker, `rc: 0` with stderr `denied connect refused: [Errno 13] Permission denied`, i.e. allowed connect succeeded and denied connect refused in one run. The refuted design was equally measured (`allowed 40001`, child bound `56659`, own-socket connect `EPERM`). | yes |
| D-3 | PR-803: does the `CONTRACT_FIELDS` append move into E-03, or does E-03 depend on E-05? | Move the one-line append into E-03. | Reordering so E-05 precedes E-03 (would make the test file reference a field the dataclass lacks, failing in the other direction); declaring the red state acceptable (the plan's own gate is the bare suite, so a red middle state has no honest evidence path). | Measured both states: E-03's edits alone give `1 failed, 73 passed` with the exact assertion text; adding the tuple entry gives `74 passed`. `tests/test_host_capability_extension.py` `test_new_contract_fields_and_defaults` imports `CONTRACT_FIELDS` from the sibling module, so the coupling is real and not incidental. | yes |
| D-4 | PR-806: which artifact carries the production network-policy decision OQ-03 defers? | Backlog `sv9ce4`. | Sibling plan `wzhe4n`, as authored. Rejected on its own text: its Scope reads "Records and verification only; no product code", so it cannot accept a product deliverable. | `sv9ce4` verified `open` with Summary "Build host-granular outbound network filtering (netns plus filtering proxy), the only mechanism that can deny a git push without also denying the model API", which is exactly the deferred work; every other deferral row in this plan already names it. | yes |

No `Reversible: no` decision was taken in this round, so no escalation under Step 3.1 was required.
OQ-02 and OQ-03 were already `resolved` by the author and I verified rather than re-decided them,
augmenting each with measured evidence (PR-810, PR-806). No finding was left `OPEN` or `DEFERRED`, so
no `- Blocking: yes` escalation is owed under Step 4 and none was written.

### Verification performed at review

- `aw ipd lint --phase author --agent`: `conforming`, exit 0, zero findings (before semantic review).
- `aw ipd lint --phase review-finalize --agent`: `conforming`, exit 0, zero findings (after revision).
  An intermediate run reported `IPD-Z602` (PR-811) and then `IPD-I303` twice while the split items
  lacked `V-*` partners; both were repaired, not suppressed.
- Kernel measurement, two-sided: `abi: 4`, `add_rule(NET_PORT) rc: 0`, `rule struct size: 16`,
  `allowed connect ok: True`, `denied connect refused: True [Errno 13] Permission denied`,
  `RESULT: ENFORCED`.
- Refutation of the authored probe design: allowed `40001`, child bound `127.0.0.1:56659`, own-socket
  connect `[Errno 13] Permission denied`.
- Demonstration of the replacement design: `probe rc: 0`, `denied connect refused: [Errno 13]
  Permission denied`, parent listeners `46623`/`46745`.
- Both network rights separately accepted at ABI 4 (`BIND_TCP` fd 3, `CONNECT_TCP` fd 4), which is the
  basis for D-1.
- Simulated E-03 in the working tree and ran the three affected test files:
  `1 failed, 73 passed`; with the `CONTRACT_FIELDS` append, `74 passed`. Working tree restored with
  `git checkout --` and confirmed clean (`git status --porcelain` showed only the plan file).
- `aw host capabilities opencode` run for real: the new-row mechanism confirmed
  (`_capability_rows` introspects `to_dict()`), `grep -c 'REFUSED  '` = 0, bare `grep -c REFUSED` = 1,
  `grep -c deny_push` = 0.
- Probe cost: mean `0.047s` over 5 runs against warm `detect_host_capabilities` of `0.305s`.
- `ast` reference count for `PRESENCE_VS_OBSERVATION`: exactly `[('name', 235)]`.

No production code, test, or configuration file was modified by this review. The only file changed is
the plan, plus this record.
