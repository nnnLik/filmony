import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

import { cloudflare } from "@cloudflare/vite-plugin";

const envDir = path.resolve(import.meta.dirname, '../vars')

const DEFAULT_DEV_API_PROXY_TARGET = 'http://filmony-api.localhost:5080'

function normalizeApiOrigin(raw: string | undefined): string {
  return (raw ?? '')
    .replace(/^\uFEFF/, '')
    .trim()
    .replace(/\/$/, '')
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, envDir, '')
  const clientOrigin = normalizeApiOrigin(env.VITE_API_ORIGIN)
  const proxyTarget = clientOrigin || DEFAULT_DEV_API_PROXY_TARGET

  const proxy = {
    '/api': {
      target: proxyTarget,
      changeOrigin: true,
      secure: false,
    },
  }

  return {
    envDir,
    plugins: [react(), tailwindcss(), cloudflare()],
    build: {
      chunkSizeWarningLimit: 900,
    },
    server: {
      proxy,
      host: true,
      port: 5176,
      allowedHosts: true
    },
    preview: { proxy },
  };
})
