# IPD: Rewrite facet-less stem citations on rename, guarded against stems shared by sibling records

- Date: 2026-10-12
- Kind: child
- Concern: `artifact_refs.plan_reference_rewrites_with_warnings` builds only two match keys from an old/new filename pair (the full filename and the facet-bearing whole stem from `artifact_refs._whole_stem`), so a citation that names a record by its FACET-LESS stem (ending at the slug, no `.ipd`, no `.md`) is never rewritten by `aw rename`/`aw group`, and the preview looks complete while the citation is left dangling.
- Scope: IN: add a third, guarded match key (the facet-less stem, derived by stripping a `.<facet>.md` suffix drawn from the closed enum `artifact_naming.ARTIFACT_TYPE_FACETS`) to the shared reference planner and applier, with a sibling-collision guard that skips and warns when another record shares that facet-less stem, plus CLI-driven outcome tests and one CHANGELOG line. OUT: scanning `.json` files (measured unnecessary, F-05); scanning `README.md` files that `artifact_refs._SKIP_NAMES` excludes (filed as backlog `0u0ako`, F-06); research's own `.<model>.<kind>.md` naming (measured zero facet-less citations, F-04); any hand repair of an existing citation (that is plan `j7dsci`).
- Scope-Paths: agent_workflows/artifact_refs.py, tests/test_artifact_refs_rewrite.py, CHANGELOG.md
- Item-Dependencies: executed:j7dsci
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: xp6o3v
- Set: xp6o3v
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: 1v2e1o
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006. Record: .aw/records/reviews/20261012-xp6o3v-01-1v2e1o-rewrite-facet-less-stem-citations-on-rename-guarded-against.review.md Round 1

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): graduated backlog `xp6o3v`. The item's open question (is a facet-less key safe across the whole corpus?) is RESOLVED FROM A CORPUS MEASUREMENT rather than deferred (F-03, F-04): every sampled facet-less occurrence of a unique record stem is a file citation, and a full stem always carries date, set, order and id6, so it cannot be confused with a bare slug. The one real ambiguity (714 `.ipd.md`/`.review.md` pairs share a facet-less stem) is closed by a skip-and-warn guard modelled on the existing `count_legacy_prefix_records` precedent. The `.json` blind spot is resolved by evidence that `rlcq7g` already re-keyed the only affected fixture.

## Goal

Make every rename or regroup that rewrites references also rewrite a citation that names the renamed record by its facet-less stem, so a maintainer's preview of `aw rename`/`aw group` lists, and `--apply` repairs, the citations backlog `xp6o3v` measured it silently misses.

Do it without widening the matcher into ambiguity: when a facet-less stem is shared by another record (for example a plan and its `.review.md`), skip it and say so, exactly as the module already does for a shared legacy prefix.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline

- [x] E-01 CAPTURE THE PRE-CHANGE BASELINE under `/tmp/opencode/1v2e1o-baseline/`: (a) `python3 -m pytest -o addopts="" tests/test_artifact_refs_rewrite.py` output, recording the passing test NAMES (14 at authoring and 14 at review; context, not a bar); (b) a READ-ONLY planner call `artifact_refs.plan_reference_rewrites_with_warnings(Path('.'), {old: new})` for a real record whose facet-less stem is cited, recording the set of files and edit count. Use the `49eeuc` plan, `20260722-assess-and-00-49eeuc-assess-and-producers-closing-artifacts-report.ipd.md` -> `20260722-assess-and-00-49eeuc-probe-slug.ipd.md`, because `DECISIONS.md` cites it facet-less ("Executed per IPD 20260722-assess-and-00-49eeuc-assess-and-producers-closing-artifacts-report"). If `j7dsci` has executed and `qrokie` no longer has a facet-less citation, this record still serves. Do NOT apply anything; the planner is pure. (c) Re-run the F-03/F-04 census script (paste it) and record its counts at execution HEAD, including the number of facet-less occurrences of SHARED stems (0 at authoring and at review) and of stems whose record name is NOT dated (`artifact_naming.parse_clustered` and `artifact_naming._LEGACY_TIMESTAMP_RE` both fail, e.g. `.aw/records/prompt-library/fix-bar.prompt.md`: 6 occurrences in 2 files at review).
  - Depends on: none
  - Expected outcome: Saved baseline showing the existing tests passing and a preview for `49eeuc` that does NOT list `DECISIONS.md` for a facet-less hit, plus the census counts as re-measured.
  - Execution state: performed

### Task group 2: the matcher

- [x] E-02 ADD THE FACET-LESS KEY. In `agent_workflows/artifact_refs.py`: add a helper `_facetless_stem(name)` that returns `name` minus a trailing `.<facet>.md` where `<facet>` is in `artifact_naming.ARTIFACT_TYPE_FACETS` (import already present as `_naming`), else `None`. It ALSO returns `None` unless `name` is a DATED record name, i.e. `_naming.parse_clustered(name)` or `_naming._LEGACY_TIMESTAMP_RE.match(name)` matches: an undated name such as `.aw/records/prompt-library/fix-bar.prompt.md` has the facet-less stem `fix-bar`, which is an ordinary hyphenated phrase in prose, so admitting it would rewrite prose (F-08). Add a module constant `FACETLESS_STEM = "facetless-stem"` beside `FULL_NAME`/`BARE_STEM`, and update the `RefEdit` docstring to list it. Add a matcher `_facetless_boundaried(stem)` that is `_boundaried`'s pattern plus a negative lookahead refusing a following `.<facet>` or `.md` token (`(?!\.(?:<facets>|md)(?![0-9A-Za-z]))`), so a facet-bearing occurrence is never double counted or double rewritten. In `plan_reference_rewrites_with_warnings`, build a `facetless_stem_map` from each changed pair when both stems exist, differ from each other, and differ from the whole stem; emit `RefEdit(f, FACETLESS_STEM, old, new, n)` using the new matcher, AFTER the whole-stem and legacy loops. In `apply_reference_rewrites`, order edits FULL_NAME, then BARE_STEM, then FACETLESS_STEM, and substitute FACETLESS_STEM edits with `_facetless_boundaried`. Keep fenced-code and permalink masking exactly as today (both functions already mask before matching).
  WHY A NEW KIND RATHER THAN REUSING `bare-stem`: the applier picks its substitution pattern by `kind`, and the facet-less key needs the stricter pattern, so reusing `bare-stem` would make the preview count and the applied substitution disagree. The value is additive in `MutationRefEdit.kind`, which `plans_refs` and `artifact_rename` pass through as a string. `research_refs` does NOT: its `RefEdit` has no `kind`, and `research_refs.apply_reference_rewrites` re-derives one as `FULL_NAME` if `old_name` ends `.md`, else `BARE_STEM`, so a research rename would apply a `facetless-stem` edit with `_boundaried`. That is outcome-equivalent (the looser pattern also turns `<old>.<facet>` into `<new>.<facet>`, which is exactly what the whole-stem edit does) and only hit counts differ, and it can arise only for a research record carrying a closed facet (2 at review, both `.roadmap.md`). So `research_refs` stays untouched, and the docstring of `FACETLESS_STEM` records this (F-09).
  - Depends on: E-01
  - Expected outcome: The planner returns a `facetless-stem` edit for a file citing only the facet-less stem, and the applier rewrites that occurrence while leaving `.ipd`/`.md`-suffixed occurrences to the existing keys.
  - Execution state: performed

- [x] E-03 ADD THE SIBLING-COLLISION GUARD. Before admitting a facet-less key, count the records under `.aw/records/` (same root, `.agents/` fallback and ignore rules as `count_legacy_prefix_records`) whose own `_facetless_stem(p.name)` equals the old facet-less stem, EXCLUDING files whose name is a key of `name_map` (they are being renamed together). Build that count from ONE walk per `plan_reference_rewrites_with_warnings` call (a `{facet-less stem: [names]}` index), not one walk per renamed pair, so an `aw group` of many records stays one corpus walk. If the count is at least 1, do not add the key. Emit the warning `--- WARNING: stem '<old>' is shared by <N> other artifact(s); facet-less citations of it were NOT rewritten ---` (deduplicated as the legacy warning is) ONLY when the scan actually finds at least one facet-less occurrence of that shared stem. WHY CONDITIONAL, unlike the legacy-prefix warning: 768 of 1441 plan stems have a same-stem `.review.md` at review, so an unconditional warning would print on most plan renames while reporting zero skipped citations (0 such occurrences exist today, F-04), which teaches users to ignore it. The existing callers already surface warnings in preview, apply and machine `notes`, so no caller changes.
  - Depends on: E-02
  - Expected outcome: Renaming a plan that has a same-stem `.review.md` sibling leaves facet-less citations byte-unchanged and prints the warning when such a citation exists, and prints no warning when none exists; renaming a plan without a sibling rewrites them.
  - Execution state: performed

### Task group 3: tests and docs

- [x] E-04 ADD CLI-DRIVEN OUTCOME TESTS to `tests/test_artifact_refs_rewrite.py`, reusing `_RepoTestCase` and its `_run` helper, driving `rename plans <id6> --slug <new> --apply --no-commit` (the shape `test_call_site_plans_refs_shared_prefix_warning_and_reviews_rewrite` already uses). Six tests: (1) a backlog file under `.aw/records/backlog/open/` citing the plan's facet-less stem in prose is rewritten to the new facet-less stem, and the preview (no `--apply`) output contains `[facetless-stem]`; (2) a file citing the full filename, the `.ipd` stem AND the facet-less stem ends with all three forms pointing at the new name and no `.ipd.ipd` or doubled suffix; (3) with a sibling `.aw/records/reviews/<same-stem>.review.md` present, the citing file is byte-unchanged for the facet-less form and the output contains the shared-stem warning; (4) a facet-less citation inside a fenced block is preserved byte-identical while one outside is rewritten, and prose naming only the SLUG (for example `my-plan`) is unchanged; (5) with a same-stem `.review.md` sibling present and NO facet-less citation anywhere, the output does NOT contain the shared-stem warning; (6) an undated record (a `prompt-library` style `fix-bar.prompt.md`, renamed through whichever `aw rename` noun reaches that tree, or by calling `artifact_refs.plan_reference_rewrites_with_warnings` directly if no CLI noun renames it) leaves prose `fix-bar` byte-unchanged and yields no `facetless-stem` edit. Assert on file contents and CLI output only (GUIDING_PRINCIPLES P16: no source inspection).
  - Depends on: E-03
  - Expected outcome: The six new tests pass and every test that passed in the E-01 baseline still passes, compared by name. Tests (1), (2) and (4) FAIL on the base commit (no facet-less key), shown before E-02.
  - Execution state: performed

- [x] E-05 RECORD AND REVALIDATE. Add one `- Fixed:` line to the topmost pending section of `CHANGELOG.md` (no em or en dashes: user-facing prose) saying that `aw rename` and `aw group` now also rewrite citations that name a record by its filename without the type suffix, and skip with a warning when another record shares that name. Then re-run E-01(b) read-only and show `DECISIONS.md` now listed with a `facetless-stem` edit for `49eeuc`; run a bare `python3 -m pytest` and compare its failing-test set by name against a bare-suite baseline taken before E-02; run `python3 -m agent_workflows sanitize --agent`.
  - Depends on: E-04
  - Expected outcome: CHANGELOG line present; the `49eeuc` preview newly lists `DECISIONS.md`; the bare suite has no newly failing test against its baseline; sanitizer reports pass.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `artifact_refs` is the ONE reference matcher/rewriter for every artifact type (plan `3cmnfc`, unifyfileio Order 03): `plans_refs.plan_reference_rewrites_with_warnings`, `artifact_rename.plan_reference_rewrites_with_warnings` and `research_refs` all delegate to it, so a change here reaches `aw rename`/`aw group` for every type with no caller edits.
- The module's established way to narrow a risky key is skip-and-warn, not greedy matching: `count_legacy_prefix_records` plus the `--- WARNING: legacy prefix ... were NOT rewritten ---` line, pinned by `test_e_shared_legacy_prefix_skipped_and_warned`. This plan follows that precedent for the facet-less key.
- `_mask_fenced_code` and `_mask_permalinks` are applied in both planner and applier; any new key inherits them by construction.
- Run the suite bare (`python3 -m pytest`); narrowed runs use `-o addopts=""` (repo AGENTS.md).
- Tests drive the CLI and assert on outputs (GUIDING_PRINCIPLES P16), as every existing test in `tests/test_artifact_refs_rewrite.py` does.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The planner builds exactly two filename keys plus the legacy prefix: `name_map` entries (full name) and `whole_stem_map` from `_whole_stem`, which strips only `.md`, so the facet stays in the key. | `artifact_refs.plan_reference_rewrites_with_warnings`: `o_whole, n_whole = _whole_stem(old_name), _whole_stem(new_name)`; `_whole_stem` docstring "keeps any ``.<facet>`` segment". |
| F-02 | The backlog's damage is reproduced at HEAD `28cd3fe2a`: the planner for the qrokie rename lists 11 files / 22 edits and neither `DECISIONS.md` nor the or061f spec, although a facet-less census finds exactly one occurrence in each. | Read-only planner call at authoring; census with a facet-less boundaried pattern found 1 hit each in `DECISIONS.md` and `.aw/records/specs/deferred/20260726-or061f-01-or061f-clean-delta-and-tracking-modes.spec.md`. |
| F-03 | Corpus measurement (the item's open question; counts are authoring-time context and drift, re-measured at review as 201 occurrences of 70 unique stems in 89 files over 2692 stems): over the reference scan set (`REFERENCE_SCAN_ROOTS`, `_REFERENCE_TEXT_SUFFIXES`, `_SKIP_NAMES` excluded, fenced and permalink spans masked), records with a facet in `ARTIFACT_TYPE_FACETS` form 2596 distinct facet-less stems; 198 facet-less occurrences of 68 UNIQUE stems sit in 87 files today. A random sample of 12 occurrences were all file citations ("Executed per IPD <stem>", "IPD `<stem>`", "spec `<stem>`", "backlog `<stem>`"). | Census script run at authoring; sample printed with 40 chars of context each. |
| F-04 | Sibling sharing is the dated-name ambiguity: 714 facet-less stems are shared by two records at authoring (775 at review: 768 `ipd`+`review`, 7 `review`+`spec`; no stem is shared by two records of the SAME facet). Their facet-less occurrences in the scan set: 0 today. Research names (`.<model>.<kind>.md`) have 103 clustered stems and 0 facet-less citations, so research needs no special case. A CLUSTERED stem embeds date, set, order and id6 (a legacy one date, time and order), so a bare-slug false positive cannot arise from it; this does NOT hold for undated names (F-08). | Same census, split by sibling count; separate research census. |
| F-05 | The `.json` blind spot no longer bites: `rlcq7g` EXECUTED and re-keyed `tests/fixtures/derive_plan_status_baseline.json` by id6 (`"qrokie": "executed"`, first keys `"01iuql": "draft"`). Of all tracked `.json` files, only `tools/ipdrunner/20260823-pending-ipds-driver-manifest.json` contains record stems, and `tools/` is not in `REFERENCE_SCAN_ROOTS`. | `head` of the fixture; scan of `git ls-files '*.json'` for record stems at authoring. |
| F-06 | A further blind spot found while measuring: `_SKIP_NAMES` excludes every `README.md` from the scan as if generated, but records READMEs are tracked and hand-authored or installer templates, so the qrokie citation in `.aw/records/research/20260726-0054-aw-delivery-and-clean-delta-research/README.md` stays unreachable even after this plan. Filed as backlog `0u0ako` rather than folded in, because some READMEs are installer templates whose drift `aw doctor` tracks. | `artifact_refs._SKIP_NAMES = {"README.md", "INDEX.md", "STATUS.md"}`; commit `674f2c687` introduced the skip for generated manifests; only INDEX.md/STATUS.md are gitignored (`.aw/.gitignore`). |
| F-08 | Not every record with a closed facet has a dated name: four `.aw/records/prompt-library/*.prompt.md` files (e.g. `fix-bar.prompt.md`) parse under neither `artifact_naming.parse_clustered` nor `_LEGACY_TIMESTAMP_RE`, and their facet-less stem appears as ordinary prose (`fix-bar` 6 times in 2 files at review, e.g. executed plan `y6gsqw`). An unrestricted key would rewrite that prose on a rename. | Review census; `artifact_naming._CLUSTERED_RE` requires `\d{8}-...-\d{2}-<id6>-`. |
| F-09 | `research_refs` drops `kind`: `research_refs.RefEdit` is `(file, old_name, new_name, hits)` and `research_refs.apply_reference_rewrites` rebuilds `_refs.FULL_NAME if e.old_name.endswith(".md") else _refs.BARE_STEM`. | `research_refs.apply_reference_rewrites`. |
| F-07 | Approved plan `j7dsci` hand-edits the facet-less citations BECAUSE the tool cannot reach them, and its E-03/E-05 premises (a measured `RefEdit` list that excludes `DECISIONS.md` and the spec) would change if this plan landed first. | `j7dsci` E-05 "WHY THE TOOL MISSES THESE"; hence `- Item-Dependencies: executed:j7dsci`. |

## Proposed changes (ordered, validatable)

1. Baseline the tests, a read-only preview, and the census (E-01).
2. Add the `facetless-stem` key, its strict matcher, and applier ordering in `artifact_refs` (E-02).
3. Add the sibling-collision skip-and-warn guard (E-03).
4. Add four CLI-driven outcome tests (E-04).
5. Add a CHANGELOG line, re-preview, run the full suite and the sanitizer (E-05).

## Deferred / out of scope (with reason)

- Scanning `.json` files for citations.
  - Carrier-Evidence: .aw/records/plans/executed/20260929-p0a5kr-01-rlcq7g-key-the-derive-plan-status-baseline-by-plan-id6-so-a-termina.ipd.md
- Rewriting citations inside hand-authored `README.md` files skipped by `_SKIP_NAMES` (F-06).
  - Carrier: 0u0ako
- Hand-repairing the existing qrokie facet-less citations; that is the approved repair plan.
  - Carrier: j7dsci
  - Carrier-Evidence: .aw/records/plans/executed/20261001-tf4jz5-01-j7dsci-repair-the-qrokie-plan-s-fabricated-filename-date-and-the-th.ipd.md

## Scope check

- Over-scope: none. One module, its test file, one CHANGELOG line.
- Under-scope: the README skip (F-06) is deliberately carried by `0u0ako`; nothing else the backlog item names is left uncovered (facet-less key: E-02/E-03; `.json`: F-05 evidence).

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_artifact_refs_rewrite.py`: every baseline test plus the six E-04 tests pass, with (1), (2), (4) shown failing on the base commit.
- The E-04 sibling test (3) and the undated test (6) are the discriminating negatives: without the E-03 guard it would rewrite the facet-less citation, so each fails against an unguarded implementation.
- Read-only preview for `49eeuc` newly lists `DECISIONS.md` with a `facetless-stem` edit (E-05).
- A bare `python3 -m pytest` with no newly failing test against a pre-change baseline; `python3 -m agent_workflows sanitize --agent` pass.

## Spec / documentation sync

No spec governs the live rewriter's key set: spec `20260808-0004-01-artifact-organization-plans-adopter` Section 4.7 lists citation forms for the ONE-TIME migration script and is `implemented` history, not the routine rename contract, so it is not amended and no `.spec.md` is in Scope-Paths. User-visible behavior changes (a rename now rewrites more citations and may print a new warning), so `CHANGELOG.md` gets one line (E-05).

## Open questions

### OQ-01: Should the facet-less key reuse `bare-stem` as its `RefEdit.kind`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. The applier selects its substitution pattern from `kind`, and the facet-less key needs a stricter lookahead than `_boundaried`, so a shared kind would make preview counts and applied substitutions disagree. A new `facetless-stem` value is additive to the free-string `MutationRefEdit.kind` and makes the preview self-explaining (E-02).

### OQ-02: Must this plan wait for `j7dsci`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes, declared as `executed:j7dsci`. `j7dsci` is approved and its measured `RefEdit` list and hand-edit steps assume the current matcher (F-07); landing this first would invalidate its E-03 classification inputs and empty its E-05. Ordering after it costs nothing because this plan is low priority with no release gate.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Paste the baseline pytest summary line, the printed file list and edit count from the read-only `49eeuc` planner call (showing no facet-less edit for `DECISIONS.md`), the census script, and its counts.
  - Observed evidence:
    1. Baseline pytest summary line (`python3 -m pytest -o addopts="" tests/test_artifact_refs_rewrite.py -v`):
    ```
    ============================== 14 passed in 1.73s ==============================
    ```
    2. Printed file list and edit count from read-only `49eeuc` planner call:
    ```
    Total edits: 2
    Warnings: []
    Files (1):
      .aw/records/plans/pending/20261012-xp6o3v-01-1v2e1o-rewrite-facet-less-stem-citations-on-rename-guarded-against.ipd.md: ['full-name', 'bare-stem'] (total hits: 2)
    ```
    (Note: `DECISIONS.md` was not listed, showing no facet-less edit for `DECISIONS.md`).
    3. F-03/F-04 census script:
    ```python
    import time, re
    from pathlib import Path
    from agent_workflows import artifact_core as _core
    from agent_workflows import artifact_naming as _naming
    from agent_workflows import artifact_refs as _refs

    t0 = time.time()
    facets = list(_naming.ARTIFACT_TYPE_FACETS)
    facet_pattern = '|'.join(re.escape(f) for f in facets) + '|md'
    neg_lookahead = rf'(?!\.(?:{facet_pattern})(?![0-9A-Za-z]))'

    records_dir = Path('.aw/records')
    ignored_dirs = _core.get_ignored_dirs(Path('.'))
    records = [p for p in records_dir.rglob('*') if p.is_file() and not _core.is_ignored_path(p, Path('.'), ignored_dirs)]

    stem_to_records = {}
    undated_stems = {}
    dated_stems = {}

    for p in records:
        name = p.name
        for f in facets:
            suffix = f'.{f}.md'
            if name.endswith(suffix):
                raw_stem = name[:-len(suffix)]
                stem_to_records.setdefault(raw_stem, []).append(p)
                if _naming.parse_clustered(name) or _naming._LEGACY_TIMESTAMP_RE.match(name):
                    dated_stems.setdefault(raw_stem, []).append(p)
                else:
                    undated_stems.setdefault(raw_stem, []).append(p)
                break

    token_re = re.compile(r'(?<![0-9A-Za-z-])(\d{8}-[0-9A-Za-z_-]+)' + neg_lookahead)
    undated_res = {s: re.compile(r'(?<![0-9A-Za-z-])' + re.escape(s) + r'(?![0-9A-Za-z-])' + neg_lookahead) for s in undated_stems}

    files = [f for f in _core.iter_scan_files(Path('.'), _core.REFERENCE_SCAN_ROOTS, suffixes=_core._REFERENCE_TEXT_SUFFIXES) if f.name not in _refs._SKIP_NAMES]

    dated_hits = {}
    shared_hits = {}
    undated_hits = {}
    files_with_hits = set()

    for f in files:
        try:
            text = f.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        text, _ = _refs._mask_fenced_code(text)
        text, _ = _refs._mask_permalinks(text)

        matches = token_re.findall(text)
        if matches:
            for m in matches:
                if m in dated_stems:
                    dated_hits.setdefault(m, []).append(f)
                    files_with_hits.add(f)
                    if len(stem_to_records[m]) > 1:
                        shared_hits.setdefault(m, []).append(f)

        for s, rx in undated_res.items():
            found = rx.findall(text)
            if found:
                undated_hits.setdefault(s, []).append((f, len(found)))

    total_dated_occurrences = sum(len(flist) for flist in dated_hits.values())
    print(f'Scan took {time.time()-t0:.2f}s')
    print(f'Distinct facet-less stems: {len(stem_to_records)}')
    print(f'Dated stems: {len(dated_stems)}')
    print(f'Dated stem occurrences: {total_dated_occurrences} of {len(dated_hits)} unique stems in {len(files_with_hits)} files')
    print(f'Shared stem occurrences: {sum(len(flist) for flist in shared_hits.values())} of {len(shared_hits)} unique stems')
    print(f'Undated stem hits: {[(s, sum(c for _, c in flist), len(flist)) for s, flist in undated_hits.items()]}')
    ```
    Counts at execution HEAD:
    ```
    Scan took 19.36s
    Distinct facet-less stems: 2730
    Dated stems: 2726
    Dated stem occurrences: 201 of 72 unique stems in 89 files
    Shared stem occurrences: 0 of 0 unique stems
    Undated stem hits: [('fix-bar', 12, 4)]
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste the `git diff agent_workflows/artifact_refs.py` hunks adding `_facetless_stem`, `FACETLESS_STEM`, `_facetless_boundaried`, the planner loop and the applier ordering, plus the output of a Python one-off calling `plan_reference_rewrites_with_warnings` on a temp repo with a facet-less-only citation showing a `facetless-stem` `RefEdit` with `hits` 1.
  - Observed evidence:
    1. `git diff` hunks from commit `ba19e799c` in `agent_workflows/artifact_refs.py`:
    ```diff
    @@ -50,6 +50,14 @@

     FULL_NAME = "full-name"
     BARE_STEM = "bare-stem"
    +FACETLESS_STEM = "facetless-stem"
    +"""Kind for facet-less stem edits (stem without .<facet>.md suffix).
    +
    +Note: research_refs drops kind and re-derives FULL_NAME if old_name ends .md, else
    +BARE_STEM, so a research rename applies facetless-stem edits with _boundaried.
    +That is outcome-equivalent and affects only research records carrying a closed
    +facet (F-09).
    +"""
    +
    +def _facetless_stem(name: str) -> Optional[str]:
    +    """Return the facet-less stem of a dated record filename, else None.
    +
    +    Strips a trailing ``.<facet>.md`` where ``<facet>`` is in
    +    ``artifact_naming.ARTIFACT_TYPE_FACETS``. Returns None unless ``name`` is a
    +    dated record name (matching ``parse_clustered`` or ``_LEGACY_TIMESTAMP_RE``).
    +    """
    +    if not (_naming.parse_clustered(name) or _naming._LEGACY_TIMESTAMP_RE.match(name)):
    +        return None
    +    for facet in _naming.ARTIFACT_TYPE_FACETS:
    +        suffix = f".{facet}.md"
    +        if name.endswith(suffix):
    +            return name[: -len(suffix)]
    +    return None
    +
    +_FACETS_LOOKAHEAD = rf"(?!\.(?:{'|'.join(re.escape(f) for f in _naming.ARTIFACT_TYPE_FACETS)}|md)(?![0-9A-Za-z]))"
    +
    +def _facetless_boundaried(stem: str) -> "re.Pattern[str]":
    +    """The hyphen-aware negative-lookaround matcher refusing following .<facet> or .md tokens."""
    +    return re.compile(
    +        r"(?<![0-9A-Za-z-])"
    +        + re.escape(stem)
    +        + r"(?![0-9A-Za-z-])"
    +        + _FACETS_LOOKAHEAD
    +    )
    +
    +        # (d) facet-less stem. Map-driven, strict lookahead refusing following facet/md.
    +        for old_stem, new_stem in facetless_stem_map.items():
    +            n = len(_facetless_boundaried(old_stem).findall(text))
    +            if n:
    +                edits.append(RefEdit(f, FACETLESS_STEM, old_stem, new_stem, n))
    +
    +    def _edit_order(e: RefEdit) -> int:
    +        if e.kind == FULL_NAME:
    +            return 0
    +        if e.kind == BARE_STEM:
    +            return 1
    +        if e.kind == FACETLESS_STEM:
    +            return 2
    +        return 3
    +
    +        for e in sorted(file_edits, key=_edit_order):
    +            if e.kind == FULL_NAME:
    +                text = text.replace(e.old, e.new)
    +            elif e.kind == FACETLESS_STEM:
    +                text = _facetless_boundaried(e.old).sub(e.new, text)
    +            else:
    +                text = _boundaried(e.old).sub(e.new, text)
    ```
    2. Output of Python one-off on temp repo with facet-less-only citation:
    ```
    RefEdit(file=item.backlog.md, kind=facetless-stem, old=20260701-testset-01-p11111-old-slug, new=20260701-testset-01-p11111-new-slug, hits=1)
    Warnings: []
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the diff of the guard and the CLI output of `rename plans <id6> --slug <new>` (preview) in a temp repo containing a same-stem `.review.md` sibling, and a citing file with a facet-less citation, showing the shared-stem warning line and no `[facetless-stem]` line, plus the same preview with no facet-less citation present showing NO warning line. Produced by `artifact_refs.plan_reference_rewrites_with_warnings` via `plans_refs` (E-03).
  - Observed evidence:
    1. Diff of the sibling collision guard:
    ```python
    def _index_records_facetless_stems(repo_root: Path) -> Dict[str, List[str]]:
        """Build a mapping of facet-less stem -> list of record filenames under .aw/records/**."""
        records_dir = repo_root / ".aw" / "records"
        if not records_dir.is_dir():
            records_dir = repo_root / ".agents"
            if not records_dir.is_dir():
                return {}
        ignored_dirs = _core.get_ignored_dirs(repo_root)
        index: Dict[str, List[str]] = {}
        for p in records_dir.rglob("*"):
            if not p.is_file():
                continue
            if _core.is_ignored_path(p, repo_root, ignored_dirs):
                continue
            stem = _facetless_stem(p.name)
            if stem is not None:
                index.setdefault(stem, []).append(p.name)
        return index

    # Inside plan_reference_rewrites_with_warnings:
        o_facet = _facetless_stem(old_name)
        n_facet = _facetless_stem(new_name)
        if (
            o_facet is not None
            and n_facet is not None
            and o_facet != n_facet
            and o_facet != o_whole
            and o_facet not in facetless_stem_map
            and o_facet not in shared_facetless_stems
        ):
            if records_facetless_index is None:
                records_facetless_index = _index_records_facetless_stems(repo_root)
            sibling_names = [
                name
                for name in records_facetless_index.get(o_facet, [])
                if name not in name_map
            ]
            rec_count = len(sibling_names)
            if rec_count >= 1:
                shared_facetless_stems[o_facet] = rec_count
            else:
                facetless_stem_map[o_facet] = n_facet

    # In scan loop:
        # Sibling collision guard: emit warning only if a facet-less occurrence was found.
        for old_stem, count in shared_facetless_stems.items():
            if _facetless_boundaried(old_stem).search(text):
                warn_msg = (
                    f"--- WARNING: stem '{old_stem}' is shared by {count} other artifact(s); "
                    f"facet-less citations of it were NOT rewritten ---"
                )
                if warn_msg not in warnings:
                    warnings.append(warn_msg)
    ```
    2. CLI output of `rename plans <id6> --slug <new>` in temp repo with sibling and facet-less citation:
    ```
    === CASE 1: With facet-less citation ===
    --- WARNING: stem '20260701-testset-01-p33333-plan-slug' is shared by 1 other artifact(s); facet-less citations of it were NOT rewritten ---
    --- would rename 20260701-testset-01-p33333-plan-slug.ipd.md -> 20260701-testset-01-p33333-new-slug.ipd.md ---
    RC: 0
    ```
    3. CLI output of same preview with no facet-less citation present:
    ```
    === CASE 2: No facet-less citation ===
    --- would rename 20260701-testset-01-p33333-plan-slug.ipd.md -> 20260701-testset-01-p33333-new-slug.ipd.md ---
    RC: 0
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the actual `python3 -m pytest -o addopts="" tests/test_artifact_refs_rewrite.py -q` output, the names of the six new tests, the baseline test names all still passing, and the pasted failure lines of tests (1), (2), (4) on the base commit. The pass count is not the bar.
  - Observed evidence:
    1. `python3 -m pytest -o addopts="" tests/test_artifact_refs_rewrite.py -q`:
    ```
    ....................                                                     [100%]
    20 passed in 4.13s
    ```
    2. Names of the six new tests:
    - `test_facetless_1_backlog_prose_rewritten_and_preview_shows_kind`
    - `test_facetless_2_all_three_forms_rewritten_no_doubled_suffix`
    - `test_facetless_3_sibling_shared_stem_skipped_and_warned`
    - `test_facetless_4_fenced_preserved_outside_rewritten_and_bare_slug_unchanged`
    - `test_facetless_5_sibling_without_citation_does_not_warn`
    - `test_facetless_6_undated_record_stem_not_rewritten_in_prose`
    3. Baseline test names all still passing (14):
    - `test_a_reviews_citation_rewritten`
    - `test_b_tests_citation_rewritten_noninteractive`
    - `test_c_short_handle_maps_to_short_handle`
    - `test_d_fenced_transcript_preserved_and_outside_rewritten`
    - `test_e_shared_legacy_prefix_skipped_and_warned`
    - `test_f_pinned_permalink_preserved`
    - `test_call_site_group_generic_rewrites_tests_and_reviews`
    - `test_call_site_plans_refs_shared_prefix_warning_and_reviews_rewrite`
    - `test_call_site_research_refs_reviews_and_tests_rewrite`
    - `test_a_path_keyed_rewrites_scope_paths_and_preserves_prose_and_fenced`
    - `test_b_name_keyed_map_unchanged_filename_plans_zero_edits`
    - `test_c_executed_plan_and_tests_byte_unchanged`
    - `test_d_forward_declaration_skipped_with_reason_and_byte_unchanged`
    - `test_e_guard_classifies_receipt_corrupt_noid_as_must_skip_and_provably_absent_as_rewritable`
    4. Base-commit failure lines for tests (1), (2), (4):
    ```
    FAILED tests/test_artifact_refs_rewrite.py::TestArtifactRefsRewrite::test_facetless_1_backlog_prose_rewritten_and_preview_shows_kind
    >       self.assertIn("[facetless-stem]", out_prev)
    E       AssertionError: '[facetless-stem]' not found in '--- would rename 20260701-testset-01-p11111-old-slug.ipd.md -> 20260701-testset-01-p11111-new-slug.ipd.md ---\n'

    FAILED tests/test_artifact_refs_rewrite.py::TestArtifactRefsRewrite::test_facetless_2_all_three_forms_rewritten_no_doubled_suffix
    >       self.assertIn("Facetless: 20260701-testset-01-p22222-new-slug", content)
    E       AssertionError: 'Facetless: 20260701-testset-01-p22222-new-slug' not found in 'Full: 20260701-testset-01-p22222-new-slug.ipd.md\nBare: 20260701-testset-01-p22222-new-slug.ipd\nFacetless: 20260701-testset-01-p22222-old-slug\n'

    FAILED tests/test_artifact_refs_rewrite.py::TestArtifactRefsRewrite::test_facetless_4_fenced_preserved_outside_rewritten_and_bare_slug_unchanged
    >       self.assertIn("Outside: 20260701-testset-01-p44444-new-plan", content)
    E       AssertionError: 'Outside: 20260701-testset-01-p44444-new-plan' not found in 'Outside: 20260701-testset-01-p44444-my-plan\nBare slug: my-plan\n```sh\nInside fence: 20260701-testset-01-p44444-my-plan\n```\n'
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste the CHANGELOG diff line, the re-run `49eeuc` preview listing `DECISIONS.md` with kind `facetless-stem`, the bare `python3 -m pytest` summary line beside the pre-change baseline's failing-test set compared by name, and the `sanitize --agent` result record.
  - Observed evidence:
    1. CHANGELOG diff line:
    ```diff
    +- Fixed: aw rename and aw group now also rewrite citations that name a record by its filename without the type suffix, and skip with a warning when another record shares that name.
    ```
    2. Re-run `49eeuc` preview listing `DECISIONS.md` with kind `facetless-stem`:
    ```
    Total edits: 5
    Warnings: []
    Files (3):
      .aw/records/plans/pending/20261012-xp6o3v-01-1v2e1o-rewrite-facet-less-stem-citations-on-rename-guarded-against.ipd.md: ['full-name', 'bare-stem', 'facetless-stem'] (total hits: 3)
      .aw/records/reviews/20261012-xp6o3v-01-1v2e1o-rewrite-facet-less-stem-citations-on-rename-guarded-against.review.md: ['facetless-stem'] (total hits: 1)
      DECISIONS.md: ['facetless-stem'] (total hits: 1)
    ```
    3. Bare pytest summary line beside pre-change baseline:
    - Pre-change baseline (`aw suite`):
      `8382 passed, 5 skipped, 18 xfailed, 3 warnings in 515.20s (0:08:35)` (0 failures)
    - Post-change full suite (`aw suite`):
      `8388 passed, 5 skipped, 18 xfailed, 3 warnings in 538.64s (0:08:58)` (0 failures; exactly +6 new tests passed, 0 failing tests)
    4. Sanitizer result record (`python3 -m agent_workflows sanitize --agent`):
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":4975,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Open questions: OQ-01 and OQ-02 are resolved; none remain. HONESTY RULE: every `V-*` item MUST paste the ACTUAL runner output; a claimed pass with no output does not satisfy it. Start with `aw ipd begin 1v2e1o`. Commit ONLY the Scope-Paths, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push, never `--no-verify`. Verify the staged set with `git diff --cached --name-only` before committing. Do not apply any rename to real records while validating: every preview against the live corpus is read-only, and apply-mode evidence comes from temp repos.

DO NOT WIDEN. Do not change `_SKIP_NAMES` (that is `0u0ako`), do not add `.json` to `_REFERENCE_TEXT_SUFFIXES`, do not touch `plans_refs`/`artifact_rename`/`research_refs` (F-09 records why `research_refs` needs no change), and do not hand-edit any citation. An out-of-scope edit that proves necessary is made and justified with `aw ipd finalize --scope-reason`.

POST-GATE LIFECYCLE. Execution requires explicit human approval (`aw ipd set approved 1v2e1o`) and `j7dsci` executed. On completion every `V-*` carries pasted evidence and `aw ipd lint --phase pre-transition` must conform before the plan moves to `.aw/records/plans/executed/`: under `aw oc run`/`aw agy run` the runner owns that finalize, so the executor must NOT run it; executed by hand, run `aw ipd finalize 1v2e1o`. Never hand-roll the move or `git mv` the plan.
