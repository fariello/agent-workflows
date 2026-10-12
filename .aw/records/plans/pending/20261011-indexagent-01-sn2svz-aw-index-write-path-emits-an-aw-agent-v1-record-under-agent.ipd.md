# IPD: aw index write path emits an aw.agent/v1 record under --agent and --json for every type

- Date: 2026-10-11
- Kind: child
- Concern: The WRITE path of `aw index <type>` (no `--check`) ignores `--agent` and `--json` for two of its three backends and prints the same human status line it prints to a terminal. MEASURED in this lane at HEAD `8538be828`: `python3 -m agent_workflows index plans --agent` prints `wrote        .aw/records/plans/INDEX.json, INDEX.md (1366 plans)` (and `up to date   ...` on a re-run) and `index plans --json` prints the same line; `index prompts --agent` and `index prompts --json` print `wrote INDEX.json (17 prompts)` and `wrote INDEX.md`. An agent cannot parse either, cannot tell `wrote` from `up to date` structurally, and gets no record at all. `docs/cli-output-contract.md` Section 10 rules "Exactly one canonical machine format (`aw.agent/v1`) is active", the ruling plan `n9ua3b` cited to convert the `--check` branch of the very same three functions. The third backend, `research_index.run_index`, already emits a record on success, but its drift-refusal branch emits `{"outcome":"findings","exit":1,"verified":false,"complete":false,"findings":0}` with NO diagnostics, so a refused regeneration (the live tree's state today: 332 research findings) tells an agent it failed and nothing about why.
- Scope: IN: one shared write-result emitter in `artifact_core` (sibling of `emit_index_check_result`) that builds a `CommandResult` carrying the outcome as `applied` plus per-file `changes`, the scan drift as `diagnostics`, and repo-relative facts in `data`; routing the `--agent`/`--json` branch of `plans_index.run_index`, `prompts_index.run_index` and `research_index.run_index` (both its success and its drift-refusal branch) through it; removing the now-false `index` entry from `tests/conformance_matrix.EXEMPTION_REGISTRY` so the shared conformance sweep covers the leaf; a new behavior test module; a CHANGELOG bullet. OUT, each with a carrier below: the human output of all three verbs (kept byte-identical, including the prompts verb's unconditional `wrote` wording, `vcqobe`); the `FileNotFoundError` traceback when a records directory does not exist yet (`o6cbp7`); `index all`'s one-record-per-type exit-parity violation (`hu2wka`); the absolute `data.repo_root` on the `--check --json` path (`aavf6a`); the unsupported-type case, which already emits a cannot-run record (F-04).
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/plans_index.py, agent_workflows/prompts_index.py, agent_workflows/research_index.py, tests/test_index_write_agent_records.py, tests/conformance_matrix.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 4izduy
- Blocks-Release: next
- Set: indexagent
- Order: 1
- Highest E allocated: 08
- Author: opencode
- Id: sn2svz
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved

- 2026-10-12 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 fixed (silence probe made non-vacuous with --apply; emitter signature carries pre-write existence; scope-fence stop wording replaced with justify-at-finalize; research fixture details pinned)
- 2026-10-12 reviewed (aw set): plan-review revisions applied (PR-001..PR-004)
- 2026-10-12 draft (opencode): created.
- 2026-10-11 to-review (opencode): authored from backlog `4izduy` (inherits `Blocks-Release: next`). Every claim in the item was re-measured at HEAD `8538be828`. Two of its five per-type measurements are STALE and narrow the work: `index specs --agent` and `index backlog --agent` now emit a conforming `kind:error` cannot-run record at exit 2 (F-04), and `index research --agent` now emits a record (F-03), though its refusal branch is diagnostic-free. The item's open design decision (record shape for a mutation verb) is resolved in OQ-01 from repository precedent. Four adjacent defects measured while authoring were filed rather than folded in: `o6cbp7`, `vcqobe`, `hu2wka`, `aavf6a`.

## Goal

Make every `aw index <type>` invocation that is asked for `--agent` or `--json` answer in `aw.agent/v1`, on the write path as it already does on the `--check` path, so an agent can tell structurally what was written, what was already current, and why a regeneration was refused, while every human byte stays the same.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: failing baseline before any production edit

- [ ] E-01 WRITE `tests/test_index_write_agent_records.py` AND SHOW IT RED AT THE BASE COMMIT. Drive the CLI as a subprocess through `tests.conformance_matrix.run_cli(argv, cwd=<fixture>)` against a temp fixture repository (never the live tree). Build the plans and prompts records with `tests.test_index_check_agent_records._create_fixture_repo(root, mode="missing")` and the research record with `tests.test_research_index._write(...)` (the `_create_fixture_repo` research file is NOT recognized by the scanner: measured `(0 docs)`; pass `created` as `YYYYMMDD`, since a dashed date yields `name-invalid` and a refusal, measured at review; `_write` places the doc under `research_contract.RESEARCH_ROOT` = `.agents/docs/research`, which `research_index._roots` resolves in a fixture lacking `.aw/records/research/`, so research `changes` paths are under `.agents/docs/research/`; a doc written with `status="bogus-status"` produces the `frontmatter-invalid` drift the refusal case needs, measured at review), so every count asserted is one the test created; `git init` the fixture so the repo root resolves. For each of `plans`, `prompts`, `research`, assert under `--agent`: (a) stdout is exactly one line that `json.loads` parses, `agent_schema.validate_agent_record` returns `[]`, and its `exit` equals the process exit code; (b) FIRST run (no index files): `applied` is `true`, `changes` lists both `INDEX.json` and `INDEX.md` as repo-relative paths under the type's records dir, and `target` is the type; (c) SECOND run unchanged: `applied` is `false` and no `changes` key; (d) after editing only `INDEX.md` on disk, a third run reports exactly one change, `INDEX.md`; (e) no `\033` and no home-path prefix anywhere in stdout. Assert under `--json`: stdout parses as one JSON document whose `data` carries `target`, `count`, `json_changed`, `md_changed` and no absolute path anywhere in the document. Add two refusal/drift cases: a plans fixture with an extra plan lacking `- Id:` (write still happens, exit 0, record carries a diagnostic with rule `id-missing`), and a research fixture with one frontmatter-invalid doc (exit 1, `outcome` `findings`, `findings` >= 1, a diagnostic naming that doc's repo-relative location and rule `frontmatter-invalid`, and the index files NOT written). Add the HUMAN invariance cases: capture each verb's unflagged stdout on the fixture (first run and second run, `NO_COLOR=1`) as literal expected strings IN THE TEST, matching what the base commit prints today (for prompts that is `wrote INDEX.json (1 prompts)\nwrote INDEX.md\n` on BOTH runs, per `vcqobe`). Add the unsupported-type regression: `index specs --agent` emits a `kind:error` record at exit 2 (passes at base; pins F-04). No static analysis of source (GUIDING_PRINCIPLES P16).
  - Depends on: none
  - Expected outcome: a new module whose plans/prompts agent and json assertions and whose research refusal-diagnostics assertion FAIL at the base commit, while the human-invariance and unsupported-type assertions PASS there.
  - Execution state: pending

### Task group 2: the shared emitter and the three call sites

- [ ] E-02 ADD `artifact_core.emit_index_write_result(args, repo_root, index_dir, *, target, noun, count, json_changed, md_changed, json_existed, md_existed, drift, refused=False)` beside `artifact_core.emit_index_check_result`, reusing its imports (`result_types.CommandResult`, `Diagnostic`, `Change`, `select_output`, `renderers.get_renderer`, `check_engine.enrich_drift` for severity). It builds: `command="index"`, `target=<type>`; `changes` = one `Change(path=<repo-relative index_dir>/INDEX.json|INDEX.md, kind="update" if the file existed before else "create", applied=True)` per changed file, where `json_existed`/`md_existed` are the `Path.exists()` values each caller reads BEFORE its write (the helper cannot recover them afterwards); `applied = json_changed or md_changed` (False when refused); `diagnostics` from `drift` exactly as the check emitter maps them; `summary` the same wording the human line uses minus styling (`wrote ...`, `updated ...`, `up to date ...`, or `refusing to regenerate index: N drift finding(s)`); `data={"target", "count", "noun", "json_changed", "md_changed", "index_dir"}` with `index_dir` REPO-RELATIVE and NO `repo_root` key (do NOT copy the check emitter's absolute `data["repo_root"]`, `aavf6a`); `status="ok"`, `exit_code=0` normally, and `status="findings"`, `exit_code=1`, `verified=True`, `complete=False` when `refused`. It returns `get_renderer(ctx).emit(result, ctx)`. It is called ONLY when `select_output(args)` is agent or json mode; it never renders human output.
  - Depends on: E-01
  - Expected outcome: a helper that, called directly, returns 0 for a normal write and 1 for a refusal, and whose agent record validates.
  - Execution state: pending

- [ ] E-03 ROUTE `plans_index.run_index`'s write path. After the write and before the human print block, if `select_output(args)` is agent or json and not `quiet`, return `_core.emit_index_write_result(...)` with `target="plans"`, `noun="plans"`, `count=len(entries)`, the computed `json_changed`/`md_changed`, the scan `drift`, and `json_existed`/`md_existed` captured before the write. The human branch (drift lines, then the `Term.status_256` line) is left byte-identical; the existing long comment block about the outcome words stays.
  - Depends on: E-02
  - Expected outcome: `index plans --agent`/`--json` emit one record; human output unchanged; exit 0.
  - Execution state: pending

- [ ] E-04 ROUTE `prompts_index.run_index`'s write path the same way (`target="prompts"`, `noun="prompts"`). Leave the two human `print("wrote ...")` lines byte-identical.
  - Depends on: E-02
  - Expected outcome: `index prompts --agent`/`--json` emit one record that distinguishes written from up to date; human output unchanged.
  - Execution state: pending

- [ ] E-05 REPLACE `research_index.run_index`'s two hand-built machine records with the helper: the drift-refusal branch calls it with `refused=True` and the scan `drift` (so the record carries the diagnostics it lacks today), and the success branch calls it with `target="research"`, `noun="docs"`. This changes that record's `cmd` from `research index` to `index` (OQ-01) and moves `docs_count` to `count`; both spellings (`aw index research`, `aw research index`) reach this one function, and `aw research index --check --agent` already reports `cmd: index` (measured). Human branches unchanged.
  - Depends on: E-02
  - Expected outcome: a refused research regeneration emits exit 1 with one diagnostic per drift finding and writes nothing; a successful one emits the shared shape.
  - Execution state: pending

### Task group 3: make the shared sweep cover the leaf, document, and prove nothing else moved

- [ ] E-06 IN `tests/conformance_matrix.py`, DELETE the `"index"` entry of `EXEMPTION_REGISTRY` (its reason, "outputting raw tab-separated lines or index notices rather than an envelope", is false after `n9ua3b` and this plan), update the `# sanctioned_raw (7):` comment to 6, and add `"index": ["plans", "--check"]` to `RUNNABLE_ARGV` so the sweep in `tests/test_agent_surface_conformance.test_agent_surface_conformance` runs it READ-ONLY against the live tree (the sweep's precondition is read-only; the write path is covered by E-01's fixture module instead). Do NOT add any new exemption.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: `index` appears in `UNIVERSE` and its parametrized case passes.
  - Execution state: pending

- [ ] E-07 ADD ONE `CHANGELOG.md` bullet under `## 2.0.0 (pending)`, adjacent to the existing "Changed: the three aw index <type> --check verbs ..." bullet, stating that `aw index <type>` without `--check` now emits one `aw.agent/v1` result record under `--agent` (and a structured document under `--json`) reporting which index files changed, and that a refused research regeneration now lists its findings. User-facing prose: no em or en dashes.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: one new bullet; no other CHANGELOG line changes.
  - Execution state: pending

- [ ] E-08 RUN THE REGRESSION SET. (1) The new module green. (2) Existing modules unchanged and green: `tests/test_plans_index.py`, `tests/test_prompts_index.py`, `tests/test_research_index.py`, `tests/test_research_index_name_fm_mismatch.py`, `tests/test_index_check_agent_records.py`, `tests/test_nv_backend_args_climb.py`, `tests/test_research_rename_frontmatter.py`, `tests/test_rename_group_machine_output.py`, `tests/test_agent_surface_conformance.py`, `tests/test_command_surface_declarations.py`. (3) Internal-caller silence: the in-process callers (`plans_refs.apply_renames`, `research_refs`, `artifact_rename`, `status_set`, `ipd_lifecycle`, `artifact_adopt`, `research_cmd`) pass `quiet=True` with agent/json false; prove they still print nothing by running `aw rename plans <id6> --slug x --apply --agent` on a `_create_fixture_repo` fixture and asserting stdout is exactly one record whose `cmd` is `rename plans`, AND that `INDEX.json`/`INDEX.md` now exist in the fixture's plans dir (proving `run_index` actually ran inside the call). The PREVIEW form is NOT a valid probe: measured at review, `plans_refs.apply_renames` returns before reaching `run_index` on preview, so the fixture's plans dir holds no index files afterwards and the probe would pass even if the silence broke; with `--apply` both index files appear and stdout stays one line. (4) The bare suite `python3 -m pytest` before and after, with the failure-set delta stated as a set and required to be empty. (5) Restore any live-tree `INDEX.md`/`INDEX.json` touched by probing (gitignored, `.aw/.gitignore`), and paste `git status --short` showing only Scope-Paths files.
  - Depends on: E-06, E-07
  - Expected outcome: every listed module green; empty failure-set delta; clean status outside Scope-Paths.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE `--check` PRECEDENT IS THE PATTERN. `artifact_core.emit_index_check_result` (plan `n9ua3b`) already routes all three `run_index` `--check` branches through `get_renderer(select_output(args)).emit(...)`; its record uses `cmd: "index"` and `target: <type>` for all three types. E-02 is its sibling, not a new mechanism.
- MACHINE MODE ONLY. `HumanRenderer.render` produces a banner report unless `data["human_rendered"]` is set (n9ua3b PR-002). This plan sidesteps that entirely by leaving every human branch on its existing print code and calling the helper only when `select_output(args).is_agent or .is_json`.
- `quiet=True` IS HOW INTERNAL CALLERS SILENCE THE VERB. Nine in-process call sites (`plans_refs.apply_renames`, `research_refs`, `artifact_rename` x4, `status_set` x2, `ipd_lifecycle`, `artifact_adopt`, `research_cmd` x2) call `run_index(argparse.Namespace(..., quiet=True))` with agent/json false. The new branch must not emit under `quiet`, or a `rename --agent` would print two records (the problem plan `gzb2rq` fixed).
- THE INDEX FILES ARE GITIGNORED (`.aw/.gitignore` lists `records/plans/INDEX.json` and five siblings), so tests assert on the written file and on stdout, never on git state.
- NO CODE-PINNING TESTS (GUIDING_PRINCIPLES P16): drive the CLI, assert on stdout, exit codes and files.
- BARE SUITE: `python3 -m pytest`, no added flags (repo-local AGENTS.md contract).
- NO EM OR EN DASHES in user-facing prose (CHANGELOG).

## Findings

| id | finding | evidence |
| --- | --- | --- |
| F-01 | `index plans --agent` and `--json` emit the human status line, never a record. | Measured at `8538be828`: `index plans --agent` -> `wrote        .aw/records/plans/INDEX.json, INDEX.md (1366 plans)`, rerun -> `up to date   ...`; `index plans --json` -> `wrote        .aw/records/plans/INDEX.json, INDEX.md (1367 plans)`. Cause: `plans_index.run_index` has no machine branch after the write; it falls to the `Term.status_256` print block (which already forces color off in machine mode, so only the format is wrong). |
| F-02 | `index prompts --agent` and `--json` emit two human lines, never a record. | Measured: `wrote INDEX.json (17 prompts)` / `wrote INDEX.md`, identical under `--json`. `prompts_index.run_index` ends with two bare `print` calls. |
| F-03 | `index research --agent` ALREADY emits a record on success (backlog measurement stale), but its refusal record carries no diagnostics. | Success: `{"cmd":"research index","outcome":"ok","exit":0,"applied":true,...}` (fixture). Live tree: `{"cmd":"research index","outcome":"findings","exit":1,"verified":false,"complete":false,"findings":0,"next":null}` while `index research --check --agent` reports `findings: 332`. `research_index.run_index` builds the refusal `CommandResult` without `diagnostics`. |
| F-04 | The unsupported-type case is ALREADY a cannot-run record (backlog measurement stale). | `index specs --agent` -> `{"kind":"error","cmd":"index specs","outcome":"cannot-run","exit":2,...,"diagnostics":[{"location":"specs","rule":"type-error"}]}`, rc 2; same for `backlog`; `--json` likewise. Produced by `cli._run_noun_verb` after `_nv_resolve_types` fails. Nothing to fix; E-01 pins it. |
| F-05 | A `result` record with `applied`, `changes` and `diagnostics` at exit 0 validates. | Driven: `CommandResult(command="index", status="ok", changes=[Change(..., applied=True)], diagnostics=[...], applied=True).to_agent_record(...)` -> `validate_agent_record` returned `[]`; an `applied: false` `ok` record with `findings: 0` also validates. |
| F-06 | The conformance sweep exempts `index` with a reason that is now false. | `tests/conformance_matrix.EXEMPTION_REGISTRY["index"]` reason: "outputting raw tab-separated lines or index notices rather than an envelope". `--check` emits records since `n9ua3b`; after this plan the write path does too. `research index` is already in `MUTATION_UNIVERSE` (computed). |
| F-07 | `--limit` already works on this verb; no change needed. | Backlog item's own correction, re-confirmed: `index plans --limit 3` rewrote `INDEX.md` and the human line reported `updated ... (INDEX.json up to date; ...)`. |
| F-08 | Four adjacent defects measured, filed, not folded in. | `o6cbp7` (prompts/research `FileNotFoundError` traceback when the records dir is absent); `vcqobe` (prompts human line always says `wrote`); `hu2wka` (`index all --agent` emits one record per type, two of which disagree with the process exit, violating Section 4 exit parity); `aavf6a` (`--check --json` puts the absolute repo path in `data.repo_root`). |
| F-09 | Review re-measurement at HEAD `cec043bab` (fixture repos, no tracked file changed). | `index plans --agent` -> `wrote        .aw/records/plans/INDEX.json, INDEX.md (1 plans)` then `up to date ...`, `--json` the same line; `index prompts --agent`/`--json` -> `wrote INDEX.json (1 prompts)` / `wrote INDEX.md` on every run; `index research --agent` with one `bogus-status` doc -> `{"cmd":"research index","outcome":"findings","exit":1,...,"findings":0}` while `--check --agent` lists `frontmatter-invalid`; a hand-built `CommandResult(command="index", status="findings", exit_code=1, verified=True, complete=False, diagnostics=[...])` validates `[]`; live `index plans --check --agent` exits 1 with record `exit` 1 (parity holds for E-06's sweep case); `rename plans ... --agent` preview leaves no index files, `--apply` writes both and still prints one line. |

## Proposed changes (ordered, validatable)

1. E-01 writes the failing fixture-driven baseline for all three types under `--agent`, `--json` and human output.
2. E-02 adds the shared write-result emitter beside the check emitter.
3. E-03, E-04, E-05 route the three write paths through it, the research one including its refusal branch.
4. E-06 removes the false conformance exemption so the shared sweep covers `index`.
5. E-07 records the change in CHANGELOG.
6. E-08 proves the regression set, internal-caller silence, and an empty full-suite failure delta.

## Deferred / out of scope (with reason)

- The prompts human line printing `wrote` when nothing changed. A human-surface wording change; this plan keeps human bytes identical so its invariance proof stays clean.
  - Carrier: vcqobe
- The `FileNotFoundError` traceback from `index prompts`/`index research` when the records directory does not exist. Needs a create-versus-refuse decision and affects the human path equally.
  - Carrier: o6cbp7
- `index all --agent` emitting one record per type whose `exit` fields disagree with the process exit. Needs an aggregation-shape decision shared by the `--check` and write paths; this plan only makes each per-type record conform.
  - Carrier: hu2wka
- The absolute `data.repo_root` on the `--check --json` record. E-02 deliberately does not copy it; the check emitter is untouched here.
  - Carrier: aavf6a
- `command_surface` declaring `index` as `command_class="read"` with `mutation_gate="dry_run_default"` and `research index` as `dry_run_default`, while both write by default. Declaration metadata, not output; changing the class would move `index` between conformance universes and is not needed for the defect.
  - Carrier-Declined: no user-visible output defect follows from the declaration once the verb emits a conforming record; E-06 brings the leaf under the read sweep it is already classed into, and reclassifying is a taxonomy decision with no measured consequence.

## Scope check

- Over-scope: none. `artifact_core.py` gets E-02's helper; the three index modules get E-03/E-04/E-05; `tests/test_index_write_agent_records.py` is E-01; `tests/conformance_matrix.py` is E-06; `CHANGELOG.md` is E-07. `cli.py`, `result_types.py`, `renderers.py` and `agent_schema.py` are NOT edited (F-04, F-05 show nothing is needed there).
- Under-scope: the risk is the `cmd` change on research's record (E-05) breaking a consumer. Searched: no test or source asserts `"research index"` as a `cmd` value (only `command_surface`'s declaration name, which is the leaf name, not the record field), and the `index` verb is in no released tag (n9ua3b F-02). If a test surfaces at E-08 asserting the old value, update that assertion; if the test file is outside Scope-Paths, make the edit anyway and justify it with `--scope-reason <path>=<why>` at finalize (the fence is a declaration, not a stop condition). Measured at review: `rg '"research index"' tests` finds none, and the mutation sweep case `test_agent_surface_conformance_mutation[research index]` asserts no `cmd` value.

## Required tests / validation

- New module `tests/test_index_write_agent_records.py` (E-01): RED at base for the plans/prompts machine assertions and the research refusal-diagnostics assertion; GREEN after E-05.
- Existing modules listed in E-08 green, unchanged.
- The shared sweep `tests/test_agent_surface_conformance.py` covering `index` after E-06.
- Internal-caller silence probe (E-08 item 3).
- Bare `python3 -m pytest` before and after, empty failure-set delta.
- `aw ipd lint` conforming at `--phase author` now and `--phase pre-transition` before the terminal move.

## Spec / documentation sync

No spec amendment and no `.spec.md` in Scope-Paths, so the run must announce no declared spec edits. The governing text is `docs/cli-output-contract.md` (a normative document, not a spec record): Section 10 already requires `aw.agent/v1` as the only machine format and Section 11.3 already describes `applied`/`changes` for mutations, so the document is made TRUE by this plan rather than amended. Searched `.aw/records/specs/` for `aw index` (four hits: `2lcqno`, `20260818-1525-02`, `20260818-1525-01`, `4sd62s`); none specifies the write-path output bytes. `CHANGELOG.md` gets one bullet (E-07).

## Open questions

### OQ-01: What record shape does the write path emit, and what is its `cmd`

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE. Shape: a single `result` record with `applied` (true iff a file changed), one `changes` entry per changed index file, `diagnostics` for scan drift, and exit 0, or `findings`/exit 1 for research's refusal. This is what `docs/cli-output-contract.md` Section 11.3 prescribes for applied mutations ("emit `applied: true`, `complete: true`, `changes: [...]`"), what the backlog item proposed ("map naturally onto CommandResult.changes plus the 'applied' flag"), and what `research_index.run_index` already emits for the up-to-date case (`applied: false`, F-03), so the three outcomes map as wrote -> two changes, updated -> one change, up to date -> `applied: false` and no changes. `cmd` is `index` with `target: <type>` for all three, matching the `--check` record the same functions already emit (`emit_index_check_result(..., command="index", target=<type>)`); keeping `research index` for one type would give one function two `cmd` values depending on the flag. Exit code on the plans/prompts write path stays 0 even with drift, matching the documented human behavior ("metadata drift ... is reported but does NOT block the write. Use `--check` as the gate", `plans_index.run_index`).
- 2026-10-11 (opencode): resolved at authoring.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Paste the new module's run at the BASE commit (before any production edit) via `python3 -m pytest tests/test_index_write_agent_records.py -o addopts="" -v`, showing each plans/prompts `--agent`/`--json` test and the research refusal-diagnostics test FAILED with its assertion message, and the human-invariance and `index specs --agent` tests PASSED. A summary line alone is not sufficient.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the `git diff` of `agent_workflows/artifact_core.py` showing the new helper, and paste one `--agent` record and one `--json` document it produced for a first-run plans fixture (observed via E-03's call site), showing `cmd: index`, `target: plans`, `applied: true`, two repo-relative `changes`, and a `data` with no `repo_root` key and no absolute path.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste `index plans --agent` output from a fixture on first run, second run, and after editing only `INDEX.md` (three records: two changes, `applied: false`, one change `INDEX.md`), each with `echo rc=$?`; paste the unflagged human output of the same three runs proving byte-identity with the strings E-01 captured.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste `index prompts --agent` first and second run on a fixture showing `applied: true` with two changes and then `applied: false`, plus `index prompts --json` first run, and the unflagged human output proving it still prints `wrote INDEX.json (1 prompts)` / `wrote INDEX.md` on both runs.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste `index research --agent` on a fixture holding one frontmatter-invalid doc showing exit 1, `findings` >= 1 and a diagnostic with that doc's location and rule `frontmatter-invalid`, plus `ls` of the research dir showing no `INDEX.json` was written; paste a successful run's record showing `cmd: index`, `target: research`; paste `research index --agent` on the same fixture showing the identical shape (both spellings reach one function).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Paste the `git diff` of `tests/conformance_matrix.py` (exemption removed, comment count 6, `RUNNABLE_ARGV` entry added) and the output of `python3 -m pytest tests/test_agent_surface_conformance.py -o addopts="" -k "index" -v` showing `test_agent_surface_conformance[index]` PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Paste the `git diff` of `CHANGELOG.md` showing exactly one added bullet and no removed lines, and paste `grep -nP '[\x{2013}\x{2014}]'` over the added line returning nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: Paste the pytest output for the new module and every existing module named in E-08 (all passed, with the `N passed` line); paste the internal-caller silence probe output (`--apply`; exactly one stdout line, a valid `rename plans` record, plus `ls` of the fixture plans dir showing `INDEX.json` and `INDEX.md`); paste the bare `python3 -m pytest` summary lines from before and after with the failure-set delta stated as a set and empty; paste `git status --short` showing only Scope-Paths files plus this plan.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only the paths in `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push. Paste ACTUAL runner output for every test claim. This plan declares no `.spec.md` file, so no spec edit may be made. Verify the staged set with `git diff --cached --name-only` before committing.

ORDER. E-01 must be RED before E-02 lands, or V-01 cannot be produced. E-03, E-04 and E-05 each depend only on E-02 and may run in any order; E-06 must follow all three, because removing the exemption before the write path conforms is harmless (the sweep runs `--check`) but the CHANGELOG and exemption reason would be asserted before they are true.

BOUNDARIES. Do not change any human output byte (that is `vcqobe`'s). Do not touch `artifact_core.emit_index_check_result` (that is `aavf6a`'s). Do not change `cli._run_noun_verb`'s `all` aggregation (that is `hu2wka`'s). Do not create missing records directories (that is `o6cbp7`'s). An out-of-scope edit that proves necessary is made and justified with `aw ipd finalize --scope-reason`, never silently.

POST-GATE LIFECYCLE. After every `E-*` is performed and every `V-*` carries concrete pasted evidence, run `aw ipd lint --phase pre-transition` and require it conforming. In a managed runner lane (`AW_EXECUTION_ROLE=worker`) the runner owns `aw ipd begin`/`aw ipd finalize`; by hand, run `aw ipd begin` before the first edit and `aw ipd finalize` for the terminal move. Never hand-edit status or `git mv` the plan into `executed/`.
