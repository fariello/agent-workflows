# Review: untrack the four generated index manifests and reconcile stale-index semantics (child yvvf98, Set idxuntrack)

- Subject-Id: yvvf98
- Subject-Type: ipd
- Reviewed-At: 2026-09-06
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `cf496c51` (the plan cites `7f80180e`; every citation was re-verified at the current
HEAD and all of them still hold at the lines given). Structural preflight `aw ipd lint --phase author`
conformed BEFORE semantic review and `--phase review-finalize` conformed after the revisions. This is
the sibling of child `4r0qp1`, reviewed immediately before it in the same session, and it INHERITS one
finding from that review (PR-008 there, F-7 here).

THE PLAN'S PREMISE IS TRUE AND I VERIFIED IT END TO END, including the part that mattered most and was
easiest to take on faith. All four manifests are still tracked and none gitignored (`git ls-files` lists
them, `git check-ignore` exits 1 for all four). More importantly I REPRODUCED the motivating failure and
its fix rather than trusting the `ueg5cf` narrative: with a manifest TRACKED, two branches differing only
in that file produce `CONFLICT (content)` and the merge fails; with it gitignored and `git rm --cached`ed,
the identical merge succeeds ("Merge made by the 'ort' strategy", only the code file in the stat) and the
manifest survives on disk. So the change does what the item claims, and E-05 no longer asks an executor to
discover an outcome that is now measured.

WHAT ROUND 1 CHANGED, in order of how much it mattered:

FIRST, THE CHANGE WOULD NOT HAVE REACHED ANY OTHER REPO (F-7, inherited as PR-008 from child 01's
review). This repo's `.aw/.gitignore` is BYTE-IDENTICAL to `engine._AW_GITIGNORE_TEMPLATE`, which a fresh
`aw install` writes verbatim, and `_ensure_aw_gitignore` is the only path that back-fills an
already-installed repo. The plan edited the file and nothing else, so the toolkit would have shipped a fix
that did not apply to its own users, the next install would have re-diffed this repo against its own
template, and the `ueg5cf` failure class would have stayed live everywhere but here while the Set claimed
success. That is now E-06, and OQ-02 records why it lands here rather than as a follow-on.

SECOND, THE PLAN LEFT OQ-01 OPEN WHEN THE REPOSITORY HAD ALREADY DECIDED IT, and the framing hid the
mechanism (F-11). The plan asked whether a missing manifest should be "silent, informational, or a
warning" and told the executor to decide from the doctor's aggregation. But severity here is not a message
or a per-emitter concern: it is a `check_engine.RULE_REGISTRY` entry, and `stale-index` is UNREGISTERED, so
it currently receives `_DEFAULT_RULESPEC` severity `error` (verified live). `artifact_core.drift_exit_code`
fails the gate for anything that is not `info`. So `warning` for absence would STILL fail every fresh
clone, which is precisely the outcome the plan wanted to avoid. The question therefore had ONE correct
answer, not two acceptable ones, and there is a near-exact precedent with a recorded rationale:
`check.system-layout-missing`/`check.system-layout-drift`, created for the gitignored generated
`layout.json`. I resolved OQ-01 to `info` for missing and `warning` for stale and rewrote E-02 around the
registry rather than the message string.

THIRD, THREE CONSUMER AND SURFACE GAPS. A FOURTH document asserts the manifests are committed, and it is
the one that propagates: the shipped installer template `agents-docs-research-README.md:50` carries the
same sentence verbatim and is written into every managed repo, so correcting only the three in-repo
documents would have re-seeded the false claim on every install (F-8). `check_engine.check_content` calls
both emitters' `check_drift`, so the rule also flows through `aw check plans`/`aw check research`/`aw check
all`, a consumer class the plan never mentioned (F-9). And the scoped test file is the wrong one:
`tests/test_doctor.py` has ZERO `stale-index` references, while four modules that DO break were unscoped,
two of which assert `d.rule == "stale-index"` EXACTLY and would fail the instant E-02 renames the rule
(F-10). I also flagged that all five `doctor.py` sites match on the SUBSTRING `"stale-index"`, so E-03 now
has to choose ids deliberately or break five matches silently.

WHAT I LEFT ALONE, DELIBERATELY. The plan's E-01 same-commit requirement (gitignore edit plus four
`git rm --cached` in one commit) is correct and well-argued, and I did not touch it. Its anchored-pattern
warning, drawn from the `/inbox/` comment in the same file, is exactly the right lesson and I extended it
into E-06 rather than restating it. And I did NOT widen scope to register severities for the other
unregistered rules I noticed in passing (`name-metadata-mismatch`, `dangling-citation`, and most of both
emitters' vocabulary all fall through to the `error` default); that is a real observation but a separate
item, and I recorded it in Deferred rather than smuggling a registry audit into an untracking change.

TWO CONSEQUENCES I MEASURED AND THE PLAN DID NOT MENTION (F-12), now documented in E-04 instead of
engineered away: a NEW WORKTREE has no manifest at all until `aw index` runs there, and switching branches
no longer changes the manifest, since it becomes one local file shared across every branch. Neither is a
defect. The first matters operationally for THIS plan, because the plan tells the executor to validate in
an isolated worktree, where the manifest will legitimately be absent; I added a caution so an executor does
not read the expected `info` case as a failure.

ONE THING I COULD NOT SETTLE AND DID NOT PRETEND TO. E-03 must pick rule ids, and whether the existing
five `doctor.py` substring matches survive depends on that choice. I stated the constraint and the safer
option (ids that preserve the `stale-index` substring) and required verification, but I did not pick the
ids myself: naming a public-ish rule id is the kind of small decision better made with the implementation
in front of you, and either family works if E-03 checks. I also did not run the full suite; I ran the five
directly implicated modules (78 passed, recorded in the plan as the executor's reference baseline).

DISCLOSURE: the plan's `- Author:` names the same tool/model string I run as, so this may be a SELF-REVIEW
and is worth correspondingly less than an independent one. I have no access to the authoring session, so I
treated the plan as unfamiliar and re-derived every claim from code; F-7 through F-12, and the reproduced
merge experiment, are the evidence that this was more than a re-reading. An independent reviewer would
still be a better control, particularly on the OQ-01 severity ruling, which now hard-codes a behavior
choice into the plan on my authority plus one precedent.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | high | UNDER-SCOPE | C. Architecture; F. Principles (general-case) | `agent_workflows/engine.py:4274-4308,5323-5370` | The change would not reach any other repo. `.aw/.gitignore` is BYTE-IDENTICAL to `engine._AW_GITIGNORE_TEMPLATE` (a fresh install writes it verbatim) and `_ensure_aw_gitignore` is the only back-fill path for an installed repo. Editing the file alone leaves every managed repo tracking the manifests, re-diffs this repo on the next install, and leaves the `ueg5cf` failure class live everywhere but here. Inherited from child 01's review as PR-008. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | fixed | F-7 added; new E-06 extends BOTH the template and the back-fill list; V-06 requires a fresh-install AND a back-fill exercise plus a byte-comparison; OQ-02 records why it lands here. |
| PR-002 | high | UNDER-SCOPE | F. Honest documentation | `.aw/system/workflows/templates/agents-docs-research-README.md:50`; `engine.py:5134-5175` | A FOURTH document asserts the manifests are committed, and it propagates: the shipped installer template carries the sentence verbatim ("both are COMMITTED so a fresh clone and a weak agent have them without running the tool") and `ensure_docs_readmes` writes it into every managed repo. Fixing only the three in-repo docs re-seeds the false claim on every install. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | F-8 added; E-04 extended to four documents and notes the research README states the REASON for committing, so it needs rewriting rather than a caveat; `Scope-Paths` extended. |
| PR-003 | high | IN-SCOPE | A. Correctness; E. Testing | `check_engine.py:294-309`; `artifact_core.py:405-415`; live `rule_spec('stale-index')` | OQ-01 was left open on a question the repository had already decided, and its framing missed the deciding mechanism. Severity comes from `RULE_REGISTRY`, not a message; `stale-index` is UNREGISTERED so it gets `_DEFAULT_RULESPEC` `error`; and `drift_exit_code` fails on anything not `info`, so a `warning` for absence would still fail every fresh clone (the outcome the plan wanted to avoid). `check.system-layout-missing`/`-drift` is a near-exact precedent with a recorded rationale. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | OQ-01 RESOLVED at review (`info` for missing, `warning` for stale, both REGISTERED); F-11 added; E-02 rewritten around the registry mechanism and the precedent; V-02 now requires exit codes and `rule_spec` output. |
| PR-004 | medium | UNDER-SCOPE | A. Correctness; G. Executability | `check_engine.py:629,727` | A third consumer class was unscoped: `check_content` calls both emitters' `check_drift`, so the rule flows through `aw check plans`/`aw check research`/`aw check all`, not only `aw index --check` and `aw doctor`. A rename or severity change silently alters `aw check` behavior. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | F-9 added; new E-07 covers the `aw check` path and also pins the verified fact that the generator excludes the manifests BY NAME before the ignore filter, so gitignoring them cannot make it skip real inputs; V-07 requires both. |
| PR-005 | medium | IN-SCOPE | E. Testing | `tests/test_doctor.py`; `tests/test_plans_index.py:233-237`; `tests/test_research_index.py:203-207`; `tests/test_doctor_remediations.py:54-56,231-233`; `tests/test_ci_check_parity.py:92-115` | The scoped test file has ZERO `stale-index` references, and four modules that DO break were unscoped: two assert `d.rule == "stale-index"` EXACTLY, one constructs that literal, and one carries a clean-tree comment claiming the index "mirrors the committed state CI runs against", which becomes false. Validation could have passed while `aw index --check` was broken. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | F-10 added; new E-08 retargets the four real modules and drops `test_doctor.py` from scope; V-08 requires the passing run, the 78-test baseline, and a mutation check. |
| PR-006 | medium | IN-SCOPE | A. Correctness; D. Anti-regression | `agent_workflows/doctor.py:859,938,1049,1382,1460` | All five doctor sites match on the SUBSTRING `"stale-index"`, so E-02's rename either keeps working by accident or breaks all five silently, and the plan's "locate by SYMBOL" instruction does not surface the coupling. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | E-03 rewritten to state the substring coupling, prefer ids that preserve it, and require verification; V-03 requires a grep proving each of the five still matches or was updated. |
| PR-007 | low | UNDER-SCOPE | F. Honest documentation; UX | measured this review (`git worktree add`; branch switch) | Two user-visible consequences no document mentions: a NEW WORKTREE has no manifest until `aw index` runs there, and switching branches no longer changes the manifest (one local file shared across branches). The first also affects THIS plan's own validation instruction to use an isolated worktree, where an absent manifest is expected rather than a failure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | F-12 added; E-04 must document both; a caution added to `Required tests / validation` so the executor does not misread the expected `info` case in a fresh worktree. |
| PR-008 | low | IN-SCOPE | G. Executability | plan `## Approval and execution gate` | `Cohesion rationale: not required` while the plan now spans a repo file, an installer template, a rule registry, two consumer surfaces, four documents, and four test modules. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Size note (8 leaves / 2 groups) and a cohesion rationale added, explaining why E-01/E-06 are adjacent-but-separate and why E-02/E-03/E-07 are split by consumer surface. |
| PR-009 | low | OVER-SCOPE | C. Architecture | `check_engine.py:85-310` (registry) | Noted in passing: most of both emitters' rule vocabulary (`name-metadata-mismatch`, `dangling-citation`, and others) is also unregistered and falls through to the `error` default. Tempting to fix alongside E-02, but it is a different concern with a wider blast radius. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | deferred | Explicitly excluded in `Deferred / out of scope` so it is recorded rather than silently either done or forgotten. Only `stale-index` changes meaning in this plan. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should a MISSING manifest be silent, informational, or a warning? (the plan's OQ-01, left open for the executor) | `info` for MISSING and `warning` for PRESENT-BUT-STALE, both as REGISTERED rules. | `warning` for missing (rejected: `drift_exit_code` fails on anything not `info`, so it would still fail every fresh clone, the exact outcome the plan wanted to avoid); fully silent (rejected: the `layout.json` precedent keeps a detectable condition reportable, and silence removes the only signal a fresh clone gets); leaving it to the executor (rejected: it is a mechanism question with one correct answer, not a taste question). | `check_engine.py:294-309` (`check.system-layout-missing`/`-drift`, same problem for the gitignored generated `layout.json`, with its `warning`-not-`error` rationale recorded inline); `artifact_core.py:405-415`; live `rule_spec('stale-index')` -> `severity='error'` because it is unregistered. | yes |
| D-2 | Should the installer template + back-fill change (PR-001) land in this child, or as a follow-on item? | This child, as E-06. | A third child (rejected: the edit is two small additions to one file and shares E-01's exact four lines, and deferring leaves a window where the toolkit ships a fix that does not apply to its own users); leaving it to child 01 (rejected: child 01 deliberately touches no gitignore, which is why child 01's review deferred it HERE). | `engine._AW_GITIGNORE_TEMPLATE == Path('.aw/.gitignore').read_text()` is `True`, so the two must change together or the next install re-diffs this repo; `engine.py:5323-5370` is the only path reaching an installed repo. | yes |
| D-3 | Should this review pick the new rule ids for E-02, or state the constraint and let the executor choose? | State the constraint (all five `doctor.py` sites match the SUBSTRING `"stale-index"`), recommend ids that preserve it, and require verification. | Pick the ids here (rejected: a small naming decision better made with the implementation in view, and either family works provided E-03 verifies); say nothing about it (rejected: the substring coupling is invisible from the plan's "locate by SYMBOL" instruction and would break five matches silently). | `doctor.py:859,938,1049,1382,1460` all test `"stale-index" in rule` or the substring in a comment/predicate. | yes |
| D-4 | Should the broader registry gap (PR-009: most emitter rules are unregistered and default to `error`) be fixed alongside E-02? | No; record it in Deferred and change only `stale-index`. | Fix the whole vocabulary while in the file (rejected: it changes the severity of unrelated findings across `aw check`, which is a wider blast radius than an untracking change should carry, and would confound whether a regression came from the ignore or the registry). | `check_engine.py:312-315` documents the `error` default as deliberate ("fail toward visible"), so the other rules are not accidentally broken; only `stale-index` changes MEANING in this plan. | yes |
