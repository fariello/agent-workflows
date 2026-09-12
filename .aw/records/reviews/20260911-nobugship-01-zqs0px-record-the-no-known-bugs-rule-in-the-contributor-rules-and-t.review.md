# Review: record the no-known-bugs rule in the contributor rules and the decisions log, child zqs0px (Set nobugship)

- Subject-Id: zqs0px
- Subject-Type: ipd
- Reviewed-At: 2026-09-12
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `839c1ff8`. Structural preflight `aw ipd lint --phase author --agent` CONFORMED
(clean, exit 0, 0 findings) before semantic review, and `--phase review-finalize` conformed again after
every revision below. The suite was measured bare: `5971 passed, 3 skipped, 2 xfailed in 68.73s`.

DISCLOSURE: this Set was authored in the same repository by the same model family, so treat this as a
near-self-review worth less than an independent one. Its value rests on what was EXECUTED rather than on
the reading. Five things were driven rather than recalled: the managed-block boundary read out of
`AGENTS.md`; the originating commit message of the section under edit; a `grep` for the section's prose
in the generator; the installer's own `merge_aw_block` CALLED over the live `AGENTS.md`; and the
shipped parity assertions run.

SCOPE OF THE LEDGER. The invocation named this child only, so the ledger is that one plan. The
orchestrator `qmgn12` and siblings `di08i9` / `rgaasb` were read as EVIDENCE and NOT edited, matching how
this repository reviews a Set (each member carries its own record). Nothing found here reaches into a
sibling's scope, so nothing needed cross-referencing into one.

THE PLAN'S THESIS IS CORRECT AND ITS SHAPE IS RIGHT. The rule really is written nowhere: the `grep` for
"don't ship known bugs", "no known bugs", "every bug blocks" and "known bugs" across `AGENTS.md`,
`DECISIONS.md`, `GUIDING_PRINCIPLES.md`, `.aw/records/backlog/README.md`, `CONTRIBUTING.md` and
`RELEASING.md` returns NOTHING (exit 1) at this HEAD. Writing it in the release-gates section plus a
numbered decision is the right two-part answer, and review changed neither.

THE ONE FINDING THAT MATTERED IS THAT THE PLAN'S DEFINING HAZARD WAS FALSE. The plan states, in five
separate places including a capitalized closing note, that `AGENTS.md`'s release-gates text is GENERATED
from `engine.py` and that a direct edit would be silently reverted, and it instructs the executor to edit
the generator instead. Four independent proofs say otherwise. The section sits at line 125 while the
managed block CLOSES at line 108. Its originating commit (`9cf9178`, 2026-08-18) says in its own message
that it was "Placed in the hand-maintained region (outside the managed aw:block) so a regen preserves
it". `grep -c` for the heading or its opening sentence in `engine.py` returns `0`. And driving
`engine.merge_aw_block` over the live file returns action `refreshed` with the section INTACT and a
three-line diff consisting only of blank-line removals.

WHY THAT IS A BLOCKER RATHER THAN A CORRECTION. This is the plan's most emphatic instruction, so it is
the one most likely to be obeyed. Following it would put this repository's own release policy into
`engine.py`, which is INSTALLED INTO EVERY ADOPTER REPO, giving a repo-local decision a global blast
radius. It would also break `tests/test_shared_checkout_contract.py:132`, which asserts this repo's
managed block equals the generated text, until `AGENTS.md` was regenerated to match. The plan's own goal
would be met in the wrong file, and the honest recording it exists to produce would be a change to
every downstream user's contract.

THE ROOT CAUSE THE FINDINGS SHARE is that the plan reasoned about `AGENTS.md` as a GENERATED FILE when
it is a MIXED file with a marked boundary. Everything else follows: the wrong `Scope-Paths` entry
(PR-002), the E-01 that asks for the boundary and then presupposes the answer (PR-003), the E-02 that
edits the generator (PR-001), and the E-04 whose success criterion is inverted because it expected a
regeneration diff (PR-004). Three further findings are the ordinary kind: an instruction with no
question to carry its one judgement call (PR-005), a mis-scoped grep that would fail on prose the
executor did not write (PR-006), and a missing suite baseline (PR-008).

WHAT REVIEW CHANGED. Nine findings, all FIXED, no deferrals, no open questions left. `engine.py` was
removed from `Scope-Paths` (4 paths to 3). E-items grew 4 to 5 and V-items 4 to 5, keeping the
bijection: E-01 now re-proves the boundary with three pasteable commands and a STOP condition, E-02
edits `AGENTS.md` directly and forbids the generator, E-04 was INVERTED to run the two shipped parity
assertions and expect them unchanged, and a new E-05 drives the merge post-edit to prove the rule
survives an install (the durability claim the whole Set rests on, previously untested). OQ-01 was
RESOLVED from evidence, a new OQ-02 records the no-threshold ruling, and the false hazard is retracted
in place with its correction rather than deleted, so a later reader can see which claim moved and why.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. correctness; C. architecture; G. executability | `AGENTS.md:108` (`<!-- /aw:block -->`) versus `:125` (`## Release gates`); commit `9cf9178` message; `grep -c "Release gates\|first-class record under" agent_workflows/engine.py` = 0; `engine.merge_aw_block` driven over the live file returns `refreshed` with the section intact | **The plan's defining hazard is false, and acting on it would ship a repo-local policy to every adopter.** The plan asserts in five places (history line, E-01, E-02, F-4, closing note) that the release-gates text is GENERATED from `engine.py` and that a direct `AGENTS.md` edit is reverted on install, and instructs editing the generator. FOUR PROOFS SAY OTHERWISE: the section is below the closing managed marker; its originating commit says the placement was chosen "so a regen preserves it"; no generator carries the prose; and driving the installer's own merge leaves it untouched. The generator block is installed into every managed repo, so following the instruction would export this repository's release policy to all adopters AND break the parity assertion at `tests/test_shared_checkout_contract.py:132` until `AGENTS.md` was regenerated | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected in all five places. Metadata drops `agent_workflows/engine.py` from `Scope-Paths`; E-01 re-proves the boundary with three pasteable commands plus a STOP condition; E-02 states the target as the existing hand-maintained section and explicitly forbids the generator edit and a regeneration; F-4 is rewritten as a CORRECTED finding carrying all four proofs; the authored history line keeps its claim marked RETRACTED with the correction beside it, so the record shows what moved; the closing note is inverted and names the real hazard (an edit straying ABOVE the marker) |
| PR-002 | HIGH | OVER-SCOPE | C. architecture; G. executability | `- Scope-Paths:` as authored; PR-001's proofs | **`agent_workflows/engine.py` is declared in `Scope-Paths` for a change that must not touch it.** A declared path is a promise the run is reconciled against, so declaring the generator invites the very edit PR-001 forbids and would make a wrong edit look sanctioned at finalize | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Removed from `Scope-Paths`, leaving three paths. The deferred section and the scope check both record the removal WITH its reason, so a later reader does not restore it as an oversight. V-02 adds `git status --porcelain -- agent_workflows/engine.py` proving the file is unmodified |
| PR-003 | HIGH | IN-SCOPE | G. executability; E. testing | E-01 as authored ("ALSO DETERMINE WHETHER THE TEXT IS GENERATED. The release-gates section is installed into managed repos from `engine.py`") | **E-01 asks the executor to establish the generated-versus-local boundary and then states the wrong answer in the same breath, so the investigation is prejudiced.** An agent reading a capitalized assertion of the conclusion will confirm rather than measure it. The item also gave no command to run and no failure branch | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 rewritten to RE-PROVE the settled answer with three specific pasteable commands (marker positions, the zero-hit generator grep, the driven merge), each with review's measured result stated so a disagreement is visible, plus an explicit STOP-and-report branch if any command disagrees, which is the legitimate unsafe-condition stop rather than a scope stop. V-01 now demands all three outputs |
| PR-004 | HIGH | IN-SCOPE | E. testing | E-04 as authored ("If the regeneration produces a near-empty diff, treat that as a FAILURE signal") | **E-04's success criterion is inverted, so a correct execution would be reported as a failure.** It demands a nonempty regeneration diff as proof the edit landed, which follows only from PR-001's false premise. Under the true premise the edit is outside the managed block, so the managed-block diff MUST stay empty, and a nonempty one means the edit landed in the wrong place. As written the item would push an executor to keep editing until it broke something | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 rewritten to RUN the two shipped assertions by name (`tests/test_shared_checkout_contract.py::NoDriftTests::test_repo_agents_block_equals_generated` at `:132`, and its P8 sibling `test_contract_is_not_duplicated_inside_and_outside_the_block` at `:139`) and to expect BOTH passing unchanged, stating explicitly that this is the correct result and not a weak one. V-04 matches |
| PR-005 | HIGH | UNDER-SCOPE | G. executability; F. principles | plan text "Do not write a numeric cutoff into the rule unless the maintainer sets one"; the plan had no `## Open questions` entry for it | **The plan's one genuine judgement call had no question to carry it, so the executor would decide it silently.** It instructs against inventing a threshold while providing no recorded resolution, which is exactly how a plan ends up with an agent's own number written into a policy document on its own authority | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added OQ-02, RESOLVED from the maintainer's own 2026-09-12 framing rather than asked: no numeric cutoff, the test is user-perceptibility, and the filer owes a measurement of the end-to-end command a user runs. Cites backlog `59t9x5` as the model, which already carries "best 530.2ms, median 571.5ms over 7 runs", the `~128ms` attribution, and the counterfactual "had the same double read cost 3ms, `chore` would have been correct". V-02 enforces the absence of a threshold |
| PR-006 | MEDIUM | IN-SCOPE | E. testing | authored V-02 ("paste a grep proving the wording contains none of `never`, `no exception`, `always must`"); `grep -c "never\|Never" AGENTS.md` = 16 | **The no-absolutes check is mis-scoped to the whole file and would fail on prose the executor did not write.** `AGENTS.md` legitimately uses "never" 16 times in other rules (the never-push contract among them), so a file-wide grep cannot pass, and an executor trying to make it pass would edit other rules | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02 narrowed to grep THE ADDED PARAGRAPH ONLY and says plainly why the whole-file grep is wrong. E-02 carries the same scoping note. The forbidden-word list was also corrected to the maintainer's actual words, quoted from plan `u06zo2` OQ-04: "never", "no override possible", "permanent", "in perpetuity" |
| PR-007 | MEDIUM | IN-SCOPE | G. executability; F. principles (P8) | authored OQ-01 left `open`; spec `20260818-1525-03` R6 ("Document the concept ... in AGENTS.md ... in ONE place") | **OQ-01 was left open when the repository already answers it, and the answer changes where the rule goes.** The plan asked whether a spec owns release-gate policy and deferred to E-01. Spec `20260818-1525-03` (`Status: implemented`) owns the MECHANISM (R1 to R5: record shape, field grammar, setter, dangling validation) and its R6 explicitly DELEGATES documenting the model to `AGENTS.md`; it says nothing about which items must carry the field. So no spec owns this policy and duplicating it into one would violate P8 rather than serve it | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 marked `resolved` with the spec cited by requirement number and the delegation quoted. Recorded as F-6 in the plan's findings table, and the spec-sync section now states the verdict as settled with the reason, while E-01 still re-runs the search so a spec that has since taken the policy would be caught. Spec-sync also states that no `.spec.md` is in scope and why |
| PR-008 | MEDIUM | IN-SCOPE | E. testing | authored required-tests section: "It must run the EXISTING generator-parity assertion (E-04) and the bare suite" with no figure and no bare-run rule | **No suite baseline and no run discipline, so a pre-existing failure would be read as caused by this change.** The section named the suite without a reference figure or the repository's bare-run rule, which the agent contract requires because the configured `addopts` already supply parallelism and quiet mode | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required-tests now carries the review-measured baseline (`5971 passed, 3 skipped, 2 xfailed in 68.73s` at HEAD `839c1ff8`) labelled REFERENCE ONLY, instructs re-measuring before the first edit and judging on the failure-SET delta, and states the bare-run rule with the reason (`-n0` or a second `-q` makes it slower and suppresses the summary line the contract requires). V-04 compares failure sets rather than counts |
| PR-009 | LOW | UNDER-SCOPE | E. testing; G. executability | the plan's Goal ("Make the rule discoverable ... and citable"); no item tested survival of an install | **Nothing tested the plan's actual durability claim.** The Set exists because an unrecorded rule does not persist, yet no item proved the newly written rule survives the mechanism that could erase it. E-04 proves only that the MANAGED block is undisturbed, which is a different property | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-05: drive `engine.merge_aw_block` post-edit and assert on the NEW RULE TEXT rather than on the section heading, with V-05 requiring the printed action and `True`. Watermark advanced 04 to 05 and the E/V bijection re-verified by `aw ipd lint --phase review-finalize` (clean) |

NO FINDING WAS DEFERRED. Every one of the nine is FIXED, so the Fix Bar's deferral machinery does not
engage: no axis rating reached Medium-High, and effort, time, cost and tokens played no part in any
decision. PR-001 is a BLOCKER by SEVERITY (it would produce a wrong, globally-scoped change) and yet
Low by Remediation Risk, because the repair is local, evidence-settled, and verifiable by running the
shipped assertions. That combination is the normal case the Bar describes and is why severity does not
decide the fix.

WHAT REVIEW DID NOT CHANGE, recorded because a reviewer that rewrites a sound plan does harm: the
two-deliverable shape (contributor rules plus a numbered decision), the choice of the existing
release-gates section as the home, both stated limits (the author-classification leak, and live-items
only), the refusal to gate `security` without asking, the refusal to retrospectively gate a `done` bug,
the instruction to state the rule as currently-enforced rather than absolute, and the decision to have
the plan gate its own release. All were checked against evidence and all are correct. The plan's
`- Item-Dependencies: none` is also correct and untouched: this child is the Set's independent first
third.

ONE THING WAS DELIBERATELY LEFT AS A JUDGEMENT FOR THE EXECUTOR rather than resolved. The plan declares
`.aw/records/backlog/README.md` and review kept it, because a filer choosing `- Work-Kind:` reads that
file and a pointer belongs there. But whether a pointer is warranted is a reading of the file's role,
not a fact, so the scope check now names the honest alternative: leave it untouched and `--scope-ack` the
unmodified declared path at finalize rather than inventing an edit to justify the declaration. That is
recorded as guidance, not as a finding, because either outcome is defensible.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan's generation premise contradicts the repository. Fix it in place, or REPLAN the child? | FIX IN PLACE. The premise is wrong but the plan's goal, home, wording constraints and limits are all correct, so the repair is bounded to the edit TARGET rather than the design. | (a) `REJECT - NEEDS REPLAN`, rejected because nothing about the deliverable changes: same rule, same section, same decisions entry, only a different file to type it into. Replanning would discard eight correct sections to fix one factual claim. (b) Deleting the false claim silently, rejected because the claim appears in the workflow history, which is a record of what the author believed; overwriting it would hide that the correction happened. Marked RETRACTED in place instead. | `AGENTS.md:108` versus `:125`; commit `9cf9178` message; zero-hit generator grep; `merge_aw_block` driven returning `refreshed` with the section intact | yes |
| D-2 | Should `AGENTS.md` be the home at all, given spec `20260818-1525-03` exists and is `implemented`? | YES, the contributor rules. The spec owns the MECHANISM and its own R6 delegates documenting the model to `AGENTS.md`. | (a) Writing the policy into that spec, rejected because it is `implemented` and this is not a mechanism change, so amending it would assert an implementation claim about text nothing implements. (b) Authoring a NEW spec for the policy, rejected as disproportionate for one paragraph of prose whose home the existing spec already names, and it would put the rule where a filing agent does not read. | spec `20260818-1525-03` R1 to R6, Status `implemented`; `AGENTS.md:125-183` already carrying the section | yes |
| D-3 | The plan wants a perceptibility test but no threshold. Ask the maintainer for a number, or resolve it? | RESOLVE, recording that there is NO numeric cutoff and that the filer owes a measurement. | (a) Asking the maintainer to set a millisecond threshold, rejected because they already answered in substance on 2026-09-12 by setting a PERCEPTIBILITY test, and asking again would re-litigate a settled ruling in a narrower form they did not choose. (b) Letting E-02 phrase it freely, rejected because the plan's own text warns against inventing a cutoff while giving the executor nothing to cite, which is how an invented number gets written into a policy document. | maintainer ruling of 2026-09-12 as recorded in backlog `59t9x5`'s history and its "Why this qualifies as a bug" section, including the 3ms counterfactual | yes |
| D-4 | Was reading the markers enough to overturn the generation claim, or should the installer be driven? | DRIVE IT. Called `engine.merge_aw_block` over the live `AGENTS.md` and inspected the result. | Reading the marker positions alone, rejected because that establishes only where the section sits, not what an install DOES to it: a generator could in principle append or rewrite below the block, and the plan's claim was specifically about install behavior. Driving the real merge settled the actual question in one step and produced the concrete evidence (`refreshed`, section intact, three blank-line diff) that the correction now cites. Editing the file to test it, rejected outright: it is a shared checkout and the merge was run in-memory with no write. | `engine.merge_aw_block` invoked with `agents_managed_sections(target_layout="aw")`; no file written; `git status` clean before and after | yes |

Every decision above is `Reversible: yes`, so recording is sufficient and no escalation is owed. None
of them changes a published interface, migrates data, deletes anything, or touches a released artifact;
the strongest is D-1, whose worst case is that a future maintainer disagrees with keeping the retracted
claim visible and deletes a paragraph.
