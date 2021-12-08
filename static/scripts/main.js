const APIs = {
    devices: {
        all(callback) {
            $get({
                url: `/devices`,
                params: {'all': true}
            }, callback);
        },
        connected(callback) {
            $get({
                url: `/devices`,
                params: {'connected': true}
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
    },
    tasks: {
        stop(device_id, callback) {
            $post({
                url: `/devices/${device_id}/tasks`,
                data: {"code": -1},
            }, callback);
        },
        execute(device_id, code, data, callback) {
            $post({
                url: `/devices/${device_id}/tasks`,
                data: {"code": code, "data": data},
            }, callback);
        },
    },
};
const vm = new Vue({
    el: '#app',
    data: {
        allDevices: [],
        connectedDevices: [],
    },
    methods: {
        init() {
            this.queryAllDevices();
            this.queryConnectedDevices();
        },
        queryAllDevices() {
            APIs.devices.all((result) => {
                if (!result.success) {
                    return;
                }
                this.allDevices = result.data
            });
        },
        queryConnectedDevices() {
            APIs.devices.connected((result) => {
                if (!result.success) {
                    return;
                }
                this.connectedDevices = result.data
                for (let i in result.data) {
                    this.queryScreenshot(result.data[i].id)
                }
            });
        },
        queryScreenshot(deviceId) {
            let device = null
            for (let i in this.connectedDevices) {
                let d = this.connectedDevices[i]
                if (d.id == deviceId) {
                    device = d
                    break
                }
            }
            if (device == null) {
                return
            }
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
                console.log(device)
                console.log(device.screenshot)
            });
        }
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
