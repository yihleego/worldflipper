import asyncio
import uuid
from datetime import datetime

import tidevice
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from worldflipper import images
from worldflipper.device import Device, DeviceStatus, DeviceType
from worldflipper.models import Result, TaskExecuteParam, ActionType, ScreenshotType

app = FastAPI()
app.mount("/worldflipper", StaticFiles(directory='static', html=True), name="static")
app.mount("/assets", StaticFiles(directory='assets'), name="assets")
app.devices = {}
app.lock = asyncio.locks.Lock()


@app.get("/")
async def index():
    return RedirectResponse("/worldflipper", 302)


@app.get("/devices")
async def get_devices(all: bool = Query(None), connected: bool = Query(None)):
    result = []
    if all:
        um = tidevice.Usbmux()
        for info in um.device_list():
            if info.udid in app.devices:
                result.append(app.devices[info.udid].to_dict())
            else:
                result.append(get_tidevice_info(info.udid))
    elif connected:
        for d in app.devices.values():
            result.append(d.to_dict())
    return Result.build_success(result)


@app.get("/devices/{device_id}")
async def get_device(device_id):
    if device_id in app.devices:
        result = app.devices[device_id].to_dict()
    else:
        result = get_tidevice_info(device_id)
    return Result.build_success(result)


@app.post("/devices/{device_id}")
async def connect_device(device_id):
    device = app.devices.get(device_id)
    if device is None or device.status == DeviceStatus.DISCONNECTED:
        if device:
            device.close()
        tid = get_tidevice(device_id)
        device = Device(id=tid.udid, name=tid.name, type=DeviceType.IOS, conn_type=tid.info.conn_type)
        app.devices[device_id] = device
    return Result.build_success(device.to_dict())


@app.delete("/devices/{device_id}")
async def disconnect_devices(device_id):
    device = app.devices.pop(device_id)
    if device:
        device.close()
    return Result.build_success(True, "OK")


@app.get("/devices/{device_id}/screenshots")
async def get_device_screenshot(device_id, scale: float = Query(1), type: str = Query(ScreenshotType.BASE64)):
    if device_id in app.devices:
        image = app.devices[device_id].screenshot()
    else:
        image = get_tidevice(device_id).screenshot()
    if type == ScreenshotType.BASE64:
        result = images.base64(image, scale)
    elif type == ScreenshotType.FILE:
        filename = 'screenshots/{}/{}.png'.format(datetime.now().strftime("%Y%m%d"), uuid.uuid4())
        images.download(image, 'static/' + filename, scale)
        result = filename
    else:
        result = None
    return Result.build_success(result)


@app.post("/devices/{device_id}/actions")
async def execute_device_action(device_id, type: str = Query(None)):
    result = None
    if type == ActionType.HOME:
        if device_id in app.devices:
            result = app.devices[device_id].home()
    return Result.build_success(result)


@app.post("/devices/{device_id}/tasks")
async def start_task(device_id, param: TaskExecuteParam):
    device = app.devices.get(device_id)
    if device is None:
        return Result.build_failure("No device detected")
    device.start_task(param.code, param.config)
    return Result.build_success()


@app.delete("/devices/{device_id}/tasks")
async def stop_task(device_id):
    device = app.devices.get(device_id)
    if device is None:
        return Result.build_failure("No device detected")
    device.stop_task()
    return Result.build_success()


@app.on_event("startup")
async def startup():
    pass


@app.on_event("shutdown")
async def shutdown():
    if app.devices:
        for i in app.devices:
            app.devices[i].close()


@app.middleware("http")
async def request_lock(request: Request, call_next):
    await app.lock.acquire()
    try:
        return await call_next(request)
    finally:
        app.lock.release()


@app.exception_handler(Exception)
async def catch_any_exception(_, e: Exception):
    return JSONResponse(Result.build_failure(message=str(e)).dict())


@app.exception_handler(HTTPException)
async def catch_http_exception(_, e: HTTPException):
    return JSONResponse(status_code=e.status_code, content=e.detail)


def get_tidevice(device_id) -> tidevice.Device:
    try:
        um = tidevice.Usbmux()
        return tidevice.Device(device_id, um)
    except:
        raise Exception("No device detected")


def get_tidevice_info(device_id) -> dict:
    try:
        um = tidevice.Usbmux()
        device = tidevice.Device(device_id, um)
        return dict(id=device.udid, name=device.name, type=DeviceType.IOS, conn_type=device.info.conn_type, connected=False)
    except:
        raise Exception("No device detected")
