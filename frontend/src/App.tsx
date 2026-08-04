import '@telegram-apps/telegram-ui/dist/styles.css'

import { AppRoot } from '@telegram-apps/telegram-ui'
import { isTMA } from '@telegram-apps/sdk'

import { TelegramMiniAppStartParamRedirect } from './navigation/TelegramMiniAppStartParamRedirect'
import { AuthProvider } from './auth/AuthProvider'
import { useAuthStatus } from './auth/useAuthStatus'
import { MentionProfileLookupBootstrap } from './components/MentionProfileLookupBootstrap'
import { ComposeFeedPostProvider } from './compose/ComposeFeedPostProvider'
import { ScrollToTopFab } from './components/navigation/ScrollToTopFab'
import { ScrollRestoreProvider } from './features/scrollRestore/ScrollRestoreProvider'
import { RoutePageFallback } from './layout/RoutePageFallback'
import { getPendingStartParamRedirect } from './lib/miniAppCardDeepLink'
import { QueryProvider } from './providers/QueryProvider'
import { AppRoutes } from './routes'

function AppRoutesGate() {
  const auth = useAuthStatus()
  const pendingStartParam = isTMA() && auth.kind === 'loading' ? getPendingStartParamRedirect() : null

  if (pendingStartParam != null) {
    return <RoutePageFallback />
  }

  return (
    <MentionProfileLookupBootstrap>
      <ComposeFeedPostProvider>
        <ScrollRestoreProvider>
          <AppRoutes />
        </ScrollRestoreProvider>
      </ComposeFeedPostProvider>
    </MentionProfileLookupBootstrap>
  )
}

export default function App() {
  return (
    <AppRoot appearance="dark">
      <div className="filmony-theme min-h-dvh">
        <QueryProvider>
          <AuthProvider>
            <TelegramMiniAppStartParamRedirect />
            <AppRoutesGate />
          </AuthProvider>
        </QueryProvider>
        <ScrollToTopFab />
      </div>
    </AppRoot>
  )
}
