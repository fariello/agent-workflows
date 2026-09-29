# Review findings: plan emzbut

- Subject-Id: emzbut
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `b233857e` in an isolated worktree. Structural preflight `aw ipd lint --phase author`
reported `clean` (`findings: 0`) before any edit; re-run at `--phase review-finalize` after revisions, also
clean. No pre-review snapshot was owed: the plan was committed and unmodified, and the lane-input copy under
`.aw/state/lane-inputs/rev-29/` is the same content. Bare suite at review HEAD: `3246 passed, 2 skipped, 3
warnings in 47.81s`, matching the plan's own F-10 baseline exactly. NO PRODUCTION FILE OR TEST WAS MODIFIED
by this review; every measurement was a read or an in-process probe in a temp directory, and every `mock.patch`
was scoped to a context manager that restored on exit.

THE PLAN'S CENTRAL THESIS IS CORRECT AND ITS HEADLINE MEASUREMENT REPRODUCES. Appending what
`capture_command` returns to a real `RunLedgerStore` persists the output text: the persisted line's keys
include `stdout`, `stdout_excerpt`, `stderr` and `stderr_excerpt` beside `stdout_sha256`/`stdout_len`, and
`run_ledger_schema.validate_record` returns `ok=True` on the text-bearing mapping because the schema
enumerates required fields and never a permitted key set. F-01, F-02 and F-11 all hold. The proposed
`CapturedToolEvent` shape also works exactly as F-03 claims: `isinstance(x, dict)` holds, `.get()` and
subscript reads are unchanged, `json.dumps`, `dict(x)` and `copy.deepcopy(dict(x))` all see schema fields
only, `__slots__` refuses an undeclared attribute, and positional 2-tuple unpacking is unaffected. I
additionally confirmed a property the plan does not claim: `copy.deepcopy` of the OBJECT (rather than of
`dict(x)`) preserves the attributes, and so does a `pickle` round trip, so the type is not fragile under
ordinary copying.

F-05 THROUGH F-09 AND F-12 THROUGH F-13 ALSO REPRODUCE. The two deleted test files are gone in `19313eed`;
there is no test of `capture_command`, no call site of `run_suite_check`, and no test of
`run_worker_process`; both consumers work today (F-07 re-measured live, giving `summary='3 passed in 0.42s'`
and a two-stream `RawWorkerResult`); `max_output_bytes=100` against 50,000 bytes still returns 50,001
(F-08); `max_output_bytes=10` still gives `stdout_len: 10` against `stderr_len: 100` with `truncated: True`
(F-09, the item records 101 and I measure 100, an off-by-one in the item's own note, immaterial); the digest
matches the truncated bytes (F-11); and both carriers `fqseay` and `lijmwy` resolve to real `open`
release-blocking bug items with the correct content.

SIX DEFECTS WERE FOUND, all in the plan's TEST RECIPES and its blast-radius enumeration rather than in its
design. The design decision (OQ-01's `dict` subclass) is right and I did not disturb it. What was wrong is
that four of the plan's prescribed validation steps CANNOT BE EXECUTED AS WRITTEN, and each would have cost
the executor a discovery pass on a plan whose whole purpose is to leave behind trustworthy evidence.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | HIGH | IN-SCOPE | E (testing) / D (anti-regression) | plan E-05 "fail-loud" bullet and F-04; `runner_shared.run_suite_check`'s `except Exception`; `host_runner.run_worker_process` | E-05 prescribed `pytest.raises(AttributeError)` "against a consumer handed a bare `dict`", and F-04 asserted the new contract "converts the failure mode from silent-wrong to loud". FALSE AT ONE OF THE TWO CONSUMERS: `run_suite_check` wraps the read in a DELIBERATE blind `except Exception` that E-03 explicitly preserves, so the `AttributeError` is CAUGHT and converted into a fail-closed `SuiteCheckResult(passing=False, exit_code=127)`. Measured at review: nothing propagated, reason `suite check could not run (fail-closed): 'dict' object has no attribute 'stdout'`. `run_worker_process` has no handler at all, so there the error genuinely propagates. As written the test would either fail or, worse, be "made to pass" by removing the blind catch, turning a fail-closed gate into a crashing one - the exact anti-pattern E-03 guards | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | F-04 rewritten with the per-consumer measurement and the pre-fix contrast (a text-less double currently returns `passing=True` with an empty summary). E-05's bullet split into (a) `pytest.raises` at `run_worker_process` and (b) a non-raising fail-closed refusal assertion at `run_suite_check`, with an explicit prohibition on a blanket `pytest.raises` and on removing the blind catch. V-05(d) updated to match |
| PR-402 | HIGH | UNDER-SCOPE | C (architecture) / B (privacy of captured text) | plan F-12 and OQ-01's `dict(result)` caveat; `verify_roles.build_verifier_packet`, `verifier_packet_from_dict`, `procedure_test_falsifiability` | F-12 enumerated the blast radius as "exactly two invocations ... No CLI surface, doc example, or test invokes it", and OQ-01 conceded only abstractly that "a reader who does `dict(result)` to normalize it will silently lose the text". A LIVE code path does precisely that: both verifier-packet builders normalize their evidence manifest with `tuple(dict(e) for e in ...)`, and `procedure_test_falsifiability` then reads `ev.get("stdout", "")` to detect RED/GREEN falsifiability proof. Measured at review: a `CapturedToolEvent` carrying `stdout="RED then GREEN"` becomes `{'kind':'tool_event','exit_code':0}` and the read returns `''` - silent loss with NO `AttributeError`, the one failure mode the chosen shape cannot make loud. It is LATENT today (no in-tree path routes a capture into `raw_evidence_manifest`; the only `build_verifier_packet` caller passes no manifest), so it does not block the design, but leaving the enumeration claiming completeness would let the next author wire worker output into the verifier and lose it | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | F-12 extended with the review's per-surface check of `validate_evidence`, `run_cli` and `host_capability_registry` (none reads the text, so none breaks), and new F-14 records the `verify_roles` path with its measurement and its latency. E-01 now requires the docstring to name that call path BY SYMBOL rather than warning abstractly about `dict()` |
| PR-403 | MEDIUM | IN-SCOPE | E (testing) / A (correctness) | plan E-05 "exact expected key set"; `run_evidence.capture_command`'s `max_bytes` argument to `build_tool_event` | E-05 demanded "the exact expected key set rather than a substring probe" and named four schema fields, implying one constant set. The emitted key set is NOT constant: `max_bytes` appears only when `max_output_bytes` is passed. Measured at review, the unbounded call emits 22 keys and the bounded call 23. A single hardcoded `==` assertion therefore fails against whichever shape it was not authored against, and both shapes are production-reachable (`run_suite_check` bounded at 512,000; `run_worker_process` unbounded) | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now requires the exact-set assertion PER CALL SHAPE (or a set-union-with-`max_bytes` formulation against a named base constant), keeps the exact-set requirement, and records both measured counts plus which consumer uses which shape. V-05(b) updated |
| PR-404 | MEDIUM | IN-SCOPE | E (testing) / G (executability) | plan E-05 persistence bullet and V-02; `RunLedgerStore.append`'s validate-before-seq-0-check order; `run_ledger_schema.ROLES`; `runner_shared.run_suite_check`'s `actor="driver"` | The persistence proof, which is the plan's load-bearing evidence, cannot be run from the recipe given. TWO blockers, both hit at review. (1) The seed record: "a seed `kind: "run"` record" is insufficient because `append` schema-validates BEFORE the seq-0 kind check, so a minimal seed is refused with `RL-E010` plus four `RL-E020`s (`workflow_digest`, `requirement_digest`, `repo`, `head`). (2) The actor: `validate_record` REJECTS `actor="driver"` with `RL-E014`, and `driver` is literally what `run_suite_check` passes, so an executor probing with the gate's own actor gets a false failure on the very step V-02 says must return ok. The second blocker also exposed a pre-existing inconsistency worth recording so it is neither absorbed nor "fixed" opportunistically | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-05 now gives the working seed record field-by-field and mandates `actor="executor"`; V-02 carries the same correction plus the distinction between the 10,548-byte RETURNED mapping and the 11,827-byte PERSISTED line the review re-measured (the store adds `seq`/`prev_hash`/`timestamp`), so a reader reconciles against the right figure. New F-15 records the `driver`-not-in-`ROLES` condition, its bounded consequence, and an explicit instruction not to change any actor value in this plan |
| PR-405 | MEDIUM | IN-SCOPE | A (correctness) / E (testing) | plan E-01 and E-05 non-UTF-8 bullets, V-05(f) | The prescribed demonstration of the length asymmetry does not demonstrate it. E-05 said to "write raw bytes that are not valid UTF-8" and assert `stdout_len` describes raw bytes while the attribute decodes with replacement. Measured at review: `b"\xff\xfe\xfd"` gives `stdout_len` 3 and exactly 3 replacement characters, so the numbers are EQUAL and an inequality assertion fails while an equality assertion pins nothing. The asymmetry is about raw bytes versus decoded CHARACTERS, not about validity: a valid two-byte `e-acute` gives `stdout_len` 2 against 1 character. The plan's framing ("non-UTF-8 output") would send an executor to the one input class where the property is invisible | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01's docstring requirement reframed to raw-bytes-versus-decoded-characters with the measurement; E-05 and V-05(f) now require BOTH cases (multi-byte for the length divergence, invalid bytes for the replacement decode with the digest over raw bytes) |
| PR-406 | LOW | IN-SCOPE | D (anti-regression) / G (executability) | plan F-05; `tests/fixtures/runnerlayer_rehomed_premove_fingerprints.json`; plan E-06 mutation bullet | Two gaps a reader could stumble on. (a) F-05 said the surviving `stdout_excerpt` text is "outside a stored AST fingerprint fixture" without establishing whether anything READS that fixture; since it contains an `ast.dump` of `run_suite_check` including the exact `.get("stdout_excerpt")` call E-03 edits, an executor could reasonably fear E-03 turns it red, or could "helpfully" re-baseline a deliberate historical record. Confirmed at review that NO test, Makefile target or config reads it. (b) E-06's mutation proof, the item's own load-bearing evidence, did not state that the patch mechanism works or that the mutation must be introduced by hand rather than found in history | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-05 extended with the no-reader measurement and an explicit "do not re-baseline" instruction. E-06 now records that `SUITE_CHECK_ARGV` is read as a module attribute at call time (so `mock.patch.object` reaches it), pastes the review's pre-fix measured values, and warns that since the current code already works (F-07) the mutation must be introduced deliberately. I also verified the mutation proof is achievable: against a post-fix producer, the reverted `.get("stdout_excerpt")` read yields `''` and an empty summary, so the test does fail as required |

No finding was DEFERRED and none was left OPEN, so no escalation to a `- Blocking: yes` question is owed
(`check.review-finding-unescalated` satisfied vacuously). No BLOCKER was found. The two HIGHs are both
FIXED in place: PR-401 is a prescribed assertion that contradicts a guard the same plan protects, and PR-402
is an incomplete completeness claim, and neither touches the plan's design.

WHAT I DELIBERATELY DID NOT FLAG, with the reason, since each is a place a reviewer could add noise.
OQ-02's refusal to persist output text is correct and well argued, and I confirmed its load-bearing premise
independently: no verifier, CLI surface or validator reads output TEXT back out of a ledger record
(`validate_evidence` reads only `exit_code`/`stdout_sha256`/`truncated`/`cwd`/`argv`; `run_cli` projects only
`argv`/`exit_code`/`stdout_sha256`/`cwd`). The four `Carrier-Declined` entries each meet the repository's bar:
they decide rather than defer, and each states what is left unbroken. The deferrals of F-08 and F-09 to real
carriers are right, and the plan is scrupulous about not folding them in even though both sit within three
lines of code it edits. The gate's scope wording is a DECLARATION with no "STOP and report" directive for a
scope question, which is what the 2026-09-01 ruling requires. The plan correctly omits `- Readiness:` at
authoring, so nothing was forged; this review writes it. F-13's no-spec-amendment conclusion reproduces
(`7ckptx`'s only mention is about a timeout constant).

ONE THING WORTH THE MAINTAINER'S ATTENTION THAT IS NOT A FINDING AGAINST THIS PLAN: F-15's discovery that
`run_suite_check` captures with `actor="driver"`, a role the ledger schema rejects. It is harmless today
because such a record can never be appended, and it is correctly out of scope here, but it means the suite
gate's tool events are permanently unpersistable. Whether `driver` should join `ROLES` or the gate should pass
`runtime` is a real question with a behavioral consequence either way, and it belongs to the maintainer to
file rather than to this plan to absorb.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | PR-401 shows the fail-loud property holds at only one consumer. Does that invalidate OQ-01's chosen `dict`-subclass shape, or only the test that pins it? | Only the test. Keep the shape, correct E-05 to assert the behavior each consumer actually has | Reopening OQ-01 to reconsider a third return value, rejected because the fail-loud argument was never the shape's only or main justification (closing the F-01 persistence leak is, and both candidate shapes do that equally); and the blind catch converting the error into a NAMED fail-closed refusal is itself a good outcome, strictly better than today's silent pass | Measured at review: the same text-less double gives `passing=True, summary=''` pre-fix and `passing=False, exit_code=127` with the cause in `reason` post-fix; `run_suite_check`'s `except Exception` docstring states why it must stay | yes |
| D-2 | PR-402's `verify_roles` silent-loss path is latent, not live. Fold a fix into this plan, file a carrier, or record it? | Record it as F-14 and require E-01 to name the path by symbol in the docstring | Filing a backlog carrier, rejected because nothing is BROKEN: no code path routes a capture into that manifest, so there is no defect to carry, and an `open` item describing a hazard that cannot fire would be noise in the release-gate view. Folding a fix in, rejected because there is nothing to fix without inventing a consumer | Measured at review that `host_sandbox_profile` is the only in-tree `build_verifier_packet` caller and supplies no manifest; the repository's own `Carrier-Declined` convention for a decision that leaves nothing broken | yes |
| D-3 | PR-404 surfaced that `run_suite_check` passes an actor the ledger schema rejects. Fix it here, carry it, or record and forbid? | Record as F-15, forbid any actor change in this plan, and surface it to the maintainer in the report | Fixing it here, rejected as an unreviewed behavior change inside a plan a reviewer is reading for a contract cleanup, exactly the reasoning the plan itself applies to F-08. Filing a carrier myself, rejected because the remedy is a genuine choice between widening `ROLES` and changing the gate's actor, which is the maintainer's call and not a reviewer's to pre-empt | Measured `RL-E014` for `driver` against `ok=True` for `executor`; `run_ledger_schema.ROLES` membership; the plan's own precedent for carrying an adjacent defect rather than folding it in | yes |
| D-4 | E-05 and E-06 both carry several assertions. Do they breach the right-sizing / conceptual-density bar? | No. Keep both whole | Splitting E-05 into producer-contract and error-path items, and E-06 into per-consumer items, rejected because each is ONE concern over ONE new file and ONE verification surface: E-05 pins the producer's contract and E-06 pins its two consumers, and splitting would duplicate the same fixture setup and the same suite run across items with no added signal. The linter agrees (no `IPD-Z602` advisory on either) | The rubric's four density diagnostics applied per item: one deliverable each (one test file, extended once), one test-surface each, and neither needs unrelated V-items; `aw ipd lint` clean at both phases | yes |

No `Reversible: no` decision was taken, so no escalation is owed under the irreversible-decision rule.
