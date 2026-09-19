# Review findings: plan dpdyed

- Subject-Id: dpdyed
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `352b9201`. The plan on disk was byte-identical to the sealed lane input
(`source_sha256` `0ba5e79b1ab478bdbc33be5866269490c3659ec696e0a69f6e98ff9b46493ac8`, re-computed and
matched) and `git status --short` was empty, so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author --agent` reported `clean`, 0 findings, exit 0; the watermark is
unchanged at 05 (no E-item added; every finding was fixed by strengthening an existing item or
resolving the open question).

DISCLOSURE: same agent/model authored this plan, so this is a SELF-REVIEW, and its value rests on
EXECUTING the claims rather than re-reading them. This round therefore BUILT the grammar E-01
specifies and ran it over the live corpus, BUILT E-02's resolver composition and drove all four of its
required cases against real orchestrators, and read the import graph by AST rather than by eye. Five of
the six findings are things the prose asserted and the code contradicted.

THIS PLAN'S CORE IS SOUND AND ITS CENTRAL CLAIMS SURVIVED EXECUTION, which is worth stating before the
findings. I implemented the R1a grammar as written and confirmed: all five of the parent `d1u4sy`'s rows
conform; the pattern is genuinely anchored (a mid-line `CONFIRM`, a trailing-prose row, and an
over-indented row all fail); a ticked `- [x]` box is tolerated; and across all 12 pending orchestrators
and 38 `E-*` rows, exactly 5 conform and all 5 are the parent's, so the corrected "38 rows across 12
orchestrators, zero conforming apart from the parent" is EXACT. The prior round's PR-003 correction also
holds up under construction: composing `runner_shared.child_table_rows` for Id cells with
`ipd_set_plan.parse_child_table` for the order graph produces all four required E-02 outcomes, and the
six no-`Id` orchestrators each refuse with a usable message naming the missing column. E-05's `rh5tt6`
anchor is verified verbatim, including "the part no child owns" at that plan's line 58.

WHERE THIS REVIEW SPENT ITS EFFORT: two HIGH findings, one of which would have shipped a rule that can
never fire, and one of which resolved an open question the plan had wrongly left to the executor on
reasoning that pointed at the wrong module.

**1. The plan would have shipped a rule that never fires (PR-102, HIGH).** E-04 said to "ADD THE STABLE
RULE CODE to `ipd_lint`'s existing `C_*` block" and stopped there. A `C_*` constant is INERT: I read
`lint_text` and it builds `diags` from an explicit list of eleven `check_*` calls, with
`disposition = CONFORMING if not diags else ERROR`. A rule whose code exists but whose checker is never
called contributes nothing to any disposition, so `aw ipd lint` would keep reporting `conforming` on a
violating orchestrator while every V-item in this plan still passed. That is the worst available outcome
for this Set specifically, because children 02 and 03 would then wire two consumers to a control that
does nothing, and child 05's criterion-1 grep would find the one function and call it proven. E-04 now
requires a `check_*` function CALLED from `lint_text`, gated on `doc.meta_fields.get("Kind")`, and V-04
now demands `aw ipd lint` reporting the new code at a NONZERO exit on a violating fixture plus
non-firing on a `Kind: child` plan, explicitly failing a validation that shows only the constant. A
pleasant side effect I verified: reading Kind from `doc.meta_fields` satisfies this Set's
read-the-plan's-own-bullet rule for free, because `parse` bounds the metadata region rather than
searching the file.

**2. OQ-01 was left open on inverted reasoning, and the repository answers it decisively (PR-101,
HIGH).** The rationale warned that "a shared symbol that the renderer must read cannot live in
`runner_shared` without risking a cycle". Measured: `render_stream` imports ZERO first-party modules
(only `datetime`, `json`, `re`, `signal`, `threading`, `time`), so it reads nothing and no cycle through
it is possible; and `ipd_lint` does not import `runner_shared` anywhere, so there is no cycle in that
direction either. The real constraint runs the OTHER WAY and FORECLOSES one of the two options:
`runner_shared` keeps exactly `{agent_workflows.render_stream, agent_workflows.runner_profiles}` at
module level, and `tests/test_orchestrator_probe_cache.py` asserts that by SET EQUALITY with the failure
message "runner_shared gained a module-level first-party import: ...". So a separate shared module is
not neutral: child 03 would import it from `runner_shared` and BREAK A SHIPPED TEST. `parse_plan_file`'s
docstring states the reason and names five modules that would be newly taxed. OQ-01 is therefore
RESOLVED to `ipd_lint`, which costs nothing because `ipd_lint` already imports `ipd_schema as S` and
`runner_shared` already reaches `ipd_lint` function-locally in four places. This also converts
`- Scope-Paths:` from provisional to known-correct, which is what the question was blocking.

**3. E-04's own freedom check can take a code that is already used (PR-104, MEDIUM).** It prescribed
"confirm by grep that the chosen code is unused". Three of the 30 constants are MULTI-LINE assignments
(`C_EXEC_ATTRIBUTION`=`IPD-S406`, `C_READINESS_UNATTESTED`=`IPD-M107`,
`C_GATE_HAND_ROLLED_MOVE`=`IPD-M108`), and I demonstrated the failure: a single-line regex over the
source finds 27 of 30 values while importing the module finds all 30. So the prescribed method can
report `IPD-S406` free when it is taken. The plan's own family list also omitted those three codes. Both
are corrected, the method is now compare-imported-values, and the measured next free shape-family code
(`IPD-S407`) is recorded so the executor does not re-derive it.

**4. E-03 was written as though `ipd_schema.py` might need an edit; it does not (PR-103, MEDIUM).**
`RECOGNIZED_STATUS` is already a module-level `FrozenSet[str]` of nine values and `ipd_lint` already
imports the module, so the vocabulary is in hand as `S.RECOGNIZED_STATUS` with no export work
(confirmed in-process). Left as written, the declared path invites an executor to manufacture an edit to
justify it. The plan now states the expectation plainly: reconcile that path UNCHANGED with a
`--scope-ack`, and say why if you do edit it.

**5. A false-positive path the plan half-anticipated (PR-102 / F-13, LOW).** The conventions block
correctly names `_structural_lines` as the fence-aware view, but no E- or V-item required using it. This
plan quotes the grammar template twice, so a rule scanning raw lines would eventually flag a plan for
DESCRIBING the rule. I measured the current exposure and it is zero (no non-orchestrator plan contains a
conforming-shaped row), which is why this is LOW rather than HIGH; V-01 now requires a fenced-code
fixture proving no false positive.

**6. The suite baseline moved DURING this review, and the plan now says so (PR-105, MEDIUM).** First
bare run: `7306 passed, 3 skipped, 2 xfailed`, fully green. Second run minutes later:
`1 failed, 7305 passed`, the failure being
`tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today`,
which names three `reaskscore` plans another party is editing in this shared checkout. I did not accept
that it was pre-existing on the timing alone: I STASHED every review edit and re-ran the single node,
and it still FAILED, proving it independent of this Set. The plan previously named no baseline at all,
so an executor meeting this failure could have chased a phantom regression or, worse, "fixed" another
party's plans. It is now recorded by node id with the instruction not to touch it.

WHAT I DELIBERATELY DID NOT CHANGE. The five-item shape is right and I found no reason to re-cut it:
E-01 through E-03 are the three fields of one grammar, E-04 is the entry point they compose into, E-05
is its refusal. The deliberate exclusion of all three call sites is correct and is what makes the
consumers separately reviewable. I did not touch the semantic probe, and I did not relax any
requirement: every fix made a demand more specific or added one, and V-04 is now materially harder to
satisfy than as authored.

VALIDATION RUN AT REVIEW. `aw ipd lint --phase author` and `--phase review-finalize` conform. The
carrier rule is CLEAN at `pre-transition` (OQ-01 is now `resolved`, so it owes nothing).
`python3 -m pytest tests/test_orchestrator_probe_cache.py -o addopts="" -q` -> `56 passed`, and the
specific import-rule node passes when selected with `-k no_new_module_level` (`1 passed, 55
deselected`). Bare suite: one pre-existing, proven-unrelated failure as described above. `aw check all`
reports 0 findings against this plan.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | HIGH | IN-SCOPE | C (architecture); OQ resolution | `render_stream` imports (zero first-party); `ipd_lint` has no `runner_shared` reference; `runner_shared` module-level set `{render_stream, runner_profiles}` by AST; `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared` | OQ-01 was left open on INVERTED reasoning: it warned of a cycle through `render_stream`, which imports nothing first-party, and `ipd_lint` does not import `runner_shared` at all. The real constraint runs the other way and FORECLOSES the separate-module option, because child 03 would need a module-level import there that a shipped test refuses by set equality. The question had a decisive in-tree answer and should not have been deferred to the executor. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | OQ-01 RESOLVED to `ipd_lint` with the measurement and the enforcing test named; the inverted rationale replaced. E-04 carries the siting decision; V-04 requires the import-rule test pasted passing; the Scope check's under-scope note narrowed from "siting is open" to "report a finding naming that test if you disagree". |
| PR-102 | HIGH | UNDER-SCOPE | E (verification); `ipd_lint.lint_text` | `lint_text` builds `diags` from eleven explicit `check_*` calls; `disposition = CONFORMING if not diags else ERROR` | E-04 required adding a `C_*` code but never adding or CALLING a `check_*` function, and a constant alone is inert. The rule would never fire, `aw ipd lint` would keep reporting `conforming` on a violating orchestrator, and every V-item would still pass - after which children 02/03 wire two consumers to a control that does nothing and child 05's criterion-1 grep calls it proven. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 now requires a `check_*` function CALLED from `lint_text`, gated on `doc.meta_fields.get("Kind")`, reading rows via `_structural_lines`. V-04 demands `aw ipd lint` reporting the code at a NONZERO exit on a violating fixture and NOT firing on a `Kind: child` plan, and explicitly FAILS a validation that shows only the constant. V-01 adds the fenced-code no-false-positive fixture. |
| PR-103 | MEDIUM | IN-SCOPE | F (KISS); scope accuracy | `ipd_schema.RECOGNIZED_STATUS` is a module-level `FrozenSet[str]`; `ipd_lint` imports `ipd_schema as S`; `ipd_lint.S.RECOGNIZED_STATUS` yields nine values | E-03 was phrased as if the vocabulary might need exporting, and the Scope check said `ipd_schema.py` is touched "only if the vocabulary needs exporting". It does not need anything: the value is already reachable with no new import, so the declared path invites a manufactured edit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 states no edit is required and to expect a `--scope-ack`; the Scope check says the same and asks for a reason if the path does change. Recorded as F-11. |
| PR-104 | MEDIUM | IN-SCOPE | A (correctness); rule-code allocation | single-line regex finds 27 of 30 `C_*` values, import finds 30; `C_EXEC_ATTRIBUTION`=`IPD-S406`, `C_READINESS_UNATTESTED`=`IPD-M107`, `C_GATE_HAND_ROLLED_MOVE`=`IPD-M108` | E-04's prescribed grep-to-confirm-unused CAN TAKE AN ALREADY-USED CODE, because three constants are multi-line assignments a single-line grep misses. The conventions block's family list omitted the same three codes. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 requires confirming freedom by comparing IMPORTED VALUES and names the three multi-line cases; the measured next free shape-family code `IPD-S407` is recorded along with the other free numbers. The conventions family list corrected to the full measured set. V-04 requires the 30-value set pasted with the new code absent from it. |
| PR-105 | MEDIUM | UNDER-SCOPE | E (verification); baseline honesty | run 1 `7306 passed, 3 skipped, 2 xfailed`; run 2 `1 failed, 7305 passed`; stash-and-rerun of the single node still FAILED | The plan named NO suite baseline, and the baseline moved during the review itself: `test_no_pending_plan_is_refused_on_a_verdict_today` began failing on three `reaskscore` plans another party is editing concurrently. Without a recorded baseline an executor could chase a phantom regression or "fix" a co-worker's plans. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Both measurements recorded with the failing NODE ID, proven pre-existing by stashing all review edits and re-running, marked not-this-plan's and not-to-be-fixed, with the criterion restated as AFTER-minus-BEFORE node ids being empty. |
| PR-106 | LOW | IN-SCOPE | G (executability) | the plan's Goal section | The Goal described only DEFINING the rule, so the separate obligation to make it FIRE (PR-102) had no home in the plan's own statement of purpose. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Goal now carries the wiring obligation explicitly, stating that a defined-but-unwired rule changes no disposition. Proposed-changes list and Required-tests section updated to match. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Where should the one shared conformance function live (the plan's own OQ-01)? | Inside `ipd_lint`, reached from `runner_shared` by a function-local import. | A new `orchestrator_shape.py` imported by both (rejected on evidence, not taste: child 03 must import it from `runner_shared`, whose module-level first-party imports are pinned to a two-element allowlist by a set-equality test, so the import would break a shipped test). Siting it in `runner_shared` (rejected: `ipd_lint` would then have to import a runner to lint, which the review-side consumer must do with no run in progress). | AST of `runner_shared` module-level imports; `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared` and its failure message; `parse_plan_file` docstring naming five newly-taxed modules; `runner_shared` already reaching `ipd_lint` function-locally in four places | yes |
| D-2 | Which `C_*` family and number should the new rule take? | The `IPD-S4xx` state/shape family, `IPD-S407`, recorded as the measured next free number rather than mandated. | `IPD-M109` metadata (rejected: this is a checklist-shape rule, not a metadata-field rule). `IPD-Z603` size (rejected: unrelated concern). Leaving the family entirely to the executor (rejected: the multi-line-constant trap in PR-104 means an unguided choice can collide). | imported all 30 `C_*` values and computed per-family occupancy: M1 1-8, H2 1-5, I3 1-5, S4 1-6, Q5 1, Z6 1-2; `IPD-S407`/`M109`/`I306`/`Z603` all verified absent from `agent_workflows/` and `tests/` | yes |
| D-3 | Should the failing `test_no_pending_plan_is_refused_on_a_verdict_today` be treated as this plan's problem? | No. Recorded as pre-existing and explicitly out of scope, with the three affected plans named as another party's concurrent work. | Fixing it here (rejected: it would mean editing three `reaskscore` plans this reviewer did not author, which the shared-checkout rule forbids). Ignoring it silently (rejected: an executor would then meet an unexplained red suite). | stashed every review edit and re-ran the single node: still FAILED, so it is independent of this Set; `git log` shows the three plans changed in commits belonging to the reaskscore work | yes |
| D-4 | Should the new rule read raw lines or the fence-aware structural view? | The fence-aware `_structural_lines` view, now required by E-04 and pinned by a V-01 fixture. | Raw lines (rejected: this plan quotes the grammar template twice and a future plan may quote a full row, so raw scanning creates a false positive that flags a plan for describing the rule). | matched the grammar against every pending plan at review: zero non-orchestrator plans currently contain a conforming-shaped row, so the exposure is latent rather than present, which set the severity at LOW | yes |
