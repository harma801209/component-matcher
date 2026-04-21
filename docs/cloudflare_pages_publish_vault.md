# Cloudflare Pages Publish Vault

This project uses a local token vault so Cloudflare Pages deploys can run without opening the Cloudflare dashboard every time.

## Vault files

- `cloudflare_account_api_token.txt`

## Rules

1. Do not commit the token file.
2. `deploy_cloudflare_pages_proxy.ps1` reads the token vault automatically.
3. The deploy script also resolves the Cloudflare account ID from local cache or a fallback constant.
4. If the token is missing or invalid, the deploy should fail fast instead of prompting for an interactive login.

## Standard flow

1. Make public-facing changes.
2. Run `publish_public.ps1`.
3. If proxy files changed, the Cloudflare Pages shell deploy should run non-interactively with the token vault.

## Recovery

If Cloudflare rotates or revokes the token, create a new account token, save it to the same vault file, and rerun the publish script.
