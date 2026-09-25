# IPD: Five small cleanups: runner parser seam, stale runner comment, tracked-tree reachability test, backlog CI gate, and relocation note

- Date: 2026-09-25
- Kind: child
- Concern: Five small, independent items verified live at HEAD: (1) `runner_shared.discover_plans` still takes an injected `parse_plan_file` though all three drivers share one parser (ykfgpd); (2) `agy_runipd.py` still states the two drivers' PlanRecords differ, which is false (1gw7nl); (3) no test proves each tracked tree's records reach `aw attention`, only that a scan root is declared (2rb85l); (4) CI runs `aw check backlog` advisory although its stated precondition, a clean baseline, is now met (e85snf); (5) the git mv then untrack resolution for relocating tracked content into an ignored tree lives only in a docstring (q0m7qf).
- Scope: IN: exactly those five concerns, across nine right-sized E-items. OUT: anything else in the files touched, plus four things review named explicitly and Deferred records with consequences: editing or deleting the orphaned fingerprint fixture, restoring a fingerprint/refork guard, flipping the adjacent `aw check release-gates` CI step, and sweeping the two terminal `.aw/records/` artifacts that still quote the dissolved record split.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shared.py, tests/test_attention_contract.py, .github/workflows/tests.yml, .aw/records/specs/implemented/20260817-2124-01-records-taxonomy-cleanup.spec.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- Set: smallfix
- Order: 1
- Highest E allocated: 09
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 0i4fkt
- Approval: 2026-09-25, recorded via aw ipd set: status set to approved
- From-Backlog: ykfgpd

## Workflow history
- 2026-09-25 approved (aw set): status set to approved
- 2026-09-25 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; 10 findings PR-401..PR-410 all FIXED, 6 decisions D-1..D-6 recorded; review record written; aw ipd lint --phase review-finalize conforming
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlogs ykfgpd, 1gw7nl, 2rb85l, e85snf, q0m7qf (all verified live at HEAD; each E-group names its item). Measured: `oc_runipd.parse_plan_file is agy_runipd.parse_plan_file is runner_shared.parse_plan_file` -> True; `aw check backlog` -> conforms, exit 0; walkthrough of the git mv/rm --cached mechanism reproduced in a scratch repo.

## Goal

Remove a seam that carries no information and a comment that is false, prove tracked trees are actually visible, gate CI on backlog conformance, and make the relocation technique findable by plan authors.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: ykfgpd + 1gw7nl: runner seam

- [ ] E-01 (ykfgpd) Drop the `parse_plan_file` keyword-only parameter from `runner_shared.discover_plans` (`agent_workflows/runner_shared.py:10217`), whose body already calls the module's own `parse_plan_file` (`:10041`) by name so the body needs no edit beyond the signature; update the ONE in-package call site that passes it, `initialize_run_core` at `runner_shared.py:23442`; and reduce each host's `discover_plans` to a PLAIN RE-EXPORT of the shared function (`oc_runipd.py:1916`, `agy_runipd.py:1844`), using the `from agent_workflows.runner_shared import discover_plans as discover_plans` form the hosts already use for a re-export, NOT a deleted name.
  - Depends on: none
  - Expected outcome: `runner_shared.discover_plans` takes `(repo)` only; `oc_runipd.discover_plans is agy_runipd.discover_plans is runner_shared.discover_plans` is True; the three call sites in `tests/test_oc_runipd.py:377`, `:2800` and `tests/test_orchestrator_retirement.py:3266` (`driver.discover_plans(repo)` / `agy_runipd.discover_plans(root)`) are UNCHANGED and still pass, because the arity they use is the arity that survives.
  - Note on the re-export form, load-bearing: `ruff` has stripped bare re-exports in this package before (`oc_runipd.py:514`), which is why the `as <same-name>` spelling is required rather than preferred. The name MUST remain an attribute of BOTH host modules; deleting it breaks the three test call sites above.
  - Execution state: pending

- [ ] E-02 (ykfgpd) Correct the `INJECTED DEPENDENCIES` block in `runner_shared.py`'s module docstring (`:49-90`), which is the module's contract of record: remove the `discover_plans` bullet (`:57-72`, the 16-line paragraph explaining why the vestigial parameter is retained), and change the count sentence `TEN symbols call something they cannot reach from here` (`:51`) to NINE. Do NOT leave the count stale: a docstring asserting ten while listing nine is the same class of false contract the bullet itself was written to avoid.
  - Depends on: E-01
  - Expected outcome: the block lists nine bullets and says nine; no surviving sentence claims the parameter is retained on purpose.
  - Execution state: pending

- [ ] E-03 (1gw7nl) Retire the dissolved-record-split citations that E-01 falsifies, in the three places a reader meets them, each verified present at review: the `DIFFERENT NamedTuples` justification comment above agy's wrapper (`agy_runipd.py:1836-1843`), the `THE INJECTION IS NOW VESTIGIAL` / `WHY THE PARAMETER STAYS ANYWAY` comment above oc's wrapper (`oc_runipd.py:1901-1915`, whose own text says the signature is pinned and collapsing it is "a later plan's work" - this IS that plan), and the lowercase restatement inside the docstring bullet E-02 removes (`runner_shared.py:69`). Replace each with a one-line statement of what is now true, or delete it where the mechanism it explained is gone. Do NOT touch the two docstring paragraphs that already CORRECTLY retract the claim while drawing a still-valid distinction (`runner_shared.py:10284` `SpecRecord`, `:14171` `SetMember`): they are the desired end state, not debt.
  - Depends on: E-01
  - Expected outcome: no in-package comment justifies a decision on the dissolved record split; the two correct retractions survive verbatim.
  - Execution state: pending

- [ ] E-04 (ykfgpd) Reconcile `tests/test_runner_shared.py` with the collapsed seam, WITHOUT asserting a proof the file does not perform. Remove the `"discover_plans": "parse_plan_file"` row from `INJECTED` (`:73`) so `WrapperTests.test_each_runner_keeps_a_wrapper_at_the_original_name` (`:350`, the file's ONLY consumer of that table, confirmed by reading every `INJECTED` reference at `:28`, `:58`, `:70`, `:83`, `:227`, `:274`, `:351`) no longer demands a wrapper for a re-exported name; and correct the module docstring's own arithmetic, which the removal changes: `5 symbols gained ONE keyword-only parameter` (`:28`) and the `THE COUNT IS 8, NOT THE PLAN'S 5` comment (`:65-69`) must both still be true of the surviving table.
  - Depends on: E-01
  - Expected outcome: `INJECTED` has seven rows, the docstring's counts match it, and `DiscoverPlansRecordTypeTests` (`:525`) still passes unchanged, since it calls `discover_plans(repo)` positionally.
  - Do NOT, and this is the item's main risk: do not update `tests/fixtures/runner_shared_premove_fingerprints.json`, and do not add a row to any refork table. MEASURED AT REVIEW, correcting the source backlog item `ykfgpd`, whose stated work is partly obsolete: NO code anywhere reads that fixture (the only three mentions of it in the tree are PROSE: the `1. FINGERPRINT EQUALITY.` sentence in `tests/test_runner_shared.py`'s module docstring, the `# exemption. \`INJECTED\` above is pinned against` comment in that same file above the `INJECTED` table, and the `# signature is fingerprint-pinned in` comment above `oc_runipd.discover_plans`), and `tests/test_runner_refork_guard.py` NO LONGER EXISTS (deleted in `19313eed`, "test: trim test suite from 9,136 to under 2,000 tests"). The fingerprint harness the backlog item and both host comments describe as pinning this signature is GONE; only the fixture file and the prose describing it remain. So the signature is NOT in fact pinned by any executing test, which is what makes E-01 a small change rather than a fixture migration. Editing the orphaned fixture would be churn; asserting the harness still protects the change would be false.
  - Execution state: pending

- [ ] E-05 (ykfgpd, 1gw7nl) Correct the now-false prose about the vanished harness, which E-04 discovered and which would otherwise outlive this plan as the same class of stale citation `1gw7nl` exists to retire: in the three prose sites E-04 names (the `1. FINGERPRINT EQUALITY.` sentence in `tests/test_runner_shared.py`'s module docstring, the `# exemption. \`INJECTED\` above is pinned against` comment above that file's `INJECTED` table, and the `# signature is fingerprint-pinned in` comment above `oc_runipd.discover_plans`), state that `runner_shared_premove_fingerprints.json` is a RETAINED HISTORICAL CAPTURE that no test reads, rather than a live pin. Do NOT delete the fixture file: deciding its fate is out of scope (see Deferred) and an unread fixture is harmless where a false claim about it is not.
  - Depends on: E-04
  - Expected outcome: no surviving sentence claims a fingerprint test enforces anything; the fixture file is untouched.
  - Execution state: pending

### Task group 2: 2rb85l: reachability test

- [ ] E-06 (2rb85l) Add a per-tree REACHABILITY test class to `tests/test_attention_contract.py`, beside the existing `TrackedTreeScanCoverageTests` (`:375`) whose docstring already states the DECLARATION-not-REACHABILITY limit this closes, and modelled on `ReleaseRecordsReachTheViewTests` (`:451`) which does this for `releases` alone: for each of the five trees in `attention_contract.TRACKED_TREES`, synthesize ONE minimal valid record in a temp repo under the tree's LOAD-BEARING `.aw/records/<tree>/` root and assert `attention.scan` returns exactly that record with the `attention_class` its `CLASS_MAPS` entry declares, and that `drift == []`.
  - Depends on: none
  - Expected outcome: five subtests pass. Use `subTest(tree=...)` over the real `TRACKED_TREES` tuple so a SIXTH tracked tree added later fails here until it has a fixture, which is the drift the guard exists to catch.
  - Fixture shapes, MEASURED at review by running `attention.scan` on each (so the executor does not rediscover them): four trees take the repository's `- Key: value` bullet front matter, and `research` DOES NOT - it requires a `---` delimited YAML-ish block parsed by `research_contract.parse_frontmatter`, with a LOWERCASE `status` key drawn from `research_contract.STATUSES` (`todo`/`active`/`reference`/`archive`). A bullet-style research fixture yields ZERO items plus an `attention.missing-status` drift, which is how this was measured. The working five: `specs` -> `.aw/records/specs/<name>.spec.md` with `- Id:` + `- Status: draft`; `plans` -> `.aw/records/plans/pending/<name>.ipd.md` with `- Id:`/`- Status: to-review`/`- Set:`/`- Order:`/`- Kind:`; `research` -> `.aw/records/research/<name>.research.md` with `---\nid: ...\nstatus: todo\n---`; `backlog` -> `.aw/records/backlog/open/<name>.backlog.md` with `- Id:`/`- Status: open`/`- Priority:`/`- Work-Kind:`/`- Summary:`; `releases` -> `.aw/records/releases/<name>.release.md` with `- Status: planned`/`- Id:`/`- Version:`.
  - Note the five fixtures are the COST the source item named as its reason for deferral ("would couple one contract test to five trees' record shapes"). That cost is accepted here deliberately, and it is the item's own stated remaining work; it is not an accident to be trimmed.
  - Execution state: pending

### Task group 3: e85snf: backlog CI gate

- [ ] E-07 (e85snf) In `.github/workflows/tests.yml:166-170`, make the `aw check backlog` step fail-closed: delete the `|| echo "::warning::..."` fallback, rename the step to say `fail closed` (matching the `aw check plans` and `aw check releases` steps at `:153` and `:157`), and REPLACE the stale `ADVISORY until baseline cleaned` comment block at `:161-165` rather than leaving it above a fail-closed step. The replacement cites this plan, item `e85snf`, and the baseline re-measured at review.
  - Depends on: none
  - Expected outcome: a backlog conformance finding fails CI.
  - The baseline is clean AND the reason is subtler than "zero findings", which the executor must not simplify: `python3 -m agent_workflows check backlog --agent` exits 0 while reporting ONE finding, `check.collisions-not-checked`, whose severity is `info` (`check_engine.py:453`) and which `artifact_core.drift_exit_code` (`:643`) deliberately ignores. So the gate passes today BECAUSE info findings do not fail, not because nothing was reported. Re-derive the exit code at execution time rather than trusting this paragraph: the tree is live and a per-type run is scoped to it (DECISION 18-r2ks4k-D1's precondition was the 286-item, now 336-item, name/summary debt, which is cleared).
  - OUT OF SCOPE, named because the adjacent step invites it: leave the `aw check release-gates` step (`:172-182`) ADVISORY. It measures clean too (verified at review: `check release-gates --agent` -> `findings:0`, exit 0), but its precondition is a DIFFERENT decision owned by backlog `7dcw6z`, which is still `open`. Flipping it here would close another item's decision silently.
  - Execution state: pending

### Task group 4: q0m7qf: relocation note

- [ ] E-08 (q0m7qf) Amend the records-taxonomy spec (`.aw/records/specs/implemented/20260817-2124-01-records-taxonomy-cleanup.spec.md`, `- Status: implemented`) with a short section recording the relocate-into-an-ignored-tree technique: `git mv` and COMMIT it (so the rename is in the commit graph and `git log --follow` can traverse), THEN `git rm --cached` and commit that (so the path leaves the index and the `.aw/.gitignore` rule finally governs it); untracking costs no history. Record the non-obvious corollary too, because it is the part a future author would re-derive: a path-scoped `git commit -- <paths>` re-reads those paths from the WORKING TREE, so it cannot express an index-only removal while the file is present, which is why `engine._commit_relocation` (`agent_workflows/engine.py:3097`, see its docstring at `:3100-3124`) moves each destination aside for that one commit and restores it in a `finally`.
  - Depends on: none
  - Expected outcome: a plan author reaching for this finds it in the spec rather than in migration code.
  - Write the section body ONLY. Do NOT hand-edit the spec's `- Status:` or its `## Workflow history`: `.aw/records/specs/README.md:73` forbids it and directs a history entry through `aw specs note <path> --message <text>`, which is the verb to use if a history line is wanted. An `implemented` spec is amendable in place (AGENTS.md: "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT"), and this plan declares it in `- Scope-Paths:`; amending the body does NOT re-open the status.
  - Execution state: pending

### Task group 5: verification

- [ ] E-09 Run the bare suite (`python3 -m pytest`, no added flags) and paste the actual summary line.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07, E-08
  - Expected outcome: 0 failed, and any failure named as pre-existing with evidence from the base commit or as new.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The maintainer prefers fixing small items in one pass over one plan each; these five are independent, each under about 60 lines, and grouped here for that reason.
- Plans may amend a spec and must declare it in `Scope-Paths` (AGENTS.md); E-08 amends the records-taxonomy spec. A spec's `- Status:` and `## Workflow history` are owned by `aw specs` and may not be hand-edited (`.aw/records/specs/README.md`), so an amendment writes body only.
- A re-export in either host runner must use the `from ... import <name> as <name>` form: `ruff` strips the bare form, and the repository records six such re-exports being stripped on one commit attempt, caught only by a cross-driver symmetry test.
- A plan may not add commits to a plan already in `.aw/records/plans/executed/` (AGENTS.md), which is why the `1gw7nl` sweep stops at the package boundary and does not touch the two terminal records that still quote the dissolved record split.

## Findings

F-1 through F-5 were measured by the author at HEAD `0c2e7970`. F-6 through F-9 were measured at `/plan-review` (2026-09-25, HEAD `22dd0448`), and F-6 in particular CORRECTS the source backlog item rather than merely adding detail.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | LOW | `runner_shared.discover_plans` | The injected parser is the same object in every driver. | `o.parse_plan_file is a.parse_plan_file is r.parse_plan_file` -> True |
| F-2 | LOW | `agy_runipd.discover_plans` comment | States the PlanRecords differ; they are one class. | `oc_runipd.PlanRecord is agy_runipd.PlanRecord is runner_shared.PlanRecord` -> True |
| F-3 | LOW | `test_attention_contract` | The guard proves a scan root is declared, not that records arrive; only releases has a reachability test. | read `TrackedTreeScanCoverageTests`, `ReleaseRecordsReachTheViewTests` |
| F-4 | LOW | CI | Backlog check is advisory; its precondition (clean baseline) is met. | `check backlog --agent` -> conforms, exit 0 |
| F-5 | LOW | records-taxonomy spec | The relocation technique is only in `engine._commit_relocation`'s docstring. | grep of specs and DECISIONS.md: no hit |
| F-6 | LOW | `tests/fixtures/runner_shared_premove_fingerprints.json` + the prose citing it | THE FINGERPRINT HARNESS IS GONE, so the signature this plan changes is NOT pinned by any executing test, contradicting the source item `ykfgpd` (which specifies updating the fixture and adding a refork-table row) and both host comments (which call the signature "fingerprint-pinned"). The fixture file survives ORPHANED and three prose sites still describe it as live. This SHRINKS E-01's blast radius and ADDS the prose correction now carried by E-04/E-05. | `tests/test_runner_refork_guard.py` deleted in `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"); an AST walk of `tests/test_runner_shared.py` finds NO definition named `test_every_clean_symbol_is_a_STRICT_fingerprint_match`, `test_no_call_site_was_rewritten`, `test_an_unwrapped_symbol_is_the_SAME_OBJECT_in_both_runners` or `test_exactly_one_definition_package_wide`, all four of which surviving comments cite; a tree-wide scan finds `premove_fingerprints` on 7 lines, ALL prose, and no `json.load`/`read_text` of it anywhere |
| F-7 | LOW | `runner_shared.py` module docstring, `INJECTED DEPENDENCIES` block | The count is a hand-maintained number that E-01 falsifies: the block opens `TEN symbols call something they cannot reach from here` and E-01 removes one of the ten. The same block holds a 16-line paragraph whose entire content is why the parameter is retained. Neither is reachable from the original E-01 wording, which named only the two host comments. | read `runner_shared.py` docstring, the `TEN symbols` sentence and the `discover_plans(..., parse_plan_file=)` bullet |
| F-8 | MEDIUM | V-06's mutation (originally V-02) | THE PROPOSED MUTATION SILENTLY PASSES, so the plan's only falsifiability proof for the new test would have been vacuous. `attention.scan` reaches `SCAN_ROOTS` through `iter_scan_files(repo_root, scan_roots=SCAN_ROOTS)`, a DEFAULT ARGUMENT bound at def time, so rebinding `artifact_core.SCAN_ROOTS` at runtime has no effect. Measured BOTH ways: attribute rebind -> the specs item is still returned (mutation appears to fail to fail); source-file edit -> zero items (mutation works). | `artifact_core.iter_scan_files` signature; two scripted runs at review |
| F-10 | LOW | this plan's `## Deferred / out of scope` section | Each deferred row needs a TYPED durable carrier, not prose. The four rows review added would otherwise vanish when this plan reaches `executed` and classes `done` in `aw attention`, which is exactly what `check.ipd-uncarried-obligation` exists to stop; measured at review, adding the rows without carriers turned the plan's `aw check plans` finding count from 0 to 1 at `error` severity. | `check_engine.evaluate_durable_carrier`; `aw check plans --json` before the fix: `4 obligation(s) name no durable carrier`, severity `error`; after: no finding on this plan |
| F-9 | LOW | `research` fixture for the new per-tree test | The five tracked trees do NOT share one front-matter grammar, so a uniform fixture cannot work: `research` is parsed by `research_contract.parse_frontmatter`, which REQUIRES a `---` delimited block and returns `None` for the repository's ordinary `- Key: value` bullets. A bullet-style research fixture yields zero items plus an `attention.missing-status` drift, which is how this was measured. | scripted `attention.scan` over all five synthesized records at review; `research_contract.parse_frontmatter` returns `None` unless line 1 is `---` |

## Proposed changes (ordered, validatable)

1. E-01: collapse the `discover_plans` signature and reduce both host wrappers to re-exports.
2. E-02: correct the `INJECTED DEPENDENCIES` docstring block and its count (F-7).
3. E-03: retire the three dissolved-record-split citations, preserving the two correct retractions.
4. E-04: reconcile the `INJECTED` test table without touching the orphaned fixture (F-6).
5. E-05: correct the prose that still claims a live fingerprint pin (F-6).
6. E-06: per-tree reachability test, with a mutation that actually fails (F-8) and per-tree fixtures (F-9).
7. E-07: flip the backlog CI step to fail-closed, leaving release-gates advisory.
8. E-08: document the relocation technique in the records-taxonomy spec.
9. E-09: bare suite.

## Deferred / out of scope (with reason)

- DELETING `tests/fixtures/runner_shared_premove_fingerprints.json`. F-6 establishes that no test reads it, which makes deletion tempting and makes it a SEPARATE decision: the file is the only surviving record of the pre-move source of 34 symbols across two host modules, and whether that historical capture is worth keeping once its harness is gone is a judgement about the repository's own audit trail, not a cleanup. E-05 corrects the false claims ABOUT it, which removes the harm, at no risk. The residual consequence of deferring: an unread fixture stays in the tree, now correctly labelled.
  - Carrier-Declined: There is nothing outstanding to carry. E-05 removes the only harm (three prose sites asserting a live pin), and what remains is a correctly-labelled unread file, which is a state and not an obligation. Filing a backlog item to "decide about a harmless fixture" would add tracked work whose own answer is plausibly "leave it", and the next reader who wonders reaches E-05's corrected prose, which states exactly what the file is.
- RESTORING a fingerprint or refork guard for the runner seam. The same commit that removed `tests/test_runner_refork_guard.py` removed 680 lines of structural pinning as a deliberate suite-trimming decision, so re-adding one here would reverse a maintainer decision this plan has no mandate to revisit. Consequence: the collapsed seam is protected by behavior tests (`DiscoverPlansRecordTypeTests`, the three `discover_plans(repo)` call sites) and not by a structural pin.
  - Carrier-Declined: This is a DECLINE of work, not a deferral of it. The maintainer removed the structural pins deliberately in `19313eed`; carrying a reminder to re-add one would record an intent nobody holds, and the repository's own position is that behavior tests are the intended replacement. If that position ever changes it is a maintainer decision, not a debt this plan discovered.
- FLIPPING the adjacent `aw check release-gates` CI step to fail-closed, even though it measures clean (`findings:0`, exit 0 at review). Its precondition is owned by backlog `7dcw6z`, which is still `open`; closing another item's decision as a side effect is the drift E-07's own scope note forbids. Consequence: a release-gate finding still only warns in CI.
  - Carrier: 7dcw6z
- The wider `1gw7nl` SWEEP of `.aw/records/` for dissolved-record-split phrases. Measured at review: the phrases survive in exactly two records, `.aw/records/plans/executed/20260903-rununify-02-818uru-...ipd.md` and its review record. Both are TERMINAL historical artifacts, and AGENTS.md forbids adding commits to an executed plan; a record that was true when written is not debt. Consequence: a reader of that executed plan meets the claim in its original context, which is where it belongs.
  - Carrier-Declined: Nothing is outstanding. The sweep's live surface is the package code, which E-03 clears completely; the only remaining occurrences are inside two terminal records whose statements were true when written, and AGENTS.md forbids amending an executed plan. Carrying this forward would file an obligation whose only possible discharge is a prohibited edit.

## Scope check

- Over-scope: none. E-02 through E-05 are not new scope: each is a site the original E-01 wording would have had to touch (a docstring the signature change falsifies) or a fact review measured about the same seam (F-6/F-7). They are split out because a single item spanning a signature, two host modules, a module docstring, a test table and three prose sites failed the plan's own right-sizing rule.
- Under-scope: none remaining. Three gaps were closed in review: the `INJECTED DEPENDENCIES` docstring block and its count (F-7), the now-false harness prose (F-6), and V-06's vacuous mutation (F-8).

## Required tests / validation

- `python3 -m pytest tests/test_runner_shared.py tests/test_attention_contract.py tests/test_oc_runipd.py tests/test_orchestrator_retirement.py -o addopts="" -q`. The last two are REQUIRED, not optional: they hold the three `driver.discover_plans(repo)` call sites E-01 must leave working, and a run scoped to `test_runner_shared.py` alone would not exercise them.
- The V-06 mutation, applied to `agent_workflows/artifact_core.py`'s source and reverted, with the revert proven by an empty `git diff --stat` (see F-8 for why a runtime monkey-patch does not substitute).
- Bare `python3 -m pytest`.

## Spec / documentation sync

Amends `.aw/records/specs/implemented/20260817-2124-01-records-taxonomy-cleanup.spec.md` (E-08), declared in `Scope-Paths`, because that spec documents where run scratch goes and is where a plan author looks before relocating tracked content.

WHY the amendment is legitimate on a spec whose `- Status:` is `implemented`, stated because the status invites the opposite conclusion: AGENTS.md rules that "Specs are living contracts, not immutable history" and that a plan changing behavior a spec describes SHOULD carry the amendment in the same change. This amendment records a TECHNIQUE the spec's own implementation used and did not write down; it changes no requirement and no acceptance criterion, so it does not re-open the status. The one hard boundary, carried on E-08 itself: the spec's `- Status:` and `## Workflow history` are owned by `aw specs` (`.aw/records/specs/README.md`: "Do NOT hand-edit the status or history"), so this plan writes the section body and nothing else. A history line, if wanted, goes through `aw specs note`.

No OTHER spec is touched. `aw oc run` / `aw agy run` announce declared spec edits before the run starts and reconcile them at finalize, so this one file is the whole declared surface.

## Open questions

### OQ-01: Should the `discover_plans` host wrappers be deleted outright?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No, resolved from the tests: `driver.discover_plans(repo)` is called from `test_oc_runipd.py`, `test_orchestrator_retirement.py` and `test_runner_shared.py`, so the names stay as re-exports and no call site changes. REINFORCED at review: the re-export must use the `as <same-name>` form, because `ruff` has stripped bare re-exports in this package before (recorded at `oc_runipd.py`'s success-bar import block), so the spelling is a correctness requirement rather than a style choice.

### OQ-02: The source item `ykfgpd` specifies work that no longer exists. Proceed on the corrected premise?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes, proceed, and the plan now carries the corrected premise explicitly rather than inheriting the item's. `ykfgpd` instructs the executor to "move `discover_plans` from `INJECTED` into the clean-fingerprint set (which changes the pinned clean-move count of 23)" and to "add it to `tests/test_runner_refork_guard.py`'s `REFORK_TABLE`". Measured at review (F-6): that file was DELETED in `19313eed`, and no test anywhere reads the fingerprint fixture, so there is no clean-fingerprint set to move into and no table to add to. An executor following the item literally would look for two absent surfaces and could plausibly RECREATE one, which would reverse a deliberate suite-trimming decision. Resolved from repository evidence rather than by asking, because the repository answers it unambiguously (a deleted file and an AST walk finding none of the four cited test names). E-04 now states the prohibition, E-05 corrects the prose, and both deletion of the fixture and restoration of a guard are recorded as Deferred with their consequences. This is REVERSIBLE: if a maintainer wants the structural pin back, nothing here prevents adding one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff of the three changed definitions; paste `python3 -c "import inspect; from agent_workflows import runner_shared as r; print(inspect.signature(r.discover_plans))"` showing `(repo: pathlib.Path) -> dict[str, typing.Any]` with NO `parse_plan_file`; paste `python3 -c "from agent_workflows import oc_runipd as o, agy_runipd as a, runner_shared as r; print(o.discover_plans is a.discover_plans is r.discover_plans)"` printing `True`; paste `grep -rn "parse_plan_file=parse_plan_file" agent_workflows/` returning NOTHING; and paste a passing `python3 -m pytest tests/test_oc_runipd.py tests/test_orchestrator_retirement.py -o addopts="" -q` proving the three unchanged `discover_plans(repo)` call sites still work.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the docstring diff; paste the count sentence showing `NINE`; and paste a count of the surviving bullets in the `INJECTED DEPENDENCIES` block proving the stated number equals the listed number (a stale count is exactly the defect this item exists to prevent, so the two must be shown TOGETHER, not asserted).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `grep -rn "DIFFERENT NamedTuples\|different NamedTuples\|per-runner NamedTuples\|per-host NamedTuples" agent_workflows/` returning NOTHING (note the case-sensitive variants: the lowercase spelling at `runner_shared.py:69` is a real occurrence that an upper-case-only grep MISSES, which is how it was found at review); AND paste `grep -n "CORRECTED BY rununify 06" agent_workflows/runner_shared.py` plus the `SetMember` retraction still present, proving the two correct retractions were NOT collateral damage.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `INJECTED` table diff showing seven rows and the corrected docstring counts; paste a passing `python3 -m pytest tests/test_runner_shared.py -o addopts="" -q`; and paste `git status --porcelain tests/fixtures/runner_shared_premove_fingerprints.json` returning NOTHING, proving the orphaned fixture was not edited.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the three prose diffs; and paste `grep -rn "premove_fingerprints" tests/ agent_workflows/` showing every surviving mention now describes a historical capture rather than a live pin (quote each line, do not summarize).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the run showing one PASSING subtest per tracked tree (all five named). Then prove the test can FAIL, by mutation, and the mutation must be applied to the SOURCE FILE rather than to a module attribute: delete the `".aw/records/specs",` line from `agent_workflows/artifact_core.py`'s `SCAN_ROOTS` in the worktree, paste the specs case FAILING, then restore and paste `git diff --stat agent_workflows/artifact_core.py` showing an EMPTY diff. Monkey-patching `artifact_core.SCAN_ROOTS` at runtime does NOT work and must not be substituted: `iter_scan_files` binds `SCAN_ROOTS` as a DEFAULT ARGUMENT at def time (`artifact_core.py:531`), so a rebound module attribute is ignored and the mutation silently passes. Measured both ways at review: the attribute rebind still returned the specs item, the source edit returned zero items.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the workflow diff; paste `python3 -m agent_workflows check backlog --agent` with its EXIT CODE, and state explicitly whether any finding is error-or-warning severity versus `info` (an `info` finding is expected and does not fail the gate, so a bare "0 findings" claim would be false); and paste `grep -n "release-gates" -A3 .github/workflows/tests.yml` proving the adjacent release-gates step is STILL advisory.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the spec diff; paste `python3 -m agent_workflows specs check` with its exit code; and paste `git diff .aw/records/specs/implemented/20260817-2124-01-records-taxonomy-cleanup.spec.md` filtered to show that neither the `- Status:` line nor any `## Workflow history` line changed.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` (no added flags) showing 0 failed, and name any failure as pre-existing (with its node id and evidence it fails at the base commit) or new.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: five independent small cleanups grouped at the maintainer's stated preference for fixing small items together; each group is separately verifiable. The nine E-items are still FIVE concerns: items E-01 through E-05 are one concern (the `discover_plans` seam and every site whose text the signature change falsifies), split at review because one item spanning a signature, two host modules, a module docstring, a test table and three prose sites is not executable in one focused pass.

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING, since one part is not the routine cleanup the title suggests: E-07 makes a CI step FAIL-CLOSED, so after it lands any backlog conformance finding reds `main` for everyone. The baseline is clean at review, and the precondition DECISION 18-r2ks4k-D1 named (the backlog name/summary debt) is cleared, but the backlog tree is live and 336 items large, so the gate's cost is borne by whoever next writes a malformed item. The rest of the plan is comment, docstring, test and spec-prose work plus one signature change with no behavior effect.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the seven paths in `- Scope-Paths:` are the whole intended surface. Within `agent_workflows/runner_shared.py` only the `discover_plans` signature, its one call site in `initialize_run_core`, and the module docstring's `INJECTED DEPENDENCIES` block; within each host module only the `discover_plans` wrapper and the comment above it; within `tests/test_runner_shared.py` only the `INJECTED` table, the docstring counts that describe it, and the three prose sites naming the fingerprint fixture; within `tests/test_attention_contract.py` only the added test class; within `.github/workflows/tests.yml` only the `aw check backlog` step and its comment; within the spec only a new body section. An edit outside that surface is MADE and then JUSTIFIED at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path, which `aw ipd finalize` refuses to complete without.

EXPLICITLY NOT IN SCOPE, each carrying its own reason in Deferred: `tests/fixtures/runner_shared_premove_fingerprints.json` (do not edit and do not delete), any restored fingerprint or refork guard, the `aw check release-gates` CI step, and the two terminal records under `.aw/records/` that still quote the dissolved record split.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; `addopts` already supplies `-q -n auto --dist=worksteal` and the deselection markers, so do not add `-n0`, a second `-q`, or `-p no:randomly`. V-06's mutation must be RUN, not described: a pasted failure you did not produce is the specific dishonesty this plan is most exposed to, because F-8 shows the obvious form of that mutation passes vacuously.

GENUINE STOP CONDITIONS (unsafe or unresolvable, not scope questions): if any executing test turns out to read `runner_shared_premove_fingerprints.json` after all, stop and report rather than editing the fixture, because F-6 and therefore E-04's prohibition would be wrong; if `python3 -m agent_workflows check backlog` reports an ERROR-or-WARNING severity finding at execution time, stop and report rather than flipping the CI step, since E-07's premise is a clean baseline and reding `main` is the outcome it exists to avoid; if the records-taxonomy spec is found to already document the relocation technique, report it rather than adding a second copy.

Commit through `aw commit <plan> -- <paths>`, path-scoped, never `git add -A`, never push. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence before the terminal transition, which the RUNNER owns when it executes this plan in a lane and which the executor otherwise performs with `aw ipd finalize`, never with a raw `git mv`. Then set the five source backlog items (`ykfgpd`, `1gw7nl`, `2rb85l`, `e85snf`, `q0m7qf`) `done` with `--evidence` citing the executed plan; none carries `- Blocks-Release:`, so no gate handoff is required.
