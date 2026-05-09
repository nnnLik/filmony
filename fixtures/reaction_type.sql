-- Каталог кастомных реакций. Вкладки по `category_slug` (backend/src/const/reaction_packs.py).
-- Картинки: `asset_key` = ключ в RustFS после `make sync-reactions-rustfs` (`reactions/<slug>/<filename>` как в emoji/).
-- Ответ API строит URL как REACTION_MEDIA_PUBLIC_BASE_URL + '/' + asset_key. `image_url` — fallback в БД.
INSERT INTO public.reaction_type (id, image_url, category_slug, asset_key)
VALUES
  (1, 'reactions/pepe/9137-gasp.png', 'pepe', 'reactions/pepe/9137-gasp.png'),
  (2, 'reactions/cats/72953-cat-1.png', 'cats', 'reactions/cats/72953-cat-1.png'),
  (3, 'reactions/meme_pt1/6290-harold.png', 'meme_pt1', 'reactions/meme_pt1/6290-harold.png')
ON CONFLICT (id) DO UPDATE SET
  image_url = EXCLUDED.image_url,
  category_slug = EXCLUDED.category_slug,
  asset_key = EXCLUDED.asset_key;

SELECT setval(
  pg_get_serial_sequence('reaction_type', 'id'),
  GREATEST((SELECT MAX(id) FROM reaction_type), 1)
);
