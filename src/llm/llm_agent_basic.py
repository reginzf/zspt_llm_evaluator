import time
import logging

from abc import ABC, abstractmethod
from typing import Dict, Tuple

from datetime import datetime
import threading


class BaseLLMAgent(ABC):
    """LLM Agent 基础类"""

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
                 max_tokens: int = 512, timeout: int = 60, **kwargs):
        """
        初始化基础Agent

        Args:
            name: Agent名称
            api_key: API密钥
            api_url: API端点URL
            headers: 请求头
            temperature: 温度参数
            max_tokens: 最大token数
            timeout: 超时时间
            **kwargs: 其他配置参数
        """
        if not hasattr(self, '_initialized'):
            self.name = name
            self.api_key = api_key
            self.api_url = api_url
            self.headers = headers or {}
            self.temperature = temperature
            self.max_tokens = max_tokens
            self.timeout = timeout
            self.config = kwargs
            self._initialized = True

            # 版本标识（用于追踪同一模型的不同测试时间）
            self.version = kwargs.get('version', datetime.now().strftime('%Y%m%d_%H%M%S'))

    @abstractmethod
    def _build_request_payload(self, question: str, context: str) -> Dict:
        """构建请求载荷 - 子类必须实现"""
        pass

    @abstractmethod
    def _parse_response(self, response: Dict) -> str:
        """解析API响应 - 子类必须实现"""
        pass

    def test_connection(self) -> Tuple[bool, str]:
        """
        测试API连接

        Returns:
            (是否成功, 消息)
        """
        try:
            test_result = self.ask(
                question="你好",
                context="这是一个测试。",
                max_tokens=10
            )
            if test_result.get('success'):
                return True, "连接测试成功"
            else:
                return False, f"连接测试失败: {test_result.get('error', '未知错误')}"
        except Exception as e:
            return False, f"连接测试异常: {str(e)}"

    def ask(self, question: str, context: str, max_tokens: int = None) -> Dict:
        """
        向Agent提问

        Args:
            question: 问题
            context: 上下文
            max_tokens: 可选的最大token数覆盖

        Returns:
            包含结果的字典
        """
        import requests

        try:
            payload = self._build_request_payload(question, context)
            if max_tokens:
                payload['max_tokens'] = max_tokens

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

                # 提取token使用量（如果有）
                usage = response_data.get('usage', {})

                return {
                    "success": True,
                    "answer": answer,
                    "inference_time": inference_time,
                    "usage": usage,
                    "raw_response": response_data
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "inference_time": inference_time
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": f"请求超时 ({self.timeout}秒)",
                "inference_time": self.timeout
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "inference_time": 0
            }

    def get_config_dict(self) -> Dict:
        """获取配置字典（用于保存）"""
        return {
            'name': self.name,
            'api_url': self.api_url,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'timeout': self.timeout,
            'version': self.version,
            **self.config
        }


class DeepSeekAgent(BaseLLMAgent):
    """DeepSeek Agent 实现"""

    def __init__(self, name: str = "DeepSeek", api_key: str = None,
                 api_url: str = "https://api.deepseek.com/v1/chat/completions",
                 model: str = "deepseek-chat",
                 temperature: float = 0.1, max_tokens: int = 512,
                 timeout: int = 60, **kwargs):
        """
        初始化DeepSeek Agent

        Args:
            name: Agent名称
            api_key: API密钥
            api_url: API端点
            model: 模型名称
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
            timeout=timeout,
            model=model,
            **kwargs
        )
        self.model = model

    def _build_request_payload(self, question: str, context: str) -> Dict:
        """构建DeepSeek请求载荷"""
        prompt = f"""基于以下文档内容回答问题：
文档内容：
{context}
问题：
{question}
请直接给出答案，不需要解释过程。"""

        return {
            "model": self.model,
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


class OpenAIAgent(BaseLLMAgent):
    """OpenAI Agent 实现"""

    def __init__(self, name: str = "OpenAI", api_key: str = None,
                 api_url: str = "https://api.openai.com/v1/chat/completions",
                 model: str = "gpt-3.5-turbo",
                 temperature: float = 0.1, max_tokens: int = 512,
                 timeout: int = 60, **kwargs):
        """初始化OpenAI Agent"""
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
            timeout=timeout,
            model=model,
            **kwargs
        )
        self.model = model

    def _build_request_payload(self, question: str, context: str) -> Dict:
        """构建OpenAI请求载荷"""
        prompt = f"""基于以下文档内容回答问题：
文档内容：
{context}
问题：
{question}
请直接给出答案，不需要解释过程。"""

        return {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

    def _parse_response(self, response: Dict) -> str:
        """解析OpenAI响应"""
        try:
            return response['choices'][0]['message']['content'].strip()
        except (KeyError, IndexError) as e:
            raise ValueError(f"无法解析OpenAI响应: {e}")


class QwenAgent(BaseLLMAgent):
    """千问(Qwen) Agent 实现 - 支持阿里云百炼/通义千问API"""

    def __init__(self, name: str = "Qwen", api_key: str = None,
                 api_url: str = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                 model: str = "qwen-turbo",
                 temperature: float = 0.1, max_tokens: int = 512,
                 timeout: int = 60, **kwargs):
        """
        初始化千问 Agent

        Args:
            name: Agent名称
            api_key: API密钥 (阿里云DashScope的API Key)
            api_url: API端点
            model: 模型名称 (如 qwen-turbo, qwen-plus, qwen-max 等)
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
            timeout=timeout,
            model=model,
            **kwargs
        )
        self.model = model

    def _build_request_payload(self, question: str, context: str) -> Dict:
        """构建千问请求载荷"""
        prompt = f"""基于以下文档内容回答问题：
文档内容：
{context}
问题：
{question}
请直接给出答案，不需要解释过程。"""

        return {
            "model": self.model,
            "input": {
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            },
            "parameters": {
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "result_format": "message"
            }
        }

    def _parse_response(self, response: Dict) -> str:
        """解析千问响应"""
        try:
            # 阿里云百炼API响应格式
            if 'output' in response and 'choices' in response['output']:
                return response['output']['choices'][0]['message']['content'].strip()
            # 兼容OpenAI格式的响应
            elif 'choices' in response:
                return response['choices'][0]['message']['content'].strip()
            else:
                raise ValueError(f"未知的响应格式: {response}")
        except (KeyError, IndexError) as e:
            raise ValueError(f"无法解析千问响应: {e}")


class CustomAgent(BaseLLMAgent):
    """自定义Agent实现"""

    def __init__(self, name: str = "Custom", api_key: str = None,
                 api_url: str = None, request_template: Dict = None,
                 response_parser: str = None, temperature: float = 0.1,
                 max_tokens: int = 512, timeout: int = 60, **kwargs):
        """初始化自定义Agent"""
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
            timeout=timeout,
            request_template=request_template,
            response_parser=response_parser,
            **kwargs
        )
        self.request_template = request_template or {}
        self.response_parser = response_parser

    def _build_request_payload(self, question: str, context: str) -> Dict:
        """构建自定义请求载荷"""
        payload = {}
        for key, value in self.request_template.items():
            if isinstance(value, str):
                payload[key] = value.format(
                    question=question,
                    context=context,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
            else:
                payload[key] = value
        return payload

    def _parse_response(self, response: Dict) -> str:
        """解析自定义响应"""
        try:
            if self.response_parser:
                import ast
                parser_func = ast.literal_eval(self.response_parser)
                return parser_func(response)
            else:
                # 默认尝试常见字段
                if 'choices' in response and len(response['choices']) > 0:
                    choice = response['choices'][0]
                    if 'message' in choice:
                        return choice['message'].get('content', '').strip()
                    elif 'text' in choice:
                        return choice['text'].strip()
                elif 'answer' in response:
                    return str(response['answer'])
                elif 'response' in response:
                    return str(response['response'])
                elif 'text' in response:
                    return str(response['text'])
                else:
                    return str(response)
        except Exception as e:
            raise ValueError(f"无法解析自定义响应: {e}")


def create_agent(agent_config: Dict) -> BaseLLMAgent:
    """
    根据配置创建Agent实例

    Args:
        agent_config: Agent配置字典

    Returns:
        BaseLLMAgent实例
    """
    agent_type = agent_config.get('type', '').lower()
    name = agent_config.get('name', 'Unknown')

    # 构建版本标识
    version = agent_config.get('version', datetime.now().strftime('%Y%m%d_%H%M%S'))

    if agent_type == 'deepseek':
        return DeepSeekAgent(
            name=name,
            api_key=agent_config.get('api_key'),
            api_url=agent_config.get('api_url'),
            model=agent_config.get('model', 'deepseek-chat'),
            temperature=agent_config.get('temperature', 0.1),
            max_tokens=agent_config.get('max_tokens', 512),
            timeout=agent_config.get('timeout', 60),
            version=version
        )

    elif agent_type == 'openai':
        return OpenAIAgent(
            name=name,
            api_key=agent_config.get('api_key'),
            api_url=agent_config.get('api_url'),
            model=agent_config.get('model', 'gpt-3.5-turbo'),
            temperature=agent_config.get('temperature', 0.1),
            max_tokens=agent_config.get('max_tokens', 512),
            timeout=agent_config.get('timeout', 60),
            version=version
        )

    elif agent_type == 'qwen':
        return QwenAgent(
            name=name,
            api_key=agent_config.get('api_key'),
            api_url=agent_config.get('api_url'),
            model=agent_config.get('model', 'qwen-turbo'),
            temperature=agent_config.get('temperature', 0.1),
            max_tokens=agent_config.get('max_tokens', 512),
            timeout=agent_config.get('timeout', 60),
            version=version
        )

    elif agent_type == 'custom':
        return CustomAgent(
            name=name,
            api_key=agent_config.get('api_key'),
            api_url=agent_config.get('api_url'),
            request_template=agent_config.get('request_template', {}),
            response_parser=agent_config.get('response_parser'),
            temperature=agent_config.get('temperature', 0.1),
            max_tokens=agent_config.get('max_tokens', 512),
            timeout=agent_config.get('timeout', 60),
            version=version
        )
    
    elif agent_type == 'other':
        # 对于'其他'类型，使用CustomAgent作为通用实现
        # 允许用户通过配置自定义请求模板和响应解析器
        logger = logging.getLogger(__name__)
        logger.info(f"使用CustomAgent处理'other'类型模型: {name}")
        return CustomAgent(
            name=name,
            api_key=agent_config.get('api_key'),
            api_url=agent_config.get('api_url'),
            request_template=agent_config.get('request_template', {}),
            response_parser=agent_config.get('response_parser'),
            temperature=agent_config.get('temperature', 0.1),
            max_tokens=agent_config.get('max_tokens', 512),
            timeout=agent_config.get('timeout', 60),
            version=version
        )
    
    else:
        # 对于任何未知的类型，使用CustomAgent作为默认实现
        # 而不是抛出异常，这样更灵活
        logger = logging.getLogger(__name__)
        logger.warning(f"未知的Agent类型 '{agent_type}'，使用CustomAgent作为默认实现: {name}")
        return CustomAgent(
            name=name,
            api_key=agent_config.get('api_key'),
            api_url=agent_config.get('api_url'),
            request_template=agent_config.get('request_template', {}),
            response_parser=agent_config.get('response_parser'),
            temperature=agent_config.get('temperature', 0.1),
            max_tokens=agent_config.get('max_tokens', 512),
            timeout=agent_config.get('timeout', 60),
            version=version
        )
