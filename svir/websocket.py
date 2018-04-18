import subprocess
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
from uuid import uuid4
import json

ws_conns = {}


class ExtApp:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.allowed_meths = ['ext_app_open']
        self.pending = {}

    def ext_app_open(self, *args):
        print("ext_app_open: begin")
        print(args)
        if len(args) != 1:
            return False
        print("ext_app_open: 2")

        cmd = ["xclock", "-bg", self.color, "-geometry",
               "%sx%s" % (args[0], args[0])]
        print("CMD FIRED: [%s]" % cmd)
        subprocess.Popen(cmd)

        return {'success': True}

    def send(self, api_msg):
        hyb_msg = {'app': self.name, 'msg': api_msg}
        in_loop = False
        for k, v in ws_conns.items():
            in_loop = True
            v['socket'].write_message(hyb_msg)
        if not in_loop:
            print('Send failed! No connections')

    def receive(self, api_msg):
        api_uuid = api_msg['uuid']
        if 'reply' in api_msg:
            app_msg = api_msg['reply']
            uuid = api_msg['uuid']
            if uuid in self.pending:
                print("Command pending found [%s]" % uuid)
                # FIXME: call CB
                if ('complete' not in app_msg or
                        app_msg['complete'] is True):
                    print("Command pending deleted [%s]" % uuid)
                    del self.pending[uuid]
            return
        else:
            app_msg = api_msg['msg']
            command = app_msg['command']
            if command not in self.allowed_meths:
                api_reply = {'uuid': api_uuid, 'reply': {
                    'success': False, 'msg': 'method not found'}}
                self.send(api_reply)

            args = app_msg['args']
            meth = getattr(self, command)

            # FIXME: manage command exception
            ret = meth(*args)

            api_reply = {'uuid': api_uuid, 'reply': ret}
            self.send(api_reply)


apps = {}
app_one = ExtApp('app_one', 'cyan')
app_two = ExtApp('app_two', 'pink')
app_three = ExtApp('app_three', 'lightgreen')
apps = {
    'app_one': app_one,
    'app_two': app_two,
    'app_three': app_three
}


class WebSocketServer(tornado.websocket.WebSocketHandler):
    def open(self):
        self.id = uuid4()
        ws_conns[self.id] = {'id': self.id, 'socket': self}
        print('New connection')

    def on_message(self, message):
        print('\nNew message: %s' % message)
        hyb_msg = json.loads(message)
        if ('app' not in hyb_msg or hyb_msg['app'] not in apps or
                'msg' not in hyb_msg):
            print('Malformed msg: [%s]' % message)
            return

        app_name = hyb_msg['app']
        api_msg = hyb_msg['msg']
        app = apps[app_name]

        app.receive(api_msg)

    def on_close(self):
        if self.id in ws_conns:
            del ws_conns[self.id]
        print('Closed connection')

    def check_origin(self, origin):
        return True
