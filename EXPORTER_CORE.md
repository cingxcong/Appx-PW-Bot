# Exporter core

This is the first executable component of the authorized exporter rebuild.

## What it does

- Normalizes one supplied API response page into stable JSON manifest records.
- Preserves explicit HTTP(S) URLs exactly, including signed query parameters.
- Recognizes common video, PDF, image, folder, and test material labels.
- Distinguishes a TEST item's PDF attachment from an interactive test.
- Preserves question fields only when the API response actually includes them.
- Deduplicates repeated records and reports status counts.

## What it deliberately does not do

- Make provider API calls or assume undocumented endpoint paths.
- Construct HLS/DASH URLs from thumbnail URLs, item IDs, or file paths.
- Decrypt opaque fields or resolve DRM-protected streams.
- Retry without authentication.
- Claim a test is interactive when the response only contains a PDF attachment.

## Run tests

From the repository root:

```bash
python -m unittest discover -s tests -v
```

## Integration status

This module is a tested normalizer, not yet a complete provider adapter. Classplus and Appx folder traversal, pagination, entitlement checks, and signed-URL behavior still need redacted response fixtures from an account authorized for the selected course. Until then, the existing legacy bot routes remain disabled on the feature branch.
