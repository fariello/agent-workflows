# IPD: Record the P15 gate audit: every anti-malice mechanism with its keep, simplify or delete decision and evidence

- Date: 2026-09-30
- Kind: child
- Concern: GUIDING_PRINCIPLES P15 was added 2026-09-26 ("we guard against honest mistakes, never against a malicious agent") and nothing has yet applied it to the gates that already ship. Backlog `ariaau` asks for a DURABLE RECORD listing every mechanism found with a keep / simplify / delete decision and the evidence behind it, and that record is the item's first named output. Without it the two remediation children in this Set are unexplained deletions: a future reader meeting a removed predicate or a reworded comment cannot tell whether P15 was applied deliberately or whether a guard was lost by accident. The audit is also the only artifact that records the mechanisms judged KEEP, which is the half no code change will ever show.
- Scope: Write ONE research decision record under `.aw/records/research/` enumerating every anti-malice mechanism found in the tree, each with its keep / simplify / delete decision, the evidence measured for it, and the carrier that acts on it. Covers the four families backlog `ariaau` names (the `wtiso_gate.py` raising predicates, the `8zgybk` / `x03wgn` adversarial scaffolding, the 'determined same-user' and 'malicious' justifications, and any hook or verb that hides or verifies a secret from an agent) plus whatever the enumeration finds beyond them. EXCLUDES every code, comment, spec and test edit, which belong to Orders 02 and 03; this plan changes no behavior and touches no file under `agent_workflows/`. EXCLUDES re-deciding the four items the backlog item marks ALREADY DECIDED, which are recorded with their prior decision and cited, not reopened.
- Scope-Paths: .aw/records/research/20260930-malgate-01-*.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: ariaau
- Set: malgate
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: bec7ee

## Workflow history

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored while graduating backlog `ariaau`. Every START HERE item in the backlog item was re-measured in this lane rather than inherited, and TWO measurements change the Set's shape. FIRST, the item says the `wtiso_gate.py` predicates are "Pinned by tests/test_containment_predicates.py"; that file DOES NOT EXIST (deleted in `19313eed`, the 2026-09-24 suite trim), so the predicates are pinned by nothing and the module cites a deleted file three times. That converts Order 02 from "delete a pinned guard, which needs the pin retired first" into "delete an unpinned stub and strike its false citations", a materially smaller and safer change. SECOND, the enumeration found the `wtiso_gate` surface is nine predicates with ZERO product callers between them, not five: the four the module documents as REAL are equally uncalled, and the single symbol any other module imports is one string constant. That widens Order 02's subject from the five raising stubs to the module's disposition as a whole.
- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Produce the durable record backlog `ariaau` asks for, so that every mechanism this repository built against
a hypothetical hostile agent is listed once, with its decision, its evidence, and either a carrier that
acts on it or a stated reason it stays.

The record is the deliverable, not a by-product of the code changes. Two of the four decision classes leave
NO trace in the tree: a KEEP produces no diff at all, and an ALREADY-DECIDED item produces no diff either.
If only Orders 02 and 03 ship, the repository ends up with a set of deletions and rewordings whose
rationale lives in commit messages, and the next reviewer who meets `--by-human` or the suite baseline has
to re-derive from scratch whether those were considered and kept or simply missed. P15's closing sentence
("When a review touches an existing gate, apply this principle to it: keep it, simplify it into a clear
refusal, or delete it") makes that re-derivation a recurring cost, which is exactly what a written audit
removes.

FIVE FACTS ESTABLISHED AT AUTHORING, so the executor inherits measurement rather than the backlog item's
diagnosis. Each was measured in this lane; the executor must re-measure rather than copy (E-01).

1. THE `wtiso_gate.py` PINNING TEST DOES NOT EXIST. The backlog item states the five raising predicates are
   "Pinned by tests/test_containment_predicates.py". Neither that file nor `tests/test_wtiso_adversarial.py`
   is present; both were deleted in commit `19313eed` ("test: trim test suite from 9,136 to under 2,000
   tests", 2026-09-24). The module's own docstrings cite them as live pins at three sites. So the claim that
   a deletion must first retire a pin is FALSE, and the module additionally carries the dangling-citation
   defect this repository has already recorded twice (backlog `ikxtkj`, backlog `gia5i7`).

2. EVERY ONE OF THE NINE PREDICATES HAS ZERO PRODUCT CALLERS, including the four the module documents as
   REAL. Measured by walking the AST of every `.py` file outside the module itself for an import of, or an
   attribute access on, `wtiso_gate`: the ONLY import anywhere in the tree is
   `from agent_workflows.wtiso_gate import AW_MISSING_INPUT as _AW_MISSING_INPUT` in `lane_containment`, one
   string constant. No caller reaches `check_scope`, `check_permission_deadline`, `format_missing_input` or
   `parse_missing_input` either, and the latter two are one-line delegations INTO `lane_containment`, i.e.
   the module that imports the constant back out. So the module is a 443-line file whose entire consumed
   surface is one 17-character string.

3. THE FIVE RAISING PREDICATES DO RAISE, AND ARE REACHABLE ONLY BY A DELIBERATE CALL. Confirmed by calling
   each with placeholder arguments: `check_lifecycle_role`, `check_hook_bypass`, `classify_retention`,
   `check_receipt` and `check_protected_refs` each raise `NotImplementedError`. Since fact 2 shows no caller
   exists, no shipped path can reach any of them, so the fail-loud discipline spec `7ckptx` R6.2 requires is
   protecting a caller that does not exist.

4. THE 'MALICIOUS AGENT' JUSTIFICATIONS SPLIT CLEANLY INTO TWO CLASSES, and conflating them would produce
   exactly the wrong edit. Measured across `agent_workflows/`, the phrase family appears in two shapes.
   (a) HONEST-LIMIT DISCLAIMERS that already say the mechanism is NOT a defense against a hostile agent:
   `runner_shared`'s pre-work-baseline banner (four numbered reasons, ending "THE TARGET IS SLOPPINESS, NOT
   MALICE"), `host_sandbox_profile`'s "explicitly NOT a boundary against a MALICIOUS same-user worker",
   `attention_contract`'s "NOT anti-malice crypto", and the `local-forgeable` labels in `work_cmd`. These
   are P15 COMPLIANT ALREADY and are the model the principle cites. (b) JUSTIFICATIONS PROPER, where the
   phrase is offered as the reason a check exists or as the fix for its weakness: `ipd_lifecycle`'s "hard
   enforcement against a determined same-user agent requires an OS sandbox or separate principal
   (`1o4eif`)", which sits beside the driver-attestation token. Class (a) must be LEFT ALONE; class (b) is
   Order 03's subject.

5. THE DRIVER ATTESTATION TOKEN IS OUT OF SCOPE BUT STILL PRESENT, and the audit must say so rather than
   listing it as undecided. `ipd_lifecycle.mint_driver_attestation` / `verify_driver_attestation`,
   `DRIVER_ATTEST_ENV`, the `driver-attest.token` file, its owner-only creation through `private_file`, and
   `tests/test_driver_attestation_gate.py` all still ship. Backlog `ariaau` records the removal as ALREADY
   DECIDED and owned by backlog `dvonrn` (lifegate), explicitly out of scope here. The audit lists it with
   that disposition and that carrier, because an audit that silently omits the single largest anti-malice
   mechanism in the tree would read as having missed it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure the enumeration before writing a word of it

- [ ] E-01 RE-DERIVE THE ENUMERATION IN YOUR OWN LANE, and treat this plan's facts as claims to check rather than inputs to copy. Produce four measured lists. (a) THE CALLER CENSUS for `wtiso_gate`: walk the AST of every `.py` file in the tree except the module itself and report every `Import` / `ImportFrom` naming it and every attribute access on a name bound to it; a plain text grep is NOT sufficient, because the module's own docstrings mention every predicate name and a grep drowns the real callers in prose. (b) THE RAISE CHECK: call each of the nine predicates and record which raise and which return. (c) THE PHRASE CENSUS: search `agent_workflows/` for the case-insensitive family `malicious`, `determined same-user`, `hostile`, `adversarial`, `tamper`, `forge`, `deception`, and classify EACH hit as fact 4's class (a) disclaimer or class (b) justification, with the deciding words quoted. (d) THE ARTIFACT CHECK: for every test file and doc the module or the phrase sites cite, record whether it exists on disk. Record the full result even where it contradicts this plan.
  - Depends on: none
  - Expected outcome: the four pasted lists, plus one explicit sentence per fact 1 through 5 stating whether it reproduced. A fact that fails to reproduce is a finding to record, not a reason to abandon the plan; but if fact 2 fails (a real product caller exists), say so plainly, because Order 02's deletion is then unsafe and this Set must stop.
  - Execution state: pending

- [ ] E-02 CLASSIFY EVERY ENUMERATED ITEM into exactly one of four dispositions, and write the deciding test you applied rather than only the verdict. The four are: KEEP (it catches an honest mistake and its message names the cause and the remedy), SIMPLIFY (the mechanism is worth keeping but its shape or its stated justification is anti-malice and must become a plain refusal with a remedy), DELETE (its only purpose is stopping a deliberately hostile agent, or it guards a caller that does not exist), and ALREADY-DECIDED (the backlog item or a prior maintainer ruling settled it; record the decision and cite it, do NOT re-litigate). Apply P15's own test as the discriminator: ask whether an HONEST actor could trip this, and whether the mechanism would survive an actor who simply edited it. Every DELETE and SIMPLIFY must name the carrier that acts on it (Order 02, Order 03, or a backlog item you file), and every KEEP must state what honest mistake it catches.
  - Depends on: E-01
  - Expected outcome: a complete classification table, one row per enumerated item, with no item left unclassified and every DELETE / SIMPLIFY row carrying a carrier.
  - Execution state: pending

### Task group 2: write the record

- [ ] E-03 CREATE THE RECORD with `aw research new`, never by hand-naming a file: the research tree's naming and its manifest are tool-owned (AGENTS.md; `.aw/records/research/README.md`). Use `--kind` from the contract vocabulary appropriate to a decision record, `--set malgate`, and a slug naming the audit. Then write the enumeration and the classification table from E-01 and E-02 into it. The record MUST carry, for each item: the mechanism named by SYMBOL, its disposition, the evidence measured for it, and its carrier or its keep-reason. It MUST also carry the four ALREADY-DECIDED items from the backlog item (the driver attestation token, `--by-human`, the suite-baseline adjudication, and the opt-in hardened sandbox) with their prior decision and the citation, so a reader can see they were considered.
  - Depends on: E-02
  - Expected outcome: the record file written at the tool-derived path, containing every row from E-02 plus the four already-decided items.
  - Execution state: pending

- [ ] E-04 STATE THE AUDIT'S OWN LIMITS IN THE RECORD, because an audit that reads as exhaustive when it is not is worse than one that admits its edges. Record at minimum: that the backlog item's START HERE list is explicitly "not exhaustive" and what method you used beyond it (the E-01(c) phrase census) together with what that method CANNOT find, namely an anti-malice check whose comments never use the vocabulary; that a DELETE changes behavior other plans or specs may cite, so each removal's reference sweep is the carrier's obligation and is recorded as such; and that the classification is a JUDGEMENT a reviewer may dispute, with the deciding test written down so the dispute can be about the test rather than about a verdict.
  - Depends on: E-03
  - Expected outcome: a limits section in the record naming at least those three, each stated as a limit rather than as a hedge.
  - Execution state: pending

- [ ] E-05 REFRESH THE RESEARCH MANIFEST with `aw research index` so the new record is discoverable by id6, and confirm with `aw research index --check` that the tree and the manifest agree. Do not hand-edit the index (AGENTS.md). DO NOT COMMIT THE MANIFEST and do not add it to `- Scope-Paths:`: it is a DERIVED artifact and `.aw/records/research/INDEX.json` and `INDEX.md` are both gitignored, so staging either would commit an ignored generated file. The committed deliverable is the record alone.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation here is by symbol or quoted string; `19313eed` is a durable sha.
- RESEARCH IS TOOL-NAMED AND TOOL-INDEXED (AGENTS.md; `.aw/records/research/README.md`). `aw research new` derives the filename and `aw research index` maintains the manifest; hand-naming a research file or hand-editing the index is non-conforming. This is why E-03 and E-05 are separate items and why `- Scope-Paths:` carries a glob for the record rather than a guessed filename.
- THE RESEARCH MANIFEST IS GITIGNORED AND MUST NOT BE DECLARED OR COMMITTED, measured in this lane: `aw research index` writes `.aw/records/research/INDEX.json` and `INDEX.md`, and `git check-ignore -v` reports both matched by `.aw/.gitignore`. So E-05 refreshes a DERIVED local artifact rather than producing a committed one, and `- Scope-Paths:` declares only the record itself. An earlier draft of this plan declared a nonexistent `.aw/records/research/index.md` and `aw check` reported it as `check.scope-path-target-stale` (an `error`, since a stale declared path makes a plan unexecutable as written); the declaration was corrected rather than the check worked around.
- RESEARCH IS CITED BY `<id6>`, NOT BY PATH (GUIDING_PRINCIPLES P5). That is what makes a research record the right home for this audit: Orders 02 and 03 can cite it durably even though the file may later move between states or into a weekly archive shard.
- THE PHRASE CENSUS MUST BE CLASSIFIED, NOT COUNTED, and this convention is the one most likely to be violated by a fast executor. This repository's honest-limit style DELIBERATELY names the hostile agent in order to DISCLAIM protection against it (fact 4a), so the vocabulary appears most densely in exactly the comments P15 holds up as correct. An executor who treats every hit as a defect would reword the compliant majority and thereby delete the repository's record of what it does NOT defend against.
- AN AUDIT RECORD IS NOT A WORK SURFACE (AGENTS.md). Any residue this audit finds that this Set does not fix must be filed with `aw backlog new` and cited from the record, not left as prose inside it, or the attention view cannot see it.

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | The pinning test the backlog item names does not exist | `tests/test_containment_predicates.py` and `tests/test_wtiso_adversarial.py` both absent; `git show --stat 19313eed` lists both as deleted | The item's premise that the predicates are pinned is false; the audit records the true state and Order 02's subject shrinks accordingly |
| F-2 | All nine `wtiso_gate` predicates have zero product callers | AST walk of every `.py` outside the module: the sole import anywhere is `AW_MISSING_INPUT` into `lane_containment` | The audit's `wtiso_gate` row covers the whole module, not only the five raising stubs (E-01a, E-02) |
| F-3 | The five raising predicates raise as documented, but no path reaches them | Direct calls to each return `NotImplementedError`; combined with F-2 no caller exists | The fail-loud discipline protects a nonexistent caller; recorded as the evidence for a DELETE disposition |
| F-4 | The 'malicious agent' vocabulary is mostly a COMPLIANT disclaimer, not a defect | `runner_shared`'s baseline banner ("THE TARGET IS SLOPPINESS, NOT MALICE"), `host_sandbox_profile` ("explicitly NOT a boundary against a MALICIOUS same-user worker"), `attention_contract` ("NOT anti-malice crypto") | E-01(c) must CLASSIFY rather than count, and the audit must record class (a) as KEEP so Order 03 does not reword it |
| F-5 | One justification-proper site exists beside the token code | `ipd_lifecycle`: "hard enforcement against a determined same-user agent requires an OS sandbox or separate principal (`1o4eif`)" | Recorded as SIMPLIFY with Order 03 as carrier; backlog `dvonrn` D7 already says this wording is updated when the token code beside it is deleted |
| F-6 | The driver attestation token still ships in full | `mint_driver_attestation`, `verify_driver_attestation`, `DRIVER_ATTEST_ENV`, `driver-attest.token` via `private_file`, `tests/test_driver_attestation_gate.py` | Recorded as ALREADY-DECIDED with carrier `dvonrn`, explicitly out of scope, so the audit does not read as having missed it |
| F-7 | `private_file` exists to protect two secrets, one of which is not an anti-malice mechanism | `private_file`'s docstring names the attestation token AND the analytics pseudonym salt (`run_analytics_privacy.load_or_create_salt`) | The audit must NOT mark `private_file` for deletion with the token: its second consumer is a privacy mechanism protecting the USER, which P15 does not touch |
| F-8 | `orchestrate_isolation`'s 'adversarial protections' are a misnomer for merge-safety checks | Its E-04 line reads "Seeded orchestration adversarial protections against role collisions, leaked prose, unauthorized mutations, shared-worktree conflicts, stale branches"; every named hazard is an honest-mistake hazard | Recorded as SIMPLIFY (the word, not the mechanism) with Order 03 as carrier |
| F-9 | `run_ledger_store` is 'tamper-evident' by construction, and this is NOT an anti-malice gate to remove | Its hash chain detects DAMAGE (torn writes, truncation) and `NotALedgerError` exists precisely to avoid accusing healthy data; `is_ledger_shaped` "can never mask real tampering" | Recorded as KEEP: integrity checking against corruption is honest-mistake protection, and the vocabulary overlap with anti-malice work is coincidental |
| F-10 | The repository has recorded this dangling-citation defect class twice already | Backlog `ikxtkj` (five doc citations to deleted tests) and backlog `gia5i7` (nine `runner_shared` citations to a deleted class), both citing `19313eed` | The audit cites both rather than re-filing a third, and Order 02 fixes only the `wtiso_gate` instances it deletes outright |

## Proposed changes (ordered, validatable)

1. Re-derive the caller census, the raise check, the classified phrase census, and the artifact check in the executor's own lane (E-01).
2. Classify every enumerated item as KEEP / SIMPLIFY / DELETE / ALREADY-DECIDED with its deciding test and carrier (E-02).
3. Create the record with `aw research new` and write the enumeration and classification into it (E-03).
4. State the audit's own limits in the record (E-04).
5. Refresh and check the research manifest (E-05).

## Deferred / out of scope (with reason)

- EVERY CODE, COMMENT, SPEC AND TEST EDIT. This plan writes a record and changes no behavior. The two remediation children carry the edits, which is why this plan declares only research paths.
  - Carrier: 38pxaz, dmjp0u
- THE DRIVER ATTESTATION TOKEN'S REMOVAL. Backlog `ariaau` marks it ALREADY DECIDED and out of scope, and its design lives in backlog `dvonrn` D1 (delete the token, the minting, `verify_driver_attestation`, and the `lane_worktree_active` location guess). The audit records it with that disposition rather than deciding it.
  - Carrier: dvonrn
- RE-DECIDING `--by-human`, THE SUITE-BASELINE ADJUDICATION, AND THE OPT-IN HARDENED SANDBOX. The backlog item marks all three ALREADY DECIDED as KEEP, and F-4 independently measured the first two as the P15-compliant model. Recording them is in scope; reopening them is not.
  - Carrier-Declined: Nothing is owed because no latent work exists. Each is already in the state P15 wants, and filing an item would assert the repository intends to revisit a decision it does not.
- THE DANGLING CITATIONS OUTSIDE `wtiso_gate.py`. F-1 and F-10 show the same `19313eed` deletion orphaned citations across `docs/` and `runner_shared`. Those are filed and owned; this audit cites them as prior art rather than absorbing a repository-wide citation sweep.
  - Carrier: ikxtkj, gia5i7
- A DETERMINISTIC DETECTOR FOR ANTI-MALICE JUSTIFICATIONS, i.e. a checker rule that flags a new comment justifying a gate by naming a hostile agent. Attractive under GUIDING_PRINCIPLES P11, and refused here on measurement: F-4 shows the vocabulary appears most densely in the COMPLIANT disclaimers, so a pattern rule would fire overwhelmingly on correct code, and distinguishing class (a) from class (b) is the judgement E-02 makes by reading. A detector that cannot make that distinction would be a warning generator, not a gate.
  - Carrier-Declined: Nothing is owed because this is not latent work but a rejected design. Filing it would imply the repository intends to build a rule whose false-positive rate its own measurement predicts.

## Scope check

- Over-scope: none. The plan writes one research record and refreshes the research manifest, which is exactly the backlog item's first named output ("A research or decision record listing every item found with its keep/simplify/delete decision and evidence"). No file under `agent_workflows/`, `tests/` or `.aw/records/specs/` is touched.
- Under-scope: `agent_workflows/wtiso_gate.py` and the phrase sites are READ but not modified, deliberately: reading is how the audit is produced, and every edit belongs to a sibling. The second half of the item's output ("plus one reviewed plan per non-trivial removal or simplification") is delivered by Orders 02 and 03 existing, not by this plan. `- Scope-Paths:` carries a GLOB for the record because `aw research new` derives the filename and this plan cannot know it in advance; the executor must confirm at finalize that the path it wrote matches the declared pattern and nothing else changed.

## Required tests / validation

- THIS PLAN ADDS NO TEST, and that is a deliberate consequence of its deliverable rather than an omission. Its output is a records-tree document; the behavior-affecting work is in Orders 02 and 03, each of which carries its own test obligations. Asserting on the record's prose would be a text pin of exactly the kind GUIDING_PRINCIPLES P16 forbids and the kind that rotted into F-1.
- `aw research index --check` reporting the tree and manifest consistent, pasted (E-05).
- Bare `python3 -m pytest` with the `N passed` summary line pasted, against a baseline captured the same way BEFORE any file lands, proving a records-only change broke nothing. A pre-existing failure must be shown pre-existing by that baseline rather than argued harmless.
- `aw ipd lint --phase pre-transition` conforming, `aw check` no worse than a pre-change baseline with both counts pasted, and `aw sanitize --agent` clean (the record quotes code comments and must not carry a local path).
- THE ENUMERATION EVIDENCE IS THE REAL VALIDATION HERE: V-01 requires the four pasted lists, and V-02 requires that no enumerated item is left unclassified. A record that is well-formed but incomplete satisfies neither.

## Spec / documentation sync

- NO SPEC IS AMENDED BY THIS PLAN, and `- Scope-Paths:` declares no `.spec.md` file. Stated explicitly because a reader may expect spec `7ckptx` here: its R6.1 / R6.2 / R6.3 govern the `wtiso_gate` predicates and Non-goal text names the module as "the designated home for shared containment predicates ... a fail-loud skeleton by design", so DELETING the module requires amending that spec. That amendment belongs to Order 02, which owns the deletion and declares the spec file itself. Splitting it that way keeps the amendment in the same change as the behavior it describes, which is what AGENTS.md requires.
- NO CHANGELOG ENTRY. A records-tree addition with no user-visible behavior change.
- THE AUDIT RECORD IS CITED BY THE SIBLINGS, not the other way round. Orders 02 and 03 cite this record's `<id6>` as the evidence for their decisions, which is why E-05's manifest refresh is a required item rather than a tidiness step: an uncited-because-unindexed record cannot be resolved by id6.
- HISTORICAL RECORDS ARE LEFT ALONE. Executed plans `8zgybk`, `604wra` and `u27oh3` record what was decided when they ran; the plan contract forbids changing what an executed record records. The audit describes the CURRENT state and cites those plans as provenance.

## Open questions

### OQ-01: Should the audit record be filed as a decision record under `reference/`, or as a plain research report?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: E-03 lets the executor choose from the contract vocabulary `aw research new --kind` offers, and RECORD which it chose and why. The argument for a reference-tier record: this is durable, it will be cited by id6 by both siblings and by any future review that touches a gate, and P15's closing sentence makes it a standing reference rather than a one-off investigation. The argument against: it is an audit performed once at a point in time, and filing it as reference asserts a currency it will lose as gates change. NOT BLOCKING because the record's CONTENT, its path derivation, and its manifest entry are identical either way, and `aw research set-assign` can regroup it later without breaking an id6 citation (GUIDING_PRINCIPLES P5).
- Carrier-Declined: No carrier is owed under either answer. Both are fully implemented inside E-03 and neither leaves anything unbuilt; V-03's required evidence is the same in both cases.

### OQ-02: Should an item classified KEEP be re-examined when its neighbourhood changes, and if so how is that recorded?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: The record states the deciding test for every KEEP (E-02), which is what lets a future reader re-apply it rather than re-derive it, and P15 already obliges any review that touches a gate to apply the principle. The plan does NOT add a re-examination schedule or a staleness marker. Against that: a KEEP decided today against a mechanism that later grows a token or a location guess would be stale and nothing flags it. NOT BLOCKING because the remedy under either answer is the same (P15 applies at the next touch), and building a staleness mechanism for an audit record is a larger design than this plan's deliverable justifies.
- Carrier-Declined: Nothing is owed because no latent work is identified, only a residual risk that P15's standing obligation already addresses. Filing an item would imply a tracking mechanism is intended when none has been designed or requested.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: all FOUR pasted lists from the executor's own lane: (a) the AST-derived caller census for `wtiso_gate` showing every import and attribute access found, with the method shown to be AST-based and not a text grep; (b) the per-predicate raise/return result for all nine; (c) the phrase census with EACH hit classified as disclaimer or justification and the deciding words quoted; (d) the existence check for every cited test file and doc. Plus one explicit sentence per fact F-1 through F-5 stating whether it reproduced. Plus a pasted `git status --short` showing the measurement modified no file. Numbers differing from this plan's are EXPECTED and satisfy this item; reusing this plan's numbers without running does NOT. If fact 2 failed to reproduce, this item is satisfied only by saying so explicitly and stopping the Set.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the complete classification table pasted, shown to leave NO enumerated item from E-01 unclassified (state the two counts and that they match). Every DELETE and SIMPLIFY row must name its carrier; every KEEP row must name the honest mistake it catches; every ALREADY-DECIDED row must cite the prior decision. Confirm explicitly that the class (a) disclaimers from F-4 are classified KEEP and NOT marked for rewording, since misclassifying them is the single most likely error and would cause Order 03 to delete the repository's honest-limit record.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the `aw research new` invocation and its output showing the TOOL derived the path, plus the written record's front matter and its classification table. State which `--kind` was chosen and why (OQ-01). Confirm the four ALREADY-DECIDED items from the backlog item are present with citations. A hand-named file does NOT satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the record's limits section pasted, showing at least the three required limits (the START HERE list is not exhaustive and what the phrase census cannot find; a deletion's reference sweep is the carrier's obligation; the classification is a disputable judgement with its test written down). Each must be stated as a limit with its consequence, not as a disclaimer sentence.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `aw research index --check` output reporting the tree consistent, plus the manifest line for the new record showing it is resolvable by its `<id6>`. Plus a statement that the index was refreshed by the tool and not hand-edited. Plus a `git status --short` and a `git diff --cached --name-only` reconciled against `- Scope-Paths:`, showing the committed set is the record alone: the manifest must NOT appear, since both `INDEX.json` and `INDEX.md` are gitignored and committing a derived ignored file would be a defect, not thoroughness.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries NO `- Readiness:` field, whose absence is deliberate: that field is
an output of `/plan-review` and writing it at authoring time would forge the attestation a gate reads.

The executor must: perform E-01 through E-05 in order, respecting the declared `Depends on` edges; treat
E-01 as a HARD GATE, because if a real product caller for any `wtiso_gate` predicate exists then Order 02's
deletion is unsafe and the Set must stop rather than proceed on a false premise; create the record through
`aw research new` and refresh the manifest through `aw research index`, never by hand; commit only the
paths matching `- Scope-Paths:` via `aw commit <plan> -- <paths>`; never push; paste ACTUAL command output
for every measurement claim; and verify each `V-*` in a separate pass from the `E-*` that produced it. Do
NOT mark this plan executed or move it to `.aw/records/plans/executed/` until every `V-*` carries concrete
pasted evidence and `aw ipd lint --phase pre-transition` conforms.

THE ONE WAY TO GET THIS PLAN WRONG is to treat every appearance of the word 'malicious' as a defect to
remove. F-4 measured the opposite: this repository's honest-limit style NAMES the hostile agent precisely
in order to DISCLAIM protection against it, and those disclaimers are what P15 holds up as correct. If your
classification marks `runner_shared`'s baseline banner, `host_sandbox_profile`'s docstring, or
`attention_contract`'s `--by-human` note for rewording, you have inverted the principle: you would be
deleting the record of what this repository does not defend against, which is the honest half.

A SECOND WAY TO GET IT WRONG is to fix things. This plan's deliverable is a RECORD. If you find yourself
editing `wtiso_gate.py` or a comment under `agent_workflows/`, stop: that work is owned by Orders 02 and 03,
and doing it here would put a behavior change in a plan whose validation has no test for it.

Backlog item `ariaau` is this plan's origin (`- From-Backlog: ariaau`). That item carries NO
`- Blocks-Release:` gate and none is invented here. The `chore` classification is inherited and CONFIRMED
by measurement: no user-perceptible behavior is wrong and no operator waits on anything, because F-2 shows
the audited `wtiso_gate` surface is unreachable from any shipped path. The cost falls on the next author to
read a gate and re-derive whether P15 was applied to it.
