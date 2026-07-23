import { Button } from '@telegram-apps/telegram-ui'

export type TasteQuizFollowSoftBannerProps = {
  ownerName: string
  ownerUserId: string
  following: boolean
  followBusy?: boolean
  onFollow: () => void
}

export function TasteQuizFollowSoftBanner({
  ownerName,
  following,
  followBusy = false,
  onFollow,
}: TasteQuizFollowSoftBannerProps) {
  if (following) {
    return null
  }

  return (
    <div className="rounded-2xl border border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_35%,var(--tgui--divider_color))] bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_8%,var(--tgui--secondary_bg_color))] px-4 py-3">
      <p className="text-sm text-(--tgui--text_color)">
        Хотите следить за {ownerName}?
      </p>
      <Button
        className="mt-2"
        mode="filled"
        size="s"
        stretched
        disabled={followBusy}
        onClick={onFollow}
      >
        {followBusy ? '…' : `Подписаться на ${ownerName}`}
      </Button>
    </div>
  )
}
