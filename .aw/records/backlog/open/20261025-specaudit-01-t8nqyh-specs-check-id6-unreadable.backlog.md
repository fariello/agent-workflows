- Id: t8nqyh
- Status: open
- Blocks-Release: next
- Set: specaudit
- Priority: low
- Work-Kind: bug
- Summary: aw specs check <id6> falsely reports attention.unreadable; it only accepts a file path

## Workflow history
- 2026-10-25 created (aw backlog): Filed 2026-10-25 from the spec audit (session report).

At HEAD 5db4791c1, 'aw specs check c4gd2h' (and 7ckptx, z7nbn1, 25kzda, 89xjll) reports attention.unreadable: cannot read/decode spec, while the same specs pass when checked by full path. Other spec verbs accept an id6. Either resolve the id6 selector or refuse with a clear 'expected a path' usage error. User-perceptible: a false error on a valid spec.
