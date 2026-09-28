"""Limited-tag HTML sanitizer for remote README fragments."""
from __future__ import annotations

import html
import re
from html.parser import HTMLParser

ALLOWED_TAGS = frozenset(
    {
        "a",
        "abbr",
        "article",
        "b",
        "blockquote",
        "br",
        "code",
        "dd",
        "del",
        "details",
        "div",
        "dl",
        "dt",
        "em",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "hr",
        "i",
        "img",
        "kbd",
        "li",
        "ol",
        "p",
        "picture",
        "pre",
        "source",
        "span",
        "strong",
        "sub",
        "summary",
        "sup",
        "table",
        "tbody",
        "td",
        "tfoot",
        "th",
        "thead",
        "tr",
        "u",
        "ul",
        "wbr",
    }
)
DROP_TAGS = frozenset(
    {"script", "style", "iframe", "object", "embed", "link", "meta", "form", "template"}
)
VOID_TAGS = frozenset({"br", "hr", "img", "wbr", "source"})
GLOBAL_ATTRS = frozenset(
    {"title", "align", "colspan", "rowspan", "width", "height", "class", "id", "dir"}
)
URL_ATTRS = frozenset({"href", "src", "srcset"})
ATTR_ALLOW: dict[str, frozenset[str]] = {
    "a": frozenset({"href", "name", "rel", "target"}),
    "img": frozenset({"src", "srcset", "alt", "loading", "decoding"}),
    "source": frozenset({"srcset", "type", "media"}),
    "td": frozenset({"colspan", "rowspan"}),
    "th": frozenset({"colspan", "rowspan", "scope"}),
}
SAFE_URL_PREFIXES = ("http://", "https://", "mailto:", "#", "/", "./", "../")
SCHEME_PATTERN = re.compile(r"^[a-z][a-z0-9+.\-]*:")


def sanitize_html(fragment: str) -> str:
    """Return the fragment with only the allow-listed tags and safe URLs kept."""
    parser = _FragmentSanitizer()
    parser.feed(fragment or "")
    parser.close()
    return parser.result()


def _is_safe_url(value: str) -> bool:
    """Reject non-http schemes while keeping normal links and relative paths."""
    cleaned = value.strip().lower()
    if not cleaned:
        return False
    if cleaned.startswith(SAFE_URL_PREFIXES):
        return True
    return SCHEME_PATTERN.match(cleaned) is None


def _is_safe_srcset(value: str) -> bool:
    """Reject a srcset when any candidate URL is unsafe."""
    candidates = [chunk.strip().split()[0] for chunk in value.split(",") if chunk.strip()]
    return bool(candidates) and all(_is_safe_url(item) for item in candidates)


class _FragmentSanitizer(HTMLParser):
    """Rebuild HTML keeping only allow-listed tags, attributes and URL schemes."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._open: list[str] = []
        self._skip_depth = 0

    def result(self) -> str:
        """Return the sanitized HTML and close any still-open allowed tags."""
        while self._open:
            self._parts.append(f"</{self._open.pop()}>")
        return "".join(self._parts)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Emit an allow-listed start tag with filtered attributes."""
        name = tag.lower()
        if name in DROP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth or name not in ALLOWED_TAGS:
            return
        rendered = self._render_attrs(name, attrs)
        if name in VOID_TAGS:
            self._parts.append(f"<{name}{rendered}>")
            return
        self._parts.append(f"<{name}{rendered}>")
        self._open.append(name)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Emit an allow-listed self-closing tag."""
        name = tag.lower()
        if self._skip_depth or name in DROP_TAGS or name not in ALLOWED_TAGS:
            return
        self._parts.append(f"<{name}{self._render_attrs(name, attrs)}>")

    def handle_endtag(self, tag: str) -> None:
        """Close the nearest matching allow-listed tag."""
        name = tag.lower()
        if name in DROP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth or name not in ALLOWED_TAGS or name not in self._open:
            return
        while self._open:
            current = self._open.pop()
            self._parts.append(f"</{current}>")
            if current == name:
                break

    def handle_data(self, data: str) -> None:
        """Append escaped text while outside dropped subtrees."""
        if self._skip_depth:
            return
        self._parts.append(html.escape(data, quote=False))

    def handle_comment(self, data: str) -> None:
        """Drop comments."""
        return

    def handle_decl(self, decl: str) -> None:
        """Drop doctype declarations."""
        return

    def handle_pi(self, data: str) -> None:
        """Drop processing instructions."""
        return

    def _render_attrs(self, tag: str, attrs: list[tuple[str, str | None]]) -> str:
        """Render the safe subset of attributes for the given tag."""
        allowed = GLOBAL_ATTRS | ATTR_ALLOW.get(tag, frozenset())
        chunks: list[str] = []
        for raw_name, raw_value in attrs:
            name = raw_name.lower()
            value = raw_value or ""
            if name not in allowed:
                continue
            if name == "srcset" and not _is_safe_srcset(value):
                continue
            if name in URL_ATTRS and name != "srcset" and not _is_safe_url(value):
                continue
            if name in {"class", "id"}:
                value = "".join(ch for ch in value if ch.isalnum() or ch in "-_ ")
            chunks.append(f' {name}="{html.escape(value, quote=True)}"')
        return "".join(chunks)
