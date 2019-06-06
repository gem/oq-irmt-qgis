# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2016-06-29
#        copyright            : (C) 2018 by GEM Foundation
#        email                : devops@openquake.org
# ***************************************************************************/
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

from uuid import uuid4
from qgis.PyQt.QtCore import QObject
from qgis.core import Qgis
from qgis.PyQt.QtCore import pyqtSignal
from hybridge.utilities.utils import log_msg


class WebApi(QObject):
    caller_sig = pyqtSignal('QVariantMap')
    send_to_wss_sig = pyqtSignal('QVariantMap', 'QVariantMap')
    unload_sig = pyqtSignal('QVariantMap')

    def __init__(self, plugin, plugin_name, app_name,
                 action, message_bar, parent=None):
        assert app_name is not None
        super().__init__(parent)
        self.plugin = plugin
        self.plugin_name = plugin_name
        self.app_name = app_name
        self.action = action
        self.message_bar = message_bar
        self.allowed_meths = [
            'window_open', 'ext_app_open', 'set_cells',
            'notify_click', 'info', 'warning', 'error',
            'hybridge_apptrack_status']
        self.pending = {}
        self.apptrack_status_pend = []

    def run_command(self, command, args, cb=None, reg=None):
        print('run_command on %s: %s(%s)' % (self.app_name, command, args))
        # called when caller plugin wants to send a command to the websocket
        if command not in self.allowed_meths:
            return (False, 'Method "%s" not allowed' % command)
        uuid = uuid4().urn[9:]
        api_msg = {
            'uuid': uuid,
            'msg': {
                'command': command,
                'args': args
            }
        }
        # MN: FIXME ws_info is missing
        self.send(api_msg, None)
        api_msg['cb'] = cb
        self.pending[uuid] = api_msg
        if reg is not None:
            reg(uuid)
        return (True, uuid)

    def receive(self, api_msg, ws_info):
        # it happens when the websocket receives a message
        api_uuid = api_msg['uuid']
        if 'reply' in api_msg:
            app_msg = api_msg['reply']
            uuid = api_msg['uuid']
            if uuid in self.pending:
                pend = self.pending[uuid]
                print("Command pending found [%s]" % uuid)
                if pend['cb']:
                    pend['cb'](uuid, pend['msg'], app_msg)
                if ('complete' not in app_msg or
                        app_msg['complete'] is True):
                    print("Command pending deleted [%s]" % uuid)
                    del self.pending[uuid]
            return
        else:
            app_msg = api_msg['msg']
            command = app_msg['command']
            if command not in self.allowed_meths:
                api_reply = {
                    'uuid': api_uuid,
                    'reply': {
                        'success': False,
                        'msg': 'Method "%s" not allowed' % command
                    }
                }
                self.send(api_reply, ws_info)
                return

            args = app_msg['args']
            meth = getattr(self, command)

            # FIXME: manage command exception
            ret = meth(api_uuid, *args)
            if isinstance(ret, tuple):
                app_msg = {'result': ret[0], 'complete': ret[1]}
            else:
                app_msg = {'result': ret, 'complete': True}

            api_reply = {'uuid': api_uuid, 'reply': app_msg}
            self.send(api_reply, ws_info)

    def send(self, api_msg, ws_info):
        # it sends a message to the websocket
        hyb_msg = {'app': self.app_name, 'msg': api_msg}
        # self.wss.caller.send_to_wss_sig.emit(hyb_msg)
        self.send_to_wss_sig.emit(hyb_msg, ws_info)

    # apptrack_status

    def apptrack_status_reg(self, uuid):
        self.apptrack_status_pend.append(uuid)
        print('Registering apptrack_status for %s' % uuid)

    def apptrack_status_cb(self, uuid, pend_msg, reply):
        print('%s: apptrack_status_cb: %s' % (self.app_name, reply['success']))
        self.set_app_icon(reply['success'])

    def set_app_icon(self, connected):
        if self.action is None:  # e.g. taxonomy has no toolbar button
            return
        if connected:
            self.action.setIcon(self.icon_connected)
        else:
            self.action.setIcon(self.icon_standard)

    def apptrack_status(self):
        success, err_msg = self.run_command(
            'hybridge_apptrack_status', (), cb=self.apptrack_status_cb)
        print(success, err_msg)

    def apptrack_status_cleanup(self):
        print('apptrack_status_cleanup')
        for uuid in self.apptrack_status_pend:
            print('Deleting %s' % uuid)
            del self.pending[uuid]
        self.apptrack_status_pend = []

    # API

    # Deprecated
    def ext_app_open(self, api_uuid, content):
        # FIXME: the name is misleading. This method just prints in the message
        # bar a string specified in the first arg
        msg = "%s ext_app_open: %s" % (self.app_name, content)
        log_msg(msg, message_bar=self.message_bar)
        return {'ret': 0, 'content': None, 'reason': 'ok'}

    # FIXME: adapt the following to the new websocket approach

    # # take a javascript object and return string
    # # javascript objects come into python as dictionaries
    # # functions are represented by an empty dictionary
    # @pyqtSlot('QVariantMap', result=str)
    # def json_encode(self, jsobj):
    #     # import is here to keep it separate from 'required' import
    #     return json.dumps(jsobj)

    # # take a string and return an object (which is represented in python
    # # by a dictionary
    # @pyqtSlot(str, result='QVariantMap')
    # def json_decode(self, jsstr):
    #     return json.loads(jsstr)

    def notify_click(self, api_uuid):
        self.info(api_uuid, "Clicked!")
        return {'ret': 0, 'content': None, 'reason': 'ok'}

    def success(self, api_uuid, message):
        self.message_bar.pushMessage(message, level=Qgis.Success)
        return {'ret': 0, 'content': None, 'reason': 'ok'}

    def info(self, api_uuid, message):
        self.message_bar.pushMessage(message, level=Qgis.Info)
        return {'ret': 0, 'content': None, 'reason': 'ok'}

    def warning(self, api_uuid, message):
        self.message_bar.pushMessage(message, level=Qgis.Warning)
        return {'ret': 0, 'content': None, 'reason': 'ok'}

    def error(self, api_uuid, message):
        self.message_bar.pushMessage(message, level=Qgis.Critical)
        return {'ret': 0, 'content': None, 'reason': 'ok'}

    # @pyqtSlot(result=int)
    # def dummy_property_get(self):
    #     "A getter must be defined to access instance properties"
    #     return self.dummy_property
