# IPD: Reframe every determined same-user and malicious agent justification as the honest-mistake guard it actually is

- Date: 2026-09-30
- Kind: child
- Concern: GUIDING_PRINCIPLES P15 forbids building against a hostile agent AND forbids justifying a mechanism by naming one ("WHAT NOT TO BUILD: ... any mechanism whose justification is 'in case the agent lies'"). Two sites in the shipped package still offer that justification. `ipd_lifecycle` tells a reader that "hard enforcement against a determined same-user agent requires an OS sandbox or separate principal (`1o4eif`)", which frames the opt-in sandbox as the real answer to a hostile agent; backlog `dvonrn` D7 rules the opposite ("REFRAME, do not rebuild: it is OPTIONAL ISOLATION an operator may choose, NOT 'the real fix for malicious agents'"). `orchestrate_isolation` advertises "Seeded orchestration adversarial protections" for a list of hazards (role collisions, leaked prose, shared-worktree conflicts, stale branches, lane timeouts) that are every one of them honest-mistake hazards, so the word misdescribes the mechanism and invites the next author to extend it in the wrong direction. Left alone, each site teaches a future author that anti-malice reasoning is the house style, which is how the machinery P15 exists to stop gets rebuilt.
- Scope: Reframe the small number of comment and docstring sites whose stated JUSTIFICATION for a mechanism is a hostile agent, so each states the honest mistake it actually catches. Two sites are confirmed at authoring (`ipd_lifecycle`'s sandbox pointer, `orchestrate_isolation`'s module docstring) and the executor re-derives the full list from Order 01's audit. EXCLUDES every HONEST-LIMIT DISCLAIMER that names a hostile agent in order to deny protecting against it, which is P15-compliant already and must be left alone. EXCLUDES all behavior: no predicate, refusal, exit code, message a user sees, or test outcome changes. EXCLUDES the driver-attestation comments deleted by backlog `dvonrn`, the `wtiso_gate` prose deleted by Order 02, and every dangling test citation.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/orchestrate_isolation.py
- Item-Dependencies: executed:bec7ee, executed:38pxaz
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: ariaau
- Set: malgate
- Order: 3
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: dmjp0u
- Approval: 2026-10-01, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-01 approved (aw set): status set to approved

- 2026-10-01 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): plan-review complete; 7 findings all fixed; the census family was corrected because the authored one could not reach one of the plan's own two named subjects, and both reviewer-owned open questions are resolved.
- 2026-10-01 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-401 (BLOCKER, fixed), PR-402 (HIGH, fixed), PR-403 (MEDIUM, fixed), PR-404 (MEDIUM, fixed), PR-405 (MEDIUM, fixed), PR-406 (LOW, fixed), PR-407 (LOW, fixed). Plan byte-identical to the lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent` reported `clean` before semantic review and `--phase review-finalize --agent` reports `clean` with zero findings after revision; this plan is `- Kind: child`, so the `IPD-S407` orchestrator row check does not apply. EVERY ONE OF F-1 THROUGH F-10 WAS RE-DRIVEN RATHER THAN READ, and the plan's central judgement is right: both target sites exist verbatim (`ipd_lifecycle:4383` "hard enforcement against a determined same-user agent requires an OS sandbox or separate principal", `orchestrate_isolation`'s docstring "Seeded orchestration adversarial protections"), the three disclaimers it fences off are all real and all P15's own cited model, and its refusal to add a test is correct under P16. THE DOMINANT FINDING IS THAT THE PLAN WAS UNEXECUTABLE AS WRITTEN FOR THE SAME CLASS OF REASON ITS SIBLINGS WERE: E-01's declared search family (`malicious`, `determined same-user`, `hostile`, `adversarial`) DOES NOT MATCH THE F-2 SITE AT ALL, whose words are "not a hardened boundary", "can unset the variable" and "Hard enforcement is an OS sandbox / separate principal". An executor running exactly the authored census would therefore build a target list with F-2 ABSENT and then be instructed by E-03 to edit it; `determined same-user` matches exactly ONE line in the whole package, which is F-1. Fixed by adding a FRAMING family beside the vocabulary one and by making V-01 fail outright if the census does not contain F-2. THE SECOND MEASUREMENT RESHAPES THE PLAN'S OWN SEQUENCING: `dvonrn` is no longer a backlog item to check but `- Status: graduated` into Set `lifegate`, and its child `e25iy9` (`Blocks-Release: next`, `bug`, `high`) declares the F-1 comment EXPLICITLY in its E-04, so F-1 is double-declared and E-02 now resolves it to a definite disposition in both states rather than assuming the comment will still be there. A third measurement replaced the authored three-class scheme, which left 25 of 30 vocabulary hits unclassifiable: 14 are `benchmark_scorer`'s seeded-case data taxonomy, 8 are `run_analytics_*` describing hostile INPUT DATA rather than an agent, and 3 are `wtiso_gate`'s citations of a deleted test file, so the defect-to-noise ratio is 2 in 30 and a word-keyed sweep would be wrong 28 times. Two further corrections: F-10 asserted `orchestrate_isolation` carries vocabulary-bearing symbol names and an AST walk found NONE (its twelve exception classes are named for the condition, which is already the P15-correct style), and `tests/test_orchestrate_isolation.py` carries the near-identical "Seeded orchestration adversarial suite" line while sitting outside `- Scope-Paths:`, so E-04 now forbids editing it and explains why the word is accurate there. BOTH OPEN QUESTIONS CARRIED `Owner: reviewer` AND ARE NOW RESOLVED: OQ-01 to DROP the sandbox pointer from the F-2 site entirely (the two sites are not symmetric, and at F-2 the mention is pure inference bait while the sandbox's position is already stated at its own home in `host_sandbox_profile`), and OQ-02 to declare NO dependency edge, on the measured grounds that the two plans are in different Sets so no runner ordering applies anyway, that an edge would gate a `chore`/`low` comment fix on a `bug`/`high` release blocker, and that E-02 now makes both orders safe. Baseline measured in this lane: `3527 passed, 2 skipped, 3 warnings in 64.58s`, 208 deselected; `aw check` 70 findings with ZERO attributable to this plan. Full findings and decisions: `.aw/records/reviews/20260930-malgate-03-dmjp0u-reframe-every-determined-same-user-and-malicious-agent-justi.review.md`.
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

2. A NEARLY IDENTICAL SITE SITS IN THE SAME FILE, AND IT IS THIS PLAN'S ALONE. The worker-role block's honest
   limit reads "this is an environment SELECTOR ... not a hardened boundary. A same-user worker with shell
   access can unset the variable. Hard enforcement is an OS sandbox / separate principal (x03wgn, Phase 6
   `1o4eif`)". Its FIRST half is a compliant disclaimer; only its closing "hard enforcement is" clause is a
   justification. CORRECTED AT REVIEW on two points. FIRST, this site is NOT shared with `dvonrn`: `e25iy9`
   declares only the TOKEN block (F-1), and spec `7ckptx` R4.5's matching honest-limit sentence is kept
   VERBATIM by its E-09, so nothing else claims these three lines. SECOND, and decisively, this site is the
   one the authored census COULD NOT FIND, because none of the four authored search terms appears in it
   (F-11). That is why E-01 now carries a framing family and why V-01 fails if the census misses it.

3. `orchestrate_isolation`'s LABEL MISDESCRIBES ITS OWN MECHANISM. Its module docstring advertises "E-04:
   Seeded orchestration adversarial protections against role collisions, leaked prose, unauthorized
   mutations, shared-worktree conflicts, stale branches, lane timeouts, and unsafe background completions".
   Every hazard named is an honest-mistake hazard: a forgetful agent collides roles, a stale branch is a
   timing accident, a lane timeout is a hang. The module's actual refusals are merge-safety and
   role-isolation checks, and its most-cited line is the P15-shaped "Per-lane green NEVER implies integrated
   green!". So the word "adversarial" is a misnomer inherited from the research vocabulary, not a
   description of what the code does.

4. THE VOCABULARY IS DENSEST OUTSIDE THE DEFECT, which is why a pattern-matched sweep would do damage.
   `runner_shared`'s pre-work-baseline banner, four numbered reasons ending "THE TARGET IS SLOPPINESS, NOT
   MALICE", is the maintainer ruling P15 generalizes and its own text forbids anyone to "improve" it away.
   QUANTIFIED AT REVIEW, which sharpens the authored claim: of 30 vocabulary hits across
   `agent_workflows/*.py`, just TWO are this plan's subject (F-1 and F-3), THREE are the compliant
   disclaimers, and the remaining 25 are not gates at all (14 the `benchmark_scorer` seeded-case taxonomy,
   8 `run_analytics_*` describing untrusted INPUT DATA, 3 `wtiso_gate` citations of a deleted test FILE that
   Order 02 removes). So the ratio of defect to noise is 2 in 30, and a sweep keyed on the words would be
   wrong 28 times. That is the measurement behind E-01's five-class scheme.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: derive the target list, and prove what is NOT in it

- [ ] E-01 BUILD THE TARGET LIST FROM ORDER 01's AUDIT PLUS YOUR OWN RE-MEASUREMENT, and classify every hit before editing a character. Read the audit record Order 01 produced (cite it by `<id6>`) and take its SIMPLIFY rows for this family as the starting list. THE SEARCH FAMILY IS NOT THE AUTHORED ONE, corrected at review for a measured reason stated in F-11: the authored family (`malicious`, `determined same-user`, `hostile`, `adversarial`) DOES NOT MATCH THE F-2 SITE AT ALL. That site's words are "not a hardened boundary", "can unset the variable" and "Hard enforcement is an OS sandbox / separate principal", none of which contains any of the four terms, so an executor who ran exactly the authored census would build a target list with F-2 ABSENT and would then be told by E-03 to edit it. Search the UNION of two families: (a) the VOCABULARY family `malicious`, `malice`, `determined same-user`, `hostile`, `adversarial`, `adversary`, `tamper`, `forge`, `deception`, and (b) the FRAMING family, which is what actually finds a justification whose words are mild: `hard enforcement`, `hardened boundary`, `real fix`, `requires an OS sandbox`, `separate principal`, plus any sentence pointing at `1o4eif` or `host_sandbox_profile` as a remedy. Report BOTH families' hits.
  - THEN CLASSIFY INTO FIVE CLASSES, NOT THREE. Measured at review over `agent_workflows/*.py`: the authored three-class scheme leaves 25 of 30 vocabulary hits unclassifiable, because 14 are `benchmark_scorer`/`benchmark_metrics`'s `ADVERSARIAL_CLASSES` data taxonomy (a corpus of seeded false-completion cases, not a gate at all), 8 are `run_analytics_*` describing HOSTILE INPUT DATA (a malformed JSON value, a manifest path, an undecodable byte: input validation, which is not an agent at all), and 3 are `wtiso_gate`'s dangling `tests/test_wtiso_adversarial.py` FILENAME citations that Order 02 deletes outright. None is a JUSTIFICATION, a DISCLAIMER, or an INTEGRITY-OR-CLAIM, so forcing them into those three would either misfile them or silently drop them from the sum E-01 must report. Use: JUSTIFICATION (the hostile agent is the reason the mechanism exists, or the named fix for its weakness) which is IN scope; DISCLAIMER (names the hostile agent to deny protecting against one) OUT of scope; INTEGRITY-OR-CLAIM (damage, or a mistaken attestation, rather than an attacker) OUT of scope; HOSTILE-INPUT (untrusted DATA, not an agent) OUT of scope; VOCABULARY-ONLY (a data taxonomy, a test filename, or other naming carrying the word with no mechanism behind it) OUT of scope. Quote the deciding words for every classification and report all five counts.
  - Depends on: none
  - Expected outcome: the classified census pasted for BOTH search families, with each JUSTIFICATION site named by symbol and each OUT-of-scope classification carrying the quoted words that decided it. The five counts must sum to the total hits found. The census MUST contain the F-2 site (`ipd_lifecycle`'s role-gate honest limit), which is the proof the corrected framing family works; a census that does not reach it has reproduced the authored defect and fails this item.
  - Execution state: pending

- [ ] E-02 CHECK WHETHER `dvonrn`'s WORK HAS LANDED, and reconcile rather than collide. THE CARRIER IS NO LONGER THE BACKLOG ITEM, corrected at review (F-12): `dvonrn` is `- Status: graduated` with `- Graduated-To: lifegate`, and its D1/D7 work now lives in FOUR pending plans (`u4glub` Order 0, `urv602` Order 1 `reviewed`, `e25iy9` Order 2, `m47znv` Order 3), so "has `dvonrn` landed" is answered by those plans' disposition and not by the item. The one that matters is `e25iy9`, whose own E-04 says in as many words: "Also remove the honest-limit comment block that names the token and points at `1o4eif` as the fix for a 'determined same-user agent'". THAT IS THE F-1 SITE, SO F-1 HAS TWO DECLARED OWNERS, and `e25iy9` carries `- Blocks-Release: next` while this plan does not. Determine the state on disk by checking whether `mint_driver_attestation`, `verify_driver_attestation`, `DRIVER_ATTEST_ENV` and `lane_worktree_active` are present in `ipd_lifecycle`. IF THEY ARE GONE, `e25iy9` has executed and the F-1 site went with it: do NOT re-add a reframed comment where code no longer exists; record that F-1 is closed by `e25iy9` and reduce this plan to F-2 and F-3. IF THEY ARE PRESENT, F-1 is still there and you may reframe it, but write the replacement so it says nothing about the token, so that `e25iy9` deleting the surrounding block later removes your text cleanly rather than stranding a comment about a mechanism that no longer exists. EITHER WAY, F-2 AND F-3 ARE UNAMBIGUOUSLY THIS PLAN'S: no sibling declares the role-gate SELECTOR block at `ipd_lifecycle` lines 66-68 (`e25iy9` names only the token block, and spec `7ckptx` R4.5's honest-limit sentence is kept VERBATIM by its E-09), and no plan in either Set touches `orchestrate_isolation` at all.
  - Depends on: E-01
  - Expected outcome: a recorded statement of which of the four `lifegate` plans have reached `executed`, the presence or absence of the four token symbols pasted, the resulting adjustment to the target list (explicitly whether F-1 is still this plan's to edit or is closed by `e25iy9`), and (where the token is present) confirmation that the reframed wording names no token and so survives its deletion.
  - Execution state: pending

### Task group 2: reframe the justifications

- [ ] E-03 REFRAME THE `ipd_lifecycle` SITES per facts 1 and 2, preserving every true statement and removing only the anti-malice framing. For the role-gate honest limit: KEEP the accurate part ("an environment SELECTOR, not a hardened boundary", and that a same-user worker can unset the variable, which is the honest limit a reader needs), and REPLACE the closing "hard enforcement is an OS sandbox / separate principal" clause, which frames a stronger defense as the intended direction. State instead what the selector is FOR: it tells a managed worker plainly that the lifecycle transition is the runner's step, which is the one honest mistake actually observed (a worker forking a second receipt), and cite P15 so the next reader knows the framing is deliberate. PER OQ-01, RESOLVED AT REVIEW: the F-2 replacement carries NO sandbox pointer and no `1o4eif` citation at all. At this site the mention is pure inference bait, since nothing in the neighbourhood concerns isolation, and the sandbox's position is already stated at its own home in `host_sandbox_profile`'s docstring. Dropping it loses no true statement because the genuine limitation is a separate sentence you keep. For the sandbox pointer beside the attestation gate (F-1), FIRST honor E-02's verdict: if `e25iy9` already deleted that block, there is nothing to edit and this clause is satisfied by recording that; otherwise apply `dvonrn` D7's ruling that the hardened profile is OPTIONAL ISOLATION an operator may choose and that NOTHING may depend on it being on, rather than the real fix for a determined agent, and write it without naming the token so `e25iy9` can delete the block cleanly. Do NOT weaken or remove any statement of a genuine limitation. A reader must still learn that the selector can be unset.
  - DO NOT EDIT SPEC `7ckptx` R4.5. Its honest-limit sentence ("an environment selector and not a hardened boundary") is a DISCLAIMER that `dvonrn` D8 measured as already matching P15, and `e25iy9`'s E-09 keeps it VERBATIM. This plan declares no spec and must not create a conflicting spec edit.
  - Depends on: E-02
  - Expected outcome: the `git diff` of `ipd_lifecycle`, showing comment text only, the genuine limitations preserved, the anti-malice framing gone, and no executable line altered.
  - Execution state: pending

- [ ] E-04 REFRAME `orchestrate_isolation`'s MODULE DOCSTRING per fact 3, so the label matches the mechanism. Replace "Seeded orchestration adversarial protections against ..." with a description of what those protections actually catch: the honest-mistake hazards already listed (role collisions, leaked prose, unauthorized mutations, shared-worktree conflicts, stale branches, lane timeouts, unsafe background completions) are things a FORGETFUL or MISTAKEN orchestrator does, and the module's refusals exist to catch them early with a clear message. Keep every named hazard: the list is accurate and is the module's contents page. Do NOT rename any symbol, exception class, or test; this is a docstring change. A SYMBOL CENSUS WAS RUN AT REVIEW AND IS REPORTED IN F-10, so the executor need not rediscover it: an AST walk of `orchestrate_isolation` finds NO symbol carrying the vocabulary (its twelve exception classes are named for the CONDITION, `StaleBaseError`, `LaneExecutionTimeoutError`, `CombinedRevalidationFailedError`, which is already the P15-correct style), while `benchmark_scorer` holds `ADVERSARIAL_CLASSES` and `adversary_class`, both out of scope as a data taxonomy. Re-derive it to confirm and report the result; if it differs, record the difference and still leave every name alone.
  - DO NOT EDIT `tests/test_orchestrate_isolation.py`, which is NOT in `- Scope-Paths:` and must not be added. Measured at review (F-13): its own module docstring carries the near-identical line "E-04 / V-04: Seeded orchestration adversarial suite", so an executor sweeping the phrase will find it and be tempted. Leave it. It is a TEST docstring describing a test suite that genuinely does seed adversarial cases, so the word is accurate there in a way it is not in the production module, which claims the protections THEMSELVES are adversarial. Record the sighting in the evidence so the next reader knows it was seen and deliberately left, and do not file a carrier for it.
  - Depends on: E-03
  - Expected outcome: the `git diff` of the module docstring, showing the hazard list intact, the misnomer replaced, no symbol renamed, no executable line altered, and `tests/test_orchestrate_isolation.py` absent from the diff.
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
| F-8 | `e25iy9` will edit the same `ipd_lifecycle` neighbourhood, and declares the F-1 comment explicitly | `dvonrn` D1 deletes the token, `verify_driver_attestation` and the `lane_worktree_active` guess; D7 ties the sandbox wording to that deletion. Its graduated carrier `e25iy9` E-04 says "Also remove the honest-limit comment block that names the token and points at `1o4eif` as the fix for a 'determined same-user agent'" | E-02 exists to reconcile rather than collide, and E-03's wording must name no token so it survives the removal. Superseded in part by F-12, which measures that the carrier is the PLAN and that F-1 is therefore double-declared |
| F-9 | No test can validate this plan's output without violating P16 | P16 forbids asserting that exact phrases or docstrings exist in production files | This plan adds no test; the diffs plus an unchanged full suite are the evidence, stated in Required tests / validation |
| F-10 | Symbol NAMES carrying the vocabulary are a contract change, not a comment fix | MEASURED AT REVIEW by an AST walk: `orchestrate_isolation` has NO symbol carrying the vocabulary (its twelve exception classes name the CONDITION: `StaleBaseError`, `LaneExecutionTimeoutError`, `CombinedRevalidationFailedError`); `benchmark_scorer` defines `ADVERSARIAL_CLASSES` and `adversary_class`, a data taxonomy, not a gate | E-04 reports the census and leaves every name alone; renaming a public symbol is deliberately unscoped. The authored row implied `orchestrate_isolation` had such names, which measurement disproved |
| F-11 | THE AUTHORED SEARCH FAMILY CANNOT FIND THE F-2 SITE, so the plan was unexecutable as written | E-01's family was `malicious`, `determined same-user`, `hostile`, `adversarial`. The F-2 site reads "not a hardened boundary. A same-user worker with shell access can unset the variable. Hard enforcement is an OS sandbox / separate principal" and contains NONE of the four terms (verified by grepping the three lines for the family: zero matches). Across `agent_workflows/*.py` the family returns 30 hits and `determined same-user` matches exactly ONE line, `ipd_lifecycle:4383`, which is F-1 | E-01 now searches a VOCABULARY family plus a FRAMING family (`hard enforcement`, `hardened boundary`, `real fix`, `separate principal`, pointers at `1o4eif`), and V-01 FAILS the item if the census does not contain F-2 |
| F-12 | `dvonrn` IS ALREADY GRADUATED, and one of its children declares the F-1 site this plan also claims | `dvonrn` is `- Status: graduated`, `- Graduated-To: lifegate`, with four pending plans (`u4glub`, `urv602`, `e25iy9`, `m47znv`). `e25iy9`'s E-04: "Also remove the honest-limit comment block that names the token and points at `1o4eif` as the fix for a 'determined same-user agent'". `e25iy9` carries `- Blocks-Release: next`; this plan does not | E-02 rewritten to read the state from the four plans rather than the item, and to make F-1 CONDITIONAL: closed by `e25iy9` if the token is gone, reframed token-free if present. F-2 and F-3 are unambiguously this plan's |
| F-13 | A test file carries the same phrase E-04 replaces and is NOT in `- Scope-Paths:` | `tests/test_orchestrate_isolation.py`'s module docstring reads "E-04 / V-04: Seeded orchestration adversarial suite"; the declared scope is only the two `agent_workflows/` files | E-04 forbids editing it and explains why the word is ACCURATE there (the suite really does seed adversarial cases) while it is a misnomer in the production module; V-04 requires the diff to show the test file absent |

## Proposed changes (ordered, validatable)

1. Build and classify the target census from Order 01's audit plus a fresh measurement, over the vocabulary AND framing families, into five classes (E-01).
2. Determine the `lifegate` Set's landed state and reconcile the target list with it, deciding whether F-1 is still this plan's (E-02).
3. Reframe the two `ipd_lifecycle` sites, preserving every genuine limitation (E-03).
4. Reframe `orchestrate_isolation`'s module docstring, keeping the hazard list (E-04).

## Deferred / out of scope (with reason)

- EVERY HONEST-LIMIT DISCLAIMER (F-5). `runner_shared`'s baseline banner, `host_sandbox_profile`'s docstring, `attention_contract`'s `--by-human` note, and the `local-forgeable` labels in `work_cmd` all name a hostile agent in order to DENY protecting against one. They are P15-compliant and are the principle's cited model.
  - Carrier-Declined: Nothing is owed because these are not defects. Filing an item would assert the repository intends to remove its own record of what it does not defend against, which P15 requires it keep.
- THE INTEGRITY AND FORGERY VOCABULARY (F-6, F-7). `run_ledger_store`'s tamper-evident chain detects damage; `plan_readiness` refuses a claim no review substantiates. Neither targets an attacker.
  - Carrier-Declined: Nothing is owed because neither is anti-malice machinery. P15 explicitly endorses the attestation class, and corruption detection is outside its subject entirely.
- THE DRIVER ATTESTATION TOKEN AND ITS SURROUNDING CODE. Marked ALREADY DECIDED by backlog `ariaau` and designed in `dvonrn` D1, which is now GRADUATED into Set `lifegate` (F-12), so the live carrier is the plan and not the item. This plan reads that neighbourhood (E-02) and reframes only comment text that will outlive the token.
  - Carrier: e25iy9
- THE F-1 COMMENT ITSELF IS DOUBLE-DECLARED, and this is recorded rather than resolved by an ordering edge. `e25iy9`'s E-04 removes the same honest-limit block this plan's E-03 reframes. No `- Item-Dependencies:` edge is added, deliberately, for the reason OQ-02 gives: `e25iy9` carries `- Blocks-Release: next` and is a much larger behavior change, so gating a comment fix behind it inverts the urgency, and E-02 makes this plan correct in either order (reframe a token-free replacement, or record F-1 as closed). The accepted residual risk is a text-level merge collision in one neighbourhood of one file, which the runner's isolated-worktree and merge-revalidate path handles.
  - Carrier: e25iy9
- RENAMING ANY SYMBOL, EXCEPTION CLASS, OR CONSTANT that carries the vocabulary (F-10). A public symbol rename is a contract change with its own compatibility analysis, and no finding measures a defect in behavior. E-04 records any such name for a future decision.
  - Carrier-Declined: Nothing is owed because no defect was measured, only a naming preference. Filing an item would assert an intended rename that nobody has requested and whose blast radius is unmeasured.
- `runner_shared`'s BASELINE BANNER DIRECTION DEFECT. A real defect in the same neighbourhood (the banner's prohibition is stated without direction and is false as written against shipped code), but a different subject with its own measurement and its own spec amendment.
  - Carrier: kcc71f
  - Carrier-Evidence: .aw/records/plans/executed/20260929-aced01-01-kcc71f-name-the-direction-the-pre-work-suite-baseline-prohibition-f.ipd.md
- A DETERMINISTIC RULE FLAGGING NEW ANTI-MALICE JUSTIFICATIONS. Attractive under GUIDING_PRINCIPLES P11 and refused on this plan's own measurement: F-5 shows the vocabulary is densest in the COMPLIANT sites, so a pattern rule would fire overwhelmingly on correct code, and the JUSTIFICATION-versus-DISCLAIMER distinction is the judgement E-01 makes by reading.
  - Carrier-Declined: Nothing is owed because this is a rejected design rather than latent work. Filing it would imply the repository intends to build a rule whose false-positive behavior its own measurement predicts.

## Scope check

- Over-scope: none. Two files, comments and docstrings only. `agent_workflows/ipd_lifecycle.py` holds F-1 and F-2; `agent_workflows/orchestrate_isolation.py` holds F-3. No spec is declared because no spec states either wording: the sandbox's own spec position is `host_sandbox_profile`'s docstring (a class-(a) disclaimer, out of scope) and spec `7ckptx` R4.5's honest-limit wording already matches P15, as backlog `dvonrn` D8 measured and recorded.
- Under-scope: `agent_workflows/runner_shared.py`, `agent_workflows/host_sandbox_profile.py`, `agent_workflows/attention_contract.py`, `agent_workflows/run_ledger_store.py`, `agent_workflows/plan_readiness.py` and `agent_workflows/work_cmd.py` all carry the vocabulary and are deliberately NOT declared: F-5, F-6 and F-7 classify each as compliant. `agent_workflows/wtiso_gate.py` is not declared because Order 02 deletes its prose outright, and editing it here would collide. The five `agent_workflows/run_analytics_*.py` files and the two `benchmark_*` files are likewise NOT declared, and the reason is the new HOSTILE-INPUT and VOCABULARY-ONLY classes E-01 adds: measured at review, 8 of the 30 vocabulary hits are analytics code describing untrusted DATA (a malformed JSON value, a manifest path, an undecodable byte) and 14 are the benchmark corpus's seeded-case taxonomy, so neither family is a gate against an agent and neither is in P15's subject at all. `tests/test_orchestrate_isolation.py` is not declared either, per F-13. If E-01's census finds a JUSTIFICATION site outside the two declared files, that is a scope change to stop and re-declare rather than absorb; say so and file the residue if it is genuinely separate.

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
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW - DROP THE POINTER FROM THE F-2 SITE, and keep one only at F-1 if that site still exists. The question was addressed to the reviewer, so leaving it open would strand it. The deciding evidence is that the two sites are not symmetric, which the authored question treated as one case. AT F-2 (the role-gate selector block) the sandbox mention is PURE INFERENCE BAIT: nothing in that neighbourhood concerns isolation, the sentence exists only to say what the selector is not strong enough to do, and that is precisely the "weak version of a real defense" reading P15 forbids. Dropping it loses NO true statement, because the genuine limitation ("a same-user worker with shell access can unset the variable") is a separate sentence that E-03 keeps. AT F-1 the mention is at least topical, since that block is about the token gate, so D7's reframed pointer may stay there. THE REPOSITORY ALREADY MODELS THIS SPLIT: `host_sandbox_profile`'s own docstring is where the sandbox's position is stated ("explicitly NOT a boundary against a MALICIOUS same-user worker"), which is a DISCLAIMER at the mechanism's own home and is out of scope here, so an operator who wants isolation is not deprived by removing a cross-reference from an unrelated gate. CONSEQUENCE FOR THE EXECUTOR: E-03's F-2 replacement must contain no sandbox pointer and no `1o4eif` citation at all; V-03 already demands the anti-malice framing be gone and the limitation survive, which this satisfies.
- Carrier-Declined: No carrier is owed. The answer is implemented inside E-03 and leaves nothing unbuilt; the audit record captures the SIMPLIFY decision either way.

### OQ-02: Should this plan run before or after the `lifegate` Set lands?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW - RUN IN EITHER ORDER, DECLARE NO EDGE, and the question's premise is corrected first. The authored question asks about "backlog `dvonrn`", which measurement shows is already `- Status: graduated` into Set `lifegate` (F-12), so the real question is whether to declare an edge on its child `e25iy9`. The answer is NO, on three pieces of evidence rather than on the authored cost argument. FIRST, the two plans are in DIFFERENT SETS, so no runner ordering exists to lean on in any case: `aw oc run <setid>` orders within a Set, and a cross-Set edge would have to be an explicit `- Item-Dependencies:` entry. SECOND, declaring one would invert the urgency measurably: `e25iy9` carries `- Blocks-Release: next` and `- Work-Kind: bug` with `- Priority: high`, while this plan is `chore`/`low`, so gating the comment fix on the release blocker means the trivial change waits on the largest one in the neighbourhood. THIRD, and this is what makes it safe rather than merely convenient, E-02 as revised now resolves F-1 to a definite disposition in BOTH states (reframe a token-free replacement if the block is present, record it closed by `e25iy9` if gone), and F-2 and F-3 are unaffected by `e25iy9` entirely, so neither order can leave work unbuilt or double-done. THE RESIDUAL RISK, named and accepted: a text-level merge collision in one neighbourhood of `ipd_lifecycle` if both execute concurrently, which the runner's isolated-worktree plus merge-and-revalidate path is built to handle and which AGENTS.md says not to raise as a runtime hazard.
- Carrier-Declined: No carrier is owed. E-02 handles both states inside this plan, so nothing is left unbuilt in either order, and V-02 records which state was found.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted classified census for BOTH search families (vocabulary AND framing) across `agent_workflows/`, with EVERY hit assigned to one of the FIVE classes (JUSTIFICATION, DISCLAIMER, INTEGRITY-OR-CLAIM, HOSTILE-INPUT, VOCABULARY-ONLY) and the deciding words QUOTED for each, plus the five counts shown to sum to the total. THE F-2 SITE MUST APPEAR IN THE CENSUS AND BE CLASSIFIED JUSTIFICATION (its "Hard enforcement is an OS sandbox / separate principal" clause); its absence proves the executor ran the authored vocabulary-only family, which F-11 measured cannot reach it, and fails this item. Plus the `<id6>` of Order 01's audit record and a statement of how its SIMPLIFY rows for this family compare to the fresh census (a difference is a finding to record, not an error). Plus confirmation that `runner_shared`'s baseline banner, `host_sandbox_profile`'s docstring and `attention_contract`'s `--by-human` note were each classified DISCLAIMER and are NOT on the target list; misclassifying any of them fails this item, because rewording them would delete the repository's honest-limit record.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: a statement of `dvonrn`'s landed state read from its FOUR graduated `lifegate` plans rather than from the item (F-12), naming each plan's `- Status:`, evidenced by showing whether `mint_driver_attestation`, `verify_driver_attestation`, `DRIVER_ATTEST_ENV` and `lane_worktree_active` are present on disk, plus the resulting target-list adjustment. MUST state explicitly whether F-1 was edited here or recorded as closed by `e25iy9`, since both are correct answers and the evidence must say which happened. Where the token is still present, show that the replacement text names no token, which is what makes it survive `e25iy9`'s later deletion without a second edit.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the `git diff` of `ipd_lifecycle`, shown to change comment text ONLY, with the method for confirming that stated from the diff. The diff must show: the anti-malice framing gone from both F-1 and F-2 sites (or F-1 recorded closed by `e25iy9` per V-02); the GENUINE LIMITATION preserved, demonstrated by quoting the original limitation and its replacement side by side (the selector can be unset by a same-user worker); P15 cited so the framing reads as deliberate; the F-2 replacement shown to contain NO sandbox pointer and no `1o4eif` citation, which is OQ-01's resolved answer; `7ckptx` shown absent from the diff; and no executable line altered. Plus the result of searching the specs tree for the changed phrases, confirming no spec states them.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the `git diff` of `orchestrate_isolation`'s module docstring, shown to change docstring text only, and shown to contain NO path other than `agent_workflows/orchestrate_isolation.py` (specifically not `tests/test_orchestrate_isolation.py`, per F-13). The diff must show every named hazard from the original list PRESENT, the "adversarial protections" misnomer replaced with a description of the honest mistakes those protections catch, NO symbol or exception class renamed, and no executable line altered. Plus the re-derived symbol census result compared against F-10's (NO vocabulary-carrying symbol in this module; `ADVERSARIAL_CLASSES`/`adversary_class` in `benchmark_scorer`, out of scope), and the specs-tree search result for the changed phrases.
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

A FOURTH WAY TO GET IT WRONG, and the one review measured actually happening, is to run the census as a plain
vocabulary grep. The authored family could not reach the F-2 site at all (F-11), so an executor who greps the
four words, finds 30 hits, classifies them and starts editing will have a target list that is MISSING one of
the plan's own two named `ipd_lifecycle` subjects while being padded with 25 hits that are not gates at all.
The corrected E-01 searches a FRAMING family as well, and V-01 fails the item outright if the census does not
contain F-2. A justification does not have to use the word "malicious" to be one; "hard enforcement is an OS
sandbox" is the whole defect, in mild words.

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
