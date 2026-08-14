import { apiJson } from './client'
import type { EveningForTwoPick } from './profileTypes'

export async function getEveningForTwoPick(partnerUserId: string): Promise<EveningForTwoPick> {
  const q = new URLSearchParams({ partner_user_id: partnerUserId })
  return apiJson<EveningForTwoPick>(`/api/me/watchlist/evening-for-two?${q.toString()}`)
}
