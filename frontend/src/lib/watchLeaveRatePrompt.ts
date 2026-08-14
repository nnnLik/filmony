import { isTMA } from '@telegram-apps/sdk'

import { endWatchParty, leaveWatchParty } from '../api/watchPartyApi'

export const WATCH_LEAVE_RATE_MESSAGE = 'Оценить фильм?'

export type WatchLeaveChoice = 'rate' | 'close' | 'cancel'

export function filmRateCardPath(filmId: number, myCardId: number | null | undefined): string {
  if (myCardId != null && myCardId > 0) {
    return `/cards/${myCardId}/edit`
  }
  return `/cards/new?filmId=${encodeURIComponent(String(filmId))}`
}

export function promptWatchLeaveRate(onChoice: (choice: WatchLeaveChoice) => void): void {
  if (!isTMA()) {
    onChoice('cancel')
    return
  }

  const wa = window.Telegram?.WebApp
  if (wa?.showPopup) {
    wa.showPopup(
      {
        message: WATCH_LEAVE_RATE_MESSAGE,
        buttons: [
          { id: 'rate', type: 'default', text: 'Оценить фильм' },
          { id: 'close', type: 'destructive', text: 'Просто закрыть' },
        ],
      },
      (buttonId) => {
        if (buttonId === 'rate') {
          onChoice('rate')
        } else if (buttonId === 'close') {
          onChoice('close')
        } else {
          onChoice('cancel')
        }
      },
    )
    return
  }

  onChoice('cancel')
}

export async function leaveWatchPartyQuietly(partyId: string | null, isHost: boolean): Promise<void> {
  if (partyId == null) {
    return
  }
  try {
    if (isHost) {
      await endWatchParty(partyId)
    } else {
      await leaveWatchParty(partyId)
    }
  } catch {
    /* ignore */
  }
}
