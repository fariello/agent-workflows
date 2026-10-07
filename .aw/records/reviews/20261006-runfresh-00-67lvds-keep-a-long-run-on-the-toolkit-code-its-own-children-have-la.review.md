# Review findings: plan 67lvds

- Subject-Id: 67lvds
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T030816Z-4078927` at HEAD `845ece5b5`. The plan was
committed and byte-identical to the sealed lane input (rev-1); no snapshot needed. `- Kind: orchestrator`.
`aw ipd lint --phase author` clean before review. `IPD-S407`: no violations. `IPD-S408`: after revision the edited
text invalidated the recorded fingerprint (lint reported `IPD-S408` once); attempt 1: `aw ipd coverage 67lvds
--no-commit` re-asked the model, which returned `ready: true`, no findings, `written: true`; `review-finalize`
then clean. Rows: 6 -> 6.

Re-measured: all six child plans exist in `pending/` at `to-review`, each `- Set: runfresh`, `- Blocks-Release:
f33nrj` (release record `f33nrj` is `planned`), and their `- Item-Dependencies:` match the child table exactly;
`runner_shared.pinned_child_env`, `runner_shared.assert_child_tool_identity` and the module-level
`runner_shared._TOOL_IDENTITY_VERIFIED` dict exist; spec `7ckptx` A8 exists; `1f4faf` and `8mabmu` are under
`executed/`; `resume` reloads `set_sessions` from state (`runner_shared` "Set sessions" summary line).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G executability | 67lvds Scope check "lists only the five child plans"; `- Scope-Paths:` lists six | Stale count after Order 06 was added. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Now "six child plans". |
| PR-002 | MEDIUM | IN-SCOPE | D anti-regression / cross-child | 67lvds Cross-IPD "byte-identical before and after"; hohlc6 E-02 "compare the `state.json` snapshot ... ignoring the restart fields" of status, attempts, frozen options | Parent asserted a stronger proof than the owning child measures. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Cross-IPD bullet now states preservation is by construction via `resume` and the evidence is hohlc6 E-02's comparison; criterion 1 cites it. |
| PR-003 | MEDIUM | IN-SCOPE | C architecture / cross-child contradiction | 67lvds "Order 03 must reset the per-process identity cache"; re15ol conventions "THE CHILD-PIN CACHE IS PER PROCESS ... No code change is needed"; `runner_shared._TOOL_IDENTITY_VERIFIED` module-level dict | Parent demanded reset code the child correctly says is unnecessary after `os.execv`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten: fresh process starts empty; no reset code; Orders 03 and 05 assert a fresh `tool-identity-verified` event. |
| PR-004 | LOW | IN-SCOPE | E testing / traceability | 67lvds ONE DETECTOR "a fixture change to a non-Python file does not restart" attributed to Order 05; hohlc6 E-02 tests only the `.py` edit; 34zv7d V-01 covers `.md`/`__pycache__` | Check pointed at a child that does not own it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Re-attributed to 34zv7d V-01/V-02, re15ol E-01, hohlc6 E-02. |
| PR-005 | LOW | IN-SCOPE | G evidence feasibility | V-01..V-06 `grep -n '^- Status:'`; children carry OQ `- Status: resolved/open` lines (e.g. 7kczdo line 108) | The grep returns several lines; evidence ambiguous. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Each V now requires the first (front-matter) `- Status:` line. |
| PR-006 | LOW | IN-SCOPE | A correctness / OQ-01 basis | 67lvds OQ-01 "reads only metadata fields this Set does not add"; retirement also runs the coverage re-check, and 7kczdo changes `orchestrator_readiness` | Resolution omitted the coverage re-check path that Order 06 changes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 now covers the coverage path (changed only for unsaved answers; this plan's is recorded) and the Order 03 restart. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the parent keep the byte-identical whole-state claim and push it into hohlc6? | No; align the parent to hohlc6's field comparison | add a byte-identical assertion to hohlc6 (restart record and `driver.loaded_code` legitimately change state) | hohlc6 E-02; re15ol Scope (appends event and `driver.loaded_code` entry) | yes |
| D-2 | Does Order 03 need identity-cache reset code? | No | add an explicit reset (dead code after `os.execv`) | `runner_shared._TOOL_IDENTITY_VERIFIED`; re15ol conventions | yes |
