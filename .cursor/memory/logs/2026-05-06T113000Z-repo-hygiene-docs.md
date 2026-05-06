# 2026-05-06T11:30:00Z

- Feature slug: `repo-hygiene`
- Action type: docs
- Summary: Корневой `.gitignore` (Python, Node, IDE, env), `README.md`, шаблон `vars/.env.example`.
- Files:
  - `.gitignore`
  - `README.md`
  - `vars/.env.example`
- Verification: шаблон без секретов; `vars/.env.*` игнорируются с исключением `.env.example`.
