- Id: bplplj
- Status: open
- Set: bplplj
- Priority: medium
- Work-Kind: followup
- Summary: Wire skill-package emission into the installer run() path across hosts

## Workflow history
- 2026-08-24 created (aw backlog): Wire skill-package emission into the installer run() path across hosts

execset Order 05 (2h7777) proved skill/shim generation at the library level (build_skill_package digest parity + generate_shim_members drift-free) and exposed /exec-set via the existing shim path, but did NOT wire skill-package emission (host_adapters.generate_adapter_bundle / build_skill_package .to_files()) into engine.install_all (which today writes only body_members + shim_members). Wiring skill emission into the installer is a cross-cutting installer-output change touching all hosts + uninstall + idempotency + install-diff tests; it was deliberately kept out of the packaging Order's scope (D21-2h7777-D2). Follow-up: wire it and extend the installer tests.
