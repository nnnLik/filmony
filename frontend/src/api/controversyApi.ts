import { apiJson } from './client'
import type { WeeklyControversyResponse } from './controversyTypes'

export async function getMyWeeklyControversy(): Promise<WeeklyControversyResponse> {
  return apiJson<WeeklyControversyResponse>('/api/me/weekly-controversy')
}
