# External Access Guide

There are two ways to expose this Streamlit app without renting a cloud server:

1. Quick tunnel for temporary sharing
2. Named tunnel for a fixed domain

Both options still require one local computer to stay on and connected to the internet.

## 1. Quick tunnel

This is the fastest way to get a public URL, but the URL changes every time you restart it.

The `start_public.ps1` script now does two convenience things:

- Reuses the existing local Streamlit app if `8501` is already running
- Downloads the Windows `cloudflared` binary from the official Cloudflare release if it is not already installed

Install `cloudflared` on Windows:

```powershell
winget install --id Cloudflare.cloudflared
```

Start the app with:

```powershell
.\start_public.ps1
```

Or double-click `start_public.bat`.

Official docs:

- [Downloads](https://developers.cloudflare.com/tunnel/downloads/)
- [Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/do-more-with-tunnels/trycloudflare/)

## 2. Fixed domain

This is the recommended mode if you want a stable URL such as `bom.example.com`.

Cloudflare's official flow is:

1. Create a named tunnel in Cloudflare Zero Trust.
2. Add a public hostname route for the tunnel, such as `bom.example.com`.
3. Install `cloudflared` on the local machine.
4. Start the local app and keep the tunnel online.

Cloudflare docs:

- [Create a Cloudflare Tunnel](https://developers.cloudflare.com/learning-paths/clientless-access/connect-private-applications/create-tunnel/)
- [Published applications](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/routing-to-tunnel/)
- [Tunnel run parameters](https://developers.cloudflare.com/tunnel/advanced/run-parameters/)
- [Tunnel tokens](https://developers.cloudflare.com/tunnel/advanced/tunnel-tokens/)

### What I added in this project

- `start_streamlit.ps1`
- `setup_fixed_domain.ps1`
- `setup_fixed_domain.bat`

### How to use the fixed-domain setup

1. In Cloudflare Zero Trust, create a named tunnel and add the public hostname you want.
2. Copy the tunnel token from Cloudflare.
3. On Windows, install `cloudflared` if needed:

```powershell
winget install --id Cloudflare.cloudflared
```

4. Run this script and paste your token. It will prompt for elevation if needed:

```powershell
.\setup_fixed_domain.ps1 -TunnelToken "PASTE_YOUR_TUNNEL_TOKEN_HERE"
```

Or double-click `setup_fixed_domain.bat` and follow the prompt.

What the setup does:

- Creates an auto-start entry for Streamlit in your Windows Startup folder
- Installs the Cloudflare Tunnel service using the token you provided
- Leaves the fixed hostname managed by Cloudflare

### URLs

- Local URL: `http://127.0.0.1:8501`
- Fixed public URL: the hostname you created in Cloudflare, for example `bom.example.com`

### Notes

- The fixed URL does not change on restart
- The local PC must remain powered on
- If you later change the hostname, you only need to update the Cloudflare dashboard route

## 3. Free fixed URL on Streamlit Community Cloud

If you want a stable free public link without keeping this PC online, Streamlit Community Cloud is the best fit.

What you need:

- Push this folder to a GitHub repository
- Use `streamlit_app.py` as the entry file
- Keep `streamlit_cloud_bundle.zip` in the repo and track it with Git LFS so the app can restore `components.db` and the search caches on startup
- Do not commit the unpacked `components.db` / `cache/*` files to the cloud repo if you are creating a clean deployment repo; the zip bundle is what matters at runtime
- If you want the cloud deployment to be protected too, set `app_access_code` in Streamlit Cloud secrets; the same access-code gate will work there

What the app now does for Cloud:

- Uses relative paths instead of Windows-only absolute paths
- Automatically extracts `streamlit_cloud_bundle.zip` if the local database files are missing
- Avoids unnecessary startup rebuilds when the database already exists
- Remains portable without Windows-only absolute paths

Main caveat:

- This app is data-heavy, so the cloud bundle is large. The good news is that it is still much smaller than the raw database files and is much more suitable for GitHub / Cloud than the unpacked `.db` files.

## 4. One-click local launchers in this folder

Two double-click launchers are now included in the `DATA` folder:

- `start_lan.cmd`
  - Starts the app on the machine's LAN IP when available, otherwise falls back to `0.0.0.0:8501`
  - Best for devices on the same local network
  - The host machine opens the local browser URL automatically
- `start_public_fixed.cmd`
  - Starts the app on `127.0.0.1:8501`
  - Starts a Cloudflare Tunnel using a fixed tunnel token
  - Best for a stable public URL after one-time Cloudflare tunnel setup

For the fixed public launcher:

- Place your Cloudflare tunnel token in `public_tunnel_token.txt`
- `start_public_fixed.ps1` will generate `public_access_code.txt` the first time it runs, or you can create it yourself from `public_access_code.txt.example`
- Optionally place the public URL in `public_fixed_url.txt` so the script can open it automatically
- The tunnel itself must already be configured in Cloudflare to point at `http://127.0.0.1:8501`
- The example files in this folder show the expected format

Security notes:

- The app now supports an access-code gate when `APP_ACCESS_CODE` is set by the launcher or by Streamlit Cloud secrets
- Search input and BOM upload now have size limits so a single request cannot flood the app with very large payloads
- For a stricter public deployment, you can also add Cloudflare Access in front of the tunnel; that keeps the fixed URL but adds identity-based protection

## 5. One-click sync for both LAN and public releases

If you change rules, database content, or public-facing text locally and want the LAN version and the Streamlit public version to stay aligned, use:

- `sync_local_and_public.cmd`

Or:

```powershell
.\sync_local_and_public.ps1
```

What it does:

1. Rebuilds `streamlit_cloud_bundle.zip` from the current local database and caches
2. Syntax-checks the main app and sync scripts
3. Stages only the publishable release files
4. Creates a git commit
5. Pushes through GitHub SSH on port `443`
6. Lets Streamlit Community Cloud auto-deploy the updated public app

Useful options:

```powershell
.\sync_local_and_public.ps1 -CommitMessage "更新 MLCC 规则"
.\sync_local_and_public.ps1 -SkipBundleRebuild
.\sync_local_and_public.ps1 -SkipPush
```

This is the recommended path if you do not want to repeat the same publish work twice after every local change.
