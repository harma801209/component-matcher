const ORIGIN_BASE = "https://fruition-componentmatche.streamlit.app";
const SHARE_BASE = "https://share.streamlit.io";
const STREAMLIT_APP_SUBDOMAIN = "fruition-componentmatche";
const STREAMLIT_APP_ID = "5addba1a-a463-41bf-b91e-bb794d7ab37e";
const EMBED_OPTION_VALUES = ["hide_loading_screen"];
const APP_CACHE_BUSTER = "20260421-footer-1";
const PROD_APP_HOSTS_LITERAL = '["*.streamlit.app","*.streamlitapp.com","*.streamlit.run"]';
const FAVICON_DATA_URL = "data:image/png;base64,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";

const STATIC_PREFIXES = [
  "/-/build/",
  "/_stcore/",
  "/static/",
  "/favicon",
  "/manifest",
  "/robots.txt",
  "/service-worker",
];
const APP_RUNTIME_PREFIX = "/~/+";
const ROOT_PATHS = new Set(["/", APP_RUNTIME_PREFIX]);

export default {
  async fetch(request) {
    return proxyRequest(request);
  },
};

async function proxyRequest(request) {
  const incomingUrl = new URL(request.url);
  const dispatchPath = normalizeDispatchPath(incomingUrl.pathname);

  if (shouldServeEmbedShell(request, incomingUrl, dispatchPath)) {
    return buildEmbedShellResponse(request, incomingUrl);
  }

  if (shouldBootstrapSession(request, incomingUrl, dispatchPath)) {
    return bootstrapStreamlitSession(incomingUrl);
  }

  if (dispatchPath === "/_stcore/health" || dispatchPath === "/_stcore/script-health-check") {
    return buildHealthResponse(request);
  }

  if (dispatchPath === "/favicon.png" || dispatchPath === "/favicon.ico") {
    return buildFaviconResponse(request);
  }

  if (dispatchPath === "/service-worker.js" || dispatchPath === "/service-worker") {
    return buildServiceWorkerResetResponse(request);
  }

  if (dispatchPath === "/_stcore/host-config") {
    return buildHostConfigResponse(request);
  }

  if (dispatchPath === "/api/v2/app/disambiguate") {
    return proxyShareJson(
      `${SHARE_BASE}/api/v2/apps/disambiguate?subdomain=${STREAMLIT_APP_SUBDOMAIN}`,
      incomingUrl,
      "disambiguate",
    );
  }

  if (dispatchPath === "/api/v2/app/context") {
    return proxyShareJson(
      `${SHARE_BASE}/api/v2/apps/${STREAMLIT_APP_ID}/context`,
      incomingUrl,
      "context",
    );
  }

  if (dispatchPath === "/api/v2/app/status") {
    return proxyShareJson(
      `${SHARE_BASE}/api/v2/apps/${STREAMLIT_APP_ID}/status`,
      incomingUrl,
      "status",
    );
  }

  if (dispatchPath === "/api/v1/app/event/open") {
    return buildOpenEventResponse(request);
  }

  if (dispatchPath === "/api/v1/app/event/focus") {
    return buildFocusEventResponse(request);
  }

  if (dispatchPath === "/api/v1/app/event" && incomingUrl.searchParams.get("type") === "last-app-views") {
    return buildLastAppViewsResponse(request);
  }

  const upstreamUrl = buildUpstreamUrl(incomingUrl, request);
  if (isWebSocketUpgrade(request)) {
    return proxyWebSocketRequest(request, upstreamUrl, incomingUrl);
  }

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

function shouldServeEmbedShell(request, incomingUrl, dispatchPath) {
  if (!["GET", "HEAD"].includes(request.method.toUpperCase())) {
    return false;
  }
  if (incomingUrl.pathname !== "/") {
    return false;
  }
  if (dispatchPath !== "/") {
    return false;
  }
  return acceptsHtml(request.headers);
}

function buildEmbedShellResponse(request, incomingUrl) {
  const headers = new Headers({
    "cache-control": "no-store",
    "content-type": "text/html; charset=utf-8",
  });

  if (request.method.toUpperCase() === "HEAD") {
    return new Response(null, {
      status: 200,
      headers,
    });
  }

  const appUrl = `${ORIGIN_BASE}/~/+/?embed=true&embed_options=hide_loading_screen&v=${APP_CACHE_BUSTER}`;
  const html = `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <meta name="theme-color" content="#ffffff" />
    <title>富临通元器件匹配系统</title>
    <link rel="icon" type="image/png" sizes="128x128" href="/favicon.png?v=20260404a" />
    <link rel="shortcut icon" type="image/png" href="/favicon.png?v=20260404a" />
    <link rel="apple-touch-icon" href="/favicon.png?v=20260404a" />
    <style>
      html, body {
        margin: 0;
        width: 100%;
        height: 100%;
        background: #ffffff;
        overflow: hidden;
      }
      body {
        display: flex;
        flex-direction: column;
      }
      .app-frame {
        flex: 1 1 auto;
        min-height: 0;
        width: 100%;
        border: 0;
        display: block;
        background: #ffffff;
      }
      .proxy-footer {
        position: fixed;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 9999;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 0.5rem;
        padding: 8px 12px 12px;
        border-top: 1px solid rgba(226, 232, 240, 0.9);
        background: rgba(255, 255, 255, 0.98);
        color: #5f6b7a;
        font-size: 13px;
        line-height: 1.4;
        box-sizing: border-box;
        text-align: center;
        white-space: normal;
        box-shadow: 0 -4px 14px rgba(148, 163, 184, 0.16);
      }
      .proxy-footer a {
        color: #1565c0;
        text-decoration: none;
      }
    </style>
  </head>
  <body>
    <iframe
      class="app-frame"
      src="${appUrl}"
      title="富临通元器件匹配系统"
      allow="clipboard-read; clipboard-write"
      referrerpolicy="strict-origin-when-cross-origin"
    ></iframe>
    <div class="proxy-footer">
      网站管理员：Terry Wu
      系统问题请与管理员联系：
      <a href="mailto:terry@fruition-sz.com">terry@fruition-sz.com</a>
    </div>
  </body>
</html>`;

  return new Response(html, {
    status: 200,
    headers,
  });
}

async function proxyWebSocketRequest(request, upstreamUrl, incomingUrl) {
  try {
    const websocketHeaders = buildUpstreamHeaders(request.headers, { allowConnectionHeader: true });
    websocketHeaders.set("upgrade", "websocket");
    websocketHeaders.set("x-forwarded-host", incomingUrl.host);
    websocketHeaders.set("x-forwarded-proto", incomingUrl.protocol.replace(":", ""));
    websocketHeaders.set("x-original-host", incomingUrl.host);

    const upstreamResponse = await fetch(upstreamUrl, {
      method: request.method,
      headers: websocketHeaders,
    });

    if (!upstreamResponse.webSocket) {
      const responseHeaders = new Headers(upstreamResponse.headers);
      responseHeaders.set("cache-control", "no-store");
      return new Response(upstreamResponse.body, {
        status: upstreamResponse.status,
        statusText: upstreamResponse.statusText,
        headers: responseHeaders,
      });
    }

    // Preserve the upstream websocket handshake as-is. Rebuilding the 101
    // response with copied headers has been unstable on Pages and can throw
    // a Worker 1101 during the websocket upgrade path.
    return upstreamResponse;
  } catch (error) {
    console.error("websocket proxy failed", error);
    return new Response("WebSocket proxy failed", {
      status: 502,
      headers: {
        "cache-control": "no-store",
        "content-type": "text/plain; charset=utf-8",
      },
    });
  }
}

function shouldBootstrapSession(request, incomingUrl, dispatchPath) {
  if (!["GET", "HEAD"].includes(request.method.toUpperCase())) {
    return false;
  }
  if (!ROOT_PATHS.has(incomingUrl.pathname) && dispatchPath !== "/") {
    return false;
  }
  if (!acceptsHtml(request.headers)) {
    return false;
  }

  const cookieHeader = request.headers.get("cookie") || "";
  return !hasCookie(cookieHeader, "streamlit_session");
}

async function bootstrapStreamlitSession(incomingUrl) {
  const redirectTarget = `${ORIGIN_BASE}/`;
  const authUrl = new URL("/-/auth/app", SHARE_BASE);
  authUrl.searchParams.set("redirect_uri", redirectTarget);

  const authResponse = await fetch(authUrl.toString(), {
    method: "GET",
    headers: {
      accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    },
    redirect: "manual",
  });

  const authCookies = extractSetCookies(authResponse.headers);
  const loginLocation = authResponse.headers.get("location");
  if (!loginLocation) {
    return proxyAuthFailure("auth bootstrap did not return login redirect");
  }

  const loginResponse = await fetch(loginLocation, {
    method: "GET",
    headers: {
      accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      cookie: buildCookieHeaderFromSetCookies(authCookies),
    },
    redirect: "manual",
  });

  const loginCookies = extractSetCookies(loginResponse.headers);
  const streamlitSessionCookie = findCookieValue(loginCookies, "streamlit_session");
  const csrfCookie = findCookieValue(authCookies, "_streamlit_csrf") || findCookieValue(loginCookies, "_streamlit_csrf");

  if (!streamlitSessionCookie) {
    return proxyAuthFailure("login bootstrap did not yield streamlit_session");
  }

  const headers = new Headers({
    location: `${incomingUrl.protocol}//${incomingUrl.host}${incomingUrl.pathname}${incomingUrl.search}`,
    "cache-control": "no-store",
  });
  headers.append("set-cookie", serializeCookieForIncomingHost("streamlit_session", streamlitSessionCookie, {
    httpOnly: true,
    secure: true,
    sameSite: "Lax",
    path: "/",
  }));
  if (csrfCookie) {
    headers.append("set-cookie", serializeCookieForIncomingHost("_streamlit_csrf", csrfCookie, {
      httpOnly: true,
      secure: true,
      sameSite: "Lax",
      path: "/",
      maxAge: 43200,
    }));
  }

  return new Response(null, {
    status: 302,
    headers,
  });
}

function buildUpstreamUrl(incomingUrl, request) {
  const upstreamPath = normalizeUpstreamPath(incomingUrl.pathname);
  const upstreamUrl = new URL(`${upstreamPath}${incomingUrl.search}`, ORIGIN_BASE);
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

function normalizeUpstreamPath(pathname) {
  return stripRepeatedAppRuntimePrefix(pathname);
}

function normalizeDispatchPath(pathname) {
  return stripRepeatedAppRuntimePrefix(pathname);
}

function stripRepeatedAppRuntimePrefix(pathname) {
  if (!pathname || pathname === "/") {
    return "/";
  }

  let normalized = pathname;
  while (normalized === APP_RUNTIME_PREFIX || normalized.startsWith(`${APP_RUNTIME_PREFIX}/`)) {
    normalized = normalized.slice(APP_RUNTIME_PREFIX.length) || "/";
  }

  return normalized || "/";
}

function shouldUseEmbedMode(incomingUrl, request) {
  if (STATIC_PREFIXES.some((prefix) => incomingUrl.pathname.startsWith(prefix))) {
    return false;
  }
  return true;
}

function isWebSocketUpgrade(request) {
  return (request.headers.get("upgrade") || "").toLowerCase() === "websocket";
}

async function buildClientResponse(upstreamResponse, incomingUrl) {
  const responseHeaders = new Headers(upstreamResponse.headers);
  responseHeaders.set("cache-control", "no-store");
  stripClearingStreamlitCookies(responseHeaders);

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

function buildFaviconResponse(request) {
  const headers = new Headers({
    "cache-control": "public, max-age=31536000, immutable",
    "content-type": "image/png",
  });
  const base64 = FAVICON_DATA_URL.split(",", 2)[1] || "";
  const bytes = Uint8Array.from(atob(base64), (char) => char.charCodeAt(0));

  if (request.method.toUpperCase() === "HEAD") {
    return new Response(null, {
      status: 200,
      headers,
    });
  }

  return new Response(bytes, {
    status: 200,
    headers,
  });
}

function buildHostConfigResponse(request) {
  const headers = new Headers({
    "cache-control": "no-cache",
    "content-type": "application/json; charset=utf-8",
  });
  const incomingUrl = new URL(request.url);
  const incomingOrigin = `${incomingUrl.protocol}//${incomingUrl.host}`;

  const payload = {
    allowedOrigins: [
      incomingOrigin,
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

async function proxyShareJson(url, incomingUrl, responseKind = "") {
  const upstreamResponse = await fetch(url, {
    method: "GET",
    headers: {
      accept: "application/json",
    },
  });

  const responseHeaders = new Headers(upstreamResponse.headers);
  responseHeaders.set("cache-control", "no-store");
  const payloadText = await upstreamResponse.text();
  let rewrittenPayload = payloadText;

  try {
    const payload = JSON.parse(payloadText);
    if (responseKind === "disambiguate" && payload && typeof payload === "object") {
      // Keep the original owner/repo metadata, but point the frontend at the
      // custom Pages host so it stays on the proxy domain instead of jumping
      // straight to the upstream Streamlit app.
      if (payload.host) {
        payload.host = incomingUrl.host;
      }
      rewrittenPayload = JSON.stringify(payload);
    } else if (responseKind === "context" && payload && typeof payload === "object") {
      if (payload.app && typeof payload.app === "object") {
        payload.app.creatorProfilePage = payload.app.creatorProfilePage || {};
        payload.app.creatorProfilePage.userName = "";
      }
      if (payload.workspace && typeof payload.workspace === "object") {
        payload.workspace.name = "";
      }
      rewrittenPayload = JSON.stringify(payload);
    }
  } catch {
    rewrittenPayload = payloadText;
  }

  return buildTextResponse(rewrittenPayload, upstreamResponse, responseHeaders);
}

function buildJsonHeaders() {
  return new Headers({
    "cache-control": "no-store",
    "content-type": "application/json; charset=utf-8",
  });
}

function buildUpstreamHeaders(sourceHeaders, options = {}) {
  const allowConnectionHeader = options.allowConnectionHeader === true;
  const blocked = new Set([
    "content-length",
    "host",
    "transfer-encoding",
  ]);
  if (!allowConnectionHeader) {
    blocked.add("connection");
  }

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

function acceptsHtml(headers) {
  const accept = (headers.get("accept") || "").toLowerCase();
  return !accept || accept.includes("text/html") || accept.includes("application/xhtml+xml") || accept.includes("*/*");
}

function hasCookie(cookieHeader, cookieName) {
  return cookieHeader
    .split(";")
    .map((part) => part.trim())
    .some((part) => part.startsWith(`${cookieName}=`));
}

function extractSetCookies(headers) {
  if (typeof headers.getSetCookie === "function") {
    return headers.getSetCookie();
  }

  const combined = headers.get("set-cookie");
  if (!combined) {
    return [];
  }

  return combined.split(/,(?=[^;,]+=)/g).map((part) => part.trim()).filter(Boolean);
}

function buildCookieHeaderFromSetCookies(setCookies) {
  const pairs = [];
  for (const rawCookie of setCookies) {
    const [pair] = rawCookie.split(";", 1);
    if (pair && pair.includes("=")) {
      pairs.push(pair.trim());
    }
  }
  return pairs.join("; ");
}

function findCookieValue(setCookies, cookieName) {
  for (const rawCookie of setCookies) {
    const [pair] = rawCookie.split(";", 1);
    if (!pair) {
      continue;
    }
    const separator = pair.indexOf("=");
    if (separator === -1) {
      continue;
    }
    const name = pair.slice(0, separator).trim();
    const value = pair.slice(separator + 1).trim();
    if (name === cookieName) {
      return value;
    }
  }
  return "";
}

function serializeCookieForIncomingHost(name, value, options = {}) {
  const segments = [`${name}=${value}`];
  segments.push(`Path=${options.path || "/"}`);
  if (options.httpOnly) {
    segments.push("HttpOnly");
  }
  if (options.secure) {
    segments.push("Secure");
  }
  if (options.sameSite) {
    segments.push(`SameSite=${options.sameSite}`);
  }
  if (options.maxAge) {
    segments.push(`Max-Age=${options.maxAge}`);
  }
  return segments.join("; ");
}

function stripClearingStreamlitCookies(headers) {
  const setCookies = extractSetCookies(headers);
  if (!setCookies.length) {
    return;
  }

  const filteredCookies = setCookies.filter((rawCookie) => {
    const [pair] = rawCookie.split(";", 1);
    if (!pair || !pair.includes("=")) {
      return true;
    }

    const separator = pair.indexOf("=");
    const name = pair.slice(0, separator).trim();
    const value = pair.slice(separator + 1).trim();
    const lowerRaw = rawCookie.toLowerCase();

    if ((name === "streamlit_session" || name === "_streamlit_csrf") && (value === "" || lowerRaw.includes("max-age=0"))) {
      return false;
    }

    return true;
  });

  if (filteredCookies.length === setCookies.length) {
    return;
  }

  headers.delete("set-cookie");
  for (const rawCookie of filteredCookies) {
    headers.append("set-cookie", rawCookie);
  }
}

function proxyAuthFailure(reason) {
  return new Response(`Proxy auth bootstrap failed: ${reason}`, {
    status: 502,
    headers: {
      "cache-control": "no-store",
      "content-type": "text/plain; charset=utf-8",
    },
  });
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

  rewritten = rewritten.replaceAll(`src="//${originHost}/`, `src="${incomingOrigin}/`);
  rewritten = rewritten.replaceAll(`href="//${originHost}/`, `href="${incomingOrigin}/`);
  rewritten = rewritten.replace(/<script src="https:\/\/www\.streamlitstatus\.com\/embed\/script\.js"><\/script>/gi, "");
  rewritten = rewritten.replace(/<iframe[^>]+statuspage\.io\/embed\/frame[^>]*><\/iframe>/gi, "");
  return rewritten;
}

function shouldRewriteJavaScript(incomingUrl, response) {
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("javascript")) {
    return false;
  }

  return /\/-\/build\/assets\/.+\.js$/i.test(incomingUrl.pathname) ||
    /\/static\/js\/.+\.js$/i.test(incomingUrl.pathname);
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
