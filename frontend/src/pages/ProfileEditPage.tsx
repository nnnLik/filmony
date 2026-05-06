import { Avatar, Button, Input, Title } from '@telegram-apps/telegram-ui'
import { type ChangeEvent, type FormEvent, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { ApiError, formatApiDetail } from '../api/client'
import { getMyProfile, patchMyProfile } from '../api/profileApi'
import type { MyProfile, PublicProfile } from '../api/profileTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { displayNameFromProfile, profileInitials } from '../lib/profileDisplay'
import { readMyProfileBundleCache, writeMyProfileBundleCache } from '../lib/myProfileBundleCache'

function toPublicShape(p: MyProfile): PublicProfile {
  return {
    id: p.id,
    profile_slug: p.profile_slug,
    username: p.username,
    first_name: p.first_name,
    last_name: p.last_name,
    photo_url: p.photo_url,
    display_name: p.display_name,
    bio: p.bio,
    cards_count: p.cards_count,
    friends_count: p.friends_count,
  }
}

export function ProfileEditPage() {
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const cached = useMemo(() => readMyProfileBundleCache(), [])

  const [profile, setProfile] = useState<MyProfile | null>(() => cached?.profile ?? null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  const [displayName, setDisplayName] = useState(() => cached?.profile.display_name ?? '')
  const [bio, setBio] = useState(() => cached?.profile.bio ?? '')

  useEffect(() => {
    if (auth.kind !== 'ready') {
      return
    }
    let alive = true
    void (async () => {
      try {
        const p = await getMyProfile()
        if (!alive) {
          return
        }
        setProfile(p)
        setDisplayName(p.display_name ?? '')
        setBio(p.bio ?? '')
        setLoadError(null)
      } catch (e) {
        if (!alive) {
          return
        }
        if (e instanceof ApiError) {
          setLoadError(formatApiDetail(e.detail))
        } else {
          setLoadError(e instanceof Error ? e.message : 'Ошибка загрузки')
        }
      }
    })()
    return () => {
      alive = false
    }
  }, [auth.kind])

  async function saveProfile() {
    if (profile == null) {
      return
    }
    setSaveError(null)
    setSaving(true)
    try {
      const next = await patchMyProfile({
        display_name: displayName.trim() || null,
        bio: bio.trim() || null,
      })
      setProfile(next)
      const bundle = readMyProfileBundleCache()
      writeMyProfileBundleCache(next, bundle?.cards ?? null)
      void navigate('/profile')
    } catch (err) {
      if (err instanceof ApiError) {
        setSaveError(formatApiDetail(err.detail))
      } else {
        setSaveError(err instanceof Error ? err.message : 'Не удалось сохранить')
      }
    } finally {
      setSaving(false)
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    void saveProfile()
  }

  if (auth.kind === 'loading') {
    return (
      <div className="px-4 py-16 text-center text-sm text-(--tgui--hint_color)">
        <p className="filmony-text-panel inline-block">Вход…</p>
      </div>
    )
  }

  if (auth.kind === 'error') {
    return (
      <div className="mx-auto max-w-md px-4 py-12">
        <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">{auth.message}</p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to="/">
          На главную
        </Link>
      </div>
    )
  }

  if (auth.kind === 'skipped') {
    return (
      <div className="mx-auto max-w-md px-4 py-12">
        <p className="filmony-text-panel text-sm text-(--tgui--hint_color)">
          Откройте приложение в Telegram, чтобы редактировать профиль.
        </p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to="/">
          На главную
        </Link>
      </div>
    )
  }

  if (loadError != null) {
    return (
      <div className="mx-auto max-w-md px-4 py-12">
        <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">{loadError}</p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to="/profile">
          К профилю
        </Link>
      </div>
    )
  }

  if (profile == null) {
    return (
      <div className="px-4 py-16 text-center text-sm text-(--tgui--hint_color)">
        <p className="filmony-text-panel inline-block">Загрузка…</p>
      </div>
    )
  }

  const pub = toPublicShape(profile)

  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-20 flex items-center gap-2 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] px-2 py-2 backdrop-blur-md">
        <Link
          className="flex min-h-10 min-w-10 items-center justify-center rounded-xl text-lg text-(--tgui--link_color) no-underline"
          to="/profile"
          aria-label="Назад к профилю"
        >
          ←
        </Link>
        <h1 className="text-base font-semibold tracking-tight text-(--tgui--text_color)">Редактирование</h1>
      </header>

      <main className="px-4 py-6">
        <div className="mb-5 flex flex-col items-center text-center">
          <Avatar src={profile.photo_url ?? undefined} acronym={profileInitials(pub)} size={72} />
          <Title className="mt-3" level="2" weight="2">
            {displayNameFromProfile(pub)}
          </Title>
          <p className="mt-1 font-mono text-xs text-(--tgui--hint_color)">@{profile.profile_slug}</p>
        </div>

        <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
          <div className="filmony-text-panel flex flex-col gap-3">
            <Input
              header="Отображаемое имя"
              placeholder={displayNameFromProfile(pub)}
              value={displayName}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setDisplayName(e.target.value)}
            />
            <div className="flex flex-col gap-1">
              <span className="px-3 text-xs font-medium uppercase tracking-wide text-(--tgui--hint_color)">
                О себе
              </span>
              <textarea
                className="min-h-[88px] rounded-xl border border-(--tgui--divider_color) bg-(--tgui--tertiary_bg_color) px-3 py-2 text-(--tgui--text_color) outline-none"
                maxLength={500}
                placeholder="Коротко о вкусе"
                value={bio}
                onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setBio(e.target.value)}
              />
            </div>
          </div>
          {saveError != null ? (
            <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">{saveError}</p>
          ) : null}
          <Button type="submit" disabled={saving} stretched>
            {saving ? 'Сохранение…' : 'Сохранить'}
          </Button>
        </form>
      </main>
    </div>
  )
}
