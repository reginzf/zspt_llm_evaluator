from label_studio_sdk import Client

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
        # 调用父类构造函数
        super().__init__(url=url, api_key=api_key)
        self.initialized = True

