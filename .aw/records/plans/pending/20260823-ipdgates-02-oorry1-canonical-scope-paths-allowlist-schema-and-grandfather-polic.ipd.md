# IPD: Canonical Scope-Paths allowlist schema and grandfather policy

- Date: 2026-08-23
- Kind: child
- Concern: IPD scope is expressed only in free-form `Scope:` prose, which tooling cannot compare against the actually-changed paths - so an executor can expand file scope (as p7dqwz did with `tests/test_empty_state_ux.py`) and nothing deterministic catches it. There is no machine-readable declared-path contract on an IPD.
- Scope: Add a canonical `Scope-Paths` allowlist to the IPD schema and its build/validate surfaces, with a grandfather policy for already-reviewed pending plans. Touch: agent_workflows/ipd_schema.py (the metadata contract), agent_workflows/ipd_authoring.py (scaffold emits a `Scope-Paths` stub), agent_workflows/ipd_lint.py (parse + validate + checkpoint diagnostics), the implemented IPD structure/lifecycle spec (via `aw specs note` / the managed spec verb), and focused tests/test_ipd_schema.py + tests/test_ipd_authoring.py + tests/test_ipd_lint.py. Does NOT implement begin/finalize (Orders 03/04) or compare paths at runtime (that is finalize, Order 04); this child only defines and validates the declared contract.
- Status: approved
- Set: ipdgates
- Order: 2
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: oorry1

## Workflow history
- 2026-08-24 approved (aw set, --by-human): status set to approved
- 2026-08-24 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. PR-001 (MEDIUM, correctness): E-01 now specifies Scope-Paths goes in META_RECOGNIZED only, NOT META_REQUIRED (adding to required would fail every pending plan at author phase and defeat the grandfather guarantee - verified ipd_schema.py:128,147 + check_metadata runs all phases). PR-002 (LOW, clarity): there is no 'approval' lint phase (CHECKPOINTS = author/pre-execution/pre-transition/post-transition/review-finalize); E-02 now fires at pre-execution + for approved/auto-approved status, in check_checkpoint not check_metadata. PR-003 (MEDIUM, UNDER-SCOPE right-sizing): split the old E-02 into E-02 (lint conditional gate) + E-03 (bulk 21-file cross-Set grandfathered stamping); tests renumbered to E-04; V-items re-bijected; watermark 03->04. PR-004 (LOW density): IPD-Z602 advisory on E-01 investigated and kept atomic (define-the-field is one coherent unit) with recorded rationale. Verified all 3 Set memberships (unifyfileio 6 + execset 6 + ipdgates 9 = 21) resolve to real on-disk plans; modules/tests/spec exist; OQ-01 resolved.

- 2026-08-23 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created (decomposition of 39fz2x E-02).
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. Verified cited modules exist and check_engine.check_names consumes npn.is_conformant (check_engine.py:125) / ipd_lint._name_conformant (:72); both sibling Sets exist. OQ-01 resolved by human: explicit per-plan `Scope-Paths: grandfathered` sentinel marker (immune to the re-review flip that the rejected lifecycle-state option would suffer). PR-001 (the ipdgates Set's OWN plans were omitted from the grandfather set though the orchestrator Self-bootstrap requires them - added ipdgates to Step-0/E-02, ~19 total); PR-002 (resolved via OQ-01); PR-003 (marker stored in each plan's metadata block, not a separate config). Scope-fence expanded to permit adding ONLY the single `Scope-Paths: grandfathered` line to the ~19 pre-cutoff plans (a bounded metadata migration), with re-resolve/STOP-on-ambiguity; E-01/E-02/V-02/V-03 updated for the marker predicate + stamping.
- 2026-08-24 consistency-fix (opencode its_direct/pt3-claude-opus-4.8-1m-us): post-renumber Set audit - the grandfather enumeration was stale after the ipdgates reconciliation split: it listed ipdgates as 7 plans and omitted the NEW Order 05 (`qmt3yk`), and OQ-01 said "~17" while the rest of the file said "~19". Corrected to the true count (unifyfileio 6 + execset 6 + ipdgates 8 = 20, incl. `qmt3yk`) and added "enumerate current Set membership via `aw find` at execution time" so the grandfather set is robust to future membership drift rather than a brittle fixed list. Reset `reviewed` -> `to-review` because this is a MATERIAL correction (a plan missing from the grandfather set could be wrongly blocked), not a pointer-only fix. (The prior `/plan-review` history line above is left verbatim; its "~19" was accurate at that time.)
- 2026-08-24 grandfather-count-bump (opencode its_direct/pt3-claude-opus-4.8-1m-us): ipdgates gained Order 08 (`dulzpy`, local pre-commit executed-gate), so the ipdgates own-plan count is now 9 and the grandfather total is 21 (unifyfileio 6 + execset 6 + ipdgates 9). Added `dulzpy` to the enumeration and updated ~20->~21 throughout the live text (the "aw find at execution time" instruction remains the authoritative source).

## Goal

Give every post-cutoff IPD ONE deterministic, machine-readable `Scope-Paths` allowlist (repo-relative literal paths or bounded pathspecs) that later tooling (`aw ipd finalize`, Order 04) can compare against the real changed paths. Define a safe grammar (reject absolute paths, `..` parent escapes, and repo-wide globs), implicit lifecycle-artifact exceptions (the plan file itself, its index refresh), and generated-file treatment. Require the allowlist at approval / pre-execution for NEW or re-reviewed plans, while GRANDFATHERING the already-reviewed pending sibling Sets (`unifyfileio`, `execset`) as `Scope-Paths`-optional with only an advisory diagnostic; existing terminal records stay untouched.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Define the contract

- [ ] E-01 Add `Scope-Paths` as a RECOGNIZED-BUT-OPTIONAL field to the canonical IPD metadata contract in `agent_workflows/ipd_schema.py` (add it to `META_RECOGNIZED` only; do NOT add it to `META_REQUIRED`, and do NOT add it to any all-or-none paired group). Making it universally required would fail every existing pending plan at the `author` checkpoint (non-terminal plans always run `check_metadata`) and defeat the grandfather guarantee; the requirement is CONDITIONAL and belongs in the checkpoint layer (E-02), not the always-on metadata-required set. Emit a `Scope-Paths` stub from `aw ipd scaffold` (`ipd_authoring.py`): a list of repo-relative literal paths or bounded pathspecs, OR the reserved sentinel value `grandfathered` (per OQ-01). Define the safe grammar - reject absolute paths, `..` parent escapes, and repo-wide/`**`-at-root globs; allow directory-bounded pathspecs; accept the `grandfathered` sentinel as a distinct legal value; define implicit exceptions (the plan's own file + its manifest/index refresh are always allowed) and how generated files are declared. Document the field (including the `grandfathered` sentinel and the recognized-but-optional status) in the spec via the managed spec verb.
  - Depends on: none
  - Expected outcome: the schema and scaffold know `Scope-Paths`, its grammar is specified, and the spec documents it.
  - Execution state: pending

### Task group 2: Validate + grandfather

- [ ] E-02 Add `Scope-Paths` parsing and CONDITIONAL validation to `ipd_lint.py` using the OQ-01 marker predicate, in the checkpoint layer (`check_checkpoint`) - NOT in the always-on `check_metadata`. The lint `--phase` vocabulary is `author`/`pre-execution`/`pre-transition`/`post-transition`/`review-finalize` (there is no `approval` phase); the requirement therefore fires at the `pre-execution` checkpoint AND for any plan whose `Status` is `approved`/`auto-approved` (the ready-to-execute tier), so an approved plan cannot slip through without the field. At that gate: a plan with NO `Scope-Paths` field at all is HARD-REQUIRED (blocking diagnostic with actionable text); a plan carrying `Scope-Paths: grandfathered` is advisory-satisfied (non-blocking); a plan declaring a REAL allowlist is validated against the E-01 grammar (malformed = blocking). Existing TERMINAL records are unaffected (terminal-dir files short-circuit to the `legacy` disposition before `check_checkpoint`, so they are never claimed conformant and never blocked). The `author` phase does NOT require the field (so a fresh draft and every un-stamped pending plan still lint clean until they reach the pre-execution/approved gate).
  - Depends on: E-01
  - Expected outcome: at `pre-execution` and for approved/auto-approved plans, a fieldless plan is blocked, a `grandfathered`-marked plan is advisory-only, and a real-allowlist plan is grammar-validated; the `author` phase and terminal records are unaffected.
  - Execution state: pending

- [ ] E-03 STAMP the `Scope-Paths: grandfathered` marker onto every pre-cutoff pending plan (a bounded metadata migration; enumerate the CURRENT membership of each Set via `aw find` at execution time rather than trusting this list): the `unifyfileio` Set (g6mbht/o6b8l3/laykok/3cmnfc/52zgqr/9a655p = 6), the `execset` Set (5ahblp/iy1a2g/3m4e54/m2wwns/31744f/2h7777 = 6), and the `ipdgates` Set's OWN plans (do64fh + v6zie5/oorry1/xjbvu2/v7e88a/qmt3yk/3xh53a/wezhxg/dulzpy = 9, incl. Order 05 reconciliation `qmt3yk` and Order 08 local commit-gate `dulzpy` - the ipdgates Set predates its own requirement, per the orchestrator Self-bootstrap section); total ~21. Add ONLY the single `Scope-Paths: grandfathered` line to each plan's metadata block, nothing else; re-resolve via `aw find` and STOP-and-report on any ambiguity (status/location drift) rather than force-stamping. Commit them path-scoped with this plan's own changes.
  - Depends on: E-01, E-02
  - Expected outcome: all ~21 pre-cutoff pending plans carry the `grandfathered` marker (added line only, no other content changed) so none is retroactively blocked once E-02's gate is live.
  - Execution state: pending

### Task group 3: Prove it

- [ ] E-04 Add tests in `tests/test_ipd_schema.py`, `tests/test_ipd_authoring.py`, and `tests/test_ipd_lint.py` covering: `Scope-Paths` is recognized-but-optional (present in `META_RECOGNIZED`, absent from `META_REQUIRED`; a fieldless plan lints clean at `author`); valid literals + bounded pathspecs accepted; absolute/parent/repo-wide patterns rejected; implicit lifecycle + generated-file exceptions; missing-allowlist BLOCKING refusal at `pre-execution` and for an `approved`/`auto-approved` fixture; ADVISORY-only (non-blocking) diagnostic for a `grandfathered`-marked pre-cutoff fixture standing in for a `unifyfileio`/`execset` sibling; unchanged grandfathered-terminal behavior (terminal-dir -> legacy); and spec/scaffold/schema parity. Confirm `pytest -n auto` is green.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: the contract, the conditional-checkpoint enforcement, and the grandfather policy are falsifiably tested, including the recognized-but-optional and non-retroactivity guarantees.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The IPD metadata contract and its required/optional fields are defined in `agent_workflows/ipd_schema.py`; the structural linter is `agent_workflows/ipd_lint.py`; the scaffold that emits a conformant skeleton is `agent_workflows/ipd_authoring.py`. The canonical structure/lint spec is `.aw/records/specs/20260802-1904-01-ipd-structure-and-linting.spec.md` (implemented).
- ~21 already-reviewed/in-flight pending plans exist that MUST NOT be retroactively blocked (39fz2x OQ-03 + ipdgates orchestrator Self-bootstrap, human-resolved): the `unifyfileio` Set (g6mbht/o6b8l3/laykok/3cmnfc/52zgqr/9a655p = 6), the `execset` Set (5ahblp/iy1a2g/3m4e54/m2wwns/31744f/2h7777 = 6), AND the `ipdgates` Set's own plans (do64fh/v6zie5/oorry1/xjbvu2/v7e88a/qmt3yk/3xh53a/wezhxg/dulzpy = 9, incl. Order 05 reconciliation `qmt3yk` and Order 08 local commit-gate `dulzpy`; this Set predates its own requirement). Total = 21. Enumerate the CURRENT membership of each Set at execution time via `aw find` rather than trusting this list, since Sets may gain/lose members. All are grandfathered via the OQ-01 marker.

## Findings

Free-form `Scope:` prose is not machine-comparable, so scope expansion is undetectable by tooling. A declared `Scope-Paths` allowlist is the substrate the finalize transaction (Order 04) needs to compare declared vs actual changed paths. Introducing it must not invalidate the reviewed backlog of pending plans, hence the grandfather cutoff.

## Proposed changes (ordered, validatable)

1. Add `Scope-Paths` (recognized-but-optional) to schema + scaffold + spec with a safe grammar (E-01).
2. Add conditional lint validation (blocking at pre-execution/approved, advisory when `grandfathered`) in the checkpoint layer (E-02).
3. Stamp the `grandfathered` marker onto the ~21 pre-cutoff pending plans (E-03).
4. Test the grammar, the conditional checkpoints, the recognized-but-optional guarantee, and the non-retroactivity guarantee (E-04).

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
- Status: resolved
- Owner: human
- Resolution or deferral rationale: RESOLVED by human (2026-08-23, /plan-review): an EXPLICIT per-plan marker `Scope-Paths: grandfathered` (a reserved sentinel value of the `Scope-Paths` field). Lint treats `Scope-Paths: grandfathered` as advisory-satisfied (non-blocking); a plan that declares a REAL `Scope-Paths` allowlist is validated against the grammar; a plan with NEITHER (no `Scope-Paths` at all) is hard-required/blocked at approval/pre-execution. This is unambiguous per plan, auditable in git, and immune to the re-review flip that a lifecycle-state cutoff (rejected option C) would suffer. The one-time cost - stamping `Scope-Paths: grandfathered` onto the pre-cutoff plans - is done by E-02 as an explicit sub-step over the ~21 pre-cutoff plans: the `unifyfileio` Set (6), the `execset` Set (6), and the `ipdgates` Set's own plans (9 - its orchestrator + eight children incl. Order 05 reconciliation and Order 08 local commit-gate, per the ipdgates orchestrator Self-bootstrap section - the ipdgates Set predates its own requirement and MUST be grandfathered too). Enumerate current Set membership via `aw find` at execution time rather than trusting a fixed count. The marker is stored IN each plan's metadata block (the `Scope-Paths:` field itself), not in a separate config, so it travels with the plan.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: schema + scaffold tests show a `Scope-Paths` stub is emitted and the grammar accepts valid literals/bounded pathspecs and rejects absolute/parent/repo-wide patterns; the spec documents the field.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: lint tests show that at `pre-execution` (and for an `approved`/`auto-approved` fixture) a plan with NO `Scope-Paths` field is BLOCKED, a plan carrying `Scope-Paths: grandfathered` is advisory-satisfied (non-blocking), a real-allowlist plan is grammar-validated, and a terminal-dir record is unaffected (legacy disposition); AND that the `author` phase does NOT block a fieldless plan. Show the enforcement lives in `check_checkpoint`, not `check_metadata`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: a scan shows every enumerated pre-cutoff plan (unifyfileio + execset + ipdgates Sets, current membership via `aw find`) now carries `Scope-Paths: grandfathered`; the per-file diff shows ONLY the single added line (no other content changed); the count matches the enumerated set (~21) and any drift was re-resolved/STOP-reported, not force-stamped.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: `tests/test_ipd_schema.py`/`test_ipd_authoring.py`/`test_ipd_lint.py` pass including the recognized-but-optional guarantee (in `META_RECOGNIZED`, not `META_REQUIRED`; fieldless lints clean at `author`), the conditional gate (fieldless=blocked at pre-execution/approved, `grandfathered`=advisory, real-allowlist=validated), and the non-retroactivity guarantee (a `grandfathered`-marked fixture is not blocked); `pytest -n auto` is green (pasted).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - define + validate the machine-readable scope contract with a safe grammar and a non-retroactive grandfather policy - split into four focused passes: E-01 defines the field (schema recognized-but-optional + grammar + scaffold stub + spec doc, an atomic "define the field" unit; the IPD-Z602 density advisory on E-01 was reviewer-assessed and kept atomic because a half-defined field is not independently useful or verifiable), E-02 adds the conditional checkpoint enforcement, E-03 stamps the ~21 pre-cutoff plans (a bounded data migration, deliberately separated from the E-02 code), and E-04 tests all of it.

### Execution contract

1. Open questions RESOLVED: OQ-01 (cutoff representation) resolved by human (2026-08-23) - an explicit per-plan `Scope-Paths: grandfathered` sentinel marker; E-03 stamps it onto the ~21 pre-cutoff pending plans (enumerate current Set membership via `aw find`).
2. Scope fence: touch ONLY `ipd_schema.py`, `ipd_authoring.py`, `ipd_lint.py`, the IPD structure/lint spec (via its managed verb), the three named test files, AND - solely to add the single `Scope-Paths: grandfathered` metadata line (nothing else) - the ~21 pre-cutoff pending plan files enumerated in E-03 (the `unifyfileio`, `execset`, and `ipdgates` Sets; enumerate current membership via `aw find`). Do NOT otherwise edit those sibling plans, and do NOT implement begin/finalize or runtime path comparison (Orders 03/04). If a sibling plan has meanwhile changed status/location, re-resolve it via `aw find` and STOP-and-report on any ambiguity rather than force-stamping.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit (via the existing lifecycle workflow, since `aw ipd finalize` does not exist until Order 04).
