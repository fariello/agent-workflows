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


# --------------------------------------------------------------------------------------------------
# revsweep-02 (`6ypimw`) E-01: THE DIVERGENCE PROPERTY - sweep membership == dispatch-table routing
# --------------------------------------------------------------------------------------------------
#
# THIS IS THE LOAD-BEARING TEST OF THAT PLAN, and it is worth more than the refactor it guards. Spec
# `25kzda` 2.4a property 2 makes the rule normative: an item is in `reviews` IF AND ONLY IF the Section
# 3 dispatch table gives it a review action at its current status, implemented ONCE. Before `6ypimw`
# the two disagreed and the disagreement was INVISIBLE: each runner's `expand_selectors` carried its
# own closure testing `status == "to-review"` while `determine_action` routed `to-review` AND `draft`
# to `review`, so a complete draft named EXPLICITLY was reviewed while the SAME draft was silently
# absent from the sweep.
#
# DRIVEN FROM THE ROUTING, NEVER FROM A HAND-WRITTEN STATUS LIST. A test enumerating the statuses it
# expects has to be edited whenever a status is added, and whoever edits it will edit it to match
# whatever the code then does - which is how the original divergence survived review. Asking the
# ROUTER what it routes makes a future status addition FAIL here until the predicate agrees.
#
# BOTH HOSTS, because the deleted closure was duplicated verbatim in both: a property proven on one
# runner would have left `aw agy run reviews` free to diverge again.

_HOSTS = ("oc", "agy")

#: A COMPLETE plan body (no anchored scaffold placeholder), parameterized by id6 and status. Complete
#: on purpose: spec 2.5a splits a draft on authoring completeness, and this property is about what the
#: table routes, so the completeness variable is held at "complete" here and varied in its own test.
_COMPLETE_PLAN = """\
# IPD: sweep property fixture

- Date: 2026-09-05
- Kind: child
- Concern: a real concern sentence, so no anchored placeholder remains.
- Scope: a real scope sentence.
- Scope-Paths: src/
- Item-Dependencies: none
- Status: {status}
- Set: s1
- Order: {order}
- Highest E allocated: 01
- Author: test
- Id: {id6}

## Workflow history

- 2026-09-05 draft (test): created.

## Goal

A real goal sentence for the fixture.

## Detailed Implementation Checklist (TODO)

### Task group 1: fixture

- [ ] E-01 Do one observable thing.
  - Depends on: none
  - Expected outcome: the observable thing happened.
  - Execution state: pending

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: the observable thing, pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: small
- Cohesion rationale: one concern.

Real gate prose: commit path-scoped, never push.
"""


def _host_module(host: str):
    from agent_workflows import agy_runipd, oc_runipd

    return {"oc": oc_runipd, "agy": agy_runipd}[host]


def _sweep_members(driver, plans_by_id: dict, repo: Path) -> set:
    """The ids `driver.expand_selectors` sweeps for `reviews`, as a set (empty when none)."""
    manifest = {
        "schema_version": 1,
        "plans": plans_by_id,
        "sets": {"s1": {"order": sorted(plans_by_id)}},
    }
    try:
        return set(driver.expand_selectors(manifest, ["reviews"], repo=repo))
    except driver.EmptyStatusSelection:
        return set()


@pytest.mark.parametrize("host", _HOSTS)
def test_sweep_membership_equals_dispatch_routing_for_every_status(
    host: str, tmp_path: Path
):
    """E-01, spec 2.4a property 2. FAILS AT PRE-CHANGE HEAD ON THE `draft` CASE, for both hosts."""
    from agent_workflows import plans as _plans

    driver = _host_module(host)
    plans_by_id: dict = {}
    routed_to_review: set = set()
    for n, status in enumerate(sorted(_plans.RECOGNIZED), start=1):
        id6 = "st{0:04d}".format(n)
        bucket = "pending"
        if status in ("executed", "superseded", "not-executed", "reusable"):
            # A terminal STATUS lives in its terminal DIRECTORY; putting it under pending/ would test
            # a directory/status mismatch, which spec 3.2 makes a red abort rather than a review.
            bucket = status
        rel = ".aw/records/plans/{0}/20260101-s1-{1:02d}-{2}-x.ipd.md".format(
            bucket, n, id6
        )
        _write(tmp_path / rel, _COMPLETE_PLAN.format(id6=id6, status=status, order=n))
        plans_by_id[id6] = {
            "set": "s1",
            "file": rel,
            "status": status,
            "order": n,
            "dependencies": [],
        }
        if driver.determine_action(status) == "review" and bucket == "pending":
            routed_to_review.add(id6)

    swept = _sweep_members(driver, plans_by_id, tmp_path)
    # Report by STATUS, not by id6: a failure that says `st0003` sends the reader to a fixture loop to
    # decode it, while one that says `draft` names the defect.
    status_of = {id6: info["status"] for id6, info in plans_by_id.items()}
    assert swept == routed_to_review, (
        "spec 25kzda 2.4a property 2 violated on host {0!r}: the `reviews` sweep and the dispatch "
        "table disagree. swept-but-not-routed={1}, ROUTED-BUT-NOT-SWEPT={2}".format(
            host,
            sorted(status_of[i] for i in swept - routed_to_review),
            sorted(status_of[i] for i in routed_to_review - swept),
        )
    )


@pytest.mark.parametrize("host", _HOSTS)
def test_a_complete_draft_is_swept_and_an_incomplete_one_is_not(
    host: str, tmp_path: Path
):
    """The draft split spec 2.5a/3.2 requires, at the SWEEP, on both hosts.

    The incomplete fixture is a real `aw ipd scaffold` body, so completeness is decided by the shipped
    anchored check and not by a heuristic invented for the test.
    """
    from agent_workflows import ipd_authoring

    driver = _host_module(host)
    stub_text = ipd_authoring.build_skeleton(
        kind="child",
        title="stub",
        author="test",
        when="2026-09-05",
        set_name="s1",
        order=2,
        plan_id="dr0002",
    )
    assert ipd_authoring.authoring_placeholders_resolved(stub_text) is False
    assert (
        ipd_authoring.authoring_placeholders_resolved(
            _COMPLETE_PLAN.format(id6="dr0001", status="draft", order=1)
        )
        is True
    )

    complete_rel = ".aw/records/plans/pending/20260101-s1-01-dr0001-complete.ipd.md"
    stub_rel = ".aw/records/plans/pending/20260101-s1-02-dr0002-stub.ipd.md"
    _write(
        tmp_path / complete_rel,
        _COMPLETE_PLAN.format(id6="dr0001", status="draft", order=1),
    )
    _write(tmp_path / stub_rel, stub_text)
    plans_by_id = {
        "dr0001": {
            "set": "s1",
            "file": complete_rel,
            "status": "draft",
            "order": 1,
            "dependencies": [],
        },
        "dr0002": {
            "set": "s1",
            "file": stub_rel,
            "status": "draft",
            "order": 2,
            "dependencies": [],
        },
    }
    assert _sweep_members(driver, plans_by_id, tmp_path) == {"dr0001"}


# --------------------------------------------------------------------------------------------------
# revsweep-02 (`6ypimw`) E-02: the ONE predicate, and what it deliberately does NOT decide
# --------------------------------------------------------------------------------------------------


def test_membership_derives_from_the_action_table_not_a_status_comparison():
    """Spec 2.4a property 2: `ACTION_REVIEW` is the single source of truth.

    Asserted as a PROPERTY over the tables rather than by re-listing statuses: for every row the
    table actually carries, the predicate agrees with `_action_for`. A corrected copy of the old
    `status == "to-review"` comparison would pass a to-review test and fail this one.
    """
    for spec_type, table in pol._ACTION_TABLES.items():
        for status, action in table.items():
            assert pol.needs_review(spec_type, status) is (
                action == pol.ACTION_REVIEW
            ), "{0}/{1} disagrees with the table".format(spec_type, status)


def test_undetermined_is_not_treated_as_needs_review():
    """THE failure mode that would sweep up stubs and past-review plans.

    `_IPD_ACTIONS` omits `draft` AND `reviewed` on purpose, mapping both to `ACTION_UNDETERMINED`
    (they branch on content, `--full-auto`, or `--action`). Only the `draft` row consults the
    completeness input; `reviewed` must answer False, and a draft whose completeness could not be
    determined must answer False too.
    """
    assert pol._action_for("ipd", "reviewed") == pol.ACTION_UNDETERMINED
    assert pol.needs_review("ipd", "reviewed") is False
    assert pol.needs_review("ipd", "reviewed", authoring_complete=True) is False
    assert pol._action_for("ipd", "draft") == pol.ACTION_UNDETERMINED
    assert pol.needs_review("ipd", "draft") is False  # completeness not supplied
    assert pol.needs_review("ipd", "draft", authoring_complete=None) is False
    assert pol.needs_review("ipd", "draft", authoring_complete=False) is False
    assert pol.needs_review("ipd", "draft", authoring_complete=True) is True
    # An unknown status is undetermined and is never review-worthy (spec 3.2 makes it a red abort).
    assert pol.needs_review("ipd", "no-such-status", authoring_complete=True) is False


def test_only_the_draft_row_consults_completeness():
    """The "which rows need content" rule has ONE definition, so no caller hardcodes `draft`."""
    assert pol.review_depends_on_completeness("ipd", "draft") is True
    assert pol.review_depends_on_completeness("spec", "DRAFT ") is True
    for status in ("to-review", "reviewed", "approved", "executed", None):
        assert pol.review_depends_on_completeness("ipd", status) is False
    # A type with no action table has no completeness-dependent row either.
    assert pol.review_depends_on_completeness("research", "draft") is False


def test_the_terminal_directory_exclusion_survives():
    """NOT redundant with status: a directory and a `- Status:` line CAN disagree, and spec 3.2 makes
    that mismatch a red abort rather than a review. Both deleted closures performed this check."""
    for bucket in ("executed", "superseded", "not-executed", "reusable"):
        path = ".aw/records/plans/{0}/20260101-s1-01-aaa111-x.ipd.md".format(bucket)
        assert pol.is_in_terminal_directory(path) is True
        assert pol.needs_review("ipd", "to-review", file_path=path) is False
        assert (
            pol.needs_review("ipd", "draft", authoring_complete=True, file_path=path)
            is False
        )
    pending = ".aw/records/plans/pending/20260101-s1-01-aaa111-x.ipd.md"
    assert pol.is_in_terminal_directory(pending) is False
    assert pol.needs_review("ipd", "to-review", file_path=pending) is True


# --------------------------------------------------------------------------------------------------
# revsweep-02 (`6ypimw`) E-05: TYPE-AWARE SIGNATURE, IPD-ONLY REACH
# --------------------------------------------------------------------------------------------------


def test_the_predicate_answers_for_a_spec_handed_to_it_directly():
    """E-05: the signature takes a type and consults `_ACTION_TABLES`, which carries `spec`."""
    assert pol.needs_review("spec", "to-review") is True
    assert pol.needs_review("spec", "draft", authoring_complete=True) is True
    assert pol.needs_review("spec", "draft", authoring_complete=False) is False
    assert (
        pol.needs_review("spec", "approved") is False
    )  # spec 3.3 routes that to `plan`
    assert pol.needs_review("spec", "implemented") is False


def test_the_ipd_only_limit_is_stated_at_the_definition_and_discovery_is_unchanged():
    """E-05's honest half, asserted so it cannot decay into an implied capability.

    NOTHING can hand the predicate a spec today: discovery walks only the two plans trees and neither
    host registers `--type`. `5slbpi` owns that gap. The limit must be stated AT THE DEFINITION, not
    merely in the plan, because a later reader sees the signature and not the IPD.
    """
    import inspect

    from agent_workflows import runner_shared

    doc = inspect.getdoc(pol.needs_review) or ""
    assert "IPD-ONLY" in doc or "IPD-only" in doc
    assert "5slbpi" in doc, "the definition must name the owner of the cross-type gap"
    source = inspect.getsource(runner_shared.discover_plans)
    assert "specs" not in source, "discovery is IPD-only; a spec tree would change this"


# --------------------------------------------------------------------------------------------------
# revsweep-02 (`6ypimw`) E-03: THE DRAFT ADMISSION GATE (spec 25kzda 2.5a)
# --------------------------------------------------------------------------------------------------

SPEC_PATH = (
    Path(__file__).resolve().parents[1]
    / ".aw"
    / "records"
    / "specs"
    / "20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md"
)


def _spec_2_5a_blocks() -> list:
    """The fenced `text` blocks of spec 2.5a, read from the SPEC FILE so a spec edit fails here."""
    text = SPEC_PATH.read_text(encoding="utf-8")
    section = text.split("### 2.5a Draft admission gate", 1)
    assert len(section) == 2, "spec 2.5a heading not found; did the spec move?"
    body = section[1].split("### 2.6", 1)[0]
    return [chunk.split("```", 1)[0].strip() for chunk in body.split("```text")[1:]]


def _drafts(complete: int = 0, incomplete: int = 0, spec_type: str = "ipd") -> list:
    out = [
        pol.DraftCandidate("c{0}".format(i), spec_type, True) for i in range(complete)
    ]
    out += [
        pol.DraftCandidate("i{0}".format(i), spec_type, False)
        for i in range(incomplete)
    ]
    return out


def test_the_exclusion_notice_is_the_specs_text_character_for_character():
    """Transcribed, never recomposed: the code prefix, the counts, and the recovery command are all
    fixed by spec 2.5a's `Exact refusal` block."""
    spec_refusal = _spec_2_5a_blocks()[-1]
    assert pol.DRAFTS_EXCLUDED_TEMPLATE == spec_refusal


def test_the_preview_is_byte_identical_to_the_specs_own_example():
    """Spec 2.5a's example block, reproduced by the SHARED renderer (2 IPDs, 1 spec, 1 incomplete)."""
    spec_preview = _spec_2_5a_blocks()[0]
    candidates = _drafts(complete=2) + [
        pol.DraftCandidate("s0", "spec", True),
        pol.DraftCandidate("bad", "ipd", False),
    ]
    verdict = pol.decide_draft_admission(
        candidates, interactive=False, allow_drafts=True
    )
    assert verdict.record.preview == spec_preview


def test_the_exact_phrase_is_required_and_reflex_answers_are_rejected():
    candidates = _drafts(complete=2)
    assert pol.DRAFTS_CONFIRM_PHRASE == "run drafts"
    good = pol.decide_draft_admission(
        candidates, interactive=True, response="run drafts\n"
    )
    assert good.admitted == ("c0", "c1")
    assert good.excluded_complete == ()
    for bad in ("y", "yes", "Y", "", "run", "run draft", "run drafts please", None):
        verdict = pol.decide_draft_admission(candidates, interactive=True, response=bad)
        assert verdict.admitted == (), "reflex answer {0!r} admitted a draft".format(
            bad
        )
        assert verdict.excluded_complete == ("c0", "c1")


def test_allow_drafts_admits_them_unattended():
    verdict = pol.decide_draft_admission(
        _drafts(complete=1), interactive=False, allow_drafts=True
    )
    assert verdict.admitted == ("c0",)
    assert verdict.record.response_or_flag == "--allow-drafts"
    assert verdict.message is None


def test_asymmetry_one_an_incomplete_draft_is_never_admitted_at_any_flag_setting():
    """spec 2.5a bullet 1. NO flag admits it, and it is never an abort: one unfinished draft must not
    deny review to the finished items beside it."""
    candidates = _drafts(complete=1, incomplete=1)
    for interactive, allow, response in (
        (False, False, None),
        (False, True, None),
        (True, False, "run drafts"),
        (True, True, "run drafts"),
    ):
        verdict = pol.decide_draft_admission(
            candidates,
            interactive=interactive,
            allow_drafts=allow,
            response=response,
        )
        assert "i0" not in verdict.admitted
        assert verdict.skipped_incomplete == ("i0",)
    # And with ONLY an incomplete draft the gate does not even apply, yet the skip is still reported.
    only_bad = pol.decide_draft_admission(_drafts(incomplete=1), interactive=False)
    assert only_bad.gate_applied is False
    assert only_bad.skipped_incomplete == ("i0",)
    assert only_bad.admitted == ()


def test_asymmetry_two_an_ungated_draft_is_excluded_while_the_run_proceeds():
    """spec 2.5a bullet 4, and the reason it differs from the mixed-type refusal.

    THE DIFFERENCE IS THE POINT: `decide` REFUSES a mixed selection (`proceed=False`, "No work
    started."), because the operator's intent is unclear. This gate excludes ONE item's admission and
    the rest proceeds, because the remaining items' intent is not in doubt. `DraftVerdict` therefore
    has no `proceed` field at all, which is what stops a later reader "fixing" the inconsistency.
    """
    verdict = pol.decide_draft_admission(
        _drafts(complete=2), interactive=False, allow_drafts=False, remaining_count=3
    )
    assert verdict.excluded_complete == ("c0", "c1")
    assert verdict.admitted == ()
    assert verdict.code == pol.RUN_DRAFTS_EXCLUDED
    assert not hasattr(verdict, "proceed")
    # The notice states what proceeded, so the operator is not told the run stopped.
    assert "2 complete draft item(s)" in verdict.message
    assert "3 item(s) proceeded" in verdict.message
    assert "No work started." not in verdict.message


def test_the_gate_reuses_the_shipped_primitives_rather_than_copying_them():
    """A second confirmation implementation is how `y` eventually gets accepted somewhere."""
    import inspect

    source = inspect.getsource(pol.decide_draft_admission)
    assert "is_confirmation_accepted" in source, "the shipped matcher must be reused"
    assert "render_action_preview" in inspect.getsource(pol.render_drafts_preview)
    # The exact-phrase matcher is ONE function, parameterized, not two.
    assert pol.is_confirmation_accepted("run drafts", phrase="run drafts") is True
    assert pol.is_confirmation_accepted("run mixed", phrase="run drafts") is False
    assert pol.is_confirmation_accepted("y", phrase="run drafts") is False
    # `decide` did not acquire a second override, which its own docstring forbids.
    assert pol.Verdict.WAIVES == ("type-mixing",)
    assert pol.DraftVerdict.WAIVES == ("draft-admission",)
    assert "allow_drafts" not in inspect.signature(pol.decide).parameters


def test_the_ledger_facts_are_returned_not_written():
    """`MixedTypeRecord`'s convention, followed: the module returns the facts, the runner persists."""
    verdict = pol.decide_draft_admission(
        _drafts(complete=2) + [pol.DraftCandidate("s0", "spec", True)],
        interactive=False,
        allow_drafts=True,
    )
    payload = verdict.record.as_dict()
    assert payload["draft_counts"] == {"ipd": 2, "spec": 1}
    assert payload["admitted"] == ["c0", "c1", "s0"]
    assert payload["response_or_flag"] == "--allow-drafts"
    assert payload["preview"].startswith(pol.DRAFTS_PREVIEW_HEADER)
    import json

    json.dumps(payload)  # JSON-ready, as the ledger append requires


def test_the_draft_gate_is_pure_and_deterministic():
    candidates = _drafts(complete=2, incomplete=1)
    first = pol.decide_draft_admission(candidates, interactive=False)
    second = pol.decide_draft_admission(candidates, interactive=False)
    assert first == second


def test_the_combined_case_collects_both_confirmations_in_one_interaction():
    """spec 2.5a bullet 5: both previews together, both answers before any work starts.

    PROVEN AT THE SEAM WITH A CONSTRUCTED CLASSIFICATION, and it is proven CORRECT, NOT proven FIRED:
    no real invocation can produce a mixed selection yet (discovery is IPD-only, neither host has
    `--type`), so this path cannot be triggered in production. See
    `test_no_live_invocation_can_yet_produce_a_mixed_selection` in `tests/test_run_flag_surface.py`.
    """
    mixed = _spec_example()
    assert mixed.is_mixed is True
    combined = pol.decide_selection_gates(
        mixed,
        _drafts(complete=1),
        interactive=True,
        mixed_response="run mixed",
        drafts_response="run drafts",
    )
    assert combined.proceed is True
    assert combined.mixed.gate_applied is True
    assert combined.drafts.admitted == ("c0",)
    # BOTH previews, together, in ONE rendered block.
    assert "Mixed work-item selection:" in combined.combined_preview
    assert pol.DRAFTS_PREVIEW_HEADER in combined.combined_preview
    # Each answer is independent: the mixed phrase does not admit drafts, nor vice versa.
    only_mixed = pol.decide_selection_gates(
        mixed,
        _drafts(complete=1),
        interactive=True,
        mixed_response="run mixed",
        drafts_response=None,
    )
    assert only_mixed.proceed is True
    assert only_mixed.drafts.admitted == ()
    only_drafts = pol.decide_selection_gates(
        mixed,
        _drafts(complete=1),
        interactive=True,
        mixed_response=None,
        drafts_response="run drafts",
    )
    assert only_drafts.proceed is False  # the mixed gate still refuses the run
    assert only_drafts.drafts.admitted == ("c0",)


# --------------------------------------------------------------------------------------------------
# runnoop Order 02 (`m85gxh`): the per-artifact disposition line and its closed reason set
# --------------------------------------------------------------------------------------------------
#
# WHY THESE LIVE HERE AND NEED NO RUN. The renderer is PURE, so every branch is a function of its
# inputs and can be asserted directly; a test that needed a live run to prove a reason string would be
# proving the driver's wiring, which is `tests/test_oc_runipd.py`'s and `tests/test_agy_runipd_cli.py`'s
# job. What is proven here is the CONTRACT: one renderer for both shapes, a closed reason vocabulary,
# and a dependency reason that NAMES the unmet dependency.


def _queue_entry(**over):
    """One queue entry in the shape `runner_shared.initialize_run_core` actually freezes."""
    entry = {
        "position": 1,
        "id6": "abc123",
        "setid": "wtiso",
        "action": "execute",
        "status": "reviewed",
        "attempts": [],
    }
    entry.update(over)
    return entry


def test_one_renderer_produces_the_acted_on_and_skipped_lines_in_the_same_shape():
    """The backlog item's actual requirement: a skipped artifact reported in the SAME shape.

    ASSERTED STRUCTURALLY, not by eyeballing two strings: both lines come from the SAME function, and
    the field layout (`- <pos> <id6> [<set>] <action> -> <disposition>: <reason>`) is identical up to
    the reason text. Two renderers would drift exactly as `render_action_preview`'s docstring records.
    """
    skipped = pol.render_item_disposition(
        "abc123",
        "execute",
        "reviewed",
        "needs_human_approval (frozen)",
        position=1,
        setid="wtiso",
    )
    acted = pol.render_item_disposition(
        "def456", "execute", "executed", None, position=2, setid="wtiso"
    )
    assert (
        skipped
        == "- 01 abc123 [wtiso] execute -> reviewed: needs_human_approval (frozen)"
    )
    assert acted == "- 02 def456 [wtiso] execute -> executed: acted on by this run"
    # The SHAPE is identical: same prefix, same arrow, same colon, same field count.
    for line in (skipped, acted):
        head, _, reason = line.partition(": ")
        assert head.startswith("- ")
        assert " -> " in head
        assert reason  # never blank, which is what keeps the two shapes comparable


def test_an_acted_on_artifact_never_renders_a_blank_reason():
    """A blank reason reads as missing information, so the acted-on case carries a fixed label."""
    assert pol.ACTED_REASON_LABEL in pol.render_item_disposition(
        "a", "execute", "executed"
    )
    assert pol.ACTED_REASON_LABEL in pol.render_item_disposition(
        "a", "execute", "executed", "   "
    )


def test_the_skip_reason_set_is_closed_and_uses_the_spec_names():
    """Spec `25kzda` supplies EVERY name; this plan mints none (E-02).

    The four dependency/approval/capability names come from 5.4's "Stable dependency reason codes"
    and 5.7's failure-class table; `ipd_already_executed` from Section 6's worked example item 8; and
    `type_or_status_not_runnable` from 5.7's "Non-runnable state/type" row.
    """
    assert set(pol.SKIP_REASONS) == {
        "needs_human_approval",
        "dependency_not_met",
        "dependency_not_met_external",
        "ipd_already_executed",
        "type_or_status_not_runnable",
        "host_capability_unavailable",
    }
    # Every reason is documented with WHERE its value is read from, and glossed for a human.
    for code in pol.SKIP_REASONS:
        assert pol.SKIP_REASON_SOURCES[code].strip()
        assert pol.SKIP_REASON_LABELS[code].strip()
    # CLOSED: an invented seventh reason is refused rather than silently rendered.
    with pytest.raises(ValueError) as err:
        pol.skip_reason_text("gate_refused")
    assert "unknown skip reason code" in str(err.value)


def test_every_named_reason_renders_a_line_carrying_its_code_and_gloss():
    """The code is the machine-stable half; the gloss is what makes the line legible."""
    for code in pol.SKIP_REASONS:
        line = pol.render_item_disposition_for_reason(
            "abc123", "execute", "reviewed", code
        )
        assert code in line
        assert pol.SKIP_REASON_LABELS[code] in line


def test_the_dependency_reason_names_the_unmet_dependency():
    """The backlog item requires this specifically, so it is asserted specifically."""
    lines = pol.render_queue_dispositions(
        [
            _queue_entry(
                status="dependency-blocked",
                unsatisfied_dependencies=["executed:zz5yxq"],
                unsatisfied_dependency_reasons={
                    "executed:zz5yxq": "in-run target zz5yxq is 'reviewed'"
                },
            )
        ]
    )
    assert len(lines) == 2  # header + one artifact
    assert "dependency_not_met" in lines[1]
    assert "executed:zz5yxq" in lines[1]
    assert "in-run target zz5yxq is 'reviewed'" in lines[1]


def test_an_external_unsatisfiable_dependency_takes_the_external_reason_code():
    """`edge_satisfied`'s own wording for an out-of-queue target selects the spec's EXTERNAL code."""
    lines = pol.render_queue_dispositions(
        [
            _queue_entry(
                status="dependency-blocked",
                unsatisfied_dependencies=["executed:aaa111"],
                unsatisfied_dependency_reasons={
                    "executed:aaa111": (
                        "executed:aaa111: external target aaa111 is 'approved' (directory 'pending'), "
                        "it is not in this run, so it cannot become satisfied here"
                    )
                },
            )
        ]
    )
    assert "dependency_not_met_external" in lines[1]


def test_the_needs_approval_line_explains_reviewed_to_a_reader_who_does_not_know_it():
    """THE MEASURED DEFECT (backlog `em0z50`): `reviewed` displayed with no explanation.

    The summary table already shows `reviewed` for this item. What was missing is the REASON, so this
    asserts the reason is present and mentions approval in words, not merely that a line exists.
    """
    lines = pol.render_queue_dispositions([_queue_entry(needs_input=True)])
    assert len(lines) == 2
    assert "needs_human_approval" in lines[1]
    assert "approval" in lines[1]


def test_one_line_per_matched_artifact_regardless_of_attempt_count():
    """The once-per-artifact property, which is what makes child 03's counts sum (E-03)."""
    queue = [
        _queue_entry(position=1, id6="abc123", needs_input=True),
        _queue_entry(
            position=2,
            id6="def456",
            status="executed",
            attempts=[{"n": 1}, {"n": 2}, {"n": 3}],
        ),
        _queue_entry(position=3, id6="ghi789", status="executed"),
        _queue_entry(position=4, id6="jkl012", status="not-attempted"),
    ]
    lines = pol.render_queue_dispositions(queue)
    assert lines[0] == pol.DISPOSITION_HEADER
    assert len(lines) - 1 == len(queue)
    # Four DISTINCT dispositions, each explained; the three-attempt item still gets exactly one line.
    assert sum(1 for line in lines if "def456" in line) == 1
    assert "needs_human_approval" in lines[1]
    assert pol.ACTED_REASON_LABEL in lines[2]
    assert "ipd_already_executed" in lines[3]
    assert "type_or_status_not_runnable" in lines[4]


def test_an_empty_selection_renders_no_header():
    """A stray header over nothing is worse than silence."""
    assert pol.render_queue_dispositions([]) == []


def test_a_recorded_refusal_supplies_the_reason_through_the_owning_plans_reader():
    """E-05's seam: `orchprobe` `r2i1b1`'s record WINS, and this plan defines no record type.

    The reader is INJECTED (that plan's shipped `refusal_of_item`), so this module never imports
    `render_stream` and never reads the refusal key itself.
    """
    from agent_workflows import render_stream

    entry = _queue_entry(status="merge-conflict")
    render_stream.record_refusal(
        entry,
        code="merge-conflict",
        reason="the lane conflicted with main on two files",
        remedy="inspect the lane, resolve, then re-integrate",
    )
    lines = pol.render_queue_dispositions(
        [entry], refusal_reader=render_stream.refusal_of_item
    )
    assert "the lane conflicted with main on two files" in lines[1]
    # The REMEDY is deliberately NOT duplicated here: the summary's diagnostics block already prints it.
    assert "inspect the lane" not in lines[1]
    # Without the reader, no refusal is consulted at all.
    assert "conflicted" not in pol.render_queue_dispositions([entry])[1]


def test_the_refusal_record_outranks_an_inferable_reason():
    """A producer that said WHY is more specific than anything inferable from a status."""
    from agent_workflows import render_stream

    entry = _queue_entry(needs_input=True)
    render_stream.record_refusal(
        entry, code="custom", reason="a specific recorded reason", remedy="do the thing"
    )
    line = pol.render_queue_dispositions(
        [entry], refusal_reader=render_stream.refusal_of_item
    )[1]
    assert "a specific recorded reason" in line
    assert "needs_human_approval" not in line


def test_the_renderer_is_pure_no_print_no_filesystem():
    """PURITY IS A PROPERTY TO PRESERVE (the module's own convention), so it is asserted."""
    import io
    import contextlib

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        out = pol.render_queue_dispositions([_queue_entry(needs_input=True)])
    assert buf.getvalue() == ""
    assert isinstance(out, list) and out


def test_the_module_gained_no_first_party_import():
    """The two-import purity other plans depend on, asserted by AST rather than by eye."""
    import ast
    import pathlib

    tree = ast.parse(pathlib.Path(str(pol.__file__)).read_text(encoding="utf-8"))
    first_party = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "agent_workflows":
            first_party |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
            "agent_workflows."
        ):
            first_party.add((node.module or "").split(".", 1)[1])
        elif isinstance(node, ast.Import):
            for a in node.names:
                if a.name.startswith("agent_workflows"):
                    first_party.add(a.name.split(".", 1)[1])
    assert first_party == {"selectors", "status_set"}


def test_a_dependency_token_that_already_carries_its_reason_is_not_double_explained():
    """The TWO producers of `unsatisfied_dependencies` write DIFFERENT shapes (measured).

    The drain path writes a BARE token plus a separate reason MAP, while `cascade_dependency_blocked`
    writes the reason INTO the token and no map. A `reasons.get(d, "unsatisfied")` fallback renders the
    cascade's token as `executed:aaa111 (target reviewed) (unsatisfied)`: two contradictory reasons on
    one line. This pins the fix.
    """
    line = pol.render_queue_dispositions(
        [
            _queue_entry(
                status="dependency-blocked",
                unsatisfied_dependencies=["executed:aaa111 (target reviewed)"],
            )
        ]
    )[1]
    assert "executed:aaa111 (target reviewed)" in line
    assert "(unsatisfied)" not in line
    # And the OTHER producer's shape still renders its recorded reason.
    other = pol.render_queue_dispositions(
        [
            _queue_entry(
                status="dependency-blocked",
                unsatisfied_dependencies=["executed:bbb222"],
                unsatisfied_dependency_reasons={
                    "executed:bbb222": "in-run target is 'reviewed'"
                },
            )
        ]
    )[1]
    assert "executed:bbb222 (in-run target is 'reviewed')" in other


# --------------------------------------------------------------------------------------------------
# The END-OF-RUN DISPOSITION SUMMARY (`runnoop` Order 03, `bsc457`)
# --------------------------------------------------------------------------------------------------


def test_a_run_that_acted_on_nothing_still_gets_a_summary_naming_every_artifact():
    """THE MEASURED INCIDENT (backlog `em0z50`), at the pure-renderer level.

    `aw oc run wtiso` matched 8 plans, acted on NONE, and no surface said so. The counts must SUM to
    the number matched, which is the property worth asserting rather than any individual number.
    """
    queue = [
        _queue_entry(position=i, id6="id%04d" % i, needs_input=True)
        for i in range(1, 9)
    ]
    lines = pol.render_disposition_summary(queue)
    text = "\n".join(lines)
    assert pol.SUMMARY_HEADER in text
    # The HONEST VERDICT: the table says COMPLETED at 100% for this same queue.
    assert "NO WORK WAS PERFORMED" in text
    assert "matched 8 artifact(s) and acted on NONE" in text
    # The count, and the remedy beside it, in the shape the backlog item specifies.
    assert "needs_human_approval (8)" in text
    assert "aw ipd set approved <id6> --by-human" in text
    rows = pol.summarize_dispositions(queue)
    assert sum(count for _c, count, _r in rows) == len(queue)


def test_the_counts_sum_to_the_number_matched_for_a_mixed_queue():
    """The partition property: every entry lands in exactly one bucket, so nothing is lost or double-counted."""
    queue = [
        _queue_entry(position=1, id6="aaa111", needs_input=True),
        _queue_entry(position=2, id6="bbb222", status="executed"),
        _queue_entry(position=3, id6="ccc333", status="not-attempted"),
        _queue_entry(
            position=4,
            id6="ddd444",
            status="dependency-blocked",
            unsatisfied_dependencies=["executed:aaa111"],
        ),
        _queue_entry(position=5, id6="eee555", status="executed", attempts=[{"n": 1}]),
    ]
    rows = pol.summarize_dispositions(queue)
    assert sum(count for _c, count, _r in rows) == len(queue)
    text = "\n".join(pol.render_disposition_summary(queue))
    assert "total: 5 matched, 1 acted on, 4 not acted on" in text


def test_every_actionable_disposition_carries_a_remedy_and_terminal_ones_do_not():
    """A needed-no-remedy disposition and an unknown one must render DIFFERENTLY, never alike."""
    # Actionable -> a remedy.
    for code in pol.DISPOSITION_REMEDIES:
        assert pol.remedy_for_disposition(code) == pol.DISPOSITION_REMEDIES[code]
    # Legitimately terminal -> None, meaning "nothing to do, and that is correct".
    for code in pol.DISPOSITIONS_NEEDING_NO_REMEDY:
        assert pol.remedy_for_disposition(code) is None
    # Unrecognized -> an explicit admission, NOT silence.
    unknown = pol.remedy_for_disposition("a_reason_nobody_wrote_a_remedy_for")
    assert unknown == pol.REMEDY_UNKNOWN_TEXT
    assert unknown != pol.remedy_for_disposition(pol.SKIP_ALREADY_EXECUTED)


def test_every_closed_skip_reason_resolves_to_a_remedy_or_an_explicit_no_remedy():
    """A new reason cannot be added without an author noticing its remedy is missing."""
    for code in pol.SKIP_REASONS:
        assert (
            code in pol.DISPOSITION_REMEDIES
            or code in pol.DISPOSITIONS_NEEDING_NO_REMEDY
        ), f"{code} has neither a remedy nor an explicit 'needs none' marker"
        assert pol.remedy_for_disposition(code) != pol.REMEDY_UNKNOWN_TEXT


def test_the_unknown_and_the_no_remedy_cases_render_differently():
    """Asserted on the RENDERED block, because rendering a gap as a correct outcome is the defect."""
    known = "\n".join(pol.render_disposition_summary([_queue_entry(status="executed")]))
    assert "ipd_already_executed (1)" in known
    assert pol.REMEDY_UNKNOWN_TEXT not in known

    class _Refusal:
        code = "a_brand_new_refusal_code"
        reason = "something novel happened"
        remedy = ""

    gap = "\n".join(
        pol.render_disposition_summary(
            [_queue_entry(status="blocked")], refusal_reader=lambda _e: _Refusal()
        )
    )
    assert "a_brand_new_refusal_code (1)" in gap
    assert pol.REMEDY_UNKNOWN_TEXT in gap


def test_a_recorded_refusals_own_remedy_is_sourced_not_duplicated():
    """E-06's executed branch: `orchprobe` `r2i1b1` shipped the record, so its remedy is the authority."""
    from agent_workflows import render_stream

    entry = _queue_entry(status="integration-blocked", attempts=[{"n": 1}])
    render_stream.record_refusal(
        entry,
        code="integration-blocked",
        reason="the lane finalized but could not be merged",
        remedy="re-attempt with `aw oc run integrate <run-id>`",
    )
    text = "\n".join(
        pol.render_disposition_summary(
            [entry], refusal_reader=render_stream.refusal_of_item
        )
    )
    assert "integration-blocked (1)" in text
    # The record's OWN remedy, rather than a second copy maintained in this module.
    assert "re-attempt with `aw oc run integrate <run-id>`" in text
    assert "integration-blocked" not in pol.DISPOSITION_REMEDIES


def test_the_line_and_the_summary_cannot_disagree_about_one_artifact():
    """CID-3: ONE disposition vocabulary, because both read the SAME derivation."""
    queue = [
        _queue_entry(position=1, id6="aaa111", needs_input=True),
        _queue_entry(position=2, id6="bbb222", status="executed"),
    ]
    lines = pol.render_queue_dispositions(queue)
    summary = "\n".join(pol.render_disposition_summary(queue))
    for code in (pol.SKIP_NEEDS_HUMAN_APPROVAL, pol.SKIP_ALREADY_EXECUTED):
        assert any(code in line for line in lines[1:])
        assert code in summary


def test_an_acted_on_artifact_is_a_real_bucket_so_the_counts_can_sum():
    """`acted_on` is a KEY, not the absence of one, or the partition would not be total."""
    queue = [_queue_entry(status="executed", attempts=[{"n": 1}])]
    rows = pol.summarize_dispositions(queue)
    assert rows == ((pol.DISPOSITION_ACTED_ON, 1, None),)
    text = "\n".join(pol.render_disposition_summary(queue))
    assert "acted on all 1 artifact(s)" in text


def test_the_summary_orders_attention_first_and_acted_on_last():
    """A reader must reach the things needing action before the total of what went fine."""
    queue = [
        _queue_entry(position=1, id6="aaa111", status="executed", attempts=[{"n": 1}]),
        _queue_entry(position=2, id6="bbb222", needs_input=True),
    ]
    codes = [code for code, _n, _r in pol.summarize_dispositions(queue)]
    assert codes == [pol.SKIP_NEEDS_HUMAN_APPROVAL, pol.DISPOSITION_ACTED_ON]


def test_the_summary_renderer_is_pure_no_print_no_filesystem():
    """Same purity contract the module's other renderers carry."""
    import io
    import contextlib

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        out = pol.render_disposition_summary([_queue_entry(needs_input=True)])
    assert buf.getvalue() == ""
    assert isinstance(out, list) and out


def test_an_empty_selection_renders_no_summary():
    """Nothing matched is NOT the zero-action case; a stray header over nothing is noise."""
    assert pol.render_disposition_summary([]) == []
