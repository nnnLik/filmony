import { useAuthStatus } from '../auth/useAuthStatus'

export function useAuthReadyGate() {
  const auth = useAuthStatus()
  const isAuthPending = auth.kind === 'loading' || auth.kind === 'skipped'
  const isAuthReady = auth.kind === 'ready'

  return { auth, isAuthPending, isAuthReady }
}
