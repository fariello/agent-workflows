---
id: fc2n5j
created: 20260808
set: attention-registry-spec-review
order: 02
topic: [attention-registry, spec-review, external-review]
model: sonnet5
kind: assessment
status: active
outcome: none-yet
summary: Sonnet-5 review of the attention-registry spec
consumed-by: []
---

# Review: attention registry and cross-tree status model (aw attention)

Reviewer: Claude Sonnet 5
Reviews-spec: .agents/docs/specs/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md

## A note on sourcing (established vs informed-inference)

Most of this review is architectural reasoning applied directly to the spec's own text - i.e.
informed inference from a senior-reviewer's engineering judgment, not claims drawn from
external literature. That is the right label for the bulk of it: e.g. "class_of is not pure
as specified" is derived by reading Sections 6 and 9 against each other, not from any
outside source. Two specific technical claims, however, rest on well-documented, citable
engineering practice rather than my own judgment alone, and are marked inline with [1]-[3]
and listed in the References section at the end: (1) that file modification time (mtime) is
an unreliable signal for build/registry determinism because common tooling (git checkout,
archive/packaging tools, CI clone steps) does not preserve it across machines or runs, and
(2) the "do one thing well, delegate rather than duplicate" argument against having one CLI
tool shell out to another tool's own command surface, which traces to the original Unix
philosophy literature on single-responsibility tools composed via well-defined interfaces
rather than internal cross-calling. Everything else - the class taxonomy critique, the
phasing contradiction, the acceptance-criteria gaps, the registry-shape recommendation - is
my own analysis of this specific spec and should be weighed as expert judgment, not as
something independently verifiable against a citation.

## (a) Overall assessment

The core move (keep each tree's native status enum, add one pure mapping to a small
tree-agnostic attention class, materialize a committed registry, make /whatnext a reader)
is the right shape of solution and is a clear improvement over runtime re-derivation. The
spec is unusually well scoped for a v1 (goals are testable, non-goals are explicit, phasing
exists). However, there are two load-bearing problems that should block sign-off as written:
first, Section 6's "pure function class_of(tree, native_status)" is not actually pure once
you read the deferred-with-gate-vs-deferred-as-decision split, which silently depends on
gate content, not just status; second, there is a real internal contradiction between the
Goals section (G4, write verbs, marked Must, unphased) and Section 13 (write verbs deferred
to Phase 2), which will cause disagreement about what "done" means for v1. Neither problem
is hard to fix, but both should be fixed before implementation starts, because the drift
gate's entire value proposition rests on the mapping function actually being pure and on
the phase boundary actually being unambiguous.

## (b) Strongest concerns, ranked

1. **class_of is not pure as specified.** Section 6 states the mapping is a pure function of
   (tree, native_status), then describes a deferred status splitting into needs-attention or
   parked depending on whether the gate is "an open gate" versus "a deliberate decision" -
   information that lives in the gate field, not the status field. This is either a spec bug
   (the function's actual signature is class_of(tree, native_status, gate_kind)) or a real
   design gap (how do you tell "open blocker" from "deliberate decision" from free text?).
   See Q1 and Q4 below.

2. **Write-verb phasing contradicts the Goals section.** G4 is listed as [Must] with no phase
   qualifier: "Provide write verbs... then refresh the registry." Section 13 says write verbs
   are Phase 2. Section 9 (F5, F6) lists the write-verb requirements as unphased Musts. Pick
   one. See Q7 and (d) below.

3. **--check is not wired into CI in Phase 1**, but Phase 1 is exactly when the registry is
   newest and least trusted. A registry that is not enforced from the moment it exists will
   start drifting the first time someone hand-edits a spec's Status line, which is likely
   given specs currently carry free-form prose. "Prevent drift by construction" (the spec's
   own framing) requires the gate to exist from day one, not Phase 2. See Q6 and Q7.

4. **Registry duplication (MD + JSON) is a second drift surface on top of the one the spec is
   trying to eliminate.** Nothing in the spec requires both files to be produced by a single
   regenerate() call and forbids independent regeneration; without that constraint, MD and
   JSON can diverge from each other even while each individually "matches" its own idea of
   disk state. See Q8.

5. **Acceptance criteria mix code-testable and behavior-testable claims**, and at least one
   (A1) hardcodes corpus-specific counts ("three deferred specs... two implemented specs")
   that will silently go stale. See Q10.

## (c) Answers to questions 1-10

### Q1: tree-agnostic mapping vs unified enum; critique of the four classes

Keeping native enums and standardizing only the mapping is correct. A single unified status
enum across plans/research/specs/prompts/comms would either have to be the union of all
existing enums (in which case it buys nothing over a mapping table, since most trees would
use a small subset and the union would be full of tree-specific dead states) or a genuine
lowest-common-denominator abstraction (in which case it loses exactly the distinctions each
tree's owning tool needs to do its own validation, e.g. plans' approved-vs-auto-approved
distinction, which the plan executor presumably cares about but /whatnext does not). Forcing
one enum onto tools that already have working, tool-validated enums is the more invasive and
more failure-prone change; the mapping-table approach is additive and reversible.

What breaks with a mapping-table approach: the mapping is now a second place that has to
change whenever a tree's enum changes, and there is no structural guarantee that it does (see
Q6). What breaks with a unified enum: every existing per-tree validator (aw plans, aw
research) would need to be rewritten or dual-write to two fields, which is a much larger,
higher-risk change for a lower payoff, and violates the stated non-goal "NOT replacing the
per-tree lifecycles or their enums."

On the four classes: needs-attention / in-flight / done / parked is a reasonable coarse
partition, but two things are underspecified:

- **done and parked are both "not moving," and /whatnext's usefulness depends on being able
  to tell them apart without opening the artifact.** A superseded plan (parked) and an
  executed plan (done) are both terminal, but "parked" carries an implicit "someone may
  revisit this" signal that "done" does not. That's fine as designed, but the spec should
  say explicitly that /whatnext's board treats parked as informational-only (never surfaced
  as needing action), or a maintainer could reasonably expect parked items to show up in a
  "needs a decision" view they don't currently have.

- **The deferred split (needs-attention if gated-and-open vs parked if gated-as-decision) is
  the purity violation flagged above.** As written it is not deducible from native_status
  alone. Either (a) split "deferred" into two distinct status values in the tree's own enum
  (e.g. deferred-blocked vs deferred-parked), which keeps class_of pure on status alone, or
  (b) explicitly widen the function's signature to class_of(tree, native_status, gate_kind)
  and document that widening in Section 6, rather than calling it pure over (tree, status).
  Option (a) is cleaner because it keeps the "pure over status" invariant that the rest of
  the spec (F1: "pure class_of covering every native status") relies on, and it makes the
  distinction a first-class, closed-enum fact instead of something parsed out of a free-text
  gate field.

### Q2: one roll-up registry vs per-tree + roll-up

One roll-up file for v1. The stated goal is a cheap single read for /whatnext and a stable
CI --check; a single file satisfies both directly. Per-tree registries plus a roll-up adds a
second reconciliation problem structurally identical to the MD/JSON duplication issue in
concern 4: now the roll-up can drift from the per-tree files, which is exactly the kind of
drift-of-a-derived-artifact the whole feature exists to prevent elsewhere. Given the current
corpus size (a handful of trees, ~8 specs plus existing structured trees), the performance
or attribution argument for per-tree files does not yet exist. If CI failure attribution
becomes a real pain point once specs grow, that is a reasonable Phase 3 reconsideration, not
a v1 requirement - but the spec should say this is a deliberate, revisitable choice (it
already leans this way in OQ3; promote that lean to a stated decision with a stated trigger
for revisiting it, e.g. "revisit if the registry exceeds N entries or if CI failures on the
roll-up are frequently misattributed to the wrong tree").

### Q3: write verbs vs tool-owned trees

Refuse-and-point, not delegate, for tool-owned trees (plans, research). Delegation sounds
convenient but creates a second maintenance surface: attention.py would need to track the
owning tool's CLI argument shape, its error codes, and its output format, and any change to
`aw plans set` (if it even exists as a verb) would need to be mirrored in the delegation
logic or attention.py silently breaks. Shelling out to your own CLI from within your own CLI
is also awkward from a testing and error-handling standpoint (parsing your own subprocess
output to decide what to tell the user), and runs against the general single-responsibility
argument for composing small tools rather than having one absorb another's surface. [3] Refusing with a clear pointer ("this artifact is
owned by aw plans; run `aw plans set <id> <status>` instead") is less code, has one place
that can drift (the pointed-to command name, which is cheap to keep current with a shared
constant), and matches the existing division of responsibility described in Non-goal
"NOT replacing the per-tree lifecycles or their enums." This also matches where OQ7 was
already leaning; the spec should just commit to it and delete the "delegates" branch from
Section 8.2, or explicitly scope delegation out as a rejected alternative with a one-line
rationale.

### Q4: expressing a gate

Do not overload a free-text Gate field to also carry the blocked-vs-decision distinction
(see Q1). Propose a two-field, closed-vocabulary contract:

```
Status: deferred
Gate-Kind: blocked | decision
Gate: <short human-readable reason, plus optional reference, e.g. "waiting-on:D07" or
       "waiting-on:TODO#42" or "decision:post-v2">
```

`Gate-Kind` is what class_of actually branches on (closed enum, two values, trivially
validated - a missing or unknown Gate-Kind on a deferred artifact is a contract violation
under F3, same bucket as missing/unknown Status). `Gate` stays free text for the human board
and is never machine-branched on; it is rendered verbatim next to the artifact in
ATTENTION.md and included as a string field in ATTENTION.json. This keeps class_of pure over
(tree, native_status, gate_kind) - a small, still-closed, still-deterministic input space -
rather than pure over status alone with gate content sniffed at render time.

### Q5: --check scope and CI pitfalls

The scope (registry-vs-disk drift, plus the contract violations: missing status, unknown
status, deferred-without-gate) is correctly drawn - that is exactly the set of things a
deterministic scanner can and should catch. Pitfalls to close before implementation:

- **last_history_date must be parsed from the history section content, not from file
  mtime.** [1][2] mtime is not preserved across git clone/checkout and will differ across CI
  runners and contributors' machines, producing spurious drift that has nothing to do with
  the artifact's actual state.
- **Sort/tie-break order for entries within a class must be fully specified** (e.g. path,
  lexical, ascending) so that regenerate() is byte-for-byte reproducible across runs and
  across machines; otherwise --check will flap on ordering alone, which is worse than not
  having the gate at all because it teaches contributors to ignore --check failures.
- **Line-ending and trailing-whitespace normalization** should be pinned (e.g. LF only, no
  trailing whitespace) given the artifact_core walker and atomic_write presumably already
  make this decision for the other trees; the spec should say attention.py reuses the same
  normalization rather than leaving it implicit.
- The spec should state explicitly that regenerate always does a **full rescan**, not an
  incremental update keyed off git diff, so that a deleted artifact's stale registry entry
  cannot survive a partial regen. (Section 8.1 implies this but does not say it.)

### Q6: where the registry silently diverges from truth, and how to prevent it by construction

- **Hand-edited Status/history without going through `set`/`note`.** Prevented by --check
  being wired into the same CI gate that already exists for `aw plans index --check` /
  `aw research index --check` (A5 checks those still pass but nothing checks that attention
  --check is itself gated anywhere - see concern 3).
- **Renamed/moved artifacts that bypass the git-mv helper.** The registry would keep a stale
  path. Prevented by requiring set/note (and any future move helper) to go through the same
  git-mv helper already used elsewhere, and by --check treating "path in registry, file
  absent on disk" as a first-class drift condition (this should be stated explicitly in F3,
  not left implicit under "registry-vs-disk drift").
- **A new tree or artifact type added to the repo but never wired into the scanner's tree
  list.** The walker will simply never visit it - no error, silent omission, and the
  omission looks identical to "this tree has nothing needing attention." Prevent by
  construction with an explicit, tested inventory check: a test that asserts the set of
  directories under .agents/ matches the set of trees the scanner knows about, failing
  loudly (not silently) when a new top-level tree appears without a corresponding mapping
  entry.
- **A tree's enum evolves (new status value added) without the mapping table being
  updated.** F1 already turns this into a contract violation (unknown -> drift) rather than
  a silent drop, which is the right default. Recommend going one step further
  architecturally: have each tree module (plans.py, research.py) own and export its own
  `ATTENTION_MAPPING` dict next to its own status enum definition, and have attention.py
  import and aggregate them, rather than centralizing every tree's mapping inside
  attention.py. This keeps the mapping physically adjacent to the enum it maps, so a
  developer adding a new plans status is far more likely to notice and update the mapping in
  the same file/PR, rather than needing to remember a separate module exists.

### Q7: is v1 phasing right?

Directionally yes - specs standardization plus scanner/registry over already-structured
trees plus whatnext-as-reader is a sensible first slice, and deferring the full write-verb
surface and walkthroughs/roadmaps adoption is reasonable scope discipline. Two changes:

1. **Resolve the G4/Section 13 contradiction** (concern 2). If write verbs really are Phase
   2, G4 needs a phase qualifier and F5/F6 need to move out of the unphased Musts list, or
   be marked "Phase 2" explicitly in Section 9. As written, a reader following Section 9
   would reasonably expect set/note to ship in v1.
2. **Move CI wiring of --check earlier**, out of Phase 2 and into the end of Phase 1, even
   if only as a lightweight pre-commit/CI stanza gating regenerate-and-diff. Without it, the
   window between "registry exists" and "registry is enforced" is exactly when the first,
   most damaging drift is likely to happen (specs still transitioning off free-form prose,
   contributors not yet in the habit of running `aw attention`).

A secondary gap: 8.3's /whatnext fallback/reconcile behavior ("keeping existing sources as
fallback... for what the registry cannot know") is nontrivial dual-source logic that could
reintroduce the exact token-cost problem the spec exists to solve if the fallback triggers
often, and it has no acceptance criterion (A6 does not test fallback behavior at all). Either
scope the fallback out of Phase 1 entirely (registry-only, no fallback, accept that
walkthroughs/roadmaps are simply invisible to /whatnext until Phase 3) or add an explicit,
testable acceptance criterion bounding when fallback triggers.

### Q8: simpler alternative

The class-mapping-plus-registry architecture itself is justified (see Q2's reasoning: without
a committed registry you're back to runtime re-derivation, which is the problem being
solved). The place to simplify is the dual MD+JSON output. Consider committing only
ATTENTION.json as the source of truth, and generating ATTENTION.md on demand (`aw attention
--render` or similar) rather than committing it - this removes one of the two
independently-driftable artifacts described in concern 4. The tradeoff is losing the
"glance at the board directly in the GitHub UI" convenience of a committed Markdown file,
which is a real goal (Section 5 describes a human maintainer reading .agents/ATTENTION.md
directly), so this may not be worth taking. If both are kept, the spec must add an explicit
requirement that MD and JSON are only ever produced together by a single regenerate() call
that writes both atomically, and that --check diffs both, not just one - this constraint is
currently implied but not stated as a requirement (add to F2/F3).

### Q9: naming, CLI ergonomics, existing surface

`aw attention` is fine, avoids the `aw status` collision, and reads naturally next to `aw
plans` / `aw research` / `aw ipd`. Two smaller points:

- `note` vs `set`: as written, `set` changes status and appends a history line, while `note`
  only appends a history line. That's a reasonable pair but the naming doesn't make the
  relationship obvious - a first-time reader could plausibly expect `set` to only touch
  status without also writing history. Either document this explicitly in the CLI help text
  (cheap) or rename `note` to something that signals "history-only," e.g. `log`, to pair more
  legibly with the "Workflow history" concept the spec already uses elsewhere.
- Confirm `--check` and `--agent` on `aw attention` follow the exact same flag semantics and
  exit-code convention as the existing `--check` usages on `aw plans index` / `aw research
  index` (the spec asserts reuse of Drift/render_agent_drift/drift_exit_code, which implies
  this, but Section 9 should state it as an explicit requirement rather than leaving it
  implied by "reuses the existing... convention").

### Q10: untestable/ambiguous/wrong acceptance criteria

- **A1** ("lists the three deferred specs... and the two implemented specs") hardcodes
  corpus-specific counts in prose. This will go stale the moment another spec is added or
  migrated, and as a general acceptance criterion (rather than a specific fixture-based test)
  it is ambiguous about whether it means "the current real corpus" or "a test fixture."
  Rewrite as a fixture-based test: construct a small synthetic set of specs with known
  statuses and assert the registry classifies them correctly, independent of the real
  corpus's current size.
- **A2** ("exits 0 after regenerate, nonzero after any hand-edit") - "any hand-edit" is too
  broad; a hand-edit that happens to be a no-op (e.g., reformatting that produces byte-
  identical output) would not trigger drift and the criterion as stated would be violated
  by a correct implementation. Narrow to "any hand-edit that changes a status or history
  field."
- **A4** bundles three distinct violation types (missing Status, unknown Status, deferred-
  without-gate) into a single acceptance criterion. Split into three so a regression in one
  is attributable without re-reading the others.
- **A6** ("/whatnext produces its board from the registry and reads only flagged artifacts
  thereafter") is a behavioral claim about an LLM-driven workflow, not something the
  unittest suite referenced in A7 can actually verify. Either reword A6 as a documentation/
  prompt-design requirement separate from the code-testable criteria A1-A5/A7, or replace it
  with a testable proxy (e.g., "the /whatnext prompt template's first read step references
  .agents/ATTENTION.json and no other source file path").
- **G4 vs Section 13** contradiction already covered in concern 2 - flagging again here
  because it also makes F5/F6 ("Must") inconsistent with their own acceptance criteria (A3
  tests `set`, which per Section 13 would not exist until Phase 2).

## (d) Concrete proposed spec edits, by section

- **Section 6**: Replace "a pure function class_of(tree, native_status)" with "a pure
  function class_of(tree, native_status, gate_kind)" and require Gate-Kind as a closed
  two-value field (blocked | decision) wherever Status is deferred, rather than inferring
  needs-attention-vs-parked from free-text gate content.
- **Section 6 / F1**: Add explicit note that "done" and "parked" are both terminal from
  /whatnext's perspective but differ in intent (parked = deliberately shelved, may be
  revisited; done = complete); state that /whatnext's board never treats parked as
  actionable.
- **Section 7 / Q4**: Add the two-field gate contract (Gate-Kind, Gate) as shown above,
  replacing the single implied "Gate:" field.
- **Section 8.2**: Remove the "delegates to the owning verb" branch; commit to refuse-and-
  point for tool-owned trees (plans, research), with the pointed-to command name centralized
  as a shared constant so it can't silently go stale.
- **Section 8.1 / F2, F3**: State explicitly that (1) regenerate always performs a full
  rescan, never incremental; (2) MD and JSON are only ever produced together by one
  regenerate() call; (3) --check diffs both files, not just one; (4) last_history_date is
  parsed from the artifact's history section, never from filesystem mtime; (5) entry
  ordering within a class is fully specified (e.g., lexical by path) so regenerate is
  byte-reproducible.
- **Section 9**: Resolve the G4 vs Section 13 phase contradiction - either mark G4, F5, F6 as
  Phase 2 explicitly, or move write verbs into Phase 1 in Section 13. Pick one and make
  Sections 3, 9, and 13 agree.
- **Section 9**: Add an explicit requirement that a top-level directory under .agents/ with
  no corresponding scanner/mapping entry is itself a contract violation caught by --check
  (prevents the "new tree silently invisible" failure mode from Q6), rather than a scanner
  that simply never visits unknown trees.
- **Section 13**: Move CI wiring of `aw attention --check` from Phase 2 to the end of Phase
  1 (even a minimal pre-commit/CI stanza), so the registry is enforced from the moment it is
  introduced rather than during the window before write verbs exist.
- **Section 8.3**: Either scope /whatnext's fallback-to-raw-read path out of Phase 1 entirely
  (registry-only), or add a testable acceptance criterion bounding when it triggers, so the
  token-cost problem the spec is solving cannot silently reappear via an unbounded fallback.
- **Section 10 (A1)**: Rewrite against a fixture, not the live corpus's current counts.
- **Section 10 (A2)**: Narrow "any hand-edit" to "any hand-edit of a status or history
  field."
- **Section 10 (A4)**: Split into three criteria (missing Status / unknown Status /
  deferred-without-gate-kind).
- **Section 10 (A6)**: Reword as a documentation/prompt requirement, or replace with a
  testable proxy on the /whatnext prompt template's source-of-truth ordering.
- **Section 11**: Add a note that each tree module (plans.py, research.py, the new specs
  status module) owns and exports its own attention-class mapping fragment, and attention.py
  imports/aggregates rather than centralizing all trees' mappings inside attention.py itself
  (reduces the risk in Q6 of a tree's enum evolving without its mapping being updated in the
  same place).

## (e) Smaller nits

- Section 3, G6: "ship in the importable package as aw attention and python -m
  agent_workflows attention" - confirm this matches the exact invocation pattern used by the
  other subcommands (e.g. is it `python -m agent_workflows attention` or `python -m
  agent_workflows.attention`); the spec should be unambiguous here since it will be copied
  verbatim into tests.
- Section 9, N6 ("no em/en dashes") is a stylistic constraint embedded in a requirements
  list alongside functional/non-functional engineering requirements; consider moving it to a
  style-guide reference rather than numbering it alongside N1-N5, since it is not the same
  kind of requirement and dilutes the list's testability.
- Section 12, OQ1: "does canonical map to done/implemented or its own value?" is still open
  in the spec under review but Section 6's prose already asserts "spec/canonical reference
  specs map to implemented" as if decided. Reconcile: either close OQ1 in favor of what
  Section 6 already states, or remove the premature statement from Section 6.
- Consider whether `note`/`log` should be restricted to artifacts that already have a
  Status field (i.e., can you `note` an artifact in a tree that hasn't been standardized
  yet, like a walkthrough in Phase 1)? The spec doesn't say what happens if you try to run a
  write verb against an out-of-scope tree; should be an explicit, tested error case.
- The spec's non-goal "NOT auto-committing beyond what a verb explicitly does" is good, but
  Section 8.2 should state explicitly whether `set`/`note` stage the change (`git add`) or
  merely write to the working tree, since "path-scoped-committable" is ambiguous between
  those two.

## References

[1] "Git Doesn't Set the Modification Time on Files at Checkout" - discusses how, per the
Git FAQ, Git deliberately does not preserve source file modification times on checkout (in
part so build systems relying on mtime, like make, behave predictably), meaning mtime at
checkout reflects clone/checkout time rather than any meaningful edit history.
https://www.scolby.com/2021/02/15/git-doesnt-set-the-modification-time-on-files-at-checkout/

[2] "GitHub Checkout Action Preserve File Modification Time" (Finisky Garden) - confirms
that by default, Git does not preserve file modification times, and that after a standard
checkout action the modification time reflects the current (checkout) time, not the file's
actual last-edit time; restoring "real" mtimes requires third-party tooling reading the git
log/reflog. https://finisky.github.io/en/github-action-to-restore-file-mtime/

[3] Doug McIlroy's original statement of the Unix philosophy ("Make each program do one
thing well... Expect the output of every program to become the input to another, as yet
unknown, program"), as collected on Wikiquote and discussed in Eric Raymond's "The Art of
Unix Programming" - the basis for preferring small tools with clear, stable interfaces over
one tool internally absorbing or shelling out to another tool's command surface.
https://en.wikiquote.org/wiki/Doug_McIlroy and
https://cscie2x.dce.harvard.edu/hw/ch01s06.html

Everything else in this review (the class-taxonomy critique, the purity-of-class_of
argument, the registry-shape recommendation, the phasing and acceptance-criteria findings)
is derived directly from the spec text under review, cross-referenced against itself, and
should be read as expert engineering judgment rather than externally sourced fact.
