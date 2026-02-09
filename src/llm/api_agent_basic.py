from abc import ABC, abstractmethod
from typing import Dict, Optional
import time
import threading
import requests


class BaseAgent(ABC):
    """API代理基础类"""

    _instances = {}
    _lock = threading.Lock()

    def __new__(cls, name: str, **kwargs):
        """实现单例模式"""
        with cls._lock:
            if name not in cls._instances:
                instance = super().__new__(cls)
                cls._instances[name] = instance
            return cls._instances[name]

    def __init__(self, name: str, api_key: str = None, api_url: str = None,
                 headers: Dict = None, temperature: float = 0.1,
                 max_tokens: int = 150, timeout: int = 30):
        """
        初始化基础代理

        Args:
            name: 代理名称
            api_key: API密钥
            api_url: API端点URL
            headers: 请求头
            temperature: 温度参数
            max_tokens: 最大token数
            timeout: 超时时间
        """
        if not hasattr(self, '_initialized'):  # 避免重复初始化
            self.name = name
            self.api_key = api_key
            self.api_url = api_url
            self.headers = headers or {}
            self.temperature = temperature
            self.max_tokens = max_tokens
            self.timeout = timeout
            self._initialized = True

    @abstractmethod
    def _build_request_payload(self, question: str, context: str) -> Dict:
        """
        构建请求载荷 - 子类必须实现

        Args:
            question: 问题
            context: 上下文

        Returns:
            请求载荷字典
        """
        pass

    @abstractmethod
    def _parse_response(self, response: Dict) -> str:
        """
        解析API响应 - 子类必须实现

        Args:
            response: API响应

        Returns:
            解析后的答案
        """
        pass

    def _make_api_call(self, question: str, context: str) -> Dict:
        """
        发送API请求的基础方法

        Args:
            question: 问题
            context: 上下文

        Returns:
            包含结果的字典
        """
        try:
            # 构建请求载荷
            payload = self._build_request_payload(question, context)

            # 发送请求
            start_time = time.time()
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            inference_time = time.time() - start_time

            if response.status_code == 200:
                response_data = response.json()
                answer = self._parse_response(response_data)

                return {
                    "success": True,
                    "answer": answer,
                    "inference_time": inference_time,
                    "raw_response": response_data
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "inference_time": inference_time
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "inference_time": 0
            }

    def ask(self, question: str, context: str) -> Dict:
        """
        公共接口：向代理提问

        Args:
            question: 问题
            context: 上下文

        Returns:
            评估结果字典
        """
        result = self._make_api_call(question, context)
        return result

    @classmethod
    def get_instance(cls, name: str) -> Optional['BaseAgent']:
        """获取已存在的实例"""
        return cls._instances.get(name)

    @classmethod
    def list_instances(cls) -> list:
        """列出所有实例名称"""
        return list(cls._instances.keys())


class DeepSeekAgent(BaseAgent):
    """DeepSeek代理实现"""

    def __init__(self, name: str = "DeepSeek", api_key: str = None,
                 api_url: str = "https://api.deepseek.com/v1/chat/completions",
                 temperature: float = 0.1, max_tokens: int = 150, timeout: int = 30):
        """
        初始化DeepSeek代理

        Args:
            name: 代理名称
            api_key: DeepSeek API密钥
            api_url: DeepSeek API端点
            temperature: 温度参数
            max_tokens: 最大token数
            timeout: 超时时间
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        super().__init__(
            name=name,
            api_key=api_key,
            api_url=api_url,
            headers=headers,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )

    def _build_request_payload(self, question: str, context: str) -> Dict:
        """构建DeepSeek请求载荷"""
        prompt = f"""基于以下文档内容回答问题：

文档内容：
{context}

问题：
{question}

请直接给出答案，不需要解释过程。"""

        return {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

    def _parse_response(self, response: Dict) -> str:
        """解析DeepSeek响应"""
        try:
            return response['choices'][0]['message']['content'].strip()
        except (KeyError, IndexError) as e:
            raise ValueError(f"无法解析DeepSeek响应: {e}")


class CustomAgent(BaseAgent):
    """自定义代理实现"""

    def __init__(self, name: str = "Custom", api_key: str = None,
                 api_url: str = None, request_template: Dict = None,
                 response_parser: str = None, temperature: float = 0.1,
                 max_tokens: int = 150, timeout: int = 30):
        """
        初始化自定义代理
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        super().__init__(
            name=name,
            api_key=api_key,
            api_url=api_url,
            headers=headers,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )
        self.request_template = request_template or {}
        self.response_parser = response_parser

    def _build_request_payload(self, question: str, context: str) -> Dict:
        """构建自定义请求载荷"""
        payload = {}
        for key, value in self.request_template.items():
            if isinstance(value, str):
                payload[key] = value.format(question=question, context=context)
            else:
                payload[key] = value
        return payload

    def _parse_response(self, response: Dict) -> str:
        """解析自定义响应"""
        try:
            if self.response_parser:
                # 使用自定义解析器
                import ast
                parser_func = ast.literal_eval(self.response_parser)
                return parser_func(response)
            else:
                # 默认尝试常见字段
                if 'answer' in response:
                    return str(response['answer'])
                elif 'response' in response:
                    return str(response['response'])
                elif 'text' in response:
                    return str(response['text'])
                else:
                    return str(response)
        except Exception as e:
            raise ValueError(f"无法解析自定义响应: {e}")


def create_agent(agent_config: Dict) -> BaseAgent:
    """
    根据配置创建代理实例

    Args:
        agent_config: 代理配置字典

    Returns:
        BaseAgent实例
    """
    agent_type = agent_config.get('type', '').lower()
    name = agent_config.get('name', 'Unknown')

    if agent_type == 'deepseek':
        return DeepSeekAgent(
            name=name,
            api_key=agent_config.get('api_key'),
            api_url=agent_config.get('api_url'),
            temperature=agent_config.get('temperature', 0.1),
            max_tokens=agent_config.get('max_tokens', 150),
            timeout=agent_config.get('timeout', 30)
        )

    elif agent_type == 'custom':
        return CustomAgent(
            name=name,
            api_key=agent_config.get('api_key'),
            api_url=agent_config.get('api_url'),
            request_template=agent_config.get('request_template', {}),
            response_parser=agent_config.get('response_parser'),
            temperature=agent_config.get('temperature', 0.1),
            max_tokens=agent_config.get('max_tokens', 150),
            timeout=agent_config.get('timeout', 30)
        )
    else:
        raise ValueError(f"不支持的代理类型: {agent_type}")
