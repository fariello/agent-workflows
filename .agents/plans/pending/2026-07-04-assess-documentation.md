# IPD: Assess documentation - fix stale command syntax in the by-tool guide and orient the prompts library

- Date: 2026-07-04
- Concern: documentation
- Scope: whole project (repo-level user-facing docs: README, ARCHITECTURE, CONTRIBUTING, AGENTS, GUIDING_PRINCIPLES, the workflow manifest `index.md`, and `prompts/`). The workflow *bodies* are treated as product, their READMEs/manifest as documentation.
- Status: PENDING (awaiting human approval; not executed)
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Run record: `workflow-artifacts/assess-documentation/20260704-180630/`

## Goal

Keep the documentation honest and accurate to what the framework does *today* (GUIDING_PRINCIPLES P2). This repo's entire value is disciplined, self-consistent instruction docs, so a doc that tells a newcomer to type a command that no longer exists is a direct hit on the product's core promise. This plan fixes the one remaining accuracy defect (a stale command form in the canonical per-tool run guide) and closes a small orientation gap around the `prompts/` library.

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md` (P2 honest docs, P4 durable cold-start knowledge, P8 single source of truth). No universal fallback needed.
- Pending-plans location/format used: `.agents/plans/pending/` (new IPDs) with terminal dir `.agents/plans/done/` (this repo uses the `done/` alias, both dirs exist). IPD format: `.agents/workflows/assess/templates/ipd.md`.
- Contributor/spec-sync contract: `CONTRIBUTING.md` ("Doc-sync checklist"), `AGENTS.md` (pointer only). CONTRIBUTING step 5 requires README/ARCHITECTURE to still describe the current set accurately.
- Stack / relevant context: instruction-doc framework + three stdlib Python tools + an installer; docs are Markdown; house rule: no em dashes in authored Markdown.
- Self-review caveat: the same author who built and last edited these docs is assessing them, so this is a rigorous self-check, not an independent audit. Findings are tied to `file:line` evidence.

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate for whether to act now. Persona = which reviewer perspective surfaced it.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| DOC-01 | Medium | Low | novice | accuracy/consistency | The manifest's "Running a workflow (by tool)" table shows the retired per-concern command syntax `/assess-security` and `/assess-performance src/server` (and `/assess-security` for Claude Code). D31 collapsed the surface to a single parameterized `/assess <concern>`; the same file's Notes and README/ARCHITECTURE all use `/assess <concern>`. A newcomer copying the canonical per-tool guide types a command that does not exist. | `.agents/workflows/index.md:87-88`; contradicted by `.agents/workflows/index.md:198-199`, `README.md:50-56` |
| DOC-02 | Low | Low | novice | completeness/navigation | `prompts/` is called a "reusable prompt library" in README and ARCHITECTURE but has no index. A reader cannot tell what the four files are, which are current vs. superseded by the shipped `.agents/workflows/` framework, or how to use them; `prompts/fix-bar.md` opens by referencing RhodyPACT-specific paths with no orientation. | `README.md:216`; `ARCHITECTURE.md:25-26`; `prompts/*`; `prompts/fix-bar.md:3-5` |

Everything else assessed as accurate and current: README quick-start and command tables, the `/assess <concern>` pipeline description, the install-details/versioning section (matches `install-workflows.py --help` and `--version` output `20260704-02`), ARCHITECTURE (verified against the current tree and D31-D39), CONTRIBUTING doc-sync + self-tests + em-dash rule, GUIDING_PRINCIPLES, AGENTS pointer, and the `getting-started`/`list-workflows` bodies (which already use the correct `/assess <concern>` / `/advise <persona>` forms). The "Twelve core workflows" count and the 15-shim math (12 core + assess + advise + assess-all) reconcile with the manifest. No em dashes in any authored doc.

## Proposed changes (ordered, validatable)

Fix by default; each item is safe, well-scoped, and verifiable.

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | DOC-01 | In the "Running a workflow (by tool)" table, change the OpenCode row example from `/assess-security` and `/assess-performance src/server` to `/assess security` and `/assess performance src/server`; change the Claude Code row example from `/assess-security` to `/assess security`. Leave `/assess-all` untouched (it is a real shim). Optionally add a half-sentence noting the concern is the first argument, matching README:54. | `.agents/workflows/index.md` (lines ~87-88) | Low | Run `grep -nE "/(assess\|advise)-[a-z]" .agents/workflows/index.md`. This pattern requires a leading slash, so it never matches the `\| assess-... \|` catalog *rows*; the only legitimate remaining match is the `/assess-all` mention on the `assess-all` manifest row (line ~39). Expected after the fix: exactly that one `assess-all` line, and NO `/assess-<concern>` or `/advise-<persona>` command example in the by-tool table (lines 87-88). Also read the by-tool table and confirm it shows `/assess security`. |
| 2 | DOC-02 | Add `prompts/README.md`: a short index with one line per file (what it is; current vs. historical/reference; relationship to the maintained `.agents/workflows/` workflows), plus a lead sentence stating the canonical, maintained versions of these ideas ship under `.agents/workflows/` and these prompts are kept as origin/reference material. Note that `fix-bar.md` predates and inspired `release-review/fix-decision-policy.md`. | `prompts/README.md` (new) | Low | File exists; each of the four `prompts/*.md` files is named with a one-line description; no em dashes: grep for a literal em-dash character (U+2014) in `prompts/README.md` and expect 0, e.g. `grep -c $'\u2014' prompts/README.md` (Bash `$'...'` expands the escape) or paste the literal character. Do NOT write the pattern as a plain double-quoted `"\u2014"`: `grep` does not expand that escape, so it matches the literal text `u2014` and would falsely report 0. |
| 3 | DOC-02 | Point the two prose references at the new index. README:216 gains "(see `prompts/README.md`)". ARCHITECTURE:25-26 already carries a parenthetical ("e.g. fix-bar.md, an origin note for the Fix Bar"); extend or replace that same parenthetical to add "see `prompts/README.md`" rather than appending a second, separate mention. | `README.md`, `ARCHITECTURE.md` | Low | Both references mention `prompts/README.md`; ARCHITECTURE has a single combined parenthetical (no duplicate prompts note); both files still em-dash-free (a literal-U+2014 grep returns 0 on each). |

## Deferred / out of scope (with reason)

None. Both findings are Low Remediation Risk and are proposed for fixing. Nothing was deferred; nothing was dropped.

## Scope check

- Over-scope (untraceable to a need; propose removal/deferral): none. Deliberately NOT rewriting the historical `prompts/*.md` bodies (they are origin/reference artifacts; editing them for "currency" would falsify history, against P4) - only adding an orienting index. Deliberately NOT documenting the internal D39 pending-plans review gate in the user-facing README (it is a release-review internal behavior, already covered in the workflow bodies and DECISIONS; adding it to README would be bloat, Complexity axis).
- Under-scope (needed capability missing; propose adding): the `prompts/` orientation index (Step 2) is the one missing piece; it is proposed above.

## Required tests / validation

Docs-only; no code or behavior change, so no automated tests are required. Validation is the per-step checks above plus:

- `grep -rnE "/(assess|advise)-[a-z]" README.md ARCHITECTURE.md .agents/workflows/index.md` shows no per-concern/per-persona *command* examples. Note the leading slash in the pattern: it does NOT match the `| assess-<concern> |` manifest catalog rows (those have no slash), so the only legitimate matches are the real `/assess-all` command mentions (README and the `assess-all` manifest row). Any `/assess-security`-style hit is a leftover to fix.
- Em-dash sweep over changed files returns 0, matching a literal em-dash character (U+2014), e.g. `grep -c $'\u2014' <file>` in Bash (which expands the escape) or by pasting the literal character. Do NOT write the pattern as a plain double-quoted `"\u2014"`: shell `grep` does not expand that escape, so it matches the literal string `u2014` and returns 0 even when em dashes are present (a false pass).
- Optional: `python3 -m unittest discover -s tests -t .` still passes (should be unaffected; documents only).

## Spec / documentation sync

This plan *is* the documentation sync. No user-visible product behavior changes. Per CONTRIBUTING step 6, if the maintainer considers the `prompts/README.md` addition a design choice worth recording, add a short dated `DECISIONS.md` entry; otherwise it is a routine doc fix and needs none. No VERSION bump required (docs-only), consistent with prior doc-fix executions.

## Open questions

1. For `prompts/README.md`, should each historical prompt be labeled explicitly "superseded by <workflow>" where a successor exists (e.g. `modular-release-review-instruction-set-generation-prompt.md` -> `release-review/`, `fix-bar.md` -> `release-review/fix-decision-policy.md`), or kept as a neutral "reference material" note? Assumption for execution: label the clear successors and mark the two general QA/validation prompts as reference material.
2. Confirm the terminal dir choice: this repo uses `.agents/plans/done/` (not `executed/`). Assumption: keep `done/` (accepted alias; existing repo convention). (Also stated in the conventions and the approval gate below; recorded here only for the executor's convenience.)

## Plan-review revisions applied (2026-07-04)

This IPD was hardened by `plan-review` before approval. Fixes applied in place:

- PR-01 (High, validation false-negative): Steps 2 and 3 originally specified the em-dash
  check as a plain double-quoted `"\u2014"`, which shell `grep` treats as the literal text
  `u2014` and reports 0 even when em dashes are present - it would falsely pass a doc that
  violates the house rule. Rewritten to grep for a literal em-dash character (U+2014), e.g.
  via Bash `$'\u2014'` or the pasted character.
- PR-02 (Medium, misdescribed validation): Step 1's expected grep result claimed the pattern
  matches the manifest catalog rows. It does not (the pattern needs a leading slash); the
  only legitimate match is the `/assess-all` mention. Corrected so the check is accurate and
  actionable.
- PR-03 (Low, consistency): Step 3 now integrates the `prompts/README.md` pointer into
  ARCHITECTURE's existing "fix-bar.md, an origin note" parenthetical (ARCHITECTURE:25-26)
  rather than appending a second, separate prompts note.

No scope, findings, or approach changed; the review only corrected the validation and edit
instructions so execution can be verified honestly.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run the `plan-review` workflow to harden it).
2. On approval, execute the ordered changes, run the validation, and sync docs.
3. Only then move this IPD from `.agents/plans/pending/` to the terminal dir `.agents/plans/done/` (this repo's convention).
