import base64
import requests
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import urllib3
from env_config_init import settings
urllib3.disable_warnings()
__all__ = ["LoginManager"]


class LoginManager:
    def __init__(self, base_url):
        # 从代码中提取的公钥片段
        self.key1 = settings.KEY1
        self.key2_addition = settings.KEY2_ADD
        self.p = settings.PK
        self.base_url = base_url
        self.ticket = None
        self.auth_token = None
        # 初始化session
        self.session = requests.Session()
        # 初始化header
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

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
            print(f"加密错误: {e}")
            return None

    def login(self, username, password, domain="default"):
        """执行登录请求"""
        # 请求URL
        url = f"{self.base_url}/api/sys/oapi/v1/double_factor/login"
        # 加密密码
        encrypted_password = self.encrypt_password(password)

        if not encrypted_password:
            print("密码加密失败")
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
            print(f"请求异常: {e}")
            return None
        try:  # 获取ticket
            ticket = response.json().get("data", {}).get("ticket")
            if ticket:
                print(f'ticket: {ticket}')
                self.ticket = ticket
                self.session.headers.update({'X-Auth-Token': ticket})
            else:
                print("\n未在响应中找到 ticket 字段")
        except:
            print(f"原始响应: {response.text}")
        return response

    def get_auth_key(self):
        # 获取auth_token
        response = self.session.post(
            f"{self.base_url}/api/sys/oapi/v1/double_factor/ticket",
            verify=False,
            json={"skip": False}
        )
        auth_token = response.json().get("data", {}).get("token")
        print(f"auth_token: {auth_token}")
        if auth_token:
            self.auth_token = auth_token
        self.session.headers.update({'X-Auth-Token': auth_token})


# 使用示例
if __name__ == "__main__":
    # 创建登录管理器
    login_manager = LoginManager('https://10.220.49.200')
    # 测试登录（请替换为实际的用户名和密码）
    username = "nrgtest"
    password = "Admin@123"
    domain = "default"

    # 执行登录
    response = login_manager.login(username, password, domain)
    # 获取auth_token
    response = login_manager.get_auth_key()
