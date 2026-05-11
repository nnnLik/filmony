-- Текстовые посты ленты (после movie_card и movie_card_comment: FK user, опционально карточка и комментарий).
INSERT INTO public.feed_post (id, user_id, body, image_url, referenced_movie_card_id, source_comment_id, created_at) VALUES
	 (1, '5f1370d8-8150-49b5-bafe-2d757636d64b'::uuid, 'Короткая заметка для ленты: пересмотрел любимый вестерн, настроение на вечер поймано.', NULL, NULL, NULL, '2026-05-10 18:00:00+03'),
	 (2, '84d5d773-465f-4194-bd78-d94b9f3de41d'::uuid, 'Фикстура: пост без картинки и без ссылки на карточку — проверка чистого текста в ленте.', NULL, NULL, NULL, '2026-05-10 18:05:00+03'),
	 (3, 'f0000001-0000-4000-8000-000000000001'::uuid, 'Общий фильм на всех: коротко о совместном просмотре, без спойлеров.', NULL, 46, NULL, '2026-05-10 18:10:00+03'),
	 (4, 'f0000002-0000-4000-8000-000000000002'::uuid, 'Вынес из обсуждения бобров отдельный пост — финал реально сильнее захода.', NULL, 1, 6, '2026-05-10 18:15:00+03'),
	 (5, 'f0000003-0000-4000-8000-000000000003'::uuid, 'Сегодня только короткие заметки: не люблю спойлерить, но саундтрек заслуживает плейлиста.', NULL, NULL, NULL, '2026-05-10 18:20:00+03'),
	 (6, 'f0000004-0000-4000-8000-000000000004'::uuid, 'Тест с image_url: постер с CDN-плейсхолдером для проверки превью.', 'https://cdn.example/feed/fixture-feedpost-6.png', NULL, NULL, '2026-05-10 18:25:00+03'),
	 (7, 'f0000005-0000-4000-8000-000000000005'::uuid, 'Независимое кино на выходных — кто пойдёт на сеанс вместе?', NULL, 52, NULL, '2026-05-10 18:30:00+03'),
	 (8, 'f0000006-0000-4000-8000-000000000006'::uuid, 'Один сезон за раз держу; сериалы откладываю, зато фильм досмотрел до титров.', NULL, NULL, NULL, '2026-05-10 18:35:00+03')
ON CONFLICT (id) DO UPDATE SET
  user_id = EXCLUDED.user_id,
  body = EXCLUDED.body,
  image_url = EXCLUDED.image_url,
  referenced_movie_card_id = EXCLUDED.referenced_movie_card_id,
  source_comment_id = EXCLUDED.source_comment_id,
  created_at = EXCLUDED.created_at;

SELECT setval(
	pg_get_serial_sequence('public.feed_post', 'id'),
	COALESCE((SELECT MAX(id) FROM public.feed_post), 1),
	true
);
