import json
from uuid import uuid4


class WebApp(object):

    def __init__(self):
        raise NotImplementedError()

    def open_webapp(self):
        data = {
            "app": "app_one",  # FIXME self.app_name,
            "msg": {
                "uuid": uuid4().get_urn()[9:],
                "msg": {
                    "command": "window_open",
                    "args": []}
                }
        }
        data_js = json.dumps(data)
        data_js_unicode = unicode(data_js, "utf-8")
        self.wss.send_message(data_js_unicode)
