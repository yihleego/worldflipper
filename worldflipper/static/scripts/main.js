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
        screenshot(device_id, params, callback) {
            $get({
                url: `/devices/${device_id}/screenshots`,
                params: params,
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
        execute(device_id, params, callback) {
            $post({
                url: `/devices/${device_id}/tasks`,
                data: params,
            }, callback);
        },
        stop(device_id, callback) {
            $delete({
                url: `/devices/${device_id}/tasks`,
            }, callback);
        },
    },
};
const vm = new Vue({
    el: '#app',
    data: {
        listener: null,
        interval: 1,
        showNewTask: false,
        task: {},
        devices: [],
        deviceTypes: [
            {code: 0, name: 'iOS'},
            {code: 1, name: 'Android'}
        ],
        deviceStatuses: [
            {code: 0, name: '初始化中'},
            {code: 1, name: '已连接'},
            {code: 2, name: '已断开'},
        ],
        taskTypes: [
            {code: 0, name: 'クエスト', style: 0},
            {code: 10, name: '救援依頼', style: 1},
            {code: 20, name: 'ボスバトル', style: 2},
            {code: 30, name: '降臨討伐', style: 2},
            {code: 40, name: '揺れぎの迷宮', style: 0},
            {code: 50, name: '揺れぎの迷宮 崩壊域', style: 0},
            {code: 60, name: '揺れぎの迷宮 宝物域', style: 0},
            {code: 100, name: '戦陣の宴', style: 0},
            {code: 101, name: '戦陣の宴 ガチャ', style: -1},
        ],
        taskStatuses: [
            {code: 0, name: '初始化中'},
            {code: 1, name: '运行中'},
            {code: 2, name: '已完成'},
            {code: 3, name: '已失败'},
            {code: 4, name: '已终止'},
        ],
        styleTypes: [
            {code: 0, name: 'single'},
            {code: 1, name: 'bell'},
            {code: 2, name: 'host or join'},
        ],
        assets: {
            items: [
                {code: 'potion_small', name: '体力药剂（小）', uri: '/assets/items/potion_small.png'},
                {code: 'potion_medium', name: '体力药剂（中）', uri: '/assets/items/potion_medium.png'},
                {code: 'potion_large', name: '体力药剂（大）', uri: '/assets/items/potion_large.png'},
                {code: 'potion_timelimit', name: '体力药剂（限时）', uri: '/assets/items/potion_timelimit.png'},
                {code: 'aruku_chocolate', name: 'アルク的巧克力', uri: '/assets/items/aruku_chocolate.png'},
                {code: 'shiro_marshmallow', name: 'シロ的棉花糖', uri: '/assets/items/shiro_marshmallow.png'},
                {code: 'lodestar_bead', name: '星导石', uri: '/assets/items/lodestar_bead.png'},
            ]
        }
    },
    methods: {
        init() {
            this.config();
            this.resetTask();
            this.queryDevices();
            this.listener = setInterval(this.refreshDevices, this.interval * 1000);
        },
        config() {
            let interval = this.getCookie('auto_refresh_interval');
            if (interval != null && interval > 0) {
                this.interval = interval
            }
        },
        changeAutoRefreshInterval(v) {
            this.setCookie('auto_refresh_interval', v, 31536000)
            clearInterval(this.listener);
            this.listener = setInterval(this.refreshDevices, this.interval * 1000);
        },
        changeAutoRefreshSwitch(deviceId) {
            let device = this.getDevice(deviceId);
            if (device == null) {
                return;
            }
            if (device.enableAutoRefresh) {
                this.setCookie('device_auto_refresh_' + deviceId, 1, 31536000)
            } else {
                this.setCookie('device_auto_refresh_' + deviceId, 0, 0)
            }
        },
        refreshDevices() {
            for (let i in this.devices) {
                if (this.devices[i].enableAutoRefresh) {
                    this.queryDevice(this.devices[i].id)
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
            let params = {'scale': 0.2, 'type': 'file'}
            APIs.devices.screenshot(device.id, params, (result) => {
                if (!result.success) {
                    return;
                }
                device.screenshot = result.data
                device.refreshing = false
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
            device.type_name = this.code2name(device.type, this.deviceTypes)
            device.status_name = this.code2name(device.status, this.deviceStatuses)
            device.task_type_name = this.code2name(device.task_type, this.taskTypes)
            device.task_status_name = this.code2name(device.task_status, this.taskStatuses)
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
            let enableAutoRefresh = this.getCookie('device_auto_refresh_' + device.id)
            device.enableAutoRefresh = enableAutoRefresh != null && enableAutoRefresh == 1
            device.refreshing = false
            device.screenshot = null
            this.devices.push(device)
            this.getScreenshot(device.id)
        },
        startTask() {
            let params = this.task
            if (params.config.potions) {
                for (let i in params.config.potions) {
                    delete params.config.potions[i].name
                    delete params.config.potions[i].uri
                }
            }
            console.log(JSON.stringify(params));
            APIs.tasks.execute(params.deviceId, params, (result) => {
                if (!result.success) {
                    return;
                }
                this.queryDevice(params.deviceId);
                this.resetTask();
            });
        },
        stopTask(deviceId) {
            APIs.tasks.stop(deviceId, (result) => {
                if (!result.success) {
                    return;
                }
                this.queryDevice(deviceId);
            });
        },
        resetTask() {
            this.showNewTask = false
            this.task = {
                deviceId: null,
                code: null,
                config: {
                    potions: null,
                    skip_pre: true,
                },
            }
        },
        changeTaskType() {
            let showPotions = true;
            for (let i in this.taskTypes) {
                if (this.task.code == this.taskTypes[i].code) {
                    if (this.taskTypes[i].style == -1) {
                        showPotions = false
                        break
                    }
                }
            }
            if (showPotions) {
                let potions = [];
                for (let i in this.assets.items) {
                    let item = this.assets.items[i]
                    potions.push({code: item.code, name: item.name, uri: item.uri, quantity: 0})
                }
                this.task.config.potions = potions
            } else {
                this.task.config.potions = null
            }
        },
        showNewTaskForm(deviceId) {
            this.showNewTask = true
            this.task.deviceId = deviceId
        },
        code2name(code, enums) {
            for (let i in enums) {
                if (code == enums[i].code) {
                    return enums[i].name
                }
            }
            return ''
        },
        getCookie(key) {
            let cookies = document.cookie.split("; ");
            for (let i = 0; i < cookies.length; i++) {
                let entry = cookies[i].split("=");
                if (entry[0] === key) {
                    return decodeURI(entry[1]);
                }
            }
            return null;
        },
        setCookie(key, value, time) {
            let date = new Date();
            date.setTime(date.getTime() + time);
            document.cookie = key + "=" + value + "; expires=" + date.toGMTString();
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
