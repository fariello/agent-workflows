# IPD: Give research documents a companion directory that index, mv, set-assign, promote and archive carry along

- Date: 2026-10-12
- Kind: child
- Concern: Backlog `bh1cy5` (research report `l6cbbb` defect D13, second half). The research tree has no convention for non-Markdown companions (CSV ledgers, a zip) of a research document. The observed workaround, a sibling directory `<report-stem>.data/`, is invisible to `aw research index`, is orphaned by `aw research mv` / `set-assign` (which rename only the `.md`), is left behind by `aw research promote` / `aw archive` (which move only the `.md`), and its files surface as `attention.missing-status` violations, so `aw attention` reports `valid: false`. A `.md` file placed inside it is additionally scanned as a malformed research document and makes `aw research index` exit 1.
- Scope: IN: define the companion convention (a sibling directory `<doc-stem>.data/`, where `<doc-stem>` is the document's filename minus `.md`, so it carries the doc's `<id6>` and sorts beside it); one shared contract helper; every research `*.md` walk skips companion contents; `aw research index` lists a doc's companion in `INDEX.json` and `--check` flags an orphaned companion with a registered rule; `mv`/`set-assign` rename the companion with the doc and refuse a colliding destination; `promote`/`archive` move the companion with the doc; `aw attention` does not treat companion files as artifacts; README (template and this repo's copy), installer retired-hash census, spec amendment, CHANGELOG; behavior tests. OUT: an adopt verb for companions (`aw adopt` already covers the Markdown half per the backlog item; companion adoption was not requested); migrating any existing directory (none exists in this repo: `find .aw/records/research -type d -name '*.data'` prints nothing).
- Scope-Paths: agent_workflows/research_contract.py, agent_workflows/selectors.py, agent_workflows/completion.py, agent_workflows/artifact_refs.py, agent_workflows/research_index.py, agent_workflows/research_refs.py, agent_workflows/research_archive.py, agent_workflows/research_cmd.py, agent_workflows/artifact_adopt.py, agent_workflows/attention.py, agent_workflows/check_engine.py, agent_workflows/engine.py, .aw/system/workflows/templates/agents-docs-research-README.md, .aw/records/research/README.md, .aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md, CHANGELOG.md, tests/test_research_companion.py, tests/test_installed_text_current.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: low
- From-Backlog: bh1cy5
- Set: rescomp
- Order: 1
- Highest E allocated: 10
- Author: opencode/claude-opus-5.5
- Id: mtdxiu

## Workflow history
- 2026-10-12 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005. Record: .aw/records/reviews/20261012-rescomp-01-mtdxiu-give-research-documents-a-companion-directory-that-index-mv.review.md Round 1
- 2026-10-12 to-review (aw set): authored from backlog bh1cy5 after reproducing F-01..F-04 in a scratch target at HEAD ad4a07f9f

- 2026-10-12 draft (opencode/claude-opus-5.5): created.

## Goal

A research document can carry non-Markdown companion files in one documented place that every research verb recognizes and carries along, so renaming, regrouping, promoting or archiving a report never orphans its data and the companion never corrupts the index or the attention view.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish

- [ ] E-01 Re-measure at the execution HEAD in a scratch target (temp git repo, `AW_NO_REEXEC=1`, `HOME` pointed at the temp dir, `aw install . -y --preset private-target`): create a report with `aw research new --set probe --kind research-report --slug rep --summary s --apply`, add `<stem>.data/t.csv` and `<stem>.data/notes.md`, then run `aw research index` (exit code), `aw research index --check`, `aw find <id6>` after replacing `notes.md` with a copy of the doc under its own conformant name inside the companion, `aw attention --all --format json` (violations, `valid`), and `aw research mv <id6> --slug renamed --apply` followed by `ls` of the research root. Also re-run `find .aw/records/research -type d -name '*.data'` in this repository (F-08 is a live count). Paste the outputs with the HEAD sha. If every symptom in F-01..F-04 is already gone, record that and stop.
  - Depends on: none
  - Expected outcome: the F-01..F-04 symptoms reproduce (index exit 1 on the inner `notes.md` with `name-invalid`; companion absent from `INDEX.json`; two `attention.missing-status` violations; the `.data/` directory keeps the old stem after `mv`; `aw find <id6>` lists two files for the id6 with the "claimed by 2 files of the SAME type" warning, F-10).
  - Execution state: pending

### Task group 2: the convention

- [ ] E-02 Add the convention to `agent_workflows/research_contract.py`: a constant `COMPANION_SUFFIX = ".data"`, `companion_dir_for(doc_path) -> Path` (sibling `<doc-stem>.data`), and `companion_owner_stem(path, research_root) -> Optional[str]` that returns the owning doc stem when `path` is a companion directory or lies inside one (any path component ending in `.data` whose stem parses with `parse_name(stem + ".md")`). Use it so every research `rglob("*.md")` walk skips companion contents: `research_index._scan_docs`, `research_archive._all_docs`, `research_refs._current_id6s`, `research_cmd._existing_id6s`, `research_cmd._next_order_for_set`, `research_cmd._set_date_for_set`, the `--order` occupancy scan in `research_cmd.plan_new`, and the duplicate scan in `artifact_adopt` (`for p in sorted(Path(root).rglob("*.md"))`). Re-grep `rglob("*.md")` across `agent_workflows/research_*.py` and `agent_workflows/artifact_adopt.py` at execution and cover any walk added since.
  - Depends on: E-01
  - Expected outcome: a `notes.md` (with or without front matter, conformant name or not) inside a companion is never indexed, never minted against, never counted for order/date, and never reported as `name-invalid`; `aw research index` exits 0 in the E-01 scenario.
  - Execution state: pending

- [ ] E-10 Make the TYPE-AGNOSTIC record walks companion-blind for the research type, using the same E-02 helper (no second definition). These walk every records tree including research and so see a `.md` inside a companion as a research record (F-10): `selectors._iter_md` (behind `selectors._iter_paths`/`_iter_files`, which serve `aw find` and every selector resolve), `check_engine._iter_type_files`, the `aw find`/listing walk in `cli.py` over `selectors.record_dirs(...)` (`for p in sorted(base.rglob("*.md"))`), `completion.py`'s id6 walk over `selectors.record_dirs`, and `artifact_refs`'s cross-type `existing` name walk (`for p in d.rglob("*.md")`). In `selectors._iter_md`, prune a companion directory from `dirnames` in place (as `EXCLUDED_RECORD_DIRS` already are) rather than filtering files. Re-grep `rglob("*.md")` and `_iter_md` across `agent_workflows/` at execution and cover any other walk that enumerates research records; out-of-list edits are justified with `--scope-reason`.
  - Depends on: E-02
  - Expected outcome: in the E-01 scenario with a conformantly named copy of the doc inside its companion, `aw find <id6>` lists exactly one file and prints no "claimed by 2 files" warning, and `aw check all` reports no finding for the companion path.
  - Execution state: pending

### Task group 3: index and check

- [ ] E-03 `aw research index` lists companions: add a defaulted trailing field `companion: str = ""` to `research_index.DocEntry`, filled in `_doc_entry` with the companion directory path relative to the research root when `companion_dir_for(p).is_dir()`, so it lands in `INDEX.json` via `_asdict()`. In `research_index.check_drift`, emit a new rule `check.research-companion-orphaned` for every `*.data` directory under the research root (outside ignored dirs) whose owning stem names no document in the SAME directory; when the stem's `<id6>` resolves to a doc elsewhere, the detail names that doc and the recovery names the expected companion path. Register the rule in `check_engine.RULE_REGISTRY` at `warning` severity (so `--check` fails on it, per the backlog item's "--check flags orphans"), `ASSURANCE_REPOSITORY`, `DET_DETERMINISTIC`, and stamp severity at the emitter via `_ce.enrich_drift`, like the neighbouring rules.
  - Depends on: E-02
  - Expected outcome: `INDEX.json` carries `"companion": "<stem>.data"` for a doc with one and `""` otherwise; `aw research index --check` exits 1 naming an orphaned companion and exits 0 once it sits beside its doc; `aw check research` reports the same rule.
  - Execution state: pending

### Task group 4: carry it along

- [ ] E-04 `aw research mv` and `aw research set-assign` carry the companion: in `research_refs._apply_renames`, for each `RenamePlan` whose source has a companion, move `companion_dir_for(old_path)` to `companion_dir_for(new_path)` with `_git_mv` right after the doc, add both paths to `touched`, and add a `MutationTarget(kind="rename")` for it in both the preview and the applied target lists (preview prints `--- would rename <old companion> -> <new name> ---`). BEFORE any move (beside `_refuse_uncontained_destination`), refuse the whole operation with an error naming the path when a destination companion already exists or escapes the research root. Confirm the existing whole-stem reference rewrite already rewrites a citation `<old-stem>.data/t.csv` to `<new-stem>.data/t.csv` (the `_boundaried` lookahead `(?![0-9A-Za-z-])` admits a following `.`); if it does not, extend `plan_reference_rewrites` to cover it.
  - Depends on: E-03
  - Expected outcome: after `mv --slug renamed --apply` and after `set-assign` into another set, the companion sits beside the renamed doc with its files intact, `git status` shows renames, a doc citing `<old-stem>.data/t.csv` now cites the new path, and a pre-existing destination companion makes the verb exit nonzero having moved nothing.
  - Execution state: pending

- [ ] E-05 `aw research promote` and `aw archive` carry the companion: in `research_archive.apply_moves`, after `RF._git_mv` of the doc, move `companion_dir_for(m.old_path)` to `companion_dir_for(m.new_path)` when it exists and append both paths to `touched`; refuse before the first move (no partial application) when a destination companion exists. Show the companion move in the preview paths of `run_promote` and `run_archive` (human and `--agent`/`--json` output).
  - Depends on: E-04
  - Expected outcome: `aw research promote <id6> --to reference --apply` and `aw archive <id6> --apply` leave the companion beside the doc in its shard; the self-commit path list includes the companion paths; previews name the companion.
  - Execution state: pending

- [ ] E-06 `aw attention` stops flagging companion files: in `attention.py`'s scan loop, skip (exclude, not flag) any research-tree file for which `research_contract.companion_owner_stem` returns an owner, with a comment citing this plan; an ORPHANED companion is still policed, by `check.research-companion-orphaned` (E-03), not by attention.
  - Depends on: E-03
  - Expected outcome: in the E-01 scenario `aw attention --check` exits 0 and `--format json` shows no violation for the companion's files.
  - Execution state: pending

### Task group 5: document and pin it

- [ ] E-07 Document the convention: add a `## Companion files` section to `.aw/system/workflows/templates/agents-docs-research-README.md` and to `.aw/records/research/README.md` (user-facing prose, no em or en dashes) stating the `<doc-stem>.data/` shape, that index lists it and `--check` flags an orphan, and that `mv`/`set-assign`/`promote`/`archive` carry it. Because the template changes, append the CURRENT (pre-edit) template's `manifest.hash_content` hash with its commit to `engine.RETIRED_RESEARCH_README_HASHES`, so an upgrade repairs an unmodified installed copy, and extend `tests/test_installed_text_current.py` only if its stale-README fixture needs the new census entry. Add a CHANGELOG entry under the pending 2.0.0 section.
  - Depends on: E-06
  - Expected outcome: both READMEs describe the convention; upgrading a target whose research README is the pre-edit template reports `[overwrite]` and installs the new text; a customized README is still `[preserved]`.
  - Execution state: pending

- [ ] E-08 Amend implemented spec `20260730-2152-01`: add a dated `AMENDED 2026-10-12 (rescomp mtdxiu)` paragraph to Section 5.2 (index lists companions, `--check` flags `check.research-companion-orphaned`), Section 5.6 (`set-assign`/`mv` rename the companion and refuse a collision) and Section 5.7 (archive/promote carry it), stating the `<doc-stem>.data/` convention once in 5.2 and pointing to it from the others; record it with `aw specs note .aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md --message "..."` citing this plan and backlog `bh1cy5`.
  - Depends on: E-07
  - Expected outcome: the three sections agree with the shipped behavior; the spec's workflow history carries the note; `aw specs check` reports no new finding on the spec.
  - Execution state: pending

- [ ] E-09 Add `tests/test_research_companion.py` driving the real CLI (`cli.main` or subprocess) in a temp git repo with `HOME`/`XDG_CONFIG_HOME` isolated as in `tests/test_research_first_order.py` `setUp`, asserting on filenames, `INDEX.json` content, exit codes and git status: (a) index lists the companion and a `.md` inside it is not indexed and does not fail index; (b) `--check` exits 1 on an orphan and 0 once fixed; (c) `mv` carries the companion and rewrites a `<stem>.data/t.csv` citation; (d) `set-assign` carries it; (e) a colliding destination companion makes `mv` exit nonzero and move nothing; (f) `promote --to reference` carries it into the shard; (g) `archive <id6>` carries it; (h) `aw attention --check` exits 0 with a companion present, including a non-Markdown file such as `r.txt` (F-04 also flags those); (j) with a conformantly named copy of the doc inside its companion, `aw find <id6>` lists one file and no duplicate warning (E-10); (i) a conformantly named `.md` with front matter inside a companion does not affect `aw research new` order or id6 minting. Prove (c) can fail by disabling the companion move in `_apply_renames` and pasting the failure, then restore it.
  - Depends on: E-08, E-10
  - Expected outcome: all cases pass; the mutation fails case (c); the existing research, adopt, attention and check-engine tests still pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Research verbs move files with `artifact_core.git_mv` (re-exported as `research_refs._git_mv`), which falls back to `shutil.move` for untracked paths and creates the destination parent; a directory moves through the same call.
- `research_refs._apply_renames` is the single apply path for both `run_set_assign` and `run_mv`; `research_archive.apply_moves` is the single apply path for `run_promote` (both `--suggest` and single) and `run_archive` (targeted and sweep), so two call sites cover all four verbs.
- `research_index.DocEntry` is a `NamedTuple` serialized whole into `INDEX.json` by `build_index_json` (`e._asdict()`); a defaulted trailing field keeps positional construction valid (the `priority`/`has_body` precedent).
- Drift severity comes from `check_engine.RULE_REGISTRY`; `artifact_core.drift_exit_code` exempts only `info`, so a `warning` rule fails `--check`. Rule ids must avoid the substrings `graduation` and `duplicate` (`tests/test_check_engine_spec_criteria.py`).
- The installer repairs a research README only when its hash is in `engine.RETIRED_RESEARCH_README_HASHES` (`classify_records_root_readme`); any other differing text is `user-owned` and preserved, so a template edit must add the old hash to the census.
- An implemented spec may receive a dated amendment recorded with `aw specs note` (precedent: zye6k4 amending Section 5.1 of the same spec).
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | A `.md` inside a companion breaks the index. | scratch target at HEAD `ad4a07f9f`: `<stem>.data/notes.md` with front matter -> `aw research index` prints `notes.md: name-invalid: name must include a '.<kind>' suffix before '.md'`, exit 1, no `INDEX.json` written |
| F-02 | The index does not know companions exist. | same target with only `t.csv`: `INDEX.json` keys are `consumed_by, created, date, has_body, id6, kind, model, order, outcome, path, priority, set_id, status, summary, topic`; `index --check: clean` |
| F-03 | `mv` orphans the companion. | `aw research mv vxanrj --slug renamed --apply` -> research root lists `20261012-probe-01-vxanrj-renamed.research-report.md` beside `20261012-probe-01-vxanrj-rep.research-report.data`; `index --check` still `clean` |
| F-04 | Attention flags companion files. | `aw attention --all --format json` -> `attention.missing-status` "no research frontmatter status" for `<stem>.data/notes.md` and `<stem>.data/r.txt`; `valid False`; `aw attention --check` exit 1 |
| F-05 | promote/archive move only the doc. | `research_archive.apply_moves`: "Move as a tracked rename." then `RF._git_mv(repo_root, src_rel, dst_rel)` on `m.old_path` only |
| F-06 | mv/set-assign move only the doc. | `research_refs._apply_renames`: `_git_mv(repo_root, src_rel, dst_rel)` per `RenamePlan(old_path, new_path)`, no other path |
| F-07 | Every research walk is `*.md`-wide and would see companion Markdown. | `rglob("*.md")` in `research_index._scan_docs`, `research_archive._all_docs`, `research_refs._current_id6s`, `research_cmd` (four walks), `artifact_adopt` duplicate scan |
| F-08 | No companion exists in this repo, so nothing migrates. | `find .aw/records/research -type d -name '*.data'` prints nothing |
| F-10 | The type-agnostic walks see companion Markdown too, so E-02's research-only list is not enough. | scratch target at HEAD `5188004da`, a copy of the doc named `<stem>.md` placed in `<stem>.data/`: `aw research index` -> "wrote ... (2 docs)" exit 0; `aw find 5b1tk3` lists both files and warns "id6 5b1tk3 is claimed by 2 files of the SAME type, in different lifecycle directories". Walks: `selectors._iter_md` ("Walk `base` yielding *.md files"), `check_engine._iter_type_files` (`for p in sorted(d.rglob("*.md"))`), `cli.py` (`for p in sorted(base.rglob("*.md"))` over `selectors.record_dirs`), `completion.py` and `artifact_refs` (`for p in d.rglob("*.md")`) |
| F-09 | The stem-based reference rewrite probably already covers companion paths. | `artifact_refs._boundaried`: `(?<![0-9A-Za-z-])` + stem + `(?![0-9A-Za-z-])`, and `.` is outside the lookahead class (to be confirmed by test (c)) |

## Proposed changes (ordered, validatable)

1. Contract helper and companion-blind research walks (E-02); companion-blind type-agnostic walks, including `aw find` (E-10).
2. Index field and orphan rule (E-03).
3. Rename carry with collision refusal (E-04).
4. Shelf-move carry (E-05).
5. Attention exclusion (E-06).
6. READMEs, installer census, CHANGELOG (E-07); spec amendment (E-08).
7. Behavior tests with mutation proof (E-09).

## Deferred / out of scope (with reason)

- Adopting companion files through `aw adopt`.
  - Carrier-Declined: not requested by backlog `bh1cy5`, whose adopt half is already fixed at HEAD by `lznpv6`; a human places companion files by hand beside an adopted doc.
- Migrating existing companion-like directories.
  - Carrier-Declined: none exist in this repository (F-08); a target with the old `<report-stem>.data/` workaround already matches the convention by construction.

## Scope check

- Over-scope: none. The attention change (E-06) is in scope because without it a documented companion makes `aw attention` invalid (F-04), defeating the convention.
- Under-scope: none known after review (E-10 added the type-agnostic walks, F-10). The shared helper in E-02 is what keeps the walks, the index, the carry and attention agreeing on one definition.

## Required tests / validation

- `tests/test_research_companion.py` (E-09) cases (a) to (j), narrowed run `python3 -m pytest -o addopts="" tests/test_research_companion.py`, with the mutation proof.
- `python3 -m pytest -o addopts="" tests/test_research_index.py tests/test_research_archive.py tests/test_research_cmd_create.py tests/test_research_first_order.py tests/test_research_rename_frontmatter.py tests/test_artifact_adopt.py tests/test_installed_text_current.py tests/test_severity_tier_contract.py tests/test_check_engine.py` passes.
- Bare `python3 -m pytest` summary line pasted before and after.
- `aw research index --check` and `aw check research` in this repo report no new finding.

## Spec / documentation sync

- Spec `20260730-2152-01` Sections 5.2, 5.6, 5.7 amended and noted (E-08). WHY a plan edits an implemented spec: those sections define what `index --check`, `set-assign`/`mv` and archive do, and this plan changes all three; leaving them unedited would make the spec silently contradict the shipped behavior.
- Research README template and this repo's research README gain a companion section; the installer census gains the old template hash; CHANGELOG entry (E-07).

## Open questions

### OQ-01: What exact shape should the companion take?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED from repository evidence: a sibling directory `<doc-stem>.data/`. It is exactly the workaround already used in the field (backlog `bh1cy5`), so such a target needs no migration; it contains the doc's `<id6>`, satisfying the backlog's "sharing the doc's id6"; and it sorts directly beside its doc in a name-sorted tree, the clustering property spec `20260730-2152-01` is built around. The alternative `<id6>.data/` would survive renames without moving but would sort away from its doc and break the field workaround. Reversible: the shape lives in one constant and helper (E-02).

### OQ-02: Should an orphaned companion fail `--check` or only advise?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED as `warning` (fails `--check`): the backlog item asks that `--check` "flags orphans", and an orphan is exactly the data loss the convention exists to prevent. Changing it later is a one-line `RULE_REGISTRY` edit.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the HEAD sha and the actual output of the five E-01 probes (index exit code and message, `INDEX.json` keys, `--check`, attention violations and `valid`, `ls` after `mv`).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: PASTE `git diff agent_workflows/research_contract.py` (the helper) and the E-01 scenario re-run showing `aw research index` exit 0 with `<stem>.data/notes.md` present, plus `INDEX.json` containing exactly one entry for the probe doc.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: PASTE `git diff` of the walk changes, and in the E-01 scenario with a conformantly named doc copy inside the companion, the `aw find <id6>` output (one file, no "claimed by 2 files" line) and `aw check all --agent` showing no diagnostic whose location is under the companion.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: PASTE an `INDEX.json` excerpt showing `"companion": "<stem>.data"` for the doc with one and `"companion": ""` for one without; `aw research index --check` on an orphan (exit 1, rule `check.research-companion-orphaned`, detail naming the owning doc) and after repair (exit 0); `aw check research` showing the same rule.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: PASTE `aw research mv <id6> --slug renamed` preview naming the companion, then `--apply` output, `ls` of the research root, `git status --short` showing the renames, the rewritten `<new-stem>.data/t.csv` citation line, a `set-assign` run carrying the companion, and the collision refusal (exit code nonzero, message, `ls` unchanged).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: PASTE `aw research promote <id6> --to reference` preview naming the companion, the `--apply` output and `ls` of the shard showing doc and companion together, and the same for `aw archive <id6> --apply`.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: PASTE `aw attention --check` exit code (0) and the `--format json` violations list (no companion path) in the E-01 scenario.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: PASTE the README diffs, the added `RETIRED_RESEARCH_README_HASHES` line with its commit, an upgrade run over a pre-edit research README reporting `[overwrite]`, and the CHANGELOG diff.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: PASTE the spec diff of Sections 5.2, 5.6 and 5.7, the `aw specs note` output, and `aw specs check` output for the spec.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: PASTE the narrowed run of `tests/test_research_companion.py` (cases (a) to (j) passing), the mutation failure output for case (c), the listed regression files passing, and the bare `python3 -m pytest` summary line before and after.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one convention, defined once and honored by every verb that walks or moves research documents; splitting the carry from the definition would ship a convention the tools break.

EXECUTION CONTRACT. Execute only after explicit human approval. OQ-01 and OQ-02 are resolved from repository evidence; no question is open. Execute E-items in dependency order (E-10 after E-02). Commit only files changed for this plan through `aw commit mtdxiu -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first, since this is a shared checkout. HONESTY RULE (hard MUST): every `V-*` demands PASTED actual output; run the suite BARE as `python3 -m pytest` and paste the actual summary line; a claim without pasted output satisfies no item. Run every scratch install and `aw` subprocess with `AW_NO_REEXEC=1` and `HOME` pointed at a temp dir. SPEC EDIT: this plan amends implemented spec `20260730-2152-01` (declared in `- Scope-Paths:`, reason in the spec-sync section). SCOPE FENCE: `- Scope-Paths:` is a DECLARATION; an out-of-scope edit (for example another test found pinning the `INDEX.json` key set) is made and then justified at finalize with `--scope-reason`, and a declared path left unmodified is acknowledged with `--scope-ack`. LIFECYCLE, CONDITIONAL OWNERSHIP: under `aw oc run` / `aw agy run` the runner finalizes this plan after its merge-and-revalidate gate, so the executor does not; in a hand execution, the executor fills every `V-*`, confirms `aw ipd lint --phase pre-transition` conforms, and transitions with `aw ipd finalize mtdxiu`, never by a hand `git mv`.
