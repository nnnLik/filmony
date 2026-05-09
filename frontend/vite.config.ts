import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

import { cloudflare } from "@cloudflare/vite-plugin";

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
  const apiOrigin = resolveApiOrigin(env.VITE_API_ORIGIN, 'http://127.0.0.1:8888')

  const proxy = {
    '/api': {
      target: apiOrigin,
      changeOrigin: true,
      secure: false,
    },
  }

  return {
    envDir,
    plugins: [react(), tailwindcss(), cloudflare()],
    server: {
      proxy,
      host: true,
      port: 5176,
      allowedHosts: true
    },
    preview: { proxy },
  };
})