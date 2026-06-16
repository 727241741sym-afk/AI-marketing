export function apiPath(path) {
  if (typeof path !== "string" || /^https?:\/\//i.test(path)) {
    throw new Error("API requests must use same-origin /api paths");
  }

  const normalized = path.startsWith("/") ? path : `/${path}`;
  if (!normalized.startsWith("/api/") && normalized !== "/api") {
    throw new Error("API requests must target /api");
  }
  return normalized;
}
