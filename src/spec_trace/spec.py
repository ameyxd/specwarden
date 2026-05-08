from __future__ import annotations

import re
from collections.abc import Callable
from datetime import date, datetime, timezone

from .paths import RepoPaths


class SpecError(Exception):
    """Base class for spec lifecycle errors."""


class SpecAlreadyExists(SpecError):
    pass


class SpecNotFound(SpecError):
    pass


_SLUG_KEEP = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    lowered = text.strip().lower()
    collapsed = _SLUG_KEEP.sub("-", lowered)
    return collapsed.strip("-")


def _today() -> date:
    return datetime.now(timezone.utc).date()


SPEC_TEMPLATE = """\
# {spec_id}: {title}

**Created:** {created}
**Status:** active
**Author:** {author}

## Assumptions
What we are taking as given. If any of these turns out to be false, the spec is invalid and must be revised before more code lands.

- TODO

## Scope
What this change is. Concrete, files-and-functions level if possible.

- TODO

## Non-goals
What this change is explicitly not. The point of this section is to prevent scope creep mid-implementation.

- TODO

## Success criteria
How we will know we are done. Must be checkable.

- [ ] TODO
"""


def create_spec(
    paths: RepoPaths,
    title: str,
    *,
    author: str,
    today: Callable[[], date] = _today,
) -> str:
    paths.ensure_dirs()
    slug = slugify(title)
    if not slug:
        raise SpecError("title produced an empty slug")
    spec_id = f"{today().isoformat()}_{slug}"
    spec_file = paths.specs_dir / f"{spec_id}.md"
    if spec_file.exists():
        raise SpecAlreadyExists(spec_id)
    body = SPEC_TEMPLATE.format(
        spec_id=spec_id,
        title=title,
        created=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        author=author,
    )
    spec_file.write_text(body, encoding="utf-8")
    return spec_id


def activate_spec(paths: RepoPaths, spec_id: str) -> None:
    spec_file = paths.specs_dir / f"{spec_id}.md"
    if not spec_file.exists():
        raise SpecNotFound(spec_id)
    paths.ensure_dirs()
    paths.active_marker.write_text(spec_id + "\n", encoding="utf-8")


def deactivate_active(paths: RepoPaths) -> None:
    if paths.active_marker.exists():
        paths.active_marker.unlink()


def mark_done(paths: RepoPaths) -> str:
    spec_id = paths.active_spec_id()
    if spec_id is None:
        raise SpecNotFound("no active spec")
    spec_file = paths.specs_dir / f"{spec_id}.md"
    text = spec_file.read_text(encoding="utf-8")
    updated = text.replace("**Status:** active", "**Status:** completed", 1)
    spec_file.write_text(updated, encoding="utf-8")
    deactivate_active(paths)
    return spec_id
