"""Behavioral guards for docs/cli-agent-protocol.md token control documentation (IPD moegsl).

This test module verifies the token control escape hatch documentation across
the agent protocol reference (`docs/cli-agent-protocol.md`) and the normative
CLI output contract (`docs/cli-output-contract.md`).

In accordance with GUIDING_PRINCIPLES P16 and AGENTS.md:
1. This module tests the documentation artifacts under test directly, without
   inspecting production Python code, symbols, or ASTs.
2. It asserts invariants and semantic relationships (e.g. stated count word
   matching actual top-level bullet count, and parity between reference and contract)
   rather than pinning frozen prose or literal paragraphs.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROTOCOL_DOC_PATH = REPO_ROOT / "docs" / "cli-agent-protocol.md"
CONTRACT_DOC_PATH = REPO_ROOT / "docs" / "cli-output-contract.md"

_ENGLISH_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}

_FLAG_BULLET_RE = re.compile(r"^- (?:\*\*)?`(--[a-z-]+)")
_COUNT_WORD_RE = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+escape\s+hatches\b",
    re.IGNORECASE,
)


def _extract_token_control_section(markdown_text: str) -> str:
    """Extract lines in the Token Control section up to the next heading or thematic break."""
    lines: list[str] = []
    in_section = False
    for line in markdown_text.splitlines():
        if re.match(r"^#{1,3}\s+(?:\d+\.\s*)?Token [Cc]ontrol", line):
            in_section = True
            continue
        if in_section:
            if re.match(r"^(?:#{1,3}\s+|---)", line):
                break
            lines.append(line)
    if not in_section:
        raise AssertionError(
            "Could not locate 'Token Control' section heading in document"
        )
    return "\n".join(lines)


def _extract_hatch_flag_tokens(section_text: str) -> list[str]:
    r"""Extract backticked CLI flag tokens from top-level bullet items in a section.

    Matches top-level bullets starting with a backticked flag (e.g. `- \`--fields\``
    or `- **\`--fields\`**`), excluding non-hatch bullets such as `**Compact Defaults**`.
    Sub-bullets (indented with whitespace) are excluded so that secondary bullet
    breakdowns do not pollute top-level escape hatch enumeration.
    For composite bullets like `- **\`--verbose\` / \`--json\`**:`, this extracts the
    primary hatch flag token (`--verbose`), normalizing the composite entry.
    """
    flags: list[str] = []
    for line in section_text.splitlines():
        if not line.startswith("- "):
            continue
        m = _FLAG_BULLET_RE.match(line)
        if m:
            flags.append(m.group(1))
    return flags


class CliAgentProtocolDocTests(unittest.TestCase):
    """Test token control escape hatch documentation accuracy and invariants."""

    def test_token_control_count_word_agrees_with_bullet_count(self) -> None:
        """The introductory count word in ## Token control must match its bullet count.

        Asserts the semantic relationship between the English number word in the
        introductory sentence ('Two escape hatches...', 'Three escape hatches...')
        and the number of top-level bullet items listed in that section.
        """
        self.assertTrue(
            PROTOCOL_DOC_PATH.is_file(),
            f"Missing protocol doc: {PROTOCOL_DOC_PATH}",
        )
        content = PROTOCOL_DOC_PATH.read_text(encoding="utf-8")
        section = _extract_token_control_section(content)

        m = _COUNT_WORD_RE.search(section)
        self.assertIsNotNone(
            m,
            "Could not find '<number> escape hatches' in ## Token control section",
        )
        word = m.group(1).lower()
        stated_count = _ENGLISH_NUMBER_WORDS.get(word)
        self.assertIsNotNone(
            stated_count,
            f"Unrecognized number word: {word!r}",
        )

        top_level_bullets = [
            line for line in section.splitlines() if line.startswith("- ")
        ]
        bullet_count = len(top_level_bullets)

        self.assertEqual(
            stated_count,
            bullet_count,
            f"Stated escape hatch count word ({word!r} -> {stated_count}) does not match "
            f"number of top-level bullets ({bullet_count}) in ## Token control",
        )

    def test_token_control_enumerates_limit(self) -> None:
        """## Token control in docs/cli-agent-protocol.md must enumerate --limit.

        Guards against regression of backlog item 9qya0k where --limit was omitted
        from the token control escape hatch list.
        """
        self.assertTrue(
            PROTOCOL_DOC_PATH.is_file(),
            f"Missing protocol doc: {PROTOCOL_DOC_PATH}",
        )
        content = PROTOCOL_DOC_PATH.read_text(encoding="utf-8")
        section = _extract_token_control_section(content)
        flags = _extract_hatch_flag_tokens(section)

        self.assertIn(
            "--limit",
            flags,
            f"docs/cli-agent-protocol.md ## Token control does not enumerate '--limit'. "
            f"Found flags: {flags}",
        )

    def test_protocol_and_contract_agree_on_token_control_hatches(self) -> None:
        """docs/cli-agent-protocol.md and docs/cli-output-contract.md must agree on hatches.

        The set of escape hatches enumerated in docs/cli-agent-protocol.md ## Token control
        must match the escape hatches enumerated in docs/cli-output-contract.md Section 6.
        Normalizes composite bullets such as '--verbose / --json' to the primary flag token.
        Non-hatch bullets (such as '**Compact Defaults**') are excluded.
        """
        self.assertTrue(
            PROTOCOL_DOC_PATH.is_file(),
            f"Missing protocol doc: {PROTOCOL_DOC_PATH}",
        )
        self.assertTrue(
            CONTRACT_DOC_PATH.is_file(),
            f"Missing contract doc: {CONTRACT_DOC_PATH}",
        )
        proto_content = PROTOCOL_DOC_PATH.read_text(encoding="utf-8")
        contract_content = CONTRACT_DOC_PATH.read_text(encoding="utf-8")

        proto_section = _extract_token_control_section(proto_content)
        contract_section = _extract_token_control_section(contract_content)

        proto_flags = set(_extract_hatch_flag_tokens(proto_section))
        contract_flags = set(_extract_hatch_flag_tokens(contract_section))

        self.assertEqual(
            proto_flags,
            contract_flags,
            f"Escape hatch sets disagree between protocol ({proto_flags}) "
            f"and contract ({contract_flags})",
        )


if __name__ == "__main__":
    unittest.main()
