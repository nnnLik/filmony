/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_ORIGIN?: string
  readonly VITE_TELEGRAM_BOT_USERNAME?: string
  /** `true` — подключить Eruda (консоль/Network) в прод-сборке; в dev всегда вкл. */
  readonly VITE_ENABLE_ERUDA?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
