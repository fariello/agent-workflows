# .aw/records/specs/

Design specifications and RFC-style documents. This is the `spec` workflow's home for detailed
proposals that are larger than an IPD and describe a design or contract before implementation.

Named `YYYYMMDD-HHMM-NN-<slug>.md` (local time).

Specs describe intended design and rationale. When a spec is implemented, the implementation plan
(IPD) and its walkthrough carry the execution record; the spec remains as the design reference.

## Status and history (owned by `aw specs`)

Every spec carries a machine-legible, single-line bare-enum `- Status:` front-matter bullet (no
trailing prose; put rationale in history) and a `## Workflow history` section. The closed status enum
and its cross-tree attention class (see `aw attention`):

`draft` (ready) -> `to-review` (ready) -> `reviewed` (ready) -> `approved` (ready) -> `implementing`
(active) -> `implemented` (done); plus `deferred` (blocked, MUST carry a typed `- Gate-Kind:` +
`- Gate-Ref:`), `parked` (parked), and `superseded` (parked). Authority is tracked separately with an
optional `- Canonical: true` (a spec can be authoritative and unimplemented); `canonical` is NOT a
status.

Do NOT hand-edit the status or history. Use the owner verbs (they validate the transition, the
anti-self-approval floor, and typed gates, then write atomically): `aw specs set <path> --status
<enum> --message <text>` (an agent records human approval with `--by-human` as an explicit attested
speed bump, and may not set `implemented` without a resolvable evidence citation), `aw specs note
<path> --message <text>` (history only), and `aw specs check [path]` (validate; fail closed). `aw
attention` surfaces every spec's attention class across the repo. See `aw specs --help` and `aw
attention --help`.
