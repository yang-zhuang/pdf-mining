"""
提纲提取标注模板配置模块

定义提纲提取任务的标注模板元数据和配置信息。

模板类型：
- two_column: 两栏模板（左侧显示文本，右侧 JSON 编辑）
- three_column: 三栏模板（左栏文本，中栏 JSON 编辑，右栏预览）
"""

from typing import Dict, List, Optional
from datetime import datetime


# 模板元数据定义
TEMPLATE_METADATA: Dict[str, Dict] = {
    'two_column': {
        'name': 'two_column',
        'display_name': '两栏提纲标注模板',
        'description': '适用于提纲提取任务的两栏标注模板，左侧显示原始文本，右侧提供 JSON 编辑器进行提纲标注。',
        'version': '1.0.0',
        'author': 'PDF Workbench Team',
        'created_date': '2026-02-16',
        'features': [
            '原始文本展示',
            'JSON 格式提纲编辑',
            '语法高亮',
            '实时验证',
            '快捷键支持'
        ],
        'data_fields': {
            'prompt': {
                'type': 'string',
                'description': 'OCR 提取的原始文本内容',
                'required': True,
                'display': 'text'
            },
            'answer': {
                'type': 'string',
                'description': 'LLM 提取的提纲结果（JSON 格式）',
                'required': True,
                'display': 'json_editor'
            },
            'reasoning': {
                'type': 'string',
                'description': '模型的推理过程（如果有）',
                'required': False,
                'display': 'text'
            }
        },
        'label_fields': {
            'outline': {
                'type': 'json',
                'description': '提纲结构（JSON 格式）',
                'required': True,
                'schema': {
                    'type': 'object',
                    'properties': {
                        'sections': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'level': {'type': 'integer'},
                                    'title': {'type': 'string'},
                                    'page': {'type': 'integer', 'optional': True}
                                }
                            }
                        }
                    }
                }
            }
        },
        'ui_config': {
            'layout': 'two_column',
            'left_panel': {
                'title': '原始文本',
                'fields': ['prompt']
            },
            'right_panel': {
                'title': '提纲编辑',
                'fields': ['answer', 'reasoning']
            }
        }
    },
    'three_column': {
        'name': 'three_column',
        'display_name': '三栏提纲标注模板',
        'description': '适用于提纲提取任务的三栏标注模板，左栏显示原始文本，中栏提供 JSON 编辑器，右栏实时预览提纲结构。',
        'version': '1.0.0',
        'author': 'PDF Workbench Team',
        'created_date': '2026-02-16',
        'features': [
            '原始文本展示',
            'JSON 格式提纲编辑',
            '语法高亮',
            '实时验证',
            '结构化预览',
            '快捷键支持',
            '导出功能'
        ],
        'data_fields': {
            'prompt': {
                'type': 'string',
                'description': 'OCR 提取的原始文本内容',
                'required': True,
                'display': 'text'
            },
            'answer': {
                'type': 'string',
                'description': 'LLM 提取的提纲结果（JSON 格式）',
                'required': True,
                'display': 'json_editor'
            },
            'reasoning': {
                'type': 'string',
                'description': '模型的推理过程（如果有）',
                'required': False,
                'display': 'text'
            }
        },
        'label_fields': {
            'outline': {
                'type': 'json',
                'description': '提纲结构（JSON 格式）',
                'required': True,
                'schema': {
                    'type': 'object',
                    'properties': {
                        'sections': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'level': {'type': 'integer'},
                                    'title': {'type': 'string'},
                                    'page': {'type': 'integer', 'optional': True}
                                }
                            }
                        }
                    }
                }
            }
        },
        'ui_config': {
            'layout': 'three_column',
            'left_panel': {
                'title': '原始文本',
                'fields': ['prompt']
            },
            'middle_panel': {
                'title': '提纲编辑',
                'fields': ['answer', 'reasoning']
            },
            'right_panel': {
                'title': '预览',
                'fields': ['outline'],
                'preview_type': 'tree_view'
            }
        }
    }
}


def get_template_info(template_name: str) -> Optional[Dict]:
    """
    获取指定模板的元数据信息

    Args:
        template_name: 模板名称（如 'two_column', 'three_column'）

    Returns:
        模板元数据字典，如果模板不存在则返回 None

    Example:
        >>> info = get_template_info('two_column')
        >>> print(info['display_name'])
        两栏提纲标注模板
    """
    return TEMPLATE_METADATA.get(template_name)


def list_templates(include_metadata: bool = False) -> List:
    """
    列出所有可用的模板

    Args:
        include_metadata: 是否包含完整的模板元数据
            - False: 只返回模板名称列表
            - True: 返回模板元数据字典列表

    Returns:
        模板列表（名称或完整元数据）

    Example:
        >>> names = list_templates()
        >>> ['two_column', 'three_column']

        >>> templates = list_templates(include_metadata=True)
        >>> [TEMPLATE_METADATA['two_column'], TEMPLATE_METADATA['three_column']]
    """
    if include_metadata:
        return list(TEMPLATE_METADATA.values())
    return list(TEMPLATE_METADATA.keys())


def validate_template(template_name: str) -> bool:
    """
    验证模板是否存在且有效

    Args:
        template_name: 模板名称

    Returns:
        如果模板有效返回 True，否则返回 False

    Example:
        >>> validate_template('two_column')
        True

        >>> validate_template('invalid_template')
        False
    """
    template = get_template_info(template_name)
    if not template:
        return False

    # 检查必需字段
    required_fields = ['name', 'version', 'data_fields', 'label_fields']
    return all(field in template for field in required_fields)


def get_data_field_schema(template_name: str, field_name: str) -> Optional[Dict]:
    """
    获取指定模板中特定字段的 schema 定义

    Args:
        template_name: 模板名称
        field_name: 字段名称

    Returns:
        字段 schema 字典，如果不存在则返回 None

    Example:
        >>> schema = get_data_field_schema('two_column', 'prompt')
        >>> schema['type']
        'string'
    """
    template = get_template_info(template_name)
    if not template:
        return None

    return template.get('data_fields', {}).get(field_name)


def get_label_field_schema(template_name: str, field_name: str) -> Optional[Dict]:
    """
    获取指定模板中标签字段的 schema 定义

    Args:
        template_name: 模板名称
        field_name: 标签字段名称

    Returns:
        标签字段 schema 字典，如果不存在则返回 None

    Example:
        >>> schema = get_label_field_schema('two_column', 'outline')
        >>> schema['type']
        'json'
    """
    template = get_template_info(template_name)
    if not template:
        return None

    return template.get('label_fields', {}).get(field_name)
