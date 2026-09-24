# Review findings: plan 7jqev2

- Subject-Id: 7jqev2
- Subject-Type: ipd
- Reviewed-At: 2026-09-24
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `97c79615` in an isolated review lane. The plan file was committed and byte-identical to
the lane input, so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming` (exit 0) BEFORE semantic review; `--phase review-finalize` conforms after
revision. Nothing below is structural.

DISCLOSURE: the same agent and model authored this plan, so this is a SELF-REVIEW. Its value rests
entirely on RUNNING the claims rather than re-reading them. Doing so found that one of the plan's three
deliverables instructed work an APPROVED SPEC FORBIDS.

### What re-measured TRUE

F-1, F-2, F-3 and F-5 all hold, re-probed rather than re-read.

```text
# F-1: the slimmer keeps the OLDEST round on a newest-first file
records parsed (file order):
    - 2026-09-20 approved (aw specs): the --by-human attestation NEWEST
    - 2026-09-10 reviewed (aw specs): middle round
    - 2026-09-01 created (aw specs): OLDEST
keep = records[-1] -> - 2026-09-01 created (aw specs): OLDEST
--- AFTER _slim_inline_history ---
## Workflow history

- 2026-09-01 created (aw specs): OLDEST      # the attestation is GONE

# F-3: the reader is positional, so an oldest-first block misreports
oldest-first block -> - 2026-09-01 created (x): older      # WRONG (newest is 2026-09-15)
newest-first block -> - 2026-09-15 reviewed (x): newer     # right

# F-5: both writers preserve priors, and fbf85068 is ancestral
r3: KEPT   r2: KEPT   r1: KEPT   prepended (NEW before r3)? True
git merge-base --is-ancestor fbf85068 HEAD -> YES ancestor

# F-2: the migration test is green on an OLDEST-FIRST fixture
3 passed in 2.34s
fixture: "- 2026-01-01 draft (t): a\n- 2026-01-02 to-review (t): b\n- 2026-01-03 reviewed (t): c\n"
assertion: self.assertEqual(inline, ["- 2026-01-03 reviewed (t): c"])
```

F-4 was UPGRADED from source inspection to a behavioral measurement, through the real CLI:

```text
call 1: exit=0   call 2: exit=0   call 3: exit=0
=== history block after 3 IDENTICAL `aw specs note --message "identical note"` ===
- 2026-09-24 note (aw specs): identical note
- 2026-09-24 note (aw specs): identical note
- 2026-09-24 note (aw specs): identical note
- 2026-09-01 created (aw specs): born
identical-note record count: 3
```

### THE BLOCKER: E-03 instructed work an approved spec forbids

E-03 offered two options and told the executor to "Prefer normalization". Backlog `jhrao5`, the item
E-03 graduated from, forbids BOTH, in these words:

> DO NOT fix it by making the reader date-aware (measured: that widens the approval gate) and DO NOT
> bulk-reorder the files (shared checkout; and spec 2vev8j 4.3 rules that order should become EXPLICIT
> via a per-artifact monotonic seq rather than inferred from position at all). The honest fix is the seq
> field spec 2vev8j already approved; this item exists so the residue is tracked rather than discovered
> later.

Spec `2vev8j` is `- Status: approved` (2026-09-09, `--by-human`) with `- Blocks-Release: next`, and its
Section 4.3 says the direction question is answered "NEITHER WAY": ordering becomes an explicit
per-artifact `seq`, timestamps are display-only, and the reader gets SIMPLER. The plan cited neither
`2vev8j` nor `jhrao5`'s guidance; `2vev8j` appears nowhere in it.

The third aggravating fact is local: a detection heuristic would add a THIRD ordering authority to the
one function whose docstring exists because two once disagreed and misreported 373 of 679 multi-record
plans, and whose max-by-date alternative is measured to flip `history_verdict_approves` for 20 plans,
widening an unattended approval gate.

### Two further corrections of record

```text
# F-7: the slimmer is reachable from NO shipped command
grep migrate_inline_history across agent_workflows/ and tests/
  -> sole caller: tests/test_record_history_migrate.py   (x4)
aw --help | grep -i migrate  -> only `migrate-layout` (unrelated)
# 8pcdoa states this; the plan omitted it. F-1 downgraded BLOCKER -> HIGH as a LATENT trap.

# F-8: a declared, validated test file does not exist
ls tests/test_specs.py                -> No such file or directory
pytest tests/test_specs.py            -> no tests ran in 1.68s     # measures NOTHING
ls tests/test_specs_verbs.py          -> exists                    # the real home
```

And E-04's unverified premise was discharged IN THE PLAN'S FAVOR rather than left to the executor:

```text
status_set.same_status_message_is_duplicate against a spec block
  status='note'    -> True      # fits the `aw specs note` record shape
  multi-part actor -> True      # "(aw specs, --by-human)" parses
  diff message     -> False     diff date -> False
```

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | OVER-SCOPE | C (architecture); D (anti-regression); B (gate integrity) | `jhrao5` history (quoted verbatim); `.aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md` `- Status: approved` + Section 4.3; `attention_contract.newest_history_record` docstring (max-by-date flips `history_verdict_approves` for 20 plans; two readers once misreported 373 of 679 plans) | E-03 INSTRUCTED WORK AN APPROVED SPEC AND ITS OWN SOURCE ITEM FORBID, AND RECOMMENDED THE MORE FORBIDDEN OPTION. Its two options were a date-aware reader and normalizing the 77 legacy files; `jhrao5` prohibits both by name, and told the reader the honest fix is `2vev8j`'s `seq`. The plan cites `2vev8j` nowhere. `jhrao5` also states it exists to TRACK residue, not to request a fix. Executing E-03 as authored would either widen a live unattended approval gate or bulk-rewrite records in a shared checkout. | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | E-03 CONVERTED to a report-only verification item quoting both prohibitions; `agent_workflows/attention_contract.py` REMOVED from `- Scope-Paths:`; Goal, Scope, Concern, Proposed changes and V-03 rewritten; two STOP conditions added to the gate (no reader edit, no record reorder); `2vev8j` named as owner in Deferred and in a new conventions bullet; spec-sync forbids amending `2vev8j`. |
| PR-002 | HIGH | IN-SCOPE | F (honest documentation); G (plan executability) | grep: sole caller of `migrate_inline_history` is `tests/test_record_history_migrate.py`; `aw --help` exposes no such verb; `8pcdoa` ("has no CLI entry point... reachable only by a direct call today") | THE FIRST HOLE IS NOT REACHABLE FROM ANY SHIPPED COMMAND, AND THE PLAN NEVER SAYS SO THOUGH ITS OWN SOURCE ITEM DOES. The plan calls this a BLOCKER that "DESTROYS" human attestations, present tense, and rests its release-gate argument on that. No user or agent can currently trigger it. The fix is still owed (a latent attestation-destroying helper is a trap for whoever wires it up, which is why `8pcdoa` recommends retiring it), but an executor reading the plan would believe live data loss is occurring. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as plan F-7; F-1 downgraded BLOCKER -> HIGH and relabelled LATENT; Concern carries the reachability paragraph and the honest framing; E-01 must re-verify reachability and V-01 must state it; a conventions bullet records that reachability is part of severity here. |
| PR-003 | MEDIUM | IN-SCOPE | E (testing); G (plan executability) | `ls tests/test_specs.py` -> No such file; `pytest tests/test_specs.py` -> `no tests ran in 1.68s`; `tests/test_specs_verbs.py` exists | THE PLAN DECLARED AND VALIDATED AGAINST A FILE THAT DOES NOT EXIST. `tests/test_specs.py` appears in `- Scope-Paths:` and in Required tests. `pytest` given a nonexistent path reports `no tests ran` and exits without failing, so the validation step would have SILENTLY measured nothing and an executor could paste that as evidence. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as plan F-8. `- Scope-Paths:` and Required tests re-pointed to `tests/test_specs_verbs.py`; E-05 requires the dedup regression test there and notes the original error; a scope-check bullet requires declaring any different module before writing in it. |
| PR-004 | MEDIUM | IN-SCOPE | F (honest documentation) | all seven items under `.aw/records/backlog/done/`; `raxuyq` close record (2026-09-23, SATISFIED path, cites `vhbvwz`/`fbf85068`, names this plan as residue carrier); `8pcdoa` line 4 `- Blocks-Release: next` | TWO FACTUAL ERRORS IN ONE SENTENCE OF THE HISTORY LINE, BOTH ABOUT THE GATE. The plan says the seven already-fixed items "should be closed as done citing `vhbvwz`" and its Deferred section declines to perform those closes: they were ALREADY closed on 2026-09-23, so an executor would hunt for bookkeeping that does not exist. And it says `8pcdoa` "carries no gate of its own" when `8pcdoa` does carry `- Blocks-Release: next`, making the gate DIRECT rather than inherited. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as plan F-9. Concern gained a paragraph stating the seven are already closed; the Deferred bullet corrected; E-01 told not to look for the closes; both errors annotated inline in the original history line rather than rewritten, preserving the audit trail. |
| PR-005 | MEDIUM | IN-SCOPE | F (honest documentation) | `4vh5nb` `- Priority: low`, `- Work-Kind: chore`, no `- Blocks-Release:`; its own text "NOT A REGRESSION, and that is why this is a chore rather than a bug" | THE THIRD HOLE'S SEVERITY IS OVERSTATED BY OMISSION. The plan lists F-4 as MED beside two HIGHs on a release-gated plan without recording that `4vh5nb` is `low`/`chore`, carries NO release gate, and explains why: the production duplicate-growth path is the runner's, which already routes through `status_set` where the rule lives. Presenting it undifferentiated invites an executor to spend equal care on the cheapest item. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-4 severity corrected MED -> LOW with `4vh5nb`'s own fields and wording quoted; the Concern's third-hole paragraph carries the same correction while noting the defect itself was CONFIRMED behaviorally (stronger evidence, lower severity). |
| PR-006 | MEDIUM | UNDER-SCOPE | E (testing); G | `specs.py` calls `_append_history` at three sites (the `--status` set path, the migrate path, `run_note`); `4vh5nb` names `aw specs set` and `aw specs migrate`; review reproduced the duplicate through `run_note` | E-04 NAMES ONE DEFECT WITH THREE CALL SITES AND DOES NOT SAY WHICH TO FIX. `4vh5nb` names `set` and `migrate`; the review reproduced it through `note`, which the item does not mention. A fix landing on one site leaves the item half-closed and the test could pass while two routes still duplicate. E-04 also directed the executor to "the rule the backlog writer already has", but the predicate lives in `status_set.py`, not `backlog.py`. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 now enumerates the three call sites and requires any skipped one be justified; names `status_set.same_status_message_is_duplicate` and corrects the module; forbids moving or editing it (`status_set.py` undeclared, with a scope-check bullet); warns against "improving" it into a whole-file scan, which would restore the `x6tk1u` defect in reverse; V-04 requires the enumeration and a changed-message case. |
| PR-007 | LOW | IN-SCOPE | G (plan executability) | `specs._append_history(lines: List[str], record: str)`; the review's first probe raised `TypeError: _append_history() takes 2 positional arguments but 5 were given` | E-01'S PROBE INSTRUCTION MISDESCRIBES THE FUNCTION IT ASKS THE EXECUTOR TO CALL. "Call `specs._append_history` on a 3-round block and on an id-less spec" reads as a text-and-metadata call; the real signature takes a LINE LIST and a preformatted record string. Minor, but it cost this review a failed probe and the id-less-spec framing does not correspond to any parameter. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now states the real signature inline and drops the id-less framing; the behavioral requirement (priors survive, record prepended) is unchanged. |
| PR-008 | LOW | UNDER-SCOPE | E (testing); A (correctness) | E-05's `- Depends on: E-02, E-03, E-04` with E-03 now changing no code; OQ-01's retire branch leaving no slimmer to test | E-05 COULD NOT BE SATISFIED UNDER ONE OF OQ-01'S OWN ANSWERS. It requires a newest-first fixture and an attestation-survival case failing before E-02; if E-02 RETIRES the helper there is nothing to slim, no such test can exist, and an executor might reintroduce the helper to keep the fixture meaningful. It also depended on E-03, which now produces no code. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now carries both shapes explicitly (re-pointed fixture with attestation case, OR a reduced/removed test asserting no slimming), forbids reintroducing the helper to keep a test green, requires the landed shape be stated, and drops the E-03 dependency; V-05 accepts either shape. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-03 is forbidden work. Delete the item, or convert it? | CONVERT to a report-only verification item that reproduces the defect, cites the authority, and proves nothing was edited. | DELETING E-03 entirely: rejected because the defect is real, `jhrao5` is `graduated` to THIS plan, and a plan that silently drops a graduated item's subject leaves the item pointing at work nobody did. Keeping it as a fix with a warning: rejected because the plan already carried warnings and still recommended the forbidden option; only removing the code mandate makes it safe. | `jhrao5`'s quoted prohibitions; `2vev8j` `- Status: approved` + 4.3; `plan-review.md` 2.4 (preserve valid content, replace ambiguity, remove unsupported scope) | yes |
| D-2 | Should this review resolve OQ-01 (keep-newest versus stop-slimming)? | No. Left OPEN and `Blocking: no`, with two facts added that tilt it toward retirement. | RESOLVING it to retire: rejected. Deleting a shipped helper is a scope call the maintainer owns, and while the evidence favors it (no shipped caller; `8pcdoa` lists retirement first and says "do not leave a helper in the tree whose one action is to destroy the provenance the amended spec now requires"), the sidecar fold retains a diagnostic purpose and E-02 is safe under either answer. Eliminating neither option while supplying the missing evidence is what review could honestly do. | `plan-review.md` Step 3.1 (never guess a human decision); F-7's reachability grep; `8pcdoa`'s own recommendation ordering | yes |
| D-3 | Does F-7 (unreachable helper) justify clearing `- Blocks-Release: next`? | No. Gate left in place. | CLEARING it: rejected. The gate does not depend on the plan's own severity prose: `8pcdoa` carries `- Blocks-Release: next` directly (contradicting the plan's own claim, PR-004) and `jhrao5` carries it too, both live `bug` items under the live-bug policy. A latent trap in provenance-handling code is still a defect the release gate legitimately covers. What was corrected is the plan's OVERSTATEMENT of the harm, not the gate. | `8pcdoa` and `jhrao5` front matter; AGENTS.md live-bug policy | yes |
| D-4 | Is PR-001 a finding against this plan, or does it belong to `2vev8j`'s future implementation plan? | Against THIS plan. The instruction to do forbidden work lives here, so the correction must live here. | Filing it as a note on the future `seq` plan: rejected because an executor reads THIS plan, and the harm (a widened approval gate, or a bulk record rewrite in a shared checkout) would occur before any future plan existed. A prohibition recorded only elsewhere protects nobody holding this document. | the plan's own E-03 text ("Prefer normalization"); `plan-review.md` 2.4 | yes |
| D-5 | Should the two stale claims in the 2026-09-23 history line be rewritten or annotated? | ANNOTATED inline with dated `[REVIEW CORRECTION 2026-09-24: ...]` markers, leaving the original wording intact. | Rewriting the line to be correct: rejected because that history record was the author's honest statement at the time and silently correcting it destroys the audit trail, which is the same class of harm this entire plan exists to prevent. Appending a separate record only: rejected because a reader of the old line would not see the correction next to the claim. | the escalation-return-path convention (append rounds, never edit in place); the plan's own subject matter | yes |
| D-6 | Does E-04 need its premise verified before the executor starts, or is that E-01's job? | Verified AT REVIEW and recorded, so the executor does not spend a turn discovering it. | Leaving it to E-01: rejected because `plan-review.md` Step 3.1 forbids deferring what the repository already answers, and the answer took one probe. Had the predicate NOT fit (for example refusing the `note` token or the multi-part actor), E-04 would have needed re-planning rather than execution, so this was a question that could have changed the plan's shape. | probes: `status='note'` -> True, multi-part actor -> True, changed message/date -> False; `plan-review.md` Step 3.1 | yes |

### Deferred and open

No finding is DEFERRED or REPLAN. Every finding above is FIXED, so no escalation to a `- Blocking: yes`
question is owed under the `review_findings_gate` rule (default `block_at: HIGH`; no
`review_findings_gate` key is configured in `.aw/config/project.json`).

OQ-01 remains OPEN by design (D-2): it is `- Blocking: no`, E-02 is safe under either answer, and the
choice to delete a shipped helper belongs to the maintainer. A non-blocking open question does not make
a plan `NO-GO`.

### Notes on what was NOT changed, and why

- No code or test file was touched by this review. Only the plan under review and this record. Every
  probe ran read-only or in a throwaway directory under the lane's own `.aw/state/`, each removed
  afterwards; the lane tree was verified clean before and after.
- NO RECORD FILE WAS REORDERED and `agent_workflows/attention_contract.py` was not edited, which is the
  same restraint this review now requires of the executor.
- F-1, F-2, F-3 and F-5 were NOT retracted. All four re-measured TRUE. F-1's severity moved on
  REACHABILITY alone; its code analysis was exactly right, and the destroyed-attestation measurement
  reproduced precisely as the plan described.
- F-4 was NOT dropped despite the severity correction. The defect is real and now has stronger
  (behavioral) evidence than the plan had; only its priority relative to the other items changed.
- THE SEVEN ALREADY-CLOSED ITEMS WERE NOT RE-CLOSED OR MODIFIED. They are correct as they stand; only
  the plan's description of them was wrong.
- `- Blocks-Release: next` was left in place (D-3), on the carrier items' own fields rather than on the
  plan's severity prose.
- `- Highest E allocated: 05` is unchanged and the E/V bijection stays 5/5. E-03 was converted rather
  than removed, so no renumbering occurred.
- The plan's `- Status:` is left at `to-review` in the file; the transition to `reviewed` is applied
  through `aw ipd set reviewed` so it carries an attributed history line, per the untooled-status gate.
