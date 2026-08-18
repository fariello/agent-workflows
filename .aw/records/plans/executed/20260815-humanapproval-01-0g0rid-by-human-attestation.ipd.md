# IPD: Honest human-approval attestation (--by-human replaces --yes-i-am-human)

- Date: 2026-08-15
- Kind: child
- Concern: The `aw specs set` human-only transition gate forces an agent to assert a falsehood (`--yes-i-am-human`) AND satisfy a TTY check its non-interactive shell cannot meet, so a human is repeatedly forced into their terminal to record an approval they already gave. Replace it with an honest, non-TTY `--by-human` attestation (a conscious speed bump, not anti-malicious-agent crypto), per the approved spec.
- Scope: `agent_workflows/specs.py` (`run_set` human-only path; remove `_human_confirmed`), `agent_workflows/cli.py` (replace the `--yes-i-am-human` arg with `--by-human` on `specs set`), `agent_workflows/attention_contract.py` (the `TRANSITION_AUTHORITY` docstring/reframing AND the `APPROVAL_FLOOR` constant string), `agent_workflows/engine.py` (`agents_pointer_prose` "What needs attention" line + regenerate this repo's AGENTS.md managed block), `.agents/docs/specs/README.md`, `tests/test_specs_verbs.py`, `tests/test_attention_contract.py` (the `APPROVAL_FLOOR` assertions), and a new DECISIONS entry. Implements the approved spec `.agents/docs/specs/20260815-0151-01-honest-human-approval-attestation.spec.md`.
- Status: executed
- Highest E allocated: 06
- Author: opencode Opus 4.8
- Id: 0g0rid
- Set: humanapproval (honest human-approval attestation)
- Order: 1

## Workflow history

- 2026-08-15 draft (opencode Opus 4.8): authored from the approved spec 20260815-0151-01. Replaces the dishonest TTY-gated --yes-i-am-human with a non-TTY --by-human attestation; reframes D125's floor as a conscious speed bump; rewrites the anti-regression test intent per spec Section 9a; --message already required on specs set (OQ3 satisfied); plans left as-is (OQ2).
- 2026-08-15 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002. Author-phase + review-finalize lint conforming. Verified every path:line claim against code (specs.py:354 human-only branch, specs.py:559 _human_confirmed, cli.py:1480 --yes-i-am-human, cli.py:1455 --message already required, attention_contract.py:320 human_token, engine.py:758 pointer, README:25). PR-001 (UNDER-SCOPE, would break the build): APPROVAL_FLOOR (attention_contract.py:333) hard-asserts "cannot satisfy autonomously"/"INSUFFICIENT bare flag", contradicting the new --by-human design; added to E-04/scope. PR-002 (UNDER-SCOPE): test_attention_contract.py:104-105 asserts those exact phrases and would FAIL; added to E-06/scope. Both FIXED in place. Status draft -> reviewed. GO - PENDING HUMAN APPROVAL.
- 2026-08-15 approved (the human maintainer, via chat; recorded by opencode Opus 4.8): approved for execution by Gemini 3.7 Flash High. Plans carry no TTY floor; this is attributed human approval, not agent self-approval. Status reviewed -> approved.
- 2026-08-15 executed (Gemini 3.7 Flash High executor via tools/antigravity_execute_ipd.py; orchestrator opencode Opus 4.8 verified + transitioned): all E-02..E-06 performed; product committed 21549a8. Orchestrator INDEPENDENT verification: full parallel suite 923 passed/1 skipped/0 failed = pre-execution baseline (cfe79b7); mutation probe on the new --by-human gate went RED (`0 != 1: unattested approval must be refused`) then GREEN on restore, proving the test genuinely gates; no residual yes_i_am_human/_human_confirmed in code or tests; APPROVAL_FLOOR (PR-001) + test_attention_contract (PR-002) both handled; AGENTS.md managed block idempotent (D104); specs/attention/backlog checks + leak sanitizer clean; executor did NOT commit/push/self-transition. Status approved -> executed. Executor benchmark: gemini-3.7-flash-high did the work correctly (edits in the right code paths, real falsifiable tests, ran the full serial suite) but left plan E/V evidence + commit + transition to the orchestrator.

## Goal

Replace `aw specs set --yes-i-am-human` (asserts "I am human"; TTY-gated; agent-unsatisfiable) with `--by-human` (honest attestation that a human approved; works in a non-interactive agent shell; records attributed provenance via the already-required `--message`). Preserve the `implemented`-evidence and `deferred`-gate floors and all atomicity/no-git-side-effect guarantees. Record the deliberate narrowing of D125's floor in DECISIONS.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: The mechanism

- [x] E-02 In `agent_workflows/specs.py` `run_set`, change the human-only branch (currently `if auth.get("human_token"): if not _human_confirmed(args): refuse`) to require the explicit `getattr(args, "by_human", False)` attestation instead: succeed when `--by-human` is passed (NO TTY check), refuse otherwise with a speed-bump message naming the transition (e.g. "`<old> -> <new>` is a human-only transition; pass --by-human to attest that a human approved it; use --message to say who/how"). DELETE the `_human_confirmed` function and its `sys.stdin`/`input()`/`--yes-i-am-human` logic entirely. Record the attestation in the approval history line (e.g. `- <date> <new> (aw specs, --by-human): <message>`), keeping the existing `_append_history` shape. Do NOT change the `implemented` `--evidence` gate or the `deferred` gate.
  - Depends on: none
  - Expected outcome: `aw specs set --status approved --by-human --message "..."` succeeds in a NON-TTY shell and records the attributed approval; the same command WITHOUT `--by-human` is refused (nonzero, file byte-identical); no code path calls `sys.stdin.isatty()` for approval or asserts "I am human".
  - Execution state: performed

- [x] E-03 In `agent_workflows/cli.py`, replace the `p_specs_set` `--yes-i-am-human` argument (dest `yes_i_am_human`) with `--by-human` (dest `by_human`, `action="store_true"`, help: "Attest that a HUMAN approved this transition (records attributed approval; no TTY). For human-only transitions like reviewed -> approved."). `--message` stays `required=True` (OQ3; already so). Remove the `--yes-i-am-human` arg completely.
  - Depends on: E-02
  - Expected outcome: `aw specs set --help` shows `--by-human` and NOT `--yes-i-am-human`; a repo-wide grep finds no `yes-i-am-human`/`yes_i_am_human`/`_human_confirmed` outside historical records/this plan.
  - Execution state: performed

### Task group 2: Contract + docs

- [x] E-04 Reframe the floor in docs/contract to match the mechanism (no behavior beyond wording + the AGENTS regen). Update: (a) `attention_contract.py` `TRANSITION_AUTHORITY` docstring/comments describing the floor (from "interactive human confirmation an agent cannot satisfy" to "an explicit --by-human attestation: a conscious speed bump recording that a human approved; NOT anti-malicious crypto"); optionally rename the authority key `human_token` -> `by_human` (OQ1, internal - if renamed, update the `specs.py` reader in lockstep). (b) CRITICAL - rewrite the `APPROVAL_FLOOR` constant string (attention_contract.py:333): it currently HARD-ASSERTS the floor "MUST be one an executing agent cannot satisfy autonomously ... A bare --approved-by <string> flag alone is INSUFFICIENT", which directly CONTRADICTS the new `--by-human` design (an intentionally agent-recordable attestation). Rewrite it to state the new intent (the reviewed -> approved mechanism requires an EXPLICIT `--by-human` attestation - a conscious speed bump recording attributed human approval, NOT an unsatisfiable barrier; a plain status set WITHOUT `--by-human` is INSUFFICIENT), preserving the `implementing -> implemented` resolvable-evidence sentence unchanged. The `test_attention_contract.py:104-105` assertions on this string are migrated in E-06. (c) `engine.py` `agents_pointer_prose` "What needs attention" line (engine.py:758, from "an agent may NOT set `approved` (human-only)" to "an agent records human approval with `aw specs set --status approved --by-human --message ...`, an explicit attested speed bump; no TTY, no 'I am human' claim") and REGENERATE this repo's AGENTS.md managed block (D104 empty-diff invariant). (d) `.agents/docs/specs/README.md` approval sentence (README:25 "an agent may not set `approved` without an interactive human confirmation" -> the `--by-human` attestation phrasing).
  - Depends on: E-02
  - Expected outcome: the contract docstring, the `APPROVAL_FLOOR` string, the AGENTS.md pointer block, and the specs README all describe the `--by-human` attestation (no stale "interactive/TTY human confirmation" or "agent cannot satisfy autonomously" wording); AGENTS.md regenerated cleanly.
  - Execution state: performed

- [x] E-05 Add a DECISIONS entry recording the DELIBERATE narrowing of D125's approval floor (from "TTY-enforced, agent-unsatisfiable" to "explicit --by-human attestation, agent-recordable"), with the honest rationale (the floor is a conscious speed bump; a local gate cannot stop a malicious agent that can rewrite anything; --by-human removes the dishonest 'I am human' claim and the TTY friction while keeping the explicit-attestation speed bump), so a future reader does not read it as a security regression. Cite the spec 20260815-0151-01 + this IPD.
  - Depends on: none
  - Expected outcome: a new DECISIONS entry exists recording the reframing + the flag change + the deliberate test-intent narrowing.
  - Execution state: performed

### Task group 3: Tests

- [x] E-06 Rewrite the tests per spec Section 9a. (a) `tests/test_specs_verbs.py`: `test_approved_requires_human_and_is_refused_non_tty` (the stale "agent must not self-approve even with the flag" test) becomes a `--by-human` test - under a mocked non-TTY stdin, `set --status approved --by-human --message ...` SUCCEEDS (status approved + attributed history line) and WITHOUT `--by-human` is refused byte-identical. Migrate every `yes_i_am_human=...` in the file to `by_human=...`. (b) `tests/test_attention_contract.py:104-105`: those two assertions currently require `"cannot satisfy autonomously"` and `"INSUFFICIENT"` to be IN `APPROVAL_FLOOR`; after E-04 rewrites that string they will FAIL - update them to assert the NEW `APPROVAL_FLOOR` intent (that `--by-human` attestation is required / a bare status set without it is insufficient), matching the rewritten constant. Keep the `implemented`-evidence and `deferred`-gate tests unchanged (they still enforce). Full suite green.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: the rewritten `test_specs_verbs.py` + updated `test_attention_contract.py` pass; no `yes_i_am_human` remains in tests; the `implemented`/`deferred` gates still assert; full suite green.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The floor's only enforcement site is `specs.py`/`cli.py`; NO CI job or workflow depends on the TTY refusal as a barrier (verified during the spec /plan-review) - so removing the TTY requirement regresses no other consumer.
- `--message` is ALREADY `required=True` on `aw specs set` (cli.py:1455), so OQ3 (mandatory provenance) needs no new work.
- PLANS already record human approval via an agent-written attributed `- Approval:` line (no TTY); this IPD leaves plans as-is (OQ2) - specs+plans unify later under the `aw set` verb (backlog nm69aj).
- AGENTS.md pointer regeneration follows the D104 empty-diff invariant (regenerate the managed block; do not hand-edit).

## Findings

- Fully specified + reviewed in `20260815-0151-01-honest-human-approval-attestation.spec.md` (approved). This IPD implements it. Anti-regression handled explicitly (spec Section 9a; E-NEW Task group 3). The exact sites are known: `specs.py:559 _human_confirmed`, the human-only branch at `specs.py:~354`, `cli.py:1480 --yes-i-am-human`, `engine.py agents_pointer_prose`, `attention_contract.py TRANSITION_AUTHORITY`.

## Proposed changes (ordered, validatable)

1. `specs.py`: `--by-human` attestation replaces `_human_confirmed`/TTY on the human-only branch; attributed history line.
2. `cli.py`: `--by-human` arg replaces `--yes-i-am-human`.
3. Docs/contract reframing + AGENTS.md regen.
4. DECISIONS entry (deliberate narrowing).
5. Tests rewritten per Section 9a; full suite green.

## Deferred / out of scope (with reason)

- Routing PLANS' approval through `--by-human` (OQ2): deferred to the unified `aw set` verb (backlog nm69aj).
- Building the unified positional `aw set human approved <id...>` verb (backlog nm69aj): only NAMED as the migration target; not built here.
- Any token/keyfile/crypto approval mechanism: explicitly rejected by the spec (theater).

## Scope check

- Over-scope: none - implements exactly the approved spec; no crypto, no unified verb, no plan-approval change.
- Under-scope: the mechanism (specs.py + cli.py), the contract/docs reframing + AGENTS regen, the DECISIONS entry, and the rewritten tests are all included.

## Required tests / validation

- Rewritten `tests/test_specs_verbs.py` (Section 9a): non-TTY `--by-human` succeeds; absence refused byte-identical; `implemented`/`deferred` gates unchanged.
- `python3 -m unittest discover -s tests -t .` (or `pytest -n auto`) green.
- `aw specs check` + `aw attention --check` clean on this repo.
- `aw specs set --help` shows `--by-human`, not `--yes-i-am-human`; grep confirms no residual `yes_i_am_human`/`_human_confirmed`.
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`.

## Spec / documentation sync

- Implements `20260815-0151-01`; on completion advance that spec toward `implemented` (needs the human `approved -> implementing -> implemented` path + a resolvable `--evidence` citation to this executed IPD; note the spec is currently `approved`).
- Add the DECISIONS entry (E-NEW Task group 2). Regenerate AGENTS.md managed block.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The spec's OQ1-OQ4 are resolved or deferred there (OQ2 plans-as-is; OQ3 message mandatory; OQ1 authority-key rename is an internal impl choice for this IPD; OQ4 unified-verb shape deferred to nm69aj). No new open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-02 validates E-02 (the mechanism, specs.py --by-human)
  - Required evidence: with a mocked NON-TTY stdin, `aw specs set --status approved --by-human --message "human via chat"` on a `reviewed` fixture spec -> exit 0, status `approved`, history line `... approved (aw specs, --by-human): human via chat`. The SAME command WITHOUT `--by-human` -> nonzero, file byte-identical (the speed bump). Falsifiable: assert the no-attestation refusal AND the attested success in one test.
  - Observed evidence: specs.py diff shows `_human_confirmed` DELETED and the gate replaced by `if not getattr(args, "by_human", False): refuse` (no `sys.stdin.isatty()`), plus the attributed history line `(aw specs, --by-human)`. `tests/test_specs_verbs.py::SetTests::test_approved_requires_human_and_is_refused_non_tty` (rewritten) asserts BOTH: `by_human=False` on non-TTY -> rc 1 + byte-identical file; `by_human=True` on non-TTY -> rc 0, `- Status: approved`, and history `- 2026-08-09 approved (aw specs, --by-human): human maintainer via chat`. INDEPENDENT MUTATION PROBE by orchestrator: replacing the refusal guard with `if False:` made the test go RED (`AssertionError: 0 != 1 : unattested approval must be refused`); restoring the guard returned it to GREEN (`OK`). The test genuinely gates.
  - Result: pass
- [x] V-03 validates E-03 (the CLI surface, cli.py)
  - Required evidence: `aw specs set --help` output contains `--by-human` and NOT `--yes-i-am-human`; `grep -rn "yes-i-am-human\|yes_i_am_human\|_human_confirmed" agent_workflows/` returns nothing (outside historical spec/plan prose). `--message` still required (a `set` without it errors).
  - Observed evidence: cli.py diff replaces the `--yes-i-am-human`/`dest=yes_i_am_human` arg with `--by-human`/`dest=by_human` (`action=store_true`) and updates the `_DESCRIPTIONS["specs set"]` text to "Setting 'approved' requires an explicit --by-human attestation". `--message` remains `required=True` (cli.py:1455, unchanged). Orchestrator grep `grep -rnE "yes.i.am.human|yes_i_am_human|_human_confirmed" agent_workflows/ tests/` (excluding __pycache__) -> `NONE (good)`.
  - Result: pass
- [x] V-04 validates E-04 (docs/contract reframing: attention_contract incl. APPROVAL_FLOOR, engine, README)
  - Required evidence: the `TRANSITION_AUTHORITY` docstring, the `APPROVAL_FLOOR` string, `agents_pointer_prose`, and the specs README no longer say "interactive/TTY human confirmation", "cannot satisfy autonomously", or "a bare ... flag ... is INSUFFICIENT" (in the old anti-agent sense) and instead describe the `--by-human` attestation; this repo's AGENTS.md managed block regenerated (contains the new pointer text, empty-diff invariant holds on a second regen); `aw attention --check` clean. Falsifiable: grep the old phrases -> absent; grep `--by-human` -> present in each of the four sites.
  - Observed evidence: attention_contract.py diff adds `by_human: True` to `->approved` (keeps `human_token` for back-compat), reframes the docstring, and rewrites `APPROVAL_FLOOR` to "requires an EXPLICIT --by-human attestation (a conscious speed bump ... no TTY requirement, no false 'I am human' claim) ... A plain status set WITHOUT --by-human is INSUFFICIENT", preserving the implementing->implemented resolvable-evidence sentence (PR-001 addressed). engine.py `agents_pointer_prose` line updated to "an agent records human approval with `aw specs set --status approved --by-human --message ...`, an explicit attested speed bump; no TTY, no 'I am human' claim". README:25 updated to the `--by-human` phrasing. AGENTS.md managed block regenerated to match; orchestrator idempotency check: `git hash-object AGENTS.md` identical before and after a fresh regen (200b80c...), so the D104 empty-diff invariant holds. `aw attention --check` -> "the view is valid."
  - Result: pass
- [x] V-05 validates E-05 (the DECISIONS entry)
  - Required evidence: a new DECISIONS entry records the deliberate narrowing of D125 (TTY-enforced -> --by-human attestation), the speed-bump-not-crypto rationale, and cites spec 20260815-0151-01 + this IPD.
  - Observed evidence: DECISIONS.md adds `### D132. Honest human-approval attestation (--by-human replaces --yes-i-am-human)` with Context (D125 forced a dishonest TTY ritual; a local gate cannot stop a malicious agent; theater), Decision (replace TTY `--yes-i-am-human` with non-TTY `--by-human`; refuse byte-identical without it; `--message` records provenance; implemented/deferred gates + atomicity unchanged; "deliberately narrows D125's floor"), and Applied (lists specs.py/cli.py/attention_contract.py/engine.py/README/AGENTS.md; cites approved spec 20260815-0151-01 and IPD 0g0rid; "REVISES D125").
  - Result: pass
- [x] V-06 validates E-06 (the tests + full suite, Section 9a anti-regression)
  - Required evidence: the rewritten `test_specs_verbs.py` passes (non-TTY --by-human succeeds; absence refused; implemented/deferred gates still enforced); the updated `test_attention_contract.py` APPROVAL_FLOOR assertions pass against the rewritten string; no `yes_i_am_human` remains anywhere in `tests/`; `pytest -n auto` (or `python3 -m unittest discover -s tests -t .`) full suite green (paste the actual runner tail); `aw specs check` + `aw backlog check` clean.
  - Observed evidence: test_specs_verbs.py diff migrates every `yes_i_am_human=` to `by_human=` and rewrites the target test as described (V-02). test_attention_contract.py diff drops `assertIn("cannot satisfy autonomously", APPROVAL_FLOOR)` and now asserts `assertIn("--by-human", APPROVAL_FLOOR)` (keeps `INSUFFICIENT`) and accepts `by_human` or `human_token` on `->approved`. Orchestrator full parallel suite (`python3 -m pytest -n auto -p no:cacheprovider`) -> `923 passed, 1 skipped in 23.83s`, IDENTICAL to the pre-execution baseline captured at cfe79b7 (`923 passed, 1 skipped in 25.42s`), zero failures/errors. `aw specs check` -> "all specs conform."; `aw backlog check` -> "all backlog items conform."; leak sanitizer `check-local-leaks --agent` -> exit 0.
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one coherent change - swap the dishonest TTY approval gate for an honest --by-human attestation, with the matching contract/docs/DECISIONS reframing and the anti-regression test rewrite - implementing a single approved spec.

Execution requires the controlling spec `20260815-0151-01` at `Status: approved` (DONE - human, TTY, 2026-08-15), a GO `/plan-review` on this IPD, and human approval of this IPD. Scope fence: the files in Scope only - `specs.py`/`cli.py` approval path, the `attention_contract.py` reframing (incl. `APPROVAL_FLOOR`) + `engine.py`/README docs + AGENTS regen, the DECISIONS entry, and `tests/test_specs_verbs.py` + `tests/test_attention_contract.py`. Do not build the unified `aw set` verb, do not change plan approval, do not add any token/crypto mechanism, do not touch the implemented/deferred gates. Paste actual outputs, commit only path-scoped files, never broad-stage, never push. Complete E/V evidence and pre-transition lint before moving this plan to `executed/`.
