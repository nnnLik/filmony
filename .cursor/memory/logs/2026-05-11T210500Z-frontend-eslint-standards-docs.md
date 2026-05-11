# Action log — frontend ESLint / typing standards (docs)

- **Timestamp:** 2026-05-11T21:05:00Z
- **Feature slug:** `engineering-docs` (cross-cutting)
- **Action type:** `docs`
- **Summary:** Зафиксированы правила: нулевой ESLint на фронте, без `eslint-disable` для `no-unsafe-*`/`react-hooks/*`, узкие `src/lib` для DTO-хелперов, явные дженерики для `useQuery`, Tailwind-подсказки; ссылки из `.cursor/tech.md`, `project-structure-and-style.md`, `ui-conventions.md`.
- **Files:**
  - `.cursor/rules/frontend-react-telegram-ui-standards.mdc`
  - `.cursor/tech.md`
  - `docs/engineering/project-structure-and-style.md`
  - `docs/frontend/ui-conventions.md`
  - `.cursor/memory/logs/action-log.md`
  - `.cursor/memory/logs/2026-05-11T210500Z-frontend-eslint-standards-docs.md`
- **Verification:** правки только в markdown/mdc; `npm run lint` в `frontend/` не требовался для этих файлов.
