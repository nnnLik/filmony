import '@telegram-apps/telegram-ui/dist/styles.css'

import { AppRoot } from '@telegram-apps/telegram-ui'

import { AuthProvider } from './auth/AuthProvider'
import { AppRoutes } from './routes'

export default function App() {
  return (
    <AppRoot appearance="dark">
      <div className="filmony-theme min-h-dvh">
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </div>
    </AppRoot>
  )
}
