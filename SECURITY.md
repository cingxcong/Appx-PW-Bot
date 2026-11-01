# Security and authorized-export policy

## Immediate credential action

The previous `config.py` committed live-looking Telegram credentials as source defaults. Treat any credential that was ever committed to a public repository as compromised, even after replacing the file.

1. Revoke and regenerate the Telegram bot token with BotFather.
2. Review/regenerate the Telegram API credentials if they were exposed.
3. Set the replacement values as deployment environment variables.
4. Review repository history and rotate any other exposed tokens. Rewriting history does not replace rotation.
5. Check deployment logs and hosting environment variables for stale values.

## Export scope

This project should export course metadata and URLs only for content that the authenticated account is entitled to access.

- Do not enumerate preview-only or unpurchased course content as if it were owned content.
- Do not retry failed authenticated requests without authentication.
- Do not derive video manifest URLs from thumbnail naming patterns.
- Do not decrypt, strip, defeat, or otherwise bypass DRM or access controls.
- Preserve the exact API-returned URL and its content type; record whether a URL is direct, signed, or expires when the API explicitly supplies that information.
- Treat HTTP 401/403 as an authorization failure and stop that item or export.
- Test-series data may be exported only when the authorized API response exposes it to the account. Do not guess hidden endpoints or fabricate question/answer data.

## Validation expectations

Before an export is marked complete, report discovered, exported, skipped, and failed counts separately. Validate URL syntax and, where permitted, perform a lightweight authenticated metadata request. Do not download media as part of metadata discovery. Keep signed URLs private because they may grant temporary access.
