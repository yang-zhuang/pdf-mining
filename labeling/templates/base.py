"""
Label Studio 模板基类和核心实现

本模块定义了 Label Studio 模板系统的核心组件：
- BaseLabelStudioTemplate: 所有模板的抽象基类
- OutlineTemplate: 单栏大纲标注模板
- OutlineTwoColumnTemplate: 双栏标注模板
- OutlineThreeColumnTemplate: 三栏标注模板
- TEMPLATE_REGISTRY: 模板注册表
- get_template(): 模板获取函数

使用示例：
    from labeling.templates.base import get_template

    # 获取模板
    template = get_template("outline")
    config = template.generate_config()

    # 转换数据
    annotations = template.from_label_studio([label_studio_result])
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import yaml

from ..types import (
    LabelStudioAnnotation,
    LabelStudioConfig,
    LabelStudioResult,
    OutlineNode,
    TrainingDataItem,
)


class BaseLabelStudioTemplate(ABC):
    """
    Label Studio 模板抽象基类

    定义所有模板必须实现的核心接口。

    属性:
        template_name: 模板唯一标识名称
        description: 模板描述
        config: Label Studio 配置（JSON 格式字符串）
        config_dict: Label Studio 配置（字典格式）

    子类必须实现:
        generate_config(): 生成 Label Studio 配置
        from_label_studio(): 将 Label Studio 结果转换为标注数据
        to_label_studio(): 将标注数据转换为 Label Studio 格式
    """

    def __init__(
        self,
        template_name: str,
        description: str,
        config: Optional[str] = None,
        config_dict: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        初始化模板

        Args:
            template_name: 模板名称
            description: 模板描述
            config: JSON 格式的配置字符串（与 config_dict 二选一）
            config_dict: 字典格式的配置（与 config 二选一）
        """
        self.template_name = template_name
        self.description = description

        if config and config_dict:
            raise ValueError("不能同时提供 config 和 config_dict")

        if config:
            self.config = config
            self.config_dict = json.loads(config)
        elif config_dict:
            self.config_dict = config_dict
            self.config = json.dumps(config_dict, ensure_ascii=False, indent=2)
        else:
            # 子类应该通过 generate_config 生成默认配置
            self.config = ""
            self.config_dict = {}

    @abstractmethod
    def generate_config(self, **kwargs: Any) -> str:
        """
        生成 Label Studio 配置

        Args:
            **kwargs: 模板特定的配置参数

        Returns:
            JSON 格式的配置字符串
        """
        pass

    @abstractmethod
    def from_label_studio(
        self,
        results: List[LabelStudioResult],
        task: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        将 Label Studio 标注结果转换为应用格式

        Args:
            results: Label Studio 的结果列表
            task: 任务信息（包含元数据等）

        Returns:
            转换后的标注数据
        """
        pass

    @abstractmethod
    def to_label_studio(
        self,
        data: Dict[str, Any],
        task: Optional[Dict[str, Any]] = None,
    ) -> List[LabelStudioResult]:
        """
        将应用格式转换为 Label Studio 格式

        Args:
            data: 应用格式的标注数据
            task: 任务信息

        Returns:
            Label Studio 结果列表
        """
        pass

    def save_config(self, path: Path) -> None:
        """
        保存配置到文件

        Args:
            path: 保存路径（支持 .json 或 .yaml）
        """
        path = Path(path)

        if path.suffix == ".json":
            path.write_text(self.config, encoding="utf-8")
        elif path.suffix in [".yaml", ".yml"]:
            path.write_text(
                yaml.dump(self.config_dict, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
        else:
            raise ValueError(f"不支持的文件格式: {path.suffix}")

    @classmethod
    def load_config(cls, path: Path) -> Dict[str, Any]:
        """
        从文件加载配置

        Args:
            path: 配置文件路径（支持 .json 或 .yaml）

        Returns:
            配置字典
        """
        path = Path(path)
        content = path.read_text(encoding="utf-8")

        if path.suffix == ".json":
            return json.loads(content)
        elif path.suffix in [".yaml", ".yml"]:
            return yaml.safe_load(content)
        else:
            raise ValueError(f"不支持的文件格式: {path.suffix}")

    def get_annotation_id(self, result: LabelStudioResult) -> Optional[str]:
        """
        从结果中提取标注 ID

        Args:
            result: Label Studio 结果对象

        Returns:
            标注 ID，如果不存在则返回 None
        """
        return result.get("id") or result.get("original_id")


class OutlineTemplate(BaseLabelStudioTemplate):
    """
    大纲标注模板（单栏）

    适用于文档结构标注场景，支持多级大纲、角色分类、内容类型等。

    配置特点：
    - 单列视图，适合长文档标注
    - 支持树形结构展示
    - 多级大纲层级
    - 角色和类型分类

    标注字段：
    - outline: 文档大纲结构（递归节点列表）
    """

    def __init__(self) -> None:
        """初始化大纲模板"""
        super().__init__(
            template_name="outline",
            description="单栏大纲标注模板，适用于文档结构标注",
        )
        # 生成默认配置
        self.config = self.generate_config()
        self.config_dict = json.loads(self.config)

    def generate_config(
        self,
        role_labels: Optional[List[str]] = None,
        content_type_labels: Optional[List[str]] = None,
        max_depth: int = 6,
    ) -> str:
        """
        生成大纲标注配置

        Args:
            role_labels: 角色标签列表（默认: 论文, 章节, 小节, 子小节, 段落, 其他）
            content_type_labels: 内容类型标签列表
            max_depth: 最大大纲层级

        Returns:
            JSON 格式的配置字符串
        """
        if role_labels is None:
            role_labels = ["论文", "章节", "小节", "子小节", "段落", "其他"]

        if content_type_labels is None:
            content_type_labels = ["标题", "正文", "图表", "引用", "公式", "其他"]

        # 构建角色选择器
        role_choices = ", ".join([f'"{role}"' for role in role_labels])

        # 构建内容类型选择器
        content_type_choices = ", ".join(
            [f'"{ctype}"' for ctype in content_type_labels]
        )

        config = {
            "<View>": [
                '<Text name="text" value="$text"/>',
                f'<HyperText name="html" value="$html"/>',
                '<Rectangle name="image" toName="html" strokeWidth="0"/>',
                '<Header value="文档大纲标注"/>',
                "<Panel name=\"panel_1\" selectedValue=\"outline\" toggleable=\"true\" "
                "showInline=\"true\">",
                f'<PanelView name="outline_view" label="大纲结构">',
                f'<Tree name="outline" toName="html" '
                f'choice="{role_choices}" '
                f'parentValue="parent" '
                f'depth="{max_depth}" '
                f'minUsableWidth="250px"/>',
                "</PanelView>",
                "</Panel>",
                f'<Header value="节点属性"/>',
                f'<Taxonomy name="role" toName="outline" value="{role_choices}" '
                f'allowNested="true"/>',
                f'<Taxonomy name="content_type" toName="outline" '
                f'value="{content_type_choices}" allowNested="true"/>',
            ]
        }

        # 构建 JSON 配置
        config_dict = {
            "view": config,
            "labels": role_labels,
            "content_types": content_type_labels,
        }

        return json.dumps(config_dict, ensure_ascii=False, indent=2)

    def from_label_studio(
        self,
        results: List[LabelStudioResult],
        task: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, OutlineNode]:
        """
        将 Label Studio 结果转换为大纲节点

        Args:
            results: Label Studio 结果列表
            task: 任务信息（包含元数据等）

        Returns:
            大纲节点字典（按 ID 索引）
        """
        outline_nodes: Dict[str, OutlineNode] = {}

        for result in results:
            if result.get("type") == "tree":
                # 处理树形结构
                value = result.get("value", {})
                outline_id = result.get("id")
                parent_id = value.get("parent")
                text = value.get("text", "")
                role = value.get("choice", "其他")

                # 查找相关的分类标注
                role_annotation = None
                content_type = None

                for r in results:
                    if r.get("type") == "taxonomy":
                        tax_value = r.get("value", {})
                        if outline_id in tax_value.get("selected", []):
                            if r.get("name") == "role":
                                role_annotation = tax_value.get("selected", [outline_id])
                            elif r.get("name") == "content_type":
                                content_type = tax_value.get("selected", [outline_id])

                # 构建节点
                node = OutlineNode(
                    id=outline_id,
                    text=text,
                    role=role_annotation or role,
                    content_type=content_type or "其他",
                    parent_id=parent_id,
                    children=[],
                )

                outline_nodes[outline_id] = node

        # 构建父子关系
        for node_id, node in outline_nodes.items():
            if node.parent_id and node.parent_id in outline_nodes:
                outline_nodes[node.parent_id].children.append(node)

        # 只返回根节点（没有父节点的节点）
        return {
            node_id: node
            for node_id, node in outline_nodes.items()
            if not node.parent_id
        }

    def to_label_studio(
        self,
        data: Dict[str, OutlineNode],
        task: Optional[Dict[str, Any]] = None,
    ) -> List[LabelStudioResult]:
        """
        将大纲节点转换为 Label Studio 格式

        Args:
            data: 大纲节点字典（按 ID 索引）
            task: 任务信息

        Returns:
            Label Studio 结果列表
        """
        results: List[LabelStudioResult] = []

        def process_node(node: OutlineNode, depth: int = 0) -> None:
            """递归处理节点"""
            # 添加树形节点
            results.append(
                {
                    "type": "tree",
                    "name": "outline",
                    "toName": "html",
                    "id": node.id,
                    "value": {
                        "text": node.text,
                        "choice": node.role,
                        "parent": node.parent_id,
                    },
                }
            )

            # 添加角色分类
            results.append(
                {
                    "type": "taxonomy",
                    "name": "role",
                    "toName": "outline",
                    "value": {
                        "selected": [node.id],
                    },
                }
            )

            # 添加内容类型分类
            results.append(
                {
                    "type": "taxonomy",
                    "name": "content_type",
                    "toName": "outline",
                    "value": {
                        "selected": [node.id],
                    },
                }
            )

            # 递归处理子节点
            for child in node.children:
                process_node(child, depth + 1)

        # 处理所有根节点
        for node in data.values():
            if not node.parent_id:
                process_node(node)

        return results


class OutlineTwoColumnTemplate(BaseLabelStudioTemplate):
    """
    大纲标注模板（双栏）

    适用于需要对比或并行查看文档内容的标注场景。

    配置特点：
    - 双栏布局，左栏显示文档内容，右栏显示标注面板
    - 适合中等长度文档的标注
    - 保持大纲模板的所有标注能力
    """

    def __init__(self) -> None:
        """初始化双栏大纲模板"""
        super().__init__(
            template_name="outline_two_column",
            description="双栏大纲标注模板，左栏内容，右栏标注",
        )
        self.config = self.generate_config()
        self.config_dict = json.loads(self.config)

    def generate_config(
        self,
        role_labels: Optional[List[str]] = None,
        content_type_labels: Optional[List[str]] = None,
        max_depth: int = 6,
    ) -> str:
        """
        生成双栏大纲标注配置

        Args:
            role_labels: 角色标签列表
            content_type_labels: 内容类型标签列表
            max_depth: 最大大纲层级

        Returns:
            JSON 格式的配置字符串
        """
        # 使用 OutlineTemplate 的参数
        base_template = OutlineTemplate()
        base_config = base_template.generate_config(
            role_labels=role_labels,
            content_type_labels=content_type_labels,
            max_depth=max_depth,
        )

        # 添加双栏布局配置
        config_dict = json.loads(base_config)
        config_dict["layout"] = "two_column"
        config_dict["column_ratio"] = [60, 40]  # 左栏 60%，右栏 40%

        return json.dumps(config_dict, ensure_ascii=False, indent=2)

    def from_label_studio(
        self,
        results: List[LabelStudioResult],
        task: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, OutlineNode]:
        """
        将 Label Studio 结果转换为大纲节点

        双栏模板使用与单栏模板相同的数据格式。

        Args:
            results: Label Studio 结果列表
            task: 任务信息

        Returns:
            大纲节点字典
        """
        # 使用 OutlineTemplate 的转换逻辑
        base_template = OutlineTemplate()
        return base_template.from_label_studio(results, task)

    def to_label_studio(
        self,
        data: Dict[str, OutlineNode],
        task: Optional[Dict[str, Any]] = None,
    ) -> List[LabelStudioResult]:
        """
        将大纲节点转换为 Label Studio 格式

        Args:
            data: 大纲节点字典
            task: 任务信息

        Returns:
            Label Studio 结果列表
        """
        # 使用 OutlineTemplate 的转换逻辑
        base_template = OutlineTemplate()
        return base_template.to_label_studio(data, task)


class OutlineThreeColumnTemplate(BaseLabelStudioTemplate):
    """
    大纲标注模板（三栏）

    适用于复杂的标注场景，可以同时查看文档、大纲结构和详细属性。

    配置特点：
    - 三栏布局：左栏文档内容，中栏大纲结构，右栏详细属性
    - 适合复杂文档的详细标注
    - 最大化的信息展示

    栏位说明：
    1. 左栏：文档原始内容（HTML/PDF 预览）
    2. 中栏：大纲树形结构
    3. 右栏：节点详细属性（角色、内容类型、元数据等）
    """

    def __init__(self) -> None:
        """初始化三栏大纲模板"""
        super().__init__(
            template_name="outline_three_column",
            description="三栏大纲标注模板，内容、大纲、属性分栏显示",
        )
        self.config = self.generate_config()
        self.config_dict = json.loads(self.config)

    def generate_config(
        self,
        role_labels: Optional[List[str]] = None,
        content_type_labels: Optional[List[str]] = None,
        max_depth: int = 6,
        column_ratios: Optional[List[int]] = None,
    ) -> str:
        """
        生成三栏大纲标注配置

        Args:
            role_labels: 角色标签列表
            content_type_labels: 内容类型标签列表
            max_depth: 最大大纲层级
            column_ratios: 三栏比例（默认: [50, 30, 20]）

        Returns:
            JSON 格式的配置字符串
        """
        if column_ratios is None:
            column_ratios = [50, 30, 20]

        # 使用 OutlineTemplate 的参数
        base_template = OutlineTemplate()
        base_config = base_template.generate_config(
            role_labels=role_labels,
            content_type_labels=content_type_labels,
            max_depth=max_depth,
        )

        # 添加三栏布局配置
        config_dict = json.loads(base_config)
        config_dict["layout"] = "three_column"
        config_dict["column_ratio"] = column_ratios

        return json.dumps(config_dict, ensure_ascii=False, indent=2)

    def from_label_studio(
        self,
        results: List[LabelStudioResult],
        task: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, OutlineNode]:
        """
        将 Label Studio 结果转换为大纲节点

        三栏模板使用与单栏模板相同的数据格式。

        Args:
            results: Label Studio 结果列表
            task: 任务信息

        Returns:
            大纲节点字典
        """
        # 使用 OutlineTemplate 的转换逻辑
        base_template = OutlineTemplate()
        return base_template.from_label_studio(results, task)

    def to_label_studio(
        self,
        data: Dict[str, OutlineNode],
        task: Optional[Dict[str, Any]] = None,
    ) -> List[LabelStudioResult]:
        """
        将大纲节点转换为 Label Studio 格式

        Args:
            data: 大纲节点字典
            task: 任务信息

        Returns:
            Label Studio 结果列表
        """
        # 使用 OutlineTemplate 的转换逻辑
        base_template = OutlineTemplate()
        return base_template.to_label_studio(data, task)


# 模板注册表
TEMPLATE_REGISTRY: Dict[str, Type[BaseLabelStudioTemplate]] = {
    "outline": OutlineTemplate,
    "outline_two_column": OutlineTwoColumnTemplate,
    "outline_three_column": OutlineThreeColumnTemplate,
}


def get_template(template_name: str) -> BaseLabelStudioTemplate:
    """
    根据模板名称获取模板实例

    Args:
        template_name: 模板名称（在 TEMPLATE_REGISTRY 中注册的名称）

    Returns:
        模板实例

    Raises:
        ValueError: 当模板名称不存在时

    使用示例：
        template = get_template("outline")
        config = template.generate_config()
    """
    if template_name not in TEMPLATE_REGISTRY:
        available = ", ".join(TEMPLATE_REGISTRY.keys())
        raise ValueError(
            f"未知的模板名称: {template_name}. 可用的模板: {available}"
        )

    template_class = TEMPLATE_REGISTRY[template_name]
    return template_class()


def register_template(
    template_name: str,
    template_class: Type[BaseLabelStudioTemplate],
) -> None:
    """
    注册新的模板

    Args:
        template_name: 模板名称
        template_class: 模板类（必须继承自 BaseLabelStudioTemplate）

    Raises:
        TypeError: 当 template_class 不是 BaseLabelStudioTemplate 的子类时

    使用示例：
        class MyCustomTemplate(BaseLabelStudioTemplate):
            # 实现必要的方法...
            pass

        register_template("my_custom", MyCustomTemplate)
    """
    if not issubclass(template_class, BaseLabelStudioTemplate):
        raise TypeError(
            f"模板类必须继承自 BaseLabelStudioTemplate, "
            f"但得到的是: {template_class.__name__}"
        )

    TEMPLATE_REGISTRY[template_name] = template_class


def list_templates() -> Dict[str, str]:
    """
    列出所有可用的模板

    Returns:
        模板名称到描述的字典
    """
    return {
        name: cls.description
        for name, cls in TEMPLATE_REGISTRY.items()
        if cls.description
    }
