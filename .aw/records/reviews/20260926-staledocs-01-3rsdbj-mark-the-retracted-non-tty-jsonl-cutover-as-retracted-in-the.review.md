# Review findings: plan 3rsdbj

- Subject-Id: 3rsdbj
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated lane worktree. Structural preflight `aw ipd lint --phase author --detail`
CONFORMED (exit 0, no advisory) before revision. No pre-review snapshot was needed: `git status
--short` was empty, so the plan was committed and unmodified.

THE PREMISE IS CORRECT AND I RE-MEASURED IT RATHER THAN TRUSTING IT. `python3 -m agent_workflows
status | cat` prints `agent-workflows status` / `Environment:`; `check plans | cat` prints the human
`AW check plans` banner; `status --agent | head -1` prints `{"schema":"aw.agent/v1",...}`. The
retraction is real and correctly dated: `docs/cli-output-contract.md` section 9 records it, and plan
`yaxr4i`'s OQ-01 resolution reads "RESOLVED BY THE MAINTAINER 2026-09-10 ... OPTION B, CORRECT THE
DOCUMENT", so the plan's 2026-09-10 citation is exact and F-7's observation about the 09-19 heading
is right. All five cited doc locations exist with the quoted text. The plan's claim that
`docs/cli-human-guide.md` and `docs/cli-output-contract.md` are already correct is true, and using
them as reference wording is the right call: it follows the shape plan `7p3tt8` used on the same
file for the same ruling, which I verified in that plan's E-02 ("labelling the policy RETRACTED
rather than deleting it silently, exactly as that ruling requires"). Adding `CHANGELOG.md` beyond
the brief (F-5) was correct and well reasoned, since an unreleased entry announcing a break the
release will not make is the one instance with a hard deadline.

**THE CLI ITSELF PRINTS THE FALSE CLAIM, AND THAT OUTRANKS EVERY DOC IN THIS PLAN.** This is the
finding that justifies the review. `agent_workflows/renderers.py`, in the human renderer's "Agent
Output Hint" block, appends the literal line `Agent output: --agent (automatic when piped)` unless a
result sets `suppress_agent_hint`. That parenthetical is the retracted promise, printed by every
command that uses the shared human renderer. Measured: `python3 -m agent_workflows check plans | cat`
ends with that exact line while everything above it is human prose, so the claim is refuted by the
very invocation that makes it. A doc is read by whoever opens it; this reaches everyone who runs the
tool. It is NOT fixed here, and deliberately so: the string is pinned by four conformance goldens
(`check_findings.human.golden`, `error_cannot_run.human.golden`, `mutation_preview.human.golden`,
`read_clean.human.golden`), so closing it means a code edit plus golden regeneration plus a suite
run, inside a plan whose fence declares no code at all. I filed backlog `zdjhug` and the plan now
cites it and explicitly forbids the tempting one-line fix. Worth recording: `result_types.select_output`'s
docstring was ALREADY corrected for this ruling ("TTY-NESS OF STDOUT AFFECTS COLOR ONLY, NEVER THE
MODE"), so the resolver is right and only the user-visible string was missed, which is exactly the
pattern this plan exists to clean up.

**THE PLAN WOULD HAVE REPLACED ONE FALSE CLAIM WITH ANOTHER.** E-03 as authored said to keep the
three legacy byte-form items "only as far as they are still true (the machine shapes are what
`--agent` emits)", and OQ-01's resolution asserted the same. The author measured item 1 only
(`check plans --agent` does print a `diagnostics` array). Item 2 is false: `artifact_core.render_agent_drift`
still exists and has three live callers (`artifact_types.py`, `plans_index.py`, `prompts_index.py`),
and `python3 -m agent_workflows index plans --check --agent` prints
`INDEX.json<TAB>check.stale-index-stale<TAB>INDEX.json is out of date; run 'aw index plans'`. So the
TSV form the guide calls "GONE and are now `aw.agent/v1`" is still precisely what those `--agent`
surfaces emit. Reframing that list around `--agent` would have written a fresh false statement into
the file being corrected for false statements. The remedy is deliberately minimal: leave the list
textually alone, point at a carrier, and do not take a position. That is because the real fix is a
CHOICE (migrate three callers and change the bytes of a published `--agent` surface, or admit in the
docs that these verbs still emit TSV), and it needs a maintainer ruling on whether `aw.agent/v1` is
mandatory everywhere `--agent` is accepted. Filed as `qczq5r`.

**THE VERIFICATION WOULD HAVE PASSED WITH THE WORST SENTENCES INTACT.** The authored E-08 grep
pattern was `hard cutover\|default when piped\|machine format automatically`. It does not match
`docs/cli-migration.md`'s "This is automatic and immediate" or `docs/cli-agent-protocol.md`'s
"whenever stdout is not a terminal (piped, redirected, or driven by an agent)", which are the two
sentences that state the retracted behavior most plainly in the whole corpus. It also scanned only
the five declared files. Widening it found a SIXTH doc nobody had noticed, `docs/run-analytics.md`
("`--agent` is automatic when the output is piped"), now E-08 in the plan. A verification that would
have reported success on a file still containing the defect is worse than no verification, because
it manufactures confidence.

ON THE DASH CHECK, a small thing checked because the plan puts it in a gate. `git diff ... | grep
'^+' | grep -P '[\x{2013}\x{2014}]'` works (I confirmed `grep -P` handles those escapes here), but a
bare `grep` finding nothing exits 1, which is the PASS case and would abort a `set -e` shell in a
runner lane. The plan now appends `|| echo "no dashes"`. I also ran the check against the six files
at their current state: no em or en dashes present, so the baseline is clean and any hit would be
the executor's own.

SIBLING SAFETY, checked because three `staledocs` plans are pending at once. Order 02 (`xts8ux`)
declares `agent_workflows/work_cmd.py` and Order 03 (`fsme8o`) declares one release record, so
neither touches a file in this fence. I recorded that as a note for a HAND execution and explicitly
flagged that the runner isolates each item in its own worktree anyway, so it is not a runtime
hazard; the repository's own guidance is emphatic that file overlap is not a reason to warn a
maintainer about a queue.

ON THE BACKLOG CLOSE, where I found my own error and corrected it rather than shipping it. The gate
told the executor to close `sm0vgn` after execution, which is right, but I initially wrote that the
HANDOFF path was verified as legitimate. Driving it showed the opposite while the plan is pending:
`evaluate_blocking_close` returns `legitimate=False`, severity `error`, "the work has not shipped
(carrier is not executed/implemented)". The close becomes legitimate only once `aw ipd finalize`
moves the plan to `executed/`. The gate now states the refusal and the ordering rather than a
verification I had not actually obtained.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | HIGH | UNDER-SCOPE | F. honest documentation; C. operability | `agent_workflows/renderers.py` "Agent Output Hint" block: `lines.append("Agent output: --agent (automatic when piped)")`; measured `python3 -m agent_workflows check plans \| cat` ends with that line amid human prose; four goldens pin it (`check_findings`, `error_cannot_run`, `mutation_preview`, `read_clean`) | **THE CLI PRINTS THE RETRACTED PROMISE ON EVERY COMMAND.** The shared human renderer's hint claims `--agent` is "automatic when piped", which is the exact policy retracted on 2026-09-10 and never shipped. It reaches every user of the tool, far more than any doc in this plan's fence, and it is self-refuting in the same terminal. `select_output`'s docstring was already corrected for this ruling, so only the user-visible string was missed. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Recorded as F-9 and carried to new gated backlog `zdjhug`, not fixed here: it is code plus four goldens, outside a docs-only fence. The gate now names it under "what this deliberately does not fix" and the scope fence explicitly FORBIDS editing `renderers.py` or its goldens, so an executor cannot quietly turn a prose plan into a code plan. |
| PR-202 | MEDIUM | IN-SCOPE | A. correctness; F. honest documentation | `artifact_core.render_agent_drift` exists with callers in `artifact_types.py`, `plans_index.py`, `prompts_index.py`; `python3 -m agent_workflows index plans --check --agent` -> `INDEX.json<TAB>check.stale-index-stale<TAB>...` | **THE PLAN WOULD HAVE ASSERTED A SECOND FALSE CLAIM WHILE FIXING THE FIRST.** E-03 and OQ-01 both rested on "the machine shapes are what `--agent` emits". True for item 1, false for item 2: the TSV form the guide calls "GONE" is still exactly what those `--agent` verbs emit. Reframing the list around `--agent` would have written a fresh falsehood into the file being corrected for falsehoods. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F-10. E-03 now FORBIDS re-asserting the list, requires it left textually unchanged apart from auto-switch wording, and requires a `qczq5r` pointer; E-07 carries the same constraint for the CHANGELOG's copy; V-03 makes a reframed item 2 a FAILED validation. OQ-01's resolution was rewritten with the measurement, since its old rationale was the premise that failed. |
| PR-203 | MEDIUM | UNDER-SCOPE | E. verification | authored pattern `hard cutover\|default when piped\|machine format automatically` does not match `docs/cli-migration.md` "This is automatic and immediate" or `docs/cli-agent-protocol.md` "whenever stdout is not a terminal"; widening it surfaced `docs/run-analytics.md` | **THE ONLY MECHANICAL CHECK WOULD HAVE REPORTED SUCCESS ON FILES STILL CONTAINING THE DEFECT.** The three-phrase grep misses the two most direct statements of the retracted behavior and scanned only the five declared files, so it could neither catch a missed sentence in an edited file nor see a seventh instance elsewhere. A check that passes while the defect remains manufactures confidence. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-09 (was E-08) widens the pattern to six wordings and the path set to `docs README.md CHANGELOG.md`, and requires each remaining hit to be ENUMERATED with a disposition rather than the grep asserted clean. The known-legitimate hits are pre-identified so the executor is not left guessing. |
| PR-204 | MEDIUM | UNDER-SCOPE | F. honest documentation | `docs/run-analytics.md` "The agent surface": "`--agent` is automatic when the output is piped" | **A SIXTH DOC CARRIES THE SAME FALSE PROMISE** and was missed by the brief, the backlog item, the authored plan, and the authored grep. One sentence in a feature doc, but the identical wrong mental model, and it would have survived a plan whose whole purpose is removing that claim. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added as F-8 with its own item E-08 and V-08; `docs/run-analytics.md` added to `- Scope-Paths:`, Concern and Scope updated to say SIX docs, and the Task group 3 heading corrected from four to five. |
| PR-205 | LOW | IN-SCOPE | A. correctness (a live-artifact count in evidence) | F-6 recorded `CONFORMS 24 plans checked`; re-measured in review: 51 | **A DRIFTING COUNT SAT INSIDE THE PREMISE MEASUREMENT.** The count is incidental to the finding (the point is prose versus JSONL), but it is quoted as part of the evidence an executor re-derives at E-01, and a mismatch would read as a failed confirmation of a premise that in fact holds. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-6 now marks the count a live-artifact number, records both readings, and states that E-01 confirms the SHAPE only; V-01 says not to compare the count against any number in the plan. |
| PR-206 | LOW | IN-SCOPE | E. verification (a check that aborts on success) | `printf '+clean\n' \| grep '^+' \| grep -P '[\x{2013}\x{2014}]'` -> rc 1 with no output | **THE DASH CHECK EXITS NONZERO WHEN IT PASSES.** A bare `grep` that finds nothing returns 1, which under `set -e` in a runner lane aborts the step on the success path. The check itself is sound (verified `grep -P` handles the escapes here) and the current baseline is clean. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-09 appends `\|\| echo "no dashes"` and records why; V-09 expects that literal output. |
| PR-207 | LOW | IN-SCOPE | G. executability (a gate asserting an unverified fact) | my own first revision claimed a verified HANDOFF; driven: `evaluate_blocking_close(repo, <sm0vgn>, "done")` -> `legitimate=False`, `error`, "the work has not shipped (carrier is not executed/implemented)" | **THE CLOSE INSTRUCTION'S ORDERING IS LOAD-BEARING AND WAS UNSTATED**, and I nearly shipped a false verification of it. Closing `sm0vgn` `done` FAILS CLOSED while this plan sits in `pending/`; it is legitimate only after finalize moves the plan to `executed/`. Recorded rather than quietly corrected, because a reviewer who writes an unverified verification has done the thing this workflow exists to catch. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now states the measured refusal, its reason, and that the item stays `graduated` until the plan is executed. |
| PR-208 | LOW | UNDER-SCOPE | E. verification (an honesty limit) | no test under `tests/` references `CHANGELOG.md`, `docs/cli-migration.md`, or "hard cutover" (grepped) | **NOTHING TESTS THIS PLAN'S OUTPUT, AND THE PLAN DID NOT SAY SO.** Its verification is a grep plus a suite run, which together prove the old phrasings are gone and say nothing about whether the replacements are accurate. That is inherent to a docs change and fine, but leaving it implicit invites a reader to treat a clean grep as an accuracy proof. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | An explicit honesty limit added to Required tests and repeated in the gate ("A GREP IS NOT AN ACCURACY PROOF"), naming the two reference files the new prose must be read against; V-09 requires the executor to state it too. The suite item became its own E-10/V-10 with the measured no-op expectation recorded. |
| PR-209 | LOW | IN-SCOPE | G. executability | three `staledocs` plans pending; Order 02 declares `agent_workflows/work_cmd.py`, Order 03 one release record | Sibling scope was unstated. Verified DISJOINT from this fence, so there is nothing to coordinate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | A Project-conventions bullet records the disjointness AND states that the runner isolates items per worktree, so it is a note for hand execution and explicitly not a runtime hazard. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The CLI prints the same false claim as the docs (PR-201). Fix it in this plan, or carry it? | CARRY IT, to new gated backlog `zdjhug`, and forbid the fix here by name. | (a) Fix it here: rejected. The one-line wording change is trivial but four conformance goldens pin the bytes, so it brings golden regeneration and a suite run into a plan whose `- Scope-Paths:` declares six markdown files and no code; the executor would be making an undeclared code change to the shared renderer. (b) Widen this plan's fence to include `renderers.py` and the goldens: rejected, that converts a prose plan into a code plan mid-review and the maintainer approved neither. (c) Say nothing and let it be found later: rejected outright, it is the highest-reach instance of the exact defect under review. | Measured the string, its `suppress_agent_hint` guard, the self-refuting piped output, and the four pinning goldens; `select_output`'s docstring shows the ruling was already applied to the resolver, so this is a missed straggler rather than an open design question. | yes |
| D-2 | E-03 and OQ-01 rest on "the machine shapes are what `--agent` emits", which is false for item 2. Correct the docs' byte-form list here, or freeze it? | FREEZE IT: leave the three items textually unchanged, point at `qczq5r`, and forbid re-asserting them. | (a) Reframe them around `--agent` as authored: rejected, that writes a NEW false claim into the file being corrected for false claims, which is strictly worse than leaving a known-stale paragraph pointed at a carrier. (b) Correct item 2 to say these verbs still emit TSV: rejected, it is a position on whether `aw.agent/v1` is mandatory on every `--agent` surface, and a docs plan must not settle a machine-contract question by wording choice. (c) Migrate the three callers here: rejected, code change outside the fence and a bytes-level break on a published surface. | Drove `index plans --check --agent` and `index prompts --check --agent`: both emit TSV. Located `render_agent_drift` and its three live callers. The author's supporting measurement covered item 1 only. | yes |
| D-3 | Should `docs/run-analytics.md` be added to an already-authored plan, or filed separately? | ADDED to this plan as E-08. | (a) A separate backlog item: rejected, it is one sentence of the identical defect in a doc, and the plan is already editing five docs for it; deferring it would leave the corpus inconsistent for no gain and would need its own review round. (b) Leave it: rejected, the plan's stated goal is that every user-facing doc agree with the shipped behavior. | Found by widening the plan's own grep (PR-203); the sentence is a verbatim instance of the retracted promise; `docs/cli-human-guide.md` supplies the replacement wording so no new formulation is invented. | yes |
| D-4 | The plan's byte-form and hint findings both touch the same underlying question. File one carrier or two? | TWO: `zdjhug` (the renderer hint) and `qczq5r` (the byte forms). | (a) One combined item: rejected, they differ in kind, severity, and remedy. The hint is a WRONG STRING with an obvious correct value and only test churn in the way; the byte forms are a genuine open question about the machine contract needing a maintainer ruling. Bundling them would let the easy half be blocked by the hard half. (b) No carrier, findings recorded in the review only: rejected, a finding recorded only in a review record is not on any work surface and `check.ipd-uncarried-obligation` exists precisely to refuse that shape. | AGENTS.md requires a durable carrier for an outstanding obligation; the deterministic rule refuses a prose reference (it fired on my sibling review this session for exactly that). Severity and remedy differ, so priorities differ (medium versus low). | yes |
| D-5 | My own gate revision asserted a verified HANDOFF close that turned out to be refused. Silently fix, or record it? | RECORD IT as PR-207 and state the measured refusal in the gate. | (a) Silently correct the sentence: rejected, a reviewer who writes an unverified verification and then quietly removes it has still shipped an unreviewed claim, and this workflow's whole premise is that such claims are recorded and checkable. (b) Drop the close instruction: rejected, it is correct guidance and the plan legitimately inherits the gate; only the ORDER needed stating. | Drove `evaluate_blocking_close` on `sm0vgn` with the plan in `pending/`: `legitimate=False`, severity `error`, reason naming the unshipped carrier. | yes |

### Deferred and open

- (none). All nine findings were FIXED, two of them (PR-201, PR-202) by carrying the underlying work
  to a filed, gated backlog item rather than by doing it inside a docs-only fence (recorded as
  `FIXED` because the closed-vocabulary column admits no "carried" value; what was fixed in the PLAN
  is stated per row). No deferral was
  taken on the Fix Bar: nothing reached Medium-High or High Remediation Risk. PR-201 is the highest
  severity at HIGH and the highest risk at Medium overall, and it is worth being precise about what
  `FIXED` means there: the false string is STILL PRINTED by the CLI after this plan
  executes. What was fixed is the plan's blindness to it, plus the fence language that would have let
  an executor half-fix it without declaring code. The string itself is `zdjhug`'s.
- No question required the human. OQ-01 was already marked resolved, but its RATIONALE was false, so
  I rewrote the rationale with the measurement rather than reopening the question: the answer (keep
  the items) survives, the reason changed, and the part that genuinely needs a maintainer ruling is
  now a separate carrier instead of an assumption inside this plan.
- No `Reversible: no` decision was made, so no escalation to a `- Blocking: yes` question was owed.
  All five decisions are plan-text or triage choices on an unexecuted plan, each undoable.

HONEST LIMITS, stated because they bound what this round proves. FIRST, I verified that the CURRENT
text is false and that the plan's targets and reference files are right; I did not and cannot verify
that the REPLACEMENT prose will be accurate, because nothing tests it. That is the gap PR-208 makes
explicit rather than closing, and it means the approver's own read of the new text is a real part of
the verification chain here. SECOND, my search for further instances covered `docs/`, `README.md`,
`CHANGELOG.md`, `.aw/system/`, and the package source for the six known wordings; a seventh instance
phrased differently enough to miss all six patterns would still be out there, and the widened E-09
grep inherits exactly that limitation. THIRD, I did not run the suite: this review changed no code,
and E-10 owns that. FOURTH, on the byte-form question I established that item 2 is false and that
items 1 and 3 behave as the author said for the verbs I drove; I did not audit every `--agent`
surface in the CLI, so `qczq5r`'s true blast radius may be larger than the three callers I named.
