# Review findings: plan jo55oo

- Subject-Id: jo55oo
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `d84e8b06f`. The pending plan matched the sealed lane input byte for byte and was committed, so no snapshot commit was needed. `aw ipd lint --phase author` and `--phase review-finalize` both reported `clean`. `- Kind: child`.

The cited mechanisms resolve. `host_sandbox_profile.forced_runner_safety_verdicts` is a restoring context manager, and `probe_runner_safety_capabilities` consults `_FORCED_RUNNER_SAFETY` before running a probe. The `_probe_fresh_verifier_session` note contains "ACCEPTED a reused session identity". The test file was last changed by `163874fcc` (psgyzw, +6 lines). F-4's four executed plans each cite `4dktme`. Siblings `a8yn86` (reviewed) and `r6ykw2` (to-review) are both pending and edit the same file.

The E-01 to E-03 shape was prototyped in a gitignored scratch copy, then deleted. Results are recorded as plan F-6.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E (test correctness) | Review prototype, frozen descriptor plus forced verdict: `MUTATED fail-gate verified False` (no `host_capability_unavailable`); `runner_shared.execute_item_core` later lifecycle gate | E-02's `assert item_mutated["status"] != "fail-gate"` would FAIL on the normal path. In this fixture the mutated item ends `fail-gate` even after it reached verification and was marked `verified`. The fix would turn a passing test red. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now discriminates on the `host_capability_unavailable` attempt key and the refusal code (`SKIP_HOST_CAPABILITY_UNAVAILABLE` via `render_stream.refusal_of_item`), and forbids a status assertion. Measured: the unforced, unfrozen run carries that key, so the assertion catches the regression. |
| PR-002 | MEDIUM | IN-SCOPE | G (coordination / traceability) | F-5 called `qkzet8` a duplicate to be closed by a human; `a8yn86` (From-Backlog `qkzet8`) is pending and also adds a comment and a parameter to `_drive_execute_turn` | The plan ignored the sibling that owns `qkzet8` and edits the same helper, so execution order could duplicate or clobber that edit. The Deferred row carried no carrier. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-5 rewritten to name `a8yn86` and `r6ykw2` with their split of responsibilities. E-01 and the gate now say to merge with a landed sibling. The Deferred row carries `Carrier: a8yn86`. The fixture mutation check allows `freeze_host_capabilities=False`. |
| PR-003 | LOW | IN-SCOPE | G (execution contract) | Original gate; the gate committed "<this plan>" but Scope-Paths omitted it; OQ-01 `Owner: none` | The gate had no scope declaration, no finalize ownership, and no paste-output rule. Scope-Paths was inconsistent with the commit, and OQ-01 had no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate, added the plan to Scope-Paths, and set OQ-01 `Owner: plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Keep this plan separate from `a8yn86`, or merge them? | Keep them separate, with explicit coordination. | Merge both into one plan; retire one as a duplicate. | They pin different behaviors (probe verdict plus decoupling here, pipeline refusal in `a8yn86`) and both are already authored. Sequencing is handled by the runner's per-lane merge-and-revalidate (AGENTS.md runner paragraph). | yes |
