# Review findings: plan 9wzlou

- Subject-Id: 9wzlou
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-101 (HIGH, fixed), PR-102 (MEDIUM, fixed), PR-103 (MEDIUM, fixed), PR-104 (LOW, fixed), PR-105 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `b66eb5f9`. The plan file was committed and byte-identical to
the lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review, and
`--phase review-finalize` reports `clean` with zero findings after revision, on this plan and on both
children I edited.

THE `IPD-S407` CHECK APPLIED AND PASSED. This plan's own first `- Kind:` bullet reads `orchestrator`, so
the typed child-tracking row check ran rather than being skipped; it reported no violation, so the bounded
repair loop never engaged and no attempt log is owed.

THE ORCHESTRATOR COVERAGE QUESTION IS THE ONE THAT MATTERS MOST FOR A PARENT, AND IT PASSES. I mapped
every one of the eight completion criteria onto a named child item rather than trusting the plan's claim
to carry orchestration only: the new spec to `jjh4aj` E-03 through E-09; the `grep` inversion, the sibling
verifier, the cutover key registration, the production wiring and both test surfaces to `rtvdak` E-03
through E-08; and the citation-not-implementation honesty to `jjh4aj` E-07 (contract) plus `rtvdak` E-05
(code). Nothing is parked on the parent, both `E-*` items are confirmations of a child's terminal state
rather than work, and the child checklist is present. So the runner may legitimately retire this plan
without an agent turn, which is exactly the premise the skipped pre-transition checkpoint rests on.

MOST OF THE PLAN'S FACTUAL BASE RE-VERIFIES. `rg -rn 'SPEC-PLAN-TRACE' agent_workflows/` returns nothing,
inverting-to-be as the plan says and matching what executed plan `aeq7f8` recorded. `25kzda` 4.8's TRACE
row exists with exactly the quoted pass criterion, message template and `RETRY, then FAIL ITEM` Action.
`z7nbn1` 4.4 carries the deferral and the words "a produced plan MUST NOT be described as trace-verified"
verbatim. The three sibling verifiers (`spec_plan_count`, `spec_plan_conformance`, `spec_plan_gate_carry`)
exist in `production_checks.py` and are all three called at one site in `runner_shared.py`, so "a fourth
sibling beside three shipped ones" is an accurate description of the landing site.
`config.KNOWN_FEATURE_CUTOVERS` is a real registry and `resolve_cutover_date` does return `None` for an
unregistered key, so E-06's stated failure mode is real. The maintainer's 2026-09-26 ruling exists in both
`z7nbn1` OQ-02 and backlog `vy20et`, and it does postdate research `vkub9o` (2026-09-20). The "other NINE
unbuilt codes" is arithmetically consistent with `z7nbn1` 4.4's "THIRTEEN codes" minus the four
`SPEC-PLAN-*`.

THE DOMINANT FINDING IS THAT THE PLAN ARGUED AWAY A GUARD THE REPOSITORY ALREADY SHIPS. The plan states
the dependency grammar offers "`executed:`/`exists:`/`state:` edges over plans", concludes `executed:jjh4aj`
"CANNOT express 'and a human approved it'", and tells a reader the approval "no runner can perform or
detect for them". The first half is right and important: a runner must never perform a `--by-human`
approval. The second half is false, and the falsehood has a cost, because it is used to justify leaving
the Set's single human gate to an executing agent's self-discipline. Measured four ways:

- `25kzda` Section 2.7's grammar reads `state-edge = "state:" target-type ":" status ":" id6` with
  `target-type = "ipd" | "spec" | "backlog"`, so a spec is a first-class edge target.
- `runner_shared.parse_dependency_token("state:spec:approved:abc123")` returns
  `ItemDependency(kind='state', target_type='spec', status='approved', id6='abc123')`, while
  `state:spec:bogus:abc123` returns `None`, so the status token is validated too.
- `runner_shared.edge_satisfied`'s `state:` branch resolves the artifact and refuses with
  `"<tok>: spec <id6> is <actual>, needs exactly 'approved'"` until the status matches, and its own
  comment notes a `spec` target is never mutated by the runner, which is precisely why the edge is safe
  here.
- `aw ipd dependencies set rtvdak executed:jjh4aj state:spec:approved:llbr2b --dry-run --yes` validated and
  reported `unchanged (dry-run)`, proving the two-edge statement is writable by a shipped verb that
  canonicalizes order and refuses a dangling or ambiguous target before writing.

So the runner CAN hold Order 02 until the spec is genuinely `approved`. The fix had one real wrinkle I had
to resolve rather than hand-wave: the spec's id6 is MINTED by Order 01's E-03 (`aw specs new`), so Order 02
cannot declare the edge at authoring time, which is the legitimate reason it was absent. The edge therefore
has to be written DURING Order 01, so I put the obligation on `jjh4aj` E-09, the item that already performs
the handoff, and added the verification to this parent's V-02. Order 02's E-01 refusal stays as the second
layer, because the edge proves the status FIELD says `approved` while only the spec's history proves a
human attested it with `--by-human`. I also corrected `rtvdak`'s F-10, which stated the same false claim.

I ALSO CORRECTED MY OWN FIRST ATTEMPT AT THAT FIX, which is worth recording because it would have shipped
a command that does not exist. I initially wrote the instruction as `aw ipd set ... --item-dependencies
'...'`; `aw ipd set --help` and `aw specs set --help` carry no such flag. The real writer is the dedicated
`aw ipd dependencies set <selector> <edge...>` verb, which I then exercised with `--dry-run` before leaving
the instruction in the plan. An executor handed the first version would have been blocked at a
nonexistent flag.

THE SURVEY RECONCILIATION IS STRONGER THAN THE PLAN CLAIMS, which I record because the plan names this as
"the reviewer's sharpest question" and invites exactly this scrutiny. Research `vkub9o` recommendation #3
is a flat "Do NOT build: a requirement parser", and this Set builds one, so the reconciliation carries real
weight. The plan's argument (the survey's decisive objection was a missing plan-to-spec edge, which does
not reach a check inside the dispatcher) is sound as far as it goes, but it understates the position: the
survey's own "single most important structural finding" was FILED as backlog `1zknu7`, that item is now
`done`, discharged by executed plan `0ykozn`, and the survey's recommendation #2 ("add ONE `aw check` rule
on the JOIN EDGE, not on requirement ids") SHIPPED as `check.plan-spec-link-missing`, which fires on 34
plans in the live tree. The survey's worked example moved with it: `c4gd2h` had 0 of 37 plans carrying
`- From-Spec:` at survey time and 1 of 71 now, with a live checker nagging the rest. So #3 rested on a
blocker that #2 was written to remove, and #2 is done. I was careful to write this into the plan as a
strengthening and NOT as licence to skip re-measurement, because the survey's cost arguments against a
corpus-wide retrofit are untouched and are what this Set still correctly defers.

THE STALE CO-EDITOR CLAIM IS A SMALL FINDING WITH A REAL LESSON. The plan names five pending plans
(`00pirb`, `cpi6p3`, `mt54wr`, `6uhtko`, `4gx141`) queuing `25kzda` edits "measured at HEAD `764442f7`".
Re-measured: `00pirb` has since executed (as `b7tlsh`/`00pirb`), and `mt54wr` and `6uhtko` declare no
`25kzda` path at all. I checked the cited HEAD before calling it drift, and they did not declare it there
either, so two of the five were wrong when written rather than merely stale. Thirteen pending plans declare
one today. This is the live-artifact re-derivation convention exactly: a count of pending plans is a
drifting population and belongs in prose as context, never as a claim an executor relies on. The claim
that actually matters is unaffected and I kept it: this Set declares no `.spec.md` edit at all, so it
cannot collide with any of them whatever the number.

ONE THING I CHECKED AND DELIBERATELY DID NOT FLAG. The parent's `- Scope-Paths:` names only itself, which
looks under-declared for a plan whose V-items read two children and a spec. It is correct: those are READS,
and the scope fence governs what the plan WRITES. Flagging it would have pushed the executor toward
declaring paths it must not modify.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | HIGH | IN-SCOPE | Rubric A/C (correctness, use existing canonical mechanisms) | Plan "Cross-IPD validation" SECOND point and "Scope check" under-scope row; `.aw/records/specs/approved/20260826-25kzda-...spec.md` Section 2.7 dependency grammar; `runner_shared.parse_dependency_token`; `runner_shared.edge_satisfied` `state:` branch; `rtvdak` F-10 | The plan asserts the dependency grammar offers edges only "over plans", that no edge can express "a human approved it", and that the approval is something "no runner can perform or detect". The detect half is FALSE: `state:spec:approved:<id6>` is a legal, parsed, and runner-enforced edge. The consequence is not cosmetic: the Set's ONLY human gate was left to Order 02's own first item (an agent's self-discipline) when the runner could refuse dispatch outright. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Parent's Cross-IPD SECOND point rewritten with the four measurements and the correction labelled; "Scope check" under-scope row corrected; a new completion criterion added; V-02 now requires the edge be pasted and `aw check` show it non-dangling. Owning child `jjh4aj` E-09 now writes the edge with `aw ipd dependencies set rtvdak executed:jjh4aj state:spec:approved:<id6> --yes` (verified by `--dry-run` at review), with the id6-minting reason stated; dependent child `rtvdak` F-10 corrected to match. Order 02's E-01 refusal retained as the second layer. |
| PR-102 | MEDIUM | IN-SCOPE | Rubric G (execution contract), AGENTS.md agent execution contract | Plan "Approval and execution gate"; `rg -c "ACTUAL"` -> 0, `rg -c "never push"` -> 0 (only a bare "Never push") | The gate lacked three required execution-contract elements: the hard-MUST honesty rule (paste the ACTUAL output), a path-scoped commit instruction with the staged-set verification, and conditional finalize OWNERSHIP (it said "through the tooled transition" but never distinguished runner-owned from hand-run, so an agent in a managed lane could wrongly invoke `aw ipd finalize`). For a parent whose entire deliverable is verifying its children, the missing paste rule is the load-bearing one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a PASTE ACTUAL OUTPUT paragraph stating that an unpasted claim verifies nothing; a COMMIT PATH AND SCOPE paragraph (`aw commit <plan> -- <paths>`, never `git add -A`/`-a`, never push, verify with `git diff --cached --name-only`, and the scope line as a DECLARATION with `--scope-reason` rather than a stop); and rewrote POST-GATE LIFECYCLE with conditional ownership plus the rule that a retirement refusal is reported, never fixed by deleting a checklist or child row. |
| PR-103 | MEDIUM | IN-SCOPE | Rubric G, live-artifact re-derivation convention | Plan "Cross-IPD validation" THIRD point; `aw find plans 00pirb` -> `executed`; `rg -n '^- Scope-Paths:' ` on `mt54wr` and `6uhtko`; `git show 764442f7:<path>` for all five | The named five-plan `25kzda` co-editor population is a LIVE artifact count used as a claim. It is partly false and now stale: `00pirb` has executed, and `mt54wr` and `6uhtko` declare no `25kzda` path, including at the cited HEAD `764442f7`, so two were wrong when written. Thirteen pending plans declare one today. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced the hardcoded list with the PROPERTY plus a re-derivation command (`rg -l '^- Scope-Paths:.*25kzda' .aw/records/plans/pending/`), kept the measurements as dated context, and restated the claim that actually matters (this Set declares no `.spec.md` edit, so it cannot collide whatever the count). |
| PR-104 | LOW | IN-SCOPE | Rubric D (evidence strength), honest reconciliation | `.aw/records/research/20260920-specreq-00-vkub9o-...survey.md` recommendations #2 and #3; `.aw/records/backlog/done/20260920-1zknu7-...backlog.md`; `check_engine` `check.plan-spec-link-missing`; live count 34; `c4gd2h` edge census 1 of 71 | The plan's reconciliation of the survey's "Do NOT build a requirement parser" understates its own case. The survey's decisive objection (the missing plan-to-spec edge) was filed as backlog `1zknu7`, which is `done`, and the survey's recommendation #2 shipped as `check.plan-spec-link-missing`. So #3 rested on a blocker #2 was written to remove. The plan argues only that the objection does not REACH the dispatcher. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a paragraph to the gate recording the discharge with its measurements, explicitly bounded so no child may cite it as licence to skip its own re-measurement, and noting the survey's retrofit cost arguments remain untouched and still correctly deferred. |
| PR-105 | LOW | IN-SCOPE | Rubric E (expected evidence) | Plan V-01's `grep -nE '^- (Approval\|Readiness):' <spec>` | V-01 requires a command whose PASS is an empty result and a nonzero exit, which an executor can easily misread as a broken command and "fix" by weakening. Verified at review on a real `to-review` spec: exit 1, no output. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now states that an empty result IS the pass and was confirmed at review against a real `to-review` spec, so the absence of output is not read as a failed command. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The plan says no dependency edge can express the human spec approval. Is that true, and if not, must the Set use one? | False, and the Set must use one: add `state:spec:approved:<spec-id6>` beside `executed:jjh4aj`. | (a) Leave the claim and rely on Order 02's E-01 refusal alone. REJECTED: that is an agent's self-discipline standing in for a gate the runner can enforce, and the plan's own framing ("no runner can detect") would have taught future readers a false limit. (b) Replace `executed:jjh4aj` with the `state:` edge. REJECTED: the two prove different things (Order 01's work landed vs the spec reached `approved`), so both are needed. | `25kzda` 2.7 grammar (`target-type = "ipd" \| "spec" \| "backlog"`); `parse_dependency_token` returning a valid edge and `None` for a bad status; `edge_satisfied`'s `state:` refusal message; `aw ipd dependencies set ... --dry-run` validating the two-edge statement. | yes |
| D-2 | Which plan owns writing that edge, given the spec id6 does not exist until Order 01 runs? | Order 01's E-09, the existing handoff item. | (a) Declare it in Order 02's front matter now. IMPOSSIBLE: `aw specs new` mints the id6 during Order 01 E-03, so there is nothing to name, which is the legitimate reason it was absent. (b) Put it on the parent. REJECTED: the parent must carry orchestration only; a write parked there is performed by nobody because the runner retires an orchestrator without an agent turn or an E/V checkpoint. | `jjh4aj` E-03 (`aw specs new --apply` mints the id6) and E-09 (already performs the handoff); the orchestrator-coverage rule in AGENTS.md. | yes |
| D-3 | Which command writes `Item-Dependencies`? | `aw ipd dependencies set <selector> <edge...>`. | `aw ipd set --item-dependencies`, which I wrote FIRST and then refuted: no such flag exists on `aw ipd set` or `aw specs set`. Caught by reading `--help` and by locating `status_set.run_ipd_dependencies_set`. | `aw ipd dependencies set --help` (documents all three edge kinds and pre-write validation); a successful `--dry-run` of the exact two-edge statement. | yes |
| D-4 | Should the stale five-plan `25kzda` co-editor list be corrected to today's 13, or replaced? | Replaced with the property plus a re-derivation command, keeping the numbers as dated context. | Update the count to 13. REJECTED: that re-commits the same error one day later, since a pending-plan population drifts daily; the rubric's live-artifact convention requires the property be the bar and the count be context. | Measured drift (`00pirb` executed; `mt54wr`/`6uhtko` never declared the path, checked at `764442f7` too); the live-artifact vs stable-code-fact convention in the plan-review rubric. | yes |
| D-5 | Is the plan's departure from research `vkub9o`'s "Do NOT build a requirement parser" acceptable? | Yes, and it is better supported than the plan argues; recorded as a strengthening rather than reopened. | Treat the survey as controlling and flag the Set as REPLAN. REJECTED: the maintainer's 2026-09-26 ruling postdates the survey and directs exactly this work, backlog `vy20et` records it, and the survey's decisive objection has since been discharged (`1zknu7` `done`, `check.plan-spec-link-missing` live on 34 plans). The survey's retrofit cost arguments stand and remain deferred. | `vy20et` history line quoting the ruling; `z7nbn1` OQ-02 REVISED 2026-09-26; `vkub9o` sections 3.2 and 5; `1zknu7` closure evidence; live checker count. | yes |
| D-6 | May this review edit the two child plans, which were not the named target? | Yes, for the one cross-plan finding, fixing it in the OWNING plan and cross-referencing the dependent. | Record the finding only against the parent. REJECTED: the workflow directs a cross-plan finding be fixed in the owning plan, and the parent cannot write Order 02's dependency field; leaving `rtvdak` F-10 asserting the false claim would also strand a contradiction in an unedited sibling. Checked first that no concurrent lane input names `jjh4aj` or `rtvdak`. | Plan-review Step 2.4 ("fix it in the owning plan and cross-reference it from dependent plans"); `ls .aw/state/lane-inputs/*/` showing no lane holds either child. | yes |

No decision in this round is `Reversible: no`, so none requires escalation beyond this record. No finding
was left `OPEN` or `DEFERRED`, so no `- Blocking: yes` escalation is owed under the gate threshold.
