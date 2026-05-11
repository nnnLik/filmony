import { readAccessToken } from '../lib/filmonySession'

import { readHttpErrorDetail } from './readHttpErrorDetail'

export function resolveApiUrl(path: string): string {
  const base = import.meta.env.VITE_API_ORIGIN?.trim().replace(/\/$/, '') ?? ''
  if (!base) {
    return path
  }
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  return `${base}${path.startsWith('/') ? path : `/${path}`}`
}

export class ApiError extends Error {
  readonly status: number
  readonly detail: unknown

  constructor(status: number, detail: unknown) {
    super(typeof detail === 'string' ? detail : `HTTP ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

export async function readErrorDetail(res: Response): Promise<unknown> {
  return readHttpErrorDetail(res)
}

export async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const token: string | null = readAccessToken()
  const headers: Record<string, string> = {
    ...(init?.headers as Record<string, string> | undefined),
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  return fetch(resolveApiUrl(path), {
    ...init,
    credentials: 'include',
    headers,
  })
}

export async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await apiFetch(path, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init?.method && init.method !== 'GET' && init.method !== 'HEAD'
        ? { 'Content-Type': 'application/json' }
        : {}),
      ...(init?.headers as Record<string, string> | undefined),
    },
  })
  if (!res.ok) {
    throw new ApiError(res.status, await readErrorDetail(res))
  }
  return (await res.json()) as T
}

export async function postJson(path: string, body: unknown): Promise<Response> {
  return apiFetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function formatApiDetail(detail: unknown): string {
  if (detail == null) {
    return 'Неизвестная ошибка'
  }
  if (typeof detail === 'string') {
    return detail
  }
  if (Array.isArray(detail)) {
    return detail.map((x) => (typeof x === 'object' && x && 'msg' in x ? String((x as { msg: unknown }).msg) : JSON.stringify(x))).join('; ')
  }
  return JSON.stringify(detail)
}
