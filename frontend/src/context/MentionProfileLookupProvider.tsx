import { useContext, useMemo, type ReactNode } from 'react'

import { mergeMentionProfileMaps, type MentionProfileRowInput } from '../lib/mentionProfileLookupUtils'

import { MentionProfileLookupContext } from './mentionProfileLookupContext'

export function MentionProfileLookupProvider({
  value,
  children,
}: {
  value: readonly MentionProfileRowInput[]
  children: ReactNode
}) {
  const parent = useContext(MentionProfileLookupContext)
  const merged = useMemo(() => mergeMentionProfileMaps(parent, value), [parent, value])
  return <MentionProfileLookupContext.Provider value={merged}>{children}</MentionProfileLookupContext.Provider>
}
