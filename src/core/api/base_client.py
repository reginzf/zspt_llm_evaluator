import json
import urllib3
import mimetypes
from requests_toolbelt.multipart.encoder import MultipartEncoder

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
                                    'get_file': self._get_file, 'patch': self._patch}

    def call_request(self, uri, method, data, headers, _name, auth):
        if method in ('get', 'get_file'):
            return self.network_request_map[method](uri, headers=headers, auth=auth)
        else:
            return self.network_request_map[method](uri, data=data, headers=headers, auth=auth)

    def send_request(self, api, method, data={}, headers=None, files=None, _name=None, auth=None, **kwargs) -> dict:
        """
               发送HTTP请求，支持multipart/form-data文件上传

               Args:
                   api: API路径
                   method: HTTP方法
                   data: 请求数据（JSON格式）
                   headers: 请求头
                   _name: 请求名称
                   auth: 认证信息
                   files: 文件上传参数，格式为字典：
                         {
                             'field_name': ('filename', file_content, 'mime_type'),
                             'field_name2': ('filename2', file_content2, 'mime_type2')
                         }
                   **kwargs: 查询参数

               Returns:
                   响应结果字典
               """
        method = method.lower()
        # 处理parse
        if kwargs:
            uri = "/{api}?{params}".format(api=api, params='&'.join(
                ["{key}={value}".format(key=key, value=value) for key, value in kwargs.items()]))
        else:
            uri = "/{api}".format(api=api)
        try:
            # 如果有文件上传，使用multipart/form-data
            if files:
                res = self.call_request_multipart(uri, method, data, files, headers, _name, auth)
            else:
                res = self.call_request(uri, method, data, headers, _name, auth)
        except Exception as e:
            return {'msg': '调用接口失败', 'uri': uri, 'data': data, 'e': str(e)}
        try:
            res = json.loads(res.content.decode("utf-8"))
        except Exception as e:
            return {'msg': '响应解析失败', 'content': res.content, 'e': str(e)}

        return res

    def call_request_multipart(self, uri, method, data, files, headers=None, _name=None, auth=None):
        """
        发送multipart/form-data请求

        Args:
            uri: 请求URI
            method: HTTP方法
            data: 表单数据
            files: 文件数据
            headers: 请求头
            _name: 请求名称
            auth: 认证信息

        Returns:
            响应对象
        """
        # 构建multipart数据
        multipart_data = {}

        # 添加表单数据
        for key, value in data.items():
            multipart_data[key] = str(value)

        # 添加文件数据
        for field_name, file_info in files.items():
            if isinstance(file_info, tuple):
                if len(file_info) == 2:
                    # (filename, file_content)
                    filename, content = file_info
                    mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
                    multipart_data[field_name] = (filename, content, mime_type)
                elif len(file_info) == 3:
                    # (filename, file_content, mime_type)
                    multipart_data[field_name] = file_info
                else:
                    raise ValueError(f"Invalid file info format for field '{field_name}'")
            else:
                # 如果是文件路径或文件对象
                multipart_data[field_name] = self._prepare_file(field_name, file_info)

        # 创建MultipartEncoder
        encoder = MultipartEncoder(fields=multipart_data)
        # 设置请求头
        if headers is None:
            headers = {}
        # 添加multipart特定的headers
        headers['Content-Type'] = encoder.content_type
        # 发送请求
        self.call_request(uri, method, encoder, headers, _name, auth)

    def _prepare_file(self, field_name, file_info):
        """
        准备文件数据

        Args:
            field_name: 字段名
            file_info: 文件信息，可以是文件路径、文件对象或字节内容

        Returns:
            (filename, content, mime_type) 元组
        """
        import os

        if isinstance(file_info, str):
            # 文件路径
            if not os.path.exists(file_info):
                raise FileNotFoundError(f"File not found: {file_info}")

            filename = os.path.basename(file_info)
            with open(file_info, 'rb') as f:
                content = f.read()
            mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'

        elif hasattr(file_info, 'read'):
            # 文件对象
            filename = getattr(file_info, 'name', field_name)
            content = file_info.read()
            mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'

        elif isinstance(file_info, bytes):
            # 字节内容
            filename = field_name
            content = file_info
            mime_type = 'application/octet-stream'

        else:
            raise ValueError(f"Unsupported file type for field '{field_name}': {type(file_info)}")

        return (filename, content, mime_type)
