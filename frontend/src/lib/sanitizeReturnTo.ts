/** Sanitize post-login redirect target — blocks open redirects. */
export function sanitizeReturnTo(raw: string | null): string {
  if (!raw) {
    return '/'
  }
  if (!raw.startsWith('/') || raw.startsWith('//')) {
    return '/'
  }
  return raw
}
