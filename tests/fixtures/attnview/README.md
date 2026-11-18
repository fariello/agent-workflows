# attnview fixtures (Set attnview, Order 01)

Deterministic fixtures the attention-view contracts, the `aw specs` verbs (Order 02), and the
`aw attention` scanner (Order 03) test against. Two groups:

- `specs-valid/` is retired from tracked fixtures. The consuming test modules (`tests/test_attention_contract.py`, `tests/test_specs_verbs.py`, and `tests/test_specs_releases_unsafe_field.py`) build one spec per spec native status dynamically with `RecordBuilder.spec(...)` (`tests/record_builder.py`), each mapping to its attention class.
- `violations/` stays literal malformed input, providing one sample per `--check` violation class (each ties to a `RULE_IDS` catalog id).

Some violation classes (unreadable file, unsupported-encoding, symlink-escaping-repo) cannot be
committed as portable text fixtures; they are documented here and simulated in-test:

- `attention.unreadable` simulated by pointing the reader at a path that raises on read.
- `attention.unstable-path` simulated by constructing a symlink whose target escapes a temp repo root
  inside the test (never committed).

These fixtures are contract samples, not a live tree; the scanner (Order 03) runs over the real
`.agents/` trees, not this directory.
