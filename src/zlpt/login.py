import base64
import requests
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import urllib3
from src.utils.logger import logger
import threading
import time
from datetime import datetime, timedelta

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
        try:
            user_id, current_project_id = self.login_unsafe(self.username, self.password)
            if not user_id:
                logger.error("Failed to retrieve user info")
                return False

            switch_data = {"user": {"userId": user_id, "projectId": current_project_id}}
            switch_url = f"{self.base_url}/api/sys/oapi/v1/project/login"

            response = self.session.post(switch_url, json=switch_data, verify=False, timeout=30)
            if response.status_code == 200:
                logger.info(f"Successfully switched to project: {project_id}")
                res_json_token = response.json()['data']['token']
                self.current_project_id = project_id
                self.session.headers.update({'X-Auth-Token': res_json_token})
                self.session.cookies.update({"token": res_json_token, "f.token": res_json_token})
                return True
            else:
                logger.error(f"Project switch failed with status code: {response.status_code}")
                logger.error(f"Response content: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error during project switch: {e}")
            return False

    def get_current_project(self) -> str:
        return getattr(self, 'current_project_id', None)

    def login_unsafe(self, username=None, password=None):
        url = f"{self.base_url}/api/sys/auth/v1/tokens"
        payload = {"auth": {"identity": {"methods": ["password"], "password": {"user": {"name": username}, "password": password}}}}

        try:
            response = self.session.post(url, json=payload if username else None, verify=False, timeout=30)
            res_dict = response.json()
            user_id = res_dict["token"]["user"]["id"]
            project_id = res_dict["token"]["project"]["id"]
            return user_id, project_id
        except Exception as e:
            logger.error(f"Unsafe login error: {e}")
            return None, None

if __name__ == "__main__":
    base_url = 'https://10.220.49.203'
    username = "nrgautotest"
    password = "Admin@123"
    domain = "default"

    login_manager = LoginManager(base_url, username, password, domain,
                                 'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCbPqaFZ0lgebihx',
                                 'Cw5wzjkahPKr6ZI2JNTHbHDnNbOn3Cif6GgnMBr44MhQCRPQTF2FgcxBbn3u7eGcEPMT6OZqcLzcmiMCUQRJ2MUbFI+',
                                 'E1vI1f+iuCQ2w8XZhRoRrmb7wBA0L63gnSwXRkJD0baL5zqlQhpSKfSH0t3opAoahwIDAQAB')

    response = login_manager.login_unsafe(username, password)
    print(response)

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("Program exited")
