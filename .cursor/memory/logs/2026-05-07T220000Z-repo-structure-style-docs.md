# 2026-05-07T22:00:00Z

- Feature slug: `repo-structure-style`
- Action type: docs
- Summary: Инженерный гайд по структуре репозитория и стилю; выравнивание `.cursor/tech.md`, README, Ruff `target-version` с реальным compose; мелкие правки импортов фронта и докстринга `services.subscriptions`.
- Files:
  - `docs/engineering/project-structure-and-style.md`
  - `.cursor/tech.md`
  - `README.md`
  - `backend/pyproject.toml`
  - `backend/src/services/subscriptions/__init__.py`
  - `backend/src/services/reactions/list_reaction_catalog.py`
  - `frontend/src/routes.tsx`
  - `frontend/src/main.tsx`
  - `.cursor/memory/logs/2026-05-07T220000Z-repo-structure-style-docs.md`
  - `.cursor/memory/logs/action-log.md`
- Verification: `make backend-lint`; `cd frontend && npm run lint` (ожидается после поднятого compose для backend)
- Links:
  - План: `.cursor/plans/repo_structure_style_audit_73126119.plan.md` (не редактировался в ходе выполнения)
