# IPD: Assess documentation - CHANGELOG version-scoping + post-session doc accuracy

- Date: 2026-07-15
- Concern: documentation (lens: `documentation`), with a CHANGELOG + version-scoping PRIMARY emphasis and
  a full-docs-surface accuracy pass SECONDARY. Driven by: this session executed six IPDs (D79-D84) and
  the durable/specialized docs (DECISIONS, CHANGELOG bullets, workflow bodies, plans README) captured
  them well, but the CHANGELOG mis-scopes new features as a patch, and several SECONDARY discoverability
  surfaces (TODO, top-level README/ARCHITECTURE/AGENTS, the generated STATUS/AGENTS artifacts) did not
  catch up. Assessed with the framework itself as the subject (its own docs are the product here).
- Scope: authored docs only - CHANGELOG.md (primary), TODO.md, README.md, ARCHITECTURE.md, CONTRIBUTING.md,
  the repo's own AGENTS.md block, `.agents/README.md`; plus two REGENERATED artifacts (`.agents/plans/STATUS.md`
  via `aw plans --write-index`, and this repo's `AGENTS.md` block via `aw install .`). NO product code
  change. NO change to the versioning MECHANISM (git-tag-driven / bake-then-tag) - only CHANGELOG content
  re-scoping. The version-scoping is a release-scoping RECOMMENDATION the human decides at approval (or
  defers to release-review Section 8).
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-15 /assess documentation (its_direct/pt3-claude-opus-4.8-1m-us): assessed; proposed 8 changes.
  Run with the framework as the subject and a CHANGELOG-primary emphasis, using two parallel read-only
  audit lanes (dogfooding D84: lane 1 CHANGELOG/versioning, lane 2 broader docs), coordinator synthesized.
  The two highest-severity findings (CHANGELOG mis-scoping; TODO calling comms "on trial") were
  independently re-verified against source before filing.

## Project conventions discovered (Step 0)

- Plans lifecycle `.agents/plans/{pending,executed,superseded,not-executed,reusable}`; IPD front-matter
  `Status:` readiness enum; `YYYYMMDD-HHMM-NN-<slug>.md`. This IPD is born `to-review`.
- Versioning is git-tag-driven, bake-then-tag, first PyPI = 1.2.0 (D74/D75); CHANGELOG/RELEASING/
  CONTRIBUTING agree on the MECHANISM (verified consistent). The issue is CHANGELOG CONTENT scoping, not
  the mechanism.
- House rule: no em or en dashes in authored Markdown. (Verified: zero dash violations across authored
  docs; the house rule holds - no finding.)
- assess produces a PROPOSAL only; a human approves before execution.

## Findings (severity + evidence)

Verified against source (the two High findings independently re-checked by the coordinator).

- F1 [HIGH] CHANGELOG version mis-scoping. `## 1.2.1 (pending)` (CHANGELOG.md:27, a PATCH heading)
  contains NEW user-facing features whose own executed IPDs scope them MINOR: D81 comms convention
  (CHANGELOG.md:47), D80 readiness vocab + `GO - PENDING HUMAN APPROVAL` (CHANGELOG.md:56), D82 Set/Order
  (CHANGELOG.md:41). Meanwhile `## 1.3.0 (pending)` (CHANGELOG.md:7) sits ABOVE them holding only D83/D84.
  IPD scoping statements: 1451-01 "target the next MINOR", 1033-01 "MINOR release", 1602-01 "next MINOR".
  So the CHANGELOG contradicts the decision record and semver (adding a new convention is minor, not
  patch).
- F2 [HIGH] TODO.md stale: calls the agent-comms convention un-formalized. `TODO.md:51-52` says the
  protocol "is on trial ... formalizing it into the framework (installer scaffolding, ... an always-loaded
  pointer) is gated on the trial and would be its own IPD" - but D81 ALREADY shipped exactly that
  (scaffolding + the always-loaded "check your inbox" clause). `TODO.md:27,47` also cite the RETIRED draft
  spec `20260712-2133-02` as the live reference instead of the canonical `20260715-1722-01-agent-comms-convention.md`.
- F3 [MEDIUM] This repo's own `AGENTS.md` lacks the D81 "check your inbox" clause it now INSTALLS into
  other repos (`grep` count 0 in AGENTS.md; the generator emits it at `engine.py:576-582`). The block was
  generated pre-D81 and never re-synced - the framework fails to dogfood its own current pointer block.
- F4 [MEDIUM] `.agents/plans/STATUS.md` (the generated GitHub-web board) is badly stale: says "Total: 46
  ... pending/ (3) ... executed/ (42)" (STATUS.md:5-14); reality is 0 pending / 60 executed. Regeneration
  gap since 2026-07-12.
- F5 [MEDIUM] `.agents/comms/` (a D81 default-on installed convention) is not discoverable from ANY
  top-level doc (README/ARCHITECTURE/AGENTS) - only from DECISIONS, the spec, CHANGELOG, and the
  installer-generated `.agents/comms/README.md`. Comparable first-class features (plan lifecycle, docs
  buckets) ARE described in README/ARCHITECTURE.
- F6 [LOW] CONTRIBUTING.md:54 self-test module list omits the new `comms` and `plans` modules (and
  `pypi_links`); a contributor touching them may not see themselves in the "run the suite" trigger.
- F7 [LOW] ARCHITECTURE.md:386-400 test-coverage inventory omits `test_comms.py` and `test_plans_board.py`
  (incl. the D82 `SetOrderTests`).
- F8 [LOW] `.agents/README.md:5-10` lists only `workflows/` and `plans/`, omitting the `docs/` bucket set
  (and future `comms/`); and README.md:282-283 lists only `.agents/docs/prompts/`, not the full bucket set.

Confirmed clean (no action): em/en dashes (0 violations); versioning MECHANISM consistency (git-tag/
bake-then-tag/first-PyPI-1.2.0 all agree); every D79-D84 CHANGELOG bullet faithfully matches its
DECISIONS body + executed IPD (no orphans either direction); install/getting-started path current
(`aw install`); counts (16-row table, 18 shims) accurate; D80/D82/D84 accurately documented in the
workflow bodies + plans README; no `tmp/agent-comms` leakage into current authored docs.

## Proposed changes (ordered, validatable; all Low Remediation Risk unless noted)

1. **[F1] Re-scope the CHANGELOG (PRIMARY).** Move the three new-feature bullets (D81 comms L47-55, D80
   readiness vocab L56-62, D82 Set/Order L41-46) OUT of `## 1.2.1 (pending)` and INTO `## 1.3.0 (pending)`.
   Result: `1.2.1` holds only true patches (D75 baked-VERSION, D76/D77 pre-flight, D78 test flakiness);
   `1.3.0` holds all new user-facing features (comms, Set/Order, readiness vocab, auto-parallel lanes) +
   the internal orchestrator unification (D83). RECOMMENDED scoping table is in the run record; the human
   confirms it at approval (or defers to release-review Section 8, which formally owns release scoping).
   Then revise the 1.3.0 boundary note (CHANGELOG.md:9-10) to state 1.3.0 = all new features this session,
   1.2.1 = pure bug-fix patch. Remediation Risk: Low (content re-org; no mechanism change).
2. **[F1c] Decide + document D79's `aw plan-names` bucket-recognition line** (CHANGELOG.md:70): it is a
   small user-facing behavior change inside a docs "patch" bullet. Either keep it in 1.2.1 as a bug fix
   (recognizing an already-shipped bucket that drifted) or move that one line to 1.3.0. Document the
   choice explicitly rather than leaving it implicit. (Human decides; lean: keep as a 1.2.1 bug fix.)
3. **[F2] Update TODO.md.** Change the "Notes" bullet (TODO.md:51-52) to state the agent-comms convention
   was FORMALIZED in D81 (installer scaffolding + always-loaded pointer shipped); repoint the still-open
   items (trust tiers, verifiable provenance, `aw comms` helper) at the canonical spec
   `20260715-1722-01-agent-comms-convention.md`, not the retired draft `20260712-2133-02`. Keep `aw comms`
   as a legitimately-open idea but drop the false "gated on the trial / would be its own IPD" framing.
4. **[F3] Re-sync this repo's `AGENTS.md` block (REGENERATE, do not hand-edit).** Run `aw install .` so the
   managed `AGENT-WORKFLOWS` block picks up the D81 "check your inbox" clause. This is a generated artifact;
   regenerate it, do not author it by hand. Verify the block then contains the clause.
5. **[F4] Regenerate `.agents/plans/STATUS.md`** via `aw plans --write-index` (generated artifact; do not
   hand-edit). Confirm it then reads 0 pending / 60 executed (or whatever is current at execution time).
6. **[F5] Surface `.agents/comms/` in a top-level doc.** Add a short subsection + a repo-tree line to
   ARCHITECTURE.md (near the distribution/setup-artifacts discussion) and a brief mention in README's
   "What's in this repo", pointing at `.agents/comms/README.md` and the canonical spec. Keep it concise
   (Complexity axis: no bloat).
7. **[F6/F7/F8] Small accuracy/navigation fixes.** Add `comms`/`plans` (+`pypi_links`) to the CONTRIBUTING
   self-test module list and coverage summary; add `test_comms.py`/`test_plans_board.py` to the
   ARCHITECTURE test inventory (or generalize the sentence); add a `docs/` bullet (and gated `comms/`) to
   `.agents/README.md` and broaden README's docs-bucket mention.

## Deferred / out of scope

- Any change to the versioning MECHANISM (git-tag-driven / bake-then-tag / first-PyPI-1.2.0) - only
  CHANGELOG CONTENT is re-scoped.
- The actual release cut / tag / push (a release-review Section 9 action after a human GO; explicitly not
  now - no release before the queue is finished, per the maintainer).
- The `aw comms` helper tool itself (a genuinely-open future idea; this IPD only fixes TODO's framing of
  it, it does not build it).
- STATUS.md commit-vs-gitignore policy question (whether a drift-prone generated board should be tracked)
  - noted for the maintainer, not decided here.

## Open questions (v1 leans for review)

1. Version-scoping confirmation: accept the recommended 1.2.1(patch)/1.3.0(feature) split now, or defer
   the final scoping to release-review Section 8? (Lean: accept the re-scope now so the CHANGELOG is
   honest in the interim; release-review can still adjust. The re-scope is reversible content movement.)
2. F1c bucket line: 1.2.1 bug fix vs 1.3.0 feature? (Lean: keep in 1.2.1 as a bug fix - it recognizes an
   already-documented bucket that had drifted, not a new capability.)
3. F5 depth: a few-sentence pointer in ARCHITECTURE + README, or a fuller section? (Lean: concise pointer;
   the canonical spec + `.agents/comms/README.md` hold the detail. Avoid doc bloat.)

## Dependencies / sequencing

- Independent of code IPDs; pure docs + two regenerations. No ordering constraint.
- Naturally PRECEDES a future `/release-review` (a clean, correctly-scoped CHANGELOG makes release-review's
  docs/version reconciliation a confirmation rather than a discovery), which is the maintainer's stated
  intent for sequencing.

## Approval and execution gate

`to-review`. Execution contract (follow EXACTLY):

1. SCOPE FENCE. Edit ONLY: CHANGELOG.md, TODO.md, ARCHITECTURE.md, README.md, CONTRIBUTING.md,
   `.agents/README.md`. REGENERATE (do not hand-edit) `.agents/plans/STATUS.md` (via `aw plans
   --write-index`) and this repo's `AGENTS.md` managed block (via `aw install .`). Do NOT change product
   code, the versioning mechanism, any DECISIONS entry, or cut/tag/push a release. If a fix seems to need
   more, STOP and report.
2. Authoring style: NO em dashes or en dashes in any Markdown you write.
3. VALIDATE: run the FULL test suite; paste the ACTUAL runner output. Confirm: CHANGELOG 1.2.1 holds only
   D75/D76/D77/D78 (+ the F1c-decided docs line) and 1.3.0 holds D79-D84 features; TODO no longer says
   comms is "on trial"/"gated"; this repo's AGENTS.md now contains the "check your inbox" clause; STATUS.md
   shows the current 0-pending count; `aw plan-names` clean; the two plans-README copies remain
   byte-identical if touched (not expected here).
4. COMMIT only this IPD's touched/regenerated files, PATH-SCOPED; never `git add -A`/bare/`-a`; never push.
5. When implemented and tests actually pass, `git mv` this file to `.agents/plans/executed/`, set
   `Status:` to `executed`, append a `## Workflow history` line, commit path-scoped.

HARD MUST: paste the real test output; regenerate (never hand-edit) STATUS.md and the AGENTS block; stay
inside the scope fence; do not cut/tag/push a release; never push. Not auto-executed; requires human
approval.
