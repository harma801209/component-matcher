const ORIGIN_BASE = "https://fruition-componentmatche.streamlit.app";
const SHARE_BASE = "https://share.streamlit.io";
const STREAMLIT_APP_SUBDOMAIN = "fruition-componentmatche";
const STREAMLIT_APP_ID = "5addba1a-a463-41bf-b91e-bb794d7ab37e";
const EMBED_OPTION_VALUES = ["hide_loading_screen"];
const PROD_APP_HOSTS_LITERAL = '["*.streamlit.app","*.streamlitapp.com","*.streamlit.run"]';

const STATIC_PREFIXES = [
  "/-/build/",
  "/_stcore/",
  "/static/",
  "/favicon",
  "/manifest",
  "/robots.txt",
  "/service-worker",
];

export default {
  async fetch(request) {
    return proxyRequest(request);
  },
};

async function proxyRequest(request) {
  const incomingUrl = new URL(request.url);

  if (incomingUrl.pathname === "/_stcore/health" || incomingUrl.pathname === "/_stcore/script-health-check") {
    return buildHealthResponse(request);
  }

  if (incomingUrl.pathname === "/service-worker.js" || incomingUrl.pathname === "/service-worker") {
    return buildServiceWorkerResetResponse(request);
  }

  if (incomingUrl.pathname === "/_stcore/host-config") {
    return buildHostConfigResponse(request);
  }

  if (incomingUrl.pathname === "/api/v2/app/disambiguate") {
    return proxyShareJson(`${SHARE_BASE}/api/v2/apps/disambiguate?subdomain=${STREAMLIT_APP_SUBDOMAIN}`);
  }

  if (incomingUrl.pathname === "/api/v2/app/context") {
    return proxyShareJson(`${SHARE_BASE}/api/v2/apps/${STREAMLIT_APP_ID}/context`);
  }

  if (incomingUrl.pathname === "/api/v2/app/status") {
    return proxyShareJson(`${SHARE_BASE}/api/v2/apps/${STREAMLIT_APP_ID}/status`);
  }

  if (incomingUrl.pathname === "/api/v1/app/event/open") {
    return buildOpenEventResponse(request);
  }

  if (incomingUrl.pathname === "/api/v1/app/event/focus") {
    return buildFocusEventResponse(request);
  }

  if (incomingUrl.pathname === "/api/v1/app/event" && incomingUrl.searchParams.get("type") === "last-app-views") {
    return buildLastAppViewsResponse(request);
  }

  const upstreamUrl = buildUpstreamUrl(incomingUrl, request);
  const requestHeaders = buildUpstreamHeaders(request.headers);

  requestHeaders.set("x-forwarded-host", incomingUrl.host);
  requestHeaders.set("x-forwarded-proto", incomingUrl.protocol.replace(":", ""));
  requestHeaders.set("x-original-host", incomingUrl.host);

  const requestInit = {
    method: request.method,
    headers: requestHeaders,
    redirect: "manual",
  };

  if (!["GET", "HEAD"].includes(request.method.toUpperCase())) {
    requestInit.body = request.body;
  }

  const upstreamResponse = await fetch(new Request(upstreamUrl, requestInit));
  return buildClientResponse(upstreamResponse, incomingUrl);
}

function buildUpstreamUrl(incomingUrl, request) {
  const upstreamUrl = new URL(`${incomingUrl.pathname}${incomingUrl.search}`, ORIGIN_BASE);
  if (shouldUseEmbedMode(incomingUrl, request)) {
    upstreamUrl.searchParams.set("embed", "true");
    for (const value of EMBED_OPTION_VALUES) {
      const existingValues = upstreamUrl.searchParams.getAll("embed_options");
      if (!existingValues.includes(value)) {
        upstreamUrl.searchParams.append("embed_options", value);
      }
    }
  }
  return upstreamUrl.toString();
}

function shouldUseEmbedMode(incomingUrl, request) {
  if (STATIC_PREFIXES.some((prefix) => incomingUrl.pathname.startsWith(prefix))) {
    return false;
  }
  return true;
}

async function buildClientResponse(upstreamResponse, incomingUrl) {
  const responseHeaders = new Headers(upstreamResponse.headers);
  responseHeaders.set("cache-control", "no-store");

  const location = responseHeaders.get("location");
  if (location) {
    responseHeaders.set("location", rewriteLocation(location, incomingUrl));
  }

  if (isHtmlResponse(upstreamResponse)) {
    const html = await upstreamResponse.text();
    const rewrittenHtml = rewriteHtml(html, incomingUrl);
    return buildTextResponse(rewrittenHtml, upstreamResponse, responseHeaders);
  }

  if (shouldRewriteJavaScript(incomingUrl, upstreamResponse)) {
    const script = await upstreamResponse.text();
    const rewrittenScript = rewriteJavaScript(script, incomingUrl);
    return buildTextResponse(rewrittenScript, upstreamResponse, responseHeaders);
  }

  responseHeaders.delete("content-length");
  return new Response(upstreamResponse.body, {
    status: upstreamResponse.status,
    statusText: upstreamResponse.statusText,
    headers: responseHeaders,
  });
}

function buildTextResponse(text, upstreamResponse, responseHeaders) {
  const encoded = new TextEncoder().encode(text);
  responseHeaders.delete("accept-ranges");
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("transfer-encoding");
  responseHeaders.set("content-length", String(encoded.byteLength));
  return new Response(text, {
    status: upstreamResponse.status,
    statusText: upstreamResponse.statusText,
    headers: responseHeaders,
  });
}

function buildHealthResponse(request) {
  const headers = new Headers({
    "cache-control": "no-cache",
    "content-type": "text/plain; charset=utf-8",
  });

  if (request.method.toUpperCase() === "HEAD") {
    return new Response(null, {
      status: 200,
      headers,
    });
  }

  return new Response("ok", {
    status: 200,
    headers,
  });
}

function buildHostConfigResponse(request) {
  const headers = new Headers({
    "cache-control": "no-cache",
    "content-type": "application/json; charset=utf-8",
  });

  const payload = {
    allowedOrigins: [
      "https://devel.streamlit.test",
      "https://*.streamlit.apptest",
      "https://*.streamlitapp.test",
      "https://*.streamlitapp.com",
      "https://share.streamlit.io",
      "https://share-demo.streamlit.io",
      "https://share-head.streamlit.io",
      "https://share-staging.streamlit.io",
      "https://*.demo.streamlit.run",
      "https://*.head.streamlit.run",
      "https://*.staging.streamlit.run",
      "https://*.streamlit.run",
      "https://*.demo.streamlit.app",
      "https://*.head.streamlit.app",
      "https://*.staging.streamlit.app",
      "https://*.streamlit.app",
    ],
    useExternalAuthToken: false,
    enableCustomParentMessages: false,
    enforceDownloadInNewTab: false,
    metricsUrl: "",
    blockErrorDialogs: false,
    resourceCrossOriginMode: null,
  };

  if (request.method.toUpperCase() === "HEAD") {
    return new Response(null, {
      status: 200,
      headers,
    });
  }

  return new Response(JSON.stringify(payload), {
    status: 200,
    headers,
  });
}

function buildServiceWorkerResetResponse(request) {
  const headers = new Headers({
    "cache-control": "no-store",
    "content-type": "application/javascript; charset=utf-8",
  });
  const script = `self.addEventListener("install", (event) => { self.skipWaiting(); });
self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map((key) => caches.delete(key)));
    await self.registration.unregister();
    await self.clients.claim();
    const clients = await self.clients.matchAll({ type: "window" });
    for (const client of clients) {
      client.navigate(client.url);
    }
  })());
});
self.addEventListener("fetch", () => {});`;

  if (request.method.toUpperCase() === "HEAD") {
    return new Response(null, {
      status: 200,
      headers,
    });
  }

  return new Response(script, {
    status: 200,
    headers,
  });
}

async function buildOpenEventResponse(request) {
  const headers = buildJsonHeaders();
  if (request.method.toUpperCase() === "HEAD") {
    return new Response(null, {
      status: 200,
      headers,
    });
  }

  const now = new Date().toISOString();
  const payload = {
    sessionId: crypto.randomUUID(),
    createdAt: now,
  };

  return new Response(JSON.stringify(payload), {
    status: 200,
    headers,
  });
}

async function buildFocusEventResponse(request) {
  const headers = buildJsonHeaders();
  if (request.method.toUpperCase() === "HEAD") {
    return new Response(null, {
      status: 200,
      headers,
    });
  }

  let payload = {};
  try {
    payload = await request.json();
  } catch {
    payload = {};
  }

  const responsePayload = {
    sessionId: payload.sessionId || crypto.randomUUID(),
    createdAt: payload.createdAt || new Date().toISOString(),
  };

  return new Response(JSON.stringify(responsePayload), {
    status: 200,
    headers,
  });
}

function buildLastAppViewsResponse(request) {
  const headers = buildJsonHeaders();
  if (request.method.toUpperCase() === "HEAD") {
    return new Response(null, {
      status: 200,
      headers,
    });
  }

  const payload = {
    views: [],
    count: 0,
  };

  return new Response(JSON.stringify(payload), {
    status: 200,
    headers,
  });
}

async function proxyShareJson(url) {
  const upstreamResponse = await fetch(url, {
    method: "GET",
    headers: {
      accept: "application/json",
    },
  });

  const responseHeaders = new Headers(upstreamResponse.headers);
  responseHeaders.set("cache-control", "no-store");
  const payload = await upstreamResponse.text();
  return buildTextResponse(payload, upstreamResponse, responseHeaders);
}

function buildJsonHeaders() {
  return new Headers({
    "cache-control": "no-store",
    "content-type": "application/json; charset=utf-8",
  });
}

function buildUpstreamHeaders(sourceHeaders) {
  const blocked = new Set([
    "connection",
    "content-length",
    "host",
    "transfer-encoding",
  ]);

  const headers = new Headers();
  for (const [key, value] of sourceHeaders.entries()) {
    const lowerKey = key.toLowerCase();
    if (blocked.has(lowerKey) || lowerKey.startsWith("cf-")) {
      continue;
    }
    if (lowerKey === "accept-encoding") {
      continue;
    }
    headers.set(key, value);
  }
  return headers;
}

function rewriteLocation(location, incomingUrl) {
  try {
    const resolved = new URL(location, ORIGIN_BASE);
    const origin = new URL(ORIGIN_BASE);
    if (resolved.origin === origin.origin) {
      resolved.protocol = incomingUrl.protocol;
      resolved.host = incomingUrl.host;
      return resolved.toString();
    }
    return location;
  } catch {
    return location;
  }
}

function rewriteHtml(html, incomingUrl) {
  const incomingOrigin = `${incomingUrl.protocol}//${incomingUrl.host}`;
  const originHost = new URL(ORIGIN_BASE).host;
  let rewritten = html.replaceAll(ORIGIN_BASE, incomingOrigin);

  rewritten = rewritten.replaceAll(`src="//${originHost}/`, `src="${ORIGIN_BASE}/`);
  rewritten = rewritten.replace(/<script src="https:\/\/www\.streamlitstatus\.com\/embed\/script\.js"><\/script>/gi, "");
  rewritten = rewritten.replace(/<iframe[^>]+statuspage\.io\/embed\/frame[^>]*><\/iframe>/gi, "");

  const customChrome = `
<style>
  html, body, #root {
    height: 100%;
    margin: 0;
    background: #ffffff;
  }

  [title="streamlitApp"] {
    position: fixed !important;
    inset: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    border: 0 !important;
    display: block !important;
    visibility: visible !important;
    background: #ffffff !important;
  }

  a[href="https://streamlit.io/cloud"],
  a[href^="https://share.streamlit.io/user/"],
  img[data-testid="appCreatorAvatar"],
  iframe[src*="statuspage.io"] {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
  }
</style>
<script>
  window.addEventListener("DOMContentLoaded", () => {
    const purgeLegacyCaches = async () => {
      if (!("serviceWorker" in navigator) || !("caches" in window)) {
        return;
      }
      try {
        const registrations = await navigator.serviceWorker.getRegistrations();
        const cacheKeys = await caches.keys();
        const hadLegacyState = registrations.length > 0 || cacheKeys.length > 0;
        await Promise.all(registrations.map((registration) => registration.unregister()));
        await Promise.all(cacheKeys.map((cacheKey) => caches.delete(cacheKey)));
        if (hadLegacyState && !window.sessionStorage.getItem("fruition-proxy-cache-reset")) {
          window.sessionStorage.setItem("fruition-proxy-cache-reset", "1");
          window.location.reload();
        }
      } catch (error) {
        console.warn("legacy cache purge failed", error);
      }
    };

    const hideChrome = () => {
      document.querySelectorAll('a[href="https://streamlit.io/cloud"], a[href^="https://share.streamlit.io/user/"], img[data-testid="appCreatorAvatar"], iframe[src*="statuspage.io"]').forEach((node) => {
        const container = node.closest("a, div, iframe");
        if (container) {
          container.style.display = "none";
        }
        node.style.display = "none";
      });
    };

    const normalizeAppFrame = () => {
      const iframe = document.querySelector('iframe[title="streamlitApp"]');
      if (!iframe) {
        return;
      }

      const iframeUrl = new URL(iframe.getAttribute("src") || iframe.src, "${ORIGIN_BASE}/");
      iframeUrl.protocol = "https:";
      iframeUrl.searchParams.set("embed", "true");
      if (!iframeUrl.searchParams.getAll("embed_options").includes("hide_loading_screen")) {
        iframeUrl.searchParams.append("embed_options", "hide_loading_screen");
      }

      if (iframe.src !== iframeUrl.toString()) {
        iframe.src = iframeUrl.toString();
      }

      iframe.removeAttribute("hidden");
      iframe.hidden = false;
      iframe.style.display = "block";
      iframe.style.visibility = "visible";
      iframe.addEventListener("load", () => {
        const spinner = document.querySelector('[title="appLoadingSpinner"]');
        if (spinner) {
          spinner.style.display = "none";
        }
      }, { once: true });
    };

    purgeLegacyCaches().finally(() => {
      hideChrome();
      normalizeAppFrame();
    });
    const intervalId = window.setInterval(() => {
      hideChrome();
      normalizeAppFrame();
    }, 500);
    window.setTimeout(() => window.clearInterval(intervalId), 10000);
  });
</script>`;

  rewritten = rewritten.replace("</head>", `${customChrome}\n</head>`);
  return rewritten;
}

function shouldRewriteJavaScript(incomingUrl, response) {
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("javascript")) {
    return false;
  }

  return /\/-\/build\/assets\/.+\.js$/i.test(incomingUrl.pathname);
}

function rewriteJavaScript(script, incomingUrl) {
  const hostLiteral = JSON.stringify(incomingUrl.hostname);
  let rewritten = script;

  if (rewritten.includes(PROD_APP_HOSTS_LITERAL) && !rewritten.includes(hostLiteral)) {
    const injectedHosts = `${PROD_APP_HOSTS_LITERAL.slice(0, -1)},${hostLiteral}]`;
    rewritten = rewritten.replace(PROD_APP_HOSTS_LITERAL, injectedHosts);
  }

  if (incomingUrl.hostname === "127.0.0.1" && !rewritten.includes('"localhost"')) {
    rewritten = rewritten.replace('"*.localhost"]', '"*.localhost","localhost"]');
  }

  return rewritten;
}

function isHtmlResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  return contentType.includes("text/html");
}
