# IPD: Pin the leak-detector fixture inputs as location-independent and remove the ambient cwd coupling the audit found

- Date: 2026-09-29
- Kind: child
- Concern: Backlog `rd2yh7` asks for the repo-wide sweep executed plan `zx9dkq` deferred: find any OTHER test that derives leak-detector INPUT from the live checkout location, the shape that cost `zx9dkq` a false alarm mid-merge. I RAN THE SWEEP AS THE MEASUREMENT THE ITEM ASKS FOR, AND THE ANSWER IS NOT THE ONE THE ITEM EXPECTED. The planted-value shape the item was written to hunt is GONE from the tree, because the file `zx9dkq` fixed was deleted wholesale by the suite trim (`git log --diff-filter=D -- tests/test_run_analytics_spa.py` names commit `19313eed` "test: trim test suite from 9,136 to under 2,000 tests", 3,220 lines deleted; `PLANTED_HOME_PATH`, `CLEAN_CONTROL_PATH` and `_leaky_repo_path` are absent from the whole tree). Every surviving plant is ALREADY a fixed literal: the only detector-input plant left is `tests/test_run_analytics._ABS_HOME`, spelled `"/ho" + "me/" + _HANDLE + "/VC/agent-workflows"`, which is the exact fix pattern the item prescribes. BUT THE SWEEP FOUND A DIFFERENT, LIVE INSTANCE OF THE SAME CLASS OF DEFECT, on the OTHER side of the call: `tests/test_run_analytics` builds its ruleset from `build_ruleset(Path.cwd())` at three call sites, so the DETECTOR (not the plant) is derived from the ambient working directory. That contradicts the premise `zx9dkq` recorded as settled. Its F6 and V-01(b) concluded "the ruleset is NOT location-dependent at all", measured by comparing fail-rule NAMES; that comparison is blind to the allowlist, and the allowlist is where the coupling actually lives. MEASURED: `build_ruleset` from the repo root carries 8 `allow_line_substrings`, from a temp dir only 4, because `load_repo_allowlist` reads `<root>/.aw/config/local-leaks-allowlist.toml` (`leak_sanitizer.resolve_allowlist_path`) which exists under one root and not the other. On a line carrying BOTH a real leak and a repo-allowlisted public substring, the repo-root ruleset returns 0 findings and the temp-root ruleset returns 3 (`home-path`, `private-repo`, `handle`). The fail-rule names are identical and the OUTCOME still differs, which is precisely the hole in `zx9dkq`'s test.
- Scope: Answer the backlog's audit question with recorded evidence (so the obligation is discharged by measurement, not by assertion), and fix the one live coupling it found: make the three `tests/test_run_analytics` ruleset constructions derive from the repository root rather than from the ambient `cwd`, and add the regression that pins the location-independence as an OUTCOME. Does NOT change `leak_sanitizer`'s rules, its allowlist, or any production module; does NOT touch `tests/test_leak_sanitizer.py` or `tests/test_local_leaks.py`, which measurement shows already use `REPO_ROOT` correctly; does NOT restore the deleted SPA test file; and does NOT decide the skip-versus-synthesize convention, which is pending plan `kmzude`'s subject.
- Scope-Paths: tests/test_run_analytics.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: rd2yh7
- Set: rd2yh7
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: yumxwz

## Workflow history

- 2026-09-29 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from the sweep the backlog item asks for, run rather than described. TWO RESULTS WORTH THE REVIEWER'S ATTENTION. FIRST, the item's expected target is GONE: the planted-value shape lives only in a file the suite trim deleted (`19313eed`), and every surviving plant is already the fixed-literal form the item prescribes, so the audit's original question closes CLEAN. SECOND, and this is why the plan is not a no-op: the sweep found the same class of defect on the detector side, `build_ruleset(Path.cwd())` at three call sites in `tests/test_run_analytics.py`, and it REFUTES a premise executed plan `zx9dkq` recorded as settled. That plan's F6/V-01(b) concluded the ruleset is location-independent, having compared only fail-rule NAMES; the allowlist is not in that comparison and is where the coupling is. Measured: 8 allowlist substrings from the repo root versus 4 from a temp dir, and on a line carrying both a real leak and an allowlisted public substring the two rulesets return 0 and 3 findings. Reachable without any exotic setup: running from `tests/` resolves the allowlist to `tests/.aw/config/...`, which does not exist. The proposed fix was measured working before being written down (`build_ruleset(REPO_ROOT)` gives 8 substrings and 0 findings from all three cwds).

## Goal

Discharge backlog `rd2yh7`'s audit with evidence, and remove the one live location coupling it turned up,
so a leak-detector test in this suite means the same thing regardless of where the repository sits and
which directory the runner happened to start in.

The narrower point worth keeping: `zx9dkq` fixed the coupling on the PLANT side and explicitly cleared the
DETECTOR side. That clearance was measured with a comparison (fail-rule names) that cannot see the
allowlist, so it was true as far as it looked and wrong as a conclusion. This plan closes the half that was
missed and pins it with a test, so the same premise cannot be re-adopted by the next reader.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: discharge the audit, then fix what it found

- [ ] E-01 RUN THE SWEEP THE BACKLOG ITEM ASKS FOR AND RECORD ITS RESULT, so the obligation is discharged by measurement rather than by a read-through. Enumerate every test-side call to a detector entry point (`scan_text`, `scan_working_tree`, `build_ruleset`), and for each one record (a) where its INPUT comes from, and (b) where its RULESET comes from, classifying each as a fixed literal, `REPO_ROOT`-derived, or ambient-`cwd`-derived. The item's suggested method is `Path(__file__)` co-occurring with `build_ruleset`/`scan_text` in one test class; USE A WIDER NET THAN THAT, because measurement shows the surviving coupling involves neither `Path(__file__)` nor a plant (it is `build_ruleset(Path.cwd())`), so the item's own grep would have missed it. Record explicitly that the shape the item was filed to hunt is absent from the tree and WHY (the file carrying it was deleted by the suite trim), since a reader who does not know that will keep looking for it.
  - Depends on: none
  - Expected outcome: a written per-call-site classification covering all detector call sites in `tests/`, naming which are safe and which are coupled, plus the recorded finding that the item's original target no longer exists in the tree with the deleting commit cited.
  - Execution state: pending

- [ ] E-02 PROVE THE COUPLING CHANGES AN OUTCOME, NOT MERELY A RULESET FIELD, because that is the difference between a real defect and a cosmetic one, and it is exactly where `zx9dkq`'s measurement stopped. Two parts, both required. (a) Show the ruleset DIVERGES by location: `build_ruleset` from the repository root versus from a directory with no `.aw/config/local-leaks-allowlist.toml`, compared on `allow_line_substrings`, not only on fail-rule names. (b) Show a SCAN RESULT flipping as a consequence: construct input carrying both a real leak token and a repo-allowlisted public substring on one line, and scan it under both rulesets. Part (b) is the load-bearing one; without it this plan is proposing to change a line that provably does not matter. ALSO show the coupling is reachable from an ordinary invocation (a cwd that is not the repository root, e.g. `tests/`), so it is not dismissed as only a foreign-checkout concern.
  - Depends on: E-01
  - Expected outcome: pasted output showing the allowlist-count divergence AND a scan whose finding count differs between the two rulesets on identical input, plus the resolved allowlist path for at least two different working directories showing one hit and one miss.
  - Execution state: pending

- [ ] E-03 DERIVE THE RULESET FROM THE REPOSITORY ROOT AT THE THREE COUPLED CALL SITES, replacing the ambient `Path.cwd()` with the module's existing repo-root anchor. `tests/support.REPO_ROOT` is the established anchor and is already imported by the other two detector-calling test modules (`tests/test_leak_sanitizer.py`, `tests/test_local_leaks.py` both call `build_ruleset(REPO_ROOT)`), so this makes the three inconsistent sites agree with the convention already in the suite rather than inventing one. DO NOT WEAKEN ANY ASSERTION TO ACHIEVE THIS: the clean-side assertions must still demand an EMPTY finding list and the control must still demand real `fail` findings. If a site cannot be made location-independent, say so and leave it, rather than relaxing what it asserts. Leave the three `_ABS_HOME`-style planted literals exactly as they are; they are already correct and are not this defect.
  - Depends on: E-02
  - Expected outcome: the three call sites deriving their ruleset from the repo-root anchor, the affected tests passing from BOTH the in-tree checkout and an outside-home clone, and the assertions shown unchanged in strength.
  - Execution state: pending

- [ ] E-04 PIN THE LOCATION-INDEPENDENCE AS A BEHAVIORAL REGRESSION, so the fix cannot silently revert. Assert an OUTCOME, not the code: that the ruleset the test uses carries the repository's committed allowlist REGARDLESS of the process working directory, demonstrated by changing `cwd` within the test and observing the same scan verdict on the same input. THIS MUST NOT BE A CODE-PINNING TEST: do not grep the test source for `Path.cwd()`, do not assert a call count, do not assert on module text (`AGENTS.md` execution contract; GUIDING_PRINCIPLES P16). Restore `cwd` in a cleanup so the test cannot leak a directory change into the rest of the suite, which matters because the suite runs under `-n auto` with random ordering. INCLUDE THE NEGATIVE HALF in the same test: the mixed-content input must be clean under the correct ruleset, and the test must also show that the input genuinely contains a detectable leak (otherwise a rule that matched nothing would satisfy it vacuously).
  - Depends on: E-03
  - Expected outcome: one new test that passes in-tree and in an outside-home clone, whose assertions are outcome-based, that restores `cwd`, and that FAILS when the E-03 change is reverted (a mutation check proving it actually guards the fix).
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE SUITE IS THE INTEGRATION GATE, which is what makes a location-coupled test expensive rather than untidy. `zx9dkq`'s own Step 0 records that a single red test refused lane integration for every lane finishing afterwards, stranding eight plans in one night. `zx9dkq` also records the concrete cost of this exact defect class: it fired while establishing a baseline for a conflicted merge and had to be ruled out as a merge regression first.
- `REPO_ROOT` IS THE ESTABLISHED REPO-ROOT ANCHOR FOR TESTS, defined once as `Path(__file__).resolve().parent.parent` in `tests/support` and imported where needed. The two other detector-calling test modules already use it for exactly this purpose, so E-03 is an alignment with existing convention and not a new pattern.
- `Path(__file__)` IS LEGITIMATE AND WIDELY USED; ITS USE IS NOT THE DEFECT. It appears in 34 test modules for reading source text and locating repo files. `zx9dkq`'s V-01 already recorded this distinction ("`Path(__file__)` is used widely and legitimately ... those uses are NOT this defect"), and the backlog item restates it. What matters is whether a checkout-derived value becomes detector INPUT or a detector RULESET, which is why E-01 classifies both sides per call site.
- WEAKENING A GUARD TO MAKE IT PASS IS FORBIDDEN, with precedent recorded in this repository: `tests/test_nested_tty_noninteractive.py`'s docstring notes that lowering a threshold "would have made this pass while silently accepting a future change that actually removed a `stdin=`". `zx9dkq` applied the same reasoning to tolerating zero leak findings. E-03 and E-04 inherit that prohibition.
- TESTS MUST ASSERT OUTCOMES, NOT CODE STRUCTURE. The `AGENTS.md` execution contract and GUIDING_PRINCIPLES P16 forbid reading production source with `inspect`/`ast`/regex or asserting symbol censuses as a correctness proxy. This directly constrains E-04, where the tempting cheap test is to grep for `Path.cwd()`, which would pin the code and prove nothing about behavior.
- THE CONCATENATION IDIOM EXISTS TO KEEP PLANTS OUT OF THE LEAK GATE. `_ABS_HOME` is spelled `"/ho" + "me/" + ...` so the test file itself does not trip `aw sanitize`. `zx9dkq`'s V-03 measured why the account name must also be real-looking: `user` is a placeholder the `home-path` rule deliberately allows, so planting it yields zero findings and passes vacuously. Any new literal this plan introduces must follow both halves of that idiom.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | MEDIUM | `tests/test_run_analytics` (three `build_ruleset(Path.cwd())` call sites) | **THE DETECTOR IS DERIVED FROM THE AMBIENT WORKING DIRECTORY, so the ruleset these tests assert against depends on where the runner was started.** This is the same defect class `zx9dkq` fixed, on the opposite side of the call: it fixed the planted INPUT, and this is the RULESET. Two of the sites assert an empty finding list (privacy projection, cache entry) and one is the CONTROL asserting real `fail` findings. | the three call sites; the divergence and outcome-flip measured in F2 and F3 |
| F2 | MEDIUM | `leak_sanitizer.build_ruleset` -> `load_repo_allowlist` -> `resolve_allowlist_path` | **THE RULESET IS LOCATION-DEPENDENT THROUGH THE ALLOWLIST, which refutes `zx9dkq`'s F6.** That plan concluded "the ruleset is NOT location-dependent at all" from a comparison of fail-rule NAMES. The names ARE identical (8 both ways), but `build_ruleset` also loads `<root>/.aw/config/local-leaks-allowlist.toml`, so `allow_line_substrings` is 8 from the repository root and 4 from a root without that file. A name-only comparison is structurally blind to this. | `build_ruleset` reads `load_repo_allowlist(repo_root)` and extends `rs.allow_line_substrings`; measured 8 versus 4 |
| F3 | MEDIUM | the same, as an observable outcome | **THE DIVERGENCE FLIPS A SCAN VERDICT, so it is a real defect and not a cosmetic field difference.** On one line carrying both a real leak token and the repo-allowlisted public substring `hermes-agent-org/hermes`, the repo-root ruleset returns 0 findings and the allowlist-less ruleset returns 3 (`home-path`, `private-repo`, `handle`). An allowlist suppresses findings LINE-WIDE, which is why its absence can only ever make a clean-side assertion fail, never silently pass. | the two scans of identical input under the two rulesets |
| F4 | LOW | reachability | **IT DOES NOT TAKE A FOREIGN CHECKOUT TO HIT THIS; AN ORDINARY `cwd` DOES.** `resolve_allowlist_path` resolves relative to whatever `Path.cwd()` returns, so running from `tests/` resolves to `tests/.aw/config/local-leaks-allowlist.toml`, which does not exist, yielding the 4-substring ruleset inside the real repository. Recorded because "we always run from the repo root" is the obvious dismissal and it is not a guarantee the tests state. | the resolved allowlist path printed for three working directories, two of them misses |
| F5 | LOW | the backlog item's stated target | **THE SHAPE THE ITEM WAS FILED TO HUNT IS ABSENT FROM THE TREE, so the audit half of this plan closes clean.** The only module that planted a checkout-derived value as detector input was `tests/test_run_analytics_spa.py`, deleted wholesale (3,220 lines) by the suite trim in commit `19313eed`; `PLANTED_HOME_PATH`, `CLEAN_CONTROL_PATH` and `_leaky_repo_path` occur nowhere now. Every surviving plant is already a fixed literal. Stated so the audit is not left ambiguous, and so a reader does not hunt for a file that no longer exists. | `git log --diff-filter=D -- tests/test_run_analytics_spa.py`; a tree-wide search for the three identifiers returning nothing |
| F6 | LOW | `tests/test_leak_sanitizer.py`, `tests/test_local_leaks.py` | THOSE TWO MODULES ARE ALREADY CORRECT AND MUST NOT BE "FIXED". Both call `build_ruleset(REPO_ROOT)`, deriving from the module location rather than the ambient `cwd`, which is the convention E-03 adopts. They are cited as the precedent for the fix, not as subjects of it. | their `build_ruleset(REPO_ROOT)` call sites |
| F7 | LOW | the whole-tree scans | A WHOLE-TREE SCAN TEST NEEDS A GIT REPOSITORY, AND THAT IS NOT THIS DEFECT. `leak_sanitizer.run` enumerates tracked files via `git ls-files`, so `test_this_repo_tree_clean` and `test_this_repo_working_tree_is_clean` fail in a plain copy of the tracked files with `fatal: not a git repository` (observed while preparing the measurement). Those tests legitimately require the repository layout, which is why the outside-home measurement must use a real clone; a `--no-hardlinks` clone gives 92 passed. Noted so an executor does not mistake a bad measurement harness for a defect. | the `CalledProcessError` from the non-repo copy; the same targets green in a clone |

## Proposed changes (ordered, validatable)

1. Run and record the per-call-site sweep of detector inputs and rulesets, discharging the backlog item's audit and recording that its original target is gone (E-01).
2. Prove the ambient-`cwd` coupling changes a scan OUTCOME, not just a ruleset field, and that an ordinary working directory reaches it (E-02).
3. Point the three coupled ruleset constructions at the repo-root anchor already used elsewhere in the suite, weakening no assertion (E-03).
4. Add one outcome-based regression that pins location-independence, restores `cwd`, carries a negative half, and fails when the fix is reverted (E-04).

REVIEW NOTE: the change to production code is NONE. `- Scope-Paths:` declares one test file. If an executor
finds themselves editing `leak_sanitizer`, that is out of scope and the sanitizer is behaving correctly:
an absent allowlist SHOULD yield a smaller allowlist. The defect is that a test asks for the wrong root.

## Deferred / out of scope (with reason)

- CORRECTING `zx9dkq`'s RECORDED F6/V-01(b) CONCLUSION IN PLACE. Its "the ruleset is NOT location-dependent at all" is refuted by F2/F3 here, but that plan is `executed` and the execution contract forbids changing what an executed plan records. The honest route is this plan standing as the correction, plus at most an appended `## Workflow history` line on `zx9dkq` pointing here, which the contract does permit.
  - Carrier-Declined: this plan (`yumxwz`) IS the correction, so nothing is outstanding for a carrier to track. The refuted conclusion is restated and corrected here in F2/F3, and an executor MAY append the pointer line to `zx9dkq`'s `## Workflow history`. Filing a carrier would assert future work that this plan itself performs.
- DECIDING THE SKIP-VERSUS-SYNTHESIZE CONVENTION for a test whose property genuinely depends on location. That is backlog `5mc38x`, already carried by pending plan `kmzude`, which measured the question's premise false and proposes a three-option rule. Duplicating it here would produce two plans writing the same convention.
  - Carrier-Declined: already carried by `kmzude`; filing another would duplicate it.
- RESTORING THE DELETED SPA LEAK-SANITIZER TESTS. The suite trim removed the module `zx9dkq` fixed (F5). Whether that deletion cost real coverage is a question about the trim, not about this audit, and it is a much larger scope than the item asks for.
  - Carrier-Declined: this plan takes no position on the trim and inherits no obligation about it; the item asks for an audit of surviving tests, which F5 answers.
- MAKING THE WHOLE SUITE PASS FROM AN ARBITRARY WORKING DIRECTORY. Out of scope and not obviously desirable: some tests legitimately require being in a git repository with this layout (F7). This plan fixes the sites whose assertion does NOT depend on the working directory but whose implementation did, which is the same fence `zx9dkq` drew.
  - Carrier-Declined: a scope fence, not a deferred obligation; the plan's position is that the general property is not desirable, so there is nothing for a carrier to track.

## Scope check

- Over-scope: none as scoped, but ONE RISK NAMED. The backlog item's summary says "audit", and an audit that
  finds nothing would close with no code change. This plan DOES change code, because the sweep found a live
  coupling the item did not anticipate (F1). An executor should not widen from there into the two modules
  that are already correct (F6) or into `leak_sanitizer` itself.
- Under-scope: the audit's original question is answered NEGATIVELY (F5), which could look like under-delivery
  against the item's wording. It is not: the item asks for a MEASUREMENT, and the measurement's result is that
  the plant-side shape is gone while a detector-side instance of the same class survives. Recording that
  honestly is the deliverable.

## Required tests / validation

1. `python3 -m pytest` bare, pasted summary line, compared against a pre-execution baseline taken in the SAME tree (also pasted). RUN IT BARE: `pyproject.toml` `addopts` already supplies the quiet/parallel/fast-subset flags, and a second `-q` compounds to `-qq` and suppresses the summary line this item requires. Gate on NO NEW failures rather than an absolute count.
2. The affected `tests/test_run_analytics.py` classes passing from the in-tree checkout, pasted with the location named.
3. The same passing from a checkout OUTSIDE the home tree, pasted with the location named. USE A REAL `git clone`, not a file copy: the whole-tree scan tests shell out to `git ls-files` and fail in a non-repository for reasons unrelated to this plan (F7).
4. THE COUPLING SHOWN TO FLIP AN OUTCOME BEFORE THE FIX and not after: the mixed-content input scanned under a repo-root ruleset and an allowlist-less ruleset, finding counts pasted for both, then the same input under the fixed construction from at least two different working directories showing one verdict.
5. THE NEW REGRESSION SHOWN TO ACTUALLY GUARD: revert the E-03 change with the E-04 test in place and paste the FAILURE, then restore and paste the pass. A regression that passes both before and after the fix is not guarding anything.
6. THE NEW TEST SHOWN NOT TO LEAK A DIRECTORY CHANGE: demonstrate `cwd` is restored (for example by asserting it in a cleanup, or by running the new test before an existing cwd-sensitive test and showing both green under `-p no:randomly`). This matters because the suite runs parallel with random ordering.
7. NO ASSERTION WEAKENED: quote the before and after of each touched assertion, showing the clean-side ones still demand an empty finding list and the control still demands `fail` findings.
8. `aw ipd lint --phase pre-transition` conforming; `aw sanitize --agent` clean (the test file gains detector-input literals, so the concatenation idiom must hold).

## Spec / documentation sync

No spec change expected, and `- Scope-Paths:` declares no `.spec.md`. This is test construction, not a
documented contract: the sanitizer's behavior, its rules, and its allowlist semantics are all unchanged, and
an absent repo allowlist yielding a smaller allowlist is correct behavior rather than a contract this plan
renegotiates.

TWO CITATIONS RECORDED HERE RATHER THAN EDITED. FIRST, the test-authoring convention this plan's E-04 obeys
(outcomes not code structure) lives in the `AGENTS.md` managed block and GUIDING_PRINCIPLES P16; pending plan
`kmzude` is the one amending that documentation, so this plan cites it and does not edit it. SECOND, the
claim this plan corrects lives inside executed plan `zx9dkq` (its F6 and V-01(b)), which the execution
contract forbids rewriting; the permitted and sufficient route is an appended `## Workflow history` line on
that plan pointing here, which an executor MAY add and which asserts nothing about its original execution.

## Open questions

### OQ-01: Should the fixed regression also cover `local_leaks`, which re-exports the same engine?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED NO, from repository evidence, rather than referred to the maintainer: there is no live defect on that path to pin. `tests/test_local_leaks.py` already calls `build_ruleset(REPO_ROOT)` (F6), the same repo-root-derived form E-03 adopts, so the `local_leaks` alias is not coupled to the ambient `cwd` and a regression there would guard nothing that is broken. Adding a second test for another alias of an engine whose behavior this plan already pins is generality for a hypothetical need, which GUIDING_PRINCIPLES P6 forbids. The measurement also shows the coupling is not a property of the alias at all but of the ARGUMENT passed, so the one regression E-04 adds covers the actual failure mode wherever the engine is reached from. Recorded rather than dropped because the broader guard is a reasonable instinct, and a reviewer who wants it can say so; nothing is outstanding in the meantime.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the written per-call-site classification, pasted, covering EVERY detector call site in `tests/` by file and line, and for each one naming where its input comes from and where its ruleset comes from. It must state which sites are safe and which are coupled, and it must record that the backlog item's original target shape is absent with the deleting commit cited. A statement that merely repeats this plan's Concern does NOT satisfy this item; the classification must be produced against the tree at execution HEAD, since the trim already moved once and may move again.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted output at execution HEAD with THREE parts. (a) `allow_line_substrings` counts for a ruleset built from the repository root and from a directory with no allowlist, showing they differ. (b) THE OUTCOME FLIP: one input containing both a real leak token and a repo-allowlisted public substring, scanned under both rulesets, with the differing finding counts and rule names visible. (c) The resolved allowlist path printed for at least two working directories, one existing and one not, proving an ordinary `cwd` reaches the coupled state. Part (b) is not optional: without it this plan cannot show the defect is more than a ruleset field difference, and the whole justification for touching the file collapses. Part (a) alone is exactly the measurement `zx9dkq` stopped at.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the affected tests pasted PASSING from TWO checkout locations with each location named, one inside the home tree and one outside it, the outside one a real `git clone` (F7). PLUS each touched assertion quoted before and after, showing none was weakened: clean-side assertions still compare to an empty list and the control still demands `fail` severity. PLUS the three changed call sites quoted, showing the ruleset now derives from the repo-root anchor and not from `Path.cwd()`. PLUS confirmation that the planted literals were left alone and that `tests/test_leak_sanitizer.py` and `tests/test_local_leaks.py` are untouched (F6), which a `git diff --name-only` satisfies.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the new test quoted in full, plus its pass pasted from the OUTSIDE-home clone specifically. THE MUTATION CHECK IS MANDATORY: revert the E-03 change with this test in place and paste the FAILURE, then restore and paste the pass, proving the regression guards the fix rather than merely coexisting with it. PLUS evidence the test asserts OUTCOMES and not code structure: it must contain no `inspect`, no `ast`, no read of a source file, and no assertion on module text or call counts (quote the test and say so explicitly). PLUS evidence `cwd` is restored after the test, and that the input used genuinely contains a detectable leak so the clean assertion cannot pass vacuously.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (4 E-items in 1 task group, under the 18-leaf / 5-group thresholds).

EXECUTION CONTRACT. `OQ-01` is non-blocking; execute the narrow form (pin only the path that was broken) and
do not widen to a second engine alias without a reviewer asking for it. SCOPE FENCE: this plan declares
`tests/test_run_analytics.py` only; an out-of-scope edit must be genuinely required and then JUSTIFIED to
`aw ipd finalize` with a `--scope-reason` per path. THE FOUR THINGS THIS PLAN MUST NOT DO, each a short path
to a green test that proves less than it claims. FIRST, do NOT weaken a clean-side assertion to tolerate
findings, or the control to tolerate none; an allowlist absence can only ADD findings, so the temptation here
is to relax the clean side, which would delete the property being asserted. SECOND, do NOT write E-04 as a
source grep for `Path.cwd()`: that pins code structure, is forbidden by the execution contract and
GUIDING_PRINCIPLES P16, and would keep passing if the ruleset became location-dependent by some other route.
THIRD, do NOT measure the outside-home case with a file copy instead of a `git clone`; the whole-tree scans
need `git ls-files` and will fail for an unrelated reason (F7), which would waste a cycle chasing a phantom.
FOURTH, do NOT edit `leak_sanitizer`, its allowlist, or the two already-correct test modules (F6). THE HARD-MUST
HONESTY RULE: paste the ACTUAL test output for every `V-*`, and for V-03 and V-04 paste it from BOTH checkout
locations with the location named, since a single-location run cannot demonstrate a location fix. Commit
through `aw commit <plan> -- <paths>`; never `git add -A`; never push; verify `git diff --cached --name-only`
before every commit and unstage anything not yours. After the gate, move this plan to
`.aw/records/plans/executed/` via `aw ipd finalize`, and do not claim done until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries real observed evidence.
