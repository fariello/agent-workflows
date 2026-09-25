# IPD: Make the release-gating work-kind set configurable per repository

- Date: 2026-09-25
- Kind: child
- Concern: The work-kinds that automatically gate the next release are hardcoded as `backlog.GATE_DEFAULT_KINDS = frozenset(("bug",))`, so a repository that wants `security` (or anything else) to gate cannot say so, and AGENTS.md records the configurable version as "designed but NOT yet built (backlog `0htqmm`)".
- Scope: Add a `release_gate_work_kinds` key to `.aw/config/project.json`, read by one new `config` reader that defaults to `bug` alone, and route BOTH consumers of the hardcoded set (`backlog.decide_gate_default` and `check_engine.check_live_bug_gate`) through it; update the AGENTS.md sentence and the `backlog.py` comment that say it is unbuilt.
- Scope-Paths: agent_workflows/config.py, agent_workflows/backlog.py, agent_workflows/check_engine.py, AGENTS.md, tests/test_config_release_gate_kinds.py, tests/test_check_engine_release_gate.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: medium
- Set: gatekinds
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: kxawm4
- From-Backlog: 0htqmm

## Workflow history

- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 0htqmm; re-measured that no gating-kind config key exists (only `backlog.GATE_DEFAULT_KINDS`, consumed at `backlog.decide_gate_default` and `check_engine.check_live_bug_gate`) and that the AGENTS.md sentence is hand-maintained with no generator in `engine.py`.

## Goal

Let each repository name the work-kinds whose live items must carry `- Blocks-Release:`, defaulting to `bug` alone so a repository that configures nothing behaves exactly as today, following the `review_findings_gate` precedent in `config.py`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the reader

- [ ] E-01 In `agent_workflows/config.py`, beside `read_review_findings_gate` / `findings_gate_threshold`, add `RELEASE_GATE_WORK_KINDS_KEY = "release_gate_work_kinds"`, `RELEASE_GATE_WORK_KINDS_DEFAULT = frozenset({"bug"})`, and `release_gate_work_kinds(repo_root, *, warn=None) -> frozenset[str]`. Accepted shapes: an object `{"kinds": ["bug", "security"]}` and, for convenience, a bare list or a bare string (one kind). Values are lowercased, stripped, and intersected against the `backlog.KINDS` vocabulary (pass the vocabulary in, or define the legal set in `config` with a comment, so `config` does not import `backlog`). Posture follows the `policy_retry_budget` rule recorded in that section's comment ("FALL BACK TO THE DEFAULT AND EMIT A VISIBLE WARNING NAMING THE KEY AND THE BAD VALUE"): an absent key returns the default silently; a malformed value or an unknown kind name returns the default (or drops just the unknown name) and warns once naming the key, the value, and the file. An explicit empty list `[]` is legal and means "no kind auto-gates" (explicit opt-out, mirroring `review_findings_gate`'s `off`). Do NOT register the key in `CONFIG_SCHEMA`, for the reason documented above `REVIEW_FINDINGS_GATE_KEY`.
  - Depends on: none
  - Expected outcome: `release_gate_work_kinds(tmp)` returns `frozenset({"bug"})` with no project.json, and the configured set when one is written.
  - Execution state: pending

- [ ] E-02 Add `tests/test_config_release_gate_kinds.py` covering: absent file, absent key, object form, bare list, bare string, empty list, unknown kind name (warns, dropped), non-list garbage (warns, default), and that the key round-trips through `project_schema.parse_portable_policy` (lands in `unknown_fields` and is written back).
  - Depends on: E-01
  - Expected outcome: new test module passes.
  - Execution state: pending

### Task group 2: route both consumers through the reader

- [ ] E-03 In `agent_workflows/backlog.py` `decide_gate_default`, replace `if (kind or "") not in GATE_DEFAULT_KINDS:` with a check against `config.release_gate_work_kinds(repo_root)` (the function already receives `repo_root`). Keep `GATE_DEFAULT_KINDS` as a deprecated alias of `config.RELEASE_GATE_WORK_KINDS_DEFAULT` so any importer keeps working. Generalize the two notice strings that say "this bug" to name the item's kind (e.g. "on this security item"). Rewrite the comment block above `GATE_DEFAULT_KINDS` ("making the set configurable per repository (defaulting to `bug`) is designed and carried by its own backlog item, NOT shipped here") to state it is now configured via the key.
  - Depends on: E-01
  - Expected outcome: with `{"release_gate_work_kinds": {"kinds": ["bug","security"]}}` and a planned release, `aw backlog new --work-kind security ...` defaults `- Blocks-Release: next`; with no config it does not.
  - Execution state: pending

- [ ] E-04 In `agent_workflows/check_engine.py` `check_live_bug_gate`, replace `if item.kind not in _backlog.GATE_DEFAULT_KINDS:` with membership in `config.release_gate_work_kinds(repo_root)` computed ONCE before the loop. Keep the rule id `check.live-bug-ungated` (renaming a shipped rule id is out of scope) but make the detail text name the actual kind instead of hardcoding "Work-Kind: bug". Add to `tests/test_check_engine_release_gate.py`: (a) a live ungated `security` item is CLEAN with no config; (b) it is FLAGGED when the key lists `security`; (c) a live ungated `bug` is CLEAN when the key is `[]`.
  - Depends on: E-01
  - Expected outcome: the three new tests pass; the existing `test_rule_live_bug_ungated_reachable` and `test_live_bug_with_gate_is_clean` still pass unchanged.
  - Execution state: pending

### Task group 3: docs and suite

- [ ] E-05 Edit `AGENTS.md` section "### Every live bug gates the next release": replace "`bug` is the only gating work-kind today; making that set configurable per repository, defaulting to `bug` alone, is designed but NOT yet built (backlog `0htqmm`), so do not look for a config key to widen it." with a sentence naming the key `release_gate_work_kinds` in `.aw/config/project.json`, its default (`bug` alone), the empty-list opt-out, and the fall-back-and-warn posture. Also generalize "whose `- Work-Kind:` is `bug`" in the opening sentence to "whose `- Work-Kind:` is in the repository's gating set (default `bug`)". Edit `AGENTS.md` DIRECTLY: this section is outside the managed `<!-- aw:block -->` region and has no generator (see Findings F-3).
  - Depends on: E-01
  - Expected outcome: AGENTS.md no longer contains "designed but NOT"; `engine.py` untouched.
  - Execution state: pending

- [ ] E-06 Run the bare suite `python3 -m pytest`.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: summary line with 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Repository policy keys live in `.aw/config/project.json`, read by dedicated `config.py` readers that never raise and are deliberately NOT in `CONFIG_SCHEMA` (comment above `REVIEW_FINDINGS_GATE_KEY`; `read_run_policy`).
- Malformed repository policy falls back and warns (maintainer ruling 2026-09-10, `y4adch` OQ-01, recorded in the `policy_retry_budget` section comment).
- `decide_gate_default` is "THE SINGLE AUTHORITY" for defaulting and has three call sites (`backlog.run_new`, `backlog.run_set`, `status_set.apply_status_change`), so changing it once covers all three.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-1 | Still unbuilt: no config key names gating kinds. | `grep -rn -i 'gating_work_kinds\|release_gate_work\|gate_work_kinds' agent_workflows/*.py` returns nothing; the only set is `backlog.GATE_DEFAULT_KINDS = frozenset(("bug",))`. |
| F-2 | Exactly two consumers read the set. | `grep -rn GATE_DEFAULT_KINDS agent_workflows/`: `backlog.decide_gate_default` ("if (kind or \"\") not in GATE_DEFAULT_KINDS") and `check_engine.check_live_bug_gate` ("if item.kind not in _backlog.GATE_DEFAULT_KINDS"). No test imports it. |
| F-3 | The AGENTS.md sentence is hand-maintained; no generator emits it. | `grep -c 'configurable per repository' agent_workflows/engine.py` = 0. The sentence is at AGENTS.md:165, after `<!-- /aw:block -->` at :123. Plan `zqs0px`'s review record retracted the same "emitted from engine.py" claim with four proofs. So `engine.py` is deliberately NOT in Scope-Paths, contrary to the triage brief's expectation. |
| F-4 | Only other "unbuilt" statement in code is the comment above `GATE_DEFAULT_KINDS` in `backlog.py`. | `grep -rn 'configurable per repository' agent_workflows/` hits only `backlog.py`. |

## Proposed changes (ordered, validatable)

1. Reader + default in `config.py` (E-01) with its unit tests (E-02).
2. Both consumers use the reader (E-03, E-04), with tests showing the set is honored and the default preserved.
3. Contributor rule text updated (E-05); full suite (E-06).

## Deferred / out of scope (with reason)

- A general "all auto-gates" config object: explicitly offered and DECLINED by the maintainer in `0htqmm` ("would design a surface before a second real case exists").
  - Carrier-Declined: maintainer declined the broader surface on 2026-09-12, recorded in backlog 0htqmm "Deliberately NOT in scope".
- Renaming rule id `check.live-bug-ungated` to a kind-neutral name: a shipped rule id; renaming breaks suppressions and docs for no behavior gain.
  - Carrier-Declined: cosmetic; the detail text names the real kind, which is sufficient.
- Retroactively gating existing live `security` items in this repo: this repo keeps the default, so none become flagged.
  - Carrier-Declined: default is unchanged here by design (0htqmm "Why the default is `bug` only").

## Scope check

- Over-scope: none.
- Under-scope: specs and plans carrying `- Work-Kind:` are not checked by `check_live_bug_gate` today (it iterates backlog items only); this plan preserves that and does not widen it.

## Required tests / validation

New `tests/test_config_release_gate_kinds.py`; three new cases in `tests/test_check_engine_release_gate.py`; one proven failing before E-04; bare suite.

## Spec / documentation sync

AGENTS.md "Every live bug gates the next release" (E-05). No `.spec.md` governs `Blocks-Release` defaulting, so no spec amendment. `DECISIONS.md` optional; not required.

## Open questions

### OQ-01: Should the key also accept per-kind statuses or a release other than `next`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. `decide_gate_default` always writes `next` and the skip-status set is policy, not preference; 0htqmm asks only for the kind set. Default: kinds only.

### OQ-02: Unknown kind name in the list: drop just it, or reject the whole value?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default: drop the unknown name and warn, keeping the valid ones, because rejecting the whole list would silently remove a `security` gate the repository asked for over one typo. Maintainer may prefer whole-value fallback.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -c "from agent_workflows import config; import tempfile; print(sorted(config.release_gate_work_kinds(tempfile.mkdtemp())))"` printing `['bug']`, and `grep -n release_gate_work_kinds agent_workflows/config.py` showing the key, default, and reader; `grep -c release_gate_work_kinds agent_workflows/project_schema.py` = 0 (not registered).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest tests/test_config_release_gate_kinds.py` summary line showing all passed, including the round-trip case.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: in a scratch repo with a planned release record and `{"release_gate_work_kinds": {"kinds": ["bug","security"]}}`, paste the output of `python3 -m agent_workflows backlog new --work-kind security ...` showing the "defaulted - Blocks-Release: next" notice and the file line `- Blocks-Release: next`; then with the key removed, paste the same command producing no gate. `grep -n 'designed and carried by its own backlog item' agent_workflows/backlog.py` returns nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_check_engine_release_gate.py` with the new security-flagged test FAILING before the `check_live_bug_gate` change (write the tests first and run them before applying the `check_engine.py` edit), then the full module passing after.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `grep -c 'designed but NOT' AGENTS.md` = 0; `grep -n release_gate_work_kinds AGENTS.md` shows the new sentence; `git diff --name-only -- agent_workflows/engine.py` is empty.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the bare `python3 -m pytest` summary line showing `N passed` and 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval. Commit through `aw commit <plan> -- <Scope-Paths>`, never push. After every V-* item carries pasted evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `executed/` via `aw ipd finalize`.
