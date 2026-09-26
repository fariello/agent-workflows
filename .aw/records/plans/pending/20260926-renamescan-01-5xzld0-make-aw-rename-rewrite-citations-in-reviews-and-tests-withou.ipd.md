# IPD: Make aw rename rewrite citations in reviews and tests without corrupting short handles, transcripts or shared legacy prefixes

- Date: 2026-09-26
- Kind: child
- Concern: `aw rename`/`aw group` rewrite inbound citations through ONE matcher (`artifact_refs.plan_reference_rewrites`) that has four measured defects: it never scans `.aw/records/reviews/` or `tests/`, so renamed artifacts leave dangling citations there; it expands a short legacy handle (`YYYYMMDD-HHMM-NN`) into the FULL new stem; it rewrites quoted command transcripts inside fenced code, falsifying recorded output; and it rewrites a legacy prefix that two artifacts of different types share, cross-contaminating citations of the other artifact.
- Scope: IN: a separate reference-scan root list (NOT `SCAN_ROOTS`) that adds `.aw/records/reviews` and `tests`, with `.py` scanned only under it; short-handle to short-handle mapping; fenced-code masking in plan and apply; skip-and-warn for a legacy prefix that is not unique across `.aw/records`; an interactive confirmation for `tests/` edits (default yes, non-interactive rewrites); outcome tests. OUT: widening `artifact_core.SCAN_ROOTS` or `_TEXT_SUFFIXES` (read by `aw attention` and the dangling detectors); masking indented code or quoted prose outside fences; repairing citations already broken by past renames.
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/artifact_refs.py, agent_workflows/artifact_rename.py, agent_workflows/plans_refs.py, agent_workflows/research_refs.py, tests/test_artifact_refs_rewrite.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: 7oql4z
- Blocks-Release: next
- Set: renamescan
- Order: 1
- Highest E allocated: 09
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 5xzld0

## Workflow history
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 7oql4z: aw rename gains reviews/tests reference roots, short-handle mapping, fenced-code masking and a shared-legacy-prefix skip.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make a rename rewrite every real citation of the renamed artifact, including those in review records and test files, while leaving untouched the text that is not a citation of it: quoted transcripts in fenced code, pinned permalinks, and a legacy prefix that also names a different artifact. A short handle must stay a short handle.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: failing outcome tests first

- [ ] E-01 Add `tests/test_artifact_refs_rewrite.py` with a tmp git repo fixture (the `_RepoTestCase` shape in `tests/test_spec_id6_filenames.py`: `git init`, `.aw/records/specs/`, `.aw/records/plans/pending/`, `.aw/config/project.json`) and SIX outcome tests, each driving `cli.main(["rename", "specs", <legacy-name>, "--to-id6", "--apply", "--no-commit", "--dir", tmp])` and asserting only file contents after the run: (a) a `.aw/records/reviews/<x>.review.md` citing the spec's full filename now cites the new filename; (b) a `tests/test_x.py` citing it is rewritten when stdin is NOT a TTY (default under pytest); (c) a file containing the short handle `20260701-1200-01` (backticked, no slug) now contains `20260701-<id6>-01` and NOT the full new stem; (d) a plan whose fenced block (```` ``` ````) contains `--- would rename .../20260701-1200-01-legacy.spec.md -> ... ---` is byte-identical after the rename, while a citation of the same name OUTSIDE the fence in that same file IS rewritten; (e) a second artifact of another type sharing the prefix (`.aw/records/prompts/executed/20260701-1200-01-other.prompt.md`) exists, and a plan citing `20260701-1200-01-other` and the bare `20260701-1200-01` is byte-identical after renaming the spec, and the command output names the skipped prefix; (f) a pinned permalink `https://example.invalid/o/r/blob/0123456789abcdef/.aw/records/specs/20260701-1200-01-legacy.spec.md` stays byte-identical. Tests assert OUTCOMES only: no source-text, fingerprint, docstring or call-count assertions.
  - Depends on: none
  - Expected outcome: at HEAD (a), (b), (c), (d) and (e) FAIL and (f) passes (permalink masking already exists); this pins the four defects before any code changes.
  - Execution state: pending

### Task group 2: the fixes

- [ ] E-02 Add a reference-scan root list and use it only for citation rewriting. In `artifact_core`, beside `SCAN_ROOTS`, define `REFERENCE_SCAN_ROOTS = SCAN_ROOTS + (".aw/records/reviews", "tests")` and `_REFERENCE_TEXT_SUFFIXES = _TEXT_SUFFIXES + (".py",)`, and let `iter_scan_files` take an optional `suffixes` argument (default `_TEXT_SUFFIXES`, so every existing caller is unchanged). Change the DEFAULT `scan_roots` of `artifact_refs.plan_reference_rewrites` to `REFERENCE_SCAN_ROOTS` with the widened suffixes, and use the same list in `artifact_rename.find_unrewritable_path_citations` (its `_core.iter_scan_files(repo_root)` call). Do NOT change `SCAN_ROOTS`, `_TEXT_SUFFIXES`, `find_dangling_citations`, `dead_filename_citations`, `research_archive`, `research_index` or `attention`: `attention_contract`'s `reviews` TreePolicy comment records that a reviews scan root was refused because `attention.scan` would read ~340 review files per call and discard them, and `tests/test_attention_contract.py` asserts no `SCAN_ROOTS` entry covers `reviews`. Keep the `_SKIP_NAMES` generated-manifest skip. Keep `tests/fixtures/**/*.json` OUT (json is not added to the suffixes): `tests/fixtures/derive_plan_status_baseline.json` keys executed plan paths and is a frozen baseline.
  - Depends on: E-01
  - Expected outcome: E-01 (a) passes; the `aw attention` scan set is unchanged.
  - Execution state: pending

- [ ] E-03 Map a short legacy handle to the NEW SHORT handle. In `plan_reference_rewrites`, replace `legacy_stem_map[o_leg] = n_whole` with the new name's clustered identity prefix `<date>-<set>-<nn>` from `artifact_naming.parse_clustered_prefix(new_name)` (for `20260826-25kzda-01-25kzda-...spec.md` that is `20260826-25kzda-01`, which is what the maintainer hand-restored in d6b2fa00 for cjefq5/1bdxcp). When the new name does not parse as clustered (a legacy-to-legacy slug rename, where the prefix is unchanged), emit no legacy-prefix edit. Update the stale comment "The plans engine rewrites a legacy prefix to the NEW whole stem" to state the new rule.
  - Depends on: E-01
  - Expected outcome: E-01 (c) passes; the full-name and whole-stem rewrites are unchanged.
  - Execution state: pending

- [ ] E-04 Mask fenced code in both planning and applying. Add `_mask_fenced_code(text)` beside `_mask_permalinks`, same `(masked, restore)` contract with its own sentinel token, masking every block from an opening line matching the fence regex `ipd_lint._FENCE_RE` uses (``` or ~~~, optional indent) to its matching close (an unclosed fence masks to end of file, fail-safe). Apply it BEFORE `_mask_permalinks` in both `plan_reference_rewrites` and `apply_reference_rewrites`, so the planned hit count and the applied edit see the same text. Also skip fenced lines in `find_unrewritable_path_citations`, otherwise a transcript inside a fence that cites a different directory makes `--apply` fail loud on text that is deliberately not rewritten. Rationale for fences only: both measured falsifications (plans ha55fi and 3i6rso, restored by hand in d6b2fa00/084689ef) were transcripts; 3i6rso's sits in a ```` ``` ```` block. ha55fi's sits in an indented quoted string with NO fence, so it is NOT covered; record that in Findings as a known residual rather than masking indented text, which would also hide the indented evidence bullets that hold real citations.
  - Depends on: E-01
  - Expected outcome: E-01 (d) passes; (f) still passes.
  - Execution state: pending

- [ ] E-05 Refuse to rewrite a non-unique legacy prefix. Before emitting a legacy-prefix edit for `o_leg`, count tracked-or-present files under `.aw/records/**` (all types, all dispositions, recursive, excluding `untracked/` via the existing ignored-dir logic) whose filename starts with `o_leg + "-"`. If more than one (the file being renamed is one), emit NO legacy-prefix edit for that stem and return a warning; the full-name and whole-stem edits still apply, because those are unambiguous. Carry the warning out: add a `warnings` list to the function's result (a second return value from a new function `plan_reference_rewrites_with_warnings`, keeping the existing signature for the three callers that do not need it) and have `artifact_rename.run_rename_generic`, `run_group_generic`, `plans_refs.apply_renames` and `research_refs._apply_renames` print each as `--- WARNING: legacy prefix '<p>' is shared by <n> artifacts; short-handle citations of it were NOT rewritten ---` on preview and apply. Measured at HEAD: exactly ONE shared prefix exists, `20260725-0957-01` (the prompt `20260725-0957-01-external-delivery-host-probe.prompt.md` and the spec `20260725-0957-01-external-delivery-and-skills.spec.md`); `aw rename prompts 20260725-0957-01-external-delivery-host-probe.prompt.md --to-id6` preview today plans to rewrite `20260725-0957-01` in executed plan 1bdxcp's `deferred (2): 20260725-0957-01, ...` line, which is a citation of the SPEC.
  - Depends on: E-01
  - Expected outcome: E-01 (e) passes; that preview no longer lists the 1bdxcp rewrite and prints the warning.
  - Execution state: pending

- [ ] E-06 Confirm `tests/` rewrites interactively. In `artifact_rename.run_rename_generic` and `run_group_generic`, and in the plans and research apply paths, on `--apply` partition the planned edits into those under `tests/` and the rest. If the tests partition is non-empty AND the session is interactive (both stdin and stdout are TTYs and neither `AW_NONINTERACTIVE` nor `CI` is set, the same fence as `artifact_adopt.leak_gate_is_interactive`; reuse that predicate, or move it to `artifact_core` if importing `artifact_adopt` would create a cycle), print the affected test files and ask `Rewrite citations in these test files? [Y/n]` (empty answer is yes, EOF or `n` is no). On no, drop only the tests partition and say so. Non-interactive runs rewrite without asking (maintainer decision 2026-09-26: default is to rewrite tests/ too). `--yes` if present on the verb also skips the question.
  - Depends on: E-02
  - Expected outcome: E-01 (b) passes non-interactively; a scripted interactive test is not required (the predicate is already exercised by `artifact_adopt`'s tests), but the executor must demonstrate the prompt once by hand (V-06).
  - Execution state: pending

### Task group 3: prove it

- [ ] E-07 Live preview against this repository, no `--apply`: run `python3 -m agent_workflows rename prompts 20260725-0957-01-external-delivery-host-probe.prompt.md --to-id6` and `python3 -m agent_workflows rename specs 20260802-1904-01-ipd-structure-and-linting.spec.md --to-id6`, and save both outputs. The first must show the shared-prefix warning and no rewrite of 1bdxcp; the second must now list rewrites in `.aw/records/reviews/` and `tests/test_ipd_lint.py` (both cite that spec at HEAD) and any short-handle rewrite in the `<date>-<id6>-01` form. Then confirm `git status --porcelain` is unchanged (preview writes nothing).
  - Depends on: E-03, E-04, E-05, E-06
  - Expected outcome: both previews show the new behavior; the tree is untouched.
  - Execution state: pending

- [ ] E-08 Run `ruff check` and `ruff format --check` on the edited modules and the new test file, then the bare suite `python3 -m pytest`.
  - Depends on: E-07
  - Expected outcome: no ruff findings; suite passes.
  - Execution state: pending

- [ ] E-09 Add one `Fixed:` line to the pending 2.0.0 section of `CHANGELOG.md` stating, in user terms, that `aw rename` now also updates citations in review records and test files, keeps short handles short, leaves fenced transcripts alone, and warns instead of rewriting a date-time prefix two records share. No em or en dashes (user-facing prose).
  - Depends on: E-07
  - Expected outcome: one new line under the 2.0.0 heading.
  - Execution state: pending

## Project conventions discovered (Step 0)

- ONE matcher: `artifact_refs.plan_reference_rewrites` / `apply_reference_rewrites` serve every type; `plans_refs`, `research_refs` and `artifact_rename` delegate to it (IPD 3cmnfc). Fix it there once.
- `artifact_core.SCAN_ROOTS` is shared by `aw attention` (`attention.py` `_TREE_TO_SCAN_ROOTS` fallback), `find_dangling_citations`, `dead_filename_citations`, `research_archive` and `research_index`. Its `reviews` exclusion is a recorded decision (`attention_contract.py`, the `reviews` TreePolicy block) guarded by `tests/test_attention_contract.py` ("any(_scan_root_covers_tree(r, "reviews") for r in core.SCAN_ROOTS)" asserted False).
- Pinned-permalink masking (`_mask_permalinks`) is the precedent shape for masking: mask before counting AND before substituting, restore after.
- `ipd_lint._structural_lines` already defines fence semantics for plans (`_FENCE_RE`, matching open/close markers).
- Interactivity fence: `artifact_adopt.leak_gate_is_interactive` requires BOTH stdin and stdout TTYs and honors `AW_NONINTERACTIVE`/`CI`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Re-verified at HEAD 2026-09-26:

| Id | Severity | Evidence | Finding |
|---|---|---|---|
| F-1 | HIGH | `artifact_core.SCAN_ROOTS` (the tuple ending `".aw/records/prompts"`) has no reviews entry; `_TEXT_SUFFIXES = (".md", ".txt")`; 340 tracked `.review.md` files; `tests/*.py` cite 7 tracked record filenames/stems | Renames never reach reviews or tests. d6b2fa00 had to fix 9 reviews by hand. Confirmed. |
| F-2 | HIGH | `artifact_refs.plan_reference_rewrites`: `legacy_stem_map[o_leg] = n_whole`; d6b2fa00 restored 2 short handles (cjefq5, 1bdxcp) to `20260826-25kzda-01` | Short handle becomes a full stem. Confirmed. `artifact_naming.parse_clustered_prefix` returns `date/set/nn` for the new name, e.g. `20260826 25kzda 01`. |
| F-3 | HIGH | no fence masking anywhere in `artifact_refs`; 3i6rso's transcript line is inside a ```` ``` ```` block (fence opens 2 lines above); ha55fi's transcript is an indented quoted string with NO fence | Transcripts get rewritten. Fence masking fixes the 3i6rso shape; the ha55fi shape is a residual (see Deferred). The brief described both as "fenced code/transcripts"; only one was fenced. |
| F-4 | HIGH | Only one shared `YYYYMMDD-HHMM-NN` prefix among tracked `.aw/records` files: `20260725-0957-01` (a prompt and a spec). Live preview `aw rename prompts 20260725-0957-01-external-delivery-host-probe.prompt.md --to-id6` plans `rewrite 1x '20260725-0957-01' -> '20260725-a0p41s-01-a0p41s-external-delivery-host-probe.prompt'` in executed plan 1bdxcp, whose line reads `deferred (2): 20260725-0957-01, 20260726-1239-01` (the deferred SPECS) | Cross-type contamination, and it also shows F-2 on the same edit. The brief's example (an executed plan citing `20260725-0957-01-external-delivery-and-skills`) is protected already by the hyphen-boundaried matcher when the slug follows; the real victim is the BARE prefix citation of the spec. The fix (skip non-unique prefix) covers both. |
| F-5 | MEDIUM | `artifact_rename.find_unrewritable_path_citations` walks `iter_scan_files(repo_root)` (default `SCAN_ROOTS`); measured with widened roots, `tests/test_ipd_schema.py` cites `.agents/docs/specs/20260802-1904-01-...spec.md` and 3 review records cite `.aw/records/specs/<name>` without the status subdir | Once tests and reviews are scanned, those stale-directory path citations will make `--apply` fail loud for those specs. That is the existing, intended fail-loud contract applied to newly visible files, not a regression; E-05 keeps fenced lines out of it. |
| F-6 | LOW | `tests/fixtures/derive_plan_status_baseline.json` keys executed plan paths; `test_history_order` compares it to the live tree | JSON under tests/ must NOT be scanned, or a plan rename would rewrite a frozen baseline. `.json` is not added to the suffixes. |

## Proposed changes (ordered, validatable)

1. Failing outcome tests for all four defects plus the permalink guard (E-01).
2. Reference-scan roots separate from `SCAN_ROOTS`, `.py` under the reference scan only (E-02).
3. Short handle to short handle (E-03).
4. Fenced-code masking in plan, apply, and the unrewritable-path check (E-04).
5. Skip-and-warn on a shared legacy prefix (E-05).
6. Interactive confirmation for tests/ edits, default yes (E-06).
7. Live preview proof, ruff, suite, changelog (E-07..E-09).

## Deferred / out of scope (with reason)

- Masking UNFENCED transcripts (indented quoted `--- would rename ... ---` text such as executed plan ha55fi's V-04 evidence).
  - Carrier-Declined: indented lines in plans are also where real evidence citations live, so masking them would silently stop legitimate rewrites; the fenced shape is the one the tool can distinguish deterministically, and an unfenced transcript can be fenced by its author. The measured instance was already restored by hand in 084689ef.
- Widening `SCAN_ROOTS` for `aw attention` or the dangling detectors.
  - Carrier-Declined: explicitly refused by the recorded `reviews` TreePolicy decision in `attention_contract.py`; reference rewriting has its own list instead.

## Scope check

- Over-scope: none; the dangling detectors and attention keep their roots.
- Under-scope: `plans_refs.apply_renames` and `research_refs._apply_renames` must also print the shared-prefix warning and honor the tests/ confirmation, or `aw rename plans`/`aw rename research` would keep the silent behavior; both are in Scope-Paths.

## Required tests / validation

Outcome tests only, per the maintainer's standing rule: `tests/test_artifact_refs_rewrite.py` (E-01) asserts file contents after a real `aw rename --apply` in a tmp repo, never source text, fingerprints, docstrings or call counts. Six tests, one per defect plus the permalink guard. Plus the live preview (E-07), ruff, and the bare suite.

## Spec / documentation sync

No spec governs the reference matcher's roots or masking (checked: only `kw5y2s` and `4sd62s` mention `artifact_refs`, both in passing). One CHANGELOG `Fixed:` line (E-09). The `--no-refs` help text in `cli.py` ("do NOT rewrite citing documents") stays accurate.

## Open questions

### OQ-01: Should a shared legacy prefix be resolved by artifact type instead of skipped?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. A bare `YYYYMMDD-HHMM-NN` token carries no type, so the matcher cannot know which artifact a given occurrence cites; the maintainer's brief requires "only rewrite a legacy stem when it is unique across .aw/records, else skip and warn". Measured population is one shared prefix, so the cost of skipping is one warning.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" tests/test_artifact_refs_rewrite.py -v` run BEFORE any code change, showing tests (a), (b), (c), (d), (e) FAILED and (f) PASSED, with each failure's assertion message visible (e.g. the old full stem found where the short handle was expected for (c)).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_artifact_refs_rewrite.py tests/test_attention_contract.py -v` showing (a) now PASSES and every `test_attention_contract.py` test passes (proving `SCAN_ROOTS` still does not cover reviews); plus pasted `git diff agent_workflows/artifact_core.py` showing `SCAN_ROOTS` and `_TEXT_SUFFIXES` unchanged and only the new list/parameter added.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output showing (c) PASSES, and the pasted post-rename line of the fixture file containing `20260701-<id6>-01` with no `-legacy` tail.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted pytest output showing (d) and (f) PASS; for (d) additionally paste `sha256sum` (or the test's own byte comparison output) of the fenced block before and after, identical, AND the out-of-fence line rewritten.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted pytest output showing (e) PASSES, and the pasted `--- WARNING: legacy prefix '20260701-1200-01' is shared by 2 artifacts ...` line from the test's captured output.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted pytest output showing (b) PASSES non-interactively; AND a pasted by-hand interactive session in a scratch tmp repo (a real terminal) showing the `Rewrite citations in these test files? [Y/n]` prompt listing the test file, answered `n`, followed by the test file unchanged (`git diff --stat` empty for it) while a non-test citer was rewritten.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the two pasted preview outputs. Prompt preview: contains the shared-prefix WARNING for `20260725-0957-01` and NO `would rewrite ... in .aw/records/plans/executed/20260908-specdirs-02-1bdxcp-...` line. Spec preview: contains at least one `would rewrite` line whose path is under `.aw/records/reviews/` and one under `tests/`. Plus pasted `git status --porcelain` before and after, identical.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: pasted `ruff check` and `ruff format --check` output on `agent_workflows/artifact_core.py agent_workflows/artifact_refs.py agent_workflows/artifact_rename.py agent_workflows/plans_refs.py agent_workflows/research_refs.py tests/test_artifact_refs_rewrite.py` with no findings, and the pasted final summary line of bare `python3 -m pytest` showing `N passed` and no failures.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: pasted `git diff CHANGELOG.md` showing the single added `Fixed:` line under the 2.0.0 heading, and pasted `grep -nP '[\x{2013}\x{2014}]'` on that line returning nothing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A bug fix (Blocks-Release next, inherited from 7oql4z) to the one citation rewriter used by every `aw rename`/`aw group`. After it, a rename also updates citations in `.aw/records/reviews/` and `tests/` (asking first on a real TTY, rewriting by default otherwise), maps a short handle to the new short handle, leaves fenced transcripts and pinned permalinks alone, and refuses (with a warning) to rewrite a date-time prefix two records share. `aw attention`'s scan set is deliberately unchanged.

SCOPE FENCE, a declaration for reconciliation: the `- Scope-Paths:` list. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`aw ipd finalize --scope-reason`). EXPLICITLY NOT IN SCOPE: `SCAN_ROOTS`, `_TEXT_SUFFIXES`, the dangling detectors, `attention*.py`, and any already-broken citation in the tree.

HARD MUST: paste the ACTUAL output for every `V-*`; never claim a command passed without running it. Run the suite BARE as `python3 -m pytest`. E-07 is PREVIEW ONLY: do not `--apply` a rename of a real record in this plan.

Commit only the Scope-Paths files via `aw commit 5xzld0 -- <paths>`, never `git add -A`, never push. The plan reaches `executed/` only after every `V-*` carries observed evidence and `aw ipd lint --phase pre-transition` conforms, via `aw ipd finalize` (or the runner under `aw oc run`/`aw agy run`). This plan inherits `- Blocks-Release: next` from `7oql4z`; the gate is discharged by this plan reaching `executed`.
