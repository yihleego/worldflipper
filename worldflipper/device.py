import subprocess
import sys
import threading
import time

import tidevice
import wda
from tidevice._wdaproxy import WDAService

from worldflipper import config, images
from worldflipper.task import Task, TaskType


class Device:
    def __init__(self, id, name=None, type=None, conn_type=None, task: Task = None):
        self.id = id
        self.name = name
        self.type = type
        self.status = DeviceStatus.INIT
        self.conn_type = conn_type
        self.task = task
        self.port = config.next_wda_port()
        self.bundle_id = config.get_wda_bundle_id()
        self.lock = threading.Lock()
        self.wda_uri = f"http://127.0.0.1:{self.port}"
        self.air_uri = f"{DeviceType.name(self.type)}:///127.0.0.1:{self.port}"
        self.c = wda.Client(self.wda_uri)
        self.d = tidevice.Device(id)
        self.wda_service = WDAService(self.d, bundle_id=self.bundle_id, env={}, check_interval=30)
        self.wda_proxy_thread = threading.Thread(target=wda_proxy, args=(self.id, self.port, self.wda_service, self), daemon=True)
        self.wda_proxy_thread.start()
        self.status = DeviceStatus.RUNNING

    def close(self):
        self.status = DeviceStatus.RUNNING
        self.stop_task()
        self.wda_service.stop()
        self.d.app_stop(self.bundle_id)

    def start_task(self, type, config=None):
        self.lock.acquire()
        try:
            # Stop the old task
            old_task = self.stop_task()
            # Return if just stop
            if type == -1:
                return
            # Create a new task and replace the old one
            new_task = TaskType.create_task(type, self.air_uri, config)
            if not new_task:
                raise Exception(f"Invalid task type: {type}")
            self.run_task(new_task, old_task)
        finally:
            self.lock.release()

    def stop_task(self):
        if self.task:
            self.task.stop()
        return self.task

    def run_task(self, new_task, old_task):
        if not new_task:
            return
        t = threading.Thread(target=new_task.start, daemon=True)
        if not old_task:
            self.task = new_task
            t.start()
            return
        while True:
            if old_task.is_terminated():
                self.task = new_task
                t.start()
                break
            time.sleep(0.1)

    def home(self):
        self.c.home()
        return True

    def screenshot(self, scale: float = 1):
        return images.base64(self.d.screenshot(), scale)

    def to_dict(self):
        return dict(id=self.id,
                    name=self.name,
                    type=self.type,
                    status=self.status,
                    task_type=self.task.type if self.task else -1,
                    task_status=self.task.status if self.task else -1,
                    conn_type=self.conn_type,
                    connected=True)


class DeviceType:
    IOS = 0  # iOS
    ANDROID = 1  # Android

    @staticmethod
    def name(t):
        if t == 0:
            return 'iOS'
        elif t == 1:
            return 'Android'
        else:
            return 'Unknown'


class DeviceStatus:
    INIT = 0
    RUNNING = 1
    STOPPED = 2


class ActionType:
    HOME = "home"


def wda_proxy(id, port, wda: WDAService, device):
    cmds = [
        sys.executable, '-m', 'tidevice', '-u', id, 'relay',
        str(port), '8100'
    ]
    p = subprocess.Popen(cmds, stdout=sys.stdout, stderr=sys.stderr)
    try:
        wda.start()
        while wda._service.running and p.poll() is None:
            time.sleep(.1)
    finally:
        p and p.terminate()
        wda.stop()
        device.status = DeviceStatus.STOPPED
