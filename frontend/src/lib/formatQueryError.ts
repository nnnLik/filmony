import { ApiError, formatApiDetail } from '../api/client'

export function formatQueryError(error: unknown, fallback: string): string | null {
  if (error == null) {
    return null
  }
  if (error instanceof ApiError) {
    return formatApiDetail(error.detail)
  }
  return fallback
}
