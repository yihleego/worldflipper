import threading

import tidevice
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from device import Device, DeviceStatus
from models import Result, TaskCreateParam, DeviceCreateParam

app = FastAPI()
app.mount("/worldflipper", StaticFiles(directory="static", html=True), name="static")
app.devices = {}
app.lock = threading.Lock()


@app.post("/tasks")
async def create_task(param: TaskCreateParam):
    app.lock.acquire()
    try:
        device = app.devices.get(param.device)
        if device is None:
            return Result.build_failure("Device does not exist")
        device.start_task(param.code, param.data)
        return Result.build_success(True, "OK")
    finally:
        app.lock.release()


@app.post("/devices")
async def create_device(param: DeviceCreateParam):
    app.lock.acquire()
    try:
        device = app.devices.get(param.device)
        if device is None or device.status == DeviceStatus.STOPPED:
            if device:
                device.close()
            try:
                um = tidevice.Usbmux()
                tid = tidevice.Device(param.device, um)
            except:
                return Result.build_failure("Device does not exist")
            device = Device(tid.udid, tid.name, tid.info.conn_type)
            app.devices[param.device] = device
        return Result.build_success(device.to_dict())
    finally:
        app.lock.release()


@app.get("/devices")
async def get_devices(connected: bool = Query(None)):
    app.lock.acquire()
    try:
        result = []
        if connected:
            for d in app.devices.values():
                result.append(d.to_dict())
        else:
            um = tidevice.Usbmux()
            for info in um.device_list():
                udid, conn_type = info.udid, info.conn_type
                try:
                    tid = tidevice.Device(udid, um)
                    name = tid.name
                except:
                    name = ""
                result.append(dict(id=udid, name=name, conn_type=conn_type))
        return Result.build_success(result)
    finally:
        app.lock.release()


@app.delete("/devices/{id}")
async def delete_devices(id):
    app.lock.acquire()
    try:
        device = app.devices.pop(id)
        if device:
            device.close()
        return Result.build_success(True, "OK")
    finally:
        app.lock.release()


@app.on_event("startup")
async def startup():
    pass


@app.on_event("shutdown")
async def shutdown():
    if app.devices:
        for d in app.devices:
            d.stop()


@app.exception_handler(Exception)
async def catch_any_exception(_, e: Exception):
    return JSONResponse(Result.build_failure(message=str(e)).dict())


@app.exception_handler(HTTPException)
async def catch_http_exception(_, e: HTTPException):
    return JSONResponse(status_code=e.status_code, content=e.detail)
