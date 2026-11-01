# Authorized course exporter: implementation requirements

This document defines what counts as a correct export. It is intentionally stricter than the legacy URL-scraping behavior.

## Export record

Every discovered item should be represented as structured JSON with:

- `platform`: `classplus`, `appx`, or another explicitly supported provider
- `course_id`, `course_name`
- `item_id`, `parent_id`, `title`, `content_type`
- `kind`: `video`, `pdf`, `image`, `test_attachment`, `test_series`, or `other`
- `url`: the exact URL supplied by the authenticated API response
- `url_type`: `direct`, `signed`, or `unknown`
- `expires_at`: only when the API explicitly provides an expiry
- `metadata`: safe, non-secret source metadata
- `status`: `exported`, `missing_url`, `unauthorized`, `unsupported`, or `failed`

Do not rewrite thumbnail URLs into guessed HLS/DASH paths. Do not infer a URL from an item ID. Do not strip query parameters from signed URLs.

## Platform behavior

### Classplus

The legacy code enumerates public preview courses and uses a hard-coded access token to request content. That is not proof that the current account is entitled to the course. The replacement must use a documented or observed authenticated account flow and must verify the selected course is present in that account's entitled/purchased course list before enumerating it.

Keep the URL exactly as returned by the authorized content API. If a provider-supported signing operation is required, call it only with the authenticated account context and preserve the returned signed URL as a separate field. Never reconstruct a manifest from a thumbnail.

### Appx

The legacy code falls back to requests without `Authorization` and queries DRM-link endpoints. The replacement must never remove authentication headers after a failure and must not access or defeat DRM-protected streams.

Use the authorized account's course list and folder/content responses. Preserve direct video and PDF URLs returned in those responses. If a field is an opaque encrypted value or the response omits a URL, mark it unsupported/missing until its official, entitlement-preserving resolution is established. Do not silently invent a URL.

The current legacy implementation classifies `material_type == TEST` as a PDF attachment. That is not extraction of an interactive test series.

### Test series

A test series is complete only if the authorized API actually returns its structure. Where available, preserve:

- test/assessment ID and title
- section IDs and titles
- question IDs and question text
- question type and marks
- options with stable option IDs
- answer key / correct option only if returned to the entitled account
- explanation / solution only if returned to the entitled account
- attachment URLs, if any

If the API exposes only a PDF attachment, export that attachment as `test_attachment`; do not label it an extracted interactive test. Do not guess hidden endpoints or scrape content the account cannot access.

## Error handling and completeness

- HTTP 401/403 is an authorization failure. Do not retry without credentials.
- Retry only transient network errors, 429, and 5xx with bounded backoff.
- Track pagination and folder traversal explicitly; detect repeated IDs to avoid loops.
- Deduplicate by stable item ID, not by title.
- Validate URL syntax. Do not make unauthenticated HEAD/GET requests to test protected URLs.
- Produce a manifest plus a summary of discovered/exported/missing/unauthorized/unsupported/failed counts.
- Never print access tokens, authorization headers, signed URLs, or PDF encryption keys in logs.

## Required fixtures before platform integration

Before enabling a platform adapter, add redacted JSON fixtures captured from an account that is entitled to the relevant course:

1. entitled course list
2. one folder/list response with at least one video and one PDF
3. one video detail response
4. one test-series list/detail response (or evidence that the API only returns a PDF attachment)
5. pagination response, if pagination is used

Remove bearer tokens, cookies, user IDs, phone numbers, signed URL query secrets, and other personal data before committing fixtures. Keep URL host/path structure only if it does not grant access; otherwise replace the host/path with a stable placeholder and retain the field structure.

## Acceptance criteria

A fixture-driven test suite must prove that:

- video URLs are copied exactly from source fields
- PDF URLs are copied exactly from source fields
- test attachments are not misreported as interactive tests
- missing URLs remain missing rather than being guessed
- duplicate folders/items do not create duplicate records
- 401/403 does not trigger an unauthenticated retry
- pagination and nested folders are fully traversed
- export counts reconcile with the manifest


## TXT manifest intake

`exporters/txt_input.py` parses user-supplied TXT manifests independently of provider adapters. It accepts either a raw HTTP(S) URL per line or `Title: URL`, ignores blank/comment/non-URL lines, rejects non-HTTP schemes and URLs containing embedded credentials, deduplicates exact URLs, and enforces 2 MiB / 10,000-line limits. It preserves the supplied URL including its query string; it does not fetch or rewrite it.

The parser is a preprocessing stage only. A provider adapter must still establish that a supplied URL/resource belongs to the authenticated user's authorized account before any export or Telegram upload. Do not use the parser as an entitlement check.
