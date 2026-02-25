"""
提纲提取标注模板模块

提供提纲提取任务的标注模板配置和数据转换功能。

模板类型：
- two_column: 两栏模板（文本展示 + JSON 编辑）
- three_column: 三栏模板（文本展示 + JSON 编辑 + 预览）

功能：
- 模板元数据管理
- LLM 日志数据转换
- 支持多种模型名称格式（model, used_model）
"""

from .config import (
    TEMPLATE_METADATA,
    get_template_info,
    list_templates
)
from .converter import OutlineDataConverter

__all__ = [
    'TEMPLATE_METADATA',
    'get_template_info',
    'list_templates',
    'OutlineDataConverter',
]
