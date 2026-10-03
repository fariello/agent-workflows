# Review findings: plan 0b7fic

- Subject-Id: 0b7fic
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `36bfe1f06` in an isolated review lane. The plan was committed and byte-identical to the
lane input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` clean before
semantic review; `--phase review-finalize` clean after revision.

Verified from code and records: the `PERMISSION_TIMEOUT` `#:` block (`agent_workflows/lane_containment.py:1107-1121`)
carries exactly the hedge and the "Set this to 30 only together with a captured stream" sentence E-02 quotes;
`TurnBoundWatch.__init__` clamps `check_interval` to `nearest/4` (`lane_containment.py:1317-1325`), `_expired`
and `_run` match E-05's TIMING note (`:1363-1390`); the only turn-bound calls in the drivers are
`turn_bounds.note_progress()` (`oc_runipd.py:3164`, `agy_runipd.py:2679`); the deny posture is scoped under
the "ISOLATED TURNS ONLY" comment (`oc_runipd.py:2897`); spec R4.4b, A10b, A10c text matches the plan's
quotes (spec lines 348-359, 588-601); R4.4(a) still says "default 30 SECONDS" (spec line 325);
`8ctu3u`/`e6zeta` open, `3vh74b` and `uuh71v` approved in pending; research `7so8uz` carries
`consumed-by: [0b7fic]`, `status: active`, `outcome: answered`; `aw sanitize --agent` clean.

Prototype (`tmp/pr/permprobe.py`, gitignored, no production edit): real `{'a': [], 'b':
[('permission-timeout', 0.1)] at 0.104s interval 0.025, 'c': [], 'd': []}`; with `_expired` patched to
`lambda self, now: None`: `b` `[]` at the 2.002s ceiling, a/c/d `[]`. `git status --porcelain
agent_workflows/` empty.

Reachability probe: `ls .aw/records/runs` in the lane: "No such file or directory"; `.aw/.gitignore:14:records/runs/`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G. Reachability | `.aw/.gitignore:14` `records/runs/`; lane `ls .aw/records/runs` absent; `stall_progress.default_log_path()` resolves under the user data dir outside the workspace; `LANE_PERMISSION_POLICY` `external_directory: deny` (`lane_containment.py:785-788`) | E-01/V-01 demanded re-measuring two corpora that are unreachable from an isolated lane, and on absence ordered STOP and `blocked`, which also gated E-02/E-04. Under `aw oc run`'s default isolation the plan was unexecutable by construction. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01/V-01/E-06/V-06/scope-ack: attempt; if unreachable, record what was looked for, cite committed `7so8uz` as a dated measurement, phrase every figure as dated and cited, and proceed. The hard stop on a nonzero stdout permission count is kept for when the corpora are reachable. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing | `lane_containment.py:1317-1325` (clamp); `MAX_TURN_TIMEOUT` 4h makes `enabled` True by default; required-validation item 3 | With defaults, (a) runs at a 1.0s interval, and (b) had no stated wait shape, so the required `_expired` mutation could HANG rather than FAIL. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05: explicit small `check_interval` in every test, deadline-bounded poll for (b). Demonstrated split pasted. |
| PR-003 | MEDIUM | UNDER-SCOPE | D. Honest docs | Scope line, F-8, F-9 and gate promise the limits "belong in the documentation it writes"; E-02 did not require them | E-02/V-02 did not require the code block to name the isolated-only deny posture or antigravity's lack of one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added to E-02's instructions and Expected outcome, and to V-02 (vi). |
| PR-004 | MEDIUM | UNDER-SCOPE | D. Spec consistency | spec line 325 `(a) PERMISSION_TIMEOUT, default 30 SECONDS` | Recording option (ii) as permanent left R4.4(a)'s normative 30s default unqualified, which is the same contradiction one clause up. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04/V-04: qualify R4.4(a) without deleting it (A10b and OQ-01 own removal). |
| PR-005 | LOW | UNDER-SCOPE | G. Traceability | spec `## Workflow history` lines 14-15 `AMENDED ... (aw specs note)` | No instruction to record the amendment in the spec's history. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04: `aw specs note ... "AMENDED ..."`; V-04 pastes it. |
| PR-006 | LOW | IN-SCOPE | E. Validation commands | `pyproject.toml` addopts `-q -n auto` | `pytest ... -v` without clearing addopts does not show per-test names, which V-05 requires. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both commands use `-o addopts=""`. |
| PR-007 | LOW | IN-SCOPE | C. Cross-plan coherence | `3vh74b` E-07 (a) and its "UNPROVEN" docstring wording | Overlapping assertion, and the docstring wording will contradict the amended R4.4b. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-10 now carries a cross-plan note; the duplicate assertion is accepted. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | When the corpora are unreachable in the executing lane, block, or proceed on the committed research record? | Proceed, citing `7so8uz` as a dated, committed measurement, with figures phrased as such | Keep the STOP and `blocked` (no runner execution could ever complete it); require `--no-isolate-worktree` (widens the turn's permissions for a docs plan) | `.aw/.gitignore:14`; research `7so8uz` is tracked; P4 durable record; the argument rests on a committed measurement rather than an unmeasured one | yes |
| D-2 | Delete R4.4(a)'s 30s default or qualify it? | Qualify | Delete (needs A10b amendment, which is OQ-01's and `e6zeta`'s decision) | Plan OQ-01; spec A10b line 588 | yes |
