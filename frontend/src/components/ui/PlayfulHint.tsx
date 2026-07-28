import type { MicroFunPoolKey } from '../../lib/microFun'
import { useMicroFunLine } from '../../lib/microFun'

type PlayfulHintProps = {
  poolKey: MicroFunPoolKey
  fallback: string
  userId?: string | number | null
  className?: string
}

export function PlayfulHint({ poolKey, fallback, userId, className }: PlayfulHintProps) {
  const line = useMicroFunLine(poolKey, fallback, userId ?? null)
  return <p className={className}>{line}</p>
}
