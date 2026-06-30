export type RouteKeyInput = {
  pathname: string;
  search?: string;
  params?: Record<string, string>;
  allowedQueryKeys?: string[];
};

export function buildRouteKey({
  pathname,
  search,
  params,
  allowedQueryKeys,
}: RouteKeyInput): string {
  const query = new URLSearchParams(search ?? '');
  const queryKeys = allowedQueryKeys ?? [];
  const normalizedQuery = queryKeys
    .map((key) => [key, query.get(key) ?? ''])
    .filter(([, value]) => value.length > 0)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, value]) => `${key}=${value}`)
    .join('&');

  const normalizedParams = params
    ? Object.keys(params)
        .sort()
        .map((key) => `${key}=${params[key]}`)
        .join('&')
    : '';

  const parts = [pathname];
  if (normalizedParams.length > 0) {
    parts.push(`params:${normalizedParams}`);
  }
  if (normalizedQuery.length > 0) {
    parts.push(`query:${normalizedQuery}`);
  }
  return parts.join('|');
}
