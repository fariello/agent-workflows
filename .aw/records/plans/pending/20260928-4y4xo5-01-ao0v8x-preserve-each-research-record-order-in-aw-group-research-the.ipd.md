# IPD: Preserve each research record Order in aw group research the way aw group plans already does

- Date: 2026-09-28
- Kind: child
- Concern: `aw group research <id6...> --set X --apply` WITHOUT `--order` RENUMBERS EVERY NAMED RECORD FROM ZERO. RE-REPRODUCED AT AUTHORING against this lane's own source (not inferred from the backlog item, and not taken on `e3hzyc`'s word) in a fresh throwaway git repo, driving the real CLI as a subprocess with `PYTHONPATH` pinned to this worktree. Two records seeded at filename Orders `03` and `07` were regrouped in one bare call and came back as `-00-` and `-01-`: `20260901-oldsetid-03-aaaaaa-first-doc.notes.md` -> `20260928-newsetid-00-aaaaaa-first-doc.notes.md` and `20260901-oldsetid-07-bbbbbb-second-doc.notes.md` -> `20260928-newsetid-01-bbbbbb-second-doc.notes.md`, exit 0, no warning that an Order changed.
  THE ROOT CAUSE IS ONE LINE WITH AN AMBIGUOUS SENTINEL, and it is the byte-identical line `e3hzyc` removed from the sibling backend. `research_refs.run_set_assign` reads the flag then substitutes ZERO when it is absent: `start = getattr(args, "order", None)` followed by `start_order=start if start is not None else 0`. `plan_set_assign` then formats `order=f"{start_order + i:02d}"` per named record, so the first named record always lands on `00` and the rest renumber from there. The signature default `start_order: int = 0` is what makes an ABSENT flag indistinguishable from a deliberate `--order 0`.
  THE FIX SHAPE IS ALREADY PROVEN IN THIS REPOSITORY, TWICE, which is why this is a port rather than a design. `plans_refs.plan_set_assign` now takes `start_order: Optional[int] = None` and resolves an absent flag PER RECORD through `plans_refs._preserved_order`, whose docstring names this exact defect and this exact id6 (`e3hzyc`); and `artifact_rename.run_group_generic` threads an `Optional[int]` (`order_val = (start_order + i) if start_order is not None else None`) so `compute_target_name` falls back to the filename's own `NN` (`order_num = new_order if new_order is not None else int(m_uni.group("nn"))`). Either is a direct model and E-02 must choose deliberately.
  THE RESOLUTION TIERS CANNOT BE COPIED BLIND, AND THIS IS THE FINDING THAT MOST CHANGES WHAT GETS BUILT (F-03). `plans_refs._preserved_order` reads the front-matter `- Order:` FIRST and the filename `NN` only as a fallback. On the research tree that tier order is ACTIVELY UNSAFE, because sibling item `f7a2kc` (`open`, unfixed at this HEAD) proves these very verbs leave `order:` STALE: they rename the file and never rewrite its frontmatter. Measured here in the same probe output that reproduces this defect: after the bare regroup the two records' names read `-00-`/`-01-` while their frontmatter still reads `order: 03`/`order: 07`. So a front-matter-first fix would read a value the previous run of this same verb corrupted. `f7a2kc`'s own note says so in as many words: fixing 4y4xo5 front-matter-first on a tree this item corrupted "would preserve a wrong Order with a clean conscience". This plan therefore resolves an absent `--order` from THE FILENAME's `NN`, which is the one tier the naming grammar guarantees and the tier the research tree's own `plan_mv` already trusts (it carries `order=parsed.order` straight from `parse_name`).
  IT IS ALSO THE REPAIR PATH, which is what makes it worse than a cosmetic renumber: `aw group research ... --set <new>` is how an operator regroups a record set, so following the documented verb silently renumbers the set it was asked to fix.
  AND THE HELP STRING DOCUMENTS THE BUG VERBATIM. `aw research set-assign --order` still reads `"Starting NN (default 0)."` (cli.py, the `p_research_setassign` parser), while the SHARED `rename`/`group` string `e3hzyc` fixed now reads "Omit it to PRESERVE each artifact's existing Order". Both spellings dispatch to the one backend this plan fixes (`artifact_types.TYPE_BACKENDS["research"]["group"] == "research_refs.run_set_assign"`, and `aw research set-assign` reaches `rr.run_set_assign` in cli.py), so after E-02 the research-specific string is not merely stale, it is WRONG about behavior the same command now has.
  SEVERITY, stated as the bug rule requires, AND IT IS WORSE THAN THE BACKLOG ITEM CLAIMS (F-10). The item's severity note says research records "carry no orchestrator-reserved 00 slot the way plans do", so the harm is merely a silent renumber. THAT IS WRONG, and the correction is a spec citation made twice in one spec: `agents-artifact-organization`'s `<NN>` naming bullet reads "`00` is the originating prompt (Section 4.6); `01..NN` are members; the reconciliation/synthesis is the last", and its Section 5.8 frontmatter schema repeats `order: 02  # read/execute order within the set (00 = originating prompt)`. So `00` IS a semantically reserved slot in the research tree too, and a bare regroup moves the FIRST NAMED RECORD INTO IT, claiming an arbitrary record is the set's originating prompt. That is the same class of corruption as parking a `Kind: child` in a plan's orchestrator slot, reached by a different route. On top of that it is a SILENT renumber of the whole named set, exit 0, leaving the recorded `order:` and the name disagreeing; `aw find --set` and the research INDEX read those values, and Section 5.8 calls that frontmatter "the source of truth".
- Scope: Make `aw group research` (and its `aw research set-assign` spelling, one shared backend) PRESERVE each named record's existing Order when `--order` is absent, resolving it from the filename's own `NN`, while keeping an explicit `--order N` renumbering the named records sequentially from `N` (including `--order 0`). Correct the one research-specific `--order` help string that documents the old default. Give `group research` the regression coverage it has none of. EXCLUDES: the stale-frontmatter defect owned by `f7a2kc` (this plan must not start writing frontmatter), the `aw group plans` date fallback owned by `j84jg3`, `plans_refs.py` and `artifact_rename.py` (both already correct and deliberately left byte-unchanged), extracting a shared helper across the two backends, and any refusal to place a record at Order 0.
- Scope-Paths: agent_workflows/research_refs.py, agent_workflows/cli.py, tests/test_group_verb_policy.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: 4y4xo5
- Blocks-Release: next
- Set: 4y4xo5
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: ao0v8x

## Workflow history

- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `4y4xo5`. NOTHING IN THE ITEM IS OBSOLETE: the defect re-reproduces at this HEAD through the real CLI, and the item's cited `research_refs.py` line offsets have DRIFTED (it names `:326`/`:164`/`:181`; the code is now at `run_set_assign` :384 and `plan_set_assign` :180, so every citation here is by SYMBOL with the offset appended, per `IPD-C801`). TWO CORRECTIONS THE ITEM DOES NOT CONTAIN, both found by reading rather than assumed. (1) THE ITEM'S OWN RECOMMENDED FIX ORDER IS UNSAFE AND IS NOT ADOPTED (F-03): it says to copy `plans_refs`'s "front-matter Order then the filename NN" tiers, but research frontmatter is exactly what sibling `f7a2kc` (still `open`) proves these verbs leave stale, and the probe run for this plan shows the stale `order: 03` sitting under a `-00-` name. This plan resolves from the FILENAME only and records why. (2) THE ITEM UNDERSTATES THE SEVERITY AND A SPEC SAYS SO (F-10): its severity note claims research has no reserved `00` slot, but spec `agents-artifact-organization` 5.8 annotates the schema `order: 02  # read/execute order within the set (00 = originating prompt)`, so a bare regroup moves an arbitrary record into the originating-prompt slot. The specs were read rather than grepped past, which also corrected an earlier draft of this plan's spec-sync section that wrongly asserted no spec governs the verb. (3) THE TEST FILE `e3hzyc` USED AS ITS MODEL NO LONGER EXISTS: `tests/test_awnaming_grammar_and_producers.py` was deleted in commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"), so `PlansMvPreservesOrderAndDateTests` and `PlansGroupPreservesOrderTests` are both gone and `grep -rn '_preserved_order' tests/` is empty. The plans-side fix is therefore UNPINNED too; this plan adds its own coverage to the surviving `tests/test_group_verb_policy.py`, which already drives `aw group` for both backends in a temp git repo, and does NOT restore the deleted file or re-pin the plans backend (out of fence).

## Goal

Stop a repair verb corrupting what it repairs: give `aw group research` the Order preservation `aw group plans` gained in `e3hzyc`, resolved from the one tier the research tree can currently trust.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the defect before changing it

- [ ] E-01 REPRODUCE THE DEFECT AS A FAILING TEST FIRST, so the fix is demonstrated rather than asserted. Add a test that seeds two conformant research records at filename Orders `03` and `07`, runs `aw group research <id6> <id6> --set <new> --apply` with NO `--order`, and asserts each record's filename `NN` slot is UNCHANGED (`03` stays `03`, `07` stays `07`). That assertion MUST FAIL at HEAD, where they become `00` and `01`.
  ADD THE SINGLE-RECORD CASE IN THE SAME ITEM, because it is the common operator action and it isolates the sentinel from the `+ i` arithmetic: one record at Order `03`, bare regroup, asserts `03` survives (at HEAD it becomes `00`).
  HOUSE IT IN `tests/test_group_verb_policy.py` AND REUSE THAT FILE'S EXISTING MACHINERY rather than inventing a fixture: it already has a `temp_git_repo` fixture (`git init -q` in `tmp_path`) and an in-process `_run_group` helper that calls `cli.main(["group", artifact_type, ...])` under `redirect_stdout`/`redirect_stderr`, and it already asserts that `"research" in GROUP_TYPES`. Seed records with the full required frontmatter block (`research_contract.FRONTMATTER_FIELDS`: id, created, set, order, topic, model, kind, status, outcome, summary, consumed-by) or the record will not resolve.
  DRIVE IT IN-PROCESS VIA `cli.main`, NOT AS A SUBPROCESS CLI CALL. This is a deliberate correction of a measured hazard: `e3hzyc`'s execution record reports that an editable install made `python3 -m agent_workflows` in a lane import the MAIN checkout, so a subprocess assertion can pass while the tree under test is unfixed (filed as `ccbe60`). The existing helper in this file is already in-process, so following the file's own convention avoids the hazard rather than working around it.
  - Depends on: none
  - Expected outcome: Two new tests FAILING at HEAD (one multi-record, one single-record), each showing a bare `aw group research` renumbering a named record's filename `NN` from its real Order to a zero-based position.
  - Execution state: pending

### Task group 2: port the shipped fix

- [ ] E-02 MAKE AN ABSENT `--order` DISTINGUISHABLE FROM `--order 0`, then preserve. In `research_refs.plan_set_assign` change `start_order: int = 0` to `start_order: Optional[int] = None`, and in `research_refs.run_set_assign` pass the flag THROUGH instead of collapsing it: delete the `start_order=start if start is not None else 0` substitution so `getattr(args, "order", None)` reaches the planner unchanged. In the planner's per-record loop, compute the Order as `(start_order + i)` when `start_order is not None` and otherwise from the record's OWN filename `NN`, which `plan_set_assign` already has in hand as `parsed.order` from `R.parse_name(src.name)` (note it is a two-digit STRING there, while the explicit branch is an int, so format both through the existing `f"{...:02d}"` or convert deliberately; do not let a string reach `+ i`).
  RESOLVE FROM THE FILENAME ONLY, AND SAY WHY IN A COMMENT. Do NOT copy `plans_refs._preserved_order`'s front-matter-first tiers: research frontmatter `order:` is left stale by these same verbs (`f7a2kc`, still open), so reading it first would preserve a value this verb previously corrupted. The filename `NN` is grammar-guaranteed and is the tier this module's own `plan_mv` already trusts. Cite `f7a2kc` in the comment so the next reader does not "fix" the tier order back.
  RECORD THE SHAPE CHOICE EXPLICITLY. Two in-repo precedents exist (`plans_refs._preserved_order`'s tiered lookup versus `artifact_rename.run_group_generic`'s threaded `Optional[int]`); state which was taken and why in the execution record. Do NOT extract a shared helper across the two backends, and do NOT touch `plans_refs.py` or `artifact_rename.py`.
  - Depends on: E-01
  - Expected outcome: `research_refs.plan_set_assign` takes `Optional[int]`; a bare regroup preserves each record's filename `NN`; an explicit `--order N` still renumbers sequentially from `N`. E-01's two tests now pass.
  - Execution state: pending

- [ ] E-03 FIX THE PREVIEW PATH SO A DRY RUN CANNOT ADVERTISE A RENUMBER THE APPLY NO LONGER PERFORMS. `research_refs._apply_renames` prints `--- would rename {p.old_path} -> {p.new_path.name} ---` from the planned names, so verify the preview reflects the preserved Order and correct it if it does not. This item exists because `e3hzyc`'s execution record reports exactly this site was missed by its own plan on the sibling backend ("`apply_renames`'s PREVIEW printed the loop index, so a dry run advertised a renumber the apply no longer performs"), so it is a KNOWN trap on the twin code path, not speculation. If inspection shows the research preview derives wholly from planned names and is already correct, record that negative finding with the evidence rather than editing the file.
  - Depends on: E-02
  - Expected outcome: A bare `aw group research` WITHOUT `--apply` previews the same preserved-Order names the `--apply` run produces, demonstrated by comparing the two, or a recorded negative finding that the preview was already correct.
  - Execution state: pending

### Task group 3: prove it, including the cases the fix must not break

- [ ] E-04 PIN THE MUST-NOT-BREAK BEHAVIORS, so the sentinel change cannot silently remove a working feature. Add: (a) an EXPLICIT multi-record renumber, `--order 1` over two records seeded at `03` and `07`, asserting they become `01` and `02` (measured working at HEAD, so this is a guard and MUST PASS both before and after E-02); and (b) an EXPLICIT `--order 0`, asserting the record lands at `00`, which proves the new `None` sentinel did not make a deliberate zero unreachable. Case (b) is the specific regression a naive "preserve always" fix introduces.
  ADD THE TIER-DISAGREEMENT CASE, which is this plan's own decision made falsifiable: seed ONE record whose filename `NN` is `00` while its frontmatter says `order: 03` (the exact state `f7a2kc` leaves, measured in the authoring probe), regroup it bare, and assert the result follows the FILENAME (`00`), not the frontmatter. This is the test that would fail if someone later reintroduces the front-matter-first tiers.
  - Depends on: E-02
  - Expected outcome: Three further tests passing, one of which (the explicit multi-record renumber) also passes at HEAD and is therefore proof the fix preserved an existing feature rather than replacing it.
  - Execution state: pending

- [ ] E-05 CORRECT THE HELP STRING THAT DOCUMENTS THE OLD DEFAULT. In `cli.py`, the `p_research_setassign` parser's `--order` argument reads `help="Starting NN (default 0)."`; rewrite it to describe the new contract in the same terms the SHARED `rename`/`group` string already uses ("Omit it to PRESERVE each artifact's existing Order; give it to renumber the named artifacts sequentially from NN"), adapted to records. Leave that shared string BYTE-UNCHANGED: `e3hzyc` already corrected it and it is out of this fence. Change no other help text.
  - Depends on: E-02
  - Expected outcome: `aw research set-assign --help` describes preservation rather than "default 0", and `aw group research --help` (the shared string) is unchanged.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This plan was authored against drifted offsets in its own backlog item and so follows this strictly.
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do not add `-n0`, a second `-q`, or `-p no:randomly` (AGENTS.md).
- Tests must assert OBSERVABLE BEHAVIOR, never code structure: no `inspect`/`ast`/regex reads of production source, no symbol censuses (AGENTS.md, GUIDING_PRINCIPLES P16). Every test this plan adds drives `aw group research` and asserts on resulting filenames.
- `tests/test_group_verb_policy.py` is the surviving home for `aw group` behavior across backends; it iterates `artifact_types.TYPE_BACKENDS` dynamically and drives `cli.main` in-process.
- A research record's frontmatter is a fenced YAML block whose required keys are fixed and ordered (`research_contract.FRONTMATTER_FIELDS`), with `order` validated as a two-digit STRING (`_ORDER_RE = re.compile(r"\A\d{2}\Z")`), unlike a plan's integer `- Order:`.
- Commit through `aw commit <plan> -- <paths>`, never `git add -A`; verify the staged set, since this checkout is shared (AGENTS.md).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The defect reproduces at this HEAD through the real CLI: two records at Orders `03`/`07` regrouped bare come back `00`/`01`, exit 0, no warning. | Throwaway git repo, subprocess CLI with `PYTHONPATH` pinned to this lane; output quoted in E-01/V-01. |
| F-02 | Root cause is the byte-identical line `e3hzyc` removed from the sibling backend: `start_order=start if start is not None else 0` in `research_refs.run_set_assign` against `start_order: int = 0` in `plan_set_assign`, formatted `order=f"{start_order + i:02d}"`. | `research_refs.run_set_assign` (:384ff), `plan_set_assign` (:180ff). |
| F-03 | THE BACKLOG ITEM'S RECOMMENDED TIER ORDER IS UNSAFE HERE. Research frontmatter `order:` is left stale by these same verbs (sibling `f7a2kc`, still `open`), so a front-matter-first resolution reads a value the verb itself corrupted. The authoring probe shows `order: 03` under a `-00-` name in the same output. | `f7a2kc` backlog item ("would preserve a wrong Order with a clean conscience"); probe AFTER block. |
| F-04 | `e3hzyc`'s cited model test file NO LONGER EXISTS: `tests/test_awnaming_grammar_and_producers.py` was deleted in `19313eed` (suite trim), so the plans-side fix is itself unpinned and `grep -rn '_preserved_order' tests/` returns nothing. | `git log --diff-filter=D`; empty grep over `tests/`. |
| F-05 | Two valid fix precedents exist, not one: `plans_refs._preserved_order` (tiered lookup) and `artifact_rename.run_group_generic` (threaded `Optional[int]` with a filename-`NN` fallback in `compute_target_name`). | `plans_refs.py` :208ff/:230ff; `artifact_rename.py` `order_val = (start_order + i) if start_order is not None else None` (:878), `compute_target_name` (:142). |
| F-06 | An explicit `--order` ALREADY WORKS and must not be broken: `--order 1` over `03`/`07` yields `01`/`02`, and `--order 0` yields `00`. Measured at HEAD. | Authoring probe cases 2 and 3. |
| F-07 | Both `aw group research` and `aw research set-assign` dispatch to the ONE backend fixed here, but have SEPARATE `--order` help strings; only the research-specific one still says "Starting NN (default 0)." | `artifact_types.TYPE_BACKENDS["research"]["group"]`; `rr.run_set_assign` dispatch in cli.py; `p_research_setassign` help versus the shared `rename`/`group` help. |
| F-08 | The research tree's own `plan_mv` already trusts the filename tier, carrying `order=parsed.order` from `R.parse_name`, so filename-only resolution is consistent with the sibling verb in the same module. | `research_refs.plan_mv` (:223ff). |
| F-09 | Baseline is clean in this lane, so any failure after the change is attributable to it. | `python3 -m pytest` -> `3202 passed, 2 skipped, 3 warnings in 53.77s`. |
| F-10 | THE BACKLOG ITEM UNDERSTATES THE SEVERITY. It says research has no reserved `00` slot, so the harm is only a renumber. The spec says otherwise TWICE: the naming section states "`00` is the originating prompt (Section 4.6); `01..NN` are members; the reconciliation/synthesis is the last", and the frontmatter schema repeats `order: 02  # read/execute order within the set (00 = originating prompt)`. So `00` IS semantically reserved and a bare regroup moves an arbitrary record into it. | Spec `agents-artifact-organization`, `<NN>` naming bullet and Section 5.8 schema; probe showing the first named record landing at `-00-`. |
| F-11 | `--order` is specified as OPTIONAL on the shared group surface (`aw group <type> <selector...> --set S [--order N] [--apply]`), so an omission that silently rewrites data is a defect against a written contract rather than an undefined case. | Spec `command-surface-redesign`, group row of the verb table. |

## Proposed changes (ordered, validatable)

1. Add failing coverage for the bare-regroup clobber, multi-record and single-record, in `tests/test_group_verb_policy.py` (E-01).
2. Change `research_refs.plan_set_assign`'s `start_order` to `Optional[int] = None`, stop `run_set_assign` collapsing absent to `0`, and resolve an absent flag from each record's filename `NN` with a comment citing `f7a2kc` for the tier choice (E-02).
3. Verify and if necessary correct the dry-run preview in `research_refs._apply_renames` so it cannot advertise a renumber the apply no longer performs (E-03).
4. Add the must-not-break guards (explicit multi-record renumber, explicit `--order 0`) and the tier-disagreement test pinning filename-over-frontmatter (E-04).
5. Rewrite the `p_research_setassign` `--order` help string, leaving the shared `rename`/`group` string byte-unchanged (E-05).

## Deferred / out of scope (with reason)

- STALE RESEARCH FRONTMATTER after rename/regroup (`set:`, `order:`, `model:` renamed in the filename and never rewritten in the block). This plan's F-03 DEPENDS on that defect still being live, because it is the reason an absent `--order` resolves from the filename rather than the frontmatter, so fixing it here would both break the fence and invalidate the tier decision. Kept name-only deliberately.
  - Carrier: f7a2kc
- `aw group plans` DATE fallback to the literal `20260101` for a plan carrying no `- Date:` line. A different field in a different backend, filed with its measurement by `e3hzyc` for the same reason this item was.
  - Carrier: j84jg3
- The lint/sweep REACHABILITY gap that let this class of defect stay invisible to `aw check` (a repair verb committing a state only a per-file verb detects). ALREADY DISCHARGED, not outstanding: `k9awrq` shipped and `aw check` now runs the `IPD-*` family, which is directly observable in this plan's own authoring, where `aw check plans` raised `check.ipd-uncarried-obligation` against this very file and `aw ipd lint` alone reported conforming. Recorded here because the backlog item cites the gap as context.
  - Carrier-Evidence: .aw/records/plans/executed/20260908-lintreach-01-k9awrq-run-the-ipd-lint-family-from-the-repo-wide-sweep-so-a-lint-r.ipd.md
- RESTORING the deleted `tests/test_awnaming_grammar_and_producers.py`, or otherwise re-pinning the plans-side `e3hzyc` fix that the suite trim left uncovered (F-04). Out of fence: `plans_refs.py` is not in `Scope-Paths`, and whether a deliberate suite trim should be partly reversed is a maintainer call about suite size rather than a defect this plan can assert. Raised for the reviewer to convert into an item if they disagree.
  - Carrier-Declined: not a defect this plan can assert; reversing a deliberate trim is a maintainer decision about suite size, and the plans backend's behavior is unchanged and still correct.
- EXTRACTING A SHARED HELPER across `plans_refs` and `research_refs`. Explicitly forbidden by `e3hzyc`'s approval gate, and F-03 now supplies an independent technical reason: the two backends need DIFFERENT resolution tiers (plans can trust their front matter, research cannot), so a shared helper would have to be parameterized by the very difference that matters.
  - Carrier-Declined: deliberate design choice, not deferred work; a shared helper is now known to be wrong rather than merely out of scope.
- ANY REFUSAL to place a record at Order `00`, as opposed to simply not doing it silently. Once E-02 lands, reaching `00` requires an explicit `--order 0`, which is a deliberate operator act; refusing it would also need a policy for the legitimate originating-prompt case that Section 5.8 defines.
  - Carrier-Declined: not a defect; the silent path is what this plan removes, and the explicit path is legitimate by spec.

## Scope check

- Over-scope: none. The three declared paths are the backend holding the defect, the one help string documenting it, and the test file pinning it.
- Under-scope: the fix does NOT make the record's frontmatter `order:` agree with its new name; after this plan a regrouped record still carries whatever `order:` it had, which is `f7a2kc`'s defect and is deliberately left visible rather than half-fixed here. A reviewer who wants name and frontmatter to agree in one pass should sequence `f7a2kc` first and re-fence both, accepting that the tier decision in E-02 would then need revisiting.

## Required tests / validation

- The five new cases in `tests/test_group_verb_policy.py`: bare multi-record preserve, bare single-record preserve, explicit `--order 1` sequential renumber, explicit `--order 0` reachable, and filename-over-frontmatter tier disagreement.
- FAILING-FIRST CONTRAST IS MANDATORY, not optional: run the new tests against UNFIXED source and paste the failure count, then against the fixed tree and paste the pass count. The bare-preserve cases must fail before and pass after; the explicit-renumber guard must pass in BOTH runs. A fix whose tests were never seen to fail has not been demonstrated.
- Bare `python3 -m pytest` before and after, with both summary lines pasted, against the `3202 passed, 2 skipped` baseline in F-09. The delta must be exactly the new cases.
- `aw sanitize --agent` clean (no maintainer/machine identifiers in anything authored).
- Negative proof that the fence held: `git diff --stat` shows no change to `agent_workflows/plans_refs.py` or `agent_workflows/artifact_rename.py`, and no shared helper was extracted.

## Spec / documentation sync

No spec amendment is required and no `.spec.md` file is in `Scope-Paths`, but that conclusion rests on reading the two specs that DO govern this verb rather than on a grep miss, and one of them corrected this plan's own severity claim.
- `agents-artifact-organization` Section 5.6 (`aw research set-assign` / `aw research mv`) specifies WHAT the verb does: "rename the target files to a set's `YYYYMMDD-<set-id>` and assign `NN`". It does not specify WHICH `NN` an absent `--order` assigns, so preserving the existing `NN` is consistent with it and no amendment is needed.
- THE SAME SPEC RESERVES `00`, which is what makes the defect worse than the backlog item claims (F-10). Its `<NN>` naming bullet reads "`00` is the originating prompt (Section 4.6); `01..NN` are members; the reconciliation/synthesis is the last", and Section 5.8's schema (which the spec calls "the source of truth") repeats the annotation. So the current behavior does not merely renumber: it asserts that an arbitrary named record is the set's originating prompt. This plan brings the code TOWARD that spec rather than changing it, which is precisely why no amendment is required.
- `command-surface-redesign` Section 73 specifies the shared surface `aw group <type> <selector...> --set S [--order N] [--apply]`, showing `--order` as OPTIONAL. A flag the spec marks optional whose omission silently rewrites data is a defect against that surface, not a contract this plan may rewrite.
So the behavior change is a DEFECT FIX toward contracts already written, matching what the sibling backend implements since `e3hzyc`. The only user-facing documentation touched is the `p_research_setassign --order` help string (E-05).
IF THE EXECUTOR FINDS a spec or README sentence asserting the "default 0" renumber as INTENDED behavior, that discovery changes this section: stop, add the file to `Scope-Paths`, amend it in the same change, and say why here, per the plan-may-amend-a-spec rule.

## Open questions

### OQ-01: Should an absent `--order` resolve from the filename `NN` only, or from frontmatter first as the backlog item recommends?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, filename-only. The item recommends copying `plans_refs`'s "front-matter Order then the filename NN" tiers, but that tier order is safe on plans and unsafe on research: sibling item `f7a2kc` (still `open`) establishes that `aw group research` and `aw research mv` rename the file and never update its frontmatter, and the authoring probe reproduces exactly that state (`order: 03` under a `-00-` name). Front-matter-first would therefore read a value this same verb corrupted. The filename `NN` is guaranteed by the naming grammar and is the tier this module's own `plan_mv` already uses. E-04 pins the decision with a tier-disagreement test so a later reader cannot quietly reverse it.

### OQ-02: Should a bare regroup PRESERVE, or should a multi-record call still renumber sequentially?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED as preserve-when-absent, renumber-when-explicit, matching the contract `e3hzyc` shipped for plans and the shared help string already advertises. Measured at HEAD (F-06): `--order 1` over two records yields `01`/`02`, which is a WORKING feature an operator uses to assemble a Set, so a preserve-always fix would be a regression. E-04 guards it, and also guards `--order 0` staying reachable once `None` becomes the sentinel.

### OQ-03: Does `aw research mv` share the defect?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: NO, and that is why the fix is a port rather than a design. `research_refs.plan_mv` carries `order=parsed.order` straight from `R.parse_name(src.name)`, so it already preserves the filename's `NN` and needs no change (F-08). It is out of `Scope-Paths` and must stay byte-unchanged. Its correctness is also the precedent E-02 follows within this one module.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: The pytest output for the two new bare-regroup tests run against UNFIXED source, pasted verbatim, showing them FAILING with the actual observed names (the `03`/`07` record asserted-`03`/`07` but found `00`/`01`). A pass here is a FAILURE of this validation: a test that does not fail at HEAD does not pin this defect.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: The same two tests now PASSING, pasted; plus the `git diff` of `research_refs.py` showing `start_order: Optional[int] = None`, the removal of the `else 0` collapse, and the filename-`NN` fallback with its `f7a2kc` comment. Plus a one-line statement of WHICH precedent shape was adopted (`_preserved_order` tiers versus threaded `Optional[int]`) and why. Plus negative proof of the fence: `git diff --stat` listing neither `plans_refs.py` nor `artifact_rename.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste BOTH the dry-run output (no `--apply`) and the `--apply` output for the same bare regroup, showing the previewed names and the applied names are the SAME preserved-Order names. If no edit was needed, paste the preview output proving it was already correct and state that `research_refs.py`'s preview code was not modified.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pytest output for the three guard tests in BOTH runs. The explicit-renumber guard must appear PASSING against unfixed source as well as after the fix (proving a preserved feature, not a new one); the `--order 0` and tier-disagreement cases must pass after. Paste both summary lines. Plus the bare `python3 -m pytest` summary after the change, compared against the `3202 passed, 2 skipped` baseline, with the delta shown to be exactly the five new cases.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `aw research set-assign --help` output showing the `--order` line no longer says "default 0", beside `aw group research --help` output showing the SHARED string byte-unchanged. Plus `git diff agent_workflows/cli.py` proving exactly one help string changed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution; it must not be executed on the strength of this authoring turn.

EXECUTION CONTRACT. Stay inside `Scope-Paths`: `agent_workflows/research_refs.py`, `agent_workflows/cli.py`, `tests/test_group_verb_policy.py`. Leave `plans_refs.py` and `artifact_rename.py` byte-unchanged and extract no shared helper between the backends. Do not begin writing research frontmatter: that is `f7a2kc`'s fence, and this plan's filename-only tier decision depends on not pre-empting it. Commit through `aw commit <plan> -- <paths>` with the staged set verified (the checkout is shared); never `git add -A`, never push, never `--no-verify`.
EVIDENCE CONTRACT. The failing-first contrast in V-01 is the gate: if the new bare-regroup tests cannot be observed failing against unfixed source, stop and report rather than proceeding, because the defect has then not been pinned. Paste actual runner output for every `V-*`; never record a pass not run. Be aware of the measured hazard behind E-01's in-process requirement: an editable install can make a subprocess `python3 -m agent_workflows` import the MAIN checkout rather than this lane (`ccbe60`), so a subprocess assertion can pass against unfixed source.
POST-GATE LIFECYCLE. On completion move this plan to `.aw/records/plans/executed/` only once `aw ipd lint --phase pre-transition` conforms and every `V-*` carries inspected evidence. The runner owns the transition in a managed lane (`aw ipd begin` refuses with `AW-LIFECYCLE-ROLE-001` there). Backlog item `4y4xo5` is set `graduated`, not `done`, by the authoring flow; do not close it here.
