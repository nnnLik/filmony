# Filmony

<p align="center">

[![CI Backend](https://github.com/nnnLik/Filmony/actions/workflows/ci-backend.yml/badge.svg?branch=master)](https://github.com/nnnLik/Filmony/actions/workflows/ci-backend.yml?query=branch%3Amaster)
[![Codecov](https://codecov.io/gh/nnnLik/Filmony/branch/master/graph/badge.svg)](https://codecov.io/gh/nnnLik/Filmony)
[![CI Frontend](https://github.com/nnnLik/Filmony/actions/workflows/ci-frontend.yml/badge.svg?branch=master)](https://github.com/nnnLik/Filmony/actions/workflows/ci-frontend.yml?query=branch%3Amaster)
[![Deploy](https://github.com/nnnLik/Filmony/actions/workflows/deploy.yml/badge.svg)](https://github.com/nnnLik/Filmony/actions/workflows/deploy.yml)

![Python](https://img.shields.io/badge/python-3.13+-3776AB?logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Postgres](https://img.shields.io/badge/Postgres-4169E1?logo=postgresql&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Mini_App-26A5E4?logo=telegram&logoColor=white)

</p>

**Telegram Mini App** для тех, кто не может просто «посмотрел и забыл». Оценивай фильмы, делись впечатлениями с друзьями и собирай свою кино-историю — прямо в Telegram.

<p align="center">
  <img src="docs/assets/screenshots/01-feed.png" alt="Лента подписок — оценки друзей, посты и карточки фильмов" width="240" />
</p>

## Что это

Filmony — личный кино-дневник в формате мини-приложения. Поставил оценку от 1 до 10, наклеил теги настроения и компании — и карточка уже в ленте. Подписываешься на друзей, реагируешь мемами, сравниваешь вкусы. Без лишних вкладок и регистраций: открыл бота — и ты в кино.

## Фичи

### Карточка фильма

Не просто «7 из 10», а контекст: с кем смотрел, какое было настроение до и после, свои теги и полка в коллекции. Карточка живёт дольше, чем одна строчка в заметках.

<p align="center">
  <img src="docs/assets/screenshots/02-create-card.png" alt="Создание карточки — оценка, контекст просмотра и теги" width="240" />
</p>

На деталке — теги, оценки друзей, реакции и комментарии. Место для hot take, когда лента уже пролистана.

<p align="center">
  <img src="docs/assets/screenshots/08-card-detail.png" alt="Деталка карточки — теги, оценки друзей и комментарии" width="240" />
</p>

### Мем-реакции

Не лайки, а настроение: Pepe, котики, кастомные стикеры и прочий хаос. Реагируй так, как фильм того заслужил.

<p align="center">
  <img src="docs/assets/screenshots/03-reactions.png" alt="Мем-реакции на карточке" width="240" />
</p>

### Угадай вкус

Taste Quiz — угадай, как друг оценил фильм. Попал — получи Knowledge badge. Промахнулся — ну, бывает, пересмотришь.

<p align="center">
  <img src="docs/assets/screenshots/04-taste-quiz.png" alt="Итоги раунда «Угадать вкус»" width="240" />
</p>

### Taste Match

Алгоритм находит похожие профили: те, кто смотрит и чувствует примерно как ты. Полезно, когда «что посмотреть?» уже не вопрос, а крик души.

### Профиль и коллекция

Публичный профиль: подписчики, био, любимые фильмы и все карточки на одном экране. Хвастаться можно и цифрами, и полкой.

<p align="center">
  <img src="docs/assets/screenshots/06-passport.png" alt="Профиль — статистика, био и коллекция «Любимое»" width="240" />
</p>

Heatmap просмотров, средний балл, полярность оценок — смотри, как менялся твой вкус и чей ещё рядом.

<p align="center">
  <img src="docs/assets/screenshots/05-profile-stats.png" alt="Статистика профиля — heatmap и инсайты" width="240" />
</p>

### Геймификация

Кино-паспорт со штампами, марафоны, полка с физикой — коллекция, которой хочется хвастаться. Каждый просмотренный фильм — ещё один штамп в паспорте.

### «Позже» и смотрим вместе

Watchlist «Позже» — фильмы в закладки, пока не созреешь. Видно, кто из друзей тоже отложил — можно пригласить на совместный просмотр.

<p align="center">
  <img src="docs/assets/screenshots/07-watchlist.png" alt="Watchlist «Позже» — свои отложенные и фильмы друзей" width="240" />
</p>

### Audio vibe

На карточках — короткий audio vibe: атмосфера фильма в пару секунд, без спойлеров и без «прочитай синопсис».

---

## Для разработчиков

Хочешь поднять локально или покопаться в коде? → [Как запустить / для разработчиков](docs/engineering/getting-started.md)
