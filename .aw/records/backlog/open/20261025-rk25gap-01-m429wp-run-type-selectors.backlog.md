- Id: m429wp
- Status: open
- Set: rk25gap
- Priority: medium
- Work-Kind: feature
- Summary: Extend aw <host> run --type to all and named selectors per spec 25kzda 2.3-2.4

## Workflow history
- 2026-10-25 created (aw backlog): Filed 2026-10-25 from the spec audit of 25kzda (maintainer ruling: ungate the spec, file the unbuilt pieces as items).

Spec 25kzda Sections 2.3-2.4 let `--type` scope `all` and named selectors (e.g. `aw oc run all --type spec`, `--type ipd --type spec --type prompt` invoking the mixed-type policy). At HEAD 5db4791c1 `--type` only scopes a needs-review sweep; `--type prompt <file>` refuses citing z7nbn1. Confirm the intended vocabulary (ipd/spec/backlog/prompt/research/release/walkthrough) before building.
