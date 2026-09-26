# Review findings: plan 4petcj

- Subject-Id: 4petcj
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `05fa2a7b`. Structural preflight `aw ipd lint --phase author --agent` CONFORMED
(exit 0, `findings: 0`) before revision, and `--phase review-finalize` conforms after. No pre-review
snapshot was needed: the plan was committed and unmodified, and the lane-input copy is byte-identical
to the tracked file.

THE PLAN IS DIAGNOSTICALLY RIGHT AND ITS DESIGN IS THE RIGHT SHAPE. Every structural claim reproduced:
CI's test step really does inherit `addopts` and so has never run a `slow` test; the
"the `unittest` job already runs the full suite" comment in the same workflow really is false; xdist
really does swallow the deselected count that a serial run prints; the two comments in `pyproject.toml`
and `Makefile` really do claim CI runs the full suite. I verified F-3 on a fixture rather than trusting
it:

```text
-n 2          -> "1 passed in 0.68s"                 <- no deselected count at all
-p no:xdist   -> "1 passed, 1 deselected in 0.02s"   <- only serial tells the truth
```

**THE PLUGIN AS DESIGNED CRASHES ANY RUN WITHOUT XDIST, AND THE PLAN'S OWN TEST MATRIX WOULD HAVE HIT
IT IMMEDIATELY.** This is the finding worth the most. `pytest_testnodedown` is an XDIST-owned hookspec,
so a plugin declaring it at module level fails pluggy validation at registration when xdist is not
loaded. I ran the plan's described design verbatim:

```text
-n 0           rc=0  ok                 <- why the plan's prototype looked fine
-p no:xdist    rc=3  INTERNALERROR> pluggy._manager.PluginValidationError:
                     unknown hook 'pytest_testnodedown' in plugin <module 'dn' ...>
```

E-04 explicitly requires a `-p no:xdist` case, and `make test-serial` exists, so this was not
hypothetical. The plan prototyped `-n 2` and `-n0` and those are precisely the two invocations that
CANNOT catch it, because `-n 0` still loads xdist. I verified the fix (register the xdist hook from
`pytest_configure` behind `config.pluginmanager.hasplugin("xdist")`) across all four invocations:

```text
-n 2         rc=0  NOTE present
-n 0         rc=0  NOTE present
-p no:xdist  rc=0  NOTE present
-m ""        rc=0  NOTE correctly ABSENT
```

I also checked the MAX-not-SUM reasoning instead of accepting it, since getting it wrong would print a
count that is wrong by a factor of the worker count: with 10 deselected, per-worker counts were
`[10, 10]` at `-n 2` and `[10, 10, 10, 10]` at `-n 4`, so MAX is right and SUM would report 40.

**THE FAILING SET IS FOUR, NOT THREE, AND THE FOURTH IS OWNED BY NOBODY.** The plan is built around
three known failures, each owned by a gated bug item. Measured:

```text
-m slow        -> 4 failed, 170 passed in 49.12s
make test-all  -> 4 failed, 2628 passed, 2 skipped in 77.02s
FAILED tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description
```

That fourth failure lists eight subparser description gaps (`upgrade-test list/new/sandboxes/probe/env/
clean` have EMPTY descriptions; `config unset` and `conf unset` have descriptions shorter than their
help). No backlog item mentions it. It is `slow` only because `tests/test_cli.py` carries a module-level
`pytestmark = pytest.mark.slow`, and `git log -S "upgrade-test" -- agent_workflows/cli.py` dates it to
`64859728` THE SAME DAY, from plan `8ud1is` which is already `executed`. So this is a live regression
that reached `main` today and that only the deselected slow set could see: the plan's thesis
demonstrating itself, hours after the plan was written. Left as-authored, E-02 would have noted three
items, E-06 would have claimed "exactly the three known failures" about a four-failure run, and the
regression would have stayed untracked behind an advisory step. E-02 now re-derives the set and FILES a
gated bug item for any unowned failure.

**THE NUMBERS WERE ALREADY STALE, WHICH IS THE ARGUMENT FOR PROPERTIES OVER COUNTS.** The plan says 172
slow of 2411; HEAD has 174 of 2634, with 2460 deselected. Nothing important turns on it, but E-01's step
name embedded three backlog ids and E-06's bar was a literal count of three failures, so the drift had
somewhere to do damage. Both are now properties: the step name carries no ids (they live in the comment
E-02 maintains), and E-06's bar is "every FAILED node id appears in E-02's re-derived owned set".

**A DECLARED SCOPE PATH DOES NOT EXIST.** `3ypquf` is `graduated` (to Set `deepclean`, pending plan
`baxbdh`), so its file is under `graduated/`, not the `open/` path the plan declares; `ls` of the
declared path fails. Corrected in `- Scope-Paths:`.

**WHAT I CONFIRMED RATHER THAN CHANGED.** The gate's stop condition is sound and I verified its premise
directly: `parse_suite_summary` returns the count line with the NOTE line placed either before or after
it, so the NOTE cannot displace what the runner's merge gate reads. OQ-01 (`continue-on-error` over
`|| true`) is correctly resolved and its reasoning is right, since `|| true` would render the step green
and hide exactly what this plan exists to expose. The decision not to refresh
`.aw/system/managed-sections.json` is safe and I checked that nothing enforces the digest (no test
selects on it, no `check_engine` rule verifies it). The `.aw/system` force-include claim is accurate, so
E-05's generic phrasing for a file that ships to other repositories is the right call. `livecorpus` is
still carried by zero tests, so F-5 holds and the slow step needs no livecorpus handling. The
runner-suite-gate deferral is correct (a fast lane gate is deliberate design). Right-sizing: 6 E-items
across independent surfaces (CI yaml, a plugin, a workflow body), well under threshold, and the
dependency graph is honest.

ONE SMALL INACCURACY worth fixing because E-01 inserts a step by position: the plan quotes the CI
command as `-n auto -q`; it is actually `-n auto -rs`. The conclusion is unaffected.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. correctness (a design that aborts the test runner) | the plan's described design run verbatim on a scratch fixture: `-p no:xdist` -> exit 3, `INTERNALERROR> pluggy._manager.PluginValidationError: unknown hook 'pytest_testnodedown'`; `-n 0` -> exit 0 (xdist still loaded) | **E-03's PLUGIN DECLARES AN XDIST-ONLY HOOK UNCONDITIONALLY, SO ANY RUN WITHOUT XDIST ABORTS BEFORE COLLECTION.** `pytest_testnodedown` is validated against loaded hookspecs at registration. E-04 requires a `-p no:xdist` case and `make test-serial` exists, so this is on the plan's own path. The plan's `-n 2`/`-n0` prototype could not catch it because `-n 0` keeps xdist loaded. | C:Low; U:Low; S:Low; F:Medium; Overall:Low (the fix is a three-line capability probe, verified working on all four invocations) | FIXED | E-03 now requires registering the xdist hook from `pytest_configure` behind `config.pluginmanager.hasplugin("xdist")`, forbids the module-scope `try: import xdist` alternative (it tests importability, not what this run loaded), and records the per-process-counter constraint (`pytest_deselected` gets no `config`). E-04 gains a distinct `-n 0` case and an `INTERNALERROR`-absent assertion so a pluggy abort is not misreported as a missing NOTE. V-04 gains a second negative control that reproduces the unguarded bug. F-7 added. |
| PR-002 | HIGH | UNDER-SCOPE | D. anti-regression (an untracked live regression) | `-m slow` -> `4 failed, 170 passed`; `make test-all` -> `4 failed, 2628 passed, 2 skipped`; the fourth is `tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description` listing eight gaps; no backlog item references it; `git log -S "upgrade-test" -- agent_workflows/cli.py` -> `64859728 2026-09-26` (plan `8ud1is`, executed) | **THE SLOW SET HAS FOUR FAILURES AND THE FOURTH IS OWNED BY NO BACKLOG ITEM.** The plan hardcodes three. E-02 would note three items, E-06 would assert "exactly the three known failures" against a four-failure run, and an untracked same-day regression would sit behind an advisory step, which is the exact invisibility this plan exists to end. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 now RE-DERIVES the failing set from an actual `-m slow` run as the authority, requires an owning item for every failure, and requires filing one with `aw backlog new --work-kind bug --blocks-release next` for any unowned failure before proceeding. E-01's comment carries the ids; E-06's bar became a property. A new Deferred row declines fixing the eight descriptions here with the filed item as the record. V-02 requires the re-derived set plus per-failure ownership. F-8 added. |
| PR-003 | MEDIUM | IN-SCOPE | G. plan executability (a declared path that does not exist) | `ls .aw/records/backlog/open/20260923-3ypquf-...` -> `No such file or directory`; the item is at `graduated/` with `- Status: graduated`, `- Graduated-To: deepclean` | **A `- Scope-Paths:` ENTRY POINTS AT A MOVED FILE.** `3ypquf` graduated, so E-02's note would target a missing path and finalize would see a declared-but-unmodified path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- Scope-Paths:` corrected to the `graduated/` path; E-02 records that a note on a graduated item is still correct (the item is the durable carrier until its plan executes). F-9 added. |
| PR-004 | MEDIUM | IN-SCOPE | G. plan executability (authored counts used as acceptance bars) | plan says 172 slow of 2411 with 2239 deselected; measured 174 of 2634 with 2460 deselected; E-01's step name embedded `57dwkc, 3ypquf, 4vfkl1`; E-06's bar was "exactly the three known failures" | **LIVE COUNTS ARE USED AS SUCCESS CRITERIA AND HAVE ALREADY DRIFTED.** A count measured at authoring belongs in prose as context, never as the bar (rubric G's re-derivation convention). The step name additionally bakes a mutable id list into a durable CI UI label. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01's step name de-identified (ids move to the comment); E-01/E-03/E-06 state properties with the measured numbers kept as context and explicit "re-derive, do not hardcode"; the Findings section carries a drift note; V-03 already re-derived its count and is unchanged. |
| PR-005 | LOW | IN-SCOPE | A. correctness of a quoted anchor | `grep -n "run: python -m pytest" .github/workflows/tests.yml` -> `77: run: python -m pytest tests/ -n auto -rs` | **THE PLAN MIS-QUOTES THE CI COMMAND AS `-q` WHERE IT IS `-rs`.** The conclusion (the step inherits `addopts`, so it never runs a slow test) is unaffected, but E-01 inserts a step directly after this one, so an executor matching on the quoted command would not locate it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- Concern:` corrected to `-rs`; F-12 records it; V-01 now requires pasting the inserted step's position relative to "Run self-tests (parallel)" so placement is verified rather than assumed. |
| PR-006 | LOW | IN-SCOPE | E. testing (a test pair that cannot detect its own bug class) | `-n 0` keeps xdist loaded; only `-p no:xdist` unloads it (measured) | **E-04's TWO CASES ARE NOT INDEPENDENT.** Testing `-n 2` and `-p no:xdist` without `-n 0`, or treating `-n 0` and `-p no:xdist` as interchangeable, leaves the hook-validation path untested; and a bare "NOTE missing" assertion reports a pluggy abort as the wrong defect. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now carries four cases with `-n 0` and `-p no:xdist` distinguished and an explicit `INTERNALERROR`-absent assertion; the expected outcome names which cases fail under which bug. Gate stop condition 2 forbids deleting the `-p no:xdist` case to go green. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan describes a plugin design. Accept the described hooks, or run the design before reviewing it? | RUN IT, on a scratch fixture, across four invocations; the described design aborts under `-p no:xdist`. | (a) Read it and reason: rejected, the plan already reported a prototype under `-n 2`/`-n0` and those are exactly the invocations that cannot surface an xdist-hookspec problem, so reasoning from its prototype would have inherited the blind spot. (b) Flag the risk without a fix: rejected, the fix is three lines and leaving it as "verify at execution" would spend an execution turn discovering a known defect. | The verbatim design -> exit 3 + `PluginValidationError` under `-p no:xdist`; the guarded design -> correct on `-n 2`, `-n 0`, `-p no:xdist`, `-m ""`. | yes |
| D-2 | The slow set has a fourth, unowned failure. Fold it into the advisory comment, fix it here, or require E-02 to file an item? | REQUIRE E-02 TO FILE a gated bug item, and decline the fix here. | (a) Fold it into the comment unowned: rejected, an advisory step naming an untracked failure is how a regression becomes permanent, and it contradicts the repository rule that a live bug carries `Blocks-Release`. (b) Fix the eight descriptions in this plan: rejected, CLI help text is unrelated to test visibility and would put an unreviewed behavior change inside a tooling plan. (c) Ask the maintainer: rejected, "file an item for an unowned failing test" needs no ruling and the repository rule already prescribes it. | `-m slow` showing 4 failed; no backlog item matching the node id; `git log -S` dating it to `64859728` the same day; the "every live bug gates the next release" rule in AGENTS.md. | yes |
| D-3 | E-06's bar was a literal count of failures, and E-01's step name carried three ids. Update the numbers, or restate as properties? | RESTATE AS PROPERTIES, keeping the measured numbers as context. | (a) Update the numbers to today's four: rejected, it just re-arms the same trap; the set changed within hours of authoring and will change again as the owning items close. (b) Leave them: rejected, the count is an acceptance criterion counting live artifacts, which rubric G requires be re-derived at execution. | The measured drift (172/2411 -> 174/2634); rubric G's live-artifact re-derivation convention; the step name being a durable Actions UI label. | yes |
| D-4 | Does the NOTE line endanger the runner's merge gate, as the stop condition fears? | NO, verified directly; keep the stop condition as a cheap re-check rather than deleting it. | (a) Delete the stop condition as unnecessary: rejected, it costs one paste and guards the one thing that could break a queue for every concurrent lane. (b) Leave it unverified: rejected, a reviewer able to settle it in one command should, so the executor is not left uncertain about the plan's riskiest interaction. | `parse_suite_summary` on samples with the NOTE line both after and before the count line -> returns the count line in both. | yes |

### Deferred and open

- (none). All six findings were FIXED in place, four of them by changing what the plan will DO (a
  capability-probed hook registration, a re-derived failing set with an item filed for the unowned
  failure, a fourth test case with an abort-distinguishing assertion, and properties in place of
  counts) rather than by rewording. No question required the human: OQ-01 was already correctly
  resolved, and every decision above rests on a measurement or an existing repository rule.

HONEST LIMITS, stated because they bound what this round proves. I verified the DEFECTS and the FIXES
in prototype, but I did not write `tests/deselect_notice.py` or run it inside this repository's own
conftest, so that the guarded design composes with the root `conftest.py`'s xdist auto-install re-exec
remains E-03's work and V-03's evidence. My four-invocation matrix used a scratch fixture with one
deselected test; the real suite deselects 2460 across many workers, and while I verified the MAX
reasoning at `-n 4`, I did not verify it at this machine's full `-n auto` width. I ran `-m slow` and
`make test-all` once each, so a flaky failure would look identical to a deterministic one here; the four
failures were consistent across both runs, which is suggestive and not proof. I did not attempt to
confirm the CI step's runtime cost (the plan's "about one extra minute per leg"): locally the slow set
took 49s on this machine, and a GitHub runner is slower, so that estimate is plausible but unverified.
Finally, I did not run the `-p no:xdist` path over the real suite, only over the fixture.
