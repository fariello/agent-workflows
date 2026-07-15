# IPD: Correct documentation/instruction inconsistencies found in the repo-wide .md audit

- Date: 2026-07-15
- Concern: correctness / honest-documentation (GUIDING_PRINCIPLES) across the normative instruction
  surface. A repo-wide audit of instruction/skill/workflow/governance `.md` files (4 parallel read-only
  lanes) found a set of real inconsistencies: contradictory release facts, a stale version stamp, a
  drifted shipped tool constant, duplicate DECISIONS numbers that make live cross-references ambiguous,
  and several smaller drift/label/reference nits. These ship wrong or contradictory instructions to
  readers and (in two cases) to downstream repos, so they need correcting.
- Scope: LIVE, editable governance/instruction/doc files only. Explicitly EXCLUDES frozen/verbatim
  surfaces (`workflow-artifacts/**`, `.agents/docs/research/**` external artifacts, `.agents/plans/executed|superseded|not-executed/**`),
  and does NOT rewrite append-only DECISIONS history in place (the duplicate-D fix is an ADDITIVE erratum
  entry plus fixing the live references). One shipped Python tool constant is corrected. No product code
  logic beyond that constant; the shim generator is untouched.
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-15 to-review (its_direct/pt3-claude-opus-4.8-1m-us): created from a maintainer-requested
  repo-wide `.md` consistency audit. Findings gathered by 4 parallel `explore` lanes (root governance;
  workflows+manifest+templates; mirrors+skills+READMEs; engine-baked strings) and the two highest-severity
  items (F1 RELEASING first-release, F4 duplicate D-numbers) were re-verified by direct inspection before
  filing. Confirmed-clean areas (mirror parity, byte-identical baked AGENT-WORKFLOWS block and
  plans/docs templates, no authored em/en dashes, no stale tmp/agent-comms refs, roadmaps-not-in-DOCS_SUBDIRS
  is by-design per D73) are recorded so they are not re-litigated. Complete proposal; born to-review.

## Findings to correct (VERIFIED against source)

Severity in brackets. Each line cites evidence and the minimal fix.

- F1 [BLOCKER] `RELEASING.md:57` states "The first PyPI release is `1.1.0` (DECISIONS D51); `1.0.0` was
  git-tag only." This contradicts the canonical story: `CHANGELOG.md` "1.2.0 - first PyPI publish" and
  DECISIONS D74 (first PyPI publish is v1.2.0; D74 revised D51's 1.1.0 plan). RELEASING.md is declared the
  single source of truth for release conventions, so the wrong first-release number is a blocker. FIX:
  reword to "first PyPI release is `1.2.0` (DECISIONS D74; D51 originally planned `1.1.0`, revised by
  D74); `1.0.0` and `1.1.0` were git-tag only." Do NOT edit D51 (history).
- F2 [HIGH] `.agents/workflows/index.md:3-4` stamp `WORKFLOWS-VERSION: 1.1.0` / "Version: `1.1.0`"
  contradicts `.agents/workflows/VERSION` = `1.2.1`, which the same line names as its source of truth.
  `list-workflows`/`getting-started` report this stamp, so agents report a two-releases-stale version.
  FIX: set both lines to `1.2.1`. (Also recommend the re-bake step stamp this from VERSION to prevent
  recurrence; capture as a follow-up note, not necessarily code here.)
- F3 [HIGH] `.agents/workflows/setup-repo/tools/normalize_plan_names.py:72-75` `DOCS_SUBDIRS =
  ("research","walkthroughs")` is drifted from `agent_workflows/engine.py:2285-2290`
  (`research,walkthroughs,specs,prompts`) and from DECISIONS D73. `aw plan-names` run from the installed
  workflow tree will not recognize `.agents/docs/specs/` and `.agents/docs/prompts/`. FIX: add `specs`
  and `prompts`; correct the pre-D73 docstring (line ~29) that says it scans `.agents/prompts/`. Confirm
  whether this file is maintained or mirror-generated; if mirrored, fix the source.
- F4 [HIGH] Duplicate DECISIONS numbers: `DECISIONS.md:456/481/508` are D22/D23/D24, and
  `:534/557/589` REPEAT D22/D23/D24 for different decisions. Five live `ARCHITECTURE.md` cross-refs
  (`:165,:175,:247,:259,:406`) become ambiguous. FIX (append-only-safe): add a dated ERRATUM entry at the
  end of DECISIONS.md recording the collision and assigning disambiguating IDs to the second occurrences
  (e.g. D22b/D23b/D24b, or next-free numbers with an "originally mislabeled" note), then update the five
  ARCHITECTURE.md references to the disambiguated IDs. Do NOT rewrite the historical headings in place.
- F5 [MEDIUM] `CONTRIBUTING.md:91-94` describes tag-then-rebake ("create a tag ... then regenerate
  VERSION"), contradicting the bake-then-tag order mandated by DECISIONS D75 and `RELEASING.md:42-48`.
  FIX: rewrite to `make version-file VERSION=<X.Y.Z>` -> commit -> `git tag -a vX.Y.Z`, and refresh the
  stale `1.0.0` example.
- F6 [MEDIUM] Status lifecycle enum: `auto-approved` (D65, actively set by verify-execution) appears in
  `.agents/workflows/assess/templates/ipd.md:19-21` but is ABSENT from both `.agents/plans/README.md` and
  `.agents/workflows/templates/plans-README.md` (which are byte-identical and claim to be the canonical
  enum). FIX: add the `auto-approved` sibling-of-`approved` line (with the D65 caveat: set only by an
  automated checker, not human approval) to BOTH READMEs, keeping them byte-identical.
- F7 [MEDIUM] `CONDITIONAL-GO` (hyphen) at `.agents/workflows/verify/verify.md:93` and
  `release-review/08-final-ship-review.md:53` vs the ~30 canonical space-form `CONDITIONAL GO`. FIX:
  normalize both to the space form. NOTE: this exact item is also in scope of pending IPD
  `20260715-1451-01-unify-readiness-verdict-vocabulary`. To avoid double-ownership, this IPD DEFERS F7 to
  that IPD (cross-reference only); if that IPD is retired/deferred, fold F7 back here.
- F8 [LOW] `.agents/workflows/plan-review-long/report-template.md:15` uses `NOT ELIGIBLE:` while the same
  file (`:51`), `01-discover-and-snapshot.md:12`, and the parity twin `plan-review/plan-review.md:387,418`
  use `NOT REVIEWED:`. FIX: change `:15` to `NOT REVIEWED:`.
- F9 [LOW] `.agents/docs/research/README.md:13-16` calls the docs-convention IPD `pending` and says
  "reconcile ... when it executes"; it now lives in `.agents/plans/executed/20260712-0033-01-...`. FIX:
  past-tense the note and point at the executed path. (This README is authored, not a verbatim external
  artifact, so editing it is in-bounds even though it sits under `.agents/docs/research/`.)
- F10 [LOW] `.agents/docs/README.md:11` advertises `roadmaps/` as a standard bucket, and
  `.agents/docs/roadmaps/` exists with content, but it has no `README.md` while the other four buckets do.
  FIX: add a short `.agents/docs/roadmaps/README.md` matching the sibling pattern. (Do NOT add roadmaps to
  engine `DOCS_SUBDIRS`; that omission is intentional per D73/DECISIONS.md:2036.)
- F11 [LOW] `.agents/workflows/index.md:203,209` reference the deprecated `install-workflows.py` and place
  symbols (`is_concern_catalog_row`,`CATALOG_ROW_PREFIXES`,`DOCS_SUBDIRS`) there, though they now live in
  `agent_workflows/engine.py` and the entry point is `aw install`. FIX: reword to name the `aw` CLI /
  `engine.py` (or "the installer" generically).
- F12 [LOW] `README.md:228-235,71-72` and `ARCHITECTURE.md:374-379` frame versioning examples as `1.0.x`,
  reading as if the project is at 1.0. FIX: refresh the illustrative baseline to a current number or
  explicitly label "example only". (Low: illustrative, not a hard fact.)
- F13 [LOW] `CONTRIBUTING.md:79` says "no em dashes" while the canonical AGENTS `AGENT-WORKFLOWS` block
  (and engine.py:580) says "no em or en dashes". FIX: align CONTRIBUTING to "em or en dashes". (Neither
  file currently contains dashes; wording-consistency only.)

## Confirmed clean (recorded so they are not re-litigated)

- Mirror parity: `.opencode/commands/` and `.claude/commands/` are the same 18-command set; every shim
  `description:` matches the manifest verbatim; every body pointer resolves; no orphan/missing shim.
- Engine-baked `AGENT-WORKFLOWS` block is byte-identical to `AGENTS.md`; the installed `plans-README` and
  `agents-docs-README` templates are byte-identical to this repo's copies; baked paths are all current;
  no hardcoded version; no em/en dashes in any baked Markdown.
- No em/en dashes in any AUTHORED governance/workflow/README doc (dashes exist only in explicitly-exempt
  `docs/prompts/` and `docs/research/` verbatim artifacts).
- No stale `tmp/agent-comms` / root `prompts/` / root `docs/` references in live docs.
- Manifest covers all 17 workflow dirs; all lens/persona/body paths resolve; plan-review vs
  plan-review-long verdict/memory-kernel parity holds. No project skills exist (nothing to validate).
- `roadmaps` absent from engine `DOCS_SUBDIRS` is BY DESIGN (D73 / DECISIONS.md:2036), not a defect.

## Deferred / out of scope

- F7 (`CONDITIONAL-GO` spelling) is owned by pending IPD `20260715-1451-01`; not fixed here.
- Any rewrite of append-only DECISIONS history in place; any edit to `workflow-artifacts/**` or executed/
  superseded/not-executed plans; any change to the shim generator logic; any change to product runtime
  behavior beyond the `normalize_plan_names.py` constant (F3).
- Automating the index.md version-stamp re-bake (F2 recurrence prevention) is noted as a FOLLOW-UP, not
  built here, to keep this IPD a pure consistency-correction pass.

## Open questions (v1 leans for review)

1. F4 disambiguation style: `D22b/D23b/D24b` suffixes vs assigning the next free numbers (D79+) to the
   second occurrences? (Lean: suffix form `D22b` etc. via an erratum entry, because the SECOND occurrences
   are the newer ones and downstream text already cites both numbers; a suffix preserves intent with
   least churn. Confirm.)
2. F3: is `normalize_plan_names.py` hand-maintained or generated from engine.py? (Lean: appears
   hand-maintained; fix in place AND add a test/guard so its `DOCS_SUBDIRS` cannot silently drift from
   engine's again. Confirm during execution.)
3. F12: refresh version examples to `1.2.1` vs annotate as illustrative? (Lean: annotate "example only"
   AND bump to a current number, so it neither goes stale again nor misleads.)

## Dependencies / sequencing

- Independent of the agent-comms IPD line. Coordinate F7 with `20260715-1451-01` (that IPD owns it).
- Pure docs/consistency + one shipped-constant fix; target the next MINOR (some changes are user-visible
  via installed workflows/version stamp). No behavior change beyond F3.

## Approval and execution gate

`to-review`. Execution contract (follow EXACTLY):

1. SCOPE FENCE. Edit ONLY the specific files/lines named in F1-F6, F8-F13 (RELEASING.md, index.md,
   normalize_plan_names.py, DECISIONS.md [ADD erratum only] + ARCHITECTURE.md refs, CONTRIBUTING.md,
   .agents/plans/README.md + .agents/workflows/templates/plans-README.md, plan-review-long/report-template.md,
   .agents/docs/research/README.md, a new .agents/docs/roadmaps/README.md, README.md), plus CHANGELOG.md
   and a DECISIONS erratum entry. Do NOT touch F7 (owned by 20260715-1451-01). Do NOT rewrite append-only
   DECISIONS headings in place, edit workflow-artifacts/ or executed/superseded plans, or change the shim
   generator. If a fix seems to need more, STOP and report.
2. Authoring style: NO em dashes or en dashes in any Markdown you write.
3. VALIDATE: run the FULL test suite; paste the ACTUAL runner output. Re-grep to confirm: zero
   `WORKFLOWS-VERSION: 1.1.0` in index.md, zero remaining `first PyPI release is 1.1.0`, `DOCS_SUBDIRS`
   in normalize_plan_names.py matches engine.py, no `NOT ELIGIBLE:` in plan-review-long. Keep the two
   plans-README copies byte-identical (diff them). Confirm `aw plan-names` clean.
4. COMMIT only this IPD's touched files, PATH-SCOPED (new files need `git add <path>` first); never
   `git add -A`/bare/`-a`; never push.
5. When implemented and tests actually pass, `git mv` this file to `.agents/plans/executed/`, set
   `Status:` to `executed`, append a `## Workflow history` line, commit path-scoped.
6. RELEASE: cut separately via release-review Section 9 after a human rung choice.

HARD MUST: paste the real test output; never rewrite append-only DECISIONS in place (erratum only); keep
the two plans-README copies identical; stay inside the scope fence; never push. Not auto-executed;
requires human approval.
