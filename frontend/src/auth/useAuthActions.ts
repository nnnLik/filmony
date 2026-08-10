import { useContext } from 'react'

import { AuthActionsContext } from './auth-actions-context'

export function useAuthActions() {
  const ctx = useContext(AuthActionsContext)
  if (ctx == null) {
    throw new Error('useAuthActions must be used within AuthProvider')
  }
  return ctx
}
