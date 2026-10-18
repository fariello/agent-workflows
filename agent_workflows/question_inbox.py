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
from typing import Any, Mapping, NamedTuple, Optional, Sequence

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


def question_fingerprint(text: str, options: Any = None) -> str:
    """Compute question fingerprint using shared implementation."""
    from agent_workflows import runner_shared

    return runner_shared.question_fingerprint(text, options)


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


class QuestionGroupMember(dict):
    """A member question in a QuestionGroup."""

    def __init__(
        self,
        question_id: str,
        artifact_id6: str,
        action: str,
        artifact_hash: str,
        position: int = 0,
        **extra: Any,
    ) -> None:
        super().__init__(
            question_id=question_id,
            artifact_id6=artifact_id6,
            action=action,
            artifact_hash=artifact_hash,
            position=position,
            **extra,
        )

    @property
    def question_id(self) -> str:
        return self["question_id"]

    @property
    def artifact_id6(self) -> str:
        return self["artifact_id6"]

    @property
    def action(self) -> str:
        return self["action"]

    @property
    def artifact_hash(self) -> str:
        return self["artifact_hash"]

    @property
    def position(self) -> int:
        return self.get("position", 0)

    @property
    def raw(self) -> dict[str, Any]:
        val = self.get("raw")
        return val if isinstance(val, dict) else self

    @property
    def blocking(self) -> bool:
        return bool(self.get("blocking", True))


class QuestionGroup:
    """A deduplicated group of questions sharing a fingerprint and collision guard."""

    def __init__(
        self,
        group_id: str,
        fingerprint: str,
        text: str,
        options: list[str] | None,
        allow_free_text: bool,
        members: list[Any],
        unblock_count: int = 0,
    ) -> None:
        self.group_id = group_id
        self.fingerprint = fingerprint
        self.text = text
        self.options = options
        self.allow_free_text = allow_free_text
        self.members = [
            m if isinstance(m, QuestionGroupMember) else QuestionGroupMember(**m)
            for m in members
        ]
        self.unblock_count = unblock_count

    @property
    def raisers(self) -> list[str]:
        return sorted({m.artifact_id6 for m in self.members if m.artifact_id6})

    @property
    def member_count(self) -> int:
        return len(self.members)

    @property
    def oq_id(self) -> str:
        return self.members[0].question_id if self.members else ""

    @property
    def heading(self) -> str:
        return self.text

    @property
    def artifact_id6(self) -> str:
        return self.members[0].artifact_id6 if self.members else ""

    @property
    def blocking(self) -> bool:
        return any(m.blocking for m in self.members)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __repr__(self) -> str:
        return (
            f"QuestionGroup(group_id={self.group_id!r}, "
            f"members={len(self.members)}, unblock_count={self.unblock_count})"
        )


class GroupAnswerResult(NamedTuple):
    """Result of writing an answer to a question group."""

    status: str  # "recorded", "already", "rejected"
    reason: str
    group_id: str
    results: dict[str, AnswerResult]
    applied_to: list[dict[str, str]]

    @property
    def recorded(self) -> bool:
        return self.status == "recorded"

    @property
    def already(self) -> bool:
        return self.status == "already"

    @property
    def rejected(self) -> bool:
        return self.status == "rejected"

    @property
    def recorded_count(self) -> int:
        return sum(1 for r in self.results.values() if r.recorded)

    @property
    def already_count(self) -> int:
        return sum(1 for r in self.results.values() if r.already)

    @property
    def refused_count(self) -> int:
        return sum(1 for r in self.results.values() if not r.recorded and not r.already)

    @property
    def refused_reasons(self) -> list[str]:
        return [
            r.reason
            for r in self.results.values()
            if not r.recorded and not r.already and r.reason
        ]


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
    applied_to: list[dict[str, Any]] | None = None,
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
        effective_applied_to = applied_to
        if effective_applied_to is None:
            effective_applied_to = [
                {
                    "question_id": qid,
                    "artifact_id6": str(q_data_locked.get("artifact_id6", "")),
                }
            ]
        ans_record = {
            "schema": ANSWER_SCHEMA,
            "question_id": qid,
            "answer": str_answer,
            "choice": choice,
            "actor": actor,
            "channel": str_channel,
            "sender": str_sender,
            "artifact_hash": artifact_hash,
            "applied_to": effective_applied_to,
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
                "applied_to": effective_applied_to,
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


def group_questions(
    records: Sequence[Any],
    state: Mapping[str, Any] | None = None,
) -> list[QuestionGroup]:
    """Group questions by fingerprint and collision guard, ordered by unblock count and action (E-01).

    Group key: question_fingerprint(text, options) AND exact equality of normalized text,
    normalized options, and allow_free_text. Stable group_id: g-<fingerprint> plus -<n> suffix
    only for collision splits.
    Unblock count: size of UNION over group's raisers of {the raiser} plus every queue item
    transitively depending on it that is still queued or awaiting-human.
    Order: unblock count descending; ANY execute member precedes only review/preflight; lowest member queue position.
    """
    from agent_workflows import runner_shared

    if not records:
        return []

    # 1. Normalize each record into a common dict representation
    norm_records: list[dict[str, Any]] = []
    for r in records:
        if isinstance(r, Mapping):
            q_id = str(r.get("question_id") or r.get("oq_id") or "")
            art_id6 = str(r.get("artifact_id6") or "")
            action = str(r.get("action") or "execute")
            art_hash = str(r.get("artifact_hash") or "")
            text = str(r.get("text") or r.get("heading") or "")
            raw_opts = r.get("options")
            options = list(raw_opts) if raw_opts is not None else None
            allow_free = bool(r.get("allow_free_text", True))
            fp = r.get("fingerprint")
            pos = int(r.get("position", 0))
        else:
            q_id = str(
                getattr(r, "question_id", None) or getattr(r, "oq_id", None) or ""
            )
            art_id6 = str(getattr(r, "artifact_id6", None) or "")
            action = str(
                getattr(r, "action", None)
                or (
                    "preflight"
                    if isinstance(r, runner_shared.PreflightQuestion)
                    else "execute"
                )
            )
            art_hash = str(getattr(r, "artifact_hash", None) or "")
            text = str(getattr(r, "text", None) or getattr(r, "heading", None) or "")
            raw_opts = getattr(r, "options", None)
            options = list(raw_opts) if raw_opts is not None else None
            allow_free = bool(getattr(r, "allow_free_text", True))
            fp = getattr(r, "fingerprint", None)
            pos = int(getattr(r, "position", 0))

        if not fp:
            fp = runner_shared.question_fingerprint(text, options)

        if pos <= 0 and q_id:
            m_pos = re.match(r"^(\d+)-", q_id)
            if m_pos:
                pos = int(m_pos.group(1))

        norm_text = runner_shared._normalize_question_text(text)
        if options is not None:
            norm_opts = tuple(
                runner_shared._normalize_question_text(opt) for opt in options
            )
        else:
            norm_opts = None

        norm_records.append(
            {
                "record": r,
                "question_id": q_id,
                "artifact_id6": art_id6,
                "action": action,
                "artifact_hash": art_hash,
                "text": text,
                "options": options,
                "allow_free_text": allow_free,
                "fingerprint": fp,
                "norm_text": norm_text,
                "norm_opts": norm_opts,
                "position": pos,
            }
        )

    # 2. Group by collision key: (fingerprint, norm_text, norm_opts, allow_free_text)
    subgroups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for nr in norm_records:
        collision_key = (
            nr["fingerprint"],
            nr["norm_text"],
            nr["norm_opts"],
            nr["allow_free_text"],
        )
        subgroups.setdefault(collision_key, []).append(nr)

    # 3. Group subgroups by fingerprint to detect collision splits
    by_fp: dict[str, list[tuple[Any, ...]]] = {}
    for col_key in subgroups.keys():
        fp = col_key[0]
        by_fp.setdefault(fp, []).append(col_key)

    # 4. Assign stable group_id: g-<fp> or g-<fp>-<n>
    group_items_map: dict[str, list[dict[str, Any]]] = {}
    for fp, col_keys in by_fp.items():
        if len(col_keys) == 1:
            group_items_map[f"g-{fp}"] = subgroups[col_keys[0]]
        else:
            # Sort collision splits deterministically
            sorted_keys = sorted(
                col_keys,
                key=lambda k: (k[1], k[2] or (), k[3]),
            )
            for idx, k in enumerate(sorted_keys, 1):
                group_items_map[f"g-{fp}-{idx}"] = subgroups[k]

    # 5. Build queue metadata from state for unblock counts
    queue: list[Mapping[str, Any]] = []
    if isinstance(state, Mapping):
        q = state.get("queue")
        if isinstance(q, Sequence):
            queue = [it for it in q if isinstance(it, Mapping)]

    status_by_id: dict[str, str] = {}
    pos_by_id: dict[str, int] = {}
    dependents: dict[str, set[str]] = {}

    for idx, it in enumerate(queue):
        it_id = str(it.get("id6") or "")
        if it_id:
            status_by_id[it_id] = str(it.get("status") or "")
            pos_by_id[it_id] = int(it.get("position", idx + 1))
            deps = it.get("dependencies") or []
            if isinstance(deps, Sequence):
                for dep in deps:
                    target_id = runner_shared.dependency_target_id6(str(dep))
                    if target_id:
                        dependents.setdefault(target_id, set()).add(it_id)

    # 6. Construct QuestionGroup objects
    groups: list[QuestionGroup] = []
    for gid, member_dicts in group_items_map.items():
        first = member_dicts[0]
        fp = first["fingerprint"]
        text = first["text"]
        options = first["options"]
        allow_free = first["allow_free_text"]

        members = []
        for m in member_dicts:
            rec_dict = (
                dict(m.get("record")) if isinstance(m.get("record"), Mapping) else {}
            )
            kw = dict(rec_dict)
            kw["question_id"] = m["question_id"]
            kw["artifact_id6"] = m["artifact_id6"]
            kw["action"] = m["action"]
            kw["artifact_hash"] = m["artifact_hash"]
            kw["position"] = pos_by_id.get(m["artifact_id6"], m["position"])
            kw["raw"] = rec_dict
            members.append(QuestionGroupMember(**kw))

        raisers = {m.artifact_id6 for m in members if m.artifact_id6}
        if queue:
            # Transitive dependents BFS
            candidates = set(raisers)
            bfs_q = list(raisers)
            visited = set(raisers)
            while bfs_q:
                curr = bfs_q.pop(0)
                for child in dependents.get(curr, ()):
                    if child not in visited:
                        visited.add(child)
                        candidates.add(child)
                        bfs_q.append(child)

            unblocked_set = {
                cid
                for cid in candidates
                if status_by_id.get(cid)
                in ("queued", runner_shared.AWAITING_HUMAN_STATUS)
            }
            unblock_count = len(unblocked_set)
        else:
            unblock_count = len(raisers)

        groups.append(
            QuestionGroup(
                group_id=gid,
                fingerprint=fp,
                text=text,
                options=options,
                allow_free_text=allow_free,
                members=members,
                unblock_count=unblock_count,
            )
        )

    # 7. Sort groups by unblock count, action rank, lowest queue pos, and group_id
    def _group_sort_key(grp: QuestionGroup):
        # 1. unblock count descending
        # 2. ANY execute member precedes only review/preflight
        has_execute = any(m.action == "execute" for m in grp.members)
        action_rank = 0 if has_execute else 1
        # 3. lowest member queue position
        min_pos = min(
            (m.position for m in grp.members if m.position > 0), default=999999
        )
        # 4. lowest member question_id (natural ordering of questions within item)
        min_qid = min((m.question_id for m in grp.members if m.question_id), default="")
        # 5. stable group_id
        return (-grp.unblock_count, action_rank, min_pos, min_qid, grp.group_id)

    groups.sort(key=_group_sort_key)
    return groups


def group_open_questions(
    run_dir: Path | str,
    state: Mapping[str, Any] | None = None,
) -> list[QuestionGroup]:
    """Group all open questions belonging to the current park of awaiting-human items (E-01).

    Reads run-scoped qids (item['question_ids']) stored on each awaiting-human item
    in state['queue'], loads those question files from questions/, filters to status 'open',
    and passes them to group_questions.
    """
    run_dir = Path(run_dir).resolve()
    records: list[dict[str, Any]] = []

    if (
        isinstance(state, Mapping)
        and "queue" in state
        and isinstance(state["queue"], Sequence)
    ):
        for item in state["queue"]:
            if isinstance(item, Mapping) and item.get("status") == "awaiting-human":
                qids = item.get("question_ids") or []
                if not qids and item.get("questions"):
                    # Fallback to questions list
                    qids = [
                        q.get("question_id")
                        for q in item["questions"]
                        if isinstance(q, Mapping) and q.get("question_id")
                    ]
                for qid in qids:
                    if not qid:
                        continue
                    q_data = read_question(run_dir, qid)
                    if q_data and q_data.get("status") == QUESTION_STATUS_OPEN:
                        if "position" in item and "position" not in q_data:
                            q_data["position"] = item["position"]
                        records.append(q_data)
    if not records:
        # Fallback if state has no awaiting-human items or no queue: read all open questions in questions/
        records = read_open_questions(run_dir)

    return group_questions(records, state)


def write_group_answer(
    run_dir: Path | str,
    state: Mapping[str, Any] | None,
    group_id: str,
    *,
    answer: str | None = None,
    choice: int | None = None,
    channel: str,
    sender: str,
    actor: str,
) -> GroupAnswerResult:
    """Write an answer to all open questions in a question group (spec 6kwd2e R4.2, R9.2, E-02).

    Under answers/.group.lock:
    - recomputes the group with group_open_questions
    - refuses an unknown group_id
    - calls write_answer once per member, passing applied_to naming all members
    - returns per-member results and aggregate status
    """
    run_dir = Path(run_dir).resolve()
    answers_dir = run_dir / "answers"
    answers_dir.mkdir(parents=True, exist_ok=True)
    group_lock_file = answers_dir / ".group.lock"

    with FileLock(str(group_lock_file)):
        groups = group_open_questions(run_dir, state)
        matched_group = None
        for g in groups:
            if g.group_id == group_id:
                matched_group = g
                break

        if matched_group is None:
            return GroupAnswerResult(
                status="rejected",
                reason=f"unknown group_id: {group_id!r}",
                group_id=group_id,
                results={},
                applied_to=[],
            )

        applied_to = [
            {"question_id": m.question_id, "artifact_id6": m.artifact_id6}
            for m in matched_group.members
        ]

        results: dict[str, AnswerResult] = {}
        recorded_count = 0
        already_count = 0
        first_rejection_reason = "rejected"

        for m in matched_group.members:
            qid = m.question_id
            res = write_answer(
                run_dir,
                qid,
                answer=answer,
                choice=choice,
                channel=channel,
                sender=sender,
                actor=actor,
                applied_to=applied_to,
            )
            results[qid] = res
            if res.recorded:
                recorded_count += 1
            elif res.already:
                already_count += 1
            else:
                if first_rejection_reason == "rejected":
                    first_rejection_reason = res.reason

        if recorded_count > 0:
            status = "recorded"
            reason = "recorded"
        elif already_count == len(matched_group.members):
            status = "already"
            reason = "already answered"
        else:
            status = "rejected"
            reason = first_rejection_reason

        return GroupAnswerResult(
            status=status,
            reason=reason,
            group_id=group_id,
            results=results,
            applied_to=applied_to,
        )


def _clean_worker_text_for_answers_file(text: str) -> str:
    """Clean worker-authored text for answers.md: strip ANSI and control characters."""
    from agent_workflows import term

    s = term.strip_ansi(str(text))
    cleaned: list[str] = []
    for ch in s:
        if ch in ("\n", "\t") or (
            ord(ch) >= 32 and ord(ch) != 127 and unicodedata.category(ch) != "Cc"
        ):
            cleaned.append(ch)
    return "".join(cleaned)


def write_answers_file(
    run_dir: Path | str,
    state: Mapping[str, Any] | None = None,
    *,
    resume_command: str,
) -> Path:
    """Write <run_dir>/answers.md atomically (spec 6kwd2e R5.1, R5.2, E-03)."""
    run_dir = Path(run_dir).resolve()
    groups = group_open_questions(run_dir, state)

    run_id = str(
        (state.get("run_id") if isinstance(state, Mapping) else None) or run_dir.name
    )
    distinct_count = len(groups)
    all_artifacts = sorted({art for g in groups for art in g.raisers})
    artifact_count = len(all_artifacts)
    total_unblock = sum(g.unblock_count for g in groups)

    lines: list[str] = [
        f"# Answers for Run {run_id}",
        "",
        f"- Distinct questions: {distinct_count}",
        f"- Artifacts affected: {artifact_count}",
        f"- Total unblock count: {total_unblock}",
        "",
        "## How to answer",
        "",
        "Edit this file and fill in the `Answer:` line for any question group below, or run:",
        f"  aw runs answer {run_id}",
        "",
        "To resume the run after editing answers:",
        "```sh",
        f"{resume_command}",
        "```",
        "",
    ]

    for g in groups:
        lines.append(f"<!-- aw:group {g.group_id} -->")
        lines.append(f"### Group {g.group_id}")
        lines.append("")
        qids_str = ", ".join(m.question_id for m in g.members)
        lines.append(f"- Question IDs: {qids_str}")
        lines.append(f"- Raisers ({len(g.raisers)}): {', '.join(g.raisers)}")
        lines.append(f"- Unblocks: {g.unblock_count} item(s)")
        if g.options:
            lines.append("- Options:")
            for idx, opt in enumerate(g.options, 1):
                clean_opt = _clean_worker_text_for_answers_file(opt)
                lines.append(f"  {idx}. {clean_opt}")
        lines.append("")

        # Quoted worker text: every line prefixed `> `
        cleaned_text = _clean_worker_text_for_answers_file(g.text)
        text_lines = cleaned_text.splitlines() if cleaned_text else [""]
        for tl in text_lines:
            lines.append(f"> {tl}" if tl else ">")
        lines.append("")
        lines.append("Answer: ")
        lines.append("")

    target_file = run_dir / "answers.md"
    content = "\n".join(lines) + "\n"

    tmp_file = run_dir / f".tmp_answers_{os.getpid()}_{time.time_ns()}.md"
    try:
        with tmp_file.open("w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(tmp_file), str(target_file))
    finally:
        if tmp_file.exists():
            tmp_file.unlink()

    return target_file


def ingest_answers_file(
    run_dir: Path | str,
    state: Mapping[str, Any] | None = None,
) -> int:
    """Ingest answers filled into <run_dir>/answers.md (spec 6kwd2e R5.1, R5.2, E-03).

    Reads only the unquoted Answer: line directly following each group's quoted block
    under an <!-- aw:group <group_id> --> marker. Ignores empty answer lines.
    Writes non-empty answers through write_group_answer with channel="answers-file",
    actor="human", sender=getpass.getuser().
    Returns the count of answers recorded.
    """
    import getpass

    run_dir = Path(run_dir).resolve()
    answers_md = run_dir / "answers.md"
    if not answers_md.is_file():
        return 0

    try:
        content = answers_md.read_text(encoding="utf-8")
    except Exception:
        return 0

    recorded_count = 0
    pattern = re.compile(r"<!--\s*aw:group\s+([A-Za-z0-9._-]+)\s*-->", re.MULTILINE)
    matches = list(pattern.finditer(content))
    for i, match in enumerate(matches):
        group_id = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        section = content[start:end]

        lines = section.splitlines()
        found_quoted = False
        answer_text = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(">"):
                found_quoted = True
            elif found_quoted and stripped.startswith("Answer:"):
                ans_val = stripped[len("Answer:") :].strip()
                if ans_val:
                    answer_text = ans_val
                break

        if answer_text:
            res = write_group_answer(
                run_dir,
                state,
                group_id,
                answer=answer_text,
                channel="answers-file",
                actor="human",
                sender=getpass.getuser(),
            )
            if res.recorded:
                recorded_count += 1

    return recorded_count
