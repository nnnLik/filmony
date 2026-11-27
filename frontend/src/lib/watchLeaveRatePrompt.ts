import { isTMA } from '@telegram-apps/sdk'

import { endWatchParty, leaveWatchParty } from '../api/watchPartyApi'

export const WATCH_LEAVE_RATE_MESSAGE = 'Оценить фильм?'

export type WatchLeaveChoice = 'rate' | 'close' | 'cancel'

export function filmRateCardPath(
  filmId: number,
  opts?: {
    myCardId?: number | null
    plannedCardId?: number | null
  },
): string {
  const mine = opts?.myCardId != null && opts.myCardId > 0 ? opts.myCardId : null
  const planned = opts?.plannedCardId != null && opts.plannedCardId > 0 ? opts.plannedCardId : null
  if (mine != null && (planned == null || mine !== planned)) {
    return `/cards/${mine}/edit`
  }
  if (planned != null) {
    return `/cards/new?fromCard=${encodeURIComponent(String(planned))}&intent=rate`
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
