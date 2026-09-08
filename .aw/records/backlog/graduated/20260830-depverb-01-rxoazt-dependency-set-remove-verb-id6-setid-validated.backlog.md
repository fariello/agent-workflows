- Id: rxoazt
- Status: graduated
- Set: depverb
- Priority: high
- Work-Kind: feature
- Summary: No aw verb sets/removes dependencies for backlog items or specs, none removes a single edge, none accepts a setid target, and 'aw ipd dependencies set' accepts a dangling id6 pre-write (validated only later by aw check)

## Workflow history
- 2026-09-08 graduated (aw set): PARTIALLY GRADUATED: two of five gaps. Graduated to plan f6idxs (Set depverb, .aw/records/plans/pending/20260908-depverb-01-f6idxs-...ipd.md), which carries From-Backlog: rxoazt. This item carries no Blocks-Release, so the plan inherits none. Status graduated (design handed off), NOT done. ALL FIVE GAPS RE-VERIFIED LIVE 2026-09-08 at HEAD a2e0438a, so nothing is dropped as obsolete; the narrowing is about ownership and prerequisites. GAP 4 (validation not pre-write) reproduces exactly as filed: 'aw ipd dependencies set <plan> exists:backlog:zzzzzz --dry-run --yes' reports 'unchanged (dry-run)' and exits 0 although zzzzzz matches no artifact. GAP 2 reproduces: the subcommand choices are {set} only. GAP 1 reproduces: aw backlog new, aw backlog set and aw specs set each return zero matches for a dependency flag. GAP 3 reproduces AND today's behavior is CORRECT: 'exists:backlog:worksequence' is refused pre-write with 'exists target worksequence is not a 6-char base36 id6. Refusing before making changes.' exit 2, which is the grammar path working, so GAP 3 is a feature request rather than a defect. GRADUATED: GAP 4 (resolve every target through the shared selector resolver and refuse pre-write for all three edge forms executed:<id6>, exists:<type>:<id6> and state:<type>:<status>:<id6>, reusing the existing 'Refusing before making changes.' contract at status_set.py:1558) and GAP 2 (a remove subcommand that drops a single edge idempotently, errors when the named edge is absent unless --if-present is passed, and writes the explicit zero 'none' when the statement is emptied). The plan also implements the escape-hatch DECISION this item demanded rather than leaving today's accidental permissiveness: --allow-dangling, chosen over an unconditional existence requirement because authoring a Set parent-first with children named before they exist is routine here, and made LOUD (each dangling target named in the output) with the surviving aw check error as the fail-closed backstop. THIS ITEM'S OPEN QUESTION IS NOW ANSWERED BY EVENTS, which is the main change since filing. It asks whether this item should be MERGED INTO 2k42zu (worksequence) and says to decide before authoring. 2k42zu IS NOW done, closed 2026-09-05 by the execution of IPD i6015i (the aw next --order-by work) with that plan cited as its evidence. So there is no live sibling to merge into and this item correctly stays separate as the narrower CLI/validation item. DEFERRED, each with a reason recorded in the plan. GAP 1 (source-side dependency fields on backlog and specs): its stated blocker is GONE now that 2k42zu is done, and spec 25kzda section 2.92 sanctions it as a follow-on, but it is a DATA-MODEL change adding a field to two artifact types with its own validation, rendering, check rules and migration questions, so it is deferred on SIZE and deserves its own plan rather than riding along with a setter fix. GAP 3 (setid-valued edges): this item itself frames it as an undecided DESIGN QUESTION (a setid edge is one-to-many and its membership CHANGES when a plan joins the Set, so 'all current members' versus 'all members at evaluation time' must be specified deliberately), and its prerequisite is still open: sjsoqq (setiduniq, cross-type setid uniqueness) is open, so a setid edge could resolve ambiguously. Since today's refusal is correct, nothing is broken while this waits. GAP 5 (close-time dependency checking): this item states the decision is open (refused, warned, or allowed) and flags a hard constraint from 2k42zu that a close-time gate must not be able to disagree with aw attention; that is a policy design question about surface consistency, not a setter fix. THE ONE-EVALUATOR CONSTRAINT IS PRESERVED AND VERIFIED: spec 25kzda section 2.10 requires every surface to call check_engine.evaluate_ipd_dependencies and none to reimplement it, and I confirmed four surfaces already do (aw check at check_engine.py:2609, aw ipd lint at ipd_lint.py:1119, the runner preflight at oc_runipd.py:2651, and the staged-overlay hook at hooks/ipd_dependency_statement_gate.py:96); the plan's E-05 proves no second evaluator or private regex was added.
- 2026-08-30 created (aw backlog): No aw verb sets/removes dependencies for backlog items or specs, none removes a single edge, none accepts a setid target, and 'aw ipd dependencies set' accepts a dangling id6 pre-write (validated only later by aw check)

REQUESTED 2026-08-30 by the maintainer: "an `aw` command to set and remove dependencies via id6 or
setid; the id6/setid MUST be validated before it can be set or removed; dependencies MUST be able to
have no, one, or many dependent id6 or setid values; and runners, checkers, commit-hooks, etc. MUST
check against those before starting, running, closing, finishing, etc."

WHAT ALREADY EXISTS, so this is a GAP-CLOSING item and not a greenfield one. The `ipddeps` Set
(`r7xku3`, `g69y23`, `ovbnyq`, `mp88bl`, all executed) already shipped most of the requested model,
graduated from spec `25kzda`
(`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, sections 2.7-2.11):

- The FIELD: `- Item-Dependencies:` on an IPD, typed and id6-grounded, grammar
  `none` | `unresolved` | comma/space-separated `executed:<id6>` | `exists:<type>:<id6>` |
  `state:<type>:<status>:<id6>` with `<type>` in `ipd|spec|backlog`
  (`agent_workflows/ipd_schema.py:508-643`, `parse_item_dependencies`/`canonical_item_dependencies`).
- ZERO/ONE/MANY is ALREADY satisfied for plans: `none` is the explicit zero, and the value is a
  comma/space-separated list, so one and many both work. Verified:
  `canonical_item_dependencies('exists:backlog:2k42zu, exists:spec:zzzzzz')` returns that value.
- The SETTER: `aw ipd dependencies set <selector> [edges...]`, where a bare/`-`/`none` edge list
  clears (`agent_workflows/status_set.py:1425-1500`).
- ONE shared evaluator, `check_engine.evaluate_ipd_dependencies`
  (`agent_workflows/check_engine.py:2009`), consumed by every enforcement surface already:
  `aw check` (`check_engine.py:2213`), `aw ipd lint` (`ipd_lint.py:1058`), the runner preflight
  (`oc_runipd.py:2126`), and the opt-in staged-overlay pre-commit hook
  (`hooks/ipd_dependency_statement_gate.py:96`). Rules `check.ipd-dependency-{malformed,dangling,
  ambiguous,cycle,unresolved,findings-blocked}` are all `error` severity (`check_engine.py:184-213`).

So the parts of the request that are DONE are: the typed field, zero/one/many, a setter, and
runner/checker/commit-hook consumption. Do not rebuild those. FIVE genuine gaps remain.

GAP 1, THE SOURCE SIDE IS IPD-ONLY. `aw backlog new`, `aw backlog set`, and `aw specs set` have NO
dependency flag (verified 2026-08-30: `aw backlog new --help | grep -i depend` and the same for
`backlog set` and `specs set` all return nothing). A backlog item or spec can only ever be a
dependency TARGET, never a source. Spec `25kzda` section 2.92 DELIBERATELY deferred this ("Specs and
backlog items may be dependency targets. A later design may add source-side dependency fields to
those types, but the runner must not infer them from prose in v1"), so closing this gap is a
sanctioned follow-on, not a contradiction of the spec. This overlaps heavily with open item `2k42zu`
(`worksequence`), which asks the same question from the ordering angle and explicitly names
`evaluate_ipd_dependencies` as the thing that "might generalize"; RECONCILE WITH `2k42zu` BEFORE
DESIGNING, and consider closing one of the two as the duplicate.

GAP 2, NO REMOVE. There is no `remove`/`rm` subcommand: `aw ipd dependencies` exposes only `set`
(verified: `aw ipd dependencies remove bl9q3d` -> "invalid choice: 'remove' (choose from 'set')").
Today removing ONE edge from a many-edge statement means re-stating the whole list by hand, which is
exactly the hand-editing this repo's verbs exist to prevent, and it silently races a concurrent
edit. Wanted: remove a single edge idempotently, and error (not silently no-op) when the named edge
is absent, unless a `--if-present` style flag is passed.

GAP 3, NO SETID TARGETS. The grammar rejects a setid outright (verified:
`aw ipd dependencies set <plan> exists:backlog:worksequence` -> FAIL "exists target 'worksequence' is
not a 6-char base36 id6", nothing written, exit 2). Yet a setid is the natural unit for "wait for that
whole phase chain", and the `wtiso` Set today encodes exactly that as a hand-built strictly linear
seven-link id6 chain. DESIGN QUESTION, not a decided outcome: a setid edge is a ONE-TO-MANY edge whose
membership CHANGES when a plan is added to the Set, so it is semantically different from an id6 edge
and must be specified deliberately (does it mean all current members, or all members at evaluation
time?). Note also that cross-type setid uniqueness is NOT yet hard-enforced; that is open item
`sjsoqq` (`setiduniq`), so a setid edge could resolve ambiguously until `sjsoqq` lands. Treat
`sjsoqq` as a likely prerequisite.

GAP 4, VALIDATION IS NOT PRE-WRITE FOR EXISTENCE, which is the sharpest defect and directly
contradicts the requested "MUST be validated before it can be set". The setter validates GRAMMAR
before writing but does NOT validate that the target EXISTS. Verified 2026-08-30:

    $ aw ipd dependencies set .aw/records/plans/pending/20260828-wtiso-00-bl9q3d-...ipd.md \
        exists:backlog:zzzzzz --dry-run --yes
    - >  plan  20260828-wtiso-00-bl9q3d  [blocking]  unchanged  (dry-run)
    exit=0

`zzzzzz` matches no artifact (`aw find backlog zzzzzz` finds nothing), yet the setter accepts it.
Same for `executed:zzzzzz` and `state:backlog:done:zzzzzz` at the schema layer. The dangling edge is
caught only LATER, by `aw check`; confirmed in a throwaway repo:

    Issue: exists:backlog:zzzzzz: no backlog artifact has id6 zzzzzz
    - .aw/records/plans/pending
      1. 20260830-deptst-01-aaaaaa-probe.ipd.md

That is fail-closed at the repository gate, so nothing ships broken; the defect is that the ERROR
ARRIVES LATE, at a different surface, after the file is already written. Resolve the target in the
setter and refuse pre-write with the same "Refusing before making changes" contract the grammar path
already uses. Keep an explicit escape hatch decision: authoring a chain top-down may legitimately
need a forward reference to a plan that does not exist yet, so either require `--allow-dangling` for
that case or require the target to exist unconditionally, but decide it rather than leaving today's
accidental permissiveness.

GAP 5, "CLOSING/FINISHING" IS UNCHECKED. The request says dependencies must be checked before
closing/finishing, not only before starting/running. Today `evaluate_ipd_dependencies` gates
readiness and execution; the CLOSE direction is enforced only for the separate `Blocks-Release`
concern (`check_engine.evaluate_blocking_close`). Whether closing an item that others depend on
should be refused, warned, or allowed is an open decision. Note `2k42zu`'s warning against surfaces
that can contradict each other: a close-time dependency gate must not be able to disagree with
`aw attention`.

DESIGN CONSTRAINTS for whoever graduates this.

1. ONE evaluator. Spec `25kzda` section 2.10 is explicit: "All surfaces call this evaluator; none
   reimplements it." Any new source type or edge kind extends `evaluate_ipd_dependencies`; it does
   NOT get a parallel code path in the runner, the checker, or the hook.
2. Do NOT collide with the intra-plan `Depends on:` E-row field. They are different namespaces by
   design (spec section 2.8: an E-id is never legal in `Item-Dependencies`, an id6 never legal in an
   E row).
3. Do NOT collide with `Gate-Kind`/`Gate-Ref`, which is the item's OWN blocked state, nor with
   `Blocks-Release`, which points at a release. AGENTS.md already distinguishes these.
4. Honest limit to state, not to hide: a git pre-commit hook is local, not cloned, and skippable
   with `--no-verify`, so the portable authority stays `aw check` plus CI.

OPEN QUESTION FOR THE MAINTAINER, because it is a scope decision and not answerable from the repo:
should this item be merged into `2k42zu` (`worksequence`), which already owns the "generalize
dependencies beyond plans" question, or stay separate as the narrower CLI/validation item with
`2k42zu` owning the ordering semantics? Recommend deciding that before authoring a spec, so two
items do not graduate overlapping designs.
