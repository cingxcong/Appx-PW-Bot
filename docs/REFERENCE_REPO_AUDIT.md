# Reference repository audit

This note records the useful architecture patterns from the three supplied repositories. It does not copy their implementation or credentials.

## Bot 1: warener4455/ii7755

- The repository's `requirements.txt` is accessible, but the expected root `README.md`, `main.py`, and `bot.py` paths were not present at the time of review.
- The supplied description says this bot discovers URLs by organization code without a user login.
- We will not reproduce discovery or extraction of unlicensed, non-public, or access-restricted material. Organization-code discovery alone does not establish a user's entitlement.

## Bot 2: capoduc/ITsGOLU_UPLOADER_FAST-V2

- The root application is `main.py`; its `/drm` flow asks the user to upload a TXT file and parses lines containing URLs.
- The code combines URL extraction, provider-specific API calls, media processing, and Telegram upload in a large handler. Our implementation should keep those concerns separate.
- The inspected source contains hardcoded JWT-like values and DRM-oriented functionality. Do not copy those values or the DRM/bypass paths. If any real token was committed to a public repository, its owner should revoke/rotate it.
- Reusable idea: TXT upload and Telegram upload as independent stages, with validation and per-item status reporting.

## Bot 3: cingxcong/Webtokenboth

- The root `main.py` is a Flask application that requests a Classplus email OTP, verifies the OTP, and obtains an account token through Classplus API endpoints.
- It supports manual OTP verification and an automated email-reading path using IMAP credentials supplied through environment variables.
- The code reads configuration from environment variables, which is preferable to embedding credentials in source.
- The private-mode gate defaults to disabled unless `PRIVATE_MODE` is enabled. A deployment must explicitly enable a private gate and use strong secrets; do not expose a token-generation service publicly.
- This is an authentication/token-acquisition workflow, not proof that every course or media item is licensed for export. Tokens must belong to the user requesting the export and must never be logged or shared.

## Target architecture for Appx-PW-Bot

1. **Authentication** — use an explicit user-owned account session/token. Keep token acquisition separate from content extraction. Store secrets outside the repository and redact them from logs.
2. **TXT intake** — accept a bounded-size UTF-8 TXT file, parse one URL or identifier per line, reject malformed entries, and deduplicate inputs.
3. **Provider adapters** — make authenticated API requests only for resources visible to that account. Treat 401/403 as authorization failures; do not retry anonymously or remove authorization headers.
4. **Manifest normalization** — preserve URLs returned by the provider exactly; never synthesize media URLs from thumbnails, IDs, or guessed path patterns.
5. **Telegram delivery** — upload only files/streams the authorized API actually returns and report success/failure per item.
6. **Tests** — use redacted fixtures from the user's own entitled account. Tests must cover videos, PDFs, missing URLs, pagination, authorization failures, and interactive tests separately from PDF attachments.

## Remaining evidence needed

The reference repositories do not establish the exact current response schemas for this user's Classplus/Appx/PW account. A redacted `content.json` response containing one video and one PDF is still required before implementing provider-specific field mappings. Never include cookies, authorization headers, OTPs, tokens, encryption keys, or signed URL secrets in the fixture.
