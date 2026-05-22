-- Минимальная связка RAWG: одна строка game + один catalog_item (общая для нескольких user_card ниже по списку).
INSERT INTO game (id, rawg_id, slug, name, released, background_image)
VALUES (
  9900101,
  991234567,
  'fixture-qa-shared-rawg-title',
  'Fixture QA RAWG Shared Title',
  '2024-06-01',
  'https://cdn.example/game/fixture-rawg-991234567-cover.jpg'
)
ON CONFLICT (rawg_id) DO UPDATE SET
  slug = EXCLUDED.slug,
  name = EXCLUDED.name,
  released = EXCLUDED.released,
  background_image = EXCLUDED.background_image;

INSERT INTO catalog_item (
  provider,
  external_id,
  film_id,
  game_id,
  created_at
)
VALUES (
  'rawg'::varchar,
  '991234567'::varchar,
  NULL,
  9900101,
  '2026-05-22 12:05:01'
)
ON CONFLICT ON CONSTRAINT uq_catalog_item_provider_external DO UPDATE SET
  game_id = EXCLUDED.game_id,
  film_id = EXCLUDED.film_id;
