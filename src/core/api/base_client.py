from src.core.base import ApiBase
import json

__all__ = ['BaseClient']


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
