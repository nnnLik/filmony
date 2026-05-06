export interface Movie {
  id: string
  title: string
  year: number
  poster: string
  rating: number | null
  company: 'alone' | 'friends' | null
  moodBefore: 'happy' | 'tired' | null
  moodAfter: 'laughed' | 'cried' | null
  customTags: string[]
  friendRatings: FriendRating[]
  comments: Comment[]
}

export interface FriendRating {
  id: string
  name: string
  avatar: string
  rating: number
}

export interface Comment {
  id: string
  userId: string
  userName: string
  avatar: string
  text: string
  likes: number
  liked: boolean
}

export interface User {
  id: string
  name: string
  avatar: string
  friendsCount: number
  movies: Movie[]
}
