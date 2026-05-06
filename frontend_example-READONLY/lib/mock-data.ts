import { Movie, User } from './types'

export const mockMovies: Movie[] = [
  {
    id: '1',
    title: 'Оппенгеймер',
    year: 2023,
    poster: 'https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=300&h=450&fit=crop',
    rating: 9,
    company: 'friends',
    moodBefore: 'happy',
    moodAfter: 'cried',
    customTags: ['Шедевр', 'Ноланомания'],
    friendRatings: [
      { id: '1', name: 'Аня', avatar: 'https://i.pravatar.cc/100?img=1', rating: 10 },
      { id: '2', name: 'Максим', avatar: 'https://i.pravatar.cc/100?img=2', rating: 8 },
      { id: '3', name: 'Катя', avatar: 'https://i.pravatar.cc/100?img=3', rating: 9 },
    ],
    comments: [
      { id: '1', userId: '1', userName: 'Аня', avatar: 'https://i.pravatar.cc/100?img=1', text: 'Киллиан — гений! Лучшая роль года.', likes: 12, liked: true },
      { id: '2', userId: '2', userName: 'Максим', avatar: 'https://i.pravatar.cc/100?img=2', text: 'Затянуто местами, но финал оправдывает всё.', likes: 5, liked: false },
    ],
  },
  {
    id: '2',
    title: 'Барби',
    year: 2023,
    poster: 'https://images.unsplash.com/photo-1509281373149-e957c6296406?w=300&h=450&fit=crop',
    rating: 7,
    company: 'friends',
    moodBefore: 'tired',
    moodAfter: 'laughed',
    customTags: ['Фемповестка', 'Яркий'],
    friendRatings: [
      { id: '1', name: 'Аня', avatar: 'https://i.pravatar.cc/100?img=1', rating: 9 },
      { id: '4', name: 'Дима', avatar: 'https://i.pravatar.cc/100?img=4', rating: 6 },
    ],
    comments: [
      { id: '3', userId: '1', userName: 'Аня', avatar: 'https://i.pravatar.cc/100?img=1', text: 'Грета Гервиг сделала невозможное!', likes: 8, liked: false },
    ],
  },
  {
    id: '3',
    title: 'Дюна: Часть вторая',
    year: 2024,
    poster: 'https://images.unsplash.com/photo-1534447677768-be436bb09401?w=300&h=450&fit=crop',
    rating: 10,
    company: 'alone',
    moodBefore: 'happy',
    moodAfter: 'cried',
    customTags: ['Эпик', 'Визуал', 'Циммер'],
    friendRatings: [
      { id: '2', name: 'Максим', avatar: 'https://i.pravatar.cc/100?img=2', rating: 10 },
      { id: '3', name: 'Катя', avatar: 'https://i.pravatar.cc/100?img=3', rating: 9 },
      { id: '5', name: 'Олег', avatar: 'https://i.pravatar.cc/100?img=5', rating: 10 },
    ],
    comments: [],
  },
  {
    id: '4',
    title: 'Бедные-несчастные',
    year: 2023,
    poster: 'https://images.unsplash.com/photo-1518676590629-3dcbd9c5a5c9?w=300&h=450&fit=crop',
    rating: 8,
    company: 'alone',
    moodBefore: 'tired',
    moodAfter: 'laughed',
    customTags: ['Артхаус', 'Эмма Стоун'],
    friendRatings: [
      { id: '1', name: 'Аня', avatar: 'https://i.pravatar.cc/100?img=1', rating: 9 },
    ],
    comments: [
      { id: '4', userId: '1', userName: 'Аня', avatar: 'https://i.pravatar.cc/100?img=1', text: 'Визуально потрясающе, но не для всех.', likes: 3, liked: false },
    ],
  },
  {
    id: '5',
    title: 'Убийцы цветочной луны',
    year: 2023,
    poster: 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=300&h=450&fit=crop',
    rating: 8,
    company: 'alone',
    moodBefore: 'happy',
    moodAfter: 'cried',
    customTags: ['Скорсезе', 'ДиКаприо'],
    friendRatings: [
      { id: '2', name: 'Максим', avatar: 'https://i.pravatar.cc/100?img=2', rating: 7 },
      { id: '5', name: 'Олег', avatar: 'https://i.pravatar.cc/100?img=5', rating: 8 },
    ],
    comments: [],
  },
]

export const currentUser: User = {
  id: 'current',
  name: 'Алексей',
  avatar: 'https://i.pravatar.cc/100?img=8',
  friendsCount: 24,
  movies: mockMovies,
}

export const friends: User[] = [
  {
    id: '1',
    name: 'Аня',
    avatar: 'https://i.pravatar.cc/100?img=1',
    friendsCount: 18,
    movies: mockMovies.slice(0, 3),
  },
  {
    id: '2',
    name: 'Максим',
    avatar: 'https://i.pravatar.cc/100?img=2',
    friendsCount: 32,
    movies: mockMovies.slice(1, 4),
  },
]
