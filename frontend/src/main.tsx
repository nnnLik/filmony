import { init, isTMA } from '@telegram-apps/sdk'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router'

import App from './App'
import { applyEarlyStartParamPathReplace } from './lib/miniAppCardDeepLink'
import './index.css'

if (isTMA()) {
  init()
  applyEarlyStartParamPathReplace()
}

if (import.meta.env.DEV) {
  void import('eruda')
    .then((m) => {
      m.default.init()
    })
    .catch(() => {
      console.error('Failed to load Eruda')
    })
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)
