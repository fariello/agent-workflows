# Review findings: plan 1i300e

- Subject-Id: 1i300e
- Subject-Type: ipd
- Reviewed-At: 2026-09-24
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `89350467` in an isolated review lane. The plan file was committed and byte-identical to
the lane input, so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming` (exit 0) BEFORE semantic review, so nothing found below is structural;
`--phase review-finalize` conforms after revision.

DISCLOSURE: the same agent and model authored this plan, so this is a SELF-REVIEW. Its value rests
entirely on RUNNING the claims rather than re-reading them, which is what produced the findings below.

THE PLAN'S DIAGNOSIS IS FULLY CONFIRMED. All three steps reproduce exactly as claimed:

```text
STEP 1  is_review_history_entry('- 2026-09-22 reviewed (aw set): status set to reviewed') = True
STEP 1  is_review_history_entry('- ... /plan-review (opencode/model-x): APPROVE ...')     = True

STEP 2  before bookkeeping: ('positive', '- 2026-09-21 /plan-review (...): APPROVE WITH REVISIONS APPLIED; PR-001 FIXED')
STEP 2  after  bookkeeping: (None,       '- 2026-09-22 reviewed (aw set): status set to reviewed')

STEP 3  (Readiness field absent from both fixtures)
        is_plan_review_approved BEFORE = True
        is_plan_review_approved AFTER  = False
```

And it is not merely a predicate-level artifact. Driven END TO END through the real CLI on a throwaway
git repo holding one `- Readiness:`-absent plan whose only substantive record is a positive review:

```text
$ aw ipd set reviewed aaa111 --priority high --yes
-    plan        20260921-probe-01-aaa111  [low]  unchanged
Committed 1 path(s): 8a9268a8...

## Workflow history
- 2026-09-24 reviewed (aw set): status set to reviewed

- 2026-09-21 /plan-review (opencode/model-x): APPROVE WITH REVISIONS APPLIED; PR-001 FIXED

Readiness field present? False
newest_verdict          = (None, '- 2026-09-24 reviewed (aw set): status set to reviewed')
is_plan_review_approved = False
```

So F-1 through F-4 all stand, and the `high` severity argument holds. THE PROBLEM IS THE FIX.

**SUPPRESSION CANNOT CLOSE THE HOLE (PR-001).** OQ-01 recommended writing no record when no
`--message` was supplied. But the shadowing is decided by the record's STATUS TOKEN, not its message:

```text
# the record the plan is REQUIRED to preserve shadows just as completely
$ aw ipd set reviewed aaa111 --message "deliberate operator note" --yes
- 2026-09-24 reviewed (aw set): deliberate operator note        <- newest

is_review_history_entry('- 2026-09-24 reviewed (aw set): deliberate operator note') = True
  classify_verdict('deliberate operator note') = (None, None)
newest_verdict          = (None, '- 2026-09-24 reviewed (aw set): deliberate operator note')
is_plan_review_approved = False
```

That record is LEGITIMATE. `x6tk1u` is a `done` bug whose entire content is that such a message must
not be dropped, and its fix is live in `apply_status_change`'s `_write_history_anyway` block. The plan
itself forbids re-breaking it. So the recommended option would have shipped a change that leaves the
defect fully reachable through the one path that must keep working.

**TWO FURTHER MEASURED FACTS THE PLAN OMITS**, each of which would have misled the executor:

```text
# PR-002: a PURE no-op already writes nothing, so "field-only NO-OP write" conflates two cases
apply_status_change:
  if not content_changed and not path_changed and not _write_history_anyway:
      return rec.path, norm_status
$ aw ipd set reviewed aaa111 --yes          # bare, third consecutive call
-    plan  20260921-probe-01-aaa111  [medium]  unchanged
grep -c "aw set" -> 2                        # unchanged: NOTHING was written
# the defect needs the write to change something on disk, which --priority does.

# PR-003: the shadowing record also DUPLICATES unboundedly
$ aw ipd set reviewed aaa111 --priority medium --yes    # second field-changing write, same day
- 2026-09-24 reviewed (aw set): status set to reviewed
- 2026-09-24 reviewed (aw set): status set to reviewed   # two byte-identical records
# same_status_message_is_duplicate EXISTS and would catch this, but is consulted only via
# _write_history_anyway, which is gated on an EXPLICIT --message. A defaulted message never
# reaches the dedup. This is the growth failure vhbvwz F-10 fixed, by another route.
```

**AND ONE OF THE PLAN'S OWN FINDINGS IS STALE (PR-004).** F-6 asserts the two setter paths still
disagree about a no-op, citing `x6tk1u`. That fix has landed:

```text
# WRITE A DELIBERATE `--message` EVEN WHEN NOTHING ELSE MOVED (plan `vhbvwz` E-01, bug `x6tk1u`).
_explicit_message = (getattr(args, "message", None) or "").strip()
_write_history_anyway = bool(_explicit_message) and not (
    same_status_message_is_duplicate(text, status=norm_status, date=today, message=message))
```

So E-04 is a VERIFICATION, not a change, and an executor who believes F-6 literally may manufacture a
diff to satisfy it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A (correctness); G (plan executability) | live CLI drive with `--message`: `newest_verdict` -> `(None, '- 2026-09-24 reviewed (aw set): deliberate operator note')`, `is_plan_review_approved` -> False; `is_review_history_entry`'s `m.group("mid")` tokenization; `x6tk1u` (`done`) and its live fix in `_write_history_anyway` | THE RECOMMENDED FIX IS INSUFFICIENT. Shadowing is caused by the STATUS TOKEN, not the message, so suppressing the defaulted-message record leaves the defect fully reachable through the explicit-`--message` record this plan is REQUIRED to preserve. OQ-01's recommendation would have shipped a change that does not fix the bug. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | OQ-01 RESOLVED to TAG with the measurement recorded; E-02 rewritten to tag the record for BOTH message cases, naming that the middle field (not the message, and not the actor suffix alone) is what must change, and requiring the tagged form be proven not-a-review-record AT THIS HEAD. Goal, Scope, ordered changes, tests and V-02 rewritten. Plan F-7. |
| PR-002 | HIGH | IN-SCOPE | F (honest documentation); G | quoted early return `if not content_changed and not path_changed and not _write_history_anyway`; live third bare call leaving the record count at 2 | A PURE NO-OP ALREADY WRITES NOTHING, so the plan's framing ("a field-only NO-OP write") conflates two cases that behave differently. An executor reproducing with a bare same-status call would observe no record and wrongly conclude the defect does not exist, abandoning a real `high` bug. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Plan F-8. Concern corrected; Goal reworded from "field-only" to "same-status"; E-01 now requires reproducing with a field-changing flag AND confirming the bare-form silence; the required tests pin that pure no-ops stay silent; the scope check forbids weakening that early return. |
| PR-003 | HIGH | UNDER-SCOPE | A; C (architecture) | live double `--priority` write producing two byte-identical records; the `_write_history_anyway` gate; `same_status_message_is_duplicate`'s docstring and `vhbvwz` F-10 | THE SHADOWING RECORD ALSO DUPLICATES UNBOUNDEDLY, unmentioned by the plan. The dedup predicate exists but is reached only when an explicit `--message` is present, so a defaulted record bypasses it entirely. This is the same growth failure `vhbvwz` F-10 measured and fixed, reachable by a different route. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Plan F-9. E-03 extended to close the bypass through the EXISTING predicate rather than a second one; Scope item (c) added; the required tests and V-03 pin no-duplication for the defaulted case; spec-sync requires correcting the predicate's docstring. |
| PR-004 | MEDIUM | IN-SCOPE | F (honest documentation) | the `_write_history_anyway` block crediting `vhbvwz` E-01 and `x6tk1u` by name; `x6tk1u` front matter `- Status: done` | THE PLAN'S F-6 IS STALE. It asserts the plan and backlog paths still disagree about a no-op, but `x6tk1u`'s fix is live in the single shared writer. Left uncorrected, E-04 invites an executor to "unify" behavior that is already unified, i.e. to manufacture a change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-6 relabelled "LIKELY STALE" with the refuting quote; E-04 rewritten to expect verification, to require all four drives pasted, and to state explicitly that no diff may be manufactured; it also gained a NEW check that E-02's tag reaches both paths. |
| PR-005 | MEDIUM | UNDER-SCOPE | C; D (anti-regression) | `same_status_message_is_duplicate` parsing the newest record with the same `_HISTORY_RECORD_PARTS_RE` and comparing `m.group("mid")` against the status | A SECOND CONSUMER READS THE FIELD E-02 WILL CHANGE, and the plan did not mention it. If the tag alters the `mid` group, the dedup stops matching its own prior records and appends forever, so the fix for PR-001 could re-create PR-003 in a new form. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-02 now names this check explicitly ("BEWARE THE SECOND READER"); added to conventions; V-02 requires proof the dedup still recognizes the new form. |
| PR-006 | MEDIUM | UNDER-SCOPE | E (testing/verification) | the authored required-tests list (one mandatory fixture, defaulted-message case only) | THE MANDATED TEST SET WOULD HAVE PASSED AGAINST AN INSUFFICIENT FIX. It required only the `- Readiness:`-absent defaulted-message regression, which a suppression-only change satisfies while PR-001's `--message` path stays broken. It also pinned neither the tagged form's non-review status at this HEAD, nor no-duplication, nor the bare-no-op silence. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Required tests expanded to five mandatory properties (both message variants; tagged form not-a-review AT THIS HEAD; no-duplication including the defaulted case; bare no-op still silent; `x6tk1u`/`vhbvwz` guards still green) plus a diff check that `plan_readiness.py` is unmodified. V-01..V-04 rewritten to demand each. |
| PR-007 | LOW | UNDER-SCOPE | F (honest documentation); G | E-02 changes the writer only; history records already written keep the old form | THE RETROACTIVE CONSEQUENCE WAS UNSTATED. Every record already written in the old form keeps shadowing, so a plan whose newest record is an old-form same-status line stays un-approvable by the history fallback. Not migrating is the right call, but discovering it after the fact looks like an incomplete fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added as an explicit deferral with its reason (a records-wide rewrite is far riskier, and `AGENTS.md` forbids re-committing `executed/` plan bodies) and a durable carrier; spec-sync requires documenting the new record form. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01: suppress the same-status record, or tag it? | RESOLVED: TAG. Written into the plan with the measurement, reversing the authored recommendation. | SUPPRESS-when-no-message (the authored recommendation): rejected because it is not merely weaker but INSUFFICIENT. Measured: the explicit-`--message` record shadows identically and must be preserved (`x6tk1u` is a `done` bug about dropping it, fix live in `_write_history_anyway`), so suppression leaves the defect reachable through the one path that must keep working. | the live `--message` CLI drive (`is_plan_review_approved` False); `is_review_history_entry`'s middle-field tokenization; `x6tk1u` status and its live fix | yes |
| D-2 | The authored objection to TAG was that its correctness depends on the current reader and might only work after `ycg597`. Does that block resolving to TAG? | No. Converted into a hard requirement: the tagged form must be shown returning False from `is_review_history_entry` AT THIS HEAD with `plan_readiness` unmodified. | Declaring a dependency on `ycg597` and sequencing this plan after it: rejected because `ycg597` is still `open` with no plan, so the dependency would stall a `high` release-gated fix indefinitely; and because the at-this-HEAD test makes the two halves genuinely independent, which is what the plan's own scope boundary demands. | `ycg597` front matter (`open`, `- Set: verdshadow`, no plan in that Set but this one); the plan's own "must not edit that reader" boundary | yes |
| D-3 | Is the plan REPLAN, given its recommended fix does not work? | Repair in place. The diagnosis, the measurements, the scope boundary and three of four E-items survive; only E-02's mechanism and OQ-01's answer change. | REPLAN: rejected because nothing about the plan's analysis was wrong (F-1..F-4 all re-measured TRUE); the defect is in the chosen REMEDY, which is exactly what a review is for, and re-aiming one E-item is a bounded edit. | `plan-review.md` Step 2.4 (REPLAN only when bounded edits cannot repair); F-1..F-4 reproduced verbatim | yes |
| D-4 | Should this review also fix the reader, since that would close the hole for every old record too? | No. `plan_readiness.py` is untouched, as the plan requires. | Editing `is_review_history_entry` to key on the ACTOR (distinguishing `(aw set)` from an agent/model string): rejected because it is precisely `ycg597`'s declared fix, three items already propose changing that one predicate, and a fourth uncoordinated edit is the exact defect class those items describe. Also rejected: doing it here "because it is cheap", which would make this plan and `ycg597` collide inside one function. | the plan's `## Scope check`; `ycg597`/`nwrb0j`/`gv36a7` summaries; `plan-review.md` (review plans only, change no code) | yes |
| D-5 | Should the existing corpus of old-form records be migrated so previously-written lines stop shadowing? | No. Recorded as an explicit deferral with its reason and a carrier, not folded in. | Migrating them in this plan: rejected on blast radius (a rewrite of every artifact's history section) and on a hard rule (`AGENTS.md` forbids adding commits to plans in `executed/`, which hold many such records). Leaving it unmentioned: also rejected, since the residual gap would look like an incomplete fix to the next reader. | `AGENTS.md` executed-plan immutability; the plan's writer-only scope | yes |

### Deferred and open

No finding is DEFERRED, OPEN, or REPLAN. Every finding above is FIXED, so no escalation to a
`- Blocking: yes` question is owed under the `review_findings_gate` rule (default `block_at: HIGH`;
no `review_findings_gate` key is configured in `.aw/config/project.json`).

OQ-01 is now `- Status: resolved` (D-1), so the plan carries no open question at all.

### Notes on what was NOT changed, and why

- No code, test, or spec file was touched by this review. Only the plan under review and this record.
  In particular `agent_workflows/status_set.py` and `agent_workflows/plan_readiness.py` are unmodified,
  even though PR-001 identifies precisely what must change in the first (D-4 explains the second).
- F-1 through F-4 were NOT retracted or downgraded. All four re-measured TRUE, twice: once against the
  predicates and once end to end through the CLI. The plan's severity argument is sound; only its
  remedy was wrong.
- F-6 was relabelled rather than deleted, so the plan records what it got wrong and why, and E-04
  survives as a verification with pasted evidence instead of being dropped.
- `- Blocks-Release: next` was left in place. It is inherited from `da7w6n`, a live `bug`, and PR-001
  shows the hole is WIDER than filed (reachable through a path the plan must preserve), so the gate is
  still earned.
- The plan's `- Status:` is left at `to-review` in the file; the transition to `reviewed` is applied
  through `aw ipd set reviewed` so it carries an attributed history line, per the untooled-status gate.
  Noted for the irony: that setter write is the very mechanism this plan exists to fix, and on this
  plan it is harmless only because the review wrote an explicit `- Readiness:` field, which is exactly
  the "benign by luck" condition `da7w6n` describes.
