# Review: require an affirmative or negative defect report from every execute turn, child b7xarm (Set defreport)

- Subject-Id: b7xarm
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `62bf603f`. Structural preflight `aw ipd lint --phase author` conformed (clean, 0 findings)
before semantic review, and `--phase review-finalize` conformed after the revisions. The plan carries no
`- Blocks-Release:` and no `- From-Backlog:`, both legitimately: it was authored on a maintainer ruling
given while answering `rnkqrc` OQ-01, and it says so explicitly rather than leaving the absence to be
guessed.

DISCLOSURE: authored in the same repository and by the same model family as the plan, so treat this as a
near-self-review and worth less than an independent one.

THE PLAN'S CORE ARGUMENT IS RIGHT AND I VERIFIED THE PREMISE INDEPENDENTLY. An empty
`incomplete_requirements` really is indistinguishable from an unasked question, the field really is
scoped to this plan's own unmet requirements, and no code path treats silence as a defect. I also
measured the SIZE of the problem, which the plan asserted but never quantified: of 188 execute-turn
outcome files, 101 carry an empty list, 86 carry a non-empty one, and 1 omits the key. Those 101 empties
are the ambiguity, and they are most of the corpus.

THE FINDING THAT MOST CHANGES THE PLAN IS THAT ITS HEADLINE MEASUREMENT IS OFF A DIFFERENT FIELD, AND THE
TRUTH IS WORSE. The plan leans four times on "132 dicts against 131 strings out of 263" as evidence that
agents miss an element shape about half the time. That figure is `rbftpl`'s measurement of `tests_run`, a
VERIFIER-outcome field written by 35 verification files, and this plan's own Scope explicitly EXCLUDES the
verifier turn. On `incomplete_requirements`, the execute-turn field this plan sits beside, the count is
210 entries, ZERO dicts, 210 bare strings: 100% prose, because the literal shows `[]` and never an
element. This strengthens the plan rather than weakening it (coercion is the normal path, not an
exception, and the literal must SHOW a filled element), but the plan as authored rested a design argument
on a number a reader could check and find inapplicable.

THE SECOND HIGH FINDING WOULD HAVE BROKEN THE SUITE ON THE FIRST EDIT. E-02 says to add prompt text
"alongside the existing outcome-JSON block", and the natural reading of "add to the prompt" is to append.
`tests/test_reporting_contract.py::test_all_prose_surfaces_are_byte_equal_to_the_source` finds the
reporting-contract heading in each built prompt and asserts that everything from there TO THE END is
byte-equal to `contract_text()`, on both hosts, so anything appended after it fails. Verified safe: the
outcome literal is at index 3465 and the contract begins at 3758, so extending in place is legal and
`prompt_block()` must remain last. `tests/test_lane_prompt_purity.py` additionally digest-pins a bounded
early block on both drivers. The plan now names the one legal seam and both tests.

THE THIRD HIGH FINDING IS THAT E-05'S "NEW MACHINERY" IS HALF ALREADY BUILT, AND THE TWO HOSTS SPELL IT
DIFFERENTLY. There is genuinely no re-ask loop, so that part is correct. But session resume exists on both
hosts: `oc_runipd` passes `--session <id>`, `agy_runipd` passes `--conversation <id>` with `--continue` as
a fallback, and both already capture the id per attempt. A shared step hardcoding `--session` would
silently fail on agy, which is exactly the one-sided-guard defect class this repo has been bitten by
before. Three existing session rules also constrain the re-ask and were unstated: an isolated turn is
ALWAYS a fresh session by deliberate decision (the recorded measurement is that four consecutive lanes
were lost proving it), `max_items_per_session` (default 4) rotates a session away, and a re-ask consumes a
turn against that counter. All three must be answered in writing or they are live-run bugs.

I ALSO CHECKED THE HANDOFF THE PLAN EXISTS TO SERVE, AND IT IS NOT YET REACHABLE. `rnkqrc` declares only
`check_engine.py`, `ipd_lint.py`, `ipd_schema.py` and its test file, and its E-01 through E-04 read the
PLAN FILE's typed fields. Its own history says its predicate "should additionally read the NORMALIZED
report `b7xarm` E-06 persists on the run record", which lives in `.aw/records/runs/` and none of its
declared modules reads. So E-06 is necessary but not sufficient, and the missing reader is on `rnkqrc`'s
side of the seam. The dependency direction is correct (`rnkqrc` declares `executed:b7xarm`), so the
ordering is sound; the gap is scope, not sequence.

THE SUITE BASELINE WAS STALE IN THE DIRECTION THAT MATTERS. The plan expects `5859 passed` with no
failure; the real state is `1 failed, 5958 passed, 3 skipped, 2 xfailed`, failing at
`test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`
because of the gitignored `opencode-recovery/` tree of another party's transcripts. An executor expecting
a clean baseline could read a co-worker's artifacts as their own regression, or delete files that are not
theirs. Corrected with an explicit do-not-clean-up prohibition and a node-id comparison.

Two useful things the plan did not know it had: `reporting_contract.py` is an exact precedent for one
canonical constant shared by these two prompts with byte-equality enforced by test, which turns V-02's
host symmetry from an eyeballed diff into a structural assertion; and `.aw/records/runs/` is gitignored,
which `rbftpl` already learned the hard way, so E-07 must use a tmp_path fixture.

VERIFIED CORRECT AND LEFT ALONE: the 18-key outcome literal on both hosts (identical key lists today,
compared by no test), the four prompt builders, `incomplete_requirements`'s live reader in `run_viewer`,
the `except Exception: pass` anti-pattern (real, though at `:4202-4206` not the cited `:4149-4151`), D139
as maintainer-approved, and OQ-03's reasoning, which is sound and needed no change.

Eight findings, all FIXED in place, no deferrals. No new open questions: the three existing ones are
correctly dispositioned, and OQ-01 already states the plan's honest limit better than I could.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-A01 | HIGH | IN-SCOPE | Evidence accuracy; E. testing | `tests_run` -> 263 entries, 132 dicts / 131 strings across 35 verification files; `incomplete_requirements` -> 210 entries, 0 dicts / 210 strings across 188 execute-turn files; plan Scope excludes the verifier turn | **THE HEADLINE 50% MEASUREMENT IS OFF A FIELD THIS PLAN EXPLICITLY EXCLUDES, AND THE REAL RATE IS 100%.** The 132/131 figure is `rbftpl`'s measurement of the VERIFIER field `tests_run`. On `incomplete_requirements`, the execute-turn field this plan extends, every one of 210 entries is a bare string and none is a dict, because the literal shows `[]` with no element. The plan leans on the wrong number four times. This strengthens the design (coercion is the normal path; the literal must SHOW an element) but the authored version rested on evidence a reader could falsify | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Concern corrected with both measurements and the reason they differ; E-01 must show a filled example element; E-04 reframed so coercion is expected rather than exceptional; new F-12; conventions and required-tests carry the re-measurement; the 101/86/1 empty-versus-filled split added as the size of the problem |
| PR-A02 | HIGH | IN-SCOPE | D. anti-regression; E. testing | `test_reporting_contract.py::test_all_prose_surfaces_are_byte_equal_to_the_source`; measured indices (outcome literal 3465, contract 3758); `test_lane_prompt_purity.py` bounded digest over both drivers | **THERE IS EXACTLY ONE LEGAL PLACE FOR THE NEW PROMPT TEXT AND THE OBVIOUS MOVE BREAKS THE SUITE.** The parity test asserts everything from the reporting-contract heading to END-of-prompt is byte-equal to `contract_text()` on both hosts, so appended prose fails. A second test digest-pins a bounded early block. E-02 said only "alongside the existing outcome-JSON block", which is correct but does not warn that appending is fatal | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-02 names both tests, states that `prompt_block()` must remain last, records the verified indices proving in-place extension is legal, and drops the stale line numbers in favor of symbol re-location; V-02 requires both prompt tests pasted passing and the end-of-prompt invariant shown; new F-13 |
| PR-A03 | HIGH | UNDER-SCOPE | C. architecture; A. correctness | `oc_runipd.run_opencode` argv `--session`; `agy_runipd.run_agy_turn` argv `--conversation`/`--continue`; `isolated_turn = bool(work_dir)` with its four-lost-lanes note; `max_items_per_session` default 4 | **THE RESUME PRIMITIVE ALREADY EXISTS ON BOTH HOSTS AND THEY SPELL IT DIFFERENTLY, and three existing session rules constrain the re-ask.** The plan implies the whole mechanism is new; only the loop is. A shared step hardcoding `--session` fails silently on agy. Unstated and load-bearing: an isolated turn is ALWAYS a fresh session by deliberate decision, `max_items_per_session` may already have rotated the target session away, and a re-ask consumes a turn against that counter | C:Medium; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-05 rewritten to reuse each host's existing argv path via a per-host resume adapter, and to answer all three session rules explicitly; V-05 requires both hosts' argv shown and the three answers in writing; new F-14 |
| PR-A04 | MEDIUM | UNDER-SCOPE | C. architecture; F. KISS | `agent_workflows/reporting_contract.py`; `tests/test_reporting_contract.py` (import-not-inline, byte-equality of every surface) | **THE PRECEDENT FOR ONE CANONICAL CONSTANT SHARED BY THESE TWO PROMPTS IS ALREADY IN THE TREE AND UNCITED.** `reporting_contract` solves exactly E-01/E-02's problem and its test makes host symmetry structural. Without it, V-02's byte-identical requirement is an eyeballed diff | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 directs reuse of that shape with an explicit warning NOT to extend that module (its documented fence is user-facing prose, not machine output); spec-sync and conventions cite it; V-02 prefers a shared-constant proof over a diff; new F-15 |
| PR-A05 | MEDIUM | IN-SCOPE | G. executability; C. architecture | `rnkqrc` `Scope-Paths` (four modules, no runner path); its E-01..E-04 read plan-file fields; its 2026-09-09 history asking for the run-record read; `Item-Dependencies: executed:b7xarm` | **THE HANDOFF THIS PLAN EXISTS FOR IS NOT REACHABLE BY THE CONSUMER AS SCOPED.** `rnkqrc`'s predicate reads the plan file; the normalized record E-06 writes lives in `.aw/records/runs/`, which none of its declared modules reads. Ordering is correct, scope is not, and a reviewer of the pair should see it | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06 states the gap plainly, requires the record's location and shape be DOCUMENTED as the contract `rnkqrc`'s executor codes against, and forbids reaching across; a Deferred entry names the missing reader as that plan's side; new F-16 |
| PR-A06 | MEDIUM | IN-SCOPE | E. testing; Evidence accuracy | bare pytest at `62bf603f` -> `1 failed, 5958 passed, 3 skipped, 2 xfailed`; `.gitignore` `opencode-recovery/`; `rbftpl` graduation note on the gitignored run tree | **THE SUITE BASELINE CLAIMS A CLEAN RUN AND THERE IS A PRE-EXISTING FAILURE, and the test corpus this plan wants to read is gitignored.** The plan expects `5859 passed` with no failure. The real failure is the reporting-contract parity test, caused by another party's gitignored transcript tree. Separately, `rbftpl` already recorded that a test reading `.aw/records/runs/` passes on one box and fails in CI | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Required-tests carries the re-measured baseline, the real node id, the cause, a do-not-clean-up prohibition under the shared-checkout rule, and node-id rather than count comparison; E-06/E-07 and V-06/V-07 require tmp_path fixtures; new F-17 |
| PR-A07 | LOW | OVER-SCOPE (pre-empted) | B. security lens; C. architecture | `host_sandbox_profile.py` sets `supports_session_resume` for opencode only; agy resumes via `--conversation`; `ACTION_CAPABILITY_REQUIREMENTS` requires it for no action class | **A CAPABILITY FIELD MISDESCRIBES REALITY AND WIRING THE RE-ASK TO IT WOULD WRONGLY REFUSE AGY.** The obvious "correct" instinct for a new host-dependent step is to gate it on the descriptor. That field is opencode-only, agy demonstrably resumes, and the field gates nothing today | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 explicitly forbids gating on it and forbids fixing it here (`host_sandbox_profile.py` is undeclared); a Deferred entry and F-18 record the discrepancy for a human |
| PR-A08 | LOW | IN-SCOPE | Evidence accuracy | measured by symbol: `agy_runipd.build_prompt` `:2343` not `:2297`; `item["last_outcome"]` `:6654` not `:6641`; the bare-except anti-pattern `:4202-4206` not `:4149-4151` | **THE PLAN WARNS THAT LINE NUMBERS DRIFT AND THEN CITES THREE THAT ALREADY HAD.** Harmless individually, but this plan's whole thesis is that unverified claims decay, and its own citations are the nearest instance | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The three stale citations replaced with re-locate-by-name instructions plus review-HEAD values where useful; F-19 records which were stale and which verified correct (18 keys, both literals, four builders, the anti-pattern's existence) |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The plan's headline shape measurement is off an excluded field (PR-A01). Rescope the plan to cover the verifier field too, or correct the evidence? | CORRECT THE EVIDENCE and keep the scope. Measure the field this plan actually extends (100% prose) and let that strengthen E-01/E-04 | Widen scope to the verifier outcome so the cited measurement applies (rejected: the plan's Deferred section excludes the verifier turn because three reviewed plans `1bfppy`/`bxx9af`/`fzxfph` are already editing that path, so widening would collide with all three); keep the figure with a caveat (rejected: it would still be evidence for a claim about a different field) | `tests_run` 132/131 of 263 on 35 verifier files; `incomplete_requirements` 0 dicts / 210 strings on 188 execute files; plan Scope and Deferred | yes |
| D-2 | E-05 needs same-session re-ask and the two hosts resume differently (PR-A03). Prescribe a per-host adapter, or leave the mechanism to the executor? | PRESCRIBE the per-host adapter and require both argv spellings be proven, because the failure mode is SILENT on agy and would be found only on a live agy run | Leave it open as an implementation detail (rejected: the measured history in this repo is that one-sided guards ship and go unnoticed, which is why `test_lane_prompt_purity` is parameterized over both drivers); gate on `supports_session_resume` (rejected: that field is opencode-only and would refuse agy wrongly, see D-3) | `run_opencode` `--session`; `run_agy_turn` `--conversation`/`--continue`; both capture ids per attempt | yes |
| D-3 | Should the re-ask be gated on `HostSandboxCapabilities.supports_session_resume`? | NO. Forbid it in the plan and report the field's inaccuracy instead of fixing it | Gate on it (rejected: it is TRUE for opencode only while agy demonstrably resumes, so the gate would refuse a capable host); fix the field in this plan (rejected: `host_sandbox_profile.py` is not in `Scope-Paths`, and the field gates no action class today, so the fix is neither necessary here nor safe to smuggle in) | capability assignment in `host_sandbox_profile.py`; `ACTION_CAPABILITY_REQUIREMENTS` contains no session-resume requirement | yes |
| D-4 | `rnkqrc` cannot reach E-06's record with its declared scope (PR-A05). Add the reader here, or flag it? | FLAG IT and document the record's location and shape as the contract the other plan codes against | Build the reader in this plan (rejected: `rnkqrc` owns the consuming side, the plan's own Deferred section says so, and adding it here would need `check_engine.py`/`ipd_lint.py` which are not in this plan's `Scope-Paths`); say nothing (rejected: the pair's whole value depends on the seam, and a reviewer of one must be able to see the other's gap) | `rnkqrc` `Scope-Paths` and E-01..E-04; its history's request; `Item-Dependencies: executed:b7xarm` | yes |
