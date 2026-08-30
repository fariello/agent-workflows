"""The host-neutral concise-reporting contract (terseout Order 01, `ntf6sx`).

ONE source of truth for how an agent REPORTS to a human, shared by every delivery surface so
the semantics cannot drift between hosts:

  * the installed ``aw:reporting`` managed section in ``AGENTS.md`` (and the existing
    ``CLAUDE.md``/``GEMINI.md`` mirrors), rendered by ``engine.agents_managed_sections``;
  * a one-line POINTER in every generated OpenCode/Claude command shim
    (``engine.shim_body`` / ``engine.aw_dispatcher_shim``);
  * the execution and verifier prompts of both IPD drivers (``oc_runipd``, ``agy_runipd``).

Delivery decisions this module encodes (do not "simplify" them back):

  * POINTER, NOT COPY, in command shims (plan `ntf6sx` E-03 / OQ-01). Measured: the contract
    prose is ~1.6KB against a ~42.7KB, 48-file shim corpus, so copying it into every shim
    would add ~+80% of input re-read on EVERY command invocation and defeat the very
    token-cost goal the contract exists to serve (`README.md` 2.x direction). The shims get
    :func:`shim_pointer_line`; the full prose is rendered ONCE per instruction surface.
  * FULL PROSE in driver prompts (E-04). A fresh runner worker must not depend on ambient
    host behavior, which is why the drivers already embed their other critical safeguards.
  * NOTHING appended to the review-turn prompt (E-05). ``build_review_prompt`` returns
    exactly ``/plan-review <path>`` and is handed to the host as ONE argv element, so any
    appended prose would be absorbed as ``$ARGUMENTS`` path arguments. The review turn
    inherits the contract from the shim pointer plus ``AGENTS.md``.

Scope fence: this contract governs model-authored USER-FACING prose. It is not the `aw` CLI
output contract (``docs/cli-output-contract.md`` governs CLI bytes and the ``aw.agent/v1``
records), and neither may be read as licensing fewer JSONL fields, weaker work, or truncated
evidence.

Pure stdlib, no imports from ``engine`` (engine imports THIS module).
"""

from __future__ import annotations

__all__ = [
    "POINTER_TARGET",
    "REPORTING_SECTION_TITLE",
    "REPORTING_SLUG",
    "ROUTINE_FINAL_WORD_CAP",
    "contract_text",
    "prompt_block",
    "shim_pointer_line",
]

# The managed-section slug this contract is rendered as (the manifest key is
# ``<file>#aw:reporting``). Mirrored by ``engine.AW_REPORTING_SLUG``.
REPORTING_SLUG = "reporting"

# The heading the rendered contract carries. Kept at ``##`` so the SAME text reads correctly
# both as a managed section in an instruction file and as a section of a driver prompt.
REPORTING_SECTION_TITLE = "## Concise reporting (user-facing prose)"

# What a shim pointer points AT (the managed-section manifest-key idiom used repo-wide).
POINTER_TARGET = "AGENTS.md#aw:reporting"

# The soft cap on a ROUTINE final response. Explicitly overridden by a required report.
ROUTINE_FINAL_WORD_CAP = 100

# The canonical contract prose. ASCII only (no em/en dashes), so it is safe in every
# instruction file and every prompt that is asserted to be pure ASCII.
_CONTRACT = f"""{REPORTING_SECTION_TITLE}

Report to the user concisely. Lead with the OUTCOME. Begin a yes/no answer with `Yes.` or
`No.`. Use one sentence when one sentence is enough. Omit preambles, praise, restatement of
the request, narration of routine actions (searching, reading, thinking), recaps of what you
just said, and closing offers of further help. Use plain direct language. Report only
material outcomes, changed files, verification status, and blockers, and OMIT a category
that is empty. Keep a routine final response at or below {ROUTINE_FINAL_WORD_CAP} words.
While working, emit at most one short progress sentence, and only when it tells the user
something they cannot already see.

PRECEDENCE (this default is not the top rule). An explicit user request, or a controlling
workflow that specifies a required report, OVERRIDES the default. When a workflow mandates a
report (for example `plan-review`'s findings table and the enumeration it calls "the literal
final output", or `release-review`'s final report), produce that report IN FULL and do NOT
apply the {ROUTINE_FINAL_WORD_CAP}-word cap to it; be concise only in the prose around it.
Brevity NEVER licenses truncating a mandated report, and it NEVER licenses skipping the
ACTUAL runner output the execution contract requires you to paste.

COMPLETENESS. Concision governs REPORTING, not analysis, implementation, testing, or
correctness. Keep complete: required evidence, safety warnings, destructive-action
confirmations, structured outcomes (JSON/JSONL fields and their required keys), and durable
artifacts (code, tests, plans, specs, documentation). Saying less is never permission to do
less, to verify less, or to omit something a human needs in order to decide.
"""


def contract_text() -> str:
    """The canonical contract prose, heading included, with a single trailing newline.

    This exact string is what every embedding surface uses. A surface that renders its own
    paraphrase is drift and is caught by the parity tests.
    """

    return _CONTRACT


def shim_pointer_line() -> str:
    """The ONE line a generated command shim carries instead of the full prose (E-03).

    Deliberately tiny (see the module docstring): a generated shim is re-read on every single
    invocation of its command, so the prose lives once in the instruction file and the shim
    only names it. Written in the same imperative "read this" idiom the shims already use for
    workflow bodies.
    """

    return (
        f"Reporting: follow `{POINTER_TARGET}` "
        "(concise prose; required reports still in full).\n"
    )


def prompt_block() -> str:
    """The contract as a driver-prompt section (E-04), separated from adjacent prompt text.

    Returns the same :func:`contract_text` bytes with surrounding blank lines, so a caller can
    concatenate it into a prompt without gluing it to the previous paragraph.
    """

    return "\n" + contract_text()
