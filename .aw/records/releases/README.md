# .aw/records/releases/

Release records: thin ship-gate anchors. A release record (`<...>.release.md`) names a planned release
(Version or `next`), its Status (planned/blocked/shipped), and a Summary. Items declare they gate a
release via a `Blocks-Release:` field (see AGENTS.md). This is a COMMITTED ship gate, distinct from
roadmaps (possibilities).

Named by the uniform artifact-naming grammar with the release facet:
`YYYYMMDD-<setid>-NN-<id6>-<slug>.release.md` (a standalone release uses its id6 as the setid, NN=01).

Managed by `aw` (do not hand-edit status/history; use the aw verbs).

## The `aw releases` owner verb

Read and create release records with the `releases` owner verb (alias `release`):

```sh
aw releases                     # list every release record (bare = list)
aw releases list                # the same, explicitly
aw releases show                # the planned release + everything gating it (defaults to 'next')
aw releases show f33nrj         # a specific release, by id6, version, or filename
aw releases new --version 2.1.0 --summary "why this release exists"          # preview only
aw releases new --version 2.1.0 --summary "why this release exists" --apply  # write it
```

`aw releases show` lists the LIVE items declaring `Blocks-Release` against that release. That blocker
set is the SAME one `aw attention` reports (both read it through one shared function), so the two views
cannot disagree.

`new` is preview-by-default: without `--apply` it writes nothing and prints the exact record it would
create. All three subcommands support `--json` (full structured JSON) and `--agent` (`aw.agent/v1`
JSONL); they exit 0 when clean and 2 on a usage error such as an unresolvable selector.

To VALIDATE release records, use `aw check releases`. There is deliberately no `releases check`
subcommand: a second validation entry point could drift from the canonical one.

## Release succession and the 'next' sentinel

Exactly one release record should carry `- Status: planned` at a time. The `next` sentinel resolves only in that state. When two or more records are planned, `next` is ambiguous; when zero are planned, `next` is unresolvable and every sentinel-gated record risks dangling.

Therefore, shipping a release requires two coordinated actions in the same change: mark the outgoing record `shipped` via `aw set shipped <id6>` and create its successor record with `aw releases new --version <X.Y.Z> --summary ... --apply`. The tooling enforces this sequence: `aw set shipped` refuses if it would leave zero planned releases unless an explicit attested override is passed.
