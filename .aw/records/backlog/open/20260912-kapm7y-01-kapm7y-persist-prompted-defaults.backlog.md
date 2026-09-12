- Id: kapm7y
- Status: open
- Blocks-Release: next
- Set: kapm7y
- Priority: high
- Work-Kind: feature
- Summary: Prompted defaults are not persistable: an interactive choice cannot be saved, so a user is re-asked on every install and the 2.0.0 migration prompt would nag

## Workflow history
- 2026-09-12 created (aw backlog): Maintainer-requested during plan-review of the migleftover Set; blocking on 2.0.0

WHAT IS NEEDED. When aw asks an interactive question whose answer is a POLICY rather than a one-off (migrate this legacy layout? clean up leftovers? which leftover disposition?), it must be able to offer 'remember this choice for future installs' and persist it, so the user is not re-prompted forever. Without it, defaulting a prompt to the behavior we WANT (see below) turns into a nag on every subsequent run, which trains people to type --yes and stop reading.

WHY THIS IS RELEASE-BLOCKING FOR 2.0.0. 2.0.0 gates the breaking .agents/ -> .aw/ namespace migration, and the maintainer's stated intent is to strongly encourage everyone onto the new layout rather than hiding the migration behind a flag a user must read --help to discover. That means the migration prompt should DEFAULT to migrating. The moment a prompt defaults to acting, a persistable answer becomes mandatory: otherwise every install of every repo re-asks a question the user already answered. The two changes belong to the same release.

CURRENT STATE, measured:
- The interactive legacy-migration prompt defaults to NO: cli.py:5256-5259 calls _confirm(term, 'Migrate ... from legacy .agents/ to canonical .aw/ now?', False), and _confirm renders '[y/N]' (cli.py:4799). So today the tool asks whether to do the thing we want and pre-selects 'no'. Compare _confirm_install (cli.py:4875-4878), which already takes a default and documents 'Defaults YES for interactive', so a yes-defaulting prompt is an established pattern in this codebase.
- Non-interactively, and under --yes, the legacy layout is KEPT with a deprecation warning (cli.py:5277-5282, the OQ-01 resolution). Note the consequence: 'aw install --yes' on an old repo does NOT migrate it, so an automated fleet update silently leaves every repo on the deprecated layout.
- There is nowhere to persist such an answer per policy today, but the natural home EXISTS: the user config already carries a 'defaults' section (config.py:702, currently {backup: true, prune: true}) with a ConfigKeySpec (config.py:122-123) and an allowlist gate (config.py:57-61), and 'aw config set' already reaches defaults.backup / defaults.prune (config.py:533-535). So this is an extension of a working mechanism, not new infrastructure.

SCOPE SKETCH (not a design ruling):
1. A reusable 'ask, then optionally remember' prompt helper that writes the answer under 'defaults.<policy>' in the user config, with the usual precedence (explicit flag > saved default > built-in default).
2. Apply it to the legacy-migration question and to the leftover disposition introduced by plan z1yefm.
3. Decide what --yes means for a policy question that has no saved answer. Today --yes means 'keep legacy', which contradicts the 2.0.0 intent; candidates are 'do the encouraged thing' or 'refuse and tell the user to choose once interactively'. This is the sharpest open question and is a maintainer call.
4. Make the saved defaults visible and resettable: they must appear in 'aw config show' and be clearable, or a user who answers once can never change their mind without editing JSON.

RELATED. Plan z1yefm (Set migleftover) adds the '--leftovers keep|remove|defer' flag and keeps 'defer' as the default pending this work; its OQ-01 records the default choice as the maintainer's. This item is what makes a prompted, remembered default the right answer there rather than a flag nobody discovers.
