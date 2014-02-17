import os
import tempfile
import requests


class SvDownloadError(Exception):
    pass


class SvDownloader(object):
    def __init__(self, host):
        self.host = host
        self._login = host + '/account/login/'
        #self._login = host + 'http://localhost:8000/account/login/?next=/8000/accounts/login/'
        self._page = host + '/exposure/export_sv_themes'
        self.sess = requests.Session()
        self.sess.headers.update({'Referer': self._login})

    def login(self, username, password):
        resp = self.sess.get(self._login)
        data = dict(username=username, password=password,
                    #csrfmiddlewaretoken=resp.cookies['csrftoken'])
                    )
        post_resp = self.sess.post(self._login, data=data)

    def download(self):
        """Download the data in CSV format and return the filename"""
        result = self.sess.get(self._page)
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
