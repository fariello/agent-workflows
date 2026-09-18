# Review: fix aw doctor's environment probe, child h90ij1 (Set doctorprobe)

- Subject-Id: h90ij1
- Subject-Type: ipd
- Reviewed-At: 2026-09-12
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `bba372a8`. Structural preflight `aw ipd lint --phase author` CONFORMED with zero findings
before semantic review, and `--phase review-finalize` CONFORMED after the revisions. No product code was
modified by this review.

DISCLOSURE, stated first because it bounds what this review is worth: I AUTHORED THIS PLAN in the same
session. A self-review cannot substitute for an independent one, so its value rests entirely on what was
EXECUTED rather than re-read. Nine things were run: every cited line range opened and compared against the
claim; `doctor.probe_environment(".")` executed and its `preset`/`backend`/`installed_version` read;
`engine.read_installed_version(".")` executed for comparison; both candidate config files parsed and their
key sets compared; a repo-wide grep for other `records_backend` readers; `cli._collect_repo_status_details`
executed directly on this repo; the function enclosing cli.py:6219 identified by name; its caller located;
and `aw status` run to see the user-visible surface.

THE FINDING THAT MATTERS MOST IS THAT THE PLAN CITED A PRINCIPLE AND THEN FAILED TO APPLY IT. Its own
Step 0 states that version resolution has ONE authority and that `doctor.py` is "the sole divergent
reader", which is why E-01 delegates rather than extends. That reasoning is correct for VERSION. But the
plan then proposed to fix the CONFIG read only in doctor, having never checked whether a second consumer
had the same defect. One does: `cli._collect_repo_status_details` (cli.py:6219-6226) reads
`repo/(".aw" if has_aw else ".agents")/"config.json"`, a file that does not exist in the `.aw` layout,
and it feeds `aw status` (cli.py:6367). Measured on this repo, it returns `preset: None`, `backend: None`
while correctly returning `installed: 1.2.1`. So the original plan would have fixed one command and left a
user-visible wrong answer in another, reproducing exactly the duplicate-authority pattern it was written to
remove. PR-001 adds E-05 and a shared reader, and adds `cli.py` plus `tests/test_cli.py` to `Scope-Paths`.

THE SECOND FINDING IS A TRAP IN THE FIX ITSELF. The plan instructed the executor to read `preset` from
`project.json` and `records_backend` from `config.json`, phrased as though each key lived in exactly one
file. It does not: `records_backend` is present in BOTH (`.aw/config/config.json` holds
`{"records_backend": "repository"}`, and `.aw/config/project.json` carries a `records_backend` key
alongside `preset`). An executor following the original wording would have hardcoded a precedence by
accident, and because both files currently hold the same value the mistake would pass every test and
surface only on future drift. PR-004 requires the helper to DEFINE and DOCUMENT its precedence, and records
OQ-02 to settle it from the writer side.

WHAT I VERIFIED AND LEFT ALONE. All six original findings hold as written. F-01's line range is exact
(doctor.py:355-357 reads `.aw/VERSION` then `.agents/VERSION`). F-02 reproduced: engine `1.2.1` versus
doctor `None`. F-03's masking mechanism is real (`not res.is_source_repo` at doctor.py:371). F-05's
claim about `.aw/config.json` is confirmed by direct `ls`: the path does not exist, and `preset` really is
in `.aw/config/project.json`. F-06's instruction to leave `--check-pypi` alone is correct and important;
doctor.py:387-395 deliberately compares against the RUNNING package, and "fixing" it would be a
regression. The E/V bijection, the RED-before-GREEN requirement, and the named four-failure pre-existing
baseline are all sound and were kept verbatim.

WHAT I DID NOT DO, stated plainly rather than left as a silent gap: I did not sweep the whole repository
for every other reader of these config files beyond the two now fixed. The shared helper E-02 introduces is
the structural answer (it makes the correct read the easy one), but a third divergent reader elsewhere
would still be possible today. That residual is recorded in the plan's own Scope check rather than hidden.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | G. Plan executability; C. Architecture | agent_workflows/cli.py:6219-6226 | The plan fixed the config read in `doctor.py` only, but `cli._collect_repo_status_details` contains the IDENTICAL defect and feeds `aw status`; measured `preset: None`, `backend: None` on this correctly installed repo. Fixing one consumer leaves the same wrong answer reachable from another, which is the duplicate-authority pattern the plan's own E-01 exists to remove. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-05 repointing `_collect_repo_status_details` at one shared reader introduced by E-02; added V-05 demanding both consumers agree; added `agent_workflows/cli.py` and `tests/test_cli.py` to `Scope-Paths`; recorded as F-07. |
| PR-004 | MEDIUM | IN-SCOPE | A. Correctness | .aw/config/config.json; .aw/config/project.json | E-02 told the executor to read `preset` from `project.json` and `records_backend` from `config.json` as if each key lived in one place; `records_backend` exists in BOTH. An executor would hardcode a precedence by accident, and since both files currently hold `repository` the error would pass tests and surface only on drift. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Rewrote E-02 to require an explicit, documented precedence in the shared helper; recorded as F-08; opened OQ-02 to settle which file is authoritative from the writer side (non-blocking, since both values agree today). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the second defective consumer (`cli._collect_repo_status_details`) be fixed in THIS plan or filed separately? | Fix it here, via a shared reader both consumers use. | (a) File a separate backlog item, keeping this plan doctor-only; (b) fix cli.py inline with a duplicated correct path list. | Rejected (a) because the plan's stated purpose is removing a divergent reader, and shipping a fix that leaves a second divergent reader in `aw status` would contradict the plan's own Step 0 reasoning. Rejected (b) because a duplicated path list is the defect, not the fix: engine.py:5705-5719 is cited in the plan as the single-authority precedent. | yes |
| D-2 | Should the `records_backend` precedence be settled now or left to execution? | Left to execution as non-blocking OQ-02, but the plan now REQUIRES an explicit documented precedence rather than permitting an incidental one. | (a) Pick `project.json` now on my own authority; (b) leave E-02's original ambiguous wording. | Rejected (a) because the authoritative writer is `install_wizard`'s persisted project policy and I did not trace every writer, so picking now would be a guess dressed as a decision. Rejected (b) because ambiguity is what makes the accidental-precedence bug likely. Both files currently hold `repository` on every repo measured, so no observable behavior depends on the answer today. | yes |
| D-3 | Does the plan need a concurrency or file-contention warning now that it shares `doctor.py` and `cli.py` with plan `z1yefm`? | No warning; declare the ordering edge on the DEPENDENT plan instead (`z1yefm` gained `Item-Dependencies: executed:h90ij1`). | (a) Add a "do not run concurrently" note to both plans; (b) merge the two plans into one. | AGENTS.md states the runner isolates every execute item in its own worktree and re-checks dependencies at dispatch, so file overlap is explicitly NOT a runtime hazard and warning about it wastes the maintainer's time. Rejected (b) because the two fix unrelated root causes (a misread path versus a hardcoded disposition) and carry different validation. | yes |
