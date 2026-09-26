# Review findings: plan xz59ai

- Subject-Id: xz59ai
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `aa088502`. The plan cites `f46b6775`, which is an ancestor; `evaluate_carrier_obligation`
is unchanged between the two, so the plan's measurements still hold. Structural preflight
`aw ipd lint --phase author --agent` CONFORMED (exit 0, `findings: 0`) before any revision. No pre-review
snapshot was needed: the lane-input copy at `.aw/state/lane-inputs/rev-5/` is byte-identical to the
tracked file (`diff` -> IDENTICAL) and `git status --short` was empty.

BOTH AUTHORED DEFECTS REPRODUCE EXACTLY AS STATED, on the live tree:

```text
fuk1mr -> False error
  reason: deferred row 1: carrier fuk1mr resolves only to a terminal/hidden artifact (done); nothing revisits it
  fixes: ('hand it off: ...', 'cite evidence it is already addressed: add `- Carrier-Evidence: <in-tree artifact path>`', 'decline it explicitly, with a reason: ...')
  index: [('backlog', 'done', '<abs>/.aw/records/backlog/done/20260922-revalbase-01-fuk1mr-reval-ignores-suite-baseline.backlog.md')]
tgyfs2 -> False error   (same shape; index owner ('plans','executed', '<abs>/.aw/records/plans/executed/20260922-revalbase-01-tgyfs2-...ipd.md'))
```

The design is right, and I did not change it. A terminal carrier is genuinely not proof of completion
(OQ-01 is correctly resolved, and `rwhbci`'s own text supports it: `x7wfyx` was closed `done` while half
its work was unwritten), so keeping `legitimate=False` and improving the remedy is the correct shape.
F-3's structural claim about where the text surfaces is also correct and is the reason the remedy belongs
in the reason: `ipd_lint._merge_durable_carrier` builds `Diagnostic(0, 1, d.rule, d.detail)` and nothing
else from the verdict reaches the pre-transition gate. E-02 case (5) is a genuine negative control rather
than a tautology: I confirmed `_carrier_index` really does return BOTH owners for a shared id6 and that
`_resolve_carrier` short-circuits on the live one.

**THE MOST SERIOUS FINDING IS A DEFECT THIS PLAN WOULD HAVE INTRODUCED, NOT ONE IT DESCRIBES.** E-03 says
to make the finished owner's path "repo-relative against `repo_root`". The carrier index's paths come
from `status_set.inventory_all_artifacts` over `selectors.record_dirs`, which resolves the records tree
through the project context, so they are NOT always under `repo_root`. Driven on a `companion` fixture:

```text
record_dirs: [PosixPath('/tmp/<t>/repo.aw/records/plans')]
INDEX: {'pl0001': [('plans', 'executed', '/tmp/<t>/repo.aw/records/plans/executed/20260101-s-01-pl0001-y.ipd.md')]}
relative_to RAISES ValueError: '/tmp/<t>/repo.aw/records/plans/executed/...' is not in the subpath of '/tmp/<t>/repo'
```

and the same on a `home` backend (records under `<AW home>/projects/repo-<hash>/records/`). That raise
does not surface as an error, because BOTH consumers wrap this evaluator in a bare `except Exception`
whose comments describe it as fail-isolation. Driven by raising inside `evaluate_carrier_obligation`:

```text
BEFORE rules: ['check.ipd-lint-diagnostic', 'check.ipd-uncarried-obligation']
AFTER  rules: ['check.ipd-lint-diagnostic']
```

and `ipd_lint.lint_file(..., checkpoint="pre-transition")` likewise dropped `check.ipd-uncarried-obligation`
from its diagnostics while still reporting the seventeen structural ones. So the failure mode is a SILENT
PASS at a rule that `.github/workflows/tests.yml` runs fail-closed and that gates every plan's terminal
transition. A message improvement must not be able to disable a gate, so I split the non-raising
derivation out as its own item (E-07) with its own validation (V-07), specified `os.path.relpath` plus
a containment check, and required the before/after be driven at BOTH surfaces rather than asserted.

**ONE OF THE PLAN'S TWO CLAIMED OUTCOMES WAS ALREADY IMPOSSIBLE.** The Scope and F-3 promised the remedy
would ride in `aw check`'s `recovery` field via `fixes[0]`. It cannot: `cli.py`'s check path calls
`enrich_drift(d, recovery=fix or "")` where `fix` is `doctor.build_remediation`'s value, and that
function has no branch for `check.ipd-uncarried-obligation`, so its generic fallback OVERWRITES whatever
the evaluator set. Measured by patching the evaluator's `fixes[0]` to the suggestion and running
`aw check plans --json`: `detail` carried it, while `recovery` read
`inspect .aw/records/plans/pending/<plan> frontmatter and schema conformity.` This is pre-existing and is
already filed as backlog `evwmm2` (`bug`/`high`/`Blocks-Release: next`) with this exact measurement, so
the right move was to withdraw the claim and name the owner, not to widen scope. E-04 now records the
`recovery` value as-is instead of asserting it.

**E-04's PASTE-AND-CLEAR STEP HAD NO NEGATIVE CONTROL.** As written it pastes the suggestion into the
scratch plan's only obligation and shows the rule no longer fires. But a plan with one obligation reports
nothing after ANY edit that removes that row, including deleting it, so the step could pass without the
pasted path resolving at all. It now requires a second, deliberately uncarried row and a count moving
2 -> 1 with the survivor named. Relatedly, E-02 case (3) proved paste-and-resolve for the plan arm only;
since the two suggestions cite different trees and `vtkfq8` adds a tree-scoped refusal to this same
branch, it now covers both arms and parses the path out of the verdict rather than re-deriving it.

**WHAT I MEASURED AND DID NOT TURN INTO A FINDING**, recorded because each was a live risk worth ruling
out. The multi-line reason is safe on every surface this rule reaches: the human `ipd lint` prints it
verbatim, `check plans --json` carries it in `detail`, and both `--agent` records are `location`+`rule`
only, so no newline can break them; the tab-separated `render_agent_drift` path that WOULD need
`attention_contract.escape_detail` has three call sites (`plans_index`, `prompts_index`,
`artifact_types`) and none of them run this rule. Length is bounded but worth stating: a three-row plan
produced a ~1.1k-char joined detail and the five-row cap would reach roughly 1.8k, so I required at most
one suggestion per row plus an `(and N more)` count. The suggestion itself does resolve
(`resolve_evidence_artifact` -> True, `path="SATISFIED"`) for both a `done` backlog path and an
`executed` plan path. `_resolve_carrier` has exactly ONE caller, so E-03's proposed signature change is
contained. And a `Carrier-Evidence` path outside the repo is refused by `resolve_evidence_artifact`
anyway (driven: absolute, `../`-relative and mis-spelled repo-relative forms all return False), which is
why E-07's fallback omits the suggestion rather than trying to cite an out-of-repo artifact.

**ONE SMALL CORRECTION WITH A DOCUMENTATION CONSEQUENCE.** E-05 told the author to document
`- Carrier-Note:` "optionally". It is not a field: `ipd_schema.CARRIER_FIELDS` is exactly the three
carrier fields, `DEFERRED_SUBFIELD_RE` matches only those three, and a row carrying both
`Carrier-Evidence` and `Carrier-Note` parses to `{'Carrier-Evidence': '...'}` with the note absent.
Documenting it in the plans README would advertise a typed subfield nothing reads, which is the
"documented only in code" problem `vtkfq8` F-9 exists to fix, inverted. The explanation goes in the row's
prose; a typed note would be a schema change with its own plan.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A. correctness; C. operability (a fail-closed gate that fails silently) | `check_engine._carrier_index` on a `companion` fixture -> owner path `/tmp/<t>/repo.aw/records/...`, `Path(p).relative_to(root)` -> `ValueError`; same on a `home` backend; raising inside `evaluate_carrier_obligation` took `check_content(repo,'plans')` rules from `['check.ipd-lint-diagnostic','check.ipd-uncarried-obligation']` to `['check.ipd-lint-diagnostic']` and dropped the rule from `ipd_lint.lint_file(..., 'pre-transition')`; bare `except Exception` in `check_engine.check_content` and `ipd_lint._merge_durable_carrier`; `aw check plans` fail-closed in `.github/workflows/tests.yml` | **E-03's PROPOSED `relative_to(repo_root)` WOULD SILENTLY DISABLE THE RULE ON A NON-REPOSITORY RECORDS BACKEND.** The carrier index legitimately holds paths outside `repo_root` (companion and home backends), where `relative_to` raises, and both gate surfaces swallow the exception rather than reporting it, so the finding DISAPPEARS at a CI-fail-closed sweep and at the pre-transition execution gate. This is a defect the plan would have INTRODUCED, not one it describes. | C:Low; U:Low; S:Low; F:Medium; Overall:Low (the fix is `os.path.relpath` plus a containment check, local and directly testable) | FIXED | New E-07 owns the non-raising derivation with the containment fallback; new V-07 demands the before/after at BOTH surfaces on a companion fixture; F-5 records the measurement; the Scope gains clause (d); the Required tests gain the backend fixture; E-06's same-count property is restated as the regression signature (a FALL in the carrier count is a failure, not progress); the gate names it as the first thing a human should look at. |
| PR-002 | MEDIUM | IN-SCOPE | G. plan executability (a claimed deliverable that cannot be delivered) | patched `fixes[0]` then `aw check plans --json`: `detail` carried the suggestion, `recovery` read `inspect <plan> frontmatter and schema conformity.`; `cli.py` calls `enrich_drift(d, recovery=fix or "")` with `doctor.build_remediation`'s value; `build_remediation` has no branch for this rule; `.aw/records/backlog/open/20260918-evwmm2-01-evwmm2-check-human-fix-ignores-recovery.backlog.md` | **THE PLAN PROMISES THE REMEDY WILL RIDE IN `aw check`'s `recovery` FIELD; THE CLI OVERWRITES IT.** Scope clause (a) and F-3 both asserted `fixes[0]` -> `recovery`. It is true of the evaluator and false of the surface, so half the stated delivery was unachievable and an executor would have chased it. The cause is pre-existing and already filed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope clause (a) now states the limit and names `evwmm2`; F-3 corrected in place; new F-6 records the measurement; E-01 re-measures the field so the executor sees it first; E-04 and V-01/V-04 paste `recovery` as-is and name it rather than asserting it; `doctor.py` declared explicitly out of scope. |
| PR-003 | MEDIUM | UNDER-SCOPE | E. testing (a step that passes without proving its property) | a one-obligation plan reports no carrier finding after ANY edit removing the row | **E-04's PASTE-AND-CLEAR HAS NO NEGATIVE CONTROL.** Showing the finding gone after pasting the line does not show the pasted line RESOLVED, because deleting the row produces the same output. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 now requires a second, deliberately uncarried row and a finding count of 2 -> 1 with the surviving locator named; V-04 requires that pair pasted. |
| PR-004 | MEDIUM | UNDER-SCOPE | E. testing (a case that proves one arm and assumes the other) | `resolve_evidence_artifact` accepts any in-tree `.aw/records/` path, and `vtkfq8` adds a tree-scoped refusal to this same branch; case (3) as authored used only the case-2 (plan) path | **E-02 CASE (3) PROVES THE SUGGESTION RESOLVES FOR THE PLAN ARM ONLY.** The backlog arm cites a different tree, and the walkthrough refusal `vtkfq8` lands is tree-scoped, so the backlog suggestion's resolvability was assumed rather than driven. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Case (3) now round-trips the suggestion out of BOTH the case-1 and case-2 verdicts, and must parse the path from the verdict rather than re-deriving it. |
| PR-005 | LOW | IN-SCOPE | F. KISS / honest documentation | `_deferred_section_obligations` on a row with both fields -> `{'Carrier-Evidence': '...'}`; `ipd_schema.CARRIER_FIELDS` is the three fields; `DEFERRED_SUBFIELD_RE` matches only those three; `rg -n "Carrier-Note" agent_workflows/` -> no hits | **E-05 WOULD DOCUMENT `- Carrier-Note:` AS A FIELD, AND IT IS NOT ONE.** The worked case wrote one and it reads well, but nothing parses it, so the plans README would advertise a typed subfield with no reader. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now routes the explanation to the row's PROSE and forbids presenting `Carrier-Note` as a field, noting a typed note would be a schema change in its own plan; V-05 checks it; new F-8 records the measurement. |
| PR-006 | LOW | UNDER-SCOPE | C. operability (an unbounded message on a shared surface) | three-row plan with the remedy injected -> ~1.1k-char joined `detail`; `evaluate_durable_carrier` joins up to five reasons with `"; "`; a multi-owner id6 would multiply further | **THE REMEDY'S LENGTH IS UNBOUNDED PER ROW AND PER OWNER.** The reason is concatenated across up to five failing rows into one Drift detail, and a carrier with several finished owners would emit one suggestion line each. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now caps output at the FIRST finished owner's line plus an `(and N more finished owner(s))` count, states the measured length, and V-03 requires the three-row joined detail and its length pasted. Recorded in F-7 that the multi-line form is safe on every surface this rule reaches (both `--agent` records carry no detail; the tab-separated `render_agent_drift` path has three call sites and none run this rule). |
| PR-007 | LOW | UNDER-SCOPE | G. plan executability (a missing stop condition, and one incidental drift) | the plan declares `- Item-Dependencies: executed:vtkfq8`, which the runner enforces but a hand executor does not; `f46b6775` is an ancestor of review HEAD `aa088502` with `evaluate_carrier_obligation` unchanged | **THE GATE CARRIED NO GENUINE STOP CONDITION**, though the fence, honesty rule, commit rule and finalize ownership were all correct. The two real unsafe conditions are executing before `vtkfq8` lands (both edit the same function) and being unable to derive a citable path. Also batched here: the plan's cited HEAD has moved, which is drift only, not a broken citation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a GENUINE STOP CONDITIONS paragraph covering both cases, including the explicit instruction NOT to drop the containment check to force a suggestion; the Findings preamble now states which findings were measured at which HEAD and that `f46b6775` is an ancestor. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-03 says "repo-relative against `repo_root`". Accept it, or check whether the index path is always inside the repo? | CHECK, and it is NOT: companion and home records backends put it outside, where `relative_to` raises and both surfaces swallow the finding. Split the non-raising derivation into its own item. | (a) Accept as written: rejected, it would ship a change that silently disables a fail-closed CI gate and the pre-transition execution gate on two supported backends. (b) Wrap the new code in its own `try/except` and move on: rejected, that reproduces the same silent-drop shape one level lower, and `os.path.relpath` plus a containment check simply cannot raise. (c) Fix the bare `except Exception` in both surfaces so a raise is loud: rejected as OUT of scope, since both are documented deliberate fail-isolation serving other rules, and changing them would alter the behavior of every rule in those blocks. | Companion and home fixtures driven; the raise's consequence driven through `check_content` and `ipd_lint.lint_file`; both `except Exception` blocks and their comments read; `aw check plans` fail-closed step in `.github/workflows/tests.yml`. | yes |
| D-2 | The plan claims `fixes[0]` reaches `aw check`'s `recovery`. Trust the code path, or drive the CLI? | DRIVE IT, and it is false: `doctor.build_remediation`'s generic fallback overwrites it. Withdraw the claim and name `evwmm2` as the owner. | (a) Leave the claim: rejected, it is an unachievable deliverable and V-04 would have demanded evidence that cannot exist, stalling the plan at validation. (b) Fix the overwrite here: rejected, it is a different module (`doctor.py`), it affects EVERY rule that populates recovery, and it is already filed as `evwmm2` with this same measurement; folding it in would widen a `chore` into someone else's `bug`/`high`. (c) Drop `fixes[0]` entirely: rejected, the `--json` finding shape and any future consumer still benefit, and the evaluator-level assertion is cheap. | `aw check plans --json` driven with a patched `fixes[0]`; `cli.py`'s `enrich_drift(d, recovery=fix or "")` and `doctor.build_remediation` read end to end; `evwmm2` read in full. | yes |
| D-3 | Is a multi-line refusal reason safe, or must the remedy be single-line with an escape? | SAFE on every surface this rule reaches; keep it multi-line and bound the LENGTH instead. | (a) Force a single line: rejected, it would make a three-part remedy unreadable at the gate where the executor meets it, for a rendering risk that does not exist here. (b) Route it through `attention_contract.escape_detail`: rejected, that policy exists for the tab-separated `render_agent_drift` record, whose three call sites (`plans_index`, `prompts_index`, `artifact_types`) do not run this rule; adding it would be a second mechanism guarding nothing. | Human and `--json` outputs of both `ipd lint --phase pre-transition` and `check plans` inspected with a three-line remedy injected; both `--agent` records confirmed to carry `location`+`rule` only; `rg -n "render_agent_drift"` call sites read. | yes |
| D-4 | Should E-05 document `- Carrier-Note:`, which the worked case used? | NO. Route the explanation to the row's prose; a typed note is a schema change for another plan. | (a) Document it as a field: rejected, nothing parses it (driven: the parsed field dict omits it), so the README would teach a subfield with no reader, which is exactly the inverse of the gap `vtkfq8` F-9 is fixing. (b) Add it to the schema here: rejected, this plan's Scope-Paths exclude `ipd_schema.py` and a new typed field needs its own contract, tests and lint story. | `_deferred_section_obligations` driven on a row carrying both fields; `ipd_schema.CARRIER_FIELDS` and `DEFERRED_SUBFIELD_RE` read; `rg -n "Carrier-Note" agent_workflows/` empty. | yes |
| D-5 | OQ-01 resolves that a finished carrier is NOT satisfied. Re-open it, or confirm it? | CONFIRM, unchanged. | (a) Treat `done`/`executed` as SATISFIED (the item's option 1): rejected on the evidence the plan itself cites and which I verified: `rwhbci` records `x7wfyx` closed `done` with half its work unwritten, so terminal is not proof of completion, and `_CARRIER_TERMINAL_STATUSES`' own comment names an executed plan as "the hiding place" this rule exists to close. (b) Add a verb that rewrites the row (option 2): rejected as the plan already reasons, one copy-paste against a mutating verb that edits another field at a gate. | `.aw/records/backlog/graduated/20260923-closescope-01-rwhbci-...backlog.md` read in full; `_CARRIER_TERMINAL_STATUSES`' comment block read; the worked fix in executed plan `n9na1c` read (its `Carrier-Evidence` + note row). | yes |

### Deferred and open

- (none). All seven findings were FIXED in place. PR-001 is the only one at or above the repository's
  `HIGH` gate threshold, and it is FIXED rather than deferred: the remedy is a new execution item
  (E-07) plus its validation (V-07) inside this plan's own scope, so no `- Blocking: yes` escalation
  is owed. PR-002's underlying CAUSE is not fixed, and that is correct scoping rather than a deferral:
  the cause is `doctor.build_remediation`'s generic fallback, owned by backlog `evwmm2`
  (`bug`/`high`/`Blocks-Release: next`); what this plan owed was to stop claiming an outcome it cannot
  produce, which it now does.

HONEST LIMITS, stated because they bound what this round proves. I verified the DEFECTS, the surfaces,
and the hazards; I did NOT implement the change, so that the remedy lands in exactly the right branch of
`evaluate_carrier_obligation` remains E-03's work and V-03's evidence. My PR-001 measurement used
`companion` and `home` fixtures plus a monkeypatched raise to demonstrate the swallow; I did not find a
real-world repository in this tree using either backend (this checkout is `private-target`, and all 1445
indexed id6 owners resolve inside `repo_root`), so the hazard is proven by construction on supported
configurations rather than observed in production here. I did not run the bare suite against a patched
tree, so E-06 remains a real obligation. Finally, `vtkfq8` has NOT yet executed, so every measurement
here is against the PRE-`vtkfq8` `evaluate_carrier_obligation`; E-01 exists precisely to re-measure after
it lands, and a change in that function's evidence branch could shift E-02 case (3).
