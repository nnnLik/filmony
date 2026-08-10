import { createContext } from 'react'

export type AuthStatus =
  | { kind: 'loading' }
  | { kind: 'ready' }
  | { kind: 'unauthenticated' }
  | { kind: 'error'; message: string }

export const AuthStateContext = createContext<AuthStatus | null>(null)
