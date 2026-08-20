# Streamlit Deploy Auth Vault

This project keeps deployment login state in a local vault so future releases do not need a fresh manual sign-in every time.

## Vault contents

- `streamlit_cloud_profile/`
- `streamlit_cloud_state.json`

## Rules

1. Do not commit either file to git.
2. `auto_streamlit_deploy.py` always prefers the persistent profile on disk.
3. After a successful deploy, the script refreshes the JSON snapshot as a backup.
4. If the browser ever asks for Google or GitHub verification again, treat that as a stale vault and reseed it once.
5. After the vault is reseeded, future deploys should be hands-off again.

## Standard flow

1. Make code or data changes.
2. Run `publish_public.ps1` for the normal sync and push.
3. If the live Streamlit app needs a browser nudge, run `publish_public.ps1 -TriggerStreamlitDeploy`.
4. If the auth vault is valid, the browser deploy should proceed without asking for the user again.

## Recovery

If the profile folder is ever lost, restore from the latest JSON snapshot or reseed the vault once, then keep reusing the same profile directory.
