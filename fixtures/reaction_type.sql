-- Каталог кастомных реакций (плейсхолдер-картинки). Загрузка: scripts/load-fixtures.sh
INSERT INTO reaction_type (id, label, image_url, sort_order, is_active)
VALUES
  (1, 'Интересно', 'https://placehold.co/48x48/png?text=R1', 10, true),
  (2, 'Зачёт', 'https://placehold.co/48x48/png?text=R2', 20, true),
  (3, 'Не зашло', 'https://placehold.co/48x48/png?text=R3', 30, true)
ON CONFLICT (id) DO UPDATE SET
  label = EXCLUDED.label,
  image_url = EXCLUDED.image_url,
  sort_order = EXCLUDED.sort_order,
  is_active = EXCLUDED.is_active;

SELECT setval(
  pg_get_serial_sequence('reaction_type', 'id'),
  GREATEST((SELECT MAX(id) FROM reaction_type), 1)
);
