# Review findings: plan zx9dkq

- Subject-Id: zx9dkq
- Subject-Type: ipd
- Reviewed-At: 2026-09-18
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `481465ac` in an isolated review lane, with the plan byte-identical to the lane input
(`diff -q` clean), so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author`
CONFORMED (exit 0) before revision and after.

THE DEFECT IS REAL AND REPRODUCES EXACTLY AS DESCRIBED. I ran the plan's own E-01 measurement rather than
taking it on trust:

```text
home-tree root  root=/home/<...>/agent-workflows/...   findings=2 severities=['fail']
     rules: ['handle', 'home-path']
temp-dir root   root=/tmp/aw-probe-ye_0p_9n            findings=0 severities=[]
     rules: []
```

And the per-test outcome with a synthetic outside-home root matches the plan's "two tests FAIL" claim
precisely:

```text
test_the_produced_bundle_is_clean         : findings=0 -> PASS
test_the_CONTROL_proves...                : findings=0 -> FAIL
test_a_leaky_value_travelling_through...  : findings=0 -> FAIL
```

The code description is accurate (`setUp` at `tests/test_run_analytics_spa.py:1144-1149`, the planted
`f"{self.repo}/.aw/worktrees/lane-x"` at `:1160` and `:1174`), the class docstring quote is verbatim
(`:1137-1142`), F4's warning against tolerating zero findings is exactly right, and the deferrals (do not
touch `leak_sanitizer`'s rules, do not sweep every `Path(__file__)` fixture) are well-judged. This is a
careful plan about a small real problem.

BUT ITS ROOT-CAUSE STATEMENT IS WRONG IN A WAY THAT MISDIRECTS THE FIX, which is the main finding. Both the
Concern and F1 say the planted leak and the DETECTOR are "derived from the same value", i.e. that
`build_ruleset(self.repo)` is half the coupling. It is not. Measured:

```text
two temp roots -> same fail rule NAMES: True
repo root fail rule names : ['handle','home-path','other-account','private-repo','session-id','users-path','vc-home','windows-home']
temp root fail rule names : ['handle','home-path','other-account','private-repo','session-id','users-path','vc-home','windows-home']
difference (repo-only rules): []

tmp ruleset  on a home-style string : 1 finding
repo ruleset on a temp-style string : 0 findings
```

`build_ruleset(repo_root)` uses `repo_root` only to load an optional repo allowlist/config
(`leak_sanitizer.py:441-478`); the leak patterns are HARDCODED regexes (`:65-84`), with `home-path` matching a real account name under `/home`. So the ruleset is location-INDEPENDENT and only the
PLANTED VALUE varies. That matters because an executor reading "the detector is derived from the same value"
could reasonably aim at the ruleset construction, which would fix nothing while looking like progress.

THE PLAN'S PREFERRED REMEDY IS CORRECT, AND I CONFIRMED IT WORKS AND FOUND THE TRAP IN IT. A synthetic
home-style plant does detect identically everywhere:

```text
                                                                  home-ruleset   temp-ruleset
/home/user/checkouts/agent-workflows/.aw/worktrees/lane-x            1 fail          1 fail
/Users/<user>/checkouts/agent-workflows/.aw/worktrees/lane-x         1 fail          1 fail
<Path.home()>/synthetic-checkout/.aw/worktrees/lane-x                2 fail          2 fail
```

The third row is the trap: a `Path.home()`-derived plant passes HERE only because this machine's home is
under `/home` (and it picks up the extra `handle` match for the same reason). On a macOS home, or in a container
with `HOME=/root`, it would not match `home-path` and the test would fail again, differently coupled. The
plan said "synthetic home-style root" without excluding the `Path.home()` form, so E-03 now requires a FIXED
LITERAL and V-03 refuses a home-derived one.

TWO SMALLER THINGS THE PLAN GOT WRONG ABOUT ITS OWN SCOPE. `test_the_produced_bundle_is_clean` is NOT part
of this defect: it references no `self.repo` (only `self.ruleset`) and already passes outside the home tree,
as the three-test simulation above shows. The plan speaks of "these tests" and "both tests" interchangeably
across three tests and asks E-02 to assign a reading to all three, which invites editing a passing test that
carries the shipped sanitizer-clean guarantee. And the non-vacuity pairing the class docstring relies on is
ALREADY split across two test methods, so with `pytest-randomly` active and `-k` available it was breakable
even inside the home tree; E-04's "in the same test run" instinct is right and now requires one METHOD.

WHAT I FIXED. Concern and F1 restated with the correct mechanism and the measurement; new F6 (the ruleset is
not the variable), F7 (the clean test is unaffected, with the PASS/FAIL/FAIL evidence), F8 (the pairing is
already split across methods). E-01 gained a mandatory part (b) localizing the cause to the planted value.
E-02 must record that the clean test needs no change. E-03 requires a fixed literal, with the three measured
candidate rows and the macOS/container reasoning, and is told to leave the clean test alone. E-04 requires
one method and an assertion on the RULE NAME and severity rather than a bare nonzero count. V-01..V-04
tightened to match, each refusing the specific weak evidence that would otherwise satisfy it. Required tests
gained the bare-run rule with the `770fkp` baseline, the measured before-state to flip, an
environment-free-plant check, and a mutation check. OQ-01 narrowed (no skip applies to these three tests).
Scope check records the over-scope risk; the gate now names three must-nots; spec-sync records that the
shipped guarantee is preserved because its test is untouched.

WHAT I DID NOT DO. I changed no code, test or spec; my probe script was throwaway and is deleted. I did not
answer OQ-01's residual question about a future test that genuinely asserts something about the live root.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. correctness (a root cause that misdirects the fix) | `leak_sanitizer.py:441-478` vs `:65-84`; measured identical eight fail-rule names for a repo root and a temp root with an EMPTY difference; temp-root ruleset flagging a home-style string (1 finding) while the repo-root ruleset finds 0 in a temp-style string | **THE STATED ROOT CAUSE IS WRONG.** The Concern and F1 say the planted leak and the DETECTOR are both derived from `self.repo`, so they "agree vacuously". The ruleset is in fact location-INDEPENDENT: `repo_root` only selects an optional allowlist/config and the leak patterns are hardcoded regexes. Only the PLANTED VALUE varies. An executor could aim the fix at the ruleset construction and change nothing. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Concern and F1 restated with the measurement; new F6 records the localization; E-01 gains a MANDATORY part (b) proving the ruleset is not the variable (identical rule names plus the temp-root ruleset flagging a home-style string), and V-01 refuses the item without it. The plan's remedy direction was already right, so only the explanation and the proof obligation changed. |
| PR-002 | HIGH | IN-SCOPE | A. correctness (the prescribed remedy has an unexcluded wrong form) | measured: a home-style and a macOS-style placeholder path each 1 `fail` under BOTH rulesets; `<Path.home()>/...` 2 `fail` under both but only because this machine's home is `/home/<name>`; `home-path` matching a real account name under `/home` | **"SYNTHETIC HOME-STYLE ROOT" DOES NOT EXCLUDE A `Path.home()`-DERIVED PLANT,** which would pass here and fail on a macOS home or in a container (`HOME=/root`), reintroducing the same class of coupling in a form that looks fixed. The plan never says the plant must be environment-free. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now requires a FIXED LITERAL, carries the three measured rows and the macOS/container reasoning, and V-03 requires the planted value be quoted and shown to contain no `Path.home()`, `$HOME`, or checkout-derived component, explicitly refusing a home-derived plant. The gate's must-not list carries it too. |
| PR-003 | MEDIUM | OVER-SCOPE | G. plan executability (a passing test invited into the change) | `test_the_produced_bundle_is_clean` references `self.ruleset` only, no `self.repo`; simulated outside-home run: that test PASS, other two FAIL | **ONE OF THE THREE TESTS IS NOT AFFECTED AND MUST NOT BE TOUCHED.** The plan says "these tests"/"both tests" interchangeably across three tests and asks E-02 to assign a reading and remedy to all three. That test also carries the shipped sanitizer-clean guarantee, so editing it is the one change with real downside. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F7 with the evidence; E-02 must RECORD that it needs no change (and V-02 refuses a statement that assigns it a remedy); E-03 says leave it alone; the gate's third must-not names it; the scope check records the risk; spec-sync now notes the shipped guarantee is preserved byte-for-byte because its test is untouched. |
| PR-004 | MEDIUM | UNDER-SCOPE | E. testing (the guard the plan adds is separable) | the control and the clean assertion are separate methods (`:1151`, `:1159`); `pytest-randomly` active via `addopts`; `-k` can select either alone | **THE NON-VACUITY PAIRING WAS ALREADY BREAKABLE, EVEN INSIDE THE HOME TREE.** The class docstring's "the control run is what makes the clean assertion evidence" holds only if both methods happen to run. E-04 said "in the same test run", which random ordering and `-k` do not guarantee. A guard whose halves can be separated is not a guard. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F8; E-04 now requires both halves WITHIN ONE TEST METHOD and additionally an assertion on the RULE NAME (`home-path`) and severity (`fail`) rather than a bare nonzero count, so a future change that starts matching for an unrelated reason cannot keep it green. V-04 refuses two separate green methods as evidence. |
| PR-005 | LOW | UNDER-SCOPE | E. testing (no proof the fixed test still detects) | the plan's validation set is all "shown passing" | Every validation item asked for a PASS. A fixed test that passes in both locations could still be asserting nothing detectable; nothing required showing it FAILS when it should. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required tests gained item 6, a deliberate mutation check: break the planted literal to a `/tmp/...` path and show the fixed test FAILS. Cheap, decisive, and the natural counterpart to F4's warning. |
| PR-006 | LOW | UNDER-SCOPE | E. testing (a false red baseline) | backlog `770fkp`; measured `31 failed, 7866 passed` bare in a lane this session | Required test 1 said "bare, pasted summary line, compared against the pre-execution baseline" with no note that a managed worker lane fails 31 lifecycle tests BY DESIGN, and no warning against adding flags (a second `-q` suppresses the summary the item requires). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required test 1 now states the bare-run rule with the reason, cites `770fkp`, and gates on NO NEW failures against a baseline taken in the same tree. Required test 3 also now states the measured PASS/FAIL/FAIL before-state so the after-state is comparable. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The stated root cause is wrong but the remedy direction is right. Rewrite the diagnosis, or leave it since the fix lands anyway? | REWRITE IT, and add a mandatory measurement (E-01b) that proves the localization. | (a) Leave it, rejected: the plan's own E-01 is framed as "the measurement that identifies the coupling as `self.repo` feeding both sides", so an executor would perform a measurement designed to confirm a false mechanism and could aim the fix at `build_ruleset`. (b) Escalate as a blocking question, rejected: the code determines the answer unambiguously, so asking would stall on something evidence settles. | `leak_sanitizer.py:441-478` vs `:65-84`; identical rule names for two roots; the cross-scan | yes |
| D-2 | Is a `Path.home()`-derived plant acceptable, since it passes on this machine? | NO. Require a FIXED literal and refuse the home-derived form in V-03. | (a) Allow either, rejected on measurement: `home-path` matches `/home/<name>` specifically, so on macOS or with `HOME=/root` the home-derived plant stops matching and the test fails again, which is the very defect being fixed wearing a different hat. (b) Require a skip on non-`/home` platforms, rejected: it would make the assertion conditional when a fixed literal makes it unconditional and tests the same property. | the three measured candidate rows; the `home-path` regex; `users-path` being a separate rule | yes |
| D-3 | Should I decide OQ-01 (skip vs synthesize) outright? | PARTLY: narrow it to nothing this plan must decide, and leave the residual general question to the maintainer. | (a) Close it fully as resolved, rejected: the general question (a future test that genuinely asserts something about the live root) is a real judgement about what a test is FOR, and the plan is right that it recurs. (b) Leave it untouched, rejected: as written it implies a skip might be needed for one of THESE tests, and measurement shows neither of the two affected tests asserts anything about this repo's root, so a skip would be strictly worse than the synthetic plant. | F6's hardcoded-pattern evidence; the two tests' assertions read directly | yes |
| D-4 | Verdict, given no blocking question and one HIGH-severity diagnosis error? | `APPROVE WITH REVISIONS APPLIED`, readiness `go-pending-approval`. | (a) `REVIEWED - OPEN QUESTIONS`, rejected: nothing remains that needs a human answer; OQ-01 is non-blocking and its residual part does not gate this plan. (b) Leave `no-go`, rejected: the readiness table reserves NO-GO for a genuine not-ready condition, and after revision there is no open question, no unfixed BLOCKER or HIGH, and a correct verdict, which is exactly `GO - PENDING HUMAN APPROVAL`. | workflow verdict/readiness tables; all six findings FIXED | yes |

### Escalation of the irreversible decisions

None of this round's four decisions is `Reversible: no`: each is undone by editing the plan, and I changed no
code, test or spec. Nothing this plan does is irreversible either; its worst realistic failure is a test that
looks hermetic and is not, which PR-002's fixed-literal requirement and PR-005's mutation check are there to
catch. No escalation is required, and none is recorded.

### Honest limits of this review

- MY MEASUREMENTS COME FROM A PROBE SCRIPT I WROTE AND DELETED. The transcripts above are pasted verbatim
  from real runs in this lane, but a re-verifier must rebuild it. It did four things: scanned the planted
  shape against `build_ruleset` for a home-tree root and a temp root; compared the two rulesets' `fail` rule
  names; scanned three synthetic candidate plants against both rulesets; and imported the test module to
  simulate all three tests with a synthetic outside-home `self.repo`.
- I SIMULATED THE OUTSIDE-HOME FAILURE RATHER THAN CREATING A SECOND CHECKOUT. I substituted a temp-directory
  path for `self.repo` and re-ran each test's logic; I did not `git worktree add` outside `$HOME` and run
  `pytest` there, which is what the plan's own V-03 requires. So my PASS/FAIL/FAIL result is a faithful
  simulation of the assertion logic, not an observed suite run in a relocated checkout.
- I DID NOT RUN THE FULL SUITE. I changed no code. The `31 failed, 7866 passed, 3 skipped, 2 xfailed`
  baseline I cite for PR-006 was measured earlier in this session at a nearby HEAD; the counts at THIS HEAD
  are unverified by me, which is why the plan now requires the executor to take its own baseline.
- I DID NOT TEST ON macOS OR IN A CONTAINER. PR-002's claim that a `Path.home()`-derived plant would fail
  there is read from the `home-path` and `users-path` regexes plus the fact that `Path.home()` returns a
  `/Users`-rooted path on macOS; I verified the regexes and the measured behavior on this Linux machine only.
- I DID NOT VERIFY F3's INCIDENT NARRATIVE. The claim that this cost a false alarm mid-merge while resolving
  the `tx6q0h` lane is the author's session experience and is not reconstructible from the repository. What I
  could verify is that the failure it describes is real and occurs exactly as stated.
- I DID NOT AUDIT OTHER `Path(__file__)`-DERIVED FIXTURES, which the plan defers and asks E-01 to note
  opportunistically. I looked at this module only, so F5's "re-verify rather than assume" remains open work.
