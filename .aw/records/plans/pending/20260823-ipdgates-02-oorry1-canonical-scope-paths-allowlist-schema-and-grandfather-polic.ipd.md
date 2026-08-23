# IPD: Canonical Scope-Paths allowlist schema and grandfather policy

- Date: 2026-08-23
- Kind: child
- Concern: IPD scope is expressed only in free-form `Scope:` prose, which tooling cannot compare against the actually-changed paths - so an executor can expand file scope (as p7dqwz did with `tests/test_empty_state_ux.py`) and nothing deterministic catches it. There is no machine-readable declared-path contract on an IPD.
- Scope: Add a canonical `Scope-Paths` allowlist to the IPD schema and its build/validate surfaces, with a grandfather policy for already-reviewed pending plans. Touch: agent_workflows/ipd_schema.py (the metadata contract), agent_workflows/ipd_authoring.py (scaffold emits a `Scope-Paths` stub), agent_workflows/ipd_lint.py (parse + validate + checkpoint diagnostics), the implemented IPD structure/lifecycle spec (via `aw specs note` / the managed spec verb), and focused tests/test_ipd_schema.py + tests/test_ipd_authoring.py + tests/test_ipd_lint.py. Does NOT implement begin/finalize (Orders 03/04) or compare paths at runtime (that is finalize, Order 04); this child only defines and validates the declared contract.
- Status: draft
- Set: ipdgates
- Order: 2
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: oorry1

## Workflow history

- 2026-08-23 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created (decomposition of 39fz2x E-02).

## Goal

Give every post-cutoff IPD ONE deterministic, machine-readable `Scope-Paths` allowlist (repo-relative literal paths or bounded pathspecs) that later tooling (`aw ipd finalize`, Order 04) can compare against the real changed paths. Define a safe grammar (reject absolute paths, `..` parent escapes, and repo-wide globs), implicit lifecycle-artifact exceptions (the plan file itself, its index refresh), and generated-file treatment. Require the allowlist at approval / pre-execution for NEW or re-reviewed plans, while GRANDFATHERING the already-reviewed pending sibling Sets (`unifyfileio`, `execset`) as `Scope-Paths`-optional with only an advisory diagnostic; existing terminal records stay untouched.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Define the contract

- [ ] E-01 Add `Scope-Paths` to the canonical IPD metadata contract in `agent_workflows/ipd_schema.py` and emit a `Scope-Paths` stub from `aw ipd scaffold` (`ipd_authoring.py`): a list of repo-relative literal paths or bounded pathspecs. Define the safe grammar - reject absolute paths, `..` parent escapes, and repo-wide/`**`-at-root globs; allow directory-bounded pathspecs; define implicit exceptions (the plan's own file + its manifest/index refresh are always allowed) and how generated files are declared. Document the field in the spec via the managed spec verb.
  - Depends on: none
  - Expected outcome: the schema and scaffold know `Scope-Paths`, its grammar is specified, and the spec documents it.
  - Execution state: pending

### Task group 2: Validate + grandfather

- [ ] E-02 Add `Scope-Paths` parsing and validation to `ipd_lint.py`: at the approval / pre-execution checkpoints, a POST-cutoff plan MUST carry a valid `Scope-Paths` (missing or malformed = a blocking diagnostic with actionable text); a PRE-cutoff reviewed pending plan (the `unifyfileio` and `execset` Sets, and any plan whose review predates this Set's ship date) lacking `Scope-Paths` emits an ADVISORY (non-blocking) migration diagnostic; existing TERMINAL records are unaffected (never claimed conformant, never blocked). Implement the cutoff as an explicit, testable predicate (e.g. a recorded cutoff date/marker), not an open-ended guess.
  - Depends on: E-01
  - Expected outcome: post-cutoff plans are hard-required to declare `Scope-Paths`; pre-cutoff reviewed plans and terminal records are not blocked.
  - Execution state: pending

### Task group 3: Prove it

- [ ] E-03 Add tests in `tests/test_ipd_schema.py`, `tests/test_ipd_authoring.py`, and `tests/test_ipd_lint.py` covering: valid literals + bounded pathspecs accepted; absolute/parent/repo-wide patterns rejected; implicit lifecycle + generated-file exceptions; missing-allowlist BLOCKING refusal for a post-cutoff fixture; ADVISORY-only (non-blocking) diagnostic for a pre-cutoff fixture standing in for a `unifyfileio`/`execset` sibling; unchanged grandfathered-terminal behavior; and spec/scaffold/schema parity. Confirm `pytest -n auto` is green.
  - Depends on: E-01, E-02
  - Expected outcome: the contract and grandfather policy are falsifiably tested, including the non-retroactivity guarantee.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The IPD metadata contract and its required/optional fields are defined in `agent_workflows/ipd_schema.py`; the structural linter is `agent_workflows/ipd_lint.py`; the scaffold that emits a conformant skeleton is `agent_workflows/ipd_authoring.py`. The canonical structure/lint spec is `.aw/records/specs/20260802-1904-01-ipd-structure-and-linting.spec.md` (implemented).
- ~11 already-reviewed pending sibling plans exist (`unifyfileio` g6mbht/o6b8l3/laykok/3cmnfc/52zgqr; `execset` 5ahblp/iy1a2g/3m4e54/m2wwns/31744f/2h7777) that MUST NOT be retroactively blocked (39fz2x OQ-03, human-resolved).

## Findings

Free-form `Scope:` prose is not machine-comparable, so scope expansion is undetectable by tooling. A declared `Scope-Paths` allowlist is the substrate the finalize transaction (Order 04) needs to compare declared vs actual changed paths. Introducing it must not invalidate the reviewed backlog of pending plans, hence the grandfather cutoff.

## Proposed changes (ordered, validatable)

1. Add `Scope-Paths` to schema + scaffold + spec with a safe grammar (E-01).
2. Add lint parse/validate with the post-cutoff-required / pre-cutoff-advisory grandfather policy (E-02).
3. Test the grammar, the checkpoints, and the non-retroactivity guarantee (E-03).

## Deferred / out of scope (with reason)

- Runtime comparison of declared vs actual changed paths: Order 04 (`aw ipd finalize`).
- The begin receipt: Order 03.
- Retrofitting `Scope-Paths` onto existing pending plans: out of scope; they are grandfathered (advisory only) until independently re-reviewed.

## Scope check

- Over-scope: none.
- Under-scope: none; the field, grammar, checkpoint validation, grandfather policy, and tests are all included.

## Required tests / validation

- `tests/test_ipd_schema.py` / `test_ipd_authoring.py` / `test_ipd_lint.py` per E-03.
- `aw ipd lint` parity checks on the spec/template/scaffold.
- Full suite via `pytest -n auto` (paste actual runner output).

## Spec / documentation sync

- Amend `.aw/records/specs/20260802-1904-01-ipd-structure-and-linting.spec.md` via the managed spec verb (`aw specs note` / the spec workflow) to document `Scope-Paths`, its grammar, and the grandfather cutoff. No undocumented code-only schema change.

## Open questions

### OQ-01: How is the grandfather cutoff represented so it is testable and unambiguous?

- Blocking: yes
- Status: open
- Owner: human
- Resolution or deferral rationale: TODO (human). Options: (A) a fixed cutoff DATE recorded in the schema/lint (plans with a review/creation date before it are advisory) - simple and testable, but date-based edges can be fuzzy; (B) an explicit per-plan `Scope-Paths: grandfathered` opt-out marker the pre-cutoff plans carry - unambiguous per plan but requires touching those plans once; (C) grandfather any plan already `Status: reviewed`/`approved` at ship time (advisory), require it only for plans entering review afterward - no plan edits, keys on lifecycle state. The executor MUST get a human decision before E-02 implements the predicate.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: schema + scaffold tests show a `Scope-Paths` stub is emitted and the grammar accepts valid literals/bounded pathspecs and rejects absolute/parent/repo-wide patterns; the spec documents the field.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: lint tests show a post-cutoff plan without `Scope-Paths` is BLOCKED at approval/pre-execution while a pre-cutoff fixture gets only an ADVISORY diagnostic and a terminal record is unaffected; the cutoff predicate is exercised per OQ-01's resolution.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: `tests/test_ipd_schema.py`/`test_ipd_authoring.py`/`test_ipd_lint.py` pass including the non-retroactivity guarantee (a unifyfileio/execset-like fixture is not blocked); `pytest -n auto` is green (pasted).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - define + validate the machine-readable scope contract with a safe grammar and a non-retroactive grandfather policy.

### Execution contract

1. Open questions RESOLVED: OQ-01 (cutoff representation) MUST be resolved by a human before E-02.
2. Scope fence: touch ONLY `ipd_schema.py`, `ipd_authoring.py`, `ipd_lint.py`, the IPD structure/lint spec (via its managed verb), and the three named test files. Do NOT implement begin/finalize or runtime path comparison (Orders 03/04). If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit (via the existing lifecycle workflow, since `aw ipd finalize` does not exist until Order 04).
