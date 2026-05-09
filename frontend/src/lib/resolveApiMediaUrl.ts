import { resolveApiUrl } from '../api/client'

export function resolveApiMediaUrl(url: string): string {
  return resolveApiUrl(url.trim())
}
