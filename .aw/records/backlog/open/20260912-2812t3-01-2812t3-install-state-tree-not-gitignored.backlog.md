- Id: 2812t3
- Status: open
- Blocks-Release: next
- Set: 2812t3
- Priority: high
- Work-Kind: bug
- Summary: aw install left .aw/state/ and .aw/config/local.json untracked-and-unignored in target repos, offering machine paths (aw_home) to git add

## Workflow history
- 2026-09-12 created (aw backlog): aw install left .aw/state/ and .aw/config/local.json untracked-and-unignored in target repos, offering machine paths (aw_home) to git add

## Reported and FIXED 2026-09-12 (filed for the record, per the carrier rule)

The maintainer reported six files left "uncommitted, untracked, and not ignored" after `aw install`,
and asked whether they were all supposed to be committed. FIVE OF THEM WERE NOT, so the fix is the
opposite of the reported assumption; the item exists so the reasoning is durable rather than living in
one conversation.

## What was wrong

`engine._AW_GITIGNORE_TEMPLATE` (fresh install) and `engine._ensure_aw_gitignore` (the ONLY path that
reaches an already-installed repo) both covered `records/*/untracked/`, `records/runs/`, `/inbox/`,
the generated `system/layout*.json` and the four `INDEX.*` manifests, but had NO entry for the
`state/` tree or for `config/local.json`. `install_wizard.persist_project_policy` writes
`config/project.json`, `config/local.json`, `state/durable/install.json` and an appended
`state/durable/history/installs.jsonl`, so every managed repo offered those to `git add -A`.

## Why they must stay untracked, which is the part worth keeping

`state/durable/install.json` embeds the RESOLVED POLICY, including `aw_home`, an ABSOLUTE HOME PATH,
and the `installs.jsonl` history appends one such snapshot per install. Measured on a real file with
the shipped sanitizer:

    $ python3 -m agent_workflows check-local-leaks <tmp> --agent
    "findings":2, "diagnostics":[{"location":"install.json:11","rule":"home-path"},
                                 {"location":"install.json:11","rule":"handle"}], "exit":1

So committing them publishes the operator's home directory and username into permanent git history
(D92). This repository already encodes exactly that in its OWN root `.gitignore` (`.aw/state/`,
`.aw/config/local.json`), which is the authority for the intent; target repos simply never inherited
it. Spec `kw5y2s` Section 4.2/10 draws the same line: `config/project.json` is PORTABLE, `local.json`
is machine-local and untracked.

`config/project.json` is the ONE exception and IS meant to be committed. An over-broad `/config/`
pattern would silently stop shipping project policy, which is why there is a test asserting it stays
trackable.

## The fix

Both the template and the back-fill list gained two ANCHORED patterns, `/state/` and
`/config/local.json`. Anchored for the reason the `/inbox/` comment records: a bare `state/` matches at
any depth and would swallow an unrelated nested directory. This repo's own `.aw/.gitignore` was
re-synced to the template, which an existing guard test (`test_template_and_this_repos_own_gitignore_agree`)
caught as divergent.

New `MachineLocalStateGitignoreTests` in `tests/test_engine_install.py` covers: the template carries
both patterns; a fresh install ignores all five paths IN EFFECT via real `git check-ignore`; the
back-fill reaches an already-installed repo (with a precondition asserting the pre-fix state);
idempotency across repeated calls; the anchoring guard; that `project.json` stays trackable; and a
PREMISE test asserting the snapshot really does still carry an absolute `aw_home`, so the rationale
cannot quietly become false while the rule remains.

## Note for whoever reads this later

Already-installed repos pick the patterns up on their NEXT `aw install`/update, since that is when
`_ensure_aw_gitignore` runs. Until then those files keep showing as untracked in that repo; they were
never committed there, so nothing needs unwinding. If a repo DID commit them, that is a history-leak
cleanup and needs its own item.
