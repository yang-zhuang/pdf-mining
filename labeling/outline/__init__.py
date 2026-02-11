"""
提纲提取标注数据准备模块

用于从 LLM 调用日志中提取提纲提取任务的标注数据
"""

from .prepare import prepare_outline_labeling_data

__all__ = ['prepare_outline_labeling_data']
