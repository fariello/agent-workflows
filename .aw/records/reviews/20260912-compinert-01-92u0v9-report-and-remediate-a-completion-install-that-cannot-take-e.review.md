# Review: report and remediate a completion install that cannot take effect, child 92u0v9 (Set compinert)

- Subject-Id: 92u0v9
- Subject-Type: ipd
- Reviewed-At: 2026-09-12
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `8e81ab9c`. Structural preflight `aw ipd lint --phase author` CONFORMED (clean, 0 findings)
before semantic review, and `--phase review-finalize` conforms after every revision below, with no
blocking question added.

DISCLOSURE: this plan was authored in the same repository by the same model family, so treat this as a
near-self-review worth less than an independent one. Its value rests on what was EXECUTED. Ten things
were run rather than re-read: the F-1 grep verbatim; both discriminator commands bare AND under
`env -i` with a fake HOME; `~/.bashrc` read in full; its mtime stat'd; `aw completion install
--shell bash --dry-run` for the real message; the promise sites enumerated by grep across three files;
`_configure_completion` and `_configure_runner_profiles` read for the `--yes` precedent;
`install_wizard`'s `os.replace` sites located; the README section its own test pins; and the probe cost
timed.

THE PLAN'S DIAGNOSIS IS CORRECT AND ITS DESIGN IS SOUND, which is why every finding is a correction
rather than a rejection. F-1 re-verified exactly: `grep -n 'profile.d\|BASH_COMPLETION_VERSINFO\|
bash_completion' agent_workflows/completion.py` returns only unrelated `generate_bash_completion`
symbol hits, so the precondition is checked nowhere. F-2 re-verified at BOTH message sites. The false
pairing is real and reproducible: `aw completion install --dry-run` prints four consecutive green `OK`
lines and the next-step instruction, with no caveat. The four-state message design, the injection
mandate, the `[y/N]` polarity, the `--yes`-does-not-consent rule and the paired-fence decision are all
correct and all left intact.

THE FINDING THAT MATTERS MOST IS THAT THE PLAN'S CENTRAL MEASUREMENT IS NOW STALE, and the cause is
benign: the maintainer fixed the machine by hand after authoring. `bash -ic 'echo
${BASH_COMPLETION_VERSINFO-}'` now returns `2`, not empty, because `~/.bashrc` (mtime 2026-09-12
16:46) carries the remediation stanza this plan proposes to offer, already wrapped in the exact paired
fences E-03 prescribes. That matters three ways: V-01's stated evidence is unreproducible, so an
executor might "correct" a predicate that is right; E-04's environment-sensitivity warning was itself
written from the now-false reading; and E-03's no-duplicate detection must treat a stanza the tool did
not write as already-satisfied. The failing state still reproduces hermetically, which is now what the
plan requires.

THE ONE SUBSTANTIVE GAP WOULD HAVE SHIPPED A SELF-CONTRADICTING TREE. The plan names TWO strings to
amend for the consented write; there are NINE promise sites across `completion.py`, `cli.py` and
`README.md`. One is user-facing README prose, one is the PROMPT TEXT a user reads at the moment of
consent, and the README claim is pinned by this plan's own test file. `README.md` was not in
`Scope-Paths`, so amending it would have been an undeclared out-of-scope edit; it is now declared.

A SEPARATE CLASS OF DEFECT, WORTH NAMING BECAUSE IT IS MECHANICAL RATHER THAN ANALYTICAL: twelve
bullets across two sections were copied verbatim from the unrelated `wfartifacts` Set (run-scratch
relocation). All eight Step-0 "conventions" and all four "deferred" entries described gitignore
templates, `_ensure_aw_gitignore`, `install_into_repo`, D92 run-record tracking and a Set-wide
prohibition on deleting run records. None bears on shell completion, and one cited an "Order 05" that
does not exist in this single-child Set. A Step-0 section is exactly where an executor looks to learn
the local rules, so eight wrong rules is worse than none; both sections were replaced with conventions
and exclusions measured against this feature.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. correctness; E. testing; evidence accuracy | measured `bash -ic 'echo ${BASH_COMPLETION_VERSINFO-}'` -> `2`; `stat ~/.bashrc` -> mtime 2026-09-12 16:46; `~/.bashrc:20-33`; `env -i HOME=<empty> bash -ic` -> `[unset]` vs `-lic` -> `[2]` | **The plan's central measurement is stale because the reporting machine was fixed by hand after authoring, so the prescribed evidence cannot be reproduced.** The plan asserts `bash -ic` returns EMPTY on this box and V-01 requires pasting that. Re-measured, it returns `2`, because `~/.bashrc` now carries the remediation stanza this plan proposes to offer, wrapped in the exact paired fences E-03 specifies. An executor following V-01 literally would find its evidence criterion unmeetable and might "correct" a predicate that is behaving correctly, or fabricate the expected output. The failing state reproduces hermetically under `env -i` with an empty HOME. Three consequences: V-01's evidence, E-04's environment-sensitivity example (written from the now-false reading), and E-03's duplicate detection, which must treat a stanza the tool did NOT write as already-satisfied rather than appending a second | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-8 records the re-measurement with the mtime and the stanza location. E-01 gained a paragraph stating the authoring measurement is stale, forbidding a "fix" when the live box reports reachable, and giving the hermetic `env -i` pair as the durable demonstration. V-01 now forbids reporting `-ic` -> empty as fabricated and requires the hermetic pair plus the live reachable reading. E-03 gained the pre-existing-stanza rule. E-04's warning rewritten around the actual flip |
| PR-002 | HIGH | UNDER-SCOPE | B. contracts; G. executability; documentation sync | `grep -rn` over three files: `completion.py:31`, `:728`, `:865`, `:934`; `cli.py:5561`, `:5581`, `:5612`, `:10482`, `:10506`; `README.md:76`; `tests/test_completion.py:1098-1103` | **The consented write falsifies NINE promise sites and the plan names TWO, one of the missing ones being user-facing README prose that the plan's own test file pins.** F-5 said the restraint is "stated three times" and spec-sync named `install_shell_completion`'s docstring plus the success line. Enumerated at review there are nine, including `cli.py:5581` (the PROMPT TEXT a user reads at the moment of consent, "does NOT modify your ~/.bashrc..."), `completion.py:934` (uninstall, the asymmetry E-03 already flags), and `README.md:76` ("**never edits `~/.bashrc`...**"). `README.md` was NOT in `Scope-Paths`, so amending it would have been an undeclared out-of-scope edit caught only at finalize, and leaving it would ship a README denying shipped behavior | C:Low; U:Low; S:Low; F:Medium-High; Overall:Low | FIXED | `README.md` added to `Scope-Paths`. Spec-sync section replaced with a nine-row table of site, file:line and current claim, flagging site 9 as test-enforced, site 6 as prompt text read at consent time, and site 4 as tied to the uninstall resolution. Prescribes preserved-substance wording ("never writes a user rc/dotfile except the fenced stanza appended on explicit TTY consent") over striking the promise. F-5 severity raised MEDIUM to HIGH and rewritten with the enumeration. Scope check records why README is in scope |
| PR-003 | MEDIUM | IN-SCOPE | G. executability; evidence accuracy | the plan's own Step-0 and Deferred sections vs the `wfartifacts` Set; this Set has exactly one child | **Twelve bullets were copied from an unrelated Set, so the section an executor reads to learn the local rules describes a different feature entirely.** All eight Step-0 "conventions discovered" concern run-scratch relocation, `.aw/.gitignore` anchoring, `_ensure_aw_gitignore`, `install_into_repo` and D92 run-record tracking; none is about shell completion. All four Deferred entries likewise, and the last cites "Order 05 relocates and never deletes" in a Set whose only child is Order 01. The execution contract carried the same stray clause. Harmless-looking, but Step-0 is precisely where an executor calibrates, and a plan that appears to have surveyed the wrong subsystem also undermines trust in the findings that ARE right | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both sections rewritten with a note recording what was removed and why. Step-0 now carries six conventions measured at review: the nine promise sites, the sentinel-gated-file versus fenced-stanza policy split, the `--yes` early-return precedent with its stated reason, the deliberate prompt-polarity difference, the atomic-write shape with its authority limit, and the shared-checkout/bare-suite rule (the one original bullet that applied). Deferred now carries this plan's five real exclusions. The stray run-record clause in the gate replaced with the never-touch-the-real-bashrc rule |
| PR-004 | MEDIUM | IN-SCOPE | A. correctness; G. executability | `cli.py:5610-5613` (setup flow) and `cli.py:10501-10510` (verb, separate `term.line`); measured four `OK` lines from `--dry-run` | **The false message exists at TWO sites and the plan cites one, so a fix could leave the defect reachable by the other entry point.** F-2 and E-02 cite `cli.py:5610-5614` only. The `aw completion install` VERB path is a different block: it prints per-file `OK` lines, then an `OK` summary carrying "(no rc/dotfile modified)", then a SEPARATE `term.line` "Next  start a new {shell} shell (or run `exec {shell}`) to pick it up". Measured, the verb emits four green `OK` lines. Since the maintainer reproduced via the verb, fixing only the setup-flow string would leave the exact reported experience unchanged | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 now names both sites with corrected line ranges, states that the verb's next-step line is a separate `term.line` call, warns that fixing one leaves the defect reachable, and records the measured four-`OK` pre-change output. V-02 requires both sites covered separately |
| PR-005 | MEDIUM | IN-SCOPE | C. architecture; B. contracts | `grep -rn "bashrc" agent_workflows/*.py` (only promises); `install_wizard.py:886`, `:897`, `:909` | **E-03 points at an atomic-write precedent whose authority does not transfer, and the plan does not say that this is the codebase's first user-dotfile write.** E-03 says to use "the same shape `install_wizard._persist_policy` uses". The SHAPE is right (temp file plus `os.replace`), but every one of those three calls writes a framework-owned file under `.aw/`, never a user dotfile, and grep confirms no code anywhere writes an rc file today. An executor could read the citation as precedent for the ACT rather than the MECHANISM, when the only authority for the act is the maintainer's OQ-01 ruling | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-9 states there is no in-tree precedent, with the grep and the three call sites, and separates shape from authority. E-03 gained the same distinction in place ("the shape transfers and the authority does not"). Recorded in Step-0 conventions |
| PR-006 | MEDIUM | IN-SCOPE | A. correctness; E. testing | `~/.bashrc:20-33` (hand-added, tool-identical fences); `completion.py:756`, `:843`, `:886` (the opposite policy for FILES) | **A stanza matching E-03's own fences already exists on the target machine, and the plan has no rule for that case.** E-03 requires detecting "your own prior stanza" before writing. The stanza present was added by hand, not by the tool, so an authorship- or sentinel-keyed check would miss it and append a duplicate to the maintainer's live login-shell config. Note this is deliberately the OPPOSITE stance from the drop-in FILE policy, where a foreign file is REFUSED (`INSTALL_SENTINEL` gate): for a file, foreign means "not ours, do not touch"; for the stanza, foreign-but-equivalent means "the user already did the work" | C:Low; U:Medium; S:Low; F:Medium; Overall:Low | FIXED | E-03 now requires keying the no-duplicate check on the OPENING FENCE TEXT rather than on a sentinel or authorship, and states explicitly that this is the inverse of the file policy so nobody unifies them. V-03 requires demonstrating the already-present case against a COPY and forbids writing to the real `~/.bashrc`. Recorded in Step-0 |
| PR-007 | LOW | IN-SCOPE | E. testing | measured `time bash -ic ...` -> 0.227s real; `bash -lic` and `bash -ic` both `2` on the live box | E-01 requires the probe be "cheap and non-interactive" and treat timeout as UNKNOWN, but states no cost, so an executor has no basis for choosing a timeout and might pick one that flakes on a slow box or under load | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 records the measured 0.227s so a timeout can be chosen against a real figure rather than a guess |
| PR-008 | LOW | IN-SCOPE | E. testing | measured bare `python3 -m pytest` at HEAD `8e81ab9c`: `5971 passed, 3 skipped, 2 xfailed` | The plan requires a bare-suite run judged on the failure-SET delta (the right criterion) but records no pre-change reading, leaving nothing to notice a pre-existing failure against | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 carries the review-measured baseline labelled for reference with an instruction to re-measure rather than quote it |

No finding was deferred and none was left open, so no escalation to a blocking question was required and
the Fix Bar's deferral machinery does not engage. Every finding was overall Low remediation risk: each
was repairable by a bounded edit to the plan itself, using measurements taken during the review, with no
decision that belongs to the maintainer. PR-002 carries a Medium-High FUNCTIONALITY axis rating because
shipping the write while six or seven promise strings still deny it would be a material contract defect,
but the REMEDY (declare `README.md`, enumerate the nine sites) is local and verifiable, so overall
remediation risk stays Low and the Bar requires fixing it.

WHAT REVIEW DID NOT CHANGE, recorded because a reviewer that rewrites a sound design is doing harm: the
four-state message model, the decision to detect by asking bash rather than parsing rc files, the
paired-fence choice and its removability reasoning, the `[y/N]` polarity and its deliberate divergence
from the same-day yes-default prompts, the rule that `--yes` never consents, the uninstall-asymmetry
obligation, the atomic-write requirement, the refuse-to-create-an-absent-bashrc rule, and the injection
mandate for tests. All were verified against the tree and all are correct.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-002: amend the nine promise strings during review, or require the executor to? | REQUIRE IT, and give the executor the full enumeration as a table plus the `Scope-Paths` declaration it needs. | (a) Editing the nine strings myself, rejected because plan-review edits PLANNING documents only; changing `completion.py`, `cli.py` and `README.md` would be implementing the plan under review. (b) Naming only the two the plan already had and adding "and any others", rejected because an executor would have to re-derive the set and the README one is easy to miss precisely because it is not code. (c) Leaving `README.md` out of `Scope-Paths` and letting finalize's scope reconciliation catch it, rejected because that converts a knowable authoring gap into a late refusal, and the honest fix is to declare it up front. | the grep enumeration; `tests/test_completion.py:1098-1103` pinning README content; AGENTS.md scope-declaration rule | yes |
| D-2 | PR-001: the plan's stated measurement is now false. Correct the numbers, or flag the plan as needing re-authoring? | CORRECT IN PLACE and add the hermetic reproduction, keeping the original reading as recorded history. | (a) Marking the plan REPLAN, rejected as disproportionate: the thesis, the design and eight of nine findings are unaffected; only one measured reading and the evidence derived from it moved. (b) Silently updating the numbers to today's values, rejected because the ORIGINAL reading is the evidence that the defect was real, and deleting it would make the plan look like it was authored against a working machine. (c) Leaving it and trusting the executor to notice, rejected because V-01 states the stale value as a required paste, which invites fabrication. | both probes measured; `stat ~/.bashrc`; `~/.bashrc:20-33` | yes |
| D-3 | PR-003: delete the twelve copied bullets, or leave them as harmless noise? | DELETE, with a note recording what was removed and why, and replace with conventions measured at review. | (a) Leaving them, rejected because Step-0 is where an executor calibrates on local rules and eight wrong rules actively mislead; one also cites a nonexistent Order 05 in a single-child Set. (b) Deleting silently, rejected because a future reader comparing this plan to its siblings would see a missing section and wonder whether it was ever done. (c) Rewriting them as generic advice, rejected because a convention with no measurement behind it is the thing this repository's plans are supposed to stop producing. | the plan's own two sections; `- Order: 1` as the Set's only child | yes |
| D-4 | PR-006: should the stanza check refuse a foreign stanza (matching the drop-in FILE policy) or treat it as satisfied? | TREAT AS SATISFIED, and state in the plan that this is deliberately the inverse of the file policy. | (a) Refusing like the file path does (`INSTALL_SENTINEL` gate), rejected because the two cases differ in kind: a foreign completion FILE means another tool owns that name and we must not clobber it, whereas a foreign-but-equivalent rc STANZA means the user already performed the remediation, and refusing would report a problem where none exists. (b) Appending anyway when authorship cannot be proven, rejected outright: that duplicates a stanza in the user's live login-shell config, which is the concrete harm E-03 exists to avoid. | `~/.bashrc:20-33` (hand-added, tool-identical); `completion.py:756`, `:843`, `:886` | yes |
