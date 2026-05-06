import type { ReactionSummary } from '../../../api/profileTypes'

export const EMPTY: ReactionSummary = { counts: [], my_reaction_type_ids: [] }

export const POPOVER_GAP = 10
export const SIDE_PAD = 10
export const POPOVER_W_DEFAULT = 300
export const POPOVER_W_COMPACT = 264

/** Непрозрачная палитра попапа (как эталон Telegram). */
export const PICK_BG = 'bg-[#121212]'
export const PICK_SURFACE = 'bg-[#1c1c1f]'
export const PICK_BORDER = 'border-[#2c2c2e]'
