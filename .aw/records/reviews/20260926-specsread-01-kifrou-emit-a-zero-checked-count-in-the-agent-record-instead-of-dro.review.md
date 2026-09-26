# Review findings: plan kifrou

- Subject-Id: kifrou
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `457bad3c`. Structural preflight `aw ipd lint --phase author --agent` CONFORMED
(exit 0, `findings: 0`) before revision, and `--phase review-finalize` conforms after. No pre-review
snapshot was needed: the plan was committed and unmodified, and the lane-input copy is byte-identical
to the tracked file (`diff` reported no output).

THE PLAN'S CORE CLAIM IS TRUE, THE DIAGNOSIS IS EXACT, AND THE FIX IS THE RIGHT ONE. Verified at the
source rather than from the brief:

```text
result_types.py:403   checked_count = self.data.get("checked") or self.data.get("total_checked")
```

Driving the real `CommandResult.to_agent_record()` across the value space confirms the defect and the
proposed expression's semantics in every case that matters:

```text
=== CURRENT behavior (HEAD) ===
{'checked': 0} -> key present: False value: None      <- THE DEFECT
{'checked': 1} -> key present: True  value: 1
{}             -> key present: False value: None
{'checked': None} -> key present: False value: None
=== PROPOSED expression, simulated ===
{'checked': 0} -> emits: True  value: 0               <- FIXED
{'checked': 1} -> emits: True  value: 1
{}             -> emits: False value: None            <- unchanged for countless commands
{'checked': None} -> emits: False value: None         <- unchanged
```

Measured end to end on an empty temp repo, which reproduces the reported defect exactly:

```text
{"schema":"aw.agent/v1",...,"cmd":"specs check","outcome":"clean","exit":0,...,"findings":0,...}   (no checked)
{"schema":"aw.agent/v1",...,"cmd":"backlog check","outcome":"clean","exit":0,...,"findings":0,...} (no checked)
```

while `--json` on the same repo emits `"data": {"checked": 0, ...}` for both, corroborating the plan's
convention note that `--json` is the only surface reporting the count today.

THE PLAN'S OWN CORRECTION OF ITS BRIEF (F-3) IS RIGHT, AND I RE-DERIVED IT RATHER THAN TRUSTING IT.
`cli.py`'s `{"checked": total_checked}` is an `Evidence(key="inventory", value=...)` payload, not
`CommandResult.data`; measured, `aw check specs --agent` emits no `checked` key at any count
(`'checked' in rec` -> `False`, evidence `['inventory','rules']`). The plan correctly scopes `aw check`
OUT and correctly keeps the dead `total_checked` fallback rather than widening the change.

Every other material claim checks out: the two emitters are exactly `specs.run_check` and
`backlog.run_check`; `git grep '"checked" not in' tests/` returns nothing, so no test relies on the
omission; the three existing `checked` assertions all read `--json` `data.checked` and are unaffected;
no `.spec.md` governs the field (so the plan's "no spec amended" is correct); and the additive-field
clause in `docs/cli-output-contract.md:214` genuinely licenses this within `aw.agent/v1`. The one
falsy-`or` of this shape is confirmed unique to line 403.

WHAT I FIXED. All three findings are about the plan's EVIDENCE AND METHOD, not its approach. The
highest-value one is PR-003: V-03 prescribed a manual copy-the-file-aside-and-restore dance to obtain
before-fix failure output, which is the only step in this plan whose failure mode is IRREVERSIBLE (an
interrupted restore loses the fix), and it is unnecessary because a detached worktree at the
pre-change commit gives the same evidence with nothing at risk. I verified such a worktree does carry
the unfixed line. While prescribing it I found a trap that would have made a naive before-fix run lie:
`tests.support.run_cli` PREPENDS its own `REPO_ROOT` to `PYTHONPATH`, so a `run_cli`-based test
resolves the FIXED package no matter what the environment says, and an executor could paste a green
run believing it was the before-fix one. That caveat is now in V-03.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. testing (a validation surface that does not exist) | `tests/conformance_matrix.py:6` names its consumers `test_cli_conformance_matrix.py` / `test_cli_quality_gates.py`; `git log --diff-filter=D --all` -> both deleted in `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"); `grep -rn 'conformance_matrix' tests/` finds no importer; `python3 -m pytest --collect-only tests/conformance_matrix.py` -> `no tests collected` | **E-04 CITED AN INERT HARNESS AS ITS REGRESSION SURFACE.** It told the executor to run "the CLI conformance tests that execute `specs check` / `backlog check` live (`tests/conformance_matrix.py` `LIVE_SAFE_LEAVES`)". Those leaves ARE listed there, but the module is dead data: nothing imports it and pytest collects zero tests from it. An executor would either believe a live output-contract gate had cleared the change when none ran, or waste a cycle hunting for tests that do not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low (one checklist item's prose) | FIXED | E-04 now states the harness is inert with the deleting commit, says the bare suite is the WHOLE regression surface, and states honestly that its value here is the ABSENCE of a consumer relying on the omitted key (F-5) rather than any positive assertion of the new field, which is E-03's job. Baseline `2458 passed, 2 skipped` added with an instruction to re-derive it (live population). |
| PR-002 | MEDIUM | UNDER-SCOPE | E. testing / G. executability (a control that can pass vacuously) | measured: `aw backlog new --summary X --work-kind chore` -> `--priority required: decide the item's priority ... and work kind`; without `--apply` it previews and writes nothing, leaving `backlog check --agent` at `"checked"` absent; with `--priority low --apply` it writes and reports `"checked":1`. `aw specs new --title X --slug x --apply` -> `"checked":1` | **E-03's NON-ZERO CONTROL WAS UNDER-SPECIFIED IN THE ONE WAY THAT DEFEATS IT.** It wrote `aw backlog new ...` with a trailing ellipsis; that form REFUSES without `--priority`, and (the dangerous case) succeeds-as-preview without `--apply` while writing nothing, so the control would assert against a still-empty tree. A control that silently measures zero is the same vacuous-pass shape this plan exists to remove. Separately, the zero-case assertion `rec["checked"] == 0` did not require the KEY'S PRESENCE be asserted independently, inviting a `rec.get("checked", 0)` rewrite that passes on the unfixed code. | C:Low; U:Low; S:Low; F:Medium (a control that cannot fail proves nothing) | FIXED | E-03 gains the MEASURED argv for both control fixtures, names the two `aw backlog new` refusal/preview traps, and requires `"checked" in rec` be asserted SEPARATELY from `rec["checked"] == 0` with the reason spelled out. The empty-tree precondition (`git init`, both dirs created) is now explicit. |
| PR-003 | MEDIUM | IN-SCOPE | A. correctness / E. testing (the only irreversible step, and a before-fix run that can lie) | V-03 as written: "copy the file aside, restore HEAD's line, run, then restore your edit"; `tests/support.py:270-283` `run_cli` PREPENDS `REPO_ROOT` to `PYTHONPATH` ("pinned to THIS tree"); verified at review that `git worktree add --detach <dir> HEAD` yields a tree carrying the unfixed line 403 | **V-03's BEFORE-FIX METHOD PUT THE FIX AT RISK AND COULD PRODUCE A FALSE "BEFORE" RUN.** The prescribed dance is a hand-rolled two-step restore around a test run: if anything fails between the steps the executor's only copy of the fix is the aside file, which is the one irreversible outcome in an otherwise one-line plan. The plan was right to forbid `git stash` (shared checkout) but substituted something riskier. Worse, `run_cli` pins `PYTHONPATH` to the CURRENT tree, so the obvious cheap alternative (point `PYTHONPATH` at an old tree and re-run the new test) silently exercises the FIXED package and yields a green run an executor could paste as before-fix evidence. | C:Low; U:Low; S:Low; F:Medium-High if mishandled, but the FIX is Low (prescribe a throwaway worktree, which risks nothing) | FIXED | V-03 now prescribes `git worktree add --detach .aw/tmp/kifrou-head <pre-change-commit>` (gitignored, removed with `git worktree remove --force`), keeps `git stash` forbidden with the reason, states the `run_cli` `PYTHONPATH` caveat explicitly, offers the two-command direct reproduction as an equally acceptable substitute, and forbids pasting an unobserved failure or a fixed-tree pass mislabelled as before-fix. It also states that a control which ALSO fails means the test is broken and must be reported rather than worked around. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-04 cites a conformance harness that turns out to be inert. Delete the citation, or replace it with a real gate? | STATE THE INERTNESS with its deleting commit and narrow E-04's claim to what the bare suite actually proves (absence of a dependent consumer). Do NOT commission a replacement gate. | (a) Silently delete the sentence: rejected, the next author reads `LIVE_SAFE_LEAVES` and re-derives the same false belief; naming the deletion commit inoculates them. (b) Add resurrecting the harness to this plan: rejected as OVER-SCOPE, that is a suite-architecture decision affecting every leaf, far larger than a one-expression bug fix, and nothing about this defect requires it. (c) Ask the maintainer whether to revive it: rejected, not needed to land this fix; if it should be revived that is its own item. | `tests/conformance_matrix.py:6`; `git log --diff-filter=D --all` -> `19313eed`; zero importers; `--collect-only` -> no tests collected. | yes |
| D-2 | V-03 needs before-fix failure output, but E-03 depends on E-02, so the fix already exists when the test is written. Which mechanism? | A THROWAWAY DETACHED WORKTREE at the pre-change commit, with the `run_cli` `PYTHONPATH` caveat stated and a direct two-command reproduction allowed as a substitute. | (a) Keep the copy-aside-and-restore dance: rejected, it is the only step in the plan that can lose the fix, and the plan's own reason for banning `git stash` (protect a shared checkout) argues equally against a hand-rolled restore. (b) Reorder so E-03 precedes E-02 and the tests are simply run red first: attractive and genuinely cleaner, but rejected because it forces renumbering an already-conforming E/V bijection and the worktree method obtains identical evidence with no structural churn. (c) Drop the before-fix requirement: rejected outright, it is the only thing proving the tests are not vacuous, which is this plan's entire subject. | `tests/support.py:270-283` (`REPO_ROOT` prepended); verified a detached worktree at HEAD carries the unfixed line 403; `.aw/tmp/` gitignored (`.gitignore:42`). | yes |
| D-3 | `aw check <target>` reports no `checked` count at all. In scope? | LEAVE IT OUT, and accept the plan's `Carrier-Declined` reasoning rather than requiring a carrier. | (a) Widen the plan to add a count to `aw check`: rejected, it is a NEW field on a different command, not the reported defect, and it would turn a one-expression fix into an output-contract addition. (b) Require a backlog item as carrier: rejected, the carrier rules oblige a durable handoff for an unfixed DEFECT, and this is an absent enhancement nobody has requested; the plan's `Carrier-Declined: not a defect` is the correct disposition and the rule accepts a reasoned decline. | Measured `'checked' in rec` -> `False` for `aw check specs --agent`; `cli.py:12071` is an `Evidence` value; `ipd_schema.CARRIER_DECLINED_FIELD` semantics ("a reason is REQUIRED ... the reason's MERIT is the reviewer's job"). | yes |

### Deferred and open

- (none). All three findings were FIXED in place. No question required the human: the plan's single
  `## Open questions` entry is `None`, which is correct here, and every decision above rests on a
  measurement or on the plan's own declared scope. No `Reversible: no` decision was taken, so no
  escalation is owed.

HONEST LIMITS, stated because they bound what this round proves. I verified the DEFECT, the proposed
expression's semantics across the value space, and both emitters, but I did not apply the fix or write
the tests, so that the shipped test file asserts key-presence correctly and that the before-fix run is
genuinely red remain E-02/E-03's work and V-02/V-03's evidence. I ran the bare suite once for the
`2458 passed, 2 skipped` baseline and did NOT run the slow set (`make test-all`), so I have not
characterized slow-marked tests against this change; for a one-expression additive field that is
proportionate, but it is a hole and not a clearance. My audit for consumers relying on the key's
ABSENCE was `git grep` over `tests/` for the absence idioms plus a read of all three existing
`checked` assertions; a consumer OUTSIDE this repository (an agent or CI script reading `--agent`)
cannot be surveyed from here at all, and the plan's additive-field argument is what covers that case
rather than any measurement I made. I did not verify Windows behavior, which is irrelevant to this
expression. Finally, the `2458` baseline is a live population and will drift; V-04 is instructed to
re-derive it rather than match the number.
