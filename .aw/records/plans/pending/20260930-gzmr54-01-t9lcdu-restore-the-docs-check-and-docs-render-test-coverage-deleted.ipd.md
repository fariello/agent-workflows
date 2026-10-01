# IPD: Restore the docs_check and docs_render test coverage deleted from tests/test_docs.py

- Date: 2026-09-30
- Kind: child
- Concern: TWO SHIPPED MODULES HAVE NO TEST CALLER AT ALL, AND ONE OF THEM IS ALREADY BROKEN IN A WAY NOTHING REPORTS. Commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24) deleted `tests/test_docs.py` whole, 472 lines and 28 test functions. Plan `fzueyy` restored only the run-scratch guard arm into `tests/test_run_scratch_path_guard.py` (verified: `ShippedRunScratchPathTests`, `ShippedRunScratchGuardFalsifiabilityTests` and `_bare_run_scratch_refs` are all present there), leaving the rest unrestored. MEASURED AT AUTHORING HEAD `2e2ecce12`: `rg -l 'docs_check|docs_render' tests/` returns NOTHING, so `agent_workflows/docs_check.py` (181 lines) and `agent_workflows/docs_render.py` (173 lines) ship with zero test callers. I DID NOT STOP AT THE COVERAGE ARGUMENT, because a coverage gap is only a hypothesis until it hides something. I recovered the deleted file into gitignored run scratch, re-anchored `REPO_ROOT`, and ran it: `1 failed, 27 passed`. The single failure is a LIVE DEFECT the deletion masked: `docs_check.check_aw_commands` reports an `aw-command` finding in `docs/skill-selection.md` saying `'aw router' is not a known subcommand`, against the plain-prose heading `## The aw router skill` (line 27 at authoring), which commit `a2394b00` ("feat(agyinstall): install unified aw router skill", 2026-09-26) added TWO DAYS AFTER the tests were deleted. So the checker has a false-positive bug that no suite can see, and the module's own docstring is what makes it a bug rather than a judgement call: it promises to check "every `aw <subcommand>` referenced in a FENCED COMMAND BLOCK", while `check_doc` applies `_AW_CMD_RE` to the raw text line by line with no notion of a code span at all.
- Scope: Restore behavioral test coverage for `agent_workflows/docs_check.py` and `agent_workflows/docs_render.py` as two per-module test files, and fix the prose-versus-code-span false positive in `check_aw_commands` that the restored coverage exposes. Out of scope: the `RunAnalyticsPrivacyDocTests` and `LifecycleLegendAndDocsDriftGuardTests` classes from the same deleted file (they test neither module and are deferred with reason below), any new `aw` subcommand, any wiring of these modules into `aw check` or a hook, and any edit to a document other than the single heading named in E-04.
- Scope-Paths: tests/test_docs_check.py, tests/test_docs_render.py, agent_workflows/docs_check.py, docs/skill-selection.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: medium
- From-Backlog: gzmr54
- Set: gzmr54
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: t9lcdu

## Workflow history

- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `gzmr54` in a non-interactive authoring turn. Measurement at HEAD `2e2ecce12` ran the deleted file out of gitignored scratch and found `1 failed, 27 passed`, so the plan's subject grew from pure restoration to restoration plus the one live checker defect the deletion masked (F-04, F-05). Two of the six classes the item names are deferred with reason rather than silently dropped (F-08).

## Goal

Give `docs_check` and `docs_render` real test callers again, so a regression in either is reported by the suite instead of shipping unnoticed, and fix the `check_aw_commands` false positive that restoring the coverage immediately surfaces. The restored tests must drive the modules and assert on their outputs, never read their source.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: restore the docs_check coverage and fix what it exposes

- [ ] E-01 Create `tests/test_docs_check.py` covering the per-check FALSIFIABILITY arms of `docs_check`, recovered from `git show 19313eed^:tests/test_docs.py` (the `DocCheckFalsifiabilityTests` class) and re-verified against the CURRENT signatures of `docs_check.check_no_unicode_dashes`, `check_internal_links`, `check_aw_commands`, `check_doc` and `check_docs_dir` rather than pasted blind. Each check must be proven to FIRE on a positive input and to STAY SILENT on a negative one, since a check that cannot fail proves nothing: an em dash (U+2014) and an en dash (U+2013) each produce a `no-unicode-dashes` finding while an ASCII hyphen produces none; a relative link to a missing file produces an `internal-link` finding while a link to a file that exists, an `http://` link, a bare `#anchor` and a `mailto:` link each produce none; and an unknown subcommand produces an `aw-command` finding while a known one produces none. Assert on the `DocFinding` fields (`doc`, `line`, `check`) and on its `__str__` rendering, not merely on truthiness, so a finding attributed to the wrong line or check is caught. Build inputs with `tmp_path`, never by writing into the real `docs/` tree.
  - Depends on: none
  - Expected outcome: The file exists and passes against unmodified source. `python3 -m pytest tests/test_docs_check.py -o addopts=""` reports every collected test passing, and `rg -c 'docs_check' tests/test_docs_check.py` is non-zero where `rg -l 'docs_check' tests/` returned nothing before.
  - Execution state: pending

- [ ] E-02 Add to `tests/test_docs_check.py` the whole-tree arm restored from the deleted `DocCheckTests.test_no_findings_across_docs`: `check_docs_dir(REPO_ROOT / "docs")` must return an EMPTY finding list, with the failure message rendering every finding so a reader sees the whole set at once rather than rediscovering it one red test per document. Also cover `check_docs_dir`'s ignore behavior (it consults `artifact_core.get_ignored_dirs` / `is_ignored_path`) by asserting that a doc placed under an ignored directory inside a `tmp_path` docs tree contributes no finding, which is live behavior the deleted file never exercised. This item is expected to FAIL until E-04 lands; that failure is the point, and it must be observed before the fix rather than after.
  - Depends on: E-01
  - Expected outcome: Run before E-03/E-04 are performed, the whole-tree arm fails with one finding whose `doc` is `skill-selection.md`, whose `check` is `aw-command`, and whose message is `'aw router' is not a known subcommand`, attributed to the line carrying the heading `## The aw router skill` (the offset was 27 at authoring and may shift, so match the heading text and not the number). This reproduces the measurement this plan was authored from. The ignore arm passes immediately.
  - Execution state: pending

- [ ] E-03 Fix `docs_check.check_aw_commands` so it honors the contract its own module docstring states, scanning `aw <subcommand>` references inside FENCED BLOCKS and INLINE CODE SPANS only, and ignoring plain prose. The defect is that `check_doc` applies `_AW_CMD_RE` to raw lines, so the prose heading `## The aw router skill` is read as a command invocation. Keep the function's signature and return type, and keep the `aw-command` check name and the `line` attribution correct relative to the ORIGINAL document (a fenced-block or span scan must not renumber lines). PRESERVE FALSIFIABILITY: the recovered input `run \`aw florb\` please` must still produce a finding, because it is inside a code span; that exact string is asserted in E-01, so a fix that silenced it would be caught. I VERIFIED THIS APPROACH RATHER THAN ASSUMING IT: a span-and-fence-restricted scan over the live `docs/` tree yields 0 findings while still flagging the `aw florb` input, so no OTHER document depends on the prose-scanning behavior and the fix is not trading this false positive for a new blind spot.
  - Depends on: E-02
  - Expected outcome: `check_aw_commands` returns no finding for a prose line naming `aw router` and still returns one for `` run `aw florb` please ``. The module docstring and the checker agree where they previously did not.
  - Execution state: pending

- [ ] E-04 Correct the one document the checker legitimately flags, rewriting the `docs/skill-selection.md` heading `## The aw router skill` to put the command in a code span (`## The \`aw\` router skill`). THIS IS A SEPARATE ITEM FROM E-03 ON PURPOSE: E-03 removes the false positive class, while this item makes the document say what it means, so each can be reverted independently if review wants only one. I confirmed this is the ONLY document needing it: with the heading in a code span and the checker UNCHANGED, `check_docs_dir(Path("docs"))` returns 0 findings, which also proves the two fixes are independent rather than one masking the other. Change the heading only; do not edit the surrounding prose, and do not touch any other document.
  - Depends on: E-03
  - Expected outcome: `docs/skill-selection.md` carries the code-span heading, `git diff --stat docs/skill-selection.md` shows a one-line change, and the E-02 whole-tree arm now passes.
  - Execution state: pending

### Task group 2: restore the docs_render coverage

- [ ] E-05 Create `tests/test_docs_render.py` covering `docs_render.render_support_table` and `render_benchmark_thresholds_table`, restored from the deleted `SupportTableRendersFromRegistryTests` and `BenchmarkThresholdTableTests` and re-verified against current signatures. The property under test is EVIDENCE GATING, which is what makes these renderers worth having: built against an EMPTY `host_capability_registry.HostCapabilityRegistry`, no row of the rendered support table may claim `supported`, and the provenance line must be present. Strengthen the restored arm with its missing POSITIVE control, which the deleted version lacked: promote one capability in the registry and assert that cell, and ONLY that cell, renders as supported. For the threshold table, assert the provenance line and the non-negotiable invariants (0 critical escapes, 1.0 evidence validity) are rendered for each risk class in `benchmark_thresholds.ThresholdPolicy`, iterating the policy rather than hard-coding a row count.
  - Depends on: none
  - Expected outcome: `python3 -m pytest tests/test_docs_render.py -o addopts=""` reports every collected test passing, including the new positive control, and `rg -c 'docs_render' tests/test_docs_render.py` is non-zero where `rg -l 'docs_render' tests/` returned nothing before.
  - Execution state: pending

- [ ] E-06 Add to `tests/test_docs_render.py` the `render_model_profile_table` arms restored from the deleted `ModelProfileTableTests`: the model ID stays a column DISTINCT from the profile and the reasoning config; the header records benchmark date, task corpus, host and version, and measurement uncertainty; unmeasured combinations are listed as pending rather than asserted; the caption carries the "not a universal quality claim" disclaimer; and a profile carrying an unknown key is REJECTED with `workflow_profile.ProfileError`, which is the arm proving a semantic override cannot be smuggled through a transport profile. Assert the rendered row ORDER follows the input sequence, and that an empty `pending_combinations` renders no pending section at all, neither of which the deleted version covered.
  - Depends on: E-05
  - Expected outcome: Every arm passes, including the `ProfileError` rejection and the empty-pending case.
  - Execution state: pending

### Task group 3: prove the whole tree still holds

- [ ] E-07 Run the full suite BARE as `python3 -m pytest` with no added flags and confirm no regression, measuring the collected total against a baseline taken AT THE EXECUTION BASE rather than trusting the 3604 recorded here at authoring time (other lanes land tests between authoring and execution, so a hard-coded number would misreport a clean run as a regression). The total must rise, since this plan only adds tests. Pay specific attention to any test that reads the `docs/` tree, since E-04 edits a shipped document: `tests/test_run_scratch_path_guard.py`, `tests/test_record_producers.py` and `tests/test_precommit_verbatim_exclusions.py` all reference docs paths and are the likeliest places an unexpected coupling surfaces.
  - Depends on: E-06
  - Expected outcome: The bare suite passes with a collected total exceeding the execution-base baseline by the number of tests added, and no previously passing test fails.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS ASSERT OUTCOMES, NEVER CODE STRUCTURE. `AGENTS.md` forbids reading production source with `inspect`, `ast`, regex or substring search, forbids caller counts and symbol censuses, and requires restored coverage to CALL the code and assert on real outputs (GUIDING_PRINCIPLES P16). Every item above drives a function and asserts its return value, and the one structural-sounding claim in this plan (that the docstring and the checker disagree) is validated by CALLING `check_aw_commands`, not by reading it.
- PER-MODULE TEST FILES ARE THE CONVENTION, which is why this plan does not recreate the omnibus `tests/test_docs.py`. The tree carries `tests/test_host_capability_registry.py`, `test_host_capability_extension.py`, `test_host_capability_wiring.py` and `test_run_analytics.py` beside `test_run_analytics_cli.py` and `test_run_analytics_statistics.py`. The deleted file bundled six unrelated subjects, which is exactly why restoring it whole would re-create a file no one can place.
- THE SUITE RUNS BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`, so validation uses `python3 -m pytest` with no added flags; `-o addopts=""` appears above ONLY for the narrowed per-file runs where per-test counts are needed, which is the documented exception.
- THE PRIOR RESTORATION IS THE PRECEDENT. `fzueyy` (executed, `wfartgrowth-01`) restored one class of this same deleted file into a NEW narrowly named file, `tests/test_run_scratch_path_guard.py`, rather than reviving `tests/test_docs.py`. This plan follows that shape.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | `tests/test_docs.py` was deleted whole: 472 lines, 28 test functions. | `git show 19313eed -- tests/test_docs.py` shows `deleted file mode`; `git show 19313eed^:tests/test_docs.py \| rg -c '    def test_'` reports 28. |
| F-02 | Both target modules ship with zero test callers at authoring HEAD `2e2ecce12`. | `rg -l 'docs_check\|docs_render' tests/` returns nothing. `agent_workflows/docs_check.py` is 181 lines, `docs_render.py` is 173. |
| F-03 | The item's premise holds and the prior restoration is partial, not absent. `fzueyy` restored only the run-scratch arm. | `ShippedRunScratchPathTests`, `ShippedRunScratchGuardFalsifiabilityTests` and `_bare_run_scratch_refs` are all present in `tests/test_run_scratch_path_guard.py`; the other classes are in no file. |
| F-04 | THE GAP HIDES A LIVE DEFECT, not just absent coverage. Running the recovered file out of gitignored scratch gives `1 failed, 27 passed`; the failure is an `aw-command` finding reading `'aw router' is not a known subcommand`, attributed to `docs/skill-selection.md`'s heading `## The aw router skill` (line 27 at authoring). | Recovered to `.aw/workflow-artifacts/` (gitignored, confirmed via `git check-ignore -v`), `REPO_ROOT` re-anchored, run with `-o addopts=""`. |
| F-05 | That finding is a FALSE POSITIVE caused by the checker scanning prose. The flagged text is the plain Markdown heading `## The aw router skill`; `router` is genuinely not a subcommand (`'router' in docs_check.known_subcommands()` is `False`, over 68 real subcommands, so the fallback list is not in play), but a heading is not a command invocation. The module docstring promises to check references "in a fenced command block", which `check_doc` does not implement. | `docs/skill-selection.md` line 27; `docs_check.check_doc` passes raw text to `check_aw_commands`. |
| F-06 | The defect is NEWER than the deletion, so it was never a pre-existing failure the trim knowingly dropped. The heading arrived in `a2394b00` (2026-09-26); `19313eed` is its ancestor (2026-09-24). | `git log -S'The aw router skill' -- docs/skill-selection.md`; `git merge-base --is-ancestor 19313eed a2394b00` succeeds. |
| F-07 | BOTH fixes are independently sufficient and neither hides a second problem. Restricting the scan to fenced blocks and inline code spans yields 0 findings over the live `docs/` tree while still flagging `` run `aw florb` please ``; separately, code-spanning the heading with the checker unchanged also yields 0 findings. | Two scratch probes against `docs/`, each reverted; the heading probe restored the file byte-for-byte (verified by comparison). |
| F-08 | Two of the six classes the backlog item names belong to neither target module, so restoring them here would widen scope past the item's own stated subject. `RunAnalyticsPrivacyDocTests` tests `run_analytics_export`'s `DETECTOR_BLIND_SPOTS`/`DETECTOR_COVERED_CLASSES` against `docs/run-analytics.md`; `LifecycleLegendAndDocsDriftGuardTests` tests `cli._build_parser()` help against `lifecycle_style.STAGE_ORDER`. Both PASS today, so nothing is currently broken by deferring them, and partial coverage already exists for the latter (`tests/test_term.py` asserts `format_lifecycle_legend` covers `STAGE_ORDER`, though NO test asserts the legend reaches `--help` output). | Scratch run: both classes green. `rg -n 'LIFECYCLE LEGEND' tests/` returns nothing; `rg -n 'DETECTOR_BLIND_SPOTS' tests/` returns nothing. |
| F-10 | THE BARE SUITE IS NOT GREEN AT THE AUTHORING BASE, and the one failure is NOT this plan's. `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` fails because `backlog.py` stamps history from the LOCAL clock (`datetime.date.today()`) while `status_set.py` uses UTC, so the two `aw backlog set` spellings recorded `2026-09-30` and `2026-10-01` for one transition. Filed as backlog `fnb8pl` (`bug`, gating `next`) and OUT OF SCOPE here. The executor must expect this failure at the base and must NOT 'fix' it. | Reproduced in a clean detached worktree at HEAD `2e2ecce12` holding none of this lane's files: `1 failed, 3394 passed, 2 skipped`. |
| F-09 | The `DocsExistTests` class is subsumed rather than dropped: its required-doc list is enforced transitively, because every document it names is linked from `docs/README.md` and `check_internal_links` fails a dead relative link. A deleted required doc therefore fails E-02's whole-tree arm. | Probe over `docs/README.md` links: all 18 required paths resolve and all are linked from the index; three non-required docs (`branch-protection.md`, `runner-profiles.md`, `wtiso-state-taxonomy.md`) are unlinked, which is why a blanket orphan check is NOT added here. |

## Proposed changes (ordered, validatable)

1. `tests/test_docs_check.py` (new): per-check falsifiability arms with positive and negative controls, `DocFinding` field assertions, the whole-tree `check_docs_dir(docs/)` zero-findings arm, and an ignored-directory arm (E-01, E-02).
2. `agent_workflows/docs_check.py`: restrict `check_aw_commands` scanning to fenced blocks and inline code spans, preserving signature, return type, check name and original line attribution (E-03).
3. `docs/skill-selection.md`: one heading, `## The aw router skill` to `## The \`aw\` router skill` (E-04).
4. `tests/test_docs_render.py` (new): support-table evidence gating with a new positive control, threshold-table invariants iterated from the policy, and the model-profile arms including the `ProfileError` rejection, row order and the empty-pending case (E-05, E-06).

## Deferred / out of scope (with reason)

- `RunAnalyticsPrivacyDocTests` and `LifecycleLegendAndDocsDriftGuardTests` are NOT restored here (F-08). They exercise `run_analytics_export` and `cli`/`lifecycle_style`, not the two modules this item is about, and both pass today, so deferring them leaves nothing newly broken. They are real coverage gaps and should be filed as their own backlog items against their own modules (plausibly `tests/test_run_analytics.py` and a legend arm beside `tests/test_term.py`). NOTE THE ONE SHARP EDGE a reviewer should weigh: no test currently asserts the lifecycle legend reaches `aw --help` output at all, only that `Term.format_lifecycle_legend` covers `STAGE_ORDER`, so that gap is live while deferred.
  - Carrier: spvm3v
- `DocsExistTests` is not restored as a standalone class, because its property is already enforced transitively through the index links (F-09). A reviewer who disagrees can ask for the explicit list; the reason it is omitted is that a hand-maintained required-doc list is a second place to update whenever a doc is legitimately retired, and the link check needs no maintenance.
  - Carrier-Declined: Nothing outlives this plan to carry. The property is ENFORCED, not deferred: every one of the 18 documents the deleted class listed is linked from `docs/README.md`, and E-02's whole-tree arm fails on a dead relative link (F-09, measured), so deleting a required doc still turns the suite red. Only the hand-maintained list is dropped, and a list is not an obligation.
- Wiring `check_docs_dir` into `aw check`, a pre-commit hook, or `release_readiness.gate_docs_checks` is out of scope. `gate_docs_checks` takes a `doc_findings` sequence and NOTHING in the repository computes one (`rg -n 'doc_findings'` matches only `release_readiness.py` itself), so the gate is inert; that is a real finding but it is a wiring decision, not test restoration.
  - Carrier: tj9dq9
- The pre-existing suite failure F-10 (`test_release_exempt_setter_roundtrip_and_parity`, a local-versus-UTC history date skew between `backlog.py` and `status_set.py`) is NOT fixed here. It touches neither target module and neither declared source path, and fixing it would mean editing `agent_workflows/backlog.py` outside this plan's scope.
  - Carrier: fnb8pl

## Scope check

- Over-scope: none. The two new test files and the two source/doc edits are each required by a numbered item, and the checker fix is confined to the one function whose contract the restored test disproves.
- Under-scope: Deliberate, and named above. Two deleted classes stay unrestored (F-08), `gate_docs_checks` stays inert, and no new `aw` subcommand is introduced for `router`. A reviewer who wants any of these in scope should say so before approval, since each would change the declared `- Scope-Paths:`.

## Required tests / validation

Narrowed runs with `-o addopts=""` for per-test counts on the two new files, then the FULL suite run BARE (`python3 -m pytest`) with its actual output pasted. The baseline to compare against is 3604 tests collected at authoring HEAD `2e2ecce12` (`python3 -m pytest --collect-only -q -o addopts=""`). E-02's arm must be observed FAILING before E-03 and E-04 are performed and PASSING after, since a fix validated only after the fact does not demonstrate it addressed the measured defect. E-03's falsifiability must be shown by a negative control: a temporary edit that would reintroduce prose scanning must make the restored test fail, and must be reverted in the same pass with the revert proven by `git diff --stat`.

## Spec / documentation sync

No `.spec.md` file is amended, so none appears in `- Scope-Paths:`. The behavior changed in E-03 is governed by `docs_check`'s own module docstring rather than by a spec, and the change brings the code INTO line with that docstring rather than altering a documented contract; if the docstring needs its wording tightened to name inline code spans beside fenced blocks, that edit belongs to E-03's file and is covered by the declared path. `docs/skill-selection.md` is edited by E-04 and is declared. No user-facing document gains or loses a claim, so `CHANGELOG.md` is not touched by this plan.

## Open questions

### OQ-01: Should `check_aw_commands` ignore prose entirely, or should prose be held to the same standard with a documented exemption?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, so it does not need the maintainer. The module docstring already states the intended scope ("every `aw <subcommand>` referenced in a fenced command block"), so honoring it is a fix rather than a judgement call, and the measurement in F-07 shows the restricted scan yields 0 findings over the live tree while still catching the falsifiability input. Not blocking: were the maintainer to prefer the opposite resolution (keep prose in scope and exempt `router`), only E-03 changes and the restored tests in E-01 still stand.

### OQ-02: Should the two deferred classes be restored in this Set rather than deferred?

- Blocking: no
- Status: open
- Owner: human
- Carrier: spvm3v
- Resolution or deferral rationale: A SCOPE JUDGEMENT THAT IS THE MAINTAINER'S, which is why it is not resolved here. The repository can tell us the classes pass today (F-08) but not whether coverage for `run_analytics_export` and the `--help` legend belongs to this item or to its own. Not blocking: this plan is executable and complete as scoped either way, and the answer only decides whether follow-on work is filed. The work itself is carried by backlog `spvm3v` either way, so a 'no' answer here does not drop it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the output of `python3 -m pytest tests/test_docs_check.py -o addopts="" -q` showing every collected test passing with a count, plus the output of `rg -c 'docs_check' tests/test_docs_check.py`. Then paste a NEGATIVE CONTROL proving the arms can fail: temporarily neuter `check_no_unicode_dashes` to return `[]`, paste the resulting failure, revert it, and paste `git diff --stat` showing a clean tree.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the whole-tree arm FAILING before E-03/E-04, with the message naming `skill-selection.md` and `'aw router' is not a known subcommand` verbatim, and separately paste it PASSING after. Paste the ignored-directory arm passing. The before-and-after pair is the required shape; a single passing run does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste a Python one-liner result showing `check_aw_commands` returns `[]` for the prose line `## The aw router skill` and returns a non-empty list for `` run `aw florb` please ``, with the finding's `check` field shown as `aw-command`. Paste `git diff agent_workflows/docs_check.py` so the reviewer sees the scan restriction and can confirm line attribution is computed against the original document. Paste a NEGATIVE CONTROL: revert the restriction temporarily, show the E-01 prose arm failing, restore it, and show `git diff --stat` clean.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste `git diff docs/skill-selection.md` showing exactly one changed line, and paste the output of a `check_docs_dir(Path("docs"))` call returning an empty list. Also paste the result of REVERTING the E-03 checker fix while keeping this heading fix, showing `check_docs_dir` still returns `[]`, which proves the two fixes are independent rather than one masking the other (F-07).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste `python3 -m pytest tests/test_docs_render.py -o addopts="" -q` with a passing count and `rg -c 'docs_render' tests/test_docs_render.py`. Paste the test body or output demonstrating the POSITIVE control specifically: with one capability promoted in the registry, that cell renders supported and the others do not. An empty-registry-only run does not satisfy this item, because it cannot distinguish evidence gating from a renderer that never emits `supported` at all.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Paste the passing run covering the model-profile arms, including the `workflow_profile.ProfileError` rejection of an unknown profile key, the rendered-row order assertion, and the empty-`pending_combinations` case rendering no pending section. Paste the rendered table text for one row so the reviewer can see the model ID and reasoning config are separate columns rather than taking the assertion's word for it.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Paste the FULL bare `python3 -m pytest` output including the final `N passed` summary line, with no added flags. Paste the execution-base baseline total you measured BEFORE the change and the new total, and state the delta explicitly rather than only asserting green; the delta must equal the number of tests this plan added. EXPECT ONE PRE-EXISTING FAILURE, `test_release_exempt_setter_roundtrip_and_parity` (F-10, backlog `fnb8pl`): confirm it fails at the execution base BEFORE this plan's changes and report it unchanged. Do NOT fix it, and do NOT report the run green by excluding it. Paste `git diff --cached --name-only` before the commit showing ONLY the four declared `- Scope-Paths:` entries, and paste `aw ipd lint --phase pre-transition` reporting conforming.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution; it writes no `- Readiness:` field, since that is `/plan-review`'s output and never an author's to assert.

EXECUTION CONTRACT. Commit only the four declared `- Scope-Paths:` and only through `aw commit <plan> -- <paths>`, never `git add -A` and never with `--no-verify`; do not push; do not create a tag or release. The full suite must be run BARE (`python3 -m pytest`) and its actual output pasted, never summarized or claimed. V-01, V-03 and V-04 each require a TEMPORARY source edit as a negative control: every one must be reverted in the same pass and the revert proven with `git diff --stat`, because leaving a neutered check in the tree would ship the very blind spot this plan exists to close. ORDER MATTERS AND IS NOT OPTIONAL: E-02 must be observed failing BEFORE E-03 and E-04 are performed, so do not fix the checker first and reconstruct the failure afterwards. This is a shared checkout, so stage nothing another party modified and verify the staged set with `git diff --cached --name-only` before committing.

POST-GATE LIFECYCLE MOVE. After every `V-*` carries pasted evidence and a non-pending `Result`, run `aw ipd lint --phase pre-transition` and require it conforming, then transition the plan to `executed` through the tooled lifecycle (`aw ipd set`), which moves the file to `.aw/records/plans/executed/`. Do not hand-edit the status line or hand-move the file. This plan is the graduation carrier for backlog item `gzmr54`; whether that item closes `done` or stays open for the two deferred classes (OQ-02) is the maintainer's call, and this plan does not close it.
