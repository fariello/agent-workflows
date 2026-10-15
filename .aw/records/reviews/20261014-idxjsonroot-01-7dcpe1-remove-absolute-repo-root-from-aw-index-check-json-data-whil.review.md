# Review findings: plan 7dcpe1

- Subject-Id: 7dcpe1
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `5b6b42429` in an isolated review lane. The plan was committed and unchanged (`d50759edf`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review. `--phase review-finalize` was clean after revisions. It reported six `IPD-C801` info hits on `DECISIONS.md:1`, which is an expected output value and not a citation.

Re-verified against the live tree and temp fixtures built with `tests.test_index_check_agent_records._create_fixture_repo`:
- On the live tree, `index {plans,prompts,research} --check --json` gives `data` keys `['human_rendered', 'repo_root', 'target']` with the checkout path in stdout. `--agent --verbose` does not leak. F-01 and F-02 are reproduced.
- A clean fixture plus `DECISIONS.md` citing `PLAN-zzzzzz RSCH-zzzzzz` gives one `dangling-citation` diagnostic at `DECISIONS.md:1` (severity `info`) for plans and research. Exit is 0 on `--json` and `--agent`. The root leaks only on `--json`.
- `normalize_repo_path(<root>/DECISIONS.md:1)` with no root returns `.aw/worktrees/<lane>/DECISIONS.md:1`. With the root it returns `DECISIONS.md:1`.
- `emit_index_write_result` `data` is `{target, count, noun, json_changed, md_changed, index_dir}` with no `repo_root`. `tests/test_index_write_agent_records._run_json_verb_check` asserts `json_changed` and `md_changed`.
- `aw sanitize --agent` is clean at base.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness / D. Anti-regression | `agent_workflows/artifact_core.py` `emit_index_write_result` `data = {"target", "count", "noun", "json_changed", "md_changed", "index_dir"}`; `tests/test_index_write_agent_records.py` `_run_json_verb_check` | F-03 and E-02 claimed the write helper puts `repo_root` in `data`, which is false. The plan told the executor to replace `data` with `{"target", "count"}`, which would drop four live keys and break existing tests and the `--json` contract. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-03, E-02, Goal, Scope, and proposed change 2 were rewritten: the write helper only gains `repo_root=` out of band and normalized locations, and its `data` stays unchanged. A scope-fence line was added. |
| PR-002 | HIGH | IN-SCOPE | E. Verification (unsatisfiable demand) | `check_engine.RULE_REGISTRY` `"dangling-citation": RuleSpec("info", ...)`; `artifact_core.drift_exit_code`; review probe exit 0 | E-03 asserted `returncode == 1` for a `DECISIONS.md` dangling citation. `dangling-citation` is `info`, so the measured exit is 0, and a correct execution could not pass. It also named rule `check.index-dangling-citation`, but the emitted rule is `dangling-citation`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The test now expects exit 0 and rule `dangling-citation`. The measurement is recorded in conventions. |
| PR-003 | MEDIUM | IN-SCOPE | G. Executability (stale evidence) | `agent_schema.normalize_repo_path` `known_markers = (".aw", ".agents", ...)`; `artifact_core.SCAN_ROOTS`; `docs/cli-output-contract.md` `### Protocol Invariants and Anti-Greenwashing Rules`; `result_types.CommandResult.to_agent_record` | The conventions cited the wrong `known_markers` tuple, a nonexistent `artifact_refs.DEFAULT_SCAN_ROOTS`, a "Section 4 Path Sanitization" heading and a "data field exemption" subsection that are really a bullet under `## 4`, a nonexistent `internal_keys` set, prompts dangling scanning that does not exist, and `GEMINI.md` Rule 3. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Each was replaced with the verified symbol or quoted anchor. |
| PR-004 | MEDIUM | IN-SCOPE | E. Testing (harness mismatch) | `tests/test_index_check_agent_records.py` `class IndexCheckSubprocessTests(unittest.TestCase)`, `self.root`; no `index_fixture` | E-03 specified pytest fixtures (`index_fixture`, `tmp_path`) in a unittest module that has no such fixture. The unit-test location assertion could also pass on the tail heuristic for some temp paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The tests now use `self.root`, `VERBS`, `subTest`, and `run_cli`. The unit test requires a temp path with no known-marker component. Added `validate_agent_record` and exit-parity assertions. |
| PR-005 | MEDIUM | UNDER-SCOPE | G. Verification checklist strength / D. Invariant map | V-01 (diff only), V-04 (no full suite); no invariant map | V-01 could pass on a diff with no behavior shown. V-04 lacked a full-suite run. The plan had no invariant-to-test map. The new dataclass field position was unspecified and could shift positional construction. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 adds a direct `python3 -c` behavior probe. V-02 adds a live read-only CLI check for all verbs. V-03 needs `-o addopts="" -v` output. V-04 adds the bare full suite against base and a dash grep. Added an invariant-to-test map. The field is now pinned as last. |
| PR-006 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate lacked `aw ipd begin`, the paste-output honesty rule, path-scoped `aw commit` and never-push, a scope fence, and runner-conditional finalize, and it named the `executed` transition by `aw ipd set`. Sibling `7i4zba` overlap (identical location normalization and `target=`) was not reconciled. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate. Conventions now state the `7i4zba` overlap is idempotent in either merge order. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the write helper's `data` be reshaped? | No; add only out-of-band `repo_root` and normalized locations | Reduce `data` to `{target, count}` as authored (drops live keys, breaks tests) | `emit_index_write_result` `data` dict; `_run_json_verb_check` assertions | yes |
| D-2 | What exit code does a lone dangling citation produce in the E-03 test? | 0 | 1 as authored (unsatisfiable) | `RULE_REGISTRY` `dangling-citation` is `info`; `drift_exit_code`; fixture probe | yes |
| D-3 | Where does the new `CommandResult.repo_root` field go? | Last, after `schema_version` | After `complete` as authored (shifts positional order of `applied`/`target`/`schema_version`) | `result_types.CommandResult` field list | yes |
