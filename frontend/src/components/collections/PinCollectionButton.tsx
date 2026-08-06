import { Button } from '@telegram-apps/telegram-ui'
import { useState } from 'react'

import {
  formatCollectionPinError,
  useCollectionPinMutation,
} from '../../hooks/useCollectionPinMutation'

type PinCollectionButtonProps = {
  slug: string
  isPinned: boolean
  className?: string
}

export function PinCollectionButton({ slug, isPinned, className }: PinCollectionButtonProps) {
  const mutation = useCollectionPinMutation()
  const [error, setError] = useState<string | null>(null)

  async function handleClick() {
    setError(null)
    try {
      await mutation.mutateAsync({ slug, nextPinned: !isPinned })
    } catch (e) {
      setError(formatCollectionPinError(e))
    }
  }

  return (
    <div className={className}>
      <Button
        mode={isPinned ? 'gray' : 'filled'}
        stretched
        disabled={mutation.isPending}
        onClick={() => void handleClick()}
      >
        {mutation.isPending ? '…' : isPinned ? 'Открепить' : 'Закрепить'}
      </Button>
      {error != null ? (
        <p className="filmony-text-panel mt-2 text-center text-xs text-(--tgui--destructive_text_color)">
          {error}
        </p>
      ) : null}
    </div>
  )
}
