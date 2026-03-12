"""
统一的大模型适配层。
"""

from dataclasses import dataclass
import os
from typing import Optional

import anthropic
import google.generativeai as genai
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


@dataclass
class GenerationConfig:
    temperature: float = 0.2
    response_mime_type: Optional[str] = None
    max_output_tokens: Optional[int] = None


@dataclass
class LLMResponse:
    text: str


class GeminiClient:
    def __init__(self, api_key: str, model_name: str):
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model_name)

    def generate_content(self, prompt: str, generation_config: Optional[GenerationConfig] = None) -> LLMResponse:
        config = generation_config or GenerationConfig()
        response = self.client.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=config.temperature,
                response_mime_type=config.response_mime_type,
                max_output_tokens=config.max_output_tokens,
            ),
        )
        return LLMResponse(text=getattr(response, "text", "") or "")


class OpenAICompatibleClient:
    def __init__(self, api_key: str, model_name: str, base_url: Optional[str] = None):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name

    def generate_content(self, prompt: str, generation_config: Optional[GenerationConfig] = None) -> LLMResponse:
        config = generation_config or GenerationConfig()
        request_kwargs = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
        }

        if config.max_output_tokens:
            request_kwargs["max_completion_tokens"] = config.max_output_tokens
        if config.response_mime_type == "application/json":
            request_kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**request_kwargs)
        message = response.choices[0].message
        content = message.content or ""
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )
        return LLMResponse(text=content)


class AnthropicClient:
    def __init__(self, api_key: str, model_name: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model_name = model_name

    def generate_content(self, prompt: str, generation_config: Optional[GenerationConfig] = None) -> LLMResponse:
        config = generation_config or GenerationConfig()
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=config.max_output_tokens or 4000,
            temperature=config.temperature if config.temperature is not None else 0.2,
            messages=[{"role": "user", "content": prompt}],
        )
        text_parts = []
        for block in response.content:
            text = getattr(block, "text", None)
            if text:
                text_parts.append(text)
        return LLMResponse(text="".join(text_parts))


MODEL_PRESETS = {
    "gemini": {
        "label": "Gemini 3 Flash Preview",
        "provider": "google",
        "model_name": "gemini-3-flash-preview",
        "env_key": "GOOGLE_API_KEY",
        "client_class": GeminiClient,
    },
    "gpt5": {
        "label": "GPT-5",
        "provider": "openai",
        "model_name": "gpt-5",
        "env_key": "OPENAI_ANALYSIS_API_KEY",
        "fallback_env_key": "OPENAI_API_KEY",
        "client_class": OpenAICompatibleClient,
    },
    "claude-sonnet": {
        "label": "Claude Sonnet 4.6",
        "provider": "anthropic",
        "model_name": "claude-sonnet-4-6",
        "env_key": "ANTHROPIC_API_KEY",
        "client_class": AnthropicClient,
    },
    "minimax-m25": {
        "label": "MiniMax M2.5",
        "provider": "minimax",
        "model_name": "MiniMax-M2.5",
        "env_key": "MINIMAX_API_KEY",
        "base_url": "https://api.minimax.io/v1",
        "client_class": OpenAICompatibleClient,
    },
}


def get_available_models():
    return [
        {
            "id": model_id,
            "label": config["label"],
            "provider": config["provider"],
            "model_name": config["model_name"],
        }
        for model_id, config in MODEL_PRESETS.items()
    ]


def build_llm_client(model_id: str):
    model_id = model_id or os.getenv("DEFAULT_ANALYSIS_MODEL", "gemini")
    config = MODEL_PRESETS.get(model_id)
    if not config:
        raise ValueError(f"不支持的分析模型: {model_id}")

    api_key = os.getenv(config["env_key"])
    if not api_key and config.get("fallback_env_key"):
        api_key = os.getenv(config["fallback_env_key"])
    if not api_key:
        raise ValueError(f"分析模型 {config['label']} 未配置 API Key")

    client_class = config["client_class"]
    if client_class is OpenAICompatibleClient:
        client = client_class(
            api_key=api_key,
            model_name=config["model_name"],
            base_url=config.get("base_url"),
        )
    else:
        client = client_class(
            api_key=api_key,
            model_name=config["model_name"],
        )

    return client, {
        "id": model_id,
        "label": config["label"],
        "provider": config["provider"],
        "model_name": config["model_name"],
    }
