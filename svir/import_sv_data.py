import os
import tempfile
import requests

# FIXME Change exposure to sv when app is ready on platform
PLATFORM_EXPORT_SV_ITEMS = "/svir/export_sv_items"
PLATFORM_EXPORT_SV_DATA_BY_INDICES = "/svir/export_sv_data_by_indices"


class SvDownloadError(Exception):
    pass


class SvDownloader(object):
    def __init__(self, host):
        self.host = host
        self._login = host + '/account/ajax_login'
        self.sess = requests.Session()

    def login(self, username, password):
        session_resp = self.sess.post(self._login,
                                      data={
                                          "username": username,
                                          "password": password
                                      })
        if session_resp.status_code != 200:  # 200 means successful:OK
            error_message = ('Unable to get session for login: %s' %
                             session_resp.content)
            raise SvDownloadError(error_message)

    def get_items(self, theme=None, subtheme=None, tag=None):
        page = self.host + PLATFORM_EXPORT_SV_ITEMS
        params = dict(theme=theme, subtheme=subtheme, tag=tag)
        items = []
        result = self.sess.get(page, params=params)
        if result.status_code == 200:
            items = [l for l in result.content.splitlines()
                     if l and l[0] != "#"]
        return items

    def get_data_by_indices(self, indices):
        page = self.host + PLATFORM_EXPORT_SV_DATA_BY_INDICES
        params = dict(indices=indices)
        result = self.sess.get(page, params=params)
        if result.status_code == 200:
            # save csv on a temporary file
            fd, fname = tempfile.mkstemp(suffix='.csv')
            os.close(fd)
            with open(fname, 'w') as csv:
                csv.write(result.content)
                msg = 'Downloaded %d lines into %s' % (
                    result.content.count('\n'), fname)
                return fname, msg
        else:
            raise SvDownloadError(result.content)
