# IPD: Make aw rename rewrite citations in reviews and tests without corrupting short handles, transcripts or shared legacy prefixes

- Date: 2026-09-26
- Kind: child
- Concern: `aw rename`/`aw group` rewrite inbound citations through ONE matcher (`artifact_refs.plan_reference_rewrites`) that has four measured defects: it never scans `.aw/records/reviews/` or `tests/`, so renamed artifacts leave dangling citations there; it expands a short legacy handle (`YYYYMMDD-HHMM-NN`) into the FULL new stem; it rewrites quoted command transcripts inside fenced code, falsifying recorded output; and it rewrites a legacy prefix that two artifacts of different types share, cross-contaminating citations of the other artifact.
- Scope: IN: a separate reference-scan root list (NOT `SCAN_ROOTS`) that adds `.aw/records/reviews` and `tests`, with `.py` scanned only under it; short-handle to short-handle mapping; fenced-code masking in plan and apply; skip-and-warn for a legacy prefix that is not unique across `.aw/records`; an interactive confirmation for `tests/` edits (default yes, non-interactive rewrites); outcome tests. OUT: widening `artifact_core.SCAN_ROOTS` or `_TEXT_SUFFIXES` (read by `aw attention` and the dangling detectors); masking indented code or quoted prose outside fences; repairing citations already broken by past renames.
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/artifact_refs.py, agent_workflows/artifact_rename.py, agent_workflows/plans_refs.py, agent_workflows/research_refs.py, tests/test_artifact_refs_rewrite.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 7oql4z
- Blocks-Release: next
- Set: renamescan
- Order: 1
- Highest E allocated: 10
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 5xzld0
- Approval: 2026-09-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-27 approved (aw set): status set to approved
- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 all FIXED. All four defects reproduced end to end in one run at HEAD 8e96d348. PR-001 (HIGH): E-01's own fixture, as specified, made the rename exit 2 with nothing done, so five cases would have failed for an unrelated reason; fixture now mandates real directories plus per-test exit-code assertions. PR-002: F-5's premise measured FALSE (widening newly blocks 0 of 60 legacy targets; its example spec already exits 2 today), downgraded and E-07's expectation corrected. PR-005: E-05 split into E-05 + E-10 via aw ipd sync, clearing the IPD-Z602 density advisory. PR-003/PR-004 carried as new Blocks-Release bugs p0a5kr and zftbta; Goal narrowed so it no longer claims to reach every citation. Findings and decisions D-1..D-4 in .aw/records/reviews/20260926-renamescan-01-5xzld0-make-aw-rename-rewrite-citations-in-reviews-and-tests-withou.review.md
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 7oql4z: aw rename gains reviews/tests reference roots, short-handle mapping, fenced-code masking and a shared-legacy-prefix skip.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make a rename rewrite every real citation of the renamed artifact, including those in review records and test files, while leaving untouched the text that is not a citation of it: quoted transcripts in fenced code, pinned permalinks, and a legacy prefix that also names a different artifact. A short handle must stay a short handle.

WHAT "EVERY REAL CITATION" DOES NOT INCLUDE, narrowed at review (PR-004) because the unqualified claim is false after this plan. Citations in PRODUCTION SOURCE (`agent_workflows/*.py`) are NOT rewritten, and 44 of them exist (F-8). The scope of this plan is the two TEXT trees the carrier item names, `.aw/records/reviews/` and `tests/`; extending the rewriter into the shipped package is a materially higher-risk change and is carried separately. A reader auditing "does a rename now reach every citation?" must read F-8 before answering yes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: failing outcome tests first

- [ ] E-01 Add `tests/test_artifact_refs_rewrite.py` with a tmp git repo fixture (the `_RepoTestCase` shape in `tests/test_spec_id6_filenames.py`: `git init`, `.aw/records/specs/`, `.aw/records/plans/pending/`, `.aw/config/project.json`) and SIX outcome tests, each driving `cli.main(["rename", "specs", <legacy-name>, "--to-id6", "--apply", "--no-commit", "--dir", tmp])` and asserting only file contents after the run: (a) a `.aw/records/reviews/<x>.review.md` citing the spec's full filename now cites the new filename; (b) a `tests/test_x.py` citing it is rewritten when stdin is NOT a TTY (default under pytest); (c) a file containing the short handle `20260701-1200-01` (backticked, no slug) now contains `20260701-<id6>-01` and NOT the full new stem; (d) a plan whose fenced block (```` ``` ````) contains `--- would rename .../20260701-1200-01-legacy.spec.md -> ... ---` is byte-identical after the rename, while a citation of the same name OUTSIDE the fence in that same file IS rewritten; (e) a second artifact of another type sharing the prefix (`.aw/records/prompts/executed/20260701-1200-01-other.prompt.md`) exists, and a plan citing `20260701-1200-01-other` and the bare `20260701-1200-01` is byte-identical after renaming the spec, and the command output names the skipped prefix; (f) a pinned permalink `https://example.invalid/o/r/blob/0123456789abcdef/.aw/records/specs/20260701-1200-01-legacy.spec.md` stays byte-identical. Tests assert OUTCOMES only: no source-text, fingerprint, docstring or call-count assertions.

  FIXTURE TRAP, MEASURED AT REVIEW AND MANDATORY (PR-001). Every fenced or path-shaped citation in these fixtures MUST name the spec's REAL directory (`.aw/records/specs/`). `find_unrewritable_path_citations` treats a path citation naming ANY OTHER directory as un-auto-rewritable, and on `--apply` that makes `run_rename_generic` print `error: full-path citation ... cannot auto-rewrite` and return exit 2 BEFORE any rewrite happens. Executed at review: with case (d)'s transcript written as `x/20260701-1200-01-legacy.spec.md`, the whole command returned rc=2 and NOTHING was renamed or rewritten, so cases (a), (b), (c) and (e) would all have failed for a reason unrelated to the defects they pin - a false red that would have sent the executor hunting the wrong bug. With the same fixture citing `.aw/records/specs/20260701-1200-01-legacy.spec.md` the command returned rc=0 and reproduced all four defects in ONE run. Each test MUST also assert the run's exit code is 0 (except where a case deliberately tests a refusal), so a future fixture that trips this gate fails loudly as a fixture error instead of masquerading as a defect.
  - Depends on: none
  - Expected outcome: at HEAD (a), (b), (c), (d) and (e) FAIL and (f) passes (permalink masking already exists); this pins the four defects before any code changes. Measured at review on a fixture of exactly this shape (rc=0): the review record and `tests/test_x.py` were NOT touched (pins a and b); the out-of-fence citation AND the in-fence transcript were BOTH rewritten to `20260701-rttogp-01-rttogp-legacy.spec.md` (pins d); and the whole-stem edit fired twice, so (c)'s short-handle case needs the bare `20260701-1200-01` token with no slug following it to isolate the legacy-prefix edit.
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

- [ ] E-05 DETECT AND SKIP a non-unique legacy prefix (the decision only; the operator-facing warning is E-NEW). Before emitting a legacy-prefix edit for `o_leg`, count files present under `.aw/records/**` (all types, all dispositions, recursive, excluding `untracked/` via the existing ignored-dir logic) whose filename starts with `o_leg + "-"`. If more than one (the file being renamed is one), emit NO legacy-prefix edit for that stem. The full-name and whole-stem edits still apply, because those are unambiguous. Expose the skipped prefixes through a new `plan_reference_rewrites_with_warnings` returning `(edits, warnings)`, leaving `plan_reference_rewrites`'s existing signature untouched for the callers that do not need them. RE-MEASURED AT REVIEW: exactly ONE shared prefix exists in the whole corpus, `20260725-0957-01`, held by the prompt `20260725-0957-01-external-delivery-host-probe.prompt.md` and the spec `20260725-0957-01-external-delivery-and-skills.spec.md` (60 legacy-prefixed records scanned, one collision).
  - Depends on: E-01
  - Expected outcome: E-01 (e) passes on the CONTENT assertion (the sharing artifact's citations are byte-identical). Re-derive the shared-prefix population at execution rather than trusting the count above; the BAR is "no legacy-prefix edit is emitted for a prefix held by more than one record", not the number one.
  - Execution state: pending

- [ ] E-10 CARRY THE SKIP WARNING OUT to every operator-facing path. Have `artifact_rename.run_rename_generic`, `artifact_rename.run_group_generic`, `plans_refs.apply_renames` and `research_refs._apply_renames` consume `plan_reference_rewrites_with_warnings` and print each skipped prefix as `--- WARNING: legacy prefix '<p>' is shared by <n> artifacts; short-handle citations of it were NOT rewritten ---`, on BOTH preview and apply, so a silent skip is impossible. Split out of E-05 at review (PR-005) because E-05 is one decision in one function while this touches four call sites across three modules, and because the lint density check flagged the combined item.
  - Depends on: E-05
  - Expected outcome: `aw rename prompts 20260725-0957-01-external-delivery-host-probe.prompt.md --to-id6` preview prints the warning and NO LONGER lists the `20260725-0957-01` rewrite in executed plan 1bdxcp. Measured at review on the PRE-change code, that preview emits `--- would rewrite 1x '20260725-0957-01' -> '20260725-uaeizs-01-uaeizs-external-delivery-host-probe.prompt' in .aw/records/plans/executed/20260908-specdirs-02-1bdxcp-...ipd.md ---`, whose target line is `    - deferred (2): 20260725-0957-01, 20260726-1239-01`, a citation of the SPEC and not of the renamed prompt. That single line demonstrates BOTH F-2 and F-4 at once.
  - Execution state: pending

- [ ] E-06 Confirm `tests/` rewrites interactively. In `artifact_rename.run_rename_generic` and `run_group_generic`, and in the plans and research apply paths, on `--apply` partition the planned edits into those under `tests/` and the rest. If the tests partition is non-empty AND the session is interactive (both stdin and stdout are TTYs and neither `AW_NONINTERACTIVE` nor `CI` is set, the same fence as `artifact_adopt.leak_gate_is_interactive`; reuse that predicate, or move it to `artifact_core` if importing `artifact_adopt` would create a cycle), print the affected test files and ask `Rewrite citations in these test files? [Y/n]` (empty answer is yes, EOF or `n` is no). On no, drop only the tests partition and say so. Non-interactive runs rewrite without asking (maintainer decision 2026-09-26: default is to rewrite tests/ too). `--yes` if present on the verb also skips the question.
  - Depends on: E-02
  - Expected outcome: E-01 (b) passes non-interactively; a scripted interactive test is not required (the predicate is already exercised by `artifact_adopt`'s tests), but the executor must demonstrate the prompt once by hand (V-06).
  - Execution state: pending

### Task group 3: prove it

- [ ] E-07 Live preview against this repository, no `--apply`: run `python3 -m agent_workflows rename prompts 20260725-0957-01-external-delivery-host-probe.prompt.md --to-id6` and `python3 -m agent_workflows rename specs 20260802-1904-01-ipd-structure-and-linting.spec.md --to-id6`, and save both outputs. The first must show the shared-prefix warning and no rewrite of 1bdxcp. The second must now list rewrites under `.aw/records/reviews/` and in `tests/test_ipd_lint.py`, plus any short-handle rewrite in the `<date>-<id6>-01` form. Then confirm `git status --porcelain` is unchanged (preview writes nothing).

  WHAT THE SPEC PREVIEW ALSO PRINTS, AND WHY THAT IS NOT A FAILURE (measured at review, PR-002). At HEAD that second preview emits **25** `--- WARNING: full-path citation ... names a different directory and cannot be auto-rewritten; fix it by hand ---` lines across 14 files, from the CURRENT scan roots alone. Those warnings are pre-existing and are NOT caused by this plan; do not treat them as a regression and do not try to make them go away. The measured citers are stale `.agents/docs/specs/...` and status-dir-less `.aw/records/specs/...` paths. Note the consequence honestly: because `run_rename_generic` returns exit 2 on `--apply` whenever that list is non-empty, this particular spec CANNOT be `--apply`-renamed today without hand-fixing those citations first. That is the existing fail-loud contract, it is the same before and after this plan, and it is another reason E-07 is preview-only.
  - Depends on: E-03, E-04, E-05, E-10, E-06
  - Expected outcome: both previews show the new behavior; the tree is untouched. The prompt preview additionally shows the E-10 warning; the spec preview additionally shows its 25 pre-existing full-path warnings (re-derive the count, it drifts).
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
- `artifact_core.SCAN_ROOTS` is shared by `aw attention` (`attention.py` `_TREE_TO_SCAN_ROOTS` fallback), `find_dangling_citations`, `dead_filename_citations`, `research_archive` and `research_index`. Its `reviews` exclusion is a recorded decision (`attention_contract.py`, the `reviews` TreePolicy block) guarded by `tests/test_attention_contract.py::ReviewsTreeIsDecidedTests::test_reviews_is_excluded_with_a_rationale` ("any(_scan_root_covers_tree(r, "reviews") for r in core.SCAN_ROOTS)" asserted False). Verified at review: that assertion exists and reads exactly so. Note the surrounding test class also asserts every TRACKED tree IS covered, so adding a reviews scan root would not break that half; the specific `assertFalse` above is what refuses it.
- REVIEW-FILE COUNT, corrected at review: the tracked corpus is **364** `.review.md` files today. The `attention_contract` comment says "231 file reads per invocation" and this plan's own Concern said "~340"; both are stale snapshots of a growing population. The ARGUMENT (an excluded tree should not be read and discarded per `aw attention` call) is unaffected by the number, which is why no count is load-bearing here. Measured cost of the widened REFERENCE scan, which is a different code path and runs only on a rename: `iter_scan_files` goes from 1699 files / 97 ms to 2244 files / 119 ms, a 22 ms delta on a command a human runs deliberately. Not user-perceptible, so not a defect by the repository's own bar.
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
| F-5 | LOW (was MEDIUM; CORRECTED AT REVIEW, PR-002) | `artifact_rename.find_unrewritable_path_citations` walks `iter_scan_files(repo_root)` (default `SCAN_ROOTS`). Measured at review over all 60 legacy-prefixed records in `.aw/records/**`, comparing the unrewritable set under CURRENT roots against the WIDENED roots (`+.aw/records/reviews`, `+tests`, `+.py`): already-blocked 23, NEWLY blocked by widening **0**, clean 37 | The premise of the original F-5 is FALSE: widening the roots blocks NOTHING that is not already blocked. The two files it names are real citers, but the spec they cite (`20260802-1904-01-ipd-structure-and-linting.spec.md`) ALREADY yields 25 unrewritable citations across 14 files from the CURRENT roots, so `aw rename specs ... --to-id6 --apply` already exits 2 for it today. This finding is therefore informational, not a risk this plan introduces; the real hazard in this area is the FIXTURE trap recorded in E-01 (PR-001). E-04 still keeps fenced lines out of the check, which is correct on its own merits. |
| F-6 | LOW | `tests/fixtures/derive_plan_status_baseline.json` keys executed plan paths; `test_history_order` compares it to the live tree | JSON under tests/ must NOT be scanned, or a plan rename would rewrite a frozen baseline. `.json` is not added to the suffixes. |
| F-7 | MEDIUM (added at review, PR-003) | Measured at review: `tests/test_history_order.py::DerivationIsUnchangedTests` intersects the live terminal-plan set with the 777-key baseline and asserts `assertGreaterEqual(len(intersection), 700)`. Current intersection is **732**, a margin of only **32** | EXCLUDING `.json` (F-6) is necessary but NOT sufficient, and the plan treats it as sufficient. Because the baseline keys PATHS and is deliberately not rewritten, every `aw rename plans` / `aw group plans --rename` of a TERMINAL plan drops one key out of the intersection. 33 such renames would breach the floor and redden a test that has nothing to do with renaming. This is a pre-existing coupling this plan does not create, but the plan is the first to make renaming routine enough to hit it, and F-6's reasoning stops one step short of it. Recorded with a carrier rather than fixed here (out of `- Scope-Paths:`). |
| F-9 | LOW (added at review, PR-006) | Measured at review: `20260722-2317-01` is held by exactly ONE record on disk today (`.aw/records/prompts/executed/20260722-2317-01-token-efficient-managed-sections-research-prompt.prompt.md`), so E-05's uniqueness check finds NO collision and the legacy-prefix edit IS emitted. But the same token is cited as RESEARCH in `DECISIONS.md` ("Cross-references research `20260722-2241-01` ... and `20260722-2317-01`") and in executed plan `kemhdg` (`research '20260722-2317-01:10-38'`), and a research file with that prefix demonstrably existed (dependent plan `iyi4hc`'s F-4 cites `git log --all --name-only`). | E-05's guard is a CURRENT-TREE uniqueness test, so it cannot see HISTORICAL ambiguity: renaming that prompt would rewrite two citations that name a deleted research artifact, not the prompt. The bound is honest and narrow, and it is NOT a reason to widen E-05 (a history-walking uniqueness check would be a different and much slower design). It is recorded because the dependent plan `iyi4hc` relies on this guard and already documents the gap as its own E-03's responsibility, so the two plans must not both assume the other covers it. |
| F-8 | MEDIUM (added at review, PR-004) | Measured at review: 44 citations of real record filenames or legacy prefixes live in `agent_workflows/*.py` (e.g. `attention_contract.py` cites `20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` in full; `ipd_schema.py` cites `20260802-1904-01-ipd-structure-and-linting.spec.md`; `check_engine.py` cites two full record names). The maintainer's own `d6b2fa00` commit message lists "two spec handles in `runner_shared.py`" among what it had to fix BY HAND | The defect class F-1 names is WIDER than reviews and tests: production source carries citations too, and this plan leaves all 44 dangling after a rename, so a maintainer keeps hand-fixing them. Deliberately NOT fixed here (rewriting `agent_workflows/*.py` from a records rename is a materially riskier change than rewriting `tests/`, and every one of those modules is outside `- Scope-Paths:`), but it must be a recorded carrier rather than silence, because the plan's Goal claims "every real citation". |

## Proposed changes (ordered, validatable)

1. Failing outcome tests for all four defects plus the permalink guard (E-01), with fixture path citations naming the artifact's REAL directory so the run is not refused before it starts (PR-001).
2. Reference-scan roots separate from `SCAN_ROOTS`, `.py` under the reference scan only (E-02).
3. Short handle to short handle (E-03).
4. Fenced-code masking in plan, apply, and the unrewritable-path check (E-04).
5. Skip a shared legacy prefix (E-05), then carry the warning to all four operator-facing call sites (E-10). Split at review (PR-005).
6. Interactive confirmation for tests/ edits, default yes (E-06).
7. Live preview proof, ruff, suite, changelog (E-07..E-09).

## Deferred / out of scope (with reason)

- Masking UNFENCED transcripts (indented quoted `--- would rename ... ---` text such as executed plan ha55fi's V-04 evidence).
  - Carrier-Declined: indented lines in plans are also where real evidence citations live, so masking them would silently stop legitimate rewrites; the fenced shape is the one the tool can distinguish deterministically, and an unfenced transcript can be fenced by its author. The measured instance was already restored by hand in 084689ef.
- Widening `SCAN_ROOTS` for `aw attention` or the dangling detectors.
  - Carrier-Declined: explicitly refused by the recorded `reviews` TreePolicy decision in `attention_contract.py`; reference rewriting has its own list instead.
- Rewriting record citations in PRODUCTION SOURCE (`agent_workflows/*.py`), 44 of which exist (F-8, added at review).
  - Carrier: zftbta
- The frozen `derive_plan_status_baseline.json` path-keyed floor that a terminal-plan rename erodes (F-7, added at review). Excluding `.json` from the rewrite is necessary but does not address the erosion.
  - Carrier: p0a5kr
- HISTORICAL ambiguity of a legacy prefix that is unique on disk today (F-9, added at review).
  - Carrier-Declined: E-05's guard is deliberately a current-tree check, and that bound is now stated in F-9 rather than implied. Detecting historical ambiguity would require walking git history for deleted filenames on every rename, which is a different and far slower design for a case that is ALREADY covered downstream: the dependent plan `iyi4hc` (which carries `- Item-Dependencies: executed:5xzld0`) records the same gap as its own F-4 and assigns its E-03 per-occurrence classification to handle it. Recording the bound here is what stops both plans assuming the other covers it.

## Scope check

- Over-scope: none; the dangling detectors and attention keep their roots.
- Under-scope: `plans_refs.apply_renames` and `research_refs._apply_renames` must also print the shared-prefix warning (E-10) and honor the tests/ confirmation (E-06), or `aw rename plans`/`aw rename research` would keep the silent behavior; both are in Scope-Paths.
- Under-scope, ACCEPTED AND CARRIED (added at review): the citation-rot defect class extends beyond the two trees this plan fixes. Production source carries 44 such citations (F-8, carrier `zftbta`) and the frozen status baseline is eroded by terminal-plan renames (F-7, carrier `p0a5kr`). Neither is fixed here and neither is silently dropped; the Goal was narrowed so the plan does not claim coverage it lacks.
- Scope-Paths note: `tests/test_artifact_refs_rewrite.py` is the only NEW file. `CHANGELOG.md` is declared for E-09. Nothing in `- Scope-Paths:` is a `.spec.md`, so this run declares no spec edit.

## Required tests / validation

Outcome tests only, per the maintainer's standing rule: `tests/test_artifact_refs_rewrite.py` (E-01) asserts file contents after a real `aw rename --apply` in a tmp repo, never source text, fingerprints, docstrings or call counts. Six tests, one per defect plus the permalink guard. Plus the live preview (E-07), ruff, and the bare suite.

TWO REQUIREMENTS ADDED AT REVIEW, both from measurement:
- Every test asserts the run's EXIT CODE is 0 alongside its content assertions (PR-001). Measured at review: a fixture whose path citation named a directory other than the artifact's real one made the whole `--apply` return rc=2 with nothing renamed, which would have turned four unrelated cases red for the wrong reason. Asserting rc makes that a loud fixture error instead of a misleading defect signal.
- The new test module must carry NO `pytestmark = pytest.mark.slow`, so it runs in the bare suite E-08 gates on. `tests/test_cli.py` and `tests/test_installer.py` are both slow-marked (`pytestmark = pytest.mark.slow`), so a case placed in either would be written and then excluded from the bare run by the configured `-m 'not slow'`.

BASELINE for E-08's comparison, measured at review on this lane: `2501 passed, 2 skipped, 3 warnings in 59.95s`. RE-DERIVE it rather than matching the number (a live population); the BAR is that the after-minus-before failing node set is empty.

## Spec / documentation sync

No spec governs the reference matcher's roots or masking (checked: only `kw5y2s` and `4sd62s` mention `artifact_refs`, both in passing). One CHANGELOG `Fixed:` line (E-09). The `--no-refs` help text in `cli.py` ("do NOT rewrite citing documents") stays accurate.

VERIFIED AT REVIEW, including the one place that needed a closer look. Both spec citations are real and both are genuinely in passing: `kw5y2s` Section references `artifact_refs` only as a cross-reference, and `4sd62s` Section 4.4 names it in a LIST of scanners that must exclude a future `records/meta/` tree through one shared exclusion list in `artifact_core`. That obligation does not conflict with E-02: `4sd62s` is `- Status: reviewed` (not implemented), no `records/meta` exclusion exists in `artifact_core` today (`rg 'records/meta' agent_workflows/artifact_core.py` returns nothing), and E-02 adds a SEPARATE root list rather than changing how exclusions work, so whoever implements `4sd62s` applies its shared exclusion to both lists. Recorded so that implementer knows a second list now exists. The `--no-refs` help string was read and is unchanged by this plan. No `.spec.md` is in `- Scope-Paths:`, so this run declares no spec edit.

## Open questions

### OQ-01: Should a shared legacy prefix be resolved by artifact type instead of skipped?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. A bare `YYYYMMDD-HHMM-NN` token carries no type, so the matcher cannot know which artifact a given occurrence cites; the maintainer's brief requires "only rewrite a legacy stem when it is unique across .aw/records, else skip and warn". Measured population is one shared prefix, so the cost of skipping is one warning. CONFIRMED AT REVIEW by re-deriving the collision map over all 60 legacy-prefixed records: exactly one shared prefix, `20260725-0957-01`, and the ambiguity is genuinely unresolvable from the token alone (the two holders are a prompt and a spec, and executed plan 1bdxcp's `deferred (2): 20260725-0957-01, ...` line cites the SPEC while the prompt is what a `rename prompts` invocation is renaming).

### OQ-02: Should this plan also fix the 44 record citations in production source, and the baseline-floor erosion?

- Blocking: no
- Status: resolved
- Owner: reviewer (raised and resolved at review)
- Resolution or deferral rationale: No to both, and each is CARRIED rather than declined, because both are real unfixed defects rather than deliberate divergences. Production source (F-8, carrier `zftbta`): rewriting `agent_workflows/*.py` from a records rename changes the shipped package rather than a document, so a bad substitution is a runtime defect rather than a stale citation; every one of those 13-plus modules is outside `- Scope-Paths:`; and the carrier records a cheaper alternative worth weighing first (a CHECK that reports a dangling record citation in source, with no rewrite risk at all). Baseline erosion (F-7, carrier `p0a5kr`): the fix is to change how `tests/test_history_order.py` keys or floors its comparison, which is a test-architecture decision affecting a guard other work depends on, and the margin is 32 renames wide so it is not urgent. What this review DID do is stop the plan claiming coverage it does not have: the Goal now states the production-source exclusion explicitly.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" tests/test_artifact_refs_rewrite.py -v` run BEFORE any code change, showing tests (a), (b), (c), (d), (e) FAILED and (f) PASSED, with each failure's assertion message visible (e.g. the old full stem found where the short handle was expected for (c)).

    EACH FAILURE MUST FAIL FOR ITS OWN REASON, not because the command refused (PR-001). State explicitly, for each of (a)-(e), that the rename's exit code was 0 and the file WAS renamed, and that the failure is the missing or wrong REWRITE. A paste in which every case fails with `error: full-path citation ... cannot auto-rewrite` is the FIXTURE TRAP, not the defects: fix the fixture so its path citations name `.aw/records/specs/` and re-run. Measured at review: the trapped variant returns rc=2 and renames nothing, while the corrected one returns rc=0 and reproduces all four defects in one run.
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
  - Required evidence: pasted pytest output showing (e) PASSES on its CONTENT assertion, i.e. the sharing artifact's citations are byte-identical after the rename (the WARNING line itself is E-10's evidence, in V-10). Plus a pasted RE-DERIVATION of the shared-prefix population at execution time: the list of every `YYYYMMDD-HHMM-NN` prefix under `.aw/records/**` held by more than one record, with its holders. Do NOT assert the count is one; assert the PROPERTY that no legacy-prefix edit is emitted for any prefix in that list. Measured at review the list had exactly one entry (`20260725-0957-01`: a prompt and a spec), but it is a live population.
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
- [ ] V-10 validates E-10
  - Required evidence: paste the E-01 (e) test output showing the WARNING line captured from the command's own stdout (not from the test's expectations), for BOTH the preview and the `--apply` path, proving the skip is never silent. Then paste the live `python3 -m agent_workflows rename prompts 20260725-0957-01-external-delivery-host-probe.prompt.md --to-id6` preview (NO `--apply`) showing (i) the `--- WARNING: legacy prefix '20260725-0957-01' is shared by 2 artifacts ...` line and (ii) the ABSENCE of any `would rewrite ... '20260725-0957-01' ...` line naming `.aw/records/plans/executed/20260908-specdirs-02-1bdxcp-...`. Paste the pre-change preview line for contrast (it is quoted verbatim in E-10's Expected outcome, re-derive it from a worktree at the pre-change commit rather than trusting the quote). Also confirm all four call sites were reached, by naming for each of `run_rename_generic`, `run_group_generic`, `plans_refs.apply_renames` and `research_refs._apply_renames` either the test that drives it or the by-hand invocation that did, since an unreached call site is exactly the silent-skip regression this item exists to prevent.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A bug fix (Blocks-Release next, inherited from 7oql4z) to the one citation rewriter used by every `aw rename`/`aw group`. After it, a rename also updates citations in `.aw/records/reviews/` and `tests/` (asking first on a real TTY, rewriting by default otherwise), maps a short handle to the new short handle, leaves fenced transcripts and pinned permalinks alone, and refuses (with a warning) to rewrite a date-time prefix two records share. `aw attention`'s scan set is deliberately unchanged.

TWO THINGS THIS DOES NOT FIX, stated at review so approval is informed rather than assumed. FIRST, a rename still leaves 44 record citations dangling in the SHIPPED PACKAGE (`agent_workflows/*.py`), which the maintainer has already hand-fixed once (`d6b2fa00` names "two spec handles in `runner_shared.py`"); carrier `zftbta`. SECOND, renaming a TERMINAL plan still erodes `tests/test_history_order.py`'s frozen 700-path floor, currently 32 renames from breaching; carrier `p0a5kr`. Both are recorded as `- Blocks-Release: next` bugs of their own rather than folded in, because each changes a materially different surface (the shipped package; a test-architecture guard). The Goal was narrowed accordingly, so this plan no longer claims to reach "every real citation".

ONE OPERATIONAL NOTE for whoever runs this. `aw rename specs 20260802-1904-01-ipd-structure-and-linting.spec.md --apply` ALREADY exits 2 today, before and after this plan, because 25 full-path citations across 14 files name stale directories and the fail-loud contract refuses rather than half-rewriting them. That spec is E-07's preview subject precisely because it cannot be applied; do not read those warnings as damage this plan did.

SCOPE FENCE, a declaration for reconciliation: the `- Scope-Paths:` list. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`aw ipd finalize --scope-reason`). EXPLICITLY NOT IN SCOPE: `SCAN_ROOTS`, `_TEXT_SUFFIXES`, the dangling detectors, `attention*.py`, and any already-broken citation in the tree.

HARD MUST: paste the ACTUAL output for every `V-*`; never claim a command passed without running it. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly` (a second `-q` compounds into `-qq` and suppresses the very `N passed` line V-08 requires). E-07 is PREVIEW ONLY: do not `--apply` a rename of a real record in this plan. No test may assert on source text, a fingerprint, a docstring, or a call count (maintainer standing rule).

TWO FALSE-GREEN / FALSE-RED TRAPS the executor must not paste through. (1) V-01's before-fix run must fail for the DEFECTS, not because the fixture tripped the un-auto-rewritable path gate and the command returned rc=2 having renamed nothing; assert rc per test (PR-001). (2) The new test module must not be `slow`-marked, or E-08's bare suite will never run it.

Commit only the Scope-Paths files via `aw commit 5xzld0 -- <paths>`, never `git add -A`, never push. The plan reaches `executed/` only after every `V-*` carries observed evidence and `aw ipd lint --phase pre-transition` conforms, via `aw ipd finalize` (or the runner under `aw oc run`/`aw agy run`). This plan inherits `- Blocks-Release: next` from `7oql4z`; the gate is discharged by this plan reaching `executed`.
