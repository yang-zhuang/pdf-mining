"""
非思考模式 Token 分析

直接统计 prompt + response 的 token 数量，无需模型推理。
"""

from .analyze import analyze_non_thinking_tokens

__all__ = ['analyze_non_thinking_tokens']
