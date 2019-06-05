'''
The MIT License (MIT)
Copyright (c) 2013 Dave P.
'''
import sys
import ssl
import json
from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot, QThread, QMutex
import socket
from select import select
from hybridge.websocket.web_socket import WebSocket, CLOSE


class CloseSocketException(Exception):
    pass


class SimpleWebSocketServer(QThread):
    wss_error_sig = pyqtSignal('QVariantMap')
    from_socket_received = pyqtSignal('QVariantMap', 'QVariantMap')
    from_socket_sent = pyqtSignal('QVariantMap')
    open_connection_sig = pyqtSignal('QVariantMap')
    close_connection_sig = pyqtSignal('QVariantMap')

    def __init__(self, host, port, selectInterval=0.1):
        self.websocketclass = WebSocket
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

    @pyqtSlot('QVariantMap')
    def handle_caller_sig(self, data):
        print('From caller_sig: %s' % data)

    @pyqtSlot('QVariantMap', 'QVariantMap')
    def send_to_wss(self, hyb_msg, ws_info):
        hyb_msg_str = json.dumps(hyb_msg)
        ret = False
        for fileno, conn in list(self.connections.items()):
            if conn == self.serversocket:
                continue
            if conn.info['uuid'] != ws_info['uuid']:
                continue
            conn.sendMessage(hyb_msg_str)
            ret = True
            break
        if ret is False:
            app = hyb_msg['app']
            self.wss_error_sig.emit(
                {'app': app, 'msg': 'Send failed! No connections'})

    def handle_socket_received(self, data, ws_info):
        try:
            hyb_msg = self._loads(data)
        except ValueError:
            print('Malformed msg: [%s]' % data)
            return
        self.from_socket_received.emit(hyb_msg, ws_info)

    def handle_socket_sent(self, data):
        try:
            hyb_msg = self._loads(data)
        except ValueError:
            print('Malformed msg: [%s]' % data)
            return
        self.from_socket_sent.emit(hyb_msg)

    def _loads(self, data):
        hyb_msg = json.loads(data)
        if ('app' not in hyb_msg
                or hyb_msg['app'] not in self.caller.web_apis
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
                            raise CloseSocketException('received client close')

            except Exception as n:
                if not isinstance(n, CloseSocketException):
                    self.wss_error_sig.emit({'msg': str(n)})
                self._handleClose(client)
                del self.connections[ready]
                # already done in web_socket.handleClose
                # self.close_connection_sig.emit()
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
                    # MN: moved to web_socket where the pin/api couple is clear
                    # self.open_connection_sig.emit()
                    self.listeners.append(fileno)
                except Exception as n:
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
                except Exception as n:
                    self.wss_error_sig.emit({'msg': str(n)})
                    self._handleClose(client)
                    del self.connections[ready]
                    # aleady done in socket.handleClose
                    # self.close_connection_sig.emit()
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
                # aleady done in socket.handleClose
                # self.close_connection_sig.emit()
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

    def api_register(self, api):
        api.caller_sig['QVariantMap'].connect(self.handle_caller_sig)
        api.send_to_wss_sig['QVariantMap',
                            'QVariantMap'].connect(self.send_to_wss)

    def api_unregister(self, api):
        api.caller_sig['QVariantMap'].disconnect(self.handle_caller_sig)
        api.send_to_wss_sig['QVariantMap',
                            'QVariantMap'].disconnect(self.send_to_wss)


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
