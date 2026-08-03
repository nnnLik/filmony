import { apiJson } from './client'
import type { GamificationResponse, PublicPassportResponse } from './gamificationTypes'

export async function getMyGamification(): Promise<GamificationResponse> {
  return apiJson<GamificationResponse>('/api/me/gamification')
}

export async function getUserGamificationPassport(userId: string): Promise<PublicPassportResponse> {
  return apiJson<PublicPassportResponse>(`/api/users/${encodeURIComponent(userId)}/gamification/passport`)
}
