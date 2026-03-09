"""
分析器工厂
"""

from .gemini_analyzer import GeminiAnalyzer
from .gpt4o_analyzer import GPT4oAnalyzer
from .claude_analyzer import ClaudeAnalyzer
from .qwen_analyzer import QwenAnalyzer


def get_analyzer(model_name, api_key):
    """
    获取指定的分析器
    
    Args:
        model_name: 模型名称 (gemini, gpt4o, claude, qwen)
        api_key: API密钥
    
    Returns:
        VideoAnalyzer实例
    """
    analyzers = {
        "gemini": GeminiAnalyzer,
        "gpt4o": GPT4oAnalyzer,
        "claude": ClaudeAnalyzer,
        "qwen": QwenAnalyzer
    }
    
    if model_name not in analyzers:
        raise ValueError(f"不支持的模型: {model_name}. 支持的模型: {', '.join(analyzers.keys())}")
    
    return analyzers[model_name](api_key)


def get_available_models():
    """获取所有可用的模型列表"""
    return ["gemini", "gpt4o", "claude", "qwen"]
