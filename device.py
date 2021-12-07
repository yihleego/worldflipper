import multiprocessing
import threading
import time

import tidevice
from tidevice._relay import relay

from task import Task, create_task

BUNDLE_ID = "com.facebook.WebDriverAgentRunner.worldflipper.xctrunner"


def xctest_target(id, device):
    # Start WebDriverAgent
    tid = tidevice.Device(id)
    tid.xctest(fuzzy_bundle_id=BUNDLE_ID, env={'USE_PORT': 18100})
    print('xctest_target terminated')
    device.status = DeviceStatus.STOPPED


def relay_target(id):
    # Start proxy
    tid = tidevice.Device(id)
    relay(tid, 18100, 18100)
    print('relay_target terminated')


class DeviceStatus:
    INIT = 0
    RUNNING = 1
    STOPPED = 2


class DeviceType:
    IOS = 0
    ANDROID = 1


class Device:
    def __init__(self, id, name=None, conn_type=None, task: Task = None):
        self.id = id
        self.name = name
        self.conn_type = conn_type
        self.task = task
        self.status = DeviceStatus.INIT
        self.lock = threading.Lock()
        self.xctest_thread = threading.Thread(target=xctest_target, args=(id, self), daemon=True)
        self.xctest_thread.start()
        self.relay_process = multiprocessing.Process(target=relay_target, args=(id,))
        self.relay_process.start()
        self.status = DeviceStatus.RUNNING

    def close(self):
        self.status = DeviceStatus.RUNNING
        self.stop_task()
        self.relay_process.terminate()
        d = tidevice.Device(self.id)
        d.app_stop(BUNDLE_ID)

    def start_task(self, type, data=None):
        self.lock.acquire()
        try:
            # Stop the old task
            old_task = self.stop_task()
            # Return if just stop
            if type == -1:
                return
            # Create a new task and replace the old one
            new_task = create_task(type, "iOS:///127.0.0.1:18100", data)
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
            t.start()
            self.task = new_task
            return
        while True:
            if old_task.is_finished():
                t.start()
                self.task = new_task
                break
            time.sleep(0.1)

    def to_dict(self):
        return dict(id=self.id,
                    name=self.name,
                    status=self.status,
                    conn_type=self.conn_type,
                    running_task_type=self.task.type if self.task else -1)
