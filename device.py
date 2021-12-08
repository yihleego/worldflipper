import base64
import multiprocessing
import threading
import time

import tidevice
from tidevice._relay import relay

from task import Task, TaskType

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
    def __init__(self, id, name=None, conn_type=None, device_type=None, task: Task = None):
        self.id = id
        self.name = name
        self.conn_type = conn_type
        self.device_type = device_type
        self.task = task
        self.status = DeviceStatus.INIT
        self.lock = threading.Lock()
        self.xctest_thread = threading.Thread(target=xctest_target, args=(id, self), daemon=True)
        self.xctest_thread.start()
        self.relay_process = multiprocessing.Process(target=relay_target, args=(id,))
        self.relay_process.start()
        self.status = DeviceStatus.RUNNING
        self.tid = tidevice.Device(self.id)

    def close(self):
        self.status = DeviceStatus.RUNNING
        self.stop_task()
        self.relay_process.terminate()
        self.tid.app_stop(BUNDLE_ID)

    def start_task(self, type, data=None):
        self.lock.acquire()
        try:
            # Stop the old task
            old_task = self.stop_task()
            # Return if just stop
            if type == -1:
                return
            # Create a new task and replace the old one
            new_task = TaskType.create_task(type, "iOS:///127.0.0.1:18100", data)
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

    def screenshot_base64(self, scale: float = 1):
        image = self.tid.screenshot()
        if scale != 1 and scale > 0:
            w, h = image.size
            bytes = image.resize((int(w * scale), int(h * scale)))._repr_png_()
        else:
            bytes = image._repr_png_()
        return base64.b64encode(bytes).decode()

    def screenshot_file(self, filename: str, scale: float = 1):
        image = self.tid.screenshot()
        if scale != 1 and scale > 0:
            w, h = image.size
            image.resize((int(w * scale), int(h * scale))).save('static/' + filename)
        else:
            image.save('static/' + filename)
        return filename

    def to_dict(self):
        return dict(id=self.id,
                    name=self.name,
                    status=self.status,
                    conn_type=self.conn_type,
                    running_task_type=self.task.type if self.task else -1)
