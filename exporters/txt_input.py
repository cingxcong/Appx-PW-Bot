"""Safe parser for user-supplied TXT manifests.

Accepted formats:
    https://cdn.example/video.m3u8
    Lecture 01: https://cdn.example/video.m3u8

This module only parses URLs supplied by the user. It does not fetch, resolve,
rewrite, decrypt, or manufacture provider URLs.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

MAX_TEXT_BYTES = 2 * 1024 * 1024
MAX_LINES = 10_000
_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)


class ManifestInputError(ValueError):
    """Raised when an uploaded TXT manifest is invalid or too large."""


def _clean_url(candidate: str) -> str | None:
    candidate = candidate.strip().rstrip(".,;)")
    if not candidate:
        return None
    try:
        parsed = urlsplit(candidate)
        # Disallow non-HTTP schemes, missing hosts, and embedded credentials.
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            return None
        if parsed.username is not None or parsed.password is not None:
            return None
        # Accessing .port validates malformed port values.
        _ = parsed.port
    except ValueError:
        return None
    return candidate


def parse_txt_manifest(text: str) -> list[dict[str, object]]:
    """Parse raw URL lines or 'title: URL' lines, preserving URL bytes exactly."""
    if not isinstance(text, str):
        raise ManifestInputError("TXT content must be decoded text.")
    if len(text.encode("utf-8")) > MAX_TEXT_BYTES:
        raise ManifestInputError("TXT file exceeds the 2 MiB limit.")

    lines = text.splitlines()
    if len(lines) > MAX_LINES:
        raise ManifestInputError(f"TXT file exceeds the {MAX_LINES} line limit.")

    records: list[dict[str, object]] = []
    seen: set[str] = set()

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip().lstrip("\ufeff")
        if not line or line.startswith("#"):
            continue

        match = _URL_RE.search(line)
        if not match:
            continue
        url = _clean_url(match.group(0))
        if url is None or url in seen:
            continue

        # Treat text before the URL as a display title only; never use it to
        # alter the URL. A raw URL line gets a neutral title.
        title = line[:match.start()].strip().rstrip(":=- ").strip()
        records.append({
            "title": title or f"Item {len(records) + 1}",
            "url": url,
            "line_number": line_number,
        })
        seen.add(url)

    return records
