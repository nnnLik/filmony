import { useAuthStatus } from '../auth/useAuthStatus'

export function useAuthReadyGate() {
  const auth = useAuthStatus()
  const isAuthPending = auth.kind === 'loading'
  const isAuthReady = auth.kind === 'ready'

  return { auth, isAuthPending, isAuthReady }
}
