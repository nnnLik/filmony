import { useVirtualizer } from '@tanstack/react-virtual'
import { useCallback, useEffect, useRef, useState } from 'react'

import { listWatchPartyMessages } from '../../api/watchPartyApi'
import type { WatchPartyMessage } from '../../api/watchPartyTypes'

const PAGE_SIZE = 50

export type WatchPartyChatListProps = {
  partyId: string
  messages: WatchPartyMessage[]
  onOlderMessages: (older: WatchPartyMessage[]) => void
}

export function WatchPartyChatList({
  partyId,
  messages,
  onOlderMessages,
}: WatchPartyChatListProps) {
  const parentRef = useRef<HTMLDivElement | null>(null)
  const [loadingOlder, setLoadingOlder] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const stickToBottomRef = useRef(true)
  const prevCountRef = useRef(messages.length)

  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 52,
    overscan: 8,
  })

  const loadOlder = useCallback(async () => {
    if (loadingOlder || !hasMore || messages.length === 0) {
      return
    }
    const oldestId = messages[0]?.id
    if (oldestId == null) {
      return
    }
    setLoadingOlder(true)
    try {
      const older = await listWatchPartyMessages(partyId, {
        before_id: oldestId,
        limit: PAGE_SIZE,
      })
      if (older.length < PAGE_SIZE) {
        setHasMore(false)
      }
      if (older.length > 0) {
        onOlderMessages(older)
      } else {
        setHasMore(false)
      }
    } catch {
      /* ignore pagination errors */
    } finally {
      setLoadingOlder(false)
    }
  }, [hasMore, loadingOlder, messages, onOlderMessages, partyId])

  useEffect(() => {
    const parent = parentRef.current
    if (parent == null) {
      return undefined
    }
    const onScroll = () => {
      const distanceFromBottom = parent.scrollHeight - parent.scrollTop - parent.clientHeight
      stickToBottomRef.current = distanceFromBottom < 80
      if (parent.scrollTop < 48) {
        void loadOlder()
      }
    }
    parent.addEventListener('scroll', onScroll)
    return () => parent.removeEventListener('scroll', onScroll)
  }, [loadOlder])

  useEffect(() => {
    const parent = parentRef.current
    if (parent == null) {
      return
    }
    const grew = messages.length > prevCountRef.current
    prevCountRef.current = messages.length
    if (grew && stickToBottomRef.current) {
      parent.scrollTop = parent.scrollHeight
    }
  }, [messages.length])

  return (
    <div ref={parentRef} className="min-h-0 flex-1 overflow-y-auto">
      {loadingOlder ? (
        <p className="py-2 text-center text-xs text-(--tgui--hint_color)">Загрузка…</p>
      ) : null}
      <div
        className="relative w-full"
        style={{ height: `${virtualizer.getTotalSize()}px` }}
      >
        {virtualizer.getVirtualItems().map((item) => {
          const message = messages[item.index]
          if (message == null) {
            return null
          }
          return (
            <div
              key={message.id}
              ref={virtualizer.measureElement}
              data-index={item.index}
              className="absolute left-0 top-0 w-full px-1"
              style={{ transform: `translateY(${item.start}px)` }}
            >
              <div className="rounded-lg bg-white/5 px-2 py-1.5 text-sm">{message.body}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
