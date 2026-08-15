# Production PostgreSQL ownership

**Host:** homelab Postgres (`homelab-postgres`, database `filmony`)

Alembic runs as app role **`filmony`**. Legacy tables were created under **`homelab`**, so `ALTER TABLE` migrations failed with `must be owner of table film`.

## One-time fix (applied 2026-08-15)

As superuser `homelab`:

```sql
DO $$
DECLARE r record;
BEGIN
  FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tableowner = 'homelab'
  LOOP
    EXECUTE format('ALTER TABLE public.%I OWNER TO filmony', r.tablename);
  END LOOP;
  FOR r IN
    SELECT c.relname AS seq_name
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    JOIN pg_roles ro ON ro.oid = c.relowner
    WHERE c.relkind = 'S' AND n.nspname = 'public' AND ro.rolname = 'homelab'
  LOOP
    EXECUTE format('ALTER SEQUENCE public.%I OWNER TO filmony', r.seq_name);
  END LOOP;
END $$;
```

Verify:

```sql
SELECT tablename, tableowner FROM pg_tables
WHERE schemaname = 'public' AND tablename IN ('film', 'user')
ORDER BY 1;
```

Both should show `filmony`.

## New environments

If tables are restored or created as `homelab`, rerun the block above before `alembic upgrade head`.
