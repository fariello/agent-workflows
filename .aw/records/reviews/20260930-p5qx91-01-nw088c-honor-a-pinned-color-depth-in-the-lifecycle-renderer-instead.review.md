# Review findings: plan nw088c

- Subject-Id: nw088c
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `9f33a6eb4`. The plan file was committed and clean
(`git status --porcelain` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, one `info` `IPD-Z602` density
advisory on E-02, which the plan already examines on its merits in its conventions section and keeps
whole with a reason I agree with). This plan's own first `- Kind:` bullet reads `child`, so the
`IPD-S407` orchestrator child-row check does not apply.

THIS IS THE BEST-EVIDENCED DIAGNOSIS I HAVE REVIEWED IN THIS SWEEP, and I could not fault any of it.
I re-derived every load-bearing measurement by driving the code on a real PTY and in isolated
config homes, not by reading prose, and the plan's numbers came back character for character.

WHAT REPRODUCES EXACTLY:

- F-01 reproduces on a REAL PTY with an isolated `XDG_CONFIG_HOME`, pin `none`, no flags. The escape
  set is `['0', '1;38;5;208', '1;38;5;220', '1;38;5;45', '1;38;5;46', '38;5;244']`, identical to the
  plan's recorded list, with `any '38;5;' = True`. A user who pins the lowest tier really does get
  256-color ANSI.
- F-02 reproduces verbatim. `Term.lifecycle_depth`'s final line is
  `return DEPTH_16 if depth == DEPTH_16 else DEPTH_256`, and the method's docstring really does claim
  it satisfies "R9.3a.2's requirement", so the function advertising ladder compliance is the one
  breaking it.
- F-03 reproduces, and it is the decisive evidence the plan says it is. At pin `none`:
  `resolve_color_depth(FakeTTY())` is `none`, `Term.lifecycle_depth()` is `256`,
  `Term.style_lifecycle_text(...)` is `'\x1b[1;38;5;208mblocked\x1b[0m'`, and
  `Palette(True).lifecycle(...)` is `'blocked'`. At pins `16` and `256` the two agree exactly
  (`'\x1b[1;35mblocked\x1b[0m'` and `'\x1b[1;38;5;208mblocked\x1b[0m'`). The repository cannot be
  right in both branches, so this is a defect and not a design choice.
- F-04 reproduces: the resolver is correct at every rung (its one wrong CONCLUSION is PR-001 below).
- F-05 REPRODUCES CELL FOR CELL, which matters because it is the clause most at risk of being
  "simplified" away. Staging all three implementations against the same pins and streams:

      pin=16   default TTY  shipped 16   naive 16    override 16
      pin=16   pipe+color   shipped 256  naive none  override 16
      pin=256  pipe+color   shipped 256  naive none  override 256
      pin=none both streams  shipped 256  naive none  override none

  The naive one-line fix really does kill color for `--color` into a pipe at every pinned tier.
- F-06 reproduces. Zero `class` definitions of either name across `tests/`; three surviving
  mentions, two in `agent_workflows/term.py` docstrings (inside `should_color` and
  `resolve_color_depth`) and one comment in `tests/test_runner_shared.py`.
- F-07 reproduces: `grep -rln "COLORTERM\|256color" agent_workflows/*.py` returns `term.py` only.
- F-09's grep reproduces and is more important than the plan treated it as (see PR-001).
- The spec and carrier claims all check out: the Section 9.3 sentence
  "`tests/test_term.py` asserts the single-originating-definition property" is present, the spec is
  `- Status: approved`, `aw specs note` exists and does what E-06(a) needs, and all four carriers
  resolve (`fnb8pl` open, `o53joz` open, `nzqj6m` open, `x3zno3` a real pending plan). `x3zno3`'s
  Deferred section routes `term.py` here with `Carrier: p5qx91` verbatim, and its own E-03 owns the
  `tests/test_runner_shared.py` mention, so the file partition is exactly as the plan describes.
- The maintainer ruling is quoted accurately from the backlog item, twice over (a `note` line and the
  body), so the no-structural-pins constraint is real and the plan's response to it is correct.

PR-001 IS THE ONE SUBSTANTIVE DEFECT AND IT IS IN THE COVERAGE, NOT THE FIX. E-05 proposed six
resolver precedence assertions. ALL SIX ARE ALREADY SHIPPED, in the same file, on the same fixture
E-05 planned to reuse. `tests/test_term.py::ColorDepthPrecedenceTests` already asserts `NO_COLOR`
plus a `256` pin resolving `none` (and again for a `16` pin), `FORCE_COLOR` beating `NO_COLOR`, pins
of `16`/`none`/`256` each resolving to themselves, and in
`test_rung3_and_rung4_detection_and_defaults` that `TERM=xterm-16color` and `linux` detect `16`,
an unknown `TERM` defaults to `256`, and `DEFAULT_COLOR_DEPTH == DEPTH_256`. The file is green at
28 passed. So E-05 as written would have duplicated a shipped contract, which is exactly what this
plan's own E-04 correctly refuses to do for the color-index table ("repeating it here would duplicate
a contract").

Worse, the duplication would have come at the cost of the gap that actually exists. F-09 measured
that `grep -rn "lifecycle_depth" tests/*.py` returns NOTHING, and the plan recorded that as
reassurance ("no existing test pins the buggy behavior, so the fix requires no assertion edit")
without drawing the obvious conclusion: the method E-03 fixes has ZERO tests, which is precisely why
the bug shipped while the resolver stayed correct. I also checked the one test that iterates all
three tiers, `EveryTierKeepsTheInvariantTests`, and it HAND-BUILDS its escapes
(`f"\033[38;5;{resolved.style.color}m..."`) rather than calling `Term`, so it exercises the tier
table and would not have caught this either.

The sharpest consequence is PR-002: nothing would have guarded `override=True`. The plan defends that
clause three times in prose (E-03's body, F-05, and the approval gate's "DO NOT DROP") but no test
asserts it. E-04 drives the CLI with `--color` into a pipe at the pinned tiers, which does exercise
the path, but through the full CLI where a regression would surface as a diffuse color change rather
than as a named failure; and E-05 as authored tested the resolver, which is not where the argument
lives. A later refactor dropping `override=True` would pass the suite. So I redirected E-05 onto the
consumer: four `lifecycle_depth` cells including an explicit `Term(stream=<pipe>, color=True)` with
pin `16` expecting `16`, plus the three-pin two-consumer agreement that F-03 measured. Net test
surface is the same size and strictly better aimed.

PR-003 and PR-004 are small. The suite baseline in E-02 records `1 failed, 3401 passed`; review
measured fully GREEN (`3692 passed, 2 skipped, 3 warnings in 71.36s`). The plan's Deferred row
already states that failure is time-dependent and instructs V-02 to record whichever state the
executor sees, which is the right instruction and is what survives, so this is a figures correction
rather than a logic one. And E-01's recipe says to call
`style_lifecycle_text("blocked", resolve_lifecycle("backlog","blocked"))`; `resolve_lifecycle` lives
in `term`, while `lifecycle_style`'s function is named `resolve`, so reaching for
`lifecycle_style.resolve_lifecycle` raises `AttributeError`. My own first probe hit exactly that, and
E-01 is the first thing the executor runs, so it is worth one clause.

ON THE RECLASSIFICATION (OQ-01), WHICH THE PLAN CORRECTLY FLAGS AS THE REVIEWABLE DECISION. I upheld
it. The item is `chore` with no gate; the plan is `bug` with `Blocks-Release: next`. The repository's
test is user-perceptible impact, and here the entire symptom is wrong bytes on the user's terminal,
measured on a real PTY, so there is no internal-only reading. The counterargument the plan itself
records (the pin is niche, so few users are affected) is correctly rejected: blast radius is not the
stated test, and the affected population is specifically the accessibility users the override exists
for. F-10's claim that the gate is the corpus norm also checks out in shape. I did not re-run
`aw check release-gates` as part of this review because the plan's own figure is about the corpus
rather than about this plan's conformance, and `aw check` is in the plan's validation set.

ON RIGHT-SIZING. Six E-items in three groups, and the decomposition is sound: two measurement items,
a one-line fix, two test items, one citation item. E-01 and E-02 being measurement-only is unusual
but correct here, because three of the four facts provably move under concurrent lanes and the plan
specifies narrowing or stopping on each outcome. E-06 bundles three citation edits across two files,
which I considered splitting; I did not, because they are one decision (what now holds the property)
applied three times, and V-06 verifies all three in one pass. No split recommended.

ON THE EXECUTION CONTRACT. Strong. It already carries path-scoped `aw commit` with never-push and
never `--no-verify`, the paste-actual-output honesty rule stated as a contract violation rather than
a preference, a declared spec amendment with the correct mechanism (`aw specs note`, not
`/spec-review`, with the reason that the latter would de-approve a release-gating spec), a correct
statement that the backlog item must not be closed `done` from the plan, and the tooled finalize
transition. I added one prohibition to the executor warnings (do not add resolver precedence
assertions) and promoted the `override=True` warning to name its new test guard.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | OVER-SCOPE | E. Testing and verification | `tests/test_term.py:829` (`class ColorDepthPrecedenceTests(_DepthTestBase)`), `:830` (`test_rung1_color_off_and_accessibility_convention`), `:882` (`test_rung3_and_rung4_detection_and_defaults`); `tests/test_term.py -o addopts=""` -> `28 passed` | E-05's six proposed resolver precedence cells are ALL already shipped, in the same file and on the same `_DepthTestBase` fixture it planned to reuse, so the item would duplicate a contract (which this plan's own E-04 refuses to do for the color table) while leaving the only untested depth surface uncovered. F-09 measured that `lifecycle_depth` has ZERO tests and the plan recorded it as reassurance instead of acting on it; `EveryTierKeepsTheInvariantTests` hand-builds escapes rather than calling `Term`, so it would not have caught this either. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 rewritten onto the `Term.lifecycle_depth` consumer: four cells plus the three-pin two-consumer agreement, with an explicit prohibition on adding resolver cells; V-05 now requires stating that `ColorDepthPrecedenceTests` was read; F-04's wrong conclusion and F-09's severity corrected; Goal, Proposed changes, Required tests, Scope check and the executor warnings updated; recorded as F-11. |
| PR-002 | MEDIUM | UNDER-SCOPE | D. Anti-regression | review probe: `Term(stream=<pipe>, color=True)` pin `16` -> shipped `256`, naive `none`, `override=True` `16`; `agent_workflows/render_stream.py` `Palette.lifecycle_term` docstring ("silently return `none` on a pipe, discarding the caller's decision") | F-05's refutation of the naive fix reproduces, but NOTHING in the suite would catch a regression of it. The plan defends `override=True` three times in prose and zero times in a test: E-04 exercises the path only through the full CLI, and E-05 as authored asserted the resolver, where the argument does not live. A later "simplification" would pass green. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 gains cell (d), `Term(stream=<fake pipe>, color=True)` with pin `16` expecting `16`, specified as required; V-05 must call it out and state what it reads without the argument; Required tests names it the second decisive validation; the approval gate's warning now points at it; recorded as F-12. |
| PR-003 | LOW | IN-SCOPE | G. Plan executability | plan E-02 Expected outcome ("`1 failed, 3401 passed, 2 skipped`") | The authored baseline is stale: review measured a fully green `3692 passed, 2 skipped, 3 warnings in 71.36s` with `tests/test_term.py` at `28 passed`. The plan's Deferred row already correctly states the failure is time-dependent and tells V-02 to record what it sees, so only the figures mislead. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02's Expected outcome carries both measurements and says a green baseline is legitimate and not to be hunted; Required tests restates the bar as no new failing node id against a self-measured baseline; recorded as F-13. |
| PR-004 | LOW | IN-SCOPE | Evidence accuracy (Step 1) | `agent_workflows/lifecycle_style.py` exposes `resolve`, not `resolve_lifecycle`; `grep -rn "def resolve_lifecycle" agent_workflows/` -> `term.py` only | E-01's measurement recipe names `resolve_lifecycle(...)` without a module; the function with that name is in `term`, while `lifecycle_style`'s is `resolve`, so one natural reading raises `AttributeError`. E-01 is the first thing the executor runs. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now names `term.resolve_lifecycle(...)` or `lifecycle_style.resolve(...)` explicitly and records the failure mode; recorded as F-14. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-05's cells are already covered. Delete the item, or redirect it? | Redirect it onto the untested `Term.lifecycle_depth` consumer, keeping the item and its dependency edge. | (a) Delete E-05 and rely on E-04's CLI coverage (rejected: that leaves `override=True` unguarded, PR-002, and leaves the fixed method with no direct test); (b) keep the resolver cells as "defence in depth" (rejected: duplicating a shipped assertion in the same file is what this plan's own E-04 refuses, and a duplicate that drifts is worse than none); (c) move the new cells into a separate new test file (rejected: `_DepthTestBase` and the shipped precedence class both live in `tests/test_term.py`, which is already declared). | `tests/test_term.py::ColorDepthPrecedenceTests` read in full; `grep -rn "lifecycle_depth" tests/*.py` returning nothing; the plan's own E-04 anti-duplication clause. | yes |
| D-2 | Should the review uphold the plan's reclassification from `chore` to `bug` with `Blocks-Release: next`? | Uphold it. | Reverting to `chore` with no gate (rejected: the symptom is entirely user-facing bytes, measured on a real PTY, so it is perceptible by construction; the niche-setting counterargument addresses blast radius, which is not the stated test, and the affected population is the accessibility users the override exists for). | `AGENTS.md`'s user-perceptible-impact test and its every-live-bug-gates-the-release rule; F-01 reproduced on a PTY; the plan's own OQ-01 which records the counterargument for exactly this challenge. | yes |
| D-3 | Is E-06's spec edit a weakening that should instead be escalated for human sign-off? | No. It is a citation correction plus a coverage restatement, correctly done with `aw specs note` at `approved`. | (a) Require `/spec-review` (rejected: the spec's own Section 12a records that its transition step would de-approve a release-gating spec, which the plan cites correctly); (b) restore the deleted class so the citation becomes true again (rejected: forbidden twice, by the maintainer ruling on this item and by P16, and the deleted classes were themselves P16 violations). | `aw specs note --help` confirming the verb appends history without changing status; the maintainer ruling quoted from the backlog item; the spec's Section 12a note the plan cites. | yes |
| D-4 | `x3zno3` is now `Status: reviewed` where this plan describes it as `to-review`. Does the partition still hold? | Yes, unchanged. No edit needed beyond noting it here. | Adding an `- Item-Dependencies:` edge (rejected: the two plans partition the citation set by FILE and neither reads the other's output; the runner isolates each item's worktree, so declared-file disjointness is sufficient). | `x3zno3`'s `- Scope-Paths:` (`runner_shared.py`, `test_runner_shared.py`, its own plan file) sharing no path with this plan's three; its Deferred row carrying `Carrier: p5qx91` verbatim. | yes |
