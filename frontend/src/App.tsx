import '@telegram-apps/telegram-ui/dist/styles.css'

import { isMiniAppDark } from '@telegram-apps/sdk'
import { useSignal } from '@telegram-apps/sdk-react'
import { AppRoot } from '@telegram-apps/telegram-ui'

import { AuthProvider } from './auth/AuthProvider'
import { AppRoutes } from './routes'

export default function App() {
  const isDark = useSignal(isMiniAppDark)
  const appearance = isDark ?? true ? 'dark' : 'light'

  return (
    <AppRoot appearance={appearance}>
      <AuthProvider>
        <div className="min-h-dvh">
          <AppRoutes />
        </div>
      </AuthProvider>
    </AppRoot>
  )
}
