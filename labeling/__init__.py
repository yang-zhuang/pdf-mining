"""
标注数据准备模块

用于从日志文件中提取数据，为 Label Studio 等标注平台准备数据集。
按任务类型组织，每个任务类型有独立的子模块。

目录结构：
    labeling/
    ├── __init__.py
    ├── utils.py                    # 共享工具函数
    ├── outline/                     # 提纲提取标注任务
    │   ├── __init__.py
    │   ├── prepare.py              # 提纲标注数据准备脚本
    │   └── README.md               # 提纲标注说明
    └── [future_tasks]/             # 其他未来的标注任务
        ├── __init__.py
        ├── prepare.py
        └── README.md
"""

from .utils import BaseLabelingExporter
from .outline.prepare import prepare_outline_labeling_data

__all__ = [
    'BaseLabelingExporter',
    'prepare_outline_labeling_data',
]
