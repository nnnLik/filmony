/** Минимальный набор полей для человекочитаемой подписи автора (карточки, комментарии, посты ленты). */
export type AuthorDisplayNameFields = {
  display_name: string | null
  username: string | null
  first_name: string | null
  last_name: string | null
}

export function displayNameFromAuthorFields(a: AuthorDisplayNameFields): string {
  if (a.display_name && a.display_name.trim() !== '') {
    return a.display_name
  }
  if (a.username && a.username.trim() !== '') {
    return `@${a.username}`
  }
  const full = [a.first_name, a.last_name].filter(Boolean).join(' ').trim()
  return full === '' ? 'Автор' : full
}
