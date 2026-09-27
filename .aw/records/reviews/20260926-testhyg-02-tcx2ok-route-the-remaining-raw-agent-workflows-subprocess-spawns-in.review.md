# Review findings: plan tcx2ok

- Subject-Id: tcx2ok
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated lane worktree at HEAD `bfdd8821`. Structural preflight `aw ipd lint --phase
author --detail` CONFORMED before revision; `--phase review-finalize --detail` conforms after (one
`IPD-Z602` density advisory appeared on my first rewrite of E-06 and was resolved by restructuring it
rather than by arguing with it). No pre-review snapshot was needed: `git status --short` was empty.
Suite baseline re-measured before touching anything: `2598 passed, 2 skipped, 3 warnings in 41.66s`.

THE PLAN'S FACTS ARE UNUSUALLY GOOD AND I CHECKED THEM ONE BY ONE. The 19-site census is exactly
right, per file and per call kind, including the detail that one of the two `test_concurrent_driver_guard`
sites is a `Popen` and the other a `run`. F-2's count of 10 bare `"python3"` spawns is exactly right,
and I confirmed the stronger claim implied by it: those 10 live in exactly three files and NO other
test file in the tree carries a bare `"python3"` spawn. F-4 is right in both halves: `run_cli` builds
`[sys.executable, "-m", "agent_workflows", *cli_args]` with no submodule hook, and `aw comms` really is
an invalid choice, so `agent_workflows.comms_acks` genuinely is unreachable through the CLI and the
`module=` argument is the minimum needed. F-3 reproduces VERBATIM, both halves:
`python3 -m unittest tests.test_completion.CompletionInstallSubprocessTests` under a decoy gives
`Ran 1 test` / `FAILED (failures=1)`, and `tests/test_comms_acks.py` under pytest from the decoy's
directory gives `5 failed, 15 passed in 0.56s`. E-03's TestCase-class arithmetic is right too (0 in
`test_comms_acks` against 11/8/3/1/1 in the others), so its "unittest collects 0 tests there" is a
correct expectation rather than a hedge.

**THE PLAN EXCLUDED A SEVENTH FILE ON A PREMISE THAT IS FALSE, AND THE SITE IT MISSED IS THE WORST ONE
IN THE WHOLE SET.** F-5 said `test_driver_attestation_gate.py` and `test_oc_runipd.py` "pin `PYTHONPATH`
explicitly ... not defective, out of scope". I audited every `agent_workflows` spawn in both files by
AST, printing each call's `env=` argument rather than trusting the presence of a helper. `test_oc_runipd.py`
is clean: all 20 of its spawns pass an env, 12 via `_DRIVER_ENV` and the rest via a local pinned `env`.
`test_driver_attestation_gate.py` has FIVE, and only FOUR use `self._env()`:
`CliNoTokenFlagTests.test_finalize_help_has_no_token_flag` passes no `env` and no `cwd` at all. So the
exclusion was a whole-file judgement applied to a file that is not uniform.

AND THE REASON IT MATTERS IS NOT THAT IT IS ONE MORE SITE. Its three assertions are
`assertNotIn("--driver-token"/"--driver-attest"/"--attestation", proc.stdout)`. I drove the spawn with
a decoy first on a cleaned `PYTHONPATH`: it returns rc 0 with stdout `DECOY`, and all three
`assertNotIn` checks are satisfied. Every one of the other 19 sites asserts something POSITIVE and
therefore goes RED when its child is hijacked, which is exactly how F-3 was measurable at all. This one
goes GREEN while testing nothing, so no test runner would ever surface it, and a reviewer reading only
the pass/fail record would never learn it had been hijacked. That is F-6, and it is now in scope with
its own before/after demonstration in E-05.

**E-02's CONVERSION SHORTCUT WOULD HAVE SILENTLY WEAKENED TWO TESTS.** The instruction said to convert
each spawn and "drop kwargs `run_cli` already defaults". `capture_output` and `text` are genuinely safe
to drop. `check` is not: `run_cli` uses `kwargs.setdefault("check", False)`, so omitting a previously
explicit `check=True` turns a raising spawn into a non-raising one whose return code nothing inspects.
Two sites in `tests/test_records_untracked_backend.py` (the `install --help` and `migrate-layout --help`
pair) pass `check=True` today. I verified both directions of the behavior:
`run_cli("no-such-verb", check=True)` raises `CalledProcessError`, and `run_cli("no-such-verb")` returns
rc 2 silently. So the pass-through works and the hazard is purely the instruction to drop it. That is
F-7, and E-03 now names both sites and forbids it.

**THE EXPOSURE CLAIM WAS UNIFORM AND THE REALITY IS NOT, WHICH CHANGES WHAT THE FIX IS FOR.** The
Concern said the child "resolves `agent_workflows` from whatever is first on its path", implying all 19
sites are live defects. CWD PRECEDES `PYTHONPATH` on `sys.path`, and 12 of the 19 already pass
`cwd=<repo root>`. I measured all three classes against a decoy on a cleaned `PYTHONPATH`: with
`cwd=<repo root>` the child imports the REPO's package; with cwd a temp dir holding no
`agent_workflows/` it imports the DECOY (this is `test_completion`'s 2 sites, and it is precisely F-3's
unittest failure); with no `cwd=` it inherits the test process's (this is `test_comms_acks`' 5, and it
is why F-3's second reproduction had to run pytest FROM the decoy directory rather than merely setting
`PYTHONPATH`). So 5 + 2 are live-exposed and 12 are defence in depth against a future cwd change or a
`-P` child. The fix is unchanged and still correct; I corrected the claim, not the work. That is F-8.

A METHOD NOTE I AM RECORDING BECAUSE IT NEARLY MISLED ME TWICE. First, my own initial AST census used
the shape E-02 prescribed (a list or tuple LITERAL containing the adjacent constants `"-m"` and
`"agent_workflows..."`) and found only 13 of the 19 sites: it missed all six in `test_project_context.py`
and `test_project_registry.py`, which assign `cmd = ["python3", "-m", ...]` first and then call
`subprocess.run(cmd, ...)`. E-02 now requires the scan to map argv-list assignments to their variable
names. Second, my first decoy attempt appeared to show the defect NOT reproducing, purely because the
invoking shell already exported a `PYTHONPATH` whose earlier entry answered ahead of the decoy; a repro
that leaves the ambient value in place proves nothing in either direction. E-05 and the gate now say to
clear it first, because an executor hitting that would plausibly conclude the bug is gone.

ON WHAT THIS PLAN RISKS. It touches only test harness code and one documentation sentence, so nothing
shipped can regress and the failure mode is one-directional: a weakened test. That is also why the suite
is nearly worthless as evidence here, and I said so in three places. The defect is invisible under
pytest by construction (`conftest.py` pins `PYTHONPATH`), one affected site passes even when fully
hijacked, and a dropped `check=True` is invisible until something exits nonzero. Reporting a green suite
as if it settled this is the most plausible honest-looking mistake available. I also checked the sibling:
`yx9xsa` (testhyg Order 01) declares `conftest.py` and `tests/test_ipd_lifecycle_cli.py`, so there is no
file overlap with this plan, and the Scope check now tells an executor to leave `conftest.py` alone.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | HIGH | UNDER-SCOPE | D. anti-regression; E. testing | per-call AST audit: `test_oc_runipd.py` 20/20 spawns pass an env; `test_driver_attestation_gate.py` has 5, of which 4 use `self._env()` and `CliNoTokenFlagTests.test_finalize_help_has_no_token_flag` passes NO env and NO cwd | **A SEVENTH FILE WAS EXCLUDED ON A FALSE WHOLE-FILE PREMISE.** F-5 declared both files pinned and out of scope; one of them is not uniform. The excluded site is an unpinned spawn of exactly the shape the plan exists to fix. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | `tests/test_driver_attestation_gate.py` added to `- Scope-Paths:` and to Scope (20 sites, seven files); E-03 converts it; F-5 rewritten to state the 4-of-5 split and that `test_oc_runipd` was VERIFIED clean rather than assumed; the deferred row narrowed so it no longer covers this spawn. |
| PR-802 | HIGH | IN-SCOPE | E. testing (a test that cannot fail) | driven with a decoy on a cleaned `PYTHONPATH`: the spawn returns rc 0 with stdout `DECOY`, and all three `assertNotIn("--driver-token"/"--driver-attest"/"--attestation", stdout)` hold | **THAT SITE FAILS SILENTLY GREEN, UNLIKE ALL 19 OTHERS.** Its assertions are NEGATIVE, so a hijacked child satisfies them vacuously; every other site asserts something positive and goes red, which is how F-3 was measurable. No runner would ever report this one, so it is the least visible and most valuable member of the set. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as F-6 with the measurement; E-05 requires a before/after demonstration of THIS site specifically (stdout `DECOY` with the test still PASSING, then the real usage block), and V-05 names that pair the load-bearing half of the validation. |
| PR-803 | HIGH | IN-SCOPE | A. correctness (a silent semantic change) | `run_cli` body: `kwargs.setdefault("check", False)`; `tests/test_records_untracked_backend.py` `install --help` and `migrate-layout --help` both pass `check=True`; driven: `run_cli("no-such-verb", check=True)` raises `CalledProcessError`, `run_cli("no-such-verb")` returns rc 2 silently | **"DROP KWARGS `run_cli` ALREADY DEFAULTS" WOULD CONVERT TWO RAISING SPAWNS INTO NON-RAISING ONES.** `capture_output`/`text` are safe to drop; `check` is not, because the helper's default is the OPPOSITE of the explicit value at those two sites, and nothing downstream inspects the return code. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 names both sites, forbids dropping `check`, records that the helper honors a passed-through `check=True`, and states which kwargs ARE safe to drop and why. V-03 requires the post-conversion source showing `check=True` still present, and says dropping it is a failed validation even with a green suite. Recorded as F-7. |
| PR-804 | MEDIUM | IN-SCOPE | A. correctness (an overstated premise) | with a decoy on a cleaned `PYTHONPATH`: `cwd=<repo root>` -> repo's `__init__.py`; `cwd=<temp dir>` -> decoy's; `cwd=<decoy dir>` -> decoy's. 12 of 19 sites pass `cwd=<repo root>` | **THE 19 SITES ARE NOT EQUALLY EXPOSED, THOUGH THE CONCERN IMPLIED THEY WERE.** CWD outranks `PYTHONPATH`, so 12 sites are protected today and the pin there is defence in depth; the live-exposed ones are `test_completion`'s 2 (cwd is a temp target repo) and `test_comms_acks`' 5 (no cwd, so inherited). Left unstated, the plan claims more than it fixes, and F-3's second repro looks like a `PYTHONPATH` result when it is actually a cwd result. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The Concern now states the three exposure classes with the measurement and says the value claim is corrected rather than withdrawn; Step 0 records the cwd-precedence rule; added as F-8. |
| PR-805 | MEDIUM | IN-SCOPE | E. verification (a census that misses sites) | my own literal-only AST scan found 13 of 19, missing all six variable-assigned argv sites in `test_project_context.py` and `test_project_registry.py` (`cmd = ["python3", "-m", ...]` then `subprocess.run(cmd, ...)`) | **THE PRESCRIBED SCAN SHAPE CANNOT SEE A THIRD OF THE SITES.** E-02 specified a scan for a list/tuple LITERAL containing the adjacent constants; six of the plan's own sites do not match that shape. An executor following the instruction literally would report 13 and, since 13 < 19, might treat the difference as already-fixed work. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 rewritten as its own item requiring the scan to also map argv-list ASSIGNMENTS to their variable names and to record the per-site `cwd=`/`env=` triple; its Expected outcome states the 20-site breakdown per file and declares a 13 or 19 result a FAILED E-02 rather than a number to accept. V-02 mirrors it. |
| PR-806 | MEDIUM | IN-SCOPE | E. verification (a repro that can mislead) | review's first decoy attempt showed the defect apparently absent; cause was an ambient `PYTHONPATH` carrying two entries, the first of which held an `agent_workflows` package and answered ahead of the decoy | **A DECOY REPRO THAT DOES NOT CLEAR THE AMBIENT `PYTHONPATH` PROVES NOTHING IN EITHER DIRECTION,** and the plausible wrong conclusion is that the bug does not exist. The authored E-04 gave the `PYTHONPATH=<decoy>` command without saying the variable must be SET rather than prepended to. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 requires clearing `PYTHONPATH` and setting it to the decoy directory ALONE, with the measured masking recorded as the reason; V-05 requires pasting the command that shows it; the gate carries it as a STOP condition so a non-reproducing before-state is investigated rather than believed. Step 0 records it too. |
| PR-807 | MEDIUM | IN-SCOPE | E. verification (evidence that does not support its claim) | pytest's `conftest.py` already pins `PYTHONPATH`; F-6's site passes when hijacked; a dropped `check=True` is invisible until a nonzero exit | **A GREEN SUITE IS NEARLY MEANINGLESS ON THIS PLAN AND THE PLAN LEANED ON IT.** All three of the defects this plan addresses are invisible to a bare pytest run, so "bare suite green" is a no-regression check and not evidence the fix works. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | An explicit limit added to Required tests and to the gate's honesty rule, each naming V-05's decoy pair and V-03's `check=True` proof as the load-bearing evidence instead. |
| PR-808 | LOW | IN-SCOPE | F. honest documentation; C. architecture | `tests/__init__.py` provides a home sandbox under unittest; `conftest.py` is what carries the pin and role scrub; `yx9xsa` declares `conftest.py`; the "HOW TO RUN THE SUITE" phrase occurs once in `engine.py` and once in `AGENTS.md` | E-05's proposed sentence said unittest loses "its role scrub, home sandbox and `PYTHONPATH` pin", but the home sandbox survives (it is in `tests/__init__.py`, not `conftest.py`), so the sentence would have shipped a false statement in user-facing prose. Separately, an executor tempted to fix this in `conftest.py` would collide with the sibling plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 rewritten to name only what unittest actually loses, with an explicit wording constraint against the home-sandbox claim and the no-dashes rule; V-06 checks both. Scope check forbids editing `conftest.py`/`tests/__init__.py` and names `yx9xsa` as the owner of the former; the generated-`AGENTS.md` reason is recorded as verified. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | One unpinned spawn sits in a file the plan excluded (PR-801/802). Add the file, or file a follow-up? | ADD IT to this plan: one call site, identical fix, and it is the highest-value member of the set. | (a) Follow-up backlog item: rejected, it is the same defect found in the same sweep, and shipping a plan whose stated goal is "every unpinned spawn" while knowingly leaving one is the incompleteness pattern this repository has ruled against before. (b) Convert ALL five spawns in that file for uniformity: rejected, the other four are correctly pinned and churn without an outcome change is what the plan's own deferred row declines. (c) Leave it and note it: rejected, its assertions pass vacuously when hijacked, so "noted" means nothing will ever surface it. | Per-call AST audit of both excluded files; the decoy run showing rc 0 / stdout `DECOY` with all three `assertNotIn` assertions satisfied. | yes |
| D-2 | `check=True` at two sites (PR-803). Preserve it, or accept `run_cli`'s default? | PRESERVE IT explicitly. | (a) Accept the default and rely on later assertions: rejected, neither site inspects the return code, so a nonzero exit would surface only as a confusing `assertIn` failure on empty stdout, or not at all. (b) Change `run_cli`'s default to `check=True`: rejected, it is a shared helper with many existing callers that rely on inspecting `returncode`, and flipping a default under them is far riskier than typing one kwarg. | `run_cli`'s `kwargs.setdefault("check", False)`; driven both branches; the two call sites' surrounding assertions read `assertIn(..., res.stdout)` only. | yes |
| D-3 | 12 sites are already protected by cwd (PR-804). Narrow the plan to the 7 live ones, or keep all 20? | KEEP ALL 20 and correct the CLAIM. | (a) Narrow to the live-exposed 7: rejected, the protection is incidental (it depends on a cwd that a future edit may change, and a `-P`/`PYTHONSAFEPATH` child strips cwd from `sys.path` entirely), and leaving 12 sites spawning raw preserves the pattern the next author copies. (b) Leave the uniform claim: rejected, it overstates what the fix repairs, and the honest version costs three sentences. | Measured all three cwd classes against a decoy; `-P` strips the cwd entry (measured on a separate occasion in this same repository's rehearsal work). | yes |
| D-4 | The prescribed census misses six sites (PR-805). Widen the scan, or list the sites? | WIDEN THE SCAN and state the expected per-file breakdown as a bar. | (a) Just list the 20 sites in the plan: rejected, a hand list rots and gives the executor no way to detect a site added between authoring and execution; the point of a census is that it re-derives. (b) Keep the literal-only scan and accept 13: rejected, six real sites would go unfixed while the item reported success. | My literal-only scan returned 13; the widened one returned 19 plus the attestation-gate site; the six missed sites all use `cmd = [...]` then `run(cmd, ...)`. | yes |
| D-5 | The ambient `PYTHONPATH` masked the repro (PR-806). Note it, or make it a stop condition? | BOTH: record the mechanism in Step 0 and E-05, and make a non-reproducing before-state a STOP condition. | (a) Note it only: rejected, the failure mode is an executor concluding the defect does not exist and either skipping the fix or reporting a false "already fixed"; that deserves a stop, not a footnote. (b) Say nothing, since the authored command is technically correct: rejected, `PYTHONPATH=<decoy>` in a shell that already exports one is ambiguous about whether it replaces or prepends, and it bit this review. | Measured: with the ambient value present the decoy lost; with `PYTHONPATH` set to the decoy alone it won and printed `DECOY`. | yes |
| D-6 | The proposed CONTRIBUTING sentence claims unittest loses the home sandbox (PR-808). Correct it, or drop the clause? | CORRECT IT: name only `conftest.py`'s role scrub and `PYTHONPATH` pin. | (a) Drop the whole sentence: rejected, the documentation gap is real and the maintainer asked for it to be considered; a reader choosing `make test-serial` should know what it does not load. (b) Keep the home-sandbox clause: rejected, it is false (`tests/__init__.py` provides it under unittest) and it would ship a wrong statement into user-facing prose, which P2 forbids. | `tests/__init__.py` provides the home sandbox; `conftest.py` carries the `PYTHONPATH` pin and the role scrub. | yes |

### Deferred and open

- (none). All eight findings were FIXED in place. None reached Medium-High or High Remediation Risk
  (every repair was a plan-text change verifiable by measurement, and the three HIGH-severity ones were
  fixed by ADDING one call site, one prohibition and one demonstration rather than by reducing scope), so
  the Fix Bar permitted no deferral. Because nothing was left `OPEN` or `DEFERRED`, no escalation to a
  `- Blocking: yes` question was required.
- The single authored open question (OQ-01, "tell agents never to use unittest?") was re-verified rather
  than accepted: `AGENTS.md`'s managed paragraph does direct a bare `python3 -m pytest`, and
  `make test-serial` is a real target (`python3 -m unittest discover -s tests -t .`) documented in
  `CONTRIBUTING.md` as a minimal-environment and isolation-debugging fallback. Its resolution stands.
- Both `Carrier-Declined` rows were checked against the tooling: `check_engine.evaluate_durable_carrier`
  returns `[]`, so no obligation is uncarried. One row's SCOPE was too broad (it declined converting
  "the two explicitly pinned files", which would have covered the unpinned spawn PR-801 found) and was
  narrowed; the declination itself stands for the genuinely pinned spawns.
- No `Reversible: no` decision was made. All six decisions are plan-text choices on an unexecuted plan.

HONEST LIMITS, stated because they bound what this round proves. FIRST, I executed no part of the plan:
`support.pinned_env` does not exist and no spawn was converted, so my confidence that `run_cli` can
carry these 20 sites rests on driving the CURRENT helper (including `module=`'s target, which I ran as a
raw pinned spawn rather than through the not-yet-written parameter). SECOND, my exposure analysis used a
decoy package that prints and exits; a real hijack by a genuine older checkout could behave differently
at each site, so F-8's three classes describe import RESOLUTION and not per-test outcomes. THIRD, I
audited `test_oc_runipd.py` for the presence of an `env=` argument on each spawn, not for whether every
one of those env values actually contains `REPO_ROOT`; 12 demonstrably do (`_DRIVER_ENV`), and for the
other 8 I confirmed only that an env is passed. FOURTH, I did not run the six (now seven) files under
`unittest` to confirm they pass there TODAY, so E-04's before-state is unmeasured by me. FIFTH, the
suite baseline I recorded is from this lane at this HEAD in a shared checkout, so it will differ at
execution; it is offered as a comparison point, not as a bar.
