# IPD: Reframe every determined same-user and malicious agent justification as the honest-mistake guard it actually is

- Date: 2026-09-30
- Kind: child
- Concern: GUIDING_PRINCIPLES P15 forbids building against a hostile agent AND forbids justifying a mechanism by naming one ("WHAT NOT TO BUILD: ... any mechanism whose justification is 'in case the agent lies'"). Two sites in the shipped package still offer that justification. `ipd_lifecycle` tells a reader that "hard enforcement against a determined same-user agent requires an OS sandbox or separate principal (`1o4eif`)", which frames the opt-in sandbox as the real answer to a hostile agent; backlog `dvonrn` D7 rules the opposite ("REFRAME, do not rebuild: it is OPTIONAL ISOLATION an operator may choose, NOT 'the real fix for malicious agents'"). `orchestrate_isolation` advertises "Seeded orchestration adversarial protections" for a list of hazards (role collisions, leaked prose, shared-worktree conflicts, stale branches, lane timeouts) that are every one of them honest-mistake hazards, so the word misdescribes the mechanism and invites the next author to extend it in the wrong direction. Left alone, each site teaches a future author that anti-malice reasoning is the house style, which is how the machinery P15 exists to stop gets rebuilt.
- Scope: Reframe the small number of comment and docstring sites whose stated JUSTIFICATION for a mechanism is a hostile agent, so each states the honest mistake it actually catches. Two sites are confirmed at authoring (`ipd_lifecycle`'s sandbox pointer, `orchestrate_isolation`'s module docstring) and the executor re-derives the full list from Order 01's audit. EXCLUDES every HONEST-LIMIT DISCLAIMER that names a hostile agent in order to deny protecting against it, which is P15-compliant already and must be left alone. EXCLUDES all behavior: no predicate, refusal, exit code, message a user sees, or test outcome changes. EXCLUDES the driver-attestation comments deleted by backlog `dvonrn`, the `wtiso_gate` prose deleted by Order 02, and every dangling test citation.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/orchestrate_isolation.py
- Item-Dependencies: executed:bec7ee, executed:38pxaz
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: ariaau
- Set: malgate
- Order: 3
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: dmjp0u

## Workflow history

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored while graduating backlog `ariaau`. THE MEASUREMENT INVERTED THE ITEM'S IMPLIED SHAPE, which is the single most important fact for whoever executes this. The item's START HERE says to find "Code comments and docstrings citing a 'determined same-user agent' or 'malicious' agent as the justification for a check", which reads as a sweep over every hit of that vocabulary. Measured across `agent_workflows/`, the large majority of hits are the OPPOSITE of a defect: they are honest-limit disclaimers that name the hostile agent precisely in order to say the mechanism does NOT defend against one (`runner_shared`'s baseline banner ending "THE TARGET IS SLOPPINESS, NOT MALICE"; `host_sandbox_profile`'s "explicitly NOT a boundary against a MALICIOUS same-user worker"; `attention_contract`'s "NOT anti-malice crypto"). Those are the model P15 itself cites, and rewording them would delete the repository's record of what it does not defend against. So this plan is NARROW by measurement: it targets only the sites where the hostile agent is offered as the REASON a mechanism exists or as the FIX for its weakness, and it states that discriminator as the executor's primary obligation.
- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the shipped package stop teaching anti-malice reasoning, by giving the few sites that justify a
mechanism with a hostile agent the honest-mistake justification the mechanism actually has.

This is the smallest and lowest-risk member of the Set, and it is worth doing for a specific reason rather
than tidiness. P15's value comes from being APPLIED, and an agent or human applies what the surrounding code
models. A comment that says "hard enforcement against a determined same-user agent requires an OS sandbox"
reads as a roadmap: it tells the next author that the current check is a weak approximation of a proper
defense and that strengthening it is the direction of travel. That is exactly backwards under P15, and it is
the reasoning that produced the per-run driver token whose own honest-limits note conceded a same-user agent
could read the token file, and which then blocked a human's own feature worktree (measured 2026-09-26,
recorded in P15 and in backlog `dvonrn`).

WHAT THIS PLAN IS NOT. It is not a vocabulary sweep. The words "malicious", "adversarial", "tamper" and
"forge" appear across the package in three legitimate shapes that must survive untouched:

- HONEST-LIMIT DISCLAIMERS, which name the hostile agent to DENY protecting against one. These are
  P15-compliant and are the principle's own cited model.
- INTEGRITY LANGUAGE about DAMAGE rather than attack, such as `run_ledger_store`'s tamper-evident hash
  chain, whose sibling `NotALedgerError` exists specifically to avoid accusing healthy data of damage.
- FORGERY LANGUAGE about a mistaken CLAIM rather than an attack, such as `plan_readiness`'s refusal of an
  unattested `- Readiness:` field. AGENTS.md itself frames that case as an honest error ("an agent authoring
  a four-plan Set wrote `Readiness: go-pending-approval` into all four having run no review"), and P15
  explicitly endorses attestations as "a conscious pause and an honest record, not a lock".

THE DISCRIMINATOR, stated once because every item below depends on it: does the comment offer the hostile
agent as the REASON the mechanism exists, or as the FIX for what it cannot do? If yes, it is this plan's
subject. If the comment names the hostile agent in order to DISCLAIM protection, or describes damage or a
mistaken claim rather than an attacker, it is not.

FOUR FACTS ESTABLISHED AT AUTHORING. The executor re-derives the list from Order 01's audit rather than
copying this one (E-01).

1. THE `ipd_lifecycle` SITE IS A JUSTIFICATION, NOT A DISCLAIMER, AND ITS DISPOSITION IS ALREADY RULED ON.
   The comment reads "hard enforcement against a determined same-user agent requires an OS sandbox or
   separate principal (`1o4eif`)". Backlog `dvonrn` D7 rules that the hardened profile is "OPTIONAL
   ISOLATION an operator may choose, NOT 'the real fix for malicious agents' and NOT something any gate
   relies on", and says in as many words that "Documentation that frames it as the answer to a 'determined
   same-user agent' ... is updated when the token code it sits beside is deleted in this design, and
   elsewhere by the `ariaau` audit". So this site is assigned to THIS audit by name.

2. A NEARLY IDENTICAL SITE SITS IN THE SAME FILE AND IS SHARED WITH `dvonrn`. The worker-role block's honest
   limit reads "this is an environment SELECTOR ... not a hardened boundary. A same-user worker with shell
   access can unset the variable. Hard enforcement is an OS sandbox / separate principal (x03wgn, Phase 6
   `1o4eif`)". Its FIRST half is a compliant disclaimer; only its closing "hard enforcement is" clause is a
   justification. This matters for sequencing: `dvonrn` will edit this neighbourhood when it deletes the
   token, so the executor must check whether `dvonrn` has already landed and reconcile rather than collide.

3. `orchestrate_isolation`'s LABEL MISDESCRIBES ITS OWN MECHANISM. Its module docstring advertises "E-04:
   Seeded orchestration adversarial protections against role collisions, leaked prose, unauthorized
   mutations, shared-worktree conflicts, stale branches, lane timeouts, and unsafe background completions".
   Every hazard named is an honest-mistake hazard: a forgetful agent collides roles, a stale branch is a
   timing accident, a lane timeout is a hang. The module's actual refusals are merge-safety and
   role-isolation checks, and its most-cited line is the P15-shaped "Per-lane green NEVER implies integrated
   green!". So the word "adversarial" is a misnomer inherited from the research vocabulary, not a
   description of what the code does.

4. THE VOCABULARY IS DENSEST IN THE COMPLIANT SITES, which is why a pattern-matched sweep would do damage.
   The single largest concentration is `runner_shared`'s pre-work-baseline banner, four numbered reasons
   ending "THE TARGET IS SLOPPINESS, NOT MALICE", which is the maintainer ruling P15 generalizes and which
   that banner's own text forbids anyone to "improve" away. A sweep keyed on the words would hit it first.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: derive the target list, and prove what is NOT in it

- [ ] E-01 BUILD THE TARGET LIST FROM ORDER 01's AUDIT PLUS YOUR OWN RE-MEASUREMENT, and classify every hit before editing a character. Read the audit record Order 01 produced (cite it by `<id6>`) and take its SIMPLIFY rows for this family as the starting list. Then re-run the census yourself across `agent_workflows/` for the case-insensitive family `malicious`, `determined same-user`, `hostile`, `adversarial`, and classify EACH hit into one of: JUSTIFICATION (the hostile agent is the reason the mechanism exists, or the named fix for its weakness) which is in scope; DISCLAIMER (names the hostile agent to deny protecting against one) which is OUT of scope; INTEGRITY-OR-CLAIM (describes damage, or a mistaken attestation, rather than an attacker) which is OUT of scope. Quote the deciding words for every classification. Report the counts of all three classes.
  - Depends on: none
  - Expected outcome: the classified census pasted, with each JUSTIFICATION site named by symbol and each OUT-of-scope classification carrying the quoted words that decided it. The three counts must sum to the total hits found.
  - Execution state: pending

- [ ] E-02 CHECK WHETHER BACKLOG `dvonrn` HAS LANDED, and reconcile rather than collide. `dvonrn` D1 deletes the driver attestation token, `verify_driver_attestation`, and `lane_worktree_active`'s location guess from `ipd_lifecycle`, and D7 says the documentation framing the sandbox as the answer to a determined same-user agent "is updated when the token code it sits beside is deleted in this design". Determine the current state on disk: if the token code is GONE, some or all of fact 1 and fact 2 may already be fixed, and this plan's edit shrinks to whatever remains. If the token code is PRESENT, make the edit as planned, and make it in a way that does not depend on the token's existence, so `dvonrn` can later delete the surrounding code without having to re-edit the reframed comment.
  - Depends on: E-01
  - Expected outcome: a recorded statement of `dvonrn`'s landed state, the resulting adjustment to the target list, and (where the token is present) confirmation that the reframed wording will survive the token's removal.
  - Execution state: pending

### Task group 2: reframe the justifications

- [ ] E-03 REFRAME THE `ipd_lifecycle` SITES per facts 1 and 2, preserving every true statement and removing only the anti-malice framing. For the role-gate honest limit: KEEP the accurate part ("an environment SELECTOR, not a hardened boundary", and that a same-user worker can unset the variable, which is the honest limit a reader needs), and REPLACE the closing "hard enforcement is an OS sandbox / separate principal" clause, which frames a stronger defense as the intended direction. State instead what the selector is FOR: it tells a managed worker plainly that the lifecycle transition is the runner's step, which is the one honest mistake actually observed (a worker forking a second receipt), and cite P15 so the next reader knows the framing is deliberate. For the sandbox pointer beside the attestation gate: apply backlog `dvonrn` D7's ruling that the hardened profile is OPTIONAL ISOLATION an operator may choose and that NOTHING may depend on it being on, rather than the real fix for a determined agent. Do NOT weaken or remove any statement of a genuine limitation: a reader must still learn that the selector can be unset.
  - Depends on: E-02
  - Expected outcome: the `git diff` of `ipd_lifecycle`, showing comment text only, the genuine limitations preserved, the anti-malice framing gone, and no executable line altered.
  - Execution state: pending

- [ ] E-04 REFRAME `orchestrate_isolation`'s MODULE DOCSTRING per fact 3, so the label matches the mechanism. Replace "Seeded orchestration adversarial protections against ..." with a description of what those protections actually catch: the honest-mistake hazards already listed (role collisions, leaked prose, unauthorized mutations, shared-worktree conflicts, stale branches, lane timeouts, unsafe background completions) are things a FORGETFUL or MISTAKEN orchestrator does, and the module's refusals exist to catch them early with a clear message. Keep every named hazard: the list is accurate and is the module's contents page. Do NOT rename any symbol, exception class, or test; this is a docstring change. If the executor finds a symbol NAME (not a comment) carrying the anti-malice framing, record it and leave it, because renaming a public symbol is a contract change this plan has not scoped.
  - Depends on: E-03
  - Expected outcome: the `git diff` of the module docstring, showing the hazard list intact, the misnomer replaced, no symbol renamed, and no executable line altered.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation here is by symbol or quoted string.
- STYLE RULES FOR PROSE APPLY TO USER-FACING TEXT, NOT INTERNAL ARTIFACTS (GUIDING_PRINCIPLES P13). Every site this plan edits is a code comment or docstring, which P13 lists explicitly as NOT user-facing, so the no-dash convention does not apply and no effort should be spent on it. What DOES apply is that comments are "for humans and models reading the code", which is precisely why a misleading justification in one is worth fixing.
- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (AGENTS.md; GUIDING_PRINCIPLES P16). Decisive for this plan's validation shape: P16 forbids asserting "that exact phrases, warning banners, or docstrings exist in production files", which is the only kind of test that could check a reworded comment. So this plan adds NO test and is validated by its diffs, and the full suite proves it changed no behavior.
- A COMMENT THAT STATES A GENUINE LIMITATION MUST SURVIVE THE REWORDING. GUIDING_PRINCIPLES P2 (honest documentation over aspirational documentation) means the reframing may not quietly upgrade a weak mechanism into a strong-sounding one. The `AW_EXECUTION_ROLE` selector really can be unset by a same-user worker, and a reader must still learn that; what changes is that its remedy is no longer framed as a stronger defense.
- THE BASELINE BANNER IS EXPLICITLY OFF LIMITS, and it says so itself. `runner_shared`'s "THE ONE SENTENCE THAT MUST NOT BE 'IMPROVED' AWAY" plus its four numbered reasons is the maintainer ruling P15 generalizes; a separate pending plan (`kcc71f`) already owns a correction to that banner's direction. This plan must not touch it, and fact 4 explains why a naive sweep would hit it first.
- RUN THE SUITE BARE (AGENTS.md). `pyproject.toml` `addopts` already supplies quiet, parallel and the fast subset; a second `-q` would suppress the `N passed` line this plan requires pasted.

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | `ipd_lifecycle` frames the opt-in sandbox as the real fix for a determined agent | "hard enforcement against a determined same-user agent requires an OS sandbox or separate principal (`1o4eif`)" | E-03's primary subject; backlog `dvonrn` D7 assigns this exact wording to the `ariaau` audit by name |
| F-2 | A second site in the same file is HALF compliant and half justification | The role-gate honest limit: "an environment SELECTOR ... not a hardened boundary. A same-user worker with shell access can unset the variable. Hard enforcement is an OS sandbox / separate principal" | E-03 must keep the first two sentences and reframe only the third; deleting the whole note would remove a genuine limitation (P2) |
| F-3 | `orchestrate_isolation` calls honest-mistake guards "adversarial protections" | Module docstring E-04 line naming role collisions, leaked prose, shared-worktree conflicts, stale branches, lane timeouts as the hazards | E-04 reframes the label and keeps the hazard list, which is accurate |
| F-4 | The same module already models the P15-correct style in its most-cited line | "CRUCIAL: Per-lane green NEVER implies integrated green!" states a real failure mode with no attacker in sight | E-04 restates in the module's own established voice rather than inventing one |
| F-5 | The vocabulary is DENSEST in the compliant disclaimers | `runner_shared`'s baseline banner ("THE TARGET IS SLOPPINESS, NOT MALICE"), `host_sandbox_profile` ("explicitly NOT a boundary against a MALICIOUS same-user worker"), `attention_contract` ("NOT anti-malice crypto") | E-01 must CLASSIFY, not count; a pattern-matched sweep would damage the principle's own cited examples |
| F-6 | `run_ledger_store`'s tamper vocabulary is about DAMAGE, not attack | Its `NotALedgerError` exists so that "calling a healthy driver event log 'corrupt' accuses good data of damage it does not have"; `is_ledger_shaped` "can never mask real tampering" | Classified INTEGRITY and OUT of scope by E-01; integrity checking against corruption is honest-mistake protection |
| F-7 | `plan_readiness`'s forgery vocabulary is about a mistaken CLAIM, not an attacker | It refuses an unattested `- Readiness:` field; AGENTS.md records the measured case as an agent writing the field into four plans having run no review | Classified CLAIM and OUT of scope; P15 endorses attestations as "a conscious pause and an honest record, not a lock" |
| F-8 | `dvonrn` will edit the same `ipd_lifecycle` neighbourhood | `dvonrn` D1 deletes the token, `verify_driver_attestation` and the `lane_worktree_active` guess; D7 ties the sandbox wording to that deletion | E-02 exists to reconcile rather than collide, and E-03's wording must survive the token's later removal |
| F-9 | No test can validate this plan's output without violating P16 | P16 forbids asserting that exact phrases or docstrings exist in production files | This plan adds no test; the diffs plus an unchanged full suite are the evidence, stated in Required tests / validation |
| F-10 | Symbol NAMES carrying the vocabulary are a contract change, not a comment fix | `orchestrate_isolation` exports exception classes and `benchmark_scorer` defines an adversary-class vocabulary that is a data taxonomy, not a gate | E-04 records such a name and leaves it; renaming a public symbol is deliberately unscoped here |

## Proposed changes (ordered, validatable)

1. Build and classify the target census from Order 01's audit plus a fresh measurement (E-01).
2. Determine `dvonrn`'s landed state and reconcile the target list with it (E-02).
3. Reframe the two `ipd_lifecycle` sites, preserving every genuine limitation (E-03).
4. Reframe `orchestrate_isolation`'s module docstring, keeping the hazard list (E-04).

## Deferred / out of scope (with reason)

- EVERY HONEST-LIMIT DISCLAIMER (F-5). `runner_shared`'s baseline banner, `host_sandbox_profile`'s docstring, `attention_contract`'s `--by-human` note, and the `local-forgeable` labels in `work_cmd` all name a hostile agent in order to DENY protecting against one. They are P15-compliant and are the principle's cited model.
  - Carrier-Declined: Nothing is owed because these are not defects. Filing an item would assert the repository intends to remove its own record of what it does not defend against, which P15 requires it keep.
- THE INTEGRITY AND FORGERY VOCABULARY (F-6, F-7). `run_ledger_store`'s tamper-evident chain detects damage; `plan_readiness` refuses a claim no review substantiates. Neither targets an attacker.
  - Carrier-Declined: Nothing is owed because neither is anti-malice machinery. P15 explicitly endorses the attestation class, and corruption detection is outside its subject entirely.
- THE DRIVER ATTESTATION TOKEN AND ITS SURROUNDING CODE. Marked ALREADY DECIDED by backlog `ariaau` and designed in `dvonrn` D1. This plan reads that neighbourhood (E-02) and reframes only comment text that will outlive the token.
  - Carrier: dvonrn
- RENAMING ANY SYMBOL, EXCEPTION CLASS, OR CONSTANT that carries the vocabulary (F-10). A public symbol rename is a contract change with its own compatibility analysis, and no finding measures a defect in behavior. E-04 records any such name for a future decision.
  - Carrier-Declined: Nothing is owed because no defect was measured, only a naming preference. Filing an item would assert an intended rename that nobody has requested and whose blast radius is unmeasured.
- `runner_shared`'s BASELINE BANNER DIRECTION DEFECT. A real defect in the same neighbourhood (the banner's prohibition is stated without direction and is false as written against shipped code), but a different subject with its own measurement and its own spec amendment.
  - Carrier: kcc71f
- A DETERMINISTIC RULE FLAGGING NEW ANTI-MALICE JUSTIFICATIONS. Attractive under GUIDING_PRINCIPLES P11 and refused on this plan's own measurement: F-5 shows the vocabulary is densest in the COMPLIANT sites, so a pattern rule would fire overwhelmingly on correct code, and the JUSTIFICATION-versus-DISCLAIMER distinction is the judgement E-01 makes by reading.
  - Carrier-Declined: Nothing is owed because this is a rejected design rather than latent work. Filing it would imply the repository intends to build a rule whose false-positive behavior its own measurement predicts.

## Scope check

- Over-scope: none. Two files, comments and docstrings only. `agent_workflows/ipd_lifecycle.py` holds F-1 and F-2; `agent_workflows/orchestrate_isolation.py` holds F-3. No spec is declared because no spec states either wording: the sandbox's own spec position is `host_sandbox_profile`'s docstring (a class-(a) disclaimer, out of scope) and spec `7ckptx` R4.5's honest-limit wording already matches P15, as backlog `dvonrn` D8 measured and recorded.
- Under-scope: `agent_workflows/runner_shared.py`, `agent_workflows/host_sandbox_profile.py`, `agent_workflows/attention_contract.py`, `agent_workflows/run_ledger_store.py`, `agent_workflows/plan_readiness.py` and `agent_workflows/work_cmd.py` all carry the vocabulary and are deliberately NOT declared: F-5, F-6 and F-7 classify each as compliant. `agent_workflows/wtiso_gate.py` is not declared because Order 02 deletes its prose outright, and editing it here would collide. If E-01's census finds a JUSTIFICATION site outside the two declared files, that is a scope change to stop and re-declare rather than absorb; say so and file the residue if it is genuinely separate.

## Required tests / validation

- THIS PLAN ADDS NO TEST, and that is a measured consequence rather than an omission (F-9). Its entire output is comment and docstring text, and the only test that could check such an output is one asserting that a phrase exists in a production file, which AGENTS.md and GUIDING_PRINCIPLES P16 forbid in as many words ("No text, banner, or docstring pins"). Writing one would also recreate the exact defect Order 02 closes, where a citation outlived the thing it cited.
- Bare `python3 -m pytest` with the `N passed` summary line pasted, against a pre-execution baseline captured the same way BEFORE any edit lands, proving a comment-only change altered no behavior. A pre-existing failure must be shown pre-existing by that baseline rather than argued harmless.
- AN EXECUTABLE-LINES-UNCHANGED DEMONSTRATION for each edited file, and the method must be stated: show from the diff that every changed line is inside a comment or a docstring. This is the evidence that replaces a test, so it must be shown rather than asserted.
- `aw ipd lint --phase pre-transition` conforming, `aw check` no worse than a pre-change baseline with both counts pasted, and `aw sanitize --agent` clean.
- A CONFIRMATION THAT NO GENUINE LIMITATION WAS LOST (P2). For each reframed site, quote the limitation the original stated and show the replacement still states it. A reframing that reads better but tells the reader less has failed.

## Spec / documentation sync

- NO SPEC IS AMENDED, and `- Scope-Paths:` declares no `.spec.md` file. This is a measured claim rather than an assumption: backlog `dvonrn` D8 searched every `.spec.md` for the token, the location guess, the refusal code and the role vocabulary, and recorded that spec `7ckptx` R4.5's honest-limit wording "already matches P15 and stays". Neither wording this plan edits is stated normatively in any spec. The executor must re-confirm by searching the specs tree for the phrases being changed and report the result in V-03 and V-04.
- GUIDING_PRINCIPLES.md IS NOT EDITED. P15 already exists and already cites the design this Set implements; this plan applies the principle rather than amending it. Stated explicitly because "update the principle" is a plausible misreading of a plan whose whole subject is that principle's vocabulary.
- NO CHANGELOG ENTRY. Comment and docstring text only, with no user-visible behavior difference.
- THE AUDIT RECORD IS THE DURABLE EXPLANATION. Order 01's record carries the SIMPLIFY decision for each site reframed here and the evidence behind it, cited by `<id6>` from E-01. That is deliberate: a comment reworded with no record of why invites the next author to revert it, and a diff is not a place to argue a principle.
- HISTORICAL RECORDS ARE LEFT ALONE. Executed plans `1o4eif` (the sandbox), `u27oh3` (the token) and `8zgybk` (the adversarial scaffolding) record the framing this plan corrects; the plan contract forbids changing what an executed record records.

## Open questions

### OQ-01: Should the reframed `ipd_lifecycle` note keep pointing at the hardened sandbox at all?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: E-03 follows backlog `dvonrn` D7, which rules the sandbox stays and is REFRAMED as optional isolation an operator may choose, with nothing depending on it. So a pointer may remain provided it does not present the sandbox as the fix for a determined agent. The argument for keeping a pointer: the sandbox is real, shipped and occasionally the right choice, and an operator who wants isolation benefits from knowing where it is. The argument for dropping it: any mention beside a role check invites the inference that the check is a weak version of it, which is the framing being removed. NOT BLOCKING because both answers satisfy D7 and V-03's required evidence is identical: the anti-malice framing must be gone and the genuine limitation must survive.
- Carrier-Declined: No carrier is owed under either answer. Both are implemented inside E-03 and neither leaves work unbuilt; the audit record captures the SIMPLIFY decision regardless of which wording ships.

### OQ-02: Should this plan run before or after backlog `dvonrn` lands?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: E-02 makes the plan work in EITHER order by checking `dvonrn`'s landed state first and adjusting, and E-03 additionally requires the reframed wording to survive the token's later removal. So no dependency edge on `dvonrn` is declared, deliberately: declaring one would block a comment fix behind a much larger behavior change, and `dvonrn` carries `Blocks-Release: next` while this does not. The residual risk is a merge-level text collision in one neighbourhood of one file, which is ordinary and which the runner's isolated-worktree and merge-revalidate path already handles. Against that: running after `dvonrn` would be simpler, since some of fact 1 and fact 2 may already be fixed and this plan would shrink.
- Carrier-Declined: No carrier is owed under either answer. E-02 handles both states inside this plan, so nothing is left unbuilt in either order, and V-02 records which state was found.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted classified census for the whole vocabulary family across `agent_workflows/`, with EVERY hit assigned to JUSTIFICATION, DISCLAIMER or INTEGRITY-OR-CLAIM and the deciding words QUOTED for each, plus the three counts shown to sum to the total. Plus the `<id6>` of Order 01's audit record and a statement of how its SIMPLIFY rows for this family compare to the fresh census (a difference is a finding to record, not an error). Plus confirmation that `runner_shared`'s baseline banner, `host_sandbox_profile`'s docstring and `attention_contract`'s `--by-human` note were each classified DISCLAIMER and are NOT on the target list; misclassifying any of them fails this item, because rewording them would delete the repository's honest-limit record.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: a statement of backlog `dvonrn`'s landed state, evidenced by showing whether `mint_driver_attestation`, `verify_driver_attestation`, `DRIVER_ATTEST_ENV` and `lane_worktree_active` are present on disk, plus the resulting target-list adjustment. Where the token is still present, state how the reframed wording was written so it survives the token's later deletion without needing a second edit.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the `git diff` of `ipd_lifecycle`, shown to change comment text ONLY, with the method for confirming that stated from the diff. The diff must show: the anti-malice framing gone from both F-1 and F-2 sites; the GENUINE LIMITATION preserved, demonstrated by quoting the original limitation and its replacement side by side (the selector can be unset by a same-user worker); P15 cited so the framing reads as deliberate; and no executable line altered. Plus the result of searching the specs tree for the changed phrases, confirming no spec states them.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the `git diff` of `orchestrate_isolation`'s module docstring, shown to change docstring text only. The diff must show every named hazard from the original list PRESENT, the "adversarial protections" misnomer replaced with a description of the honest mistakes those protections catch, NO symbol or exception class renamed, and no executable line altered. Plus a statement of any symbol NAME found carrying the vocabulary and left alone per F-10, and the specs-tree search result for the changed phrases.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries NO `- Readiness:` field, whose absence is deliberate: that field is
an output of `/plan-review` and writing it at authoring time would forge the attestation a gate reads.

The executor must: perform E-01 through E-04 in order, respecting the declared `Depends on` edges; treat
E-01 as a HARD GATE, because the classification decides what may be edited and an unclassified sweep is the
one way this plan does damage; commit only the two paths in `- Scope-Paths:` via
`aw commit <plan> -- <paths>`; never push; paste the ACTUAL suite output for the no-behavior-change claim;
and verify each `V-*` in a separate pass from the `E-*` that produced it. Do NOT mark this plan executed or
move it to `.aw/records/plans/executed/` until every `V-*` carries concrete pasted evidence and
`aw ipd lint --phase pre-transition` conforms.

THE ONE WAY TO GET THIS PLAN WRONG is to treat the words as the target. This repository's honest-limit style
NAMES the hostile agent deliberately, in order to say plainly that a mechanism does NOT stop one, and those
disclaimers are what P15 holds up as correct. `runner_shared`'s baseline banner even tells you so in its own
text, which forbids anyone to "improve" its one load-bearing sentence away. If your diff touches that banner,
`host_sandbox_profile`'s docstring, or `attention_contract`'s `--by-human` note, you have inverted the
principle: you would be deleting the record of what this repository does not defend against, which is the
honest half of P15 and the more valuable one.

A SECOND WAY TO GET IT WRONG is to make the code sound stronger. P2 forbids aspirational documentation, and
the `AW_EXECUTION_ROLE` selector really can be unset by a same-user worker. The reframing removes the claim
that a stronger defense is the intended remedy; it must NOT remove the honest statement of what the selector
cannot do. If your replacement text tells a reader less about the mechanism's limits than the original did,
it is worse, not better.

A THIRD WAY TO GET IT WRONG is to add a test. There is no conforming test for a reworded comment: asserting a
phrase exists in a production file is exactly the docstring pin P16 forbids, and it would recreate the
stale-citation defect Order 02 exists to close. The diffs and an unchanged suite are the evidence.

Backlog item `ariaau` is this plan's origin (`- From-Backlog: ariaau`). That item carries NO
`- Blocks-Release:` gate and none is invented here. `Priority: low` is a deliberate downgrade from the item's
`medium`, recorded rather than silent: this is the only member of the Set that changes no behavior, deletes
no code and closes no dangling citation, so it is the least urgent of the three. The `chore` classification
is inherited and confirmed: nothing a user perceives changes, and the cost this closes falls on the next
author who reads an anti-malice justification and takes it as the house style.
