import { parseBucketRoutes, parseObjectPath, resolveBucket } from "./buckets";
import { notifyEvent, type NotifyEnv, type R2EventPayload } from "./notify";

const DEDUPE_CACHE = caches.default;

export interface ProxyEnv extends NotifyEnv {
  BUCKET_ROUTES: string;
  DEDUPE_TTL_SECONDS?: string;
}

function dedupeTtl(env: ProxyEnv): number {
  const parsed = Number(env.DEDUPE_TTL_SECONDS ?? "600");
  if (!Number.isFinite(parsed) || parsed < 60) {
    return 600;
  }
  return Math.min(parsed, 86_400);
}

function shouldNotifyForRange(rangeHeader: string | null): boolean {
  if (!rangeHeader) {
    return true;
  }

  const match = rangeHeader.match(/bytes=(\d+)-/i);
  if (!match) {
    return true;
  }

  return match[1] === "0";
}

async function wasRecentlyNotified(
  env: ProxyEnv,
  ip: string,
  bucket: string,
  key: string,
): Promise<boolean> {
  const dedupeKey = `https://dedupe.r2-download-alerts/${ip}/${bucket}/${encodeURIComponent(key)}`;
  const hit = await DEDUPE_CACHE.match(dedupeKey);
  return hit !== undefined;
}

async function markNotified(
  env: ProxyEnv,
  ip: string,
  bucket: string,
  key: string,
): Promise<void> {
  const dedupeKey = `https://dedupe.r2-download-alerts/${ip}/${bucket}/${encodeURIComponent(key)}`;
  await DEDUPE_CACHE.put(dedupeKey, new Response("1"), {
    expirationTtl: dedupeTtl(env),
  });
}

function buildDownloadPayload(
  request: Request,
  bucket: string,
  key: string,
  bytesSent: number | null,
): R2EventPayload {
  return {
    eventType: "download",
    bucket,
    key,
    timestamp: new Date().toISOString(),
    method: request.method,
    ip: request.headers.get("CF-Connecting-IP"),
    country: request.headers.get("CF-IPCountry"),
    userAgent: request.headers.get("User-Agent"),
    referer: request.headers.get("Referer"),
    range: request.headers.get("Range"),
    bytesSent,
  };
}

export async function handleProxyRequest(
  request: Request,
  env: ProxyEnv,
): Promise<Response> {
  const url = new URL(request.url);

  if (url.pathname === "/health") {
    return new Response("ok", { status: 200 });
  }

  if (request.method !== "GET" && request.method !== "HEAD") {
    return new Response("Method not allowed", { status: 405 });
  }

  const routes = parseBucketRoutes(env.BUCKET_ROUTES);
  const parsed = parseObjectPath(url.pathname);
  if (!parsed) {
    return new Response(
      "Use /<bucket-name>/<object-key> (example: /my-bucket/videos/clip.mp4)",
      { status: 400 },
    );
  }

  const resolved = resolveBucket(env, routes, parsed.bucketSlug);
  if (!resolved) {
    return new Response("Unknown bucket", { status: 404 });
  }

  const rangeHeader = request.headers.get("Range");
  const object = await resolved.binding.get(
    parsed.key,
    rangeHeader ? { range: request.headers } : undefined,
  );
  if (object === null) {
    return new Response("Not found", { status: 404 });
  }

  const headers = new Headers();
  object.writeHttpMetadata(headers);
  headers.set("etag", object.httpEtag);
  headers.set("Accept-Ranges", "bytes");

  if (request.method === "GET") {
    const ip = request.headers.get("CF-Connecting-IP") ?? "unknown";
    const shouldNotify =
      shouldNotifyForRange(rangeHeader) &&
      !(await wasRecentlyNotified(env, ip, resolved.name, parsed.key));

    if (shouldNotify) {
      await markNotified(env, ip, resolved.name, parsed.key);
      const payload = buildDownloadPayload(
        request,
        resolved.name,
        parsed.key,
        object.size,
      );
      void notifyEvent(env, payload);
    }
  }

  if (request.method === "HEAD") {
    return new Response(null, { status: 200, headers });
  }

  const status = object.range ? 206 : 200;
  if (object.range) {
    const { offset, length } = object.range;
    const end = offset + length - 1;
    headers.set("Content-Range", `bytes ${offset}-${end}/${object.size}`);
  }

  return new Response(object.body, { status, headers });
}
