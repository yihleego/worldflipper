import threading
from abc import ABC

from airtest.core.api import connect_device, exists, touch, swipe, sleep, Template

from assets import Buttons, Items, Events, Tips, templates

WAIT_TIME = 1


class Task(ABC):
    def __init__(self, uri, type, data=None, loop=True):
        self.event = threading.Event()
        self.uri = uri
        self.type = type
        self.data = data
        self.loop = loop
        self.status = TaskStatus.INIT
        self.device = None
        self.config = Config(data)

    def execute(self):
        raise NotImplementedError

    def pre_execute(self):
        pass

    def post_execute(self):
        pass

    def break_loop(self):
        self.loop = False

    def start(self):
        self.event.set()
        self.status = TaskStatus.RUNNING
        self.device = connect_device(self.uri)
        try:
            self.pre_execute()
            if self.loop:
                while self.is_running() and self.loop:
                    self.execute()
            else:
                self.execute()
            self.post_execute()
            self.status = TaskStatus.SUCCESS
        except Exception as e:
            self.status = TaskStatus.FAILED
            print(e)
        finally:
            self.event.clear()

    def stop(self):
        self.event.clear()

    def is_running(self):
        return self.event.is_set()

    def is_terminated(self):
        return self.status == TaskStatus.SUCCESS or self.status == TaskStatus.FAILED

    def click(self, v, wait_time=0.0, retries=0, cache=False):
        if not self.is_running():
            return
        print(f"try to click {v}")
        try:
            p = None
            if isinstance(v, Template):
                for i in range(retries + 1):
                    if cache:
                        if not v.last_position:
                            v.last_position = exists(v)
                        if v.last_position:
                            p = touch(v.last_position)
                    else:
                        p = exists(v)
                        if p:
                            touch(p)
                    if p:
                        break
            elif isinstance(v, tuple):
                p = touch(v)
            if wait_time > 0 and p:
                sleep(wait_time)
            return p
        except Exception as e:
            print(e)

    def exists(self, v, wait_time=0.0):
        if not self.is_running():
            return
        try:
            p = exists(v)
            if wait_time > 0 and p:
                sleep(wait_time)
            return p
        except Exception as e:
            print(e)

    def swipe(self, v1, v2=None, vector=None, wait_time=0.0):
        if not self.is_running():
            return
        if not v2 and not vector:
            return
        try:
            p = swipe(v1=v1, v2=v2, vector=vector)
            if wait_time > 0 and p:
                sleep(wait_time)
            return p
        except Exception as e:
            print(e)

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
        print("try to add stamina")
        potions = self.config.potions
        if not potions:
            return
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
                self.swipe(pos, v2=(pos[0], pos[1] - 200), wait_time=1)
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
            print(f'Recovered with {potion.name}, remaining quantity: {potion.quantity}')
            break
        # Click the cancel button if it exists
        self.click(Buttons.CANCEL)


class BaseGacha(Task):
    def __init__(self, uri, type, data=None):
        super().__init__(uri, type, data)

    def execute(self):
        self.click(Buttons.GACHA_PULL, wait_time=2)
        self.click(Buttons.GACHA_RESET)
        self.click(Buttons.OK)
        if self.exists(Tips.NO_TOKEN):
            self.break_loop()


class Boss(Task):
    def __init__(self, uri, data=None):
        super().__init__(uri, TaskType.BOSS, data)

    def execute(self):
        pass


class Dragon(Task):
    def __init__(self, uri, data=None):
        super().__init__(uri, TaskType.DRAGON, data)

    def execute(self):
        pass


class Maze(Task):
    def __init__(self, uri, data=None):
        super().__init__(uri, TaskType.MAZE, data)

    def execute(self):
        pass


class Abyss(Task):
    def __init__(self, uri, data=None):
        super().__init__(uri, TaskType.ABYSS, data)

    def execute(self):
        pass


class Battlefield(Task):
    def __init__(self, uri, data=None):
        super().__init__(uri, TaskType.BATTLEFIELD, data)

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
        quest_result = self.exists(Tips.QUEST_RESULT)
        if quest_result:
            self.click(quest_result, wait_time=0.1)
            self.click(quest_result, wait_time=0.1)


class BattlefieldGacha(BaseGacha):
    def __init__(self, uri, data=None):
        super().__init__(uri, TaskType.BATTLEFIELD_GACHA, data)

    def pre_execute(self):
        self.go_home()
        self.go_event()
        self.click(Events.BATTLEFIELD_EVENT, wait_time=3, retries=3)
        self.click(Events.BATTLEFIELD_GACHA_ENTRANCE, wait_time=3, retries=3)


class Config:
    def __init__(self, data=None):
        self.data = data
        self.potions: list[Potion] = []
        self.analyze()

    def analyze(self):
        if not self.data:
            return
        potions = self.data.get("potions")
        if potions and isinstance(potions, list):
            for p in potions:
                try:
                    name = p.get('name')
                    quantity = p.get('quantity')
                    if name and quantity:
                        self.potions.append(Potion(name, int(quantity)))
                except Exception as e:
                    print(f'Failed to parse potion {p}', e)


class Potion:
    def __init__(self, name: str, quantity: int):
        self.name = name.lower()
        self.quantity = quantity


class TaskType:
    STORY = 0
    BELL = 10
    BOSS = 20
    DRAGON = 30
    MAZE = 40
    ABYSS = 50
    BATTLEFIELD = 60
    BATTLEFIELD_GACHA = 61

    @staticmethod
    def create_task(type, uri, data):
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
            return clazz(uri, data)


class TaskStatus:
    INIT = 0
    RUNNING = 1
    SUCCESS = 2
    FAILED = 3
