"""Drift guard for IPD awretrofit Order 02: shipped, agent-executed artifacts must not reintroduce
legacy `.agents/` paths that no longer exist in a fresh/migrated `.aw/` install.

Release-review run 20260817-153418 (findings S4-D01/S4-D02) found the shipped workflow bodies, the
`index.md` catalog, the record-README templates, and the always-loaded AGENTS.md block still
instructed agents to use `.agents/` paths.

WHY THIS IS NOT A SPENT MIGRATION GUARD, verified rather than assumed. The migration itself IS
complete (there is no `.agents/` directory in this checkout). What is NOT spent is the class of
defect: `.agents/<path>` inside a shipped workflow body is an instruction an AGENT FOLLOWS, and in a
migrated install it points at a directory that does not exist, so the step silently reads nothing.
The nearest existing structural check,
`tests/test_acceptance_matrix.py::IndependentPostcheckTests::test_e05`, covers a DIFFERENT surface:
it scans `agent_workflows/` WRITER MODULES via `record_producers.discover_legacy_write_sinks` and
exercises the runtime `guard_write` refusal. Neither touches the shipped `.aw/system/workflows/`
bundle, which is what an agent actually reads. Measured 2026-09-19: the bundle contains 9 files that
still name `.agents/`, every one of them inside this file's allowlist.

Legitimate remainders are allowlisted in `ALLOWLIST` below, each with the reason it is exempt AND
whether it must still lead with `.aw/` (so the exemption cannot decay into "stripped back to
legacy"). The allowlist is checked for NON-VACUITY: an entry that no longer matches any offending
file is reported, because a stale exemption silently widens the hole.

WHAT WAS DELETED HERE, and where the property lives now:

* `self.assertIn("source of truth: `.aw/system/VERSION`", index)`. A PROSE PIN: an English sentence
  in `index.md` whose only load-bearing part is the PATH. Replaced by asserting the path exists.
  `tests/test_cli.py` and `tests/test_cli_layout.py` additionally assert an install writes
  `.aw/system/VERSION`, so the path itself has structural owners.
* `assertIn(".aw/system/workflows/", index)` plus `assertNotIn(".agents/workflows/", index)`. The
  negative is strictly subsumed by the bundle scan below (`index.md` is not allowlisted, so any
  `.agents/` in it already fails there). The positive was a substring of a catalog that is machine
  parsed, so it is replaced by `test_every_manifest_row_resolves_to_a_real_body`, which parses the
  catalog with the real parser and requires every row's body path to EXIST: a catalog naming the
  right prefix but a dead file passed the old assertion and fails the new one.
* The rendered-AGENTS.md assertions (`.aw/records/research/` present, `.aw/records/docs/` absent).
  The generated block is the thing every adopter installs, so the legacy check now runs against
  `engine.agents_managed_block` (strictly stronger; `tests/test_shared_checkout_contract.py::
  NoDriftTests::test_repo_agents_block_equals_generated` proves this repo's file equals it). The
  flattening of the doc-family out of `docs/` has structural owners already:
  `tests/test_awretrofit_install_scaffolder.py` asserts a fresh install does NOT create
  `.aw/records/docs/README.md`, and `tests/support.py::_source_docs_root` resolves the live tree.
* `test_release_review_leads_with_aw` (one literal path in one allowlisted file). Generalized into
  the allowlist's `must_name_aw` column, which makes the same claim for EVERY allowlisted file
  rather than for one hand-picked line of one of them.
"""

from __future__ import annotations

import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_BUNDLE = _REPO / ".aw" / "system" / "workflows"

_LEGACY = ".agents/"

#: (path prefix relative to the bundle root, why it is exempt, must it ALSO name `.aw/`?)
#:
#: `must_name_aw` encodes the difference between the two KINDS of exemption, which a flat list of
#: paths hid. A layout-agnostic document reviews or migrates OTHER repos, so it legitimately names
#: both spellings and must LEAD with `.aw/`; a host-adapter artifact names `.agents/skills/`, which
#: is a host concept that this records-layout migration never touched, so requiring `.aw/` of it
#: would be wrong.
ALLOWLIST = (
    (
        "release-review/",
        "layout-agnostic runbook: it reviews OTHER repos, so it keeps `.agents/` as a NAMED legacy "
        "alternative behind the `.aw/` spelling",
        True,
    ),
    (
        "migrate/",
        "documents migrating FROM `.agents/`, so the legacy path is the subject matter",
        True,
    ),
    (
        "conformance/",
        "`.agents/skills/` is a HOST-ADAPTER concept (where a host looks for skills), not the "
        "records layout this migration changed",
        False,
    ),
    (
        "setup-repo/tools/normalize_plan_names.py",
        "legacy-fallback descriptions: the tool must still recognize a pre-migration tree",
        True,
    ),
)


def _iter_bundle_text_files():
    """Every readable shipped file in the bundle, with its bundle-relative posix path."""

    for p in sorted(_BUNDLE.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix == ".pyc" or "__pycache__" in p.parts:
            continue
        try:
            yield p.relative_to(_BUNDLE).as_posix(), p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue


class ShippedBundleLegacyPathTests(unittest.TestCase):
    """No shipped, agent-executed artifact outside the allowlist may name a legacy path."""

    def test_no_legacy_agents_path_outside_the_allowlist(self):
        offenders = []
        for rel, text in _iter_bundle_text_files():
            if any(rel.startswith(prefix) for prefix, _, _ in ALLOWLIST):
                continue
            if _LEGACY not in text:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if _LEGACY in line:
                    offenders.append(f"  {rel}:{i}: {line.strip()[:120]}")
                    break
        self.assertEqual(
            offenders,
            [],
            f"{len(offenders)} shipped bundle file(s) reintroduced a legacy `{_LEGACY}` path. An "
            "agent FOLLOWS these paths, and in a migrated install the directory does not exist, so "
            "the step reads nothing and reports no error:\n"
            + "\n".join(offenders)
            + "\n  FIX: use the `.aw/` spelling. If the file legitimately needs the legacy path "
            "(it reviews or migrates other repos), add it to ALLOWLIST in this module WITH the "
            "reason, rather than removing this check.",
        )

    def test_the_allowlist_is_not_vacuous_and_still_leads_with_aw(self):
        """Two failure modes of an allowlist, reported together because both make it a lie.

        STALE: an entry matching no offending file no longer exempts anything, so it is a hole kept
        open for a file that moved. DECAYED: an allowlisted document that names ONLY the legacy
        spelling is no longer the 'layout-agnostic' artifact the exemption claims it is; it was
        stripped back to legacy, which is the exact regression this module exists to catch.
        """

        files = list(_iter_bundle_text_files())
        problems = []
        for prefix, why, must_name_aw in ALLOWLIST:
            matched = [
                (rel, text)
                for rel, text in files
                if rel.startswith(prefix) and _LEGACY in text
            ]
            if not matched:
                problems.append(
                    f"  STALE ENTRY {prefix!r}: no shipped file under it names `{_LEGACY}` any "
                    f"more, so this exemption only keeps a hole open.\n"
                    f"    it was added because: {why}"
                )
                continue
            if must_name_aw:
                decayed = [rel for rel, text in matched if ".aw/" not in text]
                if decayed:
                    problems.append(
                        f"  DECAYED ENTRY {prefix!r}: {decayed} name `{_LEGACY}` but no longer "
                        "name `.aw/` at all, so they are not the layout-agnostic artifact this "
                        f"exemption describes.\n    it was added because: {why}"
                    )
        self.assertEqual(
            problems,
            [],
            f"{len(problems)} of {len(ALLOWLIST)} allowlist entries no longer describe the tree:\n"
            + "\n".join(problems)
            + "\n  FIX: for a STALE entry, delete it (the file it protected is gone or was fixed). "
            "For a DECAYED entry, restore the `.aw/` spelling in the named file: an allowlisted "
            "document that leads with the legacy path is the regression, not an exemption.",
        )


class ShippedCatalogTests(unittest.TestCase):
    """The catalog and the always-loaded block, asserted through their real consumers."""

    def test_every_manifest_row_resolves_to_a_real_body(self):
        """Parsed with the REAL parser: a row pointing at a dead file is a dead workflow.

        Strictly stronger than the `assertIn(".aw/system/workflows/", index)` it replaces, which a
        catalog full of correct-looking but nonexistent paths satisfied.
        """

        from agent_workflows import engine

        rows = engine.parse_manifest(_BUNDLE)
        self.assertTrue(
            rows, f"the manifest at {_BUNDLE / 'index.md'} parsed to zero rows"
        )
        dangling = [
            f"  {row.command}: body {row.body!r} does not exist"
            for row in rows
            if not (_REPO / row.body).is_file()
        ]
        self.assertEqual(
            dangling,
            [],
            f"{len(dangling)} of {len(rows)} manifest rows point at a body file that is not there. "
            "The dispatcher tells an agent to read the manifest and open that path, so each of "
            "these verbs exists in the catalog and does nothing when invoked:\n"
            + "\n".join(dangling)
            + "\n  FIX: repair the path in `index.md`, or restore the body file.",
        )

    def test_the_version_file_the_catalog_cites_exists(self):
        """Kept as a PATH check (the prose sentence quoting it is not pinned)."""

        self.assertTrue(
            (_REPO / ".aw" / "system" / "VERSION").is_file(),
            "the catalog names `.aw/system/VERSION` as the version source of truth, but the file "
            "is absent, so every reader of that citation is sent to nothing.",
        )

    def test_the_generated_agents_block_names_no_legacy_path(self):
        """Asserted on the GENERATED block: that text is what every adopter installs.

        Replaces the same check on this repo's rendered `AGENTS.md`. A legacy path here reaches
        every adopter on their next install, and `test_shared_checkout_contract.py` already proves
        the rendered file equals this block byte for byte.
        """

        from agent_workflows import engine

        block = engine.agents_managed_block(target_layout="aw")
        hits = [line.strip() for line in block.splitlines() if _LEGACY in line]
        self.assertEqual(
            hits,
            [],
            f"the generated always-loaded contract (engine.agents_managed_block) names a legacy "
            f"`{_LEGACY}` path:\n  "
            + "\n  ".join(hits)
            + "\n  FIX: correct it in `engine.py`; "
            "every adopter receives this text on their next install.",
        )


if __name__ == "__main__":
    unittest.main()
