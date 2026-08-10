import { IconButton } from '@telegram-apps/telegram-ui'
import { Send, X } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from 'react'

import { createWatchPartyMessage, sendWatchPartyTyping } from '../../api/watchPartyApi'
import type { WatchPartyMessage } from '../../api/watchPartyTypes'
import { mergeWatchPartyMessages } from '../../lib/mergeWatchPartyMessages'

import { WatchPartyChatList } from './WatchPartyChatList'

const TYPING_DEBOUNCE_MS = 2000

export type WatchPartyInlineChatProps = {
  partyId: string
  messages: WatchPartyMessage[]
  onMessagesChange: (next: WatchPartyMessage[]) => void
  typingNames: string[]
  onClose: () => void
}

export function WatchPartyInlineChat({
  partyId,
  messages,
  onMessagesChange,
  typingNames,
  onClose,
}: WatchPartyInlineChatProps) {
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
    if (chatDraft.trim() === '') {
      return undefined
    }
    const now = Date.now()
    if (now - lastTypingSentRef.current < TYPING_DEBOUNCE_MS) {
      return undefined
    }
    lastTypingSentRef.current = now
    void sendWatchPartyTyping(partyId).catch(() => undefined)
    return undefined
  }, [chatDraft, partyId])

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

  return (
    <div className="flex max-h-[38dvh] min-h-[180px] flex-col border-t border-white/10 bg-(--tgui--bg_color) px-3 py-2">
      <div className="mb-2 flex shrink-0 items-center justify-between">
        <div className="min-w-0">
          <p className="text-sm font-semibold">Чат</p>
          {typingLabel != null ? (
            <p className="truncate text-xs text-(--tgui--hint_color)">{typingLabel}</p>
          ) : null}
        </div>
        <IconButton mode="gray" size="s" onClick={onClose} aria-label="Скрыть чат">
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
    </div>
  )
}
