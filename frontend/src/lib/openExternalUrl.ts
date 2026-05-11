/** Opens an https URL in the Telegram client when embedded, otherwise in a new tab. */
export function openExternalUrl(url: string): void {
  const wa = window.Telegram?.WebApp
  if (wa?.openLink) {
    wa.openLink(url)
    return
  }
  window.open(url, '_blank', 'noopener,noreferrer')
}

export function kinopoiskTitleUrl(kinopoiskId: number): string {
  return `https://www.kinopoisk.ru/film/${kinopoiskId}/`
}
