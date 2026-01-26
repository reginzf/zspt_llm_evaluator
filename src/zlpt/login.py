import base64
import requests
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import urllib3
from utils.logger import logger
import threading
import time
from datetime import datetime, timedelta

urllib3.disable_warnings()
__all__ = ["LoginManager"]


class LoginManager:
    # 单例实例字典，以base_url和username作为key
    _instances = {}
    _lock = threading.Lock()  # 线程锁，确保线程安全

    def __new__(cls, base_url, username, password=None, domain="default",k1=None,k2_add=None,pk=None):
        # 使用base_url和username作为key
        key = (base_url, username)

        # 检查实例是否存在
        if key not in cls._instances:
            with cls._lock:
                # 双重检查，防止并发情况下创建多个实例
                if key not in cls._instances:
                    # 创建新实例
                    instance = super(LoginManager, cls).__new__(cls)
                    cls._instances[key] = instance

                    # 初始化实例属性
                    instance._initialized = False

        return cls._instances[key]

    def __init__(self, base_url, username, password=None, domain="default",k1=None,k2_add=None,pk=None):
        # 防止重复初始化
        if self._initialized:
            # 如果密码不同，更新密码
            if password is not None and password != self.password:
                self.password = password
                self.domain = domain
                # 重新执行登录过程
                self._perform_login(username, password, domain)
            return

        # 从代码中提取的公钥片段
        self.key1 = k1
        self.key2_addition = k2_add
        self.p = pk
        self.base_url = base_url
        self.username = username
        self.password = password
        self.domain = domain
        self.ticket = None
        self.auth_token = None

        # 初始化session
        self.session = requests.Session()
        # 初始化header
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        # 记录实例创建时间
        self._creation_time = datetime.now()

        # 如果提供了密码，执行登录
        if password is not None:
            self._perform_login(username, password, domain)

        # 启动定时检查线程
        self._timer_thread = threading.Thread(target=self._check_and_refresh, daemon=True)
        self._timer_thread.start()

        self._initialized = True

    def _perform_login(self, username, password, domain):
        """执行登录和获取认证密钥的过程"""
        self.login(username, password, domain)
        self.get_auth_key()

    def _check_and_refresh(self):
        """定时检查并刷新认证信息"""
        while True:
            # 每分钟检查一次
            time.sleep(60)

            # 检查是否超过4小时
            elapsed_time = datetime.now() - self._creation_time
            if elapsed_time > timedelta(hours=4):
                self._refresh_auth()  # 执行刷新操作

    def _refresh_auth(self):
        """刷新认证信息"""
        if self.password is not None:
            logger.info(f"Refreshing auth for {self.base_url} - {self.username}")
            self._perform_login(self.username, self.password, self.domain)
            # 更新创建时间，重置计时器
            self._creation_time = datetime.now()
        else:
            logger.warning(f"Password not provided, cannot refresh auth for {self.base_url} - {self.username}")

    def get_public_key(self):
        """组合完整的公钥"""
        key2 = self.key1 + self.key2_addition
        public_key_str = key2 + self.p
        return public_key_str

    def encrypt_password(self, password):
        """使用RSA加密密码"""
        public_key_str = self.get_public_key()

        # 构造完整的PEM格式公钥
        pem_public_key = f"-----BEGIN PUBLIC KEY-----\n{public_key_str}\n-----END PUBLIC KEY-----"

        try:
            # 加载公钥
            public_key = RSA.import_key(pem_public_key)
            # 创建加密器
            cipher = PKCS1_v1_5.new(public_key)
            # 加密密码
            encrypted = cipher.encrypt(password.encode('utf-8'))
            # Base64编码
            encrypted_b64 = base64.b64encode(encrypted).decode('utf-8')
            return encrypted_b64

        except Exception as e:
            logger.error(f"加密错误: {e}")
            return None

    def login(self, username, password, domain="default"):
        """执行登录请求"""
        # 请求URL
        url = f"{self.base_url}/api/sys/oapi/v1/double_factor/login"
        # 加密密码
        encrypted_password = self.encrypt_password(password)

        if not encrypted_password:
            logger.error("密码加密失败")
            return None
        # 构造请求体
        payload = {
            "username": username,
            "password": encrypted_password,
            "domain": domain
        }
        try:  # 发送POST请求
            response = self.session.post(
                url,
                json=payload,
                verify=False,  # 忽略SSL证书验证（因为可能是自签名证书）
                timeout=30
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"请求异常: {e}")
            return None
        try:  # 获取ticket
            ticket = response.json().get("data", {}).get("ticket")
            if ticket:
                logger.info(f'ticket: {ticket}')
                self.ticket = ticket
                self.session.headers.update({'X-Auth-Token': ticket})
            else:
                logger.warning("\n未在响应中找到 ticket 字段")
        except:
            logger.error(f"原始响应: {response.text}")
        return response

    def get_auth_key(self):
        # 获取auth_token
        response = self.session.post(
            f"{self.base_url}/api/sys/oapi/v1/double_factor/ticket",
            verify=False,
            json={"skip": False}
        )
        auth_token = response.json().get("data", {}).get("token")
        logger.info(f"auth_token: {auth_token}")
        if auth_token:
            self.auth_token = auth_token
        self.session.headers.update({'X-Auth-Token': auth_token})
        self.session.cookies.update({"token": auth_token})
        self.session.cookies.update({"f.token": auth_token})

    def login_unsafe(self, username=None, password=None):
        url = f"{self.base_url}/api/sys/auth/v1/tokens"
        payload = {"auth": {
            "identity": {"methods": ["password"], "password": {"user": {"name": username}, "password": password}}}}
        try:  # 发送POST请求
            logger.info(f"发送请求 - URL: {url}, Payload: {payload}")
            if username:
                response = self.session.post(
                    url,
                    json=payload,
                    verify=False,
                    timeout=30
                )
            else:
                response = self.session.post(
                    url,
                    verify=False,
                    timeout=30)
        except requests.exceptions.RequestException as e:
            logger.error(f"请求异常: {e}")
            return None
        logger.info(f"原始响应: {response.text}\nHEADERS:{response.headers}")
        # 处理headers:
        # self.session.headers.update({'X-Auth-Token': response.headers["X-Subject-Token"]})
        # self.session.cookies.update({"token": response.headers["X-Subject-Token"]})
        # self.session.cookies.update({"f.token": response.headers["X-Subject-Token"]})
        # 处理project
        res_dict = response.json()
        user_id = res_dict["token"]["user"]["id"]
        project_id = res_dict["token"]["project"]["id"]
        return user_id, project_id


# 使用示例
if __name__ == "__main__":
    # 创建登录管理器（使用完整的参数）
    base_url = 'https://10.220.49.200'
    username = "nrgtest"
    password = "Admin@123"
    domain = "default"

    login_manager = LoginManager(base_url, username, password, domain)

    # 测试登录（请替换为实际的用户名和密码）
    # 执行登录
    response = login_manager.login_unsafe(username, password)
    # 获取auth_token
    print(response)

    # 保持主线程运行，以便观察定时刷新功能
    try:
        while True:
            time.sleep(10)  # 主线程休眠，让后台线程运行
    except KeyboardInterrupt:
        print("程序退出")
