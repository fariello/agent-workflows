# Spec: aw <host> run - deterministic run-and-verify with enforced cross-item dependencies

- Date: 2026-08-26
- Status: draft
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 25kzda
- Scope: the behavior of the single canonical runner verb `aw oc run` / `aw agy run`: selector
  resolution and mixed-type policy, per-type-and-status dispatch, deterministic repository-state
  verification per file type, a mandatory id6-grounded `Item-Dependencies` statement enforced through
  one shared predicate across `aw check`/lint/an opt-in commit hook/runner preflight/CI, per-host
  capability gating (fail-closed), containment-on-failure, and restartable durable run state. It does
  NOT specify the internal module filenames (they are being consolidated) nor commit the toolkit to a
  specific storage format; those are implementation details called out in Section 6.2.

This spec is the load-bearing design for the runner-consolidation and process-adherence work. It is
the product of a two-pass frontier-model design (initial design + a revision folding in four accepted
pushbacks and a new dependency-enforcement mechanism). It is authored as the single source of truth an
IPD Set (or Sets) can be graduated from and reviewed against. NET-NEW infrastructure it presumes -
`Item-Dependencies`, `From-Spec`, the hash-chained run ledger with `AW-Run:`/`AW-Item:` commit
trailers, the prompt `Run contract` block, the per-host capability descriptor, and the
`aw ipd dependencies`/`aw runs`/`aw hooks install` surfaces - does not exist yet and must be built;
this overlaps the agentadhere policy-engine/atomic-command phases, the bklggrad `From-Backlog` work,
and the runner rename. Constraints honored: pre-release (no backward-compatibility shims or legacy
aliases) and design-against-roles (no dependence on current internal filenames).

---

## 1. Executive summary

`aw oc run <selector>` and `aw agy run <selector>` are the only commands that drive repository work items through their lifecycles. `run` has exactly one meaning: resolve a typed work item or queue, build and validate its declared cross-item dependency graph, choose the next legal action from each item's type and status, prove that the selected host can enforce the action's safety requirements, ask the host agent to perform that action, run a fresh skeptical verification turn, and then let a deterministic checker decide whether repository evidence proves completion.

The agent's prose and exit status are never completion authority. Completion comes only from typed repository state, Git state, tool-authored lifecycle receipts, captured command evidence, declared dependency state, and deterministic checks. The host runner engine owns the queue and state machine. The deterministic checker is host-neutral and uses the same rules for interactive and unattended runs. Host execution is not assumed uniform: every action is gated by a current per-host capability descriptor.

This specifies only the clean final design. No alternate, deprecated, or transitional verbs exist.

### 1.1 Normative roles

- **The `run` verb**: `aw <host> run`. It resolves work items, creates a frozen queue, and requests the next legal action.
- **The host runner engine**: evaluates the host capability descriptor, launches and resumes host sessions, emits bounded action packets, records attempts, isolates item changes, enforces timeouts and tool policy, and manages a configurable retry budget.
- **The deterministic checker**: reads repository and run-ledger state, reruns registered checks, and alone authorizes `verified` and terminal transitions.
- **The executor**: the host agent session that performs an action. It may report what it did but cannot mark the action verified.
- **The skeptical verifier**: a fresh host session that looks for omissions and proposes evidence-backed findings. Its output is advisory until the deterministic checker reproduces each machine-testable assertion.
- **The lifecycle setters**: tool-owned operations that change statuses, append history, create approval or handoff receipts, and perform terminal moves.

### 1.2 Required execution sequence

Every actionable item follows this sequence:

1. Resolve and type the item.
2. Validate its current status and structure.
3. Parse every IPD's mandatory `Item-Dependencies` statement, resolve stable IDs, reject malformed components, and build the queue DAG.
4. Freeze identity, content digest, action, declared scope, baseline Git state, dependency requirements, retry policy, required host capabilities, and completion predicates.
5. Prove from the host capability descriptor that the host can enforce every required execution guarantee.
6. Acquire a single-writer lease for the item's declared paths and allocate its isolated worktree when mutation is possible.
7. Give the executor only the current bounded action packet.
8. Capture tool calls, outputs, changed paths, commits, and artifacts in a tamper-evident run ledger.
9. Launch a fresh skeptical-verifier session with the frozen predicates and observed diff.
10. Run the deterministic checker against repository state. Do not accept the verifier's conclusion as proof.
11. If the checks pass, use the appropriate lifecycle setter or terminal transaction and check again.
12. If item-local verification fails, contain its partial changes, fail only that item, cascade `dependency-not-met` to its dependents, and continue independent work.
13. Record the per-item outcome and release newly ready queue items.

### 1.3 Disposition of behavior previously bundled together

| Behavior | Final disposition | Reason |
| --- | --- | --- |
| Drive one IPD or an IPD queue through review, approval gates, execution, and verification | Part of `aw <host> run` | This is the central lifecycle-runner behavior. |
| Execute a tracked `.prompt.md` work item | Part of `aw <host> run` | It is a known work-item type and can use a declared run contract. |
| Author an IPD from an approved spec | Part of `aw <host> run` as the `approved` spec action | This is a status-driven lifecycle action, not a separate mode. |
| Graduate an open backlog item into an IPD | Part of `aw <host> run` as the `open` backlog action | It is a typed, deterministically checkable handoff. |
| Send one inline prompt string to a host | `aw <host> prompt --text <text>` | It is a one-shot host interaction, not a repository work-item lifecycle. |
| Send an arbitrary file as a one-shot prompt | `aw <host> prompt --file <path>` | An arbitrary file is not necessarily a known or verifiable work item. A tracked `.prompt.md` remains runnable through `run`. |
| Force IPD authoring from a spec regardless of status | Dropped | Status dispatch already supplies the safe action. A force mode would bypass review or approval gates. |
| Skip the audit or deterministic verification | Dropped | A command called `run` cannot claim success without verification. |
| Audit only | The host-neutral checker, `aw runs verify <run-id>`, or `aw <host> run --resume <run-id>` | Verification is a run-state operation, not another execution mode. |
| List or select host conversations | A host session-management surface, separate from `run` | Session administration does not execute a work item. |

The `prompt` verb may report transport success, but it must not emit `verified`, perform lifecycle transitions, or use the run-and-verify success exit code.

### 1.4 Resolution of the required revisions

| Revision | Resolution in this specification |
| --- | --- |
| A1: scope violation discipline | An out-of-scope mutation fails and quarantines only that item. Its dependents become `dependency-not-met`; independent queue items continue. `ABORT RUN` is restricted to six explicitly enumerated repository-wide integrity or safety classes. |
| A2: configurable retries | `--retry-budget <0..10>` overrides repository policy; repository policy overrides the default of 2. Zero means no automatic correction after the initial attempt. Non-retryable classes remain non-retryable at every budget. |
| A3: contractless-prompt exit policy | Verification remains `unavailable`. The default aggregate result remains non-success; `--unverifiable-ok` may treat an acknowledged, completed contractless prompt as neutral for aggregate exit-code calculation without relabeling it verified. |
| A4: host asymmetry | A current per-host capability descriptor is mandatory. Each action declares required enforcement capabilities and fails closed, item-locally, when the chosen host cannot supply them. Safety guarantees are classified as host-independent or host-dependent. |
| B: first-class dependencies | Every new or active IPD must resolve a top-level `Item-Dependencies` statement. One shared graph predicate drives `aw check`, phased IPD lint, the opt-in commit-scoped hook, runner preflight, and CI. Explicit dependencies govern readiness and skip cascades; Set/Order is only a tiebreaker. |

## 2. Selector resolution and mixed-type policy

### 2.1 Command grammar

```text
aw <host> run <selector>
    [--type <ipd|spec|backlog|prompt|research|release|walkthrough>]...
    [--allow-mixed]
    [--unattended]
    [--full-auto]
    [--allow-unverifiable]
    [--unverifiable-ok]
    [--follow-generated]
    [--with-dependencies]
    [--retry-budget <0..10>]
    [--action <review|plan|execute>]
    [--json]

aw <host> run --resume <run-id> [--json]
aw runs show <run-id> [--json]
aw runs evidence <run-id> [--json]
aw runs verify <run-id> [--json]

aw <host> prompt (--text <text> | --file <path>)
```

Rules:

- `<host>` is `oc` or `agy`.
- A new run accepts exactly one selector. A selector may resolve to one item or many items.
- `--resume` is mutually exclusive with a new selector and with flags that would change the frozen queue or policy. Resume uses the original host, queue, and options. A different host cannot resume the run.
- `--full-auto` implies `--unattended`. It does not imply `--allow-mixed`, `--allow-unverifiable`, `--unverifiable-ok`, `--follow-generated`, `--with-dependencies`, permission bypass, network access, hook bypass, or human approval.
- `--retry-budget` is an integer from 0 through 10 inclusive. It counts automatic correction attempts after the initial execution attempt. The CLI value overrides repository policy; repository policy overrides the default of 2. The frozen value cannot change on resume.
- `--unverifiable-ok` is legal only when contractless prompts were explicitly admitted by `--allow-unverifiable` or the interactive `run unverifiable` confirmation. It affects only aggregate success and exit-code calculation, never the item's outcome or verification label.
- `--with-dependencies` expands the selection to the transitive declared dependency closure before the queue is frozen. Any newly introduced type is subject to the same mixed-type gate. Without the flag, dependencies outside the selection are checked against current repository state but are not silently enqueued.
- `--action` is allowed only when every selected item has the same type and the requested action is legal from every item's current status. It cannot force a status transition, execute an unapproved item, or turn a non-runnable record into a runnable one.
- There is no `--no-verify`, `--skip-audit`, `--dangerous`, or hook-bypass flag on `run`.
- Before any actionable item starts, the engine loads a current capability descriptor for the exact host/version/mode and refuses the item if a required guarantee is unsupported, unverified, degraded below the required assurance, or stale.

### 2.2 Type vocabulary

The selector layer returns exactly one of these types for every file:

| Canonical type | Recognition authority |
| --- | --- |
| `ipd` | Canonical IPD filename grammar plus valid IPD metadata and location |
| `spec` | Canonical spec filename grammar plus valid spec metadata |
| `backlog` | Canonical backlog filename grammar plus valid backlog metadata |
| `prompt` | Canonical prompt filename grammar, normally `.prompt.md` |
| `research` | Canonical research filename grammar and research kind/status/outcome metadata |
| `release` | Canonical release filename grammar and release metadata |
| `walkthrough` | Canonical walkthrough filename grammar and records-tree location |

A filename suffix is not sufficient when a structured type has required metadata. If the suffix and parsed metadata disagree, resolution fails with `SELECTOR-TYPE-CONFLICT`; the runner must not guess.

### 2.3 Resolution algorithm

Resolution is pure and occurs before any host session starts:

1. Establish the repository root and reject paths outside it.
2. Determine the search domain:
   - `all` with no `--type` means all IPDs only.
   - One or more `--type` flags replace that default with the union of the named types.
   - A direct file path with no `--type` is typed from the file.
   - Any other selector with no `--type` is searched across all known types.
3. Apply the shared precedence: exact path, exact stable ID, exact set ID, exact status token, exact canonical stem, then filename substring.
4. Reject an ambiguous unique selector. An ID or canonical stem that matches more than one file is repository corruption, not a multi-item selection.
5. Deduplicate by `(type, stable identity, canonical path)`, not by spelling of the selector.
6. Parse and structurally validate every result.
7. Freeze the complete selected set before dispatch.

Zero matches return exit 2. Unknown or unclassifiable files return exit 2. Type/status structural errors return exit 4 and start no sessions.

### 2.4 `all` and explicit type targeting

Examples:

```text
aw oc run all
```

Selects IPDs only.

```text
aw oc run all --type spec
```

Selects specs only.

```text
aw oc run all --type ipd --type spec --type prompt
```

Selects all three types and therefore invokes the mixed-type policy.

`all` never implicitly grows to include a new artifact type added in a later release. A new type must be explicitly named until the user selects it.

### 2.5 Mixed-type gate

After resolution and before leases or sessions, the runner prints a sorted count and action preview. For example:

```text
Mixed work-item selection:
  IPDs:    4 (2 review, 2 execute)
  Specs:   2 (1 review, 1 plan)
  Prompts: 1 (1 execute)
```

- In an interactive terminal, the user must type the exact phrase `run mixed`. `y`, an empty response, and a generic confirmation are rejected.
- In unattended mode, mixed execution is refused unless `--allow-mixed` was present on the original command.
- `--allow-mixed` acknowledges only type mixing. All status, approval, prompt-verifiability, scope, and safety gates still apply.
- The confirmed type counts, action preview, user response or flag, and queue digest are recorded in the run ledger.

Exact refusal:

```text
[RUN-MIXED-TYPES] Selection contains <counts>. No work started. Review the selection, then run: aw <host> run <selector> --type <type> ... --allow-mixed
```

### 2.6 Overrides

Overrides narrow behavior; they never relax invariants.

- `--action review` permits an explicit re-review of a complete `reviewed` IPD or spec. The result remains `reviewed`, with a new tool-authored history receipt.
- `--action plan` is legal only for an `approved` spec or `open` backlog item.
- `--action execute` is legal only for `approved`, `auto-approved`, or `reusable` IPDs.
- `--follow-generated` adds newly generated IPDs to the same frozen run as explicit child queue entries. Without it, the new IPD is reported as a generated next action and is not silently executed.
- `--with-dependencies` changes selection, not satisfaction semantics. Every declared dependency is enforced whether or not its target was selected.
- No override may create human approval, ignore a gate, broaden scope after execution starts, skip verification, include uncommitted pre-existing edits in a run commit, push, or bypass hooks.

### 2.7 Mandatory cross-item dependency statement

Every IPD that is new, active, being advanced, or being executed must carry exactly one top-level metadata field named `Item-Dependencies`. It lives in the IPD metadata block immediately after `Scope-Paths` and before optional `Blocks-Release`, `From-Backlog`, or `From-Spec` fields.

Valid examples:

```markdown
- Scope-Paths: `src/widget/**`, `tests/widget/**`
- Item-Dependencies: none
```

```markdown
- Scope-Paths: `src/api/**`
- Item-Dependencies: executed:a1b2c3, exists:spec:d4e5f6, state:backlog:done:g7h8j9
```

Exact grammar:

```text
statement       = "none" | edge *( ", " edge )
edge            = executed-edge | exists-edge | state-edge
executed-edge   = "executed:" id6
exists-edge     = "exists:" target-type ":" id6
state-edge      = "state:" target-type ":" status ":" id6
target-type     = "ipd" | "spec" | "backlog"
id6             = 6 lowercase characters from the repository's stable-ID alphabet
status          = one legal bare status token for target-type
```

Semantic rules:

- `none` is an affirmative assertion by the author that the IPD has no cross-item prerequisites. It cannot coexist with an edge.
- A missing field means the author did not address dependencies and is never equivalent to `none`.
- `unresolved` is the scaffold placeholder. It is intentionally outside the valid execution grammar and makes the draft not ready for review or execution.
- `executed:<id6>` may target only an IPD. It requires verified terminal execution, not merely a file whose status text says `executed`.
- `exists:<type>:<id6>` requires one structurally valid target of the declared type. Its current legal status does not otherwise constrain the edge.
- `state:<type>:<status>:<id6>` requires one structurally valid target of the declared type in exactly the named legal status. `state:ipd:executed:<id6>` is invalid; use `executed:<id6>` so verification evidence is also required.
- A target may not be the source IPD itself. Duplicate semantic edges are invalid.
- Edges are written in canonical sort order by edge kind, type where present, status where present, and id6.
- An id6 must resolve uniquely across the declared target domain. Cross-type or same-type collisions are identity ambiguity and fail the run before execution.

The lifecycle-owned setter is the only supported writer:

```text
aw ipd dependencies set <ipd-selector> none
aw ipd dependencies set <ipd-selector> executed:<id6> exists:spec:<id6> state:backlog:done:<id6>
```

It validates tokens, canonicalizes ordering, writes one metadata line, appends a workflow-history receipt, and invokes the shared predicate before committing only the IPD and tool-owned index/history paths.

This field is different from each execution row's existing `Depends on: <E-ids|none>` value:

| Layer | Field | Target | Meaning |
| --- | --- | --- | --- |
| Whole work item | `Item-Dependencies` in top-level metadata | Stable id6 handles of IPDs/specs/backlog items | Conditions that must hold before this IPD as a whole may run |
| Within one IPD | `Depends on` inside an E item | E IDs in the same IPD | Step-order constraints after the IPD has become runnable |

The names, namespaces, and target grammars do not overlap. An E ID is never legal in `Item-Dependencies`; an id6 is never legal in an E row's `Depends on` field.

### 2.8 Scope of the mandatory field

The v1 mandatory requirement is IPD-only. IPDs authorize concrete repository mutation and therefore need a complete prerequisite declaration before review and execution. Specs and backlog items already express their most important relationships through status gates, `Gate-Kind`/`Gate-Ref`, `From-Spec`, `From-Backlog`, and `Blocks-Release`; making them declare their own dependency lists in v1 would add a second graph before its semantics are needed.

Specs and backlog items may be dependency targets. A later design may add source-side dependency fields to those types, but the runner must not infer them from prose in v1.

### 2.9 Dependency satisfaction

For an IPD to become runnable, every edge must be satisfied against the frozen repository and run state:

| Edge | Satisfied when |
| --- | --- |
| `executed:<id6>` | The target resolves uniquely to an IPD, is in `executed/` with status `executed`, passes terminal lint, and has valid deterministic execution/finalization evidence. If it is in this run, its current outcome is `verified`. |
| `exists:<type>:<id6>` | Exactly one target of the named type exists and passes that type's structural checker. |
| `state:<type>:<status>:<id6>` | Exactly one target of the named type exists, passes its structural checker, and has exactly the required status. |

An `exists:` edge is evaluated immediately from current repository state and does not wait for the target to run. An already-satisfied `state:` edge is also immediately releasable, but the scheduler must execute the dependent before it advances the target away from that required state. An unsatisfied `state:` or `executed:` edge targeting an item in the same run waits until the target reaches the required verified state. A target outside the queue is evaluated from frozen repository state. `--with-dependencies` may add the target and its transitive dependencies before freezing; without it, an unsatisfied external target cannot be met in this run.

### 2.10 One shared dependency predicate and rule family

One pure shared evaluator consumes a repository snapshot, staged overlay when applicable, IPD path set, phase, and dependency-cutover marker. It parses every statement once, resolves IDs once, constructs one directed graph, and returns these stable findings. Every edge from an IPD to another IPD participates in cycle validation regardless of qualifier; spec and backlog targets are leaves in v1 because those types have no source-side dependency field. All surfaces call this evaluator; none reimplement the rules.

| Stable rule ID | Severity | Assurance class | Condition | Exact recovery command |
| --- | --- | --- | --- | --- |
| `check.ipd-missing-dependency-statement` | error for every post-cutover IPD and for any plan at review-readiness/pre-execution/pre-transition; advisory for a pre-cutover draft or eligible terminal plan at the repository-wide author check | structural; `grandfathered` for the eligible advisory case | Field is absent where mandatory for the current provenance/phase | `aw ipd dependencies set <id6> none` after actually assessing dependencies, or `aw ipd dependencies set <id6> <edge>...`; then `aw check plans` |
| `check.ipd-dependency-unresolved` | advisory on a scaffolded `draft` at author phase; error at review-readiness, pre-execution, and pre-transition | readiness | Value is `unresolved` or another authoring sentinel | `aw ipd dependencies set <id6> none` or `aw ipd dependencies set <id6> <edge>...`; then `aw ipd lint <id6> --phase author` |
| `check.ipd-dependency-malformed` | error | structural | Grammar, canonical ordering, type/status pairing, duplicate, `none` mixture, or self-edge is invalid | `aw ipd dependencies set <id6> <canonical-edge>...`; then `aw check plans` |
| `check.ipd-dependency-dangling` | error | referential | A typed id6 has zero matches | Correct or remove the edge with `aw ipd dependencies set <id6> <edge>...`; then `aw check all` |
| `check.ipd-dependency-ambiguous` | fatal | identity | A typed id6 has multiple matches or a supposedly global executed id6 is cross-type ambiguous | Repair the duplicate stable identity, then `aw check all` |
| `check.ipd-dependency-cycle` | error | graph | One or more declared IPD-to-IPD edges form a directed cycle, including a longer cycle | Break an incorrect edge with `aw ipd dependencies set <id6> <edge>...`; then `aw check plans` |

`fatal` here maps to the allowed run-wide identity/type ambiguity class. Other dependency findings fail only the affected graph component before execution; they do not abort independent components.

The same predicate appears through all enforcement surfaces:

| Surface | Required behavior |
| --- | --- |
| `aw check` and CI | Repository-wide portable authority. Report every non-grandfathered missing, unresolved, malformed, dangling, ambiguous, and cyclic statement in deterministic path/rule order. CI fails on error/fatal. |
| `aw ipd lint` author phase | New/post-cutover missing fields are errors. The scaffold value `unresolved` is an advisory that makes readiness false but still permits an honest draft stub. Well-formed edges receive per-plan referential checks and graph checks against the repository snapshot. |
| `aw ipd lint` review-readiness, pre-execution, and pre-transition phases | Missing, `unresolved`, malformed, dangling, ambiguous, or cyclic statements are blocking. The frozen statement must also equal the reviewed statement at execution time. |
| Opt-in local pre-commit hook | The `ipd-dependency-statement-gate` is commit-scoped and type-scoped to staged `.ipd.md` files. Evaluate the staged overlay plus HEAD for resolution/graph context. Fail only when a staged IPD is invalid or its staged edges introduce or participate in a cycle. Delegate directly to the shared evaluator and print the same rule IDs/recovery commands. Never make unrelated pre-existing findings block an unrelated commit. |
| Runner preflight | Evaluate the selected dependency closure before host sessions. Fail malformed/dangling/cyclic source items; mark their transitive dependents `dependency-not-met`; continue disconnected valid components. Abort the run only for identity/type ambiguity. |

The hook is local and opt-in. It improves immediate feedback but is not portable authority; `aw check`, runner preflight, and CI are authoritative and use the same evaluator.

The user-facing installation command is:

```text
aw hooks install ipd-dependency-statement-gate
```

### 2.11 Grandfathering and deterministic author pressure

The repository records one dependency-schema cutover commit in its policy. Treatment is exact:

- Any IPD created at or after the cutover must contain `Item-Dependencies`. The scaffold emits `- Item-Dependencies: unresolved` in the correct metadata position.
- A pre-cutover terminal IPD in `executed/`, `superseded/`, or `not-executed/` may remain without the field. The shared evaluator emits an advisory with assurance `grandfathered`; always-on author metadata does not mass-fail the historical corpus.
- A pre-cutover pending IPD may remain an honest draft without the field, but it cannot advance to `to-review`, pass review-readiness, begin execution, or reach pre-transition until an author resolves the field.
- A pre-cutover reusable IPD must resolve the field before its next run instance.
- No tool bulk-inserts `none`. That value is an affirmative dependency assessment and cannot be manufactured from absence.

The authoring and runner path forces an actual decision deterministically:

1. Scaffold writes `unresolved`, never blank and never `none`.
2. Draft-readiness reports the exact blocking rule.
3. The lifecycle setter refuses `to-review` while the value is missing or unresolved.
4. Pre-execution and pre-transition lint invoke the same predicate again.
5. The deterministic checker refuses review completion, approval, or execution when the frozen statement is invalid or unresolved.

The author must therefore state either `none` or concrete id6-grounded edges. A prose reminder cannot satisfy the gate.

## 3. Per-type dispatch table

### 3.1 Shared dispatch rules

After every verified action, the dispatcher reads the item's new repository state and dispatches again until one of these occurs:

- the item reaches its action-specific verified endpoint;
- a human gate is reached;
- the item is skipped as non-runnable;
- the item fails; or
- a generated child is recorded but excluded because `--follow-generated` was not selected.

Thus, a complete draft IPD may be reviewed and, under `--full-auto`, truthfully marked `auto-approved` and executed in the same run. Every intermediate transition is separately checked.

Before dispatch, two fail-closed gates apply to every actionable item:

1. Its declared dependency edges must be valid and satisfied. An invalid source item fails preflight; an unmet but valid dependency produces `dependency-not-met` without a host session.
2. The selected host's current capability descriptor must prove every host-dependent requirement for the action. An unavailable capability produces item failure `host_capability_unavailable`; its dependents cascade, while independent items continue.

### 3.2 IPDs

| Status and condition | Interactive action | Unattended action | Forbidden unattended |
| --- | --- | --- | --- |
| `draft`, authoring-completeness check fails, including missing or `unresolved` `Item-Dependencies` | Yellow skip: identify each unresolved placeholder, dependency decision, or missing section. | Same skip. | Authoring content or asserting `none` by guessing intent. |
| `draft`, authoring-completeness check passes | Tool-set `to-review`; run plan review; apply corrections; tool-set `reviewed`; redispatch. | Same. Under `--full-auto`, redispatch may continue through `auto-approved` to execution. | None beyond normal gates. |
| `to-review` | Run plan review; apply corrections; tool-set `reviewed`; redispatch. | Same. Under `--full-auto`, redispatch may continue. | None beyond normal gates. |
| `reviewed`, default | Ask for explicit approval. If approved, tool-set `approved` with a human receipt and execute. If declined, stop `needs_input` or `skipped`. | Stop `needs_input`. Exact recovery names the human approval command. | Self-approval or treating model approval as human approval. |
| `reviewed`, `--full-auto` | Tool-set `auto-approved` with a run receipt and explicit automated-approval message, then execute. | Same. | Writing `approved`, an `Approval:` human field, or a human actor receipt. |
| `approved` | Check `Item-Dependencies`; when satisfied, execute and verify. If not met, skip `dependency-not-met`. | Same. | Executing before dependencies or required host capabilities are satisfied. |
| `auto-approved` | Check `Item-Dependencies`; when satisfied, execute and verify; display that approval was automated. If not met, skip `dependency-not-met`. | Same. | Relabeling it as human-approved or bypassing dependencies. |
| `reusable` | Check `Item-Dependencies`; execute one frozen run instance. Keep the source IPD in `reusable/` with status `reusable`. | Same. | Moving it to `executed/`, bypassing dependencies, or overwriting its standing validation history with instance results. |
| `executed` | Yellow skip: already executed. Recheck structural integrity only. | Same. | Re-execution or editing the executed plan. |
| `superseded` | Yellow skip with successor/reason when recorded. | Same. | Execution. |
| `not-executed` | Yellow skip with retirement reason. | Same. | Execution. |
| Unknown status or directory/status mismatch | Red abort before sessions start. | Same. | Any repair by inference. |

The deterministic authoring-completeness check, not an LLM, distinguishes a complete `draft` from a stub. It is the author-phase IPD parser plus the shared dependency evaluator and a closed placeholder vocabulary. It requires all mandatory metadata, a resolved `Item-Dependencies` statement, sections, E/V rows, E/V bijection, commands or concrete validation methods, resolved open questions, and no template sentinel.

### 3.3 Specs

| Status and condition | Interactive action | Unattended action | Forbidden unattended |
| --- | --- | --- | --- |
| `draft`, incomplete | Yellow skip with deterministic completeness findings. | Same. | Inventing missing requirements or decisions. |
| `draft`, complete | Tool-set `to-review`; run spec review; apply corrections; tool-set `reviewed`; redispatch. | Same, then stop at the approval gate. | Human approval. |
| `to-review` | Run spec review; apply corrections; tool-set `reviewed`; redispatch. | Same, then stop at the approval gate. | Human approval. |
| `reviewed`, default | Ask the human to approve, reject, or stop. On approval, write a human approval receipt, tool-set `approved`, and redispatch. | Stop `needs_input`, including under `--full-auto`. | Any synthesized or automated approval. |
| `reviewed`, `--action review` | Re-review; keep `reviewed`; append a review receipt. | Re-review; keep `reviewed`; append a review receipt. | Approval. |
| `approved` | Author exactly one conformant IPD linked by `From-Spec`; preserve `Blocks-Release`; tool-set spec to `implementing`; verify. | Same. Do not run the generated IPD unless `--follow-generated` is present. | Modifying the approved requirements while authoring. |
| `implementing` | Resolve all `From-Spec` IPDs. Dispatch their legal actions as child queue items, subject to their own approval gates. When all are verified `executed`, tool-set spec to `implemented` with resolvable evidence. | Same, except genuine human gates stop `needs_input`. | Marking `implemented` from model prose, a pending plan, or an unresolved citation. |
| `implemented` | Yellow skip; validate evidence links and structure. | Same. | Reimplementation or leaving the terminal state implicitly. |
| `deferred` | Yellow skip and display `Gate-Kind`/`Gate-Ref`. | Same. | Ignoring the gate. |
| `parked` | Yellow skip. | Same. | Review, approval, planning, or implementation. |
| `superseded` | Yellow skip with successor/reason when recorded. | Same. | Further lifecycle work. |
| Unknown status | Red abort before sessions start. | Same. | Repair by inference. |

`From-Spec: <spec-id6>` is required on every IPD generated from a spec. It is a first-class cross-tree invariant, parallel to `From-Backlog`, and must be supported by the IPD schema and cross-tree checker.

### 3.4 Backlog items

| Status | Interactive action | Unattended action | Forbidden unattended |
| --- | --- | --- | --- |
| `open` | Author exactly one conformant IPD with `From-Backlog`; copy `Blocks-Release`; close the backlog item as `done` using the handoff receipt; verify. | Same. Do not run the generated IPD unless `--follow-generated` is present. | Closing the backlog item before the conformant handoff exists. |
| `blocked` | Yellow skip; print `Gate-Kind` and `Gate-Ref`. | Same. | Ignoring or clearing the gate. |
| `parked` | Yellow skip. | Same. | Graduating or executing it. |
| `done` | Yellow skip; validate its evidence or handoff. | Same. | Reopening or duplicating its IPD implicitly. |
| Unknown status or malformed typed gate | Red abort before sessions start. | Same. | Repair by inference. |

Graduation, rather than direct implementation, is the safe default. Backlog items are deliberately too light to authorize code changes. The IPD adds scope, execution steps, validation, review, and approval gates.

### 3.5 Prompt files

| Condition | Interactive action | Unattended action | Forbidden unattended |
| --- | --- | --- | --- |
| Valid run contract | Prove required host capabilities; execute exactly one task turn; run a fresh skeptical turn; deterministically verify the contract. | Same. | Any mutation outside the declared scope, unregistered check command, or execution on a host lacking required enforcement. |
| No run contract | Warn that task success is not deterministically decidable. Require the exact phrase `run unverifiable`; execute and report final state `ran`, verification `unavailable`. By default it makes aggregate exit non-success; `--unverifiable-ok` may make it neutral. | Refuse unless `--allow-unverifiable`; if allowed, execute but never report `verified`. Default aggregate exit is non-success; `--unverifiable-ok` may make it neutral. | Claiming verification, lifecycle transitions, an automatic commit, or changing the item label because of `--unverifiable-ok`. |
| Invalid run contract | Red fail before execution with parse findings. | Same. | Guessing the intended contract. |

A prompt remains free-form prose, but may contain this optional deterministic section:

```markdown
## Run contract

- Scope-Paths: `src/widget/**`, `tests/widget/**`
- Change-Policy: required
- Expected-Paths: `src/widget/api.py`, `tests/widget/test_api.py`
- Check-Recipes: `widget-unit`, `repo-structure`
- Commit: required
```

Normative fields:

- `Scope-Paths` uses the IPD scope grammar.
- `Change-Policy` is `required`, `forbidden`, or `optional`.
- `Expected-Paths` may be omitted. If present, every listed path must exist after the run and must have the declared digest when a digest is supplied.
- `Check-Recipes` names repository-controlled argv-list recipes. Prompt text cannot provide shell strings.
- `Commit` is `required` or `forbidden`. A mutating unattended prompt must use `required`.

### 3.6 Research artifacts, release records, and walkthroughs

| Type/status | Interactive action | Unattended action | Forbidden unattended |
| --- | --- | --- | --- |
| Research prompt or document, any valid `status`/`outcome` | Gray skip: research artifacts use the research workflow and are not coding-runner work items. | Same. | Executing research prose, changing status/outcome, or fabricating a report. |
| Release record `planned`, `blocked`, or `shipped` | Gray skip: release records are gates, not executable instructions. | Same. | Shipping, unblocking, tagging, publishing, or pushing. |
| Walkthrough, no status | Gray skip: narrative evidence has no execution semantics. | Same. | Treating narration as an instruction or completion proof. |

A file whose kind is `research-prompt` is intentionally not treated as a generic prompt. Research has different tools, provenance, output siblings, and status/outcome semantics. The user can invoke the research workflow explicitly. Likewise, release and walkthrough records remain inspectable dependencies and evidence sources, never executable payloads.

## 4. Per-type deterministic verification checklists

### 4.1 Message and recovery conventions

Every finding has a stable code. The exact messages below are templates; `<...>` placeholders are replaced with quoted concrete values. Every recovery message ends with a command.

Common command templates:

```text
RESUME = aw <host> run --resume <run-id>
SHOW   = aw runs show <run-id>
PROVE  = aw runs verify <run-id>
```

Failure actions mean:

- **ABORT RUN**: stop all dispatch only for one of the six explicitly enumerated repository-wide integrity or safety classes below.
- **FAIL ITEM**: stop the item, capture and contain its partial changes, mark it failed, cascade `dependency-not-met` to its dependents, and continue independent queue items.
- **RETRY**: enter `correction_required`, issue a bounded correction packet, and retry the checker while the frozen retry budget remains. The default correction budget is 2; the valid frozen range is 0 through 10.
- **SKIP ITEM**: start no host session and make no mutation for this item.
- **SKIP DEPENDENCY-NOT-MET**: start no host session, record the unmet edge and root-cause chain, propagate the skip to dependents, and continue independent items.
- **NEEDS INPUT**: persist the item at its human gate, mark its current dependents `dependency-not-met`, and continue independent queue items. The aggregate run reports exit 3. Resume gated and cascaded items only after the recorded decision or external lifecycle command.

#### Exhaustive `ABORT RUN` set

No other finding may abort the whole queue.

| Abort class | Why item-local continuation is unsafe or meaningless |
| --- | --- |
| Corrupt run ledger | The engine cannot trust queue state, ownership, evidence, attempts, or prior dispositions. Continuing could repeat completed work or commit unowned changes. |
| Ownership or lease conflict | The engine cannot attribute overlapping paths to one item or actor. Item-local restoration could destroy another actor's work. |
| Unknown or non-idempotent external outcome | Repetition may duplicate an irreversible external side effect; continuation may build on an unknowable state. |
| Push attempt | A prohibited remote side effect may have escaped the repository boundary. Local containment cannot restore the remote safely. |
| Hook-bypass attempt | The execution boundary was deliberately subverted. Other captured guarantees from that run are no longer trustworthy. |
| Identity or type ambiguity | The engine cannot know which durable item, status authority, dependency node, or scope applies. Dispatch and containment would target an uncertain object. |

An item-local error that later reveals one of these six classes is reclassified to that abort class. For example, an out-of-scope change is normally item failure; if the engine cannot restore it without touching another lease, the condition is an ownership conflict and the run aborts.

#### Failed-item containment transaction

Before the engine continues past any mutating item failure, including a scope violation, it must complete this deterministic containment transaction:

1. Terminate the item's executor and revoke its ability to launch tools.
2. Freeze and hash the full isolated-worktree diff, untracked-file manifest, command evidence, and candidate commits into a quarantine evidence bundle.
3. Prove that the bundle's paths belong to this item and do not overlap pre-existing changes, another lease, or coordinator-owned state.
4. Restore tracked item paths in the isolated worktree to the frozen baseline and remove only untracked paths proven to have been created by this item. Never use a repository-wide restore target.
5. Recompute the worktree/index/path digests and require exact equality with the item's baseline for every restored path.
6. Prove that no item commit was integrated into the main worktree. If one was integrated, apply a deterministic inverse only when ownership and parentage are unambiguous; otherwise classify as ownership conflict or unknown outcome and abort.
7. Tear down the isolated worktree, release its leases, record `contained: true` and the quarantine digest, then fail the item and propagate its dependency outcome.

If step 3, 5, or 6 cannot be proved, the engine must not continue. The failure is no longer a simple scope violation; it is one of the enumerated run-wide ownership or unknown-outcome classes.

### 4.2 Checks common to every actionable type

| Check | What is inspected | Pass criterion | Exact failure message and recovery command | Action |
| --- | --- | --- | --- | --- |
| `RUN-FROZEN-IDENTITY` | Canonical path, stable ID, type, content digest, and action packet digest at each step boundary | Current item is the same frozen identity; any content change is explained by a completed prior step and followed by a new freeze event | `[RUN-FROZEN-IDENTITY] <item> changed outside its recorded step. Contain the item and inspect identity/ownership with: aw runs show <run-id>` | FAIL ITEM after containment; ABORT RUN only for identity/type ambiguity or ownership conflict |
| `RUN-STRUCTURE-PREFLIGHT` | Type parser and type-specific structural checker | File has one known type, one legal status when applicable, and valid required metadata | `[RUN-STRUCTURE-PREFLIGHT] <item> violates <finding-code>: <detail>. Repair it, run aw check <type> <selector>, then: aw <host> run --resume <run-id>` | FAIL ITEM; ABORT RUN if identity/type is ambiguous |
| `RUN-BASELINE-OWNERSHIP` | Starting HEAD/index/worktree snapshot, pre-existing dirty paths, active path leases | No pre-existing or concurrently leased path overlaps this action's mutation scope | `[RUN-BASELINE-OWNERSHIP] <paths> already contain unowned changes or an active lease. Resolve the owner or wait, then: aw <host> run --resume <run-id>` | ABORT RUN |
| `RUN-LEDGER-INTEGRITY` | Append-only event sequence, schema, record hashes, parent links, packet/evidence digests | Ledger is parseable, monotonic, hash-valid, and all referenced evidence exists | `[RUN-LEDGER-INTEGRITY] Run <run-id> has invalid or missing ledger evidence at <record>. Inspect it with: aw runs verify <run-id>` | ABORT RUN |
| `RUN-HOST-CAPABILITY` | Current descriptor for exact host/version/mode, capability evidence, expiry, and action requirements | Every required host-dependent guarantee is positively supported by current evidence at the required assurance | `[RUN-HOST-CAPABILITY] Host <host> cannot enforce <capability> required by <item> action <action>. No work started for this item. Choose a capable host or enable and re-probe that capability, then run: aw <host> run <selector>` | FAIL ITEM; cascade dependents; continue independent items |
| `RUN-HOST-ATTEMPT` | Captured argv-list launch event, timeout/cancel state, exit code, stdout/stderr hashes, terminal envelope | Host process was launched by the engine, did not time out, exited 0, and returned a valid evidence-linked envelope | `[RUN-HOST-ATTEMPT] <item> has no valid completed host attempt: <detail>. Inspect evidence, then retry with: aw <host> run --resume <run-id>` | RETRY for spawn/nonzero failures; FAIL ITEM for timeout, cancellation, or exhausted budget |
| `RUN-FRESH-VERIFIER` | Verifier session ID, parentage, packet digest, verifier findings envelope | Verifier used a fresh session with no executor-session inheritance and addressed the frozen predicates | `[RUN-FRESH-VERIFIER] <item> has no valid independent verification attempt. Retry verification with: aw <host> run --resume <run-id>` | RETRY, then FAIL ITEM |
| `RUN-SCOPE-DELTA` | `git diff` and untracked paths from the step baseline through the candidate terminal commit | Every action-owned changed path matches the frozen scope; pre-existing and other-run paths are excluded | `[RUN-SCOPE-DELTA] <item> changed out-of-scope paths: <paths>. The changes were quarantined and restored to baseline. Revise and re-review the scope, then start: aw <host> run <selector>` | FAIL ITEM after containment; cascade dependents; continue independent items |
| `RUN-COMMIT-CONTENTS` | Run-owned commits identified by immutable run/item trailers, commit parents, trees, and action-owned delta | A required commit exists; its path union equals the action-owned delta; it contains no unrelated or pre-existing changes; commit parentage is reconciled | `[RUN-COMMIT-CONTENTS] Commit <sha> does not contain exactly the paths owned by <item>: <detail>. The item was quarantined. Correct its work in a new attempt with: aw <host> run <selector>` | FAIL ITEM after containment; ABORT RUN only if ownership/parentage is ambiguous |
| `RUN-COMMIT-GATEWAY` | Captured commit-gateway event and argv | The engine, not the agent, invoked `git commit ... -- <explicit paths>` as an argv list; no `-a`, broad add, shell string, or `--no-verify` occurred | `[RUN-COMMIT-GATEWAY] <item> lacks a valid path-scoped, hook-respecting commit receipt. The item was quarantined. Retry through a capable host with: aw <host> run <selector>` | FAIL ITEM after containment; ABORT RUN for a hook-bypass attempt |
| `RUN-NO-PUSH` | Enforced tool policy, network policy receipt, all captured process events, starting/ending remote config and remote-tracking refs | Capability preflight proved push denial; no push event or unexplained remote-state change exists | `[RUN-NO-PUSH] Host <host> could not prove push prevention for <item>. No work may start without that capability. Choose a capable host and run: aw <host> run <selector>` | FAIL ITEM if refused at preflight; ABORT RUN if a push was attempted |
| `RUN-CHECK-FRESHNESS` | Check command end times, final product-change time, checked HEAD/worktree digest, captured outputs | Every required check ran after the last relevant change against the exact candidate state; exit was 0 and required output was nonempty | `[RUN-CHECK-FRESHNESS] Check <recipe> is missing, stale, or failed for <item>. Run the registered check through the runner, then: aw <host> run --resume <run-id>` | RETRY, then FAIL ITEM |
| `RUN-CROSS-TREE` | Full deterministic repository checker | All reference, release-gate, dependency, status/location, naming, and index invariants pass | `[RUN-CROSS-TREE] Repository invariant <finding-code> failed after <item>: <detail>. Contain the item, repair it, run aw check all, then: aw <host> run --resume <run-id>` | FAIL ITEM; ABORT RUN only for identity/type ambiguity or ownership conflict |

The deterministic checker evaluates Git and the durable ledger, not the conversation transcript. Captured tool events are admissible because they are structured, hash-bound repository evidence, not agent narration.

### 4.3 Cross-item dependency verification

These checks apply to every IPD before review-readiness and again against the frozen graph immediately before execution. The common dependency evaluator is the only rule authority.

| Check | What is inspected | Pass criterion | Exact failure message and recovery command | Action |
| --- | --- | --- | --- | --- |
| `IPD-DEP-STATEMENT` | Metadata position, field count/value, creation/cutover provenance, lifecycle phase, and canonical grammar | Exactly one well-formed `Item-Dependencies` value exists and is not `unresolved`; only an eligible pre-cutover terminal IPD may omit it under the grandfather advisory | `[IPD-DEP-STATEMENT] IPD <id6> has <missing/unresolved/malformed> Item-Dependencies: <detail>. Assess dependencies with aw ipd dependencies set <id6> none or aw ipd dependencies set <id6> <edge>..., then run: aw check plans` | FAIL ITEM before session; eligible terminal grandfather is advisory-only |
| `IPD-DEP-RESOLUTION` | Every typed id6 edge against the frozen repository identity index | Each edge resolves to exactly one real item of the required type; the source does not target itself | `[IPD-DEP-RESOLUTION] IPD <id6> dependency <edge> does not resolve: <detail>. Correct it with aw ipd dependencies set <id6> <edge>..., then run: aw check all` | FAIL ITEM for zero matches; ABORT RUN for identity/type ambiguity |
| `IPD-DEP-ACYCLIC` | Full declared IPD dependency graph, including targets outside the selected queue | No strongly connected component contains more than one node and no self-loop exists | `[IPD-DEP-ACYCLIC] Dependency cycle detected: <ordered-cycle>. Break an incorrect edge with aw ipd dependencies set <id6> <edge>..., then run: aw check plans` | FAIL every IPD in the cyclic component; SKIP DEPENDENCY-NOT-MET for their transitive dependents; continue disconnected components |
| `IPD-DEP-SATISFIED` | Frozen edge requirements plus current repository state and in-run verified outcomes | Every `executed`, `exists`, and `state` edge meets its exact satisfaction rule before the IPD starts | `[IPD-DEP-SATISFIED] IPD <id6> requires <edge>, but observed <state>. Item skipped dependency-not-met. Satisfy or include the prerequisite, then run: aw <host> run <id6> --with-dependencies` | SKIP DEPENDENCY-NOT-MET; no session or mutation |
| `IPD-DEP-CASCADE` | Final outcome graph, root blocker, all reverse-reachable dependents, reason chains, and process events | Every dependent of a failed, unmet, terminally unsatisfied, capability-refused, or needs-input node is recorded `skipped`/`dependency_not_met`; none started a host session; each chain reaches one root cause | `[IPD-DEP-CASCADE] IPD <id6> depends on unavailable <parent-id>; root cause is <root-id>:<root-reason>. Item skipped dependency-not-met. Resolve the chain, then run: aw <host> run <id6> --with-dependencies` | SKIP DEPENDENCY-NOT-MET; if a dependent already ran, FAIL ITEM and contain it |

Propagation is deterministic. The engine first settles all currently ready nodes. When a node ends `failed`, `needs_input`, or a terminal/gated skip that does not satisfy its outgoing requirement, it marks every direct dependent `dependency_not_met`. It then repeats over reverse edges until a fixed point. Each skipped item records:

- `reason_code: dependency_not_met`;
- the immediate blocking edge and dependency ID;
- the root cause ID and stable root reason;
- the complete dependency chain;
- `session_started: false` and `mutated: false`.

If several roots block one item, the report contains all roots in stable id6 order; the primary reason is the lexicographically first shortest chain. On a later explicit resume, the engine re-evaluates every dependency-not-met item. A now-satisfied chain may return to `planned`; the earlier skip remains in event history.

### 4.4 IPD review verification

These checks apply when a `draft` or `to-review` IPD is reviewed, or when `--action review` re-reviews a `reviewed` IPD. Common checks also apply.

| Check | What is inspected | Pass criterion | Exact failure message and recovery command | Action |
| --- | --- | --- | --- | --- |
| `IPD-REVIEW-INPUT-COMPLETE` | Author-phase parser, shared dependency evaluator, and closed placeholder scan at the frozen input digest | All required sections and metadata exist; `Item-Dependencies` is resolved, well formed, referentially valid, and acyclic; E/V rows are bijective; no unresolved authoring sentinel exists | `[IPD-REVIEW-INPUT-COMPLETE] <id6> is still a stub: <findings>. Resolve dependencies and finish authoring, run aw ipd lint <id6> --phase author, then: aw <host> run <id6>` | SKIP ITEM |
| `IPD-REVIEW-LEGAL-TRANSITION` | Before/after status, lifecycle receipt, actor, and disposition directory | `draft` first moved to `to-review` through the setter; the reviewed result is `reviewed` in `pending/`; a re-review remains `reviewed` | `[IPD-REVIEW-LEGAL-TRANSITION] <id6> did not reach reviewed through a legal tool-authored transition. Repair with aw ipd set to-review <id6> --message "ready for review", then: aw <host> run --resume <run-id>` | RETRY, then FAIL ITEM |
| `IPD-REVIEW-HISTORY` | `Workflow history`, status-set receipt, run ID, actor, timestamp, summary | Exactly one new review entry binds the prior digest, resulting digest, run ID, and reviewer action | `[IPD-REVIEW-HISTORY] <id6> has no valid review history receipt for run <run-id>. Restore the tool-authored history, then: aw <host> run --resume <run-id>` | RETRY, then FAIL ITEM |
| `IPD-REVIEW-IDENTITY` | ID, Set, Order, filename grammar, `Item-Dependencies`, optional `Blocks-Release`, and source links | Stable identity is unchanged; dependency changes remain well formed and cause a new review freeze; any Set/Order change used the naming authority; release/source links remain resolvable | `[IPD-REVIEW-IDENTITY] Review changed protected identity or broke <field> on <id6>. Contain the item, repair it, run aw check all, then: aw <host> run <id6>` | FAIL ITEM after containment; ABORT RUN only for identity/type ambiguity |
| `IPD-REVIEW-NO-PRODUCT-MUTATION` | Action-owned delta | Only the IPD, tool-owned indexes/history, and run evidence changed; product source paths did not | `[IPD-REVIEW-NO-PRODUCT-MUTATION] Plan review modified product paths: <paths>. The item was quarantined. Start a clean review with: aw <host> run <id6>` | FAIL ITEM after containment |
| `IPD-REVIEW-LINT` | Reviewed-phase structural linter and shared dependency evaluator | Linter passes, including dependency statement, metadata, section order, E/V bijection, validation methods, open questions, and status/location | `[IPD-REVIEW-LINT] Reviewed IPD <id6> fails <finding-code>: <detail>. Fix it, run aw ipd lint <id6> --phase reviewed, then: aw <host> run --resume <run-id>` | RETRY, then FAIL ITEM |

The quality of a review is not deterministically provable. The checker proves that a real review action occurred, the plan remains structurally sound, and no protected invariant was bypassed. The skeptical verifier may raise semantic findings, but those findings require a correction or human disposition rather than being silently treated as machine truth.

### 4.5 IPD approval verification

| Check | What is inspected | Pass criterion | Exact failure message and recovery command | Action |
| --- | --- | --- | --- | --- |
| `IPD-HUMAN-APPROVAL` | Interactive gate record, actor, approver, timestamp, reviewed digest, resulting status | Human explicitly approved the exact reviewed digest; setter wrote `approved` and a human receipt | `[IPD-HUMAN-APPROVAL] <id6> has no human approval for its current digest. Approve it with: aw ipd set approved <id6> --by-human --message "<reason>"` | NEEDS INPUT |
| `IPD-AUTO-APPROVAL` | Original flags, reviewed digest, automated approval receipt, resulting status | Original run used `--full-auto`; setter wrote `auto-approved`; receipt actor is runtime and does not claim human approval | `[IPD-AUTO-APPROVAL] <id6> has invalid automated approval evidence. Contain the item, return it to reviewed with aw ipd set reviewed <id6> --message "invalid automated approval", then run: aw <host> run <id6>` | FAIL ITEM after containment |

An unattended runner must never write `approved`. `auto-approved` is the truthful ready-to-execute state for the explicit `--full-auto` policy.

### 4.6 One-off IPD execution verification

| Check | What is inspected | Pass criterion | Exact failure message and recovery command | Action |
| --- | --- | --- | --- | --- |
| `IPD-EXEC-READY` | Frozen status, approval receipt where applicable, resolved dependency statement, dependency satisfaction, and pre-execution lint | Status was `approved` or `auto-approved`; every dependency was satisfied; pre-execution lint passed before product mutation | `[IPD-EXEC-READY] <id6> was not execution-ready at baseline: <detail>. Repair the item or dependencies, then run: aw <host> run <id6> --with-dependencies` | FAIL ITEM before mutation; use dependency-not-met when the statement is valid but unsatisfied |
| `IPD-EXEC-BEGIN-RECEIPT` | Begin receipt containing plan digest, requirements, Scope-Paths, `Item-Dependencies`, baseline HEAD/worktree digest, actor, timestamp, retry budget, and host capabilities | Receipt predates mutation and exactly matches the frozen plan, graph, policy, capability proof, and baseline | `[IPD-EXEC-BEGIN-RECEIPT] <id6> has no valid pre-mutation freeze receipt. Contain any partial work and start a clean execution with: aw <host> run <id6>` | FAIL ITEM after containment |
| `IPD-EXEC-EV-BIJECTION` | E and V IDs and targets | Every E item has exactly one matching-suffix V item and no orphan or duplicate exists | `[IPD-EXEC-EV-BIJECTION] <id6> has invalid E/V mapping: <detail>. Contain the item, correct and re-review the IPD, then: aw <host> run <id6>` | FAIL ITEM after containment |
| `IPD-EXEC-E-COMPLETE` | Execution checklist | Every E item is checked and has an action receipt or artifact binding | `[IPD-EXEC-E-COMPLETE] <id6> has incomplete execution items: <E-ids>. Complete them, then: aw <host> run --resume <run-id>` | RETRY, then FAIL ITEM |
| `IPD-EXEC-V-EVIDENCE` | Validation rows, result tokens, observed-evidence fields, evidence IDs, captured commands/artifacts | Every V item has a passing result, nonempty concrete observed evidence, and valid evidence bound to the matching E item and candidate state | `[IPD-EXEC-V-EVIDENCE] <id6> lacks valid passing evidence for <V-ids>: <detail>. Re-run those validations, then: aw <host> run --resume <run-id>` | RETRY, then FAIL ITEM |
| `IPD-EXEC-SCOPE` | Frozen Scope-Paths and complete action-owned path delta | Every changed path is in scope. Each declared but untouched scope entry is either irrelevant by deterministic rule or has a structured, explicit acknowledgement; no free-form waiver suffices | `[IPD-EXEC-SCOPE] <id6> has scope mismatch. Outside: <outside>; declared but unexplained: <untouched>. Outside changes were quarantined and restored. Correct or re-review the plan, then run: aw <host> run <id6>` | FAIL ITEM after containment for outside paths; RETRY for unexplained untouched paths |
| `IPD-EXEC-PRE-TRANSITION` | Pre-transition linter at candidate product state | Linter passes before terminal mutation; all validations and attribution fields conform | `[IPD-EXEC-PRE-TRANSITION] <id6> cannot finalize: <finding-code> <detail>. Fix it, run aw ipd lint <id6> --phase pre-transition, then: aw <host> run --resume <run-id>` | RETRY, then FAIL ITEM |
| `IPD-EXEC-TERMINAL-TRANSACTION` | Journal, old and new path, status, lifecycle commit, file digest | One journaled transaction moved the IPD from `pending/` to `executed/`, changed status to `executed`, appended execution history, and committed the exact product/lifecycle paths | `[IPD-EXEC-TERMINAL-TRANSACTION] <id6> is not in one provable executed terminal state: <detail>. Recover the transaction with: aw <host> run --resume <run-id>` | FAIL ITEM for a known recoverable/incomplete transaction; ABORT RUN only for unknown outcome or ownership conflict |
| `IPD-EXEC-POST-TRANSITION` | Post-transition linter and committed destination | Linter passes at the committed executed path and the status/directory agree | `[IPD-EXEC-POST-TRANSITION] Executed IPD <id6> fails <finding-code>: <detail>. Do not edit the executed plan; create a corrective IPD, then inspect: aw runs show <run-id>` | FAIL ITEM |
| `IPD-EXEC-REFERENCES` | `Item-Dependencies`, `Blocks-Release`, `From-Backlog`, `From-Spec`, backlog handoff, spec implementation links, and release record | Every reference resolves; dependencies remain equal to the reviewed freeze; inherited release gates match; no done/implemented source dropped an active release gate | `[IPD-EXEC-REFERENCES] <id6> breaks cross-tree invariant <finding-code>: <detail>. Contain the item, repair the source or gate, run aw check all, then: aw <host> run <id6>` | FAIL ITEM after containment; ABORT RUN only for identity/type ambiguity |
| `IPD-EXEC-WORKTREE-CLEAN` | Item-owned paths in index and isolated worktree after lifecycle commit | No item-owned modification or untracked file remains outside the verified commit set | `[IPD-EXEC-WORKTREE-CLEAN] <id6> left uncommitted owned paths: <paths>. Quarantine and restore them, then run: aw <host> run <id6>` | FAIL ITEM after containment; ABORT RUN only if containment reveals ownership conflict |

The checker finds run-owned commits by required immutable trailers such as `AW-Run: <run-id>` and `AW-Item: <id6>`, then proves their tree diffs. It does not assume every commit between baseline and ending HEAD belongs to this run. This permits unrelated concurrent commits while refusing any overlap with the item's lease or scope.

### 4.7 Reusable IPD execution verification

Reusable execution runs all common checks plus the E/V, scope, command-freshness, commit, and reference checks above, with these replacements:

| Check | What is inspected | Pass criterion | Exact failure message and recovery command | Action |
| --- | --- | --- | --- | --- |
| `IPD-REUSE-SOURCE-STABLE` | Reusable IPD path, status, dependency statement, and pre/post digest | Source remains in `reusable/`, status remains `reusable`, dependencies were satisfied at instance start, and its bytes are unchanged by the instance | `[IPD-REUSE-SOURCE-STABLE] Reusable IPD <id6> was mutated or moved. Quarantine the instance, restore the standing source, then run: aw <host> run <id6>` | FAIL ITEM after containment |
| `IPD-REUSE-INSTANCE` | Frozen instance record keyed by run ID, E/V results, evidence and commits | A separate instance record contains the frozen plan digest, every passing V result, evidence bindings, scope delta, and commit set | `[IPD-REUSE-INSTANCE] Reusable IPD <id6> lacks a complete verified instance record. Re-run missing checks, then: aw <host> run --resume <run-id>` | RETRY, then FAIL ITEM |
| `IPD-REUSE-NO-TERMINAL-MOVE` | Git diff and lifecycle events | No move to `executed/` and no `executed` status transition occurred | `[IPD-REUSE-NO-TERMINAL-MOVE] Reusable IPD <id6> was incorrectly terminalized. Quarantine the item, restore the standing record, then run: aw <host> run <id6>` | FAIL ITEM after containment |

### 4.8 Spec verification

#### Review and approval

| Check | What is inspected | Pass criterion | Exact failure message and recovery command | Action |
| --- | --- | --- | --- | --- |
| `SPEC-REVIEW-COMPLETE` | Deterministic spec completeness parser and placeholder scan | Required purpose, requirements, decisions, acceptance criteria, open-question dispositions, metadata, and history section exist; no sentinel remains | `[SPEC-REVIEW-COMPLETE] Spec <id6> is not reviewable: <findings>. Complete it, run aw check specs <id6>, then: aw <host> run <id6>` | SKIP ITEM |
| `SPEC-REVIEW-TRANSITION` | Before/after status, status-set receipt, history, action-owned paths | Legal `draft -> to-review -> reviewed` or `to-review -> reviewed` transition occurred through setters; only spec/index/run-evidence paths changed | `[SPEC-REVIEW-TRANSITION] Spec <id6> did not reach reviewed through a legal tool-authored transition. Repair it with aw spec set to-review <id6> --message "ready for review", then: aw <host> run --resume <run-id>` | RETRY, then FAIL ITEM |
| `SPEC-REVIEW-STRUCTURE` | Spec checker after review | Status, typed gates, history, naming, links, and metadata all pass | `[SPEC-REVIEW-STRUCTURE] Spec <id6> fails <finding-code>: <detail>. Fix it, run aw check specs <id6>, then: aw <host> run --resume <run-id>` | RETRY, then FAIL ITEM |
| `SPEC-APPROVAL-AUTHORITY` | Human gate record, approved digest, setter receipt, status history | A human approved the exact reviewed digest and the setter wrote `approved`; actor is human | `[SPEC-APPROVAL-AUTHORITY] Spec <id6> requires genuine human approval for its current digest. Approve it with: aw spec set approved <id6> --by-human --message "<reason>"` | NEEDS INPUT |

`--full-auto` does not satisfy `SPEC-APPROVAL-AUTHORITY`.

#### IPD authoring from an approved spec

| Check | What is inspected | Pass criterion | Exact failure message and recovery command | Action |
| --- | --- | --- | --- | --- |
| `SPEC-PLAN-COUNT` | Baseline/current IPD inventory and `From-Spec` links | Exactly one new IPD links to the spec for this authoring action; no duplicate active plan already existed | `[SPEC-PLAN-COUNT] Spec <id6> produced <count> new linked IPDs; expected exactly one. Quarantine the authoring action, reconcile duplicates, run aw check all, then: aw <host> run <id6>` | FAIL ITEM after containment; ABORT RUN only for duplicate stable identity ambiguity |
| `SPEC-PLAN-CONFORMANCE` | New IPD parser, author/review-ready linter, source link, scope, resolved dependency field, and E/V rows | New IPD is canonical, `to-review`, in `pending/`, has `From-Spec: <id6>`, concrete Scope-Paths, a resolved `Item-Dependencies` statement, and conformant E/V checklists | `[SPEC-PLAN-CONFORMANCE] Generated IPD <plan-id> for spec <id6> fails <finding-code>: <detail>. Fix it with the IPD authoring tools, then: aw <host> run --resume <run-id>` | RETRY, then FAIL ITEM |
| `SPEC-PLAN-TRACE` | Spec requirements/acceptance IDs and IPD trace links | Every mandatory spec requirement maps to at least one E item and every acceptance criterion maps to at least one V item; there are no unknown references | `[SPEC-PLAN-TRACE] Generated IPD <plan-id> does not cover spec items: <ids>. Correct and sync the IPD, then: aw <host> run --resume <run-id>` | RETRY, then FAIL ITEM |
| `SPEC-PLAN-GATE-CARRY` | Spec/IPD `Blocks-Release` values | A spec release gate is copied exactly to the IPD; an absent spec gate is not invented | `[SPEC-PLAN-GATE-CARRY] Spec <id6> and IPD <plan-id> disagree on Blocks-Release. Quarantine the handoff, correct it, run aw check all, then: aw <host> run <id6>` | FAIL ITEM after containment |
| `SPEC-IMPLEMENTING-TRANSITION` | Spec status/history and IPD citation | Spec moved `approved -> implementing` through the setter only after the conformant IPD commit; history cites the IPD path and commit | `[SPEC-IMPLEMENTING-TRANSITION] Spec <id6> lacks a valid implementing transition tied to <plan-id>. Repair with aw spec set implementing <id6> --evidence <plan-path>, then: aw <host> run --resume <run-id>` | RETRY, then FAIL ITEM |

#### Implementing and implemented specs

| Check | What is inspected | Pass criterion | Exact failure message and recovery command | Action |
| --- | --- | --- | --- | --- |
| `SPEC-LINKED-PLANS` | All IPDs with `From-Spec: <id6>` | At least one linked plan exists; IDs are unique; no active requirement is orphaned | `[SPEC-LINKED-PLANS] Implementing spec <id6> has no complete linked plan set: <detail>. Author or repair the plan, then: aw <host> run <id6>` | FAIL ITEM |
| `SPEC-CHILD-OUTCOMES` | Child run records and current IPD states | Every required linked plan is independently verified `executed`; superseded/not-executed plans have an approved replacement or explicit spec disposition | `[SPEC-CHILD-OUTCOMES] Spec <id6> still has incomplete linked plans: <plan-ids>. Run the next plan with: aw <host> run <plan-id>` | FAIL ITEM; block spec completion |
| `SPEC-IMPLEMENTED-EVIDENCE` | Proposed evidence citation, target path/ID/commit, executed IPD validation evidence | Every citation resolves to current in-tree evidence and proves all mandatory spec requirements through executed IPDs | `[SPEC-IMPLEMENTED-EVIDENCE] Spec <id6> cannot be marked implemented; evidence <citation> is missing or incomplete. Repair evidence, then: aw <host> run --resume <run-id>` | RETRY, then FAIL ITEM |
| `SPEC-IMPLEMENTED-TRANSITION` | Status setter receipt and history | Legal `implementing -> implemented` transition was tool-authored after all evidence checks; history contains resolvable citations | `[SPEC-IMPLEMENTED-TRANSITION] Spec <id6> has an unauthorized or unsupported implemented status. Contain the item, restore implementing with aw spec set implementing <id6> --message "implementation evidence incomplete", then: aw <host> run <id6>` | FAIL ITEM after containment |

### 4.9 Backlog graduation verification

| Check | What is inspected | Pass criterion | Exact failure message and recovery command | Action |
| --- | --- | --- | --- | --- |
| `BACKLOG-GRADUATE-COUNT` | Baseline/current IPDs and `From-Backlog` links | Exactly one new active IPD was created and links to the open backlog ID | `[BACKLOG-GRADUATE-COUNT] Backlog <id6> produced <count> linked IPDs; expected exactly one. Quarantine the action, reconcile them, run aw check all, then: aw <host> run <id6>` | FAIL ITEM after containment; ABORT RUN only for duplicate identity ambiguity |
| `BACKLOG-GRADUATE-IPD` | New IPD linter, status/location, scope, resolved dependency field, and E/V rows | IPD is canonical, `to-review`, in `pending/`, has resolved `Item-Dependencies`, and is conformant | `[BACKLOG-GRADUATE-IPD] IPD <plan-id> generated from backlog <id6> fails <finding-code>: <detail>. Fix it, then: aw <host> run --resume <run-id>` | RETRY, then FAIL ITEM |
| `BACKLOG-GATE-HANDOFF` | Backlog/IPD `Blocks-Release`, `From-Backlog`, active release resolution | If backlog blocks release R, IPD also blocks R before backlog closes; all references resolve | `[BACKLOG-GATE-HANDOFF] Backlog <id6> did not preserve release gate <release> on IPD <plan-id>. Quarantine the handoff, correct the fields, run aw check all, then: aw <host> run <id6>` | FAIL ITEM after containment |
| `BACKLOG-DONE-LEGITIMACY` | Backlog setter receipt, status/history, handoff evidence | Backlog changed `open -> done` through the setter only after the IPD handoff commit; history cites the IPD | `[BACKLOG-DONE-LEGITIMACY] Backlog <id6> was closed without a valid IPD handoff. Contain the item, restore it with aw backlog set open <id6> --message "handoff incomplete", then: aw <host> run <id6>` | FAIL ITEM after containment |
| `BACKLOG-CROSS-TREE` | Full cross-tree checker | No dangling gate, mismatched gate, orphaned live blocker, or dangling source link exists | `[BACKLOG-CROSS-TREE] Backlog handoff violates <finding-code>: <detail>. Quarantine the item, repair it, run aw check all, then: aw <host> run <id6>` | FAIL ITEM after containment |

For `blocked`, `parked`, and `done` items, the checker validates the current record and proves that the run started no host session and made no action-owned repository change. A malformed blocked gate is a preflight failure, not a skip.

### 4.10 Prompt verification

| Check | What is inspected | Pass criterion | Exact failure message and recovery command | Action |
| --- | --- | --- | --- | --- |
| `PROMPT-CONTRACT-PARSE` | Frozen prompt `Run contract` | Contract has only known fields; scope grammar and recipe names are valid; policy combinations are consistent | `[PROMPT-CONTRACT-PARSE] Prompt <path> has an invalid run contract: <detail>. Fix it, run aw check prompts <selector>, then: aw <host> run <selector>` | FAIL ITEM before execution |
| `PROMPT-SOURCE-FROZEN` | Prompt digest and action packet | Prompt did not change during its own execution unless explicitly listed as an expected path | `[PROMPT-SOURCE-FROZEN] Prompt <path> changed after dispatch. Quarantine the item, review the new instructions, and start: aw <host> run <selector>` | FAIL ITEM after containment |
| `PROMPT-CHANGE-POLICY` | Baseline/current delta | `required` has a nonempty owned delta; `forbidden` has none; `optional` accepts either | `[PROMPT-CHANGE-POLICY] Prompt <path> expected <policy> but observed <delta-summary>. Correct the work, then: aw <host> run --resume <run-id>` | RETRY, then FAIL ITEM |
| `PROMPT-EXPECTED-PATHS` | Expected path existence, type, and optional digest | Every declared path exists and any declared digest matches | `[PROMPT-EXPECTED-PATHS] Prompt <path> is missing or mismatches expected artifacts: <paths>. Correct them, then: aw <host> run --resume <run-id>` | RETRY, then FAIL ITEM |
| `PROMPT-CHECK-RECIPES` | Repository recipe registry and fresh captured recipe results | Every declared recipe exists, ran as an argv list after the last change, exited 0, and produced required output | `[PROMPT-CHECK-RECIPES] Prompt <path> failed check recipe <recipe>: <detail>. Correct the work, then: aw <host> run --resume <run-id>` | RETRY, then FAIL ITEM |
| `PROMPT-COMMIT-POLICY` | Commit field, action-owned delta, commit gateway receipt | `required` has an exact path-scoped commit; `forbidden` has no run-owned commit | `[PROMPT-COMMIT-POLICY] Prompt <path> violates Commit: <policy>. Quarantine the item and retry through the runner with: aw <host> run <selector>` | FAIL ITEM after containment; ABORT RUN only for hook-bypass attempt or ownership conflict |
| `PROMPT-UNVERIFIABLE` | Absence of a valid contract, original acknowledgement, host completion, and aggregate policy | Without a contract, final item state is `ran`, verification is `unavailable`, and no automatic commit occurs. Default aggregation treats it as non-success; frozen `--unverifiable-ok` treats it as neutral only for aggregate exit calculation | `[PROMPT-UNVERIFIABLE] Prompt <path> ran, but verification is unavailable. Add a Run contract and run again with aw <host> run <selector>, or explicitly accept aggregate neutrality with --unverifiable-ok` | Final `ran`, verification `unavailable`; exit contribution 1 by default or neutral under `--unverifiable-ok`; no retry |

Host exit 0 proves only that the host process returned normally. It does not prove that a free-form request succeeded. A valid contract can prove observable artifacts and checks, but not every semantic requirement implied by prose.

### 4.11 Research, release, and walkthrough skip verification

| Check | What is inspected | Pass criterion | Exact failure message and recovery command | Action |
| --- | --- | --- | --- | --- |
| `NONRUN-TYPE-VALID` | Type-specific parser, status/outcome when present, naming and location | Record is structurally valid for its non-runnable type | `[NONRUN-TYPE-VALID] <path> is not a valid <type>: <detail>. Repair it and run: aw check <type> <selector>` | FAIL ITEM |
| `NONRUN-NO-ATTEMPT` | Run ledger, process events, action-owned delta | No executor or verifier session started and no repository mutation was attributed to the item | `[NONRUN-NO-ATTEMPT] Non-runnable <type> <path> unexpectedly started work or changed <paths>. Quarantine the item and inspect: aw runs evidence <run-id>` | FAIL ITEM after containment; ABORT RUN only if containment reveals ownership conflict |
| `NONRUN-SKIP-REASON` | Per-item outcome | Outcome is `skipped` with stable reason `type_not_runnable` and the type-specific guidance | `[NONRUN-SKIP-REASON] <path> lacks a valid non-runnable disposition. Rebuild the report with: aw runs verify <run-id>` | FAIL ITEM |

### 4.12 Terminal and gated-item skip verification

An IPD/spec/backlog item skipped because of a terminal, standing, parked, deferred, blocked, or already-done status must pass:

1. The type-specific structural checker.
2. Status/location consistency.
3. Resolution of any retirement reason, successor, gate, or evidence required by that status.
4. `NONRUN-NO-ATTEMPT`.
5. A stable, status-specific skip reason.

A skip is successful only as a dispatch decision. It is never reported as newly executed or verified work.

## 5. Cross-cutting design

### 5.1 Deterministic authority boundary

The following are admissible completion inputs:

- tracked and untracked file state relative to a frozen baseline;
- Git objects, refs, index, worktree, commit trees, and run/item trailers;
- tool-owned lifecycle receipts and transaction journals;
- hash-bound argv-list tool events with exit codes and captured-output digests;
- artifacts with content digests;
- registered check recipes rerun against a bound HEAD/worktree digest;
- valid human gate receipts issued through the trusted approval channel;
- the append-only, hash-chained run ledger.

The following are not completion evidence:

- “done,” “tests pass,” or similar agent prose;
- an agent-authored summary or checklist without captured evidence;
- host exit 0 by itself;
- a verifier's opinion;
- a file's mere existence when content or provenance is required;
- stale test output from before the final change;
- a hand-edited status or history line;
- an unresolvable path, commit, ID, or URL citation.

The skeptical-verifier turn is still valuable. It receives the frozen requirement set, diff, commits, and evidence manifest in a fresh session. It returns structured findings, each naming a predicate and proposed evidence. The deterministic checker independently executes or inspects those predicates. An unmachine-testable concern becomes `human_review_required`; it never becomes a fabricated deterministic pass.

### 5.2 Safety policy

#### Per-host capability descriptor

OpenCode and Antigravity are not assumed to have the same session, interception, sandbox, permission, or isolation behavior. For the exact host executable version and run mode, the engine requires a current capability descriptor backed by positive and fail-closed probe evidence. Its storage format is an implementation detail; its semantics are mandatory.

At minimum the descriptor answers, independently, whether the host can:

- create/resume an executor session and create a genuinely fresh verifier session;
- launch only captured argv-list tools and enforce a deny policy;
- deny push-capable network routes and withhold remote credentials;
- prevent the agent from committing except through the engine's commit gateway;
- preserve normal Git hook execution and reject hook-bypass arguments;
- allocate and confine mutation to an isolated Git worktree;
- enforce filesystem/path policy and coordinator-owned path exclusions;
- capture exit/output/diff evidence with redaction and provenance;
- terminate or time out a worker without losing outcome evidence;
- prove fail-closed behavior when any of the above is denied.

Every entry includes host, exact version, mode/configuration, capability name, support status, evidence digest, observed time, expiry, assurance, and positive/negative probe results. `supported` without current evidence is not sufficient. `oc` may support a capability that `agy` does not, or vice versa; the descriptor controls the decision for the current installation.

Each action packet declares `required_host_capabilities`. Typical requirements are:

| Action | Required host capabilities |
| --- | --- |
| Read-only classification/skip/check | Repository read and captured evidence only; no agent session for a skip |
| Plan/spec review or IPD authoring | Isolated worktree, path policy, argv capture, no-push enforcement, commit gateway, hook-preserving commit, timeout/cancel, fresh verifier |
| IPD or contract prompt mutation | All review capabilities plus required command/check execution and complete diff capture |
| Contractless prompt | Read-only confinement unless the descriptor proves the complete mutation boundary; never an automatic commit |

Fail-closed rule:

> If the descriptor cannot positively prove every capability required by an action, the engine starts no session and performs no mutation for that item. It records `failed` / `host_capability_unavailable`, cascades `dependency-not-met` to dependents, and continues independent items.

Exact message:

```text
[RUN-HOST-CAPABILITY] Host <host> cannot enforce <capability> required by <item> action <action>. No work started for this item. Choose a capable host or enable and re-probe that capability, then run: aw <host> run <selector>
```

#### Guarantee classification

Each safety guarantee belongs to one bucket. Host-independent guarantees are re-derived after the action from repository/Git state. Host-dependent guarantees require controlled execution and cannot be recovered by trusting the agent afterward.

| # | Safety guarantee | Bucket | Enforcement or proof |
| --- | --- | --- | --- |
| 1 | `run` does not push, tag, publish, release, or change remote configuration | Host-dependent | Tool/network/credential denial plus captured process policy. An actual push attempt aborts the run. |
| 2 | The agent cannot commit except through a path-scoped engine gateway | Host-dependent | Commit interception and gateway capability; the gateway uses explicit argv/path lists. |
| 3 | Hooks are not bypassed and a hook refusal remains a failure | Host-dependent | Hook-preserving gateway and deny policy for `--no-verify` or equivalent. |
| 4 | Item mutation is confined to an isolated worktree and coordinator-owned paths are inaccessible | Host-dependent | Worktree isolation, filesystem policy, and timeout/cancel capabilities. |
| 5 | Executor and skeptical verifier session separation is real | Host-dependent | Host session-model capability and fresh-session probe evidence. |
| 6 | A commit contains exactly the action-owned paths and no pre-existing edits | Host-independent | Compare frozen baseline, Git trees, index/worktree delta, and run/item commit trailers. |
| 7 | Declared Scope-Paths contain every item change | Host-independent | Recompute the complete tracked/untracked delta from the frozen baseline. |
| 8 | `Item-Dependencies`, status, directory, references, release gates, and E/V evidence are valid | Host-independent | Shared parsers, graph predicate, lifecycle receipts, Git state, and registered checks. |
| 9 | Human-required spec approval is genuine; automated IPD approval is labeled `auto-approved` | Host-independent | Trusted approval receipt and lifecycle-setter authority checks. |
| 10 | Mixed types, unverifiable prompts, generated work, dependency expansion, and aggregate unverifiable policy use separate explicit consent | Host-independent | Frozen invocation flags or exact interactive gate receipts in the ledger. |

Pre-existing dirty paths are never absorbed into an item delta or commit. Unrelated dirty paths and concurrent commits may exist, but overlap with a frozen lease is the enumerated ownership-conflict abort class. A scope expansion requires returning the item to review and starting a new frozen execution attempt.

Executor commits remain on the item's isolated branch until scope, commit-content, hook, dependency, and deterministic completion checks pass. Only then may the coordinator integrate the verified commit set and perform lifecycle finalization. A failed item therefore normally has nothing to undo in the main worktree; its isolated branch and worktree are quarantined and removed after evidence capture.

### 5.3 Durable state and restartability

The engine stores repository-local, crash-safe run state. The storage location is an implementation detail; the data contract is not. Each event is append-only and contains:

- schema version, run ID, monotonic sequence, timestamp, actor role, parent event, and previous-event hash;
- host, exact host version/mode, capability-descriptor digest, required capabilities, and host-session IDs;
- selector text, type filters, mixed-type acknowledgement, dependency-expansion choice, prompt policies, options, and queue digest;
- per-item stable identity, canonical path, type, status, content digest, canonical `Item-Dependencies`, dependency edges/satisfaction, and queue position;
- graph digest, dependency root-cause chains, and every dependency-not-met propagation event;
- action and attempt IDs, packet digest, baseline HEAD/index/worktree digest, isolated worktree, scope fence, lease, frozen retry budget, and remaining retries;
- quarantine/containment evidence and baseline-restoration proof for every failed mutating item;
- structured process, artifact, commit, approval, transition, verifier, and checker evidence;
- final outcome and reason code.

Writes use atomic replacement for snapshots and append-plus-fsync for events. A snapshot is a cache; replaying the ledger is authoritative.

Resume algorithm:

1. `aw <host> run --resume <run-id>` verifies the ledger chain before doing anything.
2. It reacquires or reconciles leases and compares repository state with the last checkpoint.
3. It re-runs the deterministic checker first.
4. If repository state already satisfies the frozen predicates, it records `verified` and does not re-execute.
5. If no action-owned side effect occurred, it starts the next numbered attempt.
6. If a known partial state exists and retry budget remains, it emits a correction packet containing only failed predicates and existing evidence.
7. If a terminal Git commit exists but the post-transition check was interrupted, it resumes post-transition verification without rewriting history.
8. It re-evaluates dependency-not-met skips. A now-satisfied chain may return to `planned`; the original skip event remains durable.
9. If ownership, commit parentage, or transaction outcome is ambiguous, it marks the appropriate enumerated abort class and stops. It never guesses or repeats a possibly non-idempotent action.

Starting the same selector while a matching nonterminal run exists does not silently create a second run. Interactive mode offers the exact resume command. Unattended mode exits 3 with that command.

### 5.4 Queue ordering and dependencies

The queue is a frozen directed acyclic graph whose prerequisite edges come only from valid top-level `Item-Dependencies` statements. The runner does not synthesize whole-item prerequisites from Set/Order, prose, E-row `Depends on`, `From-Spec`, `From-Backlog`, `Blocks-Release`, or a typed gate. Those fields keep their own provenance, release, intra-plan, or lifecycle meanings.

Rules:

1. The shared predicate parses and validates the full selected graph and all referenced targets before any host session. Zero-match/malformed/cyclic source nodes fail preflight; identity/type ambiguity aborts the run.
2. `--with-dependencies` computes the transitive closure before mixed-type confirmation and freezing. Without it, outside targets remain state checks and are not silently added.
3. A node becomes ready only when all declared edges meet their exact satisfaction semantics. The engine never uses Set/Order as evidence that a dependency is satisfied.
4. Execute sequentially by default. Among simultaneously ready independent nodes, sort by dependency depth, type rank (`spec`, `backlog`, `ipd`, `prompt`), Set, numeric Order, stable ID, then canonical path.
5. Explicit declared dependencies always win. Set/Order is only a deterministic tiebreaker among nodes already ready; lower Order cannot make an unsatisfied node runnable, and higher Order cannot delay an otherwise independent prerequisite relationship.
6. When a prerequisite fails, is capability-refused, ends `needs_input`, is skipped in a state that does not satisfy the edge, or is outside the queue and unsatisfied, the direct dependent becomes `skipped` / `dependency_not_met` without a session.
7. Propagate `dependency_not_met` over reverse edges to a fixed point. Preserve immediate blocker, all root causes, and complete chains. Independent nodes continue.
8. `executed` status text alone does not satisfy an `executed:` edge. Terminal structure and deterministic execution/finalization evidence must pass.
9. A `superseded`, `not-executed`, `blocked`, `parked`, or `deferred` target satisfies only an explicit `exists:` edge or a matching `state:` edge. It never satisfies `executed:`.
10. Newly generated IPDs are recorded in the result. They join the active graph only with `--follow-generated`; otherwise they are next actions. A generated IPD must still resolve `Item-Dependencies` before review-readiness.
11. The queue never incorporates unrelated files discovered after freezing.

Stable dependency reason codes:

| Condition | Source outcome | Direct/transitive dependent outcome |
| --- | --- | --- |
| Missing, unresolved, malformed, or dangling statement | `failed` / `dependency_graph_invalid` | `skipped` / `dependency_not_met` |
| Cycle member | `failed` / `dependency_cycle` | `skipped` / `dependency_not_met` |
| Prerequisite action failed | Its specific failure code | `skipped` / `dependency_not_met` |
| Required host capability unavailable | `failed` / `host_capability_unavailable` | `skipped` / `dependency_not_met` |
| Human gate stopped prerequisite | `needs_input` / `needs_human_approval` | `skipped` / `dependency_not_met` for the current run state |
| Valid target has wrong terminal/status state | Target retains its own outcome | `skipped` / `dependency_not_met` |
| Dependency omitted from queue and currently unsatisfied | No target run outcome | `skipped` / `dependency_not_met_external` |

### 5.5 Retry policy

Retry budget precedence is:

1. `--retry-budget N` on the original invocation;
2. repository policy `run.retry_budget`;
3. default `2`.

`N` must be an integer from 0 through 10 inclusive. It counts correction attempts after the initial attempt, separately for each action. `0` means the first failed deterministic check or retryable host attempt immediately fails the item; no correction packet is issued. The frozen budget cannot be raised on resume. A new run may choose a different policy.

The engine may spend budget only on failures classified as retryable:

- host spawn failure;
- host nonzero exit that did not create an ambiguous side effect;
- missing expected artifact or failed deterministic check for which a bounded correction is safe;
- missing or stale validation evidence;
- verifier transport failure.

It must never retry these classes regardless of budget:

- out-of-scope mutation;
- overlapping ownership or lease conflict;
- corrupt ledger;
- unknown commit or transaction outcome;
- unauthorized status change;
- human approval gate;
- hook bypass attempt;
- push attempt;
- changed frozen requirements;
- any non-idempotent external action whose outcome is unknown.

An out-of-scope mutation therefore fails and contains the item on the first occurrence even if ten retries remain. A human gate and dependency-not-met outcome are state gates, not retryable failures. Each permitted correction has a new attempt number and idempotency key and invalidates stale evidence from earlier attempts.

### 5.6 Reporting

Human output uses color only on a TTY and never makes color the sole carrier of meaning:

- cyan: running or verifying;
- green: deterministically verified;
- yellow: skipped, needs input, or ran but unverifiable;
- red: failed or run-aborting safety violation;
- gray: non-runnable informational record.

The final table includes position, ID/path, type, starting status, action trace, final item state, verification state, reason code, commit(s), and next command.

Machine output is one JSON object in `--json` mode and one JSON object per event in agent-stream mode. Each final item has at least:

```json
{
  "run_id": "run-<id>",
  "queue_digest": "sha256:<digest>",
  "item": {
    "id": "<id6-or-path-digest>",
    "path": "<repo-relative-path>",
    "type": "ipd",
    "starting_status": "approved"
  },
  "actions": ["execute", "skeptical_verify", "deterministic_check", "finalize"],
  "outcome": "verified",
  "verification": "passed",
  "reason_code": "IPD_EXECUTED_VERIFIED",
  "item_dependencies": ["executed:a1b2c3"],
  "dependency_state": "satisfied",
  "dependency_roots": [],
  "host_capability_descriptor": "sha256:<digest>",
  "required_host_capabilities": ["isolated_worktree", "commit_gateway", "deny_push"],
  "retry_budget": 2,
  "unverifiable_ok": false,
  "attempts": 1,
  "commits": ["<sha>"],
  "evidence_ids": ["<evidence-id>"],
  "next_command": null
}
```

Allowed final per-item outcomes are:

- `verified`: all required deterministic predicates passed;
- `ran`: execution occurred but verification is unavailable, allowed only for an explicitly acknowledged contractless prompt;
- `failed`: an action or required check failed;
- `skipped`: no execution was appropriate for the current valid state, including `dependency_not_met` with its explicit reason chain;
- `needs_input`: a human gate stopped the item;
- `cancelled`: explicit cancellation with no completion claim.

`planned` is the pre-dispatch state and `running`/`verifying` are transient states. Reports retain them in the event history.

For a contractless prompt that was explicitly acknowledged and whose host attempt ran to transport completion:

- the item always remains `outcome: ran`, `verification: unavailable`, `reason_code: verification_unavailable`;
- by default it contributes non-success to aggregate calculation and therefore exit 1 unless a higher-priority exit applies;
- with frozen `--unverifiable-ok`, it contributes neither success nor failure. The overall run may exit 0 only if every other actionable item is verified and every other skip is benign;
- `--unverifiable-ok` cannot mask a failed prompt process, scope/containment failure, host-capability refusal, dependency-not-met item, human gate, or run-wide abort class.

Run exit codes:

| Exit | Meaning |
| --- | --- |
| 0 | Every actionable item is verified; remaining items were benign skips; and any contractless `ran`/`unavailable` item was explicitly made aggregate-neutral by frozen `--unverifiable-ok`. |
| 1 | At least one item failed, ended `dependency_not_met`, or ended `ran`/`unavailable` without `--unverifiable-ok`; no run-wide integrity failure occurred. |
| 2 | Invalid invocation, selector, or unknown type. |
| 3 | Human input or explicit acknowledgement is required. |
| 4 | One of the six enumerated run-wide classes: ledger corruption, ownership/lease conflict, unknown/non-idempotent external outcome, push attempt, hook-bypass attempt, or identity/type ambiguity. |
| 130 | User interruption; durable state is resumable unless reconciliation reports unknown outcome. |

### 5.7 Failure taxonomy

| Class | Detection | Response | Stable reason |
| --- | --- | --- | --- |
| Agent did not act | Exit 0 but no required delta/artifact/event | One bounded retry, then fail item | `agent_no_effect` |
| Agent acted wrongly | Deterministic predicate or registered check fails | Correction packet, then fail item | `wrong_result` |
| Partial action | Some expected artifacts/E/V evidence exist, others do not | Resume from failed predicates only | `partial_result` |
| False completion report | Agent says success but checker fails | Ignore prose; correction or failure | `self_report_rejected` |
| Host/transport failure | Spawn, timeout, protocol, or session failure | Retry only when no ambiguous side effect exists | `host_failure` |
| Hook refusal | Commit gateway returns hook failure | Preserve worktree, fail item, show hook output | `hook_refused` |
| Hook bypass attempt | Captured argv or policy sees bypass token/path | Abort run | `hook_bypass_attempt` |
| Out-of-scope mutation | Delta outside frozen scope | Stop and quarantine item, restore its isolated worktree to baseline, fail item, cascade dependents, continue independent items | `out_of_scope_change` |
| Concurrent overlap | Lease or baseline ownership conflict | Abort run | `ownership_conflict` |
| Unauthorized status change | Status/history changed without authorized setter/actor | Contain and fail item; cascade dependents; continue independent items | `unauthorized_transition` |
| Missing/stale evidence | Evidence absent, invalid, or predates final change | Correction retry | `evidence_unsatisfied` |
| Corrupt ledger | Hash/schema/sequence/reference failure | Abort run; no execution | `ledger_corrupt` |
| Unknown external outcome | Non-idempotent action may have occurred but cannot be proved | Abort run; require human reconciliation | `unknown_outcome` |
| Human gate | Required human receipt absent | Persist and stop | `needs_human_approval` |
| Non-runnable state/type | Valid terminal/gated/narrative record | Skip without a session | `type_or_status_not_runnable` |
| Unverifiable prompt | No valid run contract | Refuse, or explicitly run as `ran`/`unavailable`; aggregate non-success by default or neutral only under frozen `--unverifiable-ok` | `verification_unavailable` |
| Push attempt | Tool policy sees push-capable action | Terminate worker and abort run | `push_attempt` |
| Host guarantee unavailable | Capability descriptor lacks current positive proof for an action requirement | Refuse the item before session start; cascade dependents; continue independent items | `host_capability_unavailable` |
| Invalid dependency statement | Shared predicate reports missing/unresolved/malformed/dangling statement | Fail source item before session; cascade dependents | `dependency_graph_invalid` |
| Dependency cycle | Shared predicate returns a cyclic component | Fail cycle members; cascade dependents; continue disconnected components | `dependency_cycle` |
| Dependency not met | Required edge's target failed, stopped, was unsatisfied, or could not be met in this run | Skip without session; record and propagate root chain | `dependency_not_met` |

### 5.8 Interactive and unattended parity

Both modes use identical resolution, freezing, host packets, evidence capture, skeptical verification, deterministic predicates, retry budgets, status transitions, commits, and reports. They differ only at decision gates:

| Gate | Interactive | Unattended |
| --- | --- | --- |
| Mixed types | Type `run mixed` | Requires `--allow-mixed` |
| Reviewed IPD | Human may approve, decline, or stop | `--full-auto` creates `auto-approved`; otherwise `needs_input` |
| Reviewed spec | Human may approve, decline, or stop | Always `needs_input`; `--full-auto` has no effect |
| Contractless prompt admission | Type `run unverifiable` | Requires `--allow-unverifiable` |
| Contractless prompt aggregate policy | Optional original `--unverifiable-ok`; item remains `ran`/`unavailable` | Same flag; item remains `ran`/`unavailable` |
| Dependency expansion | Optional original `--with-dependencies`; any new type triggers mixed confirmation | Requires original `--with-dependencies` and `--allow-mixed` when expansion mixes types |
| Generated child | User may choose a new run, or original command may include `--follow-generated` | Requires original `--follow-generated` |

No timeout or default answer may synthesize consent.

## 6. Open questions and honest limits

### 6.1 Limits that the implementation must state plainly

1. **Semantic correctness is not fully decidable.** Tests, artifacts, metadata, and traceability can be proved. Whether an implementation truly satisfies every natural-language intent cannot. The runner must say “deterministically verified against declared predicates,” not “guaranteed correct.”
2. **A contractless prompt cannot be verified.** Exit 0 and a diff are weak observables, not task success. Such a run never receives the `verified` outcome.
3. **Review quality is not deterministic.** The system can prove that an isolated review occurred and that findings were recorded and addressed. It cannot prove that the reviewer noticed every conceptual flaw.
4. **No-push and hook guarantees require control of execution.** Local Git state alone cannot prove that an unobserved process did not contact a remote or that a hook body truly ran. The design therefore requires the engine to own process launch, deny push-capable network/credentials, own commits, and record the commit gateway. If a host cannot provide those controls, unattended mutation must fail closed.
5. **External side effects may be unverifiable or non-idempotent.** A registered checker may verify an external API result only if it can capture a stable, attributable receipt. Otherwise the action must stop for human reconciliation after an unknown outcome.
6. **Nondeterministic tests remain nondeterministic.** The checker can prove which command ran, when, against which digest, and with what output. Flake management must be an explicit recipe policy; repeated passing runs must not be silently substituted for a failed required run.
7. **Human identity depends on the approval channel.** A TTY prompt records presence, not organizational identity. If named approvers matter, the implementation needs a trusted signed or authenticated approval mechanism. An agent-supplied `--by-human` string is not sufficient.
8. **A declared dependency list cannot prove conceptual completeness.** The system can force an author to choose `none` or id6-grounded edges and can prove syntax, resolution, cycles, and runtime satisfaction. It cannot prove that the author remembered every real-world prerequisite. Review must assess the assertion, especially `none`.
9. **A capability descriptor is only as strong as its probes and freshness.** The engine can fail closed on missing, stale, or negative evidence. It cannot infer enforcement from a host name or documentation claim. Capabilities must be re-probed when host version, mode, sandbox, or permission configuration changes.

### 6.2 Implementation choices still requiring repository-level definition

These do not change the behavioral specification:

- the durable storage location for run ledgers and large captured outputs;
- the authenticated approval-receipt mechanism for named human approvers;
- the repository-controlled check-recipe registry format;
- the exact set of host sandbox capabilities used to deny push/network access;
- the evidence TTL and probe recipes for each host capability descriptor entry;
- the repository's dependency-schema cutover commit and the exact CI severity policy for grandfather advisories;
- the bounded placeholder vocabulary and completeness rules for specs and prompt contracts;
- whether generated IPD trace links use requirement IDs already present in specs or require adding stable requirement IDs.

The internal filenames of the host runner engine and deterministic checker are deliberately unspecified.

## 7. Concrete worked example

Assume the repository contains these items. All id6 values are unique and every non-stub active IPD has a valid statement.

| Item | Type | Status/condition | `Item-Dependencies` | Set/Order |
| --- | --- | --- | --- | --- |
| `stub01` | IPD | `draft`, unresolved placeholders | `unresolved` | `alpha/01` |
| `draft2` | IPD | `draft`, otherwise complete | `none` | `alpha/02` |
| `revw03` | IPD | `reviewed`; its agent will change an out-of-scope path | `executed:draft2` | `alpha/03` |
| `ready4` | IPD | `approved` | `executed:revw03` | `alpha/04` |
| `leaf05` | IPD | `approved` | `executed:ready4` | `alpha/05` |
| `host06` | IPD | `approved`; requires controlled network allowlisting for a validation recipe | `none` | `beta/01` |
| `free07` | IPD | `approved`, ordinary repository-only work | `none` | `beta/02` |
| `done08` | IPD | `executed` with valid terminal evidence | `none` | `beta/03` |
| `spec09` | spec | `approved` | Not applicable in v1 | `gamma/01` |
| `prmpt0` | prompt | no Run contract | Not applicable | `gamma/02` |

The current `oc` capability descriptor positively proves standard isolated-worktree, commit-gateway, hook, fresh-session, and no-push enforcement. It does not prove the specialized `controlled_network_allowlist` capability required by `host06`.

### 7.1 Command exactly as requested

```text
aw oc run all --full-auto
```

Because literal `all` defaults to IPDs only, the frozen queue contains eight IPDs. The spec and prompt are not silently included. The selection report says:

```text
Selected: 8 IPDs
Excluded by all-default: 1 spec, 1 prompt
Mode: unattended, full-auto, retry-budget=2
```

No mixed-type acknowledgement is needed because the resolved queue is not mixed.

#### Queue trace

| Pos. | Item | Dispatch and checks | Outcome |
| --- | --- | --- | --- |
| 1 | `stub01` | `IPD-DEP-STATEMENT` sees `unresolved`, so draft readiness fails. No host session, diff, or commit. | `skipped`, `ipd_draft_stub` |
| 2 | `draft2` | `none` is a valid affirmative statement. Review passes; `--full-auto` writes `auto-approved`; execution and all deterministic checks pass. | `verified`, `IPD_EXECUTED_VERIFIED` |
| 3 | `revw03` | `executed:draft2` is now satisfied, so execution starts. The executor changes `docs/guide.md` outside Scope-Paths. The engine stops it, hashes the quarantine bundle, restores only its isolated worktree to baseline, proves no integration escaped, and releases its lease. | `failed`, `out_of_scope_change`, `contained=true` |
| 4 | `ready4` | `executed:revw03` is unsatisfied because `revw03` failed. No session starts. | `skipped`, `dependency_not_met`; root `revw03:out_of_scope_change` |
| 5 | `leaf05` | Cascade reaches `leaf05` through `ready4`. No session starts. | `skipped`, `dependency_not_met`; chain `leaf05 -> ready4 -> revw03` |
| 6 | `host06` | Dependency statement passes, but capability preflight finds no current proof for `controlled_network_allowlist`. No session or mutation starts. | `failed`, `host_capability_unavailable` |
| 7 | `free07` | It is independent of both failed roots. The descriptor proves its ordinary requirements, so it executes and verifies normally. This demonstrates continued overnight progress. | `verified`, `IPD_EXECUTED_VERIFIED` |
| 8 | `done08` | Status/directory, dependency statement, and terminal evidence are checked. No session or mutation occurs. | `skipped`, `ipd_already_executed` |

The scope failure does not stop `host06`, `free07`, or `done08`. Only `revw03` fails for scope, and only its dependency descendants skip. The capability refusal is also item-local. The run exits 1 because it contains failed and dependency-not-met items.

The exact scope message is:

```text
[RUN-SCOPE-DELTA] revw03 changed out-of-scope paths: docs/guide.md. The changes were quarantined and restored to baseline. Revise and re-review the scope, then start: aw oc run revw03
```

The exact host refusal is:

```text
[RUN-HOST-CAPABILITY] Host oc cannot enforce controlled_network_allowlist required by host06 action execute. No work started for this item. Choose a capable host or enable and re-probe that capability, then run: aw oc run host06
```

The cascade records both the direct blocker and root cause:

```json
{
  "item": "leaf05",
  "outcome": "skipped",
  "reason_code": "dependency_not_met",
  "blocking_dependency": "ready4",
  "root_causes": [{"id": "revw03", "reason": "out_of_scope_change"}],
  "chain": ["leaf05", "ready4", "revw03"],
  "session_started": false,
  "mutated": false
}
```

### 7.2 Explicit mixed-type variant

This command selects all three types, but it refuses at prompt admission because `prmpt0` has no Run contract:

```text
aw oc run all --type ipd --type spec --type prompt --allow-mixed --full-auto
```

To admit the contractless prompt and make it neutral only for aggregate exit calculation, use:

```text
aw oc run all --type ipd --type spec --type prompt --allow-mixed --full-auto --allow-unverifiable --unverifiable-ok
```

The engine records eight IPDs, one spec, one prompt, the explicit mixed acknowledgement, and the two distinct prompt-policy flags. Dependency sorting still controls IPD readiness.

- The eight IPDs behave exactly as above.
- `spec09` is human-approved, so the runner authors exactly one `to-review` IPD with `From-Spec: spec09` and a resolved `Item-Dependencies` value. It checks trace coverage and release-gate carry-forward, commits only the spec/IPD/index paths, and tool-sets the spec to `implementing`. Without `--follow-generated`, the new IPD is reported but not executed.
- `prmpt0` runs only after its explicit admission. Its host attempt reaches transport completion, so the item remains `ran` with verification `unavailable`. `--unverifiable-ok` makes that one outcome neutral for aggregate calculation; it does not change the label to `verified` and does not mask the IPD failures, so this example still exits 1.

`--full-auto` has no power to approve a reviewed spec. If `spec09` had started as `reviewed`, its outcome would be `needs_input`, its generated plan would not exist, and its exact next command would be:

```text
aw spec set approved spec09 --by-human --message "<reason>"
```

After a human records approval, the same durable run resumes with:

```text
aw oc run --resume <run-id>
```

This example demonstrates the revised guarantees: `all` is safely bounded; dependencies are explicit id6-grounded facts; a failed item is contained instead of poisoning independent work; unmet state cascades without starting dependents; a host capability gap refuses only the affected item; contractless prompt neutrality changes only aggregate exit calculation; and deterministic repository evidence rather than agent confidence decides completion.

## Workflow history
- 2026-08-26 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): promoted from the two-pass frontier-model design (tmp/aw-run-and-verify-design.updated.md) into a conformant spec. Content is the revised run-and-verify design incorporating four accepted pushbacks (A1 scope=fail-item-not-abort + containment; A2 configurable retry budget; A3 operator-selectable contractless-prompt exit; A4 per-host capability descriptor + host-dependent/independent guarantee split) and the new mandatory id6-grounded Item-Dependencies mechanism enforced by one shared predicate across aw check/lint/opt-in commit hook/runner preflight/CI, with grandfathering and skip-cascade. Presumes net-new infrastructure (Item-Dependencies, From-Spec, run ledger + commit trailers, prompt Run contract, per-host capability descriptor, aw ipd dependencies/aw runs/aw hooks install); overlaps agentadhere + bklggrad + the runner rename. Authored to be reviewed via /spec review before it seeds an IPD Set.
