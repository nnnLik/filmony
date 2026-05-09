# Action log fragment

- **Timestamp:** 2026-05-10T18:00:00Z
- **Feature slug:** reaction-asset-url-frontend
- **Action type:** code
- **Summary:** Исправлена подгрузка картинок реакций в Mini App: относительные `/api/reactions/asset/...` теперь префиксятся `VITE_API_ORIGIN` через общий `resolveApiUrl`.
- **Files:** `frontend/src/api/client.ts`, `frontend/src/lib/resolveApiMediaUrl.ts`
- **Verification:** `cd frontend && npm run build` (exit 0)
