# IPD: aw ipd scaffold enforces clustering grammar and requires set metadata

- Date: 2026-08-19
- Kind: child
- Concern: `aw ipd scaffold` can currently emit a plan that lacks Set/Order metadata and can honor an explicit `--path` that does not follow the clustering filename grammar, so a freshly scaffolded plan is not guaranteed to be groupable by Set or correctly named.
- Scope: Change `aw ipd scaffold` (CLI parser + `run_scaffold` + `build_skeleton`) so it requires `--set`/`--order` and always writes `- Set:`/`- Order:` metadata, and so an explicit `--path` must match the clustering grammar (`YYYYMMDD-<setid>-NN-<id6>-<slug>.ipd.md`) unless an explicit legacy escape is passed. Add tests. Close backlog 7vd36f.
- Status: reviewed
- Set: backlog-medhigh-260819
- Order: 4
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: v1rj3p

## Workflow history

- 2026-08-19 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-19 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): investigated scaffold code, filled body.
- 2026-08-19 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; PR-04-1 status->to-review->reviewed, PR-04-2 canonical serial-runner note (E-06/V-06/required-tests). Anchors verified (cli.py:713-721, ipd_authoring.py:123/253, plans_refs._CLUSTERED_RE:48). OQ-01 resolved. GO - PENDING HUMAN APPROVAL.

## Goal

Make `aw ipd scaffold` enforce the two authoring invariants named by backlog 7vd36f: every scaffolded plan MUST carry `Set`/`Order` metadata, and every scaffolded filename (derived or explicit `--path`) MUST follow the clustering grammar `YYYYMMDD-<setid>-NN-<id6>-<slug>.ipd.md`, so no plan is born ungroupable or misnamed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Require Set/Order and always emit the metadata

- [ ] E-01 In `agent_workflows/cli.py` make the scaffold parser require `--set` and `--order` (change `p_ipd_scaffold.add_argument("--set", ...)` and `--order` at cli.py:713-721 to `required=True`), and update their help text to say they are required. Add a new `--legacy-name` flag (default False, `action="store_true"`) to the scaffold parser as the escape hatch used by E-03.
  - Depends on: none
  - Expected outcome: `aw ipd scaffold --kind child --title X` (no `--set`/`--order`) exits nonzero with an argparse "required" usage error; `--legacy-name` is accepted by the parser.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/ipd_authoring.py` `run_scaffold` (ipd_authoring.py:220-234) drop the now-dead "both together" branch's ability to accept both-absent: after E-01 both are always present, so keep the orchestrator/child Order checks (ipd_authoring.py:225-230) but add an explicit guard that returns exit 2 with a clear message if either `set_name` or `order` is None (defense in depth for direct `run_scaffold` callers). In `build_skeleton` (ipd_authoring.py:96-154) remove the `if set_name is not None:` conditional at ipd_authoring.py:123-125 so `- Set:`/`- Order:` are always emitted, and drop the fabricated `derived_set = ... else plan_id` fallback at ipd_authoring.py:253-256 (Set/Order are now always real inputs).
  - Depends on: E-01
  - Expected outcome: any successful scaffold writes a file whose front matter contains `- Set: <given>` and `- Order: <given>`; the derived clustered name uses the real Set id, never the synthesized plan id.
  - Execution state: pending

### Task group 2: Enforce the clustering grammar on an explicit --path

- [ ] E-03 In `run_scaffold` (ipd_authoring.py:236-267), when `--path` is given (target branch at ipd_authoring.py:238-240), validate the basename against the clustering grammar using `plans_refs._CLUSTERED_RE` (plans_refs.py:48) and require the `.ipd.md` facet; if it does not match, return exit 2 with a message naming the expected grammar UNLESS `--legacy-name` was passed. When it does match, cross-check that the filename `id6` group equals the generated `plan_id` (regenerate `plan_id` from the filename's id6 so front-matter Id and filename agree), keeping backward compatibility only behind `--legacy-name`.
  - Depends on: E-02
  - Expected outcome: `aw ipd scaffold ... --path .../explicit.md` exits nonzero and prints the expected clustering grammar; the same call with `--legacy-name` succeeds; a conforming `--path` writes a plan whose front-matter Id matches the filename id6.
  - Execution state: pending

### Task group 3: Tests, docs, and closeout

- [ ] E-04 Extend `tests/test_awnaming_grammar_and_producers.py` (the existing scaffold-naming home) with cases: (a) scaffold without `--set`/`--order` exits nonzero; (b) a successful derived scaffold's file contains `- Set:` and `- Order:` lines; (c) an explicit non-clustering `--path` (e.g. `explicit.md`) exits nonzero and the message names the grammar; (d) that same `--path` with `--legacy-name` succeeds. Reuse the `_RepoBackendCLIFixture`/`ProducerTests` CLI harness already in that file.
  - Depends on: E-03
  - Expected outcome: four new assertions; `python3 -m pytest tests/test_awnaming_grammar_and_producers.py -p no:xdist` passes.
  - Execution state: pending

- [ ] E-05 Sync docs: update the scaffold `--set`/`--order`/`--path` help strings (cli.py:711-721) to state the requirement and the grammar; if `.aw/records/specs/` has an `ipd-spec`/authoring section describing scaffold, add one line noting scaffold now enforces Set metadata + clustering grammar. If no spec section references scaffold input rules, record "N/A with reason" in the Spec / documentation sync section.
  - Depends on: E-04
  - Expected outcome: help text and spec (if applicable) describe the enforced rules; `aw ipd scaffold --help` shows `--set`/`--order` as required and mentions the grammar.
  - Execution state: pending

- [ ] E-06 Close backlog item 7vd36f to done (`aw backlog set .aw/records/backlog/open/20260815-7vd36f-01-7vd36f-ipd-scaffold-clustering-grammar.backlog.md --status done --message "scaffold enforces Set metadata + clustering grammar" --dir .`) and run the full serial suite - canonical `make test-serial` (`python3 -m unittest discover -s tests -t .`); `python3 -m pytest -p no:xdist` is equivalent only with the `.[test]` extra installed.
  - Depends on: E-05
  - Expected outcome: backlog 7vd36f moves to `.aw/records/backlog/done/`; the full serial suite passes with no failures.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Scaffold is dry-run by default; `--apply` writes; atomic write-to-temp-then-rename (ipd_authoring.py:157-170); exit codes 0/1/2 where 2 is a usage/internal error and 1 is a refuse-to-overwrite (ipd_authoring.py:277-294).
- The clustering grammar is produced by `plans_refs.clustered_name` (plans_refs.py:147-167) and matched by `plans_refs._CLUSTERED_RE` (plans_refs.py:48); the facet is a closed enum (`ARTIFACT_TYPE_FACETS`) and `.ipd.md` is the plan facet.
- Set/Order are validated as an all-or-none pair by `ipd_schema.validate_metadata` (ipd_schema.py:233-248) but are NOT in `META_REQUIRED` (ipd_schema.py:128-136), which is why a plan without them still lints; scaffold is the authoring choke point that must require them.
- The child/orchestrator templates are the single-source-of-truth `build_skeleton` output (tests/test_ipd_templates.py); changing `build_skeleton` may require regenerating those template fixtures.
- Commit path-scoped, never push; paste actual runner output; move the plan to `.aw/records/plans/executed/` only after validation passes.

## Findings

| Anchor | Current behavior | Gap |
| --- | --- | --- |
| cli.py:713-721 | `--set`/`--order` both `default=None`, not required | scaffold can run with neither -> no Set metadata |
| ipd_authoring.py:220-224 | only enforces "both or neither" | both-absent is allowed |
| ipd_authoring.py:123-125 | `build_skeleton` emits `- Set:`/`- Order:` only when `set_name is not None` | scaffolded file can lack the metadata block |
| ipd_authoring.py:253-256 | derived branch fabricates `derived_set = plan_id` when `--set` omitted | clustered name uses a fake single-plan set id, and no Set line inside |
| ipd_authoring.py:238-240 | explicit `--path` honored verbatim | a nonconforming name like `explicit.md` is accepted (see tests/test_awnaming_grammar_and_producers.py:219-234) |

## Proposed changes (ordered, validatable)

1. E-01: parser requires `--set`/`--order`; add `--legacy-name` escape.
2. E-02: `run_scaffold` guards non-None Set/Order; `build_skeleton` always emits the metadata; drop the fabricated `derived_set` fallback.
3. E-03: explicit `--path` must match `_CLUSTERED_RE` with the `.ipd.md` facet (unless `--legacy-name`), and its id6 is reconciled with the front-matter Id.
4. E-04: tests for all four behaviors.
5. E-05: help/spec sync.
6. E-06: close backlog 7vd36f and run the full serial suite.

## Deferred / out of scope (with reason)

- Making `Set`/`Order` part of `META_REQUIRED` in `ipd_schema` (would retroactively fail existing setless plans in the lint gate). This plan enforces at the authoring choke point (scaffold) only; a lint-level requirement is a separate, wider decision.
- Changing `aw ipd sync` or `aw plans mv` naming behavior (already grammar-aware).

## Scope check

- Over-scope: none.
- Under-scope: none; the change is confined to the scaffold parser, `run_scaffold`, `build_skeleton`, and their tests/docs.

## Required tests / validation

- New/extended assertions in `tests/test_awnaming_grammar_and_producers.py` (E-04).
- `python3 -m pytest tests/test_awnaming_grammar_and_producers.py tests/test_ipd_templates.py -p no:xdist` for the focused surface.
- Full serial suite at close (E-06): canonical `make test-serial` (`python3 -m unittest discover -s tests -t .`); `python3 -m pytest -p no:xdist` is equivalent only with the `.[test]` extra installed.

## Spec / documentation sync

- Update scaffold `--set`/`--order`/`--path` help strings (cli.py:711-721). If `.aw/records/specs/` documents scaffold input rules, add one line there; otherwise record N/A with reason during E-05.

## Open questions

### OQ-01: Should an explicit nonconforming `--path` be a hard error, or accepted behind a `--legacy-name` escape?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Accept behind an explicit `--legacy-name` escape (default error). This preserves the backward-compatibility path exercised by tests/test_awnaming_grammar_and_producers.py:219-234 while making conformance the default; the test for the explicit-path case is updated to pass `--legacy-name`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste of `aw ipd scaffold --kind child --title X` (no `--set`/`--order`) showing a nonzero exit and an argparse "required" error; `aw ipd scaffold --help` output listing `--set`/`--order` as required and showing `--legacy-name`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste of the generated skeleton (dry-run) for a `--set demo --order 1` scaffold showing `- Set: demo` and `- Order: 1`; confirmation (grep of ipd_authoring.py) that the `if set_name is not None` conditional and the `else plan_id` fallback are gone.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste showing `... --path .../explicit.md` exits nonzero with a message naming the clustering grammar; the same call with `--legacy-name` exits 0; a conforming `--path` writes a file whose `- Id:` equals the filename id6.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted output of `python3 -m pytest tests/test_awnaming_grammar_and_producers.py -p no:xdist` showing the new cases passing (all green).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `aw ipd scaffold --help` output showing the updated help text; diff of the doc/spec line changed, or the recorded "N/A with reason".
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `git status` showing 7vd36f moved to `.aw/records/backlog/done/`; pasted tail of the full serial suite (`make test-serial` / `python3 -m unittest discover -s tests -t .`, or `python3 -m pytest -p no:xdist` with the `.[test]` extra) showing it passed (0 failed).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: the executing agent commits ONLY the files it changed, path-scoped (`git commit -m msg -- <path> ...`), never `git add -A` and never pushes. When reporting tests passed it MUST paste the ACTUAL runner output, never a claimed success. It writes no em or en dashes in user-facing prose. After every validation item is verified with concrete evidence and `aw ipd lint --phase pre-transition` conforms, it moves this plan to `.aw/records/plans/executed/` and sets Status accordingly; otherwise it STOPS and reports. This plan requires explicit human approval before execution.
