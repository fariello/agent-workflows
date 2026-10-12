# Review findings: plan lv0dvv

- Subject-Id: lv0dvv
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `9a8d4f092`. The pending plan matched the sealed lane input byte for byte and was committed, so no snapshot commit was needed. `aw ipd lint --phase author --agent` and `--phase review-finalize --agent` both reported `clean`. `- Kind: child`.

Re-measured with the lane package (`AW_NO_REEXEC=1`, isolated `XDG_CONFIG_HOME` under `/tmp/opencode`; the operator's real config was never written). F-08 reproduces: at pins `none`, `16`, `256` on a fake TTY, `status_256`, `path`, `badge`, `colorize`, `severity_label`, `format_fix` emit identical `38;5;`/SGR bytes while `lifecycle_depth()` returns the pin. A monkeypatched prototype of E-03 (no file edited) was run over the nine test files that assert `38;5;` at `TERM=xterm-256color` and `TERM=vt100` (`2 failed, 422 passed` both; the same two node ids fail at HEAD) and over `index plans`/`check`/`find backlog` in a synthesized fixture repo at each pin.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G (stale gate state) | commit `b76d48d38` (maintainer, 2026-10-12) "reclassify cvtg9u/y11p5u/lv0dvv as release-gating bugs per maintainer ruling that color_depth=none disables all color"; plan OQ-01 still `- Status: open` | The maintainer already ruled reading B, but OQ-01, the Goal, E-01 and the gate still described the ruling as pending, so E-01 would block forever on a stale question. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Transcribed the ruling into OQ-01 (`resolved`, `Owner: maintainer`, citing `b76d48d38`); rewrote Goal, E-01 and gate accordingly. Approval left to the maintainer. |
| PR-002 | MEDIUM | IN-SCOPE | A (correctness of the 16 mapping) | `agent_workflows/status_set.py:548` `term.color256(f"[{gate}]", 203, bold=True)`; review probe: plain nearest-RGB over the twelve `_SGR_*` codes maps 203 (255,95,95) to 90 (gray) | "Standard nearest-color reduction" was underspecified and, read literally, turns a red gate label gray at pin 16. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now specifies the exact RGB table, candidate set, a chroma guard (drop 37/90 when max-min >= 64) and tie-break, with the measured mapping of all seventeen live indices; E-04 (f) asserts it. |
| PR-003 | HIGH | IN-SCOPE | E (negative control) | Review run at HEAD (no fix): `find backlog --color` emits 0 escapes at pin `none` and 0 `38;5;` at `16` | E-04 cell (g) used `find backlog` as an end-to-end red cell, but its only escapes are lifecycle tokens, which already honor the pin, so the cell passes without the fix. Also `index plans` raised `FileNotFoundError` (no `INDEX.json` dir) in a fixture lacking `.aw/records/plans/pending/`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Cell (g) now drives `index plans` and `check` (measured: 2 `38;5;` at every pin at HEAD; 0 escapes at `none`, 0 `38;5;` at `16` with the prototype), requires the plans dir and isolated `AW_HOME`, and asserts exit 0. |
| PR-004 | MEDIUM | IN-SCOPE | E (negative control feasibility) | E-04 cell (f) tests a new symbol `color_16_for_index`; the negative control reverts `term.py` | A module-level import of the new symbol makes the reverted run die at collection, which proves nothing per cell. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 requires attribute access inside cell (f); expected outcome and V-04 now demand the file collects and cells (a), (b), (f), (g), (h) fail individually. |
| PR-005 | MEDIUM | UNDER-SCOPE | D (unstated behavior change) | `term.resolve_color_depth` rung 3 `_depth_from_environment` and `_TERM_16_MARKERS` (`vt100`, `linux`, `-color`, ...) | The plan claimed "unpinned is unchanged", but routing through the shared resolver also moves UNPINNED 16-detected terminals from 256 codes to 16 codes on the generic axis. Consistent with D42, but undeclared, untested and absent from the CHANGELOG. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Declared in Scope and Goal, added E-04 cell (h), extended the E-05 CHANGELOG bullet. |
| PR-006 | LOW | IN-SCOPE | G (execution contract) | Gate lacked the scope-fence declaration wording, conditional finalize ownership, and the explicit honesty MUST; OQ-02 `Owner: none`; F-03/F-04 counts measured on a now-drifted corpus | Gate incomplete per plan-review Step 4; stale-measurement drift. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate; OQ-02 owner `plan author`; F-03/F-04 and E-02 carry re-measured review evidence with the authoring counts as context. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Is OQ-01 answered, or still the maintainer's to answer? | Answered (reading B); transcribed with the maintainer as owner and the commit as evidence. | Leave open and NO-GO. | commit `b76d48d38` message and its diffs to `cvtg9u`, `y11p5u` and this plan's history line "Maintainer ruling 2026-10-12: pin none must disable all color (reading B)". | yes |
| D-2 | How should the 16-color reduction treat saturated colors near gray? | Chroma guard excluding 37/90 when max-min >= 64. | Plain nearest RGB (203 -> gray); an authored per-index table. | Review probe over the seventeen live indices; OQ-02 rationale. | yes |
| D-3 | Should unpinned 16-detected terminals change on the generic axis? | Yes, declared and tested. | Gate the generic axis on the pin only, bypassing detection (a second depth definition, contrary to R9.3a.2 "exactly one definition"). | `term.resolve_color_depth` docstring; spec `uonrjg` R9.3a.2; DECISIONS D42. | yes |
