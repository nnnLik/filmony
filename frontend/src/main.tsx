import { init, isTMA } from '@telegram-apps/sdk'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import App from './App'
import './index.css'

if (import.meta.env.DEV || import.meta.env.VITE_ENABLE_ERUDA === 'true') {
  void import('eruda').then((m) => {
    m.default.init()
  })
}

/** `init()` вызывает retrieveLaunchParams(); вне Telegram это падает до mount. */
if (isTMA()) {
  init()
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)
