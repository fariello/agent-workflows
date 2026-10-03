# Review findings: plan h65phz

- Subject-Id: h65phz
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-301 (HIGH, fixed), PR-302 (MEDIUM, fixed), PR-303 (MEDIUM, fixed), PR-304 (MEDIUM, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `fc91266df`. The plan file was committed and the tree clean,
so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author --agent` reported
`conforming` (exit 0, zero findings) BEFORE semantic review; `--phase review-finalize` reports
`conforming` after revision, and `ipd_lint.check_density` reports zero advisories. This plan's own first
`- Kind:` bullet reads `child`, so the `IPD-S407` orchestrator child-row check does not apply.

I RE-DERIVED EVERY LOAD-BEARING CLAIM rather than trusting it. The plan's diagnosis is correct and its
design is sound; everything below is a measured correction or widening, not a disagreement with its shape.
What reproduces:

- F-01 reproduces verbatim: the spec's transcription note is present as quoted, and
  `tests/test_run_evidence_completion.py` does not exist.
- F-02 reproduces: `19313eed` removed the file whole and `19313eed^` still contains
  `test_inspects_and_pass_criterion_are_verbatim_from_the_spec`.
- F-04 reproduces: `runner_shared.py` carries the quoted docstring claim, and
  `agy_runipd.build_parser().parse_args(["start","someid"]).dangerously_skip_permissions` is `True`, so
  the shipped default is correct and only the claim is wrong.
- F-05 reproduces and is a genuine import-time hazard: the legacy glob
  `20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` matches `[]` while `*-25kzda-*.spec.md`
  matches exactly one path, so copying the deleted line forward would raise `StopIteration` at collection.
- F-06's conclusion reproduces (12 rows parsed, code sets equal both directions, zero mismatches on all
  four cells) but only under a specific normalization rule the plan never states; see PR-304.
- F-07 reproduces: `_replace`-ing `RUN-BASELINE-OWNERSHIP`'s `pass_criterion` makes byte equality return
  `False`, so the mutation demonstration E-02 promises is achievable.
- F-08's collision claim reproduces and is still current: `xjmjq4` is `pending` with `- Status: approved`
  and `- Readiness: go-pending-approval`, and `tests/test_run_finding_abort_partition.py` does NOT exist,
  so E-01's adapt-at-runtime branch is the right shape.
- F-09 reproduces: `a6i03f` is `reviewed`/`no-go`, `f7z10q` is `reviewed`/`go-pending-approval`.
- The `check.scope-path-target-stale` (`error`) and `check.review-dangling` (`warning`) precedents the
  plan cites are both registered as described, with the latter's comment carrying the blast-radius
  reasoning E-06 weighs.
- The `xvp5vx` carrier resolves: backlog item `xvp5vx` is `graduated` with `- Graduated-To: xvp5vx`, and
  plan `oyh28b` under that Set is `pending`/`to-review`, so the carrier references are live.
- Full bare suite at review HEAD: `3674 passed, 2 skipped, 3 warnings in 80.94s`.

I also independently reproduced the whole spec-versus-module comparison the plan's E-01 will build, which
is how PR-304 was found, and ran the zone census that resolves the plan's one open question.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | HIGH | IN-SCOPE | A (correctness); C (operability) | scripted citation scan over the spec with a zone test keyed on the `## Workflow history` heading (line 1604): `GONE BODY 232`, `GONE BODY 824`, `GONE BODY 1251`, `GONE HISTORY 1621` twice | The spec has a FOURTH dangling citation site the plan did not find: line 1621, a dated 2026-09-21 `## Workflow history` note citing `tests/test_run_flag_surface.py` twice. Two consequences, both breaking as written. FIRST, E-04's Expected outcome ("No `tests/test_*.py` path cited anywhere in spec `25kzda` is missing from disk") is UNACHIEVABLE without rewriting a dated record, which `AGENTS.md` and this plan's own Deferred reasoning both forbid. SECOND, and worse, E-06's rule as scoped would FLAG that line, so the new `error` rule lands RED on the very file E-04 just corrected, blocking integration for every concurrent lane. The plan specifies no history-zone exemption. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-10 records the site and the zone. E-04's Expected outcome rewritten to be BODY-SCOPED with an explicit instruction to leave the history notes byte-unchanged. E-06 given a HARD history-zone exemption with the same historical-record argument it already uses to exclude the plans tree, plus a third required test case (a history citation to a nonexistent path must be SILENT). V-04 rewritten to demand a zone verdict per path and to state that a whole-file "zero missing" result is a FAILURE of the validation because it means a dated record was rewritten. V-06 now requires all three cases. |
| PR-302 | MEDIUM | IN-SCOPE | G (plan executability) | per-file zone census over `.aw/records/specs/**/*.spec.md`: `25kzda` `{body: 3, history: 2}`; the five other affected specs `{history: 1}`, `{history: 1}`, `{history: 1}`, `{history: 1}`, `{history: 2}`; `spec files with a dangling citation in the BODY: 1` | OQ-02 was the plan's only open question, left `open` with a decision rule on the premise that six spec files carry eight dangling paths so an `error` rule would land red. The census is right and its ZONE BREAKDOWN answers the question the plan deferred: of 11 dangling spec citations, 8 are in `## Workflow history` and only 3 are in a body, and ALL THREE body hits are in `25kzda`, the file E-04 corrects. So a body-scoped `error` rule is clean by construction, and the Deferred row's warning that the other five specs "must be" amended under an `error` rule is false. Leaving this open ships an unresolved decision whose answer was one measurement away. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-11 records the breakdown. OQ-02 moved to `resolved` with `Owner: reviewer`, resolving to `error` and body-scoped, with the original authoring rationale PRESERVED beneath (its reasoning was sound; only the missing measurement held it open) and its decision rule retained as a safety net requiring re-measurement at execution. E-06 now registers `error` on that basis. The Deferred spec-amendment row corrected to `Carrier-Declined` with the measured reason. The plan now carries no open question. |
| PR-303 | MEDIUM | UNDER-SCOPE | A (correctness); B (security) | `grep -rn test_run_flag_surface agent_workflows/runner_shared.py` returning SEVEN lines; `grep -rn test_lane_permission_posture agent_workflows/agy_runipd.py` returning the comment "Do NOT 'harden' it: `tests/test_lane_permission_posture.py` PINS the default"; per-module count `runner_shared.py -> 7`, `agy_runipd.py -> 1` | F-04 names one docstring and E-05 scopes itself to "`runner_shared.py`'s module docstring". The same false-guard claim appears at SEVEN sites in that file (the docstring plus six inline comments beside the flag registry and the spec-declaration rule), so fixing one leaves the file still asserting it six more times. An EIGHTH site sits in `agy_runipd.py`, and it is the one most likely to cause harm: it instructs a maintainer not to harden a security-relevant permission default on the strength of a guard that does not exist. | C:Low; U:Low; S:Medium; F:Low; Overall:Low | FIXED | F-12 records the census and both modules. E-05 widened to all seven `runner_shared.py` sites, with an added instruction to PRESERVE each site's underlying requirement (a new flag must still be declared in spec 2.1 in the same change) rather than dropping it with the false guard claim. V-05 now requires the grep census before and after plus a quotation at the docstring AND one inline site. The `agy_runipd.py` site is NOT folded in (undeclared path, different module) and is carried to `xvp5vx` on its own Deferred row naming why it matters most; V-05 requires `git diff --stat` proof that file is untouched. |
| PR-304 | MEDIUM | IN-SCOPE | E (testing) | per-column backtick-wrap census: `message` 12/12 fully wrapped, `inspects` 0/12, `pass_criterion` 0/12, `action` 0/12; `RUN-SCOPE-DELTA`'s `inspects` corrupted to `'git diff` and untracked paths...'` under unconditional stripping; both-ends rule re-measured at 0 mismatches on all four columns | F-06 describes the parse as "five cells with backticks stripped" and reports zero mismatches. That holds only under a rule the plan never states. The columns are NOT uniformly wrapped, so an unconditional `.strip('`')` corrupts `RUN-SCOPE-DELTA`'s `inspects` (which legitimately BEGINS with a backtick) and stripping nothing reports TWELVE false mismatches on `message`. E-01's non-vacuity guard does not catch either case: a mis-normalized parse still yields 12 rows and the correct code set, so it passes that guard and then fails on cell comparison, which an executor would most plausibly misdiagnose as a real spec/module divergence and "fix" by editing a cell, which this plan's scope forbids. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-13 records the per-column census and the corrupted value. E-01 now SPECIFIES the both-ends normalization rule, requires it be stated in the test module, and names the misdiagnosis an executor would otherwise make; its Expected outcome adds "if cell comparison fails at this HEAD, suspect the normalization rule before concluding the spec and module have diverged". V-01 now requires the normalization be quoted and confirmed as the both-ends rule, with the measured reason recorded so a later reader cannot simplify it back. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-02 was left `open` with a decision rule. Resolve it at review, or leave it for execution as the plan intended? | RESOLVE it to `error`, body-scoped, keeping the decision rule as a safety net. | (a) Leave it open, honoring the plan's deliberate choice. (b) Resolve it to ADVISORY to be safe. | The workflow permits resolving a HOW question only when the resolution cites a DEMONSTRATION on the concrete case, which is exactly what the zone census is: `spec files with a dangling citation in the BODY: 1`, and that one is the file E-04 corrects. (a) was defensible and I rejected it because the plan deferred on a premise ("an `error` rule would be red") that measurement falsifies, so leaving it open preserves a worry that does not exist and ships an unresolved decision. (b) would register a weaker rule than the evidence supports, and `check.scope-path-target-stale` is the closer precedent for a stale-reference rule on a contract claim. The authoring rationale is preserved verbatim beneath the resolution and the re-measurement requirement is retained, so a tree that has changed by execution still gets the advisory branch. | yes |
| D-2 | The spec's `## Workflow history` carries two dangling citations (PR-301). Correct them, or exempt them? | EXEMPT them, in both E-04 and E-06's rule. | (a) Correct them so the file is wholly clean. (b) Correct them but add a dated note beside each. | (a) is forbidden by the rule this plan already applies to the plans tree and states in its own Deferred row: a dated record of what was measured on its date is not falsified by a later deletion, and rewriting it destroys the audit trail. (b) is incoherent for a history section, whose entries ARE the dated notes. The exemption is also what makes E-06 shippable at all: without it the rule reports the file E-04 just corrected, which would have been discovered only after the rule was registered. | no |
| D-3 | The eighth false-guard site in `agy_runipd.py` (PR-303) discourages hardening a security-relevant default. Fold it into E-05, or carry it? | CARRY it to `xvp5vx`, naming why it matters most. | (a) Add `agent_workflows/agy_runipd.py` to `- Scope-Paths:` and fix it in E-05. (b) Say nothing. | (a) was genuinely tempting because the edit is one comment and the claim is the most consequential of the eight. I rejected it on the declare-then-edit rule: the path is undeclared, so adding it means re-declaring scope on an already five-path plan for a different module, and the plan's own scope reasoning (one false claim class, two artifact kinds) stops being the thing a reviewer assessed. (b) is refused because the site is a live instruction not to make a correctness change. Carried with the measurement and the reason, so the carrier inherits the judgement rather than rediscovering it. | yes |
| D-4 | Is D-1/OQ-01's reading of P16 (restore the guard) sound, since the plan itself flags it as the thing most likely to be wrong? | SOUND; left as written. | Reject the plan's shape and recommend rewording the spec promise instead. | P16's exception reads "Content verification is permissible only where the text or file itself is the artifact under test (for example, verifying published documentation does not cite deleted test files...)", and the parenthetical is almost literally this defect. I additionally VERIFIED the two properties the argument depends on rather than taking them on trust: the comparison reads a SPEC file and `run_evidence`'s exported data, touching no `agent_workflows/*.py` source and asserting nothing about structure or caller counts; and the `message` cells it pins are operator-facing strings a human reads on a failure, which is what makes a divergence user-visible and the item a `bug`. | yes |

### Marked as reversible: no

`D-2` is recorded `Reversible: no` and is escalated here rather than only in the row, per the workflow's
requirement that an irreversible decision not rest on reviewer authority alone. It is judged
irreversible because it establishes, in a registered `aw check` rule and in a spec amendment, that a
dated `## Workflow history` citation is OUT of scope for staleness checking across the whole specs tree.
A later maintainer who disagrees must change a shipped rule's scope and re-amend the spec, not just edit
a plan. I am raising it to the maintainer in this report rather than as a `- Blocking: yes` question in
the plan, which is the honest path in a non-interactive review: adding a blocking question would hold a
plan whose every finding is fixed, and the decision follows directly from a rule the repository already
states for the plans tree. If the maintainer wants history citations checked, the remedy is a scope
change to E-06's rule before execution.
