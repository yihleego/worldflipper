from airtest.core.api import Template


def t(dir, name):
    return CachedTemplate(dir, name)


class CachedTemplate(Template):
    def __init__(self, dir, name):
        filename = f'assets/{dir}/{name}.png'
        super().__init__(filename)
        self.dir = dir
        self.name = name
        self.last_position = None


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

    @staticmethod
    def templates():
        return [
            Items.POTION_SMALL,
            Items.POTION_MEDIUM,
            Items.POTION_LARGE,
            Items.POTION_TIMELIMIT,
            Items.ARUKU_CHOCOLATE,
            Items.SHIRO_MARSHMALLOW,
            Items.STAR_STONE,
        ]
