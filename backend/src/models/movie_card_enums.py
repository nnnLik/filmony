from enum import StrEnum


class CardCompany(StrEnum):
    alone = 'alone'
    partner = 'partner'
    friends = 'friends'
    family = 'family'


class CardMoodBefore(StrEnum):
    relax = 'relax'
    laugh = 'laugh'
    sad = 'sad'
    thrill = 'thrill'


class CardMoodAfter(StrEnum):
    laughed = 'laughed'
    cried = 'cried'
    enjoyed = 'enjoyed'
    tense = 'tense'
    wasted_time = 'wasted_time'
