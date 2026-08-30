- Id: y9lcem
- Status: graduated
- Blocks-Release: next
- Set: rundeps
- Priority: high
- Kind: bug
- Summary: The runner cannot read Item-Dependencies: oc_runipd matches only the legacy Dependencies/Depends-on field, so 11 pending plans declare edges the queue silently ignores and ordering falls back to Set/Order

## Workflow history
- 2026-08-30 graduated (aw set): design handed off to plan 8guhs0 (lanetruth-03, approved, carries From-Backlog: y9lcem and Blocks-Release: next); gate preserved via handoff, code not yet written so NOT done
- 2026-08-29 created (aw backlog): Found while reviewing spec 25kzda (SR-001). Measured: 22 pending plans declare Item-Dependencies, 0 use the legacy field, 11 declare real edges, and every wtiso queue item shows dependencies=[] at runtime. ipddeps-00 deferred runner preflight because 'aw <host> run does not yet exist', but it does and runs daily

ROOT CAUSE: the runner and the schema have TWO independent dependency parsers that read DIFFERENT field names, and only the schema's knows about `Item-Dependencies`. `oc_runipd._DEPS_RE` (oc_runipd.py:100) is `^-\s*(?:Dependencies|Depends-on):\s*(.+?)$`, so `_read_deps` (oc_runipd.py:811-821) never matches the canonical `- Item-Dependencies:` line. `_read_deps` additionally strips parenthesised text and keeps ONLY bare id6 tokens (`return [tok for tok in cleaned if ID6_RE.fullmatch(tok)]`), so even under a matching field name a typed edge like `exists:spec:d4e5f6` would be dropped and `executed:a1b2c3` would not survive as an id6.

MEASURED (same input, both parsers):
  sample = '- Item-Dependencies: executed:a1b2c3, exists:spec:d4e5f6, state:backlog:done:g7h8j9'
  oc_runipd._read_deps(sample)             -> []                        <- BLIND
  ipd_schema.parse_item_dependencies(...)  -> 3 typed ItemDependency edges

LIVE IMPACT (measured against the pending tree):
  - 22 pending plans declare `- Item-Dependencies:`
  - 0   pending plans use the legacy `Dependencies:`/`Depends-on:` field the runner reads
  - 11  declare REAL edges the runner cannot see, e.g. qcqhj7 -> `executed:8zgybk`,
        rchpms -> `executed:qcqhj7`, 7p9n2v -> `executed:rchpms`, 58ha43 -> `executed:7p9n2v`
  - run-20260829T190308Z-4123955 state.json: EVERY queue item has `dependencies: []` and `order: None`

CONSEQUENCE: the declared dependency DAG is inert at runtime. Queue ordering silently falls back to Set/Order, which spec 25kzda section 2.10 explicitly calls "only a tiebreaker" and NOT the authority. A phase can therefore be launched before its declared prerequisite is verified, with no error and no advisory: the runner does not know an edge was declared. It is a SILENT failure, not a fail-closed one, which is the opposite of the spec's stated posture.

WHY THE GAP EXISTS (not a spec defect): `ipddeps-00-r7xku3` deferred this deliberately and said so in its Scope: "EXPLICITLY DEFERRED to the runner program (not this Set): the runner's dependency-graph PREFLIGHT, skip-cascade semantics, and `--with-dependencies` closure (spec 2.9/5.4) - those live with `aw <host> run`, which does not yet exist. This Set makes dependencies STATABLE and CHECKABLE; the runner later CONSUMES them." The premise was that a NEW verb would consume the field. But `aw oc run` exists TODAY and is used daily, so the deferral did not leave a pending gap awaiting a new verb; it left a silent gap in a shipped one.

SPEC RECONCILIATION: spec 25kzda section 2.10 states one shared predicate drives five surfaces. Four are real (`check_engine.py`, `ipd_lint.py`, `ipd_set_plan.py`, and the `ipd-dependency-statement-gate` hook verb, all verified to reference `dependency_errors`/`item_dependency_cycles`). The fifth, runner preflight, has ZERO references in `oc_runipd.py` (`grep -c` for the predicate names and for `Item-Dependencies` returns 0). Section 1.2 step 3 ("Parse every IPD's mandatory `Item-Dependencies` statement, resolve stable IDs, reject malformed components, and build the queue DAG") describes behavior that does not exist.

FIX SKETCH: delete the runner's private parser and CONSUME the shared one. `oc_runipd` (and `agy_runipd`) must read `Item-Dependencies` via `ipd_schema.parse_item_dependencies` and evaluate satisfaction via the same shared predicate the other four surfaces use, so there is one implementation of the rules (the spec's explicit "all surfaces call this evaluator; none reimplement the rules"). Then implement the runtime semantics from spec 2.9/5.4: an unsatisfied `executed:`/`state:` edge to an in-queue target WAITS; a target outside the queue is evaluated from frozen repository state; an unsatisfied external edge cannot be met in this run. Preflight must FAIL CLOSED on a malformed/dangling/cyclic statement before any session starts, rather than proceeding with an empty dep list. Retain the legacy field only as an explicit migration path if any tracked plan still uses it (measured: none do), otherwise remove it so two names cannot diverge again.

RELATION: sibling of xd9sll (session/worktree granularity), tfx39h (nested aw runs the lane's own tool copy), and l6rh0z (begin's dirty gate measures the wrong tree). All four are the same class: the runner's model of lanes/queue diverging from what the repository declares. This one is the QUEUE-level instance.

REPRO: take any two pending plans where B declares `- Item-Dependencies: executed:<A-id6>`, then `aw oc run <set>`; inspect the run's state.json and observe `dependencies: []` for both, and observe B eligible to start without A verified.

TEST: (a) a plan declaring `executed:<id6>` yields a runner queue whose recorded dependency list contains that edge (not `[]`); (b) an item whose `executed:` prerequisite is unverified is NOT launched, and is recorded blocked/waiting rather than started; (c) a malformed or cyclic statement refuses the run at preflight with a named rule, before any host session starts; (d) an AST/import guard asserting the runner does not define its own dependency regex, so the two parsers cannot silently diverge again.
