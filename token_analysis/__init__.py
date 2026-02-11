"""
Token 分析模块

用于分析微调模型的 token 使用情况，帮助确定合适的 max_token 配置。

功能：
1. 非思考模式分析：直接统计 prompt + response 的 token 数量
2. 思考模式分析：统计 prompt + thinking + response 的 token 数量

使用方法：
    # 非思考模式
    python -m token_analysis.non_thinking.analyze --input ../labeled_data/outline/batch_01_labeled.json

    # 思考模式
    python -m token_analysis.thinking.analyze --input ../labeled_data/outline/batch_01_labeled.json --vllm-url http://localhost:8000
"""

from .utils import TokenAnalyzer
from .non_thinking.analyze import analyze_non_thinking_tokens
from .thinking.processor import ThinkingAnalyzer
from .thinking.infer import ThinkingModelInference

__all__ = [
    'TokenAnalyzer',
    'analyze_non_thinking_tokens',
    'ThinkingAnalyzer',
    'ThinkingModelInference',
]
