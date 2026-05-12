"""Parse the canonical `Spec: <id>` trailer from a commit message body.

Conservative on purpose: the trailer must start at column 0 (no leading
whitespace, no comment prefix) and the value must be a non-whitespace token.
Anything else is silently a non-match.
"""

from __future__ import annotations

import re

SPEC_TRAILER = re.compile(r"^Spec:\s*(?P<id>\S+)\s*$", re.MULTILINE)


def find_spec_id(body: str) -> str | None:
    match = SPEC_TRAILER.search(body)
    return match.group("id") if match else None
