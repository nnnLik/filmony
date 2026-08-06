import { ApiError, apiFetch, apiJson, readErrorDetail } from './client'
import type { MyAchievementsListResponse, SetAchievementPinsRequest } from './achievementsTypes'

async function assertActionOk(res: Response): Promise<void> {
  if (!res.ok) {
    throw new ApiError(res.status, await readErrorDetail(res))
  }
}

export async function fetchMyAchievements(): Promise<MyAchievementsListResponse> {
  return apiJson<MyAchievementsListResponse>('/api/me/achievements')
}

export async function updateAchievementPins(slugs: string[]): Promise<void> {
  const body: SetAchievementPinsRequest = { achievement_slugs: slugs }
  const res = await apiFetch('/api/me/achievement-pins', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  await assertActionOk(res)
}
