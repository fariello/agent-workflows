# IPD: Cache an orchestrator probe verdict against a content digest that ignores execution state

- Date: 2026-09-07
- Kind: child
- Concern: Child 03 asks a model whether an orchestrator carries work no child covers. That answer costs tokens and time, and re-asking it about an UNMODIFIED orchestrator buys nothing. So the verdict needs a cache keyed on content. The naive key is a whole-file hash, and this repository has already MEASURED that as a dead end: `ipd_lifecycle.plan_content_digest` (`:457`) hashes exact bytes, and `frozen_region_digest` (`:462`) exists precisely because that made a begin receipt "go stale on every CORRECT execution" (backlog `xmqv5l`) - a conforming executor MUST tick checkboxes, fill `Observed evidence`, and append `## Workflow history`, so the byte digest changed while the reviewed contract had not. A byte-keyed probe cache would repeat that error and re-spend on every tick.
  THE EXISTING DIGEST ALREADY PASSES FOUR OF THE FIVE TESTS THIS CHILD PROPOSES, AND FAILS THE FIFTH. Measured at review by calling `frozen_region_digest` on a real orchestrator (`cczotj`): ticking a checkbox, filling an `Observed evidence`, appending a history line, and editing a prose section ALL leave the digest unchanged, and editing an E-item's action text DOES change it. So E-02's `xmqv5l` proof is, for those five cases, a proof about code that already exists. The ONE case where it differs is the one this child actually needs: editing the `## Child IPDs` table does NOT change `frozen_region_digest`, because `_requirements_from_plan` reads only `Scope-Paths`, E-item text and V-item text. That single gap is the whole justification for a new digest, and the plan never said so. See F-4.
- Scope: The verdict store and its key. IN: a digest over ONLY what the probe's answer depends on (the orchestrator's E-item action text plus its child table), excluding execution state, checkbox marks, workflow history, and prose sections; a per-repo verdict store recording digest, verdict, timestamp, and the model that answered; read/write helpers with a fail-closed miss; a child-table extraction, since no existing parser exposes it in a form this digest can consume. OUT: the probe itself and its prompt (child 03), the refusal surfacing (child 01), and any change to `plan_content_digest` or `frozen_region_digest`, which other gates depend on.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_orchestrator_probe_cache.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: no-go
- Set: orchprobe
- Order: 2
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 8tgg6g

## Workflow history
- 2026-09-07 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review REVIEWED - OPEN QUESTIONS; PR-001..PR-008, seven FIXED and one OPEN. THE BLOCKER IS A PORTABILITY DEFECT IN THE STORE'S SITING, AND THE FINDING THAT AUTHORIZED IT CITED THE WRONG FILE. F-3 said `.aw/.gitignore` already ignores the runtime tree, so the store needs no new rule. Measured: `.aw/.gitignore` says NOTHING about `state/` (its only `state` string is a comment about `records/runs/`); the rule that ignores it HERE is the ROOT `.gitignore:60`, which the installer explicitly never writes ("it is NOT the user's root `.gitignore` (that is never touched here)", `engine.py:4308-4313`), and `_AW_GITIGNORE_TEMPLATE` contains ZERO occurrences of `state/`. Reproduced in a throwaway repo with that exact template installed: `git check-ignore .aw/state/runtime/probe-verdicts.json` exits 1, NOT ignored. So the store is gitignored in THIS repo by an accident of local history and committable in every adopter, which for a file recording LLM verdicts against machine paths is a leak-sanitizer concern, not just untidiness. V-03's `git check-ignore` would have PASSED here and proven nothing about an adopter. SECOND, THE DIGEST'S JUSTIFICATION WAS ALMOST ENTIRELY REDUNDANT AND ITS ONE REAL GAP WENT UNSTATED: measured, `frozen_region_digest` already ignores all four mutations E-02 tests and already changes on an E-item edit, so the ONLY behavior this child adds is child-table sensitivity, which it does not change. THIRD, E-01's stated reuse cannot deliver: `ipd_lint.parse` exposes no child table at all (its `ParsedDoc` has no such field), so the extraction must come from `ipd_set_plan.parse_child_table` or be written, and E-01 claimed the reuse without checking. OPEN: OQ-02 (`Blocking: yes`, PR-001) asks where the store may live given the adopter gap. ALSO FIXED: a lazy-import requirement the plan omitted (`runner_shared` imports no first-party module but `render_stream`, and `ipd_lifecycle` imports `ipd_lint` lazily at all seven of its sites), the "~46" count (measured 47), a `frozen_region_digest` line citation off by one, and an OQ-01 that asked the executor to confirm self-invalidation without naming the property that makes it true.

- 2026-09-07 to-review (aw set): Authored and ready for critique: lint conforming, E/V bijection, every V-item demands pasted evidence. Set records the REJECTED syntactic-linter shape and why (it cannot separate legitimate orchestration from parent-only work, and its false positives push agents to delete the orchestration checklist), plus the deferred positive-assertion shape and its backfill cost.

- 2026-09-07 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the probe cheap to keep on: an orchestrator whose meaningful content has not changed is never re-probed, while any change to what the probe reasons about does re-probe. A cache MISS must never be mistaken for a pass.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: a key that ignores what does not matter

- [ ] E-01 Make the orchestrator's CHILD TABLE readable from `runner_shared` by reusing `ipd_set_plan.parse_child_table` (`:334`) through a function-local import.
  WHY THE PLAN'S ORIGINAL PREMISE WAS WRONG. It said to reuse `ipd_lint.parse`'s extraction. Measured at review, `ParsedDoc` has NO child-table field (`title`, `meta_fields`, `meta_errors`, `h2`, `exec_leaves`, `valid_leaves`, `exec_task_groups`, `open_questions`, `size_assessment`, `history_lines`). The parser that does have it is `ipd_set_plan.parse_child_table`: it finds the section by the schema heading `ipd_schema.H_CHILD_IPDS`, resolves columns by header name rather than index, and returns a typed refusal reason. Do NOT write a second table parser beside it. If its `rows` shape is insufficient for a digest, state precisely what is missing rather than reimplementing.
  WHY THE IMPORT MUST BE LAZY. `runner_shared` has exactly ONE module-level first-party import (`render_stream`, `:136`), and `ipd_lifecycle` reaches `ipd_lint` through a function-local import at all seven of its sites (`:515`, `:560`, `:950`, `:1326`, `:1783`, `:2046`, `:2618`). A module-level import here would change the graph for both host drivers.
  - Depends on: none
  - Expected outcome: a child-table extraction available to `runner_shared` via a lazy import of `ipd_set_plan`, with no new parser written and no new module-level first-party import added to `runner_shared`.
  - Execution state: pending

- [ ] E-02 Build the cache key: a stable digest over the orchestrator's E-item ACTION TEXT and its child table, and nothing else. Take the E-item text the same structural way `frozen_region_digest` does (`ipd_lint.parse` separates a leaf's action text `Leaf.text` from its sub-fields `Leaf.fields` and its checkbox `Leaf.checked`, `ipd_lint.py:146-155`), and take the child table from E-01. Serialize deterministically (`sort_keys=True`) so the digest is stable across runs and dict ordering.
  KNOW WHAT IS ACTUALLY NEW HERE, because most of it is not. Measured at review on a real orchestrator, `frozen_region_digest` ALREADY ignores a checkbox tick, a filled `Observed evidence`, an appended history line and a prose edit, and ALREADY changes on an E-item action edit. The ONLY behavior this digest adds is CHILD-TABLE SENSITIVITY: a child-table edit leaves `frozen_region_digest` unchanged, because `_requirements_from_plan` (`ipd_lifecycle.py:517-548`) reads only `Scope-Paths`, E-item text and V-item text. So this function exists for one reason, and the child-table case is the one that must not regress. Note also what it deliberately DROPS relative to `frozen_region_digest`: `Scope-Paths` and V-item text, neither of which the probe reasons about. State that choice rather than leaving it implicit.
  - Depends on: E-01
  - Expected outcome: a digest function unchanged by ticking a box, filling evidence, appending history or editing prose, and changed by editing an E-item's action text OR the child table; the divergence from `frozen_region_digest` (child table in, Scope-Paths and V-items out) stated in its docstring.
  - Execution state: pending

- [ ] E-03 Prove the `xmqv5l` trap is avoided, as a first-class deliverable rather than a side effect. Take a real orchestrator, apply each mutation a conforming executor makes (tick a checkbox, fill an `Observed evidence`, append a history line, edit a prose section), and assert the digest is IDENTICAL after each. Then edit an E-item action and assert it CHANGES. Then EDIT THE CHILD TABLE and assert it CHANGES: that case is the reason this digest exists at all, and it is the one `frozen_region_digest` fails, so a proof that omits it proves only that the new function matches the old one.
  - Depends on: E-02
  - Expected outcome: pasted before/after digests for four no-op mutations and TWO real ones (an E-item action edit and a child-table edit).
  - Execution state: pending

- [ ] E-04 Add the verdict store: per-repo, holding the digest, the verdict, when it was recorded, and WHICH MODEL answered. Record the model because a verdict is only as good as its author, and a future reader must be able to distrust an old one. Resolve the store's LOCATION per OQ-02 before writing it, and route the path through `ipd_lifecycle.checkout_control_root` (as `_runtime_dir` does, `:267-274`) rather than composing `repo_root / ".aw" / ...`, because an in-lane invocation's `repo_root` is the LANE and backlog `dh0uno` records that composing it by hand produced a second control store the driver could not see and teardown deleted.
  DO NOT ASSUME IT IS GITIGNORED. In THIS repo `.aw/state/` is ignored by the ROOT `.gitignore:60`, which the installer never writes; the framework-owned `.aw/.gitignore` it DOES write contains no `state/` entry, so in an adopter the path is NOT ignored (reproduced at review: `git check-ignore` exits 1). Whatever location OQ-02 settles on, the ignore rule must be verified in a FRESH repo carrying only what the installer emits, not in this one.
  - Depends on: E-02
  - Expected outcome: write-then-read round-trips; the store path is derived from `checkout_control_root`; a corrupt or unreadable entry is treated as absent rather than raising; the ignore status proven in an adopter-shaped repo.
  - Execution state: pending

- [ ] E-05 Make a MISS fail closed, and decide the FAIL-caching question OQ-01 records. A missing entry means "not probed", which child 03 must treat as blocking, never as a pass: the whole point is that silence stops meaning safe. Then determine from the real digest function whether a `CONTAINS EXECUTIONS` verdict can be safely cached, and record the finding either way rather than assuming it.
  - Depends on: E-02, E-04
  - Expected outcome: an explicit tri-state (`pass` / `fail` / `unknown`), with `unknown` returned for a miss, and a recorded decision on caching failures with its evidence.
  - Execution state: pending

- [ ] E-06 Add a STALENESS guard on the stored verdict, which nothing else in this child provides. A digest match proves the orchestrator has not changed; it proves nothing about whether the ANSWER is still trustworthy, and the plan already accepts that premise by recording the model ("a future reader must be able to distrust an old one") without giving anyone a mechanism to act on it. Decide and implement the minimum: at least make a verdict recorded by a DIFFERENT model than the current run resolves, or older than a stated bound, read as `unknown` rather than as its recorded value. State the rule and its default explicitly; an unbounded cache of LLM verdicts is a cache that eventually answers for a model nobody would ask.
  - Depends on: E-04, E-05
  - Expected outcome: a stated staleness rule, implemented, with a verdict that fails it returning `unknown`; the default bound recorded with its rationale.
  - Execution state: pending

- [ ] E-07 Confirm both hosts share every symbol added, by OBJECT IDENTITY not grep (`2r306y`/`818uru`). `agy_runipd` imports 47 names from `oc_runipd` (measured by AST walk 2026-09-07; backlog `cnwy8g` recorded 40, so it is growing), and no symbol this child adds may deepen that: both hosts import from `runner_shared`, never from the other host's driver.
  - Depends on: E-02, E-04, E-05, E-06
  - Expected outcome: pasted proof each new symbol is one shared object defined in `runner_shared`, and that the oc-to-agy import count did not increase from 47.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `frozen_region_digest`'s docstring is the design brief for this child. It documents both the failure (a byte digest punishes correct execution) and the fix (hash the reviewed contract, not the file), and it names exactly which fields are mutable state. Read it before writing E-02. Read `_requirements_from_plan` (`:517-548`) too, since that is what decides what the existing digest covers, and it is why a child-table edit does not move it.
- MEASURE THE EXISTING DIGEST BEFORE WRITING A NEW ONE. It already satisfies four of the five properties this child was authored to establish; only child-table sensitivity is genuinely new. A new function that merely reproduces the old one is cost with no benefit.
- `ipd_lint.parse` does NOT expose the child table. Its `ParsedDoc` fields are `title`, `meta_fields`, `meta_errors`, `h2`, `exec_leaves`, `valid_leaves`, `exec_task_groups`, `open_questions`, `size_assessment`, `history_lines`. The child-table parser is `ipd_set_plan.parse_child_table` (`:334`).
- IMPORT THE IPD PARSERS LAZILY from `runner_shared`. It has exactly ONE module-level first-party import (`render_stream`, `:136`), and `ipd_lifecycle` reaches `ipd_lint` through a function-local import at all seven of its call sites. Adding a module-level `ipd_lint`/`ipd_set_plan` import to `runner_shared` would change the import graph for both host drivers.
- THE STORE IS NOT GITIGNORED BY THE FRAMEWORK. In this repo `.aw/state/` is ignored by the ROOT `.gitignore:60`. The installer explicitly does not write that file ("it is NOT the user's root `.gitignore` (that is never touched here)", `engine.py:4312-4313`), and `_AW_GITIGNORE_TEMPLATE` has no `state/` entry, so in an adopter the path is tracked. Verify any ignore claim in a fresh repo carrying only installer output.
- Route control-state paths through `ipd_lifecycle.checkout_control_root`, never `repo_root / ".aw" / ...`: in a lane worktree `repo_root` is the LANE, and backlog `dh0uno` records that hand-composition produced a second store the driver could not see and teardown deleted.
- Do NOT modify `plan_content_digest` or `frozen_region_digest`. The begin receipt gate depends on them, and changing either would alter an unrelated safety check.
- BASELINE, MEASURED AT REVIEW: `python3 -m pytest` bare at HEAD `125105fe` gives `1 failed, 5632 passed, 3 skipped, 2 xfailed`. The single failure is `tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows`, which asserts `{"kgpptv": "reviewed"}` while `kgpptv` reads `- Status: approved`: a test coupled to this repository's mutable plan statuses, unrelated to this child. Re-measure in the executing worktree and compare failing NODE IDS, never totals.

## Findings

| Id | Severity | Location (2026-09-07) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `ipd_lifecycle.py:462` | The whole-file digest was measured to fail for this exact reason (`xmqv5l`); a byte-keyed cache would re-spend on every checkbox tick. | docstring records the measured failure |
| F-2 | MED | `ipd_lint.py:146-155` | `Leaf` already separates action text from sub-fields and checkbox state, so excluding mutable state is structural, not a fragile text rule. | source read |
| F-3 | BLOCKER | root `.gitignore:60`; `engine.py:4308-4313`, `_AW_GITIGNORE_TEMPLATE`; `.aw/.gitignore` | **THE STORE'S SITING RELIES ON AN IGNORE RULE THE FRAMEWORK NEVER SHIPS.** The original F-3 claimed `.aw/.gitignore` already ignores the runtime tree. It does not: that file says nothing about `state/` (its only `state` string is a comment about `records/runs/`). The rule ignoring it HERE is the ROOT `.gitignore:60`, which the installer explicitly never touches, and the template it DOES write contains zero occurrences of `state/`. So in every adopter repo the verdict store would be a TRACKED file holding LLM verdicts keyed to machine-local paths, which is a leak-sanitizer concern rather than mere untidiness. V-03's `git check-ignore` would have passed in this repo and proven nothing about an adopter. | reproduced in a throwaway repo carrying only `_AW_GITIGNORE_TEMPLATE`: `git check-ignore -v .aw/state/runtime/probe-verdicts.json` exits 1 (NOT ignored), while the same command in this repo matches `.gitignore:60` |
| F-4 | HIGH | `ipd_lifecycle.frozen_region_digest`, `_requirements_from_plan` (`:517-548`) | **FOUR OF THE FIVE PROPERTIES THIS CHILD PROPOSES TO ESTABLISH ALREADY HOLD, AND THE ONE REAL GAP WAS UNSTATED.** Measured on orchestrator `cczotj`: `frozen_region_digest` is UNCHANGED by a checkbox tick, a filled `Observed evidence`, an appended history line and a prose edit, and CHANGES on an E-item action edit. It does NOT change on a child-table edit, because `_requirements_from_plan` reads only `Scope-Paths`, E-item text and V-item text. Child-table sensitivity is therefore the sole justification for a new digest, and E-02's proof as authored would have demonstrated only parity with the existing function. | called `frozen_region_digest` on the real file with each mutation applied; four `same=True`, E-edit `same=False`, child-table edit `same=True` |
| F-5 | HIGH | `ipd_lint.ParsedDoc`; `ipd_set_plan.parse_child_table` (`:334`) | **E-01's STATED REUSE DOES NOT EXIST.** The plan says to reuse `ipd_lint.parse`'s extraction for the child table, but `ParsedDoc` has no child-table field, so the executor would have discovered the gap mid-implementation and most likely written a second table parser beside `ipd_set_plan.parse_child_table`, which already resolves columns by header name and returns a typed refusal reason. | printed `ParsedDoc._fields`; no child/table member |
| F-6 | MED | `runner_shared.py:136`; `ipd_lifecycle.py:515`, `:560`, `:950`, `:1326`, `:1783`, `:2046`, `:2618` | `runner_shared` has exactly ONE module-level first-party import and `ipd_lifecycle` reaches `ipd_lint` lazily at every site, so this child must import the IPD parsers inside functions. The plan did not say so, and a module-level import would change the graph for both drivers. | AST walk over `runner_shared`'s `ImportFrom` nodes at col 0 |
| F-7 | MED | measured | `agy_runipd` imports 47 names from `oc_runipd`, not the "~46" cited; `cnwy8g` recorded 40, so the coupling is still growing and a `~` figure is not a baseline a V-item can check. | AST walk over `ImportFrom` nodes targeting `oc_runipd` |
| F-8 | MED | plan E-03 (pre-revision) | The store records WHICH MODEL answered and the plan justifies it as letting "a future reader distrust an old one", but nothing consumed that field, so a verdict from a model nobody would ask today would still be served as authoritative forever. | plan read against its own E-items; no staleness rule anywhere |

## Proposed changes (ordered, validatable)

1. E-01 gets the child table from the parser that already has it, lazily.
2. E-02 builds the key; E-03 proves it, including the child-table case that is its only reason to exist.
3. E-04 adds the store (location per OQ-02, path via `checkout_control_root`); E-05 makes a miss fail closed and settles fail-caching.
4. E-06 makes the recorded model actionable via a staleness rule.
5. E-07 proves one shared definition without deepening the oc-to-agy coupling.

## Deferred / out of scope (with reason)

- The probe and its prompt: child 03 owns them, including the suspicion bias.
- Committing verdicts to git: deliberately not done. A verdict is an LLM output; keeping it box-local matches the receipt precedent and avoids a stale answer travelling to another machine. Cost accepted: a fresh clone re-probes once. NOTE this is a DECISION the current siting does not yet enforce in an adopter (F-3), which is what OQ-02 resolves.
- Any change to the two existing digest functions.
- Adding a `state/` entry to `_AW_GITIGNORE_TEMPLATE` so the framework ships the rule it relies on: that is a genuine defect this child MEASURED but it belongs to the installer, affects every adopter, and is one of OQ-02's options rather than a change to smuggle in here. If OQ-02 does not choose it, file it.
- Reconciling `frozen_region_digest` and the new digest into one parameterized function: tempting after F-4, but `frozen_region_digest` is a begin-receipt gate input and this child's fence forbids touching it.

## Scope check

- Over-scope: none. Note `Scope-Paths` deliberately does NOT include `engine.py`: the installer-template gap F-3 found is real but is OQ-02's to route, not this child's to fix silently.
- Under-scope: none remaining. The child-table extraction (E-01) and the staleness rule (E-06) were under-scope before review.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, baseline measured there and pasted, comparing failing NODE IDS not totals. In addition, the ignore-status check must run in a FRESH repo carrying only what `aw install` emits, because this repository's root `.gitignore` masks the adopter behavior (F-3).

## Spec / documentation sync

N/A for the cache mechanism: an internal store with no user-facing contract, and child 03 owns the spec sync for the gate.

ONE EXCEPTION TO CHECK RATHER THAN ASSUME: if OQ-02 resolves toward adding `state/` to `_AW_GITIGNORE_TEMPLATE`, that changes what every adopter receives on install, which IS a documented contract (spec `kw5y2s` governs the workspace hierarchy and the install-time emission). Whoever makes that change owes the spec amendment and must declare the file in `Scope-Paths`; this child does not, because the change is out of its fence.

## Open questions

### OQ-01: Is a `CONTAINS EXECUTIONS` (fail) verdict cached, or only a pass?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: E-05 decides FROM THE REAL DIGEST FUNCTION. Caching a pass is the money saver and is clearly safe. Caching a fail is probably safe, and the PROPERTY that would make it safe is now nameable rather than hoped for: the remedy for a `CONTAINS EXECUTIONS` verdict is to move the work into a new child, which edits BOTH the E-item text and the child table, and E-02's digest covers both, so a genuine fix self-invalidates the entry. CONFIRM that on the implemented digest by actually performing the remedy on a fixture and showing the digest move; do not infer it. A pinned stale fail would block a corrected orchestrator, which is the failure mode worth one test.

### OQ-02: Where may the verdict store live, given the framework does not ship the ignore rule this child assumed?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: NOT RESOLVABLE FROM THE REPOSITORY, because every option trades a different cost and one of them changes what all adopters receive. Measured: `.aw/state/runtime/` is ignored HERE only by the root `.gitignore:60`, which `aw install` never writes; the framework-owned `.aw/.gitignore` has no `state/` entry, so in a fresh adopter the store is a tracked file (reproduced: `git check-ignore` exits 1). FOUR OPTIONS. (a) ADD `state/` TO `_AW_GITIGNORE_TEMPLATE`, the honest fix, since the framework would then ship the rule its own layout policy already asserts (`install_wizard` refuses a tracked `state_runtime` policy); cost is an `engine.py` change plus a spec amendment (`kw5y2s`) and it is outside this child's fence, so it becomes its own plan or backlog item that this child depends on. (b) SITE THE STORE UNDER AN ALREADY-IGNORED PATH the template DOES cover, e.g. under `records/runs/`; cheapest and needs no installer change, but it puts durable cross-run state inside a per-run tree, which is a category error a later reader will trip over. (c) WRITE A NESTED `.gitignore` beside the store as a created deliverable, which the comms convention already does for the legacy layout (`engine.py` COMMS notes) and which respects the no-touch-root rule; small and local, at the cost of a third ignore convention. (d) PUT IT OUTSIDE THE REPO entirely, under the machine-wide `aw` home; strongest isolation, but it breaks the per-repo keying the digest assumes and loses the lane-visibility `checkout_control_root` provides. Recommendation: (a) as the correct fix with (c) as the pragmatic interim, since (c) is provable in-repo today and does not block on an installer change. A human decides, because (a) mutates every adopter's tree. Do NOT execute E-04 while this is open.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the child-table extraction for one real orchestrator showing the rows resolved, and state whether `ipd_set_plan.parse_child_table` was reused or, if not, exactly what its return shape could not supply. Paste an AST walk over `runner_shared`'s module-level `ImportFrom` nodes showing it still has exactly ONE first-party module-level import (`render_stream`), proving the parser reach is lazy.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the digest of one real orchestrator computed twice in SEPARATE PROCESSES, showing byte-identical output (determinism, not just repeatability within one run). Paste the docstring passage stating the deliberate divergence from `frozen_region_digest` (child table in; `Scope-Paths` and V-item text out).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste before/after digests for FOUR no-op mutations (tick a checkbox, fill Observed evidence, append a history line, edit a prose section) showing NO change, and for TWO real edits showing a change: an E-item action edit AND a CHILD-TABLE edit. Then paste the SAME child-table mutation run through `ipd_lifecycle.frozen_region_digest`, showing it does NOT move, which is the measurement that proves this new function earns its existence rather than duplicating the old one. A V-03 without the child-table pair is not evidence.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a write-then-read round trip including the recorded model; paste the resolved store path showing it derives from `checkout_control_root` (and that it is IDENTICAL when computed from the main tree and from a linked worktree, which is the `dh0uno` property); paste the behavior on a deliberately corrupted entry showing it reads as absent rather than raising; and paste `git check-ignore -v` for the store path run inside a FRESH repo carrying only installer output, not this one. State which OQ-02 option was implemented.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste a miss returning `unknown` (NOT pass), and the recorded fail-caching decision with its evidence: if a fail IS cached, paste the fixture where the remedy (moving the work into a new child) was actually applied and the digest MOVED, rather than an argument that it would. Include a mutation check: make a miss return pass, show a test FAILS, revert.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the staleness rule and its default bound; paste a stored verdict that fails the rule (a different model, or past the bound) being read as `unknown` rather than as its recorded value; and paste a fresh verdict being read as its recorded value, so the rule is shown to discriminate rather than to reject everything.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: pasted object-identity output per new symbol showing each resolves to the same object from both hosts and is defined in `runner_shared`, plus the AST-measured oc-to-agy import count before and after showing it did not increase from 47.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION IS BLOCKED ON OQ-02, and human approval alone does not clear it. OQ-02 carries `Blocking: yes`, so the pre-execution checkpoint refuses while it is open. The question is where the verdict store may live given that the framework does not ship the ignore rule this child assumed, and one of its options changes what every adopter receives on install, so it is not an executor's call.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set before every commit and RE-VERIFY after any failed or hook-interrupted commit. Paste ACTUAL runner output when reporting tests passed.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved 8tgg6g --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
