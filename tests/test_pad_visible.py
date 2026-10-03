"""Behavioral tests for term.pad_visible (IPD n7yaa6)."""

from __future__ import annotations

import random
import unittest

from agent_workflows import term as T


class PadVisibleBehaviorTests(unittest.TestCase):
    """Assert term.pad_visible contract as behavior (P16: no code-pinning)."""

    def test_zero_width_variation_selector_padding(self) -> None:
        """Property (a): VS-bearing text pads to requested columns, where len() would fall short."""
        # 's' (1) + '\u26a0' (1) + '\ufe0e' (0) + '1' (1) = 3 columns, 4 code points.
        text = "s\u26a0\ufe0e1"
        self.assertEqual(T.visible_width(text), 3)
        self.assertEqual(len(text), 4)

        padded = T.pad_visible(text, 6)
        self.assertEqual(padded, "s\u26a0\ufe0e1   ")
        self.assertEqual(T.visible_width(padded), 6)
        # len()-based padding would compute 6 - len(text) = 2 spaces, yielding 5 visible columns
        len_based_padded = text + (" " * (6 - len(text)))
        self.assertEqual(T.visible_width(len_based_padded), 5)
        self.assertNotEqual(padded, len_based_padded)

    def test_nfd_decomposed_combining_accent_padding(self) -> None:
        """Property (b): NFD decomposed text pads to requested columns, where len() would fall short."""
        # 'c' (1) + 'a' (1) + 'f' (1) + 'e' (1) + '\u0301' (0) = 4 columns, 5 code points.
        text = "cafe\u0301"
        self.assertEqual(T.visible_width(text), 4)
        self.assertEqual(len(text), 5)

        padded = T.pad_visible(text, 8)
        self.assertEqual(padded, "cafe\u0301    ")
        self.assertEqual(T.visible_width(padded), 8)
        # len()-based padding would compute 8 - 5 = 3 spaces, yielding 7 visible columns
        len_based_padded = text + (" " * (8 - len(text)))
        self.assertEqual(T.visible_width(len_based_padded), 7)
        self.assertNotEqual(padded, len_based_padded)

    def test_ansi_styled_padding_matches_plain(self) -> None:
        """Property (c): Styled text pads to same visible width as plain text."""
        term_obj = T.Term(color=True)
        plain = "to-review"
        styled = term_obj.color256(plain, 33, bold=True)
        width = 15

        pad_styled = T.pad_visible(styled, width)
        pad_plain = T.pad_visible(plain, width)
        self.assertEqual(T.visible_width(pad_styled), width)
        self.assertEqual(T.visible_width(pad_plain), width)
        self.assertEqual(T.visible_width(pad_styled), T.visible_width(pad_plain))
        # len(styled) includes escape sequences so len()-based pad would under-pad or fail
        self.assertGreater(len(styled), len(plain))

    def test_both_alignments(self) -> None:
        """Property (d): align='left' pads after text; align='right' pads before text."""
        text = "status"
        self.assertEqual(T.pad_visible(text, 10, align="left"), "status    ")
        self.assertEqual(T.pad_visible(text, 10, align="right"), "    status")
        # default alignment is left
        self.assertEqual(T.pad_visible(text, 10), "status    ")

    def test_overflow_and_degenerate_widths(self) -> None:
        """Overflow and boundary cases: pads only, never truncates; 0 and negative widths return text unchanged."""
        long_text = "authority-queued"  # 16 columns
        self.assertEqual(T.visible_width(long_text), 16)
        # Wider than width: returns unchanged (pad-only, no fit)
        self.assertEqual(T.pad_visible(long_text, 12), long_text)
        self.assertEqual(T.pad_visible(long_text, 12, align="right"), long_text)

        # width = 0 and negative width return text unchanged
        self.assertEqual(T.pad_visible("active", 0), "active")
        self.assertEqual(T.pad_visible("active", -5), "active")

        # empty text pads to full width
        self.assertEqual(T.pad_visible("", 5), "     ")
        self.assertEqual(T.pad_visible("", 5, align="right"), "     ")

    def test_unknown_align_raises_value_error_naming_offending_value(self) -> None:
        """Reject unknown align loudly naming the offending value."""
        with self.assertRaises(ValueError) as ctx:
            T.pad_visible("text", 10, align="center")
        self.assertIn("center", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx2:
            T.pad_visible("text", 10, align="rigth")
        self.assertIn("rigth", str(ctx2.exception))

    def test_seeded_equivalence_sweep_against_private_alias(self) -> None:
        """Seeded random sweep asserting pad_visible(t, w) == _pad_visible(t, w) on 2000 inputs."""
        rng = random.Random(0x451007)
        term_obj = T.Term(color=True)
        alphabet = [
            "a",
            "B",
            "1",
            " ",
            "-",
            "_",
            "\u26a0\ufe0e",  # VS pair (warning sign with text variation selector)
            "e\u0301",  # NFD combining acute accent
            "\u200b",  # zero-width space
            "\u25d5",  # ambiguous-width glyph
        ]
        input_count = 2000
        for _ in range(input_count):
            length = rng.randint(0, 10)
            chars = [rng.choice(alphabet) for _ in range(length)]
            raw_text = "".join(chars)
            # half styled with ANSI colors
            if rng.random() < 0.5:
                color_code = rng.randint(16, 231)
                bold = rng.choice([True, False])
                text = term_obj.color256(raw_text, color_code, bold=bold)
            else:
                text = raw_text
            width = rng.randint(0, 14)
            self.assertEqual(
                T.pad_visible(text, width),
                T._pad_visible(text, width),
                f"Mismatch for text={text!r}, width={width}",
            )


if __name__ == "__main__":
    unittest.main()
