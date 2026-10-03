# IPD: Silence the nested index refresh and tighten the rename and group machine assertions

- Date: 2026-10-01
- Kind: child
- Concern: `plans_refs.apply_renames` and `research_refs` each regenerate their manifest through a nested `plans_index.run_index` / `research_index.run_index` call that passes NO `quiet` key, so the regeneration announces itself on the OUTER command's stdout: `wrote        .aw/records/plans/INDEX.json, INDEX.md (1 plans)`. Measured at HEAD, this is the SECOND line of `aw rename plans --apply --json` stdout. Every other nested caller of the same function passes `quiet=True` and is therefore silent (`status_set._auto_index_types`, two in `artifact_rename`, and three more in `ipd_lifecycle`, `artifact_adopt` and `research_cmd`), so these two are the outliers, not the convention. `docs/cli-output-contract.md` Section 7 reserves stdout for structured results and Section 11.2 states "Progress cues MUST NEVER be written to `stdout`"; a nested regeneration's outcome line is exactly such a cue. Until it is gone, `json.loads(stdout)` cannot succeed on the `plans` or `research` paths even once Order 02 emits a correct payload.
- Scope: Pass `quiet=True` at the two nested `run_index` call sites that omit it, carry the regeneration into the structured payload as a `Change` rather than dropping the information, and TIGHTEN Order 02's parseability assertions for the `plans` and `research` types from payload-recoverability to strict `json.loads(stdout)`. EXCLUDES: changing `plans_index.run_index` or `research_index.run_index` themselves, changing `aw index <type>`'s own output, and the `--check` branch of either (which `wgp0g3` already addressed for a different caller).
- Scope-Paths: agent_workflows/plans_refs.py, agent_workflows/research_refs.py, tests/test_rename_group_machine_output.py
- Item-Dependencies: executed:vfqjc0
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: eeiytw
- Blocks-Release: next
- Set: eeiytw
- Order: 3
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: gzb2rq

## Workflow history

- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `eeiytw` as Order 03 of three children, owning the half the item calls "trivially available" plus the assertion tightening that makes the Set's claim true end to end. Every Findings row was MEASURED at HEAD `f824b915f` through the real CLI in throwaway git repos. Authoring found that the `research` path has the SAME un-quieted call, which the item does not mention (F-03).

## Goal

Make the one deliberate human-output change this Set contains, in its own Order so it is attributable: the nested manifest regeneration stops printing to the outer command's stdout. Then tighten the two assertions Order 02 had to leave loose, so that after this plan `json.loads(stdout)` succeeds on EVERY type under `--json`, which is the exact claim backlog item `eeiytw` makes and the condition for closing it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: silence the nested regeneration

- [ ] E-01 In `plans_refs.apply_renames`, add `quiet=True` to the `argparse.Namespace` passed to the nested `plans_index.run_index` call. Locate it BY SYMBOL and by the fact that it is the only `run_index` call in that module; it is wrapped in a bare `try`/`except Exception: pass` and its Namespace currently carries `dir`, `check`, `as_agent`, `json`, `no_color` and `limit`.
  - WHY `quiet=True` IS SUFFICIENT HERE AND WHY THIS IS NOT THE `wgp0g3` PROBLEM. The distinction is load-bearing and getting it wrong would mean rewriting a function that does not need it. `plans_index.run_index` honours `quiet` on its REGENERATION path: both the drift loop (`if drift and not getattr(args, "quiet", False)`) and the four outcome lines (`if not getattr(args, "quiet", False)`) are gated on it. What it does NOT honour `quiet` on is its `--check` branch, which returns before either gate. This call site passes `check=False`, so it is entirely inside the gated region. Plan `wgp0g3` had to replace a `check=True` call with a direct `check_drift` call precisely because `quiet` could not reach it; that reasoning does not apply here and must not be imported. The backlog item says this half is "trivially available", and it is right.
  - NOTE THE NAMESPACE CARRIES `as_agent` WHERE EVERY OTHER SITE CARRIES `agent`, and do not silently normalize it: `cli._nv_backend_args` reads BOTH spellings (`getattr(args,"agent",False) or getattr(args,"as_agent",False)`) because `as_agent` is a real alias elsewhere in the package, and `plans_index.run_index` passes the Namespace to `select_output`, which also reads both. Changing it is unnecessary and would be an unrelated edit inside a one-line fix. If the executor believes it is wrong, that is a separate finding to report, not to fix here.
  - DO NOT TOUCH `plans_index.run_index` ITSELF. Teaching its `--check` branch to honour `quiet`, or routing its lines to stderr, would change `aw index plans`'s own human output for every caller of that verb in order to fix one nested consumer. `wgp0g3` rejected exactly that alternative for exactly that reason and the reasoning stands.
  - Depends on: none
  - Expected outcome: `aw rename plans --apply` and `aw group plans --apply` no longer print the `wrote .aw/records/plans/INDEX.json, INDEX.md (N plans)` line, and `aw index plans` is unaffected.
  - Execution state: pending

- [ ] E-02 Do the same for `research_refs`: add `quiet=True` to the `argparse.Namespace` passed to its nested `research_index.run_index` call. This is a SEPARATE E-item and not part of E-01 because it is a different module, a different index implementation, and a different gate to verify: `research_index.run_index` has its own `quiet` handling that must be CONFIRMED to gate its outcome lines before this change can be claimed to work, rather than assumed by analogy with `plans_index`.
  - VERIFY THE GATE BEFORE TRUSTING IT. If `research_index.run_index` turns out NOT to honour `quiet` on its regeneration path, then `quiet=True` here is a no-op and this E-item's expected outcome is false. In that case do NOT widen the fix into `research_index`: report it, and carry the research half as a separate finding, because teaching that module a new option is the same "change a shared verb for one caller" move E-01 refuses. V-02 requires the gate be demonstrated, not asserted.
  - THE RESEARCH NAMESPACE DIFFERS FROM THE PLANS ONE: measured, it carries only `dir`, `check`, `agent` and `limit` (note `agent`, not `as_agent`, and no `no_color`). Add `quiet` to what is there; do not harmonize the two Namespaces, which would be unrelated churn.
  - Depends on: none
  - Expected outcome: `aw rename research --apply`, `aw group research --apply`, `aw research mv --apply` and `aw research set-assign --apply` no longer print the nested research-index outcome line, and `aw research index` is unaffected.
  - Execution state: pending

### Task group 2: keep the information rather than merely hiding it

- [ ] E-03 Carry the regeneration into the STRUCTURED payload as a `Change`, so silencing the line loses no information. Add the manifest paths to the facts Order 01 carries and Order 02 maps, with `kind="update"` and a detail naming the refresh, exactly as `status_set._auto_index_types` already does when it appends `Change(path=<...>/INDEX.json, kind="update", applied=True, detail="manifest index auto-refreshed")` after its own quiet regeneration.
  - THESE PATHS MUST NOT ENTER THE COMMIT PATH-SET, and this is the one way E-03 could do real damage. `MutationResult`'s docstring states there is "deliberately no `index_paths` companion" because the manifests "are generated output that no `aw` verb commits (idxuntrack `4r0qp1` E-03)". So the manifest entries belong in the payload's `changes` (which is a REPORT of what happened) and must NOT be added to `touched_paths` (which is the commit path-set `_offer_records_commit` consumes). V-03 requires proving the commit path-set is unchanged.
  - WHY REPORT THEM AT ALL, since they are gitignored generated views: because a machine consumer that just renamed a plan needs to know the manifest was refreshed, and because the human surface is LOSING a line here. Reporting the fact in the payload while removing it from the prose is what makes this a stream-separation fix rather than an information deletion. `status_set` already made this exact trade and is the precedent.
  - Depends on: E-01, E-02
  - Expected outcome: a machine consumer sees the manifest refresh as a `Change` with `applied: true`, while the commit path-set and the human surface carry no manifest path.
  - Execution state: pending

### Task group 3: tighten the assertions the Set left loose

- [ ] E-04 Tighten `tests/test_rename_group_machine_output.py` (created by Order 02) so the `plans` and `research` types are asserted with STRICT `json.loads(stdout)` rather than the payload-recoverability form Order 02 had to use while this nested line was still present, and add the two assertions this plan's own change requires:
  - (a) STRICT PARSEABILITY ON EVERY TYPE. Replace the recoverability assertion for `plans` and `research` with `json.loads(stdout)` under `--json`, and with "every non-blank line parses and exactly one carries `schema == "aw.agent/v1"`" under `--agent`. After this plan there is no remaining type where the loose form is needed, and V-04 must confirm that by asserting the strict form for all four types the module covers.
  - (b) THE NESTED LINE IS GONE FROM THE HUMAN SURFACE TOO. Assert the no-flag stdout of `rename plans --apply` and `research mv --apply` does NOT contain the manifest outcome line. This is the one place this Set DELIBERATELY changes human output, so it must be pinned as an intended behavior rather than left to be rediscovered as a regression.
  - (c) THE MANIFEST REFRESH IS IN THE PAYLOAD. Assert the emitted record's `changes` includes an entry whose path is the manifest and whose `applied` is true, which is E-03's deliverable.
  - (d) THE COMMIT PATH-SET IS UNCHANGED. Run `aw rename plans --apply --commit` and assert the resulting commit contains exactly the two plan paths and NO manifest path, which is the invariant E-03 could break.
  - (e) `aw index plans` AND `aw research index` ARE UNAFFECTED. Run each directly and assert their own output still contains the outcome line, which proves E-01/E-02 silenced the NESTED caller and not the verb itself.
  - UPDATING ORDER 02'S TEST FILE IS DELIBERATE AND IS WHY THAT FILE IS IN THIS PLAN'S `- Scope-Paths:`. The alternative, a second test module, would split one coherent surface across two files and leave the loose assertion in place forever as dead weight.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: the module asserts strict parseability on all covered types, pins the two deliberate human-output changes, and proves the commit path-set and the two index verbs are untouched.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE `quiet=True` CONVENTION IS ESTABLISHED AND THESE TWO SITES ARE THE OUTLIERS. Measured: `status_set._auto_index_types` passes `quiet=True` for both its plans and its research regeneration; `artifact_rename` passes it at both of its nested sites; `ipd_lifecycle`, `artifact_adopt` and `research_cmd` each pass it too. Only `plans_refs.apply_renames` and the `research_refs` regeneration omit it. So this plan is bringing two stragglers onto an existing convention, not inventing one.
- `quiet` GATES THE REGENERATION PATH BUT NOT THE `--check` PATH, and conflating the two is the specific mistake available here. `plans_index.run_index` reads `quiet` in exactly two places, both after its `if getattr(args, "check", False)` branch returns. A `check=False` caller (which both of this plan's sites are) is fully inside the gated region; a `check=True` caller is not, which is why plan `wgp0g3` had to replace its call with a direct `check_drift` instead of passing a flag.
- SILENCING MUST NOT DELETE INFORMATION, and the repository already has the pattern for that: `status_set._auto_index_types` regenerates quietly and then APPENDS a `Change` recording the refresh, so the fact survives in the structured surface. E-03 follows it rather than inventing a shape.
- THE MANIFESTS ARE GITIGNORED GENERATED VIEWS AND NO VERB COMMITS THEM (`MutationResult`'s docstring, citing idxuntrack `4r0qp1` E-03). That is why they may be REPORTED in `changes` but must never be added to `touched_paths`.
- THE SUITE RUNS BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`. Run `python3 -m pytest` with no added flags; use `-o addopts=""` only when per-test counts from a narrowed run are genuinely needed.

## Findings

Every row was measured at HEAD `f824b915f` on this lane's branch, through the REAL CLI in throwaway git repos unless the row says otherwise. A probe must pass `--no-commit` (or `--commit`), never `--yes`: measured, `rename`/`group` do NOT register `--yes`, so a probe passing it exits 2 on an argparse error and measures nothing.

| Id | Finding | Evidence |
|---|---|---|
| F-01 | **THE NESTED LINE IS REALLY THERE AND IS THE SECOND LINE OF STDOUT.** It appears on the apply path of both verbs, under both machine flags and with no flag, so it is not mode-aware in any way. | `rename plans abc123 --slug renamed-demo --apply --no-commit --json`: rc=0, stdout line 0 `renamed <old> -> <new>`, line 1 `wrote        .aw/records/plans/INDEX.json, INDEX.md (1 plans)`. `group plans abc123 --set newset --apply --no-commit --json`: 1 line, which is THAT line alone (the non-`--rename` form writes metadata only and prints no `renamed`), so on that invocation the nested line is the ENTIRE stdout. Identical under `--agent` and with no flag. |
| F-02 | **THE CALL SITE OMITS `quiet` ENTIRELY, which is the whole mechanical cause, and the fix really is one keyword.** | The Namespace passed to the nested `plans_index.run_index` in `plans_refs.apply_renames` carries `dir`, `check=False`, `as_agent=False`, `json=False`, `no_color=True`, `limit=None` and NO `quiet` key. `plans_index.run_index` gates both its drift loop and its four outcome lines on `not getattr(args, "quiet", False)`, and the `wrote ... (N plans)` string is one of those four. |
| F-03 | **THE RESEARCH PATH HAS THE SAME UN-QUIETED CALL, WHICH THE BACKLOG ITEM DOES NOT MENTION.** The item's SCOPE NOTE says the nested line "comes from a call that passes NO `quiet` key, unlike the three other nested callers" and names only the plans site. There is a second: `research_refs` calls `research_index.run_index` with a Namespace carrying `dir`, `check`, `agent` and `limit`, and no `quiet`. This is why E-02 exists as its own item. | Namespace inspected at the call site; it is wrapped in the same `try`/`except Exception: pass` shape as the plans one. Measured end-to-end, `research mv rrr123 --slug renamed --apply --no-commit --json` emits 11 stdout lines, and `aw rename research --apply --json` likewise emits a multi-line prose block, consistent with a nested index call that is not silent. |
| F-04 | **EVERY OTHER NESTED CALLER IS ALREADY SILENT, so this plan brings two stragglers onto a convention rather than inventing one.** | `status_set._auto_index_types` passes `quiet=True` in both its plans branch and its research branch; `artifact_rename` passes `quiet=True` at both its nested `run_index` sites; `ipd_lifecycle`, `artifact_adopt` and `research_cmd` each pass it as well. `rg -n "quiet=True" agent_workflows/` enumerates them. |
| F-05 | **THE INFORMATION-PRESERVING PATTERN ALREADY EXISTS AND IS WORTH COPYING RATHER THAN REINVENTING.** `status_set._auto_index_types` regenerates with `quiet=True` and then appends a `Change(path=<...>/INDEX.json, kind="update", applied=True, detail="manifest index auto-refreshed")`, so its machine consumers learn the manifest was refreshed even though nothing was printed. It does this only on the machine path (it is called with `changes=` there and without it on the human path). | Read at `status_set._auto_index_types`; the plans branch and the research branch each append their own `Change` entries. |
| F-06 | **THE MANIFESTS MUST STAY OUT OF THE COMMIT PATH-SET, and the prohibition is written down rather than inferred.** | `plans_refs.MutationResult`'s docstring: "The commit path-set is `touched_paths`, and that is the WHOLE of it. There is deliberately no `index_paths` companion: the backends still REGENERATE the INDEX.json/INDEX.md manifests, but those are generated output that no `aw` verb commits (idxuntrack `4r0qp1` E-03), so a caller must not add them back to a commit path-set." `cli._run_noun_verb`'s comment repeats it. |
| F-07 | **THE HUMAN SURFACE LOSES EXACTLY THESE LINES AND NOTHING ELSE, which is the entire user-visible cost of this plan.** On `group plans --apply` without `--rename` it is the only line, so that invocation becomes SILENT on success for a human. That is a real UX change a reviewer should agree to rather than discover, and it is the reason OQ-01 exists. | `group plans abc123 --set newset --apply --no-commit` (no flag): stdout is exactly `wrote        .aw/records/plans/INDEX.json, INDEX.md (1 plans)` and nothing else. The `--rename` form prints a `renamed ...` line too and so remains non-silent. |
| F-08 | **THE TEST BASELINE.** Bare `python3 -m pytest` on this lane at HEAD `f824b915f`, clean tree: `2 failed, 4533 passed, 2 skipped, 3 warnings in 265.54s` (232 deselected). BOTH failures are PRE-EXISTING live-corpus failures caused by OTHER parties' artifacts: `test_spec_review_attestation.py::...::test_every_real_spec_in_this_repository_still_conforms` (flagging `20261001-89xjll-...spec.md` for `attention.unsafe-field`) and `test_run_finding_reachability.py::...::test_unreachable_binding_refusal_fires_under_perturbation`. Re-derive your own; do not fix either here. | Pasted runner output, reproduced in V-04. `git status --short` and `git diff --stat` both empty at the time of the run. |

## Proposed changes (ordered, validatable)

1. `plans_refs.apply_renames`'s nested `plans_index.run_index` Namespace gains `quiet=True` (E-01, F-01, F-02).
2. `research_refs`'s nested `research_index.run_index` Namespace gains `quiet=True`, after confirming that module's gate honours it (E-02, F-03).
3. The manifest refresh is reported as a `Change` in the payload, following `status_set`'s pattern, and is kept out of the commit path-set (E-03, F-05, F-06).
4. Order 02's test module is tightened to strict `json.loads(stdout)` for `plans` and `research`, and gains assertions for the two deliberate human-output changes, the payload `Change`, the unchanged commit path-set, and the two index verbs being unaffected (E-04).

Not changed, deliberately: `plans_index.run_index` and `research_index.run_index` themselves, the `--check` branch of either, `aw index plans` / `aw research index` output, the `as_agent` spelling in the plans Namespace, and the commit path-set.

## Deferred / out of scope (with reason)

- **Teaching `plans_index.run_index`'s `--check` branch to honour `quiet`, or routing its lines to stderr.** Either changes `aw index plans --check`'s own human contract for every caller of that verb in order to fix nested consumers. `wgp0g3` faced the identical choice for a `check=True` call site and rejected it for this reason, solving it locally instead. This plan's sites pass `check=False` and are already inside the gated region (F-02), so the question does not even arise here.
  - Carrier-Declined: NOTHING IS OWED, because this row records a REJECTED ALTERNATIVE rather than unbuilt work. E-01 and E-02 close the defect completely at the two call sites that have it, so after this plan there is no residual behavior for a carrier to fix. The row exists so a reviewer meets the alternative and its cost rather than wondering whether it was considered. If a maintainer PREFERS the global change on taste grounds, that is a new preference to act on, not a defect this plan left behind.
- **`aw index <type>`'s own missing `--json`/`--agent` payload.** Measured: `aw index plans --json` emits the bare `wrote ...` line and no payload, so `index` has the same class of defect as `rename`/`group` on its own surface. It is excluded because `index` is a `read`-class verb whose `--limit` semantics are contested by open item `4uw9gy`, which measured `--limit` inert on `aw index --agent` and warns explicitly that on `index` it means a HOT-WINDOW SIZE that IS honoured in the human path, so a fixer must not "unify" it with the other verbs. Folding it in would mix that live question into this Set.
  - Carrier-Declined: NOTHING IS OWED BY THIS SET, because the only part of `aw index` that affects these verbs is the nested line, which E-01 and E-02 silence at the CALLER rather than at `index`. `index`'s own machine surface is a separate defect on a separate verb that already has an open item touching it; filing a second one from here would duplicate `4uw9gy`'s territory. Measured rather than assumed, which is what makes this a scoping decision and not an oversight.
- **The `index all` crash.** Measured incidentally: `aw index all --json` exits 1 with an unhandled `FileNotFoundError` from `prompts_index.run_index` writing `INDEX.json` into a non-existent `.aw/records/prompts/` directory.
  - Carrier-Declined: NOTHING IS OWED BY THIS SET, because it is a different defect (an unguarded directory write) on a different verb (`index`) that this Set does not modify. It is recorded rather than dropped because an executor probing index behavior will hit it and should know it is pre-existing. Whether to file an item from this measurement is a maintainer's scoping call.

## Scope check

- Over-scope: none. Two one-keyword production edits, one payload field, and a test file this Set itself created. `plans_index.py` and `research_index.py` are deliberately NOT in `- Scope-Paths:`, because F-02 shows the fix needs no change in either and a change there would alter an unrelated public surface.
- Under-scope: `aw index`'s own payload and the `index all` crash, both argued in Deferred with the measurement that makes them separate. After this plan the Set's claim is complete: `json.loads(stdout)` succeeds for every type on both verbs, which is what closes backlog item `eeiytw`.

## Required tests / validation

- `python3 -m pytest tests/test_rename_group_machine_output.py tests/test_plans_index.py tests/test_group_verb_policy.py -o addopts=""` (the Set's module, the index module whose behavior must NOT change, and the live module pinning these verbs' prose). Re-derive the baseline on the executor's clean tree first.
- Bare `python3 -m pytest`, full, against the executor's OWN clean-tree baseline, confirming F-08's two failures are still present and still pre-existing.
- END-TO-END through the real CLI in a throwaway repo: `json.loads(stdout)` SUCCEEDING under `--json` for `plans`, `specs`, `backlog` and `research`, on preview and apply, which is the Set's headline claim.
- `aw index plans` and `aw research index` run directly, showing their own outcome lines are UNCHANGED (the proof that the nested caller was silenced and not the verb).
- `aw rename plans --apply --commit` showing the commit path-set contains no manifest path.
- `aw ipd lint --phase pre-transition` conforming on this plan; `aw sanitize --agent` clean; `git status --short` showing only this plan's declared paths.

## Spec / documentation sync

- NO SPEC AMENDMENT IS REQUIRED, and the reason matters: this plan does not change a contract, it makes the code OBEY one already written. `docs/cli-output-contract.md` Section 7 already reserves stdout for structured results and Section 11.2 already states "Progress cues MUST NEVER be written to `stdout`"; HEAD violates both at these two call sites. No `.spec.md` is in `- Scope-Paths:` and none should be added, because writing one would assert a contract change that is not happening.
- NO DOC EDIT EITHER. The one user-visible change (F-07: the nested line leaves human stdout, making a bare `aw group plans --apply` silent on success) is not documented at HEAD, so there is no stale sentence to correct. If an executor finds documentation that PROMISES that line, the plan's premise is wrong and they should stop and report rather than edit prose outside the declared scope.
- The Set's one documentation amendment is Order 02's (`docs/cli-output-contract.md` Section 5's self-contradictory `complete` value) and is declared there, not here.

## Open questions

### OQ-01: Is it acceptable that a bare `aw group plans --apply` becomes SILENT on success for a human?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: YES, and it is the correct outcome, but it is flagged because it is the one change a human will SEE and a maintainer who relies on that line should be able to object at review rather than after execution. Measured (F-07): on the non-`--rename` form the nested manifest line is the ENTIRE stdout, so removing it leaves nothing. It is nonetheless right to remove, for three reasons. (1) THE LINE REPORTS THE WRONG THING: it announces that a GENERATED, GITIGNORED manifest was rewritten, not that the user's requested mutation succeeded, so a human reading it as confirmation is reading a coincidence. (2) IT IS EXACTLY THE CUE THE CONTRACT BANS ON THIS STREAM (Section 11.2), so keeping it to preserve familiarity would be preserving the defect. (3) THE INFORMATION IS NOT LOST: E-03 puts the refresh in the structured payload, where a machine consumer gets it reliably for the first time. ALTERNATIVE CONSIDERED AND REJECTED: have the verbs print their own success line so the human surface stays non-silent. Refused because it is a NEW human-output feature smuggled into a stream-separation fix, it would need its own wording decision, and the metadata-write case already has a preview line (`--- would set Set=... Order=... on <name> ---`) whose apply-path counterpart's absence is a pre-existing gap, not one this plan creates. If a maintainer wants a success line, that is a separate item to file. REVERSIBLE: yes, trivially; the fix is one keyword at two sites.

### OQ-02: Should the manifest paths be reported in the payload at all, given they are gitignored generated views?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: YES in `changes`, NEVER in `touched_paths`, and the asymmetry is the point. `changes` is a REPORT of what the command did; `touched_paths` is the COMMIT path-set `_offer_records_commit` consumes. The manifests really were rewritten, so omitting them from the report would make the payload less truthful than the prose it replaces, and this plan is removing the only signal a human had that it happened (F-07). But adding them to the commit path-set would stage generated files that `MutationResult`'s own docstring says "no `aw` verb commits" (F-06), which is a real regression with a named prior decision behind it (idxuntrack `4r0qp1` E-03). `status_set._auto_index_types` already resolves it exactly this way, reporting a `Change` after a quiet regeneration (F-05), so this is an existing pattern rather than a new judgement. V-03 requires the commit path-set be PROVEN unchanged, because that is the half where a mistake does damage. REVERSIBLE: yes; dropping the `changes` entry later would be a cosmetic reduction, whereas a committed manifest would have to be un-committed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: (a) PASTE `git diff -- agent_workflows/plans_refs.py` and confirm BY INSPECTION that the ONLY change is the addition of `quiet=True` to the nested `run_index` Namespace, that `check=False` is unchanged, that the surrounding `try`/`except Exception: pass` is unchanged, and that the `as_agent` spelling was NOT normalized. A diff that touches anything else in that function FAILS V-01, because this plan's human-output change must be exactly one line's worth and attributable. (b) PASTE THE BEFORE AND AFTER STDOUT of `rename plans --apply` and `group plans --apply` (no flag) and confirm the manifest line is present before and ABSENT after, with every other line byte-identical. (c) PROVE THE MANIFEST WAS STILL REGENERATED, which is the thing silencing could plausibly break: show `INDEX.json`/`INDEX.md` on disk reflect the new filename after the apply, so the refresh happened silently rather than not happening. (d) PASTE `aw index plans` run DIRECTLY, before and after, showing its own outcome line is UNCHANGED, which proves the nested caller was silenced and not the verb.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: (a) DEMONSTRATE THE GATE BEFORE TRUSTING IT, as E-02 requires: show that `research_index.run_index` actually honours `quiet` on its regeneration path, by calling it directly with `quiet=True` and `check=False` and pasting the captured stdout, which must be empty. If it is NOT empty, `quiet=True` is a no-op here, E-02's expected outcome is false, and V-02 FAILS: report it and do NOT widen the fix into `research_index`. (b) PASTE `git diff -- agent_workflows/research_refs.py` confirming the only change is the added `quiet=True` and that the Namespace's other keys (`dir`, `check`, `agent`, `limit`) are untouched and not harmonized with the plans one. (c) PASTE BEFORE AND AFTER STDOUT for all four research spellings (`aw rename research --apply`, `aw group research --apply`, `aw research mv --apply`, `aw research set-assign --apply`) with no flag, confirming the nested index line is gone and nothing else changed. All four, because they reach the backend from two different dispatch sites. (d) PASTE `aw research index` run DIRECTLY, before and after, showing its own output is UNCHANGED. (e) PROVE THE RESEARCH MANIFEST WAS STILL REGENERATED, the same way V-01(c) does for plans.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: (a) PASTE the emitted `--json` record for `rename plans --apply` and confirm its `changes` contains an entry for the manifest with `applied: true`, and that the path is REPO-RELATIVE (not absolute), per `docs/cli-output-contract.md` Section 4. (b) PROVE THE COMMIT PATH-SET IS UNCHANGED, which is the one way E-03 can do damage: run `aw rename plans --apply --commit`, paste `git show --stat` (or the staged path list) for the resulting commit, and confirm it contains exactly the two plan paths and NO `INDEX.json` or `INDEX.md`. F-06 records the written prohibition this protects. (c) CONFIRM THE HUMAN SURFACE DID NOT GAIN THE MANIFEST BACK: paste no-flag stdout and confirm no manifest path appears there either, so E-03 added a payload field and not a print. (d) STATE WHICH LAYER CARRIES THE ENTRY (whether the manifest paths travel as a new field on Order 01's facts or are appended by Order 02's mapper at the dispatch site) and why, since both are workable and a reviewer needs to know where to look.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: (a) PROVE THE TIGHTENED ASSERTIONS FAIL WITHOUT THIS PLAN'S PRODUCTION CHANGE. Revert E-01/E-02/E-03, run the module, and PASTE the failure output: the strict `json.loads(stdout)` assertions for `plans` and `research` MUST fail (the nested line is back), the human-surface assertions in (b) MUST fail, and the `specs`/`backlog` assertions MUST still pass (they are the control, unaffected by this plan). Then restore and paste them all passing. (b) PASTE THE STRICT ASSERTION RESULT FOR ALL FOUR TYPES, confirming no type is left on the loose recoverability form, and state plainly that Order 02's looser assertion has been REMOVED rather than left beside the new one. (c) PASTE the narrowed run `python3 -m pytest tests/test_rename_group_machine_output.py tests/test_plans_index.py tests/test_group_verb_policy.py -o addopts=""` against your OWN re-derived baseline. (d) PASTE YOUR OWN CLEAN-TREE BARE BASELINE, then the FULL BARE `python3 -m pytest` after the change, and state the delta against YOUR number. CONFIRM F-08's two failures are still present and still pre-existing; if either changed its failure mode, stop and report rather than absorbing it. (e) CONFIRM THE SET'S HEADLINE CLAIM END TO END, which is the claim backlog item `eeiytw` makes: paste `json.loads(stdout)` SUCCEEDING for `aw rename plans --apply --json` and `aw group plans --apply --json`, the two exact commands the item names, in a throwaway repo. This is the single piece of evidence a reader should be able to find fastest. (f) CONFIRM NO CODE-PINNING TEST WAS WRITTEN: no new or edited test reads production source via `inspect`, `ast`, regex or substring search, asserts a caller count or symbol census, or pins docstring or comment text (GUIDING_PRINCIPLES P16). Note that (b)'s human-surface assertion checks for the ABSENCE of a line in PROCESS STDOUT, which is an observable outcome, not a source pin. (g) PASTE `git status --short` showing only the three declared `- Scope-Paths:` entries plus this plan file, and `aw sanitize --agent` clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Explicit human approval is required before execution. This plan carries no `- Approval:` field and no `- Readiness:` field: both are attestations of acts (a human sign-off, a `/plan-review`) that have not happened, and writing either here would forge the evidence a gate reads.

An executor MUST: read `AGENTS.md`, `CONTRIBUTING.md` and this plan in full before editing; run the suite BARE (`python3 -m pytest`, no added flags, because `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`, and `-n0` costs several times the runtime here); paste ACTUAL runner output for every claim of a passing test; commit through `aw commit gzb2rq -- agent_workflows/plans_refs.py agent_workflows/research_refs.py tests/test_rename_group_machine_output.py`, never `git add -A`; and never push or tag.

HONESTY RULE (hard MUST): paste the ACTUAL runner output for every claim of a pass, never a summary you did not run. V-04(a) specifically requires a PRE-FIX FAILING run of the TIGHTENED assertions, and a fabricated one would assert exactly the coverage it exists to prove. V-01(b) and V-02(c) require BEFORE and AFTER stdout; pasting one side and asserting the other matched is not evidence.

THIS PLAN DEPENDS ON ORDER 02 AND DECLARES IT (`- Item-Dependencies: executed:vfqjc0`). Order 02 creates the test module this plan tightens and the payload this plan adds a `Change` to, so running this first would leave E-03 and E-04 with nothing to attach to. Note that E-01 and E-02 alone WOULD work standalone (they are one keyword each), so an executor may be tempted to land them early; do not, because doing so would silently falsify Order 01's and Order 02's byte-equality evidence, which both assert the human surface is unchanged.

THE ONE DELIBERATE HUMAN-OUTPUT CHANGE IN THIS ENTIRE SET LIVES HERE, which is why it is its own Order: a bare `aw group plans --apply` becomes SILENT on success for a human (F-07, OQ-01). That is intended and argued, but it is the thing a maintainer is most likely to object to, so it should be raised at review and not discovered afterwards.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the three paths in `- Scope-Paths:`. If the work genuinely requires a file outside it, MAKE the edit and JUSTIFY it at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path). Do not stop and wait over a scope question. Three conditions DO warrant stopping and reporting: `research_index.run_index` turning out NOT to honour `quiet` on its regeneration path (V-02(a)), which falsifies E-02's premise; finding documentation that PROMISES the nested line, which falsifies this plan's premise; and an unresolvable concurrent edit to `agent_workflows/plans_refs.py`, which pending plan `87m438` also declares in its own `- Scope-Paths:`.

BEFORE COMMITTING, verify the staged set with `git diff --cached --name-only` and unstage anything not yours with `git restore --staged <path>`: this is a shared checkout and a failed raw commit can leave a co-worker's restored paths in the index.

All open questions are resolved and none is blocking.

Before the terminal transition, `aw ipd lint --phase pre-transition` must report conforming AND every `V-*` item above must carry concrete pasted evidence. V-04(e) is the one that makes the whole Set meaningful: it is the backlog item's own two commands, parsing. The transition is then UNCONDITIONALLY owed with a CONDITIONAL owner: in a managed lane the RUNNER owns it (`aw ipd begin`/`finalize` refuse an agent there with `AW-LIFECYCLE-ROLE-001`), and only in an unmanaged or manual run does the executor run `aw ipd finalize gzb2rq --actor <agent/model> --message <summary> --apply` itself. Never hand-roll the move with `git mv` and never hand-edit `- Status: executed`.
