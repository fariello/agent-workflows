# Review findings: plan uz05bl

- Subject-Id: uz05bl
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-801 (HIGH, fixed), PR-802 (HIGH, fixed), PR-803 (MEDIUM, fixed), PR-804 (LOW, fixed), PR-805 (LOW, fixed)

## Round 1

Reviewed at HEAD `cff630f3` in an isolated review lane. The plan file was committed and byte-identical to
the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize` reports `conforming` after revision. The plan is `- Kind: child`, so the
`IPD-S407` orchestrator row check does not apply. This is Order 01 of Set `qbz8i1`; Orders 00, 02 and 03
were read as evidence and are NOT in the review scope.

THIS IS A STRONG PLAN AND ITS TWELVE FINDINGS ALL REPRODUCE. I re-drove every one against fresh
`git init` fixture repositories rather than reading them. F-01: the `--summary` newline exits 0 and writes
a real `- Blocks-Release: next` bullet with `validate_spec == []` and `aw specs check --agent`
`"outcome":"clean"`. F-02: the smuggled gate FUNCTIONS, with `aw releases show next` printing
`release-blockers (1)` and `get_release_blockers` returning the spec. F-03, the plan's own correction of
its backlog item, is right and is the severe one: the `--title` newline writes
`['- Status: approved', '- Status: draft']` in that order, `_find_status_index` returns 1, `_read_status`
returns `approved`, both checkers report clean, and `aw attention --format json` reports
`"native_status":"approved"` on a spec nothing approved. F-04 reproduces on both `--summary` and
`--version`, with `--status` correctly refusing at exit 2 via its enum. F-05, F-06, F-07 (including the
raw ANSI reaching `aw attention --details --no-color` while the JSON reports `"valid": true`), F-10 (the
314 and 366 character `- Scope:` pair), F-11 and F-12 all reproduce exactly as written. The plan's
conventions section is accurate, including the exit-code histograms OQ-01 rests on (`run_set` is 1 for ten
refusals, `run_new` and `run_note` are 2) and the `releases.run_new` `_usage` closure.

THEN I AUDITED WHAT THE PLAN DID NOT PRESENT, which is where both HIGH findings came from: an enumeration
of every user-supplied value that reaches front matter through these four verbs.

FIRST HIGH. `specs.run_set` has TWO MORE LIVE INJECTION VECTORS the authoring pass missed, and the plan's
Scope sentence explicitly claimed them ("every value ... write into a record"). Measured:
`aw specs set <spec> --status to-review --blocks-release $'next\n- Status: approved'` exits **0** and
writes `- Status: to-review` / `- Blocks-Release: next` / `- Status: approved`, with `validate_spec` `[]`,
`aw specs check --agent` `"outcome":"clean"`, `aw check specs --agent` `"outcome":"conforms"`, and
`aw releases show next` listing the spec as a real blocker. `--from-backlog` is identical. I then closed
the enumeration rather than stopping at two, because a coverage claim nobody can check is worth little:
`--priority` and `--work-kind` are argparse `choices` enums that refuse at parse time, `--graduated-to`
already refuses with `--graduated-to takes lowercase-kebab setids`, and `--gate-summary`, `--gate-ref` and
`--evidence` already call `A.is_safe_descriptive` at the three existing `specs.py` sites. So those two are
the complete unguarded remainder, which is what makes E-07 provably sufficient rather than arbitrary. I
also checked what they do NOT do: the injected `- Status:` lands below the legitimate one, so
`_read_status` returned `to-review` and no approval is forged through these two, which is why E-07 is
scoped as a smuggled-gate finding and not a second F-03.

SECOND HIGH. E-01's prescribed `bound_length=False` construction has a hole. The plan said to use
"an explicit `"\n" in value or "\r" in value` test plus `A.is_safe_descriptive(value[:
A.MAX_DESCRIPTIVE_LEN])`", and the slice hides anything past character 300. Measured both forms against
`"a"*500 + "\x07" + "b"`: the prescribed form returns `None` (ACCEPTED) while the real sibling
`backlog._refuse_unsafe_descriptive(..., bound_length=False)` returns `'must not contain control
characters'`, because the sibling additionally requires `not A._CONTROL_CHAR_RE.search(value)` over the
WHOLE value. This is reachable by construction and not a theoretical nit: F-09's entire argument is that a
real history message may be 2594 characters long, so the discarded region is exactly where real content
lives. The plan said "PORT IT rather than inventing a second shape" and then described a different shape;
the fix is to port verbatim and to name the extra conjunct as load-bearing. All six other vectors agree
between the two forms, which is why this survived authoring.

THREE SMALLER ITEMS. The `--message` vector is stronger than E-03's "provenance forgery" wording:
measured, `--message $'ok\n- 2026-09-29 approved (aw specs, --by-human): looks good'` exits 0 and the spec's
`## Workflow history` contains that forged `--by-human` record verbatim at zero checker drift, which is
precisely what `AGENTS.md` forbids. F-09 re-derives as 60 of 148 (40.5%), median 239, still zero control
characters, so the proportion is durable and the counts are not. And V-06 demanded `aw check specs --agent`
prove the population unaffected, but that command actually emits `"findings":1` today, a pre-existing
`check.collisions-not-checked` advisory unrelated to this plan, so the bar had to be restated as "adds no
finding" or an executor would have chased it.

ONE FIXTURE TRAP recorded so an executor does not lose the cycle I lost: a successful `aw specs set` MOVES
the spec between status directories, so a test holding the pre-call path raises `FileNotFoundError`. The
refused case is unaffected, which is exactly why the accepted and refused cases must not share a
path-caching helper.

WHAT I CHECKED AND LEFT ALONE. E-05's rendered-string approach works: `specs._render_new_spec` is callable
with signature `(*, title, id6, date_iso, summary)` and a direct call with an injected title reproduces
`_read_status == "approved"` and `validate_spec == []` with no verb involved, so those two assertions will
genuinely keep documenting the vector after the guard closes it. `create_release` still writes an unsafe
summary today, confirming E-06(d)'s deliberate under-scope, and `plan_release`'s docstring does read
"Compute (path, text) ... WITHOUT touching the filesystem", so E-04's refusal to guard the library is
correctly grounded. OQ-01, OQ-02 and OQ-03 are all sound: `core.kebab` really does reduce a newline-bearing
slug to `x-blocks-release-next`, and `A.is_safe_descriptive('../../../../outside/pwned')` really does
return True, which is the precise reason Order 02 must exist separately. The four `Deferred` rows and their
carriers are all justified, and the two `Carrier-Declined` rows argue their case properly.

Nothing in `agent_workflows/` or `tests/` was modified. All probe work lived in gitignored scratch under
`.aw/state/`; `git diff --stat agent_workflows/ tests/` is empty.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | HIGH | UNDER-SCOPE | B. Security / D. Anti-regression (a claimed coverage class with two live holes in it) | `aw specs set <spec> --status to-review --blocks-release $'next\n- Status: approved'` exits 0, writing `- Status: to-review` / `- Blocks-Release: next` / `- Status: approved`; `validate_spec` `[]`; `aw specs check --agent` `"outcome":"clean"`; `aw check specs --agent` `"outcome":"conforms"`; `aw releases show next` prints `release-blockers (1)` naming the spec. `--from-backlog` identical, writing `- From-Backlog: x` then `- Status: approved`. Remainder checked individually: `--priority`/`--work-kind` are argparse enums (exit 2), `--graduated-to` refuses (exit 2), `--gate-summary`/`--gate-ref`/`--evidence` already call the predicate | **Two more live injection vectors exist in `specs.run_set`, and the plan's Scope sentence claimed to cover them.** Shipping as authored would leave a `Blocks-Release: next` plan asserting a vector class is closed while a smuggled, checker-invisible, functioning release gate remains reachable through two flags of a function the plan already edits | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | New E-07 guards both with `bound_length=True` at exit 1 per `run_set`'s convention, stating plainly that no approval is forged through them since the injected status loses the first-match race. New V-07 requires the pre-fix counterpart, the byte-identity proof, the conforming converse, AND the enumeration of the already-refusing flags so the coverage claim is checkable. The `- Scope:` sentence is corrected and enumerated; F-13 records the measurements; E-05/E-06(e) and the Scope check updated; new OQ-04 records the fold-in decision and its three rejected alternatives |
| PR-802 | HIGH | IN-SCOPE | A. Correctness (a prescribed construction that accepts what it must refuse) | Both forms driven against `"a"*500 + "\x07" + "b"`: the prescribed slice-only form returns `None` (ACCEPTED); the real `backlog._refuse_unsafe_descriptive(..., bound_length=False)` returns `'v: --message must not contain control characters'`. The sibling's whole-value `not A._CONTROL_CHAR_RE.search(value)` conjunct is the difference. All six other vectors agree | **E-01's prescribed `bound_length=False` construction accepts a control character past character 300, because `value[: A.MAX_DESCRIPTIVE_LEN]` hides it.** The item says to PORT the sibling and then describes a different, weaker shape. It is reachable by construction, not theoretically: F-09 measures real history messages up to 2594 characters, so the discarded region is exactly where real content sits, and the guard would silently pass a control-character payload into a record | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | E-01 now requires porting the sibling's form verbatim, names the whole-value conjunct as non-redundant, and explains why the slice cannot be the only test. Its expected outcome adds the late-control vector with the measured sibling output. V-01 makes that vector MANDATORY and fails the item without it, since a session omitting it cannot distinguish the ported helper from the unsound one. E-06 and V-06 pin it beside the accepted 1200-character message. F-15 records it |
| PR-803 | MEDIUM | IN-SCOPE | Evidence accuracy (a harm described rather than measured, and one understated) | `aw specs note <spec> --message $'ok\n- 2026-09-29 approved (aw specs, --by-human): looks good'` exits 0; the spec's `## Workflow history` then contains that forged record verbatim between the real note and created records; `validate_spec` `[]`; `aw specs check --agent` clean; the `- Status:` bullet stays `draft` | **E-03 describes the `--message` harm as provenance forgery in the abstract when the concrete forged `--by-human` approval record is measurable, and does not bound the claim.** A reader cannot tell whether the attestation trail or the status field is affected, and the plan's strongest argument for guarding an unbounded field goes unevidenced | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03's harm paragraph now cites the measured forged record verbatim and states what it does NOT do (the `- Status:` bullet is untouched, so the forgery is in the trail not the field). V-03 requires it as evidence. F-14 records it |
| PR-804 | LOW | IN-SCOPE | E. Testing (a validation bar the command cannot meet) | `aw check specs --agent` at HEAD emits `"outcome":"conforms","findings":1` with the single diagnostic `{"location":"<collisions>","rule":"check.collisions-not-checked"}`. `aw specs check --agent` emits `"checked":38,"findings":0` | **V-06 requires `aw check specs --agent` as proof the existing population is unaffected, but that command already reports one finding**, a pre-existing advisory unrelated to this plan. An executor would either chase it or, worse, conclude their change caused it | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-06 now names the pre-existing `check.collisions-not-checked` advisory explicitly and restates the required property as "this plan ADDS no finding" rather than a zero count, while still requiring both counts be re-derived. F-16 records it |
| PR-805 | LOW | IN-SCOPE | G. Plan executability (drifting counts, an incomplete gate, and a fixture trap) | F-09 re-derived as n=148, 60 over 300 (40.5%), median 239, max 2594, 0 control characters (plan: 146/59/40.4%/235). A successful `aw specs set` moves the spec between status directories, raising `FileNotFoundError` on a cached path. The gate lacked the honesty MUST, a scope fence, the open-questions statement, and the conditional-ownership transition | **Three executability gaps.** F-09's counts are stated as flat facts although they grow with every landed change; nothing warns that `specs set` relocates its target, which a byte-identity test will hit; and the gate omits four required execution-contract elements | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-09 and its two restatements now carry both dated measurement sets with the PROPORTION named as the durable claim and an explicit instruction that drift is expected. E-05 warns to re-glob after any `specs set` and says why the refused case differs. The gate gains the paste-the-actual-output honesty MUST, the bare-run instruction, a declaration-style scope fence naming the one genuinely-unsafe stop condition (a concurrent `specs.py` edit, which sibling Order 02 also touches), the open-questions statement, and the unconditional-finalize/conditional-owner paragraph with the never-hand-roll prohibition. `Readiness` recorded as a review output |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-801: two more live vectors found. Fold into this plan, file a backlog item, or add a fifth plan to the Set? | FOLD IN as E-07 | (a) a new backlog item; (b) a fifth plan in Set `qbz8i1`; (c) narrow the Scope sentence and leave them open | Option (a) would file a live `bug` (a smuggled, checker-invisible, functioning release gate) as future work while THIS plan ships carrying `Blocks-Release: next` and claiming the vector class is closed, and the repository does not ship known bugs. Option (b) would touch the same function as Order 01, creating the one genuine merge overlap this Set otherwise avoids, for two call sites. Option (c) is honest but deliberately leaves a measured injection in the plan whose whole subject is closing injections. The marginal cost argues for inclusion: same helper, same function E-03 already edits, same exit code, same test module | yes |
| D-2 | PR-801 follow-on: is the enumeration of "already-validated" flags worth writing into the plan, or is naming the two fixes enough? | WRITE THE ENUMERATION, and require it as V-07 evidence | (a) just guard the two and move on; (b) guard every `run_set` flag defensively regardless of existing validation | Option (a) leaves the next reader with the same unfalsifiable coverage claim that produced this finding: "every value" was asserted and was wrong, so a second unchecked assertion is no better. Option (b) would duplicate three guards that already work (`--gate-summary`, `--gate-ref`, `--evidence` all call the predicate today) and would risk changing their shipped refusal wording as collateral, which OQ-02 specifically declined. Enumerating which flags are guarded here, which already refuse, and by what mechanism makes the claim checkable in one pass | yes |
| D-3 | PR-802: E-01 says "port the sibling" but prescribes a weaker construction. Correct the prose, or leave it and let the executor follow the port instruction? | CORRECT THE PROSE and make the late-control vector mandatory evidence | (a) leave it, since "PORT IT" already appears and an executor reading the sibling would get it right; (b) drop `bound_length=False` and bound history messages too | Option (a) gambles the guard's soundness on which of two contradictory instructions an executor follows, and the specific, concrete one (the code shape) is the likelier read. Option (b) is refuted by F-09's re-derived measurement: it would refuse roughly two fifths of the verb's own historical output. Making the vector mandatory evidence is what converts the instruction into something a validation can catch, since the two forms differ on exactly one input | yes |
| D-4 | Should the review author the guards, having measured every vector? | NO; the probes stay throwaway scratch | (a) implement E-01 through E-07 directly, since the fix is small and fully measured; (b) paste probe source into the plan as the implementation | The workflow edits planning documents only, and this plan carries `Blocks-Release: next`, so a reviewer landing unreviewed production code into a release-gating change is the worst case for that rule. The probes also cut corners the deliverable must not: they call internals directly, hand-roll fixtures without the established `_DropInFixture`-style helpers, and assert nothing about the agent envelope E-04 requires. What they legitimately contribute is the five findings plus verified feasibility of E-05's rendered-string approach | yes |
