# Review: stop losing a deliberate history message and make durable history survive a clone, child vhbvwz (Set setterguard)

- Subject-Id: vhbvwz
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `be6d2ab9`. Structural preflight `aw ipd lint --phase author` conformed (clean, 0
findings) before semantic review; `--phase review-finalize` conformed after the revisions, having
first correctly refused `E-02b` as an invalid item id (`IPD-I302`/`IPD-I305`) and then correctly
refused the renumbered `E-08` until it had its own validation item (`IPD-I303`). Both refusals were
the linter doing its job on my edits. No pre-review snapshot was needed: the plan was already
committed at `fb24832a`.

DISCLOSURE: authored in the same repository and by the same model family as the plan, so treat this
as a near-self-review and worth less than an independent one.

THE PLAN'S DIAGNOSIS OF ITS TWO NAMED DEFECTS IS CORRECT AND ITS RESTRAINT IS EXEMPLARY. The early
return really does precede the history write, so a same-status `--message` is discarded; the durable
sidecar really is gitignored, so the store `awhistory-02` relied on does not survive a clone; and the
three `aw specs note` records from the 2026-09-10 cleanup really do exist only in that sidecar (I
verified all four in it, dated `20260910`, and confirmed each spec carries exactly one inline
record). The plan also refuses to revert `awhistory-02`'s slimming, correctly identifying it as a
reviewed decision rather than a bug, and it says so in capitals having already been wrong about it
once. That self-correction is the kind of thing that makes a plan trustworthy, and it is why the
findings below are about what the plan PROPOSED rather than what it observed.

ONE BLOCKER CHANGES THE SHAPE OF THE WHOLE SET, and it was found by patching E-02 exactly as written
and measuring the result. E-02 instructed the executor to preserve prior records AND to use
NEWEST-FIRST ordering to match plans, while promising that `aw attention`'s `last_history_at`
derivation must keep working. Those instructions cannot all hold: `last_history_at` returns the date
of the LAST matching record in FILE ORDER (`attention_contract.py:540-549`), so under newest-first
ordering it returns the OLDEST record's date. Measured directly: patching `specs._append_history` as
authored and appending a `2026-06-06` record to a file holding `2026-01-01` made `last_history_at`
return `2026-01-01`. The plan would have broken the one property it named as inviolable.

WORSE, THE PLAN'S EXISTENCE PROOF FOR THAT PROPERTY IS FALSE, and this is the finding I would most
want a maintainer to read. Both E-02 and OQ-01 assert that plans prove the derivation tolerates
multi-record newest-first history, because "plans carry many inline records today and `attention`
handles them". It does not handle them. Scanning the corpus with the production readers
(`attention._history_section_lines` + `HISTORY_RECORD_RE`), 273 of 581 multi-record plans (46%)
already report a `last_history_at` that is not their newest record's date; `97df1z` reports
`2026-08-29` while its newest record is `2026-09-03`. The bug has been live and invisible precisely
because specs and backlog were slimmed to one line, where first and last coincide. So the authored
plan would have propagated a shipped defect into two more trees while citing that defect as its
safety evidence. The remedy is an ordering change, not a scope change: E-02 is now the READER fix and
must land first, E-08 is the writer change and depends on it, and the execution contract now states
that this ordering is a correctness requirement rather than a preference.

THE PLAN ALSO WALKS INTO THE TRAP IT NAMES. `x6tk1u` warns against growing duplicate history on
idempotent re-assertion, the plan repeats that warning in capitals, and then specifies a discriminator
(message presence) that does exactly what the warning forbids. Measured with the minimal patch: three
runs of an IDENTICAL `aw ipd set reviewed aaaa01 --yes -m "identical note"` produced three identical
records. This is a live path, not a hypothetical: both runners call `set_plan_approved` with the
hardcoded constant `FULL_AUTO_APPROVAL_MESSAGE` from two call sites each. E-01 now requires an explicit
dedup rule, and V-01 requires the three-identical-calls case as evidence. Note what this says about
the suite: E-01's minimal patch keeps all 5959 tests passing, so nothing existing would have caught
this, which is why the new assertion is mandatory rather than optional.

TWO SMALLER CORRECTIONS THAT WOULD HAVE COST AN EXECUTION CYCLE EACH. E-04 asked for the sidecar
failure to "BLOCK THE SLIM", but after E-08 there is no slim to block, and conditioning the inline
(now durable) write on a sidecar (now advisory) result inverts the durability model the maintainer's
own OQ-01 ruling established; the item is narrowed to "report, never swallow, always write inline",
and it now names all THREE swallowing sites rather than asking the executor to go looking for the
second. E-07 named one spec passage to amend, but four normative statements (R2, R6, AC1, AC4) each
restate the latest-one rule, and the spec's `:49` both miscites the derivation's location and states
its wrong behavior as a thing to protect; the spec is also `Status: implemented`, whose only legal
transitions are `deferred` and `superseded`, so the amendment must use `aw specs note` and leave the
status alone.

ALSO CORRECTED, and worth noting because the plan's own numbers were presented as measured: the
legacy multi-record count is 139, not 143 (of 211 such files), and the count drifts in a shared
checkout, so E-03 now says to re-count and report rather than to expect a figure. I also recorded the
measured suite baselines into the plan so the executor reproduces rather than re-derives them: 5959
passing unpatched, 5959 with E-01 alone, and `1 failed, 5958 passed` with E-08's specs half applied,
the failure being `test_specs_slims_inline`, which ASSERTS the slimming and must be rewritten rather
than deleted. Four undeclared paths were added to `- Scope-Paths:`.

WHAT I DID NOT CHANGE. The maintainer's OQ-01 ruling (inline provenance, one model for all three
types) stands untouched and is correct; my findings change HOW to reach it safely, not WHETHER. The
plan's refusal to revert the slimming decision, its refusal to bulk-rewrite the legacy files in a
shared checkout, its `aw backlog note` ergonomic fix, and its fresh-clone evidence requirement are all
right and were left alone.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | blocker | IN-SCOPE | A/D (correctness; the named invariant) | `agent_workflows/attention_contract.py:540-549` versus E-02's newest-first instruction | E-02 as authored is self-contradictory: it mandates newest-first ordering AND preserving prior records AND that `last_history_at` keep working, but that derivation takes the LAST record in FILE order, so it would return the OLDEST date. Measured: patching `specs._append_history` as authored and adding a `2026-06-06` record to a file holding `2026-01-01` made `last_history_at` return `2026-01-01`. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Set inverted: E-02 is now the reader fix and must land first; the writer change became E-08 depending on it; the execution contract states the ordering is a correctness requirement. |
| PR-002 | high | IN-SCOPE | D (false safety evidence) | corpus scan: 273 of 581 multi-record plans mismatch; `97df1z` reports `2026-08-29` vs newest `2026-09-03` | The plan's existence proof ("plans carry many inline records and `attention` handles them") is false; the derivation is already wrong for 46% of multi-record plans, hidden only because specs/backlog were slimmed to one line. E-08 would have propagated a live bug while citing it as proof of safety. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | The false claim is corrected in E-02, in OQ-01, in the Concern, and in the conventions section, each naming the measured 273/581 figure; E-02's outcome now includes the corpus re-scan. |
| PR-003 | high | IN-SCOPE | A/F (the plan's own named trap) | measured 3x-identical-call run producing 3 duplicate records; `oc_runipd.py:730-732`, `:2937`, `:6933`; `agy_runipd.py:830`, `:1975`, `:3990` | E-01's discriminator (message presence) triggers exactly the duplicate-growth trap `x6tk1u` warns about and the plan repeats: a constant-message idempotent re-assertion appends a record every run, and both runners do precisely that. E-01's minimal patch keeps all 5959 tests passing, so nothing existing catches it. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 now requires a dedup rule (non-empty AND not byte-identical to the newest record for the same status/date); V-01 and E-06 require the three-identical-calls assertion. |
| PR-004 | medium | IN-SCOPE | C (durability model coherence) | E-04's text; OQ-01's ruling; E-08's effect | E-04's "block the slim" instruction describes a state E-08 removes and inverts the durability model: it would make the inline (durable) write conditional on the sidecar (advisory) result, the opposite of the maintainer's ruling. | C:Medium; U:Low; S:Low; F:Low; Overall:Medium | FIXED | E-04 narrowed to report-never-swallow-always-write-inline, with an explicit instruction not to add the coupling and a V-04 requirement to state that it was not added. |
| PR-005 | medium | UNDER-SCOPE | G (completeness of a named investigation) | `backlog.py:544-558`; `specs.py:145-156`; `backlog.py:443` | E-04 asked the executor to "check `specs.py` for the same pattern"; the answer is yes, and there is a third site in `backlog.py`. Leaving it as a question invites a partial fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All three sites named in E-04 and F-5; V-04 requires an induced failure at each. |
| PR-006 | medium | UNDER-SCOPE | G (spec sync completeness) | `.aw/records/specs/20260818-1525-02-*.spec.md:49,59,63,67,70` | E-07 named only OQ-2, but R2, R6, AC1 and AC4 each restate the latest-one rule and `:49` miscites the derivation (`:434`) while stating its wrong behavior as a thing to protect. Amending one passage would leave four normative statements contradicting the code. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 now names all six passages; V-07 requires all six as evidence. |
| PR-007 | medium | IN-SCOPE | A (lifecycle legality) | `.aw/records/specs/20260818-1525-02-*.spec.md:4`; `SPEC_TRANSITIONS['implemented']` | The spec is `Status: implemented`, whose only legal transitions are `deferred`/`superseded`. E-07 did not say this, so an executor might attempt a status move and be refused. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 states the constraint and directs `aw specs note` (which appends history without a status change); V-07 requires confirming the status is unchanged. |
| PR-008 | medium | IN-SCOPE | E (falsifiable tests) | `tests/test_attention_contract.py:188-196`; `tests/test_history_routing.py:52-55` | Both existing `last_history_at` fixtures are oldest-first or single-record, so they pass under either newest-record rule. That is why the contradiction survived `awhistory-02`'s review, and E-06's "still derives correctly" wording would have been satisfied by an equally blind test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 now requires a NEWEST-FIRST multi-record case that fails before E-02, and V-06 rejects an assertion that passes both before and after as non-evidence. |
| PR-009 | medium | IN-SCOPE | E (reproducible baseline) | measured `5959 passed` unpatched; `5959` with E-01; `1 failed, 5958 passed` with E-08's specs half | The plan required a baseline but recorded none, and did not know that E-08 breaks a test which ASSERTS the slimming (so it must be rewritten, not deleted) or that E-01 breaks nothing (so its trap needs a new test). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All three measurements written into Required tests, with the named failing node id and the instruction to rewrite rather than delete it. |
| PR-010 | low | IN-SCOPE | G (measured-number accuracy) | production-parser census: 139 of 211 at `be6d2ab9`; sidecar 204 records / 141 id6s | The legacy multi-record count is 139, not the 143 stated as measured, and it drifts in a shared checkout. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-4 and E-03 corrected to 139 with an instruction to re-count at execution and report the observed figure; V-03 updated. |
| PR-011 | low | OVER-SCOPE (declaration gap) | G (scope fence) | this plan's `- Scope-Paths:` versus E-02's and E-06's work | The reader fix and its tests touch `attention_contract.py`, `plan_readiness.py` and `tests/test_attention_contract.py`, none of which were declared, so `aw ipd finalize` would have demanded a `--scope-reason` for each. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Three paths added to `- Scope-Paths:`; the Scope check section maps each declared path to its item. |
| PR-012 | low | IN-SCOPE | G (citation accuracy) | `attention_contract.py:540-549` is the function; `:434` is inside `TRANSITION_AUTHORITY` | Both this plan (three times) and the awhistory spec `:49` cite `attention_contract.py:434` for the `last_history_at` derivation. That line is in an unrelated table, so a reader following the citation finds nothing and may conclude the derivation is elsewhere or absent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected throughout the plan; E-07 now requires correcting the spec's copy of the same miscitation. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is E-02's newest-first-plus-preserve instruction a wording ambiguity to clarify, or a defect that changes the Set's structure? | A BLOCKER that splits E-02 into a reader fix (E-02) and a writer change (E-08) with an explicit dependency, plus an ordering clause in the execution contract. | Clarifying the wording only (rejected: the contradiction is semantic, not verbal, and either instruction alone is coherent while the pair is not). Dropping newest-first and appending oldest-first instead (rejected: contradicts `status_set.py:872-879`'s documented contract and `extract_newest_history_entry`'s explicit warning, and would split the corpus into two orderings). | `attention_contract.py:540-549`; the measured patch returning `2026-01-01` for a file whose newest record is `2026-06-06` | yes |
| D-2 | Should the review accept the plan's claim that plans prove multi-record newest-first history works with `attention`? | No: measure the corpus. The claim is false (273 of 581 multi-record plans mismatch) and is recorded as its own HIGH finding. | Accepting it (rejected: it is the plan's sole safety evidence for its biggest behavior change, and it took one scan to falsify). Treating it as a subordinate detail of PR-001 (rejected: PR-001 is about the instruction being self-contradictory; this is about a shipped bug the plan would have spread, and a maintainer needs the number). | corpus scan with `attention._history_section_lines` + `HISTORY_RECORD_RE` over `.aw/records/plans/**` | yes |
| D-3 | Does E-01's message-presence discriminator actually hit the trap `x6tk1u` names, or is the warning already satisfied by it? | It hits it: measured three identical records from three identical calls, so E-01 must carry an explicit dedup rule. | Trusting the plan's capitalized warning as sufficient guidance (rejected: the warning and the specified mechanism contradict each other, and an executor implementing exactly what E-01 said would ship the defect). | the 3x scratch run producing 4 records; `FULL_AUTO_APPROVAL_MESSAGE` constant at `oc_runipd.py:730-732` called from `:2937` and `:6933` | yes |
| D-4 | Which dedup rule should E-01 require? | Non-empty AND not byte-identical to the newest existing record's message for the same status and date; an alternative is allowed if it makes the measured three-call case produce one record. | A monotonic "only if different from the immediately previous message" (rejected as under-specified about which record is "previous", the very ambiguity PR-001 is about). Requiring a new flag such as `--force-note` (rejected: new vocabulary for a case the message content already answers). | `x6tk1u`'s stated trap; the measured duplicate run | yes |
| D-5 | Should E-04's "block the slim" coupling be kept? | No: narrow it to report-never-swallow-always-write-inline, and say explicitly that the coupling must not be added. | Keeping it (rejected: after E-08 there is no slim to block, and it would make the durable inline write depend on an advisory sidecar result, inverting the maintainer's OQ-01 durability ruling). | OQ-01's ruling text; E-08's effect on `_reattach_history` and `_append_history` | yes |
| D-6 | How many spec passages does E-07 need to amend? | Six: OQ-2, R2, R6, AC1, AC4, and the `:49` citation. | The one the plan named (rejected: four normative statements would be left instructing the opposite of the shipped code, which is the drift this plan exists to close). | grep of `.aw/records/specs/20260818-1525-02-*.spec.md` | yes |
| D-7 | Should the reader-versus-writer reconciliation choice be resolved by the reviewer or asked? | Asked as non-blocking OQ-02 with a recommendation (Route A, change the reader), because E-02 demands the OUTCOME regardless of route. | Resolving it silently (rejected: it changes the observable meaning of a derivation named in an implemented spec, and the maintainer should see the 273-plan number first). Marking it blocking (rejected: either route delivers the property, so it would stop an executable plan over a mechanism preference). | `plan_readiness.py:185-203` versus `attention_contract.py:540-549`; `status_set.py:872-879` | yes |
| D-8 | Is the plan's 143 legacy-file count correct? | No: 139 of 211, re-measured with the production parser; and the figure drifts in a shared checkout, so E-03 must re-count rather than expect a number. | Leaving 143 (rejected: it is stated as measured, and V-03 said "expect 143", so a correct execution would have reported a mismatch as a finding). | production-parser census at `be6d2ab9` | yes |
