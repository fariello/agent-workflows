"""Per-run question and answer inbox through one shared answer writer.

Spec 6kwd2e R9.1, R9.2, R4a.1, R5.4, R5.6 (qchan-03 mtmqlm).
Provides durable per-question files under ``questions/<qid>.json``, guarded answers under
``answers/<qid>.json``, status transitions (open -> answered | stale), projection rendering
to ``open-questions.md``, and atomic concurrency controls.
"""

from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, NamedTuple, Optional

from filelock import FileLock

from agent_workflows import set_records

# Run-scoped question id grammar:
# e.g. '01-mtmqlm-a1-q1', '04-epsti7-a2-cache_size'
QID_PATTERN = r"^[0-9]{2,}-[a-z0-9]{6}-a[0-9]+-[A-Za-z0-9._-]{1,40}$"
QID_RE = re.compile(QID_PATTERN)

QUESTION_SCHEMA = "aw.question/v1"
ANSWER_SCHEMA = "aw.answer/v1"

QUESTION_STATUS_OPEN = "open"
QUESTION_STATUS_ANSWERED = "answered"
QUESTION_STATUS_STALE = "stale"
VALID_QUESTION_STATUSES = frozenset(
    (QUESTION_STATUS_OPEN, QUESTION_STATUS_ANSWERED, QUESTION_STATUS_STALE)
)

MAX_ANSWER_LENGTH = 4000
MAX_CHANNEL_LENGTH = 200
MAX_SENDER_LENGTH = 200


class AnswerResult(NamedTuple):
    """Result of attempting to write an answer to a question."""

    status: str  # "recorded", "already", "rejected"
    reason: str
    path: Optional[Path] = None
    answer: Optional[dict[str, Any]] = None

    @property
    def recorded(self) -> bool:
        return self.status == "recorded"

    @property
    def already(self) -> bool:
        return self.status == "already"

    @property
    def rejected(self) -> bool:
        return self.status == "rejected"


def utc_now() -> str:
    """Current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def is_valid_qid(qid: str) -> bool:
    """Check whether a question ID matches the run-scoped grammar."""
    return bool(isinstance(qid, str) and QID_RE.match(qid))


def validate_qid(qid: str) -> None:
    """Raise ValueError if a question ID does not match the run-scoped grammar."""
    if not is_valid_qid(qid):
        raise ValueError(f"Invalid question_id {qid!r}; must match {QID_PATTERN}")


def resolve_question_path(run_dir: Path, qid: str) -> Path:
    """Resolve a question file path, verifying it stays within questions/."""
    validate_qid(qid)
    questions_dir = (run_dir / "questions").resolve()
    target = (questions_dir / f"{qid}.json").resolve()
    if target.parent != questions_dir:
        raise ValueError(f"Path traversal detected in question_id {qid!r}")
    return target


def resolve_answer_path(run_dir: Path, qid: str) -> Path:
    """Resolve an answer file path, verifying it stays within answers/."""
    validate_qid(qid)
    answers_dir = (run_dir / "answers").resolve()
    target = (answers_dir / f"{qid}.json").resolve()
    if target.parent != answers_dir:
        raise ValueError(f"Path traversal detected in question_id {qid!r}")
    return target


def _has_disallowed_control_chars(text: str) -> bool:
    """Return True if text contains control characters other than newline and tab."""
    for ch in text:
        if ch in ("\n", "\t"):
            continue
        code = ord(ch)
        if code < 32 or code == 127 or unicodedata.category(ch) == "Cc":
            return True
    return False


def _append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    """Append a JSON line with fsync."""
    from agent_workflows import runner_shared

    runner_shared.append_jsonl(path, payload)


def write_question(
    run_dir: Path | str,
    item: Mapping[str, Any],
    question: Mapping[str, Any],
    *,
    attempt: int | None = None,
    repo: Path | None = None,
) -> Path:
    """Write questions/<qid>.json at the moment an item parks (spec 6kwd2e R9.1, E-01).

    Uses O_EXCL semantics: creates a temp file then links it to the final name.
    If the question file already exists, FileExistsError is raised and the original
    file remains untouched.
    """
    from agent_workflows import runner_shared

    run_dir = Path(run_dir).resolve()
    questions_dir = run_dir / "questions"
    questions_dir.mkdir(parents=True, exist_ok=True)

    position = int(item.get("position", 1))
    id6 = str(item.get("id6") or "").strip().lower()

    if attempt is not None:
        attempt_val = int(attempt)
    elif item.get("current_attempt"):
        attempt_val = int(item["current_attempt"])
    elif (
        item.get("attempts")
        and isinstance(item["attempts"], (list, tuple))
        and len(item["attempts"]) > 0
    ):
        last_att = item["attempts"][-1]
        if isinstance(last_att, Mapping) and "number" in last_att:
            attempt_val = int(last_att["number"])
        else:
            attempt_val = len(item["attempts"])
    else:
        attempt_val = 1

    worker_qid = str(question.get("question_id") or "").strip()
    if is_valid_qid(worker_qid):
        qid = worker_qid
    else:
        qid = f"{position:02d}-{id6}-a{attempt_val}-{worker_qid}"

    target_file = resolve_question_path(run_dir, qid)

    # Resolve repo if not provided
    if repo is None:
        if "repo" in item and item["repo"]:
            repo = Path(item["repo"]).resolve()
        else:
            cur = run_dir
            while cur.parent != cur:
                if (cur / ".git").exists() or (cur / ".aw").is_dir():
                    repo = cur
                    break
                cur = cur.parent
            if repo is None:
                cfg = item.get("configured_file")
                if cfg and Path(cfg).is_absolute():
                    cur = Path(cfg).parent
                    while cur.parent != cur:
                        if (cur / ".git").exists() or (cur / ".aw").is_dir():
                            repo = cur
                            break
                        cur = cur.parent
            if repo is None:
                repo = Path.cwd().resolve()

    # Resolve artifact path and hash against main checkout
    art_path: Path | None = None
    if "artifact_path" in item and item["artifact_path"]:
        cand = Path(item["artifact_path"])
        if not cand.is_absolute() and repo:
            cand = repo / cand
        if cand.is_file():
            art_path = cand.resolve()
    if art_path is None:
        try:
            art_path = runner_shared.queue_artifact_path(repo, item)
        except Exception:
            cfg = item.get("configured_file")
            if cfg:
                p_cfg = Path(cfg)
                if not p_cfg.is_absolute() and repo:
                    p_cfg = repo / p_cfg
                if p_cfg.is_file():
                    art_path = p_cfg.resolve()
            if art_path is None:
                raise

    try:
        rel_art_path = art_path.relative_to(repo).as_posix()
    except ValueError:
        rel_art_path = str(art_path)

    if question.get("artifact_hash"):
        artifact_hash = str(question["artifact_hash"])
    else:
        artifact_hash = runner_shared.sha256_file(art_path)

    run_id = str(item.get("run_id") or run_dir.name)
    fingerprint = question.get("fingerprint")
    if not fingerprint:
        fingerprint = runner_shared.question_fingerprint(
            str(question.get("text", "")),
            question.get("options"),
        )

    gates_verdict = bool(question.get("gates_verdict", True))
    text = str(question.get("text", "")).strip()
    raw_opts = question.get("options")
    options = list(raw_opts) if raw_opts is not None else None
    allow_free_text = bool(question.get("allow_free_text", True))
    evidence = list(question.get("evidence", []))
    action = str(question.get("action") or item.get("action", "execute"))
    created_at = str(question.get("created_at") or utc_now())

    payload = {
        "schema": QUESTION_SCHEMA,
        "question_id": qid,
        "run_id": run_id,
        "artifact_id6": id6,
        "artifact_path": rel_art_path,
        "artifact_hash": artifact_hash,
        "fingerprint": fingerprint,
        "gates_verdict": gates_verdict,
        "text": text,
        "options": options,
        "allow_free_text": allow_free_text,
        "evidence": evidence,
        "action": action,
        "created_at": created_at,
        "status": QUESTION_STATUS_OPEN,
    }
    if question.get("oq_id"):
        payload["oq_id"] = str(question["oq_id"])

    # Write temp file and link atomically with O_EXCL semantics
    tmp_path = questions_dir / f".tmp_{qid}_{os.getpid()}_{time.time_ns()}"
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, indent=2) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.link(str(tmp_path), str(target_file))
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    return target_file


def read_questions(
    run_dir: Path | str,
    *,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """Read questions from questions/, optionally filtered by status."""
    run_dir = Path(run_dir)
    questions_dir = run_dir / "questions"
    if not questions_dir.is_dir():
        return []
    res: list[dict[str, Any]] = []
    for p in sorted(questions_dir.glob("*.json")):
        if p.name.startswith("."):
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                if status is None or data.get("status") == status:
                    res.append(data)
        except Exception:
            pass
    return res


def read_open_questions(run_dir: Path | str) -> list[dict[str, Any]]:
    """Read all questions with status 'open' from questions/."""
    return read_questions(run_dir, status=QUESTION_STATUS_OPEN)


def read_question(run_dir: Path | str, qid: str) -> dict[str, Any] | None:
    """Read a specific question file by qid."""
    try:
        p = resolve_question_path(Path(run_dir), qid)
    except ValueError:
        return None
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def read_answers(run_dir: Path | str) -> list[dict[str, Any]]:
    """Read all answer files from answers/."""
    run_dir = Path(run_dir)
    answers_dir = run_dir / "answers"
    if not answers_dir.is_dir():
        return []
    res: list[dict[str, Any]] = []
    for p in sorted(answers_dir.glob("*.json")):
        if p.name.startswith("."):
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                res.append(data)
        except Exception:
            pass
    return res


def read_answer(run_dir: Path | str, qid: str) -> dict[str, Any] | None:
    """Read a specific answer file by qid."""
    try:
        p = resolve_answer_path(Path(run_dir), qid)
    except ValueError:
        return None
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _record_rejection(
    run_dir: Path,
    qid: str,
    reason: str,
    actor: str,
    channel: str,
    sender: str,
    answer: Any,
    choice: Any,
    *,
    status: str = "rejected",
) -> None:
    """Record an answer rejection or duplicate attempt to answers/<qid>.rejected.jsonl and events.jsonl."""
    answers_dir = run_dir / "answers"
    answers_dir.mkdir(parents=True, exist_ok=True)
    rej_file = answers_dir / f"{qid}.rejected.jsonl"
    rejection_entry = {
        "at": utc_now(),
        "question_id": qid,
        "status": status,
        "reason": reason,
        "actor": actor,
        "channel": channel,
        "sender": sender,
        "answer": answer,
        "choice": choice,
    }
    _append_jsonl(rej_file, rejection_entry)
    if status == "rejected":
        _append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": utc_now(),
                "event": "answer-rejected",
                "question_id": qid,
                "reason": reason,
                "actor": actor,
                "channel": channel,
                "sender": sender,
            },
        )


def write_answer(
    run_dir: Path | str,
    qid: str,
    *,
    answer: str | None = None,
    choice: int | None = None,
    channel: str,
    sender: str,
    actor: str,
) -> AnswerResult:
    """Write answers/<qid>.json as the ONLY answer writer (spec 6kwd2e R9.2, E-02).

    Enforces:
    - qid matching QID_RE and residing inside questions/
    - question exists and has status 'open'
    - actor == 'human' (RL-E051)
    - choice valid within question options
    - free text permitted only when allow_free_text is true
    - length limits: answer <= 4000, channel/sender <= 200
    - control character rejection (only newline and tab allowed)
    - per-question lock (first answer wins; subsequent returns 'already')
    - atomic write
    - events.jsonl ledger records (human_answer, question_disposition)
    - projection update
    """
    run_dir = Path(run_dir).resolve()

    # 1. Validate qid grammar and path
    if not is_valid_qid(qid):
        return AnswerResult(
            status="rejected",
            reason=f"malformed question_id: {qid!r}",
        )
    questions_dir = (run_dir / "questions").resolve()
    q_file = (questions_dir / f"{qid}.json").resolve()
    if q_file.parent != questions_dir:
        return AnswerResult(
            status="rejected",
            reason=f"malformed question_id: traversal detected in {qid!r}",
        )
    if not q_file.is_file():
        return AnswerResult(
            status="rejected",
            reason=f"unknown question_id: {qid!r} not found in questions/",
        )

    # 2. Check actor == 'human' (RL-E051)
    if actor != "human":
        reason = (
            f"RL-E051: human_answer must be authored by the 'human' role, got {actor!r}"
        )
        _record_rejection(run_dir, qid, reason, actor, channel, sender, answer, choice)
        return AnswerResult(status="rejected", reason=reason)

    # 3. Read question data
    try:
        q_data = json.loads(q_file.read_text(encoding="utf-8"))
    except Exception as exc:
        reason = f"failed to read question file: {exc}"
        _record_rejection(run_dir, qid, reason, actor, channel, sender, answer, choice)
        return AnswerResult(status="rejected", reason=reason)

    # 4. Check question status is open
    q_status = q_data.get("status")
    if q_status != QUESTION_STATUS_OPEN:
        reason = f"question status is not open: {q_status!r}"
        _record_rejection(run_dir, qid, reason, actor, channel, sender, answer, choice)
        return AnswerResult(status="rejected", reason=reason)

    # 5. Validate choice and allow_free_text
    options = q_data.get("options")
    allow_free_text = q_data.get("allow_free_text", True)

    effective_answer = answer
    if choice is not None:
        if not isinstance(choice, int):
            reason = f"choice must be an integer index, got {type(choice).__name__}"
            _record_rejection(
                run_dir, qid, reason, actor, channel, sender, answer, choice
            )
            return AnswerResult(status="rejected", reason=reason)
        if options is None or not (0 <= choice < len(options)):
            count = len(options) if options is not None else 0
            reason = f"choice index {choice} outside options (count: {count})"
            _record_rejection(
                run_dir, qid, reason, actor, channel, sender, answer, choice
            )
            return AnswerResult(status="rejected", reason=reason)
        if effective_answer is None or not str(effective_answer).strip():
            effective_answer = options[choice]
    else:
        if not allow_free_text:
            reason = "free-text answer not allowed when allow_free_text is false"
            _record_rejection(
                run_dir, qid, reason, actor, channel, sender, answer, choice
            )
            return AnswerResult(status="rejected", reason=reason)
        if effective_answer is None or not str(effective_answer).strip():
            reason = "answer text required when no choice is provided"
            _record_rejection(
                run_dir, qid, reason, actor, channel, sender, answer, choice
            )
            return AnswerResult(status="rejected", reason=reason)

    # 6. Validate length bounds and control characters
    str_answer = str(effective_answer)
    if len(str_answer) > MAX_ANSWER_LENGTH:
        reason = (
            f"answer length {len(str_answer)} exceeds {MAX_ANSWER_LENGTH} characters"
        )
        _record_rejection(run_dir, qid, reason, actor, channel, sender, answer, choice)
        return AnswerResult(status="rejected", reason=reason)
    if _has_disallowed_control_chars(str_answer):
        reason = "answer contains disallowed control characters"
        _record_rejection(run_dir, qid, reason, actor, channel, sender, answer, choice)
        return AnswerResult(status="rejected", reason=reason)

    str_channel = str(channel)
    if not str_channel or len(str_channel) > MAX_CHANNEL_LENGTH:
        reason = f"channel length must be 1..{MAX_CHANNEL_LENGTH} characters"
        _record_rejection(run_dir, qid, reason, actor, channel, sender, answer, choice)
        return AnswerResult(status="rejected", reason=reason)
    if _has_disallowed_control_chars(str_channel):
        reason = "channel contains disallowed control characters"
        _record_rejection(run_dir, qid, reason, actor, channel, sender, answer, choice)
        return AnswerResult(status="rejected", reason=reason)

    str_sender = str(sender)
    if not str_sender or len(str_sender) > MAX_SENDER_LENGTH:
        reason = f"sender length must be 1..{MAX_SENDER_LENGTH} characters"
        _record_rejection(run_dir, qid, reason, actor, channel, sender, answer, choice)
        return AnswerResult(status="rejected", reason=reason)
    if _has_disallowed_control_chars(str_sender):
        reason = "sender contains disallowed control characters"
        _record_rejection(run_dir, qid, reason, actor, channel, sender, answer, choice)
        return AnswerResult(status="rejected", reason=reason)

    # 7. Acquire per-question lock on answers/<qid>.lock
    answers_dir = run_dir / "answers"
    answers_dir.mkdir(parents=True, exist_ok=True)
    lock_file = answers_dir / f"{qid}.lock"

    with FileLock(str(lock_file)):
        ans_file = answers_dir / f"{qid}.json"
        if ans_file.exists():
            _record_rejection(
                run_dir,
                qid,
                "already answered",
                actor,
                channel,
                sender,
                answer,
                choice,
                status="already",
            )
            return AnswerResult(
                status="already",
                reason="already answered",
                path=ans_file,
            )

        # Re-check question status inside the lock
        q_data_locked = json.loads(q_file.read_text(encoding="utf-8"))
        if q_data_locked.get("status") != QUESTION_STATUS_OPEN:
            reason = f"question status is not open: {q_data_locked.get('status')!r}"
            _record_rejection(
                run_dir, qid, reason, actor, channel, sender, answer, choice
            )
            return AnswerResult(status="rejected", reason=reason)

        artifact_hash = str(q_data_locked.get("artifact_hash", ""))
        answered_at = utc_now()
        ans_record = {
            "schema": ANSWER_SCHEMA,
            "question_id": qid,
            "answer": str_answer,
            "choice": choice,
            "actor": actor,
            "channel": str_channel,
            "sender": str_sender,
            "artifact_hash": artifact_hash,
            "answered_at": answered_at,
        }

        # Atomic write with temp file in same directory
        tmp_ans = answers_dir / f".tmp_{qid}_{os.getpid()}_{time.time_ns()}"
        try:
            with tmp_ans.open("w", encoding="utf-8") as handle:
                handle.write(json.dumps(ans_record, indent=2) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(str(tmp_ans), str(ans_file))
        finally:
            if tmp_ans.exists():
                tmp_ans.unlink()

        # Append human_answer and question_disposition events
        _append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": answered_at,
                "event": "human_answer",
                "kind": "human_answer",
                "question_id": qid,
                "answer": str_answer,
                "actor": "human",
                "channel": str_channel,
                "sender": str_sender,
            },
        )
        _append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": answered_at,
                "event": "question_disposition",
                "kind": "question_disposition",
                "question_id": qid,
                "disposition": "answered_by_human",
                "actor": "human",
            },
        )

        # Refresh projection
        write_projection(run_dir)

        return AnswerResult(
            status="recorded",
            reason="recorded",
            path=ans_file,
            answer=ans_record,
        )


def set_question_status(
    run_dir: Path | str,
    qid: str,
    status: str,
    *,
    reason: str,
) -> bool:
    """Set a question file's status after creation (spec 6kwd2e E-05).

    Accepts ONLY 'answered' and 'stale' from 'open' and nothing else.
    Acquires answers/<qid>.lock, updates the file atomically, logs a
    'question-status' event, and refreshes the open-questions.md projection.
    """
    run_dir = Path(run_dir).resolve()
    if status not in (QUESTION_STATUS_ANSWERED, QUESTION_STATUS_STALE):
        return False

    try:
        q_file = resolve_question_path(run_dir, qid)
    except ValueError:
        return False
    if not q_file.is_file():
        return False

    answers_dir = run_dir / "answers"
    answers_dir.mkdir(parents=True, exist_ok=True)
    lock_file = answers_dir / f"{qid}.lock"

    with FileLock(str(lock_file)):
        try:
            q_data = json.loads(q_file.read_text(encoding="utf-8"))
        except Exception:
            return False

        if q_data.get("status") != QUESTION_STATUS_OPEN:
            return False

        q_data["status"] = status
        q_data["status_reason"] = str(reason)
        q_data["status_updated_at"] = utc_now()

        # Atomic write
        tmp_q = q_file.parent / f".tmp_{qid}_{os.getpid()}_{time.time_ns()}"
        try:
            with tmp_q.open("w", encoding="utf-8") as handle:
                handle.write(json.dumps(q_data, indent=2) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(str(tmp_q), str(q_file))
        finally:
            if tmp_q.exists():
                tmp_q.unlink()

        _append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": utc_now(),
                "event": "question-status",
                "question_id": qid,
                "status": status,
                "reason": str(reason),
            },
        )

        write_projection(run_dir)
        return True


def write_projection(run_dir: Path | str) -> Path | None:
    """Write run_dir/open-questions.md using set_records.render_open_questions (E-03).

    Atomic write under questions/.projection.lock.
    Catches OSError and appends 'projection-write-failed' event so runner loop is never broken.
    """
    run_dir = Path(run_dir).resolve()
    questions_dir = run_dir / "questions"
    questions_dir.mkdir(parents=True, exist_ok=True)
    lock_file = questions_dir / ".projection.lock"

    try:
        with FileLock(str(lock_file)):
            records: list[dict[str, Any]] = []

            # Gather question records
            if questions_dir.is_dir():
                for q_file in sorted(questions_dir.glob("*.json")):
                    if q_file.name.startswith("."):
                        continue
                    try:
                        q_data = json.loads(q_file.read_text(encoding="utf-8"))
                        if isinstance(q_data, dict):
                            qid = q_data.get("question_id", q_file.stem)
                            art_id6 = q_data.get("artifact_id6")
                            records.append(
                                {
                                    "kind": "question_raised",
                                    "question_id": qid,
                                    "context": q_data.get("text", ""),
                                    "affected_nodes": [art_id6] if art_id6 else [],
                                    "timestamp": q_data.get("created_at", ""),
                                    "actor": "worker",
                                }
                            )
                            if q_data.get("status") in (
                                QUESTION_STATUS_ANSWERED,
                                QUESTION_STATUS_STALE,
                            ):
                                records.append(
                                    {
                                        "kind": "question_disposition",
                                        "question_id": qid,
                                    }
                                )
                    except Exception:
                        pass

            # Gather answer records
            answers_dir = run_dir / "answers"
            if answers_dir.is_dir():
                for a_file in sorted(answers_dir.glob("*.json")):
                    if a_file.name.startswith("."):
                        continue
                    try:
                        a_data = json.loads(a_file.read_text(encoding="utf-8"))
                        if isinstance(a_data, dict):
                            ans_qid = a_data.get("question_id") or a_file.stem
                            records.append(
                                {
                                    "kind": "human_answer",
                                    "question_id": ans_qid,
                                }
                            )
                    except Exception:
                        pass

            content = set_records.render_open_questions(records)
            out_file = run_dir / set_records.OPEN_QUESTIONS_FILE

            tmp_out = (
                run_dir
                / f".tmp_{set_records.OPEN_QUESTIONS_FILE}_{os.getpid()}_{time.time_ns()}"
            )
            with tmp_out.open("w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(str(tmp_out), str(out_file))
            return out_file
    except OSError as err:
        try:
            _append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": utc_now(),
                    "event": "projection-write-failed",
                    "error": str(err),
                },
            )
        except Exception:
            pass
        return None
