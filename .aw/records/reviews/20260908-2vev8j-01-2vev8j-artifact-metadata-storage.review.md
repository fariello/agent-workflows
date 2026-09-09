# Review: artifact metadata storage (spec 2vev8j)

- Subject-Id: 2vev8j
- Subject-Type: spec
- Reviewed-At: 2026-09-08
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `93703697` via `/aw spec-review 2vev8j`.

ROUTING CORRECTION, recorded because it changed which workflow ran: the invocation was
`plan-review 2vev8j`, but the target is a SPEC. `spec-review` documents three measured ways
`plan-review` corrupts a spec (it writes a `- Readiness:` field the schema has no place for, it
hand-edits the tool-owned `- Status:` and history, and its `aw ipd lint` preflight is IPD-only so it
SKIPS and the gate passes by not running). The maintainer confirmed re-routing to `spec-review`. No
`aw ipd lint` was invoked against this spec; `aw specs check` was the structural gate and reported
conforming before and after revision.

DISCLOSURE, because it bounds what this review is worth: I authored this spec earlier in the same
session, so this is a SELF-REVIEW, not an independent judgement. It is recorded because the repository
requires a conforming record before `to-review -> reviewed`, and because a re-measurement pass has
real value even from the author. It is NOT evidence that a second party judged the design. What I can
honestly claim: every code citation was re-verified at this HEAD, the measured counts were re-derived
(and two had already drifted), and the rubric was applied against the structure. What I cannot claim:
that an independent reviewer would reach the same design conclusions.

VERIFIED CLAIMS, each re-run for this review rather than carried over:

- `status_set.py:885` is `new_lines.insert(i + 1, hist_entry)`, i.e. the tools PREPEND. Holds.
- `specs.py:342-346` REPLACES the section with only the latest record. Holds.
- `ipd_lifecycle.py:773` is `events.reverse()`. Holds.
- `record_history.py:3-5` asserts "Append-only, so line order is irrelevant and concurrent-append git
  merges rarely conflict." Holds as a quote, and the CLAIM IS FALSE: re-ran the two-branch trial
  independently for this review; two branches each appending one different line to the same one-line
  JSONL file CONFLICT on merge. Spec finding E1 stands on re-measured evidence.
- `record_history.append` (`:66-71`) is a bare `open(p, "a")` + `write`, and `grep` for
  `filelock|platform_lock` in that module returns 0. So no lock, no atomic replace, no fsync. Spec
  finding E2 stands, and Gemini 3.1 Pro's contrary "atomic-safe" claim is false.
- `attention_contract.py:32-33` defines `last_history_at` as "the date of the LAST record in file
  order". Holds, and combined with the prepending writers this is a live defect (spec finding E3).
- `.aw/.gitignore:11` is `records/history.jsonl`. Holds (spec finding E4).
- `ipd_lint.py:66` defines `C_EXEC_HISTORY = "IPD-S405"` and it is emitted at `:793-801`. Holds.
- `check.lifecycle-transition-invalid` count is 15. Holds.
- 18 modules reference the heading. Holds, and confirms the spec's correction of the 19 that all five
  sources state.

CLAIMS THAT HAD ALREADY DRIFTED, found by re-measuring rather than trusting the spec I wrote hours
earlier. This is finding SR-001 and it is the single most useful result of this review:

| Claim | As authored | Re-measured at review |
|---|---|---|
| Plans corpus | 591 files, 15,639,697 chars | 604 files, 16,270,178 chars |
| Global sidecar | 177 records (150/26/1) | 182 records (153/28/1) |

+13 plans and +630,481 chars inside one working session. The PLANS-AT-1 sidecar figure is stable and
is the load-bearing one.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| SR-001 | HIGH | IN-SCOPE | rubric A (measured claims must be current) | `.aw/records/specs/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md:38-41` | Two measured counts were already stale hours after authoring: corpus 591/15,639,697 vs 604/16,270,178 actual; sidecar 177 vs 182. A spec whose evidence table is wrong invites an implementer to quote it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Table updated to the re-measured values, plus an explicit note that these drift fast, that every absolute number and percentage MUST be re-derived at implementation time, and that the two STABLE load-bearing figures are plans-at-1 and the 18-module surface. |
| SR-002 | HIGH | IN-SCOPE | rubric C (acceptance criteria must cover requirements) | spec Section 3 as authored | Eight MUST/Want criteria (C1-C8) with NO acceptance criteria at all. Every MUST was uncovered, so no reviewer could refuse a false claim of completion, and `aw check` had nothing to hold an implementation to. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added Section 3b: 11 acceptance criteria (AC-1..AC-11), each mapping to the criterion it covers and each naming the concrete evidence that satisfies it. Failure and refusal paths included (AC-5 concurrency, AC-7 refused/dry-run leaves no event, AC-8 eviction still passes S405, AC-11 partially-migrated corpus). |
| SR-003 | MEDIUM | IN-SCOPE | rubric A (non-goals must exclude assumable scope) | spec as authored | No Non-goals section. A reader could reasonably assume the spec rewrites the status vocabulary, migrates backlog/specs in scope, decides the rollback question, or builds the SQLite cache. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Section 3a with N1-N5, each naming something a reader would otherwise assume, including that Section 7's two out-of-scope defects are deliberately not absorbed. |
| SR-004 | MEDIUM | IN-SCOPE | rubric F (spec must state its honest limits) | spec as authored | No honest-limits statement. The spec leaned on "four independent reports agree", which is strong evidence of soundness but was not distinguished from a proof of optimality, and it inherited token percentages it never re-derived. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Section 3c: does not prove optimality, does not establish the token savings (C6 is directional and unmeasured), does not specify the schema field-by-field, and its migration sequencing is a plan rather than a measured result. |
| SR-005 | MEDIUM | IN-SCOPE | rubric B (internal consistency) | spec 4.3 vs 4.7 | 4.3 required a "contiguous" `seq` while 4.7 introduced a "`seq` 0 checkpoint", leaving the origin ambiguous: an implementer could not tell whether a born-under-contract artifact starts at 0 or 1. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | 4.3 now states the origin for both cases: migrated artifacts use `seq` 0 as the checkpoint with real events from 1; artifacts born under the contract start at 1 with no checkpoint; contiguity is per artifact with no gaps either way. |
| SR-006 | MEDIUM | IN-SCOPE | rubric B (a MUST/Want must be verifiable) | spec C6 as authored | C6 asserted removing "~10.2% of plan-corpus tokens", a number the spec inherits and never re-derives, making the criterion unverifiable as written and in tension with SR-001's drift. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | C6 restated as DIRECTIONAL with no percentage target, pointing at 3c for why, and noting that what IS testable (history no longer in the artifact body) is covered by AC-6 and AC-8. |
| SR-007 | BLOCKER | IN-SCOPE | rubric E (open questions must be dispositioned) | spec Section 8 OQ-1 | The spec's only blocking question named no owner, no closing condition, and no statement of what it blocks, so it could stall the lifecycle indefinitely with no route to resolution. The underlying contradiction is real: `validate_transition` rejects every backward rank movement, yet the corpus holds an intentional `approved -> reviewed -> approved` and the runner spec instructs that edge as a recovery. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Dispositioned (owner, what it blocks, what closes it), RAISED WITH THE MAINTAINER interactively, and RESOLVED by their decision: a backward edge is LEGAL as an explicit recovery transition. Recorded as decision 4.8 with the rejected alternative, the accepted cost (the forward-only invariant is gone, so the table must ENUMERATE legal edges rather than derive them from rank), and its irreversibility. OQ-1 retained as RESOLVED pointing at 4.8; Section 3c reconciled. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| SD-01 | Which workflow reviews a spec target invoked as `plan-review`? | Re-route to `spec-review`. | Run `plan-review` as literally asked, refusing its spec-corrupting steps ad hoc; or stop and have the maintainer re-invoke. | `spec-review.md:55-95` enumerates three measured corruptions, including an `aw ipd lint` preflight that would SKIP and pass by not running. Maintainer confirmed the re-route. | yes |
| SD-02 | Are backward lifecycle edges legal? | LEGAL as a named recovery transition (`approved -> reviewed`). | Illegal, treating the corpus round trip as a defect and replacing the runner's recovery instruction; or defer explicitly and accept the permanent false-positive noise. | MAINTAINER DECISION, taken interactively during this review. Not a reviewer call: both answers were self-consistent and the evidence supported either. | no - recorded in 4.8 as changing a public contract, and raised with the maintainer as irreversible before it was written |
| SD-03 | Should the record disclose that the reviewer authored the spec? | Yes, prominently, in the round body and in the verdict. | Omit it and let the record read as independent. | Precedent `.aw/records/reviews/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.review.md:13-21` does exactly this; an attestation that overstates its independence is worse than none. | yes |

### Verdict

APPROVE WITH REVISIONS APPLIED. Seven findings, all FIXED, none left OPEN or DEFERRED, so this record
arms no gating refusal on the spec's approval. The one BLOCKER (SR-007) was resolved by a maintainer
decision rather than by reviewer authority.

READINESS FOR THE HUMAN APPROVAL GATE, in prose because a spec never carries a `Readiness:` field:
the spec is ready for human approval. Its blocking question is answered and recorded, its MUSTs are
covered by evidence-naming acceptance criteria, and its structural gate is clean. The material caveat
a human should weigh is SD-03: this was a self-review, so the design has been re-measured but not
independently judged.
