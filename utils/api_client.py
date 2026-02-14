"""
API客户端模块 - 支持多种LLM提供商
"""

import os
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


class BaseClient(ABC):
    """API客户端基类"""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> str:
        """生成文本"""
        pass


class AnthropicClient(BaseClient):
    """Anthropic Claude API客户端"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514",
                 max_tokens: int = 64000, temperature: float = 0.7):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = None

    def _get_client(self):
        """延迟初始化客户端"""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("请安装 anthropic 库: pip install anthropic")
        return self._client

    def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> str:
        """调用Claude API生成文本"""
        client = self._get_client()

        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        temperature = kwargs.get('temperature', self.temperature)
        model = kwargs.get('model', self.model)

        messages = [{"role": "user", "content": prompt}]

        request_params = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }

        if system_prompt:
            request_params["system"] = system_prompt

        if temperature is not None:
            request_params["temperature"] = temperature

        try:
            response = client.messages.create(**request_params)
            return response.content[0].text
        except Exception as e:
            raise RuntimeError(f"API调用失败: {e}")


class OpenAIClient(BaseClient):
    """OpenAI API客户端"""

    def __init__(self, api_key: str, base_url: str = None,
                 model: str = "gpt-4-turbo-preview",
                 max_tokens: int = 4096, temperature: float = 0.7):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = None

    def _get_client(self):
        """延迟初始化客户端"""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except ImportError:
                raise ImportError("请安装 openai 库: pip install openai")
        return self._client

    def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> str:
        """调用OpenAI API生成文本"""
        client = self._get_client()

        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        temperature = kwargs.get('temperature', self.temperature)
        model = kwargs.get('model', self.model)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"API调用失败: {e}")


class ZhipuClient(BaseClient):
    """智谱AI GLM客户端"""

    # 默认API地址
    DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"

    def __init__(self, api_key: str, model: str = "glm-4-flash",
                 max_tokens: int = 4096, temperature: float = 0.7,
                 base_url: str = None):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self._client = None

    def _get_client(self):
        """延迟初始化客户端"""
        if self._client is None:
            try:
                from openai import OpenAI
                # 智谱AI使用OpenAI兼容接口
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except ImportError:
                raise ImportError("请安装 openai 库: pip install openai")
        return self._client

    def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> str:
        """调用智谱AI API生成文本"""
        client = self._get_client()

        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        temperature = kwargs.get('temperature', self.temperature)
        model = kwargs.get('model', self.model)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"API调用失败: {e}")


class APIClientFactory:
    """API客户端工厂"""

    @staticmethod
    def create(config: Dict[str, Any]) -> BaseClient:
        """根据配置创建API客户端"""
        provider = config.get('provider', 'anthropic')

        if provider == 'anthropic':
            api_key = config.get('api_key') or os.environ.get('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("请设置 ANTHROPIC_API_KEY 环境变量或在配置中提供 api_key")

            return AnthropicClient(
                api_key=api_key,
                model=config.get('model', 'claude-sonnet-4-20250514'),
                max_tokens=config.get('max_tokens', 64000),
                temperature=config.get('temperature', 0.7)
            )

        elif provider == 'openai':
            api_key = config.get('api_key') or os.environ.get('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("请设置 OPENAI_API_KEY 环境变量或在配置中提供 api_key")

            return OpenAIClient(
                api_key=api_key,
                base_url=config.get('base_url'),
                model=config.get('model', 'gpt-4-turbo-preview'),
                max_tokens=config.get('max_tokens', 4096),
                temperature=config.get('temperature', 0.7)
            )

        elif provider == 'zhipu' or provider == 'glm':
            api_key = config.get('api_key') or os.environ.get('ZHIPU_API_KEY')
            if not api_key:
                raise ValueError("请设置 ZHIPU_API_KEY 环境变量或在配置中提供 api_key")

            return ZhipuClient(
                api_key=api_key,
                model=config.get('model', 'glm-4-flash'),
                max_tokens=config.get('max_tokens', 4096),
                temperature=config.get('temperature', 0.7),
                base_url=config.get('base_url')  # 可自定义API地址
            )

        else:
            raise ValueError(f"不支持的API提供商: {provider}")


# 全局客户端实例
_global_client: Optional[BaseClient] = None


def get_client(config: Dict[str, Any] = None) -> BaseClient:
    """获取或创建API客户端"""
    global _global_client

    if _global_client is None and config:
        _global_client = APIClientFactory.create(config)

    return _global_client


def set_client(client: BaseClient):
    """设置全局客户端"""
    global _global_client
    _global_client = client
