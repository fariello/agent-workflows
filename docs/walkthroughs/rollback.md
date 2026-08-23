# Walkthrough: roll back safely

Goal: from a clean state, roll back an adapter update cleanly, and see the tool refuse an unsafe
data-schema downgrade rather than corrupting data.

## A safe adapter rollback

The `rollback` lifecycle fixture installs into an isolated repo and then performs a pure adapter
rollback:

```
python3 -c "from agent_workflows import lifecycle_fixtures as lf; \
o = lf.run_fixture('rollback'); \
print('adapter rollback safe:', o.passed, '|', o.evidence)"
```

Expected output: the rollback is classified as an adapter rollback, it is safe, and it reverses
cleanly with no record loss.

## An unsafe downgrade is refused, not performed

The `downgrade-warning` fixture seeds a runtime record written by a newer schema than the older
version can read, then attempts a rollback:

```
python3 -c "from agent_workflows import lifecycle_fixtures as lf; \
o = lf.run_fixture('downgrade-warning'); \
print('refused:', o.evidence['status'] == 'refused'); \
print('warnings:', o.evidence['warnings']); \
print('repo mutated:', o.mutated)"
```

Expected output: the rollback is refused, a warning names the unreadable future data, and the
repo was NOT mutated. The future data is left intact, never truncated.

## The corresponding operator behavior

Against a real repo, `compat_migration.CompatRollback.assess` classifies the rollback and
`rollback` refuses a data-schema downgrade unless you explicitly opt in with full knowledge that
the future data becomes unreadable by the older version (see [../recovery.md](../recovery.md)).

## Release actions are separate

Rolling back an install is reversible and safe. Tagging, publishing, deploying, or pushing a
release is NOT part of this or any command here; it is a separately authorized action
(`RELEASING.md`).
