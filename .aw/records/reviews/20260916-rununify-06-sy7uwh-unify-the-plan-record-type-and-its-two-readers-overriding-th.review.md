# Review findings: plan sy7uwh

- Subject-Id: sy7uwh
- Subject-Type: ipd
- Reviewed-At: 2026-09-16
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `2c6c3eee`. Structural preflight `aw ipd lint --phase author` CONFORMED (exit 0) before
revision. No pre-review snapshot needed: the plan was committed and unmodified. This is the fourth
`rununify` child reviewed today, and like its immediate predecessor it is well founded rather than
mistaken: every claim in its Findings table reproduces, and its central judgement (that the record split
should now be collapsed) is correct.

I VERIFIED ALL SIX FINDINGS INDIVIDUALLY, plus two claims the plan makes in passing. F-1's pin exists at
`tests/test_runner_shared.py:1530` and carries the quoted "this is a class (c) reconciliation for a later
child" docstring. F-2's premise really has dissolved: `agy.action_for is runner_shared.action_for` is
True and `action_for('orchestrator', 'approved')` returns `orchestrate`. F-3's silent, type-shaped failure
mode is real and the existing suite already warns of it. F-4's `_plan_kind` docstring does name the split
as its reason for existing. F-5's claim that `build_dynamic_manifest` differs in exactly one expression is
exact. F-6 holds. Independently: oc's field set IS a strict superset of agy's differing in exactly `kind`,
and `parse_plan_file` differs in exactly the two lines that read and pass it. This plan measured
carefully. The three findings below are OMISSIONS, and the first is serious.

THE HELPER THE PLAN WANTS DELETED HAS TWO CALLERS, AND ONLY ONE IS THE WORKAROUND. E-03 says to delete
`_plan_kind`, calling its removal "the actual payoff of this plan: it exists solely to work around the
record split." That is what its docstring says, and its docstring describes only one of its two call
sites. The second (`agy_runipd.py:2260`) is a LEGACY-MANIFEST FALLBACK with an independent reason,
documented in the comment directly above it: when a hand-written manifest carries no `kind` key, agy
re-reads the plan file rather than deriving `execute` for an orchestrator. oc has no equivalent;
`oc_runipd.py:3446` passes `plan.get("kind")` straight through. I measured both paths: with the fallback,
an approved orchestrator in a legacy manifest derives `orchestrate`; without it,
`action_for(None, "approved")` derives `execute`, so the orchestrator would be AGENT-EXECUTED. That is
precisely the defect `orchretire-03` (`pgq326`) fixed, and no test covers it, which is exactly why
deleting the helper looked free. An executor following E-03 literally would have reintroduced a fixed
defect while every existing test stayed green.

That discovery also raised a question the plan could not have known to ask, and it is the reason this is
NO-GO rather than APPROVE WITH REVISIONS. The two hosts already DISAGREE about a correctness gate, in
oc's disfavor. The Set's standing ruling is "oc is preferred unless one host does A and the other NOT
A", so this is an A / NOT-A case by the ruling's own terms and needs a per-symbol decision. The
maintainer gave such rulings for `extract_session_id` and `driver_begin` but was never asked about this,
because nobody knew the second call site existed. Preserving it as agy-only is safe and leaves the drift;
giving it to both fixes a real oc defect but changes what `aw oc run` does with an existing manifest.
That is OQ-03.

THERE ARE TWO PINS, NOT ONE. Besides `DiscoverPlansRecordTypeTests`,
`tests/test_orchestrator_retirement.py:2470` asserts `"kind" not in agy_runipd.PlanRecord._fields`, with
the comment "that invariant is not this plan's to break". E-04 inverts only the first, so the second
would fail, and its file was not in `Scope-Paths`, so `aw ipd finalize` would also refuse the
out-of-scope edit. Worth noting the surrounding test is the best end-to-end guard that exists for exactly
the risk F-3 names (it drives the real `discover_plans` plus `build_dynamic_manifest` path and asserts
agy's queue entry derives `orchestrate`), so the correct treatment is to invert one line and leave the
rest alone rather than to rewrite the test.

`parse_plan_file` CANNOT MOVE ALONE. It closes over six module-level readers absent from
`runner_shared`: `_PLAN_FILENAME_RE` (byte-identical across hosts, so it simply moves), `_read_kind`,
`_read_item_dependencies` and `_read_from_backlog` (oc-owned, with agy already importing them FROM oc, so
moving them also removes three oc-to-agy imports), plus `_read_id` and `_read_status` (both hosts import
these from `selectors`). None is hard. All are unstated, and a naive move fails at import time rather
than in a test.

TWO SMALLER THINGS. A THIRD `PlanRecord` exists in `plans.py` with entirely different fields and no
importers of that name; the parent orchestrator's F10 requires the single-definition check be REPO-WIDE,
so E-05's scan will flag it, and the executor must allowlist it rather than "fix" an unrelated type or
weaken the scan to a pairwise check (which is the check F10 exists to prevent). And the declared
dependency `executed:i3d6ml` is unfounded: nothing here references anything among child 03's 48 symbols.
The coupling in fact runs the OTHER way, since child 03's `discover_plans` and `expand_selectors` need
`parse_plan_file`, which this plan unifies. So this plan should run BEFORE child 03, and I removed the
edge. That is the third unfounded edge found in this Set today, which suggests the edges were written
from topic adjacency rather than from symbol closure.

WHAT I FIXED AND WHAT I LEFT. I rewrote E-03 to move the six readers and to remove only the record-split
call site while explicitly preserving the fallback; added the second pin to E-04 with instructions to
invert one line and leave the end-to-end guard intact; added the `plans.py` allowlist to E-02 and E-05;
added the first-ever test for the legacy-manifest fallback and a second non-vacuity control that deletes
the helper and shows the failure; recorded the review's own E-01 results including the nuanced answer to
premise 3 (nothing REQUIRES the field's absence, but two tests ASSERT it); fenced the missing test file;
named four further suites the change touches; and removed the unfounded dependency edge. I did NOT decide
the fallback's fate, because two of the three options change a runner's behavior and the third removes a
guard a prior plan deliberately added.

THE RECORD UNIFICATION ITSELF IS AUTHORIZED AND SOUND, and OQ-03 is narrow: it governs one helper's
disposition, not the merge. If the maintainer picks option 1 the plan is executable immediately.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-301 | BLOCKER | IN-SCOPE | A. correctness; D. anti-regression | `agy_runipd.py:2260` and its comment at `:2257`; `oc_runipd.py:3446`; measured both paths at review | **`_plan_kind` HAS TWO CALLERS AND E-03's "DELETE" WOULD REINTRODUCE A FIXED DEFECT.** Only `:1693` is the record-split workaround its docstring describes. `:2260` is a legacy-manifest fallback: with no `kind` key in a hand-written manifest, agy re-reads the plan file rather than deriving `execute` for an orchestrator. oc has no equivalent. MEASURED: with the fallback an approved orchestrator derives `orchestrate`; without it, `execute`, so it is AGENT-EXECUTED. That is the `orchretire-03` (`pgq326`) defect, and NO test covers it, so every existing test would stay green. | C:Low; U:Low; S:Low; F:High; Overall:Medium | OPEN | E-03 rewritten to remove ONLY the record-split call site and PRESERVE the fallback; E-05 adds the first test for it; V-05(b) adds a control that deletes the helper and shows the named failure. The remaining question, whether the fallback should be agy-only or given to both hosts, is an A/NOT-A case the standing ruling reserves for a per-symbol decision: escalated as OQ-03 with three options and a recommendation. |
| PR-302 | HIGH | UNDER-SCOPE | D. anti-regression; G. traceability of an override | `tests/test_orchestrator_retirement.py:2470` and its comment | **THERE ARE TWO PINS AND THE PLAN NAMES ONE.** This test also asserts `"kind" not in agy_runipd.PlanRecord._fields`, saying "that invariant is not this plan's to break". E-04 inverts only `DiscoverPlansRecordTypeTests`, so the second fails; its file was also absent from `Scope-Paths`, so `aw ipd finalize` would refuse the edit as out of scope. The surrounding test is additionally the best end-to-end guard for F-3's risk, so it must be preserved rather than rewritten. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 now inverts BOTH pins with a citation in each and instructs that only the single record-shape line change; V-04 requires `test_the_agy_queue_entry_carries_kind` green before and after; the file is fenced. |
| PR-303 | HIGH | UNDER-SCOPE | C. architecture (closure); G. executability | closure check of `parse_plan_file` at review | **`parse_plan_file` CLOSES OVER SIX READERS ABSENT FROM `runner_shared`,** none mentioned by the plan: `_PLAN_FILENAME_RE`, `_read_kind`, `_read_item_dependencies`, `_read_from_backlog`, `_read_id`, `_read_status`. A naive move fails at IMPORT time rather than in a test. Each is tractable (`_PLAN_FILENAME_RE` is byte-identical; three are oc-owned with agy already importing them from oc; two are `selectors` re-exports both hosts share), but the work was invisible in the checklist. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03(a) enumerates all six with their disposition; V-03 requires evidence each resolves in `runner_shared`. Noted as a side benefit: moving three of them also removes three oc-to-agy imports. |
| PR-304 | MEDIUM | UNDER-SCOPE | E. testing (a repo-wide scan with a false positive) | `agent_workflows/plans.py:90`; the parent orchestrator's F10 | **A THIRD `PlanRecord` EXISTS AND THE REQUIRED REPO-WIDE SCAN WILL FLAG IT.** `plans.py`'s type is unrelated (`path`/`area`/`disposition`/`status`/`set_id`/`order`, no importers of that name). The parent's F10 requires the single-definition check be repo-wide rather than pairwise, so an executor meeting this false positive will either "fix" an unrelated type or narrow the scan to pairwise, which is the very weakening F10 exists to prevent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 and E-05 require it allowlisted WITH its reason; V-02 and V-05(c) require the scan output showing exactly one runner-owned definition plus the allowlisted entry. |
| PR-305 | MEDIUM | IN-SCOPE | G. dependencies and sequencing | closure check of all three symbols against child 03's 48 | **THE `executed:i3d6ml` EDGE IS UNFOUNDED AND POINTS THE WRONG WAY.** Nothing here references anything child 03 owns. The real coupling is the reverse: child 03's `discover_plans` and `expand_selectors` need `parse_plan_file`, which this plan unifies, so this plan should run BEFORE child 03. Third unfounded edge found in this Set today, which suggests the edges were derived from topic adjacency rather than symbol closure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Edge removed (`Item-Dependencies: none`); the correct direction recorded in Deferred and in F-11 so the Set's sequencing can be fixed once rather than rediscovered. |
| PR-306 | MEDIUM | IN-SCOPE | A. correctness (a premise reported too cleanly) | E-01's premise 3 versus the two asserting tests | **E-01's THIRD PREMISE IS NOT A CLEAN PASS AND THE PLAN TREATS IT AS ONE.** It asks the executor to show "no code path depends on agy's record LACKING the field". True as stated, and misleading: two TESTS assert exactly that, so the honest report is "nothing requires it, two tests assert it, both must be deliberately inverted". As written, an executor could report premise 3 satisfied and then be surprised by a red suite. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now requires BOTH asserting tests be named in the premise-3 report, with the instruction to treat a test-asserted invariant as something to invert deliberately; V-01 requires the same. |
| PR-307 | LOW | UNDER-SCOPE | G. scope fence | `tests/test_orchestrator_retirement.py` (must edit); shim tests referencing `PlanRecord` | **THE FENCE OMITS THE FILE E-04 MUST EDIT,** despite the plan already naming it in Required tests. Also worth the executor's attention though no edit is expected: `tests/test_oc_runipd_shim.py:46` and `tests/test_agy_runipd_shim.py:43` require `PlanRecord` to remain a re-exported ATTRIBUTE of each runner module, which a shared type satisfies but a rename would not. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `tests/test_orchestrator_retirement.py` added to `Scope-Paths`; the shim constraint recorded in Project conventions and named in Required tests item 7. |
| PR-308 | LOW | IN-SCOPE | E. achievable bar | measured `1 failed, 7308 passed, 3 skipped, 2 xfailed`; the failure passes in isolation | **THE SUITE BASELINE IS UNSTATED AND ONE FAILURE IS PRE-EXISTING** (`ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130`, a load-dependent 30s subprocess timeout). "No new failure against the baseline at execution time" leaves the executor to rediscover it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-13 records the measurement; Required tests item 9 and V-05(d) name the flake and require the isolation re-run as disposing evidence. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | E-03 says `_plan_kind` "exists solely to work around the record split" and must be deleted. Accept that, or check its callers? | CHECK, and reject the premise: it has two callers and only one is the workaround. | (a) Accept the plan's characterization, rejected because it is sourced from the helper's own docstring, and a docstring describes intent at the time of writing rather than current call sites, which is precisely the class of claim a review must verify. (b) Note the second caller but leave the deletion instruction, rejected: an executor reading "delete this helper" will delete it. | `agy_runipd.py:2260` and the comment at `:2257`; `oc_runipd.py:3446` lacking any equivalent; measured `orchestrate` vs `execute` outcomes both ways | yes |
| D-2 | The fallback exists on agy only. Preserve as agy-only, give it to both hosts, or drop it? | ASK. Raised as OQ-03, `Blocking: yes`, three options and a recommendation (give it to both). | (a) Preserve as agy-only myself, rejected as a silent choice to leave two hosts disagreeing about a correctness gate, which is the drift this Set exists to end. (b) Give it to both myself, rejected: it changes what `aw oc run` does with an existing hand-written manifest, which is a behavior change on a live host. (c) Drop it from both, rejected outright as reintroducing `pgq326` knowingly. The standing ruling makes an A/NOT-A difference a per-symbol maintainer decision, and this one was never put to them. | the maintainer's 2026-09-14 ruling ("oc preferred UNLESS one does A and the other NOT A"); `pgq326`'s recorded reason for adding the fallback | yes |
| D-3 | Two pins assert the split. Invert both, or delete the second? | INVERT BOTH, changing only the single record-shape assertion in the second and leaving its end-to-end test intact. | (a) Delete the second assertion, rejected: `818uru`'s precedent and this repo's `test_wtiso_characterization.py` pattern both require a reversed pin be INVERTED and cited, not removed, so the override stays traceable. (b) Rewrite the whole surrounding test, rejected: it is the best existing end-to-end guard for the exact silent failure F-3 names, so it must keep passing unchanged around that one line. | `tests/test_orchestrator_retirement.py:2470` with its "not this plan's to break" comment; `tests/test_wtiso_characterization.py`'s stated invert-do-not-delete pattern | no |
| D-4 | `plans.py` defines a third `PlanRecord`. Unify it, exclude it, or narrow the scan? | EXCLUDE it via an allowlist carrying the reason. | (a) Unify it too, rejected: different fields, different concept (a plan file's location and disposition, not a runner queue record), and no importers of that name; merging them would invent a coupling. (b) Narrow the scan to a pairwise runner check, rejected explicitly: the parent's F10 requires repo-wide precisely because a pairwise check passes while a third copy sits elsewhere. | `agent_workflows/plans.py:90` field list; zero importers of `plans.PlanRecord`; the parent orchestrator's F10 wording | yes |
| D-5 | Should the `executed:i3d6ml` edge stay? | REMOVE it, and record that the real coupling runs the opposite way. | (a) Keep it as harmless ordering, rejected: a false edge makes a runnable plan wait and the runner re-checks edges at dispatch. (b) Reverse it by editing child 03, rejected as out of scope for this review: I record the direction so the Set's sequencing can be corrected once, deliberately, rather than editing another plan from here. | closure check of `PlanRecord`/`parse_plan_file`/`build_dynamic_manifest` against child 03's 48; child 03's own review recording `discover_plans`/`expand_selectors` as blocked on `parse_plan_file` | yes |

### Deferred and open

- `PR-301` - `OPEN`:
  - Reason: The deletion hazard is fixed in the plan, but the remaining question (whether agy's legacy-manifest fallback should stay agy-only, be given to oc as well, or be dropped from both) is an A/NOT-A behavior difference that the Set's standing ruling reserves for a per-symbol maintainer decision, and two of the three options change a runner's behavior.
  - Remediation Risk: Medium
  - Axis: functionality
  - Required decision or evidence: the maintainer's answer to OQ-03.
  - Consequence if unresolved: the record unification (which is authorized and sound) cannot land, and the two hosts keep disagreeing about whether an approved orchestrator in a hand-written manifest is retired or agent-executed. Note the question is narrow: option 1 makes the plan executable immediately with no behavior change.

### Escalation of the irreversible decision

D-3 is judged `Reversible: no`: it decides to INVERT rather than DELETE a pinned assertion, and the
opposite choice is what cannot be cleanly undone, because a deleted pin leaves no record that the
invariant was ever deliberate and the next agent to unify something has no precedent to find. Escalated
per the workflow rather than merely recorded: it is raised in the plan as F-8 with both file:line
citations, E-04 carries the instruction to invert-and-cite both, V-04 requires the inverted text plus the
untouched end-to-end guard as evidence, and the `Blocking: yes` OQ-03 puts the plan in front of the
maintainer before any of it executes. D-1, D-2, D-4 and D-5 are reversible (a plan edit undoes each) and
are recorded only.

### Honest limits of this review

- I DID NOT RUN THE UNIFICATION. The claim that oc's field set is a strict superset and that
  `parse_plan_file` differs in exactly two lines is from static comparison plus live `_fields`
  inspection, not from having built the shared type and imported it. E-01/E-02 re-derive it.
- MY LEGACY-MANIFEST MEASUREMENT USED A SYNTHETIC MANIFEST-ABSENT PATH: I called `_plan_kind` and
  `action_for` directly on a real plan file rather than driving `initialize_run` with a hand-written
  manifest end to end. That is sufficient to establish the `orchestrate` versus `execute` difference and
  it is NOT a full integration proof; E-05's new test is written to be that proof.
- I DID NOT ENUMERATE EVERY CONSUMER OF THE THREE SYMBOLS. I checked the tests that reference them and
  the runner call sites, and a consumer reaching them dynamically (a `getattr`, a string dispatch) would
  not appear.
- I DID NOT DECIDE THE FALLBACK's FATE (D-2), and my recommendation of option 2 is a recommendation. I
  also did not evaluate whether hand-written manifests should remain supported at all, which is the
  premise option 3 would need and which is a broader product question than this plan.
