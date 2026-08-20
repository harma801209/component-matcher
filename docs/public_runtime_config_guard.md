# Public Runtime Config Guard

This file records the rule for public runtime session/config changes.

Protected file:
- `.streamlit/config.toml`

Treat as a public-release change whenever you touch any of these settings:
- `enableXsrfProtection`
- `enableCORS`
- `cookieSecret`
- `browser.serverAddress`
- `browser.serverPort`

Required process:
1. Make the change only for an explicit public-site fix.
2. Publish with `-AllowPublicRuntimeChange` or `--allow-public-runtime-change`.
3. Recheck the live public site in a real browser after deployment.

Public embed note:
- If the live app returns `403 Forbidden - CSRF token invalid` on `api/v1/app/event/open`, set the public config to `enableXsrfProtection = false` and `enableCORS = false` before republishing.
