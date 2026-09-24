# .aw/records/specs/

Design specifications and RFC-style documents. This is the `spec` workflow's home for detailed
proposals that are larger than an IPD and describe a design or contract before implementation.

Named `YYYYMMDD-HHMM-NN-<slug>.md` (local time).

Specs describe intended design and rationale. When a spec is implemented, the implementation plan
(IPD) and its walkthrough carry the execution record; the spec remains as the design reference.

## Status subdirectories and layout

Specs are partitioned into status subdirectories reflecting their lifecycle state. The directory
location always agrees with the spec `- Status:` front-matter enum:

- `draft/`: Initial spec draft in progress.
- `to-review/`: Ready for peer or maintainer review.
- `reviewed/`: Review completed and signed off.
- `approved/`: Approved by human attestation (ready for implementation).
- `implementing/`: Currently being implemented by an active plan Set.
- `implemented/`: Terminal state; implementation verified and completed.
- `deferred/`: Blocked on a decision or external condition (carries typed `- Gate-Kind:` and `- Gate-Ref:`).
- `parked/`: Inactive or paused indefinitely.
- `superseded/`: Terminal state; superseded by a successor design specification.

Location agrees with status. The status setters (`aw specs set <path> --status <enum>` and `aw set <status> <selector>`)
automatically relocate the file to the matching directory upon status transition.


SETID LENGTH IS BOUNDED (catalog invariant I-17, spec `2lcqno` N8). A setid of 14 characters or
fewer is strongly preferred, a setid over 14 characters is a WARNING, and a setid over 24 characters
is REFUSED: the `--set`-taking verbs (`aw ipd scaffold`, `aw backlog new`, `aw research new`,
`aw group`) reject an over-length value, and `aw check` reports `check.setid-length-warn` /
`check.setid-length-error`. Grandfathering is PER ARTIFACT against the `cutovers.setid_length`
boundary stamped into `.aw/config/project.json` on install or update, so an artifact older than that
boundary keeps its long setid while a NEW artifact is judged. The intended consequence is that a new
artifact may NOT join an existing long-setid topic after the cutover; regroup the topic under a
shorter setid instead.

## Status and history (owned by `aw specs`)

Every spec carries a machine-legible, single-line bare-enum `- Status:` front-matter bullet (no
trailing prose; put rationale in history) and a `## Workflow history` section. The closed status enum
and its cross-tree attention class (see `aw attention`):

`draft` (ready) -> `to-review` (ready) -> `reviewed` (ready) -> `approved` (ready) -> `implementing`
(active) -> `implemented` (done); plus `deferred` (blocked, MUST carry a typed `- Gate-Kind:` +
`- Gate-Ref:`), `parked` (parked), and `superseded` (parked). Authority is tracked separately with an
optional `- Canonical: true` (a spec can be authoritative and unimplemented); `canonical` is NOT a
status.

## What a spec graduated into (`- Graduated-To:`)

A spec may carry an optional `- Graduated-To: <setid>[, <setid>...]` bullet naming the plan Set or Sets
it became, so a spec-first graduation is machine-readable from the spec end as well as from the plan
end. Write it with the setter rather than by hand:

```sh
aw spec set implementing <id6> --graduated-to <setid>
```

It is the FORWARD half of the same link a plan records backwards as `- From-Spec: <spec-id6>`. The two
directions are shaped differently on purpose: a plan names the ONE spec it came from, while a spec names
the whole Set it generated (an orchestrator plus its children), which no single plan id6 could name.

The field is OPTIONAL and MULTI-VALUED, because a spec may spawn more than one plan Set over its life:
separate setids with commas, and pass `-` to clear. `aw check all` reports an entry naming no real plan
Set (`check.graduated-to-dangling`), a value that is not a valid setid (`check.graduated-to-malformed`),
and a repeated setid (`check.graduated-to-duplicate`, a warning). A setid resolves if any plan carries it
in any lifecycle directory, terminal ones included, so the link keeps resolving once the work is done.
Backlog items carry the same field; see `.aw/records/backlog/README.md`.

Do NOT hand-edit the status or history. Use the owner verbs (they validate the transition, the
anti-self-approval floor, and typed gates, then write atomically and relocate): `aw spec set <status> <id6|setid|fname>...`
(or `aw specs set <path> --status <enum> [--message <text>]`; an agent records human approval with
`--by-human` as an explicit attested speed bump, and may not set `implemented` without a resolvable
evidence citation), `aw specs note <path> --message <text>` (history only), and `aw specs check [path]`
(validate; fail closed). `aw attention` surfaces every spec's attention class across the repo.
See `aw specs --help` and `aw attention --help`.
