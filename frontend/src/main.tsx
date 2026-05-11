import { init, isTMA } from '@telegram-apps/sdk'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import App from './App'
import './index.css'

if (isTMA()) {
  init()
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
