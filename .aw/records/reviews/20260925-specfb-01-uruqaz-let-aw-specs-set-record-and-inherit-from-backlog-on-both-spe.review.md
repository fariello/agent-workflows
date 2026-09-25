# Review: Let aw specs set record and inherit From-Backlog on both spellings

- Subject-Id: uruqaz
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims verified at HEAD `bd2aae40`. The target plan was committed and unchanged, so the pre-review
snapshot was correctly skipped per Step 1. Structural preflight `aw ipd lint --phase author --agent`
reported `conforming` (exit 0) BEFORE review and again at `--phase review-finalize` after the revisions.

BOTH OF THE PLAN'S FINDINGS HOLD, and its central structural insight is exactly right: the two
`aw specs set` spellings dispatch to different handlers on the presence of `--status`
(`cli.py`'s `specs_cmd == "set"` branch routes `status is None` to `status_set.run_set_command` and
otherwise to `specs.run_set`), and a field writer must therefore exist on both. The plan found that
seam itself rather than inheriting it, and `--graduated-to` is the shipped precedent for precisely
this shape, carrying a comment that states the obligation in so many words.

I DID NOT STOP AT READING THE HANDLERS, and that decided most of this review. I built a scratch git
repo holding a draft spec, a `planned` release record, and an `open` backlog item carrying
`- Blocks-Release: relaaa`, then drove each handler directly with `from_backlog="bbb111"`. The results
re-sized two of the plan's four items:

- The BARE spelling is ALREADY COMPLETE. `status_set.run_set_command` wrote `- From-Backlog: bbb111`,
  inherited `- Blocks-Release: relaaa`, printed `aw set: inherited - Blocks-Release: relaaa from
  backlog item bbb111 (graduation handoff: the gate travels with the work)`, and relocated the spec to
  `to-review/`. So E-01's flag registration ALONE finishes that path, exactly as the source item
  `mod4ml` predicted ("the write side needs no new code"), and no writer work is owed there.
- The `--status` spelling drops BOTH silently. `specs.run_set` returned rc 0, relocated the spec, and
  produced NEITHER bullet. This is the real defect and it is worse than "no writer": it is a silent
  no-op on a flag the user passed.

That asymmetry is why V-01 through V-03 now demand DRIVEN output rather than diffs. A diff of a writer
placed after an early return looks identical to a diff of one that runs, and this code path already
demonstrates the failure mode of returning success having written nothing.

THE DOMINANT FINDING IS PR-502, and it is a case of the plan proposing something the repository has
already decided against. E-02 required validating the id6 against `backlog.existing_backlog_ids` and
E-03 required refusing an unknown one. The shipped write states the opposite ruling in a comment
directly above the code this plan extends: `IT IS A WRITE, NEVER A REFUSAL. Refusing --from-backlog
when the gate cannot be applied would break a link the author is legitimately recording, and
check.from-backlog-gate-mismatch already ships at ERROR to catch a mismatch afterwards.` Two
consequences. The portable authority already covers it (`releases.check_from_backlog` ships
`check.from-backlog-dangling` at ERROR and scans specs as well as plans), so nothing is uncovered. And
decisively for THIS plan: `status_set` validates nothing, so validating on one spelling only would
leave the two disagreeing about the same flag, which is the very defect the plan exists to remove. I
resolved this against the plan rather than asking, because the repository states both the ruling and
its reason beside the code, and recorded it as OQ-02 and decision D-2.

PR-503 removes a second piece of over-scope on measurement rather than on judgement. E-01 called for
adding the flag to `command_surface.py`'s `specs set` `legacy_flags`. `COMMAND_INVENTORY` declares
parser LEAVES, not flags: `build_matrix` computes `report.undeclared = sorted(parser_leaves -
declared)`, and the matrix's hard failure is an undeclared leaf. There is ONE shared `command="set"`
declaration and it lists none of `--priority`, `--work-kind`, `--graduated-to`, so adding
`--from-backlog` alone would imply an enumeration that does not exist and make the surface less honest
than its current consistent silence. `tests/test_json_and_exitcodes.py` passes untouched. The path is
removed from `- Scope-Paths:` accordingly.

PR-504 is under-scope of the kind that matters most here. E-02's prose bundled the gate inheritance
into the field write and named no precedence rules, while the shipped implementation carries three:
an explicit `--blocks-release` in the same call WINS, an existing gate on the artifact is NEVER
overwritten (it may encode a decision the spec made for its own reasons), and a missing or
unresolvable item is not a refusal. An executor implementing "inherit the gate" without those would
produce a second, subtly different inheritance policy on the other spelling, which is a
cross-spelling inconsistency in the same class as the one being fixed. It is now E-03 with the rules
named and V-03 demanding all four outcomes driven.

PR-505 is small but would have made E-04 report a clean no-op over a real defect. The item greps for a
statement that "a spec cannot record From-Backlog through a setter"; no file says that. What AGENTS.md
actually does is name `aw ipd set <status> <plan> --from-backlog <id6>` as THE setter and then assert
that a spec is an equally valid gate carrier, giving no spec route. That IS `mod4ml`'s asymmetry,
stated positively rather than as a denial, so the grep's shape would have missed it. Neither records
README mentions the field at all, so that half is genuinely a no-op and E-05 must now report it as
one. I also confirmed the AGENTS.md section sits below `<!-- /aw:block -->` (the marker is at line 123,
the sentence at 206), so a plan may edit it; had it been inside, the next install would have reverted
the fix silently, which the gate now names as a stop condition.

PR-506 is a concrete break the plan would have caused. `specs.run_set` reads every optional field with
`getattr(args, <name>, None)`, and that is not stylistic: the suite calls it with hand-built
Namespaces carrying only the attributes each test needs (`tests/test_specs_verbs.py`'s `_args` sets
five or six; `tests/test_specs_status_dirs.py` sets a fixed list that would not include a new field).
A direct `args.from_backlog` would raise `AttributeError` across existing tests. E-02 now states the
read form and the reason, and the Required tests section adds the three files that exercise it, which
a run scoped to the new test file alone would not.

ON RIGHT-SIZING: four items was slightly too coarse in one place and the split is now six. E-02 held
two deliverables with different failure modes (a one-line write with no policy, and a three-rule
inheritance with a second artifact read), and E-04 held a doc grep plus the bare suite, which is a
different test-surface from everything above it. Nothing was split for its own sake; the four
original groups' substance is intact.

Two things I checked and found correct, recorded so a later reader does not re-derive them: the
`- From-Backlog:` write does NOT trip `specs.validate_spec` (proven by the bare spelling writing it
and the spec still conforming, and by `aw specs check` reporting all specs conform at this HEAD), and
OQ-01's `-` answer is load-bearing beyond symmetry because `status_set` guards inheritance with
`if fb != "-"`, so `-` must reach the writer as a literal. Backlog item `mod4ml` carries no
`- Blocks-Release:` and is `Work-Kind: chore`, so no release gate is owed and the every-live-bug rule
does not apply.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-501 | LOW | IN-SCOPE | A. Correctness / E. Testing | Two scripted runs at review on a scratch repo (draft spec + `planned` release + `open` item gated `relaaa`): `status_set.run_set_command` -> wrote `- From-Backlog: bbb111`, inherited `- Blocks-Release: relaaa`, printed the inheritance line, relocated the spec; `specs.run_set` -> rc 0, spec relocated, BOTH bullets ABSENT | THE ASYMMETRY RUNS THE OPPOSITE WAY FROM WHAT THE PLAN ASSUMED ON ONE PATH, and measuring it re-sizes two items. The plan treats both spellings as needing work ("write it ... on BOTH spellings"); the BARE spelling is already complete end to end, so E-01's registration alone finishes it. The `--status` spelling is worse than "has no writer": it returns SUCCESS having silently written nothing the user asked for. That failure mode is invisible to a diff, which is what the original V-02 asked for. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-3 with both measurements. E-01 now states that registration alone completes the bare path and V-01 requires a DRIVEN bare-spelling run, not just a `--help` line. V-02 and V-03 require driven `--status` output, with the reason stated (a diff cannot distinguish a writer that runs from one after an early return). |
| PR-502 | MEDIUM | OVER-SCOPE | B. Security-adjacent policy / C. Architecture (one mechanism, one policy) | `status_set.py` `IT IS A WRITE, NEVER A REFUSAL. Refusing --from-backlog ... would break a link the author is legitimately recording, and check.from-backlog-gate-mismatch already ships at ERROR`; its body calls `blocks_release_of_item` and never `existing_backlog_ids`; `releases.check_from_backlog` ships `check.from-backlog-dangling` at ERROR over plans AND specs | THE PLAN PROPOSES A REFUSAL THE REPOSITORY HAS EXPLICITLY DECIDED AGAINST, and implementing it would RE-CREATE the asymmetry the plan exists to remove. E-02 required validating the id6 and E-03 required refusing an unknown one. `status_set` validates nothing, so a validating `--status` path would leave the two spellings disagreeing about the same flag: one records the link, the other refuses it. The policy also has a stated reason (a refusal breaks a link an author is legitimately recording) and a shipped backstop at ERROR severity, so the validation buys no coverage. | C:Low; U:Medium (a refusal a user does not expect); S:Low; F:Low; Overall:Low (the fix is to NOT build something) | FIXED | E-02's validation clause and E-04's refusal assertion both REMOVED, each with the reason and the citation inline so they are not re-added. Added F-4, OQ-02 (resolved, non-blocking, recording the ruling and both reasons), decision D-2, and a Deferred entry declining validation with a `Carrier-Declined` explaining that nothing is uncovered. Scope now names it OUT. |
| PR-503 | LOW | OVER-SCOPE | C. Architecture / F. Honest documentation | `command_surface.discover_parser_leaves` docstring; `build_matrix`: `report.undeclared = sorted(parser_leaves - declared)`; the single `command="set"` declaration's `legacy_flags` lists none of `--priority`, `--work-kind`, `--graduated-to`; `tests/test_json_and_exitcodes.py` 5 passed untouched | NOTHING IS OWED IN `command_surface.py`, AND ADDING IT WOULD MAKE THE SURFACE LESS HONEST. E-01 called for declaring the flag in `legacy_flags`. That inventory declares parser LEAVES, not flags, and the conformance matrix's hard failure is an undeclared LEAF. One shared `set` declaration serves every record type and omits four sibling field flags, so adding this one alone implies an enumeration that does not exist. The step is traceable to no requirement, which is the definition of over-scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now states the prohibition WITH the mechanism, so it is not re-added by a later reader who assumes a missing declaration is an omission. `agent_workflows/command_surface.py` REMOVED from `- Scope-Paths:`. Added F-5, a Deferred entry with `Carrier-Declined`, and an explicit OUT clause in Scope. |
| PR-504 | MEDIUM | UNDER-SCOPE | A. Correctness / D. Anti-regression | `status_set.py`'s inheritance block: guarded on `fb != "-"` and `blocks_release is None`, skipped when `^- Blocks-Release:` already matches, printing a fixed line; original E-02 bundled "inherit the item's Blocks-Release ... printing the same inheritance line" into a single item with no rules named | THE GATE INHERITANCE HAD NO ITEM OF ITS OWN AND NO PRECEDENCE RULES, so an executor would have written a SECOND inheritance policy that differs from the shipped one in ways no test would name. The shipped implementation carries three rules (explicit flag wins; an existing gate is never overwritten; a missing item is not a refusal), each with a stated reason, and the middle one guards against silently discarding a decision the spec made for itself. A divergent order here is a cross-spelling inconsistency of exactly the class this plan removes, and it concerns a RELEASE GATE, so being wrong means a gate is dropped or overwritten. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Split into E-03, naming all three precedence rules, citing the shipped comment, and instructing the executor to re-read it first. V-03 requires FOUR driven outcomes (inherit + line printed; explicit flag wins; existing gate untouched; `-` clears and inherits nothing). E-04 asserts the same three cases on both spellings. Cohesion rationale states why the write and the inheritance are separate items. |
| PR-505 | LOW | UNDER-SCOPE | F. Honest documentation | `grep -n "from-backlog" AGENTS.md .aw/records/specs/README.md .aw/records/backlog/README.md` -> 4 hits, ALL in AGENTS.md, none in either README; AGENTS.md names `aw ipd set <status> <plan> --from-backlog <id6>` then says a spec is an equally valid carrier; `<!-- /aw:block -->` is at line 123, the sentence at 206 | THE DOC GREP IS KEYED ON A SENTENCE THAT DOES NOT EXIST, so E-04 would have reported a clean no-op over the real defect. No file claims a spec "cannot" record the field; AGENTS.md instead names only a PLAN route and then asserts spec parity, which is `mod4ml`'s asymmetry stated positively. A grep for the denial misses the assertion. The plan also did not establish that the section is editable at all: had it been inside the managed block, the next install would have reverted the fix silently. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into E-05, naming the actual AGENTS.md sentence, requiring the below-the-marker check before editing, requiring the README half be reported as a NO-OP rather than as a fix, and instructing that the adjacent `there is no --from-spec setter yet` sentence be left alone (different field, still true). V-05 requires the diff, the grep, and line-number evidence that no managed block was touched. Added F-6; the managed-block risk is a named stop condition. |
| PR-506 | LOW | IN-SCOPE | A. Correctness / D. Anti-regression | `specs.run_set` reads all four optional fields with `getattr(args, <name>, None)`; `tests/test_specs_verbs.py`'s `_args` builds a Namespace from kwargs only; `tests/test_specs_status_dirs.py` builds a fixed attribute list; 20+ call sites across three test files | A DIRECT ATTRIBUTE READ WOULD BREAK EXISTING TESTS, and the plan named no read form. `specs.run_set` is called throughout the suite with hand-built Namespaces carrying only what each test needs, which is why every optional field uses `getattr` with a default. `args.from_backlog` raises `AttributeError` on every one of those call sites. The plan's own validation would not have caught it either: its test list named only the new file. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 now specifies `getattr(args, "from_backlog", None)` and states the reason. Added F-7. Required tests and V-04 now include `tests/test_specs_verbs.py`, `tests/test_specs_status_dirs.py` and `tests/test_spec_review_attestation.py`, marked REQUIRED with the reason a narrowed run would not exercise them. |
| PR-507 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) | Plan gate as authored: three sentences (commit path, bare suite, per-`V-*` evidence); compare pending plan `afpmdu`'s gate | THE GATE WAS MISSING MOST OF ITS REQUIRED ELEMENTS: no statement of what a human is approving (and one judgement here, OQ-02, genuinely is the maintainer's to overrule), no scope fence enumerating the intended surface within each declared path, no named stop conditions, and an UNCONDITIONAL `aw ipd finalize` instruction, which is wrong under a runner that owns the transition itself. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate: a what-a-human-is-approving paragraph naming OQ-02 as the overrulable judgement; a per-path scope fence stated as a DECLARATION (including the two READMEs declared for ACK rather than edit); an explicitly-not-in-scope list mirroring Deferred; the hard-MUST honesty rule requiring DRIVEN output for V-01..V-03 with the reason; three genuine stop conditions (validator refusal, a managed-block surprise, a README hit contradicting F-6); and the transition with conditional runner/executor ownership plus the `mod4ml` close naming its absent gate. |
| PR-508 | LOW | UNDER-SCOPE | G. Plan executability (right-sizing) | Original E-02 (field write + three-rule gate inheritance + inheritance line) and E-04 (doc grep + bare suite); `aw ipd lint` passed on count | TWO ITEMS BUNDLED INDEPENDENT DELIVERABLES WITH DIFFERENT FAILURE MODES AND DIFFERENT EVIDENCE, which a count-based size lint cannot see. A one-line write carrying no policy and a three-rule inheritance reading a second artifact fail differently; a doc grep and a full-suite run are unrelated test-surfaces. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Six items with a 6:6 E/V bijection: E-01 flag, E-02 write, E-03 inheritance, E-04 tests, E-05 doc, E-06 suite. Cohesion rationale states it is one concern and why E-02/E-03 are separate. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the plan's claim about the two spellings be taken from reading the handlers, or measured? | Measured, by driving both handlers against a scratch repo. | (a) Read the code and trust the plan's characterization - rejected: reading shows `specs.run_set` lacks a writer but NOT that `status_set` already inherits the gate end to end, which is the fact that re-sized E-01 and E-02. (b) Rely on existing tests - rejected: no test covers either behavior, which is why the plan exists. | Two scripted runs at review; the bare spelling wrote and inherited everything, the `--status` spelling returned rc 0 having written nothing | yes |
| D-2 | The plan requires validating the `--from-backlog` id6 and refusing an unknown one. Keep it, or decline it? | Decline. Remove the validation clause and the refusal assertion; record as OQ-02 with the ruling. | (a) Implement it as written - rejected twice over: it contradicts the shipped `IT IS A WRITE, NEVER A REFUSAL` ruling, and since `status_set` validates nothing it would leave the two spellings disagreeing about the same flag, re-creating the defect the plan removes. (b) Add validation to BOTH spellings - rejected as out of scope: it changes shipped behavior on a path this plan was not asked to touch, and reverses a recorded decision. (c) Ask the maintainer - rejected: the repository states both the ruling and its reason in a comment beside the code being extended. | `status_set.py`'s `IT IS A WRITE, NEVER A REFUSAL` comment; `releases.check_from_backlog` ships `check.from-backlog-dangling` at ERROR over specs as well as plans | yes |
| D-3 | Should `--from-backlog` be added to `command_surface.py`'s `legacy_flags` for `set`? | No. Remove the step and the path from `Scope-Paths`. | (a) Add it, as the plan and the source item both suggest - rejected on measurement: the inventory is leaf-scoped, the matrix hard-fails on an undeclared LEAF, and four sibling field flags are equally absent, so adding one implies an enumeration that does not exist. (b) Add all five for consistency - rejected as a surface-wide decision about 132 declarations, unrelated to this plan's concern. | `command_surface.discover_parser_leaves`; `build_matrix`'s `undeclared` computation; the `command="set"` declaration's `legacy_flags` tuple; `tests/test_json_and_exitcodes.py` passes untouched | yes |
| D-4 | E-04's doc grep looks for a denial that does not exist. Drop the doc work, or retarget it? | Retarget it at the real defect: AGENTS.md naming only a plan route while asserting spec parity. | (a) Drop it - rejected: the asymmetry IS a doc defect and is the one `mod4ml` describes; leaving it means the doc keeps directing a spec-first graduation to a plan-only flag. (b) Keep the original grep - rejected: it returns nothing and would be reported as a clean no-op, certifying the defect as absent. | `grep -n "from-backlog"` -> 4 hits all in AGENTS.md, none in either README; the sentence at line 206 versus `<!-- /aw:block -->` at line 123 | yes |
| D-5 | Is `AGENTS.md`'s Release gates section editable by a plan, or is it installer-managed? | Editable: it sits below `<!-- /aw:block -->`. Require the executor to re-verify before editing. | (a) Assume editable and proceed silently - rejected: if wrong, the next install reverts the fix with no trace, so the assumption needs to be checked at execution time, not just at review. (b) Route the correction through the installer's own managed text in `engine.py` - rejected: the sentence is repo-local prose outside every managed block, so the installer does not own it. | `grep -n "aw:block" AGENTS.md` -> markers at 3, 4, 98, 123; the target sentence at 206; `engine.py`'s managed text does not contain it | yes |
