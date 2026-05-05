import { init, isTMA } from '@telegram-apps/sdk'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'

/** `init()` вызывает retrieveLaunchParams(); вне Telegram это падает до mount. */
if (isTMA()) {
  init()
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
