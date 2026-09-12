# IPD: Record the no-known-bugs rule in the contributor rules and the decisions log

- Date: 2026-09-11
- Kind: child
- Concern: The rule that every bug blocks the next release is recorded nowhere. `grep` across `AGENTS.md`, `DECISIONS.md`, `GUIDING_PRINCIPLES.md` and the backlog README returns nothing, so it survives only in conversation and is measurably forgotten: 28 of 60 live bug items carry no gate.
  AND THE UNRECORDED RULE HAS NOW BEEN CLARIFIED TWICE IN ONE DAY WHILE STILL UNWRITTEN, which is the sharpest evidence that conversation is not a durable medium for it. On 2026-09-12 the maintainer ruled that inefficiency IMPACTING THE USER EXPERIENCE is a defect while inefficiency users cannot notice is not, so `bug` reaches a correct-but-slow code path when a human waits on it. That ruling arrived because an agent had filed such a defect as `chore` (backlog `59t9x5`, `aw find` opening every record twice, ~128ms of a ~530ms command) on the reasonable-looking basis that nothing returned a wrong answer; the agent then over-corrected and wrote the rule as covering ALL knowingly redundant work, which the maintainer narrowed again to the perceptibility test. Both the misfiling and the over-correction happened inside one session, from the same cause: nothing in the repository states the test, so each agent supplies its own.
- Scope: State the rule where it is discoverable and where the enforcing code can cite it: the existing release-gates section of the contributor rules, and a numbered entry in the decisions log. State BOTH maintainer rulings the policy now carries (every live bug gates the next release, 2026-09-11; and inefficiency counts as a defect when it is USER-PERCEPTIBLE and not when it is invisible, 2026-09-12), plus its two honest limits. Does NOT change any code, does NOT gate any other work kind, and does NOT backfill any item.
- Scope-Paths: AGENTS.md, DECISIONS.md, agent_workflows/engine.py, .aw/records/backlog/README.md
- Item-Dependencies: none
- Status: to-review
- Set: nobugship
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: zqs0px
- Blocks-Release: next

## Workflow history

- 2026-09-11 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from the maintainer's question of 2026-09-11, "How do we ensure that approach persists?" This child is the answer's first third: an unwritten rule cannot persist. MEASURED at HEAD `2ff2b1b1`: the rule appears in none of the four candidate documents, while `AGENTS.md:125-146` ALREADY owns a "Release gates (Blocks-Release)" section that describes the mechanism without stating this policy, so the addition extends an existing section rather than inventing a home for it. `DECISIONS.md`'s highest entry is D153. NOTE THE GENERATION HAZARD: the `AGENTS.md` release-gates text is emitted from `engine.py`, so a hand-edit to `AGENTS.md` alone would be reverted by the next install; the generator is declared in `Scope-Paths` for that reason.

## Goal

Make the rule discoverable by a reader and citable by the checker, so the other two children have something to point at rather than each restating policy.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish where the rule belongs

- [ ] E-01 CONFIRM WHICH DOCUMENT OWNS THIS POLICY, AND WHETHER A SPEC ALREADY DOES, before writing anything. `AGENTS.md:125-146` has a "Release gates (Blocks-Release)" section that describes the field, how to set it, and how `Blocks-Release` differs from `Blocked-By`; that is the natural home. BUT VERIFY NO SPEC ALREADY OWNS RELEASE-GATE POLICY: if one does, the rule belongs there and `AGENTS.md` should point at it rather than duplicating it, per the single-source-of-truth principle. Search `.aw/records/specs/` for release-gate normative text and report what you find.
  ALSO DETERMINE WHETHER THE TEXT IS GENERATED. The release-gates section is installed into managed repos from `engine.py`, so a hand-edit to `AGENTS.md` would be reverted on the next install. Establish which lines are generated and which are repo-local before editing either.
  - Depends on: none
  - Expected outcome: a stated decision on the owning document, evidence for or against a spec already owning it, and the exact generated-versus-local boundary for the lines to be edited.
  - Execution state: pending

- [ ] E-02 WRITE THE RULE, IN THE GENERATOR AND NOT ONLY IN THE RENDERED FILE, and keep it to the smallest wording that carries the policy and its two limits. It must say: a backlog item, spec or plan whose `- Work-Kind:` is `bug` MUST carry `- Blocks-Release:` while it is live (`open`, `blocked` or `graduated`), because known bugs do not ship; and the gate travels to whatever plan or spec the item graduates into, which is an obligation the existing graduation paragraph already states for a gate that exists and must now apply to one that is implied.
  THE RULE COVERS INEFFICIENCY A USER CAN NOTICE, AND THE TEST IS USER-PERCEPTIBLE IMPACT, NOT REDUNDANCY. Maintainer ruling 2026-09-12: inefficiency that impacts the user experience is a defect; inefficiency that does not noticeably affect users is not. So `bug` is not limited to a wrong answer, and it is equally not extended to every wasteful code path. The discriminator is whether a user can perceive the cost, which means the filer owes a MEASUREMENT against the surface a user actually touches, not a count of redundant operations.
  WRITE THE DISCRIMINATOR THIS WAY, because the tempting wording is wrong. Provable redundancy is EVIDENCE of inefficiency but is not itself the test: doubling a 2ms internal call is redundant and unnoticeable, so it is a `chore`. Conversely a slow path with no redundancy at all can be a bug if a user waits on it. Measure the END-TO-END command a user runs, warm and cold, rather than an internal function in isolation; an isolated call can read many times its real cost when nothing else has warmed the page cache.
  THE WORKED EXAMPLE, and it qualifies on the measurement rather than on the redundancy. Backlog `59t9x5`: `aw find` opens every record TWICE (1240 opens end to end against the 620 the resolver needs). What makes it a `bug` is that the redundant read costs ~128ms of a ~530ms command an operator waits on, so removing it would leave ~402ms; that is a difference a human notices. It was filed `chore` on the reasoning that output was correct, and the maintainer reclassified it to `bug`. Had the same double read cost 3ms, `chore` would have been right.
  STATE THE JUDGEMENT HONESTLY RATHER THAN INVENTING A THRESHOLD. Do not write a numeric cutoff into the rule unless the maintainer sets one; "noticeable" is a judgement the filer makes and records with the number that supports it, so a reviewer can disagree with the number rather than with a vibe. An unmeasured hunch that something feels slow is not a bug and should not be filed as one.
  STATE THE TWO LIMITS HONESTLY, because a rule whose limits are hidden gets trusted further than it should. FIRST, the gate keys on an AUTHOR'S CLASSIFICATION, so a genuine defect filed as `chore` or `followup` escapes it; that is the parent's OQ-02 and the wording must name it rather than imply completeness. NOTE the inefficiency ruling makes this limit BITE HARDER rather than softer, and in BOTH directions: a user-visible performance defect is easy to file as `chore` (which `59t9x5` measurably was), while an invisible one is easy to over-file as `bug` now that inefficiency is nameable at all. Use `59t9x5` as the worked example of the first and say plainly that the second is also a misfiling. SECOND, the rule governs LIVE items only: a bug already `done` is not retroactively gated, because rewriting its gate now would assert a history that did not happen.
  DO NOT WRITE THE RULE AS AN ABSOLUTE. Per the maintainer's standing instruction of 2026-09-10, state what is enforced and why, without "never" or "no exception", so the text does not have to be policed later if evidence changes it.
  - Depends on: E-01
  - Expected outcome: the rule stated in the generator with its two limits, and the rendered `AGENTS.md` regenerated rather than hand-edited.
  - Execution state: pending

### Task group 2: record it as a decision and prove the file agrees with its generator

- [ ] E-03 ADD A NUMBERED `DECISIONS.md` ENTRY, since this shapes the repository beyond one artifact and constrains every future bug filing. Record WHAT was decided, WHO decided it (the maintainer, 2026-09-11), the reasoning in their own framing ("We don't ship known bugs"), and the MEASUREMENT that motivated writing it down: 28 of 60 live bug items were ungated, two of them filed by an agent hours after being told the rule in the same session.
  CHECK THE HIGHEST D-NUMBER AT WRITE TIME, do not reuse this plan's. Measured D153 at authoring, and other agents append concurrently, so a stale number would collide.
  - Depends on: E-02
  - Expected outcome: a `DECISIONS.md` entry at the next free number carrying the decision, its author, its reasoning and its motivating measurement.
  - Execution state: pending

- [ ] E-04 PROVE THE RENDERED FILE MATCHES ITS GENERATOR, which is the check that catches the hand-edit failure mode this plan is exposed to. Run whatever test asserts that `AGENTS.md`'s managed block equals the generated text; a comparable assertion already exists for the shared-checkout block, so find it rather than writing a new one. If the regeneration produces a near-empty diff, treat that as a FAILURE signal (the edit did not land) rather than success.
  - Depends on: E-03
  - Expected outcome: the parity assertion named and passing, with the regenerated diff's line count stated.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `AGENTS.md`'s guidance blocks are GENERATED from `engine.py` and installed into managed repos, so a hand-edit is reverted on the next install; the file carries managed-block markers for exactly this reason.
- A decision that shapes the repository beyond one artifact belongs in `DECISIONS.md`, which the `askme` workflow states explicitly.
- Per the maintainer's instruction of 2026-09-10, a rule should be written as what is currently enforced rather than as an absolute, because a declared inflexibility later has to be policed.

## Findings

| Id | Severity | Finding |
|---|---|---|
| F-1 | HIGH | The rule is unrecorded. `grep` for it across `AGENTS.md`, `DECISIONS.md`, `GUIDING_PRINCIPLES.md` and `.aw/records/backlog/README.md` returns nothing at HEAD `2ff2b1b1`. |
| F-2 | HIGH | Loaded context is not a sufficient mechanism, and this session is the proof: an agent filed two ungated bug items (`kyb0v5`, `mqmlug`) hours after the maintainer stated the rule to it directly. Writing it down is necessary but, on this evidence, not sufficient either, which is why children 02 and 03 exist. |
| F-3 | MEDIUM | A home already exists: `AGENTS.md:125-146` owns "Release gates (Blocks-Release)" and describes the field and the `Blocks-Release` versus `Blocked-By` distinction without stating this policy. The addition extends that section. |
| F-4 | MEDIUM | The text is GENERATED from `engine.py`, so editing `AGENTS.md` alone would be silently reverted on the next install. Both are declared. |
| F-5 | LOW | `DECISIONS.md`'s highest entry is D153 at authoring, and other agents append concurrently, so the number must be re-checked at write time. |

## Proposed changes (ordered, validatable)

1. Establish the owning document and the generated-versus-local boundary (E-01).
2. State the rule and its two limits in the generator, then regenerate (E-02).
3. Record it as a numbered decision with its motivating measurement (E-03).
4. Prove the rendered file matches its generator (E-04).

## Deferred / out of scope (with reason)

- ANY CODE CHANGE. Children 02 and 03 own the default and the enforcement; this child only makes the rule discoverable and citable.
- BACKFILLING THE 28 VIOLATIONS. Child 03 owns that, deliberately after the default is in place so the backfill cannot immediately re-diverge.
- EXTENDING THE RULE TO `security`. The parent's OQ-01; not assumed here.

## Scope check

- Over-scope: none. Four paths: the generator, the rendered contributor rules, the decisions log, and the backlog README that a filer is most likely to read.
- Under-scope: this child does not prevent a single future ungated bug on its own. That is honest rather than a gap: F-2 measures that documentation alone failed, which is why the Set has three children.

## Required tests / validation

No new test file: this child changes documentation. It must run the EXISTING generator-parity assertion (E-04) and the bare suite, with the baseline established BEFORE the first edit.

## Spec / documentation sync

This child IS the documentation change. E-01 must additionally report whether a spec already owns release-gate policy; if one does, the rule belongs there and `AGENTS.md` points at it rather than duplicating it.

## Open questions

### OQ-01: Should the rule live in a spec rather than in the contributor rules?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: RESOLVE FROM EVIDENCE IN E-01 RATHER THAN ASKING. If a spec already carries release-gate normative text, that spec owns the policy and `AGENTS.md` should point at it, per the single-source-of-truth principle. If none does, the contributor rules are the right home because that is where the existing release-gates section lives and where an agent filing an item actually reads. Non-blocking because the rule's CONTENT is identical either way and only its location moves; record the finding and the choice in E-01's outcome.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the search over `.aw/records/specs/` for release-gate normative text and state the verdict (a spec owns it, or none does). Paste the managed-block boundary showing which `AGENTS.md` lines are generated from `engine.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `engine.py` diff and the regenerated `AGENTS.md` diff side by side, showing the rule, BOTH stated limits (author-classification leak, live-items-only), AND the inefficiency ruling of 2026-09-12 with its USER-PERCEPTIBILITY test and `59t9x5` as the worked example. Quote the sentence establishing that redundancy is EVIDENCE rather than the test itself, and the sentence saying an unmeasured hunch is not a bug. Confirm the wording does NOT contain a numeric threshold, since none was set; if a reader could apply the rule without measuring anything, the wording has failed. Paste a grep proving the wording contains none of `never`, `no exception`, `always must`, per the no-absolutes instruction. State the diff line count.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the new `DECISIONS.md` entry verbatim, and paste the command showing the highest D-number IMMEDIATELY BEFORE the write, proving no collision with a concurrently-appended entry.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: name the generator-parity test, paste it passing, and paste the regenerated diff stat with its line count. A near-empty diff is a FAILURE and must be reported as one. Finally paste the bare `python3 -m pytest` summary against the pre-edit baseline, naming any failure as pre-existing or new.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until it has been reviewed and a human sets it `approved`.

It carries `- Blocks-Release: next` in line with the rule it records.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped, never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark.

NOTE THE HAZARD THAT DEFINES THIS PLAN: `AGENTS.md` is GENERATED. Editing it directly produces a change that the next install silently reverts, which would leave the rule appearing recorded while actually being absent, the exact state this Set exists to end. Edit `engine.py` and regenerate.
