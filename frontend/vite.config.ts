import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

const envDir = path.resolve(import.meta.dirname, '../vars')

function resolveApiOrigin(raw: string | undefined, fallback: string): string {
  const v = (raw ?? '')
    .replace(/^\uFEFF/, '')
    .trim()
    .replace(/\/$/, '')
  return v || fallback
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, envDir, '')
  const apiOrigin = resolveApiOrigin(env.VITE_API_ORIGIN, 'http://127.0.0.1:8000')

  const proxy = {
    '/api': {
      target: apiOrigin,
      changeOrigin: true,
      secure: false,
    },
  }

  return {
    envDir,
    plugins: [react(), tailwindcss()],
    server: {
      proxy,
      host: true,           // 🔑 Слушаем все интерфейсы
      allowedHosts: true    // 🔑 Отключаем проверку хостов (именно здесь!)
    },
    preview: { proxy },
  }
})
