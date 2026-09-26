# Review findings: plan isgno7

- Subject-Id: isgno7
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `ba22551f`. Structural preflight `aw ipd lint --phase author --agent` CONFORMED
(exit 0, `findings: 0`) before any revision. No pre-review snapshot was needed: the lane-input copy at
`.aw/state/lane-inputs/rev-8/` is byte-identical to the tracked file (`diff` -> IDENTICAL) and
`git status --short` was empty.

THIS IS A WELL-BUILT SMALL PLAN. It is honestly scoped for a `low`-priority chore, its citations are by
symbol, its OQ is resolved from real evidence, and it correctly identifies that the interesting risk is
a COLLISION with another subject producer rather than the formatting itself. I reproduced the defect end
to end rather than reading it: driving `cli.main(["commit","wk0001","--dir",<repo>,"--","src/f.py"])` on
the `test_work_gate_severity` fixture shape gave

```text
rc: 0
SUBJECT: 'work: .aw/records/plans/pending/20260828-wk-01-wk0001-demo.ipd.md'
```

F-4 holds (the `--no-plan` refusal returns 2 before the message line), and I verified the collision claim
the whole plan rests on instead of trusting the grep:

```text
"work(isgno7): Derive aw commit's default message" -> finalize match: False
'lifecycle(isgno7): finalize isgno7 -> executed'   -> finalize match: True
worktree_lease.commit_subject_is_interrupted_snapshot("work(isgno7): ...") -> False
```

So the new shape cannot be read as finalize evidence or as an interrupted snapshot, which are the two
prefix-keyed subject readers in the tree. The design is right and I did not change it.

**THE MIDDLE FALLBACK RUNG IS UNREACHABLE THROUGH ITS OWN PROPOSED MECHANISM, AND THE TEST FOR IT WOULD
HAVE PASSED WHILE PROVING THE OPPOSITE.** This is the finding that matters. E-02 reads the id6 from
`ipd_lint.parse(plan_text).meta_fields.get("Id")` and the title from the same parse, and defines a middle
rung for "id6 exists but title does not". But `parse` collects the metadata slice ONLY AFTER it has seen
the H1:

```text
no H1, bullets first     title=''                       Id=None
empty H1                 title=''                       Id=None
H1 no IPD prefix         title='Just A Title'           Id='wk0001'
```

confirmed against the `if not seen_h1: ... continue` gate in `ipd_lint.parse`. So the absent-title state
and the absent-id6 state ARRIVE TOGETHER through that reader, the middle rung is dead, and E-04 case (2)
(`plan whose H1 is empty or absent -> work(<id6>): <slug>`) would instead exercise the THIRD rung and
return `work: <plan_rel>`. Written loosely, that case would have passed on the wrong output; written
strictly, it would have failed for a reason the plan never anticipated.

**AND THE MODULE ALREADY HAS THE READER THAT FIXES IT.** `work_cmd._plan_id6(text)` is a full-line
`(?m)^- Id:\s*([0-9a-z]{6})\s*$` regex, already defined in this file and already used twice by
`run_finish` (`plan_id = _plan_id6(text) or plan_path.stem`). Being regex-based it is immune to the H1
gate, so reusing it both revives the middle rung and avoids introducing a second id6 mechanism into one
module. E-02 now reads the id6 through `_plan_id6` and uses `ipd_lint.parse` for the TITLE only, which is
the one thing it uniquely provides. E-04 case (2) is now specified to FAIL against a `meta_fields`
implementation, and V-02 must paste `meta_fields.get("Id") is None` on that same text, so the evidence
discriminates the mechanism rather than just the output.

**FOUR SMALLER THINGS, each measured.** `-m ""` falls through to the derived default because `or` treats
the empty string as falsy; that is today's behavior too, so the plan does not change it, but it is now
pinned as case (5) rather than left as an accident waiting to be "fixed" in either direction. A title can
legitimately contain backticks, quotes and `$(...)`, and that is SAFE because the message is a git
argument and `compose_message_with_trailers` is byte-for-byte with no trailers; I resolved that as a new
OQ-02 and pinned it as case (6), specifically so a later reader does not add escaping that corrupts real
titles. The history figures drifted between authoring and review (50 of 2556 and 733 scoped, versus the
authored 41 of 2396 and 702), so they are restated as re-derivable context per the live-artifact
convention. And `text`'s scope in `run_commit` is safe only because of the `--no-plan` early return, so
E-03 now says not to hoist the default out of the `or` (which would raise `UnboundLocalError` on that
path) and case (4) is its regression test.

**ONE THING I FOUND AND DELIBERATELY DID NOT WIDEN THE PLAN FOR.** `runner_shared._commit_subject`'s
docstring asserts as verified that a subject in this repository "names a plan path under `.aw/records/`",
quoting two measured peers whose subjects are `work: .aw/records/plans/pending/...`. This change makes
that stale for future commits. Nothing reads the asserted shape (the helper only truncates a subject to
120 characters for a conflict refusal), so I added it as F-9 and as a REPORT obligation in the new E-05
rather than declaring a 30k-line shared module in a `low`-priority chore's scope.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | A. correctness; E. testing (a dead code path plus a test that would pass for the wrong reason) | driven: `ipd_lint.parse("- Id: wk0001\n\n## Goal\nx\n")` -> `title=''`, `meta_fields.get("Id") is None`; same for an empty `# `; `parse("# Just A Title\n\n- Id: wk0001...")` -> `Id='wk0001'`; the `if not seen_h1: ... continue` gate read in `ipd_lint.parse` | **E-02's MIDDLE FALLBACK RUNG IS UNREACHABLE VIA `meta_fields`, BECAUSE `parse` GATES METADATA ON THE H1.** The absent-title and absent-id6 states arrive together, so "id6 but no title" cannot occur through that reader, and E-04 case (2) would silently exercise the third rung instead of the second. | C:Low; U:Low; S:Low; F:Medium; Overall:Low (swap the reader; the fix is local and directly testable) | FIXED | E-02 now reads the id6 via `work_cmd._plan_id6` and uses `parse` for the title only; E-04 case (2) is specified to FAIL against a `meta_fields` implementation; V-02 requires the `meta_fields.get("Id") is None` paste beside the middle-rung output; F-5 records the drive; the conventions section states the gate. |
| PR-002 | MEDIUM | IN-SCOPE | C. architecture (a second mechanism beside an existing one) | `work_cmd._plan_id6`'s body read; its two callers at `run_finish`'s `plan_id = _plan_id6(text) or plan_path.stem` sites | **THE MODULE ALREADY HAS AN id6 READER AND THE PLAN PROPOSED A DIFFERENT ONE.** `_plan_id6` is regex-based, immune to PR-001's H1 gate, and already the local convention; adding a `meta_fields` path beside it would be a second mechanism for one question in one module. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 reuses `_plan_id6` (filename prefix as the second rung); F-6 records the precedent and its callers; the conventions section names it as the established reader. |
| PR-003 | LOW | UNDER-SCOPE | A. correctness; B. security-adjacent (verifying no reader is confused by the new shape) | `rg -n 'format=%s' agent_workflows/` -> 5 sites; `artifact_audit._FINALIZE_SUBJECT_RE` driven (no match on `work(...)`, match on `lifecycle(...): finalize`); `worktree_lease.commit_subject_is_interrupted_snapshot` driven -> False | **NO ITEM VERIFIED THE COLLISION CLAIM; IT RESTED ON ONE GREP FOR THE LITERAL `work: `.** The real question is whether any subject CONSUMER can be confused by a new `work(<id6>):` prefix, which needs the readers driven, not the producer grepped. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-05 re-runs the consumer search and DRIVES both prefix-keyed readers; new V-05; F-3 widened with the measurements; a stop condition covers the case where a reader does match. |
| PR-004 | LOW | IN-SCOPE | A. correctness (an unstated edge case in the expression being changed) | `("" or "work: x")` -> `"work: x"`; the `getattr(args, "message", None) or ...` expression read | **`-m ""` FALLS THROUGH TO THE DERIVED DEFAULT AND THE PLAN NEVER SAYS SO.** Behavior is unchanged by this edit, but an unstated edge case in the exact expression being modified is one a later change alters by accident in either direction. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 states it explicitly as preserved-not-fixed; E-04 gains case (5) pinning it; F-7 records the measurement. |
| PR-005 | LOW | IN-SCOPE | B. security-adjacent; F. KISS (pre-empting a harmful "hardening" edit) | driven: `parse` preserves `` `backticks` ``, `"quotes"` and `$(cmd)` in `.title`; `compose_message_with_trailers`'s "byte-for-byte identical: the existing-caller guarantee"; the message reaches git as an argument, not via a shell | **NOTHING STATES THAT THE TITLE IS INTENTIONALLY UNSANITIZED.** A title may contain shell-looking punctuation; it is safe here, but an undocumented invariant invites a later reader to add escaping that would corrupt legitimate titles. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New OQ-02 resolves it with the evidence and the reasoning; E-02 forbids sanitizing; E-04 gains case (6) asserting the subject verbatim so an escaping attempt fails a test; F-8; the gate tells the human. |
| PR-006 | LOW | IN-SCOPE | E. testing; G. executability (stale live figures and an unstated regression surface) | re-measured: 50 of 2556 `work: ` and 733 scoped, versus the authored 41 of 2396 and 702; E-04 drives `cli.main(["commit", ...])` through `work_cmd.run_commit`, which `tests/test_work_gate_severity.py` also exercises | **THE HISTORY COUNTS ARE A LIVE POPULATION PRESENTED AS FIXED, AND THE EXISTING-SUITE RUN WAS LISTED WITHOUT SAYING WHY IT IS REQUIRED.** A count measured at authoring is context, not a bar (live-artifact convention), and the two named suites are the actual regression surface for this edit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 re-derives the counts and states the proportion is the point; F-2 carries both measurements; the Required tests section states why the two existing suites are REQUIRED rather than incidental; V-04 now asks for `-v` per-node output and an empty post-revert diff. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-02 reads the id6 from `ipd_lint.parse(...).meta_fields`. Accept, or check that the three rungs are each reachable? | CHECK, and the middle rung is NOT reachable that way; switch the reader to the module's existing `_plan_id6`. | (a) Accept as written: rejected, the middle rung would be dead code and its own test would pass on the wrong output, which is worse than a missing test because it asserts coverage that does not exist. (b) Keep `meta_fields` and delete the middle rung: rejected, the rung is genuinely useful (a plan with an id6 and no title still has a greppable subject) and it IS reachable with the right reader. (c) Change `ipd_lint.parse` to collect metadata without an H1: rejected outright, that is a shared parser with many callers and its H1 gating is load-bearing elsewhere; a one-module reader swap is the small correct fix. | `parse` driven on four text shapes; the `seen_h1` gate read; `_plan_id6` and its two callers read. | yes |
| D-2 | The plan asserts nothing parses `work: ` subjects. Trust the grep, or drive the readers? | DRIVE THEM. Both prefix-keyed readers correctly reject the new shape, and the check is now an item. | (a) Trust the grep: rejected, it searched for the OLD literal, which cannot answer whether a NEW prefix confuses a reader; the two risky readers key on `<keyword>(<id6>):` and `<PREFIX>:` shapes that a new `work(<id6>):` subject superficially resembles. (b) Rename the prefix to something unlike `lifecycle(...)`: rejected as unnecessary once measured, and `work(<id6>)` is the shape that matches the repository's dominant convention, which is the plan's whole purpose. | `_FINALIZE_SUBJECT_RE` and `commit_subject_is_interrupted_snapshot` driven against the new subject with a positive control; `rg -n 'format=%s'` enumerated. | yes |
| D-3 | Should the derived title be escaped before becoming a subject? | NO, and pin the verbatim behavior with a test. | (a) Escape or quote it: rejected, it would corrupt legitimate titles (backticks and quotes are ordinary in this corpus) to defend against a shell path that does not exist, since the message is passed as an argument. (b) Say nothing: rejected, an undocumented safety invariant is exactly what a future "hardening" edit breaks; recording it as OQ-02 plus a test makes the intent enforceable. | Title punctuation driven through `parse`; `compose_message_with_trailers`'s byte-for-byte guarantee read; the git invocation path confirmed argument-based. | yes |
| D-4 | `-m ""` falls through to the derived default. Preserve, or make an explicit empty message win? | PRESERVE, and pin it. | (a) Honor an empty `-m`: rejected as an unrequested behavior change to argument handling, outside a `low` chore about the DEFAULT, and arguably wrong anyway (an empty subject is not a useful commit). (b) Leave it unmentioned: rejected, it is an edge case of the exact expression being edited, so it should be recorded and tested rather than rediscovered. | The `or` expression evaluated; today's behavior confirmed identical. | yes |
| D-5 | `runner_shared._commit_subject`'s docstring goes stale. Fix it here, or report it? | REPORT it, via E-05, and leave `runner_shared.py` out of scope. | (a) Fix it here: rejected, it would declare a 30k-line shared module in a `low`-priority chore's fence for a comment, and that module is heavily contended by concurrent work in this checkout. (b) Ignore it: rejected, a docstring asserting a measured fact that the change falsifies is exactly the kind of quiet rot that later readers cite as evidence; naming it at finalize costs nothing. | The docstring read; its only consumer (`format_conflict_resolver_facts`) confirmed to truncate for display only. | yes |

### Deferred and open

- (none). All six findings were FIXED in place. None reaches the repository's `HIGH` gate threshold, so
  no `- Blocking: yes` escalation is owed, and the two MEDIUM findings (PR-001, PR-002) are the same root
  cause fixed by one reader swap. OQ-01 was already resolved by the author and I confirmed it with an
  additional measurement (no `commit-msg` hook exists to cap a subject); I added OQ-02, resolved and
  non-blocking, to record the unsanitized-title invariant.

HONEST LIMITS, stated because they bound what this round proves. I verified the DEFECT, the parser gate,
the existing reader, the two subject consumers, and the argument-not-shell path by driving each; I did
NOT implement the helper, so that the three rungs behave as specified in a real `run_commit` call remains
E-02/E-03 work and V-02/V-03 evidence. My PR-001 analysis rests on `ipd_lint.parse`'s current H1 gating,
which a concurrent plan could change under this one; I did not audit pending plans for an edit to
`ipd_lint.parse` or to `work_cmd.run_commit`, so a collision of the kind that bit two sibling plans in
this same sweep is possible and unmeasured here. I did not run the bare suite against a patched tree, so
E-04's before/after comparison is a real obligation. Finally, my re-derived history counts describe this
checkout at review time and will drift again before execution, which is why E-01 re-derives rather than
inheriting them.
