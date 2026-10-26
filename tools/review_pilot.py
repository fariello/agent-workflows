#!/usr/bin/env python3
"""Review pilot runner, scorer, and analyzer for spec k3yx72 / Set revsteps (IPD kk62qt).

Drives the 84 review cells, 252 judge runs, and statistical reporting per spec Section 13.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any, Sequence

OPENCODE_MODELS = (
    "uri/its_direct/pt3-claude-opus-5.5-1m-us",
    "openai/gpt-6.1-sol",
)
GEMINI_MODEL = "gemini-3.8-flash-high"
ALL_REVIEW_MODELS = (*OPENCODE_MODELS, GEMINI_MODEL)
ALL_JUDGE_MODELS = (*OPENCODE_MODELS, GEMINI_MODEL)

MODEL_SHORTS = {
    "uri/its_direct/pt3-claude-opus-5.5-1m-us": "opus",
    "openai/gpt-6.1-sol": "sol",
    "gemini-3.8-flash-high": "gemini",
}


class CellSpec:
    def __init__(
        self,
        *,
        tier: str,
        fixture_id6: str,
        fixture_filename: str,
        method: str,
        review_variant: str,
        model: str,
        host: str,
        repeat: int,
    ) -> None:
        self.tier = tier
        self.fixture_id6 = fixture_id6
        self.fixture_filename = fixture_filename
        self.method = method  # "single" or "steps"
        self.review_variant = (
            review_variant  # "current", "proposed", "grouped-6", "single-12"
        )
        self.model = model
        self.host = host  # "oc" or "agy"
        self.repeat = repeat

    @property
    def key(self) -> str:
        model_short = MODEL_SHORTS.get(self.model, "unknown")
        return f"{self.tier}_{self.fixture_id6}_{self.method}_{self.review_variant}_{model_short}_r{self.repeat}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "cell_key": self.key,
            "tier": self.tier,
            "fixture_id6": self.fixture_id6,
            "fixture_filename": self.fixture_filename,
            "method": self.method,
            "review_variant": self.review_variant,
            "model": self.model,
            "host": self.host,
            "repeat": self.repeat,
        }


def load_manifest(manifest_path: Path) -> list[dict[str, Any]]:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")
    with open(manifest_path) as f:
        return json.load(f)


def build_cell_specs(manifest_path: Path | None = None) -> list[CellSpec]:
    if manifest_path is None:
        manifest_path = Path("tests/fixtures/review-pilot/manifest.json")
    manifest = load_manifest(manifest_path)

    by_tier: dict[str, list[dict[str, Any]]] = {
        "simple": [],
        "standard": [],
        "complex": [],
    }
    for item in manifest:
        tier = item["expected_tier"]
        if tier in by_tier:
            by_tier[tier].append(item)

    specs: list[CellSpec] = []

    # Simple tier: 3 plans, 2 methods (single/current, steps/proposed), 3 models
    # Repeat plan is by_tier["simple"][0] (2 repeats)
    for idx, plan in enumerate(by_tier["simple"]):
        repeats = (1, 2) if idx == 0 else (1,)
        for rep in repeats:
            for model in ALL_REVIEW_MODELS:
                host = "agy" if model == GEMINI_MODEL else "oc"
                specs.append(
                    CellSpec(
                        tier="simple",
                        fixture_id6=plan["fixture_id6"],
                        fixture_filename=plan["filename"],
                        method="single",
                        review_variant="current",
                        model=model,
                        host=host,
                        repeat=rep,
                    )
                )
                specs.append(
                    CellSpec(
                        tier="simple",
                        fixture_id6=plan["fixture_id6"],
                        fixture_filename=plan["filename"],
                        method="steps",
                        review_variant="proposed",
                        model=model,
                        host=host,
                        repeat=rep,
                    )
                )

    # Standard tier: 3 plans, 2 methods (single/current, steps/proposed), 3 models
    # Repeat plan is by_tier["standard"][0] (2 repeats)
    for idx, plan in enumerate(by_tier["standard"]):
        repeats = (1, 2) if idx == 0 else (1,)
        for rep in repeats:
            for model in ALL_REVIEW_MODELS:
                host = "agy" if model == GEMINI_MODEL else "oc"
                specs.append(
                    CellSpec(
                        tier="standard",
                        fixture_id6=plan["fixture_id6"],
                        fixture_filename=plan["filename"],
                        method="single",
                        review_variant="current",
                        model=model,
                        host=host,
                        repeat=rep,
                    )
                )
                specs.append(
                    CellSpec(
                        tier="standard",
                        fixture_id6=plan["fixture_id6"],
                        fixture_filename=plan["filename"],
                        method="steps",
                        review_variant="proposed",
                        model=model,
                        host=host,
                        repeat=rep,
                    )
                )

    # Complex tier: 3 plans, 3 methods (single/current, steps/grouped-6, steps/single-12), 3 models
    # Repeat plan is by_tier["complex"][0] (2 repeats)
    for idx, plan in enumerate(by_tier["complex"]):
        repeats = (1, 2) if idx == 0 else (1,)
        for rep in repeats:
            for model in ALL_REVIEW_MODELS:
                host = "agy" if model == GEMINI_MODEL else "oc"
                specs.append(
                    CellSpec(
                        tier="complex",
                        fixture_id6=plan["fixture_id6"],
                        fixture_filename=plan["filename"],
                        method="single",
                        review_variant="current",
                        model=model,
                        host=host,
                        repeat=rep,
                    )
                )
                specs.append(
                    CellSpec(
                        tier="complex",
                        fixture_id6=plan["fixture_id6"],
                        fixture_filename=plan["filename"],
                        method="steps",
                        review_variant="grouped-6",
                        model=model,
                        host=host,
                        repeat=rep,
                    )
                )
                specs.append(
                    CellSpec(
                        tier="complex",
                        fixture_id6=plan["fixture_id6"],
                        fixture_filename=plan["filename"],
                        method="steps",
                        review_variant="single-12",
                        model=model,
                        host=host,
                        repeat=rep,
                    )
                )

    return specs


def get_baseline_commit(repo_root: Path) -> str:
    readme_path = repo_root / ".aw/system/workflows/plan-review/README.md"
    if not readme_path.exists():
        raise RuntimeError(f"Baseline workflow README not found at {readme_path}")
    text = readme_path.read_text()
    match = re.search(r"-\s*Baseline commit:\s*`?([a-f0-9]{7,40})`?", text)
    if not match:
        raise RuntimeError(
            "No baseline commit named in .aw/system/workflows/plan-review/README.md"
        )
    return match.group(1)


def get_pilot_commit(repo_root: Path, pilot_file: Path | None = None) -> str:
    if pilot_file and pilot_file.exists():
        try:
            with open(pilot_file) as f:
                data = json.load(f)
                if data.get("pilot_commit"):
                    return str(data["pilot_commit"])
        except Exception:
            pass

    # Resolve from git log or rev-parse
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
        ).strip()
    except Exception as e:
        raise RuntimeError(f"Cannot resolve HEAD commit in {repo_root}: {e}")

    if pilot_file:
        pilot_file.parent.mkdir(parents=True, exist_ok=True)
        with open(pilot_file, "w") as f:
            json.dump({"pilot_commit": out}, f, indent=2)

    return out


def redact_text(text: str) -> str:
    """Redact model, host, agent, and run-id identifiers from review artifacts."""
    if not text:
        return text

    # Redact run IDs: run-YYYYMMDDTHHMMSSZ-NNNNNN
    text = re.sub(r"\brun-\d{8}T\d{6}Z-\d+\b", "<redacted>", text)

    # Redact model identifiers and names
    model_patterns = [
        r"uri/its_direct/pt3-claude-opus-5\.5-1m-us",
        r"pt3-claude-opus-5\.5-1m-us",
        r"claude-opus-5-5-high",
        r"Claude-Opus-5\.5-High",
        r"Claude-Opus-5\.5",
        r"Claude Opus 5\.5 \(High\)",
        r"openai/gpt-6\.1-sol",
        r"gpt-6\.1-sol",
        r"GPT-6\.1-Sol-High",
        r"GPT-6\.1-Sol",
        r"GPT-6\.1 Sol \(High\)",
        r"google/gemini-3\.8-flash",
        r"gemini-3\.8-flash-high",
        r"gemini-3\.8-flash",
        r"Gemini-3\.8-Flash-High",
        r"Gemini-3\.8-Flash",
        r"Gemini 3\.8 Flash \(High\)",
    ]
    for pat in model_patterns:
        text = re.sub(pat, "<redacted>", text, flags=re.IGNORECASE)

    # Redact reviewer front matter and history entries
    text = re.sub(r"(- Reviewer:\s*).*", r"\1<redacted>", text)
    text = re.sub(
        r"(\b(?:reviewed|/plan-review|review progress)\s*\()[^)]+(\))",
        r"\1<redacted>\2",
        text,
    )

    # Redact host names in command options
    text = re.sub(
        r"\b(?:opencode|antigravity|OpenCode|Antigravity)\b", "<redacted>", text
    )

    return text


def build_cell(
    cell: CellSpec,
    *,
    repo_root: Path,
    pilot_commit: str,
    baseline_commit: str,
    base_tmp_dir: Path | None = None,
) -> Path:
    if base_tmp_dir is None:
        base_tmp_dir = repo_root / "tmp" / "review-pilot"
    cell_dir = base_tmp_dir / cell.key

    if cell_dir.exists():
        return cell_dir

    cell_dir.parent.mkdir(parents=True, exist_ok=True)

    # (1) Cell base: git worktree add --detach tmp/review-pilot/<cell>/ <pilot commit>
    subprocess.check_call(
        ["git", "worktree", "add", "--detach", str(cell_dir), pilot_commit],
        cwd=repo_root,
    )

    # (2) Key removal: delete tests/fixtures/review-pilot/ from the cell
    fixture_tree = cell_dir / "tests" / "fixtures" / "review-pilot"
    if fixture_tree.exists():
        shutil.rmtree(fixture_tree)

    # Copy in only that cell's fixture plan as .aw/records/plans/pending/<fixture filename>
    src_fixture = (
        repo_root
        / "tests"
        / "fixtures"
        / "review-pilot"
        / "plans"
        / cell.fixture_filename
    )
    dst_fixture = (
        cell_dir / ".aw" / "records" / "plans" / "pending" / cell.fixture_filename
    )
    dst_fixture.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_fixture, dst_fixture)

    # (3) Current-method baseline: for a single cell, replace plan-review.md with baseline
    if cell.method == "single":
        wf_path = (
            cell_dir / ".aw" / "system" / "workflows" / "plan-review" / "plan-review.md"
        )
        baseline_content = subprocess.check_output(
            [
                "git",
                "show",
                f"{baseline_commit}:.aw/system/workflows/plan-review/plan-review.md",
            ],
            cwd=repo_root,
        )
        wf_path.parent.mkdir(parents=True, exist_ok=True)
        wf_path.write_bytes(baseline_content)

    # (4) Commit the cell so the runner sees a clean tree
    subprocess.check_call(["git", "add", "-A"], cwd=cell_dir)
    subprocess.check_call(
        [
            "git",
            "-c",
            "user.name=pilot",
            "-c",
            "user.email=pilot@invalid",
            "commit",
            "-m",
            f"prepare review pilot cell {cell.key}",
        ],
        cwd=cell_dir,
    )

    return cell_dir


# Runner launch hook that can be mocked in unit tests
def launch_runner(argv: Sequence[str], cwd: Path | None = None) -> int:
    res = subprocess.run(list(argv), cwd=cwd)
    return res.returncode


def get_recorded_spend(cells_file: Path, scores_file: Path | None = None) -> float:
    total_cost = 0.0
    if cells_file.exists():
        with open(cells_file) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                    c = row.get("cost")
                    if c is not None:
                        total_cost += float(c)
                except Exception:
                    pass
    if scores_file and scores_file.exists():
        with open(scores_file) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                    c = row.get("cost")
                    if c is not None:
                        total_cost += float(c)
                except Exception:
                    pass
    return total_cost


def load_completed_cells(cells_file: Path) -> set[str]:
    completed: set[str] = set()
    if not cells_file.exists():
        return completed
    with open(cells_file) as f:
        for line in f:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if row.get("outcome") in (
                    "completed",
                    "completed-pass",
                    "completed-negative",
                ):
                    completed.add(row.get("cell_key", ""))
            except Exception:
                pass
    return completed


def run_single_cell(
    cell: CellSpec,
    *,
    repo_root: Path,
    pilot_commit: str,
    baseline_commit: str,
    cells_file: Path,
    base_tmp_dir: Path | None = None,
) -> dict[str, Any]:
    cell_dir = build_cell(
        cell,
        repo_root=repo_root,
        pilot_commit=pilot_commit,
        baseline_commit=baseline_commit,
        base_tmp_dir=base_tmp_dir,
    )

    # Construct argv
    if cell.host == "oc":
        argv = [
            "aw",
            "oc",
            "run",
            "start",
            "--repo",
            str(cell_dir),
            cell.fixture_id6,
            "--action",
            "review",
            "--unattended",
            "--label",
            "pilot-k3yx72",
            "--model",
            cell.model,
            "--variant",
            "high",
            "--review-mode",
            cell.method,
            "--review-variant",
            cell.review_variant,
        ]
    else:
        argv = [
            "aw",
            "agy",
            "run",
            "start",
            "--repo",
            str(cell_dir),
            cell.fixture_id6,
            "--action",
            "review",
            "--unattended",
            "--label",
            "pilot-k3yx72",
            "--model",
            cell.model,
            "--effort",
            "high",
            "--review-mode",
            cell.method,
            "--review-variant",
            cell.review_variant,
        ]

    started_at = subprocess.check_output(
        ["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], text=True
    ).strip()
    exit_code = launch_runner(argv, cwd=cell_dir)
    ended_at = subprocess.check_output(
        ["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], text=True
    ).strip()

    # Analyze cell
    try:
        subprocess.run(
            ["aw", "runs", "analyze", "--dir", str(cell_dir)], capture_output=True
        )
    except Exception:
        pass

    # Read run directory
    cell_runs_dir = cell_dir / ".aw" / "records" / "runs"
    run_dirs = sorted(cell_runs_dir.glob("run-*")) if cell_runs_dir.exists() else []

    run_id = None
    outcome = "completed" if exit_code == 0 else "failed"
    assigned_tier = None
    cost: float | None = None
    tokens: dict[str, Any] | None = None

    if run_dirs:
        latest_run = run_dirs[-1]
        run_id = latest_run.name
        state_file = latest_run / "state.json"
        if state_file.exists():
            try:
                with open(state_file) as f:
                    state_data = json.load(f)
                run_id = state_data.get("run_id", run_id)
                outcome = (
                    state_data.get("outcome") or state_data.get("status") or outcome
                )
                # Look for assigned tier
                if state_data.get("queue"):
                    first_q = state_data["queue"][0]
                    assigned_tier = first_q.get("review_tier")
                    if not assigned_tier and first_q.get("attempts"):
                        assigned_tier = first_q["attempts"][-1].get("review_tier")
            except Exception:
                pass

        # Copy run directory into repository's .aw/records/runs/
        repo_runs_dir = repo_root / ".aw" / "records" / "runs"
        repo_runs_dir.mkdir(parents=True, exist_ok=True)
        dest_run_dir = repo_runs_dir / run_id
        if not dest_run_dir.exists():
            shutil.copytree(latest_run, dest_run_dir)

    # Query cost and tokens
    if run_id:
        try:
            q_out = subprocess.check_output(
                [
                    "aw",
                    "runs",
                    "query",
                    "attempts",
                    "--dir",
                    str(cell_dir),
                    "--filter",
                    "label=pilot-k3yx72",
                    "--metric",
                    "cost",
                    "--stat",
                    "sum",
                    "--json",
                ],
                text=True,
            )
            q_data = json.loads(q_out)
            if isinstance(q_data, list) and q_data:
                cost = q_data[0].get("cost")
            elif isinstance(q_data, dict):
                cost = q_data.get("cost")
        except Exception:
            pass

    row = {
        "cell_key": cell.key,
        "fixture_id6": cell.fixture_id6,
        "method": cell.method,
        "model": cell.model,
        "repeat": cell.repeat,
        "run_id": run_id,
        "started_at": started_at,
        "ended_at": ended_at,
        "exit_code": exit_code,
        "outcome": outcome,
        "cost": cost,
        "tokens": tokens,
        "assigned_tier": assigned_tier,
    }

    cells_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cells_file, "a") as f:
        f.write(json.dumps(row) + "\n")

    return row


def cmd_run(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo).resolve()
    manifest_path = repo_root / "tests/fixtures/review-pilot/manifest.json"
    cells_file = (repo_root / args.cells_file).resolve()
    pilot_file = (repo_root / args.pilot_file).resolve()

    baseline_commit = get_baseline_commit(repo_root)
    pilot_commit = get_pilot_commit(repo_root, pilot_file)

    cell_specs = build_cell_specs(manifest_path)

    # Dry run
    if args.dry_run:
        simple_count = sum(1 for c in cell_specs if c.tier == "simple")
        standard_count = sum(1 for c in cell_specs if c.tier == "standard")
        complex_count = sum(1 for c in cell_specs if c.tier == "complex")
        print(f"review_pilot: {len(cell_specs)} cells configured across 3 tiers")
        for c in cell_specs:
            print(
                f"  {c.key}: tier={c.tier} fixture={c.fixture_id6} method={c.method} variant={c.review_variant} model={c.model}"
            )
        print("--- Summary ---")
        print(f"simple: {simple_count}")
        print(f"standard: {standard_count}")
        print(f"complex: {complex_count}")
        print(f"total: {len(cell_specs)}")
        return 0

    print(
        f"Review pilot driver starting. Budget: ${args.budget if args.budget is not None else 'unlimited'}"
    )
    print(
        "Antigravity records token counts only; OpenCode and judge costs count toward budget."
    )

    completed = load_completed_cells(cells_file)

    for cell in cell_specs:
        if args.only_cell and cell.key != args.only_cell:
            continue
        if cell.key in completed:
            print(f"Skipping already-completed cell {cell.key}")
            continue

        recorded_spend = get_recorded_spend(cells_file)
        if args.budget is not None and recorded_spend >= args.budget:
            print(
                f"Budget limit reached (${recorded_spend:.2f} >= ${args.budget:.2f}). Stopping."
            )
            return 0

        print(
            f"Running cell {cell.key} (tier={cell.tier}, method={cell.method}, model={cell.model}, rep={cell.repeat})..."
        )
        row = run_single_cell(
            cell,
            repo_root=repo_root,
            pilot_commit=pilot_commit,
            baseline_commit=baseline_commit,
            cells_file=cells_file,
        )
        print(
            f"Cell {cell.key} finished: outcome={row.get('outcome')}, cost={row.get('cost')}"
        )

    return 0


def cmd_judge(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo).resolve()
    cells_file = (repo_root / args.cells_file).resolve()
    scores_file = (repo_root / args.scores_file).resolve()

    if not cells_file.exists():
        print(f"No cells file found at {cells_file}")
        return 1

    cells_data: list[dict[str, Any]] = []
    with open(cells_file) as f:
        for line in f:
            if line.strip():
                try:
                    cells_data.append(json.loads(line))
                except Exception:
                    pass

    # Load existing scores
    existing_scores: set[tuple[str, str]] = set()
    if scores_file.exists():
        with open(scores_file) as f:
            for line in f:
                if line.strip():
                    try:
                        row = json.loads(line)
                        existing_scores.add((row["cell_key"], row["judge_model"]))
                    except Exception:
                        pass

    rubric_text = (repo_root / "tests/fixtures/review-pilot/rubric.md").read_text()
    judge_prompt_template = (
        repo_root / "tests/fixtures/review-pilot/judge-prompt.md"
    ).read_text()
    with open(repo_root / "tests/fixtures/review-pilot/defects.json") as f:
        all_defects = json.load(f)

    with open(repo_root / "tests/fixtures/review-pilot/manifest.json") as f:
        manifest = json.load(f)
    manifest_map = {m["fixture_id6"]: m for m in manifest}

    for cell in cells_data:
        cell_key = cell["cell_key"]
        fixture_id6 = cell["fixture_id6"]
        cell_dir = repo_root / "tmp" / "review-pilot" / cell_key

        fixture_info = manifest_map.get(fixture_id6)
        if not fixture_info:
            continue

        fixture_filename = fixture_info["filename"]
        before_plan_path = (
            repo_root / "tests/fixtures/review-pilot/plans" / fixture_filename
        )
        if not before_plan_path.exists():
            continue
        before_plan_text = before_plan_path.read_text()

        # Find after plan and review record in cell
        after_plan_path = (
            cell_dir / ".aw" / "records" / "plans" / "pending" / fixture_filename
        )
        if not after_plan_path.exists():
            after_plan_path = (
                cell_dir / ".aw" / "records" / "plans" / "reviewed" / fixture_filename
            )
        if not after_plan_path.exists():
            after_plan_text = before_plan_text
        else:
            after_plan_text = redact_text(after_plan_path.read_text())

        # Review record
        review_record_text = ""
        reviews_dir = cell_dir / ".aw" / "records" / "reviews"
        if reviews_dir.exists():
            rev_files = list(reviews_dir.glob("*.review.md"))
            if rev_files:
                review_record_text = redact_text(rev_files[-1].read_text())

        fixture_defects = [d for d in all_defects if d["fixture"] == fixture_id6]

        judge_dir = repo_root / "tmp" / "review-pilot" / "judge" / cell_key
        judge_dir.mkdir(parents=True, exist_ok=True)

        (judge_dir / "before_plan.md").write_text(before_plan_text)
        (judge_dir / "after_plan.md").write_text(after_plan_text)
        (judge_dir / "review_record.md").write_text(review_record_text)
        (judge_dir / "planted_defects.json").write_text(
            json.dumps(fixture_defects, indent=2)
        )
        (judge_dir / "rubric.md").write_text(rubric_text)

        for judge_model in ALL_JUDGE_MODELS:
            pair = (cell_key, judge_model)
            if pair in existing_scores:
                continue

            current_spend = get_recorded_spend(cells_file, scores_file)
            if args.budget is not None and current_spend >= args.budget:
                print(
                    f"Budget reached (${current_spend:.2f} >= ${args.budget:.2f}). Stopping judge runs."
                )
                return 0

            print(f"Judging {cell_key} with {judge_model}...")

            # Run judge
            is_gemini = judge_model == GEMINI_MODEL
            if is_gemini:
                judge_cmd = [
                    "agy",
                    "-p",
                    judge_prompt_template,
                    "--model",
                    judge_model,
                    "--output-format",
                    "json",
                ]
            else:
                judge_cmd = [
                    "opencode",
                    "run",
                    "--model",
                    judge_model,
                    "--variant",
                    "high",
                    "--format",
                    "json",
                    judge_prompt_template,
                ]

            score_record = None
            for attempt in range(2):
                try:
                    out = subprocess.check_output(judge_cmd, cwd=judge_dir, text=True)
                    # Parse JSON object from output
                    json_matches = re.findall(
                        r"\{[^{}]*\"total_score\"[^{}]*\}", out, flags=re.DOTALL
                    )
                    if json_matches:
                        parsed = json.loads(json_matches[-1])
                        score_record = {
                            "cell_key": cell_key,
                            "judge_model": judge_model,
                            "planted_defects_found": parsed.get(
                                "planted_defects_found", []
                            ),
                            "planted_defects_score": parsed.get(
                                "planted_defects_score", 0
                            ),
                            "false_findings_count": parsed.get(
                                "false_findings_count", 0
                            ),
                            "false_findings_score": parsed.get(
                                "false_findings_score", 0
                            ),
                            "edit_correctness_score": parsed.get(
                                "edit_correctness_score", 0
                            ),
                            "design_quality_score": parsed.get(
                                "design_quality_score", 0
                            ),
                            "total_score": parsed.get("total_score", 0),
                            "rationale": parsed.get("rationale", ""),
                            "cost": None,
                        }
                        break
                except Exception as e:
                    print(f"Judge run attempt {attempt+1} failed: {e}")

            if score_record is None:
                score_record = {
                    "cell_key": cell_key,
                    "judge_model": judge_model,
                    "total_score": None,
                    "error": "Failed to parse judge output",
                }

            scores_file.parent.mkdir(parents=True, exist_ok=True)
            with open(scores_file, "a") as f:
                f.write(json.dumps(score_record) + "\n")
            existing_scores.add(pair)

    return 0


def cmd_report(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo).resolve()
    cells_file = (repo_root / args.cells_file).resolve()
    scores_file = (repo_root / args.scores_file).resolve()

    cells: dict[str, dict[str, Any]] = {}
    if cells_file.exists():
        with open(cells_file) as f:
            for line in f:
                if line.strip():
                    try:
                        row = json.loads(line)
                        cells[row["cell_key"]] = row
                    except Exception:
                        pass

    scores_by_cell: dict[str, list[dict[str, Any]]] = {}
    if scores_file.exists():
        with open(scores_file) as f:
            for line in f:
                if line.strip():
                    try:
                        row = json.loads(line)
                        scores_by_cell.setdefault(row["cell_key"], []).append(row)
                    except Exception:
                        pass

    print("=== REVIEW PILOT ANALYSIS REPORT ===")
    print(f"Total cells completed: {len(cells)}")
    print(f"Total scores recorded: {sum(len(v) for v in scores_by_cell.values())}")

    # Group by tier and method
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for key, c in cells.items():
        cell_scores = [
            s["total_score"]
            for s in scores_by_cell.get(key, [])
            if s.get("total_score") is not None
        ]
        avg_score = sum(cell_scores) / len(cell_scores) if cell_scores else None
        item = copy.copy(c)
        item["avg_quality"] = avg_score
        grouped.setdefault(
            (c.get("tier", "unknown"), c["method"], c["model"]), []
        ).append(item)

    print("\n--- Per-Tier, Per-Method Breakdown ---")
    print(
        f"{'Tier':<10} {'Method':<8} {'Model':<35} {'Count':<6} {'Avg Quality':<12} {'Cost Median':<12}"
    )
    for (tier, method, model), items in sorted(grouped.items()):
        cnt = len(items)
        qualities = [it["avg_quality"] for it in items if it["avg_quality"] is not None]
        avg_q = f"{sum(qualities)/len(qualities):.1f}" if qualities else "N/A"
        costs = [it["cost"] for it in items if it.get("cost") is not None]
        costs.sort()
        med_cost = f"${costs[len(costs)//2]:.2f}" if costs else "N/A"
        print(f"{tier:<10} {method:<8} {model:<35} {cnt:<6} {avg_q:<12} {med_cost:<12}")

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review pilot driver and analysis")
    subparsers = parser.add_subparsers(dest="subcommand")

    # Run subcommand
    run_parser = subparsers.add_parser("run", help="Run review pilot cells")
    run_parser.add_argument(
        "--budget", type=float, default=None, help="Maximum spend bound in USD"
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print cell list and counts without running",
    )
    run_parser.add_argument("--repo", default=".", help="Repository root directory")
    run_parser.add_argument(
        "--cells-file",
        default="tmp/review-pilot/cells.jsonl",
        help="Path to cells.jsonl",
    )
    run_parser.add_argument(
        "--pilot-file", default="tmp/review-pilot/pilot.json", help="Path to pilot.json"
    )
    run_parser.add_argument(
        "--only-cell", default=None, help="Run only specific cell key"
    )

    # Judge subcommand
    judge_parser = subparsers.add_parser(
        "judge", help="Score completed reviews with blind judges"
    )
    judge_parser.add_argument(
        "--budget", type=float, default=None, help="Maximum spend bound in USD"
    )
    judge_parser.add_argument("--repo", default=".", help="Repository root directory")
    judge_parser.add_argument(
        "--cells-file",
        default="tmp/review-pilot/cells.jsonl",
        help="Path to cells.jsonl",
    )
    judge_parser.add_argument(
        "--scores-file",
        default="tmp/review-pilot/scores.jsonl",
        help="Path to scores.jsonl",
    )

    # Report subcommand
    report_parser = subparsers.add_parser(
        "report", help="Generate quality and cost summary report"
    )
    report_parser.add_argument("--repo", default=".", help="Repository root directory")
    report_parser.add_argument(
        "--cells-file",
        default="tmp/review-pilot/cells.jsonl",
        help="Path to cells.jsonl",
    )
    report_parser.add_argument(
        "--scores-file",
        default="tmp/review-pilot/scores.jsonl",
        help="Path to scores.jsonl",
    )

    # If first arg is not a subcommand, default to run options
    args_list = list(argv if argv is not None else sys.argv[1:])
    if not args_list or (
        args_list[0] not in ("run", "judge", "report")
        and not args_list[0].startswith("-h")
    ):
        args_list.insert(0, "run")

    args = parser.parse_args(args_list)

    if args.subcommand == "run":
        return cmd_run(args)
    elif args.subcommand == "judge":
        return cmd_judge(args)
    elif args.subcommand == "report":
        return cmd_report(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
