# Review findings: plan vddpml

- Subject-Id: vddpml
- Subject-Type: ipd
- Reviewed-At: 2026-09-22
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `c1859b5e` in an isolated review lane. The plan was committed and unmodified, so no
pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author --agent` exited `1` on
`IPD-Q501` (the blocking OQ-04 was still `open`), which is a STRUCTURAL finding and not a skip;
`--phase review-finalize` CONFORMS after revision. `aw check` was also run and reported
`check.ipd-uncarried-obligation` at `error` plus the lint diagnostic; both are now clear.

THE PROBLEM IS REAL AND THE PLAN'S SOURCE READING IS ACCURATE, which is worth stating before the findings
because every finding below is about IMPLEMENTABILITY rather than about a false premise. Verified in tree:
`platform_lock.probe_free` is three-valued and documents observing "WITHOUT creating, truncating, or
modifying anything"; `attention.get_active_runs_map` does restrict to runs "whose driver process currently
holds driver.lock"; `driver.lock` genuinely IS per-run (`oc_runipd.run_lock` / `agy_runipd.run_lock` both
build `run_dir / "driver.lock"`), so F-4's scoping diagnosis is exactly right; the
`--allow-uncovered-orchestrator-work` justification precedent exists with `kind="str"` and argparse
enforcing the reason; `engine._wire_optin_precommit_hook` exists with the four callers named; and the
AGENTS.md managed block is generated from `engine.py`. The retracted silent-revert claim is correctly
retracted, and backlog `yuffut` carries the same correction, so the provenance chain is honest. The
plan also correctly weakens its own justification to wasted work plus peer invisibility, which is the
kind of self-correction that makes a plan trustworthy.

FIVE DEFECTS WERE MEASURED, NOT REASONED, and each would have produced a guard that looks correct and is
not:

```text
# PR-001, from inside this lane worktree
run_viewer.discover_run_dirs(Path("."))            -> 0 run dirs
attention._resolve_runs_repo_root(Path("."))       -> <the MAIN checkout root>, not the lane
run_viewer.discover_run_dirs(<that root>)          -> 242 run dirs
runner_shared.state_root(Path("."))                -> <lane>/.aw/records/runs     (does not exist)
```

So a peer query written the obvious way (the docstring of `get_active_runs_map` mentions
`discover_run_dirs`) reports NO PEER from every execute lane, which is where execute items run by default.
`get_active_runs_map` is correct only because it resolves first.

```text
# PR-003, by construction: inject ONE undeclared flag into the closed table
RUN_POLICY_FLAGS_BY_FLAG['--allow-concurrent-driver'] = object()
-> FAIL test_the_spec_and_the_owned_table_agree_in_both_directions
   "registered here but NOT in spec 2.1's grammar: ['--allow-concurrent-driver']"
# and unmodified:
python3 -m pytest tests/test_run_flag_surface.py -> 70 passed
```

The flag surface is a CLOSED LIST asserted against the spec FILE, so E-04 was unimplementable as written
while the plan stated its `Scope-Paths` "contains none, deliberately".

```text
# PR-004, on the existing shared-symbol bindings
integrate_lane_branch: oc is agy -> False; oc is runner_shared -> False   (wrapper binding)
state_root:            oc is agy -> True;  oc is runner_shared -> True    (re-export)
```

E-05's "same function object" assertion therefore FAILS for a correct wrapper-shaped guard, which is worse
than having no test: it punishes the right implementation.

PR-002 is a quoted contract rather than a measurement, and it is the most dangerous of the eight.
`platform_lock`'s module docstring states "BLOCKING IS OPT-IN AND HAS EXACTLY ONE CALLER ... it is the ONLY
caller permitted to pass it. Adding a second blocking caller needs its own justification, because ... an
accidental block would HANG a driver rather than fail it." Policy B REQUIRES waiting, so this plan is that
second caller, and it proposed no bound. An integration runs a full suite, so an unbounded wait is
operationally indistinguishable from the hang that rule exists to prevent, and it can consume a night
silently. The plan's own stated hazard ("a guard which refuses too eagerly makes the driver unstartable")
was inherited from the policy-A framing and was therefore aimed at the wrong failure mode; it now names the
hang.

PR-005 corrects an over-claim about OQ-04's strongest option. `.pre-commit-config.yaml` records that
`pre-merge-commit` "does NOT run for a fast-forward merge (no commit is created)", and
`runner_shared.integrate_lane_branch` publishes with `git merge --ff-only` first, falling back to `--no-ff`
only when main advanced. So the hook is silent on the driver's clean serial path and fires only when the
merge was already non-trivial. It is not worthless (a raw hand `git merge` that creates a commit is caught)
but it is not "the only option that stops raw `git merge`" in general, and the separate plan the maintainer
files for it should inherit the measured limit rather than the stronger claim.

PR-006 is a process defect worth naming because it cost the plan every lint checkpoint: OQ-04 was marked
`Blocking: yes / open` while its own rationale ended "RECOMMENDATION: do (i) and (ii) in this plan, and file
(iii) separately ... The executor must NOT implement (iii) under this plan", and E-07/E-08 already implement
exactly that pair. The decision was recorded and the flag was not updated, so `IPD-Q501` refused the plan
for a question that was already answered. Resolved from the plan's own text, not from reviewer preference.

NOT FLAGGED, checked and correct: the `Work-Kind: bug` plus `Blocks-Release: next` pairing is required by
the repository's live-bug rule and is present; `From-Backlog: yuffut` resolves and that item is
`graduated` with the same gate, so the handoff is provable; the eight E-items are right-sized (one concern
each) and the E/V bijection is complete with concrete evidence demands; the gate already carried the
honesty rule and the path-scoped commit/never-push contract; and the cross-checkout exclusion is sound for
this repository (`records_backend: repository`), with the one `companion`/`home` caveat now noted in the
plan rather than left as an unstated assumption.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. Correctness / C. Operability | Measured in this lane: `run_viewer.discover_run_dirs(Path("."))` -> `0`; `attention._resolve_runs_repo_root(Path("."))` -> the main checkout; the same call there -> `242`; `runner_shared.state_root(Path("."))` -> `<lane>/.aw/records/runs` (absent) | The peer query would return EMPTY from every lane worktree, which is where execute items run by default, so the guard would silently report no peer in precisely the situation it exists for. `get_active_runs_map` is correct only because it resolves the runs root first; its docstring points a reader at `discover_run_dirs`, which does not. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now requires the existing `attention` resolver (not a third one), and V-01 requires the lane-worktree case as evidence; E-06 covers it as a regression. |
| PR-002 | BLOCKER | IN-SCOPE | C. Architecture and operability | `agent_workflows/platform_lock.py` module docstring: "BLOCKING IS OPT-IN AND HAS EXACTLY ONE CALLER ... the ONLY caller permitted to pass it. Adding a second blocking caller needs its own justification, because ... an accidental block would HANG a driver rather than fail it" | Policy B requires a WAITING acquire, making this the second blocking caller, and the plan specified no bound, no progress output, and no expiry behavior. An integration runs a full suite, so an unbounded wait is indistinguishable from a hang and can consume a night with no output. The plan's stated hazard was still the policy-A one (refusing too eagerly), so the real failure mode was unmitigated. | C:Medium; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | E-03 now requires amending `platform_lock`'s sole-caller sentence with this caller's justification, a BOUNDED wait with a stated timeout and progress output, and an expiry that defers/re-queues rather than failing the lane. V-03 demands that evidence; E-06 covers the timeout arm; the gate now names the hang as the hazard. |
| PR-003 | BLOCKER | UNDER-SCOPE | G. Executability / spec sync | Proven by construction: injecting one undeclared flag into `RUN_POLICY_FLAGS_BY_FLAG` turned `tests/test_run_flag_surface.py::test_the_spec_and_the_owned_table_agree_in_both_directions` RED ("registered here but NOT in spec 2.1's grammar"); unmodified the file is `70 passed`. `SPEC_PATH` resolves to `.aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` | E-04 was UNIMPLEMENTABLE as written. `RUN_POLICY_FLAGS` is a closed list whose membership is asserted against the spec FILE, so the escape-hatch flag cannot be registered without amending spec `25kzda` 2.1 in the same change, yet the plan stated its `Scope-Paths` contained no spec path "deliberately" and deferred the spec sentence to a later pass. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | The spec file is now DECLARED in `Scope-Paths` (which also makes both runners announce and reconcile the edit); E-04 requires the amendment in the same change and names the sanctioned alternative (`DECLARED_BUT_NOT_OWNED_HERE` with reason and owner); V-04 requires the flag-surface file green plus whichever route was taken; the spec-sync section explains why the contract change is worth making. |
| PR-004 | HIGH | IN-SCOPE | E. Testing and verification | Measured: `oc_runipd.integrate_lane_branch is agy_runipd.integrate_lane_branch` -> False, `is runner_shared.integrate_lane_branch` -> False (thin wrappers binding `host_label`/`action_kind`); by contrast `state_root` is identical across oc/agy/runner_shared | E-05's "both hosts resolve to the same guard function object" holds only for a bare re-export. If the guard is bound as a wrapper (the shape this codebase uses for host-varying shared symbols), the authored assertion FAILS against a CORRECT implementation, which is worse than no test because it punishes the right design. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now requires the assertion FORM to match the binding shipped (object identity for a re-export, delegation for a wrapper, the form `tests/test_runner_shared.py` already uses), and V-05 fails an identity assertion made against a wrapper. |
| PR-005 | MEDIUM | IN-SCOPE | C. Architecture / honest documentation | `.pre-commit-config.yaml`: `pre-merge-commit` "does NOT run for a fast-forward merge (no commit is created)"; `runner_shared.integrate_lane_branch` publishes `git merge --ff-only` first with a `--no-ff` fallback only when main advanced | OQ-04 called option (iii) "the only option that stops raw `git merge`", and E-08 risked presenting `--ff-only` as the safety net. Both over-claim: the hook is blind to the driver's own happy path, and `--ff-only` refuses only a DIVERGED tip, not a peer advance the local branch can still fast-forward over. A reader who takes `--ff-only` as sufficient will skip the lock, which is the behavior that caused the incident. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-08 must state the `--ff-only` limit and present the lock as the mechanism with `--ff-only` as the backstop; OQ-04 now carries the measured hook limit so the separate plan inherits the honest claim; F-11 records it. |
| PR-006 | HIGH | IN-SCOPE | G. Executability / lifecycle gates | `aw ipd lint --phase author` exit `1`, `IPD-Q501` (line 144): "OQ-04: BLOCKING question is still 'open'"; the same question's rationale ends "RECOMMENDATION: do (i) and (ii) in this plan, and file (iii) separately ... The executor must NOT implement (iii) under this plan", and E-07/E-08 already implement that pair | OQ-04 was flagged `Blocking: yes / open` while being ANSWERED IN ITS OWN BODY, so the lint gate refused the plan at every checkpoint for a decision already recorded. The plan could not have been begun in that state. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-04 set to `Blocking: no / Status: resolved` with the resolution taken verbatim from its own recommendation, carrying `- Finding: PR-006` and retaining the original rationale rather than deleting it. Lint now conforms. |
| PR-007 | HIGH | UNDER-SCOPE | C. Architecture and operability | `aw check` rule `check.ipd-uncarried-obligation` (severity `error`): "6 obligation(s) name no durable carrier ... once this plan reaches `executed` it classes `done` in `aw attention` and this vanishes with no record" | All six `## Deferred / out of scope` rows named no durable carrier, so each outstanding obligation would silently disappear from the attention view when this plan finalized. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Each row now carries a `- Carrier-Declined:` stating why nothing is outstanding (shipped contract, already discharged, out of scope by construction, or resolved into E-03). The `pre-merge-commit` row declines because filing (iii) is the maintainer's scoping decision, not this plan's to pre-commit. `aw check` now reports ZERO findings for this plan. |
| PR-008 | MEDIUM | IN-SCOPE | G. Executability | plan E-03 as authored ("either REFUSE to start (policy A) or proceed with integration serialized (policy B)") versus OQ-01 `Status: resolved` to policy B; the gate still read "OQ-01 IS BLOCKING AND MUST BE ANSWERED ... before E-03" | E-03 and the gate were left in the pre-decision conditional form after OQ-01 had been resolved, leaving an executor to re-choose a concurrency policy the maintainer already settled, and pointing the guard at the STARTUP seam when policy B belongs at the integration seam. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now states policy B unconditionally and places the lock at the shared `runner_shared.integrate_lane_branch` seam both hosts already reach through wrappers; the gate records both questions as resolved and drops the stale blocking instruction. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The blocking OQ-04 was still `open`, refusing the plan at every lint checkpoint. Resolve it or ask the maintainer? | Resolve it as options (i) and (ii) in this plan with (iii) filed separately, taken from the question's OWN recorded recommendation. | (a) Ask the maintainer again - rejected: it would re-ask a question the maintainer already answered in the body of the question, wasting a round trip on a recorded decision. (b) Leave it `Blocking: yes` and report `NO-GO` - rejected: the plan would stay unexecutable for a decision that exists, and `IPD-Q501` would keep refusing `aw ipd begin`. (c) Set `Blocking: no` but leave it `open` - rejected: the answer is recorded, so `open` would be false. | The question's own rationale: "RECOMMENDATION: do (i) and (ii) in this plan, and file (iii) separately ... The executor must NOT implement (iii) under this plan"; E-07 and E-08 already implement exactly (ii) and (i) | yes |
| D-2 | Where does policy B's lock belong, and does the plan's declared `Scope-Paths` support it? | At the shared `runner_shared.integrate_lane_branch` seam, with the lock file under the resolved runs root rather than any run directory. | (a) The startup seam, as the authored E-03 said - rejected: policy B serializes integration, not starts, so a startup lock would either refuse (policy A behavior the maintainer declined) or hold across the whole run. (b) A per-run lock path - rejected: that is exactly the scoping defect F-4 records. (c) A new lock module - rejected: the plan's own scope forbids adding a lock implementation and `platform_lock` already suffices. | `runner_shared.integrate_lane_branch` is the single shared implementation both hosts reach via thin wrappers binding only `host_label`/`run_checked`/`action_kind`; `oc_runipd.run_lock`/`agy_runipd.run_lock` build `run_dir / "driver.lock"`, confirming the per-run scope F-4 names | yes |
| D-3 | Must the spec amendment happen in THIS plan, or may it follow as the plan proposed? | In this plan, with the spec file declared in `Scope-Paths`. | (a) Defer the spec sentence, as authored - rejected: measured, the flag cannot be registered at all without it, so deferring means shipping a red suite. (b) Skip the flag entirely - rejected: it is the plan's escape hatch and the repository's precedent requires a recorded justification rather than no override. (c) Register the flag outside the shared table - rejected: that forks the parser per host, which E-05 exists to prevent. | `tests/test_run_flag_surface.py` parses `SPEC_PATH` (`20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`) and failed by construction on an undeclared flag; the file is `70 passed` unmodified | yes |
