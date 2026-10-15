# Review findings: plan v47z9u

- Subject-Id: v47z9u
- Subject-Type: ipd
- Reviewed-At: 2026-10-14
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (LOW, fixed), PR-009 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `d78f642c2`. The plan was committed and byte-identical to the
lane input (sha256 `88a5514f...`), so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`
(two `IPD-Z602` advisories). Not an orchestrator.

Re-measured at HEAD: F-01 (`RunLedgerStore.append_held` and `validate_records` raise/emit `RL-E041`), F-02
(`_KIND_FIELDS["run"]` = workflow_digest, requirement_digest, repo, head), F-04 (`resolve_ledger_path`
candidate `state_root(root) / target / store.LEDGER_FILENAME`), F-06 (`_RUN_ID_RE`) all MATCH. Live probe in
a scratch git repo with `.aw/records/`: a `step_attempt` first append raised `SchemaInvalidRecordError`
`RL-E041` with no file left; `aw run init --help` exit 2 (`invalid choice: 'init'`); `aw run start
run-abcdef1234 --step S-01` exit 2 with "no driver run writes one today"; a header built with the plan's
recipe at `state_root/<id>/ledger.jsonl` validated, and `run start` exit 0, `run record --state performed`
exit 0, `runs status` exit 1 showing `S-01: performed`, `runs verify-ledger` exit 1 with `Hash Chain: CLEAN`
and "no frozen requirements defined" (F-05 MATCH). The same probe in a bare `git init` repo resolved
`state_root` under `$HOME/.aw/projects/...` (new F-08).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric G (executability) | `agent_workflows/cli.py` `_register_run_leaf` (`_pr.add_argument("target", ...)`) | E-02 said to register `init` "through the same leaf registration"; that helper adds a REQUIRED `target` positional, so `aw run init --workflow wf.json` would fail argparse. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now registers `init` on `run_sub` with its own `add_parser` (or a registrar opt-out), adds it to the `run_cli` dispatcher, usage and epilog; F-09 added. |
| PR-002 | HIGH | UNDER-SCOPE | Rubric D/E (regression) | `tests/test_usage_refusal_agent_record.py` `test_exclusion_set_size_and_members` (`== 67`); `tests/test_completion.py` "WRITING noun's own first slot"; `tests/test_exit_vocabulary_boundary.py` `test_out_of_range_declarations_covered_by_allowlist` | A new required-arg leaf with exit 6 breaks three pinned tests, none in Scope-Paths, so the bare suite in E-07 could not go green. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-08/V-08 updates each by recording the new truth (count re-derived at execution HEAD); the three files added to Scope-Paths; F-10 added. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric C (machine contract) | `run_cli._emit_error` docstring F-16; `agent_schema.validate_agent_record`; sibling `g5s94t` OQ-02 | E-03 promised an `aw.agent/v1` record from a module whose machine output is deliberately bare JSON, without saying so, while sibling `g5s94t` depends on it being valid `aw.agent/v1`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 specifies the exact success record (rendered through `render_guarded_jsonl_record`), keeps refusals on `_emit_error`, explains why exit 6 cannot be `aw.agent/v1`; OQ-03 records the choice with a demonstration; E-07 documents it in contract doc 3.1. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric E (test environment) | `runner_shared.state_root`; review probe (bare repo -> `$HOME/.aw/projects/...`) | Tests in a bare scratch repo would write a ledger into the real home-scoped projects tree and assert on the wrong path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 and E-05 require `.aw/records/` in the scratch repo; F-08 added. |
| PR-005 | MEDIUM | IN-SCOPE | Rubric A (atomicity, partial failure) | `runner_shared.mint_run_dir` (`mkdir(..., exist_ok=False)`); `RunLedgerStore.append_held` (creates parent, `.lock`) | The existing-ledger refusal was check-then-write and keyed on `ledger.jsonl` only, so a race or a same-named driver run directory could be written into, and a failed append could leave a directory and lock behind. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 reserves the run directory atomically, maps `FileExistsError` to exit 6, and removes its own directory on append failure. |
| PR-006 | MEDIUM | IN-SCOPE | Rubric B (trust-boundary input) | `run_ledger_schema._RUN_ID_RE`; `run_cli._load_workflow_arg` (returns `None` for non-dict JSON) | Path-traversal via `--run-id` and a non-object workflow were not named; `None` from the loader could have been treated as an empty workflow. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 validates before any write, names `is_run_id` as the traversal guard and refuses `None`; E-05 (d) tests `../x` and a JSON array. |
| PR-007 | MEDIUM | IN-SCOPE | Rubric C (reuse canonical mechanisms) | `run_ledger_store.compute_record_hash`; `run_evidence.get_git_head`; `runner_shared.new_run_id`; sibling `o34rb3` E-02, `um0twl` E-02 | E-03 hand-rolled the digest and `git rev-parse` and left the default-id generator unspecified; `new_run_id`'s shape fails `_RUN_ID_RE`; `requirement_digest` semantics were not tied to `um0twl`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 names `compute_record_hash`, `get_git_head`, `secrets.token_hex(8)`, `resolve_verb_repo_root`, and states the digest is a placeholder `um0twl` replaces; F-12 added. |
| PR-008 | LOW | IN-SCOPE | Rubric G (spec sync convention) | sibling `9epp40` E-03 (`aw specs note`); spec `25kzda` `## Workflow history` | E-06 edited an approved spec with no dated provenance or history note. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 adds an in-bullet dated note, an `aw specs note` line, and `aw specs check`; V-06 demands both. |
| PR-009 | LOW | IN-SCOPE | Rubric G (evidence strength) | plan V-02..V-07 | Several V-items demanded outputs without naming the command or the concrete content to paste (e.g. `--help` only, "unchanged directory listing"). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02..V-07 now name exact commands and contents; V-08 added for E-08. |

`IPD-Z602` advisories remain on E-03, E-05, E-08: each is one deliverable (one handler, one test module,
one census reconciliation) and was not split further.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What machine shape does `run init` emit? | `aw.agent/v1` `result` on success, bare `_emit_error` JSON on refusal. | All bare JSON like siblings (REJECTED: `g5s94t` OQ-02 and `test_agent_surface_conformance_mutation` require a valid `aw.agent/v1` record); all `aw.agent/v1` (REJECTED: schema admits exit 0..2 only, refusal is exit 6). | `run_cli._emit_error` docstring; `agent_schema.validate_agent_record`; review demonstration in OQ-03. | yes |
| D-2 | How is the existing-run refusal made safe? | Atomic `mkdir(exist_ok=False)` on the run directory, exit 6, cleanup on failure. | Check `ledger.jsonl` existence first (REJECTED: racy, writes into a same-named driver run dir). | `runner_shared.mint_run_dir`. | yes |
| D-3 | Default run id generator? | `"run-" + secrets.token_hex(8)`. | `runner_shared.new_run_id` (REJECTED: `run-<stamp>-<pid>` fails `_RUN_ID_RE`). | `run_ledger_schema._RUN_ID_RE`; `runner_shared.new_run_id`. | yes |
| D-4 | Where do the census-test updates live? | In this plan (new E-08), Scope-Paths extended. | Leave to sibling `g5s94t` (REJECTED: this plan's own bare-suite gate fails without them). | F-10 tests. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
