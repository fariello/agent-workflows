- Id: 3jez8u
- Status: open
- Set: 3jez8u
- Priority: low
- Work-Kind: chore
- Summary: is_safe_descriptive misses the bidi controls Section 8.8 names explicitly, because _CONTROL_CHAR_RE covers only C0/C1 and the bidi overrides are Cf

## Workflow history
- 2026-10-01 created (aw backlog): is_safe_descriptive misses the bidi controls Section 8.8 names explicitly, because _CONTROL_CHAR_RE covers only C0/C1 and the bidi overrides are Cf

FILED AS THE CARRIER for the bidi-control deferred row and OQ-05 in plan `qpw45x` (Set `llnvwj`), which adds a control-character neutralizer to the attention board and deliberately reuses the existing predicate's character class rather than widening it as a side effect.

MEASURED 2026-10-01 in a lane: `attention_contract._CONTROL_CHAR_RE` is `[\\x00-\\x1f\\x7f-\\x9f]`, which is C0 plus C1 plus DEL. The Unicode bidirectional overrides and isolates (U+202A..U+202E, U+2066..U+2069) are general category `Cf` and lie OUTSIDE that range, so `is_safe_descriptive` returns True for a value containing them.

WHAT THE CONTRACT SAYS: spec `attention-registry-and-cross-tree-status` Section 8.8 requires that "Any C0/C1 control character (including ANSI escape sequences, NUL, and bidi controls) in a descriptive field is a contract violation". The parenthetical names bidi controls explicitly while the phrase it qualifies ("C0/C1") does not contain them, so the sentence is internally inconsistent and the implementation followed the narrower half. Deciding which half governs is part of this item.

WHY IT MATTERS: a bidi override can make rendered text read in an order that differs from its byte order, which is the classic 'Trojan Source' presentation attack. A descriptive field flows into a human terminal and into an agent's context, which is precisely the trust boundary Section 8.8 exists to defend.

WHY `qpw45x` DID NOT FIX IT, recorded so the reasoning is not relitigated: that plan's neutralizer reuses `_CONTROL_CHAR_RE` deliberately, because a renderer that neutralizes MORE than the predicate rejects creates a checker/renderer divergence, which is the same class of defect that plan documents as its own motivation (the checker reads the metadata region while the renderer reads the whole document). Widening the shared predicate changes what `aw specs check`, `aw backlog check` and `aw attention --check` reject across every tree, so it needs its own corpus census and its own decision.

THERE IS AN IN-REPO PRECEDENT FOR THE WIDER CLASS: `run_analytics_spa.sanitize_control_characters` replaces Unicode `Cc`/`Cf`/`Cs`/`Co` with U+FFFD. Note that a blanket `Cf` rejection is NOT obviously right for a descriptive field: `Cf` also contains U+200B..U+200D (zero-width space, non-joiner, joiner) and U+00AD (soft hyphen), which appear in legitimate text, so whoever closes this must decide between the targeted bidi set and the whole category, and must census the corpus before choosing.
