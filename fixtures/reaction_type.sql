-- Каталог кастомных реакций. Вкладки в API строятся по `category_slug` (см. backend/src/const/reaction_packs.py).
-- NULL slug → попадут во вкладку «Без группы»; для демо ниже заданы три разные группы + placehold.co (RustFS не обязателен).
INSERT INTO reaction_type (id, label, image_url, sort_order, is_active, category_slug, asset_key)
VALUES
  (1, 'Интересно', 'https://placehold.co/48x48/png?text=R1', 10, true, 'pepe', NULL),
  (2, 'Зачёт', 'https://placehold.co/48x48/png?text=R2', 20, true, 'cats', NULL),
  (3, 'Не зашло', 'https://placehold.co/48x48/png?text=R3', 30, true, 'meme_pt1', NULL)
ON CONFLICT (id) DO UPDATE SET
  label = EXCLUDED.label,
  image_url = EXCLUDED.image_url,
  sort_order = EXCLUDED.sort_order,
  is_active = EXCLUDED.is_active,
  category_slug = EXCLUDED.category_slug,
  asset_key = EXCLUDED.asset_key;

SELECT setval(
  pg_get_serial_sequence('reaction_type', 'id'),
  GREATEST((SELECT MAX(id) FROM reaction_type), 1)
);
