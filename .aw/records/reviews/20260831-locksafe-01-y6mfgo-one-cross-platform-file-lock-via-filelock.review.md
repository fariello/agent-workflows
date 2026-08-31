# Review: One cross-platform file lock via filelock, replacing every raw fcntl call site

- Plan-Id: y6mfgo
- Reviewed-At: 2026-08-31
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims verified at HEAD `24af3e0237392d0867d9a6122f2b546fb3e3d988`, working tree clean, target plan
committed and unchanged (pre-review snapshot correctly skipped per the workflow's Step 1).

The plan's central judgement is CORRECT and well evidenced. `fcntl` really is imported at top level in
six modules, so the package really is unimportable on Windows; the inventory of 15 call sites is exact,
not estimated; `filelock` 3.29.7 really is present only transitively (`Required-by: huggingface_hub,
tldextract`), so declaring it is genuinely necessary rather than bookkeeping; D138 really does permit a
justified runtime dependency, quoted accurately; and the `msvcrt.locking` byte-range argument for
preferring `filelock` over hand-rolling is real and is the decisive technical point. `2c122z` really does
carry 18 `platform_lock` references, and `71vjbn` really did execute `partial` with E-07/E-08 blocked.

THREE DEFECTS were found by exercising the real code and the real dependency rather than reading the
plan's prose, and all three are the same class of error: the plan generalized from "every call site uses
`LOCK_EX | LOCK_NB`" and from "`filelock` replaces `flock`", and both premises are false in one specific
place each.

1. PR-001, BLOCKER. `filelock` is RE-ENTRANT; `fcntl.flock` is not; and `runner_stop` DEPENDS on the
   non-re-entrancy. Reproduced both semantics directly. This would have silently broken the R9 stop-level
   monotonicity guarantee, and no test in the plan would have caught it, because the plan's only
   exclusion test is cross-process and the hazard is same-process.
2. PR-002, HIGH. One call site blocks. The plan asserts twice that none do, and specifies a
   non-blocking-ONLY helper on that premise, which would have converted a waiting registry writer into a
   failing one: a behavior change the plan's own Scope explicitly forbids.
3. PR-003, MEDIUM. V-03 promises to prove an operator-facing message unchanged, but no test asserts that
   message today, so the plan's own regression net for it did not exist.

All three are FIXED in place with bounded edits. The approach itself is sound and needed no replan: the
fixes are a non-re-entrancy requirement on the helper, one new decision item (E-07) for the blocking
site, and three added test obligations. No open questions remain, so this is not
`REVIEWED - OPEN QUESTIONS`.

Right-sizing re-checked after adding E-07: 7 E-leaves across 2 task groups, each addressing one concern
and executable in one focused pass. E-03 is the largest (15 mechanical call-site migrations) but they are
one concern against one measured inventory, and its risky part is now split out into E-07.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | UNDER-SCOPE | A. Correctness / D. Anti-regression | `runner_stop.py:57-65` docstring; `_sidecar_lock` at `:462`; reproduced with `filelock` 3.29.7 | `filelock` and `fcntl.flock` differ on RE-ENTRANCY and the plan treats them as interchangeable. MEASURED: a second `acquire()` on the same `FileLock` object SUCCEEDS via an internal counter, whereas a second `flock(LOCK_EX\|LOCK_NB)` on a second handle in one process raises `BlockingIOError`. `runner_stop._sidecar_lock` depends on the REFUSAL: its docstring records that a signal handler re-entering on the same thread must be refused so the level is diverted to a process-local slot, and that a blocking acquire there deadlocked (measured, 10s timeout). A re-entrant helper lets the handler enter the monotonic read-modify-write while the main thread is mid-update, silently losing or corrupting a stop level and breaking the R9 monotonicity property `runner_stop` exists to guarantee. The plan's cross-process exclusion test cannot detect this, because the counter is per-object inside one process. | C:Low; U:Low; S:Low; F:High; Overall:Low (the fix is one construction rule, verified) | FIXED | E-02 now REQUIRES a non-re-entrant helper and states the verified remedy (construct a FRESH `FileLock` per acquisition; `thread_local=False` does NOT help, the counter is per-object). E-04 now requires a SAME-PROCESS non-re-entrancy test alongside the cross-process one, with an explicit note that neither substitutes for the other. Added as F7. |
| PR-002 | HIGH | IN-SCOPE | A. Correctness / G. Plan executability | `project_registry.py:277` (bare `LOCK_EX`) vs `:293`; mode census over `agent_workflows/*.py` | The plan asserts TWICE that "every existing call site uses `LOCK_EX \| LOCK_NB`" (Concern/E-02 and Project conventions) and builds a non-blocking-ONLY helper on that premise. It is false: `project_registry.py:277` acquires a bare `fcntl.LOCK_EX` and WAITS. Census: 7 non-blocking acquisitions, exactly 1 blocking, remainder `LOCK_UN` releases. Routing that site through a non-blocking helper changes "wait for the registry lock" into "fail immediately if contended", which the plan's own Scope forbids ("Excludes changing any lock's SEMANTICS"); leaving it raw forfeits the import-portability goal for that module and preserves the very top-level-import pattern the plan exists to remove. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Low (bounded: one site, one contract decision, `filelock` supports both) | FIXED | Added E-07 to DECIDE and implement it, with a recommendation ((a) an explicit opt-in blocking acquire for this single caller) and an explicit prohibition on silently converting the site to non-blocking. E-03 now depends on E-07 and names the site. Added V-07 requiring a two-process test proving the writer still WAITS. OQ-02 narrowed rather than deleted, since its original wording forbade exactly what E-07 must do. Corrected the false claim in both places it appeared. Added as F8. |
| PR-003 | MEDIUM | UNDER-SCOPE | E. Testing and verification | `grep -rln 'already controlled by another process' tests/` returns nothing; string appears only in `oc_runipd.py` and `agy_runipd.py` | V-03 requires proving the operator-facing message "Run is already controlled by another process" is unchanged, but NO test asserts that string, so the plan's own regression net for the message it names does not exist. "The suite still passes" cannot evidence it, and a manual before/after paste rots immediately. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | V-03 now requires the new TEST asserting that string, not only a before/after paste, and the Required tests section lists it as a fourth mandatory assertion in `tests/test_platform_lock.py`. Added as F9. |
| PR-004 | LOW | IN-SCOPE | G. Plan executability | plan `- Highest E allocated: 06` | Metadata counter would have gone stale against the new E-07, which the structural linter uses. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Bumped to `07`; `aw ipd lint --phase author` re-run and conforming. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is the `filelock` re-entrancy difference a real defect or a theoretical one? | Real, and BLOCKER severity: it silently breaks a documented guarantee rather than failing loudly. | Treating it as a LOW documentation note; deferring it to execution time as "the executor will notice". Rejected because the plan's own test design (cross-process only) provably cannot surface it, so an executor would not notice. | `runner_stop.py:57-65` states the handler-safety requirement and records the measured 10s deadlock; reproduced both `filelock` and `flock` behaviors directly at 3.29.7 | yes |
| D-2 | Fix PR-002 by adding a blocking mode, or by leaving one module on raw `fcntl`? | Neither, by reviewer authority: RAISE IT AS AN EXPLICIT DECISION ITEM (E-07) with a recommendation, rather than choosing the contract myself. | Choosing (a) outright and rewriting OQ-02; choosing (b) outright. Rejected because it changes the helper's PUBLIC contract, which OQ-02 had deliberately settled the other way, and silently reversing a resolved open question is exactly the drift the review record exists to prevent. | plan OQ-02's original text forbids a blocking mode; `project_registry.py:277` requires one; `filelock` supports `blocking=` on both ctor and `acquire` (verified 3.29.7) | yes |
| D-3 | Does the false "every call site is non-blocking" premise make the plan unsound (REPLAN)? | No. The premise is wrong in exactly one place out of fifteen; the design survives with a bounded addition. | `REJECT - NEEDS REPLAN`. Rejected because the core decision (`filelock`, one helper, migrate the sites) is unaffected, and the fix is one decision item plus a test, not a different decomposition. | mode census: 14 of 15 sites match the plan's premise; the byte-range argument for `filelock` is independent of this | yes |

### Edits applied

- `E-02`: added the non-re-entrancy REQUIREMENT with the measured evidence and the verified remedy.
- `E-03`: added the blocking-site carve-out, made it depend on E-07, corrected the expected outcome.
- `E-04`: added the same-process non-re-entrancy test obligation.
- `E-07` (new): decide and implement how the one blocking site keeps blocking, with a recommendation.
- `V-07` (new): evidence for E-07, requiring a two-process test that the writer still WAITS.
- `V-03`: now requires a test asserting the operator-facing string, not only a paste.
- `Findings`: added F7 (BLOCKER), F8 (HIGH), F9 (MEDIUM).
- `Project conventions`: corrected the false "every call site is non-blocking" claim with the census.
- `Scope check`: replaced "Under-scope: NONE OUTSTANDING" with the three real gaps found.
- `Open questions`: OQ-02 narrowed, with its false premise named rather than quietly removed.
- `Required tests`: added three mandatory assertions.
- Front matter: `Highest E allocated` 06 -> 07.

### Deferred and open

- (none) All four findings FIXED. No open questions remain.
