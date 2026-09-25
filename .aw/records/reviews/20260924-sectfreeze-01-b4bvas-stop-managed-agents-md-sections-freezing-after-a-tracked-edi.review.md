# Review findings: plan b4bvas

- Subject-Id: b4bvas
- Subject-Type: ipd
- Reviewed-At: 2026-09-24
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed Order 01 of Set `sectfreeze`, the only child, `- Item-Dependencies: none`. Structural preflight
`aw ipd lint --phase author --agent` reported exit 0 BEFORE semantic review (one INFO advisory), and
`--phase review-finalize --agent` reports exit 0 after the revisions with that same advisory assessed and
declined in the gate. The plan file was committed and unchanged, so no pre-review snapshot was needed.
Everything below was measured in this lane at HEAD `f768cadd`.

EVERY AUTHOR CLAIM HELD, AND THE TWO DEFECTS ARE REAL AND REPRODUCIBLE. I drove
`engine._apply_section_consent` directly rather than re-reading the plan:

```text
CASE 1 (disk == desired, STALE record)          -- F-3, the freeze root cause
  result body == desired?   True
  recorded before           7a13186b5e91ffdc
  recorded after            7a13186b5e91ffdc      <- never refreshed
  desired hash              e040dc8863d1df9a
  hash REFRESHED?           False

CASE 4 (NO record, disk is a user edit)         -- F-4, the silent clobber
  user body KEPT?           False                <- overwritten
  result == desired?        True
  record written for key?   True

THIS REPO IS IN THE FROZEN STATE                -- F-1
  recorded AGENTS.md#aw:pointer  7446019fdd5cdd49...
  on-disk pointer hash           b8a499dfca3adedd...
  generated pointer hash         b8a499dfca3adedd...
  target layout                  aw
  => recorded != disk (frozen), and disk == generated (exactly case 1)
  siblings consistent: AGENTS.md#aw:reporting 2ab6fbfb, .gitignore#aw:untracked 137d080a
```

The design is right and minimal: four explicit branches in the one function every caller delegates to,
a warning list threaded through `merge_aw_block`, and a reconciliation performed through the installer's
own code path rather than by hand. OQ-01's resolution (preserve rather than adopt for case 4) is
correctly reasoned: the shim fallback adopts only STRUCTURALLY VALID generated content, and I confirmed
that `_shim_is_user_modified`'s no-record branch really does rest on a structural test with no analogue
for free prose, so adoption here would reintroduce F-4.

THE SUBSTANCE OF THE REVIEW IS TWO INSTRUCTIONS THAT COULD NOT HAVE WORKED, both found by running code
rather than reading it. One targets a print site that is unreachable for the case it must cover; the
other asserts an outcome that is a no-op until an earlier item lands.

```text
F-8  E-03's PRINT IS UNREACHABLE IN ensure_untracked_gitignore
     grep for print() in that function -> NO hits; it RETURNS a status string
     body order after merge_aw_block:
         if new_text == existing: return "untracked-safety block already current"   <- fires first
         if plan.dry_run:         return "would add ... [dry-run]"                  <- fires next
     a PRESERVED section is exactly the new_text == existing case, so a print after
     those returns never runs

F-9  E-05 IS A NO-OP UNTIL E-02 LANDS (ran E-05's exact command on a copied tree)
     unpatched: {'AGENTS.md': 'pointer already current', ...}   manifest keys CHANGED: []
     patched  : same status dict                                manifest keys CHANGED:
                                                                  ['AGENTS.md#aw:pointer']
                                                                  7446019f -> b8a499df
     => the claimed diff is exactly right, but only with the fix applied; a null diff
        run early diagnoses a missing E-02, not a failed reconciliation
```

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A (correctness) / F (prevent silent failure) | `agent_workflows/engine.py` `ensure_untracked_gitignore`, `install_into_repo` | E-03's INSTRUCTION LANDS ON UNREACHABLE CODE FOR THE CASE IT EXISTS TO COVER. It says to print the collected warnings in both callers, but `ensure_untracked_gitignore` contains NO `print` at all: it returns a status string that `install_into_repo` stores as `untracked_ignore_status` and renders later. Worse, it returns EARLY on both paths a preserved section takes, `if new_text == existing: return ...` first (which IS the common preserved case, since preserving means the rendered text is unchanged) and `if plan.dry_run: return ...` next. An executor following E-03 literally would add a print below those returns, watch it never fire, and either conclude the warning plumbing is broken or quietly drop the `.gitignore` half. The `update_agents_pointer` caller has a different shape again (it builds a `results` dict its caller renders), so a single "print in both callers" instruction does not fit either one cleanly. | C:Low; U:Medium; S:Low; F:Medium; Overall:Low | FIXED | E-03 rewritten to describe the two callers' ACTUAL shapes, to require the emission sit BEFORE both early returns (option a) or be returned to the call site (option b), and to require the choice be DECLARED in V-03. V-03 now demands the diff showing the emission precedes the returns, plus proof a preserved `.gitignore` section warns on the `new_text == existing` path. `Scope check` updated so "touched" is accurate for that caller. F-8 records the greps. |
| PR-002 | HIGH | IN-SCOPE | E (verification) / G (executability) | plan `E-05`; `engine.merge_aw_block`, `engine.update_agents_pointer` | E-05 ASSERTS AN OUTCOME THAT IS A NO-OP UNTIL E-02 LANDS, without saying so, so an executor who runs it early sees a null diff and can reasonably conclude the reconciliation is broken (or worse, record V-05 as satisfied by that null diff). Measured by running E-05's exact command in a throwaway copy of this repo: against CURRENT code, `AGENTS.md` unchanged and ZERO manifest keys changed, so the stale `7446019f` survives; with the four-branch fix patched in, the SAME command yields exactly the claimed one-key diff `7446019f -> b8a499df` and nothing else. The `Depends on: E-03` edge already sequences it right; what was missing is the diagnostic reading of a null result. Compounding it, the status dict says `pointer already current` in BOTH runs, because the manifest mutation happens inside `merge_aw_block` independently of the file write, so the one visible signal looks identical whether the reconciliation worked or did nothing. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 gained the measurement, an explicit statement that a null first run diagnoses a missing E-02, and the write-independent-mutation mechanism (F-10) so the misleading status line is expected rather than alarming. V-05 now says `pointer already current` is CONSISTENT with a real manifest change and forbids recording V-05 as satisfied by a null diff. The gate carries the ordering as a named hazard. |
| PR-003 | MEDIUM | IN-SCOPE | E (verification) | plan `E-05`, `V-05`, `E-04`, `V-04` | LIVE ARTIFACT VALUES WERE STATED AS THE BAR. V-05 requires the diff show the hash "moving `7446019f...` -> `b8a499df...`", and E-04 says to use "the next free number after D154". Both are facts about the repository at authoring time that drift: a re-record or a new decision between review and execution moves them, and an executor comparing against the literal would report a false failure. The stable bars are the PROPERTIES (the recorded pointer hash ends equal to the on-disk body hash and no other key moved; the decision number is the next free one). | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | V-05 states the required property, keeps the hashes as context, and requires re-derivation; V-04 requires the highest existing decision number be RE-DERIVED at execution and both it and the number used be pasted (measured `D154` at review, so `D155` was next free then). |
| PR-004 | MEDIUM | UNDER-SCOPE | G (executability) | plan `## Approval and execution gate` | THE GATE WAS ONE PARAGRAPH AND OMITTED THIS PLAN'S DEFINING HAZARDS. It carried the commit discipline, the honesty rule, the OQ disposition and the correct never-hand-edit rule, but no statement of what a human is approving (cases 3 and 4 change behavior for EVERY managed repo, not just this one), no declaration-style scope fence, and no stop conditions, even though the plan body already identifies three genuinely unsafe ones (a broader E-05 diff, the defect already fixed, and reaching the full `install . -y` verb that was measured to self-commit 95 files with a raw `git commit`). It also did not state the ordering hazard PR-002 found, nor say WHY hand-editing the manifest is forbidden rather than merely discouraged. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate rewritten: what is approved, with the accepted friction and the rejected case-4 alternative flagged for the maintainer; declaration-style fence; the ordering hazard named with its measurement; three genuinely-unsafe stop conditions; the reason hand-writing a hash is a forged-evidence problem rather than a style violation; the bare-`pytest` rule with the `-qq` trap; live-hash re-derivation; staged-set verification noting `AGENTS.md` and the manifest are contended files; conditional transition with no hand-rolled `git mv`; and the `krwl3t` HANDOFF verified as already satisfied. |
| PR-005 | LOW | IN-SCOPE | G (right-sizing) | `aw ipd lint` `IPD-Z602` on E-04 | THE SIZE ADVISORY WAS LEFT UNADDRESSED. `aw ipd lint` raises `IPD-Z602` on E-04 ("may bundle multiple concerns"), and the plan's `Size assessment: standard` says nothing about it. A passing count-based lint does not clear conceptual density, and the workflow treats a sizing signal as a finding to investigate by decomposition rather than dismiss. E-04 genuinely does touch three files, which is what trips the heuristic. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Investigated by decomposition and DECLINED with the reasoning recorded in the gate: E-04 is three FILES but one CONCERN (write down the amended four-case rule), documentation only, no independent test surface, a few lines each, and one `V-*` whose bar is precisely that all three agree. Splitting it into three items whose only relationship is that they must say the same thing makes divergence MORE likely, not less. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001: E-03's print site is unreachable in one caller. Prescribe one approach, or offer the executor a choice? | Offer two named options, require the choice be DECLARED in V-03, and state a preference. | (a) Mandate printing before the early returns only. Rejected as the sole option because a status-string test could pin that function's output shape and make the in-function print awkward; I did not exhaustively verify no such test exists, so forcing one approach risks a stop. (b) Mandate returning warnings to `install_into_repo` only. Rejected: a larger change to a function signature and its single call site, for a bug fix. | Measured that the function has no print and returns early on both preserved-section paths, so SOME restructuring is unavoidable; both options satisfy the requirement, and the `update_agents_pointer` caller has a different shape anyway, so one uniform instruction was never going to fit. Declaring the choice keeps the decision auditable at validation rather than invisible in a diff. | yes |
| D-2 | PR-002: is E-05's null-against-current-code behavior a defect in the plan, or merely an ordering nuance a competent executor would infer? | Treat it as a finding and write the diagnosis into the plan. | Leaving it implicit on the strength of the existing `Depends on: E-03` edge. Rejected: the edge sequences the work but says nothing about how to READ a null result, and the one visible signal (`pointer already current`) is byte-identical whether the reconciliation worked or did nothing, so the failure mode is genuinely indistinguishable without the note. | Measured both runs. The status dict is identical in each; only the manifest diff differs. An executor seeing `pointer already current` plus an empty diff has no way to tell "not yet fixed" from "reconciliation ineffective", and the plan's stated Expected outcome would read as violated in both. | yes |
| D-3 | Should OQ-01's resolution (preserve rather than adopt for case 4) be reopened as a blocking question, given it changes behavior for every managed repo? | No. Accept the author's resolution; surface it in the gate for the approver instead. | Re-opening it as `Blocking: yes`. Rejected: the author resolved it from evidence, the reasoning is sound, and a blocking question would hold the plan for a decision the maintainer can make at approval in one line. | Verified the asymmetry the resolution rests on: `_shim_is_user_modified`'s no-record branch adopts only STRUCTURALLY VALID generated content (its own docstring: "adopt an existing STRUCTURALLY-VALID generated shim ... and treat genuinely foreign content as user-modified"), and there is no structural validity test for free-prose sections, so adoption would be unconditional and would reintroduce F-4's silent clobber. The gate now names the alternative explicitly so approval is an informed choice. | yes |
| D-4 | PR-005: does `IPD-Z602` on E-04 require a split? | No split. Record the assessment. | Splitting E-04 into three per-file E-items. Rejected: it would create three items whose only coupling is that they must state the same rule, which increases the chance they diverge, and would fragment one coherent `V-*` bar into three weaker ones. | `plan-review` rubric G right-sizing: E-04 is one concern, documentation only, no code, no independent test surface, a few lines per file, verified by one `V-*` whose criterion is precisely that the three agree. The advisory is count-shaped (three files, semicolon-chained clauses) and does not measure that coupling. | yes |
| D-5 | The plan's `install . -y` observation (F-6: 95 files, 111 manifest entries, a self-made raw commit) is deferred as out of scope. Accept, or raise it? | Accept the deferral; do not widen this plan. Note it as a stop condition instead. | Filing it as a finding here, or adding E-items to fix the installer's raw commit. Rejected: it is genuinely unrelated to section consent, and the plan already records it honestly as an observation for the maintainer. | The plan's `Deferred / out of scope` entry states it accurately and declines it for the right reason. What was missing was protection for THIS execution, so the gate now lists "the full `install . -y` verb is reached for any reason" as a stop condition, since that verb would violate the execution contract mid-plan. That converts an observation into a guardrail without widening scope. | yes |

### Measurements taken at review

```text
aw ipd lint --phase author          --agent b4bvas -> exit 0, 1 INFO (IPD-Z602 on E-04)
aw ipd lint --phase review-finalize --agent b4bvas -> exit 0, same INFO (assessed in D-4)

THE TWO DEFECTS, driven directly through engine._apply_section_consent:
  case 1 (disk==desired, stale record): result desired True, hash REFRESHED False   # F-3
  case 4 (no record, user edit):         user body KEPT False, record written True   # F-4

THIS REPO'S FROZEN POINTER:                                                          # F-1
  recorded 7446019fdd5cdd49... | on-disk b8a499dfca3adedd... | generated (same)
  recorded != disk -> frozen ; disk == generated -> case 1 (self-heals after the fix)
  AGENTS.md slugs generated ['pointer','reporting'] == on-disk; reporting is consistent

E-05's COMMAND, run on a copied tree:                                                # F-9
  unpatched -> status {'AGENTS.md': 'pointer already current', 'CLAUDE.md': 'not present
               (skipped)', 'GEMINI.md': 'not present (skipped)'}, manifest keys changed []
  patched   -> same status, manifest keys changed ['AGENTS.md#aw:pointer'] 7446019f->b8a499df
               AGENTS.md unchanged in both

ensure_untracked_gitignore:                                                          # F-8
  print() occurrences in the function: NONE
  returns early: `if new_text == existing: return ...` then `if plan.dry_run: return ...`
  caller: install_into_repo stores it as untracked_ignore_status and renders it later

MECHANISM (why E-05 works at all):                                                   # F-10
  the manifest record happens inside merge_aw_block/_apply_section_consent;
  update_agents_pointer decides the file write separately
  (`if new_agents == existing_agents: results[rel] = "pointer already current"`)

InstallPlan(..., manifest=m) constructible as a kwarg: True, plan.manifest is m       # F-11

EDIT TARGETS, all verified present and correctly described:                           # F-12
  .aw/system/README.md line 46 contains "leave a section you edited alone"
  highest decision D154  (so D155 next free)
  CHANGELOG: grep -c Unreleased -> 0 ; "## 2.0.0 (pending)" at line 7, has "- Fixed:" lines
  tests/test_section_consent.py ABSENT (E-01 creates it)
  D104's quoted consent clause is verbatim correct
  _shim_is_user_modified no-record branch adopts only STRUCTURALLY VALID content (OQ-01's basis)

HANDOFF: krwl3t is graduated with 'Blocks-Release: next'; this plan carries
  'From-Backlog: krwl3t' + the same gate -> HANDOFF route satisfied
```

NOT RE-RUN AT REVIEW, and stated rather than implied: the repository suite. This review changed only
planning prose, so no suite baseline is claimed in either direction. E-06 runs the bare suite at
execution, which is the correct treatment.

NOT EXHAUSTIVELY VERIFIED, and recorded rather than glossed: I did not enumerate every test that pins
`ensure_untracked_gitignore`'s returned status string. That is precisely why D-1 leaves the executor two
options rather than mandating the in-function print: if a status-shape test makes option (a) awkward,
option (b) is available without a stop. I also did not run the full `install . -y` verb to re-confirm
F-6's 95-file self-commit, because doing so would itself violate the execution contract in this lane;
F-6 is the author's measurement, left as theirs, and the gate now forbids reaching that verb during
execution.

### Verdict and readiness

APPROVE WITH REVISIONS APPLIED. PR-001..PR-005 all FIXED, none deferred, none open. OQ-01 remains
resolved (not reopened, see D-3), and there is no open blocking question, so the plan is not `NO-GO`.

Readiness `go-pending-approval`. What a human should weigh at approval, none of it a finding: cases 3
and 4 change installer behavior for EVERY managed repo, not just this one. Case 3 means a drifted
section is kept and named on every install (one warning line, with a working remedy printed); case 4
means a section with no record is now KEPT rather than silently replaced, which is the direction that
protects a user's edit but also preserves a stale hand-edit the installer would previously have
cleaned up. OQ-01 chose preserve over the shim path's adopt, and that choice is the one thing here a
maintainer might reasonably reverse; if adoption is preferred, say so at approval, because it undoes
half this plan's intent. The freeze fix itself (case 1) is uncontroversial and self-heals this repo's
own pointer on the next install.
