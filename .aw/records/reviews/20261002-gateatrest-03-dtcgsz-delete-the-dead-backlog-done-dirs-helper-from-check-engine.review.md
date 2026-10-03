# Review findings: plan dtcgsz

- Subject-Id: dtcgsz
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `ac9648ed5`. The plan in `pending/` was committed and
byte-identical to the lane input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent`
reported `clean` (exit 0) before semantic review. `- Kind: child`, so `IPD-S407` does not apply.

The central claim reproduces. AST census over tracked `.py` files: `{('def', 'agent_workflows/check_engine.py'): 1}`.
`git log --all -S` returns only `596dd9acb` (2026-08-25), where `git grep -c` counts 1 occurrence. A census of
all 57 top-level private functions in `check_engine` finds only `_backlog_done_dirs` unreferenced (F-13).
`_BACKLOG_DONE_RE` is read by `_staged_backlog_done_items` (F-06). The at-rest arm uses `_backlog._iter_items`
and `_status_meta` (F-08). `aw check release-gates --agent` reports 0 findings. The F811 gate passes. `ruff format
--check` passes. `tests/test_check_engine_release_gate.py` has 40 tests, 6 of them at-rest. The deletion was
simulated in memory: cutting from `def _backlog_done_dirs` to `_BACKLOG_DONE_RE = ` removes 7 lines, and
`ruff format --check -` on the result exits 0.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G (executability) / E | `agent_workflows/check_engine.py:5037` `def _backlog_done_dirs` through `:5044` `_BACKLOG_DONE_RE = ...`; plan E-01 and V-01 | E-01 described the deletion boundary ambiguously ("five-line function ... together with the blank-line padding", "exactly 5 lines shorter plus the removed padding") and pointed at "the AST census from F-01" without giving a command. So V-01's "state the removed line count" and the before/after census had no checkable bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now says exactly 7 removed lines (5 code plus the 2 trailing blanks), and records that review verified this boundary with ruff format. The census command is pasted verbatim, with the review-time output. V-01 now requires `{...: 1}` before, `{}` after, and `git diff --numstat` showing `0 7`. |
| PR-002 | LOW | IN-SCOPE | E / live-artifact convention | Plan Required tests and V-01 (5) | V-01 required the post-edit failure set to equal "the three pre-existing failures named in Required tests". Those are authoring-time live artifacts, and an execution-time baseline may differ. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now keys on the executor's own pre-edit baseline. Any failure present after the edit but not before is a regression (`failed`). The named three are kept as context only. |
| PR-003 | LOW | IN-SCOPE | G (execution contract) | `.aw/records/backlog/graduated/20260930-gateatrest-01-y2vnr7-...backlog.md` `- Status: graduated`; `runner_shared.process_backlog_close` | The post-gate text said the runner sets `y2vnr7` to `graduated` "on verification". The item is already `graduated`. After this plan executes, the runner's backlog-close step advances it to `done`. The gate also left the finalize owner implicit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate and Spec sync now say the item is already graduated and that `process_backlog_close` advances it. They forbid a hand `git mv` or a hand status edit. They also say the runner finalizes under `aw oc run`/`aw agy run`, and the executor runs `aw ipd finalize` when executing by hand. |
| PR-004 | LOW | IN-SCOPE | Evidence accuracy | `agent_workflows/check_engine.py` `getattr(_authoring, "_AUTHORING_PLACEHOLDERS", ())`; `git grep -n _backlog_done_dirs` | F-03 said there were "five `getattr(` sites, all on record objects". There are six, and one targets the `ipd_authoring` module with a fixed literal. F-02 said "four `.aw/records/` prose lines", but measurement finds 6 lines across 3 artifacts. Neither error changes a conclusion. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-03 and F-02 are corrected with the measured counts. Each states why its conclusion stands. The approval-gate prose now says thirteen findings, not twelve. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Which blank lines go with the function? | Delete the function plus its 2 trailing blanks (7 lines). The 2 preceding blanks stay as the separator. | Delete the preceding blanks instead. That gives the same final text, but it is a less natural diff and the plan's "do not touch the line above" reads more cleanly this way. | In-memory cut piped to `ruff format --check -`, which exited 0 | yes |
| D-2 | Should the deletion itself be treated as irreversible and escalated? | No. The code deletion is a private, never-called helper and can be restored with `git revert`. | Escalate as a blocking OQ. Rejected: no published interface (no `__all__`, leading underscore, 0 references), and nothing can depend on it. | F-01/F-03/F-13 re-measured at `ac9648ed5` | yes |
