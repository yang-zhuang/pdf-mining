"""
Label Studio 类型定义模块

为模板系统提供必要的类型定义。
"""

from typing import Any, Dict, List, Optional, TypedDict


class LabelStudioResult(TypedDict, total=False):
    """Label Studio 结果类型"""
    type: str
    name: str
    toName: str
    id: Optional[str]
    original_id: Optional[str]
    value: Dict[str, Any]


class LabelStudioAnnotation(TypedDict, total=False):
    """Label Studio 标注类型"""
    id: str
    result: List[LabelStudioResult]
    created_at: Optional[str]
    updated_at: Optional[str]


class LabelStudioConfig(TypedDict, total=False):
    """Label Studio 配置类型"""
    view: Dict[str, Any]
    labels: List[str]


class OutlineNode(TypedDict, total=False):
    """提纲节点类型"""
    id: str
    text: str
    role: str
    content_type: str
    parent_id: Optional[str]
    children: List['OutlineNode']


class TrainingDataItem(TypedDict, total=False):
    """训练数据项类型"""
    prompt: str
    answer: str
    model: Optional[str]
    reasoning: Optional[str]
    metadata: Optional[Dict[str, Any]]
