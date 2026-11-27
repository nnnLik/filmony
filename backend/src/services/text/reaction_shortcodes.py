from __future__ import annotations

import re
from pathlib import Path

SHORTCODE_MAX_LEN = 32
SHORTCODE_TOKEN_RE = re.compile(r':([a-z][a-z0-9_+-]{0,31}):')
LEGACY_UNICODE_REACTION_RE = re.compile(r'⟦r(\d+)⟧')
LEGACY_ASCII_REACTION_RE = re.compile(r'\[\[r(\d+)\]\]')

_LEADING_DIGITS_HYPHEN_RE = re.compile(r'^\d+-')
_ALLOWED_SHORTCODE_CHARS_RE = re.compile(r'[^a-z0-9_+-]')
_TOKEN_SCAN_RE = re.compile(
    r':([a-z][a-z0-9_+-]{0,31}):|⟦r(\d+)⟧|\[\[r(\d+)\]\]',
)


class UnknownReactionTokenError(ValueError):
    """Legacy reaction token id is not in the provided mapping."""


def derive_shortcode_stem(asset_key: str) -> str:
    """Basename without extension, strip leading `digits-`, keep [a-z0-9_+-], must start with a letter.

    If empty or starts with non-letter, prefix `r` (if still bad, use `rx`). Truncate to
    SHORTCODE_MAX_LEN. Lowercase.
    """
    stem = Path(asset_key).stem.lower()
    stem = _LEADING_DIGITS_HYPHEN_RE.sub('', stem, count=1)
    stem = _ALLOWED_SHORTCODE_CHARS_RE.sub('', stem)
    return _ensure_letter_prefix(stem)


def allocate_unique_shortcodes(rows: list[tuple[int, str, str]]) -> dict[int, str]:
    """Assign unique shortcodes for (id, asset_key, category_slug) rows.

    First try stem, then `{stem}-{category_slug}` truncated to 32 starting with letter,
    then `{stem}-{id}`. Keep uniqueness in a set. Preserve insertion order of ids.
    """
    used: set[str] = set()
    allocated: dict[int, str] = {}
    for row_id, asset_key, category_slug in rows:
        stem = derive_shortcode_stem(asset_key)
        chosen = _first_unused_shortcode(stem, category_slug, row_id, used)
        used.add(chosen)
        allocated[row_id] = chosen
    return allocated


def rewrite_reaction_tokens(
    body: str,
    *,
    id_to_shortcode: dict[int, str],
    known_shortcodes: set[str],
) -> str:
    """Replace legacy reaction tokens with `:shortcode:` forms, left-to-right.

    `:name:` is kept when `name` is known and left literal when unknown. Legacy
    `⟦r{id}⟧` / `[[r{id}]]` map through `id_to_shortcode` or raise
    UnknownReactionTokenError.
    """
    pieces: list[str] = []
    last = 0
    for match in _TOKEN_SCAN_RE.finditer(body):
        pieces.append(body[last : match.start()])
        pieces.append(
            _rewrite_one_match(
                match,
                id_to_shortcode=id_to_shortcode,
                known_shortcodes=known_shortcodes,
            ),
        )
        last = match.end()
    pieces.append(body[last:])
    return ''.join(pieces)


def _ensure_letter_prefix(stem: str) -> str:
    if not stem or not stem[0].isalpha():
        stem = f'r{stem}'
    if not stem or not stem[0].isalpha():
        stem = 'rx'
    return stem[:SHORTCODE_MAX_LEN]


def _fit_shortcode(raw: str) -> str:
    text = _ALLOWED_SHORTCODE_CHARS_RE.sub('', raw.lower())
    return _ensure_letter_prefix(text)


def _first_unused_shortcode(
    stem: str,
    category_slug: str,
    row_id: int,
    used: set[str],
) -> str:
    for candidate in (
        stem,
        _fit_shortcode(f'{stem}-{category_slug}'),
        _fit_shortcode(f'{stem}-{row_id}'),
    ):
        if candidate not in used:
            return candidate
    suffix = f'-{row_id}'
    stem_budget = max(1, SHORTCODE_MAX_LEN - len(suffix))
    fallback = _fit_shortcode(f'{stem[:stem_budget]}{suffix}')
    if fallback not in used:
        return fallback
    raise RuntimeError(f'unable to allocate unique shortcode for id={row_id}')


def _rewrite_one_match(
    match: re.Match[str],
    *,
    id_to_shortcode: dict[int, str],
    known_shortcodes: set[str],
) -> str:
    name = match.group(1)
    if name is not None:
        if name in known_shortcodes:
            return f':{name}:'
        return match.group(0)

    raw_id = match.group(2) if match.group(2) is not None else match.group(3)
    reaction_id = int(raw_id)
    shortcode = id_to_shortcode.get(reaction_id)
    if shortcode is None:
        raise UnknownReactionTokenError('unknown reaction type')
    return f':{shortcode}:'
