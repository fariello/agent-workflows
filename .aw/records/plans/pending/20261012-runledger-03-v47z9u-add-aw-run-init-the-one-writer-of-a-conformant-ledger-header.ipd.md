# IPD: Add aw run init: the one writer of a conformant ledger header record, at the runs-root ledger location

- Date: 2026-10-12
- Kind: child
- Concern: Nothing in the package can create a run ledger. `RunLedgerStore.append` refuses any ledger whose first record is not `kind: "run"` (finding `RL-E041`, "first ledger record must be kind 'run'"), and `run_ledger_schema.validate_records` enforces the same on read, but no code under `agent_workflows/` writes such a record: every occurrence is a reader or a refusal. So the whole `aw run` write surface (`start`, `record`, `cancel`, `finalize`) and the ledger readers (`aw runs status|next|resume|show|evidence|verify-ledger`) are unreachable for an operator; only tests create a ledger, by appending the header themselves (`tests/test_run_recovery_cli.py` `_run_record`). Backlog `hegwri`.
- Scope: (1) Add `aw run init`, which creates a new run ledger at `runner_shared.state_root(repo) / <run-id> / ledger.jsonl` and writes exactly one conformant `kind: "run"` header record through `RunLedgerStore.append`, from a `--workflow` file. (2) Record the storage location decision in spec `25kzda` Section 6.2 (the "durable storage location for run ledgers" bullet). (3) Behavior tests. OUT, each carried by its own backlog item: writing `requirement_set` / `verifier_decision` records (`8l1hgw`), persisting the workflow beside the ledger (`sflov4`), the runs viewer's rendering of a ledger-only directory (`nf84rt`), conformance-harness rows for the ledger leaves (`a4tjxc`), and reconciling spec `25kzda` 1.2 step 8 and 5.1 with the `rdjka2` decision (`66ls4r`). Driver runs (`aw oc run` / `aw agy run`) keep `state.json` / `events.jsonl` and do not write a ledger (`rdjka2` option (b), decision record `utb2qr`).
- Scope-Paths: agent_workflows/run_cli.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_run_init.py, tests/test_usage_refusal_agent_record.py, tests/test_completion.py, tests/test_exit_vocabulary_boundary.py, docs/cli-output-contract.md, CHANGELOG.md, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: hegwri
- Set: runledger
- Order: 3
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: v47z9u
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008, PR-009
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): completed by hand at the maintainer's direction. The authoring turn in run-20261012T005641Z-2321995 created this skeleton and filed carriers 66ls4r, 8l1hgw, a4tjxc, nf84rt and sflov4, then its host session timed out ("UnknownError: The operation timed out.") before writing the body; the skeleton reached main via 95a7b41db. Body written from that session's recorded measurements, re-checked against main at 34b6e3a10.
- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

An operator can create a run ledger with one command and then use `aw run start` / `record` and the `aw runs` readers on it, which today is impossible outside the test suite.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: reproduce

- [ ] E-01 REPRODUCE at execution HEAD. In a scratch git repo that contains an `.aw/records/` directory (without it, `runner_shared.state_root` resolves to the home-scoped projects tree, see F-08): (a) build `run_ledger_store.RunLedgerStore` over a fresh path and append a `step_attempt`-shaped record; expect `SchemaInvalidRecordError` with `RL-E041` and no file left on disk; (b) run `aw run start run-abcdef1234 --step S-01`; expect exit 2 with the ledger-not-found message ("no driver run writes one today"); (c) search `agent_workflows/` for a writer of a `"kind": "run"` record and paste the result (zero writers expected). If any of these has changed, stop and report the plan as overtaken with the contradicting output.
  - Depends on: none
  - Expected outcome: three pasted outputs confirming no ledger can be created.
  - Execution state: pending

### Task group 2: the writer

- [ ] E-02 Register the leaf. Add `aw run init` on the `run_sub` group in `cli.py` (the WRITING noun, NOT `runs_sub`; do not add it to `run_viewer.RUNS_VIEWER_LEAF_NAMES`). It must NOT go through `_register_run_leaf` unchanged, because that helper unconditionally adds a required `target` positional and `init` has no existing target: register it with its own `add_parser("init", parents=[common], ...)` (or give `_register_run_leaf` an opt-out), with `--workflow PATH` (`required=True`), optional `--run-id`, `--dir`/`--repo` (`dest="dir"`, `default=None`, matching the other `run` leaves), and the shared output flags from `common` (`--agent`, `--json`). Add `"init"` to the `run_cli.run_cli` dispatcher (and its usage string) routing to a new `_run_init` handler, and add `init` to the `aw run` help text and EXAMPLES epilog. Add a `CommandDeclaration(command="run init", command_class="mutation", human_recipe="status", agent_record_kind="result", mutation_gate="none", empty_error_renderer="renderer_boundary", legacy_flags=("--workflow", "--run-id", "--agent", "--json"), exit_contract=(0, 2, 6))` to `command_surface.COMMAND_INVENTORY`.
  - Depends on: E-01
  - Expected outcome: `aw run init --help` exits 0 and lists `--workflow`, `--run-id`, `--dir`, `--agent`, `--json`; `aw run init --agent` with no `--workflow` exits 2 with a `cannot-run` record; `tests/test_conformance_matrix_structure.py` and `tests/test_command_surface_declarations.py` pass.
  - Execution state: pending

- [ ] E-08 Reconcile the census and contract tests a new leaf trips (F-10), each by recording the new truth, never by weakening the check. (a) Exit 6 is outside {0, 1, 2}: add a `"run init"` entry with its reason to `OUT_OF_RANGE_DECLARATION_ALLOWLIST` in `tests/test_exit_vocabulary_boundary.py`. (b) `--workflow` is required, so `tests/test_usage_refusal_agent_record.py` discovers `run init` as a new required-argument leaf: update its pinned `len(REQUIRED_LEAVES)` to the value measured at execution HEAD plus one (re-derive the base; do not assume 67). (c) `aw run <TAB>` completion is pinned exactly: add `"init"` to the `["as", "cancel", "finalize", "ipd", "record", "start"]` expectation in `tests/test_completion.py` (the "WRITING noun's own first slot" case).
  - Depends on: E-02
  - Expected outcome: `tests/test_usage_refusal_agent_record.py`, `tests/test_completion.py`, `tests/test_exit_vocabulary_boundary.py`, `tests/test_agent_surface_conformance.py` and `tests/test_shared_flag_honored.py` pass.
  - Execution state: pending

- [ ] E-03 Build and append the header. In `run_cli._run_init`: resolve `repo = resolve_verb_repo_root(args.dir)` (the same resolver `_resolve_or_error` uses, so init writes where the readers look); load the workflow with `_load_workflow_arg`; default the run id to `"run-" + secrets.token_hex(8)` (16 hex, satisfies `run_ledger_schema.is_run_id`; deliberately NOT `runner_shared.new_run_id`, whose `run-<UTC stamp>-<pid>` shape fails `_RUN_ID_RE`); compute `workflow_digest` as `run_ledger_store.compute_record_hash(workflow)` (the canonical `sort_keys=True, separators=(",", ":")` SHA-256 already in the store; sibling `o34rb3` reuses the same function, so do not hand-roll a second canonicalizer) and `requirement_digest` as `compute_record_hash` over `workflow.get("requirements", [])` (a placeholder digest of the workflow's list, NOT the `run_freeze` set digest; sibling `um0twl` E-02 replaces it with `frozen.requirement_digest`); take `repo` from `repo.name` and `head` from `run_evidence.get_git_head(repo)` (the existing helper, which returns `"unversioned"` outside git rather than raising); set the common envelope (`schema_version` = `run_ledger_schema.LEDGER_SCHEMA_VERSION`, `kind: "run"`, `run_id`, `actor: "runtime"`, `parent: ""`); and append through `RunLedgerStore.append` at `state_root(repo) / <run-id> / store.LEDGER_FILENAME`, so the store assigns `seq`, `timestamp`, `prev_hash` and creates the parent directory. Human mode prints the run id and the ledger path. Machine mode: `--agent` emits exactly one `aw.agent/v1` `result` record (`schema`, `kind: "result"`, `cmd: "run init"`, `exit: 0`, `outcome: "ok"`, `verified: true`, `complete: true`, plus `run_id` and `ledger` as a repo-relative path via `agent_schema.normalize_repo_path(ledger, repo)`), rendered through `agent_schema.render_guarded_jsonl_record` so it is schema-checked; `--json` emits the same fields as one pretty JSON object. This is a deliberate departure from the module's bare-dict `_emit_machine` payloads (see `_emit_error` docstring F-16): it is a NEW leaf with no existing consumer, and sibling `g5s94t` puts it in `MUTATION_UNIVERSE`, whose test (`test_agent_surface_conformance_mutation`) requires a valid `aw.agent/v1` terminal record and exit parity. Refusals (E-04) keep the module's `_emit_error` shape; the exit-6 refusal therefore cannot be an `aw.agent/v1` record (that schema admits only exit 0..2), which is consistent with every other `run` leaf.
  - Depends on: E-02
  - Expected outcome: `aw run init --workflow wf.json` in a scratch repo with `.aw/records/` writes `.aw/records/runs/<id>/ledger.jsonl` containing one record that `run_ledger_schema.validate_records` accepts; `aw run start <id> --step S-01 --workflow wf.json` then exits 0; `aw run init --workflow wf.json --agent` stdout is one line that `agent_schema.validate_agent_record` accepts with no errors and contains no absolute path.
  - Execution state: pending

- [ ] E-04 Refuse bad input without writing. Validate everything BEFORE any filesystem write: exit 2 (`EXIT_INVALID_INVOCATION`) for a malformed `--run-id` (fails `run_ledger_schema.is_run_id`, which also rejects path separators and `..`, so the id cannot escape the runs root), a missing workflow file, invalid JSON, or JSON whose top level is not an object (`_load_workflow_arg` returns `None` for a non-dict; treat `None` as a refusal, never as an empty workflow). Exit 6 (`EXIT_OPERATIONAL`) when the target directory `state_root(repo) / <run-id>` already exists (not only when `ledger.jsonl` exists, so a pre-existing driver run directory of the same name is never written into). Make the existence check race-safe: reserve the directory with `mkdir(parents=True, exist_ok=False)` and map `FileExistsError` to exit 6, the same atomic reservation `runner_shared.mint_run_dir` uses; if the subsequent append raises, remove the directory you just created so a failed init leaves nothing behind. Emit every refusal through `_emit_error`.
  - Depends on: E-03
  - Expected outcome: each refusal leaves the filesystem byte-for-byte unchanged (no run directory, no `ledger.jsonl`, no `.lock`), and a second init of an existing id exits 6 with the ledger unchanged.
  - Execution state: pending

### Task group 3: prove and document

- [ ] E-05 Add `tests/test_run_init.py`, driving the CLI as a subprocess (`tests.support.pinned_env`) in a scratch git repo created under `tmp_path` that CONTAINS `.aw/records/` (so `state_root` resolves inside the scratch repo and the test never writes the real home-scoped projects tree, F-08), asserting on exit codes, output, and the ledger file, never on source text. Cases: (a) init creates exactly one record at `state_root(repo)/<id>/ledger.jsonl`, `validate_records` accepts it, its `run_id` equals the printed id, and its `workflow_digest` equals `run_ledger_store.compute_record_hash` of the workflow; (b) the follow-on sequence: `aw run start <id> --step S-01 --workflow wf.json` exit 0, `aw run record <id> --step S-01 --state performed --workflow wf.json` exit 0, `aw runs status <id> --workflow wf.json` output contains `S-01: performed` (exit 1, run still incomplete), and `aw runs verify-ledger <id>` output contains `Hash Chain: CLEAN` (exit 1, completion UNSATISFIED with "no frozen requirements defined", which is backlog `8l1hgw`'s; assert it as current behavior); (c) a second init with the same `--run-id` exits 6 and leaves the ledger byte-identical; (d) malformed `--run-id` (including `../x`), missing workflow, invalid JSON, and a JSON array each exit 2 and leave `state_root(repo)` with no new entry; (e) the default id matches `^run-[0-9a-f]{16}$` and two default inits produce distinct ids; (f) `--agent` emits exactly one line that `agent_schema.validate_agent_record` accepts, naming the id and a repo-relative ledger path, and `--json` emits one parseable object with the same id; (g) `--dir <scratch>` run from a different cwd writes under the `--dir` repo. Show (a) and (b) failing on the base commit (no such leaf: argparse `invalid choice: 'init'`, exit 2).
  - Depends on: E-04
  - Expected outcome: the new module passes; (a) and (b) shown failing before the change.
  - Execution state: pending

- [ ] E-06 Record the location decision in spec `25kzda` Section 6.2: replace the bullet "the durable storage location for run ledgers and large captured outputs" with the decided ledger location (`<runs root>/<run-id>/ledger.jsonl`, the runs root being `runner_shared.state_root`, which follows the configured records backend and is gitignored, so a ledger is box-local and not committed) and keep "large captured outputs" listed as still open. Note the decision as an in-place dated amendment in the bullet (the execution date, then "decided by plan `v47z9u`, backlog `hegwri`"), and append a `## Workflow history` entry with `aw specs note <spec path> --message "..."` (the convention sibling `9epp40` E-03 also follows). Leave Sections 1.2 step 8 and 5.1 unchanged (backlog `66ls4r`, owned by sibling plan `9epp40`).
  - Depends on: E-05
  - Expected outcome: the 6.2 diff and the new history line, with 1.2 and 5.1 untouched; `aw specs check` exits 0.
  - Execution state: pending

- [ ] E-07 Document and verify. In `docs/cli-output-contract.md` Section 3.1 table 1, add `run init` to the code `2` and code `6` parentheticals (it returns 0, 2, 6), and add one sentence stating that `aw run init` is the one `run`-family leaf whose SUCCESS `--agent` output is an `aw.agent/v1` record while its refusals keep the family's bare-JSON shape. Add a CHANGELOG line under Unreleased (no em or en dashes in either). Run the bare suite and paste its summary line.
  - Depends on: E-06
  - Expected outcome: the doc and CHANGELOG diffs and a green bare suite.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Suite BARE as `python3 -m pytest`; narrowed runs `-o addopts=""`. Tests drive surfaces, never read source (P16).
- Every CLI leaf is declared in `command_surface.py`; machine output is `aw.agent/v1` records; exit vocabulary is `run_cli`'s `EXIT_*` constants.
- A run ledger owns exactly one filename, `run_ledger_store.LEDGER_FILENAME` (`ledger.jsonl`); it must never be `events.jsonl` (`run_cli.resolve_ledger_path` docstring, `e6b9kt`).
- Commit through `aw commit <plan> -- <paths>`; never push.
- Cite code by SYMBOL.

## Findings

| ID | Finding | Evidence |
|----|---------|----------|
| F-01 | The store and the schema require a `kind: "run"` first record. | `run_ledger_store.RunLedgerStore` raises `RL-E041` "first ledger record must be kind 'run'"; `run_ledger_schema.validate_records` emits the same finding for `records[0]`. |
| F-02 | The header needs four fields beyond the common envelope. | `run_ledger_schema` per-kind table, `"run"`: `workflow_digest`, `requirement_digest`, `repo`, `head` (all `str`); common envelope `schema_version`, `kind`, `seq`, `run_id`, `actor`, `timestamp`, `parent`, with `seq`/`timestamp` assigned by `RunLedgerStore.append`. |
| F-03 | No writer exists; only tests create a ledger. | Backlog `hegwri` (measured 2026-10-02, re-measured in the authoring session 2026-10-12); `tests/test_run_recovery_cli.py` `_run_record` builds the header by hand. |
| F-04 | The readers already look where `aw run init` will write. | `run_cli.resolve_ledger_path` candidates include `state_root(root) / target / store.LEDGER_FILENAME`. |
| F-05 | With a hand-appended header there, the write leaves work. | Authoring session, scratch repo at HEAD `a3084a234`: `aw run start run-abcdef1234 --step S-01 --workflow wf.json` exit 0 ("Started step S-01 (state: running)"); `aw run record ... --state performed` exit 0; `aw runs verify-ledger` "Hash Chain: CLEAN", "Completion Predicates: UNSATISFIED", "no frozen requirements defined". |
| F-06 | Run ids have a fixed shape. | `run_ledger_schema._RUN_ID_RE = ^run-[0-9a-f]{8,}$`. |
| F-07 | Driver runs do not write a ledger, by decision. | Executed plan `rdjka2`, option (b); research `20261007-runledger-00-utb2qr-driver-run-ledger-decision.findings.md`; `hegwri` history 2026-10-09 ("Scoped to aw run execution path"). |
| F-08 | `state_root` is backend-aware: in a repo WITHOUT `.aw/records/` it resolves to a home-scoped projects tree, not into the repo. | `runner_shared.state_root` (`resolve_project_context(...).logical_roots["records"]`, falling back to `<repo>/.aw/records` only when that directory exists). Review probe 2026-10-14: bare `git init` scratch repo -> path under `$HOME/.aw/projects/<name>-<hash>/records/runs`; with `.aw/records/` created -> `.aw/records/runs`. Tests must therefore create `.aw/records/` in the scratch repo. |
| F-09 | The shared run-leaf registrar adds a REQUIRED `target` positional to every leaf. | `cli._register_run_leaf` (`_pr.add_argument("target", ...)`), called for every `_run_leaf_specs` row; `init` has no existing target, so it must be registered separately. |
| F-10 | Adding a leaf trips several census/allowlist tests. | `tests/test_usage_refusal_agent_record.py` `test_exclusion_set_size_and_members` pins `len(REQUIRED_LEAVES) == 67` (discovered from parser leaves with a required argument; `--workflow` required makes `run init` one); `tests/test_completion.py` pins `aw run <TAB>` to `["as", "cancel", "finalize", "ipd", "record", "start"]`; `tests/test_exit_vocabulary_boundary.py` `test_out_of_range_declarations_covered_by_allowlist` requires an allowlist entry for any declaration with an exit outside {0,1,2}; `tests/test_conformance_matrix_structure.py` `test_no_undeclared_parser_leaves` requires a `CommandDeclaration`. |
| F-11 | `run_cli` machine output is bare JSON, not `aw.agent/v1`; the agent schema admits only exits 0..2. | `run_cli._emit_error` docstring (F-16: "DELIBERATELY NOT AN `aw.agent/v1` RECORD"); `agent_schema.validate_agent_record` ("Field 'exit' must be an integer in (0, 1, 2)"). Sibling `g5s94t` OQ-02 assumes `run init` "emits an `aw.agent/v1` record per `v47z9u` E-03" for `MUTATION_UNIVERSE`. |
| F-12 | Existing helpers cover the digest and HEAD needs. | `run_ledger_store.compute_record_hash(mapping)` (canonical `sort_keys=True, separators=(",", ":")` SHA-256); `run_evidence.get_git_head(repo_dir)` (returns `"unversioned"` outside git); `runner_shared.new_run_id` returns `run-<UTC stamp>-<pid>`, which FAILS `_RUN_ID_RE` and so is unusable here. |

## Proposed changes (ordered, validatable)

1. Reproduce (E-01).
2. `aw run init`: leaf (E-02), census/contract tests (E-08), header (E-03), refusals (E-04).
3. Tests (E-05).
4. Spec 6.2 (E-06); docs, CHANGELOG, bare suite (E-07).

## Deferred / out of scope (with reason)

- Writing `requirement_set` and `verifier_decision` records so `aw run finalize` can reach complete.
  - Carrier: 8l1hgw
- Persisting the workflow beside the ledger so later leaves need no repeated `--workflow`.
  - Carrier: sflov4
- Rendering a ledger-only run directory correctly in the `aw runs` viewer.
  - Carrier: nf84rt
- Making the ledger leaves live conformance-harness rows.
  - Carrier: a4tjxc
- Reconciling spec `25kzda` 1.2 step 8 and 5.1 with the `rdjka2` decision.
  - Carrier: 66ls4r

## Scope check

- Over-scope: none.
- Under-scope: none known. The authoring session measured the follow-on gaps and filed each as a carrier above.

## Required tests / validation

- `tests/test_run_init.py` (new), (a) and (b) failing on the base commit.
- Existing `tests/test_run_recovery_cli.py` unchanged and passing.
- Census and contract tests touched by a new leaf (F-10), each passing after its update: `tests/test_usage_refusal_agent_record.py`, `tests/test_completion.py`, `tests/test_exit_vocabulary_boundary.py`, `tests/test_conformance_matrix_structure.py`, `tests/test_command_surface_declarations.py`, `tests/test_agent_surface_conformance.py`, `tests/test_shared_flag_honored.py` (the last two: `run init` is a `mutation`/`result` declaration so it enters `MUTATION_UNIVERSE` with bare argv; with no `--workflow` it must still emit a valid `cannot-run` record at exit 2, which the usage-refusal path provides).
- Invariants and their tests: first record is `kind: "run"` (E-05 a); no partial ledger on refusal (E-05 c, d); run id cannot escape the runs root (E-05 d `../x`); readers find what init writes (E-05 b, g).
- Bare suite `python3 -m pytest`.

## Spec / documentation sync

Spec `25kzda` Section 6.2 records the decided ledger location (E-06), listed in Scope-Paths, plus an `aw specs note` history line. WHY: 6.2 lists it as an open implementation choice, and this plan makes it; leaving it open would let a later plan choose a second location. Sections 1.2 and 5.1 are deliberately untouched (backlog `66ls4r`, sibling `9epp40`, which leaves 6.2 to this plan so the two commute). `docs/cli-output-contract.md` Section 3.1 gains the new leaf's exit codes and its machine-output note; CHANGELOG line. The `aw run` parser help/epilog in `cli.py` lists `init`.

## Open questions

### OQ-01: Where should operator-created ledgers live?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Under the runs root, `runner_shared.state_root(repo) / <run-id> / ledger.jsonl`. It is the root every runs reader already resolves (`resolve_ledger_path`), it follows the configured records backend, and the authoring session showed the write leaves working there (F-05). The cost is that the driver-run viewer lists these directories (backlog `nf84rt`). Reversible: the location is one constant and one spec bullet.

### OQ-02: Should `aw run init` also write the `requirement_set` record?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. `hegwri` asks for the header as its minimum, and `run_freeze.requirement_set_record` mints `M-NN` ids that do not match a workflow's `R-NN` ids, so writing one now would bake in an id mismatch. Carried by `8l1hgw`. Reversible.

### OQ-03: What shape is `aw run init`'s machine output?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Success under `--agent` is one `aw.agent/v1` `result` record (exit 0); refusals keep `run_cli._emit_error`'s bare-JSON shape (exit 2 or 6). Basis: sibling `g5s94t` OQ-02 already depends on an `aw.agent/v1` record for `MUTATION_UNIVERSE`, whose test validates it with `agent_schema.validate_agent_record` (F-11); a new leaf has no existing consumer of a bare shape to break; and the schema cannot carry exit 6, so refusals cannot be `aw.agent/v1` records without changing the family's exit vocabulary. Demonstrated at review (2026-10-14): `agent_schema.validate_agent_record` returned `[]` for `{"schema":"aw.agent/v1","kind":"result","cmd":"run init","exit":0,"outcome":"ok","verified":true,"complete":true,"run_id":"run-0123456789abcdef","ledger":".aw/records/runs/run-0123456789abcdef/ledger.jsonl"}`, `render_guarded_jsonl_record(..., strict=True)` rendered it, and the same record with `exit: 6` returned `["Field 'exit' must be an integer in (0, 1, 2), got '6'"]`. Reversible (a new leaf, no consumers yet).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the three pasted outputs (store refusal with `RL-E041` and no file; `aw run start` exit 2; zero writers found).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `aw run init --help` output (exit 0) listing `--workflow`, `--run-id`, `--dir`, `--agent`, `--json`; pasted `aw run init --agent` (no `--workflow`) showing exit 2 and a `cannot-run` record; and pasted passing output of `python3 -m pytest -o addopts="" tests/test_conformance_matrix_structure.py tests/test_command_surface_declarations.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: a pasted `aw run init --workflow wf.json` run in a scratch repo containing `.aw/records/`, the ledger file's one line (showing `kind: "run"`, `seq: 0`, the four header fields), `validate_records` returning `ok=True`, `aw run start <id> --step S-01 --workflow wf.json` exiting 0, and `aw run init --workflow wf.json --agent` stdout with `agent_schema.validate_agent_record` returning `[]` on it (the path E-02 and E-03 create: `run_cli.run_cli` -> `_run_init` -> `RunLedgerStore.append`).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: E-05 (c) and (d) passing, plus a pasted manual run of each refusal (existing id, malformed id including `../x`, missing file, invalid JSON, JSON array) showing its exit code and a before/after listing of `state_root(repo)` that is identical.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `python3 -m pytest -o addopts="" -v tests/test_run_init.py` output with cases (a) through (g) each passing, and pasted output of (a) and (b) failing on the base commit (`invalid choice: 'init'`).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the spec 6.2 diff and the new `## Workflow history` line, `git diff` showing Sections 1.2 and 5.1 untouched, and pasted `aw specs check` exiting 0.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the doc and CHANGELOG diffs, and the pasted bare-suite (`python3 -m pytest`) summary line with zero failures (any failing node id must be shown to fail identically on the base commit to be excused).
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: the three diffs (allowlist entry, pinned `REQUIRED_LEAVES` count with its old value as measured at execution HEAD and new value one higher, completion expectation) and pasted passing output of `python3 -m pytest -o addopts="" tests/test_usage_refusal_agent_record.py tests/test_completion.py tests/test_exit_vocabulary_boundary.py tests/test_agent_surface_conformance.py tests/test_shared_flag_honored.py`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval. Open questions: all resolved. Scope fence: Scope-Paths is a declaration; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), and a declared path left untouched is acknowledged (`--scope-ack`). Commit only your own paths through `aw commit v47z9u -- <paths>`; never push. Paste the actual runner output for every test claim; a claim without pasted output is not evidence. Lifecycle: when run by `aw oc run` / `aw agy run`, the runner finalizes; when executed by hand, finish with `aw ipd finalize v47z9u` only after `aw ipd lint --phase pre-transition` conforms.
