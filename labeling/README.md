# 标注数据准备模块

本模块用于从 LLM 调用日志中提取数据，为 Label Studio 等标注平台准备数据集。

## 目录结构

```
labeling/
├── __init__.py           # 模块初始化
├── utils.py              # 共享工具类
├── README.md             # 本文档
├── templates/            # Label Studio 模板系统
│   ├── __init__.py       # 模板模块初始化
│   ├── base.py           # 模板基类和核心实现
│   └── outline/          # 提纲提取模板
│       ├── __init__.py
│       ├── config.py     # 模板配置和元数据
│       ├── converter.py  # 数据转换器
│       ├── two_column.xml   # 两栏模板配置
│       └── three_column.xml  # 三栏模板配置
├── screenshots/          # 截图文件夹
│   ├── README.md         # 截图命名和组织规范
│   └── .gitkeep          # 占位文件
└── outline/              # 提纲提取标注任务
    ├── __init__.py
    ├── prepare.py        # 提纲标注数据准备脚本
    └── README.md         # 提纲标注说明文档
```

## 设计理念

### 模板系统

模板系统为不同的标注任务提供灵活的标注界面配置。通过模板系统，可以：

- **统一的数据格式**: 所有模板共享相同的数据格式标准
- **可扩展的架构**: 轻松添加新的标注任务模板
- **类型安全**: 通过类型定义确保数据一致性
- **灵活的配置**: 支持多种布局和交互方式

#### 模板类型

当前系统支持以下模板类型：

| 模板名称 | 标识符 | 描述 | 适用场景 |
|---------|--------|------|---------|
| 提纲标注（单栏） | `outline` | 单栏大纲标注模板，适用于文档结构标注 | 长文档标注、结构化提取 |
| 提纲标注（双栏） | `outline_two_column` | 双栏大纲标注模板，左栏内容，右栏标注 | 中等长度文档、对比标注 |
| 提纲标注（三栏） | `outline_three_column` | 三栏大纲标注模板，内容、大纲、属性分栏显示 | 复杂文档、详细标注 |
| 两栏提纲模板 | `two_column` | 适用于提纲提取任务的两栏标注模板 | 提纲提取任务 |
| 三栏提纲模板 | `three_column` | 适用于提纲提取任务的三栏标注模板 | 需要预览的提纲标注 |

#### 模板系统架构

```
templates/
├── base.py              # 基类和模板注册表
│   ├── BaseLabelStudioTemplate     # 抽象基类
│   ├── OutlineTemplate             # 单栏模板
│   ├── OutlineTwoColumnTemplate    # 双栏模板
│   ├── OutlineThreeColumnTemplate  # 三栏模板
│   ├── TEMPLATE_REGISTRY          # 模板注册表
│   ├── get_template()              # 获取模板实例
│   └── register_template()        # 注册新模板
└── outline/              # 提纲提取任务模板
    ├── __init__.py
    ├── config.py         # 模板元数据和配置
    ├── converter.py      # 数据转换器
    ├── two_column.xml    # Label Studio 配置（双栏）
    └── three_column.xml  # Label Studio 配置（三栏）
```

#### 模板系统使用示例

```python
from labeling.templates.base import get_template

# 获取模板实例
template = get_template("outline")

# 生成 Label Studio 配置
config = template.generate_config()
print(config)

# 保存配置到文件
template.save_config("label_config.json")

# 转换标注数据
annotations = template.from_label_studio([label_studio_result])

# 列出所有可用模板
from labeling.templates.base import list_templates
templates = list_templates()
print(templates)  # {'outline': '单栏大纲标注模板...', ...}
```

### 按任务类型组织

每个标注任务都有独立的子模块，便于管理和扩展：

```
labeling/
├── outline/              # 提纲提取
├── classification/       # 文本分类（未来）
├── summarization/        # 文本摘要（未来）
└── ...                   # 其他任务
```

### 共享基础功能

所有任务共享以下功能：

- ✅ **日志读取**: 统一读取 .jsonl 日志文件
- ✅ **数据过滤**: 支持按文件、成功率等条件过滤
- ✅ **断点续传**: 基于内容哈希的增量导出机制
- ✅ **状态管理**: 自动保存和加载导出进度

### 可扩展架构

添加新的标注任务只需：

1. 创建新的子模块目录（如 `labeling/summarization/`）
2. 继承 `BaseLabelingExporter` 类
3. 实现 `extract_xxx_data()` 方法
4. 添加命令行接口

## 当前支持的标注任务

### 1. 提纲提取（outline）

从 PDF 文档中提取提纲结构的标注任务。

**使用方法**:
```bash
# 使用默认模板（两栏）
python -m labeling.outline.prepare

# 使用三栏模板
python -m labeling.outline.prepare --template three_column

# 列出所有可用模板
python -m labeling.outline.prepare --list-templates
```

**详细说明**: 查看 [outline/README.md](outline/README.md)

**数据格式**:
```json
{
  "prompt": "OCR 候选提纲内容...",
  "answer": "LLM 提取的提纲结果（JSON 格式）...",
  "model": "gpt-4",
  "reasoning": "推理过程...",
  "metadata": {
    "file_key": "abc123",
    "timestamp": "2026-02-16T10:30:00",
    "model": "gpt-4"
  }
}
```

## 模板系统详解

### 模板系统功能

模板系统提供以下核心功能：

1. **模板注册机制**: 通过 `TEMPLATE_REGISTRY` 管理所有可用模板
2. **配置生成**: 自动生成 Label Studio 的配置文件（JSON/XML）
3. **数据转换**: 在应用格式和 Label Studio 格式之间双向转换
4. **元数据管理**: 丰富的模板元数据（版本、作者、特性等）
5. **数据验证**: 自动验证提取的数据是否符合模板要求

### BaseLabelStudioTemplate 基类

所有模板都必须继承自 `BaseLabelStudioTemplate` 并实现以下方法：

```python
class BaseLabelStudioTemplate(ABC):
    @abstractmethod
    def generate_config(self, **kwargs) -> str:
        """生成 Label Studio 配置"""

    @abstractmethod
    def from_label_studio(self, results: List[LabelStudioResult], task: Optional[Dict]) -> Dict:
        """将 Label Studio 结果转换为应用格式"""

    @abstractmethod
    def to_label_studio(self, data: Dict, task: Optional[Dict]) -> List[LabelStudioResult]:
        """将应用格式转换为 Label Studio 格式"""
```

### 数据转换器

每个任务可以有自己的数据转换器，用于从 LLM 日志中提取数据：

```python
from labeling.templates.outline.converter import OutlineDataConverter

# 创建转换器
converter = OutlineDataConverter(strict=False)

# 从日志记录提取数据
data = converter.extract_from_log(log_record)

# 批量转换
results = converter.convert_batch(log_records)

# 带统计信息的批量转换
result = converter.convert_batch_with_stats(log_records)
print(result['stats'])
# {'total': 100, 'success': 85, 'skipped': 15, 'success_rate': 0.85}
```

### 模板配置

每个模板都有详细的配置元数据：

```python
from labeling.templates.outline.config import get_template_info

# 获取模板信息
info = get_template_info('two_column')
print(info['display_name'])  # "两栏提纲标注模板"
print(info['features'])      # ['原始文本展示', 'JSON 格式提纲编辑', ...]
print(info['data_fields'])   # 字段定义
print(info['ui_config'])     # UI 配置
```

## 使用示例

### 模板系统使用

```bash
# 查看所有可用模板
python -m labeling.outline.prepare --list-templates

# 使用两栏模板导出数据
python -m labeling.outline.prepare --template two_column

# 使用三栏模板导出数据
python -m labeling.outline.prepare --template three_column --limit 50

# 指定日志文件列表和输出目录
python -m labeling.outline.prepare \
    --log-files logs/llm_calls/file1.jsonl logs/llm_calls/file2.json \
    --output-dir data/labels \
    --template two_column
```

### 准备提纲标注数据

## 共享功能

### BaseLabelingExporter

所有标注任务的基类，提供以下方法：

```python
class BaseLabelingExporter:
    def read_log_files() -> List[Dict]
        # 读取所有 .jsonl 日志文件

    def filter_records(...) -> List[Dict]
        # 过滤记录（支持文件、哈希、成功状态等）

    def get_record_hash(record: Dict) -> str
        # 生成记录的唯一哈希值

    def export_data(...)
        # 导出标注数据（模板方法）

    def load_state() -> Dict
        # 加载断点续传状态

    def save_state(state: Dict)
        # 保存断点续传状态
```

### 断点续传机制

每个任务都有独立的状态文件：

```
.{task_name}_state.json
```

记录内容包括：

- `exported_record_hashes`: 已导出的记录哈希列表
- `last_export_time`: 最后导出时间
- `total_exported`: 总导出记录数

## 使用示例

### 准备提纲标注数据

```bash
# 导出所有提纲标注数据（使用默认两栏模板）
python -m labeling.outline.prepare

# 使用三栏模板导出
python -m labeling.outline.prepare --template three_column

# 分批导出（使用批次模式）
python -m labeling.outline.prepare --limit 100 --batch-mode
python -m labeling.outline.prepare --limit 100 --batch-mode  # 生成 batch_02.json

# 指定日志文件列表（支持 json 和 jsonl）
python -m labeling.outline.prepare --log-files file1.jsonl file2.json

# 指定输出目录（自动生成带时间戳的文件名）
python -m labeling.outline.prepare --output-dir data/my_labels

# 只导出特定文件
python -m labeling.outline.prepare --file-key 0fe25f94c682ec25

# 强制重新导出
python -m labeling.outline.prepare --force

# 列出所有可用模板
python -m labeling.outline.prepare --list-templates
```

### 在 Python 代码中使用（使用模板系统）

```python
from labeling.outline.prepare import prepare_outline_labeling_data
from labeling.templates.outline.config import list_templates

# 查看可用模板
templates = list_templates()
print(f"可用模板: {templates}")

# 准备提纲标注数据（指定模板）
prepare_outline_labeling_data(
    log_files=['logs/llm_calls/file1.jsonl', 'logs/llm_calls/file2.json'],
    output_dir='data/my_labels',
    limit=100,
    template_name='two_column',
    batch_mode=True
)

# 使用数据转换器
from labeling.templates.outline.converter import OutlineDataConverter

converter = OutlineDataConverter()
result = converter.convert_batch_with_stats(log_records)
print(f"成功率: {result['stats']['success_rate']}")
```

## 新增文件说明

### templates/ 目录

模板系统核心目录，包含所有 Label Studio 标注模板：

```
templates/
├── __init__.py           # 模板模块初始化
├── base.py               # 模板基类和核心实现
│   ├── BaseLabelStudioTemplate          # 抽象基类
│   ├── OutlineTemplate                  # 单栏模板
│   ├── OutlineTwoColumnTemplate         # 双栏模板
│   ├── OutlineThreeColumnTemplate       # 三栏模板
│   ├── TEMPLATE_REGISTRY                # 模板注册表
│   ├── get_template()                   # 获取模板实例
│   └── register_template()             # 注册新模板
└── outline/              # 提纲提取任务模板
    ├── __init__.py
    ├── config.py        # 模板元数据和配置
    ├── converter.py     # 数据转换器
    ├── two_column.xml   # Label Studio 配置（双栏）
    └── three_column.xml # Label Studio 配置（三栏）
```

**主要文件说明**:

- **base.py**: 模板系统的核心实现，包含基类、模板注册表和工具函数
- **outline/config.py**: 提纲提取任务的模板元数据，包含字段定义、UI 配置等
- **outline/converter.py**: 数据转换器，用于从 LLM 日志中提取和转换数据
- **outline/*.xml**: Label Studio 的标注配置文件

### screenshots/ 目录

用于存储 Label Studio 标注平台相关的截图：

```
screenshots/
├── README.md            # 截图命名和组织规范
├── .gitkeep             # 占位文件
├── setup/               # 项目设置相关截图
├── templates/           # 标注模板截图
├── workflows/           # 工作流程截图
├── issues/              # 问题记录截图
└── examples/            # 标注示例截图
```

**命名规范**: `YYYY-MM-DD_description.ext`

示例：
- `2026-02-16_initial_setup.png`
- `2026-02-16_three_column_template.png`
- `2026-02-16_annotation_example.png`

详细说明请参考 [screenshots/README.md](screenshots/README.md)

### skills/ 目录

用于存储标注相关的技能和工具脚本（如需要）。

## 完整工作流程

### 从 LLM 日志到 Label Studio 的数据流

```
1. LLM 调用日志
   └── logs/llm_calls/*.jsonl
       ├── timestamp
       ├── file_key
       ├── success
       ├── function
       └── response
           ├── prompt
           ├── answer
           ├── model
           └── reasoning

2. 数据准备（使用模板系统）
   └── python -m labeling.outline.prepare --template two_column
       ├── 读取日志文件
       ├── 使用数据转换器提取数据
       ├── 应用模板配置
       ├── 生成标注数据 JSON
       └── 保存断点续传状态
           ├── labeling_data/outline/batch_01.json
           └── .outline_labeling_state.json

3. 导入 Label Studio
   └── 创建项目 -> 导入 JSON 数据 -> 配置标注模板
       ├── 上传标注数据 JSON
       ├── 从模板配置生成 Label Studio XML
       └── 开始标注

4. 标注与导出
   └── 标注人员标注 -> 导出标注结果 -> 转换为训练数据
       ├── 使用 from_label_studio() 转换
       └── 生成训练数据集
```

### 数据准备完整流程

#### 步骤 1: 准备 LLM 日志

确保日志文件在 `logs/llm_calls/` 目录下，格式为 JSONL：

```jsonl
{"timestamp": "2026-02-16T10:30:00", "file_key": "abc123", "success": true, "response": {"prompt": "...", "answer": "...", "model": "gpt-4"}}
{"timestamp": "2026-02-16T10:31:00", "file_key": "def456", "success": true, "response": {"prompt": "...", "answer": "...", "model": "gpt-4"}}
```

#### 步骤 2: 查看可用模板

```bash
python -m labeling.outline.prepare --list-templates
```

输出：
```
可用的提纲标注模板：
============================================================

模板名称: two_column
显示名称: 两栏提纲标注模板
描述: 适用于提纲提取任务的两栏标注模板，左侧显示原始文本，右侧提供 JSON 编辑器进行提纲标注。
版本: 1.0.0
作者: PDF Workbench Team

特性:
  - 原始文本展示
  - JSON 格式提纲编辑
  - 语法高亮
  - 实时验证
  - 快捷键支持

UI配置: two_column
------------------------------------------------------------

模板名称: three_column
显示名称: 三栏提纲标注模板
描述: 适用于提纲提取任务的三栏标注模板，左栏显示原始文本，中栏提供 JSON 编辑器，右栏实时预览提纲结构。
版本: 1.0.0
作者: PDF Workbench Team

特性:
  - 原始文本展示
  - JSON 格式提纲编辑
  - 语法高亮
  - 实时验证
  - 结构化预览
  - 快捷键支持
  - 导出功能

UI配置: three_column
------------------------------------------------------------
```

#### 步骤 3: 导出标注数据

```bash
# 使用两栏模板导出（适合大多数场景）
python -m labeling.outline.prepare --template two_column --output-dir data/labels

# 使用三栏模板导出（需要预览时）
python -m labeling.outline.prepare --template three_column --output-dir data/labels

# 批次模式（自动生成 batch_01.json, batch_02.json...）
python -m labeling.outline.prepare --template two_column --batch-mode --limit 50
```

#### 步骤 4: 生成 Label Studio 配置

```python
from labeling.templates.base import get_template

# 获取模板
template = get_template("outline_two_column")

# 生成配置
config = template.generate_config()

# 保存到文件
template.save_config("label_config.xml")
```

#### 步骤 5: 导入 Label Studio

1. 创建新的 Label Studio 项目
2. 导入标注数据 JSON 文件
3. 配置标注界面（使用生成的 XML 配置）
4. 开始标注

#### 步骤 6: 导出标注结果

标注完成后，从 Label Studio 导出标注结果（JSON 格式），然后使用模板转换器处理：

```python
from labeling.templates.base import get_template

template = get_template("outline_two_column")

# 将 Label Studio 结果转换为应用格式
annotations = template.from_label_studio(label_studio_results)

# 保存为训练数据
import json
with open('training_data.json', 'w', encoding='utf-8') as f:
    json.dump(annotations, f, ensure_ascii=False, indent=2)
```

### 命令行参数说明

#### 通用参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--log-files` | 日志文件列表（支持 json/jsonl） | 无 | `--log-files file1.jsonl file2.json` |
| `--log-dir` | 日志目录（未指定 log-files 时使用） | `../../extractor/outline_extractor/logs/llm_calls` | `--log-dir logs/llm_calls` |
| `--output-dir` | 输出目录路径 | `../../labeling_data/outline` | `--output-dir data/labels` |
| `--limit` | 限制导出数量 | 无限制 | `--limit 100` |
| `--batch-mode` | 自动批次模式 | False | `--batch-mode` |
| `--file-key` | 只导出特定文件的记录 | 全部文件 | `--file-key abc123` |
| `--force` | 强制重新导出 | False | `--force` |
| `--template` | 选择标注模板 | `two_column` | `--template three_column` |
| `--list-templates` | 列出所有可用模板 | False | `--list-templates` |

#### 参数组合示例

```bash
# 场景 1: 首次导出，使用默认模板
python -m labeling.outline.prepare

# 场景 2: 导出特定日志文件，使用三栏模板
python -m labeling.outline.prepare \
    --log-files logs/2026_02_16/*.jsonl \
    --template three_column

# 场景 3: 分批标注，每次 50 条
python -m labeling.outline.prepare \
    --template two_column \
    --limit 50 \
    --batch-mode

# 场景 4: 强制重新导出所有数据
python -m labeling.outline.prepare \
    --template two_column \
    --force

# 场景 5: 查看模板详情
python -m labeling.outline.prepare --list-templates
```

## 添加新的标注任务

### 步骤

1. **创建目录结构**:
   ```bash
   mkdir -p labeling/your_task
   ```

2. **创建 `__init__.py`**:
   ```python
   """Your Task Annotation Module"""
   from .prepare import prepare_your_task_data

   __all__ = ['prepare_your_task_data']
   ```

3. **创建 `prepare.py`**:
   ```python
   from labeling.utils import BaseLabelingExporter

   class YourTaskExporter(BaseLabelingExporter):
       def extract_your_task_data(self, record):
           # 实现数据提取逻辑
           return {
               'prompt': ...,
               'response': ...
           }
   ```

4. **创建 README 文档**:
   ```bash
   # 添加详细的使用说明
   ```

5. **更新模块 `__init__.py`**:
   ```python
   from .your_task.prepare import prepare_your_task_data
   ```

### 示例代码

完整的示例参考 `labeling/outline/prepare.py`

## 添加新的模板

### 步骤

1. **在 `templates/` 下创建任务目录**:
   ```bash
   mkdir -p labeling/templates/your_task
   ```

2. **创建 `__init__.py`**:
   ```python
   """Your Task Templates Module"""
   from .config import get_template_info, list_templates
   from .converter import YourTaskDataConverter

   __all__ = ['get_template_info', 'list_templates', 'YourTaskDataConverter']
   ```

3. **创建 `config.py`**:
   ```python
   """模板元数据配置"""

   TEMPLATE_METADATA = {
       'your_template_name': {
           'name': 'your_template_name',
           'display_name': '你的模板显示名称',
           'description': '模板描述',
           'version': '1.0.0',
           'author': 'Your Name',
           'created_date': '2026-02-16',
           'features': ['特性1', '特性2'],
           'data_fields': {
               # 数据字段定义
           },
           'label_fields': {
               # 标签字段定义
           },
           'ui_config': {
               'layout': 'your_layout',
               # UI 配置
           }
       }
   }

   def get_template_info(template_name: str):
       return TEMPLATE_METADATA.get(template_name)

   def list_templates(include_metadata: bool = False):
       if include_metadata:
           return list(TEMPLATE_METADATA.values())
       return list(TEMPLATE_METADATA.keys())
   ```

4. **创建 `converter.py`**:
   ```python
   """数据转换器"""

   class YourTaskDataConverter:
       def __init__(self, strict: bool = False):
           self.strict = strict

       def extract_from_log(self, record: dict) -> dict:
           # 实现数据提取逻辑
           return {
               'prompt': ...,
               'answer': ...,
               'metadata': {...}
           }
   ```

5. **在 `templates/base.py` 中注册模板**:
   ```python
   from labeling.templates.your_task import YourTaskTemplate

   TEMPLATE_REGISTRY['your_template_name'] = YourTaskTemplate
   ```

6. **在任务的 `prepare.py` 中集成模板**:
   ```python
   from labeling.templates.base import get_template
   from labeling.templates.your_task.config import get_template_info

   # 使用模板
   template = get_template('your_template_name')
   config = template.generate_config()
   ```

### 示例代码

完整的示例参考 `labeling/templates/outline/` 目录

## 配置和参数（已整合）

注意：本节已整合到"完整工作流程"中的"命令行参数说明"部分。

## 数据格式规范

### 通用 JSON 格式

```json
[
  {
    "prompt": "输入数据（如 OCR 提取的文本）",
    "answer": "目标输出（如 LLM 的回答）",
    "model": "使用的模型",
    "reasoning": "推理过程（可选）",
    "metadata": {
      "file_key": "文件标识",
      "timestamp": "时间戳",
      "model": "模型名称"
    }
  },
  ...
]
```

### 特定任务格式

不同任务可能需要不同的字段，参考各任务的文档。

### 使用模板系统的数据格式

使用模板系统导出的数据会自动添加模板信息：

```json
{
  "prompt": "原始文本内容...",
  "answer": "LLM 生成的回答",
  "model": "gpt-4",
  "reasoning": "推理过程...",
  "metadata": {
    "file_key": "abc123",
    "timestamp": "2026-02-16T10:30:00",
    "model": "gpt-4"
  },
  "_template": "two_column",
  "_template_description": "适用于提纲提取任务的两栏标注模板..."
}
```

## 输出目录

建议的目录结构（包含模板系统）：

```
pdf_mining/
├── extractor/                    # PDF 提取器
│   └── logs/
│       └── llm_calls/           # LLM 调用日志
│           ├── 2026_02_08_16_59_21.jsonl
│           └── ...
├── labeling/                     # 标注准备模块
│   ├── __init__.py
│   ├── utils.py
│   ├── README.md                 # 本文档
│   ├── templates/               # Label Studio 模板系统
│   │   ├── __init__.py
│   │   ├── base.py             # 模板基类和注册表
│   │   └── outline/            # 提纲提取模板
│   │       ├── __init__.py
│   │       ├── config.py        # 模板元数据
│   │       ├── converter.py     # 数据转换器
│   │       ├── two_column.xml
│   │       └── three_column.xml
│   ├── screenshots/             # 截图文件夹
│   │   ├── README.md
│   │   ├── .gitkeep
│   │   └── (按日期命名的截图)
│   └── outline/                # 提纲提取任务
│       ├── __init__.py
│       ├── prepare.py
│       └── README.md
├── labeling_data/               # 导出的标注数据
│   └── outline/
│       ├── outline_20260216_103045.json  # 时间戳文件
│       ├── batch_01.json                  # 批次文件
│       ├── batch_02.json
│       └── ...
├── .outline_labeling_state.json           # 提纲任务状态文件
└── ...                                 # 其他任务状态文件
```

## 常见问题

### Q: 如何查看已导出的记录数？

```bash
cat .outline_labeling_state.json | grep "total_exported"
```

### Q: 如何重新导出所有数据？

```bash
python -m labeling.outline.prepare --force
```

### Q: 如何清除断点续传状态？

```bash
rm .outline_labeling_state.json
```

### Q: 可以同时导出多个任务的数据吗？

可以，每个任务的状态文件是独立的：

```bash
python -m labeling.outline.prepare --output data/outline.json
python -m labeling.classification.prepare --output data/classification.json  # 未来
```

### Q: 如何选择合适的模板？

根据文档类型和标注需求选择：

- **单栏模板 (`outline`)**: 适合长文档标注，需要专注时使用
- **双栏模板 (`outline_two_column`)**: 适合中等长度文档，需要同时参考原文和标注时使用
- **三栏模板 (`outline_three_column`)**: 适合复杂文档，需要查看详细属性时使用

### Q: 模板系统的数据格式有什么变化？

使用模板系统导出的数据会自动添加以下字段：

- `_template`: 使用的模板名称
- `_template_description`: 模板描述信息

这些字段有助于追踪数据来源，但不会影响标注流程。

### Q: 如何自定义模板？

参考"添加新的模板"部分，创建自定义模板需要：

1. 继承 `BaseLabelStudioTemplate`
2. 实现 `generate_config()`, `from_label_studio()`, `to_label_studio()` 方法
3. 在 `TEMPLATE_REGISTRY` 中注册模板
4. 创建配置和转换器模块

## 技术细节

### 哈希生成

使用 `MD5(timestamp + file_key + content)` 生成记录的唯一标识：

```python
content = f"{record['timestamp']}{record['file_key']}{record['current_batch_content']}"
record_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:16]
```

### JSONL 格式

日志文件为 JSONL 格式（每行一个 JSON 对象）：

```json
{"timestamp": "...", "function": "...", "response": {...}, "success": true, ...}
{"timestamp": "...", "function": "...", "response": {...}, "success": true, ...}
...
```

### 状态文件格式

```json
{
  "exported_record_hashes": ["abc123...", "def456...", ...],
  "last_export_time": "2026-02-08T17:30:00",
  "total_exported": 100
}
```

## 依赖

- Python 3.7+
- 标准库：`json`, `hashlib`, `argparse`, `pathlib`, `datetime`

无需安装额外的第三方库。

## 许可

与 pdf_extractor 项目一致。
