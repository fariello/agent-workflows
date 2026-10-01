# Review findings: plan bjx20r

- Subject-Id: bjx20r
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-301 (HIGH, fixed), PR-302 (MEDIUM, fixed), PR-303 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `baf4a24d`. The plan file was committed and byte-identical to
the lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review, and
`--phase review-finalize` reports `clean` with zero findings after revision. The plan's own first `- Kind:`
bullet reads `child`, so the `IPD-S407` orchestrator row check does not apply.

THIS IS AN UNUSUALLY WELL-EVIDENCED PLAN AND I RE-DROVE EVERY FINDING RATHER THAN READING THEM. All eight
authored findings reproduce:

- F-1's three non-resolving citations are all three confirmed: `check_verifier_evidence`, `HonestyTests` /
  `test_a_plausible_but_unrun_command_is_accepted_which_is_the_known_gap`, and the string
  `DO NOT DESCRIBE THIS PREDICATE AS FABRICATION-PROOF` each return zero matches. The real predicate is
  `runner_shared.has_verifier_test_evidence` and the real comment block is headed
  `RESIDUAL WEAKNESS / SCOPE BOUNDARY (honestly stated)`, which quotes verbatim including
  "proves ACTIVITY ... not correctness or proof of non-fabrication".
- F-3 reproduces exactly: `attempt["verify_log"] = str(_v_log)` in `runner_shared`,
  `attempt_log_path(run_dir, item, attempt_no, suffix="")`, and seven modules referencing `verify_log`
  (the six the plan names plus `runner_shared` itself).
- F-4 reproduces, including the detail that makes a new module necessary rather than a refactor:
  `run_dashboard._record_tool` does `_bump(stats["commands"], command_kind(command))`, keeping only the
  kind and discarding the command text. The per-host keys are exactly as cited
  (`inp.get("command") if name == "bash"`; `params.get("CommandLine") if name == "run_command"`), as is
  the `session_stats` host discriminator (`if "event" in obj` / `elif "type" in obj and "part" in obj`).
- F-6 reproduces verbatim with all four reasons and the sentence that "must not be 'improved' away".
- F-7's three spec strings all resolve in `25kzda` (admissible "hash-bound argv-list tool events...",
  inadmissible "tests pass," agent prose and "a verifier's opinion", and Section 4.2's closing sentence).
- F-8's three-step fallback is implemented exactly as described in `run_viewer.extract_step_usage`
  (recorded path re-rooted, then `{pos:02d}-{id6}-attempt-{n}-verify.jsonl`, then the glob).
- The convention claims check out too: `VALIDATION_RESULTS` is
  `frozenset(("pending", "pass", "blocked", "failed"))` so `pass` is right and `verified` would be
  rejected; `.aw/records/runs/` is gitignored with zero tracked files and is absent from this lane;
  `leak_sanitizer`'s `session-id` rule is `\bses_(?!<redacted>)[0-9A-Za-z]{8,}`, allowing exactly the
  redacted form.

THE DOMINANT FINDING IS A SELF-INCONSISTENCY THAT WOULD HAVE SHIPPED THE PLAN'S OWN NAMED FAILURE MODE,
and it is the kind only a pre-execution read catches, because the plan's prose and its checklist disagree
while each is internally coherent. F-5 is the plan's best finding: it enumerates FOUR independent
mechanisms by which a genuine test run becomes invisible or unmatchable, and correctly concludes that a
naive matcher would be "a false-accusation engine". But E-03's "at minimum it must survive" list covers
only three of them (whitespace, truncation, prose-wrapping, plus chaining), and its six-case fixture table
covers the same three plus delegation. Mechanism (b), INDIRECTION, appears in F-5 and then vanishes from
every item that implements it, including F-5's own consequence column.

I demonstrated the consequence rather than asserting it, by implementing E-03's specified matcher
(containment in either direction, plus chained-segment splitting on `&&`/`;`/`|`) and running it over all
four mechanisms:

```
exact        -> MATCH
truncated    -> MATCH
prose        -> MATCH
chained      -> MATCH
INDIRECTION  -> NO MATCH
```

Indirection is unreachable by string tolerance in principle, not by oversight in my implementation:
`make test` and `python3 -m pytest tests/` share no substring in either direction, and neither is a
segment of the other. Then, under the authored E-04, such a turn satisfies every condition for the
`uncorroborated` arm (log read successfully, at least one observed shell command, no delegation, no claim
matched), so it yields a confident accusation of fabrication against a verifier that genuinely ran the
suite. That is precisely the outcome E-04's own design paragraph says must never occur ("A false
`uncorroborated` is an accusation of fabrication against an honest verifier").

The case is live in this repository, not theoretical: `Makefile`'s `test:` target body is
`python3 -m pytest tests/`; `runner_shared.VERIFY_COMMAND_PREFIXES` contains `make`, so `make test` is an
ACCEPTED claim string; and `run_dashboard._COMMAND_KINDS` matches `make\s+test` as a `test` kind, i.e. the
tree already treats it as a test invocation. A verifier that claims `python3 -m pytest tests/` and runs
`make test`, or vice versa, is behaving exactly as the repository invites.

THE FIX IS DELIBERATELY NOT A SMARTER STRING RULE. I specified a declared, commented, known-incomplete
indirection set (`make test`, `make test-all`) plus an explicit prohibition on parsing the `Makefile` to
resolve targets, because that would couple a session-log reader to build-file syntax for two entries of
benefit. The general case then needs somewhere safe to land, so E-04 gains a SIXTH `indeterminate`
condition, `indirection-unresolved`, for an observed command whose first token is a verify prefix but
which names no resolvable test target. That keeps the plan's central asymmetry intact: every unknown
resolves to `indeterminate`, never to `uncorroborated`.

I ALSO CORRECTED A SCOPE-FENCE WORDING PROBLEM THE REPOSITORY HAS RULED ON. Both the gate and the Scope
check instructed the executor to `STOP AND REPORT` rather than broaden scope. The 2026-09-01 maintainer
ruling is explicit that a fence is a DECLARATION so the runner can reconcile afterwards, and that a plan
carrying a stop directive for an out-of-scope EDIT is itself a finding, because that wording propagated
into 224 executed plans and works against the effort to stop runs stranding unfinished turns. The correct
requirement is make-it-and-justify-it, which `aw ipd finalize` already enforces via `--scope-reason`. I was
careful to PRESERVE this plan's two legitimate stop conditions, which are a different case and remain
correct: stop if the work appears to require a refusal or downgrade (a settled ruling, F-6), and stop if a
prerequisite symbol is absent.

OQ-01 IS LEFT OPEN AND THAT IS THE RIGHT ANSWER, which I record because a reviewer is normally obliged to
resolve what the repository can answer. This one the repository cannot: the question asks for a
corpus-measured false-negative rate, that number is produced only by executing E-06, and this lane has no
corpus (`.aw/records/runs/` is gitignored, zero tracked files, absent here, all verified). Resolving it
would mean inventing the measurement the plan explicitly forbids inventing. `- Blocking: no` is also
correct rather than a mislabel, since this plan ships no consumer of the verdict. I added a reviewer note
recording that reasoning and flagging for Order 09's reviewer that a zero-row table is the EXPECTED lane
outcome and must be treated as an open risk, not a satisfied gate.

TWO THINGS I CHECKED AND DID NOT FLAG. First, the shared `tests/test_verifier_corroboration.py` in both
this plan's and `btak7a`'s `- Scope-Paths:` is not a collision: `btak7a` declares
`- Item-Dependencies: executed:bjx20r`, so the order is enforced, and the runner isolates each item
anyway. Second, this plan touching no runner module while its sibling touches `runner_shared` is exactly
the split the plan claims it is, and it is what makes this half reviewable without reasoning about either
host's control flow.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | HIGH | IN-SCOPE | Rubric A/D/F (correctness, anti-regression, prevent silent failure) | Plan F-5 (four mechanisms) vs E-03's tolerance list and six-case table and E-04's `uncorroborated` conditions; `Makefile` `test:` body `python3 -m pytest tests/`; `runner_shared.VERIFY_COMMAND_PREFIXES` contains `make`; `run_dashboard._COMMAND_KINDS` matches `make\s+test` as `test`; matcher demonstration at review (exact/truncated/prose/chained MATCH, indirection NO MATCH) | F-5 names FOUR false-negative mechanisms; E-03 handles only three. Indirection (F-5(b)) is unreachable by every listed tolerance, because `make test` and `python3 -m pytest tests/` share no substring in either direction and neither is a chained segment of the other. Under the authored E-04 that turn satisfies every `uncorroborated` condition, so the module would emit a confident false accusation of fabrication against an honest verifier - the exact outcome E-04's own design paragraph forbids, and the failure the plan's three-state design exists to prevent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 gains a DECLARED known-incomplete indirection set (`make test`, `make test-all`) with an explicit prohibition on parsing the `Makefile`, and its fixture table grows to seven cases including an indirected one that must not report no-match. E-04 gains a sixth `indeterminate` condition `indirection-unresolved` so the general case fails open. V-03 requires the `Makefile` body and the declared set be pasted; V-04 requires six distinct reason codes. New finding F-9 records the demonstration; F-5's consequence column corrected to admit the omission. |
| PR-302 | MEDIUM | IN-SCOPE | Rubric G (execution contract), 2026-09-01 maintainer ruling on scope-fence wording | Plan gate ("keep every change inside the declared Scope-Paths and STOP AND REPORT rather than broadening them") and Scope check ("the correct response is to STOP AND REPORT rather than broaden") | Both places instruct the executor to STOP over a scope question. The maintainer ruled a fence is a DECLARATION for after-the-fact reconciliation and that a stop directive for an out-of-scope EDIT is a finding to fix, because that wording propagated into 224 executed plans and contradicts the work done to stop `aw oc run` stranding unfinished turns. The correct requirement is make-it-and-justify-it, which `aw ipd finalize` enforces with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both sites reworded to declaration-plus-justification with the ruling cited and the finalize flags named. The plan's TWO legitimate stop conditions are explicitly PRESERVED and distinguished as unsafe-condition stops rather than scope stops: a required refusal/downgrade (F-6) and an absent prerequisite symbol. |
| PR-303 | LOW | IN-SCOPE | Rubric E (measured claim accuracy) | Plan F-2 ("its 22 tests across seven classes"); `python3 -m pytest tests/test_verifier_evidence.py -o addopts=""` -> `15 passed`; `--collect-only -q` -> `15 tests collected` | F-2 states `tests/test_verifier_evidence.py` has 22 tests; it has 15. The seven class names are exact and the finding's SUBSTANCE is untouched (re-verified: no test in that file asserts the fabrication gap, so E-05's honesty pin is genuinely still owed). Material only because F-2 is the justification for a deliverable, so its numbers should be right. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-2 now omits the wrong count, records the measured `15 passed` / `15 tests collected` with the commands, and instructs re-derivation at execution rather than quoting either figure. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should F-5(b) indirection be handled, given string tolerance provably cannot reach it? | A declared, commented, known-incomplete indirection set (`make test`, `make test-all`) in E-03, PLUS a new `indirection-unresolved` `indeterminate` arm in E-04 for the general case. | (a) Parse the `Makefile` to resolve the target to its real command. REJECTED: couples a session-log reader to build-file syntax, and the set is two entries, so the coupling buys nothing. (b) Treat any observed command whose first token is in `VERIFY_COMMAND_PREFIXES` as corroborating any test claim. REJECTED: that makes `git status` corroborate a pytest claim (`git` is in the prefix tuple), hollowing the matcher into a near-tautology. (c) Leave it and accept the false `uncorroborated`. REJECTED: it is the one outcome the plan's own design forbids. | Demonstrated matcher run over all four F-5 mechanisms; `Makefile` `test:` body; `VERIFY_COMMAND_PREFIXES` membership of both `make` and `git`; `run_dashboard._COMMAND_KINDS` treating `make\s+test` as a test kind. | yes |
| D-2 | Should OQ-01 be resolved at review, as the workflow prefers? | No: left `open`, with a dated reviewer note recording why and a flag for Order 09's reviewer. | Resolve it by estimating the rate, or by declaring a fixture-only calibration sufficient. BOTH REJECTED: the answer is a measurement E-06 exists to produce, this lane has no corpus to produce it from, and the plan explicitly forbids inventing or extrapolating the number ("A fabricated or extrapolated rate here would be worse than an absent one"). A reviewer resolving it would be doing the thing the plan warns against. | `.aw/records/runs/` gitignored, zero tracked files, absent from this lane (all verified); E-06's own instruction; the question gates Order 09's review rather than this plan's execution, and this plan ships no consumer. | yes |
| D-3 | Is the shared `tests/test_verifier_corroboration.py` across this plan and `btak7a` a conflict to flag? | No. | Flag it as a co-edit hazard. REJECTED: `btak7a` declares `- Item-Dependencies: executed:bjx20r`, so the runner orders them by dependency depth and re-checks at dispatch, and each item executes in an isolated worktree merged through revalidation. Raising it would be a claim about runner behavior contradicted by the code. | `btak7a` front matter; the runner's documented ordering and isolation guarantees. | yes |
| D-4 | Is "no test touches an existing surface" an under-scope gap? | No. | Require a test of the shipped gate. REJECTED: the module has no importer until Order 09, so no existing test can observe it, and E-05's honesty pin already covers the one interaction with the shipped predicate (`has_verifier_test_evidence` accepts a fabricated claim that this module reports `uncorroborated`). | Plan's Under-scope row; F-2's measured absence of any fabrication-gap test; E-05's expected outcome. | yes |

No decision in this round is `Reversible: no`, so none requires escalation beyond this record. No finding
was left `OPEN` or `DEFERRED`, so no `- Blocking: yes` escalation is owed under the gate threshold. OQ-01
remains `open` and non-blocking, which per the 2026-09-10 maintainer ruling does not make the plan `NO-GO`.
