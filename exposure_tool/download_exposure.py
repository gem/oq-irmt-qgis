import os
import tempfile
import requests


class ExposureDownloadError(Exception):
    pass


class ExposureDownloader(object):
    def __init__(self, host):
        self.host = host
        self._login = host + '/accounts/login/'
        self._page = host + '/exposure/export_population'
        self.sess = requests.Session()
        self.sess.headers.update({'Referer': self._login})

    def login(self, username, password):
        resp = self.sess.get(self._login)
        data = dict(username=username, password=password,
                    csrfmiddlewaretoken=resp.cookies['csrftoken'])
        self.sess.post(self._login, data=data)

    def download(self, lat1, lng1, lat2, lng2):
        """Download the data in CSV format and return the filename"""
        params = dict(
            outputType='csv', lat1=lat1, lng1=lng1, lat2=lat2, lng2=lng2)
        result = self.sess.get(self._page, params=params)
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
            raise ExposureDownloadError(result.content)
