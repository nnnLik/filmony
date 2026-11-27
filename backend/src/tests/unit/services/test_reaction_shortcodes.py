from __future__ import annotations

import pytest

from services.text.reaction_shortcodes import (
    SHORTCODE_TOKEN_RE,
    UnknownReactionTokenError,
    allocate_unique_shortcodes,
    derive_shortcode_stem,
    rewrite_reaction_tokens,
)


def test_derive_shortcode_stem_strips_leading_digits_from_pepe_gasp() -> None:
    assert derive_shortcode_stem('reactions/pepe/9137-gasp.png') == 'gasp'


def test_derive_shortcode_stem_keeps_hyphenated_cat_name() -> None:
    assert derive_shortcode_stem('reactions/cats/72953-cat-1.png') == 'cat-1'


def test_derive_shortcode_stem_strips_leading_digits_from_harold() -> None:
    assert derive_shortcode_stem('reactions/meme_pt1/6290-harold.png') == 'harold'


def test_derive_shortcode_stem_keeps_single_letter() -> None:
    assert derive_shortcode_stem('a.png') == 'a'


def test_derive_shortcode_stem_numeric_basename_starts_with_letter() -> None:
    stem = derive_shortcode_stem('123.png')
    assert stem[0].isalpha()
    assert stem in {'r123', 'rx'}


def test_allocate_unique_shortcodes_disambiguates_same_stem_by_category() -> None:
    rows = [
        (1, 'reactions/pepe/9137-gasp.png', 'pepe'),
        (2, 'reactions/cats/100-gasp.png', 'cats'),
    ]
    allocated = allocate_unique_shortcodes(rows)
    assert list(allocated.keys()) == [1, 2]
    assert allocated[1] == 'gasp'
    assert allocated[2] == 'gasp-cats'


def test_rewrite_keeps_known_shortcode_and_unknown_literal() -> None:
    body = 'hello :gasp: and :foo: there'
    rewritten = rewrite_reaction_tokens(
        body,
        id_to_shortcode={12: 'gasp'},
        known_shortcodes={'gasp'},
    )
    assert rewritten == body


def test_rewrite_unicode_legacy_token_to_shortcode() -> None:
    rewritten = rewrite_reaction_tokens(
        'вау ⟦r12⟧ класс',
        id_to_shortcode={12: 'gasp'},
        known_shortcodes={'gasp'},
    )
    assert rewritten == 'вау :gasp: класс'


def test_rewrite_ascii_legacy_token_to_shortcode() -> None:
    rewritten = rewrite_reaction_tokens(
        '[[r12]]',
        id_to_shortcode={12: 'gasp'},
        known_shortcodes={'gasp'},
    )
    assert rewritten == ':gasp:'


def test_rewrite_unknown_legacy_token_raises() -> None:
    with pytest.raises(UnknownReactionTokenError, match='unknown reaction type'):
        rewrite_reaction_tokens(
            '⟦r99⟧',
            id_to_shortcode={12: 'gasp'},
            known_shortcodes={'gasp'},
        )


def test_rewrite_does_not_consume_digit_clock_fragment() -> None:
    body = '10:30:'
    rewritten = rewrite_reaction_tokens(
        body,
        id_to_shortcode={},
        known_shortcodes={'30'},
    )
    assert rewritten == body
    assert SHORTCODE_TOKEN_RE.search(body) is None


def test_rewrite_mixed_known_shortcode_and_leftover_text() -> None:
    rewritten = rewrite_reaction_tokens(
        'start :gasp: leftover text',
        id_to_shortcode={12: 'gasp'},
        known_shortcodes={'gasp'},
    )
    assert rewritten == 'start :gasp: leftover text'
