# Always-On Hosting

Streamlit Community Cloud is convenient, but it sleeps after inactivity.
That is fine for a demo, but it is not a strict 24/7 backend.

For a true always-on deployment, use a container host with a minimum instance count of 1.
The current app is already prepared for that style of deployment:

- `Dockerfile` builds a Streamlit container.
- `streamlit_cloud_bundle.zip` is bundled in the image and can restore the data files on startup.
- `cloudflare-pages-proxy/dist/_worker.js` can keep serving the public front door once the backend origin is changed.

Recommended options:

- Google Cloud Run with `min instances = 1`
- A small VPS running Docker + Streamlit

Free backups are still fine:

- GitHub repo
- zipped archive in a storage bucket

But the actual always-on runtime should not be a free sleeping tier.
