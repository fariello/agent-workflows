#!/usr/bin/env bash
# Post-cutover acceptance demonstration and AC-13 measurement script (spec 4sd62s, IPD 33vxoi).
#
# Runs read-only checks on <checkout>, mutating probes inside a throwaway gitignored clone
# (tmp/cxxmyv-demo), and AC-13 warm/cold end-to-end measurements. Deletes every throwaway
# clone on exit and never modifies tracked files in <checkout>.
set -u

usage() {
    cat <<'EOF'
Usage: metastore-acceptance-demo.sh <checkout> <section> [measure options]

Sections:
  readonly    Run read-only acceptance criteria checks (AC-1, AC-1b, AC-7, AC-9, AC-11, AC-30, AC-36, AC-41).
  clone       Run mutating checks in a throwaway clone (AC-2, AC-3, AC-6, AC-16, AC-31, AC-34).
  measure     Run AC-13 before/after measurements and throwaway-clone append timing.
  all         Run readonly, clone, and measure in order.

Measure options (defaults from tub3ir F-02):
  --plan-id6 <id6>                    Plan id6 for bytes-read check (default: cxxmyv)
  --cold-cache-method <text>          Description of cold-cache reset method
  --before-plan-bytes <val>           Before value for plan bytes read (default: 31029)
  --before-find-cold-ms <val>         Before value for cold `aw find plans` ms (default: 855.5)
  --before-find-warm-ms <val>         Before value for warm `aw find plans` ms (default: 843.6)
  --before-attention-cold-ms <val>    Before value for cold `aw attention` ms (default: 6356.7)
  --before-attention-warm-ms <val>    Before value for warm `aw attention` ms (default: 6517.7)
  --exec-plan-id6 <id6>               Executed plan id6 for log size & append timing (default: median-sized)
  --journal-path <path>               Description journal path (default: <checkout>/.aw/state/durable/migrations/m0001/descriptions.jsonl)
EOF
}

if [[ $# -lt 2 ]]; then
    usage >&2
    exit 2
fi

CHECKOUT="$1"
SECTION="$2"
shift 2

# Default AC-13 before values from executed plan tub3ir F-02; callers may override via flags.
PLAN_ID6="cxxmyv"
COLD_CACHE_METHOD="delete .aw/state/index.db* and .aw/cache/*.sqlite* before each cold run"
BEFORE_PLAN_BYTES="31029"
BEFORE_FIND_COLD_MS="855.5"
BEFORE_FIND_WARM_MS="843.6"
BEFORE_ATTENTION_COLD_MS="6356.7"
BEFORE_ATTENTION_WARM_MS="6517.7"
EXEC_PLAN_ID6=""
JOURNAL_PATH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --plan-id6)
            PLAN_ID6="${2:-}"; shift 2 ;;
        --cold-cache-method)
            COLD_CACHE_METHOD="${2:-}"; shift 2 ;;
        --before-plan-bytes)
            BEFORE_PLAN_BYTES="${2:-}"; shift 2 ;;
        --before-find-cold-ms)
            BEFORE_FIND_COLD_MS="${2:-}"; shift 2 ;;
        --before-find-warm-ms)
            BEFORE_FIND_WARM_MS="${2:-}"; shift 2 ;;
        --before-attention-cold-ms)
            BEFORE_ATTENTION_COLD_MS="${2:-}"; shift 2 ;;
        --before-attention-warm-ms)
            BEFORE_ATTENTION_WARM_MS="${2:-}"; shift 2 ;;
        --exec-plan-id6)
            EXEC_PLAN_ID6="${2:-}"; shift 2 ;;
        --journal-path)
            JOURNAL_PATH="${2:-}"; shift 2 ;;
        -h|--help)
            usage; exit 0 ;;
        *)
            echo "error: unknown argument: $1" >&2
            usage >&2
            exit 2 ;;
    esac
done

case "$SECTION" in
    readonly|clone|measure|all) ;;
    *)
        echo "error: invalid section '$SECTION' (expected readonly, clone, measure, or all)" >&2
        usage >&2
        exit 2 ;;
esac

if [[ ! -d "$CHECKOUT" ]]; then
    echo "error: checkout directory does not exist: $CHECKOUT" >&2
    exit 2
fi

CHECKOUT_ABS="$(cd "$CHECKOUT" && pwd)"
if [[ -z "$JOURNAL_PATH" ]]; then
    JOURNAL_PATH="${CHECKOUT_ABS}/.aw/state/durable/migrations/m0001/descriptions.jsonl"
    JOURNAL_DISPLAY="<checkout>/.aw/state/durable/migrations/m0001/descriptions.jsonl"
else
    JOURNAL_DISPLAY="$JOURNAL_PATH"
fi

PASS_COUNT=0
FAIL_COUNT=0
SUMMARY_LINES=()

# Temporary artifacts cleaned up automatically on exit.
TMP_FILES=()
TMP_DIRS=()

cleanup_all() {
    local p
    for p in "${TMP_FILES[@]:-}"; do
        [[ -n "$p" && -e "$p" ]] && rm -f "$p"
    done
    for p in "${TMP_DIRS[@]:-}"; do
        [[ -n "$p" && -e "$p" ]] && rm -rf "$p"
    done
}
trap cleanup_all EXIT

record_result() {
    local label="$1"
    local status="$2"
    local note="${3:-}"
    if [[ "$status" == "PASS" ]]; then
        PASS_COUNT=$((PASS_COUNT + 1))
    elif [[ "$status" == "FAIL" ]]; then
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
    if [[ -n "$note" ]]; then
        echo "RESULT ${label}: ${status} (${note})"
        SUMMARY_LINES+=("${label}: ${status} (${note})")
    else
        echo "RESULT ${label}: ${status}"
        SUMMARY_LINES+=("${label}: ${status}")
    fi
    echo ""
}

# Run the target checkout's own agent_workflows package (isolated from caller checkout).
run_aw() {
    local target_dir="$1"
    shift
    local target_abs
    target_abs="$(cd "$target_dir" && pwd)"
    (cd "$target_abs" && PYTHONPATH="$target_abs" python3 -m agent_workflows "$@")
}

run_aw_in_clone() {
    local clone_dir="$1"
    local aw_home_dir="$2"
    shift 2
    local clone_abs
    clone_abs="$(cd "$clone_dir" && pwd)"
    (cd "$clone_abs" && AW_HOME="$aw_home_dir" PYTHONPATH="$clone_abs" python3 -m agent_workflows "$@")
}

# ==============================================================================
# Section: readonly (E-01)
# ==============================================================================
section_readonly() {
    # --------------------------------------------------------------------------
    # AC-1: Single-owner regex audit with the 9o83cr F-21 exclusion list
    # --------------------------------------------------------------------------
    echo "== AC-1 =="
    local excl_file
    excl_file="$(mktemp)"
    TMP_FILES+=("$excl_file")
    # 9o83cr F-21 exclusion list verbatim, plus _EV_LINE_RE added beside _EV_LEAF_RE in attention.py
    # by commit 7fd06a756 (N3 body-prose E/V checklist regex).
    echo "AC-1 exclusions: 9o83cr F-21 list + attention.py:_EV_LINE_RE (N3 E/V checklist, commit 7fd06a756)"
    cat <<'EXEOF' > "$excl_file"
^agent_workflows/plan_readiness\.py:[0-9]+:_OQ_FIELD_RE = re\.compile\(
^agent_workflows/attention\.py:[0-9]+:(_OQ_STATUS_RE =|.*Blocking:\.\*\\\(resolved\\\)|_EV_LEAF_RE =|_EV_LINE_RE =)
^agent_workflows/ipd_lint\.py:[0-9]+:_LEAF_RE = re\.compile\(
^agent_workflows/ipd_schema\.py:[0-9]+:(V_ROW_RE|E_ROW_RE) = re\.compile\(
^agent_workflows/check_engine\.py:[0-9]+:.*_re\.match\(r"\^-\+\$"
^agent_workflows/cli\.py:[0-9]+:.*_YAML_FENCE_CLOSE_RE = re\.compile\(
^agent_workflows/runner_shared\.py:[0-9]+:.*(status_m|blocking_m|owner_m|new_blocking_m|new_owner_m) = re\.search\(r"\(\?m\)\^-\[ \\t\]\+
^agent_workflows/runner_shared\.py:[0-9]+:.*bullets = list\(re\.finditer\(r"\(\?m\)\^-\[ \\t\]\+
^agent_workflows/run_viewer\.py:[0-9]+:.*(m_created|m_updated|m_selectors) = re\.search\(
^agent_workflows/git_commit_helper\.py:[0-9]+:_DIVIDER_RE = re\.compile\(
^agent_workflows/ipd_schema\.py:[0-9]+:H_WORKFLOW_HISTORY = "Workflow history"$
^agent_workflows/runner_shared\.py:[0-9]+:[[:space:]]*if heading != "## Workflow history" or not \(ours or theirs\):$
^agent_workflows/ipd_lifecycle\.py:[0-9]+:[[:space:]]*if p == f"\.aw/records/meta/\{expected_name\}":$
^agent_workflows/cli\.py:[0-9]+:[[:space:]]*"--message", default=None, help="Workflow history message\."$
^agent_workflows/(plan_readiness|specs|backlog|lane_containment|releases|attention_contract|status_set|engine|hooks/executed_transition_gate|hooks/status_untooled_gate|hooks/meta_log_append_gate|record_history|review_findings|ipd_authoring|artifact_core|ipd_lint|oc_runipd|doctor|selectors|coverage_record|check_engine|ipd_lifecycle|cli|runner_shared|artifact_naming|artifact_rename|prompts|layout)\.py:[0-9]+:[[:space:]]*(#|"""|\*|- |"`?## Workflow history|f?"|f?'|The old |``## Workflow history|the answer is,|prose section |never a default\.|PREPENDED under|SAME `- Id:`|matching tool-authored|are examined -|then the `- Key:|Exempts ## Workflow history:|A backfill appends|bullet; and the nearest|state:`, `Result:`,|the backlog-close commit|## Workflow history$|`## Workflow history`|``Observed evidence``|``Result:``,|Splits ## Workflow history|``history_date``|``<!-- aw-prompt:|`<!-- aw-prompt:|``text`` \(a `- Set:`|into the single `<!-- aw-prompt:|# or pipe-delimiter|require a matching tool-authored|`\.aw/records/meta/\*\.jsonl`)
EXEOF

    local ac1_all_hits
    ac1_all_hits="$(mktemp)"
    TMP_FILES+=("$ac1_all_hits")

    local q1 q2 q3 q4
    echo "$ rg -n 're\.(compile|search|match|finditer|findall|sub|fullmatch)\(\s*r?[\"\x27](\(\?m\))?\^-' agent_workflows | grep -Evf <9o83cr-F21-exclusions>"
    q1="$(cd "$CHECKOUT_ABS" && rg -n 're\.(compile|search|match|finditer|findall|sub|fullmatch)\(\s*r?["'\''](\(\?m\))?\^-' agent_workflows | grep -Evf "$excl_file" || true)"
    printf '%s\n' "$q1" >> "$ac1_all_hits"
    echo "Q1 surviving count: $(printf '%s\n' "$q1" | grep -c . || true)"

    echo "$ rg -n 'Workflow history' agent_workflows | grep -Evf <9o83cr-F21-exclusions>"
    q2="$(cd "$CHECKOUT_ABS" && rg -n 'Workflow history' agent_workflows | grep -Evf "$excl_file" || true)"
    printf '%s\n' "$q2" >> "$ac1_all_hits"
    echo "Q2 surviving count: $(printf '%s\n' "$q2" | grep -c . || true)"

    echo "$ rg -n 'aw-prompt|aw-managed-prompt' agent_workflows | grep -Evf <9o83cr-F21-exclusions>"
    q3="$(cd "$CHECKOUT_ABS" && rg -n 'aw-prompt|aw-managed-prompt' agent_workflows | grep -Evf "$excl_file" || true)"
    printf '%s\n' "$q3" >> "$ac1_all_hits"
    echo "Q3 surviving count: $(printf '%s\n' "$q3" | grep -c . || true)"

    echo "$ rg -n 'records/meta' agent_workflows | grep -Evf <9o83cr-F21-exclusions>"
    q4="$(cd "$CHECKOUT_ABS" && rg -n 'records/meta' agent_workflows | grep -Evf "$excl_file" || true)"
    printf '%s\n' "$q4" >> "$ac1_all_hits"
    echo "Q4 surviving count: $(printf '%s\n' "$q4" | grep -c . || true)"

    echo "Surviving hits by file:"
    grep -E . "$ac1_all_hits" | cut -d: -f1 | sort | uniq -c || true

    local ac1_outside
    ac1_outside="$(grep -E . "$ac1_all_hits" | grep -Ev '^agent_workflows/(artifact_meta\.py|migrations/m0001_)' || true)"
    local ac1_legacy_in_am
    ac1_legacy_in_am="$(printf '%s\n' "$q1" "$q2" | grep -E '^agent_workflows/artifact_meta\.py:' || true)"
    local outside_n legacy_am_n
    outside_n="$(printf '%s\n' "$ac1_outside" | grep -c . || true)"
    legacy_am_n="$(printf '%s\n' "$ac1_legacy_in_am" | grep -c . || true)"
    echo "Hits outside artifact_meta.py and migrations/m0001_*.py: ${outside_n}"
    if [[ "$outside_n" -gt 0 ]]; then
        printf '%s\n' "$ac1_outside" | head -n 40
    fi
    echo "Legacy bullet/history hits still in artifact_meta.py (0 after cutover moves legacy loader to m0001_metadata_v2.py): ${legacy_am_n}"
    if [[ "$outside_n" -eq 0 && "$legacy_am_n" -eq 0 ]]; then
        record_result "AC-1" "PASS" "0 outside hits, 0 legacy bullet/history hits in artifact_meta.py"
    else
        record_result "AC-1" "FAIL" "outside=${outside_n}, legacy_in_artifact_meta=${legacy_am_n}"
    fi

    # --------------------------------------------------------------------------
    # AC-1b: No migrated record has a bullet block; parent commit has no meta/
    # --------------------------------------------------------------------------
    echo "== AC-1b =="
    echo "$ python3 <check migrated records have no bullet block and meta/*.jsonl exists>"
    local ac1b_out ac1b_rc
    ac1b_out="$(cd "$CHECKOUT_ABS" && PYTHONPATH="$CHECKOUT_ABS" python3 - <<'PYEOF'
import re
import subprocess
from pathlib import Path

root = Path(".")
records = root / ".aw" / "records"
meta_dir = records / "meta"
log_files = sorted(meta_dir.glob("*.jsonl")) if meta_dir.is_dir() else []

EXCLUDED_EXACT = {
    ".aw/records/research/plan-review/20260712-0156-14-chatgpt-modular-report-template.md",
    ".aw/records/research/conformance-results-template.md",
}
BULLET_RE = re.compile(
    r"^-\s*(Id|Status|Set|Order|Priority|Work-Kind|Blocks-Release|Readiness|Approval|From-Backlog|From-Spec):\s*"
)

proc = subprocess.run(
    ["git", "ls-files", ".aw/records"],
    capture_output=True,
    text=True,
    check=False,
)
tracked = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
scanned = 0
with_bullets = []
for rel in tracked:
    if not rel.endswith(".md"):
        continue
    p = Path(rel)
    if p.name == "README.md" or rel in EXCLUDED_EXACT:
        continue
    parts = p.parts
    if "comms" in parts or "prompt-library" in parts or any(part.endswith(".data") for part in parts):
        continue
    if not p.is_file():
        continue
    scanned += 1
    text = p.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    # Skip leading --- front matter block if present
    idx = 0
    if lines and lines[0].strip() == "---":
        idx = 1
        while idx < len(lines) and lines[idx].strip() != "---":
            idx += 1
        if idx < len(lines):
            idx += 1
    # Check lines before the first '## ' heading for legacy metadata bullets
    found = False
    for ln in lines[idx:]:
        if ln.startswith("## "):
            break
        if BULLET_RE.match(ln):
            found = True
            break
    if found:
        with_bullets.append(rel)

print(f"meta_logs={len(log_files)} tracked_records_scanned={scanned} records_with_legacy_bullets={len(with_bullets)}")
for sample in with_bullets[:10]:
    print(f"  legacy_bullet_sample: {sample}")
raise SystemExit(0 if (len(log_files) > 0 and len(with_bullets) == 0) else 1)
PYEOF
    )"
    ac1b_rc=$?
    printf '%s\n' "$ac1b_out"

    echo "$ git ls-tree -d HEAD~1 .aw/records/meta"
    local parent_meta parent_rc
    parent_meta="$(git -C "$CHECKOUT_ABS" ls-tree -d HEAD~1 .aw/records/meta 2>&1)"
    parent_rc=$?
    printf '%s\n' "${parent_meta:-<empty: no .aw/records/meta in HEAD~1>}"
    echo "NOTE: Thorough-tier (make test-all) summary at the cutover commit is pasted by cxxmyv from its own run."
    if [[ "$ac1b_rc" -eq 0 && "$parent_rc" -eq 0 && -z "$parent_meta" ]]; then
        record_result "AC-1b" "PASS" "0 legacy bullet blocks, HEAD~1 has no .aw/records/meta"
    else
        record_result "AC-1b" "FAIL" "bullet_check_rc=${ac1b_rc}, parent_meta_present=$([[ -n "$parent_meta" ]] && echo yes || echo no)"
    fi

    # --------------------------------------------------------------------------
    # AC-7: Zero `aw check meta` findings
    # --------------------------------------------------------------------------
    echo "== AC-7 =="
    echo "$ python3 -m agent_workflows check meta --agent"
    local ac7_out ac7_rc ac7_lines
    ac7_out="$(run_aw "$CHECKOUT_ABS" check meta --agent 2>&1)"
    ac7_rc=$?
    ac7_lines="$(printf '%s\n' "$ac7_out" | wc -l | tr -d ' ')"
    echo "exit_code=${ac7_rc} output_lines=${ac7_lines}"
    if [[ "$ac7_lines" -le 30 ]]; then
        printf '%s\n' "$ac7_out"
    else
        printf '%s\n' "$ac7_out" | head -n 15
        echo "... (${ac7_lines} total lines; showing last 5) ..."
        printf '%s\n' "$ac7_out" | tail -n 5
    fi
    if [[ "$ac7_rc" -eq 0 ]]; then
        record_result "AC-7" "PASS" "aw check meta exited 0 with zero findings"
    else
        record_result "AC-7" "FAIL" "aw check meta exited ${ac7_rc}"
    fi

    # --------------------------------------------------------------------------
    # AC-9: No INDEX or STATUS file; rg hits only in migration cleanup code
    # --------------------------------------------------------------------------
    echo "== AC-9 =="
    echo "$ git ls-files | grep -E '(^|/)(INDEX\.(json|md)|STATUS\.md)$'"
    local ac9_git ac9_fs ac9_rg ac9_rg_outside
    ac9_git="$(git -C "$CHECKOUT_ABS" ls-files | grep -E '(^|/)(INDEX\.(json|md)|STATUS\.md)$' || true)"
    printf '%s\n' "${ac9_git:-<none>}"

    echo "$ find .aw/records -maxdepth 4 (INDEX.json | INDEX.md | STATUS.md)"
    ac9_fs="$(cd "$CHECKOUT_ABS" && find .aw/records -maxdepth 4 \( -name 'INDEX.json' -o -name 'INDEX.md' -o -name 'STATUS.md' \) 2>/dev/null || true)"
    printf '%s\n' "${ac9_fs:-<none>}"

    echo "$ rg -n 'INDEX\.json|STATUS\.md' agent_workflows"
    ac9_rg="$(cd "$CHECKOUT_ABS" && rg -n 'INDEX\.json|STATUS\.md' agent_workflows || true)"
    local ac9_rg_count
    ac9_rg_count="$(printf '%s\n' "$ac9_rg" | grep -c . || true)"
    echo "Total rg hits in agent_workflows/: ${ac9_rg_count}"
    ac9_rg_outside="$(printf '%s\n' "$ac9_rg" | grep -Ev '^agent_workflows/migrations/m0001_' || true)"
    local ac9_outside_count
    ac9_outside_count="$(printf '%s\n' "$ac9_rg_outside" | grep -c . || true)"
    echo "Hits outside agent_workflows/migrations/m0001_*.py: ${ac9_outside_count}"
    if [[ "$ac9_outside_count" -gt 0 ]]; then
        printf '%s\n' "$ac9_rg_outside" | head -n 30
    else
        printf '%s\n' "${ac9_rg:-<none>}" | head -n 20
    fi
    if [[ -z "$ac9_git" && -z "$ac9_fs" && "$ac9_outside_count" -eq 0 ]]; then
        record_result "AC-9" "PASS" "no INDEX/STATUS files; package hits only in migration cleanup"
    else
        record_result "AC-9" "FAIL" "git_hits=$(printf '%s\n' "$ac9_git" | grep -c . || true), fs_hits=$(printf '%s\n' "$ac9_fs" | grep -c . || true), rg_outside=${ac9_outside_count}"
    fi

    # --------------------------------------------------------------------------
    # AC-11: dcerjg AC-11 tests pass with CURRENT_METADATA_SCHEMA unpatched
    # --------------------------------------------------------------------------
    echo "== AC-11 =="
    echo "$ python3 -c 'from agent_workflows.migrations import chain; print(chain.CURRENT_METADATA_SCHEMA)'"
    local ac11_schema
    ac11_schema="$(cd "$CHECKOUT_ABS" && PYTHONPATH="$CHECKOUT_ABS" python3 -c 'from agent_workflows.migrations import chain; print(chain.CURRENT_METADATA_SCHEMA)' 2>&1)"
    echo "CURRENT_METADATA_SCHEMA=${ac11_schema}"

    echo "$ python3 -m pytest -o addopts=\"\" -v -k 'refusal_under_schema or read_and_read_at_refuse_legacy or ac11' tests/test_migrations_chain.py tests/test_install_migrate_prompt.py"
    local ac11_pytest_out ac11_pytest_rc
    ac11_pytest_out="$(cd "$CHECKOUT_ABS" && PYTHONPATH="$CHECKOUT_ABS" python3 -m pytest -o addopts="" -v -k 'refusal_under_schema or read_and_read_at_refuse_legacy or ac11' tests/test_migrations_chain.py tests/test_install_migrate_prompt.py 2>&1)"
    ac11_pytest_rc=$?
    printf '%s\n' "$ac11_pytest_out"

    echo "$ python3 <unpatched CURRENT_METADATA_SCHEMA == 2 behavioral probe for AC-11 cases 1-3>"
    local ac11_probe_out ac11_probe_rc
    ac11_probe_out="$(cd "$CHECKOUT_ABS" && PYTHONPATH="$CHECKOUT_ABS" python3 - <<'PYEOF'
import os
import subprocess
import tempfile
from pathlib import Path
from agent_workflows.migrations import chain
from agent_workflows import cli

assert chain.CURRENT_METADATA_SCHEMA == 2, (
    f"CURRENT_METADATA_SCHEMA is {chain.CURRENT_METADATA_SCHEMA}, expected 2 (unpatched)"
)

with tempfile.TemporaryDirectory() as td:
    td_path = Path(td)
    aw_home = td_path / "aw_home"
    aw_home.mkdir()
    src_wf = Path(".aw/system/workflows").resolve()

    def init_git(repo: Path) -> None:
        repo.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Demo"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "demo@example.com"], cwd=repo, check=True)

    # Case 1: legacy repo unstamped -> refused with aw migrate metadata
    leg = td_path / "legacy"
    init_git(leg)
    lp = leg / ".aw" / "records" / "plans" / "pending" / "20261101-leg-01-lg0001-s.ipd.md"
    lp.parent.mkdir(parents=True)
    lp.write_text("# IPD: Legacy\n\n- Id: lg0001\n- Status: approved\n", encoding="utf-8")
    refused = False
    try:
        chain.require_current_schema(leg)
    except chain.MetadataSchemaError as exc:
        assert "aw migrate metadata" in str(exc), str(exc)
        refused = True
    assert refused, "case 1 did not refuse legacy repo"

    # Case 2: empty repo -> aw install stamps metadata_schema: 2; backlog new + find succeed
    emp = td_path / "empty"
    init_git(emp)
    (emp / "README.md").write_text("# empty\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=emp, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=emp, check=True)
    old_env = os.environ.get("AW_HOME")
    os.environ["AW_HOME"] = str(aw_home)
    try:
        rc = cli.main(["install", str(emp), "--source", str(src_wf), "--preset", "private-target", "--yes"])
        assert rc == 0, f"case 2 install rc={rc}"
        assert chain.read_metadata_schema(emp) == 2, f"case 2 stamp={chain.read_metadata_schema(emp)}"
        rc2 = cli.main(["backlog", "new", "--dir", str(emp), "--summary", "AC11 item", "--priority", "low", "--work-kind", "chore", "--apply"])
        assert rc2 == 0, f"case 2 backlog new rc={rc2}"
        rc3 = cli.main(["find", "backlog", "--dir", str(emp)])
        assert rc3 == 0, f"case 2 find rc={rc3}"

        # Case 3: repo with legacy records -> aw install does not stamp metadata_schema
        subprocess.run(["git", "add", "."], cwd=leg, check=True)
        subprocess.run(["git", "commit", "-qm", "seed"], cwd=leg, check=True)
        rc4 = cli.main(["install", str(leg), "--source", str(src_wf), "--preset", "private-target", "--yes"])
        assert rc4 == 0, f"case 3 install rc={rc4}"
        assert chain.read_metadata_schema(leg) is None, f"case 3 unexpectedly stamped: {chain.read_metadata_schema(leg)}"
    finally:
        if old_env is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = old_env

print("AC-11 unpatched probe: all 3 cases passed with CURRENT_METADATA_SCHEMA == 2")
PYEOF
    )"
    ac11_probe_rc=$?
    printf '%s\n' "$ac11_probe_out"
    if [[ "$ac11_schema" == "2" && "$ac11_pytest_rc" -eq 0 && "$ac11_probe_rc" -eq 0 ]]; then
        record_result "AC-11" "PASS" "CURRENT_METADATA_SCHEMA=2 unpatched, pytest and 3 cases passed"
    else
        record_result "AC-11" "FAIL" "schema=${ac11_schema}, pytest_rc=${ac11_pytest_rc}, probe_rc=${ac11_probe_rc}"
    fi

    # --------------------------------------------------------------------------
    # AC-30 (case 2): No records/history.jsonl in tree or ignore templates
    # --------------------------------------------------------------------------
    echo "== AC-30 =="
    echo "$ git status --porcelain --ignored | grep 'records/history\.jsonl'"
    local ac30_status ac30_rg
    ac30_status="$(git -C "$CHECKOUT_ABS" status --porcelain --ignored | grep 'records/history\.jsonl' || true)"
    printf '%s\n' "${ac30_status:-<none>}"

    echo "$ rg -n 'history\.jsonl' .aw/.gitignore agent_workflows/engine.py agent_workflows/placement_switch.py"
    ac30_rg="$(cd "$CHECKOUT_ABS" && rg -n 'history\.jsonl' .aw/.gitignore agent_workflows/engine.py agent_workflows/placement_switch.py || true)"
    printf '%s\n' "${ac30_rg:-<none>}"
    if [[ -z "$ac30_status" && -z "$ac30_rg" ]]; then
        record_result "AC-30" "PASS" "no records/history.jsonl in status or ignore templates"
    else
        record_result "AC-30" "FAIL" "status_hits=$(printf '%s\n' "$ac30_status" | grep -c . || true), rg_hits=$(printf '%s\n' "$ac30_rg" | grep -c . || true)"
    fi

    # --------------------------------------------------------------------------
    # AC-36 (case 6): Real census of short descriptions
    # --------------------------------------------------------------------------
    echo "== AC-36 =="
    echo "$ python3 <census of short_description across .aw/records/meta/*.jsonl>"
    local ac36_out ac36_rc
    ac36_out="$(cd "$CHECKOUT_ABS" && PYTHONPATH="$CHECKOUT_ABS" python3 - <<'PYEOF'
import json
from collections import Counter
from pathlib import Path
from agent_workflows import artifact_meta as meta
from agent_workflows import meta_cli

meta_dir = Path(".aw/records/meta")
logs = sorted(meta_dir.glob("*.jsonl")) if meta_dir.is_dir() else []
if not logs:
    print("meta_logs=0 (unmigrated repository: no .aw/records/meta/*.jsonl logs)")
    raise SystemExit(1)

ctx = meta_cli.meta_context(Path("."))
rows = meta.query(project_context=ctx)
with_desc = 0
without_desc = 0
missing_ids = []
sources = Counter()
models = Counter()

for log in logs:
    first_line = next((ln for ln in log.read_text(encoding="utf-8").splitlines() if ln.strip()), "")
    if first_line:
        ev = json.loads(first_line)
        fields = ev.get("fields") or {}
        if fields.get("description_source"):
            sources[str(fields["description_source"])] += 1
        if fields.get("description_model"):
            models[str(fields["description_model"])] += 1

for st in rows:
    if st.short_description and str(st.short_description).strip():
        with_desc += 1
    else:
        without_desc += 1
        missing_ids.append(f"{st.id6} ({st.path})")

print(f"meta_logs={len(logs)} queried_records={len(rows)} with_short_description={with_desc} without_short_description={without_desc}")
if sources:
    print(f"description_sources={dict(sources)}")
if models:
    print(f"description_models={dict(models)}")
if missing_ids:
    print("records_without_short_description (first 15):")
    for m in missing_ids[:15]:
        print(f"  {m}")
raise SystemExit(0 if (len(logs) > 0 and with_desc > 0) else 1)
PYEOF
    )"
    ac36_rc=$?
    printf '%s\n' "$ac36_out"
    if [[ "$ac36_rc" -eq 0 ]]; then
        record_result "AC-36" "PASS" "description census reported from migrated logs"
    else
        record_result "AC-36" "FAIL" "description census rc=${ac36_rc}"
    fi

    # --------------------------------------------------------------------------
    # AC-41 (cases 3 and 4): No legacy filenames, no Set+order duplicates,
    # and a history line citing an old name displays with the current name
    # --------------------------------------------------------------------------
    echo "== AC-41 =="
    echo "$ python3 <AC-41 case 3: legacy filenames & plan (set, order) uniqueness; case 4: aw show --history display>"
    local ac41_out ac41_rc
    ac41_out="$(cd "$CHECKOUT_ABS" && PYTHONPATH="$CHECKOUT_ABS" python3 - <<'PYEOF'
import json
import subprocess
from collections import defaultdict
from pathlib import Path
from agent_workflows import artifact_meta as meta
from agent_workflows import artifact_naming as naming
from agent_workflows import meta_cli

EXCLUDED_EXACT = {
    ".aw/records/research/plan-review/20260712-0156-14-chatgpt-modular-report-template.md",
}

proc = subprocess.run(
    ["git", "ls-files", ".aw/records"],
    capture_output=True,
    text=True,
    check=False,
)
legacy_files = []
for rel in proc.stdout.splitlines():
    rel = rel.strip()
    if not rel.endswith(".md") or rel in EXCLUDED_EXACT:
        continue
    p = Path(rel)
    if p.name == "README.md" or "comms" in p.parts or any(part.endswith(".data") for part in p.parts):
        continue
    if naming._LEGACY_TIMESTAMP_RE.match(p.name):
        legacy_files.append(rel)

print(f"case3_legacy_timestamp_files={len(legacy_files)}")
for lf in legacy_files[:10]:
    print(f"  legacy_file: {lf}")

ctx = meta_cli.meta_context(Path("."))
plans = meta.query(type="ipd", project_context=ctx)
meta_dir = Path(".aw/records/meta")
logs = sorted(meta_dir.glob("*.jsonl")) if meta_dir.is_dir() else []

# Identify plans renamed by m0001 so we distinguish migration-created collisions (must be 0)
# from pre-existing unmapped historical duplicates (e.g. superseded vs executed plans).
old_to_new = {}
renamed_ids = set()
for log in logs:
    evs = [json.loads(ln) for ln in log.read_text(encoding="utf-8").splitlines() if ln.strip()]
    cp_path = None
    ren_path = None
    for ev in evs:
        if ev.get("op") == "checkpoint" and ev.get("path"):
            cp_path = str(ev["path"])
        elif ev.get("op") == "rename" and ev.get("path") and (ev.get("actor") or {}).get("tool") == "aw migrate metadata":
            ren_path = str(ev["path"])
    if cp_path and ren_path and Path(cp_path).name != Path(ren_path).name:
        old_to_new[Path(cp_path).name] = Path(ren_path).name
        renamed_ids.add(log.stem)

by_set_order = defaultdict(list)
for st in plans:
    if st.set_id and st.order_nn is not None:
        by_set_order[(st.set_id, int(st.order_nn))].append((st.id6, st.path))
all_collisions = {k: v for k, v in by_set_order.items() if len(v) > 1}
renamed_collisions = {
    k: v for k, v in all_collisions.items() if any(i in renamed_ids for i, _ in v)
}
print(f"case3_renamed_plan_set_order_collisions={len(renamed_collisions)}")
print(f"case3_all_plan_set_order_pairs_with_gt1={len(all_collisions)} (pre-existing unmapped historical pairs reported transparently)")
for (sid, order), items in list(renamed_collisions.items())[:10]:
    print(f"  renamed_collision ({sid}, {order}): {[f'{i}:{p}' for i, p in items]}")

# Case 4: find a migrated record whose legacy history event cites a renamed old filename
if not logs:
    print("case4_status=unmigrated (no .aw/records/meta/*.jsonl logs)")
    raise SystemExit(1)

sample_id = None
sample_old = None
sample_new = None
sample_raw = None
for log in logs:
    evs = [json.loads(ln) for ln in log.read_text(encoding="utf-8").splitlines() if ln.strip()]
    for ev in evs:
        if ev.get("op") != "legacy":
            continue
        raw_line = str(ev.get("line") or ev.get("message") or "")
        for old_bn, new_bn in old_to_new.items():
            if old_bn in raw_line:
                sample_id = log.stem
                sample_old = old_bn
                sample_new = new_bn
                sample_raw = raw_line
                break
        if sample_id:
            break
    if sample_id:
        break

if not sample_id:
    print(f"case4_renamed_records_found={len(old_to_new)} sample_history_citation=none")
    raise SystemExit(1)

print(f"case4_sample_record={sample_id}")
print(f"case4_old_name={sample_old}")
print(f"case4_current_name={sample_new}")
print(f"case4_raw_log_line={sample_raw[:200]}")

res = meta_cli.show_history(Path("."), sample_id)
rendered = meta_cli.render_history_human(res)
matching_lines = [ln for ln in rendered.splitlines() if sample_old in ln or sample_new in ln]
print("case4_show_history_lines:")
for ln in matching_lines[:10]:
    print(f"  {ln}")
has_current = any((sample_old in ln and sample_new in ln) or sample_new in ln for ln in matching_lines)
print(f"case4_displays_current_name={has_current}")

ok = (len(legacy_files) == 0 and len(renamed_collisions) == 0 and has_current)
raise SystemExit(0 if ok else 1)
PYEOF
    )"
    ac41_rc=$?
    printf '%s\n' "$ac41_out"
    if [[ "$ac41_rc" -eq 0 ]]; then
        record_result "AC-41" "PASS" "0 legacy names, 0 Set+order collisions, show --history displays current name"
    else
        record_result "AC-41" "FAIL" "AC-41 cases 3/4 check rc=${ac41_rc}"
    fi
}

# ==============================================================================
# Section: clone (E-02)
# ==============================================================================
section_clone() {
    mkdir -p tmp
    local demo_clone="tmp/cxxmyv-demo"
    local ac2_clone="tmp/cxxmyv-ac2"
    local demo_home="tmp/cxxmyv-demo-home"
    rm -rf "$demo_clone" "$ac2_clone" "$demo_home"
    TMP_DIRS+=("$demo_clone" "$ac2_clone" "$demo_home")
    mkdir -p "$demo_home"
    local demo_home_abs
    demo_home_abs="$(cd "$demo_home" && pwd)"

    echo "--- checkout git status --porcelain (before) ---"
    local status_before
    status_before="$(git -C "$CHECKOUT_ABS" status --porcelain)"
    printf '%s\n' "${status_before:-<clean>}"
    echo ""

    echo "$ git clone --no-hardlinks <checkout> tmp/cxxmyv-demo"
    if ! git clone --no-hardlinks -q "$CHECKOUT_ABS" "$demo_clone"; then
        echo "error: failed to clone checkout into ${demo_clone}" >&2
        record_result "CLONE-SETUP" "FAIL" "git clone --no-hardlinks failed"
        return 1
    fi
    git -C "$demo_clone" config user.name "Metastore Demo"
    git -C "$demo_clone" config user.email "metastore-demo@example.com"
    local base_sha
    base_sha="$(git -C "$demo_clone" rev-parse HEAD)"

    # --------------------------------------------------------------------------
    # AC-2: Shallow clone (--depth 1 via file://) preserves full state & history
    # --------------------------------------------------------------------------
    echo "== AC-2 =="
    echo "$ git clone --depth 1 file://<checkout> tmp/cxxmyv-ac2"
    local ac2_ok=0
    if git clone --depth 1 -q "file://${CHECKOUT_ABS}" "$ac2_clone"; then
        echo "$ git -C tmp/cxxmyv-ac2 rev-list --count HEAD"
        local rev_count
        rev_count="$(git -C "$ac2_clone" rev-list --count HEAD)"
        echo "${rev_count}"

        local ac2_plan_id
        ac2_plan_id="$(cd "$ac2_clone" && python3 - <<'PYEOF'
import json
from pathlib import Path
meta_dir = Path(".aw/records/meta")
best_id = ""
best_n = 0
if meta_dir.is_dir():
    for p in sorted(meta_dir.glob("*.jsonl")):
        lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if len(lines) < 3:
            continue
        ev0 = json.loads(lines[0])
        if (ev0.get("fields") or {}).get("type") == "ipd":
            if len(lines) > best_n:
                best_id = p.stem
                best_n = len(lines)
                if best_n >= 5:
                    break
print(best_id)
PYEOF
        )"
        if [[ -n "$ac2_plan_id" ]]; then
            echo "$ python3 -m agent_workflows show ${ac2_plan_id} --history (in tmp/cxxmyv-ac2)"
            local ac2_hist ac2_hrc
            ac2_hist="$(run_aw_in_clone "$ac2_clone" "$demo_home_abs" show "$ac2_plan_id" --history 2>&1)"
            ac2_hrc=$?
            printf '%s\n' "$ac2_hist" | head -n 30
            if [[ "$rev_count" == "1" && "$ac2_hrc" -eq 0 ]]; then
                ac2_ok=1
            fi
        else
            echo "No migrated plan log with >= 3 events found in tmp/cxxmyv-ac2/.aw/records/meta/"
        fi
    else
        echo "git clone --depth 1 failed"
    fi
    rm -rf "$ac2_clone"
    if [[ "$ac2_ok" -eq 1 ]]; then
        record_result "AC-2" "PASS" "depth-1 clone rev-list=1 and show --history succeeded"
    else
        record_result "AC-2" "FAIL" "depth-1 clone or show --history failed"
    fi

    # --------------------------------------------------------------------------
    # AC-3: Two branches change status of different artifacts & merge cleanly
    # --------------------------------------------------------------------------
    echo "== AC-3 =="
    git -C "$demo_clone" checkout -q -B demo-ac3-base "$base_sha"
    local ac3_ok=0
    local out_a out_b id_a id_b
    echo "$ aw backlog new (item A & item B) + branch A parks A + branch B parks B + git merge"
    out_a="$(run_aw_in_clone "$demo_clone" "$demo_home_abs" backlog new --summary "AC-3 branch A probe" --priority low --work-kind chore --apply 2>&1)"
    out_b="$(run_aw_in_clone "$demo_clone" "$demo_home_abs" backlog new --summary "AC-3 branch B probe" --priority low --work-kind chore --apply 2>&1)"
    # Resolve created ids deterministically from untracked backlog files.
    read -r id_a id_b < <(cd "$demo_clone" && python3 - <<'PYEOF'
import subprocess
from pathlib import Path
from agent_workflows import artifact_naming as naming
proc = subprocess.run(["git", "status", "--porcelain", "-uall"], capture_output=True, text=True, check=True)
ids = []
for ln in proc.stdout.splitlines():
    rel = ln[3:].strip()
    if rel.endswith(".backlog.md"):
        m = naming.parse_clustered(Path(rel).name)
        if m:
            ids.append(m.group("id6"))
print(" ".join(ids[:2]) if len(ids) >= 2 else " ")
PYEOF
    )
    if [[ -n "${id_a:-}" && -n "${id_b:-}" ]]; then
        git -C "$demo_clone" add .aw/records/
        git -C "$demo_clone" commit -q --no-verify -m "demo: seed AC-3 items ${id_a} and ${id_b}"

        git -C "$demo_clone" checkout -q -b demo-ac3-a
        run_aw_in_clone "$demo_clone" "$demo_home_abs" backlog set parked "$id_a" --message "AC-3 branch A park" --no-commit >/dev/null 2>&1
        git -C "$demo_clone" add -A .aw/records/
        git -C "$demo_clone" commit -q --no-verify -m "demo: park ${id_a}"

        git -C "$demo_clone" checkout -q -b demo-ac3-b demo-ac3-base
        run_aw_in_clone "$demo_clone" "$demo_home_abs" backlog set parked "$id_b" --message "AC-3 branch B park" --no-commit >/dev/null 2>&1
        git -C "$demo_clone" add -A .aw/records/
        git -C "$demo_clone" commit -q --no-verify -m "demo: park ${id_b}"

        echo "$ git merge --no-edit demo-ac3-a"
        local merge_out merge_rc
        merge_out="$(git -C "$demo_clone" merge --no-edit demo-ac3-a 2>&1)"
        merge_rc=$?
        printf '%s\n' "$merge_out"
        local st_a st_b
        st_a="$(run_aw_in_clone "$demo_clone" "$demo_home_abs" show "$id_a" --format json 2>&1 | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("data",{}).get("records",[{}])[0].get("status",""))' 2>/dev/null || true)"
        st_b="$(run_aw_in_clone "$demo_clone" "$demo_home_abs" show "$id_b" --format json 2>&1 | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("data",{}).get("records",[{}])[0].get("status",""))' 2>/dev/null || true)"
        echo "After merge: ${id_a} status=${st_a}, ${id_b} status=${st_b}"
        if [[ "$merge_rc" -eq 0 && "$st_a" == "parked" && "$st_b" == "parked" ]]; then
            ac3_ok=1
        fi
    else
        echo "Could not seed two backlog items in ${demo_clone}:"
        printf '%s\n%s\n' "$out_a" "$out_b"
    fi
    git -C "$demo_clone" checkout -qf --detach "$base_sha"
    git -C "$demo_clone" clean -fdq
    if [[ "$ac3_ok" -eq 1 ]]; then
        record_result "AC-3" "PASS" "two-branch status changes merged cleanly without conflict"
    else
        record_result "AC-3" "FAIL" "two-branch merge probe failed"
    fi

    # --------------------------------------------------------------------------
    # AC-6: git diff of one `aw set` transition and one finalize transition
    #       (with its `unset` of approval and scope fields)
    # --------------------------------------------------------------------------
    echo "== AC-6 =="
    git -C "$demo_clone" checkout -q -B demo-ac6 "$base_sha"
    local ac6_ok=0
    local ac6_out ac6_id ac6_plan
    echo "$ aw ipd scaffold + aw set to-review + git diff + aw ipd finalize + git diff"
    ac6_out="$(run_aw_in_clone "$demo_clone" "$demo_home_abs" ipd scaffold --kind child --title "AC-6 demo plan" --set ac6demo --order 1 --priority low --work-kind chore --summary "AC-6 transition and finalize diff probe" --author "ac6-demo" --apply 2>&1)"
    read -r ac6_id ac6_plan < <(cd "$demo_clone" && python3 - <<'PYEOF'
import subprocess
from pathlib import Path
from agent_workflows import artifact_naming as naming
proc = subprocess.run(["git", "status", "--porcelain", "-uall"], capture_output=True, text=True, check=True)
for ln in proc.stdout.splitlines():
    rel = ln[3:].strip()
    if rel.endswith(".ipd.md") and "ac6demo" in rel:
        m = naming.parse_clustered(Path(rel).name)
        if m:
            print(m.group("id6"), rel)
            break
PYEOF
    )
    if [[ -n "${ac6_id:-}" && -n "${ac6_plan:-}" ]]; then
        # Populate clean non-TODO body and log scope_paths/item_dependencies for pre-transition lint.
        (cd "$demo_clone" && AW_HOME="$demo_home_abs" PYTHONPATH="$(pwd)" python3 - "$ac6_id" "$ac6_plan" <<'PYEOF'
import sys
from pathlib import Path
from agent_workflows import artifact_meta as meta
from agent_workflows import meta_cli

id6, plan_rel = sys.argv[1], sys.argv[2]
plan_path = Path(plan_rel)
text = plan_path.read_text(encoding="utf-8")
# Preserve leading front matter and aw-managed banner before the '# IPD:' heading.
fm = ""
heading_idx = text.find("# IPD:")
if heading_idx > 0:
    fm = text[:heading_idx]
elif text.startswith("---\n"):
    end = text.find("\n---\n", 4)
    if end != -1:
        fm = text[: end + 5]
body = f"""{fm}# IPD: AC-6 demo plan

## Goal

Demonstrate the git diff of an aw set transition and an aw ipd finalize transition.

## Detailed Implementation Checklist (TODO)

### Task group 1: Probe

- [ ] E-01 Create ac6-demo-probe.txt inside the throwaway demo clone.
  - Depends on: none
  - Expected outcome: ac6-demo-probe.txt exists.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Runs inside the throwaway clone only.

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | demo clone | Synthetic plan for AC-6 diff demonstration. |

## Proposed changes (ordered, validatable)

1. E-01 creates ac6-demo-probe.txt.

## Deferred / out of scope (with reason)

None.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- V-01 verifies ac6-demo-probe.txt exists.

## Spec / documentation sync

N/A: throwaway clone probe.

## Open questions

None open.

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: paste ls output for ac6-demo-probe.txt.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute after approval.
"""
plan_path.write_text(body, encoding="utf-8")
ctx = meta_cli.meta_context(Path("."))
st = meta.read(id6, project_context=ctx)
meta.append(
    id6,
    [
        {
            "op": "set",
            "fields": {
                "scope_paths": [plan_rel, "ac6-demo-probe.txt"],
                "dependency_declaration": "none",
                "item_dependencies": "none",
            },
        }
    ],
    expect_seq=st.last_seq,
    project_context=ctx,
    actor={"tool": "ac6-demo"},
    message="set declared scope and dependencies for AC-6 probe",
)
PYEOF
        )
        git -C "$demo_clone" add -A .aw/records/
        git -C "$demo_clone" commit -q --no-verify -m "demo: seed AC-6 plan ${ac6_id}"

        echo "--- AC-6 part 1: git diff of aw set to-review ${ac6_id} ---"
        local set_out set_rc set_diff
        set_out="$(run_aw_in_clone "$demo_clone" "$demo_home_abs" ipd set to-review "$ac6_id" --message "AC-6 status transition demo" --no-commit 2>&1)"
        set_rc=$?
        set_diff="$(git -C "$demo_clone" diff -- ".aw/records/meta/${ac6_id}.jsonl" "$ac6_plan")"
        printf '%s\n' "$set_diff"
        git -C "$demo_clone" add -A .aw/records/
        git -C "$demo_clone" commit -q --no-verify -m "demo: to-review ${ac6_id}"

        # Advance to approved via gate review, then begin -> execute -> finalize
        run_aw_in_clone "$demo_clone" "$demo_home_abs" reviews record "$ac6_id" --round 1 --kind gate --verdict "APPROVE WITH REVISIONS APPLIED" --readiness go-pending-approval --review-depth standard --reviewer "ac6-demo" >/dev/null 2>&1
        run_aw_in_clone "$demo_clone" "$demo_home_abs" ipd set reviewed "$ac6_id" --message "AC-6 reviewed" --no-commit >/dev/null 2>&1
        run_aw_in_clone "$demo_clone" "$demo_home_abs" ipd set approved "$ac6_id" --by-human --message "AC-6 approved" --no-commit >/dev/null 2>&1
        git -C "$demo_clone" add -A .aw/records/
        git -C "$demo_clone" commit -q --no-verify -m "demo: approve ${ac6_id}"

        run_aw_in_clone "$demo_clone" "$demo_home_abs" ipd begin "$ac6_id" --actor "ac6-demo" >/dev/null 2>&1
        printf 'ac6 probe\n' > "${demo_clone}/ac6-demo-probe.txt"
        printf 'ac6 extra\n' > "${demo_clone}/ac6-demo-extra.txt"
        (cd "$demo_clone" && python3 - "$ac6_plan" <<'PYEOF'
import sys
from pathlib import Path
p = Path(sys.argv[1])
t = p.read_text(encoding="utf-8")
t = t.replace("- [ ] E-01", "- [x] E-01")
t = t.replace("Execution state: pending", "Execution state: performed")
t = t.replace("- [ ] V-01", "- [x] V-01")
t = t.replace("Observed evidence:", "Observed evidence: ac6-demo-probe.txt created in throwaway clone.")
t = t.replace("Result: pending", "Result: pass")
p.write_text(t, encoding="utf-8")
PYEOF
        )
        git -C "$demo_clone" add ac6-demo-probe.txt ac6-demo-extra.txt "$ac6_plan"
        git -C "$demo_clone" commit -q --no-verify -m "demo: work for ${ac6_id}"

        echo "--- AC-6 part 2: git diff of aw ipd finalize ${ac6_id} (with unset and scope fields) ---"
        local fin_out fin_rc fin_diff
        fin_out="$(run_aw_in_clone "$demo_clone" "$demo_home_abs" ipd finalize "$ac6_id" --actor "ac6-demo" --message "AC-6 finalize diff demo" --scope-reason "ac6-demo-extra.txt=AC-6 demo out-of-scope probe" --apply 2>&1)"
        fin_rc=$?
        if [[ "$fin_rc" -eq 0 ]]; then
            fin_diff="$(git -C "$demo_clone" diff -M HEAD~1 HEAD -- ".aw/records/meta/${ac6_id}.jsonl" ".aw/records/plans/")"
            printf '%s\n' "$fin_diff"
        else
            echo "finalize exited ${fin_rc}:"
            printf '%s\n' "$fin_out"
        fi
        if [[ "$set_rc" -eq 0 && -n "$set_diff" && "$fin_rc" -eq 0 ]] \
            && printf '%s\n' "$fin_diff" | grep -Eq '"op":[[:space:]]*"unset"' \
            && printf '%s\n' "$fin_diff" | grep -q '"scope_result"'; then
            ac6_ok=1
        fi
    else
        echo "Could not scaffold AC-6 plan:"
        printf '%s\n' "$ac6_out"
    fi
    git -C "$demo_clone" checkout -qf --detach "$base_sha"
    git -C "$demo_clone" clean -fdq
    if [[ "$ac6_ok" -eq 1 ]]; then
        record_result "AC-6" "PASS" "aw set diff and finalize diff (with unset and scope fields) captured"
    else
        record_result "AC-6" "FAIL" "AC-6 transition or finalize diff probe failed"
    fi

    # --------------------------------------------------------------------------
    # AC-16: attention --check exits 0 (no push); raw transition to executed and
    #        non-append edit of an executed plan's log are refused
    # --------------------------------------------------------------------------
    echo "== AC-16 =="
    git -C "$demo_clone" checkout -q -B demo-ac16 "$base_sha"
    local ac16_att_rc ac16_raw_rc ac16_nonappend_rc
    echo "$ python3 -m agent_workflows attention --check --agent (without pushing)"
    local ac16_att_out
    ac16_att_out="$(run_aw_in_clone "$demo_clone" "$demo_home_abs" attention --check --agent 2>&1)"
    ac16_att_rc=$?
    echo "attention --check --agent exit_code=${ac16_att_rc}"
    printf '%s\n' "$ac16_att_out" | tail -n 10

    # Sub-probe 2: raw transition into executed refused by ipd-executed-gate
    echo "$ <stage raw hand-edit + git mv of a pending plan into executed/> && python3 -m agent_workflows ipd-executed-gate"
    local pend_plan
    pend_plan="$(cd "$demo_clone" && find .aw/records/plans/pending -maxdepth 1 -name '*.ipd.md' | sort | head -n 1 || true)"
    ac16_raw_rc=0
    if [[ -n "$pend_plan" ]]; then
        local dest_plan=".aw/records/plans/executed/$(basename "$pend_plan")"
        (cd "$demo_clone" && python3 - "$pend_plan" <<'PYEOF'
import re, sys
from pathlib import Path
p = Path(sys.argv[1])
t = p.read_text(encoding="utf-8")
t2, n = re.subn(r"(?m)^status:\s*\S+", "status: executed", t, count=1)
if n == 0:
    t2 = re.sub(r"(?m)^-\s*Status:\s*\S+", "- Status: executed", t, count=1)
p.write_text(t2, encoding="utf-8")
PYEOF
        )
        git -C "$demo_clone" mv "$pend_plan" "$dest_plan"
        git -C "$demo_clone" add "$dest_plan"
        local raw_out
        raw_out="$(run_aw_in_clone "$demo_clone" "$demo_home_abs" ipd-executed-gate 2>&1)"
        ac16_raw_rc=$?
        echo "ipd-executed-gate exit_code=${ac16_raw_rc}"
        printf '%s\n' "$raw_out" | head -n 15
    else
        echo "No pending plan found for raw-executed probe"
    fi
    git -C "$demo_clone" reset -q --hard "$base_sha"
    git -C "$demo_clone" clean -fdq

    # Sub-probe 3: non-append edit of an executed plan's log refused by meta-log-append-gate
    echo "$ <stage non-append rewrite of an executed plan's meta/<id6>.jsonl> && python3 -m agent_workflows meta-log-append-gate"
    local exec_log
    exec_log="$(cd "$demo_clone" && python3 - <<'PYEOF'
import json
from pathlib import Path
meta_dir = Path(".aw/records/meta")
if meta_dir.is_dir():
    for p in sorted(meta_dir.glob("*.jsonl")):
        lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if not lines:
            continue
        ev0 = json.loads(lines[0])
        fields = ev0.get("fields") or {}
        if fields.get("type") == "ipd" and fields.get("status") == "executed":
            print(p.as_posix())
            break
PYEOF
    )"
    ac16_nonappend_rc=0
    if [[ -n "$exec_log" ]]; then
        (cd "$demo_clone" && python3 - "$exec_log" <<'PYEOF'
import sys
from pathlib import Path
p = Path(sys.argv[1])
lines = p.read_text(encoding="utf-8").splitlines()
# Mutate line 1 in place (non-append edit; encode_event writes compact JSON '"v":1')
mutated = lines[0].replace('"v":1', '"v": 1', 1)
if mutated == lines[0]:
    mutated = lines[0] + " "
assert mutated != lines[0], "failed to mutate line 1 in place"
p.write_text(mutated + "\n" + "\n".join(lines[1:]) + "\n", encoding="utf-8")
PYEOF
        )
        git -C "$demo_clone" add "$exec_log"
        local na_out
        na_out="$(run_aw_in_clone "$demo_clone" "$demo_home_abs" meta-log-append-gate 2>&1)"
        ac16_nonappend_rc=$?
        echo "meta-log-append-gate exit_code=${ac16_nonappend_rc} (target=${exec_log})"
        printf '%s\n' "$na_out" | head -n 15
    else
        echo "No executed plan log found under .aw/records/meta/"
    fi
    echo "NOTE: The pre-commit hook output of the cutover commit itself (without --no-verify) is pasted by cxxmyv from E-10."
    git -C "$demo_clone" reset -q --hard "$base_sha"
    git -C "$demo_clone" clean -fdq
    if [[ "$ac16_att_rc" -eq 0 && "$ac16_raw_rc" -ne 0 && "$ac16_nonappend_rc" -ne 0 ]]; then
        record_result "AC-16" "PASS" "attention --check exited 0; raw executed transition and non-append log edit refused"
    else
        record_result "AC-16" "FAIL" "attention_rc=${ac16_att_rc}, raw_gate_rc=${ac16_raw_rc}, nonappend_gate_rc=${ac16_nonappend_rc}"
    fi

    # --------------------------------------------------------------------------
    # AC-31: rename and group events; no sidecar created
    # --------------------------------------------------------------------------
    echo "== AC-31 =="
    git -C "$demo_clone" checkout -q -B demo-ac31 "$base_sha"
    rm -f "${demo_clone}/.aw/records/history.jsonl"
    local ac31_ok=0
    echo "$ aw backlog new + aw rename backlog + aw group backlog + aw backlog set + check no history.jsonl"
    run_aw_in_clone "$demo_clone" "$demo_home_abs" backlog new --summary "AC-31 rename and group probe" --priority low --work-kind chore --apply >/dev/null 2>&1
    local ac31_id
    ac31_id="$(cd "$demo_clone" && python3 - <<'PYEOF'
import subprocess
from pathlib import Path
from agent_workflows import artifact_naming as naming
proc = subprocess.run(["git", "status", "--porcelain", "-uall"], capture_output=True, text=True, check=True)
for ln in proc.stdout.splitlines():
    rel = ln[3:].strip()
    if rel.endswith(".backlog.md"):
        m = naming.parse_clustered(Path(rel).name)
        if m:
            print(m.group("id6"))
            break
PYEOF
    )"
    if [[ -n "$ac31_id" ]]; then
        git -C "$demo_clone" add -A .aw/records/
        git -C "$demo_clone" commit -q --no-verify -m "demo: seed AC-31 ${ac31_id}"

        echo "$ aw rename backlog ${ac31_id} --slug ac31-renamed --apply --no-commit --no-refs"
        run_aw_in_clone "$demo_clone" "$demo_home_abs" rename backlog "$ac31_id" --slug ac31-renamed --apply --no-commit --no-refs 2>&1 | head -n 10
        echo "$ aw group backlog ${ac31_id} --set ac31grp --rename --apply --no-commit --no-refs"
        run_aw_in_clone "$demo_clone" "$demo_home_abs" group backlog "$ac31_id" --set ac31grp --rename --apply --no-commit --no-refs 2>&1 | head -n 10
        echo "$ aw backlog set parked ${ac31_id} --message 'AC-31 setter probe' --no-commit"
        run_aw_in_clone "$demo_clone" "$demo_home_abs" backlog set parked "$ac31_id" --message "AC-31 setter probe" --no-commit 2>&1 | head -n 10

        echo "$ aw show ${ac31_id} --history"
        local ac31_hist
        ac31_hist="$(run_aw_in_clone "$demo_clone" "$demo_home_abs" show "$ac31_id" --history 2>&1)"
        printf '%s\n' "$ac31_hist"

        local ac31_check
        ac31_check="$(cd "$demo_clone" && python3 - "$ac31_id" <<'PYEOF'
import json, sys
from pathlib import Path
id6 = sys.argv[1]
log = Path(f".aw/records/meta/{id6}.jsonl")
sidecar_exists = Path(".aw/records/history.jsonl").exists()
if not log.is_file():
    print(f"log_missing sidecar_exists={sidecar_exists}")
    raise SystemExit(1)
evs = [json.loads(ln) for ln in log.read_text(encoding="utf-8").splitlines() if ln.strip()]
ren_verbs = [e.get("verb") for e in evs if e.get("op") == "rename"]
has_from_path = any("from_path" in e for e in evs if e.get("op") == "rename")
print(f"rename_verbs={ren_verbs} has_from_path={has_from_path} sidecar_exists={sidecar_exists}")
ok = ("rename" in ren_verbs and "group" in ren_verbs and not has_from_path and not sidecar_exists)
raise SystemExit(0 if ok else 1)
PYEOF
        )"
        local ac31_crc=$?
        printf '%s\n' "$ac31_check"
        if [[ "$ac31_crc" -eq 0 ]]; then
            ac31_ok=1
        fi
    else
        echo "Could not seed AC-31 backlog item"
    fi
    git -C "$demo_clone" checkout -qf --detach "$base_sha"
    git -C "$demo_clone" clean -fdq
    if [[ "$ac31_ok" -eq 1 ]]; then
        record_result "AC-31" "PASS" "rename and group events logged; no history.jsonl sidecar created"
    else
        record_result "AC-31" "FAIL" "AC-31 rename/group/sidecar probe failed"
    fi

    # --------------------------------------------------------------------------
    # AC-34: Path history of a renamed legacy record shows old path then new path
    # --------------------------------------------------------------------------
    echo "== AC-34 =="
    echo "$ python3 <query artifact_paths and resolve(old_path) for a renamed legacy record>"
    local ac34_out ac34_rc
    ac34_out="$(cd "$demo_clone" && AW_HOME="$demo_home_abs" PYTHONPATH="$(pwd)" python3 - <<'PYEOF'
import json
import sqlite3
from pathlib import Path
from agent_workflows import artifact_meta as meta
from agent_workflows import meta_cli

ctx = meta_cli.meta_context(Path("."))
meta_dir = Path(".aw/records/meta")
target_id = None
# Prefer wvlk84 (known legacy plan renamed to awphysical-17), else pick first migrated rename.
candidates = [meta_dir / "wvlk84.jsonl"] + (sorted(meta_dir.glob("*.jsonl")) if meta_dir.is_dir() else [])
for log in candidates:
    if not log.is_file():
        continue
    evs = [json.loads(ln) for ln in log.read_text(encoding="utf-8").splitlines() if ln.strip()]
    has_cp = any(e.get("op") == "checkpoint" and e.get("path") for e in evs)
    has_ren = any(e.get("op") == "rename" and e.get("path") for e in evs)
    if has_cp and has_ren:
        target_id = log.stem
        break

if not target_id:
    print("No migrated renamed record found in .aw/records/meta/")
    raise SystemExit(1)

# Warm cache through public read, then inspect artifact_paths rows in seq order.
st = meta.read(target_id, project_context=ctx)
db = ctx.state_root / "index.db"
conn = sqlite3.connect(str(db))
rows = conn.execute(
    "SELECT seq, op, verb, path, actor_id, by_human FROM artifact_paths WHERE id6 = ? ORDER BY seq ASC",
    (target_id,),
).fetchall()
conn.close()

print(f"record={target_id} current_path={st.path}")
print("artifact_paths:")
for r in rows:
    print(f"  seq={r[0]} op={r[1]} verb={r[2]} path={r[3]} by_human={bool(r[5])}")

old_path = rows[0][3] if len(rows) >= 2 else None
new_path = rows[1][3] if len(rows) >= 2 else None
resolved_old = meta.resolve(old_path, project_context=ctx) if old_path else None
print(f"resolve(old_path) -> {resolved_old}")
ok = (
    len(rows) >= 2
    and rows[0][1] == "checkpoint"
    and rows[1][1] == "rename"
    and old_path != new_path
    and resolved_old is not None
)
raise SystemExit(0 if ok else 1)
PYEOF
    )"
    ac34_rc=$?
    printf '%s\n' "$ac34_out"
    if [[ "$ac34_rc" -eq 0 ]]; then
        record_result "AC-34" "PASS" "artifact_paths shows old path (checkpoint) then new path (rename) and old path resolves"
    else
        record_result "AC-34" "FAIL" "AC-34 path history probe rc=${ac34_rc}"
    fi

    # Clean up demo clones before checking checkout status.
    rm -rf "$demo_clone" "$ac2_clone" "$demo_home"

    echo "--- checkout git status --porcelain (after) ---"
    local status_after
    status_after="$(git -C "$CHECKOUT_ABS" status --porcelain)"
    printf '%s\n' "${status_after:-<clean>}"
    if [[ "$status_before" == "$status_after" ]]; then
        echo "checkout status match: EQUAL"
    else
        echo "checkout status match: CHANGED"
        record_result "CLONE-ISOLATION" "FAIL" "checkout git status changed during clone section"
    fi
    echo ""
}

# ==============================================================================
# Section: measure (E-03, AC-13)
# ==============================================================================
section_measure() {
    echo "== AC-13 =="
    mkdir -p tmp
    local measure_clone="tmp/cxxmyv-measure"
    local measure_home="tmp/cxxmyv-measure-home"
    rm -rf "$measure_clone" "$measure_home"
    TMP_DIRS+=("$measure_clone" "$measure_home")
    mkdir -p "$measure_home"
    local measure_home_abs
    measure_home_abs="$(cd "$measure_home" && pwd)"

    echo "Cold-cache method: ${COLD_CACHE_METHOD}"
    echo "Commands used:"
    echo "  plan bytes:    wc -c < <plan path matching *-${PLAN_ID6}-*.ipd.md>"
    echo "  aw find:       python3 -m agent_workflows find plans"
    echo "  aw attention:  python3 -m agent_workflows attention"
    echo "  log append:    artifact_meta.append(<exec_id6>, [{'op':'note','message':'AC-13 append timing'}]) in throwaway clone"
    echo "  journal cost:  summary of ${JOURNAL_DISPLAY}"
    echo ""

    # Prepare throwaway clone for log-size + append-time probe
    git clone --no-hardlinks -q "$CHECKOUT_ABS" "$measure_clone"
    local measure_clone_abs
    measure_clone_abs="$(cd "$measure_clone" && pwd)"

    local m_out m_rc
    m_out="$(cd "$CHECKOUT_ABS" && PYTHONPATH="$CHECKOUT_ABS" python3 - \
        "$CHECKOUT_ABS" \
        "$measure_clone_abs" \
        "$measure_home_abs" \
        "$PLAN_ID6" \
        "$BEFORE_PLAN_BYTES" \
        "$BEFORE_FIND_COLD_MS" \
        "$BEFORE_FIND_WARM_MS" \
        "$BEFORE_ATTENTION_COLD_MS" \
        "$BEFORE_ATTENTION_WARM_MS" \
        "$EXEC_PLAN_ID6" \
        "$JOURNAL_PATH" <<'PYEOF'
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

(
    checkout_str,
    clone_str,
    clone_home_str,
    plan_id6,
    before_plan_bytes,
    before_find_cold_ms,
    before_find_warm_ms,
    before_att_cold_ms,
    before_att_warm_ms,
    exec_plan_id6,
    journal_path_str,
) = sys.argv[1:12]

checkout = Path(checkout_str)
clone = Path(clone_str)

def clear_caches(repo: Path) -> None:
    for pat in (
        ".aw/state/index.db",
        ".aw/state/index.db-wal",
        ".aw/state/index.db-shm",
        ".aw/state/index.db-journal",
    ):
        p = repo / pat
        if p.exists():
            p.unlink()
    cache_dir = repo / ".aw" / "cache"
    if cache_dir.is_dir():
        for p in cache_dir.glob("*.sqlite*"):
            if p.is_file():
                p.unlink()

def time_cmd(repo: Path, argv: list[str]) -> tuple[float, int, int]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo)
    t0 = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "-m", "agent_workflows", *argv],
        cwd=str(repo),
        env=env,
        capture_output=True,
        check=False,
    )
    dt_ms = (time.perf_counter() - t0) * 1000.0
    return dt_ms, proc.returncode, len(proc.stdout)

# 1. Bytes an agent reads for one plan
matches = sorted((checkout / ".aw" / "records" / "plans").rglob(f"*-{plan_id6}-*.ipd.md"))
if matches:
    after_plan_bytes = str(matches[0].stat().st_size)
    plan_rel = matches[0].relative_to(checkout).as_posix()
else:
    after_plan_bytes = "not-found"
    plan_rel = f"<not found for {plan_id6}>"

# 2. End-to-end time of `aw find plans` (cold, then 2 warm runs)
clear_caches(checkout)
find_cold_ms, find_cold_rc, find_cold_bytes = time_cmd(checkout, ["find", "plans"])
find_warm1_ms, find_warm1_rc, _ = time_cmd(checkout, ["find", "plans"])
find_warm2_ms, find_warm2_rc, _ = time_cmd(checkout, ["find", "plans"])

# 3. End-to-end time of `aw attention` (cold, then 2 warm runs)
clear_caches(checkout)
att_cold_ms, att_cold_rc, att_cold_bytes = time_cmd(checkout, ["attention"])
att_warm1_ms, att_warm1_rc, _ = time_cmd(checkout, ["attention"])
att_warm2_ms, att_warm2_rc, _ = time_cmd(checkout, ["attention"])

# 4. Typical executed plan log size & time of one append in throwaway clone
meta_dir = clone / ".aw" / "records" / "meta"
exec_logs = []
if meta_dir.is_dir():
    for lp in sorted(meta_dir.glob("*.jsonl")):
        first = next((ln for ln in lp.read_text(encoding="utf-8").splitlines() if ln.strip()), "")
        if not first:
            continue
        ev0 = json.loads(first)
        flds = ev0.get("fields") or {}
        if flds.get("type") == "ipd" and flds.get("status") == "executed":
            exec_logs.append((lp.stat().st_size, lp))

chosen_log = None
if exec_plan_id6 and (meta_dir / f"{exec_plan_id6}.jsonl").is_file():
    chosen_log = meta_dir / f"{exec_plan_id6}.jsonl"
elif exec_logs:
    exec_logs.sort(key=lambda pair: pair[0])
    chosen_log = exec_logs[len(exec_logs) // 2][1]

if chosen_log is not None:
    chosen_id = chosen_log.stem
    log_bytes = chosen_log.stat().st_size
    log_lines = sum(1 for ln in chosen_log.read_text(encoding="utf-8").splitlines() if ln.strip())
    log_size_str = f"{log_bytes} bytes ({log_lines} events, plan {chosen_id})"
    # Measure single append in throwaway clone using the clone's own artifact_meta.append
    env = dict(os.environ)
    env["PYTHONPATH"] = str(clone)
    env["AW_HOME"] = clone_home_str
    append_code = (
        "import time; from pathlib import Path; "
        "from agent_workflows import artifact_meta as m, meta_cli; "
        f"ctx = meta_cli.meta_context(Path('.')); st = m.read('{chosen_id}', project_context=ctx); "
        "t0 = time.perf_counter(); "
        f"m.append('{chosen_id}', [{{'op': 'note', 'message': 'AC-13 append timing probe'}}], "
        "expect_seq=st.last_seq, project_context=ctx, actor={'tool': 'ac13-measure'}); "
        "print(f'{(time.perf_counter() - t0) * 1000.0:.2f}')"
    )
    ap_proc = subprocess.run(
        [sys.executable, "-c", append_code],
        cwd=str(clone),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if ap_proc.returncode == 0 and ap_proc.stdout.strip():
        append_time_str = f"{ap_proc.stdout.strip()} ms (1 note append to {chosen_id})"
    else:
        append_time_str = f"failed (rc={ap_proc.returncode}: {ap_proc.stderr.strip()[:120]})"
else:
    log_size_str = "n/a (no executed plan logs under .aw/records/meta/)"
    append_time_str = "n/a (unmigrated)"

# 5. Short-description generation cost from description journal
jp = Path(journal_path_str)
if jp.is_file():
    total = ok_n = fail_n = 0
    total_cost = 0.0
    cost_rows = 0
    total_tokens = 0
    models = set()
    hosts = set()
    timestamps = []
    for raw in jp.read_text(encoding="utf-8", errors="replace").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except ValueError:
            continue
        total += 1
        if obj.get("text"):
            ok_n += 1
        else:
            fail_n += 1
        if obj.get("model"):
            models.add(str(obj["model"]))
        if obj.get("host"):
            hosts.add(str(obj["host"]))
        for ck in ("cost", "cost_usd"):
            if isinstance(obj.get(ck), (int, float)):
                total_cost += float(obj[ck])
                cost_rows += 1
                break
        if isinstance(obj.get("tokens"), int):
            total_tokens += obj["tokens"]
        ts = obj.get("generated_at")
        if isinstance(ts, str):
            try:
                timestamps.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
            except ValueError:
                pass
    span_str = ""
    if len(timestamps) >= 2:
        span_s = (max(timestamps) - min(timestamps)).total_seconds()
        span_str = f", wall_span={span_s:.1f}s"
    cost_str = f"${total_cost:.6f}" if cost_rows > 0 else "$0.00 (no per-entry API cost field; local or journal-only)"
    gen_cost_str = (
        f"{cost_str} ({ok_n}/{total} ok, {fail_n} failed, "
        f"hosts={sorted(hosts)}, models={sorted(models)}{span_str})"
    )
else:
    gen_cost_str = "journal absent at configured path (pass --journal-path)"

print(f"Plan file measured: {plan_rel}")
print(f"aw find plans: cold={find_cold_ms:.1f} ms (rc={find_cold_rc}, bytes={find_cold_bytes}), warm={find_warm1_ms:.1f} ms / {find_warm2_ms:.1f} ms")
print(f"aw attention:  cold={att_cold_ms:.1f} ms (rc={att_cold_rc}, bytes={att_cold_bytes}), warm={att_warm1_ms:.1f} ms / {att_warm2_ms:.1f} ms")
print(f"Typical executed plan log size: {log_size_str}")
print(f"Single append time: {append_time_str}")
print(f"Short-description generation cost: {gen_cost_str}")
print("")
print("| Metric | Before (tub3ir F-02) | After (measured) |")
print("|---|---|---|")
print(f"| Plan bytes read ({plan_id6}) | {before_plan_bytes} bytes | {after_plan_bytes} bytes |")
print(f"| aw find plans (cold) | {before_find_cold_ms} ms | {find_cold_ms:.1f} ms (rc={find_cold_rc}) |")
print(f"| aw find plans (warm) | {before_find_warm_ms} ms | {find_warm1_ms:.1f} ms / {find_warm2_ms:.1f} ms |")
print(f"| aw attention (cold) | {before_att_cold_ms} ms | {att_cold_ms:.1f} ms (rc={att_cold_rc}) |")
print(f"| aw attention (warm) | {before_att_warm_ms} ms | {att_warm1_ms:.1f} ms / {att_warm2_ms:.1f} ms |")
print(f"| Typical executed plan log size | n/a (pre-cutover) | {log_size_str} |")
print(f"| Single append time (throwaway clone) | n/a (pre-cutover) | {append_time_str} |")
print(f"| Short-description generation cost | n/a (pre-cutover) | {gen_cost_str} |")
print("")
print("NOTE: Spec 4sd62s AC-13 sets no target value; no threshold assertion is made.")
PYEOF
    )"
    m_rc=$?
    printf '%s\n' "$m_out"
    rm -rf "$measure_clone" "$measure_home"
    if [[ "$m_rc" -eq 0 ]]; then
        record_result "AC-13" "PASS" "measurements completed (no target value asserted)"
    else
        record_result "AC-13" "FAIL" "measurement script exited ${m_rc}"
    fi
}

# ==============================================================================
# Dispatch
# ==============================================================================
case "$SECTION" in
    readonly)
        section_readonly ;;
    clone)
        section_clone ;;
    measure)
        section_measure ;;
    all)
        section_readonly
        section_clone
        section_measure ;;
esac

echo "=== SUMMARY (${SECTION}) ==="
for line in "${SUMMARY_LINES[@]:-}"; do
    [[ -n "$line" ]] && echo "  ${line}"
done
echo "SUMMARY: passed=${PASS_COUNT} failed=${FAIL_COUNT}"

if [[ "$FAIL_COUNT" -gt 0 ]]; then
    exit 1
fi
exit 0
