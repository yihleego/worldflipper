class Chat {
    ssl;
    host;
    port;
    path;
    token;
    protocol;
    url;
    ws;
    tasks = {};
    futures = {};
    protobuf;
    proto = `syntax = "proto3";
import "google/protobuf/any.proto";
package ChatFactory;
message Box { int32 code = 1; google.protobuf.Any data = 2; }
message Message { int64 id = 1; int64 sender = 2; int64 recipient = 3; }`;

    constructor({ssl, host, port, path, token}) {
        this.ssl = ssl || false;
        this.host = host || 'localhost';
        this.port = port || 80;
        this.path = path || '/';
        this.token = token || '';
        this.protocol = this.ssl ? 'wss' : 'ws';
        this.url = `${this.protocol}://${this.host}:${this.port}${this.path}?access_token=${this.token}`;
    }

    init() {
        this.initProtobuf((protobuf) => {
            this.protobuf = protobuf;
            this.ws = this.initWebSocket();
            this.tasks = this.initSchedule();
        });
    }

    initProtobuf(callback) {
        protobuf.load('./google/protobuf/any.proto')
            .then((root) => {
                let proto = protobuf.parse(this.proto, root);
                callback({
                    any: root.lookupType("google.protobuf.Any"),
                    box: proto.root.lookupType("ChatFactory.Box"),
                    message: proto.root.lookupType("ChatFactory.Message"),
                })
            })
            .catch((error) => {
                throw error;
            });
    }

    initSchedule() {
        let tasks = {};
        tasks.ping = setInterval(() => this.ping(), 6000);
        return tasks;
    }

    initWebSocket() {
        let ws = new WebSocket(this.url);
        ws.binaryType = "arraybuffer";
        ws.onopen = event => this.onopen(event);
        ws.onclose = event => this.onclose(event);
        ws.onmessage = event => this.onmessage(event);
        return ws;
    }

    onopen(event) {
        console.debug("Connected", event);
        //this.listUnread(null);
    }

    onclose(event) {
        console.debug("Closed", event);
        Object.keys(this.tasks)
            .forEach(k => {
                if (!this.tasks[k]) {
                    clearInterval(this.tasks[k]);
                    delete this.tasks[k];
                }
            });
    }

    onmessage(event) {
        let buffer = new Uint8Array(event.data);
        let box = this.protobuf.box.decode(buffer);
        switch (box.code) {
            case OutboundCode.PONG:
                console.debug('pong');
                break;
            case OutboundCode.MESSAGE_PUSH:
                break;
            case OutboundCode.MESSAGE_DELIVERED: {
                console.log('MESSAGE_DELIVERED')
                let message = this.protobuf.message.decode(box.data.value);
                this.callbackFuture({tag: 'message', key: message.id, data: message})
                break;
            }
            case OutboundCode.MESSAGE_DELIVERED_OFFLINE: {
                console.log('MESSAGE_DELIVERED_OFFLINE')
                let message = this.protobuf.message.decode(box.data.value);
                this.callbackFuture({tag: 'message', key: message.id, data: message})
                break;
            }
            default:
                break;
        }
    }

    disconnect() {
        this.ws.close();
    }

    isConnected() {
        return this.ws.readyState === WebSocket.OPEN;
    }

    send({code, data, protobuf}) {
        let any = null;
        if (data && protobuf) {
            let dataBuffer = protobuf.encode(data).finish();
            any = this.protobuf.any.create({value: dataBuffer});
        }
        let box = {code: code, data: any};
        let boxBuffer = this.protobuf.box.encode(box).finish();
        this.ws.send(boxBuffer);
    }

    ping() {
        this.send({
            code: InboundCode.PING
        });
    }

    sendMessage(message) {
        return new Promise((resolve, reject) => {
            this.send({
                code: InboundCode.MESSAGE_SEND,
                data: message,
                protobuf: this.protobuf.message
            });
            this.addFuture({
                tag: 'message',
                key: message.id,
                resolve: resolve,
                reject: reject,
                data: message,
            });
            this.tasks[message.id] = setInterval(() => {
                console.log('cancelFuture')
                this.cancelFuture({tag: 'message', key: message.id, data: message});
                delete this.tasks[message.id];
            }, 5000);
        });
    }

    addFuture({tag, key, data, resolve, reject}) {
        this.futures[tag + ':' + key] = new Future({
            resolve: resolve,
            reject: reject,
            data: data,
        });
    }

    callbackFuture({tag, key, data}) {
        let future = this.futures[tag + ':' + key];
        if (future && future.callback) {
            future.callback(data);
            delete this.futures[tag + ':' + key];
        }
    }

    cancelFuture({tag, key, data}) {
        let future = this.futures[tag + ':' + key];
        if (future && future.cancel) {
            future.cancel(data);
            delete this.futures[tag + ':' + key];
        }
    }

}

class Future {
    resolve;
    reject;
    data;

    constructor({resolve, reject, data}) {
        this.resolve = resolve;
        this.reject = reject;
        this.data = data;
    }

    callback(data) {
        this.resolve(data || this.data);
    }

    cancel(data) {
        this.reject(data || this.data);
    }
}

class InboundCode {
    /** Common */
    static ERROR = 0;
    static PING = 1;
    static AUTHENTICATE = 2;
    /** Message */
    static MESSAGE_SEND = 10;
    static MESSAGE_RECEIVED = 11;
    static MESSAGE_REVOKE_SEND = 12;
    static MESSAGE_REVOKE_RECEIVED = 13;
    /** Group Message */
    static GROUP_MESSAGE_SEND = 14;
    static GROUP_MESSAGE_RECEIVED = 15;
    static GROUP_MESSAGE_REVOKE_SEND = 16;
    static GROUP_MESSAGE_REVOKE_RECEIVED = 17;
}

class OutboundCode {
    /** Common */
    static ERROR = 0;
    static PONG = 1;
    static ACCESS_GRANTED = 2;
    static ACCESS_DENIED = 3;
    static ACCESS_TIMEOUT = 4;
    /** Message */
    static MESSAGE_PUSH = 10;
    static MESSAGE_DELIVERED = 11;
    static MESSAGE_DELIVERED_OFFLINE = 12;
    static MESSAGE_REVOKE_PUSH = 13;
    static MESSAGE_REVOKE_DELIVERED = 14;
    static MESSAGE_REVOKE_DELIVERED_OFFLINE = 15;
    /** Group Message */
    static GROUP_MESSAGE_PUSH = 16;
    static GROUP_MESSAGE_DELIVERED = 17;
    static GROUP_MESSAGE_DELIVERED_OFFLINE = 18;
    static GROUP_MESSAGE_REVOKE_PUSH = 19;
    static GROUP_MESSAGE_REVOKE_DELIVERED = 20;
    static GROUP_MESSAGE_REVOKE_DELIVERED_OFFLINE = 21;
}

class DateUtils {
    static format(date, pattern) {
        if (!date) {
            return null;
        }
        let temp = pattern || "yyyy-MM-dd HH:mm:ss";
        if (/(y+)/.test(temp)) {
            temp = temp.replace(RegExp.$1, (date.getFullYear() + "").substr(4 - RegExp.$1.length));
        }
        const constants = {
            "M+": date.getMonth() + 1,
            "d+": date.getDate(),
            "H+": date.getHours(),
            "m+": date.getMinutes(),
            "s+": date.getSeconds(),
            "q+": Math.floor((date.getMonth() + 3) / 3),
            "S": date.getMilliseconds()
        }
        for (let k in constants) {
            if (new RegExp("(" + k + ")").test(temp)) {
                let replaceValue = RegExp.$1.length === 1 ? constants[k] : ("00" + constants[k]).substr(("" + constants[k]).length);
                temp = temp.replace(RegExp.$1, replaceValue);
            }
        }
        return temp;
    }
}