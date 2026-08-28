# Spec: Agent process adherence: threat model, assurance classes, and invariant catalog (Phase 0)

- Date: 2026-08-28
- Status: draft
- Id: pqsx96
- Author: aw specs new
- Scope: Phase-0 foundation for the agentadhere layered defense: threat model, three assurance classes, and an invariant catalog with observable-evidence tags.
- From-Plan: gfokao (agentadhere Set, orchestrator 3b4f8u)

This is the Phase-0 classification foundation for the agentadhere layered-defense Set
(orchestrator `3b4f8u`, child `gfokao`). It produces NO enforcement code. It is the
reviewable, citable source of truth that phases 1 through 5 target: it names the toolkit's
process invariants, assigns each an assurance class, and states what evidence (if any) is
observable enough to prove compliance. Its purpose is to stop later phases from describing a
local hook, hash, or file as a stronger guarantee than it actually is (findings `bu9yij`
sections 4.6, 7.1, and 10).

Source of truth: the reconciliation findings `bu9yij`
(`.aw/records/research/reference/202608/20260823-agentadhere-04-bu9yij-ensuring-agent-process-adherence-across-heterogeneous-coding-agents.reconciliation.findings.md`),
sections 6 (mechanism table), 7.1 (assurance levels), and 10 (residual risks and non-goals).

---

## 1. Threat model

### 1.1 The actor

The subject of this threat model is a coding agent operating inside this repository with broad
local authority: it can run arbitrary shell commands, read and write any file in the worktree,
install and edit git hooks, invoke the raw `git` binary, and read local environment variables.
It is generally cooperative (it is trying to follow the workflow) but it is unreliable: relevant
instructions may not be retrieved at the decision point, generic learned habits (direct edits,
`git add -A`, ordinary `git commit`) outcompete an unfamiliar repository convention, verbal
knowledge of a rule does not imply procedural execution, and long workflows compound the failure
probability across remembered steps (findings section 4.1). It is not assumed to be adversarial
in the security sense, but any control it can trivially bypass MUST be treated as advisory.

### 1.2 What the actor can do (capabilities that defeat local controls)

Because the actor holds broad local authority, it CAN, whether by mistake or by taking the path
of least resistance:

- use raw tools (`git add -A`, `git commit -a`, a direct `git` binary) that bypass wrapped
  `aw` commands;
- hand-edit any durable artifact, including a plan's `- Status:` line, a backlog item's status,
  a `## Workflow history` record, or a test-evidence file;
- move a file between lifecycle directories (for example `git mv` a plan into `executed/`)
  without running the tool that is supposed to perform that transition;
- install, edit, disable, or skip (`--no-verify`) a local git hook;
- recompute a local hash chain or backdate a plausible-looking ledger entry after editing the
  record it attests;
- read a local environment variable that a naive control treats as an authorization token; and
- push with whatever credential it already holds.

### 1.3 The authority boundary

The one thing the local actor CANNOT unilaterally do is cause a change to be ACCEPTED by an
authority outside its own reach: a protected remote branch, a required CI check running in a
clean environment, an external signing key, or a human reviewer's attested approval. Remote
acceptance is therefore the authority boundary. Every guarantee that must survive a fully
privileged local agent has to terminate at that boundary; a purely local mechanism can only
make noncompliance conspicuous, self-correcting, or inconvenient (findings sections 4.6, 5.4,
5.5, and 10).

### 1.4 Consequence for control design

A control is authoritative only against an actor that cannot alter or bypass it. This spec
therefore refuses to describe any local hook, local hash chain, or local file as an authority
guarantee. Each invariant below is tagged with the strongest HONEST class its available
evidence supports, and controls that are only locally checkable are labeled as detection or
guidance, not as authority.

## 2. Assurance classes

Every invariant is classified into exactly one of three assurance classes before any control is
built for it (findings section 7.1). The class states what kind of adherence the invariant can
realistically get, given the threat model, so a later phase cannot oversell it.

### 2.1 Guidance

A cooperative agent should normally follow the invariant, but the toolkit cannot deterministically
force it and, in some cases, cannot even detect a violation from durable artifacts. The control
is prose, a just-in-time nudge, a teaching error, or a heuristic detector. A Guidance invariant
is honestly probabilistic: it improves the odds and teaches the recovery path, but it is not an
enforcement boundary. Example mechanisms: `AGENTS.md` prose, a `check`/`doctor` nudge that names
a deterministically detectable smell, a host pre-tool hint.

### 2.2 Repository invariant

A noncompliant artifact MUST fail a deterministic check, and that same check MUST be able to run
at the merge boundary so noncompliant work cannot be accepted. The control is a shared,
host-independent checker (`aw check`) whose findings are reproducible from the committed tree,
run identically from the CLI, local hooks, and required CI. A Repository invariant is
deterministic FOR THE ENCODED PREDICATE over the artifacts it inspects; its authority against a
local bypass comes only when the same check gates merge in CI (a clean environment the local
agent cannot edit). Locally it is detection; remotely (required CI on a protected branch) it is
enforcement.

### 2.3 Authority invariant

Even an agent with broad local access must not be able to forge the artifact or authorize the
action. This requires an authority outside the local agent: a protected remote branch, a
required check the agent cannot disable, an external signing key, a credential broker, or an
attested human approval. A local hook, a local hash chain, or a local environment variable is
NEVER sufficient for an Authority invariant (findings sections 5.4, 5.5, 7.9). Authority-invariant
controls that need infrastructure outside the local+CI core are explicitly DEFERRED by the
agentadhere orchestrator to a later set; this spec labels them so no phase 1-5 child claims to
deliver one.

### 2.4 Observable evidence

For each invariant the catalog states its OBSERVABLE EVIDENCE: the specific artifact or event
that, if present and well-formed, proves compliance to a deterministic checker. Where no such
artifact exists, or where the artifact is forgeable by the local actor, the evidence entry says
so explicitly with an "unverifiable" or "probabilistic/forgeable-locally" label rather than
implying a guarantee. A checker can only enforce what it can observe; naming the observable
evidence (or its absence) is what keeps each control honestly scoped (findings sections 4.7, 6,
7.2, 10).

## 3. Invariant catalog

Each row names one process invariant, its assurance class (per Section 2), its observable
evidence, and the current or planned control. Rule ids in the Evidence/Control column are the
stable `aw check` codes or the pre-commit hook module that already encodes the invariant, where
one exists. An invariant with no deterministic observable is labeled honestly.

| # | Invariant | Assurance class | Observable evidence | Current / planned control | Honest limit |
|---|---|---|---|---|---|
| I-01 | Commits are path-scoped: stage only the files this task changed, never `git add -A` / `git add .` / `git commit -a`. | Repository invariant (the STAGED-TREE result is checkable; the exact typed command is not) | The staged index vs the declared task scope; an out-of-scope staged path is detectable. A pre-commit hook can inspect the resulting index, NOT reconstruct the typed command (findings 5.3). | Phase 2 `aw commit` computes allowed paths and refuses out-of-scope staged changes; phase 3 declared file scope; a pre-commit hook checks staged-vs-scope. | A hook cannot prove which command produced the index; enforce the invariant "staged paths within declared scope", not the syntax. Local until CI runs the same scope check. |
| I-02 | No push without authorization. | Authority invariant | None that is locally sufficient: a local env var or pre-push hook is visible to and bypassable by the agent. Only a protected remote branch, required check, or brokered/narrow credential is authoritative (findings 5.5, 7.9). | Pre-push hook for convenience/feedback only; the authoritative control is a protected branch + withheld/brokered push credential, DEFERRED to the external-authority set (phase 8). | A local pre-push check is not independent authorization; do NOT label it as one. |
| I-03 | No hand-edited lifecycle status: a plan/spec/backlog `- Status:` transition must go through the tool that also writes the attributed `## Workflow history` line. | Repository invariant (the untooled fingerprint is detectable) | A staged `- Status:` change with NO matching tool-authored `## Workflow history` line for the new status is the fingerprint of a careless hand-edit; deterministically detectable. | `check.status-untooled` (`check_engine`); the `status_untooled_gate` pre-commit hook (intermediate transitions); `aw set`/`aw ipd set` are the tooled path. | Predicate is textual: it catches the careless omission (status flip with no note), NOT a hand-edit that ALSO writes a plausible history line. Local hook is bypassable with `--no-verify`; the portable authority is `aw check` + CI. |
| I-04 | No raw terminal plan-to-`executed` transition: a plan reaching `executed` (status line or move into `executed/`) must be performed by `aw ipd finalize`. | Repository invariant | A durable finalize transaction journal under `.aw/state/runtime/transactions/ipd_finalize_<id6>.json` bound to this transition; a plan that gained `- Status: executed`/`done` or was moved into `executed/` in a commit with no matching journal is detectable. | The `executed_transition_gate` pre-commit hook; `aw set executed` is delegated into gated `aw ipd finalize`; the `proclint` detector (`aw check`/`aw doctor`). | Git hooks are local, not cloned by default, and skippable with `--no-verify`: this is a PREVENTION layer, not an absolute gate. There is deliberately no CI enforcement of this today. |
| I-05 | IPD finalize requires validation: a plan is not `executed` until every validation item is verified with concrete evidence, and finalize verifies changed paths stayed within `Scope-Paths`. | Repository invariant (structural conformance is checkable; genuine test execution is not) | `aw ipd lint --phase pre-transition` conformance (E/V state, evidence non-empty); the finalize scope reconciliation comparing changed paths to `Scope-Paths`; the begin receipt binding {plan digest, frozen scope, base HEAD, actor}. | `aw ipd begin`/`aw ipd finalize` (receipt + pre/post lint + scope reconciliation + atomic terminal transaction). | Lint proves the evidence FIELD is populated and structure conforms; it cannot prove the pasted test output was truly produced by running the tests on this tree (that needs a trusted runner, phase 7, deferred). Local receipt is forgeable by a fully privileged agent. |
| I-06 | Test evidence is bound to the tree it certifies (a "tests passed" transcript is a claim, not proof). | Guidance today; Repository/Authority invariant only via a trusted runner (deferred) | A tool-captured execution record binding command, exit code, stdout/stderr, environment, start/end time, and source tree/commit hash. Today no such event exists; a pasted transcript is unverifiable. | Honest label today: pasted runner output is a claim (the honesty rule requires pasting ACTUAL output). Phase 7 (trusted test runner, tree-bound evidence) is DEFERRED; required CI re-running tests is the authoritative form. | A locally produced evidence file is forgeable by a fully privileged local agent; only independent CI execution gives High-confidence acceptance (findings 6, 7.6, 10). |
| I-07 | Release-gate preservation: a release-blocking backlog item (`- Blocks-Release:`) may close `done` only if the gate is provably preserved (handoff to a `From-Backlog` plan), satisfied (resolvable in-tree evidence), or explicitly de-gated. | Repository invariant | The `- Blocks-Release:` field resolving to a real release record; a `From-Backlog` plan carrying the same gate; a resolvable evidence path; or an explicit clear. Evaluated by one shared predicate. | `check_engine.evaluate_blocking_close`; `check.blocking-item-closed-without-gate`, `check.from-backlog-gate-mismatch`, `check.orphaned-live-blocker`; `aw backlog set done` setter; the opt-in `backlog_blocking_close_gate` pre-commit hook. | The hook is local, opt-in, not cloned by default, and `--no-verify`-skippable; the portable authority is the `aw check` rule + CI, never the local hook alone (findings 7.7). |
| I-08 | Cross-IPD dependency statements are well-formed and acyclic (a plan's `Item-Dependencies` must resolve, be unambiguous, and introduce no cycle). | Repository invariant | The staged `.ipd.md` dependency statement evaluated over a staged-overlay snapshot; malformed / dangling / ambiguous / cyclic edges are deterministically detectable. | One shared evaluator `check_engine.evaluate_ipd_dependencies` behind `aw check`/`aw ipd lint` and the opt-in `ipd_dependency_statement_gate` pre-commit hook. | Commit-scoped and opt-in; bypassable locally with `--no-verify`; the durable authority is `aw check`/`aw ipd lint` + CI. |
| I-09 | Filename-grammar conformance: durable artifacts follow the uniform naming grammar for their type. | Repository invariant | The on-disk filename vs the type's grammar; a nonconformant name is deterministically detectable, with an exact rename recovery command. | `check.name-nonconformant` (`check_engine.check_names`), the shared `normalize_plan_names.is_conformant` predicate, and the `aw rename`/producer path. | A grammar check cannot judge whether the slug/date are semantically correct, only that the shape conforms. |
| I-10 | No leaked maintainer/machine identifying info in public artifacts (home paths, usernames, hostnames, private repo names, session ids). | Repository invariant | Deterministic pattern scan over tracked files, the built package, and git history; each finding emitted as `location\trule\tseverity`. | The leak-sanitizer `aw sanitize --agent` (alias `aw check-local-leaks --agent`); runnable even with no hook/CI installed. | A pattern scan can miss a novel leak shape it has no rule for; it is a deterministic backstop for KNOWN patterns, not a proof of absence. |
| I-11 | No em/en dashes in USER-FACING prose authored by an agent (READMEs, CHANGELOG, end-user docs). | Guidance | Presence of an em/en dash in a user-facing text artifact is deterministically detectable, but the USER-FACING vs internal classification of an artifact is a convention, not a hard boundary. | `AGENTS.md` prose (execution contract); could be a `check`/`doctor` nudge scoped to user-facing paths. | It does NOT apply to internal/AI-facing artifacts (IPDs, findings, prompts, specs, commit messages, code comments); a checker would need a reliable user-facing-path list to avoid false positives. |
| I-12 | A finished draft IPD is advanced to `to-review` (do not leave a completed draft silently `draft`). | Guidance | A `draft` plan that contains NO authoring placeholders (no unfilled `E-NEW`/`<action>`/TODO scaffolding) is deterministically detectable as "ready", so it can be NUDGED. | Phase-1 child 02 implements `check.ipd-draft-ready-to-review` as a detect-and-nudge rule built FROM this catalog entry; today it is prose guidance. | It is a NUDGE, not a gate: the toolkit cannot force the author to advance, and "finished" is judged by placeholder-absence (a heuristic for completeness), not by semantic completeness. This closes the recurring miss where agents finish drafting but never advance the status. |
| I-13 | An agent genuinely read and understood the plan/rules it is executing. | Guidance (unverifiable) | NONE. No durable artifact proves private cognition; a checker can at most require observable preparatory artifacts (a begin receipt, a decisions register entry) as a proxy. | Convert to observable proxies where possible (begin receipt, recorded decisions); otherwise honestly labeled unverifiable. | Fundamentally unverifiable from artifacts (findings 4.7, 10); do NOT build a control that claims to prove it. |
| I-14 | Authorship in a shared dirty worktree is attributable. | Guidance / Authority invariant (unverifiable locally) | NONE reliable locally: file timestamps and an agent's narrative do not prove who owns a change in a shared checkout. | Isolated worktrees + declared file scope (phase 3) make attribution possible by construction; without isolation it is unverifiable. | Do not infer authorship from timestamps or narrative; the honest fix is isolation, not inference (findings 5.5-relevant, 7.5, 10). |
| I-15 | Local history / hash chains are not silently forged. | Guidance (locally forgeable) | A hash chain detects ACCIDENTAL corruption and makes an unsupported edit conspicuous; it does NOT prove authenticity against an actor who can edit the record, the keys, and the checker. | A local append-only-shaped log/hash chain is a consistency aid; non-forgeable provenance needs an external key/service (phase 8, deferred). | Locally forgeable with broad access; a "round"/inconsistent timestamp is a heuristic signal, not deterministic proof (findings 5.4, 6, 10). |

### 3.1 Coverage note

The invariants named explicitly in this child's Scope are all present: path-scoped commits / no
`add -A` (I-01), no push without authorization (I-02), no hand-edited lifecycle status (I-03,
and the terminal case I-04), tree-bound test evidence (I-06), IPD finalize requires validation
(I-05), and backlog release-gate preservation (I-07). The mandated authoring-lifecycle entry is
I-12. Entries I-13 through I-15 are the honest "unverifiable / probabilistic / locally-forgeable"
residual-risk labels required by findings section 10, kept in the catalog so no later phase
mistakes their absence for a solvable gap.

## 4. Traceability (each phase-1 rule traces to a cataloged invariant)

Phase 1 (child `uisjns`) builds the versioned policy schema and the shared `aw check` engine
from THIS catalog. The traceability requirement is that every phase-1 policy rule cites a
cataloged invariant. Worked example:

- Phase-1 rule `check.ipd-draft-ready-to-review` (child 02's detect-and-nudge rule) traces
  directly to catalog invariant **I-12** ("a finished draft IPD is advanced to `to-review`",
  assurance class Guidance, observable evidence: a placeholder-free `draft` plan is
  deterministically detectable and therefore nudgeable). The rule's assurance class (Guidance /
  nudge, not a merge-blocking gate) is inherited from I-12's class, which is exactly the point
  of classifying before implementing.

Additional worked traces, to show the catalog covers the existing engine:

- `check.status-untooled` traces to **I-03**; `check.blocking-item-closed-without-gate` and its
  siblings trace to **I-07**; `check.name-nonconformant` traces to **I-09**; the
  `executed_transition_gate` hook traces to **I-04**; `evaluate_ipd_dependencies` traces to
  **I-08**. Each existing control therefore has a named catalog home, and each future phase-1
  rule must name one before it is added.

## 5. Non-goals (this child)

- NO enforcement code (no schema, engine, hooks, or CI): those are phases 1 through 5. This
  child is the classification only.
- NO machine-readable catalog data file: OQ-01 resolved to keep the Phase-0 artifact a single
  human-reviewed spec; if phase 1 benefits from a derived data file it derives one FROM this
  spec at that boundary, avoiding a premature parallel source of truth.
- NO authority-invariant control is delivered here or in phases 1 through 5; authority
  invariants (I-02, and the strong forms of I-06/I-14/I-15) are labeled and deferred to the
  later external-authority set (findings section 8).

## Workflow history

- 2026-08-28 created (aw specs): Phase-0 foundation for the agentadhere layered defense: threat model, three assurance classes, and an invariant catalog with observable-evidence tags.
