import { Avatar, Title } from '@telegram-apps/telegram-ui'

import { displayNameFromProfile, profileInitials } from '../../lib/profileDisplay'
import type { PublicProfile } from '../../api/profileTypes'

type ProfileHeaderProps = {
  profile: PublicProfile
  subtitle?: string
}

export function ProfileHeader({ profile, subtitle }: ProfileHeaderProps) {
  const name = displayNameFromProfile(profile)
  return (
    <div className="flex flex-col items-center gap-3 py-4">
      <Avatar src={profile.photo_url ?? undefined} acronym={profileInitials(profile)} size={72} />
      <div className="text-center">
        <Title level="2" weight="2">
          {name}
        </Title>
        {subtitle != null && subtitle !== '' ? (
          <p className="filmony-text-panel mt-2 inline-block max-w-[min(100%,20rem)] text-sm text-(--tgui--hint_color,#94a3b8)">
            {subtitle}
          </p>
        ) : null}
        <p className="mt-1 font-mono text-xs text-(--tgui--hint_color,#94a3b8)">@{profile.profile_slug}</p>
      </div>
    </div>
  )
}
