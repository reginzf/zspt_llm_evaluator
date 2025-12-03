import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

__all__ = ['BaseClient', 'ApiBase']


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


class BaseClient(ApiBase):

    def __init__(self, login_user):
        super().__init__(login_user)
        self.network_request_map = {'get': self._get, 'post': self._post, 'delete': self._delete, 'put': self._put,
                                    'get_file': self._get_file}

    def call_request(self, uri, method, data, headers, _name, auth):
        if method in ('get', 'get_file'):
            return self.network_request_map[method](uri, headers=headers, auth=auth)
        else:
            return self.network_request_map[method](uri, data=data, headers=headers, auth=auth)

    def send_request(self, api, method, data={}, headers=None, _name=None, auth=None, **kwargs) -> dict:

        method = method.lower()
        # 处理parse
        if kwargs:
            uri = "/{api}?{params}".format(api=api, params='&'.join(
                ["{key}={value}".format(key=key, value=value) for key, value in kwargs.items()]))
        else:
            uri = "/{api}".format(api=api)
        try:
            res = self.call_request(uri, method, data, headers, _name, auth)
        except Exception as e:
            return {'msg': '调用接口失败', 'uri': uri, 'data': data, 'e': e.__context__}
        try:
            res = json.loads(res.content.decode("utf-8"))
        except Exception as e:
            return res
        return res
