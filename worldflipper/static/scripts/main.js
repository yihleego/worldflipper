const APIs = {
    devices: {
        query(params, callback) {
            $get({
                url: `/devices`,
                params: params
            }, callback);
        },
        get(device_id, callback) {
            $get({
                url: `/devices/${device_id}`,
            }, callback);
        },
        connect(device_id, callback) {
            $post({
                url: `/devices/${device_id}`,
            }, callback);
        },
        disconnect(device_id, callback) {
            $delete({
                url: `/devices/${device_id}`,
            }, callback);
        },
        screenshot(device_id, scale, callback) {
            $get({
                url: `/devices/${device_id}/screenshots`,
                params: {'scale': scale}
            }, callback);
        },
        home(device_id, callback) {
            $post({
                url: `/devices/${device_id}/actions`,
                params: {'type': 'home'}
            }, callback);
        },
    },
    tasks: {
        stop(device_id, callback) {
            $post({
                url: `/devices/${device_id}/tasks`,
                data: {"code": -1},
            }, callback);
        },
        execute(device_id, code, config, callback) {
            $post({
                url: `/devices/${device_id}/tasks`,
                data: {"code": code, "config": config},
            }, callback);
        },
    },
};
const vm = new Vue({
    el: '#app',
    data: {
        listener: null,
        interval: 1,
        devices: [],
        deviceType: {
            0: 'iOS',
            1: 'Android',
        },
        deviceStatus: {
            0: 'init',
            1: 'running',
            2: 'stopped',
        },
        taskType: {
            0: 'クエスト',
            10: '救援依頼',
            20: 'ボスバトル',
            30: '降臨討伐',
            40: '揺れぎの迷宮',
            50: '揺れぎの迷宮 崩壊域',
            60: '揺れぎの迷宮 宝物域',
            100: '戦陣の宴',
            101: '戦陣の宴 ガチャ',
        },
        taskStatus: {
            0: 'init',
            1: 'running',
            2: 'success',
            3: 'failed',
            4: 'interrupted',
        },
    },
    methods: {
        init() {
            this.queryDevices();
            this.listener = setInterval(this.refreshScreenshot, this.interval * 1000);
        },
        changeInterval(v) {
            console.log('changeInterval', v)
            clearInterval(this.listener);
            this.listener = setInterval(this.refreshScreenshot, this.interval * 1000);
        },
        refreshScreenshot() {
            for (let i in this.devices) {
                if (this.devices[i].autoRefresh) {
                    this.getScreenshot(this.devices[i].id)
                }
            }
        },
        queryDevices() {
            APIs.devices.query({'all': true}, (result) => {
                if (!result.success) {
                    return;
                }
                for (let i in result.data) {
                    this.setDevice(result.data[i])

                }
            });
        },
        queryDevice(deviceId) {
            APIs.devices.get(deviceId, (result) => {
                if (!result.success) {
                    return;
                }
                this.setDevice(result.data)
            });
        },
        connectDevice(deviceId) {
            let device = this.getDevice(deviceId)
            if (device == null) {
                return
            }
            APIs.devices.connect(device.id, (result) => {
                if (!result.success) {
                    return;
                }
                console.log(result)
                this.queryDevice(device.id)
            });
        },
        disconnectDevice(deviceId) {
            let device = this.getDevice(deviceId)
            if (device == null) {
                return
            }
            APIs.devices.disconnect(device.id, (result) => {
                if (!result.success) {
                    return;
                }
                console.log(result)
                this.queryDevice(device.id)
            });
        },
        getScreenshot(deviceId) {
            let device = this.getDevice(deviceId)
            if (device == null) {
                return
            }
            if (device.refreshing) {
                return;
            }
            device.refreshing = true
            APIs.devices.screenshot(device.id, 0.2, (result) => {
                if (!result.success) {
                    return;
                }
                if (device.name.endsWith(' ')) {
                    device.name = device.name.trim()
                } else {
                    device.name = device.name + ' '
                }
                device.screenshot = 'data:image/png;base64,' + result.data
                device.refreshing = false
                console.log(device)
                console.log(device.screenshot)
            });
        },
        goHome(deviceId) {
            APIs.devices.home(deviceId, (result) => {
                if (!result.success) {
                    return;
                }
            });
        },
        getDevice(deviceId) {
            for (let i in this.devices) {
                let d = this.devices[i]
                if (d.id == deviceId) {
                    return d
                }
            }
        },
        setDevice(device) {
            if (device == null) {
                return
            }
            device.type_name = this.deviceType[device.type] || ''
            device.status_name = this.deviceStatus[device.status] || ''
            device.task_type_name = this.taskType[device.task_type] || ''
            device.task_status_name = this.taskStatus[device.task_status] || ''
            device.autoRefresh = false
            device.refreshing = false
            device.screenshot = ''
            for (let i = 0; i < this.devices.length; i++) {
                let d = this.devices[i];
                if (d.id == device.id) {
                    for (let k in device) {
                        d[k] = device[k];
                    }
                    this.getScreenshot(device.id)
                    return
                }
            }
            this.devices.push(device)
            this.getScreenshot(device.id)
        },
        stopTask(deviceId) {
            APIs.tasks.stop(deviceId, (result) => {
                if (!result.success) {
                    return;
                }
                console.log(result.data)
            });
        },
        executeTask(deviceId, code, config) {
            APIs.tasks.stop(deviceId, code, config, (result) => {
                if (!result.success) {
                    return;
                }
                console.log(result.data)
            });
        },
    },
    created() {
        this.init();
    },
});

function $get(value, callback) {
    $request('get', value, callback);
}

function $post(value, callback) {
    $request('post', value, callback);
}

function $put(value, callback) {
    $request('put', value, callback);
}

function $patch(value, callback) {
    $request('patch', value, callback);
}

function $delete(value, callback) {
    $request('delete', value, callback);
}

function $request(method, value, callback) {
    value.method = method;
    axios(value).then((result) => {
        if (callback) {
            callback(result.data);
        }
    }).catch((error) => {
        if (callback) {
            callback({
                success: false,
                message: error.response ? error.response.statusText : null
            });
        }
    });
}
