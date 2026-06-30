# Features Folder

This directory is the backlog and source of truth for features that may be implemented later.

Canonical layout:
- `.cursor/features/<feature-slug>/feature.md` for the feature spec
- `.cursor/active/<feature-slug>/` for in-progress execution artifacts
- `docs/features/<feature-slug>.md` for delivered outcome docs

Status rules:
- `planned` means the spec exists under `.cursor/features/...`
- `in_progress` means implementation artifacts exist under `.cursor/active/...`
- `done` means the feature has a published doc in `docs/features/...`
- `blocked` and `cancelled` are recorded in the feature metadata when needed

Machine-readable registry:
- `.cursor/features/index.yaml`

Recommended source:
- copy `.cursor/features/templates/feature-request-template.md`
