# IPD: Release consent decision tree (close-out / release-candidate / full release) + rc convention

- Date: 2026-07-12
- Concern: informed consent at the release moment / release-artifact hygiene. Root cause (identified
  by the maintainer): the current release-review approval is a BINARY, BUNDLED "GO" - approving the
  Section 8 review silently also authorizes tag + push (+ implies release-shaped artifacts). A user
  context-switching between projects reads "GO" as "I approve what I just reviewed" (the findings),
  while the system reads it as "execute the release." That divergence is a classic MODE ERROR: a
  UX/consent-design defect, not user error. It is felt most acutely across the maintainer's OTHER
  repos, but this repo GOVERNS agent behavior in those repos, so the fix belongs here and propagates
  on install. Symptom: clean semver tags (`vX.Y.Z`) getting created on commits never intended for
  PyPI, blurring "versioned" and "released".
- Scope: `.agents/workflows/release-review/08-final-ship-review.md` (replace the binary GO handoff
  with a 3-rung consent decision tree) and `09-release-execution.md` (split the terminal
  externally-visible actions - tag / GitHub Release / PyPI - into individually named, separately
  confirmed, default-NO steps; add the rc-vs-final tag rule); `.agents/workflows/release-notes/`
  (teach the `-rc.N` pre-release convention when recommending the next version); the execution-contract
  block from IPD `20260712-1206-01` (add "never create/push a tag, GitHub Release, or PyPI upload
  except inside gated release-review Section 9"); a new single-source `RELEASING.md`; templates
  (`templates/final-response.md` terminal block); docs + DECISIONS. Regenerate shims if any manifest
  row changes (none expected).
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): raised after the maintainer reflected
  that saying "Go" had, across projects, conflated "approve the review" with "cut a release", and that
  the missing safe middle option is a release CANDIDATE. Reframed from a pure versioning-convention fix
  to a consent-design fix at the decision point. Complete proposal; born to-review.
- 2026-07-12 OQs resolved + hardened for path-only handoff (its_direct/pt3-claude-opus-4.8-1m-us):
  maintainer resolved OQ1-5 interactively (all recommended leans): `-rc.N` per target with a required
  resolver PEP 440 test; rc push separate/default-NO; GitHub Release default `--draft`; rungs sit
  UNDER GO/CONDITIONAL GO/NO-GO (D53 preserved); `RELEASING.md` at repo root. Wrote a scope-fenced
  execution contract into the gate. Executable from its path once approved. Stays to-review (needs
  human approval before execution).

## Project conventions discovered (Step 0, VERIFIED against source)

- Tagging is ALREADY human-gated in code and workflows (audit 2026-07-12): no Python auto-creates a
  tag (`versioning.py` only READS `git describe`); `run_checks.py:85,88` DENIES `git push`/`twine
  upload`; the only tag-CREATION instruction in the repo is `09-release-execution.md:93`
  (`git tag -a <vX.Y.Z> ...`), reached only after a Section 8 GO + explicit approval. So the leak is
  NOT "our tooling auto-tags"; it is that (a) the single GO bundles review-approval with
  tag/push, and (b) there is no first-class "candidate, not released" outcome or standing rule against
  ad-hoc tagging outside Section 9.
- Section 8 terminus (D53): `08-final-ship-review.md:170` mandates a terminal `RELEASE REVIEW DECISION`
  block ending "AWAITING YOUR GO/NO-GO ... NOTHING IS PUSHED UNTIL YOU DO" as the literal last output;
  `:157` gates the handoff to Section 9 on GO/CONDITIONAL GO + explicit approval; `:139` already
  downgrades to CONDITIONAL GO when pending plans exist. The recommendation vocabulary today is
  GO / CONDITIONAL GO / NO-GO - a BINARY ship/don't-ship, with no "candidate" tier.
- Section 9 bundles the terminal actions: push (`09:51`), tag (`09:90-94`, MUST be annotated `09:35`),
  publish/deploy (`09:96-101`, credential-gated + hand-off). They are sequential steps under ONE prior
  GO, not individually re-confirmed.
- release-notes already RECOMMENDS the next semver and explicitly never tags/pushes/publishes
  (`release-notes.md:9,13-16,31-32,48`); it is the natural home to teach `-rc.N`.
- versioning resolver already emits PEP 440 pre-release/dev forms; `parse_describe` maps a clean tag to
  itself and an ahead/dirty tree to `X.Y.(patch+1).devN+g<sha>` (`versioning.py:79-119`). A
  `vX.Y.Z-rc.N` annotated tag is a standard SemVer pre-release and PEP 440-compatible
  (`X.Y.ZrcN`), so pip/PyPI treat it as a pre-release (not installed without `--pre`) and it sorts
  BEFORE the final `vX.Y.Z`. No resolver change is required for reading it; confirm `parse_describe`
  handles the `-rc.N` describe form (add a test if it does not already).
- Enforcement posture: advisory-first (D52) for the prose rules; the CONSENT gate is a hard
  interactive gate (P10, D53 preserved - nothing pushed without explicit approval).
- House rule: no em dashes in authored Markdown.

## Design principle (the resolution of "do not over-gate")

Gate by CONSEQUENCE and REVERSIBILITY, not by step. Do NOT add many prompts (that breeds
consent-fatigue and click-through). Instead: ONE terminal interaction whose WEIGHT matches the action,
presenting a short decision tree that NAMES each consequence and DEFAULTS to the least-irreversible
option. Each externally-visible, hard-to-reverse sub-action (tag / GitHub Release / PyPI) is named and
individually confirmed, default-NO. This directly applies this repo's own imported ui-ux principles
(safe defaults; do not require selecting the only option; never auto-commit a consequential final
action; clear states) and P2 (honest over aspirational: a candidate is labeled a candidate).

## Proposed changes (ordered, validatable)

1. **Replace the binary GO with a 3-rung release consent decision tree** in
   `08-final-ship-review.md` (and the terminal block in `templates/final-response.md`). After the
   review verdict, the terminal block presents EXACTLY these rungs, safe option pre-selected/default,
   each one line stating its consequence:
   - **(A) Close out the review only [DEFAULT].** Approve the findings and disposition. NOTHING is
     tagged, pushed, released, or published. Fully reversible. The review is "accepted"; no artifact.
   - **(B) Cut a RELEASE CANDIDATE.** Create an annotated `vX.Y.Z-rc.N` pre-release tag ONLY (optional
     push of that rc tag, separately confirmed). This says "this is the intended version, NOT live."
     Does NOT create a GitHub Release and does NOT publish to PyPI.
   - **(C) FULL RELEASE.** Proceed to Section 9, where each externally-visible action is named and
     separately confirmed (below). Only a bare final `vX.Y.Z` (no `-rc`) is used here.
   The block keeps D53's mandated "NOTHING IS PUSHED UNTIL YOU DO" line and remains the literal last
   output. The primary fork the user sees is candidate-vs-full, so the two cannot be conflated at the
   moment of consent.
2. **Section 9: split terminal actions into individually named, default-NO confirmations.** Rework
   `09-release-execution.md` so that, having entered via rung (B) or (C), each of these is a DISTINCT
   confirmation naming its exact consequence, defaulting to NO, never bundled:
   - **Tag:** "Create annotated tag `<vX.Y.Z | vX.Y.Z-rc.N>`?" (rc for rung B; bare for rung C).
   - **Push tag/commit:** "Push `<ref>` to `<remote>`?" (existing multi-remote STOP rule preserved,
     09:53-56).
   - **GitHub Release:** "Create a GitHub Release for `<tag>`? (default: DRAFT, you publish it)" - new;
     `gh release create ... --draft` by default, NEVER auto-published (OQ3 RESOLVED). The human
     publishes the draft as a separate deliberate act.
   - **PyPI:** "Publish to PyPI via twine? (requires authorized credentials)" - unchanged credential
     gate + hand-off (09:96-101), default NO.
   Rung B (rc) does NOT push implicitly (OQ2 RESOLVED): pushing the rc tag is its own default-NO
   confirmation.
   Add the rule: a bare `vX.Y.Z` tag means "intended for PyPI"; anything not PyPI-bound MUST be
   `-rc.N` (or left untagged, riding the resolver's `.devN`). Keep annotated-only (09:35). The rungs
   SIT UNDER the GO/CONDITIONAL GO/NO-GO recommendation (OQ4 RESOLVED): the recommendation vocabulary
   is unchanged; on NO-GO no rungs are offered; on approval the human picks A/B/C.
3. **release-notes: teach the `-rc.N` convention.** Where release-notes recommends the next version
   (`release-notes.md:27-32`), add: if the release is not yet intended for PyPI/prod, recommend a
   `vX.Y.Z-rc.N` pre-release, explaining it sorts before the final tag and is not installed by default.
   Still never tags/pushes (48). Keep human-confirm (31-32).
4. **Execution-contract block (coordinate with IPD 1206-01).** Add ONE standing MUST to the managed
   `agents_pointer_block()` (via 1206-01, under its brevity budget): "Never create or push a git tag, a
   GitHub Release, or a PyPI/registry upload except inside release-review Section 9 after an explicit
   human GO. No ad-hoc `git tag`, no `git push --follow-tags` of release tags." This is the piece that
   reaches downstream repos and closes the actual leak. If 1206-01 lands first, this IPD adds the line;
   if this lands first, 1206-01 integrates it - single definition, shared brevity budget with
   0014-04/0030-01.
5. **New `RELEASING.md` (single source of truth).** A short repo-root doc: the three consent rungs, the
   `-rc.N` vs bare-`vX.Y.Z` meaning, annotated+signed tags, tag-on-clean-CI-green-tree, `gh release
   --draft`, and that PyPI is a separate credentialed step. Workflows POINT at it (P3/P8) rather than
   restating; `CONTRIBUTING.md:88,113` cross-links to it.
6. **Docs + DECISIONS + validation.** DECISIONS entry (Dnn, next is D69) recording the mode-error
   diagnosis, the 3-rung consent model, the `-rc.N` convention, the anti-ad-hoc-tag standing rule, and
   `gh release --draft` default; note it REFINES D53 (adds the candidate tier + per-action gating;
   preserves the never-push-without-GO gate). Prose workflows have no unit test (repo policy), but:
   confirm `parse_describe` reads a `vX.Y.Z-rc.N` tag correctly (add a `test_versioning` case if
   missing); run the full suite; `aw plan-names`/shims stay green.

## Deferred / out of scope

- Retroactive tag surgery: do NOT remove or rewrite the existing `v1.1.0` tag. Per D51 it correctly
  labels the tree, and a git tag is not a release. This IPD is forward-looking convention only.
- A machine gate that blocks ad-hoc `git tag` (not reliably detectable; the standing prose rule +
  release-review own it). `run_checks.py` already denies `git push`/`twine`.
- Signed-tag key management / GPG setup (project-specific; RELEASING.md notes "signed if the project
  signs tags", unchanged from 09:35).
- Automated PyPI upload / CI publishing pipelines (remains a separate, credentialed, user-gated step).

## Open questions (ALL RESOLVED with maintainer 2026-07-12; execute exactly as stated)

1. rc numbering: RESOLVED - `-rc.N` per TARGET version (`v1.2.0-rc.1` -> `-rc.2` -> final `v1.2.0`),
   counter reset when `X.Y.Z` changes. The executor MUST add a `test_versioning` case proving
   `parse_describe` reads a `vX.Y.Z-rc.N` describe form into a VALID PEP 440 version (`X.Y.ZrcN`, e.g.
   `1.2.0rc1`); if the resolver does not already do so, make the minimal fix to `parse_describe` and
   test it. A candidate MUST be recognizable by pip as a pre-release (not installed on a plain
   `pip install`).
2. rc push default: RESOLVED - cutting an rc (rung B) does NOT push it. Pushing the rc tag is a
   SEPARATE, default-NO confirmation. Never push implicitly, even for a candidate (P10).
3. GitHub Release default: RESOLVED - default `--draft`; the human publishes it as a separate,
   deliberate act. Never auto-publish a GitHub Release.
4. Tree vs. recommendation vocabulary: RESOLVED - the rungs SIT UNDER the recommendation. Keep
   GO / CONDITIONAL GO / NO-GO unchanged (D53 preserved). On NO-GO, offer NO rungs. On GO/CONDITIONAL
   GO + explicit approval, the human then picks rung A/B/C. Rung A (close out only) MUST remain
   available even on a GO (approving the review's quality does not obligate cutting an artifact).
5. `RELEASING.md` location: RESOLVED - repo ROOT, cross-linked from `CONTRIBUTING.md` (beside the
   existing tag/PyPI notes at `CONTRIBUTING.md:88,113`).

## Dependencies / sequencing

- COORDINATE with IPD `20260712-1206-01` (execution-contract block): change #4 adds one line to the
  same managed block that 1206-01/0014-04/0030-01 edit under the ~6-8 line brevity budget. Whichever
  lands last integrates the line. No hard ordering otherwise; the release-review/notes/RELEASING.md
  changes are independent of the block edit.
- REFINES D53 (does not reverse it): the human GO gate is preserved; this adds the candidate tier and
  per-action consent.

## Approval and execution gate

`to-review`. All OQs are RESOLVED above, so this IPD is executable from its path once approved.
Execution contract (follow EXACTLY):

1. SCOPE FENCE. Implement ONLY changes 1-6. Touch ONLY: `08-final-ship-review.md`,
   `09-release-execution.md`, `templates/final-response.md` under `.agents/workflows/release-review/`;
   `.agents/workflows/release-notes/release-notes.md`; the managed block via coordination with
   1206-01 (change #4 - one line only; do NOT independently rewrite `agents_pointer_block()` text if
   1206-01 has not landed, leave a clearly-marked integration note instead); a NEW root
   `RELEASING.md`; `CONTRIBUTING.md` (cross-link only); `DECISIONS.md` (append D69); and, IF the
   resolver needs it for OQ1, `agent_workflows/versioning.py` + `tests/test_versioning.py`. Do NOT
   refactor, rename, or "improve" anything the plan did not ask for; if a change seems to need more,
   STOP and leave a note rather than expanding scope.
2. rc convention (OQ1): add/verify a `test_versioning` case that `parse_describe` reads a
   `vX.Y.Z-rc.N` tag into valid PEP 440 (`X.Y.ZrcN`); make the minimal resolver fix only if the test
   fails.
3. Authoring style: NO em dashes or en dashes in any Markdown you write (use a hyphen or reword).
4. VALIDATE: run the FULL test suite. When you report validation passed you MUST paste the ACTUAL
   test-runner output (real command + real summary line). Never report success you did not run.
   Confirm `aw plan-names` and shims stay clean.
5. COMMIT only the files THIS IPD touches, PATH-SCOPED, message BEFORE the `--`:
   `git commit -m "msg" -- <path> ...`. NEVER `git add -A`, a bare `git commit`, or `git commit -a`.
   NEVER push. NEVER create or push a git tag / GitHub Release / PyPI upload as part of executing this
   IPD (this IPD DEFINES that gate; it does not exercise it).
6. When implemented, verified, and tests ACTUALLY pass, `git mv` this file to
   `.agents/plans/executed/`, set `Status:` to `executed`, append a `## Workflow history` line, and
   commit that move path-scoped.

HARD MUST (do not skip): report only what you actually ran and paste the real test output; stay inside
the scope fence; do NOT retag/remove the existing `v1.1.0` tag; never push. Not auto-executed;
requires human approval to begin.
