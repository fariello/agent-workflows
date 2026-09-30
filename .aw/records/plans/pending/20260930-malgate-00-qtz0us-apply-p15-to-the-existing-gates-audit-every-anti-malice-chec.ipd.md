# IPD: Apply P15 to the existing gates: audit every anti-malice check and keep, simplify, or delete each

- Date: 2026-09-30
- Kind: orchestrator
- Concern: GUIDING_PRINCIPLES P15 was added on 2026-09-26 ("we guard against honest mistakes, never against a malicious agent") and nothing has yet applied it BACKWARDS to the mechanisms that already ship. P15 closes by obliging any review that touches a gate to keep it, simplify it, or delete it, but a principle applied only at the next accidental touch leaves the existing machinery in place indefinitely, and that machinery has already cost real recovery time: the per-run driver token blocked a human's own feature worktree while its own honest-limits note conceded a same-user agent could read the token file (measured 2026-09-26). Backlog `ariaau` asks for the deliberate sweep, and authoring measured that it cannot be one plan. It needs a RECORD (two of the four decision classes leave no diff at all, so an audit whose only output is code changes cannot show what was considered and kept), it needs a CODE DELETION whose safety rests on a caller census (nine predicates, zero product callers, and a pinning test that turns out not to exist), and it needs a COMMENT REFRAMING whose main hazard is the opposite of the obvious one (the anti-malice vocabulary is densest in the comments that are already compliant). Those three have different subjects, different risks, and different validation shapes.
- Scope: Orchestrate three children that together apply P15 to the shipped gates: `bec7ee` writes the durable audit record enumerating every mechanism with its keep / simplify / delete decision and evidence, `38pxaz` deletes the five unowned raising predicates in `wtiso_gate` plus the dangling test citations that claim they are pinned and amends spec `7ckptx` accordingly, and `dmjp0u` reframes the comment sites whose stated justification for a mechanism is a hostile agent. This plan holds ORCHESTRATION ONLY: every deliverable belongs to a child, and this file contributes no code, no test, no record and no spec edit of its own. EXCLUDES, in every child without exception: the driver attestation token and the `lane_worktree_active` location guess (designed in backlog `dvonrn`), re-deciding the four items backlog `ariaau` marks ALREADY DECIDED, rewording any honest-limit disclaimer that names a hostile agent in order to deny protecting against one, and restoring any test file deleted by the 2026-09-24 suite trim.
- Scope-Paths: .aw/records/plans/pending/20260930-malgate-00-qtz0us-apply-p15-to-the-existing-gates-audit-every-anti-malice-chec.ipd.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: ariaau
- Set: malgate
- Order: 0
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: qtz0us

## Workflow history

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated backlog `ariaau` as a Set of three children rather than one plan, because authoring measured three separable pieces of work with different risk profiles and different validation shapes. TWO MEASUREMENTS CHANGED THE SET'S SHAPE FROM THE ITEM'S DESCRIPTION. FIRST, the item states the `wtiso_gate.py` predicates are "Pinned by tests/test_containment_predicates.py", which implied a plan shape of 'retire the pin, then delete'; that file does not exist, having been deleted in commit `19313eed` (the 2026-09-24 suite trim), so nothing pins them, the module cites two deleted files as live enforcement at three sites, and Order 02's deletion is both smaller and safer than the item implies while gaining a citation strike the item does not mention. SECOND, the item's instruction to find comments "citing a 'determined same-user agent' or 'malicious' agent as the justification for a check" reads as a vocabulary sweep, and measurement inverted it: the large majority of hits are honest-limit DISCLAIMERS that name the hostile agent precisely in order to deny protecting against one, and those are the model P15 itself cites, so Order 03 is narrow and its primary obligation is a classification rather than a replacement. A third measurement widened Order 02: all NINE `wtiso_gate` predicates have zero product callers, not only the five raising stubs, so the honest subject is the module's whole disposition.
- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Apply P15 to every gate that already ships, once and deliberately, leaving a durable record of what was
kept, what was simplified, what was deleted, and why.

WHY THIS IS A SET AND NOT ONE PLAN, since that is the decision this file exists to justify. The three
children are not phases of one change; they are three different kinds of work.

- `bec7ee` produces a RECORD and changes no behavior. It is the item's first named output, and it is the only
  artifact that can show a KEEP decision, because a KEEP produces no diff. Its validation is the completeness
  of an enumeration, and it adds no test by design.
- `38pxaz` DELETES SHIPPED CODE and amends an approved spec. Its safety rests entirely on an AST caller
  census, so its first item is a hard gate that stops the whole Set if a real caller is found. Its validation
  is a full suite run plus a behavioral test for the one property that must survive the deletion.
- `dmjp0u` edits COMMENTS ONLY and can add no conforming test at all, because the only test for a reworded
  docstring is the text pin GUIDING_PRINCIPLES P16 forbids. Its validation is its diffs plus an unchanged
  suite.

Merging them would produce a plan whose deletion is validated by a records document, whose comment edits sit
in the same commit as a spec amendment, and whose single hard gate governs work that does not depend on it.
Splitting them also lets the lowest-risk member carry a lower priority honestly.

THE SEQUENCING, and the one edge that is real. `bec7ee` goes FIRST because both remediation children cite its
audit record by `<id6>` as the evidence for their decisions: a deletion explained only by a commit message is
exactly the unexplained removal this Set exists to avoid. `38pxaz` goes second and declares
`executed:bec7ee`. `dmjp0u` goes last and declares both, because Order 02 deletes prose from `wtiso_gate`
that a naive wording sweep would otherwise try to reframe, so running Order 03 first would produce an edit to
a file about to be deleted. No child depends on backlog `dvonrn`, deliberately: Order 03's E-02 checks
`dvonrn`'s landed state and reconciles either way, and declaring the edge would block a comment fix behind a
release-gating behavior change.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: run the Set in order

- [ ] E-01 CONFIRM bec7ee REACHED executed
  - Depends on: none
  - Expected outcome: `bec7ee` reads `- Status: executed` on disk and is in `.aw/records/plans/executed/`, with every `V-*` carrying concrete pasted evidence.
  - Execution state: pending
  Order 01 writes the durable audit record: every anti-malice mechanism enumerated with its keep / simplify / delete decision, the evidence measured for it, and its carrier. It MUST be first, and the reason is mechanical rather than stylistic: Orders 02 and 03 both cite the record by `<id6>` as the evidence for what they remove and reword, and Order 03's E-01 takes the record's SIMPLIFY rows as the starting point for its own census. Its E-01 is also the Set's hard gate: it measures the `wtiso_gate` caller census, and a real product caller there makes Order 02 unsafe.

- [ ] E-02 CONFIRM 38pxaz REACHED executed
  - Depends on: E-01
  - Expected outcome: `38pxaz` reads `- Status: executed` on disk and is in `.aw/records/plans/executed/`, with every `V-*` carrying concrete pasted evidence.
  - Execution state: pending
  Order 02 deletes the five unowned raising predicates, the helper that builds their error, and the error codes no surviving surface names; re-homes the one constant `lane_containment` actually imports so the import does not dangle; strikes the three citations to two deleted test files; and amends spec `7ckptx`, whose R6.2 and A16 require the raising behavior being removed. It declares `executed:bec7ee` in its own front matter. It is the only child that changes shipped code, and the only one that amends a spec.

- [ ] E-03 CONFIRM dmjp0u REACHED executed
  - Depends on: E-02
  - Expected outcome: `dmjp0u` reads `- Status: executed` on disk and is in `.aw/records/plans/executed/`, with every `V-*` carrying concrete pasted evidence.
  - Execution state: pending
  Order 03 reframes the comment sites whose stated justification for a mechanism is a hostile agent, so each states the honest mistake it actually catches. It declares `executed:bec7ee, executed:38pxaz`: the first because it consumes the audit's SIMPLIFY rows, the second because Order 02 deletes `wtiso_gate` prose that this child would otherwise try to reframe. Comment and docstring text only; it adds no test by design, since the only test for a reworded docstring is the text pin P16 forbids.

## Child IPDs, sequence, and dependencies

| Order | Id | Title | Depends on | Why this order |
|---|---|---|---|---|
| 01 | `bec7ee` | Record the P15 gate audit: every anti-malice mechanism with its keep, simplify or delete decision and evidence | none | The item's first named output, and the only artifact that can show a KEEP (which produces no diff). Both siblings cite its `<id6>` as their evidence, and its caller census is the Set's hard gate. |
| 02 | `38pxaz` | Delete the five unowned raising predicates in `wtiso_gate` and the dangling test citations that claim they are pinned | `executed:bec7ee` | The only child that changes shipped code and amends a spec. Needs the audit's DELETE decision recorded first so the removal is explained by a citable record rather than a commit message. |
| 03 | `dmjp0u` | Reframe every determined same-user and malicious agent justification as the honest-mistake guard it actually is | `executed:bec7ee`, `executed:38pxaz` | Comment-only and lowest risk, so last. Depends on Order 02 because that child deletes `wtiso_gate` prose a wording sweep would otherwise reframe in a file about to be deleted. |

## Completion criteria (the whole Set is done only when)

All five must hold. Each is falsifiable from artifacts on disk, so a reviewer can check them without
re-running anything.

1. ALL THREE CHILDREN READ `executed` ON DISK, in `.aw/records/plans/executed/`, each with every `V-*`
   carrying concrete pasted evidence rather than a placeholder. The directory is the harder-to-forge signal
   and is checked alongside the status field.
2. THE AUDIT RECORD EXISTS AND IS RESOLVABLE BY `<id6>` through the research manifest, and it classifies
   EVERY enumerated mechanism into exactly one of KEEP, SIMPLIFY, DELETE or ALREADY-DECIDED, with evidence
   for each and a carrier for each SIMPLIFY and DELETE.
3. EVERY SIMPLIFY OR DELETE ROW IN THAT RECORD HAS AN ACTOR: it was acted on by `38pxaz` or `dmjp0u`, or it
   names a carrier outside this Set (`dvonrn`, `ikxtkj`, `gia5i7`). A row with a disposition and no actor
   means the Set completed while leaving its own stated work undone, and is the single most likely way this
   Set finishes wrongly.
4. NO USER-VISIBLE BEHAVIOR CHANGED. Evidenced by each child's own bare `python3 -m pytest` summary line
   pasted against its pre-execution baseline, plus `38pxaz`'s demonstration that the preserved missing-input
   token form renders byte-identically before and after its move.
5. NOTHING P15 REQUIRES KEPT WAS REMOVED. `runner_shared`'s pre-work-baseline banner,
   `host_sandbox_profile`'s docstring, and `attention_contract`'s `--by-human` note are unmodified by every
   child, and no test deleted by the 2026-09-24 suite trim was restored in any form.

## Cross-IPD validation

Three checks span the children and cannot be performed by any child alone, which is why they live here.

- THE AUDIT-TO-ACTION RECONCILIATION (criterion 3). Read Order 01's record and Orders 02 and 03's diffs
  together, and confirm every SIMPLIFY and DELETE row maps to an edit or to a named external carrier. Order
  01 cannot check this because the edits do not exist when it runs; Orders 02 and 03 cannot, because neither
  sees the other's rows.
- THE DISCLAIMER FENCE HELD ACROSS BOTH REMEDIATION CHILDREN (criterion 5). Order 02 deletes prose and Order
  03 rewords prose, and the same three compliant sites are off limits to both. Confirm from the combined
  diff of both children that none of them was touched, rather than from either child's own scope check.
- THE SPEC SURFACE IS RECONCILED SET-WIDE. Exactly one child may amend a spec (`38pxaz`, spec `7ckptx`).
  Confirm from the combined diff that no other `.spec.md` file was modified by any child, and that
  `38pxaz`'s amendment left R6.1 intact. Both runners report declared-versus-actual spec edits per item at
  run end, so a spec changed by a child that did not declare one is visible there too.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation in this Set is by symbol or quoted string; `19313eed` is a durable sha.
- AN ORCHESTRATOR HOLDS ORCHESTRATION, NOT WORK OF ITS OWN (AGENTS.md). This file's three `E-*` items are child-confirmation items and nothing else: no deliverable, no baseline established before a child runs, no records reconciliation afterwards. That is deliberate and is what makes the runner's retirement of this plan honest, since a rollup SKIPS the pre-transition E/V checkpoint on the premise that a parent's items are performed by nobody. Every deliverable in this Set is owned by a child, and the orchestrator-coverage gate should find no work here that no child covers.
- A PLAN MAY AMEND A SPEC AND MUST DECLARE IT (AGENTS.md). Exactly one child amends a spec: `38pxaz` declares `.aw/records/specs/approved/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md` in its own `- Scope-Paths:`, because deleting the raising predicates contradicts that spec's R6.2 and acceptance A16 as literally written. This orchestrator declares no spec and no code path.
- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (AGENTS.md; GUIDING_PRINCIPLES P16). Load-bearing across the whole Set rather than in one child. The test this Set deletes the citations to was ITSELF a structure pin (it asserted a zero-caller state "structurally"), the obvious test for Order 02 would be "assert the symbol is gone", and the obvious test for Order 03 would be "assert the docstring says X". All three are forbidden, so each child states what replaces them.
- RESEARCH IS TOOL-NAMED, TOOL-INDEXED, AND CITED BY `<id6>` (AGENTS.md; GUIDING_PRINCIPLES P5). Order 01 creates its record with `aw research new` and refreshes the manifest with `aw research index`, never by hand, which is why its `- Scope-Paths:` carries a glob rather than a guessed filename.
- COMMENTS AND PLANS ARE NOT USER-FACING PROSE (GUIDING_PRINCIPLES P13). The no-dash style convention does not apply to any artifact this Set edits (code comments, docstrings, plans, a research record), so no effort is spent on it.

## Findings

| # | Finding | Evidence | Consequence for this Set |
|---|---|---|---|
| F-1 | The pinning test the backlog item relies on does not exist | `tests/test_containment_predicates.py` and `tests/test_wtiso_adversarial.py` both absent; `git show --stat 19313eed` lists both as deleted | The item's "Pinned by" premise is false. Order 02 shrinks to an unpinned deletion and gains a citation strike; recorded in Order 01's audit |
| F-2 | All nine `wtiso_gate` predicates have zero product callers, not only the five raising stubs | AST walk of every `.py` outside the module: the sole import anywhere is `AW_MISSING_INPUT` into `lane_containment` | Widens Order 02's subject to the module's whole disposition, and makes its caller census the Set's hard gate |
| F-3 | The anti-malice vocabulary is DENSEST in the sites that are already P15-compliant | `runner_shared`'s baseline banner ("THE TARGET IS SLOPPINESS, NOT MALICE"), `host_sandbox_profile` ("explicitly NOT a boundary against a MALICIOUS same-user worker"), `attention_contract` ("NOT anti-malice crypto") | Inverts Order 03 from a sweep into a classification, and makes 'do not reword the disclaimers' an explicit fence in every child |
| F-4 | Two of the four decision classes leave NO diff in the tree | A KEEP produces no change; an ALREADY-DECIDED item produces no change | Justifies Order 01 existing at all: without the record, the Set's output would be deletions whose rationale lives only in commit messages |
| F-5 | One spec names the module and requires the behavior being deleted | `7ckptx` constraints ("the designated home ... a fail-loud skeleton by design"), R6.2, and A16 ("each unimplemented one still raises naming its owner") | Order 02 must amend the spec in the same change; no other child touches a spec |
| F-6 | The item's four ALREADY-DECIDED entries are all still accurate | The driver token is owned by `dvonrn` D1; `--by-human`, the suite baseline and the opt-in sandbox are KEEP per the item and independently confirmed by F-3 | No child re-litigates them; Order 01 records each with its prior decision and citation |
| F-7 | This dangling-citation defect class is already recorded twice, from the same commit | Backlog `ikxtkj` (five doc citations) and backlog `gia5i7` (nine `runner_shared` citations), both citing `19313eed` | The Set cites both rather than filing a third, and Order 02 strikes only the citations inside code it deletes |

## Proposed changes (ordered, validatable)

1. Confirm `bec7ee` reached `executed`: the audit record exists, is indexed, and every mechanism carries a decision and evidence (E-01).
2. Confirm `38pxaz` reached `executed`: the predicates and unreferenced codes are gone, the consumed constant is re-homed with a byte-identical token form, the dangling citations are struck, and spec `7ckptx` is amended (E-02).
3. Confirm `dmjp0u` reached `executed`: the justification sites are reframed, every genuine limitation preserved, and no disclaimer touched (E-03).

## Deferred / out of scope (with reason)

- THE DRIVER ATTESTATION TOKEN, `verify_driver_attestation`, `DRIVER_ATTEST_ENV`, and `lane_worktree_active`'s location guess. The largest anti-malice mechanism in the tree, and backlog `ariaau` marks it ALREADY DECIDED and explicitly out of scope; its replacement is designed in backlog `dvonrn` D1/D2, which carries `Blocks-Release: next`. Order 01 records it with that disposition so the audit does not read as having missed it.
  - Carrier: dvonrn
- RE-DECIDING `--by-human`, THE SUITE-BASELINE ADJUDICATION, AND THE OPT-IN HARDENED SANDBOX. The item marks all three KEEP, and F-3 independently measured the first two as P15's own cited model. Recording them is in scope (Order 01); reopening them is not.
  - Carrier-Declined: Nothing is owed because no latent work exists. Each is already in the state P15 wants, and filing an item would assert the repository intends to revisit a decision it does not.
- THE DANGLING CITATIONS OUTSIDE THE CODE THIS SET DELETES (F-7). Filed and itemized already, by line, in two separate items.
  - Carrier: ikxtkj, gia5i7
- RESTORING ANY TEST DELETED BY THE SUITE TRIM. Refused on a maintainer ruling rather than deferred: the 2026-09-28 ruling recorded on backlog `gia5i7` says code-pinning guards deleted in the trim "will not be restored" and stale comments should "simply remove references to them without seeking to restore code pins". F-1's `wtiso_gate` pin was exactly such a guard, since it asserted a zero-caller state structurally.
  - Carrier-Declined: Nothing is owed because there is no latent work, only a constraint measured as withdrawn. Filing it would assert the repository intends to restore a pin its maintainer has ruled against and which AGENTS.md and P16 forbid.
- RE-IMPLEMENTING ANY DELETED PREDICATE AS A WORKING GATE. `check_hook_bypass` calls the driver-side re-check "an open gap" and `check_protected_refs` names snapshot diffing as absent, so each reads as unfinished work. Under P15 they are rejected designs rather than gaps: each targets an agent deliberately evading a gate, and P15 records such defenses as "futile by construction".
  - Carrier-Declined: Nothing is owed because filing a carrier would assert the repository intends to build a mechanism its own guiding principle forbids. Order 01's audit records the DELETE decision and its reasoning, which is the durable answer to a future reader who finds the gap.
- A DETERMINISTIC CHECKER RULE FLAGGING NEW ANTI-MALICE JUSTIFICATIONS. Attractive under GUIDING_PRINCIPLES P11 and refused on this Set's own measurement: F-3 shows the vocabulary is densest in the COMPLIANT sites, so a pattern rule would fire overwhelmingly on correct code, and the justification-versus-disclaimer distinction is a judgement made by reading.
  - Carrier-Declined: Nothing is owed because this is a rejected design rather than latent work. Filing it would imply the repository intends to build a rule whose false-positive behavior its own measurement predicts.

## Scope check

- Over-scope: none. This file declares ONLY itself, which is the correct declaration for a plan that performs no product change: it holds three child-confirmation items and a child table, and contributes no code, test, record or spec edit. Every deliverable is owned by a child, so the orchestrator-coverage gate should find no work here that no child covers.
- Under-scope: no code path, test path, spec path or records path is declared here, deliberately. `agent_workflows/wtiso_gate.py`, `agent_workflows/lane_containment.py`, spec `7ckptx` and the new token test belong to `38pxaz`; `agent_workflows/ipd_lifecycle.py` and `agent_workflows/orchestrate_isolation.py` belong to `dmjp0u`; the research record and its manifest belong to `bec7ee`. Each child declares its own fence, so a scope reconciliation at finalize measures the right file set per item rather than one union that hides which child changed what.

## Required tests / validation

- THIS PLAN RUNS NO TEST OF ITS OWN, because it performs no product change; each child carries its own test obligations and its own evidence. Stated explicitly so the runner's retirement of this plan is not read as an untested transition: retirement is gated on every child reaching `executed`, and each child's own pre-transition checkpoint is where the evidence lives.
- E-01 is satisfied by `bec7ee` on disk in `.aw/records/plans/executed/` with `- Status: executed`, its audit record present and resolvable by `<id6>` through the research manifest.
- E-02 is satisfied by `38pxaz` on disk in `.aw/records/plans/executed/` with `- Status: executed`, its full-suite result pasted in its own validation, and its spec amendment reconciled against its declared `- Scope-Paths:`.
- E-03 is satisfied by `dmjp0u` on disk in `.aw/records/plans/executed/` with `- Status: executed`, its diffs shown to change comment text only.
- THE SET-LEVEL CROSS-CHECK a reviewer should apply, since no child can apply it alone: every mechanism enumerated in Order 01's audit with a SIMPLIFY or DELETE disposition must be either acted on by Order 02 or Order 03, or carry a named carrier outside this Set. An audit row with a disposition and no actor is the one way this Set can complete while leaving its own stated work undone.

## Spec / documentation sync

- EXACTLY ONE SPEC IS AMENDED IN THIS SET, and not by this file. `38pxaz` declares spec `7ckptx` in its own `- Scope-Paths:` and amends its constraints bullet, R6.2 and acceptance A16, because deleting the raising predicates contradicts A16 as literally written (F-5). That child states the reason in its own spec-sync section. It leaves R6.1 (one predicate per rule, no forking) UNTOUCHED, which it HONORS by re-homing the one consumed constant rather than duplicating it.
- NO OTHER SPEC IS TOUCHED BY ANY CHILD, and this is a measured claim rather than an assumption. Backlog `dvonrn` D8 already searched every `.spec.md` for the token, the location guess, the refusal code and the role vocabulary, and recorded that the per-run token and the location guess "are specified in NO spec" and that `7ckptx` R4.5's honest-limit wording "already matches P15 and stays". Orders 01 and 03 each re-confirm the specs tree is unaffected in their own validation.
- GUIDING_PRINCIPLES.md IS NOT EDITED BY ANY CHILD. P15 already exists and already cites the design this Set implements; the Set APPLIES the principle rather than amending it. Stated because "update the principle" is a plausible misreading of a Set whose subject is that principle.
- NO CHANGELOG ENTRY FOR ANY CHILD. Order 01 adds a records document; Order 02 deletes symbols that F-2 shows are unreachable from any shipped path and preserves the one consumed token form byte-identically; Order 03 edits comments. No user-visible behavior changes anywhere in the Set.
- THE AUDIT RECORD IS THE SET'S DURABLE EXPLANATION, which is why it is Order 01 rather than a closing summary. A deletion or a reworded comment with no citable record of why invites the next author to revert it, and a diff is not a place to argue a principle.
- HISTORICAL RECORDS ARE LEFT ALONE BY EVERY CHILD. Executed plans `8zgybk` (created `wtiso_gate`), `604wra` (implemented four of its bodies and asserted the stubs stay raising), `1o4eif` (the opt-in sandbox) and `u27oh3` (the token) all describe the arrangements this Set changes. The plan contract forbids changing what an executed record records.

## Open questions

### OQ-01: Should the audit record be written before the remediation, as sequenced, or assembled from the children afterwards?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: The Set sequences the record FIRST, and the reason is that both remediation children cite it by `<id6>` as the evidence for what they remove: a citation cannot point at a record that does not yet exist, and a deletion explained only by a commit message is the unexplained removal this Set exists to avoid. Order 01's caller census is also the Set's hard gate, which must run before Order 02 acts on it. Against that: writing the audit first means its DELETE rows predict what the children will do, and if Order 02 legitimately decides to keep a body (its own OQ-01), the record and the tree disagree until someone reconciles them. NOT BLOCKING because Order 02's V-03 requires it to RECORD its per-body decision and reason, so the divergence is captured where a reader will find it, and a research record's status and content can be amended without breaking an id6 citation (GUIDING_PRINCIPLES P5).
- Carrier-Declined: No carrier is owed under either answer. Both orderings are fully realizable with the three children as written, and neither leaves a deliverable unbuilt; only the sequence changes.

### OQ-02: Should this Set declare a dependency on backlog `dvonrn` landing first?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: No child declares such an edge, deliberately. `dvonrn` carries `Blocks-Release: next` and deletes the driver token from `ipd_lifecycle`, a neighbourhood Order 03 also edits, so an edge would be defensible. It is refused because it would block a comment-only fix behind a much larger release-gating behavior change, and because Order 03's E-02 explicitly checks `dvonrn`'s landed state and reconciles in EITHER order, requiring its reframed wording to survive the token's later deletion without a second edit. The residual risk is an ordinary text collision in one neighbourhood of one file, which the runner's isolated-worktree and merge-revalidate path already handles. Against that: running after `dvonrn` would be simpler, since part of Order 03's target list may already be fixed and that child would shrink.
- Carrier-Declined: No carrier is owed under either answer. Order 03's E-02 handles both landed states inside the plan, so nothing is left unbuilt in either order, and its V-02 records which state was found.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `bec7ee`'s path shown to be under `.aw/records/plans/executed/` with `- Status: executed`, and its own `V-01` through `V-05` shown to carry concrete pasted evidence rather than placeholders. Plus the audit record's `<id6>` and a pasted `aw research index --check` confirming it is resolvable through the manifest. Plus the explicit outcome of that child's hard gate: whether any product caller of any `wtiso_gate` predicate was found. If one was, E-02 must NOT be confirmed and the Set stops here.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `38pxaz`'s path shown to be under `.aw/records/plans/executed/` with `- Status: executed`, and its own `V-01` through `V-06` shown to carry concrete pasted evidence. Plus, quoted from that child's record: the pasted bare `python3 -m pytest` summary line, the BEFORE and AFTER rendered value of the preserved token form shown byte-identical, and the spec `7ckptx` diff showing R6.1 unchanged. A child marked executed whose token form changed or whose spec amendment is absent does NOT satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `dmjp0u`'s path shown to be under `.aw/records/plans/executed/` with `- Status: executed`, and its own `V-01` through `V-04` shown to carry concrete pasted evidence. Plus, quoted from that child's record: its classified census showing `runner_shared`'s baseline banner, `host_sandbox_profile`'s docstring and `attention_contract`'s `--by-human` note each classified DISCLAIMER and left untouched, and its demonstration that every genuine limitation survived the reframing. Plus the SET-LEVEL CROSS-CHECK: every SIMPLIFY or DELETE row in Order 01's audit is either acted on by Order 02 or Order 03 or carries a named carrier outside this Set; list any row that is not and name its carrier.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries NO `- Readiness:` field, whose absence is deliberate: that field is
an output of `/plan-review` and writing it at authoring time would forge the attestation a gate reads.

This plan performs NO product change. It exists to sequence three children and to record why they are three
rather than one. An executor reaching this file directly should execute the children in Order (`bec7ee`,
then `38pxaz`, then `dmjp0u`), respecting each child's declared `Item-Dependencies`, and then confirm each
`E-*` here from the child's state ON DISK rather than from memory of having run it. Under `aw oc run` or
`aw agy run` this plan is retired automatically once every child reads `executed`, spending no agent turn.

THE ONE WAY TO GET THIS SET WRONG is to treat the anti-malice vocabulary as the target. This repository's
honest-limit style NAMES a hostile agent deliberately, in order to state plainly that a mechanism does NOT
stop one, and F-3 measured that those disclaimers are where the vocabulary is densest. They are what P15
holds up as correct, and `runner_shared`'s baseline banner even forbids anyone to "improve" its load-bearing
sentence away. A child whose diff touches that banner, `host_sandbox_profile`'s docstring, or
`attention_contract`'s `--by-human` note has inverted the principle: it would delete the record of what this
repository does not defend against, which is the honest half of P15 and the more valuable one.

A SECOND WAY TO GET IT WRONG is to be helpful about the missing tests. Two test files this Set's subject code
cites do not exist, and the instinct is to write them. Do not. One was an AST caller census, which AGENTS.md
and GUIDING_PRINCIPLES P16 forbid outright and which the maintainer has ruled will not be restored; the other
proved a premise for a gate this Set is deleting on principle. Every child states what evidence replaces
them.

Backlog item `ariaau` is this Set's origin (`- From-Backlog: ariaau`), and every child carries the same
field. That item carries NO `- Blocks-Release:` gate and none is invented here or in any child. The `chore`
classification is inherited and CONFIRMED by measurement rather than assumed: F-2 shows every symbol Order 02
deletes is unreachable from any shipped path, Order 01 adds a records document, and Order 03 edits comments,
so nothing a user perceives changes anywhere in the Set. The cost this closes falls on the next author who
meets a raising stub, a citation to a deleted test, or an anti-malice justification and takes any of them as
the house style.
