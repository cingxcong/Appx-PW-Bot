"""Conservative, fixture-driven normalizers for authorized course API responses.

This module does not make network requests, decrypt opaque fields, construct media
URLs, or bypass provider access controls. It records only URLs explicitly present
as HTTP(S) strings in a supplied API response.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any
from urllib.parse import urlparse

URL_FIELDS = (
    "url", "video_url", "videoUrl", "hls_url", "hlsUrl", "stream_url",
    "streamUrl", "media_url", "mediaUrl", "download_url", "downloadUrl",
    "file_url", "fileUrl", "source_url", "sourceUrl", "video_link",
    "videoLink", "pdf_url", "pdfUrl", "pdf_link", "pdfLink", "attachment_url",
)
TITLE_FIELDS = ("title", "Title", "name", "Name", "test_name")
ID_FIELDS = ("id", "item_id", "contentId", "content_id", "video_id", "test_id")


def _first(mapping: Mapping[str, Any], names: Iterable[str]) -> Any:
    for name in names:
        value = mapping.get(name)
        if value not in (None, ""):
            return value
    return None


def _valid_http_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except ValueError:
        return False


def _find_explicit_url(item: Mapping[str, Any]) -> str | None:
    """Return the first literal HTTP(S) URL; never decrypt or synthesize it."""
    for key in URL_FIELDS:
        value = item.get(key)
        if _valid_http_url(value):
            return value.strip()
    return None


def _contains_questions(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key).lower() in {"questions", "questionlist", "question_list"} and isinstance(child, list) and child:
                return True
            if _contains_questions(child):
                return True
    elif isinstance(value, list):
        return any(_contains_questions(child) for child in value)
    return False


def _kind(item: Mapping[str, Any], url: str | None) -> str:
    raw = str(_first(item, ("material_type", "materialType", "contentType", "type")) or "").lower()
    if raw in {"folder", "1"}:
        return "folder"
    if raw in {"test", "assessment", "quiz", "test_series"}:
        return "test_series" if _contains_questions(item) else ("test_attachment" if url and urlparse(url).path.lower().endswith(".pdf") else "test_series")
    if raw in {"video", "lecture", "youtube"}:
        return "video"
    if raw in {"pdf", "document", "notes", "study_material"}:
        return "pdf"
    if raw in {"image", "photo"}:
        return "image"
    path = urlparse(url).path.lower() if url else ""
    if path.endswith(".pdf"):
        return "pdf"
    if path.endswith((".m3u8", ".mpd", ".mp4", ".mkv", ".webm")):
        return "video"
    if path.endswith((".jpg", ".jpeg", ".png", ".webp")):
        return "image"
    return "other"


def _unwrap_items(payload: Any) -> list[Mapping[str, Any]]:
    """Unwrap common API envelopes without assuming undocumented endpoints."""
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, Mapping)]
    if not isinstance(payload, Mapping):
        return []
    for key in ("data", "contents", "items", "results", "content"):
        value = payload.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, Mapping)]
        if isinstance(value, Mapping):
            nested = _unwrap_items(value)
            if nested:
                return nested
    return []


def _test_structure(item: Mapping[str, Any]) -> dict[str, Any] | None:
    """Copy common assessment fields only when explicitly present in the response."""
    questions = _first(item, ("questions", "questionList", "question_list"))
    if not isinstance(questions, list):
        data = item.get("data")
        if isinstance(data, Mapping):
            questions = _first(data, ("questions", "questionList", "question_list"))
    if not isinstance(questions, list):
        return None
    allowed_question_fields = (
        "id", "question_id", "questionId", "text", "question", "question_text",
        "type", "question_type", "marks", "negative_marks", "options",
        "answer", "correct_option", "correctOption", "explanation", "solution",
        "attachments",
    )
    cleaned = []
    for question in questions:
        if not isinstance(question, Mapping):
            continue
        cleaned.append({key: question[key] for key in allowed_question_fields if key in question})
    return {
        "test_id": _first(item, ("id", "test_id", "testId")),
        "title": _first(item, TITLE_FIELDS),
        "sections": item.get("sections") if isinstance(item.get("sections"), list) else None,
        "questions": cleaned,
    }


def normalize_item(item: Mapping[str, Any], *, platform: str, course_id: str | None = None,
                   course_name: str | None = None, folder_path: str = "") -> dict[str, Any]:
    url = _find_explicit_url(item)
    kind = _kind(item, url)
    title = _first(item, TITLE_FIELDS)
    item_id = _first(item, ID_FIELDS)
    status = "exported" if url else ("unsupported" if kind == "test_series" else "missing_url")
    result = {
        "platform": platform,
        "course_id": course_id,
        "course_name": course_name,
        "item_id": str(item_id) if item_id is not None else None,
        "parent_id": str(_first(item, ("parent_id", "parentId", "folder_id", "folderId"))) if _first(item, ("parent_id", "parentId", "folder_id", "folderId")) is not None else None,
        "title": str(title) if title is not None else "Untitled item",
        "content_type": _first(item, ("material_type", "materialType", "contentType", "type")),
        "kind": kind,
        "url": url,
        "url_type": "unknown" if url else None,
        "expires_at": _first(item, ("expires_at", "expiresAt", "expiry")),
        "folder_path": folder_path,
        "status": status,
    }
    if kind == "test_series":
        test_data = _test_structure(item)
        if test_data is not None:
            result["test_data"] = test_data
    # Do not copy opaque provider fields (which may contain credentials or keys).
    return result


def normalize_response(payload: Any, *, platform: str, course_id: str | None = None,
                       course_name: str | None = None) -> list[dict[str, Any]]:
    """Normalize one API response page/list. Folder traversal belongs to adapters."""
    records = []
    seen = set()
    for item in _unwrap_items(payload):
        record = normalize_item(item, platform=platform, course_id=course_id, course_name=course_name)
        identity = (record["item_id"], record["kind"], record["url"])
        if identity in seen:
            continue
        seen.add(identity)
        records.append(record)
    return records


def summarize(records: list[Mapping[str, Any]]) -> dict[str, int]:
    counts = {key: 0 for key in ("discovered", "exported", "missing_url", "unsupported", "failed", "unauthorized")}
    counts["discovered"] = len(records)
    for record in records:
        status = str(record.get("status", "failed"))
        if status in counts and status != "discovered":
            counts[status] += 1
        elif status not in counts:
            counts["failed"] += 1
    return counts
