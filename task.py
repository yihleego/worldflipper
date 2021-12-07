import threading
from abc import ABC

from airtest.core.api import *
from tidevice import Device

from assets import Buttons, Items


class TaskType:
    BOSS = 0
    DRAGON = 1
    MAZE = 2
    ABYSS = 3
    BATTLEFIELD = 4


class TaskStatus:
    INIT = 0
    RUNNING = 1
    SUCCESS = 2
    FAILED = 3


class Config:
    def __init__(self, data=None):
        self.data = data
        self.potions = []
        self.analyze()

    def analyze(self):
        if not self.data:
            return
        potions = self.data.get("potions")
        if potions and isinstance(potions, list):
            self.potions = potions


class Task(ABC):
    def __init__(self, event, type, data=None, loop=False):
        self.event = event
        self.type = type
        self.data = data
        self.loop = loop
        self.status = TaskStatus.INIT
        self.device = None
        self.config = Config(data)

    def execute(self):
        raise NotImplementedError

    def start(self):
        self.event.set()
        self.status = TaskStatus.RUNNING
        self.connect()
        try:
            if self.loop:
                while self.event.is_set():
                    self.execute()
            else:
                self.execute()
            self.status = TaskStatus.SUCCESS
        except Exception as e:
            self.status = TaskStatus.FAILED
            print(e)
        finally:
            self.event.clear()

    def stop(self):
        self.event.clear()

    def is_finished(self):
        return self.status == TaskStatus.SUCCESS or self.status == TaskStatus.FAILED

    def connect(self):
        self.device = connect_device("iOS:///127.0.0.1:18100")

    def click(self, v, wait_time=0, cache=False):
        if not self.event.is_set():
            return
        try:
            p = None
            if cache:
                if not v.last_position:
                    v.last_position = exists(v)
                if v.last_position:
                    p = touch(v.last_position)
            else:
                p = exists(v)
                if p:
                    touch(p)
            if wait_time > 0 and p:
                sleep(wait_time)
        except Exception as e:
            print(e)

    def screenshot(self):
        if not self.event.is_set():
            return
        while True:
            d = Device()
            filename = input()
            image = d.screenshot()
            image.save("temp/" + filename + ".png")
            print(f"filename: {filename}")

    def recover(self):
        potions = self.config.potions
        if not potions:
            return
        if not exists(Items.POTION_SMALL):
            return
        for p in potions:
            for t in Items.templates():
                if p == t.name:
                    self.click(t, wait_time=1)
                    self.click(Buttons.USE, wait_time=1)
                    self.click(Buttons.OK)
                    return


class Boss(Task):
    def __init__(self, event, data=None):
        super().__init__(event, TaskType.BOSS, data, loop=True)

    def execute(self):
        pass


class Dragon(Task):
    def __init__(self, event, data=None):
        super().__init__(event, TaskType.DRAGON, data, loop=True)

    def execute(self):
        pass


class Maze(Task):
    def __init__(self, event, data=None):
        super().__init__(event, TaskType.MAZE, data, loop=True)

    def execute(self):
        pass


class Abyss(Task):
    def __init__(self, event, data=None):
        super().__init__(event, TaskType.ABYSS, data, loop=True)

    def execute(self):
        pass


class Battlefield(Task):
    def __init__(self, event, data=None):
        super().__init__(event, TaskType.BATTLEFIELD, data, loop=True)

    def execute(self):
        print("click START_CHALLENGE")
        self.click(Buttons.START_CHALLENGE, wait_time=2)
        print("click NEXT")
        self.click(Buttons.NEXT, wait_time=1)
        print("click RESTART_CHALLENGE")
        self.click(Buttons.RESTART_CHALLENGE)
        print("try to add stamina")
        self.recover()


def get_class(type):
    mapping = {
        TaskType.BOSS: Boss,
        TaskType.DRAGON: Dragon,
        TaskType.MAZE: Maze,
        TaskType.ABYSS: Abyss,
        TaskType.BATTLEFIELD: Battlefield,
    }
    return mapping.get(type)


def create_task(type, data):
    clazz = get_class(type)
    if clazz:
        event = threading.Event()
        return clazz(event, data)
