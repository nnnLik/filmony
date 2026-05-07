"""Нормализация URL для внешних HTTP-клиентов (Telegram sendPhoto, браузер)."""

from __future__ import annotations


def normalize_absolute_http_url(url: str | None) -> str | None:
    """Приводит строку к абсолютному http(s)-URL или возвращает None.

    Kinopoisk и др. часто отдают постеры как ``//host/path`` — без схемы такие URL
    не проходят проверку ``startswith('https://')`` и не уходят в ``sendPhoto``.
    """
    if url is None:
        return None
    s = url.strip()
    if not s:
        return None
    lower = s.lower()
    if lower.startswith('//'):
        return 'https:' + s
    if lower.startswith(('http://', 'https://')):
        return s
    return None
