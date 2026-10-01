# IPD: Escape Markdown metacharacters in the attention board's detail line, the one surface that renders an untrusted descriptive field

- Date: 2026-10-01
- Kind: child
- Concern: Spec `attention-registry-and-cross-tree-status` Section 8.8 requires that "The Markdown board escapes Markdown metacharacters deterministically so a field cannot break the table, inject a link/image, or start a new block", and its A14 criterion requires a fixture proving a "Markdown-table-breaking string" is caught. NOTHING in the codebase implements either: a search for `md_escape`/`escape_markdown`/`escape_md`/`markdown_escape`/`_MD_ESCAPE` finds no definition, and the only Markdown-metacharacter escaper in the tree is `review_findings._row`, which belongs to a different surface. Measured in this lane: `attention._render_item_row` interpolates `it.detail_text` into its detail line with no transformation at all, so a spec whose `- Scope:` is `a | b | c cell break [link](http://x) ![img](http://y)` reaches the board verbatim. A second, worse half is measured below: the SAME line emits raw C0 control characters, which Section 8.8's own "The renderers never emit raw control characters" forbids absolutely.
- Scope: Add ONE deterministic Markdown escaper to `attention_contract` and apply it to `detail_text` at the three board detail-emission sites in `attention.py`, plus a control-character neutralizer applied at the same sites. Add the A14 fixture that does not exist. EXCLUDES the JSON and `--agent` surfaces (measured already safe) and excludes making a metacharacter a `--check` violation.
- Scope-Paths: agent_workflows/attention_contract.py, agent_workflows/attention.py, tests/test_attention_output_safety.py, .aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: llnvwj
- Set: llnvwj
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: qpw45x

## Workflow history

- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `llnvwj`. Both questions the item left open are RESOLVED from repository evidence rather than deferred (see OQ-01 and OQ-02): the escaping surface is the board's detail line only, because the JSON and `--agent` paths were measured already safe; and the policy is ESCAPE AT RENDER rather than a `--check` violation, because 7.0 percent of the live corpus (197 of 2820 extracted details) carries a character in the candidate escape set and 883 of 2820 already exceed `MAX_DESCRIPTIVE_LEN`, so a violation-only reading would fail a clean checkout en masse. Authoring also found a defect STRICTLY WORSE than the one the item reports and folded it in as E-03: the same three sites emit raw ANSI, violating Section 8.8's absolute "never emit raw control characters", and the sibling plan `ynhst5`'s metadata-region bound cannot close it.
- 2026-10-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the one `aw attention` surface that renders an untrusted descriptive field emit it as inert text: a Markdown metacharacter cannot break a table, inject a link or image, or start a new block, and a control character cannot reach a terminal at all. Close the Section 8.8 escaping bullet and ship the A14 fixture that was specified and never written.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the two pure transforms

- [ ] E-01 In `agent_workflows/attention_contract.py`, add `neutralize_control_characters(value: str) -> str`, which replaces every character matching the EXISTING `_CONTROL_CHAR_RE` (`[\x00-\x1f\x7f-\x9f]`) with U+FFFD. Place it beside `escape_detail` at the end of the output-safety region, and reuse `_CONTROL_CHAR_RE` rather than writing a second character class.
  REUSING THE EXISTING REGEX IS THE POINT, not a convenience. `is_safe_descriptive` already decides what a control character IS, and a second class here could disagree with the predicate, producing a value the checker calls unsafe and the renderer calls clean (or the reverse). One definition, two readers.
  U+FFFD AND NOT DELETION, following the in-repo precedent `run_analytics_spa.sanitize_control_characters`, which "replaces Unicode `Cc`/`Cf`/`Cs`/`Co` with U+FFFD". A visible replacement character tells the reader that something was removed; silent deletion makes a tampered value look clean, which is the failure mode this whole section exists to prevent.
  DO NOT WIDEN TO THE UNICODE `Cf`/`Cs`/`Co` CATEGORIES that the SPA helper covers. Section 8.8's own words bound this to "Any C0/C1 control character (including ANSI escape sequences, NUL, and bidi controls)", and `_CONTROL_CHAR_RE` is the contract's existing reading of that sentence. Widening it here would silently diverge the renderer from `is_safe_descriptive` in the opposite direction, and bidi controls (U+202A..U+202E, which are `Cf` and NOT in the C0/C1 range) are a real gap worth closing DELIBERATELY in its own change; record that gap in OQ-05 rather than closing it as a side effect.
  - Depends on: none
  - Expected outcome: `A.neutralize_control_characters("red \x1b[31mX\x1b[0m")` returns `"red \ufffd[31mX\ufffd[0m"`; the function is pure, has no I/O, and `A.is_safe_descriptive` is unchanged byte for byte.
  - Execution state: pending

- [ ] E-02 In the same module, add `escape_markdown_inline(value: str) -> str`, escaping with a leading backslash EXACTLY these five characters, in this order: `\` FIRST, then `|`, `[`, `]`, `<`. Document the measured reason for each inclusion and each exclusion in the docstring.
  THE BACKSLASH MUST BE ESCAPED FIRST OR THE SCHEME IS AMBIGUOUS. If `|` were escaped before `\`, the input `\|` would become `\\|` by two different routes and a reader could not tell an authored backslash from an inserted one. `escape_detail`'s own `_AGENT_ESCAPES` table already orders `("\\", "\\\\")` first for this exact reason; follow it.
  WHY THESE FIVE AND NOT THE FULL COMMONMARK SET, argued from F-11 and F-12 rather than from taste. `|` is the table breaker Section 8.8 names first and `review_findings._row` already escapes it for the same reason. `[` and `]` are the link and image syntax Section 8.8 names second; escaping the brackets defeats `[x](y)` and `![x](y)` without needing to escape `!`, which appears in only 5 values. `<` is escaped because 133 values carry an HTML-tag-shaped `<...>` that a Markdown renderer may pass through as raw HTML, which is the "inject" half of the same sentence. `\` is escaped for unambiguity per the paragraph above.
  DELIBERATELY NOT ESCAPED, each with its measurement: backtick (1002 values, and ZERO have an odd count, so no value opens an unterminated code span); `_` (1063 values, the single largest population, and intraword emphasis is a cosmetic artifact rather than an injection); `*` (74 values, 57 with an odd count, same cosmetic reasoning); `#` and `>` (43 and 187 values) are "start a new block" risks ONLY at the START of a line, and F-7 measures that the detail text is never at line start (it follows a fixed six-space indent and a `tag: ` prefix, and six spaces is itself an indented-code context in which `#` is inert). Escaping all of these would backslash-litter the majority of the live corpus for no gain on this surface. A reviewer who disagrees should attack this list first; it is the plan's main judgement call and OQ-03 names the cost.
  THIS IS NOT A COMMONMARK-CORRECT ESCAPER AND MUST NOT BE NAMED AS ONE. Say so in the docstring. It is a targeted inline-context transform for one known surface, which is what the stdlib-only constraint permits (no Markdown library is importable; see Step 0).
  - Depends on: none
  - Expected outcome: given the input `a | b [l](u) ![i](v) <tag> back\slash`, the function returns `a \| b \[l\](u) !\[i\](v) \<tag> back\\slash` (note that the CLOSING `>` is NOT escaped, because `>` is not a member of the five-character set; only the opening `<` is). A value containing none of the five characters is returned unchanged, and a backtick, `_`, `*`, `#` or `>` in the input is returned unchanged.
  - Execution state: pending

### Task group 2: apply at the three emission sites

- [ ] E-03 In `agent_workflows/attention.py`, apply BOTH transforms to `it.detail_text` at the THREE detail-emission sites F-2 names, with the control-character neutralizer applied FIRST and the Markdown escape second. The sites are the `if colored:` detail line in `_render_item_row`, the uncolored detail line in `_render_item_row`, and the detail line in `_render_table_row`.
  ORDER IS LOAD-BEARING: neutralize, THEN escape. Run the other way, the escaper inserts backslashes around a value that still contains an ESC byte, and a `\x1b` adjacent to an inserted `\` is exactly the ambiguity the first-position backslash rule exists to remove. Neutralizing first means the escaper only ever sees control-character-free text.
  ESCAPE BEFORE COLORING, NOT AFTER, at the colored site. The current code is `detail_txt = term.color256(it.detail_text, 250)`. Transform the raw value and pass the RESULT to `color256`; do not transform the colorized string, or the neutralizer will eat the ANSI bytes `color256` itself just added and the detail will lose its styling. This is the one site where getting the order wrong produces a plausible-looking but wrong result, which is why it is called out rather than left to the executor.
  TRANSFORM ONLY `detail_text`, NOT `detail_kind`. The tag comes from the closed cascade in `_extract_detail` (`summary`/`scope`/`concern`/`question`/`title`), so it is tool-generated and not untrusted input; escaping it would add churn with no threat model behind it.
  DO NOT TOUCH THE GATE-REF PATH in either function. Those three `A.escape_detail(...)` calls are correct for what they do and are a different field with a different validator (`validate_gate_ref`); F-10 confirms the gate ref is separately handled, and the corpus carries ZERO gate refs today (measured: `GATE_REF_RE` finds none), so changing it would be unverifiable churn.
  DO NOT CHANGE `render_json` (F-8: already safe via `ensure_ascii=True`) and DO NOT CHANGE the `--agent` path (F-9: it does not carry `detail_text`). Touching either would break the byte-identical-output criterion A6 for a consumer that has no defect.
  - Depends on: E-01, E-02
  - Expected outcome: the F-1 hostile value rendered through the uncolored `_render_item_row` contains `\|` and `\[` and no bare `|`; the F-3 ANSI value rendered through the same path contains U+FFFD and NO `\x1b` or `\x07` byte; the colored path still contains the `\x1b[38;5;250m` sequence that `color256` adds; and `_render_table_row` behaves identically to the uncolored row path on the same input.
  - Execution state: pending

- [ ] E-04 Make `--format markdown` a COLOR-FREE surface, by forcing `colored` false on that branch of `attention.run`, so the flag Section 8.1 names as the Markdown board cannot emit ANSI (F-6).
  THIS IS THE SMALLEST CHANGE THAT MAKES THE SPEC SENTENCE TRUE, and it is deliberately not a new renderer. F-5 measures that `--format markdown` is byte-identical to the default board today and that `attention.py` contains no occurrence of the string `markdown` at all. Building a distinct Markdown renderer would be a far larger change whose output no consumer has asked for; forcing color off makes the existing board text valid Markdown-safe output under the flag that promises it.
  THE DEFAULT BOARD'S TTY BEHAVIOR MUST NOT CHANGE. A human running bare `aw attention` in a terminal still gets the colored board; only the EXPLICIT `--format markdown` loses color. Verify this rather than assuming it: the default path reads `color = False if getattr(args, "no_color", False) else None` and then `colored = bool(getattr(term, "color", False))`, so the change must key on `fmt == "markdown"` specifically and leave the `no_color`/TTY resolution otherwise intact.
  THIS ALSO MAKES THE FLAG HONEST ABOUT DETERMINISM. Criterion A6 requires byte-identical Markdown output across environments; a surface whose bytes depend on `FORCE_COLOR` cannot satisfy that, so this item closes an A6 gap as well as an 8.8 one. Say so in the item's commit message.
  - Depends on: none
  - Expected outcome: `FORCE_COLOR=1 python3 -m agent_workflows attention --format markdown --details` emits ZERO `\x1b` bytes, where it currently emits many; bare `aw attention` on a TTY is unchanged; and `aw attention --no-color --details` is byte-identical to `aw attention --format markdown --details`.
  - Execution state: pending

### Task group 3: the A14 fixture that was specified and never written

- [ ] E-05 Add `tests/test_attention_output_safety.py`, a NEW behavioral module that drives the REAL renderers and asserts on their REAL output strings, covering: the F-1 table-breaking value, the F-3 ANSI/BEL value, a link-and-image value, an HTML-tag value, a backslash value, and a benign value that must pass through UNCHANGED.
  ASSERT ON RENDERER OUTPUT, NEVER ON SOURCE STRUCTURE. The repository's 2026-09-26 ruling and GUIDING_PRINCIPLES P16 forbid tests that read production source with `inspect`/`ast`/regex or assert on symbol censuses; `tests/test_attention_contract.py::test_output_safety` is also NOT the model to copy, because it exercises `is_safe_descriptive` as a predicate and proves nothing about any renderer, which is precisely how this gap survived (F-13). Build `att.Item` values and call `att.render_board`, `att._render_item_row` and `att._render_table_row`, following the existing style of `tests/test_attention.py::test_detail_cascade_and_rendering`.
  THE BENIGN PASS-THROUGH CASE IS NOT OPTIONAL. Without it the suite would stay green if the escaper escaped EVERYTHING, which would be a regression dressed as a fix. Assert that a value with no member of the escape set renders byte-identically to today's output.
  INCLUDE AN END-TO-END CASE THROUGH `att.run`, in the style the existing test already uses (a `tempfile.TemporaryDirectory` repo plus an `argparse.Namespace` with `details=True`, `no_color=True`), so the assertion covers the real command path and not only the two helpers. This is what makes the A14 claim "a Markdown-table-breaking string is caught" true of the SHIPPED surface.
  ADD THE `--format markdown` NO-ANSI CASE for E-04 in this same module, asserting no `\x1b` byte appears in that surface's output with color forced on.
  NAME THE CRITERION IN THE TEST. Reference A14 and Section 8.8 in the module docstring so the next reader can tell this module discharges a named acceptance criterion rather than being incidental coverage.
  - Depends on: E-03, E-04
  - Expected outcome: a new test module whose cases FAIL against the pre-E-03 code (demonstrate this by stashing the E-03 change or by a one-line local revert, and paste both the failing and passing runs) and pass after; and the full suite is green.
  - Execution state: pending

### Task group 4: record the contract and the change

- [ ] E-06 Amend the spec Section 8.8 Markdown-escaping bullet to state the MEASURED escape set and the surface it applies to, and record that `--format markdown` is the default board rendered color-free rather than a separate renderer. Add a dated amendment note in the spec's own style. Also add a `CHANGELOG.md` entry.
  THE SPEC EDIT IS DECLARED IN `- Scope-Paths:` DELIBERATELY, per the AGENTS.md rule that a plan amending a spec must list the `.spec.md` file so the runner announces it before the run starts and reconciles it at the end. The spec is `Status: implemented`, and this amendment makes an unimplemented bullet implementable rather than relaxing a shipped contract: it NARROWS "escapes Markdown metacharacters" to the five characters F-12 measured as load-bearing, and it does NOT weaken the absolute control-character prohibition, which E-01 and E-03 strengthen from unimplemented to enforced.
  SAY WHY THE NARROWING IS HONEST, in the amendment text itself. The original bullet is unbounded ("Markdown metacharacters"), and F-11/F-12 measure that an unbounded reading would backslash-litter the majority of the live corpus while adding no safety on a surface that has no machine reader. Record the three characters deliberately left unescaped (`` ` ``, `_`, `*`) with their counts, so a future reader sees a decision rather than an omission.
  DO NOT CHANGE A14's TEXT. The criterion is correct as written and E-05 now satisfies it; editing a criterion to match what was built is the failure mode the no-forged-attestation rule exists to prevent.
  DO NOT TOUCH `- Status:` OR THE SPEC'S `## Workflow history` as a lifecycle act. This is a content amendment, not a transition; appending a dated amendment note in the body style the spec already uses is correct, and running `aw specs set` here would assert a lifecycle event that did not happen (the same reasoning `ynhst5` E-01 records for its hand repair).
  - Depends on: E-03, E-04
  - Expected outcome: Section 8.8's escaping bullet names the five escaped characters, the three deliberately-unescaped ones with their measured counts, and the `--format markdown` relationship to the default board; `CHANGELOG.md` carries one entry; and `aw check` reports no new finding on the amended spec.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE REPOSITORY ALREADY HAS A MARKDOWN-CELL ESCAPER AND ITS DESIGN IS THE PRECEDENT TO FOLLOW, not to duplicate. `review_findings._row` escapes exactly `|` and newline, with the comment "A cell containing a raw `|` would silently split into two columns, so escape it", and `review_findings._split_row` is its matching READER that honors the `\|` escape. That pairing is the convention: an escape that a reader must undo is round-trippable by construction. The board has NO machine reader (it is the human surface; machines take `--format json` or `--agent`), which is what makes a non-round-trippable escape acceptable HERE and is stated in OQ-03 so a reviewer can attack it.
- PER-SURFACE ESCAPING IS AN ESTABLISHED FAMILY, not a new idea: `run_analytics_spa` ships `escape_text`, `escape_attribute`, `escape_svg_text`, `escape_js_string` and `escape_json_for_script` as five surface-specific functions, plus `sanitize_control_characters`, which replaces Unicode `Cc`/`Cf`/`Cs`/`Co` with U+FFFD. The new escaper is the Markdown member of that family and the control-character neutralizer has a direct in-repo precedent, so neither is novel policy.
- STDLIB ONLY (spec requirement N1, "Stdlib only; zero runtime deps (D46); Python 3.9"). Confirmed in this lane that no Markdown library is importable: `import markdown`, `import commonmark` and `import mistune` each raise `ModuleNotFoundError`. So the escaper is a character-level transform, and this plan does NOT attempt a CommonMark-correct implementation (see OQ-04).
- THE BOARD'S OUTPUT IS BYTE-DETERMINISTIC BY CONTRACT (Section 8.5, requirement N5, criterion A6: "Two runs over identical source bytes produce byte-identical JSON, Markdown, and agent output"). A table-driven pure function satisfies this trivially; anything locale-, width- or environment-sensitive does not. The escaper therefore takes a string and returns a string with no reference to terminal width, `TZ` or `LANG`.
- COLUMN PADDING IS DONE BY RENDERED WIDTH, NEVER BY `len()`: `attention._render_item_row` carries the comment "PADDED BY VISIBLE COLUMNS (Section 9.4), never by `len()` on styled text" and uses `term.visible_width`. This matters here because escaping LENGTHENS a value, and F-7 below measures why that is nevertheless safe at these three sites specifically.

## Findings

All findings were driven in this lane. Each is reproducible with the command or snippet given.

| Id | Finding | Evidence |
|---|---|---|
| F-1 | The item's reported defect reproduces EXACTLY. `attention._render_item_row`'s uncolored branch builds its detail line by direct interpolation, and the hostile value survives byte for byte. | Constructing an `att.Item` with `detail_kind="scope"` and `detail_text="a \| b \| c cell break [link](http://x) ![img](http://y)"` and calling `att._render_item_row(it, A.READY, T.Term(color=False), False, False, details=True)` returns `'- [specs] ... (to-review)\n      scope: a \| b \| c cell break [link](http://x) ![img](http://y)'`. The pipes, the link and the image are present unchanged. NOTE FOR THE EXECUTOR: the pipes are written `\|` in THIS table cell only, because a bare `|` here would split the cell (which is the very defect being reported); the actual fixture value contains BARE pipes. |
| F-2 | There are THREE emission sites, not one. The item names the uncolored board line; the colored board branch and the columnar table row each repeat the same unescaped interpolation. | `attention._render_item_row` contains both an `if colored:` detail line (`line += f"\n      {tag_txt} {detail_txt}"`, where `detail_txt = term.color256(it.detail_text, 250)`) and an uncolored one (`line += f"\n      {tag}: {it.detail_text}"`); `attention._render_table_row` contains a third (`row_line += f"\n      {tag_txt} {detail_txt}"`). All three read `it.detail_text` directly. |
| F-3 | **A STRICTLY WORSE DEFECT THAN THE ONE FILED: the board emits RAW ANSI.** Section 8.8 states flatly "The renderers never emit raw control characters", with no escaping-versus-violation ambiguity, so this half is an unconditional contract breach rather than a latent one. | With `detail_text = "red \x1b[31mANSI\x1b[0m and newline-free \x07bell"`, the uncolored `_render_item_row` returns a line containing the literal `\x1b[31m` and `\x07` bytes. `A.is_safe_descriptive` on that same value returns `False`, so the contract KNOWS the value is unsafe and the renderer emits it anyway. |
| F-4 | The sibling plan `ynhst5` CANNOT close F-3, and says so itself, which is why this plan owns it. `ynhst5` bounds its checker read to the metadata region, while the renderer's extractor reads the WHOLE document. | `attention._FIELD_PATTERNS` is `("scope", re.compile(r"(?mi)^-\s*Scope:\s*(.+)$"))` with no metadata bound, and `attention._extract_detail` searches the whole text. Driven: a spec with NO metadata `- Scope:` but a body `- Scope: red\x1b[31mINJECTED\x1b[0m` after a `## ` heading yields `att._extract_detail(...) == ('scope', 'red \x1b[31mINJECTED\x1b[0m')`. `ynhst5`'s own E-02 records this: "the CHECKER and the RENDERER read different regions ... which is a renderer-side divergence carried by `llnvwj`". |
| F-5 | **`--format markdown` IS NOT A SEPARATE RENDERER; it is byte-identical to the default board.** `attention.run` reads `fmt` once and tests it once, for `json` only, so `markdown` falls through to the board path. | `rg -n "markdown" agent_workflows/attention.py` returns NOTHING. The only `fmt` test is `if fmt == "json" or ctx.is_json:`. Driven: `python3 -m agent_workflows attention --no-color --details` and the same command with `--format markdown` produce IDENTICAL bytes (346347 each). The CLI accepts the flag (`choices=("markdown", "json")`). |
| F-6 | **`--format markdown` emits raw ANSI when color is forced**, because the fall-through inherits the board's TTY-derived color decision instead of being a color-free surface. This is F-3 reached through the exact flag Section 8.8 names. | `FORCE_COLOR=1 python3 -m agent_workflows attention --format markdown --details` emits `^[[1;38;5;220m` sequences and `^[[38;5;250m`-wrapped detail text (shown via `cat -v`). The spec names `--format markdown` as a surface in Section 8.1 ("`aw attention` / `--format markdown`: the human board"). |
| F-7 | Escaping the detail text CANNOT corrupt column alignment at these three sites, which is what makes the change safely local. The detail is emitted on its OWN continuation line after `\n`, at a fixed six-space indent, and is the LAST thing on that line; no padding is computed from it. | `cat -A` on the board shows detail lines as `      summary: ...$` on their own line. In all three sites the detail is appended as `f"\n      {tag}: {...}"` after the row is fully assembled, so none of the `visible_width` pads in `_render_item_row`/`_render_table_row` read it. |
| F-8 | The JSON surface is ALREADY SAFE and must not be touched. `attention.render_json` serializes with `ensure_ascii=True`, so a control character becomes a `\uXXXX` escape, and a pipe or bracket inside a JSON string value is inert. | Driven: `att.render_json([it], [])` on the F-3 value emits `"detail_text": "red \\u001b[31mANSI\\u001b[0m and newline-free \\u0007bell"`. On the F-1 value it emits the pipes inside a quoted JSON string, which no JSON consumer can misread as a table. |
| F-9 | The `--agent` surface DOES NOT CARRY `detail_text` AT ALL in its emitted record, so it needs no change either. The `data={"items": [...]}` mapping is built but the renderer does not emit it by default. | `python3 -m agent_workflows attention --agent` emits a `result` line whose keys are exactly `cmd, complete, diagnostics, evidence, exit, findings, kind, next, outcome, schema, verified`; there is no `data` key, and `--fields data` yields an envelope with no item payload. |
| F-10 | **`A.escape_detail` is NOT the fix** (the item says so, and it is confirmed): its table is `(("\\", "\\\\"), ("\t", "\\t"), ("\n", "\\n"), ("\r", "\\r"))`, which touches NO Markdown metacharacter and NO C0/C1 character other than tab/CR/LF. It is also applied only to GATE REFS in the renderers, never to `detail_text`. | `attention_contract._AGENT_ESCAPES` as quoted. In `_render_item_row` the calls are `A.escape_detail(g.get("ref", ""))` in both branches, and in `_render_table_row` `A.escape_detail(it.gate.get("ref", ""))`. |
| F-11 | **A RENDER-TIME ESCAPE IS THE ONLY VIABLE POLICY, measured over the live corpus.** Treating a Markdown metacharacter as a `--check` violation would fail a clean checkout immediately and massively. | Over all 2820 details `attention._extract_detail` actually extracts from `.aw/records/**/*.md` in this lane: 1063 contain `_`, 1002 contain a backtick, 187 contain `>`, 136 contain `<`, 74 contain `*`, 60 contain `[`, 43 contain `#`, 25 contain `\|`. Separately, 883 of 2820 ALREADY exceed `A.MAX_DESCRIPTIVE_LEN` (300), so the existing bound is already corpus-violating at the renderer's input set. |
| F-12 | The ESCAPE SET must be narrow, and the corpus says which characters are safe to leave alone. A blunk escape of every CommonMark metacharacter would backslash-litter 1063 values over `_` alone and 1002 over backticks, for no safety gain on this surface. | Of 2820 values: ZERO contain real link or image syntax (`!?\[[^\]]*\]\([^)]*\)` matches nothing), ZERO have an odd backtick count (so no value opens an unterminated code span), and ZERO contain a newline. 57 have an ODD asterisk count and 133 contain an HTML-tag-shaped `<...>` (for example `<verb>`, `<host>`, `<argv>`), which is the real risk `<` carries. |
| F-13 | **The A14 fixture does not exist and no test asserts anything about Markdown metacharacters in a renderer.** The one existing detail-rendering test uses only benign values. | `tests/test_attention.py::test_detail_cascade_and_rendering` asserts `"scope: Implement feature X."` in the plain board, in the colored board, in `render_json`, and end-to-end through `att.run`. `tests/test_attention_contract.py::test_output_safety` exercises `is_safe_descriptive` as a PREDICATE only, never a renderer. `tests/test_backlog_descriptive_safety.py` is the repo's real hostile-string suite but targets backlog SETTERS, not attention renderers. |
| F-14 | The `attention.unsafe-field` rule id already exists in the closed catalog, so IF a reviewer overrides OQ-02 toward the violation reading, no new id is needed. Recorded so the alternative is cheap to evaluate rather than re-researched. | `attention_contract.RULE_IDS` contains `"attention.unsafe-field"`, commented "control-char / over-length / newline / non-http issue url". `tests/test_attention_contract.py::test_catalog_closed_and_named` pins catalog membership. |
| F-15 | There is NO existing test of `term.format_table`, and it does not render a descriptive field anyway, so the item's "becomes user-visible the moment a descriptive field is placed in a table cell" risk is real but belongs to a different surface and is NOT in this plan's scope. | `rg format_table tests/` returns nothing. `term.format_table` joins cells with two spaces and emits no `\|` delimiter. `releases.run_show` passes `["ID","TREE","STATUS","PRIORITY","PATH"]` and prints `Summary:` as a bare line, not a cell. |
| F-16 | Only 5 of 2820 values contain a backslash, so escaping the backslash itself (required for any escape scheme to be unambiguous) is nearly free on the live corpus. | Census over the extracted details; the single example is a value containing `Do not \"fix\" it`. |

## Proposed changes (ordered, validatable)

1. Add `escape_markdown_inline` and `neutralize_control_characters` to `attention_contract`, as pure table-driven functions beside `escape_detail`.
2. Apply BOTH to `detail_text` at the three emission sites (`_render_item_row` colored, `_render_item_row` uncolored, `_render_table_row`).
3. Add the A14 output-safety test module that does not exist, asserting on real renderer output.
4. Amend the spec to state the measured escape set and record that the board's `--format markdown` is the default board.
5. Record the change in `CHANGELOG.md`.

## Deferred / out of scope (with reason)

- **Making a Markdown metacharacter a `--check` violation.** Refused on measurement, not on preference: F-11 counts 1063 live values containing `_` and 1002 containing a backtick, and 883 of 2820 details already exceed `MAX_DESCRIPTIVE_LEN`, so a violation reading would fail a clean checkout en masse. See OQ-02.
  - Carrier-Declined: nothing is owed, because this row records a DECISION THIS PLAN MAKES (OQ-02, resolved) rather than work it postpones. The escaping policy is settled here on corpus evidence; a carrier would assert that someone must revisit a question that is answered.
- **The existing 883 over-length details.** This plan adds no length enforcement at the renderer and changes no bound. The over-length population is a real contract gap but it is the length bullet's, not the escaping bullet's, and `ynhst5` is already deciding the checker-side strictness question for the specs and releases trees. Filing or fixing it here would merge two independent decisions. FILED as backlog `tapqf2`, which records the 883/2820 measurement, why enabling the bound today would deadlock the lifecycle, and the three routes open to whoever closes it.
  - Carrier: tapqf2
- **Bidi control characters (U+202A..U+202E) and the wider Unicode `Cf`/`Cs`/`Co` categories.** Section 8.8 names "bidi controls" explicitly but `_CONTROL_CHAR_RE` does not cover them (they are outside C0/C1), so E-01 deliberately does not either; closing that needs its own decision about diverging from or widening the shared predicate. FILED as backlog `3jez8u`, which records the inconsistency in Section 8.8's own sentence (the parenthetical names bidi controls while the phrase it qualifies does not contain them) and warns that a blanket `Cf` rejection would also catch legitimate zero-width characters. Recorded in OQ-05.
  - Carrier: 3jez8u
- **`term.format_table` cell escaping.** F-15 measures that it renders no descriptive field (its callers pass ID/PATH/STATUS columns) and has no test at all. The item's own note that this becomes user-visible "the moment a descriptive field is placed in a table cell" is correct and remains true; it is a different surface with a different owner.
  - Carrier-Declined: nothing is owed TODAY, and filing a record would misstate the risk as live. F-15 measures that no `format_table` caller passes a descriptive field, so there is no present defect to carry; the hazard is CONDITIONAL on a future change that puts such a field in a cell, and E-02's docstring plus the E-06 spec amendment are where that future author is told to apply the escaper. A carrier for a defect that does not exist yet would sit open indefinitely with nothing to do.
- **A distinct CommonMark-correct Markdown renderer for `--format markdown`.** Out of scope per the stdlib-only constraint (N1) and because no consumer has asked for one; E-04 makes the existing surface safe instead. See OQ-04.
  - Carrier-Declined: nothing is owed; this is a DECLINED ENHANCEMENT, not postponed work. No requirement in the governing spec asks for a separate Markdown renderer (Section 8.1 describes `--format markdown` as "the human board"), and E-04 makes the existing surface satisfy the contract. OQ-04 records the trigger that would justify revisiting it, which is a consumer that needs fenced tables.
- **The metadata-region versus whole-document divergence itself** (F-4). This plan makes the RENDERER safe regardless of which region the value came from, which is the correct fix for a renderer. Narrowing `_extract_detail`'s read is a behavior change to what detail every artifact displays and would need its own plan.
  - Carrier-Declined: nothing is owed, because this plan CLOSES the hazard the divergence created rather than deferring it. Once E-03 lands, an unsafe value from either region is rendered inert, so the remaining divergence is a cosmetic question about which detail an artifact DISPLAYS and no longer a safety one. `ynhst5` E-02 already records the divergence itself for any future reader.

## Scope check

- Over-scope: none. Every declared path is written by at least one E-item: `attention_contract.py` by E-01/E-02, `attention.py` by E-03/E-04, the new test module by E-05, and the spec plus `CHANGELOG.md` by E-06.
- Under-scope: the three unescaped emission sites, the raw-ANSI board defect, the raw-ANSI `--format markdown` defect, and the missing A14 fixture are all covered. NOT covered, each with a reason recorded in Deferred above: the 883 over-length values, bidi controls, `term.format_table`, and `_extract_detail`'s unbounded region.

## Required tests / validation

- The new `tests/test_attention_output_safety.py` must FAIL before E-03/E-04 and pass after, with both runs pasted.
- `tests/test_attention.py`, `tests/test_attention_contract.py`, `tests/test_backlog.py` and `tests/test_term.py` must stay green: all four call `att.render_board` and so observe the changed detail line.
- The full suite, run BARE as `python3 -m pytest` per the AGENTS.md contract (the configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow'`; do not add `-n0`, a second `-q`, or `-p no:randomly`).
- `aw check` and `aw ipd lint` on this plan.
- A determinism spot-check for criterion A6: the same `--format markdown --details` command under two different `TZ` and `LANG` settings must produce identical bytes.

## Spec / documentation sync

E-06 amends `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` Section 8.8 and adds a `CHANGELOG.md` entry. The spec path is declared in `- Scope-Paths:` so both runners announce the declared spec edit before the run and reconcile it at run end. WHY the amendment is required rather than optional: the current bullet is unbounded and unimplementable as literally written (F-11/F-12 measure that escaping every Markdown metacharacter would transform the majority of the live corpus), so implementing it without recording the measured narrowing would leave the code and the contract describing different behavior, which is the drift the amendment rule exists to prevent.

## Open questions

### OQ-01: WHICH surfaces escape (the first question the backlog item left open)

- Blocking: no
- Status: resolved
- Owner: this plan
- Resolution or deferral rationale: RESOLVED from measurement: the board's detail line ONLY, at the three sites F-2 names. The JSON surface needs nothing (F-8: `ensure_ascii=True` already renders a control character as `\uXXXX` and a pipe inside a JSON string is inert) and the `--agent` surface needs nothing (F-9: it does not carry `detail_text` in its emitted record at all). Section 8.8 names three surfaces with three different policies and already has the `--agent` one implemented as `escape_detail`; this plan adds the Markdown one and leaves the JSON one alone, which matches the spec's own per-surface structure.

### OQ-02: Escape at RENDER time, or treat the metacharacter as a `--check` violation (the second question the item left open)

- Blocking: no
- Status: resolved
- Owner: this plan
- Resolution or deferral rationale: RESOLVED as ESCAPE AT RENDER, on corpus evidence rather than on the reading the item happened to assume. F-11 counts, over the 2820 details the extractor actually produces in this lane, 1063 values containing `_`, 1002 containing a backtick, 187 containing `>` and 25 containing `|`; and 883 already exceed the existing length bound. A violation-only policy would therefore fail `aw attention --check` on a clean checkout for the majority of the corpus, which is the condition THIS SAME SPEC warns about in its requirement F3a ("TWO EXCLUSIONS ARE NORMATIVE, because a check that fails on correct behavior is a check operators bypass"), and would also deadlock the lifecycle the way `ynhst5` E-02 measured for its own rule. The item's own reasoning agrees and is confirmed: "a pipe in prose is legitimate content in a way an ANSI escape is not". Note the two halves land differently and that asymmetry is deliberate: a METACHARACTER is escaped and never a violation, while a CONTROL CHARACTER is ALREADY a violation per `is_safe_descriptive` and is ADDITIONALLY neutralized at render, because Section 8.8's "the renderers never emit raw control characters" is an absolute statement about the renderer that a checker elsewhere cannot discharge (F-4).

### OQ-03: Is a non-round-trippable escape acceptable on this surface?

- Blocking: no
- Status: resolved
- Owner: this plan
- Resolution or deferral rationale: YES, and this is the judgement a reviewer should attack first. The in-repo precedent `review_findings._row` pairs its `|` escape with a `_split_row` READER that undoes it, because a `.review.md` table is re-parsed. The attention board has NO machine reader: a machine consumer takes `--format json` (F-8, unchanged by this plan) or `--agent` (F-9), and the board is explicitly the human surface in Section 8.1. So a reader that must undo the escape does not exist, and adding one would be speculative. The visible cost is that a human sees `a \| b` where the artifact says `a | b`; F-12 bounds that cost at 7.0 percent of values (197 of 2820) for the chosen five-character set, which is the price of the Section 8.8 guarantee. If a reviewer judges that cost too high for `|` specifically, the narrower alternative is to escape only `[`, `]`, `<` and `\` and accept the table-breaking risk the spec names first; this plan does not take that option because `|` is the one character Section 8.8 calls out by its consequence ("cannot break the table").

### OQ-04: Should `--format markdown` become a real, separate Markdown renderer?

- Blocking: no
- Status: deferred
- Owner: whoever first needs a machine-consumable Markdown board; triggered when a consumer requires fenced tables rather than the plain board
- Resolution or deferral rationale: DEFERRED, with the reason recorded so the next author does not re-discover F-5. Today the flag is accepted by the CLI (`choices=("markdown", "json")`) and is byte-identical to the default board, because `attention.py` contains no occurrence of the string `markdown` and `fmt` is tested only for `json`. A real Markdown renderer (fenced tables, proper headings) would be a larger change under the stdlib-only constraint with no consumer demanding it; E-04 instead makes the existing surface safe and deterministic by forcing color off. Whoever later builds a true renderer must apply `escape_markdown_inline` at every cell, and at that point the `|` escape becomes load-bearing rather than precautionary.
- Carrier-Declined: nothing is owed; no requirement asks for this renderer and E-04 makes the existing surface satisfy the contract, so there is no outstanding work for a carrier to hold. The question records a TRIGGER (a consumer needing fenced tables) rather than a postponed task, and filing a record for it would sit open with nothing actionable in it.

### OQ-05: Should the control-character neutralizer cover bidi controls, which Section 8.8 names but `_CONTROL_CHAR_RE` does not match?

- Blocking: no
- Status: deferred
- Owner: the `attention_contract` output-safety predicate owner; triggered by any change that widens `_CONTROL_CHAR_RE` or by a measured bidi-control value appearing in a tracked artifact
- Resolution or deferral rationale: DEFERRED as a NAMED GAP rather than silently closed. Section 8.8 says "Any C0/C1 control character (including ANSI escape sequences, NUL, and bidi controls)", but the shared `_CONTROL_CHAR_RE` is `[\x00-\x1f\x7f-\x9f]`, and the bidi overrides (U+202A..U+202E, U+2066..U+2069) are `Cf` and fall OUTSIDE that range, so neither `is_safe_descriptive` nor E-01 catches them. E-01 deliberately reuses the shared regex rather than widening it here, because a renderer that neutralizes more than the predicate rejects creates exactly the checker/renderer divergence F-4 documents as a hazard. Closing this properly means widening the shared predicate, which changes what `aw specs check` and `aw attention --check` reject across every tree and so needs its own plan and its own corpus census.
- Carrier: 3jez8u

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a `python3 -c` session showing `A.neutralize_control_characters("red \x1b[31mX\x1b[0m\x07")` returning a string whose `repr` contains `\ufffd` and contains NO `\x1b` or `\x07`; paste a second call on a control-character-free value returning it unchanged; and paste `git diff` for `attention_contract.py` showing the new function REUSES `_CONTROL_CHAR_RE` and that `is_safe_descriptive` and `_CONTROL_CHAR_RE` are themselves unmodified.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a `python3 -c` session showing `A.escape_markdown_inline` on an input containing all five escaped characters plus a backtick, `_`, `*`, `#` and `>`, with the `repr` of the output demonstrating that exactly the five are backslash-prefixed and the other five are untouched; and showing the backslash-first ordering by asserting that the input `"a\\|b"` yields `"a\\\\\\|b"` (one backslash escaped, then the pipe escaped) and not a value in which the two are indistinguishable.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a `python3 -c` session that constructs the F-1 hostile `att.Item` and prints `repr(att._render_item_row(...))` for BOTH the colored and uncolored branches plus `att._render_table_row`, showing in all three: `\|` present and no bare `|` in the detail segment, `\[` present, and (on the F-3 ANSI value) U+FFFD present with no `\x1b`/`\x07` byte. The colored output must STILL contain the `\x1b[38;5;250m` sequence `color256` adds, proving the neutralizer ran on the raw value and not on the colorized string. Also paste `git diff` showing `render_json` and the `--agent` path are untouched and that the three `A.escape_detail` gate-ref calls are unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `FORCE_COLOR=1 python3 -m agent_workflows attention --format markdown --details | cat -v | head -12` showing ZERO `^[[` sequences (contrast with the pre-change output in F-6, which shows many); paste a byte-comparison showing `aw attention --no-color --details` and `aw attention --format markdown --details` are identical in length and content; and paste evidence that the bare default board on a forced-color run STILL emits ANSI, proving the default path was not collaterally changed.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the FAILING run of `python3 -m pytest tests/test_attention_output_safety.py -o addopts=""` against reverted E-03/E-04 production code (naming exactly how the revert was done), then the PASSING run after restoring it, then a BARE full-suite `python3 -m pytest` with its `N passed` summary line. Confirm by inspection and state explicitly that the new module contains no `inspect`, `ast`, regex-over-source, symbol census, or line-count assertion (GUIDING_PRINCIPLES P16), and that it includes the benign pass-through case and the end-to-end `att.run` case.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the spec diff showing the amended Section 8.8 bullet naming the five escaped characters, the three deliberately-unescaped ones with their measured counts, and the `--format markdown` relationship; confirm A14's text is UNCHANGED and the spec's `- Status:` and `## Workflow history` are unchanged by a lifecycle act; paste the `CHANGELOG.md` entry; and paste `aw check` output showing no new finding. Also paste the A6 determinism spot-check: the same `--format markdown --details` command under two different `TZ`/`LANG` settings producing identical bytes.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is ONE cohesive change: two pure transforms, their application at the three sites that render the same field, the fixture that proves it, and the contract amendment that records the measured escape set. Splitting the transforms from their call sites would land dead code; splitting the fixture from the fix would land an unproven claim.

Execution requires explicit human approval first; this plan is authored `to-review` and carries no `- Readiness:` field, which is `/plan-review`'s output to write and never the author's. Commit through `aw commit qpw45x -- <paths>` with only this plan's declared paths, never `git add -A` and never a push. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` item above carries pasted, concrete evidence; a green suite claimed without its pasted output does not satisfy the execution contract.
