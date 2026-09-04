# Review: Add aw layout CLI command and workspace health check rule

- Plan-Id: 30jug9
- Reviewed-At: 2026-09-04
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 6

All claims verified at HEAD `16777ccc`, working tree clean, target plan committed and unchanged, so the
pre-review snapshot was correctly skipped. `aw ipd lint` conforming at `--phase author` and again at
`--phase review-finalize`.

RE-MEASURED LIVE:

- `aw layout` genuinely does NOT exist: argparse rejects it and enumerates every real verb. So E-01 is
  correctly net-new rather than an extension of something shipped.
- `aw migrate-layout` DOES exist, so F-2's tab-completion adjacency concern is real, and the
  read-only-inspection versus transactional-migration distinction is the right basis for keeping the
  names separate.
- `aw check reviews` still errors with "unknown artifact type 'reviews'", which is exactly the fence
  E-03 must assert flips to accepted while `aw check roadmaps` stays accepted. That pairing is the
  plan's strongest test idea: it catches a silent type DROP as well as the intended ADD.

The dependency edge is correct and non-obvious, so it is worth stating: `executed:hauwqh,executed:zvk796`
because this plan needs `hauwqh` for emission behavior and `zvk796` for the `reviews` noun its own V-03
asserts. Neither edge is decorative.

The severity design in E-02 is the sharpest thinking in this plan and I found no fault in it: because
the emitted artifacts are gitignored, a fresh clone legitimately has none, so "missing" must not be a
hard error or `aw check` would fail on every fresh clone BY DESIGN. Distinguishing (a) no workspace,
(b) installed-but-absent, and (c) present-but-drifted is the correct three-way split, and requiring the
severities be pinned by tests rather than prose is right.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | LOW | IN-SCOPE | A. Correctness (measurement staleness) | `grep -l 'agent_workflows/cli.py' .aw/records/plans/pending/*.ipd.md \| wc -l` -> 10 at HEAD `16777ccc`; plan claims 13 in F-5 and in the Scope check | THE `cli.py` CONTENTION COUNT IS STALE: the plan says 13 pending plans declare it, measured 10, the drop being siblings that have since executed. Low severity because the plan's actual protection is its re-measure-before-editing clause, which is correct and unaffected; the number is orientation. Worth fixing anyway because a reader who trusts 13 and measures 10 may conclude the plan is describing a different tree, and because this figure will keep moving as the queue drains. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-5 and the Scope check corrected to 10 with the HEAD it was measured at, plus an explicit statement that any count written in a plan is a snapshot and the re-measurement clause is what protects the edit. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the review also require `aw layout` to be added to the shell-completion surface, which the plan does not mention? | NO. Leave it to the declared contract. | Adding a completion requirement. Rejected on evidence: the plan already routes E-01 through `command_surface.py`, a `CommandDeclaration`, the `LIVE_SAFE_LEAVES` scenario, and `tests/conformance_matrix.py`, and this repo's own conformance suite is what enforces per-leaf surface obligations. Inventing an extra requirement here would either duplicate what the declaration already implies or contradict whatever the conformance matrix demands at execution time. | Plan E-01's CLI output contract clause; `Scope-Paths` including `command_surface.py` and `tests/conformance_matrix.py`; E-03's `make test-all` requirement | yes |
