import { useContext } from 'react'

import { MentionProfileLookupContext } from '../context/mentionProfileLookupContext'
import type { MentionProfileRow } from '../lib/mentionProfileLookupUtils'

export function useMentionProfileLookup(): ReadonlyMap<string, MentionProfileRow> {
  return useContext(MentionProfileLookupContext)
}
