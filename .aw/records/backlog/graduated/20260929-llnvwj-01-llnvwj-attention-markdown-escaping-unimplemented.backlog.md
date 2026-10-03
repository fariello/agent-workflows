- Id: llnvwj
- Status: graduated
- Graduated-To: llnvwj
- Set: llnvwj
- Priority: low
- Work-Kind: chore
- Summary: The attention markdown board emits a descriptive field unescaped, so a pipe or link in a spec Scope reaches the rendered surface raw; spec 8.8 requires deterministic Markdown escaping and nothing implements it

## Workflow history
- 2026-10-01 set (aw backlog): graduated by run run-20260930T053053Z-3200037: qpw45x
- 2026-09-29 created (aw backlog): The attention markdown board emits a descriptive field unescaped, so a pipe or link in a spec Scope reaches the rendered surface raw; spec 8.8 requires deterministic Markdown escaping and nothing implements it

FILED AS THE CARRIER for the Markdown-escaping row in plan `ynhst5` (Set `qbz8i1`), which makes over-length and control-character descriptive values a named finding but adds no escaping to any renderer.

MEASURED 2026-09-29 in a lane at HEAD `f4b00263`, against temporary fixture repositories.

A spec whose `- Scope:` is `a | b | c cell break [link](http://x) ![img](http://y)` is emitted verbatim by `aw attention --details --format markdown` as `      scope: a | b | c cell break [link](http://x) ![img](http://y)`, so the pipes, the link and the image reach the rendered surface unescaped.

WHAT THE GOVERNING CONTRACT REQUIRES: spec `attention-registry-and-cross-tree-status` Section 8.8 states "The Markdown board escapes Markdown metacharacters deterministically so a field cannot break the table, inject a link/image, or start a new block", and its A14 acceptance criterion requires a fixture proving "a Markdown-table-breaking string" is caught. Neither the escaping nor that fixture exists.

SEVERITY IS DELIBERATELY `low`/`chore` RATHER THAN `bug`, and the reason is worth recording so it is not silently upgraded or dismissed. The measured output is a CONTRACT GAP with no demonstrated user-visible breakage yet: the current `--details` markdown renderer emits the detail on its own indented line rather than inside a table cell, so a pipe does not in fact break a table today. The table surfaces (`term.format_table`, used by `aw releases show`) render the PATH and ID columns, not the descriptive field, so the measured payload never reaches a cell. This is therefore a latent defect that becomes user-visible the moment a descriptive field is placed in a table cell, which is why it should be closed rather than dropped.

TWO THINGS WHOEVER FIXES THIS MUST DECIDE, neither of which is settled here: (1) WHICH surfaces escape, since Section 8.8 names the Markdown board specifically while the JSON and `--agent` paths have their own already-implemented escaping (`A.escape_detail` for the `location<TAB>rule<TAB>detail` record); and (2) whether escaping is applied at RENDER time or whether the metacharacter is treated as a contract violation the way over-length and control characters are, because the spec's own text does both (it requires escaping in one bullet and names violations as `--check` failures in F10). Escaping at render is the reading this item assumes, since a pipe in prose is legitimate content in a way an ANSI escape is not.

NOTE `A.escape_detail` IS NOT THE FIX AND MUST NOT BE MISTAKEN FOR IT: it escapes tab, newline and backslash to keep an agent record on one line, and does not touch Markdown metacharacters or C0/C1 control characters.
