# Action log entry

- **Timestamp:** 2026-05-08
- **Feature slug:** `production-readiness`
- **Action type:** code
- **Summary:** Prod/dev nginx (`deploy/nginx/*.conf`), `compose.prod.yml` без inline env для Postgres/RustFS/backend, образ `rustfs:1.0.0-beta.1`, dev `compose.yml` с nginx :8888 и без порта backend на хосте; обновлены README, `vars/.env.*`, vite fallback, доки.
- **Files:** `compose.yml`, `compose.prod.yml`, `deploy/nginx/dev.conf`, `deploy/nginx/prod.conf`, `vars/.env.production.example`, `vars/.env.example`, `vars/.env.development`, `frontend/vite.config.ts`, `README.md`, `docs/features/telegram-user-base.md`, `.cursor/features/production-readiness/feature.md`
- **Verification:** рекомендуется `docker compose -f compose.yml config` и смоук через http://127.0.0.1:8888 после `make start` + `npm run dev`.
