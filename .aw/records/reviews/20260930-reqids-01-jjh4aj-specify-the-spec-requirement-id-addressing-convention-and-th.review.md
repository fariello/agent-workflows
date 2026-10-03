# Review findings: plan jjh4aj

- Subject-Id: jjh4aj
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-R01 (HIGH, fixed), PR-R02 (HIGH, fixed), PR-R03 (MEDIUM, fixed), PR-R04 (MEDIUM, fixed), PR-R05 (MEDIUM, fixed), PR-R06 (LOW, fixed), PR-R07 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `36bcbfaa3`. The plan file was committed and byte-identical to
the lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` with ZERO findings before semantic review, and
`--phase review-finalize --agent` reports `clean` with zero findings after revision. The plan is
`- Kind: child`, so the `IPD-S407` orchestrator row check does not apply.

THE PLAN'S CENTRAL ARGUMENT IS SOUND AND I RE-MEASURED ALL OF IT. This is an unusually well-grounded plan,
and the most important thing to record is that its decisive, contested claim verifies:

- F-05's hinge, which is what reconciles this Set against research `vkub9o`'s "Do NOT build a requirement
  parser". The production call site in `runner_shared` (located by the content string
  `spec-production-out-of-scope-paths`) really does compute `new_produced_paths` by iterating plan IPDs and
  excluding `baseline_plan_ids`, and really does pass that list into `_pc.spec_plan_conformance` and
  `_pc.spec_plan_gate_carry`. So the produced plan paths ARE in hand when the verifiers run, and `vkub9o`'s
  decisive objection (0 plans carrying `- From-Spec: c4gd2h` against 37 mentioning it, so "the blocker is
  the missing plan-to-spec edge, not the missing requirement parser") genuinely does not reach a check
  scoped to one dispatched spec. The reconciliation is not hand-waving.
- `run_selection_policy._SPEC_ACTIONS` maps ONLY `approved` to `ACTION_PLAN`, with every other status either
  absent or `ACTION_SKIP`, exactly as F-03 claims. So the population TRACE can judge is the 12 approved
  specs, not the corpus.
- The corpus: 38 specs recursively, 20 live, 12 approved. F-02's two named specs (`25kzda`, `kw5y2s`) carry
  no requirement-id declaration lines. F-03's "10 of 12 approved carry requirement ids" and "7 carry
  acceptance ids" both HOLD.
- `25kzda` 4.8's TRACE row, its `RETRY, then FAIL ITEM` action and its message template match the plan's
  quotation verbatim. TRACE has zero enforcement while `spec_plan_count`, `spec_plan_conformance` and
  `spec_plan_gate_carry` are all implemented. `z7nbn1` 4.4 and its OQ-02 revision read as quoted, including
  the "MUST NOT be described as trace-verified" language and the 2026-09-26 maintainer ruling.
- E-09's two mechanisms: `aw ipd dependencies set rtvdak executed:jjh4aj state:spec:approved:25kzda
  --dry-run` validates and reports `unchanged (dry-run)`, and `runner_shared` carries the refusal string
  "is {status!r}, needs exactly {edge.status!r}".
- The cutover mechanism: `config.KNOWN_FEATURE_CUTOVERS` is the single registry, its block comment says
  "Do not invent a second mechanism", and `resolve_cutover_date` reads it.

THE DOMINANT FINDING IS A SELF-CONTRADICTION THAT WOULD HAVE STOPPED THE PLAN, AND IT IS THE ONE PLACE WHERE
RESOLVING IT THE WRONG WAY WAS THE REAL RISK.

PR-R01. OQ-01 carries `- Blocking: no` together with a resolution arguing at length that blocking "would
demand the decision TWICE from the same human". Two other sites assert the opposite: F-08's cell ends "so it
is OQ-01 and it is BLOCKING", and the gate's own paragraph reads "OQ-01 IS BLOCKING AND IS NOT A WORDING
DETAIL ... this plan is not ready to execute until the maintainer answers". The `- Blocking:` FIELD is what
every gate reads, so the prose was asserting a stop nothing implements. I resolved it in favour of `no` and
recorded the judgement as OQ-04 rather than burying it in a diff, because the two readings differ by whether
the plan can execute at all. Three pieces of evidence decide it: the deliverable ships at `to-review` and
cannot reach `approved` except by `--by-human`, so the human decides once at the spec review where E-08 puts
the question; the runner enforces the gate independently through the `state:spec:approved:<id6>` edge E-09
writes, which `edge_satisfied` refuses until the status matches, so Order 02 cannot consume an unratified
decision; and setting the field to `yes` would make `aw ipd lint` report `IPD-Q501` at every checkpoint
including `author`, holding the plan whose only output is the artifact that surfaces the question. The
maintainer ruling of 2026-09-10 (`qhy3i3` OQ-01) is explicit that the flag records which questions must stop
work. I stated the rejected alternative in OQ-04 so a maintainer can overrule it.

PR-R02 is a measurement error inside the plan's own evidence, and it matters because E-07's
grandfathered-PASS requirement rests on it. F-09 claims 5 approved specs use `AC`/`A`-prefixed acceptance
ids, 5 have an acceptance section with no ids, and 2 have no acceptance section. Re-measured: SEVEN carry
acceptance-like ids, FOUR have a section with none, ONE has no section. Three specific errors: `2vev8j` is
listed as having no ids while declaring 11 `AC-N` table rows; `25kzda` is listed as having no acceptance
section while carrying 4 `A<n>:` rows (in a table, under no acceptance heading, which is why its
classification needs care in both directions); and the totals therefore mis-sum. The sharpest point is that
F-09 CONTRADICTED F-03, which independently states "7 carry acceptance-criterion ids" and is correct. The
conclusion F-09 supports (the acceptance half is structurally weaker) survives on a cleaner margin: five of
twelve lack usable acceptance ids against two lacking requirement ids.

THREE FURTHER CORRECTIONS AND TWO SMALLER FIXES.

PR-R03: V-09 required confirming "the after-minus-before failing node-ID set is empty against the authoring
baseline `3387 passed, 2 skipped`". Measured: `1 failed, 3446 passed, 2 skipped`. The count moved by 59 and
there is one pre-existing failure, `tests/test_backlog.py::BacklogPreservationTests::
test_release_exempt_setter_roundtrip_and_parity`, a filed local-versus-UTC history-clock defect owned by
backlog `fnb8pl`. Both halves of V-09's bar were therefore unmeetable: the absolute is stale and the
empty-failing-set demand would stall the executor on another item's defect.

PR-R04: E-09 writes Order 02's `- Item-Dependencies:` and therefore edits
`.aw/records/plans/pending/20260930-reqids-02-rtvdak-...ipd.md`, which matches neither declared scope entry.
I verified this does NOT cause a commit refusal, because `ipd_lifecycle._is_implicitly_allowed` admits it
under `.aw/records/plans/**`, but `aw ipd finalize` reconciles actual against declared, so a
`--scope-reason` is owed and the plan never said so. I also verified the good half: the declared
`.aw/records/specs` directory entry DOES match a new spec under both `specs/draft/` and `specs/to-review/`,
so the setter's relocation stays in scope.

PR-R05: E-06 says "five features are registered this way" and then lists six, while the sibling conventions
bullet lists a different five. Measured: the registry carries six keys, this repository stamps five (all but
`setid_length`), and `config.py`'s own block comment still says "three shipped features use this one". So
the number is drifting in the SOURCE, which makes it exactly the wrong thing for a new spec to restate.
E-06 now names the mechanism and the key and forbids restating a count without saying which set it counts.

PR-R06: F-11's five-plan `25kzda` co-editor list is stale, and the Set parent's own review had already
measured it as "partly false and stale" (`00pirb` executed; `mt54wr` and `6uhtko` never declared that path;
13 pending plans declare it now). The conclusion is strengthened rather than weakened, since more plans
contend for that file than the row claims, so E-07's adopt-rather-than-amend recommendation rests on a
larger margin. PR-R07: the gate instructed moving the plan to `executed/` "through the tooled transition
(`aw ipd finalize` / the runner's self-finalize)", which names both owners without saying which applies;
rewritten to the house conditional-owner form.

ONE THING I CHECKED AND DID NOT FLAG. The plan proceeds where `vkub9o` recommends against a parser, and the
gate flags that as "the one thing a reviewer should push on". I pushed on it and the plan wins: the ruling
postdates the survey by six days and directs "the convention and parser ... as its own spec" (`z7nbn1`
OQ-02 as revised, 2026-09-26, with SR-003 in the spec's review record saying the same), and the survey's
decisive objection is measurably out of reach of a production-scoped check. The plan also handles the
remaining risk honestly: E-02 is written so that if the produced paths turn out NOT to be in hand, the
legitimate outcome is a spec recording TRACE as still unbuildable. That is the right shape for a plan whose
premise could be falsified at execution.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-R01 | HIGH | IN-SCOPE | G. Plan executability (blocking-classification truthfulness) | OQ-01 `- Blocking: no` versus F-08's "it is OQ-01 and it is BLOCKING" and the gate's "this plan is not ready to execute until the maintainer answers"; `ipd_lint` `IPD-Q501`; maintainer ruling `qhy3i3` OQ-01 | The plan contradicts itself on whether OQ-01 blocks, in the direction that would stop it. The field is what the machinery reads, so the prose asserted a stop nothing implements; resolving it the other way would have held a plan whose only output is the artifact that surfaces the question for decision. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added F-12 and OQ-04 recording the judgement, its three pieces of evidence and the rejected alternative. F-08's cell and the gate paragraph corrected to non-blocking with the reason; the FIELD left as the author wrote it. |
| PR-R02 | HIGH | IN-SCOPE | D. Anti-regression (evidence that is wrong) | F-09 versus re-measurement: 7 carry acceptance-like ids (`7ckptx` 36, `6kwd2e` 49, `uonrjg` 25, `w15vzb` 12, `6m4kow` 11, `2vev8j` 11, `25kzda` 4), 4 have a section with none, 1 has no section | F-09's breakdown is wrong in three places and CONTRADICTS F-03's correct "7 carry acceptance ids". `2vev8j` declares 11 `AC-N` rows yet is listed as having none; `25kzda` carries 4 `A<n>:` rows yet is listed as having no acceptance section. E-07's grandfathered-PASS requirement rests on this row. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-13 with the measurement and the three errors; F-09 corrected in place and reconciled with F-03; E-01 now names the corrected breakdown as the third claim to confirm and flags `25kzda`'s table-rows-without-a-heading shape as the trap. |
| PR-R03 | MEDIUM | IN-SCOPE | E. Testing and verification | V-09's "`3387 passed, 2 skipped` at HEAD `764442f7`" and "failing node-ID set is empty"; measured `1 failed, 3446 passed, 2 skipped`; backlog `fnb8pl` | Both halves of V-09's suite bar are unmeetable: the pinned absolute is stale by 59 tests, and the suite carries one pre-existing unrelated failure, so an empty-failing-set demand would stall the executor on another item's defect or invite a false claim. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-14. V-09 and the validation preamble now require a self-measured baseline compared by failing node id, name the `fnb8pl` failure as expected in both runs, and forbid investigating it, fixing it, or claiming a green suite. |
| PR-R04 | MEDIUM | UNDER-SCOPE | G. Plan executability (scope fence) | `_scope_match` returns False for Order 02's path against both declared entries while `_is_implicitly_allowed` returns True via `.aw/records/plans/**` | E-09 edits a file the plan does not declare. It will not be refused at commit, but `aw ipd finalize` reconciles actual against declared, so a `--scope-reason` is owed and the plan never said so. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-15. The Scope check records the undeclared-but-allowed status, supplies the exact `--scope-reason`, forbids silencing it by widening `- Scope-Paths:` (D141), and records the verified good half (the `specs` entry matches both `draft/` and `to-review/`). V-09 requires the reason be stated. |
| PR-R05 | MEDIUM | IN-SCOPE | G. Plan executability (live counts) | E-06's "five features" over a six-item list; the conventions bullet's different five; `config.py`'s "three shipped features"; `project.json` stamps five of six | Three different counts of the same registry appear across the plan and its source, so an executor cannot tell which is real, and a new spec restating any of them would be stale on arrival. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-16. E-06 now states registered-versus-stamped explicitly, forbids restating a count in the spec, and requires re-derivation with the counted set named if a figure is genuinely wanted. |
| PR-R06 | LOW | IN-SCOPE | G. Plan executability (stale citation) | F-11's five-plan list; the parent `9wzlou`'s review measuring it "partly false and stale" with 13 pending plans now declaring the path | The `25kzda` co-editor census is stale, and the Set's own parent review had already measured it so. The conclusion is strengthened rather than weakened. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-11 corrected in place with the parent's measurement cited and a re-derive instruction, noting the conclusion rests on a larger margin. |
| PR-R07 | LOW | IN-SCOPE | G. Plan executability (execution contract) | the gate's "through the tooled transition (`aw ipd finalize` / the runner's self-finalize)" | Names both possible owners without saying which applies, so a runner-driven executor could race the runner's own finalize. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten to the house conditional-owner form, with a pointer to the `--scope-reason` finalize will ask for. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01's field says non-blocking and two prose sites say blocking. Correct the prose, or set the field to `yes`? | Correct the PROSE; leave the field as the author wrote it. Recorded in the plan as OQ-04 with the alternative stated. | Set `- Blocking: yes` and hold the plan until the maintainer answers (defensible, costs only latency, and would let E-04/E-07 write a settled rule instead of a recommendation). | The deliverable ships at `to-review` and cannot reach `approved` except by `aw spec set approved --by-human`, so E-08 puts the question where the authority sits and the human decides ONCE. The runner enforces the gate independently: E-09's `state:spec:approved:<id6>` edge makes `edge_satisfied` refuse Order 02 until the status matches. And `- Blocking: yes` fires `IPD-Q501` at every checkpoint including `author`, per the 2026-09-10 `qhy3i3` ruling that the flag records which questions must STOP work. | yes |
| D-2 | F-09 contradicts F-03 on acceptance-id counts. Which is authoritative? | F-03. F-09 corrected in place to match re-measurement. | Trust F-09 (would leave E-07's grandfathered-PASS requirement resting on a false population); leave both and let E-01 adjudicate (an executor would not know which to re-derive against). | Direct measurement over the 12 approved specs at review HEAD: `2vev8j` declares 11 `AC-N` table rows and `25kzda` 4 `A<n>:` rows, so seven specs carry acceptance-like ids. F-03's independent figure of 7 matches; F-09's 5 does not. | yes |
| D-3 | V-09's suite bar is unmeetable. Relax it, or hold it? | Relax to a self-measured baseline compared by failing node id, with the pre-existing failure named. | Hold the empty-failing-set bar (stalls the executor on backlog `fnb8pl`'s defect or invites a false claim); let the executor fix `fnb8pl` in passing (out of scope, has an owner, and this plan ships no code at all). | Measured `1 failed, 3446 passed, 2 skipped` on an unmodified tree, with the failure owned by `fnb8pl` as an `open` `bug`. The delta form is STRICTER about this plan's own effect (no new failing id) while no longer failing on unrelated redness, and P16's "never weaken an assertion so it passes everywhere" is not breached because the assertion about THIS plan tightens. | yes |
| D-4 | Order 02's plan file is edited but undeclared. Add it to `- Scope-Paths:`, or record the reason? | Record the `--scope-reason` and leave the declaration frozen. | Add the path to `- Scope-Paths:` (silences the finalize prompt but destroys the said-versus-did signal D141 exists to preserve); drop E-09's edge write (removes the Set's only machine-enforced human gate, which the parent's review added deliberately). | `_is_implicitly_allowed` already admits any `.aw/records/plans/**` path, so no commit is refused; the only obligation is finalize's reconciliation, whose sanctioned answer is a stated reason. The id6 does not exist until E-03 mints it, which is precisely why Order 02 could not declare the edge itself. | yes |

No `Reversible: no` decision was taken in this round, so no escalation is owed under the irreversible-decision rule.

### Escalations

None. Every finding is `FIXED`, so no finding at or above the `HIGH` gate threshold is left `OPEN` or
`DEFERRED`. OQ-01, OQ-02, OQ-03 and OQ-04 are all `- Blocking: no` and none gates readiness (maintainer
ruling of 2026-09-10, plan `qhy3i3` OQ-01). The three design recommendations OQ-01 through OQ-03 carry are
ratified by the human at the SPEC review of the artifact this plan produces, not here.
