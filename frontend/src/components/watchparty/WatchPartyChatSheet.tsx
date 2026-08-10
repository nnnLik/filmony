import { IconButton } from '@telegram-apps/telegram-ui'
import { Send, X } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { createPortal } from 'react-dom'

import { createWatchPartyMessage, sendWatchPartyTyping } from '../../api/watchPartyApi'
import type { WatchPartyMessage } from '../../api/watchPartyTypes'
import { mergeWatchPartyMessages } from '../../lib/mergeWatchPartyMessages'

import { WatchPartyChatList } from './WatchPartyChatList'

const TYPING_DEBOUNCE_MS = 2000
const TYPING_DISPLAY_MS = 3500

export type WatchPartyChatSheetProps = {
  open: boolean
  partyId: string
  messages: WatchPartyMessage[]
  onMessagesChange: (next: WatchPartyMessage[]) => void
  typingNames: string[]
  onClose: () => void
}

export function WatchPartyChatSheet({
  open,
  partyId,
  messages,
  onMessagesChange,
  typingNames,
  onClose,
}: WatchPartyChatSheetProps) {
  const [chatDraft, setChatDraft] = useState('')
  const lastTypingSentRef = useRef(0)

  const submitChat = useCallback(
    async (event?: FormEvent) => {
      event?.preventDefault()
      if (chatDraft.trim() === '') {
        return
      }
      const body = chatDraft.trim()
      setChatDraft('')
      try {
        await createWatchPartyMessage(partyId, body)
      } catch {
        setChatDraft(body)
      }
    },
    [chatDraft, partyId],
  )

  useEffect(() => {
    if (!open || chatDraft.trim() === '') {
      return undefined
    }
    const now = Date.now()
    if (now - lastTypingSentRef.current < TYPING_DEBOUNCE_MS) {
      return undefined
    }
    lastTypingSentRef.current = now
    void sendWatchPartyTyping(partyId).catch(() => undefined)
    return undefined
  }, [chatDraft, open, partyId])

  const typingLabel = useMemo(() => {
    const filtered = typingNames.filter((name) => name.trim() !== '')
    if (filtered.length === 0) {
      return null
    }
    if (filtered.length === 1) {
      return `${filtered[0]} печатает…`
    }
    return `${filtered.slice(0, 2).join(', ')} печатают…`
  }, [typingNames])

  const handleOlderMessages = useCallback(
    (older: WatchPartyMessage[]) => {
      onMessagesChange(mergeWatchPartyMessages(messages, older))
    },
    [messages, onMessagesChange],
  )

  if (!open) {
    return null
  }

  return createPortal(
    <div className="filmony-theme fixed inset-0 z-50 flex flex-col justify-end text-(--tgui--text_color) pointer-events-auto">
      <button
        type="button"
        className="absolute inset-0 bg-[color-mix(in_srgb,var(--filmony-ink,#06090d)_72%,transparent)]"
        aria-label="Закрыть"
        onClick={onClose}
      />
      <div
        className="relative z-10 mx-auto flex h-[50dvh] w-full max-w-md flex-col rounded-t-[22px] border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-3 shadow-[0_-16px_48px_rgba(0,0,0,0.5)]"
        role="dialog"
        aria-modal="true"
      >
        <div className="mb-2 flex shrink-0 items-center justify-between">
          <div className="min-w-0">
            <p className="text-sm font-semibold">Чат</p>
            {typingLabel != null ? (
              <p className="truncate text-xs text-(--tgui--hint_color)">{typingLabel}</p>
            ) : null}
          </div>
          <IconButton mode="gray" size="s" onClick={onClose} aria-label="Закрыть чат">
            <X className="block size-5" />
          </IconButton>
        </div>
        <WatchPartyChatList
          partyId={partyId}
          messages={messages}
          onOlderMessages={handleOlderMessages}
        />
        <form
          className="mt-2 flex shrink-0 items-center gap-2 border-t border-white/10 pt-2"
          onSubmit={(e) => {
            void submitChat(e)
          }}
        >
          <input
            className="min-w-0 flex-1 rounded-full bg-white/10 px-3 py-2 text-sm text-white outline-none placeholder:text-white/50"
            placeholder="Сообщение…"
            value={chatDraft}
            onChange={(e) => setChatDraft(e.target.value)}
            aria-label="Сообщение"
          />
          <IconButton mode="bezeled" type="submit" size="s" aria-label="Отправить">
            <Send className="block size-4" />
          </IconButton>
        </form>
        <p className="mt-1 shrink-0 text-center text-[10px] text-(--tgui--hint_color)">
          История чата доступна только пока комната открыта.
        </p>
      </div>
    </div>,
    document.body,
  )
}

export const WATCH_PARTY_TYPING_DISPLAY_MS = TYPING_DISPLAY_MS
