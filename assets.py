from airtest.core.api import Template


class CachedTemplate(Template):
    def __init__(self, filename):
        super().__init__(filename)
        self.last_position = None


def t(dir, name):
    return CachedTemplate(f'assets/{dir}/{name}.png')


class Buttons:
    __DIR__ = "buttons"
    USE = t(__DIR__, 'use')
    OK = t(__DIR__, 'ok')
    CANCEL = t(__DIR__, 'cancel')
    NEXT = t(__DIR__, 'next')
    START_CRUSADE = t(__DIR__, 'start_crusade')
    START_CHALLENGE = t(__DIR__, 'start_challenge')
    RESTART_CHALLENGE = t(__DIR__, 'restart_challenge')


class Items:
    __DIR__ = "items"
    POTION_SMALL = t(__DIR__, 'potion_small')
    POTION_MEDIUM = t(__DIR__, 'potion_medium')
    POTION_LARGE = t(__DIR__, 'potion_large')
    POTION_TIMELIMIT = t(__DIR__, 'potion_timelimit')
    ARUKU_CHOCOLATE = t(__DIR__, 'aruku_chocolate')
    SHIRO_MARSHMALLOW = t(__DIR__, 'shiro_marshmallow')
    STAR_STONE = t(__DIR__, 'star_stone')
