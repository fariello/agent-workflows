# IPD: Route the research mutating verbs through the one selector resolver

- Date: 2026-09-26
- Kind: child
- Concern: THE RESEARCH MUTATING VERBS BYPASS THE ONE SELECTOR RESOLVER, so the same selector resolves differently per verb. `selectors`'s module docstring states "every verb (`rename`, `group`, `set`/..., `show`, `find`, `archive`, and the per-area set-assign/mv paths) routes selector resolution through `resolve()` here, so the SAME selector resolves to the SAME file for every verb". For research that is false: `research_archive.run_archive` (targeted branch: `if parsed.id6 == target or parsed.set_id == target`), `research_archive.plan_transition` (`if parsed.id6 == id6`), `research_refs._find_by_id6` (used by `plan_set_assign` and `plan_mv`, i.e. `aw group research` and `aw rename research`), and `research_cmd.plan_set_outcome` / `research_cmd.plan_set_priority` each match against the PARSED FILENAME with a private loop, and none of the three modules imports `selectors`. Re-measured at HEAD `61ef21d8`: `aw find research reference` lists 66 documents; `aw archive research reference` prints `no research doc or set matches 'reference'` (exit 0); `aw rename research reference` prints `error: no research file has id6 'reference'`. `selectors.resolve_for_mutation(repo, "research", "reference")` meanwhile returns the ruled refusal `selector 'reference' is ambiguous (status) matching multiple files; pass --force to act on all`, and for setid `awmetastore` returns 7 paths, the same 7 `aw archive research awmetastore` previews today.
- Scope: IN: (a) `research_archive.run_archive`'s targeted branch resolves `target` via `selectors.resolve_for_mutation(repo_root, "research", target, force=...)` and feeds each resolved path into a path-keyed transition planner; (b) `research_archive.plan_transition` gains a path-keyed core (`plan_transition_for_path`) that the id6 entry point and the resolver path both use, so the per-doc rules (research-prompt hot-status refusal, shard target) live once; (c) `research_refs._find_by_id6` resolves through `selectors.resolve_for_mutation` with UNIQUE semantics (exactly one file, or the resolver's refusal), which routes `aw rename research` and `aw group research`; (d) `research_cmd.plan_set_outcome` and `plan_set_priority` resolve their single target the same way; (e) a `--force` flag on `aw archive` (declared on `p_archive` in `cli._build_parser` and in the `archive` `CommandDeclaration.legacy_flags` in `command_surface`), threaded to the resolver; (f) behavioral parity and refusal tests. OUT: the bare age sweep (`sweep_candidates`), which selects by age not selector; `plans_archive`; the resolver's own policy; porting research readers to `artifact_meta` (spec `4sd62s`).
- Scope-Paths: agent_workflows/research_archive.py, agent_workflows/research_refs.py, agent_workflows/research_cmd.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_research_archive.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: mblu3p
- Blocks-Release: next
- Set: researchsel
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: me227c

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog mblu3p. All three symptoms and the resolver's ruled outcomes re-measured at HEAD 61ef21d8; the item's research_cmd line offsets were re-identified by symbol (plan_set_outcome/plan_set_priority), and aw archive was found to have no --force flag.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every research verb that mutates by selector (`archive`, `rename`, `group`, `set-outcome`, `set-priority`) resolve that selector through `selectors.resolve_for_mutation`, so a selector learned from `aw find research` either acts on the same documents or refuses with the resolver's explanation, never a silent no-match.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 RE-MEASURE at the executing HEAD, on the real tree, READ-ONLY (previews only, never `--apply`): paste `aw find research reference | grep -c '^✓'`, `aw archive research reference`, `aw rename research reference`, `aw archive research awmetastore | grep -c 'would archive'`, and for tokens `reference`, `awmetastore`, and one real id6 (e.g. `i5gj61`) the `(kind, len(paths))` of `selectors.resolve(Path('.'), 'research', tok)` and the `(len(paths), error)` of `selectors.resolve_for_mutation`. Also paste `rg -n "^from|^import" agent_workflows/research_archive.py agent_workflows/research_refs.py agent_workflows/research_cmd.py | rg selectors` (expected empty).
  - Depends on: none
  - Expected outcome: find 66 (or the current count), archive and rename report no match; `awmetastore` previews 7 and the resolver returns the same 7; `reference` is `status` kind and `resolve_for_mutation` refuses with the `--force` message.
  - Execution state: pending

### Task group 2: one per-doc planner

- [ ] E-02 FACTOR `research_archive.plan_transition` into a path-keyed core. Add `plan_transition_for_path(research_root, path, new_status)` that reads the doc's parsed name and front matter (the same `R.parse_name` + `R.parse_frontmatter` `_all_docs` uses), applies the existing checks (status in `R.STATUSES`; research-prompt carries no hot status) and returns the `Move`; make `plan_transition(research_root, id6, new_status)` locate the path and delegate. Keep `plan_transition`'s signature and messages so its callers (the sweep branch of `run_archive`, `research_cmd`, tests) are unchanged; list every caller with `rg -n "plan_transition\(" agent_workflows tests` and paste it.
  - Depends on: E-01
  - Expected outcome: existing `TransitionTests`, `TargetedArchiveTests`, `SweepTests`, `PromptArchiveTests` pass unchanged; a path that is not a conformant research doc returns an error rather than a `Move`.
  - Execution state: pending

### Task group 3: route through the resolver

- [ ] E-03 ROUTE `run_archive`'s TARGETED branch through `selectors.resolve_for_mutation(repo_root, "research", target, force=bool(getattr(args, "force", False)))`. On an error, print it as `error: <msg>` and return 2 (a refusal is not the empty result). On success, build one `Move` per resolved path via `plan_transition_for_path(..., "archive")`, skipping (and counting in the preview) a path already in the archive shelf so re-archiving is idempotent, then keep the existing preview/apply/commit-offer flow. The resolver's `no ... artifact matched` case keeps using the existing `Term().empty_result` rendering (exit 0) so a genuine no-match reads as today.
  - Depends on: E-02
  - Expected outcome: id6 and setid targets preview exactly the documents they preview today; a `status` or filename-substring multi-match without `--force` exits 2 with the resolver's ambiguity message; with `--force` it previews every match.
  - Execution state: pending

- [ ] E-04 ADD `--force` TO `aw archive`: register it on `p_archive` in `cli._build_parser` with help mirroring the rename/group `--force` ("act on ALL matches when a status or filename-substring selector is ambiguous; does not override a unique-id collision; a setid needs no force"), and add `"--force"` to the `archive` `CommandDeclaration.legacy_flags` in `command_surface` so the parser/declaration conformance tests stay green. `cli._run_archive` already copies `vars(args)` into the backend namespace, so no dispatch change is needed; confirm by reading it and paste the lines. Plans archive ignores the flag (it does not read it); state that in the help text.
  - Depends on: E-03
  - Expected outcome: `aw archive --help` lists `--force`; `python3 -m pytest tests/test_command_surface*.py -o addopts="" -q` passes.
  - Execution state: pending

- [ ] E-05 ROUTE `research_refs._find_by_id6` through the resolver with UNIQUE semantics: call `selectors.resolve_for_mutation(repo_root, "research", token)` (derive `repo_root` from `research_root` via the existing research-root authority, or pass it in from `run_set_assign`/`run_mv`, which already hold it), return the single path when exactly one resolves, and otherwise return an error string the two planners print (the resolver's own message, or `selector <tok> matched N research files; rename/group target one document per token` for a multi-path setid). Change `plan_set_assign`/`plan_mv` to propagate that message instead of the fixed `no research file has id6` text. Keep `_find_by_id6` returning a path for a plain id6 so its behavior for the common case is unchanged.
  - Depends on: E-01
  - Expected outcome: `aw rename research <id6>` behaves as today; `aw rename research reference` refuses with the resolver's status-ambiguity message instead of `no research file has id6`; a path selector to a research doc now works.
  - Execution state: pending

- [ ] E-06 ROUTE `research_cmd.plan_set_outcome` and `plan_set_priority` target lookup through the same unique helper as E-05 (import it from `research_refs`, or add a shared `_resolve_one_research` in `research_archive` that both modules import, whichever keeps the import graph acyclic; paste `python3 -c "import agent_workflows.research_cmd, agent_workflows.research_refs, agent_workflows.research_archive"` succeeding).
  - Depends on: E-05
  - Expected outcome: `aw research set-outcome <id6>` behaves as today; a non-unique selector refuses with the resolver's message.
  - Execution state: pending

### Task group 4: prove it

- [ ] E-07 ADD BEHAVIORAL TESTS to `tests/test_research_archive.py` on a temp git repo built with the existing `_write_doc` helper: two sets (`alpha` with 3 docs, `beta` with 2), mixed statuses (at least two docs `reference`, one `active`), all under `R.RESEARCH_ROOT`. (1) PARITY: for an id6, the setid `alpha`, and a repo-relative path token, the set of paths `selectors.resolve(root, "research", tok).paths` equals the set of `old_path`s `run_archive` previews (capture stdout, or call the planning step directly if E-03 exposes one); (2) STATUS REFUSAL: `run_archive(target="reference", apply=False)` returns 2 and prints `ambiguous (status)` and `--force`; with `force=True` it previews exactly the two `reference` docs; (3) NO-MATCH: an unknown token returns 0 with the empty-result text, unchanged; (4) APPLY via setid moves exactly the `alpha` docs into the archive shelf and nothing else; (5) RENAME: `research_refs.plan_mv(root, "reference")` (or `run_mv` with `id="reference"`) refuses with the resolver's message, and `plan_mv` with a path token resolves the doc; (6) SET-OUTCOME: `research_cmd.plan_set_outcome(rroot, "reference", ...)` refuses with the resolver's message. Update the call signatures in existing tests ONLY if E-05/E-06 changed a planner's parameters.
  - Depends on: E-03, E-04, E-05, E-06
  - Expected outcome: all pass; (1) for the path token, (2), (5) and (6) FAIL against the pre-change code; (1) for id6/setid, (3) and (4) pass before and after (they pin preserved behavior).
  - Execution state: pending

- [ ] E-08 RUN THE BARE SUITE `python3 -m pytest` before and after and compare failing node IDs; then re-run E-01's commands (previews only).
  - Depends on: E-07
  - Expected outcome: the after-minus-before failing node set is empty; `aw archive research reference` now refuses with the ambiguity message (exit 2); `aw archive research awmetastore` still previews 7.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `selectors.resolve_for_mutation` is the ruled mutation policy (OQ-01 of IPD `laykok`, resolved by human): setid multi-match acts on all with no `--force`; a unique-kind (path/id6/stem) collision always refuses; a substring (and, as measured, status) multi-match refuses unless `--force`. `artifact_rename.run_rename` already applies it for the generic types.
- The rename/group parsers already carry a `--force` flag with that meaning (`cli._build_parser`, "IPD laykok E-07"); `aw archive` does not, so adding it is required for the policy's escape hatch to exist on archive.
- `command_surface.CommandDeclaration.legacy_flags` declares each command's accepted flags and is checked by conformance tests, so a new flag is declared there too.
- `research_archive.plan_transition` is the one place per-doc archive rules live (research-prompt hot-status refusal, shard path); routing through the resolver must not fork those rules, hence E-02.
- Tests exercise behavior (maintainer ruling 2026-09-26: no source-text or structure pins, so no test asserts that a module imports `selectors`). Suites run BARE as `python3 -m pytest`; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `61ef21d8`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `research_archive.run_archive` targeted branch | Filename-only id6/setid match; status/path/stem/substring selectors silently no-match. | `aw find research reference` -> 66 rows; `aw archive research reference` -> `no research doc or set matches 'reference'`. |
| F-2 | HIGH | `research_refs._find_by_id6` (rename/group) | Same bypass; message claims the token is an id6. | `aw rename research reference` -> `error: no research file has id6 'reference'`. |
| F-3 | MEDIUM | `research_cmd.plan_set_outcome`, `plan_set_priority` | Two further private loops matching `parsed.id6 == id6`; these are the functions behind the backlog item's `research_cmd.py:473`/`:598` offsets, re-identified by symbol. | `rg -n "parsed.id6 == " agent_workflows/research_cmd.py` -> two hits, in those functions. |
| F-4 | MEDIUM | `cli._build_parser` `p_archive` | `aw archive` has no `--force`, so the resolver's documented override for a status/substring multi-match would be unreachable. | `p_archive` arguments: `type_or_target`, `target`, `--age`, `--dir`, `--keep`, `--apply`, commit flags. |
| F-5 | INFO | resolver outcomes the fix will adopt | `resolve_for_mutation(".", "research", ...)`: `reference` -> refused (status ambiguity, `--force`); `awmetastore` -> 7 paths, equal to today's archive preview of 7; `i5gj61` -> 1 path. | Measured directly. |
| F-6 | INFO | backlog `mblu3p`'s honest scope note | Routing through the resolver changes what `aw archive research archive` does (32 docs match status `archive`); under the ruled policy it now REFUSES without `--force` rather than moving 32 documents, so the widening the item warns about requires an explicit `--force`. | `resolve_for_mutation(".", "research", "archive")` -> refused, 32 candidates. |

## Proposed changes (ordered, validatable)

1. E-01 reproduces.
2. E-02 factors a path-keyed per-doc planner.
3. E-03 routes targeted archive through the resolver; E-04 adds `--force`.
4. E-05 routes rename/group; E-06 routes set-outcome/set-priority.
5. E-07 adds parity and refusal tests; E-08 runs the suite and re-measures.

## Deferred / out of scope (with reason)

- Porting research readers onto `artifact_meta`.
  - Carrier-Declined: owned by spec 4sd62s (routes research readers through artifact_meta); a spec is not an accepted carrier type.
  - Rationale: that spec routes research readers through the metadata store later; landing this first leaves exactly one resolver for it to port instead of five private loops.
- Changing the bare age sweep.
  - Carrier-Declined: it selects by age and citation, not by selector, so the single-resolver claim does not govern it.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/selectors.py` is READ and not modified; if E-05 needs the repo root and no existing authority derives it from `research_root`, thread it from the callers rather than editing `selectors`.
- Scope-Paths justification: the three research modules hold the bypasses; `cli.py` and `command_surface.py` hold the `--force` registration and declaration; `tests/test_research_archive.py` holds the existing archive fixtures (`rg -l run_archive tests` -> `tests/test_research_archive.py`, `tests/test_plans_archive.py`; the latter is the plans backend and is not touched).

## Required tests / validation

- New behavioral cases in `tests/test_research_archive.py` (E-07), with the path-token parity, status refusal, rename refusal and set-outcome refusal shown FAILING before the change and the id6/setid/no-match/apply cases passing before and after.
- `tests/test_command_surface*.py` green after E-04.
- Bare `python3 -m pytest` before and after; E-01 re-run in preview.

## Spec / documentation sync

- N/A for specs: this makes the code match the claim already stated in `selectors`'s module docstring and the ruled `resolve_for_mutation` policy; no spec text changes, and no `.spec.md` is in `- Scope-Paths:`.
- The `aw archive` epilog gains nothing beyond the `--force` help line; no README change.

## Open questions

### OQ-01: Should a status selector on `aw archive` act on all matches (like setid) or refuse without `--force`?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: Refuse without `--force`, from repository evidence: that is the human-ruled policy `resolve_for_mutation` already implements (IPD `laykok` OQ-01) and applies to every other type's mutating verbs; measured F-5/F-6 show it returns exactly that refusal for `reference` and `archive`. Adopting the shared policy is the point of the fix, and it answers backlog `mblu3p`'s warning that routing would make `aw archive research archive` start relocating 32 documents: it will not, without an explicit `--force`.

### OQ-02: Does this change what id6 and setid targets archive today?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: No, for conformant documents: measured F-5 (`awmetastore` 7 = 7; `i5gj61` 1). The one intended difference is that the resolver reads the DECLARED `id:` rather than the filename slot (backlog `mblu3p` consequence 2), which E-07 case (1) pins as parity with `aw find`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste every E-01 command's output with the HEAD hash.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of `plan_transition`/`plan_transition_for_path`, the `rg -n "plan_transition\("` caller list, and a narrowed run of `tests/test_research_archive.py` passing before any other change.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff of `run_archive`'s targeted branch and, on the E-07 fixture, the preview output for an id6, a setid, `reference` without and with `--force`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `aw archive --help` lines showing `--force`, the `legacy_flags` diff, the `_run_archive` lines showing `vars(args)` is copied, and the command-surface tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the diff of `_find_by_id6`/`plan_set_assign`/`plan_mv` and the output of `aw rename research reference` (refusal text) and of a path-token rename preview on the fixture.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the diff of `plan_set_outcome`/`plan_set_priority`, the three-module import succeeding, and a refusal from `plan_set_outcome` for a status token.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest tests/test_research_archive.py -o addopts="" -q` passing with its count; then the same with the E-03 to E-06 hunks temporarily reverted, showing the four named cases FAILING and the preserved-behavior cases passing; then passing again after restoring.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the bare `python3 -m pytest` summary BEFORE and AFTER, the after-minus-before failing node-ID set (must be empty), and the E-01 previews re-run after the change.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. `aw archive`, `aw rename`, `aw group`, and `aw research set-outcome`/`set-priority` for research resolve their selector the same way `aw find research` does. id6 and setid targets do what they do today. A selector that matches several documents by status or filename fragment now REFUSES with an explanation and a `--force` hint instead of silently matching nothing; `aw archive` gains that `--force` flag. This is the widening backlog `mblu3p` flagged, delivered under the existing human-ruled policy, so nothing moves in bulk without `--force`. This graduates backlog `mblu3p` and inherits its `- Blocks-Release: next`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the three research modules, `cli.py` (`p_archive` `--force` only), `command_surface.py` (the `archive` declaration's `legacy_flags` only), and `tests/test_research_archive.py`. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-07 must show the new tests FAILING before the change. NEVER run `aw archive ... --apply`, `aw rename ... --apply` or `aw group ... --apply` against the real `.aw/records/research/` tree while executing this plan: every applied test uses a temp repo.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `mblu3p` `done` with `--evidence` citing the executed plan; its release gate is preserved by that handoff.
