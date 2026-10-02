# Review: Bound stderr against max_output_bytes with a per-stream cap

- Subject-Id: 75gxkj
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before the edits, and `--phase review-finalize` was clean after them. Before revision, `--phase pre-transition` reported `check.ipd-uncarried-obligation` on two stale carrier paths. After revision that finding is gone.

Re-verified at lane HEAD `f24bea8d1`:

- `capture_command` still slices only `stdout_raw`. Asymmetric probe: `5 5000 False 100`.
- The timeout path gives `124 219 '...\nCommand timed out.'`.
- The stdout mid-character case gives `3 'é\ufffd'`.
- A widened record validates `True`.
- `egywai` was finalized by `891f89d6e` and `emzbut` by `886fc4d58`, and both are now in `executed/`.
- `evidence_gate` with `truncated` forced True on the asymmetric record gives `gate True []`.
- `run_worker_process` with stderr at 500 bytes and a bound of 10 gives `worker 500 False`.
- `tests/test_capture_command_contract.py` and `tests/test_host_runner_output_bound.py`: `20 passed`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Anti-regression (D) | tests/test_host_runner_output_bound.py `test_stderr_remains_unbounded` (`assertEqual(len(res.stderr), 5000)`); tests/test_capture_command_contract.py `test_capture_command_key_set_per_call_shape` (`== BASE_SCHEMA_KEYS`) | The plan claimed ZERO coverage of `capture_command` (F-07). Two existing tests pin the old behavior. Both will fail after a correct execution, and neither file was in Scope-Paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote F-07. Added E-07/V-07 to update both tests, and added both files to Scope-Paths. |
| PR-002 | HIGH | UNDER-SCOPE | Architecture (C) | agent_workflows/host_runner.py `run_worker_process` injected-runner branch (`stdout_bytes[: packet.max_output_bytes]`) plus four "stderr is deliberately unbounded ... lijmwy" docstring and comment sites | `egywai` gave `run_worker_process` two branches that must behave the same. Fixing only `capture_command` makes them disagree on stderr, and four comment sites would still describe the old contract. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-06/V-06 and added `host_runner.py` to Scope-Paths. `RawWorkerResult` fields and `evidence_gate` are explicitly left unchanged. |
| PR-003 | MEDIUM | IN-SCOPE | Evidence currency | .aw/records/plans/executed/20260930-fqseay-01-egywai-...ipd.md; .aw/records/plans/executed/20260929-toolevtext-01-emzbut-...ipd.md | F-06, F-09, OQ-02, the gate text and the doc-sync text treat `egywai` and `emzbut` as pending. Both have executed. The E-05 rule against gate assertions rested on that stale premise. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote F-06, F-09, OQ-02 and the gate text. E-05 now pins the gate pair: declared bound passes, and the same record with `max_bytes` removed is rejected with `EV-TRUNCATED-OUTPUT`. |
| PR-004 | MEDIUM | IN-SCOPE | Plan executability (G) | `aw ipd lint --phase pre-transition` reported `check.ipd-uncarried-obligation` on the deferred rows' `pending/...egywai...` and `backlog/graduated/...fqseay...` paths | Two Carrier-Evidence paths no longer resolve. Pre-transition would have refused the finished plan. `- Carrier:` also cannot name a terminal artifact. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Repointed both rows to SATISFIED evidence at the `executed/` and `done/` paths, removed the `- Carrier:` lines, and confirmed pre-transition reports no carrier finding. |
| PR-005 | MEDIUM | IN-SCOPE | Correctness / honest record (A) | plan E-01 legacy-call rule; agent_workflows/run_evidence.py `build_tool_event` (`max_bytes` recorded only when supplied) | Writing both per-stream flags as `False` on a legacy-only `truncated=True` call claims that neither stream was truncated, which is the same kind of false claim the plan exists to remove. Also, the meaning of "disjunction" was undefined when both the legacy flag and a per-stream flag were passed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The new keywords now default to `None`. A call that passes neither leaves out both keys, following the `max_bytes` precedent. `truncated` is defined as the OR of all three inputs. `capture_command` always writes both keys. E-05 and V-01 were updated to match. |
| PR-006 | LOW | IN-SCOPE | Execution contract (G) | plan gate "moves this plan to `.aw/records/plans/executed/`"; OQ-01/OQ-02 `Owner: executor` | The lifecycle transition did not say who owns it, the runner or the executor. The self-resolved OQs gave `executor` as owner. The mutation-residue check also used `--stat`, which cannot see residue. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now says: the runner owns `aw ipd finalize`, or the executor runs it when executing by hand, and never a hand-rolled `git mv`. Owner is now `plan author`. The residue check now reads the full diff. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the plan extend the bound to `run_worker_process`'s injected branch? | Yes, in this plan (E-06) | Leave the branches out of step, or file a separate backlog item | egywai's parity contract in `tests/test_host_runner_output_bound.py` module docstring; `host_runner.run_worker_process` two branches | yes |
| D-2 | What should a legacy-only `build_tool_event` call record for the per-stream flags? | Leave both keys out | Write both `False` (the authoring choice), or copy the legacy value into both | `build_tool_event` records `max_bytes` only when supplied; plan's own "unknown rather than fabricated" intent | yes |
| D-3 | Should `capture_command` write the per-stream keys on unbounded calls too? | Yes, always both | Only when bounded | Avoids readers having to treat "unknown" as a separate case for capture records; `BASE_SCHEMA_KEYS` pin updated deliberately in E-07 | yes |
| D-4 | Should the plan now assert gate behavior? | Yes: declared bound passes, and with `max_bytes` removed it rejects | Keep the authoring ban | `egywai` executed (`891f89d6e`); measured `gate True []` | yes |
