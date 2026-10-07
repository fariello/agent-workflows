# Review findings: plan e25iy9

- Subject-Id: e25iy9
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-101 (HIGH, fixed), PR-102 (HIGH, fixed), PR-103 (HIGH, fixed), PR-104 (HIGH, fixed), PR-105 (LOW, fixed), PR-106 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `23444560d`. The plan was committed and byte-identical to the lane
input, so there was no pre-review snapshot. `aw ipd lint --phase author --agent` returned `clean` before review, and
`--phase review-finalize` returned `clean` after revision. The plan is a `- Kind: child`, so S407/S408 do not apply.
The 2026-10-01 review's PR-001..PR-005 were re-checked and remain correct. Its finding ids are reused in the plan
text, so this round numbers from PR-101 to avoid collision.

Verified at HEAD: `lane_worktree_active`, `mint_driver_attestation`, `verify_driver_attestation`, `DRIVER_ATTEST_ENV`,
`DRIVER_ATTEST_FILENAME` and `ROLLUP_REFUSED_NO_DRIVER_ATTESTATION` are all defined in `ipd_lifecycle`. `hmac` and
`secrets` are used only by the token functions. `get_run_attestation` lazily mints. Both hosts pop `DRIVER_ATTEST_ENV`,
set `ROLE_WORKER` when `work_dir` is set, and export `RUN_ID_ENV`. The rollup passes `run_id=` and
`driver_attestation=get_run_attestation(run_dir)` to `retire_orchestrator`. `execute_item_core` gates `driver_begin` on
`if self_finalize and not is_review and not is_production:`. `7ckptx` is `approved` and `llbr2b` is `to-review`.
Order 01 `urv602` is still pending (`reviewed`, `go-pending-approval`), which the declared `executed:urv602`
dependency handles.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | HIGH | UNDER-SCOPE | Rubric D/G (deletion surface) | `tests/test_commit_scope_reason.py` (`self.attestation = LC.mint_driver_attestation(run_dir)`; three `driver_attestation=self.attestation` calls to `LC.finalize`) | A fourth consumer of the deleted symbols was missing from the plan's site table and from `- Scope-Paths:`. E-04 would break the whole class at `setUp`. The plan's bare `attestation` search term also matches the unrelated `run_analytics_submit.build_receipt(attestation=None)`, inviting a wrong deletion. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | File declared. E-06 drops the mint and the keywords and keeps every `env={}`. The analytics hit is classified unrelated and untouched. Added F-18 and V-06 evidence. |
| PR-102 | HIGH | UNDER-SCOPE | Rubric D/E (environment-dependent tests) | `echo $AW_EXECUTION_ROLE` in this review lane prints `worker`. Direct `begin(` calls appear in 10 test modules; `tests/test_ipd_authoring.py` (2) and `tests/test_receipt_lane_record.py` (1) declare no role. `tests/support.py` `execution_role` docstring | E-02 gives `begin` an `env=None` -> `os.environ` role gate. Undeclared direct callers then pass in a human shell and fail under a runner, which is the exact defect class `support.execution_role` documents. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both files declared. E-02 requires `env={}` at each undeclared call, with the census re-derived at execution. V-02 requires the narrowed run to pass with `AW_EXECUTION_ROLE=worker` exported. Added F-19. |
| PR-103 | HIGH | IN-SCOPE | Rubric A/F (fail-closed boundary) | A fresh `git init` repo: `runs_repo_root` resolves to itself and `<root>/.aw/records/runs` does not exist. `urv602` E-06 arm (11): "pointing the resolver at an unreadable or absent root" yields UNDETERMINABLE | E-03 makes every `begin`/`finalize` consult the predicate and refuse on UNDETERMINABLE. If Order 01 reads an ABSENT runs tree (any repo that never ran the runner) as UNDETERMINABLE, the manual lifecycle is refused everywhere. That contradicts this plan's Goal, and nothing checked for it. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 now requires driving the landed predicate on an absent tree and getting NOT HELD before wiring the refusal, and STOPs otherwise (prerequisite defect, not absorbed). E-08 pins the case. Added V-03 evidence and F-20. |
| PR-104 | HIGH | IN-SCOPE | Rubric A/G (E-10 incomplete) | `execute_item_core` skips `driver_begin` when `self_finalize` is false while the item is `running` (in `urv602`'s HELD allowlist) under a held `driver.lock`. E-05 forbids `AW_RUN_ID` defaults | E-10 shape (a) un-labels the delegated agent, but that agent's `begin`/`finalize` then hits E-03's holder check against its OWN live run, with no way to pass its run id. The plan stays stranded and V-10's demanded proof cannot pass. | C:Medium; U:Low; S:Low; F:Low; Overall:Medium | FIXED | E-10 now requires passing the run id EXPLICITLY (the `--run-id` flag named in the turn prompt), only when `self_finalize` is false, never via `AW_RUN_ID`. The default worker path carries none, so E-05's fence and D2 hold. Added V-10 evidence and F-21. |
| PR-105 | LOW | IN-SCOPE | Rubric G (open questions) | OQ-01/OQ-02 both `- Status: open` with complete rationales; D3 at `.aw/records/backlog/open/20260926-lifegate-01-dvonrn-...backlog.md` ("REFUSE (maintainer ruling)") | Two questions that the evidence already answers were left `open`. PR-104's prompt-borne run id settles OQ-01. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 resolved to an argv `--run-id` flag (reviewer-owned, Decision D-2). OQ-02 resolved by citing D3, with the absent-tree boundary added. |
| PR-106 | LOW | IN-SCOPE | Rubric G (execution contract) | Gate section "EXECUTION CONTRACT" | The gate had no scope-fence declaration and no `--scope-reason`/`--scope-ack` route, although `status_set.py` is declared as possibly unmodified. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a scope-fence paragraph (a declaration, not a stop) that separates the two unsafe-prerequisite STOPs from scope questions. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How does the `--no-self-finalize` agent pass the holder check without the forbidden env default? | The run id is passed explicitly, named in that turn's prompt, only when `self_finalize` is false. | (a) Exempt `begin` from the holder check: forbidden by E-10's own text and it reopens fact 2. (b) Read `AW_RUN_ID`: violates the E-05 fence on the default worker path. (c) Make the predicate exclude the caller's lane: that is a location proxy, which P15 forbids. | `runner_shared.execute_item_core` self-finalize guard; `ipd_lifecycle.runner_owns_lifecycle_notice` conditional rationale; E-05 fence | yes |
| D-2 | OQ-01: argv or env for the holder exception? | Argv `--run-id` flag. | Purpose-named env var: works but cannot be told to an agent in a prompt, and it is one export away from leaking onto the default path. | PR-104 mechanism; authoring rationale (run id is not a secret, D2) | yes |
| D-3 | Should an absent runs tree be NOT HELD or UNDETERMINABLE? | NOT HELD. Only an existing but unlistable root is a discovery failure. | UNDETERMINABLE: it refuses every lifecycle transition in every never-run repository. | Plan Goal; D3 rules only on an unreadable LOCK; measured absent root in a fresh repo | yes |
