import { useContext } from 'react'

import { AuthStateContext, type AuthStatus } from './auth-context'

export function useAuthStatus(): AuthStatus {
  const ctx = useContext(AuthStateContext)
  if (ctx == null) {
    throw new Error('useAuthStatus must be used within AuthProvider')
  }
  return ctx
}
