"""
Label Studio 模板系统模块

本模块提供 Label Studio 的模板系统，用于生成和管理不同类型的标注模板。

主要功能：
- 模板注册表管理所有可用的模板
- 统一的模板加载和转换接口
- 支持多种标注场景（大纲标注、分栏标注等）

使用示例：
    from labeling.templates import get_template, TEMPLATE_REGISTRY

    # 获取默认的大纲模板
    template = get_template("outline")
    config = template.generate_config()

    # 查看所有可用模板
    print(TEMPLATE_REGISTRY.keys())
"""

from .base import (
    BaseLabelStudioTemplate,
    OutlineTemplate,
    OutlineTwoColumnTemplate,
    OutlineThreeColumnTemplate,
    TEMPLATE_REGISTRY,
    get_template,
)

__all__ = [
    # 基类
    "BaseLabelStudioTemplate",
    # 模板类
    "OutlineTemplate",
    "OutlineTwoColumnTemplate",
    "OutlineThreeColumnTemplate",
    # 注册表和函数
    "TEMPLATE_REGISTRY",
    "get_template",
]
