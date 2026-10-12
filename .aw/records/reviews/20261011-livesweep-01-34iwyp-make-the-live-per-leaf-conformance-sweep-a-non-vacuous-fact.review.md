# Review findings: plan 34iwyp

- Subject-Id: 34iwyp
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `b1b2fab2b`. The plan was committed (`f2d1897fe`) and byte-identical to the
lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` before review; `--phase
review-finalize`: `clean` after revision. Not an orchestrator (`- Kind: child`), so S407/S408 do not apply.

Verified: `LIVE_SAFE_LEAVES` has 16 members; `run_cli` pins env, uses pipes and `stdin=DEVNULL`;
`test_live_safe_leaves_exit_contract_membership` is `slow` + `timeout(500)` and pins `len == 16`; `19313eed7^` and
`3ec1c2d5a^` sources recover as cited; conftest arms are 60s CPU / 240s wall. Re-measured (review probes over
`tests.conformance_matrix.run_cli`): F-01..F-05 timings and banners reproduce (cheap leaves <= 3.1s; `attention` 5.6s;
`status` 3.4s; the three banner leaves emit as stated, agent `clean`, bad flag rc 2).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric E (vacuous gate), plan goal | `tests/conformance_matrix.py` `run_cli` (`capture_output=True`); review probe: every cheap leaf zero ANSI over pipes WITHOUT `NO_COLOR`; over `pty.openpty()` 7 cheap leaves emit ANSI without and none with `NO_COLOR` | E-02's no-color test over `run_cli` passes whether or not `NO_COLOR` is honored, reproducing exactly the vacuity the plan exists to remove. V-02's `FORCE_COLOR=1` falsification also does not test the property: `FORCE_COLOR` beats `NO_COLOR` (both set -> ANSI, measured). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-07: `run_cli_tty` (pty, Windows skip) plus a default-collected contrast test over a measured `COLOR_EMITTING_LEAVES`; E-02/E-03 use it; V-02 falsifies by dropping `no_color=True`; F-09 and V-07 added. |
| PR-002 | HIGH | IN-SCOPE | Rubric D/E (flaky gate) | `config.config_dir` (XDG_CONFIG_HOME else `~/.config`); review probe: `record-history f36de0` with a sidecar line renders `History for f36de0`, no banner; `list-repos` renders a table when config names repos | Two of three curated parity leaves change SHAPE (not just value) with machine-local state, so the non-vacuity assertion would fail on any machine whose config or sidecar is populated. OQ-02's resolution asserted the opposite. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04/E-05 require a `tmp_path` project with `HOME`/`XDG_CONFIG_HOME`/`AW_HOME` pinned (measured: all three banner, agent `clean`); OQ-02 rewritten; F-10 added. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric A (extractor correctness) | `3ec1c2d5a^:tests/conformance_matrix.py` `semantic_facts_from_human` loop `for tok in toks[:2]`; `term.ASCII_GLYPHS["findings"] == "FAIL"`; probe: `FAIL FINDINGS  3 found` -> `fail` | Recovering the old token rule misclassifies the ASCII banner and, once the `AW ` title guard is relaxed for shape (b), lets a glyph-less row like `STALE  /path` read as an outcome. E-04 also said "add CONFORMS if absent" when it is present. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 anchors the banner on a first token in `GLYPHS`/`ASCII_GLYPHS` values and the status as token 2; E-05 unit cases cover both glyph sets and the real `ipd lint` row; F-11, V-04 updated. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric E (tautological assertion) | E-06 "the two partitions are disjoint and their union equals `LIVE_SAFE_LEAVES`"; E-01 defines cheap as the complement | Disjointness and union are true by construction and V-06's fake-leaf probe would NOT fail (a new safe leaf lands in the cheap half). The non-trivial property is `LIVE_HEAVY_LEAVES <= LIVE_SAFE_LEAVES`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 asserts the heavy-subset property; V-06 falsifies with a heavy name absent from `LIVE_SAFE_LEAVES`. |
| PR-005 | MEDIUM | UNDER-SCOPE | Rubric G (doc sync) | `CONTRIBUTING.md` step 6 ("... `test_live_safe_leaves_exit_contract_membership` (marked `slow`, which runs in CI under `continue-on-error: true`)") | E-06 renames/splits that test and makes the cheap half enforcing, so a contributor doc becomes false; the plan said "N/A". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `CONTRIBUTING.md` added to Scope-Paths; E-06 updates the sentence (no em/en dashes); V-06 demands the diff. |
| PR-006 | LOW | IN-SCOPE | Rubric G (live-artifact bar, stability) | E-01 "over 5s per invocation"; review: `attention` 5.6s, `status` 3.4s; E-01/E-02 count bars | A 5s cutoff would flip `attention`/`status` between partitions run to run, and E-01/E-02 used counts as bars. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Named heavy members fixed; re-measurement only adds (pair > 8s); bars restated as complement/membership properties. |
| PR-007 | LOW | UNDER-SCOPE | Rubric G (execution contract, ownership) | Gate paragraph; OQ-01/OQ-02 `Owner: none` | Gate lacked scope-fence-as-declaration wording; resolved OQs named no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate amended; owners recorded. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to make the no-color scenario observable? | Pty transport (`run_cli_tty`) plus a color contrast test; Windows skips with a named reason. | `FORCE_COLOR=1` + `NO_COLOR` (rejected: FORCE_COLOR wins, measured); drop the scenario (rejected: backlog `2wowfy` item 1 asks for it); `--color` flag (rejected: also overrides NO_COLOR per its help "beats NO_COLOR"). | review pty probe; `run_cli(force_color=True, no_color=True)` probe; `--color` help text. | yes |
| D-2 | Keep `list-repos` and `record-history` as parity leaves? | Yes, only in an isolated tmp project/HOME/XDG/AW_HOME. | Drop them (rejected: only `runs query` would remain, below E-04's floor of two); use the live repo (rejected: shape varies, measured). | review isolation probe; `config.config_dir`. | yes |
| D-3 | Which partition property to assert? | `LIVE_HEAVY_LEAVES <= LIVE_SAFE_LEAVES`. | Disjoint + union (rejected: tautological given the complement definition). | E-01 definition. | yes |
| D-4 | Heavy threshold rule? | Fixed named set; re-measure only adds a leaf whose pair exceeds 8s. | Per-invocation 5s cutoff (rejected: `attention` sits at 5.5-5.6s). | review timings; F-03/F-04. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
