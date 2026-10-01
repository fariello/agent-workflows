# IPD: Make exit_contract load-bearing: a tree-wide usage-error floor gate plus declared-versus-observed membership for every live-executed leaf

- Date: 2026-09-30
- Kind: child
- Concern: `command_surface.CommandDeclaration.exit_contract` CALLS ITSELF NORMATIVE AND NOTHING COMPARES IT TO AN OBSERVED EXIT CODE FOR THE OVERWHELMING MAJORITY OF LEAVES, SO IT IS DOCUMENTATION WEARING A DATACLASS. The field's own docstring calls the object a "Normative contract declaration for a single CLI command or parser leaf", and all 163 declarations carry an `exit_contract` (measured at `ed3e462a0`: 106 at `(0,1,2)`, 47 at `(0,2)`, 2 at `(0,1)`, 8 outside those). THE BACKLOG ITEM'S FRAMING IS NEARLY RIGHT AND TWO OF ITS SPECIFICS ARE STALE, which matters because both decide the fix. FIRST, the item says `exit_contract` is referenced in "exactly ONE place in the whole test tree". It is read in FOUR live test files: `conformance_matrix.required_scenarios` (scenario selection only, via `if 1 in decl.exit_contract and decl.command_class in (read, check, bare)`), `test_run_cli_declarations.py` (SIX reads, which already implement declared-versus-observed for `runs resume` across codes 0/2/5/7 plus the negative `3 not in decl.exit_contract`), `test_host_capability_extension.py` (`assertNotIn(1, decl.exit_contract)`), and `test_workflow_artifacts_prune.py` (`assertEqual(decl.exit_contract, (0, 2))`). So the CAPABILITY exists and is shipped; what is missing is COVERAGE BREADTH, which changes this plan from "invent a pattern" to "extend a pattern to the whole surface". SECOND, the item names `test_cli_conformance_matrix.py` and `test_cli_quality_gates.py` as files that "do not read it at all". Both were DELETED by commit `19313eed7` ("trim test suite from 9,136 to under 2,000 tests"), so the statement is true but vacuous; `tests/conformance_matrix.py` survives and still names both as its drivers in its module docstring, which is open backlog `h0tiaw`. THE ITEM'S DIAGNOSIS OF THE HARD PART IS CORRECT AND ITS PESSIMISM IS MEASURABLY TOO STRONG, and this is the finding that makes the plan worth executing. The item says a general gate "needs a live-executable invocation per leaf, and the conformance harness explicitly does not have one", and concludes the reachable scope is the live-safe subset. Authoring MEASURED a tree-wide gate that needs NO live invocation at all: argparse's usage-error path. Driving `parser.parse_args([*leaf.split(), "--this-flag-does-not-exist"])` over all 162 declared leaves takes 0.072 SECONDS TOTAL and every single one exits 2 (`Counter({'2': 162})`), because argparse's `error()` is a hard floor no handler can intercept. Asserting `2 in decl.exit_contract` against that floor FINDS SIX REAL VIOLATIONS TODAY: `ipd-executed-gate` `(0,1)`, `ipd-status-untooled-gate` `(0,1)`, `runs next` `(0,3)`, `runs status` `(0,1,3,5)`, `run cancel` `(0,5,6)`, and `run finalize` `(0,1,4,6)`. Each of those six declarations asserts the verb cannot return 2, and each verb reachably returns 2 from a typo. That is a 100-percent-coverage gate over every declared leaf including mutations and installers, obtained without executing a single mutation, and the item's "likely shape" would have missed all six because only one of the six is in `LIVE_SAFE_LEAVES`. THE ITEM'S OWN PROPOSED SHAPE IS ALSO WORTH BUILDING AND FINDS NOTHING TODAY, which must be stated plainly rather than discovered by an executor expecting a red test: asserting observed membership across all 16 `LIVE_SAFE_LEAVES` on the human and `--agent` surfaces, in the repo and in a no-project directory, yields ZERO violations (64 invocations measured). Its value is REGRESSION PREVENTION, not a present bug, and the honest justification for building it is that the drift the item was filed over (`aw ipd board` declaring `(0,2)` and returning 3) WAS exactly this shape and would have been caught by it. That specific divergence still reproduces at this HEAD and is owned by approved pending plan `rwvzqm`, NOT by this plan.
- Scope: MAKE `exit_contract` LOAD-BEARING IN TWO LAYERS WHOSE COVERAGE AND COST ARE BOTH MEASURED, AND LEAVE EVERY VIOLATION THE FIRST LAYER FINDS CORRECTED AT THE DECLARATION. IN, five things. (1) A TREE-WIDE USAGE-ERROR FLOOR GATE over every declared leaf, asserting that a leaf whose observed usage-error code is 2 declares 2. This is the layer with full coverage and it is the reason the plan exists. (2) CORRECT THE DECLARATIONS the gate finds, by adding 2 to each, because each is factually wrong about its own verb and the gate cannot be green otherwise. Six were violating at authoring; the ACTED-ON SET is whatever E-01's census measures at the execution base, because approved sibling `69rdv6` widens two of the six in this same file and its wider tuples already contain 2 (F-13), so acting on the authored list after that sibling lands would NARROW a correct tuple. The fix is to the DECLARATION and never to the gate's threshold, never by excluding a leaf to make it pass, and never by removing a code from a tuple. (3) A LIVE MEMBERSHIP GATE over the 16 `LIVE_SAFE_LEAVES`, asserting the observed process exit code is a MEMBER of the leaf's declared tuple on the human and `--agent` surfaces. This is the item's own proposed shape, it is green today, and it is built for regression value. (4) A `--help` FLOOR GATE asserting that a leaf whose `--help` exits 0 declares 0, which is free (0.209s over 162 leaves, 149 exit 0 and 13 exit 2) and whose 13 non-zero rows are the REMAINDER-forwarding runner leaves whose real subprocess `--help` exits 0, a divergence this plan documents rather than asserts. (5) The `tests/conformance_matrix.py` module docstring correction, because it names two deleted drivers and this plan adds a real consumer of `LIVE_SAFE_LEAVES`. OUT, each with a reason. CHANGING ANY RUNTIME EXIT CODE: every correction here is to a DECLARATION that misdescribes shipped behavior, so no observable behavior changes and no caller breaks. The opposite direction (making `runs next` stop returning 2 on a typo) is not available, since argparse owns that path. THE HUMAN NO-PROJECT 3-VERSUS-2 DIVERGENCE on `next`/`ipd board`/`att`/`todo`/`attention`, owned by approved pending plan `rwvzqm` (backlog `c6vs7y`), whose E-05 pins exactly those two verbs; this plan must not pre-empt it and must not assert the pre-change value, which is why the live gate is scoped to `LIVE_SAFE_LEAVES` (none of the five spellings is in that dict) and why `attention --check`, which IS in it, exits 1 rather than reaching the guard. RECONCILING THE RUN-FAMILY EXIT VOCABULARY, owned by backlog `858lhj` (`graduated`, not open): four of the six authored corrections belong to that vocabulary, and adding 2 to them is NOT the reconciliation, it only records that argparse's floor applies to them too. REVIVING THE DELETED CONFORMANCE DRIVERS wholesale, owned by `h0tiaw`: this plan adds a targeted consumer and corrects the stale docstring, it does not resurrect golden/ANSI/fact-parity gates. ADDING A `domain_failure` OR SUCCESS-PATH MEMBERSHIP ASSERTION for mutations, which would require executing them. WIDENING `LIVE_SAFE_LEAVES`, since every candidate addition needs its own safety argument.
- Scope-Paths: agent_workflows/command_surface.py, tests/test_exit_contract_conformance.py, tests/conformance_matrix.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: cn5np0
- Set: exitcontract
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 1mnit8
- Approval: 2026-10-01, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-01 approved (aw set): status set to approved
- 2026-10-01 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-601 (HIGH), PR-602 (HIGH), PR-603, PR-604, PR-605, PR-606 all FIXED, zero deferred, zero open. Structural lint conforming at --phase author and --phase review-finalize (two accepted IPD-Z602 density advisories, now assessed in the Scope check). EVERY MEASUREMENT RE-DRIVEN INDEPENDENTLY AT HEAD 72b8d317c: the usage-error floor holds 162 of 162 in 0.086s and finds the same six violations; the in-process shortcut agrees with a real subprocess 30 of 30 on that path and diverges on --help for exactly the 13 REMAINDER-forwarding leaves (twelve at 0, prompts set at 2); 149 of 162 --help exits are 0 with no declaration omitting 0; the live matrix is 0 violations over 32 invocations; the no-project 3-versus-2 split reproduces on all five spellings; both former conformance drivers are absent with no live importer. TWO HIGH FINDINGS WERE THINGS THE PLAN COULD NOT HAVE EXECUTED SAFELY. PR-601: two of the six corrections are OWNED BY APPROVED SIBLING 69rdv6, whose measured tuples for runs next and runs status ALREADY CONTAIN 2, so executing the authored list after it lands would DELETE the reachable 5 and 7 and re-open the defect it fixes; nothing orders them, because runner_shared.dependency_depth honors only declared Item-Dependencies edges and this plan declares none, and merge-and-revalidate sees no conflict when a tuple is merely overwritten. Neither plan named the other, though third sibling u28vqb had independently found the same overlap. E-03 now acts on E-01's MEASURED census with a never-narrow rule and a stop condition, so it is correct in either order. PR-602: slow does NOT raise the 90s hang guard (conftest._test_timeout_seconds never consults it), proved by probe (a slow-marked 95s sleep reported 1 failed in 90.19s with TEST HANG GUARD), and the live gate measures 88.9s SERIALLY rather than the authored concurrency-assisted 61.3s, i.e. 99 percent of the guard; E-04 now requires an explicit timeout marker or a split INDEPENDENT of the slow decision. PR-603: the tree is FULLY GREEN at 3538 passed, 2 skipped, 3 warnings in 200.58s with the claimed date-rollover failure passing, so the authored 3419 drifted by 119 in a day and V-06 is now a by-name failure-set comparison rejecting every constant. PR-604 added the missing scope fence as a declaration plus conditional finalize ownership. PR-605 corrected the subprocess cost (measured 0.369s, so about 60s not 80s, which does not exceed 90s as claimed). PR-606 corrected 858lhj and cn5np0 from open to graduated and added the two missing deferral carriers. Findings and four Decisions rows in .aw/records/reviews/20260930-exitcontract-01-1mnit8-make-exit-contract-load-bearing-a-tree-wide-usage-error-floo.review.md. No production file and no test modified.

- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from open backlog item `cn5np0`, which carries NO `- Blocks-Release:` gate, so this plan correctly carries none either (AGENTS.md: inherit the item's gate "if it has one", do not invent one). `- Work-Kind: chore` and `- Priority: medium` are inherited through `--from-backlog`.
  EVERY NUMBER IN THIS PLAN WAS MEASURED IN THIS LANE AT `ed3e462a0`, NOT TRANSCRIBED FROM THE ITEM. The authoring pass drove the real CLI 64 times for the live matrix, drove all 162 declared leaves through argparse twice (usage error and `--help`), drove 30 leaves through BOTH an in-process parse and a real subprocess to prove the in-process shortcut faithful, and ran the suite bare.
  THE ITEM'S CENTRAL PESSIMISM IS WRONG IN A WAY THAT IMPROVES THE OUTCOME, which is the single most important thing a reviewer should check. The item concludes that full-surface coverage is unreachable because a general gate "needs a live-executable invocation per leaf". Authoring found a tree-wide gate needing NO live invocation: the argparse usage-error floor, 162 of 162 leaves exiting 2 in 0.072s total, finding SIX declarations that deny a code their verb demonstrably returns. The item's own proposed shape (live-safe membership) finds ZERO violations today and would have missed all six, because five of the six are not live-safe. So this plan builds BOTH layers and is explicit about which one carries the coverage and which one carries only regression value.
  THE ITEM OVERSTATES THE ABSENCE OF PRIOR ART AND THAT CHANGES THE DESIGN. It says `exit_contract` is read in exactly one place. It is read in four live test files, and `tests/test_run_cli_declarations.py::test_runs_resume_declared_exit_codes_are_reachable` already implements the exact declared-versus-observed pattern, including the negative form and the narrow `get_declaration` accessor. E-04 therefore EXTENDS that convention rather than starting a second one. This correction is the same one plan-review made against `rwvzqm` as PR-1101, so the stale claim has now been measured wrong twice and should not be repeated a third time.
  THE SIX VIOLATIONS ARE DECLARATION BUGS, NOT BEHAVIOR BUGS, AND THE PLAN FIXES THEM AT THE DECLARATION. Nothing shipped changes behavior, so there is no caller impact and no CHANGELOG-worthy user-visible change; `Scope-Paths` carries no `CHANGELOG.md` for that reason. A reviewer who expects a user-facing note should check that reasoning rather than assume an omission.
  THE PLAN DELIBERATELY DOES NOT TOUCH THE DRIFT THAT MOTIVATED THE ITEM. `aw ipd board` still declares `(0,2)` and still returns 3 from a no-project directory (re-measured here on all five spellings). That is approved pending plan `rwvzqm`'s E-02/E-05. This plan's live gate covers `LIVE_SAFE_LEAVES` only, and no spelling of that drift is in it, so the two plans are compatible in EITHER order (F-09).
  NO SPEC AMENDMENT IS REQUIRED and the reasoning is recorded in the spec-sync section rather than left implicit: `docs/cli-output-contract.md` Section 3's three-state enumeration is unchanged by this plan, and the six corrections move declarations TOWARD it.

## Goal

Turn `exit_contract` from an unverified annotation into a tested contract, by adding a tree-wide gate over the one exit path every declared leaf shares (argparse's usage-error floor, measured at 162 of 162 leaves in 0.072 seconds) plus an observed-membership gate over the 16 leaves the harness already deems safe to execute live. Correct the six declarations the tree-wide gate proves wrong.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure the base, then build the tree-wide floor gate

- [x] E-01 RE-DRIVE EVERY MEASUREMENT THIS PLAN DEPENDS ON, AT THE EXECUTION BASE, BEFORE EDITING ANYTHING, because each number below is a live property of a tree other lanes are changing concurrently and three of this plan's numbers have already drifted once between the item's authoring and now. Produce and record, as pasted output: (a) the usage-error census, by building the parser via `cli._build_parser()` and calling `parser.parse_args([*leaf.split(), "--this-flag-does-not-exist"])` inside `contextlib.redirect_stdout`/`redirect_stderr` for every leaf in `command_surface.get_declared_leaves()`, catching `SystemExit` and recording `e.code`, then printing a `collections.Counter` of the codes and the LIST of leaves whose code is 2 while `get_declaration(leaf).exit_contract` omits 2; (b) the same census for `--help`, recording the count at 0, the count at non-zero, and the leaf names of every non-zero row; (c) the live membership matrix, by calling `tests.conformance_matrix.run_cli` for every key of `LIVE_SAFE_LEAVES` with its value appended, on the human surface and with `--agent`, recording each observed `returncode`, whether it is a member of the declared tuple, and the WALL-CLOCK SECONDS of each invocation; (d) the declaration census, as the total count from `get_all_declarations()` and a `Counter` of `exit_contract` tuples. ALSO RE-DERIVE THE SUITE BASELINE HERE by running `python3 -m pytest` BARE and recording the summary line verbatim with the HEAD short SHA, because V-06 reconciles against THIS number and because a pre-existing unrelated failure exists (F-10) that an executor must distinguish from damage this plan caused. If any count in this plan disagrees with the re-measurement, TRUST THE RE-MEASUREMENT and say so in the evidence; in particular, if the six-violation set has grown or shrunk because another lane edited `command_surface.py`, E-03 corrects the set YOU measured, not the set written here. DO NOT EDIT ANY FILE IN THIS ITEM.
  - Depends on: none
  - Expected outcome: Pasted output carrying the four censuses, the per-invocation timings, and the bare-suite summary line with its HEAD SHA, with every divergence from this plan's written numbers called out explicitly.
  - Execution state: performed

- [x] E-02 BUILD THE TREE-WIDE USAGE-ERROR FLOOR GATE, in a new `tests/test_exit_contract_conformance.py`, as the layer that carries this plan's coverage claim. Assert, for EVERY leaf in `command_surface.get_declared_leaves()`, that if the leaf's observed usage-error exit code is 2 then `2 in get_declaration(leaf).exit_contract`. DERIVE THE OBSERVED CODE, NEVER HARDCODE IT: drive `parser.parse_args` and read `SystemExit.code`, so the test states the invariant "a declaration admits the code its verb actually returns" rather than "every declaration contains 2". The difference is load-bearing twice over: a future leaf that legitimately does NOT exit 2 on a usage error (an `add_help=False` REMAINDER forwarder that swallows unknown flags, which is a shape this CLI already uses) is then correctly SKIPPED instead of forcing a false 2 into its declaration, and the test cannot silently degrade into a tautology. USE THE IN-PROCESS PARSER AND JUSTIFY IT IN THE DOCSTRING WITH A MEASUREMENT YOU TAKE, NOT THE ONE WRITTEN HERE: review re-measured a real `python3 -m agent_workflows <leaf> --bad-flag` subprocess at **0.369s**, so 162 leaves is about **60 seconds**, which is two thirds of the 90s per-test hang budget in `conftest.py` (`_DEFAULT_TEST_TIMEOUT`) rather than the "about 80 seconds, which exceeds" this plan originally claimed. The conclusion is unchanged and the reasoning is now honest: 60s against a 90s guard leaves no useful headroom on a loaded machine and would push the file toward `slow` for no gain, while the in-process parse costs 0.072s TOTAL (review re-measured 0.086s), a roughly 700x saving; the shortcut is faithful for THIS path because `argparse.ArgumentParser.error` raises `SystemExit(2)` before any handler runs, and authoring verified it on a 30-leaf random sample where in-process and subprocess codes agreed 30 of 30 (F-05). FAIL WITH THE FULL VIOLATION LIST, not the first one: assert on a collected list of `(leaf, declared_tuple, observed_code)` tuples and put every member in the failure message, because a reader who adds a leaf wants the whole set at once. DO NOT read `command_surface.py` as TEXT with `inspect`, `ast`, regex, or substring search, and do not assert a COUNT of declarations: reach every declaration through `get_declared_leaves()` and `get_declaration()`, so the test pins observable behavior and not code structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16). A count assertion would also go red on every unrelated lane that adds a verb.
  - Depends on: E-01
  - Expected outcome: A new test file whose floor-gate test is RED at this base, naming exactly the leaves E-01's census measured (six at authoring; four if sibling `69rdv6` has landed, per F-13), each with its declared tuple and the observed 2.
  - Execution state: performed

- [x] E-03 CORRECT THE DECLARATIONS THE FLOOR GATE PROVES WRONG, in `agent_workflows/command_surface.py`, by adding 2 to the `exit_contract` of each leaf YOUR E-01 CENSUS NAMED, keeping each tuple in ascending order. At authoring the set was six: `ipd-executed-gate` (`(0,1)`), `ipd-status-untooled-gate` (`(0,1)`), `runs next` (`(0,3)`), `runs status` (`(0,1,3,5)`), `run cancel` (`(0,5,6)`) and `run finalize` (`(0,1,4,6)`). ACT ON THE MEASURED SET AND NEVER ON THAT LIST, because two of the six are OWNED BY AN APPROVED SIBLING THAT MAY LAND FIRST, which is the single most likely way this item goes wrong (F-13). Approved pending plan `69rdv6` (Set `runsexits`, `- Status: approved`) widens `runs next` to `(0,2,3,5,7)` and `runs status` to `(0,1,2,3,5,7)` in THIS SAME FILE, and BOTH of its target tuples ALREADY CONTAIN 2. So if `69rdv6` has landed, those two leaves are no longer violations, your census will not name them, and TOUCHING THEM WOULD NARROW A WIDER CORRECT TUPLE. Therefore: if a leaf is absent from your E-01 census, DO NOT EDIT IT, and record in the evidence which of the authored six you acted on and which the sibling had already fixed. Conversely, if your census names a leaf NOT in the authored six (another lane added a verb), correct it too. FIX THE DECLARATION, NEVER THE GATE: do not weaken E-02's assertion, do not add an exclusion list, and do not remove a leaf from `get_declared_leaves()` to make the test pass. Each violating declaration asserts its verb cannot return 2 while the verb returns 2 from a typo, which is a false statement about shipped behavior. THIS CHANGES NO RUNTIME BEHAVIOR, and the evidence must demonstrate that rather than assert it: `exit_contract` is consumed by `conformance_matrix.required_scenarios` (where the only predicate is on membership of 1, untouched here) and by assertions in four test files; grep the tree for a test pinning any OLD tuple you are changing and record what you find, because `test_workflow_artifacts_prune.py` pins `(0, 2)` for a DIFFERENT leaf (`archive`) and a careless grep will mislead. ADD A SHORT COMMENT AT EACH CORRECTED SITE, not a blanket one, recording that 2 is argparse's usage-error floor rather than a newly added domain outcome, and naming this plan. The distinction is the whole point for the run-family leaves: their 3/4/5/6/7 codes belong to the separate run-execution vocabulary that backlog `858lhj` (`graduated`, not open) exists to reconcile, and adding 2 must not read as a step in that reconciliation. PRESERVE THE EXISTING REASONING PROSE, especially the block above `runs resume` that explains why exit 3 was removed as unreachable and why exit 1 is absent deliberately: `runs resume` already declares 2 and is NOT corrected here, and that block is the best in-file explanation of why these tuples are curated rather than mechanical.
  - Depends on: E-02
  - Expected outcome: Every leaf E-01's census named carries 2 in ascending position with a site comment distinguishing argparse's floor from a domain outcome; any authored-six leaf the `69rdv6` sibling already fixed is left UNTOUCHED and named as such in the evidence; E-02's floor gate green; no runtime behavior changed.
  - Execution state: performed

### Task group 2: the live membership gate, the help floor, and the stale docstring

- [x] E-04 BUILD THE OBSERVED-MEMBERSHIP GATE OVER THE LIVE-SAFE LEAVES, in `tests/test_exit_contract_conformance.py`, which is the shape the backlog item itself proposes. For every key of `conformance_matrix.LIVE_SAFE_LEAVES`, run the real CLI through `conformance_matrix.run_cli([*leaf.split(), *extra])` and again with `--agent` appended, and assert the observed `returncode` is a MEMBER of `get_declaration(leaf).exit_contract`. EXTEND THE SHIPPED CONVENTION RATHER THAN INVENTING A SECOND ONE: follow `tests/test_run_cli_declarations.py::test_runs_resume_declared_exit_codes_are_reachable`, which already drives the real CLI and asserts `<code> in decl.exit_contract`, and reach declarations through the narrow `get_declaration` accessor as it does, not through `get_all_declarations()` plus a filter. SAY IN THE DOCSTRING THAT THIS GATE IS GREEN AT INTRODUCTION AND WHY IT IS STILL WORTH ITS RUNTIME, because a reader who finds a test that has never failed deserves the justification: the drift that caused backlog item `cn5np0` to be filed (`aw ipd board` declaring `(0,2)` while returning 3) is EXACTLY this shape, it survived two plans and a backlog round trip undetected, and this gate is what would have caught it. ALSO RECORD THE COVERAGE LIMIT HONESTLY IN THE SAME DOCSTRING: 16 of 163 declarations, because `LIVE_SAFE_LEAVES` admits only leaves that never write and never touch the network, so mutations and installers remain covered by declaration alone; a reader must not mistake this for a tree-wide guarantee, and the tree-wide guarantee in this file is E-02's floor gate, which needs no live invocation. BUDGET THE RUNTIME DELIBERATELY, AND UNDERSTAND THAT `slow` DOES NOT RAISE THE HANG BUDGET (F-14). Review re-measured all 32 invocations SERIALLY at **88.9s**, of which the `doctor` pair alone is **51.8s** and the other 15 leaves are 37.1s; that is **99 percent of `conftest.py`'s 90s per-test budget**, so a single serial test WILL intermittently trip the hang guard. AND `@pytest.mark.slow` DOES NOT HELP: review proved by probe that the guard fires on a `slow`-marked test too (a `slow` test sleeping 95s reported `1 failed in 90.19s` with the `TEST HANG GUARD` message), because `conftest._test_timeout_seconds` consults ONLY a `timeout` marker, `AW_TEST_TIMEOUT`, then the 90s default, and never looks at `slow`. So the two decisions are INDEPENDENT and you must make both, recording each with its number. (a) THE HANG BUDGET: you MUST raise it explicitly with `@pytest.mark.timeout(<seconds>)` sized from YOUR E-01 serial total with at least 2x headroom (240 is the review's recommendation against an 88.9s measurement), or else split the 16 leaves across more than one test function so no single function approaches 90s. Do NOT rely on `slow` for this and do NOT leave it at the default. (b) THE MARKER: mark `slow` if your serial total exceeds roughly a third of 90s, which at 88.9s it plainly does; note in the evidence that CI runs `-m slow` as an ADVISORY `continue-on-error` step (`.github/workflows/tests.yml`, "ADVISORY until the known slow failures are fixed"), so the mark trades enforcement for speed. In EITHER case do NOT silently drop `doctor` to get under a bar, since dropping the slowest leaf to make a timing gate pass is how coverage quietly shrinks.
  - Depends on: E-03
  - Expected outcome: A live membership test (or a split set of them) covering all 16 safe leaves on two surfaces, green, carrying an EXPLICIT `@pytest.mark.timeout(...)` sized from the measured serial total (or a split that keeps every function well under 90s), with its docstring carrying the 16-of-163 coverage limit, the `cn5np0` justification, and both recorded decisions (hang budget and `slow` marker) each with its number.
  - Execution state: performed

- [x] E-05 ADD THE `--help` FLOOR GATE AND DOCUMENT THE ONE DIVERGENCE IT EXPOSES, in `tests/test_exit_contract_conformance.py`. Assert that a leaf whose observed `--help` exit code is 0 declares 0, derived the same way as E-02 (in-process, catching `SystemExit`) and skipping any leaf whose observed code is not 0. Authoring measured 149 of 162 leaves exiting 0, zero violations, in 0.209s, and every declaration already contains 0, so this gate is green and cheap. ITS REAL VALUE IS THE 13 NON-ZERO ROWS AND THEY MUST BE DOCUMENTED, NOT ASSERTED: `agy exec`, `agy integrate`, `agy review`, `agy runipd`, `agy sessions`, `agy view`, `oc integrate`, `oc review`, `oc runipd`, `pwatch`, `run as`, `run ipd` and `prompts set` exit 2 from an IN-PROCESS `parse_args(["--help"])`, yet authoring verified by SUBPROCESS that twelve of them exit 0 for real (`prompts set` is the exception at 2, and it is also one of the two leaves `build_matrix` reports as `declared_absent`). The cause is that these leaves forward argv verbatim with `add_help=False` plus `argparse.REMAINDER`, so the in-process parse and the real process legitimately disagree on THIS path while agreeing on the usage-error path. WRITE THAT ASYMMETRY INTO THE DOCSTRING as the reason the help gate is skip-on-non-zero rather than assert-on-all, and as a standing warning that the in-process shortcut E-02 relies on is justified PER PATH and must not be assumed for a third path without re-measuring it. THIS IS A SEPARATE ITEM FROM E-02 ON PURPOSE: it exercises a different argparse path, it is green rather than red at introduction, and its skip condition encodes a different fact about the CLI's structure. Folding it into E-02 would bury the one genuinely surprising measurement in this plan inside a test about a different code.
  - Depends on: E-02
  - Expected outcome: A green `--help` floor gate whose docstring names the 13 divergent leaves and records that 12 of them exit 0 as real processes, with the per-path justification for the in-process shortcut.
  - Execution state: performed

- [x] E-06 CORRECT THE `tests/conformance_matrix.py` MODULE DOCSTRING, which names `tests/test_cli_conformance_matrix.py` and `tests/test_cli_quality_gates.py` as its drivers. BOTH FILES WERE DELETED by commit `19313eed7`, so the docstring sends a reader to two nonexistent files, and this plan is the first thing to import `LIVE_SAFE_LEAVES` and `run_cli` since that deletion. Rewrite the consumer sentence to name `tests/test_exit_contract_conformance.py` as a live consumer and to state plainly that the former drivers were removed by a test-trimming commit, naming open backlog `h0tiaw` as the item that owns deciding whether the rest of the harness should be revived. DO NOT revive the deleted gates, change `LIVE_SAFE_LEAVES`, change `required_scenarios`, or touch `build_matrix`: `h0tiaw` records the open question of whether this harness's encoded contract is still the intended one, and reviving a stale harness can assert obsolete promises. VERIFY BEFORE WRITING rather than trusting this plan: confirm both files are still absent and that no other live test imports the module, since another lane may have landed `h0tiaw` first, and if it has, reduce this item to adding the new consumer to whatever the docstring then says. THIS IS SEPARATE FROM E-02 AND E-04 because it corrects a pre-existing documentation defect in a file this plan only reads, introduced by an unrelated commit.
  - Depends on: E-04
  - Expected outcome: A docstring naming a consumer that exists, recording the deletion and pointing at `h0tiaw`, with the absence of both former drivers verified at execution time.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE SUITE IS RUN BARE. `pyproject.toml` `addopts` is `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`, so `python3 -m pytest` is already quiet, parallel and fast-scoped. Do not add `-n0` (several times slower here), a second `-q` (compounds to `-qq` and suppresses the `N passed` line this plan requires pasted), or `-p no:randomly`.
- PER-TEST HANG BUDGET IS 90 SECONDS, from `conftest.py`'s `_DEFAULT_TEST_TIMEOUT`, enforced by a repeating `SIGALRM` in `pytest_runtest_call` and overridable per test with `@pytest.mark.timeout(<seconds>)` or per run with `AW_TEST_TIMEOUT`. Its own comment records that the slowest fast-suite test is about 13s, so a new multi-subprocess test is an outlier by construction and must be budgeted rather than assumed.
- `slow` AND `livecorpus` ARE BOTH DESELECTED BY DEFAULT, and the `livecorpus` marker's `pyproject.toml` description records WHY a test asserting a property over this repository's own `.aw/records/` tree is dangerous: one such test went red on three correctly-cleared plans and cost a run 2h10m with nothing integrated. A gate over `command_surface` declarations is NOT a livecorpus test (declarations are code, not records), but the reasoning is why E-02 must not assert a declaration COUNT, which every unrelated lane adding a verb would turn red.
- TWO IMPORT STYLES COEXIST for test helpers: `from tests.support import ...` and bare `from support import ...`. `tests/__init__.py` exists and `tests.conformance_matrix` imports cleanly as a package module (verified by running it), so a new test should use the `from tests import ...` form.
- `tests/support.run_cli` PINS `PYTHONPATH` to the repo root via `support.pinned_env` precisely so a subprocess resolves THIS tree rather than an editable install (its docstring cites IPD `lhjsu0` and bug `ccbe60`). `conformance_matrix.run_cli` does NOT pin it; it pins `COLUMNS`, `TERM` and `PYTHONIOENCODING` and strips the color variables instead. E-04 uses the latter because it needs the harness's audience semantics, and the executor should record the risk rather than silently inherit it.
- THE SHIPPED DECLARED-VERSUS-OBSERVED PRECEDENT is `tests/test_run_cli_declarations.py::test_runs_resume_declared_exit_codes_are_reachable`, whose docstring is "Drive the real CLI in a subprocess for each of 0, 2, 5, 7 and verify it is in decl.exit_contract", together with its negative sibling asserting `3 not in decl.exit_contract`. Both reach the declaration through `get_declaration("runs resume")`.
- THE THREE-STATE EXIT CONTRACT is published in `docs/cli-output-contract.md` Section 3 ("The CLI enforces a uniform three-state exit classification across all verbs") and enforced for machine records by `agent_schema.validate_agent_record`, whose message is "Field 'exit' must be an integer in (0, 1, 2)". The constants are `artifact_types.EXIT_OK`, `EXIT_FINDINGS` and `EXIT_CANNOT_RUN`.
- COMMIT THROUGH `aw commit`, with explicit paths, never `git add -A` and never pushing.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | THE ITEM'S "EXACTLY ONE PLACE" CLAIM IS WRONG AND THE CORRECTION CHANGES THE DESIGN. `exit_contract` is read in FOUR live test files, not one: `conformance_matrix.required_scenarios` (scenario selection), `test_run_cli_declarations.py` (six reads, already declared-versus-observed), `test_host_capability_extension.py` (`assertNotIn(1, ...)`), `test_workflow_artifacts_prune.py` (`assertEqual(..., (0, 2))`). The pattern this plan needs is SHIPPED, so E-02/E-04 extend a convention instead of founding one. The same stale claim was corrected in `rwvzqm`'s review as PR-1101. | `rg -n exit_contract tests/` over `.py` files, excluding `__pycache__`: 12 non-binary hits across those four files. |
| F-02 | A TREE-WIDE GATE IS REACHABLE WITHOUT ANY LIVE INVOCATION, contradicting the item's stated blocker. Driving `parser.parse_args([*leaf.split(), "--this-flag-does-not-exist"])` over all 162 members of `get_declared_leaves()` yields `Counter({'2': 162})` in 0.072 SECONDS TOTAL. Argparse's `error()` raises `SystemExit(2)` before any handler runs, so the floor holds for mutations and installers the harness refuses to execute. | Measured at `ed3e462a0`: "declared leaves: 162 elapsed 0.072s / Counter({'2': 162})". The 152-leaf `discover_parser_leaves` population gives the same result. |
| F-03 | THAT GATE FINDS SIX REAL VIOLATIONS TODAY, each a declaration denying a code its verb demonstrably returns: `ipd-executed-gate` `(0,1)`, `ipd-status-untooled-gate` `(0,1)`, `runs next` `(0,3)`, `runs status` `(0,1,3,5)`, `run cancel` `(0,5,6)`, `run finalize` `(0,1,4,6)`. All six confirmed by REAL SUBPROCESS too, not only in-process. Six is also exactly the set of declarations omitting 2, so the gate's violation set and the "omits 2" set coincide at this base. | Two independent runs: in-process census listing the six, and a subprocess run from a no-project temporary directory showing `usage_rc=2 member=False` for each. |
| F-04 | THE ITEM'S OWN PROPOSED SHAPE FINDS NOTHING TODAY AND WOULD HAVE MISSED ALL SIX. All 16 `LIVE_SAFE_LEAVES` on the human and `--agent` surfaces, run both inside the repo and in a no-project directory, produce ZERO membership violations across 64 invocations. NONE of the six violating leaves from F-03 is in `LIVE_SAFE_LEAVES`, so this gate could not have found any of them. The live gate is therefore regression value only, and this plan's coverage claim rests entirely on F-02. | In-repo matrix: 16 leaves x 4 scenarios, "VIOLATIONS: 0", total 174s. No-project matrix: 16 leaves x 2 surfaces, "NO-PROJECT VIOLATIONS: 0". Cross-check of the six against `LIVE_SAFE_LEAVES` keys: no intersection. |
| F-05 | THE IN-PROCESS SHORTCUT IS FAITHFUL FOR THE USAGE-ERROR PATH AND NOT FOR `--help`, which is why E-02 and E-05 are separate items with different skip rules. On a 30-leaf random sample (seed 7), in-process `SystemExit.code` and real subprocess `returncode` agreed 30 of 30 for the usage-error path. For `--help` they DIVERGE on 13 leaves: in-process gives 2 while the real subprocess gives 0 for twelve of them (`prompts set` is the exception, 2 both ways), because those leaves use `add_help=False` plus `argparse.REMAINDER` to forward argv to a host runner's own parser. | "usage-error: sampled 30 leaves; in-process vs subprocess disagreements: 0". Help comparison on `agy exec`, `oc runipd`, `run as`: all three `in_process=2 subprocess=0 DIVERGES`; `status` and `ipd lint` agree at 0. |
| F-06 | COST IS DOMINATED BY ONE LEAF, AND IT DECIDES THE `slow` QUESTION AND THE SEPARATE HANG-BUDGET QUESTION (F-14), which this finding originally conflated. `doctor` costs 24 to 46 seconds per invocation inside the repo (authoring: 45.7s, 24.1s, 23.6s; review re-measured the pair at 26.41s and 25.35s), against roughly 0.3 to 0.5s for a typical leaf. The authored "61.3s wall clock for 32 invocations" was CONCURRENCY-ASSISTED and understates what one pytest function incurs: review's SERIAL total for the same 32 invocations is **88.9s**, i.e. 99 percent of `conftest.py`'s 90s per-test budget rather than comfortably "within" it. Outside a project `doctor` costs 0.8s, so the cost is corpus-driven, not startup-driven. | Timed runs recorded in E-01's format; review's full 32-row serial transcript with per-invocation seconds summing to 88.9s; `nproc` is 12 on the measuring host, so concurrency numbers are host-dependent and E-01 re-derives them. |
| F-07 | THE `--help` FLOOR IS FREE AND ALREADY SATISFIED. 149 of 162 leaves exit 0 from `--help` in 0.209s total, every declaration contains 0 (`decls omitting 0: []`), and the floor gate finds zero violations. Its value is documentary (F-05's 13 rows) plus regression. | "--help codes: Counter({'0': 149, '2': 13}) elapsed 0.209s / help-floor violations: []". |
| F-08 | THE HARNESS HAS NO DRIVER AT ALL, so this plan is its first live consumer since the trim. `tests/test_cli_conformance_matrix.py` and `tests/test_cli_quality_gates.py` are both absent from disk, deleted by commit `19313eed7` ("trim test suite from 9,136 to under 2,000 tests"), while `tests/conformance_matrix.py` still names both as its drivers. No live test imports the module. This is open backlog `h0tiaw` (priority low), which explicitly flags the risk that reviving the harness could assert obsolete promises, which is why E-06 corrects only the docstring. | `ls` on both paths: "No such file or directory". `rg` for `conformance_matrix` imports across `tests/*.py`: no hits outside `__pycache__`. `h0tiaw` item read in full. |
| F-09 | THIS PLAN AND APPROVED PENDING PLAN `rwvzqm` ARE COMPATIBLE IN EITHER ORDER, which matters because `rwvzqm` is queued and touches the same field. The no-project human-versus-machine split still reproduces at this base: `next`, `att`, `todo`, `attention` and `ipd board` each exit 3 on the human surface while `--agent` and `--json` exit 2, so five human rows violate their declarations. NONE of those five spellings is in `LIVE_SAFE_LEAVES`, and `attention --check`, which IS in it, exits 1 without reaching the guard. So E-04's gate neither asserts nor contradicts the pre-change value. `rwvzqm`'s E-05 pins exactly `next` and `ipd board`, in a different file (`tests/test_no_project_exit_is_cannot_run.py`), and its own deferred list names a tree-wide gate as "a reasonable follow-up", which is this plan. | Subprocess matrix from a non-git temporary directory with `HOME` redirected: all five spellings `human rc=3 member=False`, `agent rc=2 member=True`, `json rc=2 member=True`. `rwvzqm` front matter read: `Status: approved`, all E and V items unticked, `Scope-Paths` carries `command_surface.py` but its Scope does not change any tuple. |
| F-10 | THE BASE SUITE'S FAILURE SET IS A LIVE PROPERTY AND MUST BE COMPARED BY NAME, NOT AGAINST ANY TOTAL WRITTEN HERE. Authoring measured `1 failed, 3419 passed, 2 skipped, 3 warnings in 111.67s` at `ed3e462a0`, the one failure being `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, a MIDNIGHT-BOUNDARY FLAKE whose diff is `- 2026-09-30` versus `+ 2026-10-01` because it compares two artifacts written either side of UTC midnight. REVIEW RE-RAN IT AT HEAD `72b8d317c` AND THE TREE WAS FULLY GREEN: `3538 passed, 2 skipped, 3 warnings in 200.58s`, with that test passing, which confirms the flake diagnosis (it fails only across a date rollover) AND proves the authored total drifted by 119 collected tests in under a day. So the bar for V-06 is a BY-NAME failure-set comparison against E-01's own re-derived baseline: the after-set must contain no name absent from the before-set, and the collected rise must equal exactly the tests this plan adds. "Zero failures" is the wrong bar in the dangerous direction, because it invites waving a real regression through as the known flake; and reconciling against 3419 or 3538 is equally wrong, because both are spent numbers. | Authoring's pasted failure diff showing only the history-date line differing (run at 2026-10-01T01:43Z UTC); review's bare run at `72b8d317c` pasted as `3538 passed, 2 skipped, 3 warnings in 200.58s`. |
| F-11 | FOUR OF THE SIX CORRECTIONS BELONG TO THE RUN-FAMILY VOCABULARY THAT `858lhj` OWNS, and adding 2 to them is not that reconciliation. `858lhj` (`graduated`, low, chore; its design is already handed off, so it is NOT an open item and must not be cited as one) records that eight declarations legitimately sit outside 0/1/2 because the run-execution family uses a wider vocabulary where 3 means "human input required", and that `run_evidence` itself carries a comment recording the two tables disagree at 3 and 4. Note `858lhj` MISQUOTES one tuple: it lists `runs resume` as `(0,3)` where the declaration is `(0,2,5,7)`; the eight commands it names are right. `runs resume` already declares 2 and is NOT corrected by this plan, which is why its curated reasoning block must be preserved verbatim. | `858lhj` item read in full. `rg -n 'exit_contract=' agent_workflows/command_surface.py` filtered against the three common tuples returns exactly the eight out-of-range declarations plus one prose line in a comment. |
| F-12 | NO SPEC OR DOC AMENDMENT IS OWED. `docs/cli-output-contract.md` Section 3 enumerates 0/1/2 and no spec file mentions `exit_contract` at all (`rg -l exit_contract .aw/records/specs/ docs/` returns nothing). The six corrections move declarations toward Section 3's enumeration rather than away from it, and change no shipped behavior, so no `CHANGELOG.md` line is owed either. | Section 3 read verbatim; `rg -l` over the specs tree and `docs/` returns no files. |
| F-14 | **`@pytest.mark.slow` DOES NOT RAISE THE 90s HANG BUDGET, AND THE LIVE GATE SERIALLY MEASURES 99 PERCENT OF IT.** The plan treated `slow` as the answer to the timing risk; it is not. `conftest._test_timeout_seconds` reads a `timeout` marker, then `AW_TEST_TIMEOUT`, then returns `_DEFAULT_TEST_TIMEOUT` (90.0), and never consults the `slow` marker, so a `slow` test gets the SAME 90s guard. Review proved it rather than inferring it: a probe test marked `@pytest.mark.slow` sleeping 95s was killed by the guard (`1 failed in 90.19s`, `TEST HANG GUARD: ... exceeded its 90s per-test budget`). Review also re-measured the live matrix SERIALLY, which is how pytest will run it inside one test function: 32 invocations, **88.9s total**, `doctor` pair **51.8s**, remaining 15 leaves 37.1s. So as a single unmarked OR `slow`-marked function the gate sits at 99 percent of the guard and will flake on a loaded machine. E-04 therefore now requires an explicit `@pytest.mark.timeout(...)` or a split, INDEPENDENT of the `slow` decision. The plan's authored "61s wall clock" is a concurrency-assisted number and understates the serial cost it will actually incur. | `conftest.py` `_test_timeout_seconds` and `_DEFAULT_TEST_TIMEOUT = 90.0` read; probe transcript `1 failed in 90.19s (0:01:30)` on a `slow`-marked 95s sleep (probe file created and deleted, tree left clean); per-invocation serial timings summed to 88.9s. |
| F-13 | **TWO OF THE SIX CORRECTIONS COLLIDE WITH AN APPROVED SIBLING AND THE COLLISION NARROWS A CORRECT TUPLE, WHICH NOTHING IN THE RUNNER PREVENTS.** Approved pending plan `69rdv6` (Set `runsexits`, Order 1, `- Status: approved`, `- Readiness: go-pending-approval`) declares `agent_workflows/command_surface.py` in its own `Scope-Paths` and its E-01/E-02 widen EXACTLY `runs next` to `(0,2,3,5,7)` and `runs status` to `(0,1,2,3,5,7)`. BOTH of those already contain 2, so after `69rdv6` lands neither leaf is a floor violation, and this plan's authored instruction to set them to `(0,2,3)` and `(0,1,2,3,5)` would DELETE the reachable 5 and 7 that `69rdv6` added on measured evidence, silently re-opening the defect `69rdv6` exists to fix. THE RUNNER DOES NOT ORDER THESE TWO: `runner_shared.dependency_depth` contributes only edges DECLARED in `Item-Dependencies`, and this plan declares `none`, so queue order is decided by Set name and both plans may execute in either order or in parallel isolated worktrees. The merge-and-revalidate gate catches a textual conflict but NOT this one, because the second writer simply overwrites a tuple the first widened and the file still parses and still passes the floor gate. Neither plan named the other before this review (`grep -c 69rdv6` in this plan: 0; `grep -c 1mnit8` in `69rdv6`: 0), although a THIRD pending plan, `u28vqb`, had independently found the same overlap and fenced itself out of all four leaves. E-03 is therefore rewritten to act on E-01's MEASURED census rather than the authored list, which makes it correct in either order. | `69rdv6` front matter and E-01/E-02 read in full; tuple arithmetic printed (`2 in (0,2,3,5,7)` True, `2 in (0,1,2,3,5,7)` True); `runner_shared.dependency_depth` docstring read ("Only IPD-typed edges whose target is IN THE QUEUE contribute"); `u28vqb` F-11 names both siblings. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/command_surface.py`: add 2 to the `exit_contract` of every declaration E-01's census names as a floor violation (the six in F-03 at authoring; fewer if sibling `69rdv6` has already widened `runs next`/`runs status`, per F-13), each with a site comment distinguishing argparse's usage-error floor from a domain outcome and naming this plan. No other field, declaration, or prose block changes; `runs resume`'s curated reasoning block is preserved verbatim, and no tuple is ever NARROWED.
2. `tests/test_exit_contract_conformance.py` (new): three tests. A tree-wide usage-error floor gate over `get_declared_leaves()` (red before change 1, green after), deriving the observed code and asserting membership rather than hardcoding 2, failing with the complete violation list. A `--help` floor gate, skip-on-non-zero, whose docstring documents the 13 divergent REMAINDER-forwarding leaves. A live observed-membership gate over all 16 `LIVE_SAFE_LEAVES` on the human and `--agent` surfaces, carrying an explicit `@pytest.mark.timeout(...)` (or split so no function nears the 90s guard, per F-14), whose docstring carries the 16-of-163 coverage limit, the `cn5np0` justification, and both recorded timing decisions.
3. `tests/conformance_matrix.py`: module docstring only. Replace the two deleted driver names with the new consumer, record that the former drivers were removed by a test-trimming commit, and point at `h0tiaw`. No code in the module changes.

## Deferred / out of scope (with reason)

- THE HUMAN NO-PROJECT EXIT 3 ON `next`/`ipd board`/`att`/`todo`/`attention`. It is the drift that motivated this item and it still reproduces (F-09), but pinning it here would duplicate that plan's E-02/E-05 and race it in the same field. The two are order-independent because no affected spelling is live-safe.
  - Carrier: rwvzqm
- RECONCILING THE RUN-FAMILY EXIT VOCABULARY. Four of the six authored corrections touch that family; adding argparse's floor to them is deliberately not a step in deciding whether 3 through 7 should be renumbered (F-11).
  - Carrier: 858lhj
- WIDENING `runs next` AND `runs status` TO THEIR FULL MEASURED REACHABLE SETS (`(0,2,3,5,7)` and `(0,1,2,3,5,7)`). This plan adds only argparse's floor 2 to whatever is still violating; the reachable 5 and 7 are a separate, independently measured correction owned by an APPROVED sibling. E-03 is written so that if that sibling lands first this plan leaves both leaves untouched, and so that it can never narrow them (F-13).
  - Carrier: 69rdv6
  - Carrier-Evidence: .aw/records/plans/executed/20260930-runsexits-01-69rdv6-declare-runs-next-and-runs-status-by-their-measured-exit-cod.ipd.md
- DECLARING `oc runipd` AND `agy runipd` AS ADMITTING THE REACHABLE EXIT 3, the other measured-wrong pair in this same inventory. Not a floor violation (both already declare 2), so this plan's gate is silent on them, and a third pending plan already owns the correction together with the user-facing documents that restate the three-state claim.
  - Carrier: u28vqb
- REVIVING THE DELETED CONFORMANCE DRIVERS (golden-byte, ANSI, fact-parity, budget, accessibility gates), which records the open question of whether the harness's encoded contract is still intended. This plan adds one targeted consumer and corrects the stale docstring (F-08).
  - Carrier: h0tiaw
- A MEMBERSHIP GATE ON SUCCESS AND DOMAIN-FAILURE PATHS FOR MUTATIONS, which would require executing mutations and installers. The harness marks them `covered_by="declaration"` for exactly that reason, and the item names this as the hard part. F-02's floor gate is the coverage this plan claims instead.
  - Carrier-Declined: This is the backlog item's own stated blocker and it is UNREACHABLE BY CONSTRUCTION, not merely unscheduled: asserting a success-path exit code requires RUNNING the verb, and the verbs in question write commits, install into repositories, and reach the network. `LIVE_SAFE_LEAVES` exists precisely to exclude them, so no carrier can discharge this without first inventing a safe-execution sandbox for mutations, which is a different project. F-02's usage-error floor is the answer this plan offers instead, and it covers those same verbs on the one exit path they can be driven down safely.
- WIDENING `LIVE_SAFE_LEAVES`. Each candidate needs its own never-writes, never-networks safety argument, as the `layout` entry's own comment shows.
  - Carrier-Declined: There is no candidate to carry. This is a standing per-leaf judgement rather than an outstanding task: a future leaf that qualifies is added by whatever plan introduces it, with its own safety argument, exactly as `layout` was added by `30jug9`. Filing an item for "consider widening a dict someday" would create an obligation with no completion condition.
- MAKING ANY VERB STOP RETURNING 2 ON A USAGE ERROR, which argparse owns and which would be a behavior regression, not a fix.
  - Carrier-Declined: Declined on the merits and never to be carried. `argparse.ArgumentParser.error` owns this exit path, every one of the 162 declared leaves returns 2 from it (F-02), and the three-state contract in `docs/cli-output-contract.md` Section 3 classifies a usage error as exactly 2. Changing it would break the published contract to accommodate declarations that are simply wrong, which is why E-03 corrects the declarations instead.
- FIXING THE DATE-ROLLOVER FLAKE IN `tests/test_backlog.py` (F-10). Pre-existing, unrelated to this plan's files, and outside `Scope-Paths`; an executor should record it as pre-existing, not repair it here.
  - Carrier-Declined: Not this plan's defect to carry, and deliberately not filed from here. It is a pre-existing test that compares two artifacts written either side of UTC midnight; it touches neither `command_surface` nor `exit_contract`, and it is recorded in F-10 ONLY so an executor can distinguish it from damage this plan caused. If it is still failing at execution time, the executor should file it separately with its own measurement rather than attach it to an unrelated exit-code plan.

## Scope check

- Over-scope: none. All three paths in `Scope-Paths` are required: `command_surface.py` carries the false declarations, the new test file carries the gates, and `conformance_matrix.py`'s docstring names two deleted files this plan replaces as its consumer. The two `IPD-Z602` density advisories (E-04, E-06) are accepted rather than split: E-04's clauses are one test built from one leaf dict, driven by one runner, verified by one `V-*`; E-06 is a single docstring edit whose extra clauses are PROHIBITIONS (do not revive the gates, do not touch `LIVE_SAFE_LEAVES`) rather than additional deliverables.
- Under-scope: the three adjacent defects this plan deliberately leaves to their owners (`rwvzqm` for the no-project 3, `858lhj` for the run vocabulary, `h0tiaw` for the rest of the harness) remain unresolved after execution; note `858lhj` and `cn5np0` are `graduated` while `h0tiaw` is `open`, so "open" is accurate only of the last. A reader wanting "every exit code in the CLI is verified" does not get it here: mutations and installers stay covered on the usage-error and `--help` floors only, never on their success or domain-failure paths. And the collision with approved sibling `69rdv6` (F-13) is handled by making E-03 census-driven rather than by declaring an `Item-Dependencies` edge; that is a deliberate choice recorded as decision D-1 in the review record, because an edge would serialize two plans that are independently correct in either order once E-03 stops trusting a written list.

## Required tests / validation

- `python3 -m pytest tests/test_exit_contract_conformance.py -o addopts=""` for per-test counts, plus the bare `python3 -m pytest` for the suite verdict, with the `N passed` line pasted.
- The floor gate must be demonstrated RED before change 1 and GREEN after, with both outputs pasted; a gate only ever seen green has not been shown to detect anything.
- `python3 -m pytest tests/test_run_cli_declarations.py tests/test_host_capability_extension.py tests/test_workflow_artifacts_prune.py tests/test_command_surface_declarations.py -o addopts=""` as the targeted regression set, since those four files read `exit_contract` or the declaration surface.
- `aw ipd lint` on this plan, conforming at `--phase pre-transition` before any terminal move.

## Spec / documentation sync

N/A, with reason. No spec mentions `exit_contract` (`rg -l` over `.aw/records/specs/` returns nothing), and `docs/cli-output-contract.md` Section 3's three-state enumeration is unchanged: the six corrections move declarations toward it. No `CHANGELOG.md` line is owed because no shipped behavior changes; every correction records what a verb already did (F-12). `Scope-Paths` therefore carries no `.spec.md` and no `CHANGELOG.md`, which is deliberate and not an omission.

## Open questions

### OQ-01: Should the live membership gate carry `@pytest.mark.slow`, given that CI runs `-m slow` as an advisory `continue-on-error` step?

- Blocking: no
- Status: resolved
- Owner: executor
- Carrier-Declined: Resolved inside this plan rather than handed off. E-04 names both decision procedures and the measured numbers they turn on, so execution cannot reach the end of E-04 without having answered both, and both answers are required as pasted evidence by V-04. There is nothing left over for a carrier to hold.
- Resolution or deferral rationale: RESOLVED, AND THE QUESTION AS ORIGINALLY POSED CONFLATED TWO INDEPENDENT DECISIONS, which review separated on DEMONSTRATED evidence rather than argument (F-14). The original resolution treated `slow` as the lever that relieves the timeout risk. IT IS NOT: `conftest._test_timeout_seconds` consults a `timeout` marker, then `AW_TEST_TIMEOUT`, then the 90s default, and never the `slow` marker, so a `slow` test is guarded at 90s exactly like any other. Review proved this rather than reading it: a probe marked `@pytest.mark.slow` sleeping 95s was killed with `1 failed in 90.19s` and the `TEST HANG GUARD` message. Review also re-measured the gate SERIALLY at 88.9s for 32 invocations (`doctor` pair 51.8s), which is 99 percent of the guard, so the authored "61.3s" was concurrency-assisted and the risk is worse than the plan believed. THE ANSWER IS THEREFORE BOTH, AND THEY ARE INDEPENDENT. (a) The hang budget MUST be raised explicitly with `@pytest.mark.timeout(<seconds>)` sized from the measured serial total with at least 2x headroom (240 recommended against 88.9s), or the 16 leaves split across more than one function; this is NOT optional and `slow` cannot substitute for it. (b) The `slow` marker is additionally warranted at 88.9s, accepting that CI's `-m slow` step is `continue-on-error` and so trades enforcement for speed. The tempting third option (dropping `doctor` to get under a bar) stays forbidden, because shrinking coverage to pass a timing gate is the failure mode worth naming. The tree-wide floor gate (E-02) is unaffected either way: it costs 0.072s (review: 0.086s) and must never be marked `slow`.

### OQ-02: Are `ipd-executed-gate` and `ipd-status-untooled-gate` better served by a declaration admitting 2, or by a hook contract that treats any non-0/1 code as a refusal?

- Blocking: no
- Status: resolved
- Owner: none
- Carrier-Declined: Resolved from repository evidence during authoring, so there is no residue to carry. The question presupposed that a hook returning 2 might not fail closed; `engine.py`'s generated hook block shows both gates wired as plain `entry: python3 -m agent_workflows <gate>` with `language: system`, and pre-commit treats ANY non-zero exit from such a hook as a failed hook. So exit 2 already refuses the commit, and the only defect was the declaration denying a code the verb returns, which E-03 fixes.
- Resolution or deferral rationale: RESOLVED AS "ADMIT 2, AND NO HOOK CONTRACT CHANGE IS NEEDED", on measured evidence rather than deferred. Both leaves are pre-commit hooks whose in-file comments say "Exit 0 ok/no-op, 1 refused", and `engine.py` generates both hook entries as `python3 -m agent_workflows ipd-executed-gate` / `ipd-status-untooled-gate` with `language: system`, `pass_filenames: false`, `always_run: true`. Because pre-commit fails a `system` hook on ANY non-zero code, a malformed invocation already fails closed and blocks the commit; there is no path where exit 2 is silently treated as success. The narrow correction in E-03 (admit 2, the argparse usage-error floor) therefore makes the declaration true without touching hook behavior, and the alternative shape the question floated (collapsing 2 into 1 so the hook reports "refused") would LOSE information by making a typo indistinguishable from a genuine refusal. Not carried onward because nothing is outstanding.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Pasted output of all four censuses plus the bare-suite summary line with its HEAD short SHA. The usage-error census must show the total leaf count, the code `Counter`, and the explicit violation list; the `--help` census must show the 0/non-zero split and name every non-zero leaf; the live matrix must show per-invocation `returncode`, membership verdict and wall-clock seconds for all 16 leaves on both surfaces; the declaration census must show the total and the tuple `Counter`. Every divergence from the numbers written in this plan must be called out in prose, and if the violation set differs from F-03's six, the evidence must say which set E-03 will act on. Reject this item if any census is summarized rather than pasted, or if the suite line was produced with added flags.
  - Observed evidence: PASS. Baseline 4041 passed (HEAD bbe4589ea) and four censuses pasted below.
    Re-derived bare-suite baseline at HEAD short SHA `bbe4589ea` (commit `bbe4589ea217c782929bbc4468474e96023c13b0`):
    ```
    4041 passed, 2 skipped, 3 warnings in 247.33s (0:04:07)
    ```
    Failure set: empty (zero failures).

    Pasted census output:
    ```
    === (a) USAGE-ERROR CENSUS ===
    Total declared leaves: 162
    Elapsed: 0.044s
    Exit codes Counter: Counter({'2': 162})
    Violations count (code == 2 and 2 not in decl.exit_contract): 4
      VIOLATION: leaf='ipd-executed-gate', exit_contract=(0, 1), observed_code=2
      VIOLATION: leaf='ipd-status-untooled-gate', exit_contract=(0, 1), observed_code=2
      VIOLATION: leaf='run cancel', exit_contract=(0, 5, 6), observed_code=2
      VIOLATION: leaf='run finalize', exit_contract=(0, 1, 4, 6), observed_code=2

    === (b) --help CENSUS ===
    Elapsed: 0.124s
    Help codes Counter: Counter({'0': 149, '2': 13})
    Non-zero leaves count: 13
      NON-ZERO: leaf='agy exec', code=2
      NON-ZERO: leaf='agy integrate', code=2
      NON-ZERO: leaf='agy review', code=2
      NON-ZERO: leaf='agy runipd', code=2
      NON-ZERO: leaf='agy sessions', code=2
      NON-ZERO: leaf='agy view', code=2
      NON-ZERO: leaf='oc integrate', code=2
      NON-ZERO: leaf='oc review', code=2
      NON-ZERO: leaf='oc runipd', code=2
      NON-ZERO: leaf='prompts set', code=2
      NON-ZERO: leaf='pwatch', code=2
      NON-ZERO: leaf='run as', code=2
      NON-ZERO: leaf='run ipd', code=2
    Help floor violations (code == 0 and 0 not in decl.exit_contract): []

    === (c) LIVE MEMBERSHIP MATRIX (16 LIVE_SAFE_LEAVES) ===
    Total safe leaves: 16
    Leaf: attention                    | Surface: human | rc=1  | member=True  | contract=(0, 1, 2)    | time=6.263s
    Leaf: attention                    | Surface: agent | rc=1  | member=True  | contract=(0, 1, 2)    | time=6.257s
    Leaf: backlog check                | Surface: human | rc=0  | member=True  | contract=(0, 1, 2)    | time=0.436s
    Leaf: backlog check                | Surface: agent | rc=0  | member=True  | contract=(0, 1, 2)    | time=0.432s
    Leaf: check-local-leaks            | Surface: human | rc=0  | member=True  | contract=(0, 1, 2)    | time=1.610s
    Leaf: check-local-leaks            | Surface: agent | rc=0  | member=True  | contract=(0, 1, 2)    | time=1.609s
    Leaf: context                      | Surface: human | rc=0  | member=True  | contract=(0, 1, 2)    | time=0.310s
    Leaf: context                      | Surface: agent | rc=0  | member=True  | contract=(0, 1, 2)    | time=0.329s
    Leaf: doctor                       | Surface: human | rc=1  | member=True  | contract=(0, 1, 2)    | time=53.345s
    Leaf: doctor                       | Surface: agent | rc=1  | member=True  | contract=(0, 1, 2)    | time=92.121s
    Leaf: ipd lint                     | Surface: human | rc=1  | member=True  | contract=(0, 1, 2)    | time=3.653s
    Leaf: ipd lint                     | Surface: agent | rc=1  | member=True  | contract=(0, 1, 2)    | time=3.734s
    Leaf: layout                       | Surface: human | rc=0  | member=True  | contract=(0, 2)       | time=0.476s
    Leaf: layout                       | Surface: agent | rc=0  | member=True  | contract=(0, 2)       | time=0.326s
    Leaf: list-repos                   | Surface: human | rc=0  | member=True  | contract=(0, 2)       | time=0.290s
    Leaf: list-repos                   | Surface: agent | rc=0  | member=True  | contract=(0, 2)       | time=0.318s
    Leaf: research check-miscategorized | Surface: human | rc=1  | member=True  | contract=(0, 1, 2)    | time=0.841s
    Leaf: research check-miscategorized | Surface: agent | rc=1  | member=True  | contract=(0, 1, 2)    | time=0.885s
    Leaf: research check-refs          | Surface: human | rc=1  | member=True  | contract=(0, 1, 2)    | time=1.036s
    Leaf: research check-refs          | Surface: agent | rc=1  | member=True  | contract=(0, 1, 2)    | time=0.852s
    Leaf: sanitize                     | Surface: human | rc=0  | member=True  | contract=(0, 1, 2)    | time=1.540s
    Leaf: sanitize                     | Surface: agent | rc=0  | member=True  | contract=(0, 1, 2)    | time=1.563s
    Leaf: spec check                   | Surface: human | rc=0  | member=True  | contract=(0, 1, 2)    | time=0.320s
    Leaf: spec check                   | Surface: agent | rc=0  | member=True  | contract=(0, 1, 2)    | time=0.335s
    Leaf: specs check                  | Surface: human | rc=0  | member=True  | contract=(0, 1, 2)    | time=0.346s
    Leaf: specs check                  | Surface: agent | rc=0  | member=True  | contract=(0, 1, 2)    | time=0.346s
    Leaf: status                       | Surface: human | rc=0  | member=True  | contract=(0, 1, 2)    | time=2.475s
    Leaf: status                       | Surface: agent | rc=0  | member=True  | contract=(0, 1, 2)    | time=2.464s
    Leaf: workflow check-generated     | Surface: human | rc=2  | member=True  | contract=(0, 1, 2)    | time=0.281s
    Leaf: workflow check-generated     | Surface: agent | rc=2  | member=True  | contract=(0, 1, 2)    | time=0.294s
    Leaf: workflow validate            | Surface: human | rc=2  | member=True  | contract=(0, 1, 2)    | time=0.284s
    Leaf: workflow validate            | Surface: agent | rc=2  | member=True  | contract=(0, 1, 2)    | time=0.280s

    Total live serial time: 185.650s
    Live membership violations: 0

    === (d) DECLARATION CENSUS ===
    Total declarations count: 163
    exit_contract Counter:
      (0, 1, 2): 106
      (0, 2): 47
      (0, 1): 2
      (0, 2, 3, 5, 6): 2
      (0, 1, 2, 3): 1
      (0, 2, 3, 5, 7): 1
      (0, 2, 5, 7): 1
      (0, 5, 6): 1
      (0, 1, 2, 3, 5, 7): 1
      (0, 1, 4, 6): 1
    ```

    Divergences called out:
    1. Base suite passed count is 4041 (drifted from 3419 at authoring and 3538 at review, with 0 failures, confirmed clean).
    2. Usage-error violation set contains 4 leaves rather than the authored 6 (`ipd-executed-gate`, `ipd-status-untooled-gate`, `run cancel`, and `run finalize`), exactly as predicted by F-13 because sibling plan `69rdv6` landed prior to this turn and widened `runs next` to `(0, 2, 3, 5, 7)` and `runs status` to `(0, 1, 2, 3, 5, 7)`, which already declare 2. E-03 acts on the measured 4-leaf set and leaves `runs next` and `runs status` untouched to prevent narrowing.
    3. Serial live matrix timing is 185.650s (dominated by `doctor` at 145.466s total: 53.345s human, 92.121s agent; remaining 15 leaves: 40.184s total).
    4. Help census (149 at 0, 13 at 2) and live membership violations (0) match plan measurements exactly.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: The floor gate's failure output BEFORE E-03, naming every violating leaf with its declared tuple and the observed 2, and a passing run AFTER. Paste both. Also paste the test's docstring and confirm it carries the measured justification for the in-process parser (the 0.072s total against roughly 80s of subprocesses, and the 90s `conftest.py` budget). Confirm by reading the test body that the observed code is DERIVED from `SystemExit` and not hardcoded, that the leaf set comes from `get_declared_leaves()` with no exclusion list, that the failure message carries the FULL list rather than the first violation, and that the file contains no `inspect`, `ast`, or regex read of `command_surface.py` source text and no assertion on a count of declarations. Reject if the gate was made green by editing the assertion, by excluding a leaf, or if it was never observed red.
  - Observed evidence: PASS. Red-then-green proof demonstrated for usage-error floor gate (4 violations red -> 1 passed green in 1.22s); docstring pasted below.
    Failure output BEFORE E-03 (`python3 -m pytest tests/test_exit_contract_conformance.py -o addopts=""`):
    ```
    tests/test_exit_contract_conformance.py F                                [100%]

    =================================== FAILURES ===================================
    ____________________ test_usage_error_floor_gate_tree_wide _____________________
    ...
    E       AssertionError: Found 4 declared leaves where observed usage-error exit code is 2 but 2 is not in exit_contract:
    E           leaf='ipd-executed-gate', declared exit_contract=(0, 1), observed=2
    E           leaf='ipd-status-untooled-gate', declared exit_contract=(0, 1), observed=2
    E           leaf='run cancel', declared exit_contract=(0, 5, 6), observed=2
    E           leaf='run finalize', declared exit_contract=(0, 1, 4, 6), observed=2
    E       assert not [('ipd-executed-gate', (0, 1), 2), ('ipd-status-untooled-gate', (0, 1), 2), ('run cancel', (0, 5, 6), 2), ('run finalize', (0, 1, 4, 6), 2)]

    tests/test_exit_contract_conformance.py:63: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_exit_contract_conformance.py::test_usage_error_floor_gate_tree_wide
    ============================== 1 failed in 0.55s ===============================
    ```

    Passing run AFTER E-03:
    ```
    tests/test_exit_contract_conformance.py .                                [100%]
    ============================== 1 passed in 1.22s ===============================
    ```

    Pasted docstring of `test_usage_error_floor_gate_tree_wide`:
    ```python
    """Every declared leaf that exits 2 on usage error must declare 2 in exit_contract.

    Coverage claim (IPD 1mnit8 E-02):
    This gate provides 100% coverage across all declared leaves in the CLI (including
    mutating commands, installers, and check/read commands) without executing mutations.

    In-process shortcut justification:
    Subprocesses in this test environment take roughly 0.369s per invocation, which
    across 162 leaves would total ~60s - approximately two-thirds of the 90s per-test
    hang budget in conftest.py (_DEFAULT_TEST_TIMEOUT = 90.0). On a loaded machine,
    60s leaves minimal headroom and risks spurious hang timeouts. By contrast, the
    in-process parse_args invocation takes 0.044s total for all 162 leaves (over 1300x
    faster). The in-process shortcut is faithful for this specific path because
    argparse.ArgumentParser.error raises SystemExit(2) before any command handler
    runs, verified by an empirical 30-leaf sample where in-process SystemExit.code
    and real subprocess returncode agreed 30 of 30.

    Derivation invariant:
    The observed exit code is derived dynamically from SystemExit.code, never
    hardcoded. If a future leaf legitimately does not exit 2 on an unrecognized flag
    (e.g., REMAINDER forwarder with add_help=False), it is not falsely forced to declare 2.
    """
    ```

    Inspection of test body confirmed:
    - Observed code is derived dynamically from `SystemExit.code`, never hardcoded.
    - Leaves are obtained via `command_surface.get_declared_leaves()` with zero exclusion filters.
    - Failure message displays the complete collected violation list.
    - Zero use of `inspect`, `ast`, or regex against `command_surface.py` source text, and zero declaration count assertions.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: `git diff agent_workflows/command_surface.py` showing one changed `exit_contract` tuple per leaf E-01's census named and NOT ONE MORE, each with 2 inserted in ascending position and each with its new site comment, and NO other change; specifically confirm the `runs resume` reasoning block is byte-identical. STATE THE EXPECTED DIFF SIZE FROM YOUR OWN CENSUS, not from this plan: six if the full authored set was still violating, four if sibling `69rdv6` had already widened `runs next`/`runs status`. Paste the output of calling `get_declaration(<name>).exit_contract` for every corrected leaf plus `runs resume` as an untouched control, AND, for `runs next` and `runs status` specifically, paste their tuples whether or not you edited them, so a reader can see that neither was NARROWED (F-13): a diff that removes 5 or 7 from either is a REJECT regardless of what else is correct. Paste the grep used to search for a test pinning any OLD tuple you changed and state what it found, explicitly distinguishing `test_workflow_artifacts_prune.py`'s `(0, 2)` assertion about `archive`. Paste a passing run of the four-file targeted regression set. Reject if any runtime code path changed, if `required_scenarios` or any other consumer was touched, if a declaration absent from your census was edited, or if any tuple lost a code.
  - Observed evidence: PASS. Git diff shows exactly 4 corrected declarations with site comments; controls and regression suite pass.
    Expected diff size: exactly 4 leaves based on E-01's live census (`ipd-executed-gate`, `ipd-status-untooled-gate`, `run cancel`, and `run finalize`), as sibling `69rdv6` already widened `runs next` and `runs status` on main prior to this turn.

    `git diff agent_workflows/command_surface.py`:
    ```diff
    diff --git a/agent_workflows/command_surface.py b/agent_workflows/command_surface.py
    index 5b518c4d3..a600eb2f4 100644
    --- a/agent_workflows/command_surface.py
    +++ b/agent_workflows/command_surface.py
    @@ -721,7 +721,8 @@ COMMAND_INVENTORY: Tuple[CommandDeclaration, ...] = (
             mutation_gate="none",
             empty_error_renderer="renderer_boundary",
             legacy_flags=("--agent", "--json"),
    -        exit_contract=(0, 1),
    +        # Exit 2 added by IPD 1mnit8: argparse usage-error floor (not a domain outcome).
    +        exit_contract=(0, 1, 2),
         ),
         CommandDeclaration(
             # proclint 79li67: local pre-commit gate on raw (untooled) INTERMEDIATE plan status changes.
    @@ -734,7 +735,8 @@ COMMAND_INVENTORY: Tuple[CommandDeclaration, ...] = (
             mutation_gate="none",
             empty_error_renderer="renderer_boundary",
             legacy_flags=("--agent", "--json"),
    -        exit_contract=(0, 1),
    +        # Exit 2 added by IPD 1mnit8: argparse usage-error floor (not a domain outcome).
    +        exit_contract=(0, 1, 2),
         ),
         # --- IPD / Plans Family ---
         CommandDeclaration(
    @@ -1179,7 +1181,8 @@ COMMAND_INVENTORY: Tuple[CommandDeclaration, ...] = (
             mutation_gate="none",
             empty_error_renderer="renderer_boundary",
             legacy_flags=("--workflow", "--actor", "--reason", "--agent", "--json"),
    -        exit_contract=(0, 5, 6),
    +        # Exit 2 added by IPD 1mnit8: argparse usage-error floor, not a run-execution vocabulary outcome.
    +        exit_contract=(0, 2, 5, 6),
         ),
         # `command_class="read"`: `runs status` reconstructs state and displays run progress without
         # writing to the ledger or disk, matching `RUNS_VIEWER_LEAF_NAMES`.
    @@ -1248,7 +1251,8 @@ COMMAND_INVENTORY: Tuple[CommandDeclaration, ...] = (
             mutation_gate="auth_floor",
             empty_error_renderer="renderer_boundary",
             legacy_flags=("--workflow", "--actor", "--agent", "--json"),
    -        exit_contract=(0, 1, 4, 6),
    +        # Exit 2 added by IPD 1mnit8: argparse usage-error floor, not a run-execution vocabulary outcome.
    +        exit_contract=(0, 1, 2, 4, 6),
         ),
         CommandDeclaration(
             # execset Order 05 (2h7777): read-only inspection of a Set run's durable decisions
    ```

    Byte-identical confirmation: The reasoning prose block preceding `runs resume` (lines 1142-1164) is completely untouched and byte-identical.

    Inspection of declared tuples via `get_declaration`:
    ```
    ipd-executed-gate: (0, 1, 2)
    ipd-status-untooled-gate: (0, 1, 2)
    run cancel: (0, 2, 5, 6)
    run finalize: (0, 1, 2, 4, 6)
    runs resume: (0, 2, 5, 7)
    runs next: (0, 2, 3, 5, 7)
    runs status: (0, 1, 2, 3, 5, 7)
    ```
    Confirmation: `runs resume` is untouched. Neither `runs next` nor `runs status` was narrowed: both preserve reachable 5 and 7 from sibling `69rdv6`.

    Grep for tests pinning old tuples:
    `git grep -n -E "\(0,\s*1\)" tests/`: matched scenario selection in `test_deferral_passthrough_reachability.py:42`, `test_fields_flag_reach.py:106`, and `test_json_and_exitcodes.py:51`, none of which asserts on `exit_contract`.
    `git grep -n -E "\(0,\s*5,\s*6\)" tests/`: 0 hits.
    `git grep -n -E "\(0,\s*1,\s*4,\s*6\)" tests/`: 0 hits.
    (Distinguished from `test_workflow_artifacts_prune.py:100` which pins `(0, 2)` for `archive`).

    Targeted regression test suite (`tests/test_run_cli_declarations.py tests/test_host_capability_extension.py tests/test_workflow_artifacts_prune.py tests/test_command_surface_declarations.py -o addopts=""`):
    ```
    ============================= 73 passed in 25.22s ==============================
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: A passing run of the live membership test with its duration, plus its full docstring pasted, showing the 16-of-163 coverage limit, the `cn5np0` justification naming the `ipd board` drift as the shape it would have caught, and the explicit statement that it is green at introduction. Paste the per-leaf SERIAL timing and its TOTAL, then record BOTH timing decisions separately (F-14): (a) the hang budget, naming the explicit `@pytest.mark.timeout(<seconds>)` you set and the measured total it was sized against, or the split you used instead, and (b) the `slow` marker decision; if marked `slow`, the evidence must acknowledge that CI's `-m slow` step is `continue-on-error`. REJECT A `slow` MARK OFFERED AS THE HANG-BUDGET FIX: the guard ignores `slow` and fires at 90s regardless, so a test left at the default budget against an ~89s serial total is not acceptable even when marked. Confirm by reading the body that all 16 keys of `LIVE_SAFE_LEAVES` are covered with no skips, that both the human and `--agent` surfaces are driven, that membership is asserted against `get_declaration(leaf).exit_contract` rather than a hardcoded set, and that declarations are reached through the narrow accessor as `test_run_cli_declarations.py` does. Reject if `doctor` or any other leaf was dropped, or if the coverage limit is absent from the docstring.
  - Observed evidence: PASS. Live safe membership gate passed (3 passed in 360.20s); serial timing 185.650s, timeout 500s, slow marked.
    Passing run of all tests in `tests/test_exit_contract_conformance.py` (`python3 -m pytest tests/test_exit_contract_conformance.py -o addopts=""`):
    ```
    tests/test_exit_contract_conformance.py ...                              [100%]
    ======================== 3 passed in 360.20s (0:06:00) =========================
    ```

    Pasted docstring of `test_live_safe_leaves_exit_contract_membership`:
    ```python
    """Every live-executed safe leaf must produce an exit code declared in exit_contract.

    Coverage boundary (IPD 1mnit8 E-04):
    This gate covers 16 of 163 declarations (the curated LIVE_SAFE_LEAVES population in
    tests/conformance_matrix.py). It drives the real CLI in a subprocess across both the
    human and --agent surfaces (32 invocations total). Mutations, installers, and disk-writing
    verbs are excluded from live execution for safety and remain covered by declaration
    and the tree-wide usage error floor gate (test_usage_error_floor_gate_tree_wide).

    Justification and regression prevention (backlog cn5np0):
    This gate is green at introduction (0 violations across all 32 invocations). Its value
    is durable regression prevention: the silent drift that motivated backlog item cn5np0
    ('aw ipd board' declaring (0, 2) while reachably returning 3) was exactly this shape
    and would have been caught by this gate.

    Timing decisions recorded (IPD 1mnit8 F-14):
    1. Hang budget: The 32 invocations take 185.650s serially at execution base (dominated
       by 'doctor' at 53.345s human and 92.121s agent). Because conftest.py's 90s hang budget
       ignores @pytest.mark.slow, an explicit @pytest.mark.timeout(500) is set, providing
       >2.5x headroom over the measured serial total.
    2. Slow marker: Marked @pytest.mark.slow because the 185.650s serial runtime far exceeds
       one-third of 90s (~30s). In CI (.github/workflows/tests.yml), -m slow runs as an
       advisory continue-on-error step, trading enforcement for suite execution speed.
    """
    ```

    Per-leaf serial timings from E-01 measurement:
    ```
    Leaf: attention                    | human: 6.263s  | agent: 6.257s
    Leaf: backlog check                | human: 0.436s  | agent: 0.432s
    Leaf: check-local-leaks            | human: 1.610s  | agent: 1.609s
    Leaf: context                      | human: 0.310s  | agent: 0.329s
    Leaf: doctor                       | human: 53.345s | agent: 92.121s
    Leaf: ipd lint                     | human: 3.653s  | agent: 3.734s
    Leaf: layout                       | human: 0.476s  | agent: 0.326s
    Leaf: list-repos                   | human: 0.290s  | agent: 0.318s
    Leaf: research check-miscategorized | human: 0.841s  | agent: 0.885s
    Leaf: research check-refs          | human: 1.036s  | agent: 0.852s
    Leaf: sanitize                     | human: 1.540s  | agent: 1.563s
    Leaf: spec check                   | human: 0.320s  | agent: 0.335s
    Leaf: specs check                  | human: 0.346s  | agent: 0.346s
    Leaf: status                       | human: 2.475s  | agent: 2.464s
    Leaf: workflow check-generated     | human: 0.281s  | agent: 0.294s
    Leaf: workflow validate            | human: 0.284s  | agent: 0.280s
    TOTAL SERIAL TIME: 185.650s (doctor pair: 145.466s, other 15 leaves: 40.184s)
    ```

    Timing decisions recorded separately:
    (a) Hang budget decision: `@pytest.mark.timeout(500)` set explicitly. Sized against measured 185.650s serial total with >2.5x headroom. Conftest.py's 90s budget ignores `slow`, so explicit marker is mandatory.
    (b) Slow marker decision: Marked `@pytest.mark.slow` because 185.650s exceeds one-third of 90s (~30s). Acknowledged that CI runs `-m slow` as advisory `continue-on-error` in `.github/workflows/tests.yml`.

    Body confirmation:
    - Covers all 16 keys of `conformance_matrix.LIVE_SAFE_LEAVES` with no skips or dropped leaves (`assert len(safe_leaves) == 16`).
    - Drives both human and `--agent` surfaces.
    - Asserts membership against `command_surface.get_declaration(leaf).exit_contract` reached through narrow accessor.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: A passing run of the `--help` floor gate, and its docstring pasted showing the named divergent leaves and the recorded fact that twelve of them exit 0 as real subprocesses while the in-process parse gives 2. Paste a re-measurement demonstrating that divergence for at least three of the named leaves (in-process code beside subprocess code) and for at least one agreeing control leaf, so the skip condition is justified by evidence taken at execution time rather than quoted from this plan. Confirm by reading the body that the gate SKIPS non-zero observed codes rather than asserting on them. Reject if the divergence is merely asserted in prose without a pasted measurement, or if the gate was written to assert over all leaves.
  - Observed evidence: PASS. --help floor gate passed; in-process vs subprocess divergence demonstrated on 3 leaves plus controls.
    Passing run of `test_help_floor_gate` (part of `tests/test_exit_contract_conformance.py` run where all 3 tests passed).

    Pasted docstring of `test_help_floor_gate`:
    ```python
    """Every declared leaf that exits 0 from --help must declare 0 in exit_contract.

    Documented divergence and skip condition (IPD 1mnit8 E-05):
    149 of 162 declared leaves exit 0 from an in-process parse_args(["--help"]).
    Exactly 13 leaves exit 2 from the in-process parse:
      - 'agy exec'
      - 'agy integrate'
      - 'agy review'
      - 'agy runipd'
      - 'agy sessions'
      - 'agy view'
      - 'oc integrate'
      - 'oc review'
      - 'oc runipd'
      - 'prompts set'
      - 'pwatch'
      - 'run as'
      - 'run ipd'
    These leaves forward argv verbatim with add_help=False and argparse.REMAINDER to
    subordinate runner parsers. In a real subprocess, 12 of the 13 actually exit 0
    ('prompts set' is the exception, exiting 2 in subprocess too). Because of this
    architectural asymmetry, this gate SKIPS any leaf whose observed in-process code is
    non-zero, rather than asserting over all leaves.

    Standing warning on in-process shortcut:
    The in-process shortcut that test_usage_error_floor_gate_tree_wide relies on is
    justified PER PATH. While faithful for usage errors, it diverges on --help for
    REMAINDER forwarders, and must never be assumed for a new CLI path without
    empirical re-measurement.
    """
    ```

    Re-measurement demonstrating in-process vs subprocess divergence:
    ```
    leaf='agy exec'       | in_process=2 | subprocess=0 | DIVERGES
    leaf='oc runipd'      | in_process=2 | subprocess=0 | DIVERGES
    leaf='run as'         | in_process=2 | subprocess=0 | DIVERGES
    leaf='prompts set'    | in_process=2 | subprocess=2 | AGREES
    leaf='status'         | in_process=0 | subprocess=0 | AGREES
    leaf='ipd lint'       | in_process=0 | subprocess=0 | AGREES
    ```
    Confirmation: Demonstrates divergence on 3 leaves (`agy exec`, `oc runipd`, `run as`), 1 non-zero agreeing leaf (`prompts set`), and 2 agreeing zero control leaves (`status`, `ipd lint`).

    Body confirmation:
    Test body explicitly skips non-zero observed codes (`if observed_code != 0: continue`), gating only leaves whose in-process `--help` exits 0.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: `git diff tests/conformance_matrix.py` showing a docstring-only change that names `tests/test_exit_contract_conformance.py`, records the former drivers' removal, and cites `h0tiaw`; confirm no code line in the module changed (specifically `LIVE_SAFE_LEAVES`, `required_scenarios` and `build_matrix` are untouched). Paste the execution-time verification that both former driver files are still absent and that no other live test imports the module, or, if another lane has landed `h0tiaw` first, the adjusted action taken. FINALLY, paste the BARE `python3 -m pytest` summary line and reconcile it against E-01's baseline BY NAME, not by total (F-10): name the before FAILURE SET and the after FAILURE SET, require the after-set to contain no name absent from the before-set, and require the collected rise to equal exactly the tests this plan adds with any other difference explained test by test. If `test_release_exempt_setter_roundtrip_and_parity` appears in either set, identify it as the known midnight-boundary flake rather than counting it as this plan's; if it appears in the AFTER set but not the BEFORE set, say so explicitly rather than assuming the flake (review measured the tree fully green at `3538 passed`, so its presence is not guaranteed). Reject a reconciliation against any constant written in this plan (3419 or 3538) instead of against E-01's own measurement, and reject "zero failures" offered as the bar.
  - Observed evidence: PASS. Docstring of tests/conformance_matrix.py updated; former drivers verified absent; bare suite 4043 passed (0 regressions).
    `git diff tests/conformance_matrix.py`:
    ```diff
    diff --git a/tests/conformance_matrix.py b/tests/conformance_matrix.py
    index 09ce76aa8..bab46e474 100644
    --- a/tests/conformance_matrix.py
    +++ b/tests/conformance_matrix.py
    @@ -1,11 +1,17 @@
     """Generated CLI output-conformance matrix (awcliux Order 05 `e8hu4s` E-01 / E-02).

    -Stdlib only (Python 3.9+). This module is the shared harness consumed by the
    -agent surface conformance test:
    +Stdlib only (Python 3.9+). This module is the shared harness consumed by:

     - ``test_agent_surface_conformance.py``: executes every parser leaf declaring
       an ``aw.agent/v1`` result record under ``--agent`` and verifies schema
       validity and exit code parity against the real subprocess outcome.
    +- ``test_exit_contract_conformance.py``: executes safe read/check leaves in
    +  ``LIVE_SAFE_LEAVES`` via ``run_cli`` to verify observed exit-code membership
    +  against declared ``exit_contract`` (IPD 1mnit8).
    +
    +Former drivers (``test_cli_conformance_matrix.py`` and ``test_cli_quality_gates.py``)
    +were removed by test-trimming commit 19313eed7; deciding whether to revive the remainder
    +of the harness is tracked by open backlog item h0tiaw.

     Design notes
     ------------
    ```
    Confirmation: Docstring-only change; zero code lines in `tests/conformance_matrix.py` modified (`LIVE_SAFE_LEAVES`, `required_scenarios`, and `build_matrix` are byte-identical).

    Verification of former drivers and live importers at execution time:
    - `ls tests/test_cli_conformance_matrix.py tests/test_cli_quality_gates.py`:
      `ls: cannot access 'tests/test_cli_conformance_matrix.py': No such file or directory`
      `ls: cannot access 'tests/test_cli_quality_gates.py': No such file or directory`
      (Both files remain deleted by commit `19313eed7`).
    - Live importers of `tests.conformance_matrix`: `tests/test_agent_surface_conformance.py` (which imports `EXEMPTION_REGISTRY`, `RUNNABLE_ARGV`, `run_cli`, `semantic_facts_from_agent`) and the new consumer `tests/test_exit_contract_conformance.py` (which imports `LIVE_SAFE_LEAVES` and `run_cli`).

    Full bare `python3 -m pytest` summary and reconciliation against E-01 baseline:
    - E-01 baseline: `4041 passed, 2 skipped, 3 warnings in 247.33s (0:04:07)` (230 deselected by `-m 'not slow and not livecorpus'`).
      Before failure set: `set()` (empty).
    - Post-change bare run: `4043 passed, 2 skipped, 3 warnings in 151.02s (0:02:31)` (231 deselected).
      After failure set: `set()` (empty).
    - Failure set comparison: `after_failure_set == before_failure_set == set()`. After-set contains no test name absent from before-set.
    - Reconciliation of collected count:
      Fast-suite tests added: +2 passed (`tests/test_exit_contract_conformance.py::test_usage_error_floor_gate_tree_wide` and `tests/test_exit_contract_conformance.py::test_help_floor_gate`), explaining the rise from 4041 to 4043 passed.
      Slow-suite tests added: +1 deselected (`tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership`), explaining the rise from 230 to 231 deselected.
      Total tests added by this plan is exactly 3 (2 fast, 1 slow), matching all 3 test functions in `tests/test_exit_contract_conformance.py`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `- Status: reviewed` with `- Readiness: go-pending-approval` written by `/plan-review`; the author correctly omitted that field, and only the review may set it. It requires explicit human approval before execution.

WHAT THE HUMAN IS ACCEPTING. The DESIGN is confirmed sound by independent re-measurement in a review lane at HEAD `72b8d317c`: the usage-error floor holds on 162 of 162 leaves in 0.086s, it finds the same six violations, the in-process shortcut agrees with a real subprocess 30 of 30 on that path and diverges on `--help` for exactly the 13 REMAINDER-forwarding leaves the plan names, the live matrix is 0 violations over 32 invocations, and the no-project 3-versus-2 split reproduces on all five spellings. Review changed no E-item's intent. What review DID change is one ORDERING HAZARD and two VALIDATION BARS. The hazard (F-13) is that two of the six corrections belong to approved sibling `69rdv6`, whose wider measured tuples ALREADY contain 2, so executing this plan's authored list after that sibling would delete the reachable 5 and 7 it added; E-03 now acts on E-01's measured census instead of the written list, making it correct in either order. The bars: `slow` does not raise the 90s hang guard and the live gate serially measures 88.9s against it (F-14), and the base failure set is a live population that must be compared by name rather than against any total written here (F-10, re-measured fully green at 3538 passed).

EXECUTION CONTRACT. Commit only the paths in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A`, never a bare or `-a` commit, and never pushing. Paste actual runner output for every test claim; a claimed pass with no pasted summary line is a contract violation regardless of the underlying truth. Do not mark any `V-*` item complete from the matching execution checkmark; inspect the evidence in a separate pass. This lane shares a checkout with other agents: verify the staged set with `git diff --cached --name-only` before each commit and unstage anything you did not change with `git restore --staged <path>`.

SCOPE FENCE. The three paths in `- Scope-Paths:` are the declared scope. This is a DECLARATION so the lifecycle can tell afterwards whether an out-of-scope file was edited or a declared file was left unmodified; it is NOT an instruction to stop over a scope question. If the work genuinely requires editing a path outside it, MAKE the edit and JUSTIFY it at finalize (`aw ipd finalize` refuses to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path). ONE CONDITION IS A GENUINE STOP, and it is the F-13 hazard rather than a scope question: if the working tree's `runs next` or `runs status` tuple already contains 2 when you reach E-03, do NOT edit that declaration and do NOT narrow it; record which sibling landed and proceed with the leaves your census actually named.

ORDER MATTERS AND IS NOT NEGOTIABLE FOR ONE PAIR. E-02 must be written and OBSERVED RED before E-03 corrects the declarations. A gate introduced green against already-corrected declarations has demonstrated nothing, and this plan's entire coverage claim rests on that gate detecting real divergence. ONE CAVEAT FOLLOWS FROM F-13: if sibling `69rdv6` has already landed, the RED set will be four leaves rather than six, which is still a valid red and still demonstrates detection; a FULLY GREEN floor gate at E-02 is the only outcome that invalidates the demonstration, and if you observe it you must establish detection some other way (for example by reverting one declaration in a scratch copy) and say so in V-02's evidence rather than claiming a red you did not see. E-05 depends on E-02 only for the shared file, and E-06 is last so its docstring names a consumer that already exists and passes.

POST-GATE LIFECYCLE. Do not move this plan to `.aw/records/plans/executed/` or set its status terminal until `aw ipd lint --phase pre-transition` reports conforming and every `V-*` item carries concrete pasted evidence. Use the tooled transition (`aw ipd finalize` when you are the executor; the runner performs it when a run owns the lifecycle), never a hand-rolled `git mv` and never a hand edit of `- Status:`.
