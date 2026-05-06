# Movie card custom reactions

## Goal
- Реакции на **карточки фильмов** и на **комментарии** с помощью **кастомных картинок** из каталога, задаваемого продуктом/админом. Стандартные emoji мессенджеров как единственный набор **не** используются.

## Scope
- Каталог реакций в БД (изображение по URL или ключу хранилища, порядок, активность).
- Пользователь выбирает только из каталога; применимо к **своим и чужим** карточкам и комментариям (политика self-react уточняется в сервисе).
- MVP-логика: рекомендуется **одна реакция пользователя на цель** с **toggle** при повторном выборе того же типа.

## Relations
- Заменяет продуктовый смысл «лайков / emoji» из `.cursor/features/006-comments-and-likes.md`.
- Уведомления в Telegram о реакциях — см. `docs/features/telegram-engagement-notifications.md` (после появления событий).

## References
- `.cursor/features/movie-card-custom-reactions/feature.md`
- `.cursor/active/movie-card-custom-reactions/plan.md`
