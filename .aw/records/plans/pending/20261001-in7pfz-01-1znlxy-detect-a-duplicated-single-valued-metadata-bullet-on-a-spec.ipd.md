# IPD: Detect a duplicated single-valued metadata bullet on a spec, with a multi-valued allowlist the corpus requires

- Date: 2026-10-01
- Kind: child
- Concern: `specs.validate_spec` silently discards a duplicated single-valued metadata bullet, so a hand-edited spec carrying two `- Blocks-Release:` or two `- Gate-Kind:` lines conforms while the same duplicate on a plan is reported as `IPD-M102` and on a backlog item as `backlog.metadata-bullet-repeated`.
- Scope: add a duplicate-bullet finding to the SPEC validator only, mirroring the backlog detector but with the multi-valued allowlist the spec corpus requires; register its severity; test it. No change to any reader, to the backlog or plan detectors, or to any spec file's content.
- Scope-Paths: agent_workflows/specs.py, agent_workflows/check_engine.py, tests/test_specs_metadata_duplicate_bullet.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: in7pfz
- Set: in7pfz
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 1znlxy
- Approval: 2026-10-03, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-03 approved (aw set): status set to approved

- 2026-10-02 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006. Review record: .aw/records/reviews/20261001-in7pfz-01-1znlxy-detect-a-duplicated-single-valued-metadata-bullet-on-a-spec.review.md
- 2026-10-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `in7pfz`; re-measured the gap at HEAD `9b1b722e5` and found the BACKLOG half already closed by executed plan `7ohskw`, narrowing this plan to the spec half alone (see F-01/F-02).

## Goal

Close the remaining half of backlog item `in7pfz`: make `aw specs check` report a duplicated single-valued metadata bullet on a spec, so the three artifact types (plan, backlog item, spec) agree that a duplicated single-valued field is a defect. The backlog half the item describes is already closed, so this plan deliberately covers the spec validator only.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the detector

- [ ] E-01 Add a module-level `_TOP_KEY_RE` equivalent and a `SPEC_MULTI_VALUED_KEYS` frozenset to `agent_workflows/specs.py`, naming the keys a spec may legitimately repeat. Seed it with `Constrained-by` (the only repeated key the corpus carries; see F-03) plus `Related`, `Sources`, `Evidence`, `Supersedes`, `Grounding` and `Implemented-by`, whose names are inherently list-shaped. Document in the frozenset's comment that membership means "repetition is legal", that a key absent from the set is treated as single-valued, and that the backlog detector needs no such set because `backlog._TOP_KEY_RE` governs a closed, all-single-valued field block.
  - Depends on: none
  - Expected outcome: `specs.SPEC_MULTI_VALUED_KEYS` is importable and contains `Constrained-by`; no behavior change yet.
  - Execution state: pending

- [ ] E-02 In `specs.validate_spec`, count top-level `- Key:` bullets within the metadata block delimited by `specs._metadata_end` (the first `## ` heading), and append one `core.Drift` per key whose count exceeds 1 and which is NOT in `SPEC_MULTI_VALUED_KEYS`. Use rule id `spec.metadata-bullet-repeated` (the `spec.` namespace the validator already uses for `spec.priority-invalid` and `spec.work-kind-invalid`, not the `attention.` namespace), and a detail of the shape `metadata bullet - <Key>: appears <N> times`, matching the wording `backlog.validate_item` already emits. Pass the detail through `A.escape_detail` as the neighbouring spec findings do. Do NOT copy the backlog twin's `Kind` -> `Work-Kind` canonicalization: no spec reader accepts the legacy `- Kind:` spelling (`specs._WORK_KIND_RE` matches `- Work-Kind:` only) and no spec in the corpus carries it, so canonicalizing would invent an equivalence the spec contract does not have. KNOW THE BLAST RADIUS, re-measured at review: `validate_spec` is not only the `aw specs check` reader. It is also the in-memory residual gate that makes `aw specs set` and `aw specs migrate` REFUSE a non-conforming result (`specs.run_set`/`run_migrate`: "the resulting spec would not conform; refused"), the per-spec reader of `attention._spec_record` (so `aw attention --check`), the spec arm of the runner's RUN-STRUCTURE-PREFLIGHT in `runner_shared`, and `check_engine`'s specs walk. So after this lands, a hand-duplicated bullet blocks every tooled transition of that spec until a human removes the duplicate. That is the intended fail-closed outcome, and its cost is zero today because F-03 measures no real spec firing.
  - Depends on: E-01
  - Expected outcome: a spec carrying two `- Blocks-Release:` lines yields exactly one `spec.metadata-bullet-repeated` Drift; a spec carrying four `- Constrained-by:` lines yields none.
  - Execution state: pending

- [ ] E-03 Register `spec.metadata-bullet-repeated` in `check_engine.RULE_REGISTRY` as `RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "")`, matching the registration its backlog twin `backlog.metadata-bullet-repeated` carries. Place it beside its backlog twin and extend that block's existing comment to cover it, rather than recording rationale in the plan's history, which is tool-written and is not the place for execution notes. The rationale: an unregistered rule already defaults to error severity via `_DEFAULT_RULESPEC`, so registering changes no exit code; it is required so the rule is not SILENTLY unclassified, which is the stated purpose of that default's comment. CONSTRAINT: the rule id must not contain the substrings `duplicate` or `graduation`, because `tests/test_check_engine_spec_criteria.py::test_rule_id_contains_neither_graduation_nor_duplicate` refuses any such key in `RULE_REGISTRY`; `spec.metadata-bullet-repeated` satisfies this, so do not rename it to a `duplicate` spelling.
  - Depends on: E-02
  - Expected outcome: `check_engine.RULE_REGISTRY["spec.metadata-bullet-repeated"].severity == "error"`.
  - Execution state: pending

### Task group 2: evidence that the corpus still passes

- [ ] E-04 Run `aw specs check --agent` and `aw check all --agent` against the unmodified repository corpus, BEFORE E-02 and AFTER E-03, and paste both captures, confirming the new rule fires on zero real specs (the pre-measured expectation from F-03: only `Constrained-by` repeats, and it is allowlisted). THE BASELINE IS NOT CLEAN, so do not demand conformance: at review `aw specs check` reported 1 pre-existing finding (`attention.unsafe-field` on the over-length `- Scope:` of `20261001-89xjll-01-89xjll-...spec.md`) and `aw check all` reported 97 across many live rules. Those are live counts and context only; re-derive them at execution. The claim this step makes is that `spec.metadata-bullet-repeated` appears ZERO times and that the after-set restricted to spec locations equals the before-set.
  - Depends on: E-03
  - Expected outcome: neither command reports any `spec.metadata-bullet-repeated` finding; the `aw specs check` diagnostic set is identical before and after; no spec file is edited to achieve this.
  - Execution state: pending

### Task group 3: tests

- [ ] E-05 Write `tests/test_specs_metadata_duplicate_bullet.py` exercising `specs.validate_spec` on constructed spec texts (tmp paths, never production source introspection): (a) duplicated `- Blocks-Release:` is reported once with the expected detail; (b) duplicated `- Gate-Kind:` on a `deferred` spec is reported, and does NOT suppress or duplicate the existing gate findings, pinned with TWO fixtures: (b1) both lines carry the SAME valid kind with a valid `- Gate-Ref:`, so the new rule is the ONLY finding; (b2) the lines carry DIFFERENT kinds where the last one (which `_read_gate` keeps) makes the ref invalid, so exactly one `attention.gate-malformed` AND exactly one `spec.metadata-bullet-repeated` are both present. Review measured that (b2)'s shape, `Gate-Kind: date` then `Gate-Kind: decision` with `Gate-Ref: 2027-01-01`, yields `attention.gate-malformed` today and nothing else; (c) four `- Constrained-by:` lines are NOT reported; (d) a duplicate appearing only AFTER the first `## ` heading (i.e. a prose example) is NOT reported, pinning the `_metadata_end` boundary; (e) a conformant single-valued spec yields no finding; (f) the rule id is present in `check_engine.RULE_REGISTRY` with severity `error`.
  - Depends on: E-03
  - Expected outcome: the new test module passes; every assertion is on returned Drift records or registry values, never on source text.
  - Execution state: pending

- [ ] E-06 Add a `CHANGELOG.md` entry under the unreleased section recording the new `spec.metadata-bullet-repeated` rule and its multi-valued allowlist, in the same voice as the existing entry for `backlog.metadata-bullet-repeated`. No em or en dashes (user-facing prose).
  - Depends on: E-05
  - Expected outcome: one added CHANGELOG bullet naming the rule and the allowlist.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The spec validator emits findings in TWO namespaces: `attention.*` for the status/gate/history contract it shares with the attention view (`specs.validate_spec` emits `attention.missing-status`, `attention.gate-malformed`, `attention.unsafe-field`, `attention.history-missing`) and `spec.*` for spec-only field rules (`spec.priority-invalid`, `spec.work-kind-invalid`). A new spec-only field rule therefore belongs in the `spec.` namespace.
- A spec's metadata block is delimited by the first `## ` heading, computed once in `specs._metadata_end`, whose docstring states the reason: so that "prose EXAMPLES of `- Gate-*`/`- Status:` inside a spec body ... are not mistaken for real metadata". Every spec field reader (`specs._read_gate`, `specs._read_blocks_release`, `specs._read_priority`, `specs._read_work_kind`, `specs._read_scope`, `specs._read_summary`) slices `lines[:end]` with it. A new detector must use the same boundary or it will fire on documentation.
- The backlog twin is the structural precedent to copy: `backlog.validate_item` walks the leading bullet block with `backlog._TOP_KEY_RE`, builds a `key_counts` dict, canonicalizes the legacy `Kind` spelling to `Work-Kind`, and emits `backlog.metadata-bullet-repeated` with the detail `metadata bullet - <Key>: appears <N> times`. It uses NO allowlist, which is correct there and wrong here (F-03).
- `core.Drift` is constructed positionally as `core.Drift(location, rule, detail)`, and the location must be the repo-relative POSIX path from `specs.drift_location`, never an absolute path: `specs.validate_spec`'s docstring records that "spec Section 8.5 forbids an absolute path on any output surface, and both callers here feed absolute paths".
- Rule severity lives in `check_engine.RULE_REGISTRY`. An unregistered id is not an error but is "never SILENTLY unclassified" only because `_DEFAULT_RULESPEC` conservatively assumes error; `tests/test_severity_tier_contract.py` pins that every registered RuleSpec carries one of `error`/`warning`/`info`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The BACKLOG half of item `in7pfz` is ALREADY CLOSED, so this plan covers the spec half only. Executed plan `7ohskw` (`.aw/records/plans/executed/20260930-9rl7cm-01-7ohskw-flag-a-duplicated-metadata-bullet-and-a-non-blocked-or-unsaf.ipd.md`) added the detector, landing as commit `f9a1d47ff` "Validate repeated metadata bullets and non-blocked or unsafe Gate-Summary in backlog". Measured at HEAD `9b1b722e5`: injecting a second `- Blocks-Release: next` into a copy of the `in7pfz` item and calling `backlog.validate_item` returns exactly `Drift(rule='backlog.metadata-bullet-repeated', detail='metadata bullet - Blocks-Release: appears 2 times')`. The item's own text predates that plan and so still describes the backlog side as undetected; its description is NOT edited by this plan (the production contract forbids changing the item's requirements). | `backlog.validate_item` key_counts walk; measured run above |
| F-02 | The SPEC half is genuinely still open. Measured at the same HEAD: inserting a duplicate `- Blocks-Release: next` into the approved spec `5tapom` and calling `specs.validate_spec` returns ZERO drift records. Every spec field reader is a first-match-wins or last-match-wins single `.match()` loop that never counts occurrences. | `specs.validate_spec`; measured run above |
| F-03 | A BLUNT all-keys rule (the backlog approach) WOULD FALSE-POSITIVE on the live corpus, which is the one design decision this plan turns on. Censusing all 40 spec files for repeated top-level `- Key:` bullets inside `_metadata_end` finds exactly one repeated key in exactly two files: `Constrained-by`, appearing 4 times in `.aw/records/specs/to-review/20260920-llbr2b-01-llbr2b-lifecycle-automation-policy.spec.md` and 4 times in `.aw/records/specs/to-review/20261001-wy9aru-01-wy9aru-canonical-set-dispatch.spec.md`. Each occurrence cites a DIFFERENT constraining spec path, so the repetition is semantically correct and no tooling reads the key (`rg -n "Constrained-by" agent_workflows/` returns nothing). An allowlist is therefore mandatory, not a refinement. | key census over 40 spec files; `rg` for readers |
| F-04 | The duplicate is not merely cosmetic on a spec: TWO READERS OF THE SAME FILE DISAGREE about which occurrence wins, so a duplicated field can make two tools act on different values. `specs._read_blocks_release` returns on the FIRST match, while `specs._read_gate` overwrites on every match and so returns the LAST. Measured on `["- Status: approved", "- Blocks-Release: first", "- Blocks-Release: second", "- Gate-Kind: spec", "- Gate-Kind: decision", "## Body"]`: `_read_blocks_release` -> `first`, `_read_gate` -> `('decision', None, None)`. This plan does NOT change either reader (changing precedence would alter how existing specs are interpreted); it makes the ambiguous state visible instead. | measured run above |
| F-05 | The backlog item's premise that only a HAND EDIT can now produce the duplicate HOLDS, confirming `chore` rather than `bug`. Plan `izh17y` is executed (`.aw/records/plans/executed/20260930-relwriteempty-01-izh17y-...ipd.md`) and `releases._BLOCKS_RELEASE_LINE_RE` now carries the tolerant `[^\n]*` value group. Measured: `releases.set_blocks_release_line` on a text carrying two `- Blocks-Release:` lines strips BOTH and writes one, i.e. the writer SELF-HEALS the condition rather than creating it. | `releases.set_blocks_release_line`; measured run above |
| F-06 | The plan-side detector this rule is modelled on counts occurrences and reports only the SECOND, yielding exactly one finding per duplicated field rather than one per extra occurrence: `ipd_schema.parse_metadata_block` appends `MetaError(field, "duplicate field")` when `seen[field] == 2`, which `ipd_lint.check_metadata` routes to `IPD-M102`. The backlog twin instead reports once per key with a count in the detail. This plan follows the BACKLOG shape (one finding per key, count in the detail) because it is the artifact-validator precedent and is strictly more informative. | `ipd_schema.parse_metadata_block`; `backlog.validate_item` |
| F-07 | No spec file in the corpus needs editing for this rule to land, and no documentation surface enumerates the drift rules that would need a parallel update: `rg -n "backlog.metadata-bullet-repeated" docs/ .aw/records/specs/` returns nothing, so the backlog twin shipped with a CHANGELOG entry and tests as its only non-code surfaces. | `rg` over `docs/` and `.aw/records/specs/` |

## Proposed changes (ordered, validatable)

1. `agent_workflows/specs.py`: add the top-level-key regex and the `SPEC_MULTI_VALUED_KEYS` allowlist (E-01).
2. `agent_workflows/specs.py`: count keys inside `_metadata_end` in `validate_spec` and emit `spec.metadata-bullet-repeated` for a repeated non-allowlisted key (E-02).
3. `agent_workflows/check_engine.py`: register the rule at error severity (E-03).
4. `tests/test_specs_metadata_duplicate_bullet.py`: new behavior tests, including the allowlist and the prose-boundary cases (E-05).
5. `CHANGELOG.md`: one entry (E-06).

## Deferred / out of scope (with reason)

| Deferred | Reason |
|---|---|
| Changing `specs._read_gate` to first-match-wins so the two readers agree (F-04) | A precedence change alters how EXISTING specs are interpreted, which is a behavior change to every gate reader and needs its own measurement of the corpus. This plan makes the ambiguity visible; it does not silently redefine it. Worth filing separately if a maintainer wants the readers unified. |
| Extending the rule to the RELEASE record validator (`releases.validate_release`) | Not measured, not part of item `in7pfz` (which names backlog items and specs), and the release corpus is tiny. Out of this plan's declared Scope-Paths. |
| Amending the backlog item's text to record that its backlog half is now closed (F-01) | The production contract forbids modifying the backlog item's requirements. The correction is recorded here in F-01 instead, where a reviewer can see it. |
| A `--fix` / autofix that collapses a duplicated bullet | Collapsing requires choosing WHICH value survives, which is exactly the ambiguity F-04 shows the readers disagree on. A detector that refuses is honest; an autofix that guesses is not. |

## Scope check

- Over-scope: none. No reader, no backlog or plan detector, and no spec file content is changed.
- Under-scope: the plan closes the spec half of `in7pfz` only, because F-01 measured the backlog half as already closed by `7ohskw`. The item's own prose still describes both halves as open; that is a stale description, not unfinished work, and F-01 records the measurement a reviewer can re-run.

## Required tests / validation

- `python3 -m pytest tests/test_specs_metadata_duplicate_bullet.py` (new module, run narrowed with `-o addopts=""` if per-test counts are wanted).
- `python3 -m pytest` bare, for the full fast suite, BEFORE E-01 and AFTER E-06, pasting both summary lines. The baseline may carry pre-existing failures unrelated to this plan; the bar is that the after-run carries no failure absent from the before-run.
- `aw specs check` and `aw check all` against the unmodified corpus, proving zero new findings on real specs.

## Spec / documentation sync

No `.spec.md` amendment is required, and none is declared in `- Scope-Paths:`. This plan adds a validator finding within an existing validator's existing contract; it changes no documented field grammar, no status enum, and no public flag surface. F-07 records that no documentation surface enumerates the drift rules, so `CHANGELOG.md` is the only non-code surface, and it is declared.

## Open questions

### OQ-01: Should `SPEC_MULTI_VALUED_KEYS` be seeded beyond the one key the corpus actually repeats?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: Resolved from repository evidence. The corpus repeats only `Constrained-by` (F-03), so a minimal allowlist would be `{"Constrained-by"}`. E-01 seeds a slightly wider set (`Related`, `Sources`, `Evidence`, `Supersedes`, `Grounding`, `Implemented-by`) because each names an inherently list-shaped relation that a future spec will legitimately repeat, and the cost asymmetry is stark: an over-narrow allowlist makes a CORRECT spec fail `aw check` and pressures the author to mangle real content, while an over-wide one merely fails to catch a duplicate on a key nothing reads. Every allowlisted key is confirmed to have no tooling reader. The gated single-valued fields that motivate the rule (`Blocks-Release`, `From-Backlog`, `From-Spec`, `Status`, `Id`, `Gate-Kind`, `Gate-Ref`, `Priority`, `Work-Kind`) are all absent from the allowlist and so remain covered.

### OQ-02: Should the finding be `error` or advisory `info`?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: Resolved as `error`, for consistency with both existing twins: `backlog.metadata-bullet-repeated` is registered `error`, and the plan-side `IPD-M102` is a lint error. Since F-03 proves the rule fires on zero real specs once `Constrained-by` is allowlisted, `error` costs the repository nothing today, and F-04 shows the state it flags genuinely makes two readers disagree. Note also that an UNREGISTERED id already evaluates as error via `_DEFAULT_RULESPEC`, so `info` would be the only choice requiring a deliberate downgrade, and nothing in the evidence argues for one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the output of `python3 -c "from agent_workflows import specs; print(sorted(specs.SPEC_MULTI_VALUED_KEYS))"` showing `Constrained-by` present and showing `Blocks-Release`, `From-Backlog`, `From-Spec`, `Gate-Kind`, `Gate-Ref`, `Status` and `Id` ABSENT.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a run that builds a spec text with two `- Blocks-Release:` bullets and prints `specs.validate_spec(path, text)`, showing EXACTLY ONE record whose rule is `spec.metadata-bullet-repeated` and whose detail reads `metadata bullet - Blocks-Release: appears 2 times`; and a second run over a text with four `- Constrained-by:` bullets showing ZERO such records. Also show the Drift `location` is repo-relative, not absolute.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the output of `python3 -c "from agent_workflows import check_engine as c; print(c.RULE_REGISTRY['spec.metadata-bullet-repeated'])"` showing severity `error`, and the output of `python3 -m pytest tests/test_severity_tier_contract.py` showing it still passes.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the BEFORE (pre-E-02) and AFTER (post-E-03) output of `aw specs check --agent` and `aw check all --agent` run on the corpus with NO spec file modified, showing ZERO `spec.metadata-bullet-repeated` findings in the after captures and an identical `aw specs check` `{location, rule}` set before and after. Do NOT claim conformance: name each pre-existing finding as pre-existing. If any real spec does fire, do NOT edit that spec: stop and report, because F-03 predicted zero and a nonzero result falsifies the allowlist.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the output of `python3 -m pytest tests/test_specs_metadata_duplicate_bullet.py -o addopts=""` showing all cases passing with counts, AND the bare `python3 -m pytest` summary lines from BEFORE E-01 and AFTER E-06, naming any failure present in both as pre-existing and showing no NEW failure; do not describe the suite as clean if it is not. Confirm in one sentence that no test in the new module reads production source text via `inspect`, `ast`, regex or substring search (GUIDING_PRINCIPLES P16).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the added `CHANGELOG.md` bullet and confirm it contains no em or en dash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution; it is authored `to-review` and carries no `- Readiness:` field, because that field is an output of `/plan-review` and not of authoring.

On execution, follow the repository execution contract: commit only the paths named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; paste actual test output rather than claiming success. Do not mark any `V-*` as `pass` from the matching execution checkmark; inspect evidence in a separate pass.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition; if an edit outside it proves necessary, make it and JUSTIFY it, which `aw ipd finalize` enforces with a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path. Post-gate lifecycle: once every `E-*` is `performed`, every `V-*` is `pass` with pasted evidence, and `aw ipd lint --phase pre-transition` reports conforming, the terminal transition is `aw ipd finalize 1znlxy --apply`; under `aw oc run` / `aw agy run` the runner owns it, and when executed by hand the executor runs it. Never hand-roll a `git mv` to `executed/`. Backlog item `in7pfz` is then closable by the runner on the normal `graduated` path; this plan carries `- From-Backlog: in7pfz` so the handoff is machine-readable. The item carries no `- Blocks-Release:` gate, so none is inherited here.
