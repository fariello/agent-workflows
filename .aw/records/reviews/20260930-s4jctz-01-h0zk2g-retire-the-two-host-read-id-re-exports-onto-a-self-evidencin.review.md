# Review findings: plan h0zk2g

- Subject-Id: h0zk2g
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `fe2ee961c` in an isolated review lane. Plan committed and byte-identical to the sealed lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent` clean (one IPD-C801 advisory) before
semantic review; `--phase review-finalize` clean with no advisory after revision.

Re-verified (read-only probes; scratch files under `.aw/state/` removed):
- Both imports and comment blocks unchanged at HEAD; `oc_runipd.__all__` has 23 entries incl. `_ANSI_CODES`,
  `_ANSI_RESET`, `_ANSI_STRIP_RE`, `_one_line`, `_strip_ansi`; `hasattr(agy_runipd, "__all__")` False.
- `oc_runipd._read_id is selectors.read_front_matter_id` and the agy twin: True/True; `_read_status` on neither host.
- Readers on `- Id:` / `-  Id:` / `-\tId:`: `read_front_matter_id` -> `abc123` x3; `selectors._read_id` -> `abc123`, `None`, `None`.
- `runagy._read_id is agy_runipd._read_id` -> True.
- ruff `0.16.3` and hook-cached `0.4.4` (`--isolated --select F401`): `as read_front_matter_id` -> pass; `as _read_id` +
  `__all__ = ["_read_id"]` -> pass; bare `as _read_id` -> F401. Confirms F-4/F-5 on both versions.
- `ruff check --select F401` on both hosts: two `Invalid # noqa directive` warnings, `agy_runipd.py:74`, `oc_runipd.py:830`.
- `tools/ipdrunner/test_runagy.py`: `11 failed, 14 passed`; `test_read_deps_and_set` fails at line 271 on `_read_status`.
- Bare suite: `2 failed, 5219 passed, 2 skipped, 3 warnings in 354.05s`; both failures in
  `tests/test_readiness_absence_invariant.py` (live-corpus), unrelated.
- Carriers `gte0pd`, `fh8x8k` open.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | MEDIUM | UNDER-SCOPE | G. Executability | `tools/ipdrunner/test_runagy.py:272` `self.assertEqual(driver._read_deps(text), ["dep001", "dep002"])`; commit `72bb113e7` deletes `def _read_deps` from both hosts | E-04 fixes only `_read_status`, but the next line of the same test calls `_read_deps`, which is gone too, so E-04's expected outcome (the test passes; 11 -> 10) was unreachable. `_read_item_dependencies` returns `([], None)` on the fixture, so it cannot stand in. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now also drops the `_read_deps` assertion with a one-line comment citing `72bb113e7`; V-04 demands the edited test body and a one-test diff; F-13 added. |
| PR-202 | LOW | IN-SCOPE | G. Live-artifact criterion | Required tests `3387 passed, 2 skipped`; V-03(a) `at least 3388 passed`; F-9 three named failures | Suite count bars were stale at review (bare suite now 5219 passed, with two different failures). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required tests, V-03(a), V-05(d) and the gate now compare failing node ids against a pre-edit run at execution HEAD. |
| PR-203 | LOW | IN-SCOPE | Citation durability (IPD-C801) | lint advisory "citation 'oc_runipd.py:825' has no durable anchor" | The ruff-warning citation was a bare line offset that had already drifted to 830. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Anchored on the quoted prose string in E-05, F-10 and V-05; lint advisory cleared. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Drop the `_read_deps` assertion or reintroduce a reader? | Drop it with a cited comment | Reintroduce `_read_deps` on the host (rejected: reverses `72bb113e7`'s deliberate retirement of the legacy field); reroute to `_read_item_dependencies` (rejected: returns `([], None)` on the fixture) | commit `72bb113e7` message; probe output | yes |
