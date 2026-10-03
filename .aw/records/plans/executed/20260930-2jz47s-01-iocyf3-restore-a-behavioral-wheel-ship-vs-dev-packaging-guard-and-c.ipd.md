# IPD: Restore a behavioral wheel ship-vs-dev packaging guard and correct CONTRIBUTING's two unguarded packaging claims

- Date: 2026-09-30
- Kind: child
- Concern: `CONTRIBUTING.md` attributes the wheel ship-vs-dev boundary to `tests/test_packaging.py`, which commit `19313eed` deleted, so nothing asserts that boundary. Authoring BUILT THE WHEEL and measured that the boundary HOLDS today (0 forbidden entries of 356) while being wholly unguarded, and found a SECOND false claim in the same passage the item does not name: the paragraph's "there are ZERO runtime dependencies" is contradicted by the wheel's own `Requires-Dist: filelock>=3`, which `DECISIONS.md` D138 deliberately authorized.
- Scope: Restore a behavioral packaging guard at `tests/test_packaging.py` that builds the wheel and asserts the ship-vs-dev boundary plus the runtime-dependency allowlist, re-measuring both at execution HEAD; correct the THREE false claims in `CONTRIBUTING.md`'s "Packaging and the CLI" section (the dangling test citation, the zero-runtime-dependency parenthetical, and the same bullet's trailing "no runtime dependency is declared" assertion that review measured and the backlog item does not name) so each names what actually enforces it. EXCLUDES the sdist half of the deleted suite, EXCLUDES the four `docs/` danglers that pending plan `1jg2m2` owns, and EXCLUDES any change to `pyproject.toml`'s packaging configuration, which authoring measured to be correct. ON THE `CONTRIBUTING.md` PACKAGING PARAGRAPH THIS PLAN AND `1jg2m2` GENUINELY CONTEND, and the coordination is by RE-READ AND BRANCH inside E-05, NOT by `- Item-Dependencies:`, which is deliberately `none` for the reasons OQ-02 records (corrected at review: the earlier wording claimed an edge this plan does not and should not declare).
- Scope-Paths: tests/test_packaging.py, CONTRIBUTING.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: 2jz47s
- Set: 2jz47s
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: iocyf3

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: iocyf3 verified (set 2jz47s, attempt 1).
- 2026-10-01 approved (aw set): status set to approved

- 2026-09-30 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-P01 through PR-P09 all FIXED in place. Structural lint conformed at `author` and reports zero findings at `review-finalize`. INDEPENDENTLY RE-RAN THE PLAN'S CENTRAL MEASUREMENT at HEAD `170368788`: built the wheel (356 entries, 2.09s and 2.57s warm) and applied the deleted test's own forbidden sets, getting ZERO violations, so the plan's premise that the boundary HOLDS and only the guard is missing is confirmed, and restoration rather than prose-weakening is the right fix. Also re-verified the deleted file carries no `slow` marker, the build needs the network (`PIP_NO_INDEX=1` fails; `hatchling` absent so `--no-isolation` fails), `pyproject.toml` needs no change, and no surviving test builds a wheel. FOUR THINGS REVIEW FOUND THAT THE PLAN DID NOT: a THIRD false claim in the same bullet (`and that no runtime dependency is declared`), which E-05 would have left standing while claiming to fix the paragraph (F-11); F-5's substring trap is FALSE as filed, since the shipped `workflow-artifacts-README.md` does not contain the slash-bearing forbidden token and bare substring matching measures ZERO hits exactly as `startswith` does (F-5 corrected, E-03 rewritten); `1jg2m2` is `reviewed`/`go-pending-approval` rather than `to-review`, which falsifies half of OQ-02's stated basis while leaving its conclusion standing (F-12), and it also adds a citation guard scanning `CONTRIBUTING.md` that measures GREEN in BOTH landing orders (F-13); and CI's slow step is `continue-on-error: true`, so the `slow` option OQ-01 weighs would leave the guard non-blocking everywhere (F-15). Human approval is still required, and OQ-01 remains open and NON-BLOCKING. (Review record: `.aw/records/reviews/20260930-2jz47s-01-iocyf3-restore-a-behavioral-wheel-ship-vs-dev-packaging-guard-and-c.review.md`.)
- 2026-10-01 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): status transition applied by `aw ipd set reviewed iocyf3`, kept beside the `/plan-review` line above as the attributed record of the transition itself. Its date is the setter's UTC stamp while the local date was 2026-09-30, the clock skew backlog `fnb8pl` owns.

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `2jz47s`. GATE NOTE: the item carries NO `- Blocks-Release:`, so this plan inherits none; `- Work-Kind: followup` is INHERITED and is retained, because restoring absent coverage is not itself a user-perceptible defect (`AGENTS.md`'s perceptibility test), and authoring MEASURED that the guarded property currently HOLDS, so there is no live defect to gate. THE ITEM'S CLAIM VERIFIES IN FULL AND AUTHORING EXTENDED IT IN TWO DIRECTIONS. Verified: `ls tests/test_packaging.py` reports no such file; `git log --diff-filter=D --name-only -- tests/test_packaging.py` names `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24); `CONTRIBUTING.md`'s sentence containing `ship-vs-dev boundary is enforced by` still cites it; and no surviving test builds a wheel and asserts its contents (the `.whl` hits in `tests/test_local_leaks.py` and `tests/test_leak_sanitizer.py` are leak-scanner MODES, and no test matches `force-include` or `hatch.build`). FIRST EXTENSION, AND IT IS THE REASON THIS PLAN RESTORES A TEST RATHER THAN ONLY EDITING PROSE: authoring BUILT THE WHEEL (`python3 -m build --wheel`, succeeded, 356 entries) and ran the deleted test's forbidden-content assertions against it, measuring ZERO violations. So the boundary HOLDS and the only thing missing is the guard, which makes restoration the honest fix (shape (a), re-point at a guard) rather than the prose-weakening (shape (b)) that pending plan `1jg2m2` E-06 prescribes having explicitly declined to build a wheel. SECOND EXTENSION, A DEFECT NEITHER THE ITEM NOR `1jg2m2` NAMES: the SAME `CONTRIBUTING.md` paragraph asserts "there are ZERO runtime dependencies", and the built wheel's METADATA declares `Requires-Dist: filelock>=3`. That is not a packaging regression; `DECISIONS.md` D138 deliberately reframed dependency minimization as a principle rather than a prohibition and the deleted test had ALREADY been narrowed to a one-entry allowlist. The doc simply never followed, so it states a falsehood about the shipped artifact. COORDINATION, STATED BECAUSE IT IS THE LARGEST RISK IN THIS PLAN: pending plan `1jg2m2` (Set `ikxtkj`; review measured it `- Status: reviewed` with `- Readiness: go-pending-approval`, not `to-review` as authored here) declares `CONTRIBUTING.md` in `- Scope-Paths:` and its E-06 edits the SAME sentence to state the gap this plan CLOSES. If `1jg2m2` lands after this plan, it would write a false gap claim over a restored guard. No `- Item-Dependencies:` edge is declared, with reason recorded in F-8 and OQ-02 and handled inside E-05 by a re-measure-and-branch instruction that is correct in either order.

## Goal

Make the wheel's ship-vs-dev boundary actually enforced again by a behavioral test that builds the wheel and inspects its contents, and make `CONTRIBUTING.md`'s packaging paragraph true in both of its currently-false claims, so a reader can open the guard that backs the boundary claim and is not told the wheel has zero runtime dependencies when it declares one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Re-measure before restoring or editing

- [x] E-01 RE-MEASURE, at execution HEAD, the three facts every later item depends on, rather than trusting this plan's authoring numbers. (1) That `tests/test_packaging.py` is still ABSENT and that no other test builds a wheel and asserts its contents (search `tests/` for `force-include`, `hatch.build`, and `build --wheel`, and confirm the `.whl` hits in `tests/test_local_leaks.py` and `tests/test_leak_sanitizer.py` are leak-scanner modes rather than packaging-boundary assertions). (2) That `CONTRIBUTING.md` still contains BOTH false claims, located by the quoted strings `ship-vs-dev boundary is enforced by` and `are ZERO runtime dependencies`. (3) That the wheel still BUILDS and its boundary still HOLDS, by running `python3 -m build --wheel` into a gitignored output directory and applying the forbidden-content sets to its namelist. IF THE BOUNDARY IS MEASURED BROKEN AT EXECUTION HEAD, STOP AND REPORT rather than proceeding: this plan is authorized to restore a guard over a holding property and to correct prose, NOT to fix a live packaging regression, whose remedy is a `bug`-kind item carrying a release gate. Record the HEAD sha and the per-fact result.
  - Depends on: none
  - Expected outcome: a recorded execution-HEAD measurement confirming or correcting each of the three facts, with the wheel's entry count and forbidden-violation count stated, and an explicit STOP if the boundary no longer holds.
  - Execution state: performed

### Task group 2: Restore the guard, which is what makes the prose fix honest

- [x] E-02 RESTORE a behavioral packaging guard at `tests/test_packaging.py` that BUILDS the wheel in a temporary directory and asserts the SHIP-VS-DEV BOUNDARY by inspecting the built artifact's namelist: no `tests/` entry, no source `.aw/records/` or `.aw/state/` entry, none of the meta docs (`DECISIONS.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, `GUIDING_PRINCIPLES.md`, `CITATION.cff`), and POSITIVELY that the importable package and the `agent_workflows/_data/.aw/system` data tree are present (an absence-only assertion passes on an empty wheel, which is the exact weakness the `6eq3oq` review measured in the original file). THIS IS A BEHAVIORAL TEST AND NOT A CODE-STRUCTURE PIN: it runs the real build and asserts over the real artifact's contents, reading no production source text, per `GUIDING_PRINCIPLES.md` P16 and the no-code-pinning rule. DERIVE the assertion from the deleted file at `git show 19313eed^:tests/test_packaging.py` rather than inventing one, but DO NOT restore it wholesale: restore only the boundary and dependency assertions this plan's scope names, and see E-03 for the forbidden-token anchoring rule (whose trap F-5 restates correctly after review measurement) and the out-of-scope halves. ENVIRONMENT HANDLING MUST DISTINGUISH TWO CASES, which the deleted file got right and which a naive restoration gets wrong: if `import build` FAILS, SKIP (a minimal environment is not a packaging defect); if `build` imports but the build FAILS, FAIL LOUDLY (that is a real defect, and the walkthrough record for `awphysical` notes this exact hardening was added after a build failure hid behind a caught `CalledProcessError`). ALSO measure and record whether the test needs an explicit `@pytest.mark.timeout`: authoring measured the build at 1.96s warm and 2.83s with a cleared pip cache, comfortably inside `conftest.py`'s 90s `_DEFAULT_TEST_TIMEOUT`, but the build fetches `hatchling` into an isolated environment and a cold or slow network can exceed that.
  - Depends on: E-01
  - Expected outcome: `tests/test_packaging.py` exists and contains a test that builds the wheel and asserts both the forbidden-content boundary and the positive presence of the package and the `_data` tree, skipping only when `build` is unimportable and failing loudly when an importable `build` cannot produce a wheel.
  - Execution state: performed

- [x] E-03 ADD to the same file the RUNTIME-DEPENDENCY ALLOWLIST assertion, as a SEPARATE test from E-02's boundary check because it reads the wheel's `METADATA` rather than its namelist and because it is the assertion that makes E-05's prose correction checkable. It must assert that the wheel's UNCONDITIONAL `Requires-Dist` set equals exactly `{"filelock"}`: not empty (a silent DROP breaks import, since `agent_workflows/platform_lock.py` depends on it and the CLI imports `filelock` at parser build) and nothing added (a new runtime dep must be a deliberate, justified act per `DECISIONS.md` D138). EXCLUDE entries carrying `; extra ==` from the check, since the `test` extra legitimately declares `pytest`, `pytest-xdist`, `pytest-randomly` and `PyYAML` and those are never installed unless asked for. ANCHOR THE FORBIDDEN-PATH MATCH, with the trap stated CORRECTLY as review re-measured it (F-5 as filed was false and has been corrected in place). The wheel legitimately ships `agent_workflows/_data/.aw/system/workflows/templates/workflow-artifacts-README.md`. That filename does NOT contain the forbidden token `workflow-artifacts/` (hyphen versus slash), so matching `FORBIDDEN_TOP` as a bare substring over the real namelist yields ZERO hits, exactly as `startswith` does (both re-measured on the built wheel at review). THE TRAP IS REAL BUT NARROWER: it fires only if a restorer LOOSENS the token by dropping its trailing slash, matching `workflow-artifacts` instead, which DOES hit that template. So prefer the deleted file's `startswith` framing, do NOT loosen any forbidden token to a slash-less form, and record THIS measurement in the comment rather than the overstated version, since a comment claiming substring matching is itself unsafe would mislead the next author about which change is dangerous.
  - Depends on: E-02
  - Expected outcome: a separate test asserting the wheel's unconditional runtime dependency set is exactly `{"filelock"}` while ignoring extras, a forbidden-path match whose tokens keep their trailing slash and are root-anchored, and a comment recording the corrected measurement (the slash-bearing token is safe under either matching style; a slash-less token is not).
  - Execution state: performed

- [x] E-04 DECIDE AND RECORD, by measurement rather than by preference, whether the restored file carries `pytestmark = pytest.mark.slow`. Re-measure the warm and cold build cost at execution HEAD, state the decision WITH those numbers, and put the reasoning in the file's docstring.
  - WHY IT IS ITS OWN ITEM: the marker decides whether the guard runs in the default suite at all, and therefore whether it can catch the next regression.
  - FOR UNMARKED: `pyproject.toml`'s `addopts` carries `-m 'not slow and not livecorpus'`, so a `slow`-marked test is DESELECTED from every routine run and from the lane-integration suite; the build costs only about 2s warm (1.96s at authoring, 2.09s and 2.57s re-measured at review) against a 90s per-test budget; and the deleted file carried NO marker, so unmarked RESTORES the original posture rather than changing it.
  - AGAINST: the build spawns a subprocess and fetches `hatchling` into an isolated environment, which is the marker's stated category, and it needs the NETWORK, so in the default suite an outage can turn a lane red for a non-defect.
  - WEIGH IN THE COST F-15 MEASURED, which the authored item understated: CI's slow step carries `continue-on-error: true`, so a `slow`-marked guard is non-blocking THERE TOO, leaving it in no blocking gate anywhere.
  - IF MARKED, say plainly in E-05's prose that the guard exists but is deselected by default and is advisory in CI, since a reader told the boundary is enforced deserves to know the gate does not block anything. Do not describe it as running in "CI's slow step" without saying that step is advisory.
  - Depends on: E-02, E-03
  - Expected outcome: a recorded, measured decision on the `slow` marker with the build cost stated, the reasoning in the file's docstring, and (if marked) an explicit statement in the CONTRIBUTING prose that the gate is deselected by default.
  - Execution state: performed

### Task group 3: Make the prose true, and coordinate with the plan that owns the same sentence

- [x] E-05 CORRECT ALL THREE FALSE CLAIMS in `CONTRIBUTING.md`'s "Packaging and the CLI (DECISIONS D46)" section, which is one edit site and one reviewable concern. Review measured a THIRD claim the authored item missed (F-11), and leaving it would make the paragraph contradict the very test this plan restores.
  - CLAIM 1, THE TEST CITATION (keep it): the sentence containing `ship-vs-dev boundary is enforced by` may keep citing `tests/test_packaging.py` PRECISELY BECAUSE E-02 restored it, which is this plan's substantive disagreement with pending plan `1jg2m2` E-06: that item prescribes weakening the claim to "currently unguarded" having explicitly declined to build a wheel, and weakening a claim this plan makes TRUE would be a regression in accuracy. Re-verify the path resolves after E-02 before leaving the citation in place.
  - CLAIM 2, THE PARENTHETICAL (correct it): the clause containing `are ZERO runtime dependencies` is FALSE and must be corrected to state the one allowlisted runtime dependency (`filelock`), citing `DECISIONS.md` D138 for why a dependency is permitted at all (minimization is a principle, not a prohibition) and noting that E-03's test PINS the set so a new one cannot be added silently.
  - CLAIM 3, THE SAME SENTENCE'S TRAILING ASSERTION (correct it; ADDED AT REVIEW, F-11): the "Build a wheel" bullet's sentence ENDS with `and that no runtime dependency is declared.` That is a SEPARATE false clause from claim 2, in a different sentence, and it describes what the restored test asserts. Since E-03 pins the set to exactly `{"filelock"}` rather than to empty, this clause must be rewritten to say the test pins the runtime dependency set to the one allowlisted entry. LEAVING IT WOULD BE WORSE THAN THE ORIGINAL DEFECT: the paragraph would cite a test that exists (true after E-02) while misdescribing what that test asserts, which is a false claim about this plan's own deliverable.
  - PRESERVE: do NOT rewrite the surrounding description of the boundary, the `_data` mapping, the three console scripts, or the PyPI-publishing note. Each was verified correct by authoring's build and RE-VERIFIED at review (356 entries, 161 under `_data/.aw/system`, three console scripts present).
  - NO EM OR EN DASHES: `CONTRIBUTING.md` is user-facing prose under the repository's authoring convention.
  - COORDINATE WITH `1jg2m2` AT EXECUTION, do not assume this plan runs first: re-read `CONTRIBUTING.md` before editing, and if `1jg2m2` has already applied its gap-claim edit, REPLACE that claim rather than layering onto it, reporting the interaction at finalize. Note `1jg2m2` is `- Status: reviewed` with `- Readiness: go-pending-approval` (F-12), so it is one human approval from executable and may well land first.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: the packaging paragraph cites a test file that exists, states the one allowlisted runtime dependency instead of asserting zero in BOTH places it currently asserts zero, describes what the restored test actually pins, cites D138, carries no em or en dashes, leaves the verified-correct surrounding prose intact, and records any interaction with `1jg2m2`'s edit to the same sentence.
  - Execution state: performed

### Task group 4: Prove nothing else broke and nothing stray ships

- [x] E-06 RUN the whole-plan non-regression and cleanliness pass. Measure a BASELINE first, before the restored test is collected, then run the suite BARE and compare by FAILING NODE ID.
  - WHY IT IS A DISTINCT ACTION: this plan ADDS a test that spawns a subprocess build into the suite, which is a change to the suite's own behavior rather than a restatement of the items above.
  - WHY A NODE-ID DELTA AND NOT A TOTAL: this plan deliberately adds tests, so a total comparison is meaningless. It is also necessary rather than merely tidy, because the baseline is NOT green: review measured `1 failed, 3431 passed, 2 skipped` on an unmodified tree, the failure being `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, a filed local-versus-UTC clock defect owned by backlog `fnb8pl` (F-16). Expect it in BOTH runs, do not investigate it, and do not attempt to fix it.
  - CLEAN UP THE BUILD OUTPUT: remove any artifact the earlier items produced and verify it is absent from the working tree AND the staged set. `python3 -m build` writes into a gitignored `dist/` by default, and an executor who redirects `--outdir` elsewhere can leave an untracked directory behind that does not belong to this plan.
  - RUN THE LEAK GATE, since the restored test necessarily handles build and temporary paths.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: a self-measured baseline and post-change suite run compared by failing-node-id with no NEW failing id (the pre-existing `fnb8pl` failure present in both and named as such), a clean leak-gate result, and a working tree and staged set containing no build artifact.
  - Execution state: performed

## Project conventions discovered (Step 0)

- P16 PERMITS THIS TEST BY NAME AND ALSO CONSTRAINS ITS SHAPE. `GUIDING_PRINCIPLES.md`'s "The one narrow exception" bullet allows content verification "only where the text or file itself is the artifact under test", and a built wheel IS the artifact under test, so inspecting its namelist and `METADATA` is behavioral. The same principle forbids reading production source text, which is why every assertion in E-02 and E-03 runs the real build and inspects the real output rather than parsing `pyproject.toml`.
- THE `slow` MARKER IS THE DIFFERENCE BETWEEN A GUARD AND A DECORATION, which is why E-04 is its own item. `pyproject.toml` `addopts` is `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`, and `Makefile`'s `test` target inherits it while `test-all` clears it with `-m ''`. A marked test therefore does not run in the routine suite a lane's integration gate uses.
- THE DELETING COMMIT WAS A DELIBERATE TRIM, AND THIS PLAN IS A NARROW PARTIAL REVERSAL, NOT A REJECTION OF IT. `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24) deleted a 500-plus-line file containing both wheel and sdist classes plus browser-asset and installed-CLI-migration tests. This plan restores only the boundary and dependency assertions, deliberately leaving the rest out (see Deferred), so the trim's intent is respected while the claim `CONTRIBUTING.md` makes is backed again.
- CITE BY SYMBOL OR CONTENT, NOT BY A BARE LINE NUMBER (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`), because offsets expire before a plan executes. Every edit site here is located by a quoted string.
- THIS IS A KNOWN DEFECT CLASS WITH AT LEAST FOUR SIBLINGS, so an executor should expect neighbors rather than treat this as isolated. Backlog `gzmr54` (six deleted `test_docs.py` classes), `rdl9lh` (`worktree_lease` citing a deleted stdlib guard), `p5qx91` (spec `uonrjg`'s color-axis pins) and `089bq4` (a spec citing a deleted finding-table guard) all record the same shape, and `rdl9lh` names this item as one of the class. This plan fixes ONE instance and does not attempt the sweep.
- `followup` VERSUS `bug` TURNS ON USER-PERCEPTIBLE IMPACT (`AGENTS.md`), and authoring's build measurement is what settles it here: the boundary HOLDS, so no user can perceive anything today, and the inherited `followup` is correct. Had the build shown a violation, the honest filing would have been `bug` WITH a release gate, which is exactly why E-01 stops rather than proceeding if it measures one.

## Findings

| # | Severity | Finding | Evidence |
|---|---|---|---|
| F-1 | MEDIUM | THE ITEM'S CLAIM VERIFIES EXACTLY AS FILED. The cited test is gone, the citation survives, and no replacement guard exists. | `ls tests/test_packaging.py` -> "No such file or directory". `git log --diff-filter=D --name-only -- tests/test_packaging.py` -> `19313eed test: trim test suite from 9,136 to under 2,000 tests`. `grep -n` on `CONTRIBUTING.md` shows the sentence containing `ship-vs-dev boundary is enforced by tests/test_packaging.py`. No test file matches `force-include` or `hatch.build`; the `.whl` hits in `tests/test_local_leaks.py` and `tests/test_leak_sanitizer.py` are leak-scanner modes. |
| F-2 | HIGH | THE BOUNDARY ITSELF HOLDS TODAY, WHICH CHANGES THE CORRECT FIX from weakening the prose to restoring the guard. Authoring built the wheel and applied the deleted test's own forbidden-content sets to it. | `python3 -m build --wheel` succeeded (`agent_workflows-1.3.0rc2.dev6059+g63c8646c-py3-none-any.whl`, 356 entries). Applying `FORBIDDEN_TOP`, `FORBIDDEN_AGENTS_SUBSTRINGS` and `FORBIDDEN_FILES` from `git show 19313eed^:tests/test_packaging.py` yields `FORBIDDEN VIOLATIONS: 0`. Per-class counts: `tests/` 0, `.aw/records/` 0, `.aw/state/` 0, and 0 for each of the five meta docs. The package is present and 161 entries sit under `agent_workflows/_data/.aw/system`. |
| F-3 | HIGH | A SECOND FALSE CLAIM SITS IN THE SAME PARAGRAPH AND NEITHER THE ITEM NOR `1jg2m2` NAMES IT. `CONTRIBUTING.md` asserts the wheel has ZERO runtime dependencies; the built wheel declares one. | The paragraph contains `are ZERO runtime dependencies`. The built wheel's `METADATA` contains `Requires-Dist: filelock>=3` unconditionally, plus four `; extra == 'test'` entries. `pyproject.toml` declares `dependencies = ["filelock>=3"]` with a comment explaining why it is real rather than transitive. |
| F-4 | MEDIUM | THE ZERO-DEPENDENCY CLAIM IS STALE PROSE, NOT A REGRESSION, and the repository already decided the question, so the correction is a doc catching up rather than a policy change. | `DECISIONS.md` D138 ("Dependency minimization is a principle, not a prohibition") records that D46 stated a FACT about the build of the day and that the "rule" reading was a later back-reference never decided. The deleted test had ALREADY been narrowed from blanket-zero to a one-entry allowlist, its comment naming IPD `y6mfgo` and explaining that `filelock` replaced six top-level `import fcntl` sites that broke Windows import. |
| F-5 | MEDIUM | A NAIVE RESTORATION OF THE DELETED ASSERTION WOULD FAIL ON A LEGITIMATELY SHIPPED FILE, so E-03 must anchor the match. Measured while running the old sets against the new wheel. | The deleted `FORBIDDEN_TOP` contains the substring `workflow-artifacts/`, and the wheel legitimately ships `agent_workflows/_data/.aw/system/workflows/templates/workflow-artifacts-README.md`. A bare substring search reports 1 hit; the original's `startswith` framing is what kept it green, so the anchoring is load-bearing rather than stylistic. CORRECTED AT REVIEW, AND THE CORRECTION MATTERS BECAUSE THE PLAN BUILT AN E-ITEM ON IT: the claim as written is FALSE. The shipped file is `workflow-artifacts-README.md` with a HYPHEN, and the forbidden token is `workflow-artifacts/` with a SLASH, so `"workflow-artifacts/" in "...workflow-artifacts-README.md"` evaluates `False`. Re-measured directly on the built wheel: matching all of `FORBIDDEN_TOP` as a BARE SUBSTRING over the 356-entry namelist yields ZERO hits, exactly as the `startswith` framing does. One entry contains the looser token `workflow-artifacts` (no slash), which is presumably what authoring measured; a test written against THAT token would indeed trip. So the real finding is narrower and is still worth acting on: the trap is reachable only if a restorer DROPS the trailing slash or matches a loosened token, not by choosing substring over `startswith`. See F-11 for the consequence to E-03. |
| F-6 | MEDIUM | THE DELETED FILE CARRIED NO `slow` MARKER, so restoring it unmarked preserves the original posture, and the build is fast enough that the fast suite can hold it. | `git show 19313eed^:tests/test_packaging.py` contains zero occurrences of `slow` and no `pytestmark`. Measured build cost: 1.96s warm, 2.83s with `PIP_CACHE_DIR` pointed at a freshly removed directory. `conftest.py`'s `_DEFAULT_TEST_TIMEOUT` is 90.0s, and its comment records the slowest fast-suite test at ~13s. |
| F-7 | MEDIUM | THE BUILD NEEDS THE NETWORK IN A CLEAN ENVIRONMENT, which is the strongest argument for the `slow` marker and the reason E-04 weighs rather than assumes. | `import hatchling` fails in the test interpreter, so `python3 -m build --wheel --no-isolation` fails with `Backend 'hatchling.build' is not available`. With `PIP_NO_INDEX=1` the isolated build fails at the `pip install -r build-requirements` step with `CalledProcessError`. CI installs `build` explicitly, its comment stating that `build` "belongs to the packaging gate, not to the test environment". |
| F-8 | HIGH | A PENDING PLAN OWNS THE SAME SENTENCE AND WOULD WRITE THE OPPOSITE CLAIM, and whichever lands second overwrites the other, so this must be handled in the item rather than assumed away. | Pending plan `1jg2m2` (Set `ikxtkj`) declares `CONTRIBUTING.md` in `- Scope-Paths:`; its E-06 targets the same `ship-vs-dev boundary is enforced by` string and prescribes stating "the assertion is currently unguarded". Its own Deferred section records "WHETHER THE WHEEL'S SHIP-VS-DEV BOUNDARY ACTUALLY HOLDS: not measured and not claimed", and invites exactly this measurement ("If E-07's item is taken up, measuring the wheel is the first thing its executor should do"). No `- Item-Dependencies:` edge is declared here: the grammar offers `executed:`/`exists:`/`state:` edges only, and gating this item behind another plan's execution would be worse than the re-measure-and-branch E-05 requires. STATUS CORRECTED AT REVIEW: this row originally read `- Status: to-review`; it is `reviewed` with `- Readiness: go-pending-approval` (F-12), which is AHEAD of this plan, so the no-edge conclusion stands on the grammar argument alone rather than on the other plan being unreviewed. See F-13 for the measured ordering result, which is favourable in BOTH directions. |
| F-9 | LOW | ONE MORE PENDING PLAN DECLARES `CONTRIBUTING.md`, but it does not contend for this passage, so only `1jg2m2` is a real collision. | `76ic0k` (Set `structpin`, `- Status: reviewed`) declares `tests/test_no_code_structure_pins.py, CONTRIBUTING.md`; its concern is refusing new code-structure pins in tests, not the packaging section. NOTE FOR THE EXECUTOR: that plan adds an author-time guard against code-structure pins, and E-02's behavioral shape is what keeps the restored file clear of it. |
| F-10 | LOW | `pyproject.toml` NEEDS NO CHANGE, which is why it is deliberately absent from `- Scope-Paths:`. | The wheel target declares `packages = ["agent_workflows"]` plus one `force-include` mapping `.aw/system` to `agent_workflows/_data/.aw/system`; the built wheel shows that mapping working (161 entries) and three console scripts registered. `/dist/` and `/build/` are already gitignored, so authoring's probe builds needed no ignore change and left `git status` clean. RE-VERIFIED AT REVIEW: 356 entries, 161 under `agent_workflows/_data/.aw/system`, and `git status --short` clean after two builds directed outside the tree. |
| F-11 | HIGH | ADDED AT REVIEW: A THIRD FALSE CLAIM SITS IN THE SAME BULLET AND THE PLAN DOES NOT NAME IT, so E-05 as authored would have left the paragraph still false after claiming to have corrected it. The sentence E-05 keeps (because E-02 makes its citation true again) ENDS with a second assertion: `tests/test_packaging.py` "asserts the wheel contains only the package + `_data` tree and NONE of `tests/` ... or the meta docs, AND THAT NO RUNTIME DEPENDENCY IS DECLARED." That trailing clause is false on exactly the same evidence as F-3, and it is a DIFFERENT clause in a DIFFERENT sentence from the `are ZERO runtime dependencies` parenthetical F-3 names. Worse, E-02/E-03 would make the first half of the sentence true while leaving the second half asserting something the restored test must NOT assert, since E-03 pins the set to `{"filelock"}` rather than to empty. | Measured at review HEAD `170368788`. `CONTRIBUTING.md`'s "Build a wheel" bullet contains the literal string `and that no runtime` followed by `dependency is declared.`, a distinct site from the line-245 parenthetical `are ZERO runtime dependencies`. The built wheel's `METADATA` declares `Requires-Dist: filelock>=3` unconditionally. Both clauses must be corrected or the paragraph remains self-contradictory about the very test this plan restores. |
| F-12 | HIGH | ADDED AT REVIEW: F-8 MISSTATES THE CONTENDING PLAN'S STATUS, AND THE REAL STATUS INVERTS OQ-02's REASONING. F-8 and OQ-02 both assert `1jg2m2` is `- Status: to-review` and build their no-edge argument on that ("gating this item behind an unrelated chore's full review-and-execute cycle"). Measured: `1jg2m2` is `- Status: reviewed` with `- Readiness: go-pending-approval`, so it has ALREADY been reviewed and is one human approval from executable, which is strictly AHEAD of this plan in the lifecycle. The conclusion (no edge) survives but its stated basis does not, and a reader checking the reasoning would find it false. | `.aw/records/plans/pending/20260930-ikxtkj-01-1jg2m2-...ipd.md` front matter: `- Status: reviewed`, `- Readiness: go-pending-approval`, plus a 2026-09-30 `/plan-review` history line recording PR-101 through PR-106 all fixed. |
| F-13 | HIGH | ADDED AT REVIEW: `1jg2m2` ALSO ADDS A CITATION GUARD THAT SCANS `CONTRIBUTING.md`, which both strengthens this plan's case and adds an interaction neither plan's text covers. Its E-08 creates `tests/test_docs_test_citations.py` scanning every file under `docs/` PLUS an enumerated literal list that includes `CONTRIBUTING.md`, and FAILS on any `tests/test_*.py` citation that does not exist on disk. CONSEQUENCE IN THIS PLAN'S FAVOUR: if `1jg2m2` lands first and applies its shape-(b) edit, the citation is gone and the guard is green; if THIS plan lands first, the citation EXISTS again (E-02 restores the file) and the guard is ALSO green. Either order is safe, which is a stronger coordination result than OQ-02 claims. CONSEQUENCE AGAINST: if `1jg2m2`'s E-08 lands and THEN someone deletes `tests/test_packaging.py` again, the guard catches it, so this plan's restoration gains a durable keeper it does not know about. | `1jg2m2` E-08 text: "SCOPE IT TO AN EXPLICIT, ENUMERATED FILE LIST ... every file under `docs/`, plus exactly `CONTRIBUTING.md`, `README.md`, `RELEASING.md`, `AGENTS.md` and `GUIDING_PRINCIPLES.md`", and its F-11 records the scan as yielding 6 danglers including `CONTRIBUTING.md`'s. |
| F-14 | MEDIUM | ADDED AT REVIEW: THE `- Scope:` FIELD CONTRADICTS `- Item-Dependencies:` AND OQ-02. `- Scope:` states this plan "coordinates by `- Item-Dependencies:`" with `1jg2m2`, while `- Item-Dependencies:` reads `none` and OQ-02 resolves AT LENGTH that no edge should be declared. An executor reading the scope line would look for an edge that deliberately does not exist, and a reviewer could read it as a forgotten field. | `- Scope:` line versus `- Item-Dependencies: none` (line 8) and OQ-02's resolution "DECLARE NO EDGE AND HANDLE IT INSIDE E-05". |
| F-15 | MEDIUM | ADDED AT REVIEW: CI's SLOW STEP IS ADVISORY, WHICH SHARPENS OQ-01 RATHER THAN LEAVING IT A BALANCED TRADEOFF. OQ-01 weighs "marked" partly on the ground that the guard would still run in "CI's advisory slow step". Measured: that step carries `continue-on-error: true`, so a failure there does NOT fail the build, and its comment records that it is advisory "until the known slow failures are fixed" with no date. So a `slow`-marked guard would run in NO blocking gate at all: deselected from every routine run, deselected from the lane-integration suite, and non-blocking in CI. That does not decide the maintainer's risk-appetite question, but it means the "marked" option costs more than OQ-01 states. | `.github/workflows/tests.yml`: the `Run slow-marked tests (ADVISORY until the known slow failures are fixed)` step carries `continue-on-error: true` and `python -m pytest tests/ -n auto -m slow`. The blocking step above it is `python -m pytest tests/ -n auto -rfEs`, which inherits `addopts`' `-m 'not slow and not livecorpus'`. |
| F-16 | MEDIUM | ADDED AT REVIEW: THE SUITE IS NOT GREEN, so E-06's and V-06's delta framing is NECESSARY rather than merely tidy, and the plan should name the expected failure so an executor does not investigate it. Bare `python3 -m pytest` on an unmodified tree reports `1 failed, 3431 passed, 2 skipped`. The failure is `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, a filed time-dependent local-versus-UTC history-clock defect owned by backlog `fnb8pl` (`open`, `bug`, `Blocks-Release: next`), unrelated to packaging. | Measured at review HEAD `170368788`; `.aw/records/backlog/open/20260930-fnb8pl-01-fnb8pl-unify-the-history-date-clock-across-both-backlog-s.backlog.md`. |
| F-17 | LOW | ADDED AT REVIEW: THE DELETED FILE ALREADY CONTAINS E-03's ASSERTION ALMOST VERBATIM, including the extras exclusion, the two-sided equality, and the D138 reasoning in comments, so E-03 is a RECOVERY rather than a design task and should say so. Its `test_wheel_declares_only_the_allowlisted_runtime_dependency` defines `ALLOWED_RUNTIME_DEPS = {"filelock"}`, filters `Requires-Dist` lines by `"extra ==" not in ln`, normalizes the dist name, and asserts BOTH `declared - ALLOWED == []` (catching a silent ADD) and `declared == ALLOWED` (catching a silent DROP). | `git show 19313eed^:tests/test_packaging.py`, the named test plus its 20-line comment citing D138 and IPD `y6mfgo`. Its two-case environment handling in `setUpClass` (SkipTest on `ImportError`, `AssertionError` on `CalledProcessError`) is likewise exactly what E-02 specifies. |

## Proposed changes (ordered, validatable)

1. Re-measure at execution HEAD that the test is still absent, both prose claims still stand, and the wheel still builds with a holding boundary; STOP if the boundary is broken (E-01).
2. Restore `tests/test_packaging.py` with a behavioral wheel-boundary test asserting both forbidden absence and positive presence, skipping only on unimportable `build` and failing loudly on a failed build (E-02).
3. Add the separate runtime-dependency allowlist test pinning the unconditional set to exactly `{"filelock"}`, with the forbidden-path match anchored so the shipped `workflow-artifacts-README.md` template does not trip it (E-03).
4. Decide the `slow` marker from re-measured build cost, record the reasoning in the docstring, and surface a deselected-by-default gate in the prose if marked (E-04).
5. Correct all THREE false claims in `CONTRIBUTING.md`'s packaging paragraph, keeping the now-true test citation, replacing the zero-dependency parenthetical with the allowlisted one, and correcting the same bullet's trailing claim that the test asserts no runtime dependency is declared, coordinating with `1jg2m2` (E-05).

## Deferred / out of scope (with reason)

- THE SDIST HALF OF THE DELETED SUITE (`SdistBrowserAssetTests`): out of scope. `CONTRIBUTING.md`'s claim, which is this item's whole subject, is about the WHEEL; the sdist `include` allowlist is a different mechanism and asserting it is a separate deliverable that would double this plan's build cost for a property no cited prose depends on.
  - Carrier-Declined: No carrier, and this is a scope boundary rather than a debt: no record in the tree claims the sdist boundary is enforced, so nothing is currently false about it. If a future doc makes that claim, it needs a guard then.
- THE BROWSER-ASSET AND INSTALLED-CLI-MIGRATION TESTS from the deleted file (`test_wheel_ships_every_browser_asset_BY_NAME`, `test_a_gitignored_asset_would_be_DETECTED_rather_than_silently_dropped`, `test_installed_wheel_migrate_layout_without_tools`): out of scope. These belong to the `runanalytics` feature surface (plans `6eq3oq` and `9xycbh`) rather than to the ship-vs-dev boundary, and restoring them would be a far larger reversal of a deliberate trim than this item's citation warrants. Authoring did verify the assets still ship (`app.css` and `app.js` both present in the built wheel), so nothing is known-broken behind this deferral.
  - Carrier-Declined: DELIBERATELY NOT CARRIED, with the reason stated: no record in the tree currently claims those assertions exist, so unlike this item there is no false enforcement claim to correct. Filing a carrier would assert an obligation the repository has not decided it wants.
- THE FOUR `docs/` DANGLERS IN THE SAME DEFECT CLASS (`test_release_readiness.py`, `test_security_hardening.py`, `test_wtiso_taxonomy_freeze.py`, `test_wtiso_characterization.py`): out of scope because pending plan `1jg2m2` OWNS them, and duplicating its edits would create the exact two-plans-one-file collision F-8 already has to manage once.
  - Carrier-Declined: Already carried by `1jg2m2`, which is authored and awaiting review.
- THE DOCS-CITATION EXISTENCE TEST (`tests/test_docs_test_citations.py`): out of scope because `1jg2m2` E-08 owns it. NOTE THE INTERACTION, which is favorable: once this plan restores `tests/test_packaging.py`, that test passes on the `CONTRIBUTING.md` citation instead of needing an exemption for it.
  - Carrier-Declined: Already carried by `1jg2m2` E-08.
- THE BROADER SWEEP OF DOCSTRINGS AND SPECS CITING TESTS `19313eed` DELETED: out of scope. Backlog `rdl9lh` already proposes the sweep and names this item as one of its four known instances, so the sweep has an owner and this plan fixing one instance does not foreclose it.
  - Carrier-Declined: Already carried by backlog `rdl9lh`, which records the class explicitly.
- ANY CHANGE TO `pyproject.toml`: out of scope and unnecessary. Authoring measured the packaging configuration to be correct (F-10), so the defect is entirely in the missing guard and the stale prose.
  - Carrier-Declined: No defect established, so nothing to carry.

## Scope check

- Over-scope: none. `tests/test_packaging.py` is the restored guard (E-02, E-03, E-04) and `CONTRIBUTING.md` holds the two prose corrections (E-05). E-01 is read-only measurement apart from a wheel build, whose output goes to a gitignored directory (`/dist/` and `/build/` are already in `.gitignore`) and must be removed before commit so it cannot enter the staged set.
- Under-scope: the declared paths cover every edit. NO spec file is touched and no spec amendment is required: restoring a test and correcting prose changes no contract a spec defines, so the runners' declared-spec-edit announcement should report none. `pyproject.toml` is deliberately NOT declared (F-10), and `DECISIONS.md` is CITED but not edited, since D138 already says what E-05's correction needs.

## Required tests / validation

- The restored `tests/test_packaging.py` run explicitly, output pasted, PASSING, with the wheel's entry count and the measured runtime shown.
- MUTATION EVIDENCE PROVING THE GUARD CAN FAIL, which is the whole point of restoring it: temporarily perturb the inputs so each assertion goes RED (for example, assert against a deliberately wrong forbidden set or a wrong expected dependency set), paste the FAILING output, then revert and paste the pass. A pass-only run does not demonstrate falsifiability (`GUIDING_PRINCIPLES.md` P16, "Verify test sensitivity with mutation").
- Proof of whether the restored test is SELECTED or DESELECTED by the default run, matching E-04's recorded decision (a bare `python3 -m pytest tests/test_packaging.py` showing it collected and run, or showing `deselected` if marked `slow`).
- An existence check on every `tests/test_*.py` path remaining in `CONTRIBUTING.md` after E-05, so the surviving citation is verified against the filesystem rather than by eye.
- The built wheel's unconditional `Requires-Dist` set pasted, supporting E-05's corrected prose rather than quoting this plan's authoring measurement.
- The full suite run BARE as `python3 -m pytest` (configured `addopts` already supply `-q -n auto --dist=worksteal`; do not add `-n0`, a second `-q`, or `-p no:randomly`), with the summary line pasted, plus the failing-node-id delta against a baseline the executor measures itself. READ IT AS A DELTA, NOT A GREEN BAR: the baseline carries one pre-existing unrelated failure (`fnb8pl`, F-16).
- `aw sanitize --agent` clean over the worktree, since the restored test handles build paths and temporary directories and a full local path literal would fail the leak gate (`tests/test_packaging.py` IS in `leak_sanitizer._ALLOWED_PATHS`, but relying on that rather than writing clean paths is how the `rpqv4q` review planted a leak in its own fix).
- `git status --short` clean of build artifacts before commit, proving no `dist/` output entered the staged set.
- `aw ipd lint --phase pre-transition` conforming before any terminal transition.

## Spec / documentation sync

`CONTRIBUTING.md` IS the documentation sync: its packaging paragraph is corrected so both of its currently-false claims match the built artifact. NO spec is amended and no `.spec.md` path is declared in `- Scope-Paths:`, with reason: restoring a test and correcting prose changes no contract any spec defines. `DECISIONS.md` D138 is cited as the authority for the permitted runtime dependency and is deliberately NOT edited, since it already records the decision this prose failed to follow. The corrected text is user-facing prose and must carry no em or en dashes.

## Open questions

### OQ-01: Should the restored guard carry `pytestmark = pytest.mark.slow`?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: The WORK is carried: E-04 makes the decision at execution with re-measured numbers and V-04 refuses to pass without them, so nothing vanishes if this question stays open. What is undecided is only which way a genuine tradeoff falls, and that is a risk-appetite call about the default suite, which is the maintainer's.
- Resolution or deferral rationale: DEFERRED TO THE MAINTAINER WITH BOTH SIDES MEASURED. For UNMARKED: the deleted file carried no marker (zero `slow` occurrences, verified), the build costs only 1.96s warm and 2.83s cold-cache against a 90s per-test budget, and `addopts` carries `-m 'not slow and not livecorpus'` so a marked test is deselected from the routine suite AND from the lane-integration gate, meaning a marked guard would not catch the next regression where it matters most. For MARKED: the test spawns a subprocess and fetches `hatchling` into an isolated environment, which is precisely the marker's stated category, and it NEEDS THE NETWORK (measured: `PIP_NO_INDEX=1` fails the isolated build, and `--no-isolation` fails because `hatchling` is absent from the test interpreter), so in the default suite a network outage turns every concurrent lane red for a non-defect. AUTHORING'S LEAN IS UNMARKED, because a deselected guard over a claim the docs make is close to no guard at all, and the network risk argues for a clear SKIP on an unavailable build (which E-02 already requires) rather than for hiding the test from the suite. Not blocking either way: E-04 records the decision with numbers, and flipping a one-line marker later is trivial.
  REVIEW RE-MEASURED BOTH SIDES AND THE TRADEOFF IS LESS BALANCED THAN THIS QUESTION PRESENTS, which the maintainer should see before deciding; the decision itself is left to them because it is a risk-appetite call about the default suite. (1) THE TIMING HOLDS: warm build 2.09s and 2.57s on two runs at review HEAD, against `conftest.py`'s 90s `_DEFAULT_TEST_TIMEOUT`, so cost is not an argument for the marker. (2) THE NETWORK DEPENDENCY HOLDS: `PIP_NO_INDEX=1` fails the isolated build with `CalledProcessError`, and `import hatchling` fails in the test interpreter, so `--no-isolation` is not available either. (3) THE CORRECTION THAT MATTERS, F-15: this question's "marked" case says the guard would still run in "CI's advisory slow step", which understates the cost. That step carries `continue-on-error: true`, so a failure there does not fail the build. A `slow`-marked guard therefore runs in NO BLOCKING GATE ANYWHERE: not the routine suite, not the lane-integration suite, and not blockingly in CI. The honest statement of the "marked" option is that the guard becomes advisory everywhere, which is a materially weaker thing than this question described, and it strengthens authoring's unmarked lean rather than deciding it.

### OQ-02: Should this plan declare an `- Item-Dependencies:` edge against pending plan `1jg2m2`, which edits the same sentence to the opposite effect?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, DECLARE NO EDGE AND HANDLE IT INSIDE E-05, AND REVIEW UPHELD THIS WHILE CORRECTING ITS BASIS. The collision is real (F-8): `1jg2m2` E-06 rewrites the same `ship-vs-dev boundary is enforced by` sentence to say the boundary is unguarded, which this plan makes false by restoring the guard. But an `executed:` edge is the wrong instrument, for the reason this repository has recorded before in `hyuos6`: the grammar offers `executed:`/`exists:`/`state:` edges only with no way to express "prefer after", so an edge would gate this item behind another plan's entire execution. AN EDGE IN THE OTHER DIRECTION IS EQUALLY WRONG, since this plan cannot add a dependency to a plan it does not own. So E-05 requires a re-read of `CONTRIBUTING.md` immediately before editing and branches on what it finds, which is correct in either order: if `1jg2m2` landed first, E-05 replaces its gap claim with the accurate one; if this plan lands first, `1jg2m2`'s own E-01 re-measurement instruction ("If any of the four this plan fixes has been repaired upstream, DO NOT edit it") makes its executor skip the sentence.
  TWO CORRECTIONS FROM REVIEW, BOTH LEAVING THE ANSWER UNCHANGED. FIRST, THE STATUS ARGUMENT WAS FALSE AND IS REMOVED: this rationale originally rested partly on `1jg2m2` being "`- Status: to-review` rather than approved" and on the risk of "stranding it permanently if that plan is never approved". Measured at review, `1jg2m2` is `- Status: reviewed` with `- Readiness: go-pending-approval` (F-12), which is AHEAD of this plan, so that half of the argument was simply wrong. The no-edge conclusion survives on the grammar argument alone, which is the load-bearing half. SECOND, THE ORDERING IS SAFER THAN THIS QUESTION CLAIMED, measured rather than argued (F-13): `1jg2m2` E-08 adds `tests/test_docs_test_citations.py`, which scans `CONTRIBUTING.md` for `tests/test_*.py` citations and fails on any that does not exist. If `1jg2m2` lands first its edit removes the citation and the guard is green; if THIS plan lands first the citation exists again because E-02 restored the file, and the guard is ALSO green. So neither order produces a red guard, and the restoration additionally gains a durable keeper that will catch a future re-deletion.
  A REVIEWER WHO DISAGREES should say so, since the alternative (holding this plan until `1jg2m2` resolves) is defensible and costs only latency.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted execution-HEAD measurement with the HEAD sha recorded, showing (a) `ls tests/test_packaging.py` absent and the searches for `force-include`, `hatch.build` and `build --wheel` over `tests/` with their results, (b) both quoted `CONTRIBUTING.md` strings still present, and (c) the wheel build output plus the forbidden-violation count and total entry count. Must state explicitly whether the boundary HOLDS. If it does not hold, this item's evidence must show the plan STOPPED and reported rather than proceeding, and no later E-item may be marked performed.
  - Observed evidence: PASS. Execution HEAD 7168b42b89dd964950bc73443f8c520d9d48e0be confirmed test absent, false claims present, and boundary holds with 0 violations across 358 entries.
    Execution HEAD sha: `7168b42b89dd964950bc73443f8c520d9d48e0be`
    (a) `ls tests/test_packaging.py`:
    ```
    ls: cannot access 'tests/test_packaging.py': No such file or directory
    ```
    Searches across `tests/`:
    `grep -rn "force-include" tests/` -> `NO MATCH: force-include`
    `grep -rn "hatch\.build" tests/` -> `NO MATCH: hatch.build`
    `grep -rn "build --wheel" tests/` -> `NO MATCH: build --wheel`
    `.whl` matches in `tests/test_local_leaks.py` (line 375) and `tests/test_leak_sanitizer.py` (line 682) confirmed to be synthetic throwaway wheel test fixtures for leak scanner testing, not packaging boundary assertions.
    (b) `CONTRIBUTING.md` strings:
    Line 245: `are ZERO runtime dependencies` present.
    Line 253: `The ship-vs-dev boundary intends that the wheel contains only the package + '_data' tree and NONE of 'tests/', '.aw/workflow-artifacts/', the source '.aw/records/' tree (docs, plans, prompts), or the meta docs, and that no runtime dependency is declared.` (Note: commit `c50b3fa5d` from `1jg2m2` had already replaced `ship-vs-dev boundary is enforced by` with `ship-vs-dev boundary intends that...` and added the gap claim regarding deleted test `19313eed`, while both false zero-runtime-dependency claims remained).
    (c) Wheel build and boundary verification:
    ```
    Wheel built: agent_workflows-1.3.0rc2.dev7138+g7168b42b8-py3-none-any.whl
    Total entries: 358
    Forbidden violations count: 0
    agent_workflows entries: 352
    _data/.aw/system entries: 161
    ```
    The ship-vs-dev boundary HOLDS at execution HEAD.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted run of the restored boundary test showing it PASS, plus MUTATION EVIDENCE: a pasted FAILING run produced by perturbing the assertion (for example adding a path the wheel legitimately ships to the forbidden set), proving the test can go red, followed by the reverted passing run. Plus the test quoted, showing it asserts BOTH forbidden absence AND positive presence of the package and the `_data` tree (an absence-only test is a FAIL of this item, since it passes on an empty wheel). Plus pasted proof of the two-case environment handling: the `import build` failure path SKIPS and an importable-`build`-but-failed-build path FAILS (demonstrate the second by a temporary perturbation or by quoting the code path and explaining why a caught exception cannot mask it).
  - Observed evidence: PASS. Restored tests/test_packaging.py passes (2 passed), fails under mutation on forbidden list, and demonstrates two-case environment handling.
    Passing test run:
    ```
    $ python3 -m pytest tests/test_packaging.py -v
    tests/test_packaging.py::PackagingTests::test_wheel_declares_only_the_allowlisted_runtime_dependency PASSED [ 50%]
    tests/test_packaging.py::PackagingTests::test_wheel_ship_vs_dev_boundary PASSED [100%]
    ============================== 2 passed in 10.69s ==============================
    ```
    Mutation evidence (perturbing `FORBIDDEN_FILES` with `"cli.py"`):
    ```
    FAILED tests/test_packaging.py::PackagingTests::test_wheel_ship_vs_dev_boundary
    E       AssertionError: Lists differ: ['agent_workflows/cli.py'] != []
    E       First list contains 1 additional elements.
    E       First extra element 0:
    E       'agent_workflows/cli.py'
    E       - ['agent_workflows/cli.py']
    E       + [] : dev/meta content leaked into the wheel: ['agent_workflows/cli.py']
    ```
    Reverted passing run: `2 passed in 5.06s`.
    Test quoted showing both positive presence and forbidden absence assertions:
    ```python
    def test_wheel_ship_vs_dev_boundary(self):
        # Positive presence assertions
        self.assertTrue(any(n.startswith("agent_workflows/") for n in self.names), "agent_workflows package missing from wheel")
        self.assertIn("agent_workflows/cli.py", self.names)
        self.assertTrue(any(n.startswith("agent_workflows/_data/.aw/system/") for n in self.names), "bundled .aw/system data tree missing from wheel")
        self.assertIn("agent_workflows/_data/.aw/system/VERSION", self.names)
        self.assertIn("agent_workflows/_data/.aw/system/workflows/index.md", self.names)

        # Absence assertions
        leaked = []
        for n in self.names:
            base = n.split("/")[-1]
            if any(n.startswith(p) for p in FORBIDDEN_TOP):
                leaked.append(n)
            elif any(s in n for s in FORBIDDEN_AGENTS_SUBSTRINGS):
                leaked.append(n)
            elif base in FORBIDDEN_FILES:
                leaked.append(n)
        self.assertEqual(leaked, [], f"dev/meta content leaked into the wheel: {leaked}")
    ```
    Two-case environment handling proof:
    Case 1 (`import build` fails -> SKIPS):
    Simulated with `sys.modules['build'] = None`:
    `PROVED Case 1 (import build fails): raised SkipTest: the 'build' package is not installed`
    Case 2 (`build` importable but build fails -> FAILS):
    Simulated with `_build_wheel` raising `CalledProcessError(1, ['build'], stderr='Simulated build failure')`:
    `PROVED Case 2 (build fails): raised AssertionError: wheel build FAILED though the 'build' backend is installed; this is a packaging defect, not an environment skip: Simulated build failure`
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted run of the dependency-allowlist test showing PASS, plus the wheel's unconditional `Requires-Dist` lines pasted from the built artifact's `METADATA`, showing exactly `filelock>=3` and showing the four `; extra == 'test'` entries EXCLUDED from the assertion. Plus mutation evidence in BOTH directions, since the assertion is an equality and a one-sided test would miss half of it: a pasted failure when an extra dependency is expected (catching a silent ADD) and a pasted failure when the expected set is emptied (catching a silent DROP). Plus pasted proof the forbidden-path match does NOT flag `agent_workflows/_data/.aw/system/workflows/templates/workflow-artifacts-README.md`, AND the comment quoted showing it records the CORRECTED measurement per F-5 (the slash-bearing token is safe under either matching style; the hazard is loosening the token to a slash-less form). A comment repeating the original overstated claim, that substring matching is itself unsafe here, FAILS this item, because it would misdirect the next author about which edit is dangerous.
  - Observed evidence: PASS. Dependency allowlist asserts unconditional Requires-Dist is exactly {"filelock"}, excludes extras, fails under two-sided mutation, and correctly matches template path.
    Passing test run:
    `python3 -m pytest tests/test_packaging.py -k test_wheel_declares_only_the_allowlisted_runtime_dependency` -> `1 passed in 4.55s`.
    Wheel unconditional `Requires-Dist` lines pasted from `METADATA`:
    ```
    Requires-Dist: filelock>=3
    ```
    Excluded extras lines in `METADATA`:
    ```
    Requires-Dist: pytest-randomly>=3; extra == 'test'
    Requires-Dist: pytest-xdist>=3; extra == 'test'
    Requires-Dist: pytest>=8; extra == 'test'
    Requires-Dist: pyyaml>=6; extra == 'test'
    ```
    Mutation Direction 1 (silent ADD detection, `ALLOWED_RUNTIME_DEPS = set()`):
    ```
    FAILED tests/test_packaging.py::PackagingTests::test_wheel_declares_only_the_allowlisted_runtime_dependency
    E   AssertionError: Lists differ: ['filelock'] != []
    E   First extra element 0: 'filelock'
    E   - ['filelock']
    E   + [] : unexpected unconditional runtime dependencies ['filelock']: a new runtime dep needs a deliberate justification (DECISIONS D138)...
    ```
    Mutation Direction 2 (silent DROP detection, `ALLOWED_RUNTIME_DEPS = {"filelock", "extra_expected"}`):
    ```
    FAILED tests/test_packaging.py::PackagingTests::test_wheel_declares_only_the_allowlisted_runtime_dependency
    E   AssertionError: Items in the second set but not the first:
    E   'extra_expected' : the required runtime dependency is missing from the wheel: expected ['extra_expected', 'filelock'], got ['filelock']
    ```
    Forbidden-path match proof against `agent_workflows/_data/.aw/system/workflows/templates/workflow-artifacts-README.md`:
    - `startswith("workflow-artifacts/")`: False
    - bare substring `"workflow-artifacts/"`: False
    - loosened slash-less token `"workflow-artifacts"`: True (demonstrating the exact hazard)
    Quoted comment in `tests/test_packaging.py` recording F-5 corrected measurement:
    ```python
    # Anchoring and token formatting (F-5 / review measurement):
    # `FORBIDDEN_TOP` tokens retain their trailing slashes (e.g. "workflow-artifacts/").
    # The wheel legitimately ships the template file:
    #   agent_workflows/_data/.aw/system/workflows/templates/workflow-artifacts-README.md
    # That filename contains a hyphen, not a slash, so matching "workflow-artifacts/"
    # produces ZERO false positives under either startswith or bare substring matching
    # (re-measured on the built wheel: 0 hits across all entries).
    # The real hazard is loosening the token to a slash-less form ("workflow-artifacts"),
    # which WOULD incorrectly match the shipped template file.
    # We retain the startswith anchoring and trailing slashes.
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the re-measured warm AND cold build durations pasted, the decision stated with those numbers, and the docstring passage quoted showing the reasoning recorded in the file. Plus pasted proof of the resulting selection behavior that MATCHES the decision: if unmarked, a bare `python3 -m pytest tests/test_packaging.py` collecting and running it and the file containing no `pytest.mark.slow`; if marked, the same command reporting it `deselected` AND the `CONTRIBUTING.md` prose quoted showing the deselected-by-default fact is stated to the reader. A decision recorded without the numbers is a FAIL.
  - Observed evidence: PASS. Re-measured warm builds at 6.69s and 7.99s and cold cache at 6.70s; recorded unmarked decision in file docstring; runs and passes in default suite.
    Re-measured build durations at execution HEAD:
    - Warm build 1: 6.69s
    - Warm build 2: 7.99s
    - Cold cache build: 6.70s
    Decision: UNMARKED (`pytest.mark.slow` is NOT applied). The ~7s build time is well within `conftest.py`'s 90.0s `_DEFAULT_TEST_TIMEOUT`. Because `pyproject.toml` deselects `slow` tests by default and CI's slow step carries `continue-on-error: true` (making it advisory), marking it `slow` would leave the ship-vs-dev boundary without a blocking gate anywhere.
    Docstring passage quoted from `tests/test_packaging.py`:
    ```python
    Decision on pytest.mark.slow (E-04 / OQ-01):
    The file is deliberately NOT marked `pytest.mark.slow`.
    Measured build costs at execution HEAD:
    - Warm build 1: 6.69s
    - Warm build 2: 7.99s
    - Cold cache build: 6.70s
    These run comfortably inside conftest.py's 90.0s _DEFAULT_TEST_TIMEOUT.
    Because pyproject.toml's default addopts deselects `slow` tests (-m 'not slow and not livecorpus'),
    and CI's slow test step carries `continue-on-error: true` (making it advisory), marking this
    test `slow` would leave the ship-vs-dev boundary without any blocking gate in routine runs,
    lane integration, or CI. Leaving it unmarked ensures the guard runs and blocks regressions.
    ```
    Selection behavior:
    `python3 -m pytest tests/test_packaging.py` collected and ran: `2 passed in 5.06s`.
    `grep -n "pytest.mark.slow" tests/test_packaging.py` confirmed no marker decoration applied.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted `grep -n 'tests/test_' CONTRIBUTING.md` with a pasted existence check on every path it returns, all present. Plus the corrected paragraph quoted in full, showing ALL THREE false claims resolved: (1) the citation present and resolving, (2) the `are ZERO runtime dependencies` parenthetical GONE with the one allowlisted dependency named and D138 cited, and (3) the "Build a wheel" bullet's trailing `and that no runtime dependency is declared` clause GONE, replaced by an accurate description of what the restored test pins (F-11). Paste a search proving BOTH false strings are absent from the file afterwards, since the second is easy to miss while editing the first. Plus the boundary description, `_data` mapping, console-scripts and PyPI notes shown intact. Plus a pasted check that the authored text contains no em or en dash. Plus an explicit statement of what the pre-edit re-read of `CONTRIBUTING.md` found regarding `1jg2m2`'s E-06 edit (already applied and replaced, or not yet applied), since V-05 cannot be honestly marked without recording that interaction. Plus `git diff CONTRIBUTING.md` showing the edit confined to the packaging paragraph.
  - Observed evidence: PASS. CONTRIBUTING.md packaging section corrected, citations verified, zero-dependency claims removed, 1jg2m2 gap claim replaced, no em/en dashes, and docs citation guard passes.
    `grep -n 'tests/test_' CONTRIBUTING.md`:
    ```
    125:- **Enforced:** a pre-commit hook and `tests/test_local_leaks.py` run the same unified
    202:walk this list (the declaration guard in `tests/test_command_surface_declarations.py` enforces it,
    254:  ship-vs-dev boundary is enforced by `tests/test_packaging.py`, which asserts the wheel
    ```
    Existence check:
    ```
    PRESENT: tests/test_local_leaks.py
    PRESENT: tests/test_command_surface_declarations.py
    PRESENT: tests/test_packaging.py
    ```
    Pre-edit re-read finding: `1jg2m2` had already executed (commit `c50b3fa5d`), having replaced the original sentence with a gap claim that the test suite was deleted in `19313eed` and unguarded (tracked in backlog item `mflqqf`). Our edit replaced `1jg2m2`'s gap claim with the restored enforcement and pinned dependency description.
    Corrected packaging section quoted in full:
    ```markdown
    ## Packaging and the CLI (DECISIONS D46)

    The distributable is a wheel built with `hatchling` (a dev/build-time dependency; the
    only runtime dependency is `filelock`, permitted per DECISIONS D138 where minimization
    is a principle rather than an absolute prohibition). The importable package is
    `agent_workflows/`; the shipped workflow tree (`.aw/system/`) is included as package
    data via `force-include`, mapped into the wheel under `agent_workflows/_data/`.
    The console scripts `agent-workflows` / `aw` / `agentwf` all point at
    `agent_workflows.cli:main`.

    - **Dev install:** `pip install -e .` exposes the `aw` CLI against your working tree.
    - **Build a wheel:** `python -m build --wheel` (needs `pip install build`). The
      ship-vs-dev boundary is enforced by `tests/test_packaging.py`, which asserts the wheel
      contains only the package + `_data` tree and NONE of `tests/`, `.aw/workflow-artifacts/`,
      the source `.aw/records/` tree (docs, plans, prompts), or the meta docs, and that the
      unconditional runtime dependency set is pinned to exactly the one allowlisted entry (`filelock`).
    - **CLI vs the LLM `/setup-repo`:** the CLI does the deterministic, multi-repo, host-level
      work (install/update, config, discovery, fixed setup artifacts); the LLM
      `/setup-repo` workflow does the stack-tailored, judgment layer. They complement each
      other, and `aw` points the user at `/setup-repo`.
    - **Publishing to PyPI is a separate, credentialed, user-gated step** (`twine upload`); it
      is intentionally NOT part of the normal build/test flow.
    ```
    Search proving both false strings are absent:
    - `grep -n "are ZERO runtime dependencies" CONTRIBUTING.md` -> absent (exit code 1)
    - `grep -n "and that no runtime dependency is declared" CONTRIBUTING.md` -> absent (exit code 1)
    Intact surrounding elements: `## Packaging and the CLI (DECISIONS D46)`, `_data` mapping (`force-include` to `agent_workflows/_data/`), console scripts (`agent-workflows` / `aw` / `agentwf`), Dev install bullet, CLI vs LLM `/setup-repo` bullet, and Publishing to PyPI note are all preserved intact.
    Dash check: `git diff CONTRIBUTING.md | grep -E '[—–]'` produced 0 hits (NO EM OR EN DASHES IN DIFF).
    Scope confinement: `git diff CONTRIBUTING.md` shows changes strictly confined to lines 244-257 (the packaging paragraph).
    Documentation citation guard: `python3 -m pytest tests/test_docs_test_citations.py` passed (1 passed in 4.55s).
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: the summary line from a BARE `python3 -m pytest` run pasted, together with the self-measured BASELINE run it is compared against and the FAILING-NODE-ID delta between them (a total-count comparison is a FAIL of this item, since this plan deliberately adds tests). The bar is NO NEW failing node id; the pre-existing `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` failure owned by backlog `fnb8pl` is expected in both runs and must be NAMED as pre-existing rather than treated as a regression or fixed (F-16). Do not claim a green suite. Plus `aw sanitize --agent` output showing no finding introduced by the restored test. Plus `git status --short` showing no `dist/` or other build artifact present, and `git diff --cached --name-only` at commit time showing ONLY `tests/test_packaging.py` and `CONTRIBUTING.md`. Plus `aw ipd lint --phase pre-transition` conforming.
  - Observed evidence: PASS. Full suite run bare with 0 new failing node ids compared to baseline; leak gate clean with 0 findings; no build artifacts in working tree.
    Baseline bare run summary:
    `2 failed, 4349 passed, 2 skipped, 3 warnings in 575.41s (0:09:35)`
    Baseline failing node ids:
    - `tests/test_verbose_flag_reach.py::VerboseFlagReachTests::test_verbose_flag_end_to_end_observable_difference`
    - `tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs`

    Post-change bare run summary:
    `2 failed, 4351 passed, 2 skipped, 3 warnings in 480.29s (0:08:00)`
    Post-change failing node ids:
    - `tests/test_verbose_flag_reach.py::VerboseFlagReachTests::test_verbose_flag_end_to_end_observable_difference`
    - `tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs`

    Failing-node-id delta: 0 new failing node ids. Exactly 2 tests added and passed (`PackagingTests::test_wheel_ship_vs_dev_boundary` and `PackagingTests::test_wheel_declares_only_the_allowlisted_runtime_dependency`).
    Leak gate output:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`
    Tree cleanliness: `git status --short` shows no `dist/` or build artifacts.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is authoring output only and MUST NOT be executed until a human sets it `approved`; no `- Readiness:` field is written here, because that field is an output of `/plan-review` and hand-writing it would forge a review that did not happen.

THREE EXECUTION-TIME HAZARDS ARE WORTH RESTATING AT THE GATE. FIRST, E-01 IS A STOP CONDITION, NOT A FORMALITY: this plan is authorized to restore a guard over a property authoring measured to HOLD (and review RE-MEASURED as holding: 356 entries, 0 forbidden violations) and to correct stale prose. If the wheel's boundary is measured BROKEN at execution HEAD, that is a live packaging defect whose honest handling is a `bug`-kind backlog item carrying `- Blocks-Release:` per the repository's "every live bug gates the next release" rule, not a quiet fix inside a `followup`. SECOND, PENDING PLAN `1jg2m2` EDITS THE SAME SENTENCE TO THE OPPOSITE EFFECT (F-8, F-12, F-13, OQ-02), and it is `- Status: reviewed` with `- Readiness: go-pending-approval`, so it may well execute first: re-read `CONTRIBUTING.md` immediately before the E-05 edit rather than trusting this plan's quoted strings, and report the interaction at finalize. Review measured that NEITHER ORDER breaks `1jg2m2`'s own new citation guard (F-13), so this is a correctness-of-prose concern rather than a red-suite risk. THIRD, OQ-01 IS OPEN AND OWNED BY THE MAINTAINER: it is non-blocking because E-04 decides it at execution with re-measured numbers, but a maintainer approving this plan should know that choosing `slow` leaves the restored guard non-blocking in every gate including CI (F-15), which is a weaker outcome than the question originally described.

On execution the agent execution contract applies in full: commit only the paths declared in `- Scope-Paths:` through `aw commit <plan> -- <paths>`, never `git add -A` and never push, and verify the staged set before committing so no build artifact enters it. Paste ACTUAL runner output for every test claim rather than asserting success, and note that a passing run is NOT sufficient evidence here: V-02 and V-03 require pasted FAILING mutation runs, because a restored guard that cannot fail would recreate the exact false-enforcement defect this item exists to close. Because `CONTRIBUTING.md` is user-facing prose, authored text must contain no em or en dashes. After every `V-*` item carries observed evidence and `aw ipd lint --phase pre-transition` reports conforming, reaching `.aw/records/plans/executed/` is unconditionally owed, but its OWNER is conditional: under `aw oc run` / `aw agy run` the RUNNER owns that transition, so do NOT invoke `aw ipd finalize` yourself in a runner-driven execution; a HAND execution invokes it. Never hand-edit the status line and never hand-roll a `git mv` to `executed/`.
