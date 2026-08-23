"""Universal artifact rename engine for all canonical repository artifact types.

Implements the noun-verb `aw rename <type> <selector> [--slug <new-slug>] [--set <set-id>] [--order <NN>] [--apply]`
for backlog, specs, prompts, walkthroughs, roadmaps, and releases (plus plans/research via unified dispatch).
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from agent_workflows import artifact_core as _core
from agent_workflows import selectors
from agent_workflows.project_context import resolve_verb_repo_root

# Regular expression patterns for artifact filenames
_UNIFORM_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<set>[a-z0-9-]+?)-(?P<nn>\d{2})-(?P<id6>[0-9a-z]{6})-(?P<slug>[a-z0-9-]+)"
    r"(?:\.(?P<facet>[a-z0-9.-]+))?\.md\Z"
)

_LEGACY_TIMESTAMP_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<hhmm>\d{4})-(?P<nn>\d{2})-(?P<slug>[a-z0-9-]+)"
    r"(?:\.(?P<facet>[a-z0-9.-]+))?\.md\Z"
)

_WALKTHROUGH_DATED_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<slug>[a-z0-9-]+)-walkthrough\.md\Z"
)

_WALKTHROUGH_BARE_RE = re.compile(r"\A(?P<slug>[a-z0-9-]+)-walkthrough\.md\Z")

_DATED_SLUG_FACET_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<slug>[a-z0-9-]+)(?:\.(?P<facet>[a-z0-9.-]+))?\.md\Z"
)

_SET_LINE_RE = re.compile(r"(?m)^- Set:\s*(.+?)\s*$")
_ORDER_LINE_RE = re.compile(r"(?m)^- Order:\s*(\d+)\s*$")


@dataclass
class RefEdit:
    file: Path
    kind: str
    old: str
    new: str
    hits: int


def _resolve_repo_root(args: argparse.Namespace) -> Path:
    return resolve_verb_repo_root(getattr(args, "dir", None))


def find_target_record(
    repo_root: Path, artifact_type: str, selector: str
) -> Optional[Path]:
    """Resolve a selector (path, id6, setid, or substring) to an existing artifact path."""
    if not selector:
        return None
    # 1. Direct path check
    candidate = Path(selector)
    if candidate.is_file():
        return candidate.resolve()
    candidate_rel = repo_root / selector
    if candidate_rel.is_file():
        return candidate_rel.resolve()

    # 2. Use selectors resolver
    hits = selectors.resolve_one(repo_root, artifact_type, selector)
    if hits:
        return hits[0].resolve()

    # 3. Direct scan of record directories
    for d in selectors.record_dirs(repo_root, artifact_type):
        if not d.is_dir():
            continue
        for f in d.rglob("*.md"):
            if f.name in {"README.md", "INDEX.md", "STATUS.md"}:
                continue
            if selector in f.name or selector == f.stem:
                return f.resolve()
    return None


def compute_target_name(
    src_name: str,
    artifact_type: str,
    new_slug: Optional[str] = None,
    new_set: Optional[str] = None,
    new_order: Optional[int] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Compute the new filename given the existing name and mutation arguments.

    Returns (new_name, error_message).
    """
    if not new_slug and new_set is None and new_order is None:
        return None, "at least one of --slug, --set, or --order is required to rename"

    m_uni = _UNIFORM_RE.match(src_name)
    if m_uni:
        date_str = m_uni.group("date")
        set_id = _core.kebab(new_set) if new_set else m_uni.group("set")
        order_num = new_order if new_order is not None else int(m_uni.group("nn"))
        id6 = m_uni.group("id6")
        slug = _core.kebab(new_slug) if new_slug else m_uni.group("slug")
        facet = m_uni.group("facet")
        ext = f".{facet}.md" if facet else ".md"
        return f"{date_str}-{set_id}-{order_num:02d}-{id6}-{slug}{ext}", None

    m_ts = _LEGACY_TIMESTAMP_RE.match(src_name)
    if m_ts:
        date_str = m_ts.group("date")
        hhmm = m_ts.group("hhmm")
        order_num = new_order if new_order is not None else int(m_ts.group("nn"))
        slug = _core.kebab(new_slug) if new_slug else m_ts.group("slug")
        facet = m_ts.group("facet")
        ext = f".{facet}.md" if facet else ".md"
        return f"{date_str}-{hhmm}-{order_num:02d}-{slug}{ext}", None

    m_wt_d = _WALKTHROUGH_DATED_RE.match(src_name)
    if m_wt_d:
        date_str = m_wt_d.group("date")
        slug = _core.kebab(new_slug) if new_slug else m_wt_d.group("slug")
        return f"{date_str}-{slug}-walkthrough.md", None

    m_wt_b = _WALKTHROUGH_BARE_RE.match(src_name)
    if m_wt_b:
        slug = _core.kebab(new_slug) if new_slug else m_wt_b.group("slug")
        return f"{slug}-walkthrough.md", None

    m_dated = _DATED_SLUG_FACET_RE.match(src_name)
    if m_dated:
        date_str = m_dated.group("date")
        slug = _core.kebab(new_slug) if new_slug else m_dated.group("slug")
        facet = m_dated.group("facet")
        ext = f".{facet}.md" if facet else ".md"
        return f"{date_str}-{slug}{ext}", None

    # Free-form filename fallback
    if new_slug:
        clean_slug = _core.kebab(new_slug)
        if src_name.endswith(".md"):
            return f"{clean_slug}.md", None
        return f"{clean_slug}", None

    return None, f"unable to parse and compute new name for {src_name}"


def plan_reference_rewrites(
    repo_root: Path, old_name: str, new_name: str
) -> List[RefEdit]:
    """Find all inbound references across SCAN_ROOTS to rewrite."""
    edits: List[RefEdit] = []
    old_stem = old_name[:-3] if old_name.endswith(".md") else old_name
    new_stem = new_name[:-3] if new_name.endswith(".md") else new_name

    for f in _core.iter_scan_files(repo_root):
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        # 1. Full name matches
        if old_name in text:
            hits = text.count(old_name)
            edits.append(RefEdit(f, "full-name", old_name, new_name, hits))

        # 2. Bare stem word-boundary matches (if stem is distinct from full name and not purely generic)
        if old_stem != old_name and len(old_stem) >= 6:
            # Avoid duplicate counting if already matched full name
            pat = re.compile(
                r"(?<![0-9A-Za-z-])" + re.escape(old_stem) + r"(?![0-9A-Za-z-])"
            )
            matches = pat.findall(text)
            if matches:
                # Count occurrences that are not part of old_name
                # Subtract full name occurrences if they overlap
                edits.append(RefEdit(f, "bare-stem", old_stem, new_stem, len(matches)))

    return edits


def apply_reference_rewrites(edits: List[RefEdit]) -> None:
    """Apply reference rewrites to referencing files."""
    by_file: dict[Path, list[RefEdit]] = {}
    for e in edits:
        by_file.setdefault(e.file, []).append(e)

    for f, file_edits in by_file.items():
        try:
            text = f.read_text(encoding="utf-8")
            # Apply full-name rewrites first, then bare-stem
            for e in sorted(
                file_edits, key=lambda x: 0 if x.kind == "full-name" else 1
            ):
                if e.kind == "full-name":
                    text = text.replace(e.old, e.new)
                else:
                    pat = re.compile(
                        r"(?<![0-9A-Za-z-])" + re.escape(e.old) + r"(?![0-9A-Za-z-])"
                    )
                    text = pat.sub(e.new, text)
            _core.atomic_write(f, text, prefix=".aw-ref-")
        except OSError:
            pass


def _update_frontmatter_metadata(
    file_path: Path, set_id: Optional[str] = None, order: Optional[int] = None
) -> None:
    """Update Set and Order metadata in the file frontmatter if present."""
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError:
        return

    updated = False
    if set_id is not None and _SET_LINE_RE.search(text):
        text = _SET_LINE_RE.sub(f"- Set: {set_id}", text)
        updated = True

    if order is not None and _ORDER_LINE_RE.search(text):
        text = _ORDER_LINE_RE.sub(f"- Order: {order}", text)
        updated = True

    if updated:
        _core.atomic_write(file_path, text, prefix=".aw-meta-")


def _update_or_inject_set_metadata(
    file_path: Path, set_id: Optional[str] = None, order: Optional[int] = None
) -> None:
    """Update or inject Set and Order metadata in the file frontmatter."""
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError:
        return

    lines = text.splitlines()
    updated = False
    is_fenced_yaml = bool(lines and lines[0].strip() == "---")

    if is_fenced_yaml:
        new_lines = []
        set_done = False
        in_fm = True
        for line in lines:
            if in_fm and line.strip() == "---" and new_lines:
                in_fm = False
                if set_id is not None and not set_done:
                    new_lines.append(f"set: {set_id}")
                    if order is not None:
                        new_lines.append(f"order: {order}")
                    set_done = True
                    updated = True
                new_lines.append(line)
            elif in_fm and re.match(r"^set:\s*", line, re.IGNORECASE):
                if set_id is not None:
                    new_lines.append(f"set: {set_id}")
                    set_done = True
                    updated = True
                else:
                    new_lines.append(line)
            elif (
                in_fm
                and order is not None
                and re.match(r"^order:\s*", line, re.IGNORECASE)
            ):
                new_lines.append(f"order: {order}")
                updated = True
            else:
                new_lines.append(line)
        lines = new_lines
    else:
        # Markdown bullet frontmatter
        set_done = False
        new_lines = []
        in_fm = True
        for line in lines:
            if in_fm and line.startswith("## "):
                in_fm = False
                if set_id is not None and not set_done:
                    new_lines.append(f"- Set: {set_id}")
                    if order is not None:
                        new_lines.append(f"- Order: {order}")
                    set_done = True
                    updated = True
            if in_fm and _SET_LINE_RE.match(line):
                if set_id is not None:
                    new_lines.append(f"- Set: {set_id}")
                    set_done = True
                    updated = True
                else:
                    new_lines.append(line)
            elif in_fm and order is not None and _ORDER_LINE_RE.match(line):
                new_lines.append(f"- Order: {order}")
                updated = True
            else:
                new_lines.append(line)

        if set_id is not None and not set_done:
            inserted = False
            res = []
            for line in new_lines:
                res.append(line)
                if not inserted and (
                    line.startswith("# ") or line.startswith("- Date:")
                ):
                    res.append(f"- Set: {set_id}")
                    if order is not None:
                        res.append(f"- Order: {order}")
                    inserted = True
                    updated = True
            if not inserted:
                res.insert(0, f"- Set: {set_id}")
                if order is not None:
                    res.insert(1, f"- Order: {order}")
                updated = True
            lines = res
        else:
            lines = new_lines

    if updated:
        _core.atomic_write(
            file_path, "\n".join(lines).rstrip() + "\n", prefix=".aw-meta-"
        )


def run_rename_generic(args: argparse.Namespace, artifact_type: str) -> int:
    """Universal rename execution engine for an artifact type."""
    repo_root = _resolve_repo_root(args)
    selector = getattr(args, "id", None) or getattr(args, "selector", None)
    if isinstance(selector, list):
        selector = selector[0] if selector else None

    if not selector:
        print("error: at least one <id6>, <setid>, or <path> is required")
        return 2

    src = find_target_record(repo_root, artifact_type, selector)
    if src is None or not src.exists():
        print(f"error: no {artifact_type} artifact matched '{selector}'")
        return 2

    new_slug = getattr(args, "slug", None)
    new_set = getattr(args, "set", None)
    new_order = getattr(args, "order", None)

    new_name, err = compute_target_name(
        src.name,
        artifact_type,
        new_slug=new_slug,
        new_set=new_set,
        new_order=new_order,
    )
    if err:
        print(f"error: {err}")
        return 2

    assert new_name is not None
    dst = src.parent / new_name

    apply = bool(getattr(args, "apply", False))
    update_refs = not bool(getattr(args, "no_refs", False))

    if dst.resolve() != src.resolve() and dst.exists():
        print(f"error: destination file already exists: {dst.name}")
        return 2

    ref_edits = (
        plan_reference_rewrites(repo_root, src.name, new_name) if update_refs else []
    )

    if not apply:
        print(
            f"--- would rename {src.relative_to(repo_root).as_posix()} -> {new_name} ---"
        )
        if update_refs:
            for e in ref_edits:
                try:
                    rel_f = e.file.relative_to(repo_root).as_posix()
                except ValueError:
                    rel_f = str(e.file)
                print(
                    f"--- would rewrite {e.hits}x '{e.old}' -> '{e.new}' in {rel_f} ---"
                )
        return 0

    # Apply changes
    if src.resolve() != dst.resolve():
        src_rel = src.relative_to(repo_root).as_posix()
        dst_rel = dst.relative_to(repo_root).as_posix()
        _core.git_mv(repo_root, src_rel, dst_rel)
        print(f"renamed {src_rel} -> {dst_rel}")

    if new_set is not None or new_order is not None:
        _update_frontmatter_metadata(
            dst, set_id=_core.kebab(new_set) if new_set else None, order=new_order
        )

    if update_refs and ref_edits:
        apply_reference_rewrites(ref_edits)
        for e in ref_edits:
            try:
                rel_f = e.file.relative_to(repo_root).as_posix()
            except ValueError:
                rel_f = str(e.file)
            print(f"rewrote {e.hits}x '{e.old}' -> '{e.new}' in {rel_f}")

    # Auto-index if supported
    if artifact_type in {"plans", "research"}:
        try:
            if artifact_type == "plans":
                from agent_workflows import plans_index as _pidx

                _pidx.run_index(
                    argparse.Namespace(
                        dir=str(repo_root),
                        check=False,
                        as_agent=False,
                        json=False,
                        no_color=True,
                        limit=None,
                        quiet=True,
                    )
                )
            elif artifact_type == "research":
                from agent_workflows import research_index as _ridx

                _ridx.run_index(
                    argparse.Namespace(
                        dir=str(repo_root),
                        check=False,
                        agent=False,
                        limit=None,
                        quiet=True,
                    )
                )
        except Exception:
            pass

    return 0


def run_group_generic(args: argparse.Namespace, artifact_type: str) -> int:
    """Universal set assignment / group execution engine for an artifact type."""
    repo_root = _resolve_repo_root(args)
    raw_selectors = (
        getattr(args, "ids", None)
        or getattr(args, "selector", None)
        or [getattr(args, "id", None)]
    )
    if isinstance(raw_selectors, str):
        raw_selectors = [raw_selectors]
    selectors_list = [s.strip() for s in (raw_selectors or []) if s and s.strip()]

    if not selectors_list:
        print("error: at least one <id6>, <setid>, or <path> is required")
        return 2

    new_set = getattr(args, "set", None)
    if not new_set or not new_set.strip():
        print("error: --set <set-id> is required")
        return 2

    set_k = _core.kebab(new_set)
    start_order = getattr(args, "order", None)
    apply = bool(getattr(args, "apply", False))
    update_refs = not bool(getattr(args, "no_refs", False))
    rename_files = bool(getattr(args, "rename", False))

    targets: List[Tuple[Path, Path, Optional[int]]] = []
    all_edits: List[RefEdit] = []

    for i, sel in enumerate(selectors_list):
        src = find_target_record(repo_root, artifact_type, sel)
        if src is None or not src.exists():
            print(f"error: no {artifact_type} artifact matched '{sel}'")
            return 2
        order_val = (start_order + i) if start_order is not None else None
        if rename_files:
            new_name, err = compute_target_name(
                src.name,
                artifact_type,
                new_set=set_k,
                new_order=order_val,
            )
            if err:
                new_name = src.name
            assert new_name is not None
            dst = src.parent / new_name
        else:
            dst = src

        if dst.resolve() != src.resolve() and dst.exists():
            print(f"error: destination file already exists: {dst.name}")
            return 2

        targets.append((src, dst, order_val))
        if update_refs and src.name != dst.name:
            all_edits.extend(plan_reference_rewrites(repo_root, src.name, dst.name))

    if not apply:
        for src, dst, _order_val in targets:
            src_rel = src.relative_to(repo_root).as_posix()
            if src.resolve() != dst.resolve():
                print(f"--- would rename {src_rel} -> {dst.name} ---")
            print(f"--- would set metadata Set: {set_k} in {src_rel} ---")
        if update_refs:
            for e in all_edits:
                try:
                    rel_f = e.file.relative_to(repo_root).as_posix()
                except ValueError:
                    rel_f = str(e.file)
                print(
                    f"--- would rewrite {e.hits}x '{e.old}' -> '{e.new}' in {rel_f} ---"
                )
        return 0

    # Apply changes
    for src, dst, order_val in targets:
        if src.resolve() != dst.resolve():
            src_rel = src.relative_to(repo_root).as_posix()
            dst_rel = dst.relative_to(repo_root).as_posix()
            _core.git_mv(repo_root, src_rel, dst_rel)
            print(f"renamed {src_rel} -> {dst_rel}")
        _update_or_inject_set_metadata(dst, set_id=set_k, order=order_val)
        dst_rel = dst.relative_to(repo_root).as_posix()
        print(f"set metadata Set: {set_k} in {dst_rel}")

    if update_refs and all_edits:
        apply_reference_rewrites(all_edits)
        for e in all_edits:
            try:
                rel_f = e.file.relative_to(repo_root).as_posix()
            except ValueError:
                rel_f = str(e.file)
            print(f"rewrote {e.hits}x '{e.old}' -> '{e.new}' in {rel_f}")

    # Auto-index if indexed type
    if artifact_type in {"plans", "research"}:
        try:
            if artifact_type == "plans":
                from agent_workflows import plans_index as _pidx

                _pidx.run_index(
                    argparse.Namespace(
                        dir=str(repo_root),
                        check=False,
                        as_agent=False,
                        json=False,
                        no_color=True,
                        limit=None,
                        quiet=True,
                    )
                )
            elif artifact_type == "research":
                from agent_workflows import research_index as _ridx

                _ridx.run_index(
                    argparse.Namespace(
                        dir=str(repo_root),
                        check=False,
                        agent=False,
                        limit=None,
                        quiet=True,
                    )
                )
        except Exception:
            pass

    return 0


def run_rename_backlog(args: argparse.Namespace) -> int:
    return run_rename_generic(args, "backlog")


def run_rename_specs(args: argparse.Namespace) -> int:
    return run_rename_generic(args, "specs")


def run_rename_prompts(args: argparse.Namespace) -> int:
    return run_rename_generic(args, "prompts")


def run_rename_walkthroughs(args: argparse.Namespace) -> int:
    return run_rename_generic(args, "walkthroughs")


def run_rename_roadmaps(args: argparse.Namespace) -> int:
    return run_rename_generic(args, "roadmaps")


def run_rename_releases(args: argparse.Namespace) -> int:
    return run_rename_generic(args, "releases")


def run_group_backlog(args: argparse.Namespace) -> int:
    return run_group_generic(args, "backlog")


def run_group_specs(args: argparse.Namespace) -> int:
    return run_group_generic(args, "specs")


def run_group_prompts(args: argparse.Namespace) -> int:
    return run_group_generic(args, "prompts")


def run_group_walkthroughs(args: argparse.Namespace) -> int:
    return run_group_generic(args, "walkthroughs")


def run_group_roadmaps(args: argparse.Namespace) -> int:
    return run_group_generic(args, "roadmaps")


def run_group_releases(args: argparse.Namespace) -> int:
    return run_group_generic(args, "releases")
