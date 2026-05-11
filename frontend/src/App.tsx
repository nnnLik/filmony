import '@telegram-apps/telegram-ui/dist/styles.css'

import { AppRoot } from '@telegram-apps/telegram-ui'

import { TelegramMiniAppStartParamRedirect } from './navigation/TelegramMiniAppStartParamRedirect'
import { AuthProvider } from './auth/AuthProvider'
import { MentionProfileLookupBootstrap } from './components/MentionProfileLookupBootstrap'
import { ComposeFeedPostProvider } from './compose/ComposeFeedPostProvider'
import { ScrollToTopFab } from './components/navigation/ScrollToTopFab'
import { QueryProvider } from './providers/QueryProvider'
import { AppRoutes } from './routes'

export default function App() {
  return (
    <AppRoot appearance="dark">
      <div className="filmony-theme min-h-dvh">
        <TelegramMiniAppStartParamRedirect />
        <QueryProvider>
          <AuthProvider>
            <MentionProfileLookupBootstrap>
              <ComposeFeedPostProvider>
                <AppRoutes />
              </ComposeFeedPostProvider>
            </MentionProfileLookupBootstrap>
          </AuthProvider>
        </QueryProvider>
        <ScrollToTopFab />
      </div>
    </AppRoot>
  )
}
