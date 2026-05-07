import { apiJson } from './client'

export type NotificationPingResponse = {
  status: string
}

export async function postNotificationPing(): Promise<NotificationPingResponse> {
  return apiJson<NotificationPingResponse>('/api/me/notifications/ping', {
    method: 'POST',
  })
}
