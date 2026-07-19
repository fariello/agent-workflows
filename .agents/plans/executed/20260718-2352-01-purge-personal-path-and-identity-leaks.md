# IPD: Purge personal-path / identity leaks from tracked files, published packages, and git history

- Date: 2026-07-18
- Concern: privacy / data leak (maintainer PII) + release correctness
- Scope: every TRACKED file that references the maintainer's local filesystem, usernames, or private repo names; the shipped package surface; the three published PyPI releases; the full git history; and a durable anti-regression guard. Excludes gitignored `local/` comms and the intentional public author email.
- Status: executed
- Approval: approved by the human (repo maintainer) 2026-07-19
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-18 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored after an inbox task (untrusted, verified independently via `git grep`) and the human confirmed a leak concern. Human decisions captured: fix-forward + YANK v1.0.0/1.1.0/1.2.0; full git history rewrite replacing personal tokens everywhere; write-review-execute. Full verified enumeration produced (see Findings; a copy of the raw sweep was written OUTSIDE the repo at /tmp/opencode/agent-workflows-leak-report.txt and is not tracked). This plan is kept OUT of the repo (at /tmp/opencode/aw-privacy-cleanup/) because it necessarily quotes the leaked tokens; it is committed only as a redacted executed record at the end (per the agreed write-review-execute-redact-commit process).
- 2026-07-19 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed. Verified L1/L2 against source and re-swept broadly, surfacing an EXPANDED token set (L8 second account a second local account + a second-account home path + uid 1002 + real `ses_` ids; L9 the maintainer handle handle/remote). Hardened Step 7 guard (tracked-only scan, runtime-synthesized fixture, allowlist incl. remote URL), Step 9 (reviewed `--replace-text` map, preserve package name, yank-immutability honesty note), Step 4 scrub scope. Resolved OQ1-OQ6 with the human. `git-filter-repo` v2.47.0 install confirmed. Status -> reviewed. NOTE: this review made NO in-repo commit (the plan is deliberately out-of-repo); pre-review snapshot and hardened-result commits are Not Applicable for this plan.

## Goal

`agent-workflows` is a PUBLICLY published PyPI package with a public GitHub repo. No tracked file, no shipped artifact, and (per the human's decision) no historical commit should embed the maintainer's personal filesystem layout, usernames, or private repo names. The ONLY tolerated personal identifier is the intentional public author identity (`Gabriele Fariello <gfariello@fariel.com>` in `pyproject.toml`/`CITATION.cff`, and its factual mention in `CHANGELOG.md`).

This plan (1) scrubs all leaks from tracked files, (2) makes install-surface paths portable, (3) yanks the three already-published releases that carry a leak and ships a clean forward fix, (4) rewrites git history to purge the tokens from all past commits, and (5) adds a pre-commit + CI guard so the leak cannot regress.

Why it matters: publishing a maintainer's home directory, usernames, and private repo names is a privacy leak to every downstream user and bakes in paths that cannot resolve on their machines. It is both a privacy and a correctness defect.

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md` (P10 safety/reversibility; P5 externalize state). Execution contract in `.agents/plans/README.md` / `AGENTS.md`: path-scoped commits, never push (this plan's history-rewrite + yank steps are HUMAN-GATED and explicitly out of the normal auto-commit lane).
- No em/en dashes in authored Markdown.
- Packaging boundary (verified): only `agent_workflows/` and `.agents/workflows/` ship (`pyproject.toml:64-75` force-include + sdist include); `tests/`, `workflow-artifacts/`, and `.agents/{docs,plans,prompts,comms}/` are excluded (`tests/test_packaging.py:25-31`).
- Historical-record convention (from the inbox note and `.agents/plans/README.md`): executed plans and recovery transcripts are records; do not silently rewrite in place without a human call. The human HAS now made that call (history rewrite approved), so scrubbing them is authorized, recorded here.
- Released tags: `v1.0.0`, `v1.1.0`, `v1.2.0`. Version is git-tag-driven (`hatch_build.py`, D44).

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate. Personal tokens in scope (EXPANDED at review, PR-001):
- Local paths / usernames: a home-directory path, the local-checkout prefix (and the local-checkout-repo form names: a private reference-agent repo name, `opencode`, a sibling repo, a consuming repo, the former repo name, a private repo name).
- SECOND local account from the security test: a second local account, a second-account home path, and the associated uid `1002`.
- Identity: the GitHub username the maintainer handle (including the remote `git@github.com:fariello/agent-workflows.git`).
- Real session ids captured in the advisory (e.g. a real captured session id) and our own `our recovery session id` recovery id: machine/session data; abstract to a placeholder.

NOT in scope (keep): `gfariello@fariel.com` public author email; generic placeholders (`/home/u/src`, `/home/alice/data`, `a@b.co`); the LITERAL string `agent-workflows` as the package/repo NAME (it is public and load-bearing in the remote URL, package name, and install paths - do NOT blindly replace it; only `<local-checkout>/agent-workflows` as a LOCAL-path prefix is abstracted).

CAVEAT (verified at review): none of the EXPANDED tokens (a second local account, the maintainer handle, `ses_...`) appear in the SHIPPED tree (`agent_workflows/`, `.agents/workflows/`), so PyPI exposure remains ONLY a private repo name (L1). The rest are public-git-repo leaks.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| L1 | BLOCKER | Low | user / maintainer | shipped package + PyPI | a private prompt-toolkit repo path (private repo name) is inside a SHIPPED file and is PUBLISHED on PyPI in v1.0.0, v1.1.0, v1.2.0 (verified by building the v1.2.0 wheel and grepping it). | `.agents/workflows/assess/references/prose-style.md:8-9`; built wheel `agent_workflows/_data/.agents/workflows/assess/references/prose-style.md` |
| L2 | HIGH | Low | user / maintainer | shipped package (next release) | a private reference-agent repo name (private repo name) appears in a SHIPPED code comment; `comms.py` ships in the wheel and will carry it into 1.3.0. Not in v1.0.0-1.2.0 (comms.py did not exist then). | `agent_workflows/comms.py:11,75` |
| L3 | HIGH | Low | maintainer | public git repo | a maintainer home path absolute paths and `file-URL home links` links pervade tracked docs/plans/artifacts (not shipped, but public on GitHub). Includes `workflow-artifacts/release-review/*/00-run-metadata.md` `Repository:` lines and all `.agents/docs/walkthroughs/*`. | report lines 12-104; e.g. `workflow-artifacts/release-review/20260706-112559/00-run-metadata.md:6`; `.agents/docs/walkthroughs/20260712-1023-01-...:4` |
| L4 | HIGH | Low | maintainer | public git repo | the local-checkout-repo form private sibling-repo names in tracked files: a private reference-agent repo name, `opencode`, a sibling repo, a consuming repo, the former repo name, a private repo name. | `DECISIONS.md:26,701,708,740-767,1077,1081,1504,2174`; `.agents/plans/executed/20260701-1534-01-...:53,117,148`; `.agents/plans/executed/20260715-1033-01-...:31,243`; `.agents/docs/research/20260714-2300-01-...:26,28,104` |
| L5 | HIGH | Medium | maintainer | untracked-but-committable | `opencode-recovery/` (~12MB of full session transcripts, saturated with leaks) is UNTRACKED but NOT gitignored - one `git add -A` from being committed. Also the tracked recovery file `.agents/prompts/pending/20260717-1450-01-...compacted.md` and the handoff `.agents/plans/pending/20260717-1950-01-...` carry leaks. | `opencode-recovery/*` (untracked, not ignored); `.agents/prompts/pending/20260717-1450-01-...:43,68`; `.agents/plans/pending/20260717-1950-01-...:26,27,42` |
| L6 | HIGH | Medium | maintainer | git history | All of the above persist in past commits on the public repo; scrubbing the working tree does not remove them from history. Human approved a full history rewrite. | `git log` on the affected paths |
| L7 | HIGH | Low | maintainer | regression prevention | There is no guard preventing re-introduction of a personal-path leak; a one-time cleanup will drift back. | no such hook/test exists |
| L8 | HIGH | Low | user / maintainer | public git repo (second-party PII) | The OpenCode security advisory embeds a SECOND real local account's data from the cross-user test: a second local account, a second-account home path, uid `1002`, and a real captured session id a real captured session id. These are not in the shipped tree but are public on GitHub and are arguably more sensitive than a repo name (another user's home path + a live session id). | `.agents/docs/research/20260716-0850-01-...:52,56`; `.agents/docs/research/opencode-security/20260716-2100-01-...`; `DECISIONS.md` |
| L9 | MEDIUM | Low | maintainer | identity | GitHub username the maintainer handle and the remote URL `git@github.com:fariello/agent-workflows.git` appear in many tracked files and `workflow-artifacts/`. The remote is arguably public (it is the repo's own origin), but the maintainer handle is a personal handle; decide whether to abstract in-repo references (OQ5). | `.agents/plans/pending/20260717-1950-01-...:42`; `DECISIONS.md:694`; `workflow-artifacts/release-review/*/00-run-metadata.md` |

## Proposed changes (ordered, validatable)

Ordered so the repo is safe early (stop new leaks) before the destructive history step. Steps 8-9 are HUMAN-GATED side effects (never run without explicit GO).

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | L5 | Stop the bleeding: add `opencode-recovery/` to root `.gitignore` (untracked recovery transcripts must never be committable); confirm `git check-ignore` matches. Decide `workflow-artifacts/` gitignore in Step 6. | `.gitignore` | Low | `git check-ignore opencode-recovery/` returns a match; `git status` no longer offers it |
| 2 | L1 | Scrub the SHIPPED `prose-style.md`: reword the origin note to remove a private prompt-toolkit repo path, keeping meaning (e.g. "adapted from an internal nonfiction-prose prompt toolkit maintained by the author"). | `.agents/workflows/assess/references/prose-style.md` | Low | no personal token remains; `git grep a private repo name -- .agents/workflows/` empty; content-lint clean |
| 3 | L2 | Scrub the SHIPPED `comms.py`: reword the two comments to drop a private reference-agent repo name (e.g. "mirroring session-key safety guards from a reference agent implementation"). | `agent_workflows/comms.py` | Low | `git grep a private reference-agent repo name -- agent_workflows/` empty; tests still pass |
| 4 | L3,L4,L8,L9 | Abstract leaks in EDITABLE docs (research, specs, walkthroughs, DECISIONS.md): replace `<repo-root>/` and `file-URL home links` with repo-relative paths; replace the local-checkout-repo form private names with a neutral description or placeholder; ALSO abstract the SECOND-account data in the OpenCode advisory (a second local account, a second-account home path, uid `1002`, real `ses_...` ids) to placeholders like `<victim-user>`, `<victim-home>`, `ses_<redacted>` while preserving the security narrative; and stray the maintainer handle USERNAME mentions in prose (per OQ5: LEAVE the `git@github.com:fariello/...` remote URL, which is the repo's public origin). | `.agents/docs/**`, `DECISIONS.md` | Low | `git grep` for the full token set returns empty across these paths EXCEPT the allowed remote URL; docs still read correctly and the advisory still makes its point |
| 5 | L3,L4,L5 | Abstract leaks in tracked PLANS/PROMPTS/COMMS (executed plans, `.agents/plans/pending/20260717-1950-01`, `.agents/prompts/pending/20260717-1450-01`, `.agents/comms/shared/{sent,archive}`). For executed plans (historical records) add a one-line noted redaction where a value is abstracted, per convention. | `.agents/plans/**`, `.agents/prompts/pending/**`, `.agents/comms/shared/**` | Low | `git grep` tokens empty across these paths; each redacted record notes it |
| 6 | L3 | Decide + apply disposition for `workflow-artifacts/` (ephemeral run records full of absolute paths): gitignore it AND `git rm --cached -r workflow-artifacts/` to untrack going forward (recommended), OR scrub in place. (Confirm at review; lean untrack.) | `.gitignore`, `workflow-artifacts/**` | Low | `git grep` tokens empty in tracked tree; `git check-ignore workflow-artifacts/` matches if untracked |
| 7 | L7,L1,L4,L8,L9 | Add the durable guard: a stdlib scanner + pre-commit hook AND a `tests/test_no_personal_paths.py` that scan TRACKED content only (iterate `git ls-files`, so untracked scratch like the out-of-repo copy of THIS plan and gitignored files are never scanned). Patterns cover the FULL expanded token set (Findings): a home-directory path (any user, not just the maintainer, minus the generic placeholders), the local-checkout-repo form private names, a second local account, the the maintainer handle handle per OQ5, and a `ses_[0-9a-f]{6,}`-style session-id pattern. Allowlist mechanism: an explicit list of (path, pattern) exceptions for the public author email, the documented generic placeholders, the literal package name `agent-workflows`, and the public remote URL `git@github.com:fariello/agent-workflows.git` (per OQ5 - the remote is allowed, but a BARE the maintainer handle handle in prose is still flagged). The guard's OWN test fixture must SYNTHESIZE a fake leak at runtime (not store one in a tracked fixture file) so the guard does not trip on itself. | new scanner + `.pre-commit-config.yaml` + `tests/test_no_personal_paths.py` | Medium | the test FAILS on a runtime-synthesized planted leak and PASSES on the cleaned tree; pre-commit blocks a planted leak; the guard itself is not a self-leak |
| 8 | L1 | HUMAN-GATED: ship a clean forward release. After Steps 1-7 merge and 1.3.0 is cut (separate release-review Section 9), the published 1.3.0 wheel is leak-free (guarded by Step 7 + a packaging assertion that the wheel contains no personal token). | (release action) | Low | build the 1.3.0 wheel, grep it: zero personal tokens |
| 9 | L1,L6,L8 | HUMAN-GATED destructive side effects, each requiring explicit GO and done by/with the human: (a) `pip`-YANK v1.0.0, v1.1.0, v1.2.0 on PyPI; (b) full git history rewrite with `git filter-repo --replace-text <map>` across all refs AND tags, using a REVIEWED literal replacement-map file (`token==>replacement`, one per line) that (i) covers the full expanded token set, (ii) preserves the public author email, and (iii) does NOT replace the load-bearing package/repo name `agent-workflows` (only its local-path prefix `<local-checkout>/agent-workflows` / `<repo-root>`). Then a coordinated force-push. Prereq: `git-filter-repo` installed (DONE: v2.47.0, verified `git filter-repo --version`). HONESTY NOTE: a PyPI YANK hides a release from default resolution but does NOT alter or remove the already-uploaded wheel/sdist - the a private repo name string remains inside the immutable v1.0.0-1.2.0 artifacts for anyone who pins/downloads them; only DELETING the release (not chosen) removes the files, and even then PyPI does not allow re-upload of the same version. State this plainly so the yank is not mistaken for redaction of the published bytes. | replacement-map file (kept OUT of repo like this plan) + PyPI + git history | High | after rewrite, `git log -p --all | grep <token>` returns empty for the personal tokens (package name preserved); tags re-point to rewritten commits; PyPI shows the three versions yanked |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| L6 (Step 9) | High | functionality/security | The history rewrite + force-push and the PyPI yanks are irreversible/destructive and coordinate with every clone. They are PLANNED here but executed only on an explicit, separate human GO after Steps 1-8 are verified. | Execute Step 9 as a final gated action; announce the force-push to any collaborators/clones first. |

## Scope check

- Over-scope: keep the public author email and generic placeholders (`/home/u/src`, `/home/alice/data`) - abstracting those would be pointless churn. Do not touch `local/` comms (gitignored).
- Under-scope: the token list must be COMPLETE. Before executing, re-run the sweep with the full pattern set (a home-directory path, the local-checkout prefix, each private repo name, `$USER`) to catch any file added since this IPD. The Step 7 guard's allowlist must be reviewed so it does not silently permit a real leak.

## Required tests / validation

- New `tests/test_no_personal_paths.py`: scans the tracked tree (via `git ls-files`) for the personal-token patterns; FAILS on any hit outside the allowlist. Prove it by (a) it passes on the cleaned tree, (b) a planted-leak fixture makes it fail.
- Extend `tests/test_packaging.py`: assert the built wheel contains NONE of the personal tokens (belt-and-suspenders for the shipped surface).
- Full suite: `python -m pytest -q` stays green; paste ACTUAL output (baseline 266 passed, 1 skipped; expect +1-2 from the new test).
- Manual: `git grep -nI <each token>` across the working tree returns empty (except allowlisted); build the wheel and grep it (zero tokens); `git check-ignore opencode-recovery/ workflow-artifacts/`.
- Step 9 validation (human-gated): `git grep <token> $(git rev-list --all)` empty after rewrite; PyPI project page shows v1.0.0/1.1.0/1.2.0 yanked.

## Spec / documentation sync

- `DECISIONS.md`: new entry **D92** (pinned; current max D91) recording the no-personal-paths policy, the allowlist (public author email), the guard, and the one-time yank + history-rewrite decision.
- `.gitignore`: add `opencode-recovery/` (Step 1) and `workflow-artifacts/` if untracked (Step 6).
- `CHANGELOG.md`: a 1.3.0 note that references were scrubbed and a guard added (worded WITHOUT reintroducing any token).
- `CONTRIBUTING.md`: a short "no personal paths in tracked files" rule pointing at the guard.

## Open questions

All resolved at review (human, 2026-07-19); no open questions remain.

- OQ1 (workflow-artifacts disposition): RESOLVED - gitignore + `git rm --cached -r workflow-artifacts/` (untrack going forward; ephemeral run records). Encoded in Step 6.
- OQ2 (private repo-name replacement style): RESOLVED (review) - neutral description where the name carries no technical meaning; a placeholder path where the path SHAPE matters. Encoded in Steps 4-5.
- OQ3 (comms shared records): RESOLVED - abstract the absolute inbox path in the two `.agents/comms/shared/sent/*` messages to a repo-relative form (`<repo-root>/.agents/comms/shared/inbox/`); keep the messages tracked. Encoded in Step 5.
- OQ4 (guard location): RESOLVED (review) - repo-internal `tests/test_no_personal_paths.py` + a pre-commit hook; a shippable `agent_workflows` version is a later enhancement, not this plan. Encoded in Step 7.
- OQ5 (the the maintainer handle handle + remote URL): RESOLVED - LEAVE the remote URL (`git@github.com:fariello/agent-workflows.git`, the repo's public origin, a public fact); abstract only stray the maintainer handle USERNAME mentions in prose where they add nothing. The guard's allowlist therefore permits the remote URL but flags a bare the maintainer handle handle. Encoded in Steps 4 and 7.
- OQ6 (session ids): RESOLVED - redact real captured `ses_...` ids (advisory a real captured session id, recovery `our recovery session id`) to `ses_<redacted>`; they are live identifiers. Encoded in Step 4 and the guard pattern (Step 7).

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope.

SPECIAL GATES for this plan (beyond the standard contract):
- Steps 1-7 are ordinary tracked-file edits + a guard: safe to execute on approval, path-scoped, no push.
- Step 8 (clean release) happens only through release-review Section 9 with its own human GO.
- Step 9 (PyPI YANK + git history rewrite + FORCE-PUSH) is destructive and IRREVERSIBLE-ish: it requires a SEPARATE explicit human GO at the moment of execution, is performed by or directly with the human, needs `git-filter-repo` installed (ask the human; do not hand-roll), and must be announced to any other clones/collaborators before the force-push. Never perform Step 9 as part of routine execution.

Recommended next steps:
1. Review this IPD (optionally `/plan-review`; sets `Status: reviewed`). Pin D92 during review. Resolve OQ1-OQ4.
2. On human approval, set `Status: approved` (+ `Approval:`), execute Steps 1-7, run validation, sync docs; commit path-scoped (no push).
3. Coordinate Steps 8-9 as separate human-gated actions.
4. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/` once Steps 1-7 are done and verified (note Steps 8-9 disposition in the Workflow history).

## Workflow history (execution)

- 2026-07-19 approved (repo maintainer): "Approved. Go." for Steps 1-7 (Steps 8-9 remain separately human-gated).
- 2026-07-19 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): Steps 1-7 done. Scrubbed the two shipped-tree leaks and abstracted all tracked docs/plans/prompts/comms/DECISIONS; redacted the second-account and session-id data; gitignored + untracked the run-records dir and gitignored the recovery-dumps dir; added the guard (scanner under `tools/` - deliberately OUT of the shipped tree after the wheel-grep caught that a scanner under `.agents/workflows/` re-ships the token patterns - plus a pre-commit hook, `tests/test_no_personal_paths.py`, and a `test_packaging.py` wheel-token assertion); synced DECISIONS D92 / CHANGELOG / CONTRIBUTING. Validation (actual): `python -m pytest -q` = 271 passed, 1 skipped; `tools/check_personal_paths.py .` exit 0 (tracked tree clean); rebuilt wheel grepped clean of all tokens. This plan was redacted (tokens abstracted) before being committed as this executed record; the unredacted original stays out-of-repo at /tmp/opencode/aw-privacy-cleanup/. Steps 8-9 (PyPI yank of the three releases + `git filter-repo` history rewrite/force-push) NOT done: they await a separate explicit human GO.
