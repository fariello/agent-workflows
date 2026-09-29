# IPD: Refuse a new code-structure pin in tests at author time instead of discovering it after the next sweep

- Date: 2026-09-28
- Kind: child
- Concern: THE WRITTEN POLICY ALONE DOES NOT HOLD, MEASURED. `GUIDING_PRINCIPLES.md` P16 prohibits reading production source in a test, and the repository has swept four times to enforce it (`856acd63` 46 pins to 6, `ba4f205b` 52 to 30, `80db6750` 366 tests deleted, `19313eed` the suite trimmed from 9,136 tests to under 2,000). A pin came back anyway: `19313eed` (2026-09-24T17:54) removed `OneOriginatingDefinitionTests` with its `ast.parse` package walk from `tests/test_term.py`, and `64c04288` (2026-09-28T14:09) added `SingleOriginatingDefinitionTests` to `tests/test_interactivity_resolver.py`, whose docstring states it was "Recovered from commit `19313eed^:tests/test_term.py`" and lists the AST mechanism among the "four load-bearing properties" it deliberately preserved. An author acting in good faith RESURRECTED a deleted pin because nothing told them it was forbidden at the moment they wrote it, and P16 itself landed four hours later (`6a6eb66c`, 2026-09-28T18:16). NOTHING MECHANICAL NOTICES THIS TODAY: `aw check`'s rule families all scan `.aw/records` (verified: no rule in `check_engine` references a `tests` path), the three local pre-commit hooks cover leaks and plan lifecycle only, and `pyproject.toml` declares no `[tool.ruff]` section, so there is no configured lint surface to extend. The cost of the gap is measured in the sibling plan: six pins survived in the tree, and one of them (`test_add_output_mode_flags_not_reforked_in_hosts`) admits its own blindness in its docstring while still failing on any reformat.
- Scope: Add ONE guard test that refuses a new production-source read in `tests/`, carrying a documented allowlist for the narrow exception P16 already grants, and point `CONTRIBUTING.md` at P16 so an author meets the rule while authoring rather than after a sweep. Deliberately NOT an `aw check` rule and NOT a pre-commit hook; the rationale is recorded in Findings and the alternatives were evaluated rather than skipped. EXCLUDES restating or deleting the six existing pins, which is Order 01 (`b02ohu`) and MUST land first, because this guard is red on arrival while they exist. EXCLUDES detecting the count-shaped assertion in general, which is undecidable syntactically and is recorded as an accepted bound rather than silently ignored.
- Scope-Paths: tests/test_no_code_structure_pins.py, CONTRIBUTING.md
- Item-Dependencies: executed:b02ohu
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: 5zyuc8
- Set: structpin
- Order: 2
- Highest E allocated: 04
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 76ic0k

## Workflow history

- 2026-09-28 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog `5zyuc8`, whose SUGGESTED WORK asks for the sweep AND for "a lint or a review checklist item [to] stop new ones being written". Order 01 is the sweep; this is the stopper. Two design choices were made against measured evidence rather than by preference and are recorded in Findings so a reviewer can contest them: the guard is a TEST rather than an `aw check` rule (because `aw check --dir` runs against MANAGED TARGET repositories, where imposing this repository's test policy would be wrong, and because no existing rule scans `tests/`), and it detects the SOURCE-READ MECHANISM rather than the count-shaped assertion (because the mechanism is syntactically decidable and the count shape is not, so a guard aimed at counts would be a heuristic that both misses and misfires).
- 2026-09-28 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Make the next author who reaches for `inspect.getsource` or `ast.parse` in a test get a refusal that names
P16 and says what to do instead, at the moment they run the suite, rather than four days and one sweep later.

The guard must be honest about what it cannot see. It is not a proof that no pin exists; it closes the one
entry route that all six surviving pins and both deleted ancestors actually used.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the guard

- [ ] E-01 WRITE `tests/test_no_code_structure_pins.py`, A SINGLE GUARD THAT WALKS EVERY `tests/**/*.py` WITH `ast` AND REFUSES A PRODUCTION-SOURCE READ. Flag, by ATTRIBUTE-CALL form: `inspect.getsource`, `inspect.getsourcelines`, `inspect.getsourcefile`, and `ast.parse`/`ast.walk`/`ast.unparse`. Use the attribute form deliberately, not a bare-name or substring match, for a measured reason: the sanctioned exception `tests/test_carrier_scan_single_item_contract.py` contains those names as DATA (its `TARGET_FUNCTIONS` and its fixture source strings), so a substring scan would misreport them. Measured at authoring HEAD `a314c925`, NO test file imports either module in aliased or from-import form (`from ast import`, `from inspect import`, `import ast as`, `import inspect as` all return zero matches across `tests/`), so the attribute form is sufficient today; the guard must state that as its bound rather than implying completeness. THE GUARD MUST NOT READ PRODUCTION SOURCE ITSELF: it parses files under `tests/`, which are the artifact under test, squarely inside P16's stated exception ("where the text or file itself is the artifact under test"), the same footing as `tests/test_artifact_adopt.py`'s scan of `Path(__file__)`. Model the whole file on `tests/test_carrier_scan_single_item_contract.py`, which is the repository's established shape for an AST guard shipped as a test: a `NamedTuple` violation record with a `render()` method, a module docstring stating SCOPE and KNOWN HOLE, and positive and negative fixtures over source STRINGS so the detector is proven to fire and proven not to over-fire. The failure message must be actionable, not merely a refusal: name the file, the line, the call, and P16 by name, and say what to do instead (exercise the code and assert observable outputs).
  - Depends on: none
  - Expected outcome: `tests/test_no_code_structure_pins.py` exists; run against the post-Order-01 tree it reports exactly ZERO violations; its positive fixtures prove each of the six detected call forms is caught and its negative fixtures prove `inspect.signature` and a `read_text()` on a non-package path are NOT caught.
  - Execution state: pending

- [ ] E-02 GIVE THE GUARD A TYPED, JUSTIFIED ALLOWLIST OF EXACTLY ONE ENTRY, AND MAKE A STALE ENTRY FAIL. The allowlist must be a table of `(path, reason)` rather than a bare set of paths, because a path with no stated reason is how an allowlist becomes a place to hide a new pin. One entry at authoring: `tests/test_carrier_scan_single_item_contract.py`, whose subject is a quadratic-performance hazard with no behavioral proxy (its own header forbids adding timing assertions as flaky), which asserts ZERO counts as invariants (its single numeric assertion is a `>=` non-vacuity floor), and which documents its own scope and known hole. THE ALLOWLIST MUST BE SELF-CLEANING: assert that every allowlisted path EXISTS and STILL CONTAINS at least one flagged call, so an entry that stops being needed (or whose file is renamed or deleted) fails LOUDLY instead of silently granting a permanent exemption to a path nobody checks. Do NOT allowlist `tests/test_leak_sanitizer.py`, `tests/test_local_leaks.py` or `tests/test_artifact_adopt.py`: verified at authoring, none of them calls any of the six flagged forms (they use `read_text()`, which this guard deliberately does not flag; see E-03's recorded bound), so allowlisting them would create exactly the stale entry this item forbids.
  - Depends on: E-01
  - Expected outcome: the allowlist is a `(path, reason)` table with one entry carrying its full justification; a test asserts each entry's file exists and still contains a flagged call; shown to FAIL when a fabricated allowlist entry naming a clean file is added, then reverted.
  - Execution state: pending

- [ ] E-03 STATE THE GUARD'S THREE BOUNDS IN ITS MODULE DOCSTRING, BECAUSE AN OVERCLAIMED GUARD IS WORSE THAN A NARROW ONE. (a) IT DOES NOT FLAG `read_text()`, even though P16 names it, because `read_text` is the ordinary way a test reads a FIXTURE it just wrote: measured at authoring, 99 test files call `read_text` while also mentioning `agent_workflows`, and nearly all are reading temp-directory fixtures, so flagging the call would produce mass false positives, while resolving the ARGUMENT to a package path requires dataflow analysis the repository has already declined to build (`tests/test_carrier_scan_single_item_contract.py`'s KNOWN HOLE records the same trade-off for the same reason). (b) IT DOES NOT FLAG COUNT-SHAPED ASSERTIONS AT ALL, which is the backlog item's headline defect: `assertEqual(len(x), 3)` is indistinguishable, syntactically, from a legitimate assertion about a collection of OUTPUTS, and the repository has legitimate literal censuses it must not break (the declared subparser set in `tests/test_releases_cli.py`, the flag surfaces in `tests/test_runner_shared.py`). The guard closes the SOURCE-READ route those pins used to obtain code structure in the first place, which is the part that is decidable. (c) IT IS NOT A PROOF OF ABSENCE: a pin written through `importlib`, a bare-name import, or `__code__` introspection evades it. Say all three plainly, and say what covers the gap instead: P16 as the written rule, and `/plan-review` as the human pass.
  - Depends on: E-01
  - Expected outcome: a module docstring stating all three bounds, each with its reason, matching the established shape of `tests/test_carrier_scan_single_item_contract.py`'s SCOPE and KNOWN HOLE sections.
  - Execution state: pending

### Task group 2: reach the author before they write it

- [ ] E-04 ADD ONE POINTER BULLET TO `CONTRIBUTING.md` UNDER `## Authoring conventions`, AND RESTATE NOTHING. That section's own established pattern is delegation: it already reads "Keep each policy or rule in exactly one canonical place and link to it, rather than duplicating it (P8)", and its neighbouring bullets cite `GUIDING_PRINCIPLES.md` P2 and P14 by reference rather than quoting them. So the bullet names the rule (tests assert behavior, never code structure), points at P16 as the canonical home, and names the guard test so an author who trips it knows where the rule lives. DO NOT restate P16's four prohibitions here, and do NOT edit `GUIDING_PRINCIPLES.md`: P16 already says everything this Set needs, and duplicating it is the P8 violation the same section warns against. Do NOT touch `## Self-tests (run before pushing tool changes)`, which governs how to RUN the suite rather than how to author a test; keeping the two separate is what stops them drifting. NOTE the user-facing-prose dash rule applies to `CONTRIBUTING.md`: write no em or en dashes in the bullet.
  - Depends on: E-01
  - Expected outcome: one new bullet quoted from `CONTRIBUTING.md`'s `## Authoring conventions`, naming P16 and the guard test, restating no prohibition; a diff confirming no other section of the file changed; no em or en dash in the added text.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `GUIDING_PRINCIPLES.md` P16 ("Test outcomes and behavior, never code structure or text") is the canonical policy, landed in `6a6eb66c`. It prohibits production source inspection, count/census pins, text/banner/docstring pins and architectural placement pins, and grants ONE exception, "where the text or file itself is the artifact under test".
- `tests/test_carrier_scan_single_item_contract.py` is the repository's established shape for an AST guard shipped as a test, and this plan copies it deliberately: a `NamedTuple` violation record, a module docstring with explicit SCOPE and KNOWN HOLE sections, fixtures over source strings, and a `>=` non-vacuity floor rather than an `==` census.
- `agent_workflows/check_engine.py` composes whole-tree rules on a once-per-full-sweep seam inside `check_types`'s `if collisions:` branch, each in its OWN `try/except` so one failing scan cannot suppress another, with rule ids named `check.<kebab-noun-phrase>` registered in `RULE_REGISTRY` as a `RuleSpec(severity, assurance, determinism, invariant)`. This is the mechanism a check rule WOULD use; Findings records why this plan does not use it.
- `artifact_core.drift_exit_code` exempts only `info`, so a `warning` fails the gate exactly as an `error` does. A new advisory-only check rule is therefore not available as a soft-landing option.
- `.pre-commit-config.yaml` carries three local hooks (`local-leaks`, `ipd-executed-transition-gate`, `ipd-status-untooled-gate`), each `language: system` with `pass_filenames: false`, and each records in its own comment that it is "Best-effort/local only (skippable with `--no-verify`); the deterministic backstop is ... `aw check`".
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

### Why a test, and not an `aw check` rule

Two measured reasons, both decisive.

FIRST, `aw check` RUNS AGAINST MANAGED TARGET REPOSITORIES. Its parser declares `--dir DIR  Repo root (default: current directory)`, and this toolkit's whole purpose is to be installed into other repositories. A rule refusing `inspect.getsource` in `tests/` would therefore fire on a target repository's own test suite and impose THIS repository's testing policy on a codebase that never adopted it. P16 is our principle; `aw check`'s rule families are a contract we ship. Note the honest counter-argument: the rule could be scoped to fire only when the repo root IS this toolkit, but a rule that deliberately no-ops almost everywhere it runs is worse documentation than a test that lives where it applies.

SECOND, NO EXISTING CHECK RULE SCANS `tests/`. Verified: `check_engine` contains no reference to a `tests` path, and its 89 `records` references show what it is for, the `.aw/records` artifact trees. A rule reaching into source directories would be the first of its kind, and it would need its own file-discovery, its own gitignore handling and its own untracked-file policy, all of which `pytest` already provides for free.

A pre-commit hook was rejected for the reason the existing hooks state about themselves in their own comments: local, not cloned by default, skippable with `--no-verify`. The suite, by contrast, is what CI runs and what `make test` runs, so it is the surface an author actually meets.

### Why the mechanism, and not the count

The backlog item's headline defect is the COUNT-SHAPED ASSERTION, and this guard deliberately does not detect it. `assertEqual(len(callers), 2)` and `assertEqual(len(emitted_events), 2)` are the same syntax; the first is a pin and the second is correct behavioral coverage. The repository also holds literal censuses it must not break, where the number IS the operator-visible contract: `tests/test_releases_cli.py::ReleasesParserTests::test_subcommands_are_exactly_list_show_new` and the flag-surface tests in `tests/test_runner_shared.py`. A count-detecting guard would therefore need an allowlist proportional to the suite, which is the "tax on correct changes" the backlog item is complaining about, reimplemented as the cure.

What IS decidable is HOW a test obtains code structure in the first place. Every one of the six surviving pins and both deleted ancestors read production source via `inspect.getsource` or `ast.parse`. Closing that route is a real narrowing with a stable, tiny allowlist (one entry).

### The detection surface, measured at HEAD `a314c925`

Scanning every `tests/**/*.py` for attribute-form calls to the six flagged names found FOUR files and 23 call sites:

```
tests/test_carrier_scan_single_item_contract.py: 7 hits -> ['ast.parse', 'ast.walk']
tests/test_host_capability_wiring.py: 5 hits -> ['ast.parse', 'ast.walk']
tests/test_interactivity_resolver.py: 4 hits -> ['ast.parse', 'ast.walk']
tests/test_runner_shared.py: 7 hits -> ['ast.parse', 'ast.unparse', 'ast.walk', 'inspect.getsource']
TOTAL files: 4
```

Order 01 (`b02ohu`) removes the last three. That is why this plan declares `- Item-Dependencies: executed:b02ohu`: run before it, this guard is RED ON ARRIVAL with three files to explain, and its only available remedies would be a four-entry allowlist (institutionalizing the pins the Set exists to remove) or deleting them inside this plan (merging two separately reviewable concerns into one change).

### Why the allowlist is a table with reasons, and self-cleaning

An allowlist of bare paths is a place to hide a pin: an entry costs nothing to add and nothing to justify. Requiring a stated reason per entry makes the addition a visible claim a reviewer can contest. Requiring that each entry's file still CONTAIN a flagged call makes the exemption expire on its own, which matters here specifically because this repository has already had a stale exemption shape bite it: the `tests/test_runner_shared.py` census tables Order 01 deletes are dead data whose reader was removed in `19313eed`, and nothing noticed for days.

## Proposed changes (ordered, validatable)

1. E-01 writes the guard and proves it fires (positive fixtures) and does not over-fire (negative fixtures).
2. E-02 adds the one-entry justified allowlist and proves a stale entry fails.
3. E-03 records the three bounds in the docstring, so the guard does not overclaim.
4. E-04 adds the single `CONTRIBUTING.md` pointer bullet.

E-02, E-03 and E-04 each depend on E-01 and are otherwise independent of each other.

## Deferred / out of scope (with reason)

- RESTATING OR DELETING THE SIX EXISTING PINS is Order 01 (`b02ohu`). This plan must not touch them; if it did, the guard and the sweep would land in one unreviewable change.
  - Carrier: b02ohu
- DETECTING COUNT-SHAPED ASSERTIONS is out of scope on the reasoning in Findings: it is not syntactically decidable and a heuristic would misfire on the repository's legitimate censuses. The written rule (P16) and `/plan-review` cover it.
  - Carrier-Declined: This is a PERMANENT DESIGN BOUND, not deferred work, so no carrier should exist to imply it will be built later. `assertEqual(len(x), 2)` over call sites and over emitted outputs are the same syntax, so any detector is a heuristic that both misses pins and misfires on the repository's legitimate censuses (the declared subparser set in `tests/test_releases_cli.py`, the flag surfaces in `tests/test_runner_shared.py`). E-03 requires the guard's own docstring to state this bound, and `GUIDING_PRINCIPLES.md` P16 plus `/plan-review` remain the standing cover. Filing a carrier for it would promise a mechanism that should not be built.
- FLAGGING `read_text()` is out of scope: resolving its argument to a package path needs dataflow analysis, and flagging the call unconditionally would fire on the many tests that legitimately read a fixture they just wrote. Recorded as bound (a) in E-03 rather than silently omitted.
  - Carrier-Declined: A PERMANENT DESIGN BOUND with a measured basis (99 test files call `read_text` while also mentioning `agent_workflows`, nearly all reading temp-directory fixtures they just wrote), and the same trade-off `tests/test_carrier_scan_single_item_contract.py` already records as its own KNOWN HOLE for the same reason. Adding dataflow analysis to resolve the argument is complexity this repository has explicitly declined once already, so a carrier would misrepresent a settled decision as pending work.
- A PRE-COMMIT HOOK is deliberately not added, for the reason the three existing local hooks state about themselves: local, not cloned by default, skippable. If a future maintainer wants belt-and-braces, the hook is additive and needs no change here.
  - Carrier-Declined: A DELIBERATE DESIGN CHOICE, not a gap. The suite is the surface CI and `make test` both run, so it already reaches every author; a hook would add a skippable local duplicate of a check that already fails closed in CI. The hook remains purely additive if a maintainer later wants it, requiring no change to anything this plan lands, so there is no outstanding obligation to carry.
- `tests/test_walkthrough_id6.py`'s literal 24-walkthrough census is a census over the RECORDS tree rather than over code structure, so this guard would not catch it and must not be widened to try.
  - Carrier: zf1m48

## Scope check

- Over-scope: none. Two paths, one new test file and one pointer bullet. No production module is touched.
- Under-scope: the guard closes one entry route, not all of them. `importlib`-based source reading, bare-name imports and `__code__` introspection all evade it, which E-03 requires the docstring to say out loud. It also does nothing about count-shaped assertions that obtain their counts without reading source, which is a real residue of the backlog item's general defect and is left to P16 and `/plan-review`.

## Required tests / validation

The guard is itself the test, so validation is mostly about proving it is NOT VACUOUS, which is the specific failure mode of a guard that passes by finding nothing. Each of E-01 and E-02 therefore demands a demonstrated failure and a revert, not just a green run.

The suite baseline measured at authoring HEAD `a314c925` was `3235 passed, 2 skipped` with 207 deselected. Re-derive it at execution; Order 01 lands first and is expected to LOWER the count, so the authoring number is not the baseline this plan will see.

## Spec / documentation sync

No `.spec.md` amendment is owed, and no spec path appears in `Scope-Paths`. No spec describes the suite's assertion mechanisms; the policy lives in `GUIDING_PRINCIPLES.md` P16, which this plan cites and deliberately does not edit. The only documentation change is the one `CONTRIBUTING.md` pointer bullet in E-04, which is a reference and not a restatement, per P8 and per that section's own stated convention.

## Open questions

### OQ-01: Should the guard also fail a test that reads production source through `importlib` or a bare-name import?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE as NO, do not detect those routes, and state the omission as a bound instead (which E-03 already requires). Two measurements settle it without a maintainer decision. FIRST, the route is unused: searching `tests/` for `from ast import`, `from inspect import`, `import ast as` and `import inspect as` returns ZERO matches, so every existing source read, including all six pins Order 01 removes and both deleted ancestors, arrived through the attribute form this guard does detect. Building detection for a spelling nobody uses is the hypothetical-need generality `GUIDING_PRINCIPLES.md` P6 directs against. SECOND, the repository has already settled the identical question in the identical shape: `tests/test_carrier_scan_single_item_contract.py` records a KNOWN HOLE (a loop variable rebound to a temporary evades its analyzer) and declines to close it, stating the trade-off as deliberate because "the direct loop variable and comprehension bindings are the shapes that have bitten the repository in practice, while tracking arbitrary dataflow would add complex analysis machinery without practical gain". That is the same reasoning and the same conclusion, from the file this plan takes as its model. The standing cover for the residue is P16 as the written rule and `/plan-review` as the human pass. If a first instance ever appears, the correct response is to EXTEND the detector, not to allowlist the file, and E-03's docstring bound (c) is what tells a future maintainer that.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a pasted run of `tests/test_no_code_structure_pins.py` on the post-Order-01 tree showing it passes with ZERO violations. NON-VACUITY, demonstrated and not asserted: temporarily add a file under `tests/` containing one `inspect.getsource(...)` call on a package symbol, paste the resulting FAILURE showing the message names the file, the line, the call and P16, delete the probe, paste the pass. Plus the positive fixture results proving all six flagged forms are detected, and the negative fixture results proving `inspect.signature` and a `read_text()` on a non-package path are NOT flagged (this negative matters: over-firing on `inspect.signature` would break the legitimate API-surface tests in `tests/test_reap_contract.py` and `tests/test_run_selection_policy.py`, so name those files and show they still pass).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the allowlist quoted in full, showing exactly one entry with its stated reason. The self-cleaning property demonstrated: add a fabricated entry naming a file with no flagged call, paste the FAILURE, remove it, paste the pass. Confirm by search that `tests/test_leak_sanitizer.py`, `tests/test_local_leaks.py` and `tests/test_artifact_adopt.py` are NOT allowlisted and do not need to be (paste the search showing none of them calls any of the six flagged forms); if that has changed since authoring, say so and state which now needs an entry and why.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the module docstring quoted, showing all three bounds present with their reasons (no `read_text` detection, no count detection, not a proof of absence). Plus the re-measured figure supporting bound (a), the number of test files calling `read_text` while also mentioning `agent_workflows` (authoring baseline: 99 files), so the claim rests on a number taken at execution rather than on the authoring estimate.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the added `CONTRIBUTING.md` bullet quoted; `git diff` for the file pasted, showing only that one bullet changed and that `## Self-tests (run before pushing tool changes)` is untouched; a confirmation that the added text contains no em or en dash; and a confirmation that `GUIDING_PRINCIPLES.md` was NOT modified by this plan.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

DO NOT EXECUTE BEFORE ORDER 01 REACHES `executed`. This plan declares `- Item-Dependencies: executed:b02ohu` and the dependency is load-bearing, not cosmetic: run first, the guard is RED ON ARRIVAL against three files Order 01 is removing, and the only ways to make it green are to allowlist the very pins the Set exists to delete or to delete them here, outside this plan's declared scope. The runner re-checks dependencies at dispatch and will mark this item `dependency-blocked` rather than run it; an agent executing the Set by hand must honor the same order.

EXECUTE ONLY WHAT THIS PLAN DECLARES. The two `Scope-Paths` entries are the whole authorized surface. If the guard fires on a file this plan did not predict, STOP and report it: the correct response is a decision about that file, which may belong to a new carrier, and never a silent allowlist entry added to make the suite green. An allowlist entry without a stated reason is the failure mode E-02 exists to prevent, so adding one to get past a surprise would defeat the plan while appearing to complete it.

DO NOT WEAKEN THE GUARD TO MAKE IT PASS. A guard that passes because it detects nothing is worse than no guard, since it advertises a protection that does not exist. V-01 and V-02 therefore require a DEMONSTRATED failure and revert, not an assertion that the guard would fail.

HONESTY. Paste actual runner output; never claim a test run you did not perform. Where an authoring baseline is quoted (the 23 call sites in four files, the zero aliased imports, the read_text file count), re-measure at execution and report the new number if it differs rather than restating the authoring figure.

COMMIT DISCIPLINE. Commit through `aw commit <plan> -- <paths>`, path-scoped to the two files this plan names, never `git add -A`/bare/`-a`, and never push. Other agents may be working in this checkout: verify the staged set with `git diff --cached --name-only` before committing and unstage anything that is not yours with `git restore --staged <path>`.

LIFECYCLE. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` item must carry pasted evidence before this plan moves to `.aw/records/plans/executed/`. Use the tooled transition; do not hand-edit `- Status:`.
