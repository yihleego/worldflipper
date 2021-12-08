import asyncio

import tidevice
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from device import Device, DeviceStatus
from models import Result, TaskExecuteParam

app = FastAPI()
app.mount("/worldflipper", StaticFiles(directory="static", html=True), name="static")
app.devices = {}
app.lock = asyncio.locks.Lock()


@app.post("/devices/{device_id}")
async def connect_device(device_id):
    device = app.devices.get(device_id)
    if device is None or device.status == DeviceStatus.STOPPED:
        if device:
            device.close()
        tid = get_tidevice(device_id)
        device = Device(tid.udid, tid.name, tid.info.conn_type)
        app.devices[device_id] = device
    return Result.build_success(device.to_dict())


@app.get("/devices")
async def get_devices(all: bool = Query(None), connected: bool = Query(None)):
    result = []
    if all:
        um = tidevice.Usbmux()
        for info in um.device_list():
            udid, conn_type = info.udid, info.conn_type
            tid = get_tidevice(udid)
            name = tid.name
            result.append(dict(id=udid, name=name, conn_type=conn_type))
    elif connected:
        for d in app.devices.values():
            result.append(d.to_dict())
    return Result.build_success(result)


@app.delete("/devices/{device_id}")
async def delete_devices(device_id):
    device = app.devices.pop(device_id)
    if device:
        device.close()
    return Result.build_success(True, "OK")


@app.post("/devices/{device_id}/tasks")
async def execute_task(device_id, param: TaskExecuteParam):
    device = app.devices.get(device_id)
    if device is None:
        return Result.build_failure("No device detected")
    device.start_task(param.code, param.data)
    return Result.build_success(True, "OK")


@app.get("/devices/{device_id}/screenshots")
async def get_screenshot(device_id, scale: float = Query(1)):
    screenshot = None
    device = app.devices.get(device_id)
    if device:
        screenshot = device.screenshot_base64(scale)
    return Result.build_success(screenshot)


@app.on_event("startup")
async def startup():
    pass


@app.on_event("shutdown")
async def shutdown():
    if app.devices:
        for d in app.devices:
            d.close()


@app.middleware("http")
async def request_lock(request: Request, call_next):
    locked = await app.lock.acquire()
    print('locked', locked)
    try:
        return await call_next(request)
    finally:
        app.lock.release()
        print('unlocked', locked)


@app.exception_handler(Exception)
async def catch_any_exception(_, e: Exception):
    return JSONResponse(Result.build_failure(message=str(e)).dict())


@app.exception_handler(HTTPException)
async def catch_http_exception(_, e: HTTPException):
    return JSONResponse(status_code=e.status_code, content=e.detail)


def get_tidevice(device_id):
    try:
        um = tidevice.Usbmux()
        return tidevice.Device(device_id, um)
    except:
        raise Exception("No device detected")
