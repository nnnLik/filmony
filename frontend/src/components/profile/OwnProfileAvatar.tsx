import { Avatar } from '@telegram-apps/telegram-ui'
import { useQueryClient } from '@tanstack/react-query'
import { Pencil, X } from 'lucide-react'
import { useRef, useState, type ChangeEvent } from 'react'

import { ApiError, formatApiDetail } from '../../api/client'
import { deleteMyAvatar, getMyProfile, uploadMyAvatar } from '../../api/profileApi'
import type { MyProfile } from '../../api/profileTypes'
import { readMyProfileBundleCache, writeMyProfileBundleCache } from '../../lib/myProfileBundleCache'
import { myProfileQueryKey } from '../../lib/profileQueryKeys'
import { isCustomAvatarPhotoUrl, userPhotoSrc } from '../../lib/userPhotoSrc'

type OwnProfileAvatarProps = {
  photoUrl: string | null
  acronym: string
  size: number
  onUpdated?: (profile: MyProfile) => void
}

function avatarErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return error instanceof Error ? error.message : 'Не удалось сохранить аватарку'
  }
  const detail = formatApiDetail(error.detail)
  if (detail.includes('empty file')) {
    return 'Файл пустой'
  }
  if (detail.includes('unsupported')) {
    return 'Можно загрузить JPEG, PNG, WebP или GIF'
  }
  if (detail.includes('too large')) {
    return 'Файл больше 5 МБ'
  }
  if (detail.includes('not configured') || detail.includes('unreachable')) {
    return 'Не удалось сохранить аватарку'
  }
  return detail
}

export function OwnProfileAvatar({ photoUrl, acronym, size, onUpdated }: OwnProfileAvatarProps) {
  const queryClient = useQueryClient()
  const inputRef = useRef<HTMLInputElement>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const custom = isCustomAvatarPhotoUrl(photoUrl)

  async function remember(next: MyProfile): Promise<void> {
    const bundle = readMyProfileBundleCache()
    writeMyProfileBundleCache(next, bundle?.cards ?? null)
    await queryClient.invalidateQueries({ queryKey: myProfileQueryKey() })
    onUpdated?.(next)
  }

  async function onPick(event: ChangeEvent<HTMLInputElement>): Promise<void> {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (file == null) {
      return
    }
    setBusy(true)
    setError(null)
    try {
      await remember(await uploadMyAvatar(file))
    } catch (err) {
      setError(avatarErrorMessage(err))
      try {
        await remember(await getMyProfile())
      } catch {
        await queryClient.invalidateQueries({ queryKey: myProfileQueryKey() })
      }
    } finally {
      setBusy(false)
    }
  }

  async function onRemove(): Promise<void> {
    setBusy(true)
    setError(null)
    try {
      await remember(await deleteMyAvatar())
    } catch (err) {
      setError(avatarErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="group relative w-fit">
      <button
        type="button"
        className="relative block rounded-full disabled:opacity-60"
        disabled={busy}
        aria-label="Загрузить аватарку"
        onClick={() => inputRef.current?.click()}
      >
        <Avatar src={userPhotoSrc(photoUrl)} acronym={acronym} size={size} />
        <span className="pointer-events-none absolute right-0 bottom-0 flex size-6 items-center justify-center rounded-full bg-(--tgui--button_color,#2481cc) text-white opacity-0 shadow-sm transition-opacity group-hover:opacity-100 group-focus-within:opacity-100 [@media(hover:none)]:opacity-100">
          <Pencil className="block size-3.5" strokeWidth={2} aria-hidden />
        </span>
      </button>
      {custom ? (
        <button
          type="button"
          className="absolute -top-1 -right-1 flex size-6 items-center justify-center rounded-full bg-(--tgui--destructive_text_color,#e53935) text-white opacity-0 shadow-sm transition-opacity pointer-events-none group-hover:pointer-events-auto group-hover:opacity-100 group-focus-within:pointer-events-auto group-focus-within:opacity-100 disabled:opacity-60 [@media(hover:none)]:pointer-events-auto [@media(hover:none)]:opacity-100"
          aria-label="Убрать свою аватарку"
          disabled={busy}
          onClick={() => void onRemove()}
        >
          <X className="block size-3.5" strokeWidth={2} aria-hidden />
        </button>
      ) : null}
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/gif"
        className="hidden"
        onChange={(event) => void onPick(event)}
      />
      {error != null ? (
        <p role="alert" className="mt-1 max-w-40 text-center text-xs text-(--tgui--destructive_text_color)">
          {error}
        </p>
      ) : null}
    </div>
  )
}
