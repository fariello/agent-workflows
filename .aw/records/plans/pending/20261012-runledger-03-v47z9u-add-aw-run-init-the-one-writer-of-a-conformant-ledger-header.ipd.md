# IPD: Add aw run init: the one writer of a conformant ledger header record, at the runs-root ledger location

- Date: 2026-10-12
- Kind: child
- Concern: Nothing in the package can create a run ledger. `RunLedgerStore.append` refuses any ledger whose first record is not `kind: "run"` (finding `RL-E041`, "first ledger record must be kind 'run'"), and `run_ledger_schema.validate_records` enforces the same on read, but no code under `agent_workflows/` writes such a record: every occurrence is a reader or a refusal. So the whole `aw run` write surface (`start`, `record`, `cancel`, `finalize`) and the ledger readers (`aw runs status|next|resume|show|evidence|verify-ledger`) are unreachable for an operator; only tests create a ledger, by appending the header themselves (`tests/test_run_recovery_cli.py` `_run_record`). Backlog `hegwri`.
- Scope: (1) Add `aw run init`, which creates a new run ledger at `runner_shared.state_root(repo) / <run-id> / ledger.jsonl` and writes exactly one conformant `kind: "run"` header record through `RunLedgerStore.append`, from a `--workflow` file. (2) Record the storage location decision in spec `25kzda` Section 6.2 (the "durable storage location for run ledgers" bullet). (3) Behavior tests. OUT, each carried by its own backlog item: writing `requirement_set` / `verifier_decision` records (`8l1hgw`), persisting the workflow beside the ledger (`sflov4`), the runs viewer's rendering of a ledger-only directory (`nf84rt`), conformance-harness rows for the ledger leaves (`a4tjxc`), and reconciling spec `25kzda` 1.2 step 8 and 5.1 with the `rdjka2` decision (`66ls4r`). Driver runs (`aw oc run` / `aw agy run`) keep `state.json` / `events.jsonl` and do not write a ledger (`rdjka2` option (b), decision record `utb2qr`).
- Scope-Paths: agent_workflows/run_cli.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_run_init.py, docs/cli-output-contract.md, CHANGELOG.md, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: hegwri
- Set: runledger
- Order: 3
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: v47z9u

## Workflow history
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): completed by hand at the maintainer's direction. The authoring turn in run-20261012T005641Z-2321995 created this skeleton and filed carriers 66ls4r, 8l1hgw, a4tjxc, nf84rt and sflov4, then its host session timed out ("UnknownError: The operation timed out.") before writing the body; the skeleton reached main via 95a7b41db. Body written from that session's recorded measurements, re-checked against main at 34b6e3a10.
- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

An operator can create a run ledger with one command and then use `aw run start` / `record` and the `aw runs` readers on it, which today is impossible outside the test suite.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: reproduce

- [ ] E-01 REPRODUCE at execution HEAD. In a scratch git repo: (a) build `run_ledger_store.RunLedgerStore` over a fresh path and append a `step_attempt`-shaped record; expect `SchemaInvalidRecordError` with `RL-E041` and no file left on disk; (b) run `aw run start run-abcdef1234 --step S-01`; expect exit 2 with the ledger-not-found message ("no driver run writes one today"); (c) search `agent_workflows/` for a writer of a `"kind": "run"` record and paste the result (zero writers expected). If any of these has changed, stop and report the plan as overtaken with the contradicting output.
  - Depends on: none
  - Expected outcome: three pasted outputs confirming no ledger can be created.
  - Execution state: pending

### Task group 2: the writer

- [ ] E-02 Register the leaf. Add `aw run init` beside the other write leaves (`start`, `record`, `cancel`, `finalize`) through the same leaf registration in `cli.py` and the declared command surface in `command_surface.py`, with `--workflow PATH` (required), optional `--run-id`, `--dir`, and the shared output flags (`--agent`, `--json`), dispatching to a new `run_cli` handler.
  - Depends on: E-01
  - Expected outcome: `aw run init --help` lists the flags, and the leaf appears in the declared command surface.
  - Execution state: pending

- [ ] E-03 Build and append the header. In the `run_cli` handler: load the workflow with `_load_workflow_arg`; default the run id to a fresh `run-<16 hex>` that satisfies `run_ledger_schema.is_run_id`; compute `workflow_digest` (SHA-256 of the workflow's canonical JSON, `sort_keys=True, separators=(",", ":")`) and `requirement_digest` (the same over its `requirements` list); take `repo` from the repository root's name and `head` from `git rev-parse HEAD`; set the common envelope (`schema_version` = `run_ledger_schema.LEDGER_SCHEMA_VERSION`, `kind: "run"`, `run_id`, `actor: "runtime"`, `parent: ""`); and append through `RunLedgerStore.append` at `state_root(repo) / <run-id> / LEDGER_FILENAME`, so the store assigns `seq`, `timestamp` and the hash chain. Print the run id and ledger path; under `--agent`, one `aw.agent/v1` result record carrying both.
  - Depends on: E-02
  - Expected outcome: `aw run init --workflow wf.json` writes one record that `run_ledger_schema.validate_records` accepts, and `aw run start <id> --step S-01 --workflow wf.json` then exits 0.
  - Execution state: pending

- [ ] E-04 Refuse bad input without writing. Exit 6 and write nothing when a ledger already exists at the target path; exit 2 and write nothing for a malformed `--run-id`, a missing workflow file, or invalid workflow JSON. Use the existing `run_cli` `EXIT_*` constants and emit paths.
  - Depends on: E-03
  - Expected outcome: each refusal leaves the filesystem unchanged.
  - Execution state: pending

### Task group 3: prove and document

- [ ] E-05 Add `tests/test_run_init.py`, driving the CLI as a subprocess in a scratch git repo, asserting on exit codes, output, and the ledger file, never on source text. Cases: (a) init creates exactly one record at `state_root(repo)/<id>/ledger.jsonl` and `validate_records` accepts it; (b) the follow-on sequence: `aw run start <id> --step S-01 --workflow wf.json` exit 0, `aw run record <id> --step S-01 --state performed --workflow wf.json` exit 0, `aw runs status <id>` shows `S-01: performed`, and `aw runs verify-ledger <id>` reports the hash chain CLEAN (completion stays UNSATISFIED, "no frozen requirements defined", which is backlog `8l1hgw`'s; assert it as current behavior); (c) a second init with the same `--run-id` exits 6 and leaves the ledger byte-identical; (d) malformed `--run-id`, missing workflow, invalid JSON each exit 2 and create nothing; (e) the default id matches `run-<hex>`; (f) `--agent` emits one `aw.agent/v1` record naming the id and path. Show (a) and (b) failing on the base commit (no such leaf).
  - Depends on: E-04
  - Expected outcome: the new module passes; (a) and (b) shown failing before the change.
  - Execution state: pending

- [ ] E-06 Record the location decision in spec `25kzda` Section 6.2: replace the bullet "the durable storage location for run ledgers and large captured outputs" with the decided ledger location (`<runs root>/<run-id>/ledger.jsonl`, the runs root being `runner_shared.state_root`) and keep "large captured outputs" listed as still open. Leave Sections 1.2 step 8 and 5.1 unchanged (backlog `66ls4r`, a maintainer decision).
  - Depends on: E-05
  - Expected outcome: the 6.2 diff, with 1.2 and 5.1 untouched.
  - Execution state: pending

- [ ] E-07 Document and verify. Add `aw run init` to the exit-code list in `docs/cli-output-contract.md` (exits 0, 2, 6) and a CHANGELOG line (no em or en dashes in either). Run the bare suite and paste its summary line.
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

## Proposed changes (ordered, validatable)

1. Reproduce (E-01).
2. `aw run init`: leaf, header, refusals (E-02..E-04).
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
- Bare suite `python3 -m pytest`.

## Spec / documentation sync

Spec `25kzda` Section 6.2 records the decided ledger location (E-06), listed in Scope-Paths. WHY: 6.2 lists it as an open implementation choice, and this plan makes it; leaving it open would let a later plan choose a second location. Sections 1.2 and 5.1 are deliberately untouched (backlog `66ls4r`). `docs/cli-output-contract.md` gains the new leaf's exit codes; CHANGELOG line.

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

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the three pasted outputs (store refusal with `RL-E041` and no file; `aw run start` exit 2; zero writers found).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `aw run init --help` output listing the flags.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: a pasted `aw run init --workflow wf.json` run in a scratch repo, the ledger file's one line, `validate_records` accepting it, and `aw run start <id> --step S-01 --workflow wf.json` exiting 0 (the path E-02 and E-03 create).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: E-05 (c) and (d) passing, with the exit codes and an unchanged directory listing for each refusal.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the new module passing with each case named, and (a), (b) failing on the base commit.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the spec 6.2 diff, and `git diff` showing Sections 1.2 and 5.1 untouched.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the doc and CHANGELOG diffs and the bare-suite summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval. Open questions: all resolved. Scope fence: Scope-Paths is a declaration; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), and a declared path left untouched is acknowledged (`--scope-ack`). Commit only your own paths through `aw commit v47z9u -- <paths>`; never push. Paste the actual runner output for every test claim; a claim without pasted output is not evidence. Lifecycle: when run by `aw oc run` / `aw agy run`, the runner finalizes; when executed by hand, finish with `aw ipd finalize v47z9u` only after `aw ipd lint --phase pre-transition` conforms.
