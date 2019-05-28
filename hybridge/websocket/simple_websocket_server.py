'''
The MIT License (MIT)
Copyright (c) 2013 Dave P.
'''
import ssl
import json
from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot, QThread, QMutex
import socket
from select import select
from hybridge.websocket.web_api import WebApi
from hybridge.websocket.web_socket import WebSocket


__all__ = ['WebSocket', 'SimpleWebSocketServer']


_VALID_STATUS_CODES = [1000, 1001, 1002, 1003, 1007, 1008,
                       1009, 1010, 1011, 3000, 3999, 4000, 4999]

HANDSHAKE_STR = (
   "HTTP/1.1 101 Switching Protocols\r\n"
   "Upgrade: WebSocket\r\n"
   "Connection: Upgrade\r\n"
   "Sec-WebSocket-Accept: %(acceptstr)s\r\n\r\n"
)

GUID_STR = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

STREAM = 0x0
TEXT = 0x1
BINARY = 0x2
CLOSE = 0x8
PING = 0x9
PONG = 0xA

HEADERB1 = 1
HEADERB2 = 3
LENGTHSHORT = 4
LENGTHLONG = 5
MASK = 6
PAYLOAD = 7

MAXHEADER = 65536
MAXPAYLOAD = 33554432


class SimpleWebSocketServer(QThread):
    wss_error_sig = pyqtSignal('QVariantMap')
    from_socket_received = pyqtSignal('QVariantMap')
    from_socket_sent = pyqtSignal('QVariantMap', WebApi)
    open_connection_sig = pyqtSignal(WebApi)
    close_connection_sig = pyqtSignal()

    def __init__(self, host, port, hyb_plugins, selectInterval=0.1):
        self.websocketclass = WebSocket
        self.hyb_plugins = hyb_plugins
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serversocket.bind((host, port))
        self.serversocket.listen(5)
        self.selectInterval = selectInterval
        self.connections = {}
        self.listeners = [self.serversocket]
        self.mutex = QMutex()
        self.do_run = True

        super(SimpleWebSocketServer, self).__init__()

        for hyb_plugin_key, hyb_plugin_val in self.hyb_plugins.items():
            for web_api_key, web_api_val in hyb_plugin_val['web_apis'].items():
                self.register_caller(web_api_val)

    def register_caller(self, caller):
        print('Registering %s/%s' % (caller.plugin, caller.app_name))
        caller.caller_sig['QVariantMap'].connect(self.handle_caller_sig)
        caller.send_to_wss_sig['QVariantMap', WebApi].connect(self.send_to_wss)

    @pyqtSlot('QVariantMap')
    def handle_caller_sig(self, data):
        print('From caller_sig: %s' % data)

    @pyqtSlot('QVariantMap', WebApi)
    def send_to_wss(self, hyb_msg, caller):
        hyb_msg_str = json.dumps(hyb_msg)
        print(caller)
        print('send_to_wss: %s' % hyb_msg_str)
        # ret = False
        # for fileno, conn in list(self.connections.items()):
        #     if conn == self.serversocket:
        #         continue
        #     conn.sendMessage(hyb_msg_str)
        #     ret = True
        # if ret is False:
        #     app = hyb_msg['app']
        #     self.wss_error_sig.emit(
        #         {'app': app, 'msg': 'Send failed! No connections'})
        # FIXME: manage exception
        print('caller.ws: %s' % caller.ws)
        caller.ws.sendMessage(hyb_msg_str)

    def handle_socket_received(self, data, caller):
        try:
            hyb_msg = self._loads(data, caller)
        except ValueError:
            print('Malformed msg in handle_socket_received: [%s]' % data)
            return
        self.from_socket_received.emit(hyb_msg)

    def handle_socket_sent(self, data, caller):
        try:
            hyb_msg = self._loads(data, caller)
        except ValueError:
            print('Malformed msg in handle_socket_sent: [%s]' % data)
            return
        self.from_socket_sent.emit(hyb_msg, caller)

    def _loads(self, data, caller):
        hyb_msg = json.loads(data)
        print(hyb_msg)
        print(caller.app_name)
        if ('app' not in hyb_msg
                or hyb_msg['app'] != caller.app_name
                or 'msg' not in hyb_msg):
            raise ValueError
        return hyb_msg

    def _decorateSocket(self, sock):
        return sock

    def _constructWebSocket(self, sock, address):
        return self.websocketclass(self, sock, address)

    def close(self):
        self.serversocket.close()

        for desc, conn in list(self.connections.items()):
            conn.close()
            self._handleClose(conn)

    def _handleClose(self, client):
        client.client.close()
        # only call handleClose when we have a successful websocket connection
        if client.handshaked:
            try:
                client.handleClose()
            except Exception:
                pass

    def serveonce(self):
        writers = []
        for fileno in list(self.listeners):
            if fileno == self.serversocket:
                continue
            client = self.connections[fileno]
            if client.sendq:
                writers.append(fileno)

        if self.selectInterval:
            rList, wList, xList = select(
                self.listeners, writers, self.listeners, self.selectInterval)
        else:
            rList, wList, xList = select(
                self.listeners, writers, self.listeners)

        for ready in wList:
            client = self.connections[ready]
            try:
                while client.sendq:
                    self.mutex.lock()
                    do_run = self.do_run
                    self.mutex.unlock()
                    if not do_run:
                        raise Exception("closing websocket server")
                    opcode, payload = client.sendq.popleft()
                    remaining = client._sendBuffer(payload)
                    if remaining is not None:
                        client.sendq.appendleft((opcode, remaining))
                        break
                    else:
                        if opcode == CLOSE:
                            raise Exception('received client close')

            except ImportError as n:
                self.wss_error_sig.emit({'msg': str(n)})
                self._handleClose(client)
                del self.connections[ready]
                self.close_connection_sig.emit()
                self.listeners.remove(ready)

        for ready in rList:
            if ready == self.serversocket:
                sock = None
                self.mutex.lock()
                do_run = self.do_run
                self.mutex.unlock()
                try:
                    if not do_run:
                        raise Exception("closing websocket server")
                    sock, address = self.serversocket.accept()
                    newsock = self._decorateSocket(sock)
                    newsock.setblocking(0)
                    fileno = newsock.fileno()
                    self.connections[fileno] = self._constructWebSocket(
                        newsock, address)
                    # self.open_connection_sig.emit()
                    self.listeners.append(fileno)
                except ImportError as n:
                    self.wss_error_sig.emit({'msg': str(n)})
                    if sock is not None:
                        sock.close()
            else:
                if ready not in self.connections:
                    continue
                client = self.connections[ready]
                self.mutex.lock()
                do_run = self.do_run
                self.mutex.unlock()
                try:
                    if not do_run:
                        raise Exception("closing websocket server")
                    client._handleData()
                    plugin, app = client.request.path.strip('/').split('/')
                    if plugin is None or app is None:
                        raise ValueError('Inconsistent websocket path: %s' %
                                         client.request.path)
                    if plugin not in self.hyb_plugins:
                        raise Exception()  # FIXME
                        self.wss_error_sig.emit({
                            'msg': 'Plugin %s not registered' % plugin})
                    else:
                        hyb_plugin = self.hyb_plugins[plugin]
                    if app not in hyb_plugin['web_apis']:
                        raise ValueError('Inconsistent websocket path: %s' %
                                         client.request.path)
                    client.hyb_api_set(hyb_plugin['web_apis'][app])
                    self.open_connection_sig.emit(client.hyb_api)
                except ImportError as n:
                    self.wss_error_sig.emit({'msg': str(n)})
                    self._handleClose(client)
                    del self.connections[ready]
                    self.close_connection_sig.emit()
                    self.listeners.remove(ready)

        for failed in xList:
            if failed == self.serversocket:
                self.close()
                raise Exception('server socket failed')
            else:
                if failed not in self.connections:
                    continue
                client = self.connections[failed]
                self._handleClose(client)
                del self.connections[failed]
                self.close_connection_sig.emit()
                self.listeners.remove(failed)

    def serveforever(self):
        self.mutex.lock()
        do_run = self.do_run
        self.mutex.unlock()
        while do_run is True:
            self.serveonce()
            self.mutex.lock()
            do_run = self.do_run
            self.mutex.unlock()
        self.close()

    def stop_running(self):
        self.mutex.lock()
        self.do_run = False
        self.mutex.unlock()

    def run(self):
        self.serveforever()


class SimpleSSLWebSocketServer(SimpleWebSocketServer):

    def __init__(self, host, port, websocketclass, certfile, keyfile,
                 version=ssl.PROTOCOL_TLSv1):

        SimpleWebSocketServer.__init__(self, host, port, websocketclass)

        self.cerfile = certfile
        self.keyfile = keyfile
        self.version = version

    def close(self):
        super(SimpleSSLWebSocketServer, self).close()

    def _decorateSocket(self, sock):
        sslsock = ssl.wrap_socket(sock,
                                  server_side=True,
                                  certfile=self.cerfile,
                                  keyfile=self.keyfile,
                                  ssl_version=self.version)
        return sslsock

    def _constructWebSocket(self, sock, address):
        ws = self.websocketclass(self, sock, address)
        ws.usingssl = True
        return ws

    def serveforever(self):
        super(SimpleSSLWebSocketServer, self).serveforever()
