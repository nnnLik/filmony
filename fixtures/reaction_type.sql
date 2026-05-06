-- Каталог кастомных реакций. Вкладки по `category_slug` (backend/src/const/reaction_packs.py).
-- Картинки: `asset_key` = ключ в RustFS после `make sync-reactions-rustfs` (`reactions/<slug>/<filename>` как в emoji/).
-- Ответ API строит URL как REACTION_MEDIA_PUBLIC_BASE_URL + '/' + asset_key. `image_url` — только fallback в БД.
INSERT INTO reaction_type (id, label, image_url, sort_order, is_active, category_slug, asset_key)
VALUES
  (1, 'Интересно', 'reactions/pepe/9137-gasp.png', 10, true, 'pepe', 'reactions/pepe/9137-gasp.png'),
  (2, 'Зачёт', 'reactions/cats/72953-cat-1.png', 20, true, 'cats', 'reactions/cats/72953-cat-1.png'),
  (3, 'Не зашло', 'reactions/meme_pt1/6290-harold.png', 30, true, 'meme_pt1', 'reactions/meme_pt1/6290-harold.png')
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
