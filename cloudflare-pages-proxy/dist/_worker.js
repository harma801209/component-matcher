const ORIGIN_BASE = "https://fruition-componentmatche.streamlit.app";
const APP_PREFIX = "/~/+";

export default {
  async fetch(request) {
    return proxyRequest(request);
  },
};

async function proxyRequest(request) {
  const incomingUrl = new URL(request.url);
  const upstreamUrl = buildUpstreamUrl(incomingUrl);
  const upstreamHeaders = buildUpstreamHeaders(request.headers);
  const isWebSocketRequest = (request.headers.get("upgrade") || "").toLowerCase() === "websocket";
  const requestInit = {
    method: request.method,
    headers: upstreamHeaders,
  };

  if (!["GET", "HEAD"].includes(request.method.toUpperCase())) {
    requestInit.body = request.body;
  }

  const upstreamRequest = new Request(upstreamUrl, requestInit);
  const upstreamResponse = await fetch(upstreamRequest, isWebSocketRequest ? undefined : {
    redirect: "manual",
  });

  if (isWebSocketRequest) {
    return upstreamResponse;
  }

  return buildClientResponse(upstreamResponse, incomingUrl);
}

function buildUpstreamUrl(incomingUrl) {
  const upstreamUrl = new URL(ORIGIN_BASE);
  upstreamUrl.pathname = buildUpstreamPath(incomingUrl.pathname);
  upstreamUrl.search = incomingUrl.search;
  return upstreamUrl.toString();
}

function buildUpstreamPath(pathname) {
  if (!pathname || pathname === "/") {
    return `${APP_PREFIX}/`;
  }

  if (pathname.startsWith(APP_PREFIX)) {
    return pathname;
  }

  return `${APP_PREFIX}${pathname}`;
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
    return buildTextResponse(html, upstreamResponse, responseHeaders);
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

function rewriteLocation(location, incomingUrl) {
  try {
    const resolved = new URL(location, ORIGIN_BASE);
    const origin = new URL(ORIGIN_BASE);
    if (resolved.origin === origin.origin) {
      resolved.protocol = incomingUrl.protocol;
      resolved.host = incomingUrl.host;

      if (resolved.pathname.startsWith(APP_PREFIX)) {
        resolved.pathname = resolved.pathname.slice(APP_PREFIX.length) || "/";
      }

      return resolved.toString();
    }
    return location;
  } catch {
    return location;
  }
}

function isHtmlResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  return contentType.includes("text/html");
}

function buildUpstreamHeaders(sourceHeaders) {
  const blocked = new Set([
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
    headers.set(key, value);
  }

  headers.set("origin", ORIGIN_BASE);
  headers.set("referer", `${ORIGIN_BASE}/`);
  return headers;
}
