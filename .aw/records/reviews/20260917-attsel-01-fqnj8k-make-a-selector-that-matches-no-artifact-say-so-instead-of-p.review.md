# Review findings: plan fqnj8k

- Subject-Id: fqnj8k
- Subject-Type: ipd
- Reviewed-At: 2026-09-17
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `cf0ebf7a` in an isolated review lane. Structural preflight `aw ipd lint --phase author`
CONFORMED (exit 0) with one `IPD-Z602` density advisory on E-05, and `--phase review-finalize` CONFORMS
after revision with no advisory. No pre-review snapshot was needed: the plan was committed and
byte-identical to the lane input (`diff` -> IDENTICAL).

THE CENTRAL DEFECT IS REAL AND I REPRODUCED IT rather than reading it. At review HEAD, `aw att zzzzzz`
prints one blank line and exits 0; `aw att zzzzzz --agent` emits
`{"outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0}`. The cause is where the plan
says it is: `filter_items_by_selectors` (`attention.py:2635-2693`) returns a bare filtered list, so a
token that matched nothing is indistinguishable from one whose matches were removed downstream.

BUT THE PLAN'S OWN AMBIGUITY FIXTURE WAS WRONG, AND IT WAS THE SPECIFICATION FOR THREE ITEMS. The plan's
proof of ambiguity was `aw att sv0sf3` (a real parked backlog item) versus `aw att zzzzzz`, both "exit 0".
A selector FORCES `show_all` (`attention.py:3071`, with twins at `:2850` and `:2991`), so a named parked
artifact IS displayed:

```text
=== sv0sf3
## parked (1)
- [backlog] .aw/records/backlog/parked/20260829-reviewloc-01-sv0sf3-should-reviews-move-to-per-type-subdirs.backlog.md (parked)
EXIT=0
=== zzzzzz
(blank)
EXIT=0
```

Two lines versus one. So the "matched but hidden" case the plan built E-01, E-03 and V-01 around does not
exist, and an executor following the original text would have written a fixture that distinguished nothing.
The GENUINE matched-but-empty twin is a token that matches and is then removed by a DOWNSTREAM filter,
which I measured three ways: `aw att sv0sf3 -t plans`, `aw att sv0sf3 --status ready`, and
`aw att reviewloc -t plans` all print nothing and exit 0, exactly like `aw att zzzzzz`.

THAT CORRECTION BREAKS THE AUTHORED FIX SITE, which is the most consequential finding. E-03 instructed the
executor to compute per-token match facts INSIDE `filter_items_by_selectors`. But `--type` narrows `items`
BEFORE the call (`:2797-2799`, then `:2806-2808`), so the filter never receives the artifact the token
matched. Measured against the real scan:

```text
total scanned items: 1063
after -t plans: 661
filter over FULL scan  -> matches: 1
filter over -t narrowed -> matches: 0   <-- an in-filter match fact would say NO MATCH here
```

So the authored placement would have reported `aw att sv0sf3 -t plans` as a TYPO. That is precisely the
false-no-match outcome the plan's own execution contract calls "a WORSE defect than the one being fixed",
arriving through a route F4 never named. The match fact must be pinned to the UNFILTERED scan.

FIVE OUTPUT SURFACES WERE OUT OF SCOPE AND ALL ARE SILENT. The plan addressed the human board and
`--agent`. Measured with a nonexistent selector, every one of these also prints nothing and exits 0:
`--json`, `--format json`, `--check`, `-id`, `--paths`, `--filenames`. `--check` is the worst, since it
prints "aw attention --check: the view is valid." while having resolved nothing. A board-level message
reaches none of them: `--check` returns at `:2983` and the three list modes at `:3012`, both before the
board is composed. `--json` matters more than its flag count suggests: `.aw/system/workflows/whatnext/whatnext.md:50`
names `aw attention --format json` as `/whatnext`'s PRIMARY source, run FIRST, and its payload reports
`valid: true, items: []` for a typo.

A FAIL-CLOSED DEFAULT WOULD HAVE BROKEN LEGITIMATE QUERIES. `aw attention` accepts tree names, attention
classes and native statuses as selectors, and a repository can legitimately have none of a value. Measured
empty in this repo today: `abandoned`, `reusable`, `planned`, `roadmaps`, and `releases` as a tree token.
Exiting nonzero for "what is abandoned?" would be wrong, and the plan's unconditional fail-closed
instruction would have done exactly that.

AND THE REPOSITORY HAS ALREADY RULED ON OQ-01, which the plan did not know. Spec `25kzda`
(`Status: approved`) Section 2.3: "Zero matches return exit 2". Section 2.4a carves exactly one exemption,
for STATUS selectors, with the reasoning ("a standing question about repository state rather than an
assertion that a named item exists") and the closing "A misspelled id6 still exits 2; only the status
selectors are exempt". `aw runs` implements it (`aw runs zzzzzz` exits 2 on both surfaces, with
`unresolved_targets:["zzzzzz"]` in its record and the rule stated in its own help at `cli.py:2082`). The
counter-example is also live: `aw find plans zzzzzz` prints `✓ CLEAN  no matching plans` and exits 0. So
OQ-01 stays the maintainer's, but it is now a choice between two named conventions, and the vocabulary
exemption is agreed by BOTH.

F5 IS WITHDRAWN AND ITS FALSITY REMOVES AN ESCAPE HATCH. The plan warned that no honest agent record might
validate, and authorized the executor to "record it as a finding" instead. Two shapes validate:

```text
findings/exit1 errors: []
cannot-run/exit2 errors: []
clean/exit0 errors: []
```

and `aw runs` already ships the second for this exact condition. No schema change is authorized.

THE `TODO: Run /aw setup-repo` DEFERRAL RESTED ON A FALSE PREMISE. The plan called it a line printed
"unconditionally, including on successful calls in a fully-configured repo". It is gated on
`setup_needed(repo_root)` (`attention.py:1606`), which reads the marker `.aw/setup-repo-needed.md`. That
file is absent here, `setup_needed` returns False, and no `aw att` invocation in this review printed the
line. Re-scoped with the corrected diagnosis so it is not re-filed as a defect on a false premise.

WHAT I FIXED. Corrected the Concern's ambiguity proof with the measured `show_all` behavior and the real
downstream-filtered twin; added three measured facts to the Goal so the executor does not inherit the wrong
fixture; rewrote E-01 (corrected fixture, with an explicit reject condition), E-02 (both directions of the
resolve/match disagreement), E-03 (unfiltered-scan placement, existing contract preserved), E-04 (reuse
`term.format_empty_result`), E-05 (the `aw runs` precedent, no schema change), E-06 (the `25kzda`
precedent, the vocabulary exemption, drift composition); added E-07 (surface enumeration), E-08
(vocabulary), E-09 (`--json`/`/whatnext`), E-10 (`--check` and the list modes) with V-07..V-10; raised
`Highest E allocated` 06 -> 10; added `cli.py` to the fence for the `--help` contract and forbade editing
`attention_contract.py` (owned by approved plan `m867ox`); added F1a and F7..F12, withdrew F5 in place;
raised OQ-02 for the `--check` question; expanded Required tests from 6 to 12 items; and rewrote the
execution contract with the four facts an executor must not re-derive.

WHAT I DID NOT DO. I did not implement the fix. I did not decide either open question's policy: both ship
fail-closed and both are the maintainer's to relax. I did not touch the tracked-tree gap.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. correctness (the fix as authored ships the defect it forbids) | `attention.py:2797-2799` then `:2806-2808`; measured filter matches 1 over the full 1063-item scan and 0 over the `-t plans` 661-item scan | **THE AUTHORED FIX SITE COMPUTES A FALSE NO-MATCH.** E-03 put the match fact inside `filter_items_by_selectors`, but `--type` narrows `items` before the call, so the filter never sees the artifact a token matched. `aw att sv0sf3 -t plans` would have been reported as a typo, which the plan's own contract calls a worse defect than the bug. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | Added as F7. E-03 rewritten to pin the match fact to the UNFILTERED scan and to preserve `filter_items_by_selectors`'s signature and its six existing assertions. V-03 and V-04 now require the guard AT THE CLI LEVEL, since the ordering defect lives in `run()` and a pure-function check would pass while the CLI still reported a typo. Required tests item 5 added. |
| PR-002 | BLOCKER | IN-SCOPE | D. anti-regression (the fixture specifying three items was invalid) | `attention.py:3071` (twins `:2850`, `:2991`); measured `aw att sv0sf3` = 2 lines vs `aw att zzzzzz` = 1 line; `aw att sv0sf3 -t plans` = empty, exit 0 | **THE AMBIGUITY FIXTURE WAS WRONG.** A selector forces `show_all`, so the "matched but hidden" case E-01/E-03/V-01 were built on does not exist and the fixture would have distinguished nothing. The real matched-but-empty twin is a downstream-filtered match. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added as F1a. Concern, Goal fact 1, E-01 and V-01 all corrected; V-01 now carries an explicit REJECT condition for a parked-artifact fixture and requires the disproving output pasted. The "do not auto-enable --all" caution was also describing existing behavior and is re-worded in the deferral section. |
| PR-003 | HIGH | UNDER-SCOPE | F. prevent silent failure; C. architecture | measured all eight surfaces with `aw att zzzzzz <flag>`; return sites `:2983` (`--check`) and `:3012` (list modes) | **FIVE OUTPUT SURFACES WERE OUT OF THE PLAN AND ALL ARE SILENT.** `--json`, `--format json`, `--check`, `-id`, `--paths`, `--filenames` all print nothing (or `valid:true`) and exit 0. `--check` actively prints "the view is valid." A board-level message reaches none of them, because two of them return before the board is composed. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | Added as F8, plus new E-07 (enumerate and decide per surface, with the channel), E-09 (`--json`) and E-10 (`--check` and the three list modes, STDERR for the list modes so a pipe is not corrupted). Scope line widened to name all eight surfaces. V-07/V-09/V-10 added; Required tests items 7 and 11 added. |
| PR-004 | HIGH | UNDER-SCOPE | A. correctness; F. UX (a fail-closed default that breaks correct usage) | measured `abandoned`, `reusable`, `planned`, `roadmaps`, `releases`-as-tree all empty and exit 0; `attention_contract.TRACKED_TREES` = 5 declared vs 4 live trees; `25kzda:239` | **THE FAIL-CLOSED DEFAULT WOULD TURN LEGITIMATE EMPTY QUESTIONS INTO ERRORS.** Tree names, attention classes and native statuses are all valid selectors, and a repository can legitimately contain none of a value. Asking "what is abandoned?" and hearing "nothing" is a successful answer, not a typo. Unaddressed as authored. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | Added as F10 and new E-08: derive the vocabulary FROM the contract symbols (not a literal list, so a value added later cannot silently become an error), decide the exemption citing `25kzda` 2.4a, and do it BEFORE the exit code. E-06 now depends on E-08. V-08 added, including proof that `attention_contract.py` was not edited (owned by `m867ox`). Required tests item 9 added. |
| PR-005 | HIGH | IN-SCOPE | G. plan executability (an open question the repository had answered) | `25kzda:205`, `:239` (`Status: approved`); `cli.py:2082`; measured `aw runs zzzzzz` exit 2 both surfaces vs `aw find plans zzzzzz` exit 0 both surfaces | **OQ-01 WAS POSED AS AN ABSTRACT TRADE-OFF WHILE TWO LIVE CONVENTIONS ANSWER IT.** An approved spec rules "Zero matches return exit 2" with a status-selector exemption and `aw runs` implements it; `aw find` does the opposite. An executor deciding from the plan alone would have invented a third answer. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F11 and appended to OQ-01 with both precedents quoted and cited. E-06 must now cite which convention it followed and why; the question stays the maintainer's since neither spec governs `attention`. Also fed E-08, since both precedents agree on the vocabulary exemption. |
| PR-006 | MEDIUM | IN-SCOPE | A. correctness (a false premise authorizing unnecessary work) | measured `validate_agent_record` -> `[]` for `findings`/exit 1 and for `cannot-run`/exit 2; `aw runs zzzzzz --agent` -> `cannot-run`, exit 2, `unresolved_targets` | **F5 IS FALSE AND ITS ESCAPE HATCH WOULD HAVE BEEN TAKEN.** The plan warned no honest record might validate and authorized "record it as a finding" instead of emitting one. Two shapes validate and the repository already ships one of them for exactly this condition. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F5 WITHDRAWN IN PLACE with the validator output pasted, rather than deleted, so the reasoning stays auditable. E-05 rewritten to reuse the `aw runs` precedent including its `unresolved_targets` field name, and forbidden from bumping the schema. V-05 now refuses the "no valid representation" claim in advance. |
| PR-007 | MEDIUM | UNDER-SCOPE | C. architecture (a versioned payload changed without a version decision) | `attention.py:1256` (`SCHEMA_VERSION` = 4), `:1258` (`valid` from drift only); `whatnext.md:50` | **THE `--json` PAYLOAD IS `/whatnext`'S PRIMARY SOURCE AND ASSERTS `valid:true` FOR A TYPO.** The repository's own "what should I do next" workflow runs `aw attention --format json` FIRST; a mistyped selector tells it the repository is valid and empty. The payload is versioned for exactly this kind of change and the plan named no version decision. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F9 and new E-09: decide whether an unmatched token belongs in `violations` (flipping `valid`) or a new key, bump `SCHEMA_VERSION` if the shape changes, and state what `/whatnext` would then conclude. The `SCHEMA_VERSION` lever added to Project conventions. V-09 added. |
| PR-008 | MEDIUM | UNDER-SCOPE | A. correctness (two exit signals composing) | three return sites `:2983`, `:3012`, `:3238`, all `core.drift_exit_code(drift)`; measured bare `aw att --agent` -> `outcome:findings, exit:1, findings:21` | **A NO-MATCH EXIT CODE MUST COMPOSE WITH A DRIFTY VIEW AND THE PLAN DID NOT SAY SO.** This repository's view is drifty TODAY (21 stranded-lane findings), so a naive no-match code that overwrites `drift_exit_code` would mask 21 real findings behind an operator typo. Three separate return sites make an inconsistent patch easy. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added as F12; E-06 now names all three return sites and requires composition rather than replacement, with the measured drifty baseline. V-06 requires the composition case pinned by its own test. Required tests item 10 added. Also recorded in OQ-02, which requires the `--check` refusal to be a SEPARATE condition from drift so it can be relaxed independently. |
| PR-009 | MEDIUM | IN-SCOPE | G. plan executability (a deferral resting on an unreproducible claim) | `attention.py:1606` (`setup_needed` reads `.aw/setup-repo-needed.md`), `:3222-3228`; the marker file is absent; no `aw att` run printed the line | **THE `TODO: Run /aw setup-repo` DEFERRAL DESCRIBED A DEFECT THAT DOES NOT REPRODUCE.** The plan called the line unconditional "including on successful calls in a fully-configured repo". It is gated on a marker file that is absent here, so the behavior is the feature working. Left as authored it would seed a follow-up plan on a false premise. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The deferral bullet rewritten with the measured gating condition and the corrected diagnosis (if the line was seen, the marker existed), rather than deleted, so the observation survives with its real explanation. |
| PR-010 | LOW | UNDER-SCOPE | C. architecture (a second message shape for a solved problem) | `term.py:588` `format_empty_result`; `aw find plans zzzzzz` renders outcome + "Active filters:" + `Next` | E-04 specified a no-match message from scratch. An empty-state primitive already exists, already echoes the selector under "Active filters:", and is already what `aw find` shows the operator for its own empty result, so a hand-rolled shape here would diverge from a pattern the operator already reads. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires reusing `term.Term.format_empty_result` or justifying a second shape; V-04 requires that statement. `aw find`'s behavior also recorded in Project conventions as the live counter-convention. |
| PR-011 | LOW | OVER-SCOPE | D. domain invariants (a caution against a change already in place) | `attention.py:2850`, `:2991`, `:3071` | The plan repeatedly forbade "auto-enabling `--all`" and warned against showing hidden artifacts. A selector already forces `show_all`, so there was nothing to forbid; as written it implies a behavior change the fix must not make, which could lead an executor to "restore" hiding under a selector and regress current behavior. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The Project-conventions bullet and the deferral bullet both rewritten to say the override already exists and needs no change; E-03's "do not auto-enable" instruction removed in favor of the measured fact in Goal item 1. |
| PR-012 | LOW | UNDER-SCOPE | E. testing; G. documentation | `cli.py:380-388` (help text); `.github/workflows/tests.yml:145`; three pending plans declare `attention.py`; `IPD-Z602` on E-05 | Four smaller gaps: the `--help` exit contract would go stale with no fence path declared for `cli.py`; the CI gate invocation was never named as an unchanged-behavior check; the concurrent-edit risk on `attention.py` was unstated though three other pending plans declare it; and E-05 tripped the density advisory. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `agent_workflows/cli.py` added to `Scope-Paths` and the spec-sync section now names the exact help text and the `aw runs` wording pattern to follow; Required tests item 11 pins the CI invocation; the execution contract names the three-plan overlap; E-05 split into E-05/E-09/E-10, clearing the advisory (`review-finalize` lint now reports no diagnostics). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan's ambiguity fixture is invalid. Reject the plan for a wrong premise, or correct the fixture and keep the approach? | CORRECT IT. The DEFECT reproduces exactly as claimed; only the second half of the fixture (the matched-but-empty twin) was misidentified, and the correct twin is measurable in three ways. | (a) `REJECT - NEEDS REPLAN`, rejected: the approach (report per-token match facts, then surface them) is sound and unchanged; only the fixture and the fix SITE moved, both bounded edits. (b) Leave the fixture and let E-01 discover it, rejected: E-01's output is the specification for E-03 and V-01, so a wrong fixture propagates into the implementation and its verification, which is how the false-no-match would have shipped. | `attention.py:3071` forcing `show_all`; measured 2-line vs 1-line outputs; three measured downstream-filtered empties | yes |
| D-2 | Where should the match fact be computed, given `--type` runs first? | AGAINST THE UNFILTERED SCAN, with `filter_items_by_selectors`'s existing signature and assertions preserved. | (a) Inside the filter as authored, rejected on measurement: reports a false no-match for any selector narrowed by `--type` (1 match vs 0 over the two scans). (b) Change the filter's signature to take both lists, rejected as the primary route: six existing assertions bind that contract (`test_attention.py:439-471`) and breaking them for a reporting feature is a needless blast radius, though E-03 permits an explicit second RETURN value. | `:2797-2799` before `:2806-2808`; the measured 1-vs-0 match counts; `tests/test_attention.py:439-471` | yes |
| D-3 | Should the plan cover the five surfaces it never named, or should they be a follow-up? | COVER THEM HERE. The plan's stated goal is that a selector matching nothing says so; a fix reaching two of eight surfaces does not achieve it, and `--check` would keep actively asserting "the view is valid" about an unresolved token. | (a) Follow-up plan, rejected: the surfaces share one selector path and one fix, so splitting them would mean re-deriving the same match facts in a second plan, and the most misleading surface (`--check`) would keep shipping. (b) Cover only `--check` and `--json`, rejected: the list modes are what a script consumes, and silence there is the machine-facing half of the same defect. | measured silence on all eight surfaces; return sites `:2983` and `:3012`; `whatnext.md:50` | yes |
| D-4 | Does a legitimate zero-match vocabulary token deserve an exemption, and may I decide that? | YES, EXEMPT, and it is a correctness fix rather than a policy call. Exiting nonzero for `aw att abandoned` in a repo with nothing abandoned would be a NEW defect introduced by this plan. The vocabulary must be derived from contract symbols, not a literal list. | (a) Let the fail-closed default cover everything, rejected on measurement: five tokens in this repo alone would become "errors". (b) Hard-code the exempt token list, rejected: a status or tree added later would silently become an error, which is the same class of latent bug as the one being fixed. (c) Escalate as a blocking question, rejected: the repository already ruled on precisely this in `25kzda` 2.4a with its reasoning stated, so asking would be asking what the repo answers. | `25kzda:239`; five measured empty vocabulary tokens; `attention_contract.TRACKED_TREES` / `ATTENTION_CLASSES` / status enums as the derivation source | yes |
| D-5 | OQ-01 (exit code) has an approved-spec precedent. Resolve it myself, or leave it to the maintainer? | LEAVE IT OPEN, but attach both precedents so the choice is informed. E-06 ships fail-closed and must cite which convention it followed. | (a) Resolve it to exit 2 on `25kzda`'s authority, rejected: that spec governs `aw <host> run` and never mentions `attention`, so applying it would extend an approved contract to a verb it does not cover; and `aw find` proves the repository has not settled this globally. (b) Leave it as the plan had it, with no precedent, rejected: an executor would decide in a vacuum while two live conventions exist. | `25kzda:205`, `:239` scope is `aw <host> run`; `cli.py:2082`; measured `aw runs` exit 2 vs `aw find` exit 0 | yes |
| D-6 | Should the `--check` question be raised as a new blocking open question? | RAISE IT NON-BLOCKING (OQ-02), with the fail-closed form shipping and the refusal implemented as a condition SEPARATE from the drift set. | (a) Blocking, rejected: the plan executes under either answer and the CI invocation carries no selector, so nothing breaks while it is open. (b) Decide it myself, rejected: routing an operator input error into `violations` would flip the `--json` `valid` flag and change what a CI gate means, which is a public-contract call. (c) Say nothing, rejected: `--check` printing "the view is valid" for an unresolved token is the single most misleading measured output. | `.github/workflows/tests.yml:145` runs `--check --agent` with no selector; `attention.py:2983`; `:1258` `valid` from drift | yes |
| D-7 | The `TODO: setup-repo` claim does not reproduce. Delete the bullet or correct it? | CORRECT IT IN PLACE with the measured gating condition, keeping the deferral. | (a) Delete it, rejected: the author observed something, and deleting the record loses that; the corrected bullet explains what they most likely saw (the marker present). (b) Leave it as a defect claim, rejected: it would seed a follow-up plan against `setup_needed` working as designed. | `attention.py:1606`, `:3222-3228`; marker file absent; no measured invocation printed the line | yes |
| D-8 | E-08 will notice that `roadmaps`/`walkthroughs`/`releases` artifacts are invisible to the view. Fix it here? | NO. Forbid editing `attention_contract.py` and require V-08 to prove it was not touched. | (a) Fix the tree set here, rejected: approved plan `m867ox` declares `attention_contract.py` and `artifact_core.py` for exactly this, so editing it would race an approved plan in a shared checkout. (b) Say nothing, rejected: E-08 derives its vocabulary from `TRACKED_TREES` and would hit the discrepancy (`releases` declared, 4 trees live) with no guidance, and might "fix" it. | `m867ox` `Status: approved`, `Scope-Paths` includes `attention_contract.py`; measured `aw att f33nrj` empty even with `--all`; live scan yields 4 trees | yes |
| D-9 | Verdict, given two BLOCKER-severity findings? | APPROVE WITH REVISIONS APPLIED, readiness GO - PENDING HUMAN APPROVAL. Both blockers were FIXED by in-place revision; no finding is left OPEN or DEFERRED at or above the gate threshold. | (a) `REVIEWED - OPEN QUESTIONS` / NO-GO, rejected: both open questions are non-blocking, ship fail-closed, and the workflow reserves NO-GO for a genuine not-ready condition rather than for a plan whose findings were repaired. (b) `REJECT - NEEDS REPLAN`, rejected: the defect reproduces, the approach is sound, and every fix was a bounded edit to the plan text. | workflow readiness table; all twelve findings `FIXED`; `aw ipd lint --phase review-finalize` conforming, exit 0, no diagnostics | yes |

### Escalation of the irreversible decisions

None of this round's nine decisions is judged `Reversible: no`. Every one is undone by editing this plan
before it executes: nothing here publishes an interface, migrates data, deletes anything, or produces a
released artifact. Stated explicitly rather than left blank, because two LOOK irreversible and are not.
D-4 (the vocabulary exemption) shapes an exit contract, which would be irreversible once shipped, and that
is exactly why the exemption is the PERMISSIVE direction: exempting a vocabulary token can be tightened
later, while shipping nonzero for `aw att abandoned` and then relaxing it would first break whoever
scripted against it. D-6 (`--check`) shapes a CI gate, which is why the decision I made was to ship the
fail-closed form as a SEPARATE condition and escalate the policy as OQ-02, so the maintainer can relax it
without touching the drift path. The irreversible act is deliberately not authorized by me.

### Honest limits of this review

- I DID NOT IMPLEMENT THE FIX. Every measurement is against unmodified HEAD `cf0ebf7a`.
- I DID NOT RUN THE FULL TEST SUITE. I read `tests/test_attention.py:439-471` to establish which
  assertions bind `filter_items_by_selectors`'s contract, and I did not run `python3 -m pytest`. The
  plan's baseline requirement (Required tests item 1) is unverified by me.
- MY MATCH-COUNT MEASUREMENT IS A PYTHON-LEVEL RECONSTRUCTION of `run()`'s filter order, not a driven CLI
  run: I called `att.scan`, `att.parse_type_filters(['plans'])` and `att.filter_items_by_selectors` in
  sequence to mirror `:2797-2808`. The CLI-level symptom (`aw att sv0sf3 -t plans` -> empty, exit 0) I did
  measure directly, which is why V-03 and V-04 demand the CLI-level proof rather than inheriting mine.
- MY SURFACE ENUMERATION COMES FROM `aw attention --help` PLUS THE CODE PATH, so a surface reachable only
  through another entry point (a library caller, a different alias with its own flags) would not have
  appeared. E-07 must re-derive the table rather than copy mine.
- MY SPEC SEARCH WAS A CONTENT SEARCH for `attention` across `.aw/records/specs/`. A spec asserting an
  `attention` exit contract in other words would not have appeared, which is why the spec-sync section
  still instructs the executor to declare and record one if found.
- I DID NOT VERIFY F6'S SESSION HISTORY. I confirmed that `4fodkt` and `63425h` both resolve at review
  HEAD, which is consistent with the author's account that they were absent when queried, but the
  transcript itself is not in this lane.
- I DID NOT DECIDE EITHER OPEN QUESTION'S POLICY. OQ-01 (exit code) and OQ-02 (`--check`) both ship in the
  fail-closed direction and both are the maintainer's to relax.
