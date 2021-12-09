import logging
from abc import ABC

from airtest.core.api import Template, connect_device, exists, touch, swipe, sleep
from worldflipper.assets import Buttons, Items, Events, Tips, templates


class Task(ABC):
    def __init__(self, uri, type, config=None, loop=True):
        self.logger = logging.getLogger('worldflipper')
        self.uri = uri
        self.type = type
        self.loop = loop
        self.status = TaskStatus.INIT
        self.device = None
        self.config = Config(config or {}, self.logger)

    def execute(self):
        raise NotImplementedError

    def pre_execute(self):
        pass

    def post_execute(self):
        pass

    def break_loop(self):
        self.loop = False

    def start(self):
        self.status = TaskStatus.RUNNING
        self.device = connect_device(self.uri)
        try:
            if not self.config.skip_pre:
                self.pre_execute()
            if self.loop:
                while self.is_running() and self.loop:
                    self.execute()
            else:
                self.execute()
            if not self.config.skip_post:
                self.post_execute()
            self.status = TaskStatus.SUCCESS
        except:
            self.status = TaskStatus.FAILED
            self.logger.error('Failed to start', exc_info=True)

    def stop(self):
        if not self.is_terminated():
            self.status = TaskStatus.INTERRUPTED

    def is_running(self):
        return self.status == TaskStatus.RUNNING

    def is_terminated(self):
        return self.status == TaskStatus.SUCCESS or self.status == TaskStatus.FAILED

    def click(self, v, wait_time=0.0, retries=0, cache=False):
        if not self.is_running():
            return
        self.logger.info('Try to click %s', v)
        try:
            p = None
            if isinstance(v, Template):
                for i in range(retries + 1):
                    if cache:
                        if not v.last_position:
                            v.last_position = exists(v, device=self.device)
                        if v.last_position:
                            p = touch(v.last_position, device=self.device)
                    else:
                        p = exists(v, device=self.device)
                        if p:
                            touch(p, device=self.device)
                    if p:
                        break
            elif isinstance(v, tuple):
                p = touch(v, device=self.device)
            if wait_time > 0 and p:
                sleep(wait_time)
            return p
        except:
            self.logger.error('Failed to click', exc_info=True)

    def exists(self, v, wait_time=0.0):
        if not self.is_running():
            return
        try:
            p = exists(v, device=self.device)
            if wait_time > 0 and p:
                sleep(wait_time)
            return p
        except:
            self.logger.error('Failed to exists', exc_info=True)

    def swipe(self, v1, v2=None, vector=None, wait_time=0.0):
        if not self.is_running():
            return
        if not v2 and not vector:
            return
        try:
            p = swipe(v1=v1, v2=v2, vector=vector, device=self.device)
            if wait_time > 0 and p:
                sleep(wait_time)
            return p
        except:
            self.logger.error('Failed to swipe', exc_info=True)

    def click_any(self, v: list, wait_time=0.0, retries=0, cache=False):
        for i in v:
            p = self.click(i, wait_time, retries, cache)
            if p:
                return p

    def exists_any(self, v: list, wait_time=0.0):
        for i in v:
            p = self.exists(i, wait_time)
            if p:
                return p

    def go_home(self):
        clicked = self.click_any([Buttons.HOME, Buttons.HOME_ACTIVE], wait_time=1)
        if not clicked:
            self.go_back()
            self.click_any([Buttons.HOME, Buttons.HOME_ACTIVE], wait_time=1)

    def go_boss(self):
        self.click(Buttons.BOSS, wait_time=1)

    def go_event(self):
        self.click(Buttons.EVENT, wait_time=1)

    def go_back(self):
        self.click(Buttons.BACK, wait_time=1)

    def recover(self):
        potions = self.config.potions
        if not potions:
            return
        self.logger.info('Try to recover, potions: %s', potions)
        pos = self.exists(Items.POTION_SMALL)
        if not pos:
            return
        ts = {t.name: t for t in templates(Items)}
        for potion in potions:
            if potion.quantity <= 0:
                continue
            t = ts.get(potion.name)
            if t is None:
                continue
            if t == Items.LODESTAR_BEAD:
                # Swipe if using lodestar beads
                self.swipe(pos, v2=(pos[0], pos[1] - 500), wait_time=1)
                self.click(t, wait_time=1, retries=3)
                self.click(Buttons.OK, wait_time=1, retries=3)
                self.click(Buttons.OK, retries=3)
            else:
                # Consume the potion
                self.click(t, wait_time=1, retries=3)
                self.click(Buttons.USE, wait_time=1, retries=3)
                self.click(Buttons.OK, retries=3)
            # Decrease the quantity
            potion.quantity -= 1
            self.logger.info(f'Recovered with {potion.name}, remaining quantity: {potion.quantity}')
            break
        # Click the cancel button if it exists
        self.click(Buttons.CANCEL)


class BaseGacha(Task):
    def __init__(self, uri, type, config=None):
        super().__init__(uri, type, config)

    def execute(self):
        self.click(Buttons.GACHA_PULL)
        if self.exists(Tips.NO_TOKEN):
            self.break_loop()
            return
        self.click(Buttons.GACHA_RESET)
        self.click(Buttons.OK)


class Boss(Task):
    def __init__(self, uri, config=None):
        super().__init__(uri, TaskType.BOSS, config)

    def execute(self):
        pass


class Dragon(Task):
    def __init__(self, uri, config=None):
        super().__init__(uri, TaskType.DRAGON, config)

    def execute(self):
        pass


class Maze(Task):
    def __init__(self, uri, config=None):
        super().__init__(uri, TaskType.MAZE, config)

    def execute(self):
        pass


class Abyss(Task):
    def __init__(self, uri, config=None):
        super().__init__(uri, TaskType.ABYSS, config)

    def execute(self):
        pass


class Battlefield(Task):
    def __init__(self, uri, config=None):
        super().__init__(uri, TaskType.BATTLEFIELD, config)

    def pre_execute(self):
        self.go_home()
        self.go_event()
        self.click(Events.BATTLEFIELD_EVENT, wait_time=3, retries=3)
        self.click(Events.BATTLEFIELD_HELL, wait_time=3, retries=3)

    def execute(self):
        self.click(Buttons.CHALLENGE_START, wait_time=2)
        self.recover()
        self.click(Buttons.NEXT, wait_time=2)
        self.click(Buttons.CHALLENGE_RESTART, wait_time=2)


class BattlefieldGacha(BaseGacha):
    def __init__(self, uri, config=None):
        super().__init__(uri, TaskType.BATTLEFIELD_GACHA, config)

    def pre_execute(self):
        self.go_home()
        self.go_event()
        self.click(Events.BATTLEFIELD_EVENT, wait_time=3, retries=3)
        self.click(Events.BATTLEFIELD_GACHA_ENTRANCE, wait_time=3, retries=3)


class Config:
    def __init__(self, config, logger):
        self.logger = logger
        self.config = config
        self.potions: list[Potion] = []
        self.skip_pre: bool = False
        self.skip_post: bool = False
        self.analyze()

    def analyze(self):
        if not self.config:
            return
        potions = self.config.get("potions")
        skip_pre = self.config.get("skip_pre")
        skip_post = self.config.get("skip_pre")
        if potions and isinstance(potions, list):
            for p in potions:
                try:
                    name = p.get('name')
                    quantity = p.get('quantity')
                    if name and quantity:
                        self.potions.append(Potion(name, int(quantity)))
                except:
                    self.logger.error('Failed to parse potion: %s', p, exc_info=True)
        if skip_pre and isinstance(skip_pre, bool):
            self.skip_pre = skip_pre
        if skip_post and isinstance(skip_post, bool):
            self.skip_pre = skip_post


class Potion:
    def __init__(self, name: str, quantity: int):
        self.name = name.lower()
        self.quantity = quantity


class TaskType:
    QUEST = 0  # クエスト
    BELL = 10  # 救援依頼
    BOSS = 20  # ボスバトル
    DRAGON = 30  # 降臨討伐
    MAZE = 40  # 揺れぎの迷宮
    ABYSS = 50  # 揺れぎの迷宮 崩壊域
    TREASURE = 60  # 揺れぎの迷宮 宝物域
    BATTLEFIELD = 100  # 戦陣の宴
    BATTLEFIELD_GACHA = 101  # 戦陣の宴 ガチャ

    @staticmethod
    def create_task(type, uri, config):
        mapping = {
            TaskType.BOSS: Boss,
            TaskType.DRAGON: Dragon,
            TaskType.MAZE: Maze,
            TaskType.ABYSS: Abyss,
            TaskType.BATTLEFIELD: Battlefield,
            TaskType.BATTLEFIELD_GACHA: BattlefieldGacha,
        }
        clazz = mapping.get(type)
        if clazz:
            return clazz(uri, config)


class TaskStatus:
    INIT = 0
    RUNNING = 1
    SUCCESS = 2
    FAILED = 3
    INTERRUPTED = 4
