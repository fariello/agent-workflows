# Review: Restore behavioral coverage of the run_cli._emit_error machine JSON payload key set

- Subject-Id: e97wtz
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Every material claim was re-verified in this worktree by driving `cli.main` in-process with stdout
patched (the plan's own idiom), not by reading prose:

- `run_cli._emit_error` (`agent_workflows/run_cli.py:844`) builds `{"ok", "error", "exit_code"}` and
  updates with `extra` only when truthy; the stale docstring sentence quoted by E-03 is present verbatim
  at `run_cli.py:863-865`.
- `run_cli._emit_ledger_not_found` (`run_cli.py:448`) passes `extra` only for `TARGET_DRIVER_RUN`.
- `totalgibberish --dir <tmp>` on `runs verify-ledger`, `runs show`, `runs status`, `run cancel`,
  `run start` under both `--agent` and `--json`: rc 2, bare three-key payload, `error` contains
  `ledger.jsonl` and has no `error: ` prefix.
- Explicit absent path `runs verify-ledger <tmp>/nowhere/ledger.jsonl --agent`: rc 2,
  `{"error":"ledger file not found for target '...'","exit_code":2,"ok":false}`, no
  `no driver run writes one` clause.
- Empty `ledger.jsonl` passed positionally to `runs next`/`runs status`/`runs resume`, `run cancel` with `--agent`:
  each `{"error":"ledger is empty","exit_code":2,"ok":false}` at rc 2 (emitted at `run_cli.py:977`).
- Human stream: `error: ledger file not found ...` (not JSON) at rc 2.
- `tests/test_run_recovery_cli.py` `test_an_unknown_target_keeps_the_bare_machine_shape` (`:2784`) is
  the only surviving exact-key-set assertion (`runs resume --agent` only), confirming the gap.
- `19313eed7^:tests/test_run_cli_ledger_message.py` carries
  `test_machine_payload_carries_the_same_text_with_unchanged_keys` and `_exit_code_unpiped`, as cited.
- `tests/support.py:161` `declare_execution_role` exists; executed plan `ev7t1w` exists.
- Both mutation checks are reachable and would fail the named assertions (`"detail": None` breaks the
  set equality; `"exit_code": 0` breaks `payload["exit_code"] == rc` with rc still 2). `_redact_output`
  does not rewrite a `detail` key.

Approach is sound and correctly scoped (P16-compliant, behavioral, no source reads). Right-sizing:
3 E-leaves, each one concern and one pass. Security lens: test-only plus a docstring; no trust-boundary
change. Defects found were all in the gate and evidence wording.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | G. Plan executability (execution contract) | plan `## Approval and execution gate` | The gate lacked the honesty rule (paste actual runner output), a scope-fence declaration, the conditional finalize ownership (runner vs hand), the never-hand-`git mv` rule, a commit path list including the plan file, a statement that the V-01/V-02 mutations must be reverted before commit, and the release-gate/backlog-close note. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with all elements; no STOP clause for out-of-scope edits (2026-09-01 ruling). |
| PR-002 | LOW | IN-SCOPE | G. Plan executability | plan E-02; `run_cli.py:977` | E-02 said "create an empty `<tmp>/ledger.jsonl`" without stating how it is targeted; `--dir <tmp>` alone does not name a target. Measured form that reaches "ledger is empty" is the positional path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now states `<leaf> <tmp>/ledger.jsonl --agent`. |
| PR-003 | LOW | IN-SCOPE | E. Testing and verification | plan V-01 | The P16 grep (alternation of inspect, import ast, read_text) false-positives on the English word "inspect" in any docstring/comment, making V-01 spuriously unsatisfiable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with an anchored pattern for import of inspect or ast, `.read_text(`, and `getsource`. |
| PR-004 | LOW | IN-SCOPE | G. Re-derivation convention | plan V-01, V-02 | V-items bound named test functions as the bar; per rubric G a test function name is only a non-binding pointer. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a validation preamble making names pointers and the pinned behavior plus mutation detection the bar. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the plan also add exact-key-set coverage for `run record`, `run finalize`, `runs evidence` (measured bare too)? | No; the five chosen leaves span both routing paths (inline `_emit_ledger_not_found` and `_resolve_or_error`), which is what drift would split. | Enumerating all ten leaves. Rejected as gold-plating the named property. | `run_cli.py:448-484`, `:881-894`; plan Scope check | yes |
| D-2 | Is OQ-01 (new purpose-named module) correctly resolved? | Yes, keep. | Re-creating `tests/test_run_cli_ledger_message.py`. | Backlog `n2fx9i` names only the key-set property; re-using the name implies restoring the wording tests | yes |
