# IPD: Make the unclassified-tree drift fire for a records tree, and discover a tree with no policy at all

- Date: 2026-09-28
- Kind: child
- Concern: `attention.scan` appends `attention.unclassified-tree` ONLY when the scanned path starts with `.agents/`, so a file under a `.aw/records/` tree with no `TreePolicy` is dropped SILENTLY and the view still reports `valid: true`. Measured in this lane, the blind spot is actually TWO holes, not one: a tree present in `SCAN_ROOTS` but carrying no policy is silent (the prefix guard), and a tree present ON DISK but absent from `SCAN_ROOTS` is never even opened, so no per-file branch can ever see it. The second hole is the exact mechanism that let the releases gap (`m867ox`) report zero violations, and it survives the fix the item describes.
- Scope: Rekey the per-file unclassified drift off the `.agents/` prefix and onto a DERIVED exemption set (the non-tree `SCAN_ROOTS` file entries, plus the existing README/non-artifact filter), and add a separate shallow records-root TREE DISCOVERY drift that names a `.aw/records/<type>/` directory matching no inventoried `TreePolicy`, so a tree that is unreachable by the file walk is still reported. One new rule id for the tree-level finding; no change to `TREE_POLICY`, to any status map, to `SCAN_ROOTS`, or to what any existing rule means.
- Scope-Paths: agent_workflows/attention.py, agent_workflows/attention_contract.py, tests/test_attention_blind_spot.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: twvswo
- Blocks-Release: next
- Set: attnblind
- Order: 1
- Highest E allocated: 06
- Author: opencode
- Id: 1qt1u3

## Workflow history

- 2026-09-28 draft (opencode): created.
- 2026-09-28 to-review (opencode): authored from backlog `twvswo`. Reproduced the item's reported mechanism exactly, then measured that the item's stated blast radius is STALE (the naive fix flags two files in this repository, not "four root docs and three untracked trees") and that a SECOND, strictly larger hole exists which the item's own framing does not cover: a records tree absent from `SCAN_ROOTS` is never opened, so rekeying the per-file guard alone would still have reported the releases defect as `valid: true`. Scoped the plan to both holes and resolved the exemption decision the item names as "the work" from repository evidence.

## Goal

Make a records-tree blind spot LOUD instead of silent, so the `aw attention` view cannot report `valid: true` while an entire tracked-shaped tree is invisible to it. Spec `20260808-1945-01` Section 8.6 already contracts this ("A newly discovered tree that is neither is a violation ... preventing silent blind spots"), and the mechanism exists but is keyed to the `.agents/` layout while this repository's live layout is `.aw/records/`, so the contract's own violation never fires. Closing this requires the exemption decision the backlog item explicitly defers to its own work, and it requires covering the tree-DISCOVERY hole as well as the per-file one, because the per-file branch is unreachable for precisely the tree shape that caused the original defect.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the exemption set, derived rather than hardcoded

- [ ] E-01 Add to `agent_workflows/attention_contract.py` a DERIVED predicate naming which unclassified scanned paths are exempt from the per-file drift, so the decision the backlog item calls "the work" is recorded in the contract module beside `TREE_POLICY` rather than spelled as a condition inside the scanner. Shape: a module-level function `is_exempt_unclassified(rel_posix: str) -> bool` returning True for a REPOSITORY-ROOT DOCUMENT (a path with no `/` separator, which is exactly the structural form of the three non-tree `SCAN_ROOTS` entries) and for any path `is_nonartifact_name` already filters. Derive the root-doc case STRUCTURALLY from the absence of a path separator, not by importing or copying the `SCAN_ROOTS` literals: `artifact_core` imports nothing from this module today and the contract module is deliberately dependency-light, so a copied list would be a second encoding of one fact and is exactly the divergence `m867ox` was caused by. Document on the function that a root doc is a PROSE document and not a lifecycle artifact (it carries no `- Status:`, so the pure-and-total mapping Section 6 requires has no enum to be total over), which is the same rationale the shipped walkthroughs/roadmaps exclusions already carry.
  - Depends on: none
  - Expected outcome: `A.is_exempt_unclassified` returns True for `DECISIONS.md`, `README.md`, `ARCHITECTURE.md`, and `.aw/records/plans/README.md`, and False for `.aw/records/newtype/x.md` and `.agents/newtype/x.md`.
  - Execution state: pending

- [ ] E-02 Rekey the per-file unclassified branch in `attention.scan` off the `.agents/` prefix and onto `A.is_exempt_unclassified`, so a file under ANY uninventoried tree is flagged regardless of which path generation it lives in. Replace the three-part condition (`rel.startswith(".agents/")` plus the two README tests) with a single negated call to the E-01 predicate, keeping the emitted rule id `attention.unclassified-tree` and its detail text UNCHANGED, since that id is in the closed `RULE_IDS` catalog and is asserted by `tests/test_attention_contract.py` and `tests/test_attention.py`. Do NOT alter the `continue` that follows, the `if not pol.tracked: continue` filter below it, or any other branch: this E-item changes WHICH paths reach the existing drift, never what the drift says or what happens to a classified file.
  - Depends on: E-01
  - Expected outcome: a `.aw/records/newtype/x.md` under a scanned root yields one `attention.unclassified-tree` drift where it previously yielded zero, while the `.agents/newtype/x.md` control keeps yielding exactly one, and `aw attention --check` on THIS repository still exits 0.
  - Execution state: pending

### Task group 2: the tree-discovery hole the per-file guard cannot reach

- [ ] E-03 Add a new rule id `attention.uninventoried-tree` to the closed `RULE_IDS` catalog in `attention_contract.py`, distinct from `attention.unclassified-tree`. It must be a SEPARATE id rather than a reuse: the existing id is a per-FILE finding whose location is a file path, while this one is a per-DIRECTORY finding whose location is a tree root, and collapsing them would make one id mean two things and would make a `--agent` consumer unable to tell "one stray file" from "an entire tree nobody inventoried". Place it adjacent to `attention.unclassified-tree` with a comment stating that relationship. Note `RuleCatalogTests.test_catalog_closed_and_named` asserts every id starts with `attention.` and that the set has at least 12 members, so an addition is compatible by construction.
  - Depends on: none
  - Expected outcome: `attention.uninventoried-tree` is in `A.RULE_IDS`, `tests/test_attention_contract.py::RuleCatalogTests` still passes unchanged, and the two ids are distinct strings.
  - Execution state: pending

- [ ] E-04 Add tree DISCOVERY to `attention.scan`: after the per-file loop, perform ONE shallow listing of the records root (`.aw/records`, and the legacy `.agents` root when the modern one is absent, mirroring the fallback `artifact_refs` already uses) and append an `attention.uninventoried-tree` drift for each immediate SUBDIRECTORY that `_classify_tree` maps to no policy. This is what closes the hole the item's motivating case actually exercised: a tree absent from `SCAN_ROOTS` is never opened by `iter_scan_files`, so no per-file branch (including E-02's) can ever see it. Constraints, each load-bearing: the listing MUST be SHALLOW (`iterdir`, never `rglob`), because the whole point is to see a tree whose files are not walked and a deep walk would reintroduce the cost the shipped reviews exclusion deliberately avoids; it MUST respect `core.is_ignored_path` so `.aw/records/runs` (already in `DEFAULT_IGNORED_DIR_NAMES`) is not reported; it MUST skip a `type_filters`-narrowed scan, since a filtered scan is a deliberately partial view and reporting whole-tree drift from one would make `aw next --type plans` fail on an unrelated tree; and it MUST remain READ-ONLY, creating no directory and stamping nothing (spec G3/Section 8.1, and `tests/test_attention.py` already asserts `scan` does not stamp `.aw/`).
  - Depends on: E-03
  - Expected outcome: a `.aw/records/newtype/` directory present on disk and ABSENT from `SCAN_ROOTS` yields one `attention.uninventoried-tree` drift naming `.aw/records/newtype`, where it previously yielded zero drift and zero items; `aw attention --check` on THIS repository still exits 0 because all eleven live records subdirectories classify.
  - Execution state: pending

### Task group 3: pin both holes, the exemption decision, and the non-regressions

- [ ] E-05 Add `tests/test_attention_blind_spot.py` pinning the TWO holes as distinct properties, each with the pre-fix counterfactual encoded so the record states what was silent. Hole 1 (per-file): synthesize `.aw/records/newtype/x.md` in a temp repo WITH that root forced into the scanned set, assert exactly one `attention.unclassified-tree` drift naming it, and assert the `.agents/newtype/x.md` control still produces exactly one, proving the rekey generalized rather than moved the guard. Hole 2 (discovery): synthesize the same directory WITHOUT any scan root for it, assert one `attention.uninventoried-tree` drift naming the DIRECTORY, and assert `render_json(...)["valid"]` is False, which is the precise claim the backlog item makes ("a records-tree blind spot reports valid: true"). Force the root set through `core.iter_scan_files` rather than by patching `core.SCAN_ROOTS`, because that name is bound as a DEFAULT ARGUMENT at def time and patching the module attribute does NOT change scan behavior (measured; see F-06) - a test written the naive way would pass vacuously against pre-fix code.
  - Depends on: E-04
  - Expected outcome: a new module whose hole-1 and hole-2 cases each FAIL against pre-fix code (zero drift observed, `valid` true) and pass after, with the falsification pasted in V-05.
  - Execution state: pending

- [ ] E-06 In the same module, pin the EXEMPTION decision and the non-regressions, since an over-firing check is the failure mode that made this defect worth deferring in the first place. Exemptions: assert `attention.scan` on THIS repository (or a fixture carrying the three root docs plus a tree README) reports NO unclassified drift for `DECISIONS.md`, `README.md`, `ARCHITECTURE.md`, or a `<tree>/README.md`, and that `aw attention --check` exits 0 here. Non-regressions: (a) each of the five EXCLUDED trees (`walkthroughs`, `roadmaps`, `docs-prompts`, `comms`, `reviews`) still yields neither an item nor drift, proving an excluded tree is distinguished from an uninventoried one; (b) `.aw/records/runs` is NOT reported even when present, proving the ignore filter is honored; (c) a `type_filters`-narrowed `scan` reports no tree-discovery drift; (d) `scan` on a fresh empty directory still creates no `.aw/` and reports nothing, preserving the shipped write-on-read invariant. Do NOT assert any total item or drift COUNT for this repository: every count in the sibling `m867ox` plan's history went stale, and that plan's own required-tests section forbids it.
  - Depends on: E-05
  - Expected outcome: all exemption and non-regression assertions pass, and `aw attention --check --agent` on this repository still reports `"outcome":"clean"` with exit 0.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE CONTRACT ALREADY REQUIRES THIS AND NAMES THE RULE, so no spec amendment is needed. Spec `20260808-1945-01` Section 8.6: "Maintain an explicit inventory: every known tree is `tracked` (owner + contract + mapping) or `excluded` (rationale). A newly discovered tree that is neither is a violation (e.g. `attention.unclassified-tree`), preventing silent blind spots". F3 lists "an unclassified new tree" among the conditions `--check` MUST fail closed on. The code simply keys the wrong prefix, so this plan brings code into compliance with text that already says the right thing - the identical justification `m867ox` recorded for its own no-amendment decision.
- THE SIBLING PLAN DEFERRED EXACTLY THIS AND NAMED ITS OWN SUCCESSOR'S JOB. `m867ox`'s "Deferred / out of scope" F-4 row: "MAKING THE UNCLASSIFIED-FILE DRIFT FIRE OUTSIDE `.agents/` ... would immediately flag the four root docs and three untracked `.aw/records/` trees that are in `SCAN_ROOTS` by design, so it needs its own decision about what to exempt." Its "Under-scope" row repeats it. This plan is that decision. Its stated blast radius is now STALE in two ways, both measured (F-04): `TODO.md` was removed from `SCAN_ROOTS` by `diof9n`, and the three "untracked trees" it names all classify to EXCLUDED policies, so they are filtered by `pol.tracked` and never reach the unclassified branch at all.
- THE EXISTING GUARD PROVES DECLARATION, NOT REACHABILITY, AND SAYS SO. `TrackedTreeScanCoverageTests` (added by `m867ox` E-04) asserts every TRACKED tree has SOME scan root, and its docstring states the limit explicitly: "It does NOT prove REACHABILITY ... a reader must not treat this passing as evidence that a tree is surfaced." `TrackedTreeReachabilityTests` (added later by `0i4fkt`) closes reachability for the six trees that ARE tracked. Neither can see a tree with NO policy, which is the residue this plan addresses and which the backlog item states as its central point.
- THE RULE-ID CATALOG IS CLOSED AND ITS TEST ADMITS ADDITIONS. `RULE_IDS` is documented as "The CLOSED catalog of stable `--check`/`--agent` rule identifiers, one per F3/8.8 violation class", and `RuleCatalogTests.test_catalog_closed_and_named` asserts the `attention.` prefix and `len >= 12`. So adding one id is compatible, and adding it is the convention (one id per violation CLASS) rather than overloading an existing one.
- A DRIFT IS THE HOUSE SHAPE FOR THIS AND NEEDS NO NEW PLUMBING. `core.Drift(location, rule, detail)` is emitted by `attention.scan` today for thirteen conditions, rendered by `render_agent_drift`, and drives `valid` in `render_json` plus the `--check` exit code. A tree-level finding fits it unchanged by putting a DIRECTORY in `location`, which is already how `attention.unclassified-tree` behaves apart from granularity.
- THE RECORDS-ROOT FALLBACK IS ESTABLISHED IN THIS CODEBASE. `artifact_refs` resolves `repo_root/".aw"/"records"` and falls back to `repo_root/".agents"` when the modern root is absent. E-04 mirrors that rather than inventing a third spelling, and `layout.LOGICAL_ROOTS["records"]` is the single declaration of `.aw/records` if a constant is preferred to a literal.
- THE IGNORE FILTER ALREADY COVERS THE ONE DANGEROUS DIRECTORY. `DEFAULT_IGNORED_DIR_NAMES` contains `.aw/records/runs`, and `core.is_ignored_path` returns True for it (measured), so honoring that filter in E-04 keeps run state out of the report without a bespoke exclusion. `.aw/state` and `.aw/workflow-artifacts` are likewise already ignored.
- `SCAN_ROOTS` IS DELIBERATELY NOT A LIST OF LIFECYCLE TREES, which is why E-01 derives its exemption structurally instead of reading that tuple. `TrackedTreeScanCoverageTests`'s docstring records the reason: it is "the shared tracked-TEXT enumeration for the citation/dangling tools, not a list of lifecycle trees", legitimately containing root docs, a `.agents/docs` ancestor, and excluded trees, and a symmetric assertion over it "would fail immediately and WRONGLY".
- THE SCANNER IS READ-ONLY AND A TEST ALREADY ENFORCES IT. `tests/test_attention.py` asserts `scan` on a fresh directory does not create `.aw/`, and a comment in `attention.scan` records that an earlier ledger's eager `mkdir` made this read path "stamp `.aw/state/` into every scanned repo - write-on-read". E-04 therefore lists then classifies, and creates nothing.

## Findings

All findings were driven in this lane at HEAD `4f3f1213` against the live tree and temporary fixture repositories, not read off the source.

| # | Finding | Evidence |
|---|---|---|
| F-01 | THE FILED DEFECT REPRODUCES EXACTLY AS WRITTEN. A `.aw/records/newtype/x.md` present on disk AND forced into the scanned root set yields ZERO items and ZERO drift; the identical file under `.agents/newtype/` yields exactly one `attention.unclassified-tree`. | Driven in two temp repos: `.aw/records/newtype` case `items: []`, `drift: []`. `.agents/newtype` control: `drift: [('.agents/newtype/x.md', 'attention.unclassified-tree')]`. Same body, same scan, only the path generation differs, which isolates the prefix guard as the cause. |
| F-02 | THERE IS A SECOND, STRICTLY LARGER HOLE THAT THE ITEM'S FIX WOULD NOT CLOSE. A records tree present on disk but ABSENT from `SCAN_ROOTS` is never opened, so no per-file branch can see it. Rekeying the per-file guard alone leaves this silent. | Driven: with `.aw/records/newtype/x.md` on disk and no scan root for it, `core.iter_scan_files(root)` returned `[]` and `ATT.scan(root)` returned `items: []`, `drift: []`. The file is not classified-and-dropped; it is never READ. This is why E-04 exists as separate work from E-02. |
| F-03 | HOLE 2 IS PRECISELY THE MECHANISM OF THE MOTIVATING DEFECT, so the plan's second half is not speculative. Reconstructing the pre-`m867ox` root set reproduces the releases gap end to end: the release record is invisible and the view is clean. | Driven with `iter_scan_files` forced to the releases-less root tuple: `items: []`, `drift: []` for a valid `- Status: planned` release record. With the shipped roots the same record appears as `('releases','planned')`. So the original defect was hole 2, not hole 1. |
| F-04 | THE ITEM'S (AND `m867ox`'s) STATED BLAST RADIUS IS STALE, which materially shrinks this plan's risk and is why the exemption decision is now tractable. The naive fix flags TWO files in this repository, not "four root docs and three untracked trees". | Driven over the live tree: dropping the `.agents/` guard and keeping only the README filter flags exactly `ARCHITECTURE.md` and `DECISIONS.md`. `README.md` is already filtered by name. `TODO.md` is gone from `SCAN_ROOTS` (removed by `diof9n`). The three "untracked trees" (`walkthroughs`, `roadmaps`, `prompt-library`) all CLASSIFY, to excluded policies, so they never reach the unclassified branch. |
| F-05 | EVERY LIVE RECORDS SUBDIRECTORY CLASSIFIES TODAY, so both new checks are GREEN on this repository at authoring time and this plan adds no finding of its own. | Driven over all eleven subdirectories of `.aw/records`: each maps to a policy (6 tracked, 5 excluded). `python3 -m agent_workflows attention --check --agent` exits 0 with `"outcome":"clean","findings":0`. Two (`comms`, `reviews`) classify to EXCLUDED policies while having NO `SCAN_ROOTS` entry, which is consistent and is exactly the state E-06 pins as a non-regression. |
| F-06 | A TEST WRITTEN THE NAIVE WAY WOULD PASS VACUOUSLY, which is why E-05 mandates the forcing mechanism. `SCAN_ROOTS` is bound as a DEFAULT ARGUMENT of `iter_scan_files` at def time, so `mock.patch.object(core, "SCAN_ROOTS", ...)` does not change scan behavior. | Driven: `core.iter_scan_files.__defaults__[0] is core.SCAN_ROOTS` is True. Patching the module attribute and calling `ATT.scan` still walked the SHIPPED roots (the releases record was found); only patching `iter_scan_files` itself, or passing `scan_roots=` explicitly, changed the walked set. |
| F-07 | THE DISCOVERY LISTING IS EFFECTIVELY FREE, so E-04 needs no caching, no opt-out flag, and no deferral on cost grounds. | Measured on this repository: a shallow `iterdir` of `.aw/records` averages 0.123 ms over 50 iterations (11 directories), against 120.4 ms for the full `iter_scan_files` walk (1792 files) that every invocation already performs. That is about 0.1 percent of existing scan cost. |
| F-08 | THE IGNORE FILTER ALREADY EXCLUDES RUN STATE, so honoring it is sufficient and no bespoke exclusion list is needed. | Driven: `".aw/records/runs" in core.get_ignored_dirs(root)` is True, and `core.is_ignored_path` returns True for `.aw/records/runs` and `.aw/state`, False for `.aw/records/comms` and `.aw/records/reviews`. |
| F-09 | NO TEST ANYWHERE EXERCISES THE UNCLASSIFIED DRIFT OUTSIDE `.agents/`, so neither hole is pinned and the prefix guard is currently free to regress in either direction. | `grep -rn "unclassified" tests/` matches three lines: `test_attention_contract.py:262` (catalog membership only), `test_attention_contract.py:384` (a DOCSTRING that describes this very defect in prose while asserting nothing about it), and `test_attention.py:108`, whose fixture writes `.agents/docs/weird/z.md` - under `.agents/`, so it exercises only the passing side. |
| F-10 | THE BASELINE IN THIS LANE IS CLEAN, so any failure after the change is attributable to the change. | `python3 -m pytest` bare at HEAD `4f3f1213`: `3069 passed, 2 skipped, 3 warnings in 46.98s` (202 deselected as `slow`/`livecorpus` by the configured `addopts`). Targeted: `python3 -m pytest tests/test_attention.py tests/test_attention_contract.py` -> `66 passed`. |
| F-11 | THE ROOT-DOC EXEMPTION IS DERIVABLE STRUCTURALLY, so E-01 need not copy a literal list that could drift from `SCAN_ROOTS`. | Driven: the non-tree `SCAN_ROOTS` entries are exactly `('DECISIONS.md', 'README.md', 'ARCHITECTURE.md')`, and `all("/" not in r)` over them is True, while every tree entry contains a separator. `Path(r).is_file()` also distinguishes them, but the separator test is pure and needs no filesystem access, which matters on a pure read path. |

## Proposed changes (ordered, validatable)

1. E-01: add `is_exempt_unclassified` to `attention_contract.py`, deriving the root-doc case structurally and reusing `is_nonartifact_name`, recording the exemption decision beside `TREE_POLICY`.
2. E-02: rekey `attention.scan`'s per-file unclassified branch onto that predicate, leaving the `attention.unclassified-tree` id and detail unchanged (closes hole 1, F-01).
3. E-03: add the distinct `attention.uninventoried-tree` id to the closed `RULE_IDS` catalog for the tree-level finding.
4. E-04: add a shallow, ignore-respecting, filter-skipping, read-only records-root discovery pass to `attention.scan` (closes hole 2, F-02/F-03).
5. E-05: pin both holes in a new test module with the pre-fix counterfactual, forcing the root set through `iter_scan_files` per F-06.
6. E-06: pin the exemption decision and four non-regressions (excluded trees, ignored run state, filtered scans, write-on-read).

## Deferred / out of scope (with reason)

- ADDING OR CHANGING ANY `TreePolicy`, including tracking `reviews` or `comms`. Both classify correctly today as EXCLUDED with rationales (F-05), so neither is a blind spot. `m867ox` settled `reviews` as OUT with a measured reason (zero of 231 review records carry a `- Status:` field, so there is no native enum for the pure-and-total mapping Section 6 requires), and tracking either would add a status vocabulary to the cross-tree contract, which is a spec amendment plus maintainer approval. This plan reports an UNINVENTORIED tree; it does not decide any tree's disposition.
  - Carrier-Declined: Nothing is owed. Every tree that exists in this repository is already inventoried (F-05 measured all eleven), so there is no outstanding classification work to carry, and the whole point of E-04 is that the NEXT tree announces itself instead of needing a standing reminder. Filing a carrier would schedule a contract change nothing measured here requires.
- ADDING A `SCAN_ROOTS` ENTRY FOR ANY TREE, including `comms` and `reviews`. Deliberately refused: `attention.scan` filters an excluded tree AFTER reading it (`if not pol.tracked: continue`), so a root for `reviews` would cost hundreds of file reads per invocation for records immediately discarded, which is precisely the cost `m867ox` recorded as its reason for adding none. E-04's shallow listing sees such a tree WITHOUT walking it, which is why discovery is the right mechanism rather than root expansion.
  - Carrier-Declined: The obligation is discharged rather than postponed, and by design: E-04 makes an unwalked tree visible, so the reason to add a root for visibility no longer exists. Adding one would be a pure cost regression with no finding behind it.
- MAKING THE DISCOVERY PASS RECURSIVE, or extending it to `.aw/system`, `.aw/config`, `.aw/state`, or `.aw/worktrees`. Only the RECORDS root holds lifecycle artifact trees (`layout.LOGICAL_ROOTS`), the other three are machine state or shipped assets with no artifact contract, and `.aw/worktrees` is specifically forbidden as a scan target by spec F3a ("`SCAN_ROOTS` is NOT extended to `.aw/worktrees` or `.aw/records/runs`, and this clause must not be read as licensing that"). A recursive walk would also re-import the cost this design avoids (F-07).
  - Carrier-Declined: Nothing is owed, because this is a deliberate boundary rather than unfinished work: the spec forbids one of the roots outright and the others hold no artifact trees to discover. Recording a carrier would schedule work the controlling spec prohibits.
- RETIRING `TODO.md`, or repolicying the remaining root docs from `SCAN_ROOTS`. Already done and out of scope respectively: `diof9n` removed the `TODO.md` entry (F-04), and the three surviving root docs are legitimately scanned prose for the citation and dangling-reference tools, which is a different consumer from the attention view. E-01 EXEMPTS them from the attention finding without touching the shared list that other tools depend on.
  - Carrier-Evidence: .aw/records/plans/executed/20260908-durablecapture-03-diof9n-close-the-todo-md-trap-so-work-written-there-cannot-vanish-a.ipd.md
- MAKING `aw check` GROW A PARALLEL RULE for either finding. `aw attention --check` is the contracted surface for this class (spec F3 lists the unclassified-tree condition as one of its own fail-closed conditions, and Section 8.6 requires that "Local and CI observe the same validity result"), and CI already runs it. A second implementation in `check_engine` would be exactly the two-lists-encoding-one-fact divergence this plan exists to stop.
  - Carrier-Declined: Nothing is owed, and a carrier would schedule the DEFECT rather than a fix. The whole diagnosis of the motivating `m867ox` gap is that two lists encoded one fact and diverged, so a second implementation of this finding in `check_engine` is the failure mode, not deferred work. The single contracted surface already exists and CI already runs it, so there is no coverage residue for anyone to pick up.
- PER-REQUIREMENT SPEC TRACKING and any change to `render_json`'s `schema_version`. No key is added to the payload: both findings flow through the existing `violations` list and the existing `valid` flag, so the schema is unchanged and no bump is owed.
  - Carrier-Declined: Nothing is owed, because no schema change occurs: this plan adds violation ROWS to an existing list, which the shipped `schema_version` already admits, so there is no migration or bump to hand off. Per-requirement spec tracking is a separate standing concern already carried elsewhere (`m867ox` records it against backlog `f1sw71`) and is not created or worsened by this plan.

## Scope check

- Over-scope: none. One new predicate and one new rule id in `attention_contract.py`, one rekeyed condition and one new post-loop pass in `attention.scan`, and one new test module. `TREE_POLICY`, every status map, `CLASS_MAPS`, `TRACKED_TREES`, `is_nonartifact_name`, `_classify_tree`, `SCAN_ROOTS`, `iter_scan_files`, `render_json`'s schema, the `attention.unclassified-tree` detail text, and every other drift branch stay untouched. `attention_contract.py` is in scope ONLY for E-01 and E-03; do not edit an existing policy or map to make output tidier.
- Under-scope: stated rather than left as `none`. After this plan, a tree under a records root is discovered but its CONTENTS are still not read unless it has a `SCAN_ROOTS` entry, so the finding says "nobody inventoried this tree" and never "here is what is in it"; that is the intended granularity, since reading an uninventoried tree would require a policy that by definition does not exist yet. A tree outside the records root remains undiscovered (deferred above, and forbidden for `.aw/worktrees` by spec F3a). A `type_filters`-narrowed scan deliberately reports no tree-level drift, so `aw next --type plans` cannot surface this class; the unfiltered `aw attention --check` that CI runs is the authority. And a tracked tree that is declared, scan-rooted, and reachable but whose records are individually malformed is unchanged territory, already owned by the existing twelve per-file rules.

## Required tests / validation

- `python3 -m pytest tests/test_attention_blind_spot.py` for the new module, run BARE (the configured `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; do not add `-n0` or a second `-q`).
- `python3 -m pytest tests/test_attention.py tests/test_attention_contract.py tests/test_prompts_attention.py tests/test_check_engine.py tests/test_doctor.py` as the targeted regression set: the first two own the scanner and the contract module being edited (and `test_attention.py:108` owns the existing `.agents/` unclassified assertion the rekey must preserve), and `check_engine.resolve_evidence_artifact` calls `attention._classify_tree` on a path that E-02 does not change but whose neighbours it touches.
- `python3 -m pytest` (full fast suite) bare, compared against the F-10 baseline of `3069 passed, 2 skipped` by FAILING NODE IDS and not by totals. The baseline is clean, so the only acceptable end state is zero failures.
- `python3 -m agent_workflows attention --check --agent` must still exit 0 with `"outcome":"clean"` on this repository, and `aw check --agent` must report no NEW finding class, proving the two new checks are green on the live tree (F-05) and that this plan introduces no finding of its own.
- PRE-FIX FALSIFICATION IS REQUIRED, not optional. V-05 must show the new module FAILING against pre-implementation code for BOTH holes, and the hole-2 half must show `render_json(...)["valid"]` was True pre-fix, since "a records-tree blind spot reports valid: true" is the exact claim backlog `twvswo` makes and a test that passes before the fix proves nothing.

## Spec / documentation sync

N/A with reason, and this is resolved by reading rather than assumed. The controlling spec is `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` (`- Status: implemented`), which owns the tree inventory, the class mapping, and the `--check` failure set. No amendment is required, on two checks:

1. SECTION 8.6 STATES THE RULE, NOT A ROSTER, and already mandates this behavior: "every known tree is `tracked` ... or `excluded` (rationale). A newly discovered tree that is neither is a violation (e.g. `attention.unclassified-tree`), preventing silent blind spots". F3 independently lists "an unclassified new tree" among the conditions `--check` MUST fail closed on. Making the violation actually fire therefore brings the CODE into compliance with text that is already correct, which is the identical justification `m867ox` recorded and had accepted for its own no-amendment decision.
2. THE NEW RULE ID NEEDS NO SPEC CELL. Section 8.6's "e.g." is explicitly non-exhaustive, and the spec nowhere enumerates `RULE_IDS` as a closed list transcribed into code. Contrast spec `25kzda` Section 4.2, whose finding-code table IS transcribed verbatim into `run_evidence.RUN_FINDING_CODES` under a byte-equality test; no such coupling exists for the attention catalog, so adding an id is a code change only. Do NOT edit that `25kzda` table under any circumstances.

The spec file is therefore deliberately ABSENT from `- Scope-Paths:`, and must not be added: declaring a spec edit puts it in front of the runners' spec-edit announcement for no contract change. No user-facing document changes either, since `aw attention` gains no flag and no output key; the only surface change is two additional violation rows that can appear in an already-documented violation list.

## Open questions

### OQ-01: Should the tree-level finding reuse `attention.unclassified-tree` or get its own rule id?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE: its own id, `attention.uninventoried-tree`. `RULE_IDS` is documented as "one per F3/8.8 violation class" and these are two classes with different LOCATION semantics: the existing finding's location is a FILE under an uninventoried tree, the new one's is the tree DIRECTORY itself. Reusing the id would emit two different meanings under one identifier in the `location<TAB>rule<TAB>detail` agent record, so a consumer could not distinguish one stray file from an entire invisible tree, and would also break the one-to-one property the catalog's own comment asserts. `RuleCatalogTests` admits additions (it asserts the `attention.` prefix and `len >= 12`), so the cost is zero.

### OQ-02: Should the root-doc exemption read `SCAN_ROOTS`, or derive the root-doc shape structurally?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM MEASUREMENT AND FROM THE DEFECT'S OWN HISTORY: derive it structurally. Reading `SCAN_ROOTS` from `attention_contract.py` would add a dependency to a deliberately dependency-light module and would create a THIRD list encoding the tree inventory, and "two lists encoded one fact and they diverged with no test in between" is the verbatim diagnosis `TrackedTreeScanCoverageTests` records for the original releases defect. The structural test is also exact rather than approximate: measured, the non-tree `SCAN_ROOTS` entries are precisely the three entries containing no path separator (F-11), and it needs no filesystem access on a pure read path. Non-blocking because the observable behavior is identical either way; only the coupling differs.

### OQ-03: Should the discovery pass run on a `type_filters`-narrowed scan?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM THE CALL SITE'S CONTRACT: no. `attention.scan` narrows `scan_roots` when `type_filters` names only known trees, which is how `aw next --type plans` produces a deliberately PARTIAL view. A whole-tree violation is a property of the repository, not of the filtered slice, so emitting it from a narrowed scan would make `aw next --type plans` fail on a tree the caller explicitly excluded. Section 8.6's "local and CI observe the same validity result" is preserved because the authority for validity is the UNFILTERED `aw attention --check` that CI runs, which is exactly where the pass does run.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste an actual Python session calling `attention_contract.is_exempt_unclassified` on six inputs and showing each returned value: `DECISIONS.md` -> True, `README.md` -> True, `ARCHITECTURE.md` -> True, `.aw/records/plans/README.md` -> True, `.aw/records/newtype/x.md` -> False, `.agents/newtype/x.md` -> False. Also paste the function's source, showing it derives the root-doc case from the absence of a path separator and delegates the non-artifact case to `is_nonartifact_name`, proving no `SCAN_ROOTS` literal was copied (OQ-02) and no name filter was reimplemented.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste two actual scans against temp fixtures showing the rekey generalized rather than moved: a `.aw/records/newtype/x.md` with its root forced into the scanned set now yielding exactly one `attention.unclassified-tree` naming that file (it yielded `drift: []` pre-fix, per F-01), and the `.agents/newtype/x.md` control still yielding exactly one. Paste the diff of the edited branch in `attention.scan`, showing the rule id and detail string are byte-identical to before. Then paste `python3 -m agent_workflows attention --check --agent` on THIS repository showing exit 0 and `"outcome":"clean"`, proving the rekey flags nothing live (F-04, F-05).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a Python session showing `"attention.uninventoried-tree" in A.RULE_IDS` is True, that it differs from `"attention.unclassified-tree"`, and the resulting `len(A.RULE_IDS)`. Paste the actual output of `python3 -m pytest tests/test_attention_contract.py -k RuleCatalog` including its `N passed` line, proving the closed-catalog test still passes with the addition.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste an actual scan of a temp fixture containing `.aw/records/newtype/x.md` with NO scan root for it, showing exactly one `attention.uninventoried-tree` drift whose location is the DIRECTORY `.aw/records/newtype`, against the pre-fix `items: []`, `drift: []` of F-02. Paste four further runs proving each named constraint: (a) the same fixture with `.aw/records/runs/` present, showing runs is NOT reported; (b) a `scan(root, type_filters={"plans"})` call showing no tree-level drift; (c) `scan` on a fresh empty directory showing no drift and that `.aw/` was NOT created; (d) a fixture containing a legacy `.agents/` root and no `.aw/records`, showing the fallback discovers there. Also paste the source of the pass showing `iterdir` and not `rglob`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the full `python3 -m pytest tests/test_attention_blind_spot.py` output including the `N passed` summary line. Then paste the PRE-FIX run of the same module against stashed implementation code (`git stash push -- agent_workflows/attention.py agent_workflows/attention_contract.py`), showing BOTH hole cases FAILING with assertion text visible, and specifically showing that the hole-2 case observed `valid` as True and zero drift before the fix, which is the exact claim backlog `twvswo` makes. A module that passes before the fix does not validate E-05. Also state explicitly that the test forces the scanned root set through `iter_scan_files` rather than patching `core.SCAN_ROOTS`, and paste the line that does so, since F-06 measured that the naive form passes vacuously.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the exemption and non-regression test names with their outcomes from the pytest output. Paste `python3 -m pytest tests/test_attention.py tests/test_attention_contract.py tests/test_prompts_attention.py tests/test_check_engine.py tests/test_doctor.py` with its `N passed` line, then the full bare `python3 -m pytest` with its summary line, compared to the F-10 baseline `3069 passed, 2 skipped` by failing NODE IDS and not by totals. Paste `python3 -m agent_workflows attention --check --agent` (exit 0, `"outcome":"clean"`) and `aw check --agent` on this repository, reconciling any finding-count delta. Confirm in writing that no test asserts a total item or drift COUNT for this repository.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval recorded as `- Status: approved` with an `- Approval:` attestation. This plan is authored `to-review` and deliberately carries NO `- Readiness:` field, because that field is an OUTPUT of `/plan-review` and writing one here would forge a review that has not happened.

Execution contract: commit only the paths named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`; never `git add -A`; never push. Run the suite bare as `python3 -m pytest` and paste actual output. Do not mark any `V-*` item complete without the concrete evidence it names, and specifically do not mark V-05 complete without the PRE-FIX failing run for BOTH holes: the hole-2 falsification is the load-bearing half of this plan's case, because hole 2 (F-02/F-03) is the mechanism that produced the motivating defect and is the half the backlog item's own framing does not cover.

Post-gate lifecycle: after every `E-*` is performed and every `V-*` is verified with pasted evidence, run `aw ipd lint --phase pre-transition` and move this plan to `.aw/records/plans/executed/` through the tooled transition. This plan carries `- From-Backlog: twvswo` and inherits that item's `- Blocks-Release: next`, so executing it is what legitimately discharges the item's release gate; the backlog item itself moves to `graduated`, never to `done`, at authoring time.
