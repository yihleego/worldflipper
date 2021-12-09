from airtest.core.api import Template


class T(Template):
    def __init__(self, dir, name):
        filename = f'assets/{dir}/{name}.png'
        super().__init__(filename)
        self.dir = dir
        self.name = name
        self.last_position = None


def bt(name):
    return T('buttons', name)


def it(name):
    return T('items', name)


def et(name):
    return T('events', name)


def tt(name):
    return T('tips', name)


class Buttons:
    HOME = bt('home')
    HOME_ACTIVE = bt('home_active')
    BOSS = bt('boss')
    EVENT = bt('event')
    USE = bt('use')
    OK = bt('ok')
    CANCEL = bt('cancel')
    NEXT = bt('next')
    BACK = bt('back')
    CRUSADE_START = bt('crusade_start')
    CHALLENGE_START = bt('challenge_start')
    CHALLENGE_RESTART = bt('challenge_restart')
    GACHA_PULL = bt('gacha_pull')
    GACHA_RESET = bt('gacha_reset')


class Items:
    POTION_SMALL = it('potion_small')
    POTION_MEDIUM = it('potion_medium')
    POTION_LARGE = it('potion_large')
    POTION_TIMELIMIT = it('potion_timelimit')
    ARUKU_CHOCOLATE = it('aruku_chocolate')
    SHIRO_MARSHMALLOW = it('shiro_marshmallow')
    LODESTAR_BEAD = it('lodestar_bead')


class Events:
    BATTLEFIELD_EVENT = et('battlefield_event')
    BATTLEFIELD_HELL = et('battlefield_hell')
    BATTLEFIELD_GACHA_ENTRANCE = et('battlefield_gacha_entrance')


class Tips:
    NO_TOKEN = tt('no_token')
    QUEST_RESULT = tt('quest_result')


def templates(clazz):
    ts = []
    for attr in dir(clazz):
        if not attr.startswith('_'):
            v = getattr(clazz, attr)
            if isinstance(v, T):
                ts.append(v)
    return ts
