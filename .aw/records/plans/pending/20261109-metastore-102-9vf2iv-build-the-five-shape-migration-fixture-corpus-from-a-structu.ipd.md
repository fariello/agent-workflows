# IPD: Build the five-shape migration fixture corpus from a structural survey

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` C12 and AC-42 require `aw migrate metadata` to be proven on every prior record shape this toolkit has written, not only on this repository. Plan `g5hpbb` owned the corpus (its E-01) together with the cache, discovery, layout-chaining and proof work: 8 E-items and 16 work Scope-Paths. Research `nj8zdp` guidance (at most 5 E-items and 8 work Scope-Paths per plan) splits it in round 3 on 2026-11-09; this part is the corpus every later part tests against.
- Scope: `tests/migration_corpus.py`, a fixture builder (not a test module) with one function per C12 shape, derived from a structural survey of the maintainer's repositories with all text synthetic. EXCLUDES: the cache changes (`6oi2nu`), discovery and id-less conversion (`3g20ms`), layout chaining (`bv4kkj`), the AC-42 proof and changelog (`g5hpbb`).
- Scope-Paths: tests/migration_corpus.py, .aw/records/plans/pending/20261109-metastore-102-9vf2iv-build-the-five-shape-migration-fixture-corpus-from-a-structu.ipd.md
- Item-Dependencies: executed:dcerjg
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 102
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 9vf2iv

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from g5hpbb (round 3, research nj8zdp guidance).
- 2026-11-09 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

One importable builder per C12 shape writes a real git repository of that shape, so the cache, discovery, layout and proof parts all test against the same anonymized corpus.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the corpus

- [ ] E-01 (carried verbatim from `g5hpbb` E-01) Add `tests/migration_corpus.py`, a fixture builder (not a test module) with one function per C12 shape that writes a real `git init` repository into a given directory and returns its root: `legacy_agents_layout` (shape a: `.agents/plans/{pending,executed}`, `.agents/docs/{research,specs}`, plans with and without `- Id:`/`- Status:` bullets), `mixed_layout` (shape b: both trees, a record type in each), `idless_prose` (shape c: a plan whose first line is `# Implementation Plan Document (IPD) - <title>` with no bullet block, plus a `.md` the loader cannot classify), `no_sidecar` (shape d: `.aw/` layout with specs and backlog items carrying ids, no `records/history.jsonl`), and `companion_backend` (shape e: records under a companion root registered so `project_context` resolves there). Derive every shape from a STRUCTURAL survey of the maintainer's repositories (directory names, filename grammars, front-matter shapes and their counts), written into the module docstring as the evidence for each fixture WITHOUT naming any repository (they are private); copy NO record text. All prose in the fixtures is synthetic.
  - Depends on: none
  - Expected outcome: each builder produces a repository on which `aw find --all` (today's readers) lists a known, nonzero set of records; the docstring cites the survey count for each shape; `aw sanitize --agent` on the module reports clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Fixtures must not copy another repository's text: those repositories are private, and the leak-sanitizer is run on the corpus module (carried from `g5hpbb` Step 0).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (advisory `IPD-C801`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | 28 repositories on the maintainer's machine use the toolkit; most are on `.agents/`, five mix `.agents/` and `.aw/`. | `g5hpbb` F-02 (directory survey, 2026-11-07); repository names are private and deliberately not recorded. |
| F-02 | Prose plans with no metadata bullets exist in the field. | `g5hpbb` F-03. |
| F-03 | `ipd_lint` IPD-Z603 on `g5hpbb` (2026-11-09, cutover patched): 8 E-items, 16 work Scope-Paths. | Moving the corpus here is one of four parts that bring `g5hpbb` under the guidance. |

## Proposed changes (ordered, validatable)

1. E-01: the five builders and the survey docstring.

## Deferred / out of scope (with reason)

- Using the corpus: cache cases (`6oi2nu`), discovery (`3g20ms`), layout stage (`bv4kkj`), AC-42 proof (`g5hpbb`).
  - Carrier: g5hpbb

## Scope check

- Over-scope: none.
- Under-scope: none for `g5hpbb` E-01. The corpus covers shapes found on ONE machine (4sd62s 3c).

## Required tests / validation

The builder is exercised by V-01 directly (each builder run plus `aw find --all`); later parts import it in their test modules.

## Spec / documentation sync

No spec change; implements the corpus half of `4sd62s` AC-42.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste, for each of the five builders (`legacy_agents_layout`, `mixed_layout`, `idless_prose`, `no_sidecar`, `companion_backend`), the output of `aw find --all` run in the built fixture (record count and the first lines), the survey counts quoted from the module docstring with the command that produced them, and the `aw sanitize --agent` result record for `tests/migration_corpus.py`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. All open questions are resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Safety: the builders write only into a directory they are given; never point one at this checkout or at any of the maintainer's repositories.

Honesty rule: paste the ACTUAL output of each command; never claim a result you did not run.

Commits: commit only through `aw commit 9vf2iv -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 9vf2iv` itself.
