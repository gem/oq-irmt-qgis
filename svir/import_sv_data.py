import requests


class SvDownloadError(Exception):
    pass


class SvDownloader(object):
    def __init__(self, host, api_method):
        self.host = host
        self._login = host + '/account/login/'
        # FIXME Change exposure to sv when app is ready on platform
        self._page = host + api_method
        self.sess = requests.Session()
        self.sess.headers.update({'Referer': self._login})

    def login(self, username, password):
        session_resp = self.sess.get(self._login)
        if session_resp.status_code != 200:  # 200 means successful:OK
            # TODO: Display it on GUI
            print ("Unable to get session for login: status code ",
                   session_resp.status_code)
            raise SvDownloadError(session_resp.content)
        data = dict(username=username, password=password)
        login_resp = self.sess.post(self._login, data=data)
        if login_resp.status_code != 302:  # 302 = means redirect:found
            # TODO: Display it on GUI
            print "Unable to login and redirect to page: status code %s" % \
                login_resp.status_code
            raise SvDownloadError(login_resp.content)

    def get_items(self):
        items = []
        result = self.sess.get(self._page)
        if result.status_code == 200:
            items = [l for l in result.content.splitlines() if l[0] != "#"]
        return items
