- Id: 9yf5u9
- Status: open
- Set: doctorfix
- Priority: medium
- Work-Kind: bug
- Summary: aw doctor prints an unrunnable rename remediation: 'aw rename <type> <path>' exits 2 without --slug, and with --slug but no --apply it exits 0 having written nothing

## Workflow history
- 2026-09-08 created (aw backlog): aw doctor prints an unrunnable rename remediation: 'aw rename <type> <path>' exits 2 without --slug, and with --slug but no --apply it exits 0 having written nothing

FOUND 2026-09-08 while fixing the `aw doctor` findings on this repo (8 `check.name-nonconformant`
items with truncated slugs). The rule's remediation is the one `aw doctor` and `aw check` present as
the fix, and it cannot be run as printed. Both failure modes were reproduced in a throwaway repo.

THE CODE. `doctor.build_remediation` (`agent_workflows/doctor.py:847-857`):

    if "name-nonconformant" in rule:
        title = "Filename does not match artifact naming grammar"
        target_type = art_type or "plans"
        cmd = f"aw rename {target_type} {loc}"

That string is returned as BOTH `summary_fix` and `command`, so it reaches the human "Fix:" line, the
`--agent` diagnostics, and `resolve_next_actions`.

FAILURE MODE 1, REFUSES (exit 2). `compute_target_name` requires at least one mutation argument
(`artifact_rename.py:107-108`), so the printed command cannot rename anything:

    $ aw rename backlog .aw/records/backlog/open/20260908-demo-01-aaa111-a-truncated-slug-.backlog.md
    error: at least one of --slug, --set, or --order is required to rename
    exit=2

FAILURE MODE 2, THE DANGEROUS ONE (exit 0, writes nothing). Add the missing `--slug` and the command
still only PREVIEWS, because every mutation verb is dry-run by default and the remediation omits
`--apply`:

    $ aw rename backlog .../20260908-demo-01-aaa111-a-truncated-slug-.backlog.md --slug a-truncated-slug-fixed
    --- would rename ... -> 20260908-demo-01-aaa111-a-truncated-slug-fixed.backlog.md ---
    exit=0
    $ ls .aw/records/backlog/open/
    20260908-demo-01-aaa111-a-truncated-slug-.backlog.md      # UNCHANGED

Exit 0 plus a "would rename" line is what an agent reads as success. This is the more severe half:
mode 1 fails loudly and self-corrects, while mode 2 lets an agent truthfully say it ran the fix the
tool recommended, and the finding is still there on the next run. That is the shape of a false
completion claim, produced by the tooling rather than by the agent.

WHY `--slug` CANNOT SIMPLY BE ADDED. The correct slug is a JUDGEMENT, not a derivation. All eight
real cases were slugs truncated mid-word leaving a trailing hyphen (the grammar's
`[a-z0-9]+(?:-[a-z0-9]+)*` cannot end in `-`), e.g.
`...-decide-how-a-begin-receipt-should-behave-when-its-` -> the human must decide it continues
`...-base-goes-stale`. A machine could strip the trailing hyphen, but that leaves a slug ending
mid-thought. So the remediation should NOT pretend to be a one-shot command.

CANDIDATE FIXES, for whoever takes this:

1. Make the remediation HONEST rather than executable: keep `command=None` and put the required shape
   in `detailed_fix` (`aw rename <type> <path> --slug <corrected-slug> --apply`), naming `--slug` as a
   human decision. This is the posture `check.id6-identity-slot` already takes deliberately
   (`doctor.py:787-800`, `command=None` because minting an identity is a judgement call), so there is
   precedent in the same function.
2. If a runnable command is wanted, emit `--apply` and a `<corrected-slug>` PLACEHOLDER, and make
   `resolve_next_actions` treat a placeholder-bearing command as advisory so nothing auto-runs it.
   Note `setid-collision` already emits a `<new-set-id>` placeholder (`doctor.py:825-834`), so the
   placeholder convention exists but nothing marks such a command as not-auto-runnable.

CHECK THE WHOLE FAMILY, not just this rule, since the omission is systematic: `aw rename` and
`aw group` are BOTH dry-run by default and NEITHER remediation includes `--apply`. Audit every
`build_remediation` branch that returns a non-None `command` and confirm the command is runnable
exactly as printed. Also worth checking: `aw index` is declared `mutation_gate="dry_run_default"` in
`command_surface.py:444-452` but actually WRITES by default (its `--check` is the opt-in dry run), so
the declared contract and the behavior disagree in the opposite direction; a fix that assumes
"every mutation verb needs --apply" would get `aw index` wrong.

NOT A REGRESSION AND NOT URGENT: the rule reports correctly and the underlying rename works fine when
invoked properly. What is broken is only the suggested command. Filed rather than fixed inline because
option 1 versus option 2 is a UX call about whether `aw doctor` may print a command a human must edit.
