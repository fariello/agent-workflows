# Review findings: plan tgfxin

- Subject-Id: tgfxin
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `cff5a3b2a`. The plan was committed and byte-identical to the lane input, so no pre-review snapshot was taken. `aw ipd lint --phase author --agent` reported `clean`. The plan is a child, not an orchestrator.

Verified:
- F-1: `agent_workflows/run_cli.py:1249` `sys.stdout.write(agent_schema.render_guarded_jsonl_record(rec))` directly after the `rec` literal carrying `"run_id"`/`"ledger"`; no `fields` reference anywhere in `run_cli.py`.
- F-2: `tests/test_shared_flag_honored.py:55` `KNOWN_BROKEN = {("run init", "--fields"): "gm9saf"}`; baseline run: `test_fields_flag_honored_mutation[run init] XFAIL`, `4 passed, 254 deselected, 1 xfailed`.
- `agent_schema.filter_record_fields` (`agent_schema.py:506`) and the `cli._emit_config_agent_record` string normalization (`cli.py:10720-10724`) exist as cited. The shared `--fields` arg is `default=None` with help "Comma-separated field projection for --agent output" (`cli.py:1355-1358`), so OQ-01 is grounded.
- Backlog `gm9saf` (graduated) has `Blocks-Release: next` and `Work-Kind: bug`, and the plan inherits both.
- Baseline `tests/test_run_init.py`: `13 passed`.
- Mechanism demonstration (E-01): copied the package into gitignored `.aw/state/` scratch and applied the exact E-01 change. A probe showed `args.fields == 'cmd'` reaches `_run_init`. Outputs: `--fields cmd` gave envelope-only `{schema,kind,cmd,exit,outcome,verified,complete}`; `--fields cmd,run_id` added `run_id` and still had no `ledger`; no `--fields` gave the full record. Unpatched code with `--fields cmd` emitted `run_id` and `ledger`. The scratch copy was deleted afterwards.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric E (evidence feasibility) | Plan V-01; `python3 -m agent_workflows` resolves the package from cwd before `PYTHONPATH` (review probe: a first demo run in the scratch cwd silently ran the unpatched copy) | V-01's manual demonstration did not say how to invoke `aw` against a scratch repo. Run naively, it can execute a different package copy and give misleading evidence. It also did not say the workflow must carry non-empty `requirements` (otherwise refused with `RF-E007`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now gives the exact invocation (run from the lane root with `--dir <scratch>`) and the fixture prerequisites, and also demands the `--fields cmd,run_id` case. Conventions note added. |
| PR-002 | LOW | IN-SCOPE | Rubric E (command consistency) | Plan `## Required tests / validation` `-n auto -k "run and init"` vs V-03 `-v -k "run and init or known_broken"` | The validation section's selector omitted the `known_broken` tests it claimed to show, and it did not match V-03. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Aligned to the V-03 command. |
| PR-003 | LOW | UNDER-SCOPE | Rubric G (execution contract) | Plan `## Approval and execution gate` | The gate had no scope fence and no explicit paste-actual-output rule. Its lifecycle line gave no runner/hand ownership (`aw ipd finalize`, never `git mv`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with every element, and the release-gate inheritance noted. |
| PR-004 | LOW | IN-SCOPE | Rubric D/E (claims and test gating) | Plan E-02 "would fail against the unfixed code"; `pyproject.toml` `testpaths` omits both test modules; OQ-01 `- Owner: none` | E-02's red claim had no cited basis. The plan did not note that neither touched test module runs in the bare gate. OQ-01 had no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 cites the observed unfixed output and the XFAIL baseline, and names the `SAMPLE_WORKFLOW`/`_create_scratch_repo` helpers. A conventions note says both modules must be run explicitly. OQ-01 owner set to `plan author`. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should `--fields` also project `--json` output for run init (OQ-01)? | No; `--agent` only. | Project `--json` too (REJECTED: help text scopes `--fields` to `--agent`; the gate exercises `--agent` only). | `agent_workflows/cli.py:1355-1358` help text; `tests/test_shared_flag_honored.py` `test_fields_flag_honored_mutation` argv. | yes |
| D-2 | Is the E-01 mechanism (normalize string, `filter_record_fields`) sufficient, given `args.fields` arrives as a raw string? | Yes, as written. | Rely on `cli._sniff_fields_from_raw_argv` (REJECTED: not wired into `run_cli`). | Scratch probe `PROBE ns={'fields': 'cmd'}` and the projected outputs recorded above. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
