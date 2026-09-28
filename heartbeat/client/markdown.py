"""Markdown subset to HTML conversion for diary preview."""

from __future__ import annotations

import html
import re
from collections.abc import Callable

_INLINE_RULES: tuple[tuple[str, str], ...] = (
    (r"\*\*(.+?)\*\*", r"<b>\1</b>"),
    (r"\*(.+?)\*", r"<i>\1</i>"),
    (r"`([^`]+)`", r"<code>\1</code>"),
    (r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>'),
)


def _inline(text: str) -> str:
    result = html.escape(text)
    for pattern, replacement in _INLINE_RULES:
        result = re.sub(pattern, replacement, result)
    return result


def _heading(level: int) -> Callable[[re.Match[str]], str]:
    tag = f"h{level}"

    def build(match: re.Match[str]) -> str:
        return f"<{tag}>{_inline(match.group(1))}</{tag}>"

    return build


_BLOCK_RULES: tuple[tuple[str, Callable[[re.Match[str]], str]], ...] = (
    (r"^# (.+)$", _heading(1)),
    (r"^## (.+)$", _heading(2)),
    (r"^### (.+)$", _heading(3)),
    (r"^- (.+)$", lambda match: f"<ul><li>{_inline(match.group(1))}</li></ul>"),
    (r"^\d+\. (.+)$", lambda match: f"<ol><li>{_inline(match.group(1))}</li></ol>"),
    (r"^> (.+)$", lambda match: f"<blockquote>{_inline(match.group(1))}</blockquote>"),
    (r"^---+$", lambda _match: "<hr/>"),
)


def _line_html(line: str) -> str:
    for pattern, builder in _BLOCK_RULES:
        match = re.match(pattern, line)
        if match:
            return builder(match)
    return f"<p>{_inline(line)}</p>" if line else ""


def markdown_to_html(text: str) -> str:
    """Convert a Markdown subset into HTML suitable for QTextBrowser."""
    return "\n".join(_line_html(line.rstrip()) for line in text.splitlines())
