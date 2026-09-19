# Review findings: plan z8ddk0

- Subject-Id: z8ddk0
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `3a513262`. The plan on disk was byte-identical to the sealed lane input (`diff`
empty) and `git status --porcelain` was clean, so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author --agent` reported `clean`, 0 findings, exit 0, both before and
after the revisions.

THE DIAGNOSIS IS CORRECT IN EVERY PARTICULAR, WHICH I ESTABLISHED BY RE-EXECUTING RATHER THAN READING.
All four claimed defects reproduce: `FORCE_COLOR='0'` yields COLOR to a PIPE in both `term.py` and
`runner_shared.py`; `TERM=dumb` yields color in `runner_shared.py` and plain in `term.py` (and so does
`TERM=''` and `TERM` unset, which the plan did not separately claim but which follow from the same
omission); `pwatch` ignores `FORCE_COLOR` entirely; and the `FORCE_COLOR=''` half-count at
`term.py:100`/`:103` is real. The plan's framing that this blocks `uonrjg` R9.3a.2's one-definition
requirement is also right, and the decision to make this a depth-0 child ahead of `pow5sj` is correct.

So every finding below is about the FIX, not the diagnosis. There are three of consequence and they
share one root: **the plan describes the intended end state accurately and never describes the edit that
reaches it**, so each of the three named source changes has a shortest-path implementation that a
competent executor would reach for and that is wrong in a way the plan's own validation would not catch.
I found each by simulating the naive edit and measuring the result.

**1. E-01's literal reading creates an accessibility regression worse than the defect (PR-901, HIGH).**
`term.py` reads `FORCE_COLOR` TWICE: by PRESENCE at `:100`, where it CANCELS `NO_COLOR`, and by
TRUTHINESS at `:103`, where it forces. E-01 said "`FORCE_COLOR` INTERPRETS its value, so
`0`/`false`/`no`/`off` mean NOT FORCING and fall through", which names the second site only. I applied
exactly that edit and measured the 4x4 grid:

```text
NAIVE E-01 grid (TERM=xterm-256color):
  NO=''     FORCE=''     -> TTY=True  PIPE=False   <<< NO_COLOR SET YET COLOR ON A TTY
  NO=''     FORCE='0'    -> TTY=True  PIPE=False   <<< NO_COLOR SET YET COLOR ON A TTY
  NO='0'    FORCE=''     -> TTY=True  PIPE=False   <<< NO_COLOR SET YET COLOR ON A TTY
  NO='0'    FORCE='0'    -> TTY=True  PIPE=False   <<< NO_COLOR SET YET COLOR ON A TTY
  NO='1'    FORCE=''     -> TTY=True  PIPE=False   <<< NO_COLOR SET YET COLOR ON A TTY
  NO='1'    FORCE='0'    -> TTY=True  PIPE=False   <<< NO_COLOR SET YET COLOR ON A TTY
```

All TWELVE cells where `NO_COLOR` is set and `FORCE_COLOR` is present colorize on a TTY, including
`NO_COLOR=1 FORCE_COLOR=0`. That is strictly worse than the bug being fixed: the headline defect gives a
user unwanted color when they asked for none in ONE variable, while this gives it when they asked for
none in the variable that is the accessibility convention the entire maintainer ruling defers to. The
correct composition (measured for contrast) yields plain in all twelve. E-01 now mandates ONE forcing
predicate consulted at both sites, which closes the split structurally rather than at one site, and E-05
pins all twelve cells so the naive edit fails.

**2. E-02's deliverable as worded breaks four shipped guards, three of which exist to assert the
opposite of what it says (PR-902, HIGH).** E-02 said convert `runner_shared` to "consume the single
definition instead of reimplementing it", with the expected outcome "exactly one `should_color`
definition in the package". Read literally that means delete the `def` and import the symbol. But three
separate harnesses assert that `runner_shared` DEFINES this name. I ran the real guard methods against a
patched source rather than reasoning about them:

```text
===== SHAPE A (import, no local def) =====
  FAIL  test_runner_shared.py::PureMoveFingerprintTests.test_every_clean_symbol_is_a_STRICT_fingerprint_match
  FAIL  test_runner_shared.py::SingleDefinitionTests.test_exactly_one_definition_package_wide
  FAIL  test_runner_refork_guard.py::SymmetricReForkGuardTests.test_the_owning_module_really_defines_every_tabled_symbol
  FAIL  test_rununify_run_queue.py::TheClosureClassificationIsPinned.test_the_shared_resolving_names_really_do_resolve_in_runner_shared

===== SHAPE B (one-line delegating wrapper) =====
  FAIL  test_runner_shared.py::PureMoveFingerprintTests.test_every_clean_symbol_is_a_STRICT_fingerprint_match
  PASS  test_runner_shared.py::SingleDefinitionTests.test_exactly_one_definition_package_wide
  PASS  test_runner_refork_guard.py::SymmetricReForkGuardTests.test_the_owning_module_really_defines_every_tabled_symbol
  PASS  test_rununify_run_queue.py::TheClosureClassificationIsPinned.test_the_shared_resolving_names_really_do_resolve_in_runner_shared
```

Shape B is the delegating-wrapper form the repository already sanctions for precisely this case
(`is_pure_delegation`, `tests/test_rununify_run_queue.py:250`), and it keeps three of the four green.
The fourth, the byte-identical fingerprint against `tests/fixtures/runner_shared_premove_fingerprints.json`,
fails under BOTH shapes because it holds the BODY constant, and `should_color` is in none of that file's
four exemption lists. That one needs a DECLARED exemption, which is now its own item E-03, done the way
the file already does it (`SUPERSEDED_SINCE_MOVE`, where `state_root` and `_run_git` sit for the same
reason) with the two count assertions that move with it (`23`->`22`, `2`->`3`, both measured).

WHY THIS MATTERS BEYOND TEST BOOKKEEPING: those guards are the entire remaining defense against the
re-fork that `agy_runipd` performed silently on four `render_stream` symbols a Set ago. An executor
facing four red tests it has no declared authority over, with no explanation in its plan, would
plausibly "fix" them by loosening an assertion or rewriting the fixture. That destroys the evidence
rather than the defect, and it is exactly the outcome the fixture exists to make impossible. The plan
now predicts all four reactions, names the shape to use, and forbids the repair-by-deletion route.

**3. Converting `pwatch` the obvious way silently deletes a user-facing flag, and its own tests cannot
detect it (PR-903, HIGH).** `pwatch.py:951` is
`not args.no_color and os.environ.get("NO_COLOR") is None and sys.stdout.isatty()`. Only the last two
conjuncts are the shared decision; `args.no_color` is a real flag (`pwatch.py:847`) and `should_color`
reads no argparse state. So "convert it to consume the single definition" reads as replacing the whole
expression, which drops the flag. Measured on a real pty:

```text
stdout.isatty() = True
CURRENT color_enabled with --no-color : False
NAIVE   color_enabled with --no-color : True
```

The reason this one is dangerous rather than merely wrong is the test gap. Both shipped tests that pass
`--no-color` (`tests/test_pwatch.py:225`, `:236`) run through a `subprocess` PIPE, where `isatty()` is
already False, so the flag is doing nothing observable in either. `python3 -m pytest tests/test_pwatch.py`
-> `10 passed` with the flag working, and `10 passed` with it deleted. I confirmed the flag genuinely
works today by running pwatch under a pty: default gives ANSI (`10172` bytes), `--no-color` gives none
(`4443` bytes). E-04 now mandates the flag stay layered above the shared call, and E-06 adds the pty
case that can actually see it.

**A fourth finding is the one that would have made this plan's own success criterion false (PR-904,
MEDIUM).** E-04's guard ("exactly ONE `should_color` definition") and V-02's evidence
(`grep -rn "def should_color"` returning "exactly ONE line") both become FALSE the moment E-02 lands
correctly, because the sanctioned wrapper is itself a `def`: the post-fix count is 2. So the plan
demanded evidence that the correct implementation cannot produce, and a guard written to that wording
would be permanently red. This propagates outward: `pow5sj`'s V-01 demands the same `grep -c` proof of
one definition. Both are corrected here to the ORIGINATING-definition property, reusing
`is_pure_delegation` rather than authoring a second notion of the same thing, and V-07 now requires the
count of 2 be shown and explained so `pow5sj`'s executor is not caught by it.

TWO THINGS I CHECKED AND DID NOT TURN INTO WORK, recorded because each looked like a gap. First, the
plan's Deferred section declines to amend `yaxr4i` (F-03) and I agree: `yaxr4i` is `approved`, owns a
different axis, and the hazard its stale line 97 creates ("the color ENGINE is already correct and
complete") genuinely does evaporate once an engine-owning child exists. Second, the user-facing
documentation. `docs/cli-human-guide.md:27` ("`FORCE_COLOR=1` keeps color even when piped") stays TRUE
after this plan since only falsey values change. `docs/cli-human-guide.md:74` ("`NO_COLOR` disables
color and is only overridden by `FORCE_COLOR`") becomes imprecise, and I verified the carrier is right:
`7p3tt8` already declares that file and already rewrites its color section. What `7p3tt8` does not yet
name is line `:74` specifically, so that is recorded in this plan's Deferred with the carrier rather
than fixed in a file this plan does not declare. `docs/cli-output-contract.md:33` lists the three
controls without stating precedence and survives unchanged.

ONE SMALL FACTUAL CORRECTION (PR-905, LOW): the plan's Step 0 said "NOTHING in the package, the runners,
or CI ever SETS `NO_COLOR` or `FORCE_COLOR` (zero assignments)". The package and CI claim holds;
`tools/aw_upgrade_test.py:543` sets `env["NO_COLOR"] = "1"` for a sandboxed subprocess. Harmless here,
but the absolute wording would mislead the next reader auditing the same question.

The under-scope picture is worth stating plainly because it was the largest single gap. The original
plan named three source files and one test file, while the measured change touches FIVE test surfaces
it did not declare: three anti-re-fork guards, one historical fixture, and `tests/test_pwatch.py`.
`- Scope-Paths:` now declares all of them, including the fixture, which is declared precisely so the
fence is honest about the file E-03 must be seen NOT to have modified (expect a `--scope-ack` for it at
finalize, which is the correct outcome). The gate also gained the scope fence and the honesty rule its
eight sibling children all carry and this one lacked entirely, and its lifecycle sentence was the
flagged hand-rolled `git mv` form, now the conditional runner/executor wording.

Item count grew 4 -> 7. That is decomposition, not scope creep: no new concern entered the plan, and
the growth is recorded in the cohesion rationale so a later reader can check that claim.

Suite baseline at review HEAD, run bare: `7306 passed, 3 skipped, 2 xfailed in 161.81s`. Recorded in the
plan because the sibling reviews recorded `8369` and `7468` at earlier commits (rebases and suite
consolidation), so an executor comparing against a remembered number would misread a clean run.
Focused: `tests/test_runner_shared.py tests/test_runner_refork_guard.py tests/test_rununify_run_queue.py`
-> `249 passed in 33.35s`; `tests/test_pwatch.py` -> `10 passed in 0.72s`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | HIGH | IN-SCOPE | A. correctness; B/F. accessibility; D. anti-regression | `term.py:99-104` (presence test at `:100`, truthiness at `:103`); naive-edit grid executed 2026-09-19: 12 of 12 `NO_COLOR`-set cells colored on a TTY, `NO_COLOR=1 FORCE_COLOR=0` among them; correct-composition grid executed for contrast: 0 of 12 | E-01 named only the TRUTHINESS site, so the literal edit leaves a falsey `FORCE_COLOR` still CANCELLING `NO_COLOR` while no longer forcing, and the fall-through then colorizes. That voids `NO_COLOR`, the accessibility convention the whole ruling defers to, for any user who also sets a falsey `FORCE_COLOR`: a regression strictly worse than the defect being fixed | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | E-01 now mandates ONE `_force_color_is_forcing()` predicate consulted at BOTH read sites, with the naive edit and its measured result written into the item; expected outcome names the `NO_COLOR=1 FORCE_COLOR=0` cell; E-05 pins all twelve cells; V-01 requires that cell explicitly and a grep proving both sites call the one predicate; V-05 requires the NAIVE edit (not a full revert) as the mutation that must fail |
| PR-902 | HIGH | UNDER-SCOPE | C. architecture; D. anti-regression; E. testing; G. executability | Real guard methods run against patched source 2026-09-19 (Shape A: 4 FAIL; Shape B: 1 FAIL, 3 PASS); `Owned("should_color","runner_shared",BOTH)` `tests/test_runner_refork_guard.py:137`; `RESOLVES_IN_RUNNER_SHARED` `tests/test_rununify_run_queue.py:93`; `tests/test_runner_shared.py:634`, `:420`, `:199`; `is_pure_delegation` `tests/test_rununify_run_queue.py:250`; `should_color` absent from all four exemption lists | E-02's "consume it instead of reimplementing it" plus "exactly one definition in the package" reads as delete-the-def-and-import, which fails FOUR shipped guards, three of which exist specifically to assert `runner_shared` DEFINES this symbol. The fourth (byte-identical fingerprint) fails under both candidate shapes and needs a declared exemption. Neither the shape constraint nor the exemption appeared anywhere in the plan, and none of the five affected test files was declared, so an executor would face four red tests outside its fence and would plausibly repair them by loosening an assertion or rewriting the historical fixture, destroying anti-re-fork evidence rather than the defect | C:Medium; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | E-02 rewritten to mandate Shape B (the sanctioned one-line delegation), with the measured per-shape guard results in the item; new E-03 owns the `SUPERSEDED_SINCE_MOVE` exemption with the two count updates (`23`->`22`, `2`->`3`) and forbids editing the fixture; all five test surfaces added to `- Scope-Paths:`; Required tests predicts all four reactions and forbids repair-by-deletion; scope fence forbids weakening any anti-re-fork assertion; V-02 and V-03 demand the shape, the three guards by name, and proof the fixture is unchanged |
| PR-903 | HIGH | IN-SCOPE | A. correctness; D. anti-regression; E. testing; F. UX | `pwatch.py:847` (flag), `:950-952` (expression); pty measurement 2026-09-19 (`--no-color`: current `False`, naive `True`); pty run: default ANSI present, `10172` bytes vs `--no-color` none, `4443` bytes; `tests/test_pwatch.py:225,236` both piped; `python3 -m pytest tests/test_pwatch.py` -> `10 passed` either way | Only two of the three conjuncts in `pwatch`'s color expression are the shared decision; `args.no_color` is a user-facing flag and `should_color` reads no argparse state, so replacing the whole expression SILENTLY DELETES `--no-color`. The two shipped tests exercising that flag run through a pipe where `isatty()` is already False, so neither can detect the loss: the suite is green with the flag removed | C:Low; U:Medium; S:Low; F:Medium-High; Overall:Medium | FIXED | `pwatch` split out as its own item E-04 (it needs a different shape than `runner_shared` for a different reason, and bundling them is what hid this), mandating `not args.no_color and term.should_color(sys.stdout)`; new E-06 adds the pty case; `tests/test_pwatch.py` declared; V-04 explicitly REFUSES a piped `--no-color` run as evidence and requires the pty measurement; V-06 requires the flag-drop mutation to fail while noting the piped tests still pass under it |
| PR-904 | MEDIUM | IN-SCOPE | E. verification; G. executability | Post-E-02 `def should_color` count measured = 2 (`term.py` originating + `runner_shared` delegation); original E-04 ("exactly ONE `should_color` definition") and original V-02 ("returning exactly ONE line"); `pow5sj` V-01 ("Paste `grep -c` proving exactly ONE depth-resolver definition"); `is_pure_delegation` `tests/test_rununify_run_queue.py:250` | The plan's own one-definition guard and its V-02 evidence requirement are FALSE once E-02 lands correctly, because the sanctioned wrapper is itself a `def`. A guard written to that wording is permanently red, and V-02 demanded evidence the correct implementation cannot produce. The same wording propagates to `pow5sj`'s V-01, so the defect would have been inherited by the plan that builds on this seam | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-07 restated as exactly one ORIGINATING definition, permitting sanctioned delegations and reusing `is_pure_delegation` rather than a second notion, AST not substring; V-02 no longer asks for the one-line grep and says why; V-07 requires the count of 2 be shown and explained so `pow5sj`'s executor is forewarned |
| PR-905 | LOW | IN-SCOPE | G. executability | `tools/aw_upgrade_test.py:543` (`env["NO_COLOR"] = "1"`); grep over `agent_workflows/`, `tools/`, CI config 2026-09-19 | Step 0's claim that NOTHING in the package, the runners, or CI sets `NO_COLOR` or `FORCE_COLOR` ("zero assignments") is not exact: one harness sets it. Harmless to this plan's semantics, but the absolute wording would mislead a later reader auditing the same question | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Step 0 bullet rewritten to scope the claim to the package and CI and to name the one harness assignment, with a note that the earlier absolute wording was wrong |
| PR-906 | MEDIUM | UNDER-SCOPE | G. executability; project plan contract | This plan's gate before revision (three paragraphs: approval, queue-position note, provenance) versus sibling gates, e.g. `bn026f` and `qdd5jq`, which each carry a SCOPE FENCE, an HONESTY RULE, and the conditional finalize wording; plan-review Step 4 execution-contract requirement | The gate carried no scope fence and no honesty rule at all, alone among the nine `lifeglyph` children, and its lifecycle sentence was the `git mv` form the workflow flags ("`git mv` this plan to `executed/` ... via `aw ipd finalize`"). With nine declared paths after PR-902 and PR-903, an absent fence is materially worse than it was at four | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate now carries the scope fence (naming all nine declared paths, the expected `--scope-ack` for the fixture, the five forbidden neighbours, and one genuinely-unsafe stop condition), the hard-MUST honesty rule tied to the specific measurement traps, an explicit open-questions line, and the conditional runner/executor finalize wording replacing the `git mv` phrasing |
| PR-907 | LOW | IN-SCOPE | E. testing; G. executability | Review baseline `7306 passed, 3 skipped, 2 xfailed` at HEAD `3a513262`; sibling review records state `8369` (`bn026f`) and `7468` (`f9t5hz`, `qdd5jq`) at earlier commits | Required tests said only "paste the actual summary line" with no baseline, while two different totals are recorded in this Set's own sibling reviews. An executor comparing against a remembered sibling number would read a clean run as a regression, or miss a real one | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Baseline recorded in Step 0 and in Required tests with the reason the sibling numbers differ; V-07 requires the final summary be compared against it |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-02 as worded breaks four shipped guards. Fix the plan in place, or escalate the shape choice to the maintainer as blocking? | FIX IN PLACE: mandate Shape B (the one-line delegating wrapper), and split the one guard it cannot satisfy into its own item E-03 using the file's existing enumerated-exemption mechanism. | (a) Leave E-02 as written: rejected, it produces four red tests with no guidance, and the likely repair path destroys anti-re-fork evidence that took a prior Set to establish. (b) Escalate as `Blocking: yes`: rejected, nothing is open to decide. The repository has ALREADY ruled on this exact shape question: `is_pure_delegation` encodes the sanctioned wrapper form, the `818uru` OQ-02 wrapper ruling is cited in the guard itself, and `SUPERSEDED_SINCE_MOVE` is the established route for a legitimate body change. Escalating would spend a maintainer turn re-answering a settled question. (c) Mandate Shape A (import) and update the three guards to expect it: rejected, that inverts three deliberate invariants so one symbol can be tidier, and the guards' own docstrings explain why the definition-site assertion is load-bearing. | Measured per-shape guard results, 2026-09-19 (Shape A: 4 FAIL; Shape B: 3 PASS, 1 FAIL); `is_pure_delegation` `tests/test_rununify_run_queue.py:250` ("The sanctioned wrapper shape"); `tests/test_runner_shared.py:199` `SUPERSEDED_SINCE_MOVE` with `state_root` and `_run_git` precedents and the stated rule that holding a moved symbol to byte-identical AST "would freeze the defect in place"; `tests/test_runner_refork_guard.py` module docstring on why both halves are load-bearing. | yes |
| D-2 | The fingerprint harness must record a supersession. Add `should_color` to `SUPERSEDED_SINCE_MOVE`, or update the fixture capture? | ADD THE ENUMERATED EXEMPTION, and require V-03 to prove the fixture JSON is UNCHANGED. | (a) Update the fixture's captured fingerprint to the new body: rejected, and this is the one genuinely destructive option. The fixture is a HISTORICAL capture of pre-move bodies at a named HEAD; rewriting it does not record a supersession, it erases the only evidence the harness has, and every future comparison silently baselines against post-change code. (b) Add it to `DOCUMENTED_SINCE_MOVE` instead: rejected, measured, that list subtracts only a leading docstring and the remaining tokens must still match, so it fails here because the body genuinely changed. (c) Loosen the comparison for this symbol: rejected, the file's own convention is explicit that an unenumerated exemption is how the harness becomes decorative. | `tests/test_runner_shared.py:174-199` (the `SUPERSEDED_SINCE_MOVE` convention and its two written justifications); `:155-172` (`DOCUMENTED_SINCE_MOVE` is docstring-subtraction only); measured: `should_color` is in none of the four exemption lists and both candidate shapes fail the strict match; measured count effects `23`->`22` and `2`->`3`. | yes |
| D-3 | `pwatch --no-color` sits inside the expression E-04 rewrites, but the FLAG surface is `yaxr4i`'s axis. Preserve it here, or leave the flag layer to `yaxr4i`? | PRESERVE IT HERE, as a conjunct above the shared call, and say in Scope check why that is not an incursion into `yaxr4i`. | (a) Replace the whole expression and let `yaxr4i` re-add the flag: rejected, that ships a window in which a documented flag silently does nothing, and `yaxr4i`'s scope is `cli.py`'s `common` parser, which `pwatch`'s own argparse group is not part of, so nothing guarantees it would ever be re-added. (b) Add `pwatch` to `yaxr4i`'s scope: rejected, `yaxr4i` is `approved`, and widening an approved plan's scope from a sibling review is not this review's authority. (c) Leave `pwatch` unconverted entirely: rejected, it is one of the three divergent implementations this plan exists to unify, and it is the one carrying defect 3. | `pwatch.py:847` declares the flag in `pwatch`'s OWN parser, not `cli.py`'s `common`; `yaxr4i` `- Scope-Paths:` does not include `pwatch.py`; pty measurement showing the flag is currently load-bearing (ANSI present without it, absent with it); this plan's Scope already claims `pwatch.py`. | yes |
| D-4 | Should the one-definition guard assert a literal `def` count of one, as E-04 and V-02 required? | NO. Assert exactly one ORIGINATING definition, permitting sanctioned delegations, reusing `is_pure_delegation`. | (a) Keep the literal count of 1: rejected, measured false after E-02 (the correct count is 2), so the guard would be permanently red and the V-02 evidence unobtainable. (b) Count 2 and assert that: rejected, a bare count of 2 is satisfied by a genuine second implementation, which is precisely the defect the guard exists to prevent; it would be decorative. (c) Write a fresh predicate for "is a delegation": rejected, a second notion of the same property is how the two would drift apart, and the existing one is already the repository's answer. | Measured post-E-02 def count = 2; `is_pure_delegation` `tests/test_rununify_run_queue.py:250`; `tests/test_runner_refork_guard.py` module docstring on why AST and not substring matching ("EVADED by `class Palette (object):`", satisfied by a comment); `pow5sj` V-01 inherits the same wording and is corrected by V-07's required explanation. | yes |
| D-5 | `docs/cli-human-guide.md:74`'s precedence sentence becomes imprecise. Fix it here, or leave it to the carrier? | LEAVE IT TO `7p3tt8`, and record the specific line in Deferred with what the carrier does not yet name. | (a) Fix it here: rejected, this plan does not declare `docs/`, and two plans editing one paragraph of one user-facing file is the churn the Set's boundaries exist to prevent. (b) Say nothing: rejected, the carrier's own finding targets `:67-68` and never mentions `:74`, so the imprecision could survive the child that is supposed to own it. (c) Add `docs/cli-human-guide.md` to this plan's scope: rejected, same collision reason as (a), and `7p3tt8` is already declared to rewrite that exact section. | `docs/cli-human-guide.md:74` ("only overridden by `FORCE_COLOR`") versus `:27` ("`FORCE_COLOR=1` keeps color even when piped"), the latter still TRUE after this plan; `7p3tt8` `- Scope-Paths:` includes `docs/cli-human-guide.md` and its E-02/F-02 target `:67-68`; `docs/cli-output-contract.md:33` states no precedence and is unaffected. | yes |
| D-6 | The plan declines to amend `yaxr4i`'s falsified "engine is already correct and complete" premise (F-03). Accept that, or require it? | ACCEPT THE DECLINE. | (a) Require the amendment: rejected, `yaxr4i` is `approved` and owns a different axis, and the hazard is real only while no plan owns the engine. Once this child exists with its own E-items, an executor cannot act on line 97 to leave the engine alone. (b) Escalate to the maintainer: rejected, no decision is needed; the plan's own F-03 already records the falsification, which is the durable part. | `yaxr4i` line 97 and `- Status: approved`; `yaxr4i` `- Scope-Paths:` (flag surface, `cli.py`/`result_types.py`/docs) versus this plan's (the engine); this plan's F-03 and its `Carrier-Declined` rationale, which I verified reasons correctly rather than merely asserting. | yes |
| D-7 | The gate lacked a scope fence and an honesty rule. Add them, or report the omission? | ADD BOTH IN PLACE, matching the sibling children's form and tying the honesty rule to this plan's specific measurement traps. | (a) Report only: rejected, plan-review Step 4 requires the reviewer ADD a missing execution-contract element as an in-place revision and record it as a finding, which is what was done. (b) Copy a sibling's fence verbatim: rejected, a fence naming another plan's forbidden neighbours is worse than none, since it reads as authoritative while fencing the wrong things. | plan-review Step 4 execution-contract requirement and its explicit instruction to flag a hand-rolled `git mv`; sibling gates in `bn026f`, `qdd5jq`, `f9t5hz`, `9zvl2w`, `udgilu`, `n4xq3l` all carrying fence + honesty rule; this plan's nine declared paths after PR-902/PR-903. | yes |
