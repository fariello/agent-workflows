# Review findings: plan nrdrv6

- Subject-Id: nrdrv6
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `cee68756c` in an isolated review lane. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified:
- The six writers and `set_blocks_release_line` in `agent_workflows/releases.py` match the plan's description. `releases` imports `selectors as _sel`. The callers are in `status_set` as listed in Step 0.
- F-02 exposure re-measured over 3661 tracked records: Priority 11, Work-Kind 11, Item-Dependencies 5, Graduated-To 5, From-Backlog 0, From-Spec 0 (matches).
- A probe that applies each WHOLE writer to `metadata_region` and reattaches the remainder (monkeypatched, nothing written) passed `tests/test_blocks_release_reader_bounding.py`, `tests/test_releases_line_writers.py` and `tests/test_status_set.py`: 142 passed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A. Data integrity | `releases.set_item_dependencies_line` anchor `re.search(r"(?m)^- Scope-Paths:[^\n]*\n", text)`; plan Deferred "the first anchor match is therefore in the region" | The Deferred claim is false. The anchor search runs over the whole text, so a writer can insert its line INTO THE BODY. With only the strip bounded, `set_item_dependencies_line(t, "none")` on spec `25kzda` (no in-region Scope-Paths, one in the body) added a SECOND `- Item-Dependencies: none` line at body line 530 (1754 -> 1755). The plan's own V-06 target would therefore have failed. `set_priority_line` on walkthrough `v0nmuv` inserted at line 233 of an 18-line region. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now applies each writer's whole strip-and-insert to the region (helper `_in_metadata_region(text, edit)`); E-02..E-07 updated; the Deferred bullet removed; F-06 added; E-08 (e2) anchor-in-body case; V-01/V-06/V-08 updated. The probe of this shape passed the existing tests (142). |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing | plan E-08 (h) `aw backlog set <id6> --work-kind bug` | That command exits 2 ("at least one target selector ... is required"); the positional form `aw backlog set open <id6> --work-kind ...` works. `bug` also triggers the release-gate warning path. Measured on the base code: the positional form deleted the body quote. | Overall: Low | FIXED | (h) now uses `aw backlog set open <id6> --work-kind feature --no-commit --dir <root>` on a `chore` fixture. |
| PR-003 | LOW | IN-SCOPE | G. Execution contract | plan gate | The gate said to "move the plan to executed/ through the tooled lifecycle transition" with no runner/manual split, and lacked the scope-fence declaration, the OQ status, `aw ipd begin`, and the MUST-paste wording. | Overall: Low | FIXED | Added; finalize is runner-owned, and a manual run uses `aw ipd finalize nrdrv6 ... --apply`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Bound only the strip (as authored) or the whole writer? | Whole writer on the region | Strip only (inserts into the body on `25kzda`/`v0nmuv`); a separate anchor-only bound per writer (two bounding sites per writer) | review probe, F-06 | yes |
| D-2 | Extend this plan or file a follow-up for the anchor search? | Extend this plan | Follow-up backlog item (leaves V-06 failing and a live duplication path once the strip is bounded) | V-06 as authored was unsatisfiable under strip-only bounding | yes |
