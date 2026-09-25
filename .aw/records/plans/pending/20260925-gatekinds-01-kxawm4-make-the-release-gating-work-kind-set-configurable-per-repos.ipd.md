# IPD: Make the release-gating work-kind set configurable per repository

- Date: 2026-09-25
- Kind: child
- Concern: The work-kinds that automatically gate the next release are hardcoded as `backlog.GATE_DEFAULT_KINDS = frozenset(("bug",))`, so a repository that wants `security` (or anything else) to gate cannot say so, and AGENTS.md records the configurable version as "designed but NOT yet built (backlog `0htqmm`)".
- Scope: Add a `release_gate_work_kinds` key to `.aw/config/project.json`, read by one new `config` reader that defaults to `bug` alone, and route BOTH consumers of the hardcoded set (`backlog.decide_gate_default` and `check_engine.check_live_bug_gate`) through it; update the AGENTS.md sentence and the `backlog.py` comment that say it is unbuilt.
- Scope-Paths: agent_workflows/config.py, agent_workflows/backlog.py, agent_workflows/check_engine.py, AGENTS.md, tests/test_config_release_gate_kinds.py, tests/test_check_engine_release_gate.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: medium
- Set: gatekinds
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: kxawm4
- From-Backlog: 0htqmm

## Workflow history
- 2026-09-25 reviewed (aw set): status set to reviewed

- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-301..PR-307 all FIXED, no deferrals, no open questions (OQ-02 resolved from the recorded config posture). The plan's survey is accurate and its precedent well chosen; F-1, F-2, F-3 and F-4 all re-verified independently, and F-3's boundary re-proved because acting on its opposite is a measured hazard a sibling review retracted. Findings: E-03 and E-04 each named fewer hardcoded kind strings than exist (three notices in backlog.py, two drift fields in check_engine.py, plus a docstring condition and a RuleSpec comment that assert `bug` alone); V-01's schema assertion targeted `project_schema.py`, a module this plan never edits, so it would pass regardless; E-02's round-trip is real but the serializer is `to_dict`, not `as_dict`; the vocabulary-duplication choice needed the `REVIEW_GATE_THRESHOLDS` precedent stated; and the `RuleSpec` determinism tag must NOT change. Added F-5..F-10, measured the 13-test baseline and the zero-drift-when-widened result, and rewrote the gate with a scope fence, honesty rule and two stop conditions. Split E-03 and E-05 to clear two IPD-Z602 size advisories my own clarifications raised; E/V renumbered to E-01..E-08 / V-01..V-08.
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 0htqmm; re-measured that no gating-kind config key exists (only `backlog.GATE_DEFAULT_KINDS`, consumed at `backlog.decide_gate_default` and `check_engine.check_live_bug_gate`) and that the AGENTS.md sentence is hand-maintained with no generator in `engine.py`.

## Goal

Let each repository name the work-kinds whose live items must carry `- Blocks-Release:`, defaulting to `bug` alone so a repository that configures nothing behaves exactly as today, following the `review_findings_gate` precedent in `config.py`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the reader

- [ ] E-01 In `agent_workflows/config.py`, beside `read_review_findings_gate` / `findings_gate_threshold`, add `RELEASE_GATE_WORK_KINDS_KEY = "release_gate_work_kinds"`, `RELEASE_GATE_WORK_KINDS_DEFAULT = frozenset({"bug"})`, and `release_gate_work_kinds(repo_root, *, warn=None) -> frozenset[str]`. Accepted shapes: an object `{"kinds": ["bug", "security"]}` and, for convenience, a bare list or a bare string (one kind). Values are lowercased, stripped, and intersected against the `backlog.KINDS` vocabulary (pass the vocabulary in, or define the legal set in `config` with a comment, so `config` does not import `backlog`). Posture follows the `policy_retry_budget` rule recorded in that section's comment ("FALL BACK TO THE DEFAULT AND EMIT A VISIBLE WARNING NAMING THE KEY AND THE BAD VALUE"): an absent key returns the default silently; a malformed value or an unknown kind name returns the default (or drops just the unknown name) and warns once naming the key, the value, and the file. An explicit empty list `[]` is legal and means "no kind auto-gates" (explicit opt-out, mirroring `review_findings_gate`'s `off`). Do NOT register the key in `CONFIG_SCHEMA`, for the reason documented above `REVIEW_FINDINGS_GATE_KEY`.
  - Depends on: none
  - Expected outcome: `release_gate_work_kinds(tmp)` returns `frozenset({"bug"})` with no project.json, and the configured set when one is written.
  - PRECEDENTS VERIFIED AT REVIEW, and one of them constrains the vocabulary decision. `read_review_findings_gate` / `findings_gate_threshold` read an object, tolerate a bare string, never raise, and are deliberately absent from `CONFIG_SCHEMA` for the documented round-trip reason; `policy_retry_budget`'s section comment carries the fall-back-and-warn ruling verbatim. ON THE VOCABULARY: `config.py` imports NOTHING from the package (its only imports are stdlib), so the no-`backlog`-import caution is right. But note the existing precedent for the choice this item offers: `REVIEW_GATE_THRESHOLDS = ("medium","high","blocker","off")` IS a hand-maintained partial copy of `review_findings.SEVERITIES = ("low","medium","high","blocker")`, cited as its source in the docstring. So a second copy here would follow precedent AND inherit its wart. PREFER THE INJECTION FORM (the caller passes `backlog.KINDS`), because `backlog` already imports `config` locally at `from agent_workflows import config as _config` inside a function, so the cycle is avoided by the CALLER rather than by duplicating a vocabulary whose single documented home is `.aw/records/backlog/README.md` and `backlog.KINDS`. If injection proves awkward, the literal copy is acceptable but MUST carry a comment naming `backlog.KINDS` as the source and the `REVIEW_GATE_THRESHOLDS` precedent.
  - Execution state: pending

- [ ] E-02 Add `tests/test_config_release_gate_kinds.py` covering: absent file, absent key, object form, bare list, bare string, empty list, unknown kind name (warns, dropped), non-list garbage (warns, default), and that the key round-trips through `project_schema.parse_portable_policy` (lands in `unknown_fields` and is written back). THE ROUND-TRIP IS REAL AND THE SERIALIZER IS NAMED `to_dict`, NOT `as_dict`: driven at review, `parse_portable_policy({...,"release_gate_work_kinds":{"kinds":["bug","security"]}})` puts the key in `unknown_fields` and `.to_dict()` returns it verbatim as `{'kinds': ['bug', 'security']}`; a probe calling `as_dict` silently finds no method and can be misread as a failed round-trip (that happened at review before correcting it). Assert against `to_dict`.
  - Depends on: E-01
  - Expected outcome: new test module passes, including the `to_dict` round-trip returning the written value unchanged.
  - Execution state: pending

### Task group 2: route both consumers through the reader

- [ ] E-03 In `agent_workflows/backlog.py` `decide_gate_default`, replace the membership test `if (kind or "") not in GATE_DEFAULT_KINDS:` with a check against `config.release_gate_work_kinds(repo_root)`. The function already receives `repo_root`, and all THREE call sites pass it positionally (`backlog.run_new`, `backlog.run_set`, `status_set.apply_status_change`, verified at review), so no signature changes anywhere. Keep `GATE_DEFAULT_KINDS` as a deprecated alias of `config.RELEASE_GATE_WORK_KINDS_DEFAULT` so any importer keeps working.
  - Depends on: E-01
  - Expected outcome: with `{"release_gate_work_kinds": {"kinds": ["bug","security"]}}` and a planned release, `aw backlog new --work-kind security ...` defaults `- Blocks-Release: next`; with no config it does not.
  - Execution state: pending

- [ ] E-04 Correct the now-false KIND-SPECIFIC TEXT in `agent_workflows/backlog.py`, which is the half of E-03 a reader actually sees. Generalize the notice strings that say "this bug" to name the item's kind (e.g. "on this security item"): there are THREE, not the two the authored plan named - the `done`/`parked` skip notice, the unresolvable-`next` notice, and the success notice, the last of which also carries "every live bug gates the next release" and "pass '--blocks-release -' to file an ungated bug". No test pins any of that wording (`grep` over `tests/` returns nothing), so generalizing is safe. Update `decide_gate_default`'s docstring numbered condition 1 ("ONLY `GATE_DEFAULT_KINDS` (today `bug` alone) is defaulted ... `security` is deliberately excluded"), which becomes false once the key can widen the set, while PRESERVING the recorded reason the DEFAULT stays `bug` alone (the maintainer measured agent security classifications in this repository to be overstated). Rewrite the comment block above `GATE_DEFAULT_KINDS` ("making the set configurable per repository (defaulting to `bug`) is designed and carried by its own backlog item, NOT shipped here") to state it is now configured via the key.
  - Depends on: E-03
  - Expected outcome: `grep -rn "on this bug" agent_workflows/backlog.py` returns nothing, and the module's `- Work-Kind: bug | feature | ...` vocabulary line is untouched.
  - Execution state: pending

- [ ] E-05 In `agent_workflows/check_engine.py` `check_live_bug_gate`, replace `if item.kind not in _backlog.GATE_DEFAULT_KINDS:` with membership in `config.release_gate_work_kinds(repo_root)` computed ONCE before the loop, and generalize the kind-naming text. Keep the rule id `check.live-bug-ungated` (renaming a shipped rule id is out of scope). TWO drift fields hardcode the kind, not one: `detail` ("a LIVE (status ...) Work-Kind: bug item carries no - Blocks-Release:") and `observed` ("Work-Kind: bug, Status: ..., no Blocks-Release"); generalize both and leave `required` and `recovery` alone, since neither names a kind. Update the function's docstring first line and the `RuleSpec` comment at `"check.live-bug-ungated"`, both of which assert `Work-Kind: bug` specifically. The `RuleSpec` TUPLE itself stays `("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07")`: `DET_DETERMINISTIC` records that the finding's truth is reached with "No inference", and reading a committed config key remains a literal token test, so it must NOT be downgraded to `DET_HEURISTIC`.
  - Depends on: E-01
  - Expected outcome: a `security` item's drift names `security` in both fields; the `RuleSpec` line is unchanged.
  - Execution state: pending

- [ ] E-06 Add the three membership cases to `tests/test_check_engine_release_gate.py`, reusing the module's existing `_create_minimal_repo` helper (which already writes a `planned` release record): (a) a live ungated `security` item is CLEAN with no config; (b) it is FLAGGED when the key lists `security`; (c) a live ungated `bug` is CLEAN when the key is `[]`. Write these BEFORE applying E-05's edit and run them, so case (b) is observed FAILING against the hardcoded set; that is the only evidence the membership change took effect.
  - Depends on: E-05
  - Expected outcome: `13 -> 16 passed` against the review baseline (`python3 -m pytest -o addopts="" -q tests/test_check_engine_release_gate.py` -> `13 passed in 0.98s`), with the existing `test_rule_live_bug_ungated_reachable` and `test_live_bug_with_gate_is_clean` unchanged.
  - Execution state: pending

### Task group 3: docs and suite

- [ ] E-07 Edit `AGENTS.md` section "### Every live bug gates the next release": replace "`bug` is the only gating work-kind today; making that set configurable per repository, defaulting to `bug` alone, is designed but NOT yet built (backlog `0htqmm`), so do not look for a config key to widen it." with a sentence naming the key `release_gate_work_kinds` in `.aw/config/project.json`, its default (`bug` alone), the empty-list opt-out, and the fall-back-and-warn posture. Also generalize "whose `- Work-Kind:` is `bug`" in the opening sentence to "whose `- Work-Kind:` is in the repository's gating set (default `bug`)". Edit `AGENTS.md` DIRECTLY: this section is outside the managed `<!-- aw:block -->` region and has no generator (see Findings F-3).
  - Depends on: E-01
  - Expected outcome: AGENTS.md no longer contains "designed but NOT"; `engine.py` untouched.
  - F-3's BOUNDARY RE-PROVED AT REVIEW, since acting on the opposite belief is a measured hazard: `<!-- aw:block -->` opens at `AGENTS.md:3` and `<!-- /aw:block -->` closes at `:123`, the target sentence sits at `:165`, and `grep -c "configurable per repository" agent_workflows/engine.py` is `0`. So a direct edit is correct and a generator edit would export this repository's policy to every adopter, which is exactly the error the sibling `zqs0px` review retracted with four proofs. STOP CONDITION: if the sentence is found ABOVE line 123 (inside the managed block), do not edit it in place; report instead, because that would mean the section moved into managed territory and the edit belongs in the generator after all. One correction to that review's cited safeguard: the parity assertion it named in `tests/test_shared_checkout_contract.py` no longer exists (that file was deleted in the suite trim), so the marker check above is the live guard rather than a test.
  - Execution state: pending

- [ ] E-08 Run the bare suite `python3 -m pytest`.
  - Depends on: E-02, E-04, E-06, E-07
  - Expected outcome: summary line with 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Repository policy keys live in `.aw/config/project.json`, read by dedicated `config.py` readers that never raise and are deliberately NOT in `CONFIG_SCHEMA` (comment above `REVIEW_FINDINGS_GATE_KEY`; `read_run_policy`).
- Malformed repository policy falls back and warns (maintainer ruling 2026-09-10, `y4adch` OQ-01, recorded in the `policy_retry_budget` section comment).
- `decide_gate_default` is "THE SINGLE AUTHORITY" for defaulting and has three call sites (`backlog.run_new`, `backlog.run_set`, `status_set.apply_status_change`), so changing it once covers all three. Verified at review that all three pass `repo_root` positionally, so no signature changes anywhere.
- `config.py` imports ONLY stdlib (`json`, `os`, `tempfile`, `time`, `dataclasses`, `pathlib`, `typing`), which is what makes the no-`backlog`-import rule real rather than stylistic. `backlog` and `status_set` already import `config` locally inside functions (`from agent_workflows import config as _config`), so the dependency direction is established and one-way.
- `project_schema.ProjectPolicySchema` serializes with `to_dict()`, NOT `as_dict()`, and its `to_dict` re-emits `unknown_fields` verbatim for any key not in the `known_keys` set. That is the mechanism the "not in CONFIG_SCHEMA" decision relies on; a probe calling the wrong method name reads as a broken round-trip.
- The `.aw/records/backlog/README.md` line `- Work-Kind: bug | feature | chore | security | followup` plus `backlog.KINDS` are the documented single home of the work-kind vocabulary. `config.REVIEW_GATE_THRESHOLDS` is the in-repo precedent for a config-local partial COPY of another module's vocabulary (`review_findings.SEVERITIES`), so a copy here would be precedented but would add a second divergence point.
- `aw check release-gates` is ADVISORY in CI (`tests.yml` pipes it to a `::warning::`), so a repository that widens its gating set cannot break the build with new findings.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-1 | Still unbuilt: no config key names gating kinds. | `grep -rn -i 'gating_work_kinds\|release_gate_work\|gate_work_kinds' agent_workflows/*.py` returns nothing; the only set is `backlog.GATE_DEFAULT_KINDS = frozenset(("bug",))`. |
| F-2 | Exactly two consumers read the set. | `grep -rn GATE_DEFAULT_KINDS agent_workflows/`: `backlog.decide_gate_default` ("if (kind or \"\") not in GATE_DEFAULT_KINDS") and `check_engine.check_live_bug_gate` ("if item.kind not in _backlog.GATE_DEFAULT_KINDS"). No test imports it. |
| F-3 | The AGENTS.md sentence is hand-maintained; no generator emits it. | `grep -c 'configurable per repository' agent_workflows/engine.py` = 0. The sentence is at AGENTS.md:165, after `<!-- /aw:block -->` at :123. Plan `zqs0px`'s review record retracted the same "emitted from engine.py" claim with four proofs. So `engine.py` is deliberately NOT in Scope-Paths, contrary to the triage brief's expectation. |
| F-4 | Only other "unbuilt" statement in code is the comment above `GATE_DEFAULT_KINDS` in `backlog.py`. | `grep -rn 'configurable per repository' agent_workflows/` hits only `backlog.py`. |
| F-5 | F-2's census is COMPLETE, re-verified independently: no third consumer reads the gate set, directly or indirectly. `attention.py` computes the outstanding release-blocker set from `Blocks-Release` values, never from `Work-Kind`, so it needs no change. | `grep -rn "GATE_DEFAULT_KINDS" agent_workflows/ tests/` -> the definition, one docstring reference, and the two consumers; `grep -n bug agent_workflows/attention.py` finds only an unrelated prose use |
| F-6 | MORE HARDCODED KIND STRINGS THAN THE ITEMS ADMIT, in text a human or agent actually reads. `backlog.py` has THREE "this bug" notices (not two), one of which also says "every live bug gates the next release" and "an ungated bug"; `check_engine.py` hardcodes the kind in TWO drift fields (`detail` and `observed`), plus its docstring first line and its `RuleSpec` comment. None is pinned by a test, so all are safe to generalize. | `grep -rn "on this bug\|Work-Kind: bug" agent_workflows/backlog.py agent_workflows/check_engine.py`; `grep -rn "on this bug\|every live bug" tests/` returns nothing |
| F-7 | WIDENING THE SET FLAGS NOTHING IN THIS TREE TODAY, so the Deferred "no existing item becomes flagged" claim holds - but its stated reason is stale. The reason is not only that this repo keeps the default: driven with the set forced to `{bug, security}`, `check_live_bug_gate` returns ZERO drifts, because the one live `security` item already carries a gate. `0htqmm` names `754txs` as the live ungated `security` item; it is now `- Status: done`. | Driven at review: `check_live_bug_gate(".")` -> 0 drifts with `{bug}` and 0 with `{bug, security}`; the only live `security` item is `c4yixg` (`graduated`, `- Blocks-Release: next`); `754txs` is `done` |
| F-8 | The `RuleSpec` determinism tag needs NO change, which is worth stating because "reads a config file" looks like it should become heuristic. `DET_DETERMINISTIC` is defined as how the finding's truth was reached with "No inference", and a literal key read is still no inference. | `DET_DETERMINISTIC = "deterministic"` under "Determinism tags ... how a finding's truth was reached"; the rule's own comment "Deterministic: a literal `- Work-Kind:` / `- Status:` / `- Blocks-Release:` token test ... No inference" |
| F-9 | CI cannot break from a widened gate: `aw check release-gates` runs ADVISORY (report-only) in `tests.yml`, so new findings warn rather than fail. This bounds the blast radius of a repository that widens its set. | `.github/workflows/tests.yml`: "release-gates is currently ADVISORY (report-only), NOT fail-closed" and `... --agent \|\| echo "::warning::..."` |
| F-10 | The AGENTS.md rule says a "backlog item, spec, or plan" must carry the gate, but `check_live_bug_gate` iterates BACKLOG ITEMS ONLY (`backlog._iter_items`), so specs and plans are unchecked today. The plan's Scope check records this honestly; this finding pins the evidence so the gap is not mistaken for something this plan introduces. | `for f in _backlog._iter_items(repo_root):` and `_iter_items`'s docstring "Every backlog item file under either layout's status dirs"; AGENTS.md "a backlog item, spec, or plan whose `- Work-Kind:` is `bug`" |

## Proposed changes (ordered, validatable)

1. Reader + default in `config.py` (E-01) with its unit tests (E-02), including the `to_dict` round-trip.
2. `backlog.decide_gate_default` consults the reader (E-03) and its now-false kind-specific text is corrected (E-04).
3. `check_engine.check_live_bug_gate` consults the reader and generalizes its drift text (E-05), with the three membership cases proven failing first (E-06).
4. Contributor rule text updated directly, below the managed block (E-07); full suite plus a before/after `aw check release-gates` count (E-08).

## Deferred / out of scope (with reason)

- A general "all auto-gates" config object: explicitly offered and DECLINED by the maintainer in `0htqmm` ("would design a surface before a second real case exists").
  - Carrier-Declined: maintainer declined the broader surface on 2026-09-12, recorded in backlog 0htqmm "Deliberately NOT in scope".
- Renaming rule id `check.live-bug-ungated` to a kind-neutral name: a shipped rule id; renaming breaks suppressions and docs for no behavior gain.
  - Carrier-Declined: cosmetic; the detail text names the real kind, which is sufficient.
- Retroactively gating existing live `security` items in this repo: none become flagged.
  - Carrier-Declined: the default is unchanged here by design (0htqmm "Why the default is `bug` only"), and the claim was strengthened at review from "this repo keeps the default" (which is true but does not by itself prove nothing would be flagged if someone widened it) to a MEASUREMENT: driving `check_live_bug_gate` with the set forced to `{bug, security}` returns ZERO drifts on this tree, because the only live `security` item (`c4yixg`, `graduated`) already carries `- Blocks-Release: next`. Note `0htqmm` cites `754txs` as the live ungated `security` item; it is now `done`, so that example has expired.
- Widening `check_live_bug_gate` to iterate specs and plans as well as backlog items (F-10).
  - Carrier-Declined: a real gap between the AGENTS.md rule's wording ("a backlog item, spec, or plan") and the check's reach (backlog items only), but it PREDATES this plan and is orthogonal to making the kind set configurable; fixing it here would widen a shipped `error`-severity rule's blast radius in the same change that alters its membership test, so a regression could not be attributed to either. Worth a backlog item; deliberately not filed by this review.

## Scope check

- Over-scope: none.
- Under-scope: none remaining after review, with one pre-existing gap recorded rather than closed. The authored Scope check named the specs-and-plans gap and that assessment is correct and now carries evidence (F-10). Three omissions WERE found and closed in place: E-03 and E-04 each named fewer hardcoded kind strings than exist (F-6), E-03 did not update `decide_gate_default`'s docstring condition 1 which asserts `security` is excluded, and E-04 did not mention the `RuleSpec` comment or address whether the determinism tag must change (F-8, it must not).

## Required tests / validation

New `tests/test_config_release_gate_kinds.py` including the `to_dict` round-trip; three new cases in `tests/test_check_engine_release_gate.py`, with the `security`-flagged case proven FAILING before the `check_engine.py` edit; bare suite. Baseline measured at review so a regression is attributable: `python3 -m pytest -o addopts="" -q tests/test_check_engine_release_gate.py` -> `13 passed in 0.98s`.

## Spec / documentation sync

AGENTS.md "Every live bug gates the next release" (E-05), edited DIRECTLY because the section sits below the managed-block close at `:123` and no generator emits it (F-3, re-proved at review). No `.spec.md` governs `Blocks-Release` defaulting, so no spec amendment and no `.spec.md` appears in `- Scope-Paths:`, meaning the runners will announce no declared spec edit for this plan. `DECISIONS.md` optional; not required. NOTE the rule text's wording is broader than the checker's reach (F-10): E-05 must not tighten the sentence's "backlog item, spec, or plan" phrasing to match the checker, because the RULE legitimately governs all three carriers even though only one is mechanically checked; the honest edit changes only the gating-set clause.

## Open questions

### OQ-01: Should the key also accept per-kind statuses or a release other than `next`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. `decide_gate_default` always writes `next` and the skip-status set is policy, not preference; 0htqmm asks only for the kind set. Default: kinds only.

### OQ-02: Unknown kind name in the list: drop just it, or reject the whole value?

- Blocking: no
- Status: resolved
- Owner: this plan's executor
- Resolution or deferral rationale: RESOLVED AT REVIEW AS "DROP THE UNKNOWN NAME AND WARN", which was the question's own default, because the repository's recorded posture settles it and a maintainer turn is not needed. The governing ruling is in `config.py`'s own run-policy section, quoted verbatim there: "FALL BACK TO THE DEFAULT AND EMIT A VISIBLE WARNING NAMING THE KEY AND THE BAD VALUE" (maintainer decision 2026-09-10, `y4adch` OQ-01), whose stated rationale is that a SHARED, TRACKED file must not break every run over one typo. Both candidate behaviors warn, so the only question is how much of the operator's intent survives, and dropping the bad name preserves the valid gates while whole-value fallback silently discards a `security` gate the repository asked for. `findings_gate_threshold` is a weak counter-example (it falls back wholesale on a bad value) but it reads a SINGLE scalar where there is no partial answer to preserve, so it does not apply to a list. THE WARNING MUST NAME THE DROPPED NAME SPECIFICALLY, not just the key, since a silently narrowed gate set is the failure this choice risks; E-02 tests exactly that case.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -c "from agent_workflows import config; import tempfile; print(sorted(config.release_gate_work_kinds(tempfile.mkdtemp())))"` printing `['bug']`, and `grep -n release_gate_work_kinds agent_workflows/config.py` showing the key, default, and reader. Assert the not-registered property against the RIGHT registry: paste `python3 -c "from agent_workflows import config; print([k for k in config.CONFIG_SCHEMA if 'release_gate' in k])"` returning `[]`. The authored `grep -c release_gate_work_kinds agent_workflows/project_schema.py = 0` is a check on a module this plan never edits, so it would pass no matter what E-01 did; keep it only as a secondary no-edit check, not as the schema assertion. Also state which vocabulary route was taken (injection or literal copy) and, if a copy, paste the comment naming `backlog.KINDS` as its source.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_config_release_gate_kinds.py` summary line showing all passed, and name the cases so each shape is visible. The round-trip case must assert through `to_dict()` (not `as_dict`, which does not exist) and show the written value returned verbatim. The unknown-kind case must show the warning text NAMING THE DROPPED KIND, which is what OQ-02's resolution turns on.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: in a scratch repo with a planned release record and `{"release_gate_work_kinds": {"kinds": ["bug","security"]}}`, paste the output of `python3 -m agent_workflows backlog new --work-kind security ...` showing the defaulted notice and the file line `- Blocks-Release: next`; then with the key removed, paste the same command producing no gate. Both halves are required: the positive case alone cannot distinguish "the reader is consulted" from "everything is now gated".
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `security` item's notice from V-03's run showing it names the ITEM'S KIND rather than "bug". Paste `grep -rn "on this bug" agent_workflows/backlog.py` returning nothing, and `grep -n 'designed and carried by its own backlog item' agent_workflows/backlog.py` returning nothing. Show `decide_gate_default`'s docstring condition 1 no longer asserting `bug` alone is defaulted WHILE still recording why the default is `bug` alone (the measured-overstatement reason), since deleting that reason would lose the justification for the default itself. Confirm the module docstring's `- Work-Kind: bug | feature | ...` vocabulary line is untouched.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the emitted drift for a live ungated `security` item with the key listing `security`, showing BOTH generalized fields (`detail` and `observed`) naming `security` rather than `bug`. Paste the `RuleSpec` line for `"check.live-bug-ungated"` showing it still reads `("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07")`, unchanged (F-8), and the docstring first line no longer asserting `Work-Kind: bug` specifically.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_check_engine_release_gate.py` run BEFORE E-05's edit, showing case (b) FAILING, and quote its assertion text; then the same command after, showing `16 passed` against the review baseline of `13 passed in 0.98s`. A bare "1 failed" is NOT sufficient: only the quoted assertion distinguishes the hardcoded-set failure from a broken test. The existing `test_rule_live_bug_ungated_reachable` and `test_live_bug_with_gate_is_clean` must appear passing in both runs.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: `grep -c 'designed but NOT' AGENTS.md` = 0; `grep -n release_gate_work_kinds AGENTS.md` shows the new sentence; `git diff --name-only -- agent_workflows/engine.py` is empty. ALSO paste `grep -n 'aw:block' AGENTS.md` with the edited line's number, showing the edit landed BELOW the `<!-- /aw:block -->` close (at `:123` before the edit), which is the property that makes a direct edit correct rather than a change the installer will revert. Confirm the sentence still says the rule governs a "backlog item, spec, or plan", i.e. the wording was NOT narrowed to match the checker's backlog-only reach (F-10).
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the bare `python3 -m pytest` summary line showing `N passed` and 0 failed, plus the pre-change baseline count as `<before> -> <after>` so a pre-existing failure is not read as caused by this change. Paste `aw check release-gates --agent` before and after as well: this plan changes an `error`-severity rule's membership test, and with the repository keeping the default the finding count must be IDENTICAL (0 before, 0 after, measured at review), which is the evidence that no existing item's status changed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval.

WHAT A HUMAN IS APPROVING. One new `config.py` reader defaulting to `bug` alone, routed into the two consumers of the hardcoded set, plus generalized notice text, one AGENTS.md sentence, and two test modules. BEHAVIOR IN THIS REPOSITORY IS UNCHANGED, and that was measured rather than asserted: the default is `bug` alone, this repository configures nothing, and `check_live_bug_gate` returns zero drifts both today and with the set forced to `{bug, security}`, because the one live `security` item already carries a gate. What the change adds is the ABILITY for another repository to widen the set, which is exactly what maintainer ruling 2026-09-12 asked for after declining a global answer in either direction.

THE DEFAULT IS THE DECISION MOST WORTH RE-CONFIRMING, because it looks conservative in the wrong direction to a fail-closed instinct: `security` is deliberately EXCLUDED. The recorded reason is that the maintainer measured agent security classifications in THIS repository to be overstated ("an agent defaults to assuming an adversarial actor"), so a default the reference repository must immediately override is a bad default. E-03 must preserve that reasoning in the code comment even while removing the "not shipped here" sentence.

Scope fence (a DECLARATION for reconciliation, not a stop directive): in `agent_workflows/config.py`, only the new key, default, and reader beside `read_review_findings_gate`. In `agent_workflows/backlog.py`, only `decide_gate_default`'s membership test, its three notice strings, its docstring condition 1, and the comment above `GATE_DEFAULT_KINDS` (which stays as a deprecated alias). In `agent_workflows/check_engine.py`, only `check_live_bug_gate`'s membership test, its two kind-naming drift fields, its docstring first line, and the `RuleSpec` comment. In `AGENTS.md`, only the gating-set clause and the opening sentence's kind reference, both BELOW the managed-block close. Two test modules. Expected to need NO edit: `agent_workflows/engine.py` (no generator emits the sentence, F-3), `agent_workflows/project_schema.py` (the round-trip needs no schema change), `config.CONFIG_SCHEMA` (deliberately unregistered), `agent_workflows/attention.py` (computes blockers from `Blocks-Release`, never from `Work-Kind`, F-5), `status_set.py` and the three `decide_gate_default` call sites (all already pass `repo_root`), and the rule id `check.live-bug-ungated`. An edit outside that surface is MADE and then JUSTIFIED at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path, which `aw ipd finalize` refuses to complete without.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; `addopts` already supplies `-q -n auto --dist=worksteal` and the marker deselection, so do NOT add `-n0`, a second `-q`, or `-p no:randomly`. Three claims here are specifically easy to fake and must not be. V-04's BEFORE failure, because this plan's only real behavior change is a membership test and a test written after the edit cannot show it took effect; the baseline is `13 passed` and the target is `16 passed`. V-06's before/after `aw check release-gates`, because an `error`-severity rule is being altered and identical counts are the evidence no existing item's status moved. And V-01's schema assertion, because the authored `grep` targets `project_schema.py`, a module this plan never edits, and would pass regardless.

GENUINE STOP CONDITIONS (unsafe or unresolvable, not scope questions): if the AGENTS.md target sentence is found ABOVE the `<!-- /aw:block -->` line, stop and report rather than editing it, because that would mean the section moved into managed territory and a direct edit would be reverted by the installer while a generator edit would export this repository's policy to every adopter (the error a sibling review retracted with four proofs). If routing `check_live_bug_gate` through the reader changes the finding count on THIS tree, stop and report: with the default unchanged the count must be identical, so any movement means the reader's default does not match `GATE_DEFAULT_KINDS`.

Commit ONLY the Scope-Paths via `aw commit kxawm4 -- <Scope-Paths>`, never `git add -A`, never push. After every `V-*` item carries pasted evidence and `aw ipd lint --phase pre-transition` conforms, the terminal transition to `executed/` is performed with `aw ipd finalize`, never a raw `git mv`; the RUNNER owns it when it executes this plan in a lane, and the executor otherwise performs it. On execution, close backlog `0htqmm` with `--evidence` citing the executed plan; it carries no `- Blocks-Release:`, so no gate is handed off.
