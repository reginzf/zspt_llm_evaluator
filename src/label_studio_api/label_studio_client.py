from label_studio_sdk import Client
import logging
import os

logger = logging.getLogger(__name__)

__all__ = ['LabelStudioLogin']

class LabelStudioLogin(Client):
    _instances = {}
    
    def __new__(cls, url=None, api_key=None, label_studio_id=None):
        instance_key = label_studio_id or f"{url}_{api_key}"
        
        if instance_key not in cls._instances:
            cls._instances[instance_key] = super(LabelStudioLogin, cls).__new__(cls)
        return cls._instances[instance_key]

    def __init__(self, url=None, api_key=None, label_studio_id=None):
        # 避免重复初始化
        if hasattr(self, 'initialized'):
            return
        
        # 验证必要的参数
        if not url:
            raise ValueError("Label Studio URL不能为空")
        if not api_key:
            raise ValueError("Label Studio API Key不能为空")
        
        # 保存Label Studio ID
        self.label_studio_id = label_studio_id
        
        # 调用父类构造函数，但先禁用版本检查以避免网络问题
        try:
            # 设置环境变量来避免某些SDK内部问题
            os.environ.setdefault('LABEL_STUDIO_URL', url)
            os.environ.setdefault('LABEL_STUDIO_API_KEY', api_key)
            
            super().__init__(url=url, api_key=api_key)
        except Exception as e:
            logger.error(f"LabelStudioLogin初始化失败: {str(e)}", exc_info=True)
            raise RuntimeError(f"无法连接到Label Studio服务器: {str(e)}")
        
        self.initialized = True
    
    def get_versions(self):
        """重写get_versions方法，添加错误处理"""
        try:
            response = self.make_request("GET", "/api/version")
            if response and hasattr(response, 'json'):
                json_data = response.json()
                if json_data and isinstance(json_data, dict):
                    self.versions = json_data
                    return self.versions
            logger.warning("无法获取Label Studio版本信息，返回空字典")
            self.versions = {}
            return self.versions
        except Exception as e:
            logger.warning(f"获取Label Studio版本信息失败: {str(e)}")
            self.versions = {}
            return self.versions

