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
    PAUSE = bt('pause')
    CRUSADE_START = bt('crusade_start')
    CHALLENGE_START = bt('challenge_start')
    CHALLENGE_RESTART = bt('challenge_restart')
    GACHA_PULL = bt('gacha_pull')
    GACHA_RESET = bt('gacha_reset')
    BELL = bt('bell')
    JOIN = bt('join')
    NOT_READY = bt('not_ready')
    ROOM_BACK = bt('room_back')
    ROOM_EXIT = bt('room_exit')


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
    QUEST_RESULT = tt('quest_result')
    GACHA_NO_TOKEN = tt('gacha_no_token')
    GACHA_NO_CHANCE = tt('gacha_no_chance')


def templates(clazz):
    ts = []
    for attr in dir(clazz):
        if not attr.startswith('_'):
            v = getattr(clazz, attr)
            if isinstance(v, T):
                ts.append(v)
    return ts
