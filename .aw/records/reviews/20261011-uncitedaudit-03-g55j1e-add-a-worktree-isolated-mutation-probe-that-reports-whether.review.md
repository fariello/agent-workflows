# Review findings: plan g55j1e

- Subject-Id: g55j1e
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (LOW, fixed), PR-009 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `131f01291`. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` before review; `--phase
review-finalize`: `clean` after revision. Not an orchestrator (`- Kind: child`), so S407/S408 do not apply.

Demonstrations run at review in a detached worktree under `/tmp/opencode/` (added with `git worktree add --detach`,
removed with `git worktree remove --force`; `git worktree list` unchanged afterwards):
- `PYTHONPATH=<wt>` resolves `agent_workflows` to the worktree copy; a marker appended to the copy's `__init__.py`
  printed from `aw --version` run in `<wt>`, with and without `PYTHONPATH` (`checkout_pin.check_and_reexec`).
- `tests/test_run_freeze.py` from `19313eed^` passes unmutated (`12 passed in 0.15s`) and fails under a hand-applied
  `ast`-splice `raise` mutant of `freeze_requirements` (`12 failed in 0.20s`); the splice compiled.
- An import-time-raising module: without `--continue-on-collection-errors` -> `Interrupted: 1 error during
  collection`, exit 2, sibling test not run; with it and `-n 2` -> `1 passed, 2 errors`, junit XML holding the
  collection error twice with `classname=""`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A correctness (verdict logic) | Review demo (F-05); E-01 original pytest command (no `--continue-on-collection-errors`) | When a mutant breaks import, pytest interrupts the whole session. Every other node stays unrun and drops out of `mut_fail`, so the plan's rule "every collected node errors" could not be observed. The mutant would read as `killed` on one collection error, or as a shrunken run. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The command now requires `--continue-on-collection-errors`. Node ids form a set (xdist duplicates them). `killed-by-import` is redefined as "every newly failing id is a collection error". E-02 asserts that the unrelated test still runs. |
| PR-002 | HIGH | IN-SCOPE | A/D correctness (false kills) | F-03 (the bare suite has tens of failing nodes); E-01 `newly_failing = mut_fail - base_fail` | Flaky nodes that pass at baseline and fail in the mutant run would be credited as kills. Order 07's `guarded` verdict would then rest on noise. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 restores the original and re-runs only `newly_failing`. Ids that fail again go to `flaky` and are excluded from the kill. |
| PR-003 | MEDIUM | IN-SCOPE | C/G (mechanism unspecified) | E-01 ("splice the operator's replacement body at the body's indentation") | The splice was undefined for methods (qualname resolution), one-line defs, decorators and nested returns (`negate-return`), and was bundled with orchestration in one E-item. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-04 adds a pure `apply_operator`: replace the whole node via `ast.unparse` at `col_offset`, resolve dotted qualnames, leave nested scopes alone, and check that the result compiles. Unit tests are in E-02(a); V-04 is added. |
| PR-004 | MEDIUM | UNDER-SCOPE | E evidence / reachability | V-01 original (`-- tests/`, no control); F-07 | V-01 ran the whole suite twice (about 7 min) with no positive control. A `survived` there proves nothing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now runs (a) a positive control, `--extra-test 19313eed:tests/test_run_freeze.py`, which must be `killed` (demonstrated at review), and (b) a survivor run on the one surviving file naming `run_freeze`. |
| PR-005 | MEDIUM | IN-SCOPE | B/C isolation safety | `checkout_pin.check_and_reexec`; editable install | Nothing checked that the interpreter imports the mutated copy. A mis-resolved import would produce a silent false `survived`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | An isolation preflight now gives verdict `error`, reason `isolation`; E-02 tests it. |
| PR-006 | MEDIUM | IN-SCOPE | C/F (refusal semantics, shared checkout) | E-01 original ("Refuse (exit 2) if the main checkout's `git status --porcelain` changed"); AGENTS.md "Shared checkout" | In a shared checkout a co-worker's edit changes `git status`. Refusing would discard a valid result for something the probe did not cause, and it conflated exit 2 with usage errors. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The probe now records `checkout_status_changed` and warns (OQ-02). "Never writes to the checkout" is asserted on the fixture repo. |
| PR-007 | MEDIUM | UNDER-SCOPE | E testing | E-02 Expected outcome (`killed-by-import` "for example ... test-only operator hook"); no timeout/error/baseline-failing-extra/sensitivity tests; V-02 without sensitivity | The `killed-by-import` case was left to invention. `timeout`, `error` and "an extra test failing at baseline is not credited" were untested. V-02 only demanded a summary line. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now specifies a module-level `BOOT = boot()` fixture with an unrelated sibling test, plus timeout, isolation-error and baseline-failing-extra cases. The CLI is run as a subprocess. V-02 adds a scratch-copy sensitivity run. |
| PR-008 | LOW | OVER-SCOPE | F KISS | Scope, `noop` operator (F-08) | `noop` duplicated `return-none`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Dropped. Order 06 and Order 07 name no operator, so no consumer breaks. |
| PR-009 | LOW | UNDER-SCOPE | G execution contract; AGENTS.md no-dash rule; 3.1(5) | Gate paragraph; E-03; OQ-01 `Owner: none`; Required tests (no baseline capture) | The gate lacked a scope fence declaration, honesty rule, invariants and staged-set check. The README lacked the no-dash rule, OQ-01 named no owner, and nothing captured the execution-start baseline. `timeout`/`error` were unmapped by consumer `rq3q7v`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate is itemized. E-03/V-03 carry the no-dash rule. OQ-01 owner is set. A baseline capture is added. E-01 states that `timeout`/`error` are not guard evidence and cross-references `rq3q7v`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How is a function body replaced? | Replace the whole function node via `ast.unparse` at `col_offset`, then check that it compiles. | Splice body lines only. Rejected because it breaks on one-line defs. A regex is ruled out by P16 spirit and fragility. | Review demo: `ast` splice of `freeze_requirements` compiled and killed 12 tests. | yes |
| D-2 | Refuse when the invoking checkout's status changes? | No. Record it and warn. | Exit 2. Rejected because a co-worker's concurrent edits are expected. | AGENTS.md "Shared checkout"; OQ-02. | yes |
| D-3 | Confirm kills against flakiness? | Yes. Re-run newly failing ids unmutated. | Trust a single comparison. Rejected because tens of nodes fail at baseline (F-03). | F-03; rubric A. | yes |
| D-4 | Keep `noop`? | Drop it. | Keep it as an alias. Rejected because it is over-scope and no consumer names it. | Scope text; grep of Orders 06/07. | yes |
| D-5 | What does V-01's live survivor selection target? | `tests/test_agy_runipd_cli.py` plus a positive control on `tests/test_run_freeze.py`. | The whole `tests/` directory. Rejected because it runs about 7 min with no control. | `git grep -ln run_freeze -- tests`; review demo. | yes |
| D-6 | Where do `timeout`/`error` go for Order 07? | They are not guard evidence; Order 07 treats them as `unprovable`, cross-referenced from this plan. | Edit `rq3q7v` now. Rejected because it is outside this review's ledger. | `rq3q7v` Scope verdict mapping. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
