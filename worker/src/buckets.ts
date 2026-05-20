export type BucketRoutes = Record<string, string>;

export function parseBucketRoutes(raw: string | undefined): BucketRoutes {
  if (!raw) {
    return {};
  }
  try {
    const parsed = JSON.parse(raw) as BucketRoutes;
    return parsed ?? {};
  } catch (error) {
    console.error("Invalid BUCKET_ROUTES JSON", error);
    return {};
  }
}

export function resolveBucket(
  env: Record<string, unknown>,
  routes: BucketRoutes,
  bucketSlug: string,
): { binding: R2Bucket; name: string } | null {
  const bindingName = routes[bucketSlug];
  if (!bindingName) {
    return null;
  }

  const bucket = env[bindingName];
  if (!bucket || typeof bucket !== "object") {
    return null;
  }

  return { binding: bucket as R2Bucket, name: bucketSlug };
}

export function parseObjectPath(pathname: string): {
  bucketSlug: string;
  key: string;
} | null {
  const parts = pathname.replace(/^\/+/, "").split("/").filter(Boolean);
  if (parts.length < 2) {
    return null;
  }

  const bucketSlug = parts[0];
  const key = parts.slice(1).join("/");
  if (!bucketSlug || !key) {
    return null;
  }

  return { bucketSlug, key: decodeObjectKey(key) };
}

function decodeObjectKey(segment: string): string {
  try {
    return decodeURIComponent(segment);
  } catch {
    return segment;
  }
}
