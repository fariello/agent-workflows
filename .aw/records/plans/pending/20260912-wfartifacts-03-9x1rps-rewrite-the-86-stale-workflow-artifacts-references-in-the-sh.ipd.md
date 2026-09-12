# IPD: Rewrite the 86 stale workflow-artifacts references in the shipped workflow bodies

- Date: 2026-09-12
- Kind: child
- Concern: THE SHIPPED WORKFLOW BODIES SEND AGENTS TO THE RETIRED PATH 86 TIMES AND ASSERT IT IS SAFE. Measured at HEAD 2026-09-12: `grep -rhoP '(?<!\.aw/)workflow-artifacts' .aw/system/workflows --include='*.md' --include='*.py' | wc -l` -> 86 across 27 files, and `grep -rho '\.aw/workflow-artifacts' ... | wc -l` -> ZERO. Not one shipped body has been updated since Order 07.
  TWO OF THOSE LINES ARE ACTIVE FALSEHOODS, which is worse than a stale path because an agent acts on them. `assess/assess.md:139` says the run record "is gitignored by default, so do NOT commit or force-add it", and `:189` repeats that the directory "contains local-only working material". In a TARGET repo neither is true today: nothing ignores the repo-root directory, so an agent that trusts the sentence writes local context into tracked working material. The maintainer's report named these exact lines.
  THE HEAVIEST FILE IS NOT `assess.md`. `release-review/00-run-protocol.md` carries 18 references and `release-review/README.md` 11, so a mechanical sweep must cover the whole tree rather than the file that happened to be noticed.
  A NAIVE `sed` WILL CORRUPT THIS. Some references are already correct in spirit but differently shaped, some sit inside code fences and example paths, and `assess/tools/scan_secrets.py` uses the string in scanner logic rather than as instruction prose. A blind substitution also risks producing `.aw/.aw/workflow-artifacts/` on any line already carrying the prefix, which is why the count of already-correct references (zero today) must be re-measured before and after.
- Scope: Rewrite every stale `workflow-artifacts/` reference in the shipped workflow tree to `.aw/workflow-artifacts/`, and make the tracking claims TRUE rather than merely re-pointed. Covers all 27 files, prose and code fences and example paths, plus `assess/tools/scan_secrets.py`'s use of the string. EXCLUDES the installer (Order 01), the gitignore pattern (Order 02, which must land first so the "gitignored" claims are true when written), README content (Order 04), and any change to what the workflows DO beyond where they write.
- Scope-Paths: .aw/system/workflows/, tests/test_docs.py
- Item-Dependencies: none
- Status: to-review
- Priority: high
- Work-Kind: bug
- Blocks-Release: next
- From-Backlog: o9inwt
- Set: wfartifacts
- Order: 3
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 9x1rps

## Workflow history
- 2026-09-12 to-review (aw set): Authored as Order 07 delivery (Set wfartifacts) from backlog o9inwt: the spec's run-scratch relocation was implemented in this repo but never delivered to the shipped surface (86 stale references, installer still creating a repo-root dir with a 'DO NOT gitignore' README, 29 repos affected). Review-ready: no TODO placeholders, E/V bijection complete, every V-item demands pasted evidence.

- 2026-09-12 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make every shipped instruction name the one real run-scratch home, and make its tracking claims true.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure, rewrite, and re-measure

- [ ] E-01 RE-MEASURE THE REFERENCE COUNTS BEFORE EDITING ANYTHING, and record them, because they are the plan's only completion criterion.
  THE TWO COMMANDS, run from the repo root: `grep -rhoP '(?<!\.aw/)workflow-artifacts' .aw/system/workflows --include='*.md' --include='*.py' | wc -l` (expected 86) and `grep -rho '\.aw/workflow-artifacts' .aw/system/workflows --include='*.md' --include='*.py' | wc -l` (expected 0). If your numbers differ from these, say so with both sets and proceed on yours; the corpus may have moved.
  ALSO ENUMERATE THE FILES with per-file counts, so the rewrite can be checked file by file rather than only in aggregate. `release-review/00-run-protocol.md` (18) and `release-review/README.md` (11) are the heaviest and `assess/assess.md` (8) is the one reported.
  - Depends on: none
  - Expected outcome: recorded before-counts, both aggregate and per-file, with any divergence from the expected 86/0 stated.
  - Execution state: pending

- [ ] E-02 REWRITE THE REFERENCES, AND FIX THE FALSE TRACKING CLAIMS RATHER THAN JUST RE-POINTING THEM.
  DO NOT BLIND-`sed`. Guard against producing `.aw/.aw/workflow-artifacts/` on any line that already carries the prefix (zero today, but the rewrite itself creates them, so a second pass over an already-edited file is the hazard). Check every code fence and example path, not only prose sentences.
  `assess/tools/scan_secrets.py` IS CODE, NOT INSTRUCTION. Read what the string does there before changing it; if it is a scan-exclusion path, re-pointing it wrong either scans the new tree or stops excluding the old one.
  THE CLAIM AT `assess/assess.md:139` AND `:189` MUST BECOME TRUE, not merely re-pointed. After Order 02 the framework-owned `.aw/.gitignore` ignores `.aw/workflow-artifacts/`, so "it is gitignored by default" is then accurate; state WHICH file ignores it so a reader can verify rather than trust. If Order 02 has not landed, STOP: writing the claim first is what made this defect harmful.
  - Depends on: E-01
  - Expected outcome: all 86 references re-pointed, no doubled prefix anywhere, `scan_secrets.py` handled as code with its behavior stated, and the tracking claims true with the ignoring file named.
  - Execution state: pending

- [ ] E-03 RE-MEASURE AND PIN THE INVARIANT WITH A TEST, so the next body added does not reintroduce the retired path.
  THE AFTER-COUNTS MUST INVERT: the bare-reference count goes to 0 and the `.aw/`-prefixed count to at least the original 86. A residual bare reference is acceptable ONLY if it is a deliberate mention of the LEGACY path (for example in migration prose), and each such case must be named with its reason.
  ADD A GUARD TEST asserting no shipped body under `.aw/system/workflows/` contains a bare `workflow-artifacts` reference outside an explicitly allowed set, mirroring how `tests/test_docs.py` already walks the docs tree. Without it, this rewrite decays the way Order 07's did.
  - Depends on: E-02
  - Expected outcome: after-counts showing 0 bare and >=86 prefixed, every deliberate exception named, and a guard test that fails if a bare reference returns.
  - Execution state: pending

## Project conventions discovered (Step 0)

- ORDER 07 IS THE AUTHORITY AND IT IS ALREADY `implemented`: spec `20260817-2124-01-records-taxonomy-cleanup` (`u7xtni`), history line "run-artifacts -> `.aw/workflow-artifacts/`". This Set DELIVERS that decision; it does not revisit it.
- RUN SCRATCH IS UNTRACKED BECAUSE OF D92: run records carry local context, absolute home paths and session detail, so committing them publishes machine identity into permanent history. That is the reason, and it is why "just track it" is not an option.
- THIS REPO'S ROOT `.gitignore:62-68` ALREADY ENCODES THE TARGET STATE and is the best statement of intent in the tree, but it is NOT shipped: a target repo receives the framework-owned `.aw/.gitignore` instead. Never cite the root file as evidence that a target repo is protected.
- PATTERNS IN `.aw/.gitignore` ARE `.aw/`-RELATIVE AND MUST BE ANCHORED. The template's own `/inbox/` comment records the measured reason: a bare `inbox/` matched at any depth and silently swallowed the TRACKED `records/comms/shared/inbox/` lane, breaking `aw install`.
- `_ensure_aw_gitignore` IS THE ONLY PATH THAT REACHES AN ALREADY-INSTALLED REPO, because a repo that already has a `.aw/.gitignore` never re-reads the template. Every prior addition in that function carries a comment saying exactly this.
- `install_into_repo` IS THE SHARED CHOKEPOINT for every entry point (`aw install` via `engine.run()`, `aw setup` via `cli._run_setup` -> `cli._install_one`, and library callers). Wiring into `run()` reaches only one of them.
- `.aw/records/` IS TRACKED DURABLE RECORDS, NOT SCRATCH: `records/reviews/` alone holds 170 typed `.review.md` files. An agent already mistook it for the scratch home and moved run records into `.aw/records/reviews/untracked/`.
- Shared checkout, concurrent edits; the suite runs BARE (`python3 -m pytest`). Re-locate every symbol by NAME, not by the line numbers cited in these plans.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | 86 stale references, zero correct ones | `grep -rhoP '(?<!\.aw/)workflow-artifacts' .aw/system/workflows` -> 86 across 27 files; the `.aw/`-prefixed count is 0. | both greps, run at authoring |
| F-2 | HIGH | two claims are actively false, not merely stale | `assess.md:139` "it is gitignored by default, so do NOT commit or force-add it" and `:189` "contains local-only working material"; nothing ignores it in a target repo. | the file; the absent template pattern |
| F-3 | MEDIUM | the heaviest file is not the reported one | `release-review/00-run-protocol.md` has 18 references and `release-review/README.md` 11, against `assess/assess.md`'s 8. | per-file counts |
| F-4 | MEDIUM | one reference is CODE, not prose | `assess/tools/scan_secrets.py` uses the string in scanner logic; re-pointing it blindly changes what gets scanned or excluded. | the file |
| F-5 | MEDIUM | a blind sweep creates doubled prefixes | any line already carrying `.aw/` becomes `.aw/.aw/workflow-artifacts/`; the rewrite itself creates such lines, so a second pass is the hazard. | mechanical property of the edit |
| F-6 | LOW | nothing guards against regression | no test asserts the shipped tree is free of the retired path, which is how Order 07's rewrite decayed unnoticed. | absence of such a test |

## Proposed changes (ordered, validatable)

1. Re-measure and record before-counts, aggregate and per-file (E-01).
2. Rewrite all references, handle `scan_secrets.py` as code, and make the tracking claims true by naming the ignoring file (E-02).
3. Re-measure, name any deliberate legacy mentions, and add a guard test proven to fail on a reintroduced reference (E-03).

## Deferred / out of scope (with reason)

- WHERE RUN SCRATCH BELONGS. Settled by Order 07 and out of scope here; this Set delivers that ruling rather than re-opening it.
- `tools/untrack-workflow-artifacts.py`'s IN-PLACE BEHAVIOR. It untracks the repo-root path without moving anything and is not wired into install. It stays available for a user who wants only to untrack; changing it is a separate concern.
- THE PRESET/PLACEMENT DIVERGENCE recorded in backlog `2812t3` (presets still emit `state_durable: target-tracked` for a gitignored tree). Adjacent, separately carried, and not touched here.
- ANY DELETION OF A USER'S COMMITTED RUN RECORDS. Explicitly forbidden Set-wide; Order 05 relocates and never deletes.

## Scope check

- Over-scope: none.
- Under-scope, stated rather than left as `none`: this plan changes only WHERE the bodies point and whether their tracking claims are true. It does not change what any workflow DOES, does not touch the installer (Order 01), the gitignore (Order 02), the READMEs (Order 04), or any existing file's location (Order 05).

## Required tests / validation

- BOTH GREP COUNTS AFTER the rewrite: bare count 0, `.aw/`-prefixed count >= 86.
- `grep -rn '\.aw/\.aw/' .aw/system/workflows` returns NOTHING.
- The rewritten `assess.md` gitignore claims NAME the enforcing file, so a reader can verify rather than trust.
- The guard test passes, AND fails against a deliberately reintroduced bare reference (a guard that cannot fail proves nothing).
- `python3 -m pytest` BARE, failure-SET delta empty.

## Spec / documentation sync

No spec change: the bodies are being brought into line with a spec that already says this.

THE BODIES THEMSELVES ARE THE DOCUMENTATION being synced here, which is why this is its own child: 27 files is too large a surface to fold into a code change, and a reviewer needs to see the prose diff separately from the installer diff.

## Open questions

### OQ-01: Must Order 02 land before this plan executes?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: YES, AND E-02 STATES IT AS A STOP CONDITION. Resolved from the defect's own shape rather than asked: this plan WRITES the sentence "the run record is gitignored by default", and that sentence is only true once the framework-owned gitignore carries the pattern. Writing a true-sounding claim that is false is precisely the harm being repaired (`assess.md:139` has said it since Order 07 while nothing enforced it), so landing this first would reproduce the defect in a new location. The Set's `Item-Dependencies` are `none` because the runner re-checks dependencies at dispatch on ORDER, and the orchestrator's sequencing rationale plus E-02's stop condition carry the constraint. NOT BLOCKING: the constraint is recorded in the executable item itself.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste both grep commands verbatim with their numeric output, plus the per-file enumeration. State explicitly whether the counts matched the expected 86 and 0.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `grep -rn '\.aw/\.aw/' .aw/system/workflows` returning NOTHING (the doubled-prefix guard). Quote the rewritten `assess/assess.md` lines that make the gitignore claim and show they NAME the ignoring file. Paste the `scan_secrets.py` diff with one sentence on what the string does there. Quote at least one rewritten code-fence example, since fences are the shape a prose-only sweep misses.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste both grep counts AFTER the rewrite, showing 0 bare and >=86 prefixed. Name every deliberate remaining bare reference with its reason, or state that there are none. Paste the guard test's passing output, and paste it FAILING against a deliberately reintroduced bare reference, since a guard that cannot fail proves nothing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since `pre-commit`'s stash/restore can leave a co-worker's paths in the index in this shared checkout. Paste ACTUAL command output for every validation item; never claim a result you did not run. Re-locate every symbol by NAME rather than by the line numbers cited here, which are accurate at authoring time only. Run the suite BARE (`python3 -m pytest`) and judge on the FAILURE-SET delta, not counts. Run `aw sanitize --agent` before treating any output as shareable.

DO NOT DELETE A USER'S COMMITTED RUN RECORDS, anywhere in this Set. Relocation preserves history; deletion is unrecoverable and is the one outcome worse than leaving the retired directory in place.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence.
