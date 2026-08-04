---
name: git-commit-messages
description: >-
  Drafts git commit messages in this repo's Conventional Commits format.
  Use when the user asks to commit, write a commit message, or review staged
  changes before a git commit.
---

# Git Commit Messages

Message **format** follows [`.cursor/rules/git-commit-messages.mdc`](../../rules/git-commit-messages.mdc). **Git safety** (staging, HEREDOC, no amend unless asked, no secrets) follows the user's Cursor git rules — this skill covers message drafting only.

## When to use

- User asks to **commit**, **git commit**, or **write a commit message**
- User wants a message reviewed before committing
- Ambient context: user is finishing work and mentions committing

## Steps

1. **Inspect changes** (parallel when possible): `git status`, `git diff` (staged + unstaged), `git log -5` for tone/type patterns.
2. **Classify** the change: pick one primary `type`; use optional `scope` when area is clear (`frontend`, `backend`, etc.).
3. **Draft subject**: imperative, English by default, no trailing period, ~72 chars.
4. **Multiple features or files**: add a body with `-` bullets — one short line per distinct change.
5. **Present** the draft to the user. **Commit only if explicitly asked** — then stage relevant files and use HEREDOC:

```bash
git commit -m "$(cat <<'EOF'
feat(scope): short imperative summary

- first change
- second change

EOF
)"
```

Do not commit `.env`, credentials, or other secrets. Do not push unless asked.

## Examples

**Single change**

```
fix(backend): validate gamification metadata before persist
```

**Multi-change (prefer body bullets)**

```
feat(frontend): director profile rated-films section

- wire list API and pagination
- add loading, empty, and error states
- align tab layout with existing profile sections
```

**Chore + docs in one commit**

```
chore: align Makefile backend-test targets with docker compose

- document make backend-test-one in tech.md
- remove duplicate pytest invocation
```

**When subject must stay one line** (small related edits only):

```
refactor(backend): extract film gamification DTO mapping - simplify tests
```

Prefer splitting unrelated types (`feat` + `fix`) into separate commits when the user allows multiple commits.
