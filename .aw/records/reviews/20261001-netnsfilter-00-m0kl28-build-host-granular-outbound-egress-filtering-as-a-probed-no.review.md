# Review findings: plan m0kl28

- Subject-Id: m0kl28
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `2f90a295f`. The plan was committed and unchanged, so no pre-review snapshot was needed.
`aw ipd lint --phase author --agent` was clean and `aw ipd coverage m0kl28` reported "ready for review" before
and after revision. `review-finalize` was clean after revision. No `IPD-S407`/`IPD-S408` repair attempts were needed.

Re-measured at review:
- All four children exist in `pending/` at `to-review` with `Item-Dependencies` chaining `none` -> `executed:nxh5s4` -> `executed:rozdkp` -> `executed:2j4pd0`, matching the child table.
- Cited symbols resolve: `DenyPushRemovedTests` (`tests/test_host_capability_extension.py:658`), `run_evidence.validate_finding_table` and `RC-COUNT` (`agent_workflows/run_evidence.py:2130`, `:2151`), `ACTION_CLASSES = (ACTION_READ_ONLY,)` (`agent_workflows/host_sandbox_profile.py:1666`), `RUNNER_ACTION_TO_CONTRACT_ACTION = {}` (`agent_workflows/runner_shared.py:33210`), `HardModeUnavailableError` (`host_sandbox_profile.py:211`), `CERTIFIED_PLATFORM` (`:201`), `oc_runipd._hardened_credential_paths` (`oc_runipd.py:2410`), `runner_shared.pinned_child_env` (`runner_shared.py:30375`), the presence-inference prohibition (`host_sandbox_profile.py:119`) and the `RUN-NO-PUSH` retirement comment (`run_evidence.py:1670`).
- Research `akmzyq` and `uq4y6q` exist under `.aw/records/research/`.
- `wn956n` E-05/V-05 owns the bare suite, Set lint, `aw check` delta, `aw sanitize --agent`, and `aw host capabilities opencode`.
- Backlog `sv9ce4` is `- Status: open`; its 2026-10-06 history says "re-run graduation to complete the handoff".
- Backlog `wcbpqf` is `graduated`; its only handoff plan `d5ntkj` is `not-executed`; its body mentions neither `netnsfilter` nor `m0kl28`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Orchestrator covers no own work | plan E-01 Expected outcome "A recorded per-host capability baseline naming which children are validatable here" | E-01's outcome described a deliverable (a baseline) that no child produces and that the runner's retirement would mark done unperformed. | all Low | FIXED | E-01 now confirms `nxh5s4` executed and that its V-01 carries the real-host verdict; it produces nothing of its own, and a False verdict is stated as a legitimate fail-closed outcome. |
| PR-002 | MEDIUM | IN-SCOPE | E. Evidence feasibility | Completion criterion "demonstrated with a real `git` invocation against a real remote"; `2j4pd0` E-05 "using parent-held endpoints so the test needs no external network" | The Set's done-criterion demanded a real-remote `git` run no child performs; child 03 deliberately tests hermetically. Unsatisfiable as written, or silently unmet at retirement. | all Low | FIXED | Criterion now names child 03 E-05/V-05's hermetic same-port test as the bar and records the authoring-time `git ls-remote` measurement as context. |
| PR-003 | MEDIUM | UNDER-SCOPE | G. Verification checklist strength | V-01..V-04 "reached `executed` with ..." | The V-items did not demand concrete pasted evidence (status line, post-transition lint) and left ambiguous whether to re-run or quote child evidence. | all Low | FIXED | Each V-item now demands the pasted `Status: executed` line, post-transition lint, and the named child V-items' evidence QUOTED from the child record. |
| PR-004 | LOW | IN-SCOPE | G. Lifecycle / provenance | gate "the runner sets `graduated`"; `sv9ce4` `Status: open`, history 2026-10-06 | The gate implied `sv9ce4` is or will automatically be graduated; the coverage demotion reopened it and graduation must be re-run. | all Low | FIXED | Gate now states the current `open` state and that graduation is re-run, ending `graduated`, never `done`. |
| PR-005 | LOW | UNDER-SCOPE | G. Execution contract | Approval gate | The gate lacked the scope-fence declaration wording (declaration, justify with `--scope-reason`, not a stop). | all Low | FIXED | Added. |
| PR-006 | LOW | IN-SCOPE | G. Carrier accuracy | OQ-02 `Carrier: wcbpqf`; `wcbpqf` body names only `denypush` decisions; `d5ntkj` not-executed | The carrier is live in `aw attention` (`active`) but its text does not mention this question, so a maintainer closing it could miss OQ-02. Editing the backlog item is outside this plan-only review. | all Low | FIXED | Added a dated review note under OQ-02 telling the maintainer to append the question to `wcbpqf` (or file a fresh carrier) when ruling. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the Set's completion criterion require a real-remote `git` run? | No; the hermetic same-port test in `2j4pd0` E-05 is the bar | Add a networked test to child 03 (non-reproducible, needs public internet in CI) | `2j4pd0` E-05 text; research `akmzyq` Findings 3-4 already measured the real-remote case | yes |
| D-2 | Does open, non-blocking OQ-02 prevent `go-pending-approval`? | No | `REVIEWED - OPEN QUESTIONS` / `no-go` | plan-review "A NON-BLOCKING open question does NOT make a plan NO-GO" (maintainer ruling 2026-09-10); every plan refuses to add a code regardless of the answer; precedent `rdjka2` review D-1 | yes |
| D-3 | Fix the `wcbpqf` carrier text in this review? | No; note it in the plan for the maintainer | Edit the backlog item (outside a plan-only review's authority) | plan-review "Review planning documents only" | yes |
