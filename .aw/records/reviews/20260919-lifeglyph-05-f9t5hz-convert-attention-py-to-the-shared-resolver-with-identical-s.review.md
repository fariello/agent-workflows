# Review findings: plan f9t5hz

- Subject-Id: f9t5hz
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `7e002486`. The plan on disk was byte-identical to the sealed lane input (`diff`
empty) and `git status --porcelain` was clean, so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author --agent` reported `clean`, 0 findings, exit 0, before and after
the revisions.

THE TARGET AND THE SEQUENCING ARE RIGHT, AND THE DUPLICATION IS WORSE THAN THE PLAN CLAIMED. The plan
described `attention.py` as duplicating the lifecycle palette. I measured it and it is CONTRADICTING
it: 13 of the 18 statuses this board shares with spec Section 5 carry a different color from the one
the spec mandates (`active` 39->220, `approved` 46->45, `blocked` 203->208, `done` 244->46,
`implementing` 51->220, `open` 40->45, `planned` 40->45, `reference` 244->46, `reusable` 39->81,
`reviewed` 226->135, `superseded` 240->244, `to-review` 214->39, `todo` 44->45). That strengthens the
plan's own case and it is also what makes E-04's assertion churn large rather than cosmetic.

Every finding here is UNDER-SCOPE or a factual correction. That pattern is worth naming because it is
the second consecutive plan in this Set with it: this plan understated what it must touch, and an
understated plan is the dangerous kind, because it executes cleanly, passes its own validation, and
leaves a release-gating criterion unmet with every box ticked.

**1. The plan's headline defect is not reachable, and the real one is narrower (PR-502).** F-01 said
the "silent gray fallthrough" means "any status absent from the local table currently renders
indistinguishably from `parked`". An absent status cannot reach those render sites at all:
`attention_contract.class_of` is PURE and TOTAL over each tree's enum and RAISES `UnknownNativeStatus`
for anything else, which the scanner converts into an `attention.unknown-status` violation (the
releases path returns no `Item`). Verified by execution: `class_of("plans","bogus-status")` raises. So
E-03 would have implemented, and V-03 would have demanded pasted evidence for, an UNREACHABLE
`?`-plus-diagnostic row. Meanwhile the genuinely broken cases went unnamed. Diffing every tree's
`CLASS_MAPS` against the table gives exactly three:

```text
plans    auto-approved -> class ready  -> renders 40   spec 6.1 says stage `ready`
backlog  graduated     -> class active -> renders 39   spec 6.3 says stage `active`
research archive       -> class parked -> renders 244  spec 6.4 says stage `parked`
```

Only the third is actually gray; the other two borrow a CLASS color, which is a wrong-color defect and
not a gray-indistinguishability one. E-03 now fixes those three and V-03 explicitly forbids fabricating
a bogus-status row.

**2. A second live A10 violation that no plan in the Set owned (PR-503).** The artifact TYPE column is
colored today: `attention.py:2227` and `:1898` wrap the type word in `color256(..., _TREE_COLOR_256,
bold=True)`. Measured from real output, an `approved` row emits `^[[1;38;5;33mplan^[[0m` beside
`^[[1;38;5;46mapproved^[[0m`. Spec Section 9.1 says "the artifact type and title do not inherit
lifecycle color" and Section 11 item 5 limits color to glyph, id6 and status "except for an existing
independent convention". `_TREE_COLOR_256` IS such a convention for the tree SEGMENT OF A PATH
(`attention.py:1729`), but a bare type word in a row is not a path, so stretching the exemption there
makes A10 untestable. `grep -l _TREE_COLOR_256` across all eight `lifeglyph` children matched NOTHING
before this review. A reviewer testing A10 against a "conforming" implementation would have failed it.

**3. Deleting a private symbol breaks a test in an undeclared file (PR-504).**
`tests/test_term.py:127-136::test_status_palette_consistency_with_attention` does `from
agent_workflows import attention as att` and iterates `att._STATUS_COLOR_256.items()`. E-01 removes
that attribute. Verified: the test passes today, and removing the attribute raises `AttributeError`,
not a value mismatch, so it would not read as an expected palette change. `tests/test_term.py` was not
in `- Scope-Paths:`. The right fix is to RETIRE the test rather than rewrite it, because its purpose is
to catch two tables drifting and after this child there is only one table; E-01 now requires that
choice be made and justified in the same commit.

**4. The assertion churn spans two files, and one of them must NOT be recomputed (PR-506).**
`tests/test_attention.py` holds 15 hardcoded escape assertions and
`tests/test_attention_priority_blocker.py` holds 2. Both are now declared. But
`:54`/`:67` assert `38;5;196` for a PRIORITY value, not a lifecycle status, so recomputing them against
Section 5 would fold priority into lifecycle styling, which Section 3 forbids. V-04 now requires an
explicit statement that they were checked and left alone.

WHAT I RESOLVED RATHER THAN ASKING. OQ-01 asked whether `_CLASS_COLOR_256` is in scope for removal. The
code answers it: its five keys are the `A.*` attention CLASS constants and Section 3 lists attention
classes as an explicit non-goal, so it stays; parent `2xz59a` reached the same conclusion independently.
I left the E-item rather than deleting it, because the obvious check is a TRAP worth recording (PR-505):
all five class keys are BARE STRINGS equal to native status words (`'active'`, `'ready'`, `'blocked'`,
`'done'`, `'parked'`) with IDENTICAL colors in both tables today and zero class-only keys. An agent
testing "do these keys look like statuses?" gets YES for all five and deletes a protected vocabulary.
And retention is not the whole answer: the class RUNG must still leave the three lifecycle chains,
because the palettes diverge after conversion, and since they are identical today that removal is
invisible in output, so V-02 must prove it from the code.

I also checked whether the `lanes` tree is a sixth orphan of the kind that blocked `udgilu`. It is not:
`CLASS_MAPS` defines `lanes` with five uppercase states appearing zero times in the spec, but lanes join
at RENDER time as `Drift` rows and never become an `Item`, so they never reach a lifecycle site. Spec
Section 12a's claim that `pr5b0t` "adds no status this spec must cover" is confirmed rather than assumed,
and it is now recorded in Deferred so the next reader does not re-open it.

Two smaller things. All four line numbers in the plan were stale by +32, because commit `f3db5649`
landed after authoring; they were RIGHT when written, which is exactly why E-01 now mandates grep over
quoted numbers. And a new glyph column would be padded by this file's universal bare-`len()` idiom,
which leaves a VS-bearing cell one rendered column short (`⚠︎` -> 3 where `◕` -> 4), the same defect
`bn026f` F-05 fixes; E-03 now consumes that shared primitive, which Section 9.4 requires.

Suite baseline at review HEAD, run bare: `7468 passed, 3 skipped, 2 xfailed in 112.27s`. This DIFFERS
from the `8369 passed` recorded in sibling `bn026f` one commit earlier; the lane was rebased between the
two reviews (46 test files changed, 2 net removed), so the plan now carries this number with a note not
to compare across the rebase.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-501 | MEDIUM | IN-SCOPE | A. correctness; G. executability | Authored `1403/1852/1997/2160`; measured at review `1435/1884/2029/2192`; commit `f3db5649` (`0ta5vg`) landed after authoring and inserted 32 lines; `attention.py` now 3352 lines | All four line numbers in Concern, Step 0 and E-01 had drifted +32 and were stale by review time. They were correct when written, so the defect is the citation STYLE, not the author's care: a quoted line number in a 3352-line high-traffic file cannot survive to execution | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All numbers corrected with the drift and its cause recorded; E-01 and Step 0 now mandate locating sites by `grep -n`; V-01 requires the grep as evidence |
| PR-502 | HIGH | IN-SCOPE | A. correctness; E. verification | Verified by execution: `class_of("plans","bogus-status")` raises `UnknownNativeStatus`; `attention_contract.py:408-425`; `attention.py:899-909` (releases catches, returns no `Item`); diffing `CLASS_MAPS` vs the table yields exactly `plans/auto-approved`->40, `backlog/graduated`->39, `research/archive`->244 | F-01's premise was wrong: an unmapped status cannot reach a render site because `class_of` is TOTAL and raises. So E-03 would have built, and V-03 demanded evidence for, an unreachable `?`-plus-diagnostic row, while the three statuses that genuinely miss the lifecycle table went unfixed and two of them render a borrowed CLASS color rather than gray | C:Low; U:Medium; S:Low; F:Medium-High; Overall:Medium | FIXED | F-02 records the correction with the measurement; E-03 now fixes the three named statuses; A20's unreachable case moved to Deferred with `Carrier: 9zvl2w`; V-03 explicitly forbids fabricating a bogus-status row |
| PR-503 | HIGH | UNDER-SCOPE | B/F. accessibility and UX; D. anti-regression | `attention.py:2227` and `:1898` (`term.color256(..., _TREE_COLOR_256, bold=True)`); `_TREE_COLOR_256 = 33` at `:1460`; path-segment convention at `:1729`; measured `FORCE_COLOR=1` output `^[[1;38;5;33mplan^[[0m` beside `^[[1;38;5;46mapproved^[[0m`; `grep -l _TREE_COLOR_256` across all eight children matched nothing | A second live criterion A10 violation owned by NO plan in the Set: the artifact TYPE column is colored, which Section 9.1 and Section 11 item 5 forbid. The Section 11 "existing independent convention" exemption covers the tree segment of a PATH, not a bare type word, so relying on it would make A10 untestable | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | E-03 now requires dropping the type column's color or justifying it in writing as the exemption; F-03 records it; V-03 item 2 demands the negative escape evidence contrasted against current output; Spec sync records that keeping it would need a spec amendment |
| PR-504 | HIGH | UNDER-SCOPE | D. anti-regression; G. executability | `tests/test_term.py:127-136::test_status_palette_consistency_with_attention`; verified it passes today and that deleting the attribute raises `AttributeError: module 'agent_workflows.attention' has no attribute '_STATUS_COLOR_256'`; original `- Scope-Paths:` omitted the file | E-01 removes a private symbol that a shipped test in an UNDECLARED file imports and iterates. It fails as a hard import-time error rather than a value mismatch, so it cannot be mistaken for an expected palette change, and the executor would hit it with no mandate to touch the file | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | `tests/test_term.py` added to `- Scope-Paths:`; E-01 records the breakage with the measured error and requires the test be retired (its purpose is satisfied once one table remains) or re-pointed, in the same commit; V-01 demands the disposition and a clean focused run |
| PR-505 | MEDIUM | IN-SCOPE | A. correctness; C. architecture | Verified: `A.ACTIVE='active'`, `A.READY='ready'`, `A.BLOCKED='blocked'`, `A.DONE='done'`, `A.PARKED='parked'`; all five are keys of `_STATUS_COLOR_256` with identical codes; zero class-only keys; spec Section 3 non-goal; parent `2xz59a` concurs | E-02 asked the executor to determine whether `_CLASS_COLOR_256` is a lifecycle table, but the obvious test fails: all five keys are bare strings identical to native status words with identical colors today, so a key-shape check answers "lifecycle" and deletes a vocabulary Section 3 protects. Retention is also only half the answer, since the class RUNG must still leave the lifecycle chains, and because the palettes match today that removal is invisible in output | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | OQ-01 resolved; E-02 now states the determination with the `A.*` trace, records the bare-string trap, and requires removing the rung while retaining the table; V-02 requires code evidence rather than a board diff, with the reason |
| PR-506 | MEDIUM | UNDER-SCOPE | E. testing and verification | `tests/test_attention.py:242,877-879,1712-1724,1818-1824` (15 assertions); `tests/test_attention_priority_blocker.py:54,67` (2, both `38;5;196` for `high` priority); 13 of 18 shared statuses change color; original `- Scope-Paths:` named only `tests/test_attention.py` | E-04 called this a snapshot update. The real work is recomputing hardcoded escape assertions across TWO files, one undeclared, and two of the undeclared file's assertions are PRIORITY colors that must NOT change; recomputing them against Section 5 would fold priority into lifecycle styling, which Section 3 forbids | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Both files declared; E-04 records the 13 measured color changes and the two-file split with the priority caveat; V-04 requires the explicit statement that `:54`/`:67` were checked and left unchanged |
| PR-507 | MEDIUM | UNDER-SCOPE | A. correctness; F. UX | Measured: `⚠︎` (U+26A0 U+FE0E) padded to width 4 by `len()` -> 4 code points, 3 rendered columns, versus `◕` -> 4 and 4; padding sites `attention.py:1886, 2198, 2230, 2368` and more; spec Section 9.4 forbids per-renderer width guesses; `bn026f` F-05 owns the shared primitive | Adding a glyph column means padding it, and every column in this file pads with bare `len()` on unstyled text, which miscounts a variation selector and leaves a VS-bearing cell one rendered column short. Unaddressed, the first view converted would visibly misalign on exactly the glyphs the spec mandates | C:Low; U:Medium; S:Low; F:Medium; Overall:Low | FIXED | E-03 now requires padding by rendered width via `bn026f`'s primitive with the measurement inline; a local helper is listed in Deferred as spec-forbidden; V-03 item 4 demands the two-cell comparison; the gate makes a missing primitive a stop-and-report condition |
| PR-508 | LOW | UNDER-SCOPE | E. verification; G. executability | Measured `aw attention --agent` and `--json` -> 0 ANSI bytes each; baseline `7468 passed, 3 skipped, 2 xfailed` at `7e002486` versus `bn026f`'s `8369` one commit earlier (lane rebased, 46 test files changed); plan gate (original two paragraphs) | No suite baseline was recorded; A14 was framed as a gap when it is already satisfied (so it needs pinning, not fixing); and the gate lacked a scope fence, the honesty rule, the open-question disposition, and prescribed a `git mv` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Baseline recorded with the cross-rebase warning; A14 restated as a characterization test in E-04 and Required tests; gate now carries the fence (naming `_CLASS_COLOR_256`, `attention_contract.py`, `term.py` and local width helpers as forbidden), the honesty MUST including the no-fabricated-`?`-row rule, both questions' disposition, one stop condition, and conditional `aw ipd finalize` |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01: is `_CLASS_COLOR_256` a duplicate lifecycle table to delete, or the attention class vocabulary to keep? | KEEP IT, and additionally remove its RUNG from the three lifecycle fallback chains. Resolved at review rather than left to execution. | (a) Leave the question open as authored: rejected, the code answers it and an open question invites the executor to re-derive it under time pressure using exactly the key-shape test that gets it wrong. (b) Delete the table: rejected, its keys are the `A.*` class constants and Section 3 lists attention classes as an explicit non-goal, so R10.3 does not reach it. (c) Keep it and leave the fallback rung in place: rejected, the two palettes are identical today but diverge after conversion, so the rung would silently reintroduce the class palette into lifecycle rendering on the first miss. | `attention.py:1428-1434` keyed on `A.ACTIVE/READY/BLOCKED/DONE/PARKED`; spec `uonrjg` Section 3 non-goal; R10.3 scopes removal to LIFECYCLE tables; parent `2xz59a` recorded the same determination; measured that all five keys are bare strings also present in `_STATUS_COLOR_256` with identical codes and that there are zero class-only keys. | yes |
| D-2 | The artifact TYPE column is colored. Is that the Section 11 "existing independent convention" exemption, or an A10 violation? | TREAT IT AS AN A10 VIOLATION to fix, while requiring the executor to report rather than silently decide if it concludes otherwise. | (a) Accept it as the exemption: rejected, `_TREE_COLOR_256`'s convention is for the tree SEGMENT OF A PATH (`attention.py:1729`), and a bare type word in a row is not a path; accepting it would make A10 ("titles and paths are not lifecycle-colored... type does not inherit") untestable on the first view converted. (b) Escalate as blocking: rejected, Section 9.1 and Section 11 item 5 answer it as written, so no contract question is open and nothing irreversible turns on it. (c) Leave it unmentioned as the plan did: rejected, it is a live violation of a release-gating criterion that no plan in the Set owned. | Spec Section 9.1 ("The artifact type and title do not inherit lifecycle color"); Section 11 item 5; `attention.py:2227`, `:1898`, `:1460`, `:1729`; measured output `^[[1;38;5;33mplan^[[0m`; `grep -l _TREE_COLOR_256` across all eight children matched nothing. | yes |
| D-3 | Criterion A20 requires a `?`-plus-diagnostic render for an unrecognized status. Does this board owe it? | NO. Record it as unreachable here and carry the obligation to `9zvl2w`, keeping the resolver's A20 duty with `udgilu`. | (a) Keep A20 in E-03 as authored: rejected, verified `class_of` raises before any render site, so the code path does not exist and V-03 would have demanded evidence an honest executor could not produce, pushing them toward fabricating output. (b) Add a bypass so an unmapped status CAN reach the renderer, to satisfy A20 here: rejected outright, that would defeat the `attention.unknown-status` violation the contract exists to raise and would be a lifecycle change Section 3 excludes. | Verified by execution that `class_of("plans","bogus-status")` raises `UnknownNativeStatus`; `attention_contract.py:408-425`; `attention.py:899-909`; spec criterion A20 and R10.4 assign the duty to the resolver; Section 3 non-goal on transition rules. | yes |
| D-4 | The `lanes` tree has five states absent from the spec. Is this a sixth orphan mapping like `udgilu`'s `integration-deferred`, which was escalated as blocking there? | NO. Not a lifecycle surface; recorded in Deferred as confirmed rather than escalated. | (a) Escalate as blocking by analogy with `udgilu` PR-203: rejected after checking the mechanism rather than the surface resemblance - `integration-deferred` is a RUNNER ITEM STATUS that Section 7.2 must cover and that reaches a lifecycle display, whereas the lane states never become an `Item` and render only as `Drift` rows, so the spec owes them no stage. (b) Say nothing: rejected, the question is the right one to ask and an unrecorded answer invites a later reviewer to re-open it; spec Section 12a asserts the conclusion without evidence, which is now supplied. | `attention_contract.CLASS_MAPS['lanes']` = `EMPTY/LANDED/LIVE/STRANDED/UNKNOWN`, all appearing 0 times in the spec; `class_of` is called with only `plans/specs/backlog/research/releases`; `attention.py:1174` ("lanes join at RENDER time from the run records, not as scanned files") and `:3027-3033`; spec Section 12a on `pr5b0t`. | yes |
| D-5 | `tests/test_term.py`'s palette-parity test reads the symbol E-01 deletes. Rewrite it, or retire it? | RETIRE (or re-point), executor's choice, but the choice must be stated and justified in V-01. | (a) Rewrite it to compare the shared resolver against itself: rejected as tautological, since the test exists to catch TWO tables drifting and after this child only one remains. (b) Leave it and let the executor discover the `AttributeError`: rejected, the file was not in scope so they would have no mandate to fix it, and the error surfaces at import as an `AttributeError` rather than as a palette mismatch. (c) Decide retire-versus-re-point myself: declined deliberately; both are conforming and the distinction depends on whether the shared resolver ends up with a comparable public surface, which `bn026f`/`udgilu` determine. | `tests/test_term.py:127-136`; verified the test passes today and that removing the attribute raises `AttributeError`; the test's own docstring-free intent is a cross-module parity check, which R10.3's single-table outcome makes moot. | yes |
