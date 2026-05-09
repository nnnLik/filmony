/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_ORIGIN?: string
  readonly VITE_TELEGRAM_BOT_USERNAME?: string
  readonly VITE_ENABLE_ERUDA?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
