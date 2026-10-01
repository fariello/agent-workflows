# Review findings: plan m7fllj

- Subject-Id: m7fllj
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed), PR-008 (LOW, fixed), PR-009 (LOW, fixed), PR-010 (LOW, fixed), PR-011 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `a4e7f31e`, which is 196 commits after the plan's authoring HEAD
`69f341b7`. The plan file was committed and byte-identical to the lane input (`diff` reported no difference),
so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author --agent` reported
`clean` (exit 0, zero findings) BEFORE semantic review; `--phase review-finalize` reports `clean` with zero
findings after revision. The plan is `- Kind: child`, so the `IPD-S407` orchestrator row check does not apply.

THE PLAN'S DESIGN IS SOUND AND ITS TWO LOAD-BEARING CLAIMS REPRODUCE EXACTLY. I re-ran every measurement
rather than trusting any of them, and the two that the whole plan rests on are byte-for-byte correct:

- F-03 (the gate catches the `g321ny` shape, and still does under the narrowing). A reconstructed probe with
  `reap: Callable[[Any, Path], Any]` called as `reaper(process, run_dir=run_dir)` yields exactly
  `error: Unexpected keyword argument "run_dir"  [call-arg]` / `Found 1 error in 1 file`, both bare and under
  the exact ten-code `disable_error_code` list E-02 configures. This is the claim that justifies the plan
  existing, and it is correct.
- F-06 (the gate finds a live shipped bug). `build_verify_and_continue_notice` with a `verify_and_continue`
  disposition returns `RETURN VALUE: None / type: NoneType`, and the caller-shaped f-string yields
  `'Mode: recoveryNone'`. An `ast` walk confirms exactly one `Return` (the early `""`) with the body ending in
  an `Expr`. I went further than the plan and measured WHY the suite misses it: the only test naming the symbol
  is `tests/test_recovone_single_definition.py::TestSingleDefinitionIdentity::test_identity_pins`, which
  `assertIs`-compares host attributes and NEVER CALLS the function; `grep` for `verify_notice` across `tests/`
  returns zero source matches. So no test exercises it at all. That strengthens the plan's argument.

Also upheld on re-measurement: F-02 (the `ignore_missing_imports` totals are identical with and without the
flag), F-07 (every PyPI `Requires-Python` boundary reproduces, with `1.20.0` the first `>=3.10`), F-08 (a 3.9
target is refused on the CLI and silently diagnosed-then-ignored in a config file), F-09 (exactly 33
`type: ignore` comments), F-10 (the per-module override does reach `Success`, and would indeed blind `return`
across the file holding F-06), and the design choices in OQ-01 (mypy over pyright) and OQ-03 (read-and-triage
over blanket baseline). I additionally DEMONSTRATED the per-line suppression mechanism rather than accepting it
as described: a probe with `# type: ignore[no-redef]  # <reason>` reaches `Success` under the `[tool.mypy]`
section read from a `pyproject.toml`, so E-05's chosen form works in exactly the configuration E-02 writes.

THE DOMINANT FINDING IS ONE THE PLAN NEVER CONSIDERED, AND IT UNDERMINES THE ITEM THE WHOLE PLAN TURNS ON
(PR-002). The plan treats its 23-finding baseline as a property of the repository. It is not: it is a property
of the repository AND the resolved dependency versions, and I measured it moving.

```
local venv  (filelock 3.29.7):  Found 24 errors in 12 files (checked 184 source files)
3.12 venv   (filelock 4.0.7 ):  Found 23 errors in 11 files (checked 184 source files)
diff of sorted error lists:
< agent_workflows/platform_lock.py:429: error: Unexpected keyword argument "preserve_lock_file" for "SoftFileLock"  [call-arg]
```

`dependencies = ["filelock>=3"]` freely permits 4.x, and 4.0.7 is what a fresh CI `pip install -e ".[test]"`
resolves today, so CI would see 23 where the authoring machine saw 24. Two concrete consequences break items as
authored. V-05 demanded the suppression count be reconciled against "the 22 findings remaining after E-04", a
number that is unanswerable without naming the environment. And the per-line ignore E-05 would add at
`platform_lock.py:429` would be UNUSED in CI, harmless only because F-09 keeps `warn_unused_ignores` off and a
live red the moment anyone adopts that flag. New E-07 and V-07 pin both the tool ceiling and the `filelock` the
baseline is measured against, in the `test` extra and `dev` group ONLY so `dependencies` stays untouched, which
is what V-01 and validation step 6 exist to prove.

THE SECOND STRUCTURAL FINDING IS THAT A FAIL-CLOSED GATE SHIPPED WITH AN UNBOUNDED CHECKER (PR-003). The plan
declares `mypy>=1.18` with no ceiling, which delegates this repository's CI verdict to whoever next publishes a
release. That is not a theoretical worry for this tool, and the plan's own F-08 is the evidence: mypy CHANGED a
config-file behavior at `2.0.0`, which I pinned down more precisely than the plan did. Measured across four
pinned versions on a `python_version = 3.9` config file:

```
mypy 1.18.2 cfg py3.9: <no complaint; value accepted>
mypy 1.19.1 cfg py3.9: <no complaint; value accepted>
mypy 2.0.0  cfg py3.9: [mypy]: python_version: Python 3.9 is not supported (must be 3.10 or higher)
mypy 2.3.1  cfg py3.9: [mypy]: python_version: Python 3.9 is not supported (must be 3.10 or higher)
```

So the 3.10-target constraint the plan treats as a fact about mypy is a fact about mypy 2.x. I also measured
that NO baseline drift occurs across `1.18.2`, `1.19.1`, `2.0.0` and `2.3.1` on this tree (all report the same
narrowed total in the same environment), so the ceiling is insurance rather than a workaround, and E-07 asks for
a generous major-boundary cap rather than a frozen point release.

EVERY ABSOLUTE FINDING COUNT IN THE PLAN IS ALREADY WRONG, WHICH IS THE PLAN BREAKING A CONVENTION IT OBSERVES
ELSEWHERE (PR-001). The plan correctly treats the suite count as a live measurement to re-derive ("TREAT THE
DIGITS AS CONTEXT, NOT AS THE BAR") and then treats its mypy counts as fixed facts, hard-coding `321`, `23` and
`22` into E-02's required comment text, F-01/F-02/F-04, the goal, the scope, the approval gate and V-05's
reconciliation. Those are live measurements over the same drifting tree:

```
authoring HEAD 69f341b7:  321 errors in 46 files  ->  narrowed: 23 in 12
review    HEAD a4e7f31e:  335 errors in 46 files  ->  narrowed: 24 in 12   (same machine, same config)
```

196 commits moved the un-narrowed total by 14 and the narrowed one by 1. Every such number is now restated as a
PROPERTY with the digits kept as dated, HEAD-stamped context. The per-code census got the same treatment
(PR-008): every code's RANK is stable across the two measurements (`arg-type` > `attr-defined` > `assignment` >
`misc` > `union-attr`) while four of the five counts moved, so the ordering is the finding and the integers are
not. E-02's comment requirement now demands both numbers be re-derived AND stamped with the HEAD and pinned
mypy version, because an unstamped pair of digits in a source comment rots within days.

ONE TRIAGE CLASSIFICATION WAS WRONG IN A WAY THAT COULD HAVE CAUSED A BAD EDIT (PR-006). F-05 lumps
`render_stream.render_event`'s finding in with "annotation-precision issues". It is not: it is a `[return]`
finding, the SAME code and shape as F-06's live bug, so an executor following the plan's own E-04 reasoning
("the fix is the return, not a signature change") could plausibly "fix" it by inventing a return value. Its
`-> str | None` is CORRECT: its sole consuming caller in `oc_runipd.py` guards with `if rendered is not None:`
before using the value, so `None` is a documented outcome. E-05 now names it explicitly as adjudicated-not-a-bug.

I ALSO RETIRED A RISK THE PLAN LEFT UNMEASURED RATHER THAN MERELY FLAGGING IT (new F-14, PR-010). E-03 runs the
gate on one OS while F-05 classifies three findings as platform-conditional, which raises a real question about
whether a one-OS gate is a coverage hole. It is not: mypy analyzes a DECLARED platform, and all three report the
identical total (`Found 24 errors in 12 files` under default linux, `--platform win32`, and `--platform darwin`),
because Windows-only branches are type-checked everywhere. So the single-runner job is a cost choice with no
coverage consequence, and E-03/V-03 now record the measurement instead of leaving a reader to wonder.

THE SCOPE QUESTION THE PLAN HANDED TO THE REVIEWER IS DECIDED RATHER THAN PASSED ALONG (PR-004). The plan's
under-scope note asked a reviewer to choose between widening `- Scope-Paths:` for E-05's eleven modules and
splitting E-05 into a follow-on. Split is strictly worse by the plan's own argument: the gate cannot arrive
fail-closed without E-05, so splitting forces E-03 to land advisory, and E-03's own text explains at length why
an advisory gate reproduces the exact fail-open defect `fcua9q` was filed about. The widening worry does not
survive inspection of what the edits ARE, namely trailing comments on existing lines, which cannot change
behavior. All eleven are now declared, plus `CONTRIBUTING.md`, which I confirmed IS the right home for E-06
(it already documents `make test`, `make test-all`, `make test-serial`, `pre-commit install` and
`aw check-local-leaks`), resolving that conditional too.

THE SUITE IS NOT GREEN AND THE FAILURE IS NOT THIS PLAN'S (PR-005). Bare `python3 -m pytest` at review HEAD:

```
1 failed, 3446 passed, 2 skipped, 3 warnings in 64.50s
FAILED tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity
```

Isolated, it is a date-boundary bug: the test pins a history line against a hardcoded `2026-09-30` while
`date.today()` now returns `2026-10-01` (`- 2026-09-30 HIST_ACTOR` versus `+ 2026-10-01 HIST_ACTOR`). It touches
no path this plan declares. Worth recording for the same two reasons a sibling review recorded it: an executor
comparing against the authored `3387` would see a mismatch and could not tell whether they caused it, and an
executor told "the suite must pass with ZERO failures" is given an impossible bar by someone else's defect. The
bar is now no NEW failure, and the plan explicitly forbids fixing it.

TWO SMALLER MEASUREMENTS CORRECTED. F-11's cold timing is machine-dependent and larger than authored (authoring
`14.2s`, review `real 0m26.654s`), so cold is now stated as tens of seconds rather than as a figure, while the
warm number that actually governs a hook decision is tiny and stable in both (`0.23s`, `0.47s`) (PR-007). And
E-04 now carries the `RecoveryDisposition` construction shape I had to discover at review, because
`verify_and_continue` is a derived `@property` and not one of the ten `_fields`, so it cannot be set directly
and a naive attempt fails (PR-011).

ONE THING I CHECKED AND DID NOT FLAG. The plan declares `pyproject.toml`, `Makefile` and
`.github/workflows/tests.yml`, and sibling pending plan `zb81ah` declares the first two as well. No collision:
`zb81ah` edits the `addopts` marker-filter COMMENT and the `test` target comment, while this plan adds a new
`[tool.mypy]` section, new extra entries and a new `typecheck` target. The runner isolates each item in its own
worktree in any case. Pending `szkgb8` declares `tests.yml` for a ruff `F811` gate job, likewise additive and in
a different job. I verified `ruff check --select F811 agent_workflows/` is currently clean, so that sibling does
not interact with this plan's baseline either.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric G (live-artifact re-derivation convention), Rubric E | Plan F-01/F-02/F-04, Goal, Scope, E-02's comment requirement, V-05's reconciliation; `python3 -m mypy --no-incremental agent_workflows --ignore-missing-imports` at review HEAD `a4e7f31e` | Every absolute mypy finding count in the plan is a LIVE measurement over a drifting tree, hard-coded as a fixed fact and already wrong 196 commits later: authored `321 errors in 46 files` measures `335` at review, and the narrowed `23 in 12` measures `24 in 12`. E-02 required those digits be written into a source comment; V-05 required the suppression count be reconciled against "the 22 findings remaining after E-04". The plan applies the re-derivation convention correctly to its suite count and then violates it for its own central numbers. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-01, F-02 and F-04 restated as properties with both dated HEAD-stamped measurements kept as context; Goal, Scope, Concern, approval gate and deferral notes de-digitized; E-02's comment requirement now demands numbers RE-DERIVED at execution and STAMPED with HEAD plus pinned mypy version; E-05 gains an explicit "re-derive the finding set, do not work from this plan's list"; V-02 and V-05 fail an un-re-derived quote of the authored figures. |
| PR-002 | HIGH | IN-SCOPE | Rubric A/C (reproducibility), Rubric E | New F-13; two clean venvs at review HEAD `a4e7f31e` reporting `Found 24 errors in 12 files` (filelock 3.29.7) and `Found 23 errors in 11 files` (filelock 4.0.7), `diff` isolating `agent_workflows/platform_lock.py:429 ... [call-arg]`; `inspect.signature(filelock.SoftFileLock.__init__)` | The narrowed baseline is ENVIRONMENT-DEPENDENT and the plan never measured it. `platform_lock.py:429`'s `preserve_lock_file` finding exists under `filelock` 3.29.7 and VANISHES under 4.0.7, which `dependencies = ["filelock>=3"]` permits and which a fresh CI install resolves today. So V-05's count reconciliation is unanswerable without naming the environment, and E-05's per-line ignore at that site would be UNUSED in CI, which is harmless only while `warn_unused_ignores` stays off and becomes a red gate if it is ever adopted. A fail-closed gate over an unpinned environment can flip with no repository change. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New E-07 (task group 4) pins both the `filelock` the baseline is measured against and mypy's ceiling, in the `test` extra and `dev` group ONLY so `dependencies` stays exactly `["filelock>=3"]`; new V-07 requires a fresh-venv reproducibility proof plus a re-derivation of the environment delta; E-05 gains a specific instruction not to add an ignore the pinned environment does not report; V-05 gains item (f) requiring the executor to state whether that finding was present; E-06 gains a fifth documented limit; F-09 records the interaction with `warn_unused_ignores`. |
| PR-003 | HIGH | IN-SCOPE | Rubric C (operability), Rubric A | Plan E-01 (`mypy>=1.18`, no ceiling) and E-03 (fail-closed, no `continue-on-error`); plan F-08; four pinned-mypy config-file runs showing the `python_version` diagnostic first appearing at `2.0.0` | The plan makes a CI gate FAIL-CLOSED while declaring its checker with an unbounded `>=` specifier, so any future mypy release can red `main` with no repository change. This is not hypothetical for this tool: the plan's own F-08 records mypy changing a config-file behavior mid-series, which review pinned to `2.0.0` exactly (1.18.2 and 1.19.1 accept `python_version = 3.9` silently; 2.0.0 and 2.3.1 diagnose and ignore it). Review measured no baseline drift across four versions today, so the risk is forward-looking, which is precisely when a bound is cheap. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-07 owns the specifier and requires a major-boundary ceiling (e.g. `>=1.18,<3`) rather than a frozen point release, commented with the F-08 measurement as the reason to re-measure before widening; E-01 now depends on E-07 and writes what it fixes; V-01 explicitly FAILS a bare `mypy>=1.18`; F-08 records the version at which the behavior changed. |
| PR-004 | MEDIUM | UNDER-SCOPE | Rubric G (executability), scope-fence declaration | Plan `- Scope-Paths:` (5 paths) versus E-05's eleven named modules and E-06's conditional `CONTRIBUTING.md`; plan's own Under-scope note asking the reviewer to choose; `CONTRIBUTING.md` local-check material | The plan KNEW it would edit eleven modules and declared none of them, then handed the reviewer a choice between widening the fence and splitting E-05 into a follow-on. A fence that omits edits the plan intends is a fence that lies, and the split alternative is self-defeating by the plan's own argument (the gate cannot arrive fail-closed without E-05, so splitting forces the advisory gate E-03 spends paragraphs arguing against). E-06's "`CONTRIBUTING.md` if it documents local check commands, otherwise the comment block" left a second undeclared path conditional on an executor's judgement. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All eleven modules plus `CONTRIBUTING.md` added to `- Scope-Paths:` (now 17 paths); Under-scope rewritten to record the DECISION and its reasoning rather than the question; E-06's conditional resolved in favour of `CONTRIBUTING.md` (confirmed to already document `make test`, `pre-commit install` and `aw check-local-leaks`) and the fallback withdrawn; V-06 item (c) no longer asks for an `aw ipd set` widening; the scope-fence paragraph in the gate names the comment-only constraint on those eleven. |
| PR-005 | MEDIUM | IN-SCOPE | Rubric E (testing), honest baselines | Plan F-12 (`3387 passed`, "fully green"); `python3 -m pytest` at review HEAD reporting `1 failed, 3446 passed, 2 skipped`; the isolated failure's `2026-09-30` versus `2026-10-01` assertion diff | F-12 asserts "THE BASELINE IS FULLY GREEN, so any failure after this plan is this plan's to explain", and validation step 2 demanded "ZERO failures". The tree is not green: `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` fails on a hardcoded date the clock has passed. The authored bar is therefore unsatisfiable, and an executor meeting it would either misattribute a pre-existing red to their own work or paper over it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-12 rewritten to record the failure, name it, and state its cause; validation step 2's bar changed from "ZERO failures" to "no NEW failure against YOUR before-baseline"; the `## Required tests` preamble and the gate's scope fence both forbid fixing it as out of scope and another party's. |
| PR-006 | MEDIUM | IN-SCOPE | Rubric D (anti-regression), triage correctness | Plan F-05's "remaining findings ... are annotation-precision issues"; `render_stream.py:779` `render_event -> str or None`; `oc_runipd.py` three call sites, the consuming one guarded by `if rendered is not None:` | F-05 classifies `render_stream.render_event`'s finding as an annotation-precision issue. It is a `[return]` finding, the identical code and shape as F-06's live bug, and the plan elsewhere instructs the executor that the fix for that shape is to add the missing return rather than widen the annotation. An executor could reasonably apply that reasoning here and change working code: the `-> str or None` union annotation is CORRECT, because the sole consuming caller guards on `None`. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | F-05 corrected to name `render_event` as a `[return]` finding with a CORRECT annotation and to cite the caller's guard; F-05 also now classifies the other previously-unexplained residue (`cli.py`'s `argparse.error` override and `set.add`, `run_packet.py`'s snapshot type, the two `in` operands); E-05 gains an explicit instruction to suppress it and NOT treat it as a second live defect; V-05 gains item (g) requiring the executor to confirm that. |
| PR-007 | LOW | IN-SCOPE | Rubric C (operability), measurement honesty | Plan F-11 (`14.2s` cold, `0.23s` warm); review `real 0m26.654s` cold and `real 0m0.470s` warm at HEAD `a4e7f31e` | F-11's cold timing is presented as a figure but is machine- and load-dependent, measuring 26.7s at review against the authored 14.2s, a 1.9x difference that would make a reader doubt the measurement rather than the machine. The warm figure, which is the one a pre-commit decision actually turns on, is stable and tiny in both. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-11 restated with both measurements, cold characterized as tens of seconds rather than a figure, and the warm path identified as the number that governs OQ-02; OQ-02's own timing sentence rewritten to lead with the warm figure and name the stale-cache case as the real consideration. |
| PR-008 | LOW | IN-SCOPE | Rubric G (live-artifact convention) | Plan F-04's eighteen-code census; review's re-census at HEAD `a4e7f31e` | F-04 lists a per-code census to the unit (`arg-type` 71, `attr-defined` 56, `assignment` 49, `misc` 44, `union-attr` 34). Four of those five moved by review (77/56/51/44/35) while every code's RANK stayed put, so the census was reported in its least durable form. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04 restated so the ORDERING and the residue's COMPOSITION are the finding, with both dated censuses kept as context and an explicit instruction to assert the property rather than an integer. |
| PR-009 | LOW | UNDER-SCOPE | Rubric C (architecture), stated bounds | Plan `- Scope:` (gate covers `agent_workflows/`); `tools/`, `conftest.py` unmentioned | The plan documents `tests/` as a deliberate omission (OQ-06) but says nothing about `tools/` or the root `conftest.py`, leaving a reader unable to tell whether their exclusion is a decision or an oversight. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a "Deferred / out of scope" entry recording the omission as deliberate and unmeasured, carrying the same reasoning OQ-06 gives for `tests/`, with `fcua9q` as carrier. |
| PR-010 | LOW | IN-SCOPE | Rubric C/E (coverage justification) | Plan E-03 (one OS) versus F-05's three platform-conditional findings; three `--platform` runs (default, `win32`, `darwin`) each reporting `Found 24 errors in 12 files` | E-03 pins a single OS while the `unittest` job spans three and F-05 names three platform-conditional findings, which leaves an obvious unanswered question about whether the one-OS gate is a coverage hole. The plan justified single-Python at length and single-OS not at all. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-14 measures the gate platform-INVARIANT (mypy analyzes a declared platform, so Windows-only branches are checked everywhere); E-03 states it and requires the job comment to record it; V-03 gains item (e) requiring the executor to re-derive it with two `--platform` runs. |
| PR-011 | LOW | IN-SCOPE | Rubric G (executability) | Plan E-04's test instruction ("Construct a `RecoveryDisposition` with `verify_and_continue` true"); `RecoveryDisposition._fields`; `runner_shared.py:29313` `def verify_and_continue(self) -> bool` | E-04 tells the executor to construct a `RecoveryDisposition` with `verify_and_continue` true. That is not constructible as written: `verify_and_continue` is a derived `@property`, not one of the ten NamedTuple fields, so it must be reached via `disposition="verify-and-continue"`. The instruction sends the executor into a failed attempt before they discover the real shape. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now names all ten `_fields`, states that `verify_and_continue` is a derived property reached through `disposition=`, records that no existing test calls the function at all, and requires the no-op case be asserted as `""` rather than merely falsy (since `None` and `""` are both falsy and only the equality distinguishes fixed from broken). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-05 edits eleven modules the plan does not declare; widen `- Scope-Paths:` or split E-05 into a follow-on plan? (The plan explicitly handed this to the reviewer.) | Widen: declare all eleven modules plus `CONTRIBUTING.md`, 17 paths total. | Splitting E-05 into a follow-on, which the plan offered as option (b). Rejected because the gate cannot arrive fail-closed without E-05, so the split forces E-03 to land advisory, and E-03's own text argues at length that an advisory gate reproduces the fail-open defect `fcua9q` was filed about. | The plan's own E-03 text; the edits are trailing `# type: ignore[...]` comments on existing lines, which cannot change behavior; `aw ipd finalize`'s `--scope-reason`/`--scope-ack` reconciliation is the backstop the repository already uses for fence exceptions (AGENTS.md scope-fence ruling of 2026-09-01). | yes |
| D-2 | E-06 says `CONTRIBUTING.md` "if it documents the local check commands, otherwise the `[tool.mypy]` comment block". Which? | `CONTRIBUTING.md`, declared in scope, fallback withdrawn. | Leaving the conditional for the executor to resolve (the authored shape), which would have meant either an undeclared path or an arbitrary choice. | `CONTRIBUTING.md` already documents `make test`, `make test-all`, `make test-serial`, `pre-commit install` and `aw check-local-leaks` as the local developer-check commands, which is exactly the list `make typecheck` belongs beside. | yes |
| D-3 | The baseline is environment-dependent (F-13). Pin the runtime `filelock` dependency, or pin only in the test extra? | Pin in the `test` extra and `dev` group only; `dependencies` stays exactly `["filelock>=3"]`. | Tightening the runtime `dependencies` specifier, which would have made the baseline trivially reproducible. Rejected: it constrains every downstream installer to suit a developer tool. | D138 (dependency minimization); the plan's own no-runtime-dependency promise, which V-01 and validation step 6 exist to prove; `pyproject.toml` `dependencies = ["filelock>=3"]`. | yes |
| D-4 | What shape should mypy's upper bound take? | A generous major boundary (e.g. `>=1.18,<3`), not a frozen point release. | Freezing an exact version, which would make every routine upgrade a code change; leaving it unbounded, which is the defect PR-003 reports. | Review measured NO baseline drift across pinned `1.18.2`, `1.19.1`, `2.0.0` and `2.3.1` on this tree, so the risk is a future major rather than a current incompatibility; F-08 measured the one behavior change landing at a major boundary (`2.0.0`). | yes |
| D-5 | `render_stream.render_event` produces the same `[return]` code as F-06's live bug. Second defect, or correct annotation? | Correct annotation; suppress or add an explicit `return None`, do NOT invent a return value. | Treating it as a second live bug and fixing it, which is what the plan's own E-04 reasoning would lead an executor to do. | `oc_runipd.py`'s consuming `render_event` call site guards with `if rendered is not None:` before using the value, so `None` is a documented outcome rather than a failure; the other two call sites discard the return entirely. | yes |
| D-6 | The suite has a pre-existing failure. Fix it, or carry it? | Carry it as a known pre-existing failure; the plan explicitly forbids fixing it. | Fixing it inside this plan, which would be an undeclared out-of-scope edit to another party's test in a shared checkout. | The failure is a hardcoded `2026-09-30` versus `date.today() == 2026-10-01` in `tests/test_backlog.py`, touching no path this plan declares; AGENTS.md's shared-checkout rule against modifying work that is not yours. | yes |
