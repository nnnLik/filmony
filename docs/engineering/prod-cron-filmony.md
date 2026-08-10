# Filmony production cron (homelab)

**Host:** `homelab` (`/opt/filmony`)  
**Timezone:** UTC

## Active jobs

| Schedule (UTC) | Command | Purpose |
|----------------|---------|---------|
| `0 */6 * * *` | `backup-all-databases.sh` | Homelab DB backups |
| `0 10 * * 1` | `tasks.personal_digest.send_weekly_personal_digests` | Weekly personal + friends Telegram digest |
| `0 10 1 * *` | `tasks.personal_digest.send_monthly_personal_digests` | Monthly personal stats Telegram teaser |
| `0 4 * * *` | `tasks.achievement_rarity.recalculate_achievement_rarity` | Achievement rarity snapshots |
| `*/15 * * * *` | `tasks.watch_party.end_expired_watch_parties` | End watch parties past TTL |

## Logs

- `/var/log/filmony-weekly-digest.log`
- `/var/log/filmony-monthly-digest.log`
- `/var/log/filmony-achievement-rarity.log`
- `/opt/homelab-pg-backup.log`

## Manual invoke

```bash
ssh homelab 'cd /opt/filmony && docker compose exec -T -w /opt/app filmony-celery-worker celery -A celery_app call tasks.personal_digest.send_weekly_personal_digests'
ssh homelab 'cd /opt/filmony && docker compose exec -T -w /opt/app filmony-celery-worker celery -A celery_app call tasks.personal_digest.send_monthly_personal_digests'
```

## Removed (2026-08-08)

- Subscribed activity digest (6h)
- Weekly controversy standalone digest
- Oscar seed cron
- Film award badges sync cron

Design: [personal-digest-redesign spec](../superpowers/specs/2026-08-08-personal-digest-redesign-design.md)
