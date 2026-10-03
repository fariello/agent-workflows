# Review findings: plan 1xthrh

- Subject-Id: 1xthrh
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `45529f342`; the plan was committed (`3365e9fbb`) and
the tree clean, so no snapshot. `aw ipd lint --phase author` clean before review; after revision
`--phase review-finalize` clean (an `IPD-Z602` density advisory my first E-04 edit introduced was
removed by moving the rationale to Required tests). `- Kind: child`, so `IPD-S407` does not apply.

Re-measured and confirmed: `"(?:" + "|".join(three bodies) + ")" == agent_schema._HOME_PATH_RE.pattern`
is `True`, flags `32` on all four; `list(leak_sanitizer._FAIL_PATTERNS)` first three are
`home-path, users-path, windows-home`; `_REQUIRED_RULE_SUBSTRINGS` maps them to `("/home/",)`,
`("/Users/",)`, `("Users",)`, each a substring of its body; `_ALLOWED_PATHS` is exactly the five
files Step 0 names; both modules are stdlib-only at module scope; `run_analytics_export` reads
`_FAIL_PATTERNS.keys()`; `redact_home_paths` exists with the quoted docstring phrase; `scan_text`
over each candidate `"<name>": (r"<body>", ("<prefilter>",))` row returns `[]`; the six regression
modules give `119 passed in 40.76s`; `aw sanitize --agent` is clean. Concurrent pending plans
editing these files (`g8q99a`, `wqiofa`, `6rcby1`, `z7ci8k`, `wyy09f`) touch none of the three
detector definitions.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | D/E (anti-regression; vacuous test) | plan E-04 and Required tests "MUTATION SENSITIVITY"; V-04 mutation proof; review scratch model output `mutate=1 derived fused moved: True ... forked moved: False` | Every planned identity assertion also passes if E-02/E-03 are never performed, since the forked literals are byte-identical today (F-01). The planned mutation test only perturbs the renderer's input and compares renderer output, proving the renderer is not constant, not that consumers derive. V-04's "perturb the datum file" proof likewise stays green for derived consumers. The core deliverable (no re-fork) would be unpinned. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with subprocess derivation sensitivity (mutate datum before importing consumers, assert both compiled patterns and the prefilter follow); V-04 now demands a FORK proof (restore a literal in each consumer, show failure). |
| PR-002 | MEDIUM | UNDER-SCOPE | B (leak gate) | review probe: a prose example with a drive-letter `Users` path returns one `windows-home` `fail` finding; pattern rows return `[]` | E-01 asks for an explanatory docstring in a module not exempt from the sanitizer; an illustrative path example would fail `aw sanitize` and tempt an `_ALLOWED_PATHS` exemption. | all Low | FIXED | E-01 forbids example paths in the docstring/comments, with the measurement. |
| PR-003 | LOW | IN-SCOPE | E | V-01 `print(sorted(m.HOME_PATH_RULES))` | `sorted` hides the declaration order the plan calls load-bearing. | all Low | FIXED | `list(...)`, with the reason. |
| PR-004 | MEDIUM | IN-SCOPE | G (execution contract) | gate "STOP and do NOT widen scope"; no lifecycle paragraph | A STOP-on-scope directive is the wording the workflow says to remove; the gate also lacked the conditional begin/finalize ownership, the pre-transition lint rule, and staged-set verification. | all Low | FIXED | Scope fence restated as a declaration with `--scope-reason`; refuse-to-accept conditions kept for genuine behavior deltas; lifecycle, staged-set check and a concurrent-plans note added. |
| PR-005 | LOW | IN-SCOPE | G | OQ-01 `- Owner: none` | Self-resolved question should record its resolver. | all Low | FIXED | `Owner: plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Can a derivation test read a runtime value without violating P16 when it mutates a module before import? | Yes; subprocess mutation of the datum then asserting on consumers' compiled `.pattern` values is behavioral. | Source/AST check that consumers import the datum (forbidden by P16); identity-only tests (vacuous, PR-001). | AGENTS.md "NO CODE-PINNING TESTS" bans reading source, not observing runtime values; demonstrated with a scratch two-consumer model. | yes |
