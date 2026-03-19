import base64
import requests
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import urllib3
from src.utils.logger import logger
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

urllib3.disable_warnings()
__all__ = ["LoginManager"]

class LoginManager:
    _instances = {}
    _lock = threading.Lock()

    def __new__(cls, base_url, username, password=None, domain="default", k1=None, k2_add=None, pk=None):
        key = (base_url, username)
        if key not in cls._instances:
            with cls._lock:
                if key not in cls._instances:
                    instance = super().__new__(cls)
                    cls._instances[key] = instance
                    instance._initialized = False
        return cls._instances[key]

    def __init__(self, base_url, username, password=None, domain="default", k1=None, k2_add=None, pk=None):
        if self._initialized:
            if password and password != self.password:
                self.password = password
                self.domain = domain
                self._perform_login(username, password, domain)
            return

        self.key1 = k1
        self.key2_addition = k2_add
        self.p = pk
        self.base_url = base_url
        self.username = username
        self.password = password
        self.domain = domain
        self.ticket = None
        self.auth_token = None
        self.current_project_id = None

        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        self._creation_time = datetime.now()

        if password:
            self._perform_login(username, password, domain)

        self._timer_thread = threading.Thread(target=self._check_and_refresh, daemon=True)
        self._timer_thread.start()

        self._initialized = True

    def _perform_login(self, username, password, domain):
        self.login(username, password, domain)
        self.get_auth_key()
        self.project_switch()

    def _check_and_refresh(self):
        while True:
            time.sleep(60)
            if datetime.now() - self._creation_time > timedelta(hours=4):
                self._refresh_auth()

    def _refresh_auth(self):
        if self.password:
            logger.info(f"Refreshing auth for {self.base_url} - {self.username}")
            self._perform_login(self.username, self.password, self.domain)
            self._creation_time = datetime.now()
        else:
            logger.warning(f"Password not provided, cannot refresh auth for {self.base_url} - {self.username}")

    def get_public_key(self):
        return self.key1 + self.key2_addition + self.p

    def encrypt_password(self, password):
        try:
            public_key = RSA.import_key(f"-----BEGIN PUBLIC KEY-----\n{self.get_public_key()}\n-----END PUBLIC KEY-----")
            cipher = PKCS1_v1_5.new(public_key)
            encrypted = cipher.encrypt(password.encode('utf-8'))
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return None

    def login(self, username, password, domain="default"):
        url = f"{self.base_url}/api/sys/oapi/v1/double_factor/login"
        encrypted_password = self.encrypt_password(password)

        if not encrypted_password:
            logger.error("Password encryption failed")
            return None

        try:
            response = self.session.post(url, json={"username": username, "password": encrypted_password, "domain": domain}, verify=False, timeout=30)
            ticket = response.json().get("data", {}).get("ticket")
            if ticket:
                logger.info(f'Ticket: {ticket}')
                self.ticket = ticket
                self.session.headers.update({'X-Auth-Token': ticket})
            else:
                logger.warning("Ticket not found in response")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return None

    def get_auth_key(self):
        try:
            response = self.session.post(f"{self.base_url}/api/sys/oapi/v1/double_factor/ticket", verify=False, json={"skip": False})
            auth_token = response.json().get("data", {}).get("token")
            if auth_token:
                logger.info(f"Auth token: {auth_token}")
                self.auth_token = auth_token
                self.session.headers.update({'X-Auth-Token': auth_token})
                self.session.cookies.update({"token": auth_token, "f.token": auth_token})
        except Exception as e:
            logger.error(f"Auth key retrieval error: {e}")

    def project_switch(self, project_id: str = None) -> bool:
        """
        切换项目，支持自动检测和切换到非default项目

        Args:
            project_id: 指定要切换到的项目ID，None则自动选择

        Returns:
            bool: 切换是否成功
        """
        try:
            # 如果已经有 auth_token 并且不需要切换项目，验证当前项目状态
            if self.auth_token and not project_id:
                project_info = self.verify_current_project()
                if not project_info["is_default"]:
                    logger.info(f"使用已认证的 token，当前项目: {project_info['current_project_name']}")
                    self.current_project_id = project_info["current_project_id"]
                    return True
                # 是default项目，需要切换
                logger.info("当前为default项目，准备切换到非default项目")
                return self.auto_switch_project()

            # 如果指定了项目ID，直接切换
            if project_id:
                return self.switch_to_project(project_id)

            # 否则尝试自动切换
            return self.auto_switch_project()

        except Exception as e:
            logger.error(f"项目切换过程中发生错误: {e}")
            return False

    def get_current_project(self) -> str:
        return getattr(self, 'current_project_id', None)

    def login_unsafe(self, username=None, password=None):
        url = f"{self.base_url}/api/sys/auth/v1/tokens"
        payload = {"auth": {"identity": {"methods": ["password"], "password": {"user": {"name": username}, "password": password}}}}

        try:
            response = self.session.post(url, json=payload if username else None, verify=False, timeout=30)
            res_dict = response.json()
            domain_name = res_dict["token"]["user"]["domain"]
            project_name = res_dict["token"]["project"]["name"]
            if domain_name == 'default' and project_name == 'default-project':

                return None,None
            user_id = res_dict["token"]["user"]["id"]
            project_id = res_dict["token"]["project"]["id"]
            return user_id, project_id
        except Exception as e:
            logger.error(f"Unsafe login error: {e}")
            return None, None

    def get_project_list(self, user_id: str = None) -> List[Dict]:
        """
        获取用户可选的项目列表

        Args:
            user_id: 用户ID，不提供则尝试通过 login_unsafe 获取

        Returns:
            List[Dict]: 项目列表，每个项目包含 id, name, parent_id, children 等信息
        """
        try:
            # 如果没有提供 user_id，尝试获取
            if not user_id:
                user_id, _ = self.login_unsafe(self.username, self.password)
                if not user_id:
                    logger.error("无法获取 user_id，无法获取项目列表")
                    return []

            # 使用 /api/sys/oapi/v1/users/{user_id}/projects 获取当前用户可访问的项目列表
            timestamp = int(time.time() * 1000)
            url = f"{self.base_url}/api/sys/oapi/v1/users/{user_id}/projects?t={timestamp}"
            response = self.session.get(url, verify=False, timeout=30)

            if response.status_code == 200:
                res_data = response.json()
                # 新接口返回格式: {"status": "", "code": "", "data": [...], "msg": ""}
                if res_data.get('data') is not None:
                    projects = res_data['data']
                    logger.info(f"获取到 {len(projects)} 个可选项目")
                    return projects
                else:
                    logger.warning(f"获取项目列表返回异常: {res_data}")
                    return []
            else:
                logger.error(f"获取项目列表失败: HTTP {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"获取项目列表时发生错误: {e}")
            return []

    def verify_current_project(self) -> Dict:
        """
        验证当前项目信息

        Returns:
            Dict: 包含当前项目信息的字典
            {
                "is_default": bool,  # 是否为default项目
                "current_project_id": str,
                "current_project_name": str,
                "available_projects": List[Dict]  # 可选项目列表
            }
        """
        try:
            # 使用 /api/sys/auth/v1/tokens 获取当前登录信息和项目
            url = f"{self.base_url}/api/sys/auth/v1/tokens"
            response = self.session.get(url, verify=False, timeout=30)

            result = {
                "is_default": True,
                "current_project_id": None,
                "current_project_name": None,
                "available_projects": []
            }

            user_id = None
            if response.status_code == 200:
                res_data = response.json()
                if res_data.get('token') and res_data['token'].get('project'):
                    project_info = res_data['token']['project']
                    project_id = project_info.get('id')
                    project_name = project_info.get('name')
                    domain_name = res_data['token'].get('user', {}).get('domain', 'default')
                    user_id = res_data['token'].get('user', {}).get('id')

                    result["current_project_id"] = project_id
                    result["current_project_name"] = project_name
                    result["is_default"] = (domain_name == 'default' and project_name == 'default-project')

                    logger.info(f"当前项目: {project_name} (ID: {project_id}), 是否为default: {result['is_default']}")

            # 获取可选项目列表（传入 user_id）
            available_projects = self.get_project_list(user_id)
            result["available_projects"] = available_projects

            return result

        except Exception as e:
            logger.error(f"验证当前项目时发生错误: {e}")
            return {
                "is_default": True,
                "current_project_id": None,
                "current_project_name": None,
                "available_projects": []
            }

    def switch_to_project(self, project_id: str) -> bool:
        """
        切换到指定项目

        Args:
            project_id: 目标项目ID

        Returns:
            bool: 切换是否成功
        """
        try:
            if not project_id:
                logger.error("项目ID不能为空")
                return False

            # 获取当前用户信息（user_id 和 current_project_id）
            user_id, current_project_id = self.login_unsafe(self.username, self.password)

            if not user_id:
                logger.error("无法获取用户信息，无法切换项目")
                return False

            # 调用项目切换API
            switch_data = {"user": {"userId": user_id, "projectId": project_id}}
            switch_url = f"{self.base_url}/api/sys/oapi/v1/project/login"

            logger.info(f"正在切换到项目: {project_id}")
            response = self.session.post(switch_url, json=switch_data, verify=False, timeout=30)

            if response.status_code == 200:
                res_data = response.json()
                if res_data.get('data') and res_data['data'].get('token'):
                    new_token = res_data['data']['token']
                    self.current_project_id = project_id
                    self.auth_token = new_token
                    self.session.headers.update({'X-Auth-Token': new_token})
                    self.session.cookies.update({"token": new_token, "f.token": new_token})
                    logger.info(f"成功切换到项目: {project_id}")
                    return True
                else:
                    logger.error(f"项目切换响应缺少token: {res_data}")
                    return False
            else:
                logger.error(f"项目切换失败: HTTP {response.status_code}, {response.text}")
                return False

        except Exception as e:
            logger.error(f"切换项目时发生错误: {e}")
            return False

    def auto_switch_project(self, target_project_id: str = None) -> bool:
        """
        自动检测并切换到非default项目

        Args:
            target_project_id: 目标项目ID，如果不提供则自动选择第一个非default项目

        Returns:
            bool: 切换是否成功
        """
        try:
            # 1. 验证当前项目
            project_info = self.verify_current_project()

            # 如果当前不是default项目，无需切换
            if not project_info["is_default"]:
                logger.info(f"当前项目 {project_info['current_project_name']} 不是default项目，无需切换")
                self.current_project_id = project_info["current_project_id"]
                return True

            # 2. 如果没有指定目标项目，从可选项目中选择第一个非default项目
            if not target_project_id:
                available_projects = project_info.get("available_projects", [])
                for project in available_projects:
                    # 新接口返回的字段名: name (原projectName), id (原projectId)
                    proj_name = project.get("name", "")
                    proj_id = project.get("id", "")
                    # 跳过default项目
                    if proj_name != "default-project" and proj_id:
                        target_project_id = proj_id
                        logger.info(f"自动选择非default项目: {proj_name} (ID: {proj_id})")
                        break

            if not target_project_id:
                logger.warning("没有找到可切换的非default项目")
                return False

            # 3. 执行项目切换
            return self.switch_to_project(target_project_id)

        except Exception as e:
            logger.error(f"自动切换项目时发生错误: {e}")
            return False

    def refresh_auth_token(self) -> bool:
        """
        刷新认证token

        Returns:
            bool: 刷新是否成功
        """
        try:
            logger.info("开始刷新认证token")
            if not self.password:
                logger.warning("密码未提供，无法刷新认证")
                return False

            # 重新执行完整的登录流程
            self._perform_login(self.username, self.password, self.domain)
            logger.info("认证token刷新成功")
            return True

        except Exception as e:
            logger.error(f"刷新认证token时发生错误: {e}")
            return False

if __name__ == "__main__":
    base_url = 'https://10.220.49.203'
    username = "beibei-xm"
    password = "!QAZ2wsx"
    domain = "default"

    login_manager = LoginManager(base_url, username, password, domain,
                                 'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCbPqaFZ0lgebihx',
                                 'Cw5wzjkahPKr6ZI2JNTHbHDnNbOn3Cif6GgnMBr44MhQCRPQTF2FgcxBbn3u7eGcEPMT6OZqcLzcmiMCUQRJ2MUbFI+',
                                 'E1vI1f+iuCQ2w8XZhRoRrmb7wBA0L63gnSwXRkJD0baL5zqlQhpSKfSH0t3opAoahwIDAQAB')

    response = login_manager.login_unsafe(username, password)
    print(response)
    login_manager.get_project_list()
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("Program exited")
