"""
训练数据构建模块

用于从不同来源构建微调训练数据：
1. 从 Label Studio 标注数据转换
2. 从 LLM 日志数据直接提取

使用方法：
    # 从标注数据构建
    python -m training_data_builder.from_labeled.convert \
        --input ../labeled_data/outline/batch_01_labeled.json \
        --format alpaca \
        --output training_data/alpaca_batch_01.json

    # 从日志数据构建
    python -m training_data_builder.from_logs.extract \
        --log-dir ../outline_extractor/logs/llm_calls \
        --format sharegpt \
        --output training_data/sharegpt_from_logs.json
"""

from training_data_builder.outline.from_labeled.convert import convert_labeled_to_training
from training_data_builder.outline.from_logs.extract import extract_logs_to_training

__all__ = [
    'convert_labeled_to_training',
    'extract_logs_to_training',
]
