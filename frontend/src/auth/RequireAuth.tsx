import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router'

import { useAuthStatus } from './useAuthStatus'

export function RequireAuth({ children }: { children: ReactNode }) {
  const auth = useAuthStatus()
  const location = useLocation()

  if (auth.kind === 'unauthenticated') {
    const returnTo = `${location.pathname}${location.search}`
    return <Navigate to={`/login?returnTo=${encodeURIComponent(returnTo)}`} replace />
  }

  return <>{children}</>
}
