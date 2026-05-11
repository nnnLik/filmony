import { createContext } from 'react'

import type { MentionProfileRow } from '../lib/mentionProfileLookupUtils'

export const MentionProfileLookupContext = createContext<ReadonlyMap<string, MentionProfileRow>>(new Map())
