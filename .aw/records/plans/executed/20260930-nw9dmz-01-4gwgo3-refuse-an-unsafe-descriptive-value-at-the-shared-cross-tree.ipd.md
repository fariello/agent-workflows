# IPD: Refuse an unsafe descriptive value at the shared cross-tree setter so the positional set spelling cannot forge a workflow history record on any tree

- Date: 2026-09-30
- Kind: child
- Concern: `status_set.run_set_command` is the ONE setter the positional `aw <tree> set <status> <selector>` spelling (and the untyped `aw set`) dispatches to, and it interpolates `--message`, `--actor`, `--gate-ref`, `--gate-summary` and `--blocks-release` into a record having validated none of them for LINE INTEGRITY, so a newline in any of the five writes attacker-chosen bullets into a real artifact at exit 0 on every tree it serves. Measured in this lane across all five trees: a forged `- 2026-09-30 approved (aw backlog, --by-human): looks good to me` history record lands at zero `backlog.validate_item` drift with `aw backlog check --agent` reporting `"findings":0`; and on the PLANS tree one command forges `- Readiness: go` plus its own attesting `/plan-review` record, flipping `plan_readiness.is_plan_review_approved` from `False` to `True` on a plan nothing reviewed, which under `--full-auto` is what promotes a plan to approved.
- Scope: Apply line-integrity validation to every user-supplied value `status_set.run_set_command` writes into an artifact and does not already validate, refusing BEFORE any file is written or any id resolved, so one guard covers all five trees that share this dispatch. The guarded set is the five flags measured live here: `--message` and `--actor` (which land in the `## Workflow history` line) and `--gate-ref`, `--gate-summary` and `--blocks-release` (which land in FRONT MATTER). Mode is LINE INTEGRITY ONLY for `--message` (newline, carriage return, control characters; NOT length), because roughly two fifths of all committed history messages across the three populated trees already exceed the 300-character `MAX_DESCRIPTIVE_LEN` bound (measured 2589/6889 at authoring and 2847/7427 at review; the RATIO is the stable fact, the counts drift) and a length bound would refuse the setter's own normal output; the four short identifier-shaped or single-line fields get the full bounded predicate. THE COVERAGE CLAIM IS ENUMERATED, NOT ASSERTED: `--graduated-to` and `--release-exempt-ref` already refuse a newline through existing shape validators, and `--by-human`/`--allow-open-questions`/`--dry-run`/`--force`/`--yes` are store_true booleans carrying no value, so the guarded set plus the already-validated set is the complete value-bearing surface of this function. DELIBERATELY NOT COVERED: the `--status` spelling of each tree's own `run_set` (plan `uz05bl` owns it), the dead `aw prompts set` parser registration (F-09), and the `status_set` display-regex divergence (F-08).
- Scope-Paths: agent_workflows/status_set.py, tests/test_status_set_descriptive_safety.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: nw9dmz
- Blocks-Release: next
- Set: nw9dmz
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 4gwgo3

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 4gwgo3 verified (set nw9dmz, attempt 1).
- 2026-10-01 approved (aw set): status set to approved
- 2026-10-01 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): plan-review complete: PR-201..PR-205 all fixed, zero deferred, zero open

- 2026-10-01 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-201..PR-205 all FIXED, zero deferred, zero open. Reviewed at HEAD `60df6ab10`. `aw ipd lint --phase author` conformed before review and `--phase review-finalize` conforms after. THIS IS A SECURITY PLAN SO I DROVE EVERY VECTOR MYSELF on a fresh git repository installed OUTSIDE this checkout, with a real backlog item, a real scaffolded plan and a real release record. EVERY LOAD-BEARING CLAIM REPRODUCES: F-01 (exit 0, sha256 changed, forged `--by-human` record, `aw backlog check --agent` reporting `"findings":0`); F-05 IN FULL, which is the release-blocker severity (`is_plan_review_approved` `False` -> `True` and `read_readiness` `None` -> `'go'` after ONE `ipd set` call); F-07 exactly (`IPD-M107` absent at BOTH `author` and `review-finalize`, `aw check plans` reporting `"conforms"`, the only diagnostic unrelated); F-03 and F-04 including the asymmetry (`get_release_blockers` returns the PLAN for a smuggled bullet, returns nothing for the same injection on a backlog item); F-06 including the FRONT-MATTER half (`- Gate-Ref: x` / `- Readiness: go` inside the metadata block); F-09 verbatim; both already-validated flags genuinely already refusing; and all EIGHT verdicts E-01 promises from the shipped sibling helper, with no import cycle. FIVE FINDINGS, NONE ABOUT THE APPROACH. PR-201 (HIGH) is that the suite baseline this plan makes its acceptance bar is stale in the DANGEROUS direction: the named "pre-existing" failure now PASSES and the tree is fully green, so an executor would wave through a new failure in that exact test as pre-existing; corrected in all three places to zero-failures-by-node-id. PR-203 found that the `--item-dependencies` wrapper FORWARDS a user `--message`, making it a second surface this guard newly PROTECTS rather than merely must-not-break, which also strengthens OQ-01's entry placement and OQ-03's no-exemption rule. PR-205 strengthens E-04 to pin the `--status` half's shipped refusal MESSAGE, since an exit-code assertion would pass even if this plan's guard had displaced the sibling's. PR-202 restates five drifting count citations as the stable ratio plus the ZERO control characters (0 of 6889 at authoring, 0 of 7427 at review). PR-204 adds independent reproductions to F-05 and F-07 and records that the forgery does not depend on the requested status being review-ish. Nothing weakened: entry placement, delegation over a third copy, uniform no-caller-exemption, and above all line-integrity-only mode for `--message` all stand. Bare suite at review HEAD: `3578 passed, 2 skipped, 3 warnings in 128.46s`. No production file was left modified by this review.
- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `nw9dmz`. DROVE all five trees rather than trusting the item's inference, as the item explicitly requires: backlog reproduces exactly as filed, and specs, plans, releases and prompts all reproduce too. Then measured FOUR things the item does not name. (1) THE ITEM UNDERSTATES THE HARM ON THE PLANS TREE: a smuggled `- Blocks-Release:` is NOT merely a history-body bullet there, it becomes a FUNCTIONING release gate that `releases.get_release_blockers` honors, because `attention.py`'s plans reader scans the whole text rather than only front matter. (2) THE SEVERE CASE IS `- Readiness: go` PLUS A FORGED REVIEW RECORD IN ONE COMMAND, flipping `is_plan_review_approved` to True; the item does not mention readiness at all. (3) FOUR MORE FLAGS carry the same hole (`--actor`, `--gate-ref`, `--gate-summary`, `--blocks-release`), and `--gate-ref`/`--gate-summary` inject into FRONT MATTER, not the history body. (4) `aw prompts set` is dispatched by `cli.py` but never registered in its parser, so it is unreachable dead code. Also re-derived the per-tree length measurement the item cites (its specs/backlog/plans figures are all slightly stale) and confirmed ZERO control characters in 6889 committed messages, which is what makes the line-integrity half free of regression risk.
- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the shared cross-tree setter refuse a value that would break out of the line it is written into, so no spelling of `aw set` can manufacture front matter or a workflow history record its author never wrote. The severe case is not cosmetic bullet litter: one `aw ipd set` command currently writes both a `- Readiness: go` field and the `/plan-review` record that attests it, and `plan_readiness.is_plan_review_approved` then returns True for a plan no review ever saw. `AGENTS.md` forbids an agent from hand-writing exactly that field ("NEVER WRITE ANOTHER ROLE'S ATTESTATION FIELD ... a hand-written value asserts that a review cleared the plan"); this plan closes the route that writes it through a legitimate-looking verb instead.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one shared refusal helper, reached rather than re-implemented

- [x] E-01 Add a module-private refusal helper to `agent_workflows/status_set.py` that judges ONE value and returns the refusal MESSAGE (or `None`), so all five call sites refuse with identical wording. Signature shape: `_refuse_unsafe_descriptive(verb: str, flag: str, value: Optional[str], *, bound_length: bool = True) -> Optional[str]`, returning `None` when `value` is `None` or the applicable check passes.
  DO NOT WRITE A THIRD IMPLEMENTATION OF THE CONDITIONS. `backlog._refuse_unsafe_descriptive` already ships this exact helper with this exact signature (executed plan `dtg7dz`), and plan `uz05bl` E-01 adds a second copy in `specs.py` whose wording it requires be kept byte-compatible with the sibling. DELEGATE to the backlog sibling (`from agent_workflows import backlog as _backlog` at the call site, matching how this module ALREADY reaches `backlog.validate_release_exempt_flags` for the release-exemption refusal) rather than copying thirty lines a third time. THE DELEGATION IS CONFIRMED VIABLE AND THE FALLBACK SHOULD NOT FIRE (F-12, added at review): `status_set` ALREADY imports `backlog` at module level and lazily in five separate places, and importing both together raises nothing, so there is no cycle to hit. If the executor nonetheless finds one, port the sibling's body VERBATIM, say so in the V-01 evidence, AND state what the cycle was (an unexplained port is a V-01 failure, because F-12 measured that no cycle exists today and a silent port would hide a real change in the import graph). Do not invent a new construction, and in particular do not use the slice-only form plan `uz05bl` measured as unsound (it accepts a control character past character 300, which is reachable because real messages run to 5667 characters here).
  THIS IS THE THIRD CONSUMER OQ-02 NAMED, AND THE HOIST IS STILL DECLINED: see OQ-02 below for why delegating to the sibling discharges the intent without the edit that OQ-02 was protecting against.
  - Depends on: none
  - Expected outcome: a helper importable as `status_set._refuse_unsafe_descriptive` that, with the default `bound_length=True`, returns `None` for `"ok"` and for `None`, a message mentioning `newline` for `"a\nb"`, `control` for `"a\x07b"`, and both `300` and `340` for a 340-character value; and with `bound_length=False` returns `None` for that same 340-character value and for a 1200-character one, while still returning the `newline` and `control` messages, INCLUDING the `control` message for `"a"*500 + "\x07" + "b"`. Verified against the real sibling in this lane: `backlog._refuse_unsafe_descriptive("v", "--message", "a"*500 + "\x07" + "b", bound_length=False)` returns `'v: --message must not contain control characters'`.
  - Execution state: performed

### Task group 2: apply it at the one dispatch, before anything is resolved or written

- [x] E-02 Apply the helper to `--message` and `--actor` in `run_set_command`, in LINE-INTEGRITY mode (`bound_length=False`) for `--message` and BOUNDED mode for `--actor`, placed in the EXISTING pre-resolution guard block near the top of the function (beside the `--graduated-to`, `--from-spec` and release-exemption refusals that already sit there) and therefore BEFORE `inventory_all_artifacts`, so a refused call resolves no artifact and touches no file. Refuse through `term.status("fail", ...)` and `return 2`, matching every neighbouring refusal in that block.
  THE MODE ASYMMETRY IS MEASURED, NOT STYLISTIC. Re-derived over committed `## Workflow history` records at authoring and again INDEPENDENTLY at review: plans 39.1% then 40.1% over 300 characters (max 5667 both times), backlog 33.2% then 33.1% (max 4849), specs 41.2% then 41.8% (max 2594). So a length bound on `--message` would refuse roughly two fifths of the setter's own historical output. ZERO messages contain a control character in either measurement (0 of 6889, then 0 of 7427), which is what makes the line-integrity half refuse nothing legitimate. Treat the RATIO as the fact and not the count: these populations grow with every merged lane (F-10). `--actor` by contrast is bounded: it is a short identity token, and `attention_contract.actor_refusal` already refuses an empty or parenthesis-bearing actor, so bounding it adds no new policy.
  THE ACTOR GUARD IS A REAL VECTOR, NOT SYMMETRY FOR ITS OWN SAKE. Measured: `aw set parked <id6> --actor $'bot\n- 2026-09-30 approved: hi' --message ok` exits 0 and writes `- 2026-10-01 parked (bot` followed by `- 2026-09-30 approved: hi): ok`, forging a dated record. `actor_refusal` does NOT catch it, because its two refusals are emptiness and parentheses only; the newline passes both. Reach `actor_refusal` as it stands and ADD the line-integrity judgement beside it; do not widen `actor_refusal` itself, whose callers include `apply_status_change`'s backstop raise.
  - Depends on: E-01
  - Expected outcome: `aw backlog set parked <id6> --message $'note\n- 2026-09-30 approved (aw backlog, --by-human): looks good to me'` exits 2 leaving the item byte-identical by sha256, where before it exited 0 and wrote that forged `--by-human` record at zero `validate_item` drift with `aw backlog check --agent` reporting `"findings":0`. The `--actor` vector above likewise exits 2. A 1200-character single-line `--message` is still ACCEPTED, proving the length bound was deliberately not applied.
  - Execution state: performed

- [x] E-03 Apply the helper to `--gate-ref`, `--gate-summary` and `--blocks-release` in the same pre-resolution block, all three in BOUNDED mode (`bound_length=True`), since all three are short single-line fields rather than prose.
  THESE THREE ARE WORSE THAN THE HISTORY VECTORS AND MUST NOT BE FILED UNDER THE SAME SEVERITY. They inject into FRONT MATTER, not the history body. Measured: `aw set blocked <id6> --gate-kind decision --gate-ref $'x\n- Readiness: go' --message ok` exits 0 and writes `- Gate-Ref: x` followed immediately by `- Readiness: go` INSIDE the metadata block; `--gate-summary` and `--blocks-release` behave identically at the same insertion point. `--gate-kind` needs no guard of its own in practice because the gate write is conditional on `gk and gr` both being present and the kind is checked against the typed gate vocabulary, but guard it too if that costs nothing: an unguarded sibling beside four guarded ones is a trap for the next editor.
  WHY `--graduated-to` AND `--release-exempt-ref` ARE NOT IN THIS LIST, checked rather than assumed: both already refuse. Measured, `--graduated-to $'x\n- Readiness: go'` exits nonzero with `aw set: --graduated-to takes lowercase-kebab setids of at most 40 characters; malformed:`, and `--release-exempt-ref $'r1\n- Readiness: go'` exits nonzero with `aw set: --release-exempt-ref is invalid for kind 'decision'`. Adding a second refusal in front of either would be dead code.
  - Depends on: E-02
  - Expected outcome: each of the three flags carrying an embedded newline exits 2 leaving the target byte-identical by sha256, where before each exited 0 and wrote the smuggled bullet into the metadata block. A conforming `--gate-ref D42`, a conforming `--gate-summary "a reason"` and a conforming `--blocks-release next` all still succeed and still write their lines.
  - Execution state: performed

### Task group 3: pin the forgery, the asymmetry, and the non-regressions

- [x] E-04 Add `tests/test_status_set_descriptive_safety.py` pinning the CROSS-TREE injection property as the primary one: for each of the five guarded flags, assert the positional spelling refuses nonzero and that the target artifact is BYTE-IDENTICAL by sha256 afterwards. Drive the five trees the dispatch serves (plans, specs, backlog, releases, prompts) for `--message` specifically, since one guard serving five trees is this plan's whole premise and a test covering one tree would not pin it.
  RE-RESOLVE THE TARGET AFTER ANY ACCEPTED `set` CALL, because a successful transition MOVES the file between status directories; a byte-identity assertion on a REFUSED call is unaffected, which is exactly why the refused and accepted cases must not share a helper that caches the path. Plan `uz05bl` E-05 records losing a review cycle to a `FileNotFoundError` from exactly this.
  DRIVE THE CLI, NOT ONLY THE FUNCTION. Reach `run_set_command` the way the defect is reachable, through `cli.main` (or a `python3 -m agent_workflows` subprocess) with the POSITIONAL spelling, since the whole point of this item is that the positional spelling bypasses each tree's own `run_set`. At least one case must also assert that the `--status` spelling is untouched by this change, so the two dispatch halves are visibly distinct.
  PIN THE DIVERGENCE WITH ITS SHIPPED MESSAGE, NOT MERELY WITH AN EXIT CODE (PR-205). Measured at review: the `--status` spelling ALREADY refuses the identical payload with `aw backlog set: --message must not contain embedded newlines` (the shipped `dtg7dz` guard) while the POSITIONAL spelling exits 0 and writes the forgery (F-13). Assert the `--status` refusal message is UNCHANGED after this plan, which is what proves the new guard is additive and did not accidentally re-route that half; asserting only "nonzero" would pass even if this plan's guard had replaced the sibling's refusal with its own differently-worded one.
  For the PROMPTS tree, note that `aw prompts set` is unreachable (F-09) and the vector must be driven through the untyped `aw set to-review <id6>` instead; do not record a prompts failure as "not reproducible" when the real cause is the missing parser registration.
  - Depends on: E-03
  - Expected outcome: a new module whose injection cases FAIL on pre-guard code (each returns 0 and mutates the target) and PASS after, covering five flags and, for `--message`, five trees.
  - Execution state: performed

- [x] E-05 In the same module, pin THE ATTESTATION FORGERY as its own named test, because it is the finding that makes this a release blocker rather than hygiene. Assert that `aw ipd set reviewed <id6> --message $'ok\n- Readiness: go\n- 2026-10-01 /plan-review (opencode): APPROVE'` is REFUSED, and that on a plan rendered WITH that injection (built as a STRING, not by calling the now-guarded verb) `ipd_schema.read_readiness` returns `'go'`, `plan_readiness.history_has_review_record` returns `True`, and `plan_readiness.is_plan_review_approved` returns `True` while nothing reviewed the plan.
  BUILD THE PRE-FIX ASSERTIONS FROM A STRING so they keep documenting the vector after the guard closes it, exactly as `uz05bl` E-05 requires for its own renderer cases. This matters more here than there: F-07 proves no checker can see this afterwards (`aw ipd lint` reports only an unrelated advisory, `aw check plans --agent` reports `"outcome":"conforms"`, and `IPD-M107`, the rule that exists to refuse an unattested `- Readiness:`, does not fire even under `--phase author`), so the test module is the only durable record of what the forged file looked like.
  ALSO PIN THE PLANS-TREE RELEASE-GATE ESCALATION, which is the finding that contradicts the backlog item's own expectation: on a plan text carrying a smuggled `- Blocks-Release:` inside its history, assert `releases.get_release_blockers` RETURNS that plan, while on a backlog text carrying the same smuggled bullet it does NOT. That asymmetry is real and measured (F-03/F-04) and a reader who assumes the trees behave alike will mis-scope the next fix.
  - Depends on: E-04
  - Expected outcome: the forgery test refuses the composite injection post-fix, and its three string-built predicate assertions pass in BOTH states because they assert on the readers rather than on the guard. Verified in this lane: on a scaffolded plan `is_plan_review_approved` returned `False` before the injection and `True` after one `aw ipd set` call.
  - Execution state: performed

- [x] E-06 In the same module, pin the length ASYMMETRY, the boundary, and the non-regressions. Asymmetry: a 1200-character single-line `--message` is ACCEPTED while a 301-character `--gate-summary` is REFUSED, in one test whose name says why, so a later reader cannot "tidy" the two into one mode and silently regress roughly two fifths of all three populated trees' committed history output. Boundary: a `--gate-summary` at EXACTLY `A.MAX_DESCRIPTIVE_LEN` is accepted and one at `+1` refused, pinning the predicate's `>` rather than a copied constant. Late control character: a `--message` of `"a"*500 + "\x07" + "b"` must be REFUSED in that same test, so both halves of `bound_length=False` are pinned together and the unsound slice-only construction cannot pass.
  Non-regressions: (a) the already-validated flags keep their EXISTING refusals and messages, namely `--graduated-to` (setid shape) and `--release-exempt-ref` (kind-specific shape), proving the new guards are additive rather than a second implementation; (b) `attention_contract.actor_refusal`'s own two refusals (empty, parenthesis) are unchanged and still fire, including the `apply_status_change` backstop `raise` for a direct caller that skipped the pre-flight; (c) THE IN-REPO CALLERS STILL WORK, specifically `work_cmd.run_finish`'s hand-built Namespace (`message="aw finish: evidence-bound transition"`) and `status_set`'s own `--item-dependencies` wrapper, which drives a same-status transition through `run_set_command` carrying a defaulted message, AND (per PR-203) that same wrapper REFUSES when the user supplies a newline-bearing `--message`, since it forwards the user value rather than always using its default; (d) a plain conforming transition on each of the five trees still exits 0 and still writes its history record.
  (c) IS THE REGRESSION RISK WORTH NAMING, because a guard at this dispatch runs for every programmatic caller too, not only for a human at a terminal. Both callers found pass single-line literals today, so the guard is expected to be invisible to them; the test exists so that stays true rather than being assumed.
  THE `--item-dependencies` WRAPPER IS ALSO A SECOND PROTECTED VECTOR, NOT ONLY A NON-REGRESSION (PR-203). Read at review: `status_set`'s deps writer builds its Namespace with `message=getattr(args, "message", None) or default_message`, so it FORWARDS A USER-SUPPLIED `--message` into `run_set_command` and only falls back to the literal when the user supplied none. So `aw ipd set-item-dependencies ... --message $'ok\n- Readiness: go'` reaches the same interpolation through a second CLI surface. This is an ARGUMENT FOR the entry placement OQ-01 chose, since one guard at `run_set_command` covers that surface for free, and it means (c) must assert BOTH directions: the defaulted literal still succeeds, AND a newline-bearing user `--message` routed through that wrapper is REFUSED. Add the second assertion; testing only the happy path would leave the reader believing this surface is merely unaffected when it is in fact newly protected.
  - Depends on: E-05
  - Expected outcome: the asymmetry test passes (1200-character clean `--message` accepted, 301-character `--gate-summary` refused, late control character refused), the boundary test proves 300 accepted and 301 refused, and all four non-regression groups pass.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE PREDICATE AND THE HELPER BOTH ALREADY EXIST, so this plan adds CALL SITES only. `attention_contract.is_safe_descriptive` documents itself as "Section 8.8: a descriptive field is a single, bounded, control-char-free line", and `backlog._refuse_unsafe_descriptive` already wraps it with the `bound_length` asymmetry this plan needs. The defect is that the shared WRITE path consults neither.
- THIS MODULE ALREADY REACHES INTO `backlog` FOR A SHARED REFUSAL, which is the precedent for E-01's delegation rather than a third copy: `run_set_command` calls `backlog.validate_release_exempt_flags("aw set", ...)` from exactly the pre-resolution guard block these new guards belong in, and `validate_transition_allowed` calls it again. So a `from agent_workflows import backlog as _backlog` at this call site is the established shape, not a new coupling.
- THE PRE-RESOLUTION GUARD BLOCK IS THE ESTABLISHED PLACE AND ITS CONVENTION IS `term.status("fail", ...)` PLUS `return 2`. Three refusals already sit there (`--graduated-to` canonicalization, `--from-spec` resolvability, and the release-exemption pair), each with a comment explaining that it fires "BEFORE any artifact is resolved or written". New guards join them rather than being pushed down into `apply_status_change`, which is a pure write.
- THE EXIT CODE HERE IS 2, UNAMBIGUOUSLY, unlike the specs module `uz05bl` had to navigate. Every refusal in this function returns 2, including the missing-selector and no-match cases, so there is no OQ-01-style convention conflict to resolve on this tree.
- A HISTORY MESSAGE IS NOT A BOUNDED FIELD ON ANY TREE. Re-derived here over committed records, and again at review: plans 39.1% then 40.1% over 300 characters, backlog 33.2% then 33.1%, specs 41.2% then 41.8%, max 5667 both times, and releases/prompts have zero history records yet (F-10 carries both measurements and warns the counts drift while the ratio holds). No checker anywhere bounds a history message, so guarding one on LENGTH would be new policy this plan does not make.
- `actor_refusal` IS THE EXISTING PRECEDENT FOR GUARDING A HISTORY-LINE FIELD, and it is deliberately narrow: "Two refusals, in this order: an EMPTY (or whitespace-only) actor, and an actor containing a parenthesis." It also states the ordering rule this plan follows ("Callers must invoke this BEFORE any mutation - that ordering is the defect this helper exists to close").
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do not pass `-n0`, a second `-q`, or `-p no:randomly` (AGENTS.md).

## Findings

All findings were DRIVEN in this lane against fresh `git init` fixture repositories through the real CLI (`python3 -m agent_workflows`), at HEAD `0da8e0977`, not read off the source. The suite baseline at that HEAD was `1 failed, 3498 passed, 2 skipped` with the single failure `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`. THAT FAILURE IS GONE AS OF REVIEW (PR-201): at review HEAD `60df6ab10` the bare suite is `3578 passed, 2 skipped, 3 warnings` and the named test passes on its own, so the figure above is HISTORICAL CONTEXT ONLY and must NOT be used as the acceptance bar. Re-derive a fresh baseline at execution; the bar is zero failures.

| # | Finding | Evidence |
|---|---|---|
| F-01 | THE ITEM'S FILED BACKLOG DEFECT REPRODUCES EXACTLY, and the harm is the provenance forgery the item predicted rather than a smuggled gate. | Driven: `backlog set parked 9aofli --message $'note\n- 2026-09-30 approved (aw backlog, --by-human): looks good to me'` exited **0**; the item's `## Workflow history` then read `- 2026-10-01 parked (aw set): note` followed by the forged `- 2026-09-30 approved (aw backlog, --by-human): looks good to me`. `backlog.validate_item` returned `[]` and `aw backlog check --agent` emitted `"outcome":"clean","checked":1,"findings":0`. |
| F-02 | **ALL FIVE TREES REPRODUCE, SO THE ITEM'S INFERENCE IS CONFIRMED BY MEASUREMENT** as the item required ("THE OTHER FOUR TREES ARE INFERRED ... whoever fixes this MUST measure each tree"). | Driven, each exiting 0 and writing the smuggled record: `specs set to-review ggk2ei --message $'ok\n- 2026-09-30 approved (aw specs, --by-human): LGTM'`; `ipd set to-review 6l0lq3 --message $'ok\n- 2026-09-30 approved (aw ipd, --by-human): LGTM'`; `set shipped pkxwan --message ...` on a release; and `set to-review 26mktg --message ...` on a prompt. |
| F-03 | **THE ITEM UNDERSTATES THE HARM ON THE PLANS TREE: a smuggled `- Blocks-Release:` there is a FUNCTIONING release gate, not an inert bullet.** The item predicts the harm is "provenance forgery ... rather than a smuggled metadata bullet, since the value lands in the history body"; that holds for backlog and is FALSE for plans. | Driven: after `ipd set to-review 6l0lq3 --message $'ok\n- Blocks-Release: pkxwan'`, `releases.get_release_blockers(repo,'pkxwan')` returned `[{'id': '6l0lq3', 'tree': 'plans', 'native_status': 'to-review', 'blocks_release': 'pkxwan'}]`. The gate was never requested. Cause: `attention.py`'s plans reader searches `text[:4096]` and then the WHOLE text for `(?m)^- Blocks-Release:\s*(\S+)\s*$`, so a history-body bullet matches. |
| F-04 | THE BACKLOG TREE DOES **NOT** ESCALATE THE SAME WAY, which is why F-03 is a per-tree finding and not a blanket correction. | Driven: after `backlog set open 9aofli --message $'ok\n- Blocks-Release: next'`, `backlog.parse_item(...).blocks_release` was `None`, `aw attention --format json` reported `"blocks_release": null`, and `get_release_blockers` returned `[]`. The bullet is inert there. |
| F-05 | **THE SEVERE CASE IS AN ATTESTATION FORGERY COMPLETED IN ONE COMMAND: a `- Readiness: go` field PLUS the review record that attests it.** The item does not mention readiness. | Driven in a clean fixture: a scaffolded plan had `plan_readiness.is_plan_review_approved(p) == False`; after the single command `ipd set reviewed 6qs67p --message $'ok\n- Readiness: go\n- 2026-10-01 /plan-review (opencode): APPROVE'` (exit 0), `ipd_schema.read_readiness` returned `'go'`, `history_has_review_record` returned `True`, and `is_plan_review_approved` returned **True**. The attestation gate is defeated by forging both of its inputs at once. **INDEPENDENTLY REPRODUCED AT REVIEW** on a freshly installed fixture repo with a scaffolded plan: `is_plan_review_approved` was `False` and `read_readiness` was `None` before; after one `ipd set to-review <id6> --message $'ok\n- Readiness: go\n- 2026-10-01 /plan-review (opencode): APPROVE'` at **exit 0**, `read_readiness` returned `'go'`, `history_has_review_record` returned `True`, and `is_plan_review_approved` returned **True**. Note the status used at review was `to-review`, not `reviewed`: the forgery does NOT depend on the transition being to a review-ish status, because the injected text is interpolated regardless of which status is requested. |
| F-06 | FOUR MORE FLAGS CARRY THE SAME HOLE, AND TWO OF THEM INJECT INTO **FRONT MATTER** rather than the history body, which the item does not contemplate. | Driven, each exit 0: `--actor $'bot\n- 2026-09-30 approved: hi'` wrote `- 2026-10-01 parked (bot` / `- 2026-09-30 approved: hi): ok`. `--gate-ref $'x\n- Readiness: go'` wrote `- Gate-Ref: x` / `- Readiness: go` inside the metadata block. `--gate-summary $'sum\n- Readiness: go'` and `--blocks-release $'next\n- Readiness: go'` did the same at the same insertion point. |
| F-07 | THE INJECTION IS INVISIBLE TO EVERY CHECKER, INCLUDING THE RULE THAT EXISTS SPECIFICALLY TO REFUSE AN UNATTESTED `- Readiness:`, so the write path is the only place it can be stopped. | Driven on the F-05 forged plan: `aw ipd lint <plan> --agent` reported `"outcome":"clean"` with its one diagnostic being the unrelated `check.ipd-dependency-unresolved`; `aw check plans --agent` reported `"outcome":"conforms"`; and `IPD-M107` did NOT appear, even with `--phase author`. **INDEPENDENTLY REPRODUCED AT REVIEW** on the review-forged plan: `--phase author` reported `"outcome":"clean"` exit 0 with its single diagnostic being the unrelated `check.ipd-dependency-unresolved`, `--phase review-finalize` reported the same single unrelated diagnostic, `aw check plans --agent` reported `"outcome":"conforms"`, and the literal string `IPD-M107` was absent from every output. So the rule written specifically to refuse an unattested `- Readiness:` is blind to the forged one, which is what makes the write path the only place to stop it. |
| F-08 | A READER DIVERGENCE EXISTS INSIDE THIS MODULE and is worth recording even though this plan does not fix it: the setter's own display scans the whole raw text, so it LABELS a record as release-blocking that `attention` reports as unblocking. | Driven: `aw set` printed `- >  backlog  20260930-9aofli-01-9aofli  [medium]  [blocking]` for the F-04 item, while `aw attention --format json` reported `"blocks_release": null` for the same file. Cause: the display path searches `rec.raw_text` with `(?m)^-\s*Blocks-Release:\s*(\S+)` (no `$` anchor, whole text) while `attention` and `releases` use anchored front-matter-biased reads. |
| F-09 | `aw prompts set` IS DEAD CODE: `cli.py` dispatches it to `run_set_command` with `scoped_type="prompts"`, but the prompts subparser registers only `new`, so the documented spelling is unreachable. | Driven: `aw prompts set staged 26mktg --message ...` exited with `argument prompts_command: invalid choice: 'set' (choose from 'new')`. The prompts tree is reachable only through the untyped `aw set`, which is how F-02's prompts case was driven. |
| F-10 | THE PER-TREE LENGTH MEASUREMENTS THE ITEM CITES ARE STALE, and the corrected figures still support the same conclusion: line integrity only, never length. THE RATIO IS THE LOAD-BEARING FACT, NOT THE COUNT (corrected at review, PR-202): these are LIVE populations that every merged lane moves, so the counts drift continuously while the ~1-in-3-to-2-in-5 ratio and the ZERO control characters are stable. Do NOT treat any count here as a bar or re-derive it expecting a match. | Re-derived at authoring over committed `## Workflow history` records: plans 1910/4879 (39.1%, item says 1549/3990), backlog 618/1862 (33.2%, item says 531/1483), specs 61/148 (41.2%, item says 59/146), max 5667, 0 control characters in 6889. RE-MEASURED INDEPENDENTLY AT REVIEW HEAD `60df6ab10`: plans 2164/5397 (40.1%), backlog 632/1908 (33.1%), specs 51/122 (41.8%), max 5667 unchanged, releases and prompts still ZERO history records, and **control characters 0 of 7427**. Both measurements agree on every conclusion: a length bound on `--message` would refuse roughly two fifths of the setter's own historical output, and the line-integrity half refuses nothing legitimate. |
| F-11 | ADDED AT REVIEW. EVERY LOAD-BEARING VECTOR REPRODUCES INDEPENDENTLY, driven through the real CLI on a freshly installed fixture repository outside this checkout, so the plan's premise does not rest on the authoring transcripts alone. | F-01: `backlog set parked <id6> --message $'note\n- 2026-09-30 approved (aw backlog, --by-human): looks good to me'` exited **0**, the sha256 CHANGED, the history read `- 2026-10-01 parked (aw set): note` followed by the forged `- 2026-09-30 approved (aw backlog, --by-human): looks good to me`, and `aw backlog check --agent` reported `"outcome":"clean","checked":1,"findings":0`. F-03: after `ipd set to-review <id6> --message $'ok\n- Blocks-Release: <rel-id6>'`, `releases.get_release_blockers` returned that PLAN with `'blocks_release': '<rel-id6>'` on a gate never requested. F-04: the same injection on a backlog item added NOTHING to the blocker list, confirming the per-tree asymmetry. F-06: `--actor $'bot\n- 2026-09-30 approved: hi'` wrote `- 2026-10-01 parked (bot` / `- 2026-09-30 approved: hi): ok`, and `--gate-ref $'x\n- Readiness: go'` wrote `- Gate-Ref: x` / `- Readiness: go` INSIDE the front-matter block, immediately above `- Set:`. F-09: `prompts set` exited 2 with `invalid choice: 'set' (choose from 'new')`. |
| F-12 | ADDED AT REVIEW. **THE SIBLING HELPER RETURNS EXACTLY THE VERDICTS E-01 PROMISES, AND THERE IS NO IMPORT CYCLE**, so E-01's delegation is confirmed viable rather than hoped for and its verbatim-port fallback should not be needed. | `backlog._refuse_unsafe_descriptive` signature measured as `(verb: str, flag: str, value: Optional[str], *, bound_length: bool = True) -> Optional[str]`, matching E-01's stated shape exactly. All eight of E-01's expected outcomes verified: `None` for `'ok'` and for `None`; `'v: --message must not contain embedded newlines'` for `'a\nb'`; `'...must not contain control characters'` for `'a\x07b'`; `'...exceeds maximum length of 300 characters (340 > 300)'` for 340 chars; under `bound_length=False`, `None` for 340 and for 1200 chars but still the control-character message for `'a'*500 + '\x07' + 'b'`. `status_set` ALREADY imports `backlog` at module level and lazily in five separate places, and importing both modules together raises nothing, so no cycle exists. |
| F-13 | ADDED AT REVIEW (PR-205). **THE COMPLEMENT CLAIM IS VERIFIED: the `--status` spelling ALREADY REFUSES while the positional spelling does not**, which is what makes this plan's scoping correct rather than an arbitrary split. | Driven on the same fixture item: `backlog set <id6> --status open --message $'ok\n- 2026-09-30 approved (aw backlog, --by-human): LGTM'` exited **2** with `aw backlog set: --message must not contain embedded newlines` (the shipped `dtg7dz` guard on `backlog.run_set`), while the POSITIONAL `backlog set parked <id6> --message <same payload>` exited **0** and wrote the forgery. So the two dispatch halves genuinely diverge today and this plan closes the unguarded half. |

## Proposed changes (ordered, validatable)

1. `status_set._refuse_unsafe_descriptive` is added as a thin delegation to the shipped `backlog._refuse_unsafe_descriptive`, so one verdict owner serves all three modules and the refusal wording stays byte-identical across trees (E-01).
2. The five unguarded value-bearing flags are refused in `run_set_command`'s existing pre-resolution guard block, before `inventory_all_artifacts`, with `--message` in line-integrity mode and `--actor`/`--gate-ref`/`--gate-summary`/`--blocks-release` bounded (E-02, E-03).
3. `tests/test_status_set_descriptive_safety.py` pins the cross-tree injection closure (including the `--status`-versus-positional divergence by its shipped message, F-13), the attestation forgery and its plans-tree gate escalation, the length asymmetry and boundary, and the four non-regression groups, one of which also asserts a newly PROTECTED surface rather than only an unaffected one (the `--item-dependencies` wrapper's forwarded `--message`, PR-203) (E-04, E-05, E-06).

## Deferred / out of scope (with reason)

- THE `--status` SPELLING OF EACH TREE'S OWN `run_set` IS NOT TOUCHED HERE. `aw backlog set <sel> --status <s>` dispatches to `backlog.run_set`, which `dtg7dz` already guarded, and `aw specs set <sel> --status <s>` dispatches to `specs.run_set`, which plan `uz05bl` guards. This plan is the complement of those two, not a replacement, and the two halves are deliberately separate because they are different functions with different exit-code conventions.
  - Carrier-Declined: Nothing is owed. The backlog half is SHIPPED and the specs half is an approved pending plan in Set `qbz8i1`; filing a carrier would duplicate an existing owner.
- THE `status_set` DISPLAY-REGEX DIVERGENCE (F-08) IS NOT FIXED. The setter labels a record `[blocking]` on an unanchored whole-text scan while `attention` and `releases` read it differently, so the three disagree on the same file. Deferred because it is a READER defect with its own blast radius (every `aw set` line rendered for every tree) and its own correctness question (which reader is right, and does anchoring it change what a legitimate multi-line-adjacent record displays), whereas this plan is a write-path guard. Note that this plan REDUCES its reachability without closing it: once the five flags are guarded, a divergent file can no longer be produced BY THIS SETTER, but a hand-edited one still displays wrongly.
  - Carrier: 5e533q
- `aw prompts set` BEING UNREACHABLE (F-09) IS NOT FIXED. Registering a `set` subparser for the prompts family is a CLI-surface addition, not a validation fix, and it needs a decision about which statuses the prompts tree accepts through that spelling (the untyped `aw set` already refused `staged` as "not valid for prompts" while accepting `to-review`). Folding a new verb spelling into a security guard would put two unrelated changes in one commit.
  - Carrier: um8ikz
- HARDENING THE ON-DISK GRAMMAR (quoting or escaping values on write, or refusing to parse a metadata bullet that follows a continuation line) is out of scope and deliberately refused, on the same reasoning plan `uz05bl` records: it would change what every existing reader parses, which is a spec-level change to the artifact format rather than a validation fix.
  - Carrier-Declined: The obligation is DISCHARGED for every vector this plan measures, because F-01 through F-06 all enter through a flag value and E-02/E-03 refuse each before a write occurs. What structural hardening would additionally cover is a HAND-EDITED file, which is not reachable from any write path; F-07 proves the newline case is precisely the one no checker can see afterwards, so filing a carrier would name work with no available mechanism.
- BOUNDING A HISTORY MESSAGE ON LENGTH IS DELIBERATELY NOT DONE, on the measurement in F-10 (roughly two fifths of all committed messages exceed the bound: 2589/6889 at authoring, 2847/7427 at review). That is a policy decision about what a history record may contain, and it would refuse the setter's own normal output on all three populated trees.
  - Carrier-Declined: Nothing is owed. The governing spec bounds DESCRIPTIVE FIELDS, and no checker on any tree bounds a history message, so there is no contract gap here to carry; the asymmetry is the correct reading of the existing contract rather than a shortfall in this plan.

## Scope check

- Over-scope: none. Both declared paths are edited: `agent_workflows/status_set.py` receives the helper and the five guards, and `tests/test_status_set_descriptive_safety.py` is created.
- Under-scope: `attention_contract.py` and `backlog.py` are deliberately NOT edited even though the helper lives in the latter, because E-01 delegates to the shipped function rather than moving or rewording it (OQ-02). `attention.py`, `releases.py` and `cli.py` are NOT edited, which is what defers F-03's reader asymmetry, F-08's display divergence and F-09's missing registration to their carriers rather than this plan.

## Required tests / validation

- `python3 -m pytest` run BARE, with the full summary line pasted. RE-DERIVE A FRESH BASELINE ON THE UNMODIFIED TREE AND COMPARE FAILURE SETS BY NODE ID; do NOT compare against any total written in this plan (PR-201). THE AUTHORING BASELINE IS NOW WRONG IN A WAY THAT WOULD MISLEAD: it recorded `1 failed, 3498 passed, 2 skipped` at HEAD `0da8e0977` and instructed that `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` "must remain the ONLY failure". Measured at review HEAD `60df6ab10`: the suite is FULLY GREEN at `3578 passed, 2 skipped, 3 warnings`, and that named test PASSES on its own (`1 passed`). So an executor following the original instruction would either expect a failure that no longer occurs, or tolerate a real regression in that test as "pre-existing". The correct bar is ZERO failures; if a failure does appear, diagnose it rather than matching it against this paragraph.
- `python3 -m pytest tests/test_status_set_descriptive_safety.py tests/test_status_set.py tests/test_backlog_descriptive_safety.py tests/test_backlog.py` as the targeted surface, since this plan edits the setter the backlog tests also drive.
- Each refusal driven through the real CLI against a fresh fixture repository, with the exit code and the sha256 byte-identity of the untouched target pasted as evidence. A refusal asserted only through a unit call on `run_set_command` does not prove the positional spelling is closed, which is the entire claim.

## Spec / documentation sync

N/A, with reason. No `.spec.md` file is amended, so no spec edit is declared in `- Scope-Paths:`. The governing contract ALREADY specifies this behavior and needs no change: spec `attention-registry-and-cross-tree-status` Section 8.8 states that "embedded newlines are rejected (a violation), not wrapped" and that "Over-length values are a contract violation, not silently truncated", and its A14 acceptance criterion already requires hostile-string fixtures of these shapes. This plan makes a shared write path comply with a contract that is already written; it does not negotiate a new one. No user-facing documentation changes either, because no command surface, flag or output format changes: a conforming invocation behaves exactly as before, and only a malformed value newly refuses.

## Open questions

### OQ-01: Should the guard live at `run_set_command`'s entry, or inside `apply_status_change` where the values are actually interpolated?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE: at the entry. Three refusals already sit in `run_set_command`'s pre-resolution block, each commented as firing "BEFORE any artifact is resolved or written", and `attention_contract.actor_refusal`'s own docstring states the rule ("Callers must invoke this BEFORE any mutation - that ordering is the defect this helper exists to close", plan `fn2l1u`). `apply_status_change` is a pure write reached once per matched record, so guarding there would (a) run the same check N times for a multi-selector call, (b) refuse AFTER other records may already have been written, and (c) have to raise rather than return, since it returns a path/status tuple. The entry placement also means a refused call resolves no artifact at all, which is what makes the byte-identity evidence in E-02/E-03 clean. Note the existing backstop in `apply_status_change` (the `actor_refusal` raise) stays as it is, for a direct caller that skipped the pre-flight; E-06(b) pins it.

### OQ-02: This is the THIRD consumer of the refusal helper, which `uz05bl` OQ-02 named as the point a hoist becomes worthwhile. Should this plan hoist it into `attention_contract`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: no hoist, but no third copy either; DELEGATE to the shipped sibling. `uz05bl` OQ-02 declined the hoist for one concrete reason, that extracting a shared helper would mean editing `specs.run_set`'s shipped `--gate-summary` refusal wording as collateral, and it named "the THIRD consumer" as the point to revisit. Delegating satisfies the intent (one verdict owner, no duplicated conditions, zero new copies) while touching neither shipped refusal, so the collateral OQ-02 was protecting against does not arise and the reconciliation it wanted can still happen deliberately later. The honest cost is a `status_set -> backlog` import for a non-backlog concern, which is mitigated by precedent: this function ALREADY imports `backlog` for `validate_release_exempt_flags` from the very block these guards join. If the executor hits a real cycle, E-01 permits a verbatim port with the reason recorded in V-01 evidence; it does not permit a new construction.

### OQ-03: Should `--message` be refused for an in-repo programmatic caller too, or only for a value that came from a human on the command line?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: refuse uniformly, with no caller exemption. The guard runs at a function every caller shares, and distinguishing "came from argv" from "built in Python" is not available at that point (`run_set_command` receives an already-built Namespace from `cli.main` and from `work_cmd.run_finish` alike). An exemption would also be exactly the kind of bypass that makes a guard worthless: a trusted-caller path is one refactor away from carrying untrusted data. The regression risk this creates was MEASURED rather than assumed: both in-repo positional callers found pass single-line literals (`work_cmd.run_finish` passes `message="aw finish: evidence-bound transition"`, and `status_set`'s `--item-dependencies` wrapper passes a defaulted `set Item-Dependencies to <value>` string), so the guard is expected to be invisible to them, and E-06(c) pins that rather than trusting it. The runner call sites that pass model-authored multi-line text use the `--status` spelling, not this one, so they are not affected by this plan; a later change routing them here would be caught by E-06(c).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste a Python session calling `status_set._refuse_unsafe_descriptive` directly and showing ALL of: `None` for `"ok"` and for `None`; a message containing `newline` for `"a\nb"`; a message containing `control` for `"a\x07b"`; a message containing both `300` and `340` for `"a"*340`; and under `bound_length=False`, `None` for `"a"*340` and for `"a"*1200` but the `control` message for `"a"*500 + "\x07" + "b"`. ALSO paste evidence of HOW the helper reaches the verdict: either the delegation (showing the call into `backlog._refuse_unsafe_descriptive`) or, if a cycle forced a verbatim port, the diff of the ported body plus the reason the delegation was impossible. A new construction that is neither is a V-01 failure.
  - Observed evidence: PASS. Directly called status_set._refuse_unsafe_descriptive; verified all 8 verdicts and delegation into backlog._refuse_unsafe_descriptive.
    Called `status_set._refuse_unsafe_descriptive` directly:
    ```python
    >>> from agent_workflows import status_set
    >>> status_set._refuse_unsafe_descriptive('v', '--message', 'ok')
    None
    >>> status_set._refuse_unsafe_descriptive('v', '--message', None)
    None
    >>> status_set._refuse_unsafe_descriptive('v', '--message', 'a\nb')
    'v: --message must not contain embedded newlines'
    >>> status_set._refuse_unsafe_descriptive('v', '--message', 'a\x07b')
    'v: --message must not contain control characters'
    >>> status_set._refuse_unsafe_descriptive('v', '--gate-summary', 'a'*340)
    'v: --gate-summary exceeds maximum length of 300 characters (340 > 300)'
    >>> status_set._refuse_unsafe_descriptive('v', '--message', 'a'*340, bound_length=False)
    None
    >>> status_set._refuse_unsafe_descriptive('v', '--message', 'a'*1200, bound_length=False)
    None
    >>> status_set._refuse_unsafe_descriptive('v', '--message', 'a'*500 + '\x07' + 'b', bound_length=False)
    'v: --message must not contain control characters'
    ```
    Delegation inspection confirms direct call into `backlog._refuse_unsafe_descriptive`:
    ```python
    def _refuse_unsafe_descriptive(
        verb: str,
        flag: str,
        value: str | None,
        *,
        bound_length: bool = True,
    ) -> str | None:
        from agent_workflows import backlog as _backlog
        return _backlog._refuse_unsafe_descriptive(
            verb, flag, value, bound_length=bound_length
        )
    ```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: in a fresh fixture repo, paste the sha256 of a committed backlog item, then the full output and exit code of `backlog set parked <id6> --message $'note\n- 2026-09-30 approved (aw backlog, --by-human): looks good to me'` showing exit 2, then the sha256 again showing it UNCHANGED. Repeat for the `--actor $'bot\n- 2026-09-30 approved: hi'` vector. Then paste an ACCEPTED `--message` of 1200 single-line characters exiting 0 and the resulting history line, proving the length bound is absent.
  - Observed evidence: PASS. Fresh fixture tests verified --message and --actor newlines refused with exit 2 leaving sha256 byte-identical; accepted 1200-char message exited 0 with history line written.
    In fresh fixture repository:
    Pre-call sha256: `ab9bf18e3b03ff4d0123a06663fe99f7d4704a8dcb320db74d75683726935a5d`
    ```sh
    $ aw backlog set parked bk9999 --message $'note\n- 2026-09-30 approved (aw backlog, --by-human): looks good to me'
    FAIL     aw set: --message must not contain embedded newlines
    Exit code: 2
    ```
    Post-call sha256: `ab9bf18e3b03ff4d0123a06663fe99f7d4704a8dcb320db74d75683726935a5d` (UNCHANGED)

    Pre-actor sha256: `ab9bf18e3b03ff4d0123a06663fe99f7d4704a8dcb320db74d75683726935a5d`
    ```sh
    $ aw set parked bk9999 --actor $'bot\n- 2026-09-30 approved: hi' --message ok
    FAIL     aw set: --actor must not contain embedded newlines
    Exit code: 2
    ```
    Post-actor sha256: `ab9bf18e3b03ff4d0123a06663fe99f7d4704a8dcb320db74d75683726935a5d` (UNCHANGED)

    Accepted 1200-character single-line `--message`:
    ```sh
    $ aw backlog set parked bk9999 --message $(python3 -c "print('a'*1200)") --yes
    -    backlog     20261001-bk9999-01-bk9999  [medium]  open → ◇  parked
    Exit code: 0
    ```
    Resulting history line in `.aw/records/backlog/parked/20261001-bk9999-01-bk9999-item.md`:
    `- 2026-10-01 parked (aw set): ` followed by 1200 `a` characters (line length 1230).
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: for EACH of `--gate-ref`, `--gate-summary` and `--blocks-release`, paste the pre-call sha256, the refused invocation with its exit code 2, and the post-call sha256 showing no change. Then paste one conforming invocation of each (`--gate-ref D42`, `--gate-summary "a reason"`, `--blocks-release next`) exiting 0 WITH the resulting front-matter lines, proving the guards did not break the legitimate write. ALSO paste the unchanged refusals for `--graduated-to` and `--release-exempt-ref` to show the new guards are additive.
  - Observed evidence: PASS. Fresh fixture tests verified --gate-ref, --gate-summary, and --blocks-release newlines refused with exit 2 and sha256 unchanged; conforming invocations succeed; existing --graduated-to and --release-exempt-ref refusals unchanged.
    In fresh fixture repository:
    1. `--gate-ref`:
       Pre-call sha256: `f19f187a057f897621cba50f3bcaea7aa8746c10eb3638260b00c3b0eb6493dc`
       Command: `aw set blocked bk0001 --gate-kind decision --gate-ref $'x\n- Readiness: go' --message ok`
       Output: `FAIL     aw set: --gate-ref must not contain embedded newlines`
       Exit code: 2
       Post-call sha256: `f19f187a057f897621cba50f3bcaea7aa8746c10eb3638260b00c3b0eb6493dc` (UNCHANGED)

    2. `--gate-summary`:
       Pre-call sha256: `007994784a0c8b6ae792a6c2f30b91df15f3ec592a2a0ffbaaa4bfcbdf18b1a8`
       Command: `aw set blocked bk0002 --gate-kind decision --gate-ref D42 --gate-summary $'sum\n- Readiness: go' --message ok`
       Output: `FAIL     aw set: --gate-summary must not contain embedded newlines`
       Exit code: 2
       Post-call sha256: `007994784a0c8b6ae792a6c2f30b91df15f3ec592a2a0ffbaaa4bfcbdf18b1a8` (UNCHANGED)

    3. `--blocks-release`:
       Pre-call sha256: `9b46df52b4119f18579d4ec67ebf82b404d9c73e86c0efbfa7585b2e9e289bf4`
       Command: `aw set to-review pl0001 --blocks-release $'next\n- Readiness: go' --message ok`
       Output: `FAIL     aw set: --blocks-release must not contain embedded newlines`
       Exit code: 2
       Post-call sha256: `9b46df52b4119f18579d4ec67ebf82b404d9c73e86c0efbfa7585b2e9e289bf4` (UNCHANGED)

    Conforming invocations:
    - `aw set blocked bk0001 --gate-kind decision --gate-ref D42 --gate-summary "a reason" --message ok --yes` (exit 0)
      Resulting front-matter lines:
      `- Gate-Kind: decision`
      `- Gate-Ref: D42`
      `- Gate-Summary: a reason`
    - `aw set to-review pl0001 --blocks-release next --message ok --yes` (exit 0)
      Resulting front-matter line:
      `- Blocks-Release: next`

    Additive validation of existing flags:
    - `aw set graduated bk0002 --graduated-to $'x\n- Readiness: go'`
      Output: `FAIL     aw set: --graduated-to takes lowercase-kebab setids of at most 40 characters; malformed: 'x\n- Readiness: go'` (exit 2)
    - `aw set parked bk0002 --release-exempt-kind decision --release-exempt-ref $'r1\n- Readiness: go'`
      Output: `FAIL     aw set: --release-exempt-ref is invalid for kind 'decision': 'r1\n- Readiness: go'` (exit 2)
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste the targeted run of `tests/test_status_set_descriptive_safety.py` with its summary line. Separately, paste evidence that the injection cases genuinely FAIL against pre-guard code (for example by running the new module with the guards reverted, or at the pre-fix commit), since a test that passes in both states pins nothing. The paste must show the `--message` case covering all five trees (plans, specs, backlog, releases, prompts) and at least one case driving the POSITIONAL spelling through `cli.main` or a subprocess rather than calling `run_set_command` directly.
  - Observed evidence: PASS. Targeted test tests/test_status_set_descriptive_safety.py passed 15/15; pre-guard execution verified to exit 0 and mutate target; post-guard exits 2 across all 5 trees.
    Targeted test run:
    ```
    $ python3 -m pytest tests/test_status_set_descriptive_safety.py -v -o addopts=""
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=2591046910
    rootdir: .
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 15 items

    tests/test_status_set_descriptive_safety.py::TestLengthAsymmetryAndNonRegressions::test_in_repo_callers_and_deps_wrapper PASSED [  6%]
    tests/test_status_set_descriptive_safety.py::TestLengthAsymmetryAndNonRegressions::test_length_asymmetry_and_late_control_characters PASSED [ 13%]
    tests/test_status_set_descriptive_safety.py::TestLengthAsymmetryAndNonRegressions::test_non_regression_actor_refusals_and_backstop PASSED [ 20%]
    tests/test_status_set_descriptive_safety.py::TestLengthAsymmetryAndNonRegressions::test_non_regression_already_validated_flags PASSED [ 26%]
    tests/test_status_set_descriptive_safety.py::TestLengthAsymmetryAndNonRegressions::test_conforming_transitions_across_five_trees PASSED [ 33%]
    tests/test_status_set_descriptive_safety.py::TestLengthAsymmetryAndNonRegressions::test_boundary_gate_summary_length PASSED [ 40%]
    tests/test_status_set_descriptive_safety.py::TestCrossTreeInjection::test_blocks_release_injection_refused PASSED [ 46%]
    tests/test_status_set_descriptive_safety.py::TestCrossTreeInjection::test_gate_ref_injection_refused PASSED [ 53%]
    tests/test_status_set_descriptive_safety.py::TestCrossTreeInjection::test_shipped_status_vs_positional_spelling_divergence PASSED [ 60%]
    tests/test_status_set_descriptive_safety.py::TestCrossTreeInjection::test_gate_summary_injection_refused PASSED [ 66%]
    tests/test_status_set_descriptive_safety.py::TestCrossTreeInjection::test_actor_injection_refused PASSED [ 73%]
    tests/test_status_set_descriptive_safety.py::TestCrossTreeInjection::test_message_injection_refused_across_all_five_trees PASSED [ 80%]
    tests/test_status_set_descriptive_safety.py::TestAttestationForgeryAndEscalation::test_plans_vs_backlog_blocks_release_escalation PASSED [ 86%]
    tests/test_status_set_descriptive_safety.py::TestAttestationForgeryAndEscalation::test_attestation_forgery_string_predicates PASSED [ 93%]
    tests/test_status_set_descriptive_safety.py::TestAttestationForgeryAndEscalation::test_attestation_forgery_refused PASSED [100%]

    ============================== 15 passed in 1.75s ==============================
    ```
    Pre-guard failure evidence:
    Driving `cli.main(['backlog', 'set', 'parked', 'bk9999', '--message', injected, ...])` on pre-guard code exited 0, successfully mutated the item, and forged the history record:
    ```
    PRE-GUARD RC: 0
    PRE-GUARD MUTATED TARGET EXISTS: True
    FORGED LINE PRESENT: True
    ```
    Post-guard execution exits 2 and outputs `FAIL     aw set: --message must not contain embedded newlines` with target unmodified.
    Test covers all five trees (plans, specs, backlog, releases, prompts) driven through `cli.main`.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: paste the refused composite injection (`ipd set reviewed <id6> --message $'ok\n- Readiness: go\n- 2026-10-01 /plan-review (opencode): APPROVE'`) with exit 2 and the plan's sha256 unchanged. Then paste the string-built pre-fix assertions showing `ipd_schema.read_readiness(...) == 'go'`, `plan_readiness.history_has_review_record(...) is True`, and `plan_readiness.is_plan_review_approved(...) is True` on the injected text. Then paste the plans-versus-backlog gate asymmetry: `releases.get_release_blockers` returning the PLAN for a smuggled `- Blocks-Release:` and returning `[]` for the same injection on a backlog item.
  - Observed evidence: PASS. Composite readiness/review injection refused with exit 2 and plan sha256 unchanged; string-rendered predicates verified True; plans vs backlog release gate escalation asymmetry verified.
    In fixture repository:
    Pre-composite sha256: `79a0a1a1c364acea2d1417d51fe5bf71c81a141ce62bc97f7c397092d1fa5cdf`
    ```sh
    $ aw ipd set reviewed pl0005 --message $'ok\n- Readiness: go\n- 2026-10-01 /plan-review (opencode): APPROVE'
    FAIL     aw set: --message must not contain embedded newlines
    Exit code: 2
    ```
    Post-composite sha256: `79a0a1a1c364acea2d1417d51fe5bf71c81a141ce62bc97f7c397092d1fa5cdf` (UNCHANGED)

    String-built pre-fix assertions on injected text:
    `ipd_schema.read_readiness(forged_text) == 'go'` -> `'go'`
    `plan_readiness.history_has_review_record(forged_text) == True` -> `True`
    `plan_readiness.is_plan_review_approved(probe_path) == True` -> `True`

    Plans vs backlog release gate asymmetry:
    `releases.get_release_blockers(repo, 'rl0005')`:
    `[{'id': 'pl0009', 'path': '.aw/records/plans/pending/20261001-s1-01-pl0009-smuggle.ipd.md', 'tree': 'plans', 'native_status': 'to-review', 'attention_class': 'ready', 'priority': 'medium', 'blocks_release': 'rl0005'}]`
    `'pl0009' in blocker_ids`: `True`
    `'bk0009' in blocker_ids`: `False`
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: paste the asymmetry test output showing a 1200-character clean `--message` accepted, a 301-character `--gate-summary` refused, and `"a"*500 + "\x07" + "b"` refused. Paste the boundary result (300 accepted, 301 refused). Paste the four non-regression groups: the two already-validated flags' unchanged messages; `actor_refusal`'s empty and parenthesis refusals still firing INCLUDING the `apply_status_change` backstop raise; `work_cmd.run_finish` and the `--item-dependencies` wrapper still succeeding; and one conforming transition per tree exiting 0 with its history record written. FINALLY paste the BARE `python3 -m pytest` summary line showing ZERO FAILURES, alongside a freshly re-derived pre-change baseline, compared by node id (PR-201: the authoring plan expected one pre-existing failure which no longer occurs, so treating that test's failure as acceptable would now mask a real regression this plan caused).
  - Observed evidence: PASS. Asymmetry (1200-char accepted, 301-char refused, late control char refused) and boundary (300 accepted, 301 refused) verified; non-regressions (actor, programmatic callers, 5-tree conforming transitions) passed; bare pytest suite 4118 passed, 2 skipped, 3 warnings in 151.24s with 0 regressions.
    1. Asymmetry & boundary:
       - 1200-character clean `--message`: accepted (exit 0)
       - 301-character `--gate-summary`: refused (exit 2, `aw set: --gate-summary exceeds maximum length of 300 characters (301 > 300)`)
       - `"a"*500 + "\x07" + "b"`: refused (exit 2, `aw set: --message must not contain control characters`)
       - Boundary at 300 accepted (exit 0), 301 refused (exit 2)
    2. Non-regressions:
       - Already-validated flags: `--graduated-to` and `--release-exempt-ref` unchanged refusal messages (exit 2).
       - `actor_refusal`: empty (`a non-empty actor is required.`) and parenthesis (`contains a parenthesis`) checked, and `apply_status_change` raises `ValueError: ... contains a parenthesis`.
       - In-repo callers: simulated `work_cmd.run_finish` Namespace exits 0; `--item-dependencies` wrapper default message exits 0; `--item-dependencies` with custom newline message is newly refused with exit 2 (`aw set: --message must not contain embedded newlines`).
       - Conforming transitions: plans, specs, backlog, releases, and prompts all exit 0 with conforming history records written.
    3. Full bare pytest suite:
       `4118 passed, 2 skipped, 3 warnings in 151.24s (0:02:31)` with 0 failures.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is one guard at one function plus its test module, so it is a single cohesive change despite serving five trees; that breadth is a property of the dispatch, not of the plan's scope.

WHAT AN APPROVER MOST NEEDS TO KNOW, and it was independently re-driven at review rather than read off this plan's transcripts. The defect is real and severe: one `aw ipd set` command writes BOTH a `- Readiness: go` field and the `/plan-review` record that attests it, flipping `plan_readiness.is_plan_review_approved` from `False` to `True` on a plan nothing reviewed (F-05, reproduced at review on a fresh fixture). `AGENTS.md` names that field as one an agent must never hand-write, and under `--full-auto` it is what promotes a plan to approved. No checker can see it afterwards: `IPD-M107`, the rule written specifically to refuse an unattested `- Readiness:`, does not fire at any phase (F-07, reproduced). The plans tree additionally escalates a smuggled `- Blocks-Release:` into a FUNCTIONING release gate while the backlog tree leaves it inert (F-03/F-04, both reproduced), so the harm is worse than the backlog item predicted. The fix is narrow and low-risk: five call sites in one existing pre-resolution guard block, delegating to a helper that ALREADY SHIPS and whose every promised verdict was verified at review (F-12), with zero control characters in 7427 committed history messages making the line-integrity half refuse nothing legitimate (F-10). THREE THINGS REVIEW CHANGED: the suite baseline this plan told the executor to match no longer exists (the tree is now fully green, so expecting one failure would mask a regression); the `--item-dependencies` wrapper turns out to FORWARD a user `--message`, making it a second surface this guard newly protects rather than merely a non-regression; and the per-tree length counts have drifted, so the plan now leads with the stable ratio instead.

EXECUTION CONTRACT. Commit only `agent_workflows/status_set.py` and `tests/test_status_set_descriptive_safety.py` through `aw commit <plan> -- <paths>`; never `git add -A`, and never push. Before committing, verify the staged set with `git diff --cached --name-only` and unstage anything you did not change, since this is a shared checkout. Paste ACTUAL runner output for every test claim; a summary written from memory violates the execution contract. Do not weaken any E-item or V-item to make it pass, and do not widen scope to the three deferred findings (F-03's reader asymmetry, F-08's display divergence, F-09's missing registration); the latter two already have filed carriers (`5e533q` and `um8ikz`), so touching them here would duplicate an owned obligation rather than close a gap.

POST-GATE LIFECYCLE. Execution requires human approval first (`- Status:` must reach `approved`). The `- Readiness: go-pending-approval` field now present was written by `/plan-review` on 2026-10-01 as its own attestation; the AUTHOR correctly omitted it, and `reviewed` plus `go-pending-approval` is still NOT approval. Run `aw ipd begin` before implementing and `aw ipd finalize` after, so the lifecycle records the transition; do not hand-move the file to `.aw/records/plans/executed/`. Do not claim completion until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. The backlog item `nw9dmz` stays `graduated` rather than `done` until this plan is executed, since it carries `- Blocks-Release: next` and this plan is its gate carrier.
