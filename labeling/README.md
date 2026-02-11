# 标注数据准备模块

本模块用于从 LLM 调用日志中提取数据，为 Label Studio 等标注平台准备数据集。

## 目录结构

```
labeling/
├── __init__.py           # 模块初始化
├── utils.py              # 共享工具类
├── README.md             # 本文档
└── outline/              # 提纲提取标注任务
    ├── __init__.py
    ├── prepare.py        # 提纲标注数据准备脚本
    └── README.md         # 提纲标注说明文档
```

## 设计理念

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
python -m labeling.outline.prepare
```

**详细说明**: 查看 [outline/README.md](outline/README.md)

**数据格式**:
```json
{
  "prompt": "OCR 候选提纲内容...",
  "response": "LLM 提取的提纲结果..."
}
```

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
# 导出所有提纲标注数据
python -m labeling.outline.prepare

# 指定输出文件
python -m labeling.outline.prepare --output data/outline_labels.json

# 分批导出（每次 100 条）
python -m labeling.outline.prepare --limit 100 --output batch_01.json
python -m labeling.outline.prepare --limit 100 --output batch_02.json

# 只导出特定文件
python -m labeling.outline.prepare --file-key 0fe25f94c682ec25

# 强制重新导出
python -m labeling.outline.prepare --force
```

### 在 Python 代码中使用

```python
from labeling.outline.prepare import prepare_outline_labeling_data

# 准备提纲标注数据
prepare_outline_labeling_data(
    log_dir='logs/llm_calls',
    output_file='data/outline_labels.json',
    limit=100,
    file_key='0fe25f94c682ec25',
    force=False
)
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

## 配置和参数

### 通用参数

所有标注任务都支持以下参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--log-dir` | 日志目录路径 | `logs/llm_calls` |
| `--output` | 输出 JSON 文件路径 | `labeling_data/{task}_labeling.json` |
| `--limit` | 限制导出数量 | 无限制 |
| `--file-key` | 只导出特定文件的记录 | 全部文件 |
| `--force` | 强制重新导出 | 否 |

### 任务特定参数

每个任务可能有额外的参数，参考各任务的 README 文档。

## 数据格式规范

### 通用 JSON 格式

```json
[
  {
    "prompt": "输入数据（如 OCR 提取的文本）",
    "response": "目标输出（如 LLM 的回答）"
  },
  ...
]
```

### 特定任务格式

不同任务可能需要不同的字段，参考各任务的文档。

## 输出目录

建议的目录结构：

```
pdf_extractor/
├── logs/                          # 原始日志
│   └── llm_calls/
│       ├── 2026_02_08_16_59_21.jsonl
│       └── ...
├── labeling/                      # 标注准备模块
│   ├── outline/
│   └── ...
├── labeling_data/                 # 导出的标注数据
│   ├── outline_labeling.json
│   ├── batch_01.json
│   └── batch_02.json
├── .outline_labeling_state.json   # 提纲任务状态文件
└── .classification_labeling_state.json  # 分类任务状态文件（未来）
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
