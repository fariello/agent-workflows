# Review findings: plan yrq57q

- Subject-Id: yrq57q
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `a8cb09626`. The plan was committed and unchanged, so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review and `--phase review-finalize` clean after.

Re-driven at review HEAD (real functions, scratch repos under the system temp dir):
- (a) `_scope_path_entry_error(glob)` -> `None`; `parse_scope_paths` -> `([glob], False, [])`.
- (b) `_scope_match` True under `open/`, `graduated/`, `done/`; False for `...md.bak`, for a prefixed basename; `scope_entry_is_literal_file(glob)` False.
- (d) record in `graduated/`: literal `open/` -> `moved`; glob -> `[]`; nonexistent glob -> `[]`; nonexistent literal -> `vanished`.
- (e) receipt over `a.py, <glob>`: added `b.py` -> `eligible=True`, accept True; added glob -> `eligible=False`, reason "...DIRECTORY or GLOB...".
- New: record in `done/`: literal -> `moved-terminal`; glob -> `[]`. `runner_shared.execute_item_core` refuses dispatch on `moved-terminal`/`vanished` from the same predicate.
- `runner_shared.compute_scope_reconciliation` auto-acks declared-but-unmodified paths under a runner.
- Spec Section 4.5 and the "Implicit lifecycle-artifact allowances." paragraph exist; spec lives in `implemented/`. Both READMEs carry `## Execution contract in every plan's gate`. Highest decision is `### D162`.
- `.aw/system/managed-sections.json` records the template at `a51a115c...`; the file hashes `b782b27e...` (pre-existing drift from `2d6247e41`/`e490e228c`). `15df1952f` refreshed a manifest hash in the same commit as its edit.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | F. Honest documentation | `runner_shared.execute_item_core` "planstale 6h8j1r E-04 ... item-local dispatch refusal on moved-terminal or vanished literal Scope-Paths"; review probe (glob -> `[]`) | The plan presented the mistyped-glob blind spot as limited to `aw check`. It also bypasses the runner's dispatch-time `vanished` refusal, and under a runner the finalize backstop is auto-acknowledged, so the guidance as specified would understate the cost. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-06; E-04/E-05 now state that the dispatch refusal is also skipped; OQ-01 and the Deferred row now cite F-06; E-01 (f) and E-02 (f) pin the `moved-terminal` vs `[]` split at the predicate. |
| PR-002 | MEDIUM | UNDER-SCOPE | C. Operability (install manifest) | `.aw/system/managed-sections.json` entry for `templates/plans-README.md` `sha256` `a51a115c...`; disk `b782b27e...`; precedent `15df1952f` | E-05 edits a shipped, manifest-hashed template without refreshing its recorded hash, which leaves the install consent/drift manifest wrong (it is already wrong today). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the manifest to Scope-Paths; E-05 sets that one `sha256` to the new file hash; V-05 demands `sha256sum` beside the manifest diff; added F-07. |
| PR-003 | LOW | IN-SCOPE | E. Test organization | E-02 "Pin: (a) ... (e)" | Pins were not required to be separate tests, so V-02's mapping could collapse into one test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires each pin to be a separately named test. |
| PR-004 | LOW | IN-SCOPE | G. OQ ownership | OQ-01/OQ-02 `- Owner: none` | Resolved questions decided by the author recorded no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set to `plan author`. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | Gate "SCOPE FENCE: do not expand scope casually" | The fence wording lacked `--scope-ack`, and the gate lacked an open-question status line. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reworded as a declaration with `--scope-reason`/`--scope-ack`; added an OQ status line. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does the newly found dispatch-refusal bypass change OQ-01's recommendation? | No; keep optional guidance and state the cost | Withdraw the recommendation; add a code fix to report non-matching globs (out of this guidance plan's purpose, already Deferred) | The bypass only matters for a mistyped or deleted glob target; finalize still lists it; adoption is near zero (F-04) | yes |
| D-2 | Refresh the template's manifest hash in this plan? | Yes | Leave it to a later sync (it is already drifted) | `15df1952f` precedent; the edit would otherwise widen the drift | yes |
