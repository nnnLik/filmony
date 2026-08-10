# Profile Header Text Metrics

## Metadata

| Field | Value |
|-------|-------|
| Feature slug | `profile-header-text-metrics` |
| Status | `completed` |
| Stack | frontend |
| Created | 2026-08-11 |

## Problem

Profile header uses a centered large avatar and five bordered metric chips that feel heavy and cluttered on mobile.

## Goal

Left-aligned avatar with identity block on the right; replace chip grid with compact tappable text metrics (Instagram-like two lines).

## Scope

### In scope

- Shared `ProfileHeader` layout: avatar left (~76px), name/badges/slug + metrics on the right
- `ProfileCompactMetrics` rewritten as two text rows (social · library), no bordered chips
- Apply to own (`ProfilePage`) and public (`PublicProfilePage`) profiles
- Bio and primary actions left-aligned below header
- Preserve all existing click handlers and navigation targets

### Out of scope

- Tabs, favorites strip, stats sub-tabs, API changes

## Acceptance criteria

- [x] Avatar appears on the left; name and @slug on the right
- [x] Five metrics shown as plain text, two lines, still clickable
- [x] No bordered metric chip grid on profile header
- [x] Own and public profiles use the same header component
- [x] `npm run lint` and `npm run build` pass
