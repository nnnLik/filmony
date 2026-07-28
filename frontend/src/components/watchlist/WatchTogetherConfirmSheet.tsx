import { Avatar, Button, IconButton } from '@telegram-apps/telegram-ui'
import { Users, X } from 'lucide-react'
import { createPortal } from 'react-dom'

import type { WatchlistOverlapPartner } from '../../api/profileTypes'
import { profileInitials } from '../../lib/profileDisplay'

function partnerDisplayName(partner: WatchlistOverlapPartner): string {
  if (partner.display_name?.trim()) {
    return partner.display_name.trim()
  }
  if (partner.slug?.trim()) {
    return `@${partner.slug.trim()}`
  }
  return 'Пользователь'
}

function partnerInitials(partner: WatchlistOverlapPartner): string {
  return profileInitials({
    display_name: partner.display_name,
    first_name: null,
    username: partner.slug,
  })
}

export type WatchTogetherConfirmSheetProps = {
  open: boolean
  mode?: 'create' | 'invite'
  title: string
  posterUrl: string | null
  partners: WatchlistOverlapPartner[]
  busy?: boolean
  onClose: () => void
  onConfirm: () => void
}

export function WatchTogetherConfirmSheet({
  open,
  mode = 'create',
  title,
  posterUrl,
  partners,
  busy = false,
  onClose,
  onConfirm,
}: WatchTogetherConfirmSheetProps) {
  if (!open) {
    return null
  }

  const isInvite = mode === 'invite'

  return createPortal(
    <div
      className="filmony-theme fixed inset-0 z-50 flex flex-col justify-end text-(--tgui--text_color) pointer-events-auto"
      aria-hidden={false}
    >
      <button
        type="button"
        className="absolute inset-0 bg-[color-mix(in_srgb,var(--filmony-ink,#06090d)_72%,transparent)] opacity-100 transition-opacity duration-200"
        tabIndex={0}
        aria-label="Закрыть"
        onClick={onClose}
      />
      <div
        className="relative z-10 isolate mx-auto flex w-full max-w-md flex-col rounded-t-[22px] border border-(--tgui--divider_color) bg-(--tgui--tertiary_bg_color) shadow-[0_-16px_48px_rgba(0,0,0,0.5),inset_0_1px_0_rgba(255,255,255,0.06)] motion-safe:animate-[filmony-detail-fade-in_0.2s_ease-out_both] ring-1 ring-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_14%,transparent)]"
        role="dialog"
        aria-modal="true"
        aria-labelledby="watch-together-sheet-title"
      >
        <div className="flex shrink-0 items-center justify-between gap-2 border-b border-[color-mix(in_srgb,var(--tgui--divider_color)_75%,transparent)] px-3 py-2.5">
          <h2
            id="watch-together-sheet-title"
            className="min-w-0 flex-1 truncate text-[16px] font-semibold tracking-tight text-(--tgui--text_color)"
          >
            {isInvite ? 'Пригласить смотреть' : 'Смотрим вместе'}
          </h2>
          <IconButton mode="gray" size="s" onClick={onClose} aria-label="Закрыть" disabled={busy}>
            <X className="block size-5" strokeWidth={2} />
          </IconButton>
        </div>

        <div className="flex flex-col gap-3 bg-(--tgui--bg_color) p-3 pb-[max(12px,calc(10px+env(safe-area-inset-bottom)))]">
          <div className="flex gap-3 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-3">
            <div className="h-20 w-14 shrink-0 overflow-hidden rounded-lg bg-(--tgui--bg_color)">
              {posterUrl ? (
                <img src={posterUrl} alt="" className="h-full w-full object-cover" />
              ) : (
                <div className="flex h-full w-full items-center justify-center px-1 text-center text-[10px] text-(--tgui--hint_color)">
                  Нет обложки
                </div>
              )}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-(--tgui--text_color)">{title}</p>
              <p className="mt-1 flex items-center gap-1 text-xs text-(--tgui--hint_color)">
                <Users className="block" size={13} strokeWidth={2} aria-hidden />
                {isInvite
                  ? 'Отправить приглашение друзьям, которые тоже хотят посмотреть'
                  : 'Добавить в «Позже» с выбранными друзьями'}
              </p>
            </div>
          </div>

          {partners.length > 0 ? (
            <ul className="list-none space-y-1.5 p-0">
              {partners.map((partner) => (
                <li
                  key={partner.user_id}
                  className="flex items-center gap-2.5 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-3 py-2"
                >
                  <Avatar
                    src={partner.avatar_url ?? undefined}
                    acronym={partnerInitials(partner)}
                    size={36}
                  />
                  <span className="min-w-0 flex-1 truncate text-sm font-medium text-(--tgui--text_color)">
                    {partnerDisplayName(partner)}
                  </span>
                </li>
              ))}
            </ul>
          ) : null}

          <Button stretched disabled={busy} onClick={onConfirm}>
            {busy
              ? isInvite
                ? 'Отправляем…'
                : 'Добавляем…'
              : isInvite
                ? 'Пригласить'
                : 'Добавить в «Позже»'}
          </Button>
          <Button mode="gray" stretched disabled={busy} onClick={onClose}>
            Отмена
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  )
}
