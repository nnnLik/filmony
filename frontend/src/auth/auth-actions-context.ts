import { createContext } from 'react'

export type AuthActions = {
  completeLogin: () => void
}

export const AuthActionsContext = createContext<AuthActions | null>(null)
