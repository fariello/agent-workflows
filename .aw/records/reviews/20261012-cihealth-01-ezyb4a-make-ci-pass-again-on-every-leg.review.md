# Review findings: plan ezyb4a

- Subject-Id: ezyb4a
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `3e328494b`. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize` was clean after revisions (one advisory `IPD-Z602` on E-01, see D-3).

Re-verified at review HEAD:
- `pyproject.toml`: `requires-python = ">=3.9"`, `dependencies = ["filelock>=3"]`, `filelock>=4` in both the `test` extra and the `dev` group.
- `uv pip compile --python-version 3.9` over the proposed markers resolved `filelock==3.19.1`, `mypy==1.19.1`; `--python-version 3.12` resolved `filelock==4.1.1`, `mypy==2.4.0`.
- `platform_lock._supports_preserve_lock_file` already gates the filelock-4-only keyword, so the runtime tolerates filelock 3.
- `typing.Self` is imported by `agent_workflows/egress_policy.py` (`from typing import Any, Callable, Self`, for `EgressBroker.__enter__`), not by the test file; the module has `from __future__ import annotations`.
- `contextlib.chdir` at `tests/test_run_dir_outcomes_parent_is_guaranteed.py` (one use).
- `python3.9 -m py_compile tests/test_check_engine_spec_criteria.py`: line 237 `SyntaxError: f-string expression part cannot include a backslash`.
- `python3 -m mypy agent_workflows` (mypy 2.3.1, py3.14 local): "Found 15 errors in 8 files (checked 193 source files)".
- Records job steps locally: `specs check` 0, `attention --check` 0, `check plans` 1 (173 findings; failing: `check.ipd-uncarried-obligation` ERROR, `check.review-decision-unescalated` WARNING), `check releases` 0, `check backlog` 1 (2 filename-grammar errors), `check release-gates` 0, dead status token scan 0.
- `artifact_core.drift_exit_code` exempts only `info`.
- `agy` is on PATH on the maintainer machine.
- `.github/workflows/tests.yml` type gate job runs on 3.12 via `.[test]`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Evidence / G | `python -m agent_workflows check backlog --agent` exit 1 ("Filename does not match artifact naming grammar", `m88gwh`, `upkghw`) | The records job fails on a second step (`check backlog`) masked by `check plans` failing first. The plan only named `check plans`, so fixing it would leave the job red. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern names cause (5); new E-07 owns every step of the records job; E-01 measures every step; F-06 added. |
| PR-002 | HIGH | IN-SCOPE | Correctness / V-05 | `artifact_core.drift_exit_code`; `check plans` emits `check.collisions-not-checked` (info) on every per-type run | V-05 demanded `"findings":0`, which is unsatisfiable: per-type runs always emit an `info` advisory, and `info` findings do not fail the step. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Bar is now exit 0 per step; `info` findings are explicitly expected (V-07). |
| PR-003 | HIGH | UNDER-SCOPE | E. Testing | `python3.9 -m py_compile tests/test_check_engine_spec_criteria.py` line 237 SyntaxError | A 3.9 to 3.11 collection error waits behind the 3.9 install failure; the plan's review-time list could not see it, and nothing required running under 3.9 locally (the maintainer machine is 3.14). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 names it with the fix; E-01 requires a 3.9 interpreter run; F-07 added. |
| PR-004 | MEDIUM | IN-SCOPE | Evidence / B. dependency contract | `agent_workflows/egress_policy.py` `from typing import Any, Callable, Self`; `pyproject.toml` `dependencies = ["filelock>=3"]` | The `Self` import is in production code, not the test file, and the suggested fix `typing_extensions.Self` would add a runtime dependency, a published-contract change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern and F-03 corrected; E-03 prescribes a quoted class annotation or a `TYPE_CHECKING` import and forbids a new runtime dependency. |
| PR-005 | MEDIUM | IN-SCOPE | G. Right-sizing | original E-05 bundled mypy fixes and record fixes | Two independent deliverables and test surfaces (code types vs. record conformance) in one item and one V-item. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into E-05 (types) and E-07 (records) with V-05 and V-07; E-06 depends on both; Proposed changes and Required tests swept. |
| PR-006 | MEDIUM | IN-SCOPE | E. Environment parity | local mypy 2.3.1 on 3.14; CI type gate on 3.12 with floating `mypy>=1.18,<3`; `agy` on maintainer PATH | The error set depends on the resolved mypy/filelock versions, and the `agy` tests pass locally only because `agy` is installed, so local runs could falsely clear E-04/E-05. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01/E-05 require the gate on 3.12 with the resolved version recorded; E-01/E-04 require a run with `agy` off PATH. E-05 now depends on E-02 too. |
| PR-007 | MEDIUM | IN-SCOPE | V-06 evidence | E-06/V-06 | A green run on an earlier main commit would satisfy the old wording. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06/V-06 require `git merge-base --is-ancestor` showing the run's head contains the plan's commits. |
| PR-008 | LOW | IN-SCOPE | G. Executability | `pyproject.toml` `ENVIRONMENT PIN FOR filelock (E-07)` comment | E-02 left the comment stating the >=4 floor unconditionally and did not say both the extra and the dev group must change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now updates both lists and the comment, and records the review's resolver demonstration. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should 3.9 get a filelock? | Environment markers: `>=4` on 3.10+, `>=3` below | Drop 3.9 (support-contract change, needs maintainer); pin filelock 3 everywhere (loses the type gate baseline) | `uv pip compile` demo at review (3.9 -> 3.19.1, 3.12 -> 4.1.1); `platform_lock._supports_preserve_lock_file` | yes |
| D-2 | How to replace `typing.Self` on 3.9? | Quoted class annotation or `TYPE_CHECKING` import; no new runtime dependency | `typing_extensions` runtime dependency (published contract change) | `pyproject.toml` `dependencies = ["filelock>=3"]`; `egress_policy.py` has `from __future__ import annotations` | yes |
| D-3 | Split E-01 for the `IPD-Z602` advisory? | Keep E-01 as one measurement pass | Split per environment (three items that share one table) | The clauses are one deliverable (one grouped table); advisory is `info` | yes |
