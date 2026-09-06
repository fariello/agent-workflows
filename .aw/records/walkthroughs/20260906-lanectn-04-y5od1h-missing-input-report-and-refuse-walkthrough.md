# Walkthrough: the missing-input report-and-refuse cycle (`lanectn` Order 04, `y5od1h`)

- Date: 2026-09-06
- Plan: `.aw/records/plans/executed/20260901-lanectn-04-y5od1h-bounded-missing-input-repair-without-original-checkout-acces.ipd.md`
- Spec: `7ckptx` R3.1, R3.2, R3.3, R3.5, R3.6, R3.7 (R3.3a/-1/-1a/-1b/-2, R3.3b, R3.4 withdrawn)
- Base commit: `274092d3`
- Executed by: opencode/its_direct/pt3-claude-opus-5-1m-us, in lane `aw/lane/y5od1h`

## What shipped, in one paragraph

A worker that genuinely lacks a file now has a deterministic, auditable way to SAY SO, and the driver
answers with a precise REFUSAL RECORD rather than a copy. The worker emits
`AW_MISSING_INPUT:<repo-relative-path>:<why>` and keeps working; the driver parses it from stdout,
classifies the request in COORDINATOR code, refuses it with a named rule and a reason, records that on
the attempt and in `events.jsonl`, and PRESERVES the lane instead of tearing it down. Nothing is ever
copied into a lane on request, and no code path can grant access to the original checkout.

## The amendment is the story, so read it first

The plan's title still says "repair", and the obvious reading of that word is now WRONG. Spec `R3.3a`
(maintainer decision, 2026-09-01) WITHDREW the permit-and-copy branch and the secret vocabulary that
gated it. The cycle is REPORT-AND-REFUSE. Three reasons, the third decisive:

1. Policing secrets invites blame for a miss, while `gitleaks` and `aw sanitize` already cover them.
2. The research (`x03wgn`) said do-not-COPY, not adjudicate-requests.
3. Decisively, THE BRANCH WAS INERT: a lane is a `git worktree` at a commit, so it already contains
   every TRACKED file (measured: 0 of 1470 absent), and `R3.3b` permitted ONLY tracked files. The copy
   branch could therefore only ever copy a file the lane already had, while the inputs the research
   actually worries about (`.venv`, `node_modules`, generated schemas) are ignored or untracked -
   exactly the category it refused.

What is PRESERVED is the escape hatch that makes R1.1's strictness survivable: the worker still reports
(R3.1) and the driver still preserves and pauses (R3.2). Only the ANSWER changed.

HONEST CONSEQUENCE, recorded rather than hidden: a turn genuinely blocked on a missing IGNORED input now
fails with a precise record instead of self-repairing. That is the intended trade. The conforming fix, if
it ever proves an operational problem, is UP-FRONT lane assembly under an explicit policy.

## E-03 was WITHDRAWN, not skipped

E-03 was WITHDRAWN by spec amendment `R3.3a`, not skipped and not forgotten. No secret vocabulary was
added to the shared predicate, and none may be: implementing one would ship the liability the maintainer
explicitly declined and would assert behavior the amended spec forbids.

This is enforced mechanically rather than by convention.
`NoWithdrawnWorkTests::test_no_secret_vocabulary_exists_in_the_shared_predicate_or_the_classifier`
searches the predicate body, its hint tuple, the classifier body, and `MACHINE_LOCAL_PREFIXES` for
`.env`, `.pem`, `.key`, `credentials`, `id_rsa`, and `secret`, and asserts each is ABSENT. A sharper
companion, `test_a_dot_env_request_is_refused_by_an_ORDINARY_rule_not_a_secret_rule`, shows that `.env`
IS still refused (everything is) but by the generic `withdrawn-repair-path` rule, so the refusal provably
does not come from a vocabulary.

## Where the code lives, and why there

Everything host-neutral is in `agent_workflows/lane_containment.py`, the module spec R2.6 requires to be
DECLARED rather than improvised into one driver and imported from the other. Each driver contributes one
construction line and one per-line call:

| Piece | Symbol | Requirement |
| --- | --- | --- |
| Token emit/parse | `format_missing_input_token`, `parse_missing_input_token` | R3.1 |
| Classification | `classify_missing_input_report` | R3.3, R3.5 |
| Denied-event routing | `classify_denied_permission_path` | R3.7 |
| The decision type | `MissingInputDecision` | R3.5, R3.6 |
| Per-turn observer | `MissingInputObserver` (`note_line`) | R3.1, R3.2 |
| Refusal recording | `record_missing_input_refusal` | R3.5 |
| Preserve predicate | `lane_preserved_for_missing_input` | R3.2 |

The token's shape is DERIVED from `MISSING_INPUT_TOKEN_FORM`, the constant child `cqx5v7` already
publishes into the prompt, so the prompt and the parser cannot disagree about the form.

## Four decisions a reader may want to revisit

Full evidence is in the run's decisions register; the substance:

1. `nna8yz` (a declared prerequisite) is `executed` but on an UNMERGED lane branch, so its symbols are
   absent from this lane. I proceeded, because the plan's only cited use of it was R3.4's manifest
   revision, which `R3.3a` WITHDREW - so this plan consumes no symbol from it. `lhmrhx`, whose seam E-04
   genuinely needs, IS present and verified by symbol.
2. `wtiso_gate.format_missing_input` / `parse_missing_input` are stubs whose docstrings name `y5od1h` as
   owner, but sibling `604wra`'s measured ownership table assigns those BODIES to itself, and
   `wtiso_gate.py` is in ITS scope fence, not mine. I put the bodies in my declared shared home and left
   the stubs RAISING (spec R6.2), pinned by a test. **Note for `604wra`'s executor:** when you implement
   those two bodies, re-point them at
   `lane_containment.format_missing_input_token`/`parse_missing_input_token` rather than writing a
   second implementation, and delete my pinning test
   (`TwinParityTests::test_the_wtiso_gate_stubs_are_left_raising_for_their_owner`) in the same change.
3. R3.3 says the reject set MUST BE the shared worker-forbidden predicate, but that predicate holds only
   five coordinator-owned SURFACES while R3.3 lists eight shapes. I CALL it for the class it owns and
   check the other seven (path shape and filesystem state) beside it, adding NOTHING to it - because it
   is also consulted by `assert_worker_scope` to validate a lane's declared WRITES, and widening it
   would change a sibling's rule.
4. The no-live-grant property is made structural by a type with no field capable of expressing a grant
   and a single verdict constant, plus tests that read `_fields` and the constant set. Honest limit,
   stated in the code: Python has no sealed types, so this is an accident guard plus a failing test, not
   a proof that no future edit could add one.

## A process failure I made, and repaired

Partway through, I discovered my driver edits had vanished from the lane. Cause: three `edit` calls used
absolute paths into the MAIN checkout instead of my lane, so the work landed in a tree I was told not to
touch, where an unrelated `git reset` then discarded it. I captured the diff, read all 152 lines to
confirm every hunk was mine, restored the main checkout with a PATH-SCOPED `git checkout --` (never a
bare `reset`, `clean`, or `stash`), verified its `agent_workflows/` was clean and the stash list
unchanged, and re-applied the patch inside the lane. A staged deletion belonging to a co-worker was left
exactly as found. Residual risk I cannot rule out from inside the lane: for roughly 29 minutes my lines
sat in the main working tree and could in principle have been swept into another agent's path-scoped
commit; no commit landed in that window, so I believe none was.

## One sibling test I broke and did not weaken

My first placement put the observer call between `watchdog.touch()` and `runner_stop.poll_stop(run_dir)`
in `oc_runipd`. `tests/test_runner_stop.py::PollWiringTests` asserts the CHARACTER distance between those
two statements stays under 1200 (to prove the poll sits at the per-line checkpoint); my block pushed it
from 1066 to 1233. I did NOT relax that window. I moved my call to immediately AFTER the poll in BOTH
drivers - behaviorally identical, since both run for every line before any `output_mode` branch - which
restored the gap to exactly its HEAD value, and re-anchored my own parity test on the poll.

A subtler trap worth recording: my explanatory comment originally NAMED `watchdog.touch()`, and because
the sibling test locates that symbol with `rindex`, the mention itself became the anchor it measured
from, producing a nonsense 67270-character gap. The comment now avoids the symbol and says why.

## Validation

- New module `tests/test_missing_input_repair.py`: **34 passed in 1.08s**, parameterized over both hosts.
- Five sabotage runs, each with the failing assertion pasted in the plan and the product restored
  byte-identical: pause removed; durable preserve flag omitted; reason omitted from the record; a
  `granted` field added to the decision type; the shared-predicate call replaced by a copied list; and
  the agy twin's wiring removed.
- Bare `python3 -m pytest`: `18 failed, 5171 passed` versus a measured pre-change baseline of
  `18 failed, 5137 passed`; compared BY NODE ID, zero new and zero disappeared failures. The 18 are
  pre-existing and environment-dependent (14 `test_run_viewer` need a run directory a fresh lane lacks;
  4 `test_next_ordering` exit 1) and reproduce on a pristine detached worktree at the same commit.
- `make test-all`: `24 failed, 5574 passed` versus a pristine-worktree baseline of
  `24 failed, 5540 passed`; by node id, zero new and zero disappeared. This invocation carries the known
  CLI-surface declaration failures, which are not this plan's to fix. Stating a single "zero failures"
  across both invocations would be false, which is why each is reported separately.
- `check-local-leaks --agent`: `{"outcome":"clean","exit":0,"findings":0}`.
