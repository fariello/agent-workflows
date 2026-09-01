"""Tests for the mixed-type confirmation gate and the runner-facing selection policy.

IPD 6lu3rq E-05, covering spec `25kzda` 2.5. The gate is demonstrated in BOTH directions (a
one-sided test does not demonstrate a gate), the verbatim refusal is asserted against the spec's own
text rather than a paraphrase, and the classification is proven to DEFER to the shipped resolver
rather than duplicating it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_workflows import run_selection_policy as pol
from agent_workflows import selectors as sel

# --------------------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------------------


def _item(spec_type: str, action: str, n: int = 1, tag: str = "") -> list:
    return [
        pol.ClassifiedItem(
            path=Path("/repo/{0}{1}{2}.md".format(spec_type, tag, i)),
            spec_type=spec_type,
            resolver_type=None,
            status=None,
            action=action,
        )
        for i in range(n)
    ]


def _classify(items: list) -> pol.Classification:
    """Build a Classification from hand-made items (no filesystem), mirroring classify_paths."""
    return pol.Classification(
        items=tuple(items),
        counts=pol._counts_for(items),
        untyped=tuple(i.path for i in items if i.spec_type is None),
    )


def _spec_example() -> pol.Classification:
    """Spec 2.5's own example selection: IPDs 4 (2 review, 2 execute), Specs 2 (1 review, 1 plan),
    Prompts 1 (1 execute)."""
    return _classify(
        _item("ipd", pol.ACTION_REVIEW, 2, "r")
        + _item("ipd", pol.ACTION_EXECUTE, 2, "x")
        + _item("spec", pol.ACTION_REVIEW, 1, "r")
        + _item("spec", pol.ACTION_PLAN, 1, "p")
        + _item("prompt", pol.ACTION_EXECUTE, 1)
    )


def _write(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """A minimal records tree with one plan, one spec, and one backlog item, all sharing a selector
    so a single token genuinely spans three types."""
    (tmp_path / ".git").mkdir()
    recs = tmp_path / ".aw" / "records"
    _write(
        recs / "plans" / "pending" / "20260101-mixdemo-01-aaa111-demo.ipd.md",
        "# IPD: demo\n\n- Id: aaa111\n- Set: mixdemo\n- Status: approved\n",
    )
    _write(
        recs / "specs" / "20260101-bbb222-01-bbb222-demo.spec.md",
        "# Spec: demo\n\n- Id: bbb222\n- Set: mixdemo\n- Status: approved\n",
    )
    _write(
        recs / "backlog" / "20260101-ccc333-01-ccc333-demo.backlog.md",
        "# Backlog: demo\n\n- Id: ccc333\n- Set: mixdemo\n- Status: open\n",
    )
    return tmp_path


# --------------------------------------------------------------------------------------------------
# E-01: classification, and that it CONSUMES the shipped resolver
# --------------------------------------------------------------------------------------------------


def test_type_mapping_is_one_data_table_covering_the_resolver_vocabulary():
    # Every resolver type the shipped resolver knows has an explicit entry (a spec type, or an
    # explicit None), so a new type cannot be silently mistyped.
    assert set(pol.SPEC_TYPE_BY_RESOLVER_TYPE) == set(sel.KNOWN_PRIMARY_TYPES)
    # Spec 2.2's seven runnable types are exactly the non-None values.
    assert set(pol.RESOLVER_TYPE_BY_SPEC_TYPE) == set(pol.SPEC_TYPE_ORDER)
    assert len(pol.SPEC_TYPE_ORDER) == 7
    # comms/roadmaps have no spec 2.2 type.
    assert pol.SPEC_TYPE_BY_RESOLVER_TYPE["comms"] is None
    assert pol.SPEC_TYPE_BY_RESOLVER_TYPE["roadmaps"] is None
    # The mapping round-trips.
    for spec_type, resolver_type in pol.RESOLVER_TYPE_BY_SPEC_TYPE.items():
        assert pol.SPEC_TYPE_BY_RESOLVER_TYPE[resolver_type] == spec_type


def test_single_type_selection_reports_exactly_one_type(repo: Path):
    plan = next((repo / ".aw" / "records" / "plans").rglob("*.ipd.md"))
    c = pol.classify_paths(repo, [plan])
    assert c.type_count == 1
    assert c.spec_types == ("ipd",)
    assert c.is_mixed is False


def test_mixed_selection_counts_each_type(repo: Path):
    paths = [
        next((repo / ".aw" / "records" / "plans").rglob("*.ipd.md")),
        next((repo / ".aw" / "records" / "specs").rglob("*.spec.md")),
        next((repo / ".aw" / "records" / "backlog").rglob("*.backlog.md")),
    ]
    c = pol.classify_paths(repo, paths)
    assert c.spec_types == (
        "ipd",
        "spec",
        "backlog",
    )  # SPEC_TYPE_ORDER, not input order
    assert {tc.spec_type: tc.total for tc in c.counts} == {
        "ipd": 1,
        "spec": 1,
        "backlog": 1,
    }
    assert c.is_mixed is True


def test_resolution_defers_to_selectors_resolve(repo: Path, monkeypatch):
    """The policy must CALL selectors.resolve rather than reimplementing precedence/ambiguity."""
    calls = []
    real = sel.resolve

    def spy(repo_root, record_type, selector, **kw):
        calls.append((record_type, selector))
        return real(repo_root, record_type, selector, **kw)

    monkeypatch.setattr(pol._sel, "resolve", spy)
    c, errors = pol.resolve_selection(
        repo, "mixdemo", spec_types=("ipd", "spec", "backlog")
    )
    assert errors == ()
    # One delegation per type; the policy contributed no matching logic of its own.
    assert calls == [("plans", "mixdemo"), ("specs", "mixdemo"), ("backlog", "mixdemo")]
    assert c.spec_types == ("ipd", "spec", "backlog")
    assert c.is_mixed is True


def test_unique_kind_collision_is_reported_using_the_shipped_policy(repo: Path):
    """spec 2.3 step 4: an id6 matching several files is corruption, not a multi-item selection.
    The policy applies selectors' own UNIQUE_KINDS rather than a second ambiguity policy."""
    _write(
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20260101-mixdemo-02-aaa111-dupe.ipd.md",
        "# IPD: dupe\n\n- Id: aaa111\n- Set: mixdemo\n- Status: approved\n",
    )
    c, errors = pol.resolve_selection(repo, "aaa111", spec_types=("ipd",))
    assert errors and "collision" in errors[0]
    assert c.items == ()


def test_untyped_files_are_reported_not_dropped_and_do_not_make_a_selection_mixed(
    repo: Path,
):
    comm = _write(
        repo / ".aw" / "records" / "comms" / "shared" / "note.md",
        "# note\n\n- Id: ddd444\n",
    )
    plan = next((repo / ".aw" / "records" / "plans").rglob("*.ipd.md"))
    c = pol.classify_paths(repo, [plan, comm])
    assert comm in c.untyped
    assert len(c.items) == 2  # reported, not silently dropped
    assert c.is_mixed is False  # an unrunnable record is not a KIND OF WORK


# --------------------------------------------------------------------------------------------------
# E-02: the action preview
# --------------------------------------------------------------------------------------------------


def test_preview_matches_spec_2_5_example_exactly():
    expected = (
        "Mixed work-item selection:\n"
        "  IPDs:    4 (2 review, 2 execute)\n"
        "  Specs:   2 (1 review, 1 plan)\n"
        "  Prompts: 1 (1 execute)"
    )
    assert pol.render_action_preview(_spec_example()) == expected


def test_preview_is_stable_across_runs_and_input_order():
    a = _spec_example()
    shuffled = list(a.items)[::-1]
    b = _classify(shuffled)
    assert pol.render_action_preview(a) == pol.render_action_preview(b)
    assert pol.render_action_preview(a) == pol.render_action_preview(a)
    assert pol.queue_digest(a) == pol.queue_digest(b)  # digest is order-independent


@pytest.mark.parametrize(
    "spec_type,status,expected",
    [
        ("ipd", "approved", pol.ACTION_EXECUTE),
        ("ipd", "auto-approved", pol.ACTION_EXECUTE),
        ("ipd", "reusable", pol.ACTION_EXECUTE),
        ("ipd", "to-review", pol.ACTION_REVIEW),
        ("ipd", "executed", pol.ACTION_SKIP),
        ("ipd", "superseded", pol.ACTION_SKIP),
        ("ipd", "not-executed", pol.ACTION_SKIP),
        ("spec", "to-review", pol.ACTION_REVIEW),
        ("spec", "approved", pol.ACTION_PLAN),
        ("spec", "implemented", pol.ACTION_SKIP),
        ("spec", "deferred", pol.ACTION_SKIP),
        ("backlog", "open", pol.ACTION_PLAN),
        ("backlog", "blocked", pol.ACTION_SKIP),
        ("backlog", "graduated", pol.ACTION_SKIP),
        ("backlog", "done", pol.ACTION_SKIP),
        ("prompt", None, pol.ACTION_EXECUTE),
        ("prompt", "executed", pol.ACTION_SKIP),
        (
            "research",
            "active",
            pol.ACTION_SKIP,
        ),  # spec 3.6 gray skip, from the type alone
        ("release", "planned", pol.ACTION_SKIP),
        ("walkthrough", None, pol.ACTION_SKIP),
    ],
)
def test_action_derives_from_status_per_spec_dispatch_tables(
    spec_type, status, expected
):
    assert pol._action_for(spec_type, status) == expected


@pytest.mark.parametrize(
    "spec_type,status",
    [
        (
            "ipd",
            "draft",
        ),  # spec 3.2 splits draft on a completeness check (content, not status)
        (
            "ipd",
            "reviewed",
        ),  # spec 3.2 dispatches reviewed on --full-auto (a flag we cannot see)
        ("ipd", None),
        ("ipd", "banana"),  # unknown status: spec 3.2 red-aborts; we must not guess
        ("spec", "draft"),
        ("spec", "reviewed"),
        ("spec", "implementing"),
        ("backlog", "wat"),
    ],
)
def test_undeterminable_action_is_reported_not_bucketed(spec_type, status):
    assert pol._action_for(spec_type, status) == pol.ACTION_UNDETERMINED


def test_undetermined_appears_in_the_preview_rather_than_silently_counting_as_an_action():
    c = _classify(
        _item("ipd", pol.ACTION_EXECUTE, 1, "x")
        + _item("ipd", pol.ACTION_UNDETERMINED, 2, "u")
    )
    preview = pol.render_action_preview(c)
    assert "1 execute" in preview and "2 undetermined" in preview
    assert pol.ACTION_UNDETERMINED not in {
        pol.ACTION_REVIEW,
        pol.ACTION_PLAN,
        pol.ACTION_EXECUTE,
    }


def test_reviewed_ipd_is_undetermined_end_to_end_through_classify_paths(repo: Path):
    p = _write(
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20260101-mixdemo-03-eee555-rev.ipd.md",
        "# IPD: rev\n\n- Id: eee555\n- Set: mixdemo\n- Status: reviewed\n",
    )
    c = pol.classify_paths(repo, [p])
    assert c.items[0].status == "reviewed"
    assert c.items[0].action == pol.ACTION_UNDETERMINED


# --------------------------------------------------------------------------------------------------
# E-03: the decision predicate
# --------------------------------------------------------------------------------------------------


def test_single_type_selection_is_never_gated():
    c = _classify(_item("ipd", pol.ACTION_EXECUTE, 3))
    for interactive in (True, False):
        v = pol.decide(c, interactive=interactive)
        assert v.proceed is True
        assert v.gate_applied is False  # ungated, not "passed"
        assert v.code is None and v.message is None


def test_unattended_mixed_is_refused_without_the_flag_and_proceeds_with_it():
    """Both directions on the SAME selection, differing only in the flag (the falsifiable pair)."""
    c = _spec_example()
    refused = pol.decide(c, interactive=False, allow_mixed=False)
    allowed = pol.decide(c, interactive=False, allow_mixed=True)
    assert refused.proceed is False
    assert refused.code == pol.RUN_MIXED_TYPES
    assert allowed.proceed is True
    assert allowed.code is None and allowed.message is None
    assert allowed.record.response_or_flag == "--allow-mixed"


@pytest.mark.parametrize("response", ["run mixed", "  run mixed  ", "run mixed\n"])
def test_interactive_accepts_exactly_the_spec_phrase(response):
    v = pol.decide(_spec_example(), interactive=True, response=response)
    assert v.proceed is True
    assert v.gate_applied is True


@pytest.mark.parametrize(
    "response",
    [
        "y",  # spec 2.5 rejects `y` explicitly
        "",  # spec 2.5 rejects an empty response explicitly
        None,  # no answer at all
        "yes",  # a generic confirmation
        "Y",
        "YES",
        "ok",
        "Run Mixed",  # case is not folded
        "run",
        "run mixed types",
        "runmixed",
        "run  mixed",  # internal whitespace is not normalized
    ],
)
def test_interactive_rejects_near_misses_and_generic_confirmations(response):
    v = pol.decide(_spec_example(), interactive=True, response=response)
    assert v.proceed is False
    assert v.code == pol.RUN_MIXED_TYPES


def test_no_branch_requires_a_tty():
    """Every branch is reachable as a pure call: no TTY, no host, no filesystem, no ledger."""
    c = _spec_example()
    verdicts = [
        pol.decide(_classify(_item("ipd", pol.ACTION_EXECUTE, 1)), interactive=False),
        pol.decide(c, interactive=False, allow_mixed=False),
        pol.decide(c, interactive=False, allow_mixed=True),
        pol.decide(c, interactive=True, response="run mixed"),
        pol.decide(c, interactive=True, response="y"),
    ]
    assert [v.proceed for v in verdicts] == [True, False, True, True, False]


def test_allow_mixed_waives_only_type_mixing():
    """spec 2.5 third bullet: the flag acknowledges type mixing ONLY. This predicate must never be a
    place another gate can be waived, so its waiver set is exhaustive and singular."""
    assert pol.Verdict.WAIVES == ("type-mixing",)
    # The predicate's ONLY override parameter is allow_mixed; there is no approval/scope/safety knob.
    import inspect

    params = set(inspect.signature(pol.decide).parameters)
    assert params == {
        "classification",
        "interactive",
        "allow_mixed",
        "response",
        "host",
        "selector",
    }
    for forbidden in (
        "allow_unapproved",
        "skip_gates",
        "force",
        "allow_unverifiable",
        "no_verify",
    ):
        assert forbidden not in params
    # The flag does not alter the previewed actions: what dispatch would do is unchanged.
    c = _spec_example()
    assert pol.decide(
        c, interactive=False, allow_mixed=True
    ).record.action_preview == pol.render_action_preview(c)


def test_verdict_carries_all_four_spec_2_5_bullet_4_facts():
    c = _spec_example()
    for v in (
        pol.decide(c, interactive=False, allow_mixed=True),
        pol.decide(c, interactive=True, response="run mixed"),
        pol.decide(c, interactive=False),
    ):
        rec = v.record
        assert rec.type_counts == {
            "ipd": 4,
            "spec": 2,
            "prompt": 1,
        }  # 1: confirmed type counts
        assert rec.action_preview == pol.render_action_preview(c)  # 2: action preview
        assert len(rec.queue_digest) == 64  # 4: queue digest (sha256)
        assert set(rec.as_dict()) == {
            "type_counts",
            "action_preview",
            "response_or_flag",
            "queue_digest",
        }
    # 3: the response OR the flag actually used, distinguishably.
    assert pol.decide(
        c, interactive=False, allow_mixed=True
    ).record.response_or_flag == ("--allow-mixed")
    assert (
        pol.decide(c, interactive=True, response="run mixed").record.response_or_flag
        == "run mixed"
    )
    assert pol.decide(c, interactive=False).record.response_or_flag is None


def test_queue_digest_changes_with_the_queue():
    a = _spec_example()
    b = _classify(list(a.items) + _item("ipd", pol.ACTION_EXECUTE, 1, "extra"))
    assert pol.queue_digest(a) != pol.queue_digest(b)


# --------------------------------------------------------------------------------------------------
# E-04: the verbatim refusal
# --------------------------------------------------------------------------------------------------


def test_finding_code_string_is_exactly_run_mixed_types():
    assert pol.RUN_MIXED_TYPES == "RUN-MIXED-TYPES"


def test_refusal_template_is_character_identical_to_the_spec():
    """Asserted against spec 25kzda 2.5's exact refusal block. Rewording the message FAILS this."""
    spec_exact = (
        "[RUN-MIXED-TYPES] Selection contains <counts>. No work started. Review the selection, "
        "then run: aw <host> run <selector> --type <type> ... --allow-mixed"
    )
    assert pol.REFUSAL_TEMPLATE == spec_exact
    # With placeholders left literal, a rendered refusal differs from the spec ONLY at <counts>.
    rendered = pol.render_refusal(_spec_example())
    assert rendered == spec_exact.replace("<counts>", "IPDs: 4, Specs: 2, Prompts: 1")
    # The load-bearing clauses survive substitution.
    assert rendered.startswith("[RUN-MIXED-TYPES] Selection contains ")
    assert "No work started." in rendered
    assert rendered.endswith("--type <type> ... --allow-mixed")


def test_refusal_message_names_the_counts_and_the_recovery_command():
    v = pol.decide(_spec_example(), interactive=False, host="oc", selector="mixdemo")
    assert v.message is not None
    assert "IPDs: 4, Specs: 2, Prompts: 1" in v.message
    assert "aw oc run mixdemo --type <type> ... --allow-mixed" in v.message


def test_confirm_phrase_constant_is_the_spec_phrase():
    assert pol.CONFIRM_PHRASE == "run mixed"
    assert pol.is_confirmation_accepted("run mixed") is True
    assert pol.is_confirmation_accepted("y") is False


def test_refusal_path_starts_nothing_and_writes_nothing(repo: Path, monkeypatch):
    """The `No work started.` clause is a BEHAVIORAL guarantee. Prove the refusal path performs no
    mutation: no subprocess (no host session), and a byte-identical records tree afterwards."""
    import subprocess

    def boom(*a, **k):  # pragma: no cover - must never run
        raise AssertionError("refusal path spawned a process")

    monkeypatch.setattr(subprocess, "Popen", boom)
    monkeypatch.setattr(subprocess, "run", boom)
    monkeypatch.setattr(subprocess, "check_output", boom)

    def snapshot():
        return {
            str(p.relative_to(repo)): p.read_bytes()
            for p in sorted(repo.rglob("*"))
            if p.is_file()
        }

    before = snapshot()
    c, _ = pol.resolve_selection(repo, "mixdemo", spec_types=("ipd", "spec", "backlog"))
    assert c.is_mixed is True
    v = pol.decide(c, interactive=False, allow_mixed=False)
    assert v.proceed is False and v.code == pol.RUN_MIXED_TYPES
    assert snapshot() == before  # nothing created, deleted, or modified


def test_gate_is_pure_and_leaves_no_module_state():
    """A second identical decision returns an identical verdict (no caching, no accumulation)."""
    c = _spec_example()
    first = pol.decide(c, interactive=False)
    second = pol.decide(c, interactive=False)
    assert first == second
