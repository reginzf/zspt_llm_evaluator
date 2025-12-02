import datetime
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def data_pretreat(data):
    date_type = type(data)
    if (date_type is dict) or (date_type is list):
        return json.dumps(data)
    else:
        return data

class ApiBase(object):
    def __init__(self, login_user):
        self.user = login_user
        self.base_url = self.user.base_url
        self.sess = self.user.session

    def _get(self, uri, headers=None, auth=None):
        url = self.base_url + uri
        if headers is None:
            headers = self.sess.headers
        response = self.sess.get(url, headers=headers, verify=False, auth=auth)
        return response

    def _post(self, uri, data, headers=None, auth=None):
        url = self.base_url + uri
        if headers is None:
            headers = self.sess.headers
        response = self.sess.post(url, data=data_pretreat(data), headers=headers, verify=False, auth=auth)
        return response

    def _put(self, uri, data=None, headers=None, auth=None):
        url = self.base_url + uri
        if headers is None:
            headers = self.sess.headers
        response = self.sess.put(url, data=data_pretreat(data), headers=headers, verify=False, auth=auth)
        return response

    def _delete(self, uri, data=None, headers=None, auth=None):
        url = self.base_url + uri
        if headers is None:
            headers = self.sess.headers
        response = self.sess.delete(url, data=data_pretreat(data), headers=headers, verify=False, auth=auth)
        return response

    def _patch(self, uri, data, headers=None, name=None, auth=None):
        url = self.base_url + uri
        if headers is None:
            headers = self.sess.headers
        response = self.sess.patch(url, data=data_pretreat(data), headers=headers, verify=False, auth=auth)
        return response

    def _get_file(self, uri, headers=None, name=None, auth=None):
        url = self.base_url + uri
        if headers is None:
            headers = self.sess.headers
        response = self.sess.get(url, headers=headers, verify=False, auth=auth)

        return response

    def _put_file(self, uri, data=None, headers=None, name=None, auth=None):
        url = self.base_url + uri
        if headers is None:
            headers = self.sess.headers
        response = self.sess.put(url, data=data_pretreat(data), headers=headers, verify=False, auth=auth)
        return response



