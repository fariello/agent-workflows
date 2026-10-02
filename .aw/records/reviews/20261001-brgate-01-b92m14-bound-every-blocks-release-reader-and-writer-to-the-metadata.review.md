# Review: Bound every Blocks-Release reader and writer to the metadata region

- Subject-Id: b92m14
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged at lane HEAD `b64d92e86`, so the pre-review snapshot was skipped. `aw ipd lint --phase author` and `--phase review-finalize` were both clean.

Every cited symbol was re-located by symbol:

- The unbounded readers:
  - `status_set._format_status_transition_line` `m_br` (unanchored)
  - the `ipd_lint` board `m_br` (unanchored)
  - the `attention` plans `br_m` pair
  - three `releases._ITEM_BLOCKS_RELEASE_RE.search` sites
- Three `status_set` `[ \t]*`-strict gate reads: two `_existing_m` and one `_carrier_m`.
- `check_engine`'s single unbounded `_META_BLOCKS_RELEASE_RE.search(item_txt)` in the done-candidate loop, beside the bounded `_read_blocks_release`.
- The dead `status_set._BLOCKS_RELEASE_RE`.
- `selectors.metadata_region` and the public reader pair.

Importing `agent_workflows.selectors` loads none of `releases`, `status_set`, `attention`, `check_engine`, `ipd_lint`, `backlog` or `specs`, so the import is acyclic.

`set_blocks_release_line(7w6zsl, "next")` was driven in process and removed the body quote at line 22.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Live-artifact criteria (G) | plan V-05 "showing `190`, `868` and `0`"; V-08 "pass count must rise"; review probe `blockers 218 sentinel 928 check 0` | V-05 used authoring-time counts of a LIVE population as its bar, and those counts have already moved, so a correct execution would fail. V-08 also used a pass-count bar on a suite whose failure set is order-dependent (F-10). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-05 now measures before and after in the same session, and any delta must be explained by named out-of-region records. V-08 now compares failure sets by name. F-13 was added. |
| PR-002 | MEDIUM | IN-SCOPE | Evidence accuracy (E) | `.aw/records/backlog/graduated/...7w6zsl...backlog.md` line 4 `- Blocks-Release: next` (front matter) and line 22 (body); probe diff `['+- Blocks-Release: next', '-- Blocks-Release: next', '-- Blocks-Release: next']` | E-07 and V-07 expected "one line added to front matter" on a record that already carries the gate. The correct post-fix diff is empty, so the authored bar could not be met by a correct fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 and V-07 now expect an empty diff on the real record (read in process, never rewritten), plus a fixture case without the gate that shows one line added. |
| PR-003 | MEDIUM | UNDER-SCOPE | Deferral ownership | plan Deferred "Carrier: FILE ONE"; review exposure probe Priority 7, Work-Kind 7, Item-Dependencies 4, Graduated-To 3 | The deferral of the six sibling writers had no carrier, only an instruction to file one later, even though the defect class is measurably live. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Filed backlog `7afjyu` (bug, `Blocks-Release: next`, Set brgate) with the measured exposure. Deferred now cites it. |
| PR-004 | LOW | IN-SCOPE | Claim accuracy | `production_checks.spec_plan_gate_carry`, `production_checks.backlog_gate_handoff`, `runner_shared.populate_manifest_specs` each call `_ce._META_BLOCKS_RELEASE_RE.search` on whole texts | E-06's outcome "check_engine has no remaining unbounded read" could be read as the pattern being deletable or the family being fully bounded. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 now scopes the claim to `check_engine`'s own code, names the three external callers, and states that the constant stays. |
| PR-005 | MEDIUM | UNDER-SCOPE | Execution contract (G) | plan "Approval and execution gate"; E-03 "Leave the third ... converted" | The gate had no scope fence with `--scope-reason`/`--scope-ack`. It also gave an unconditional `aw ipd finalize` instruction, used `aw commit <plan>`, and had no `5e533q` close path. Separately, E-03's "Leave ... converted" was ambiguous. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the fence, conditional runner/executor finalize ownership, `aw commit b92m14`, and the HANDOFF close. E-03 now reads "ALSO convert". E-08 gained case (f), a `-` removal that is bounded to front matter. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should V-05 bound the corpus aggregates? | A same-session before/after comparison, with any delta explained by named records | Updating the fixed numbers to 218/928, which would rot again | rubric G re-derivation convention; probe at HEAD `b64d92e86` | yes |
| D-2 | Should the sibling-writer carrier be filed now or at finalize? | Now, as `7afjyu`, a gated bug | Leave it to the executor | measured exposure; AGENTS.md "every live bug gates the next release" | yes |
| D-3 | Should the three external `_META_BLOCKS_RELEASE_RE` callers be brought into scope? | No. Keep the author's exclusion and scope E-06's claim instead. | Widen to `production_checks.py`/`runner_shared.py` | plan Scope check (they read spec/plan texts whose region is unambiguous) | yes |
