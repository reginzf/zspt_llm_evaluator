from src.zlpt.api.base_client import BaseClient
import time

class Project(BaseClient):
    def project_login(self, user_id, project_id):
        api = 'api/sys/oapi/v1/project/login'
        method = 'POST'
        data = {"user": {"userId": user_id, "projectId": project_id}}
        res = self.send_request(api, method, data)
        ticket = res['data']['token']
        self.sess.headers.update({'X-Auth-Token': ticket})
        # 设置cookie
        self.sess.cookies.update({"token": ticket})
        self.sess.cookies.update({"f.token": ticket})
        time.sleep(5) # 等待前端完成token同步
        return res
