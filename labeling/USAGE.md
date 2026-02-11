# 标注数据准备 - 快速开始

## 概述

本模块采用模块化设计，按任务类型组织，便于管理和扩展不同类型的标注任务。

## 目录结构

```
pdf_extractor/
├── labeling/                         # 标注数据准备模块
│   ├── __init__.py
│   ├── utils.py                      # 共享工具类
│   ├── README.md                     # 总体说明
│   ├── .gitignore
│   └── outline/                      # 提纲提取标注任务
│       ├── __init__.py
│       ├── prepare.py                # 导出脚本
│       └── README.md                 # 详细说明
├── labeling_data/                    # 导出的标注数据（输出目录）
│   ├── outline_labeling.json
│   ├── batch_01.json
│   └── batch_02.json
└── .outline_labeling_state.json      # 断点续传状态文件
```

## 核心优势

### ✅ 按任务组织
- 每个标注任务有独立的子模块
- 清晰的职责划分
- 易于维护和扩展

### ✅ 共享基础设施
- 统一的日志读取
- 统一的断点续传
- 统一的状态管理

### ✅ 断点续传
- 基于内容哈希去重
- 自动跳过已导出记录
- 支持分批导出

### ✅ 灵活扩展
- 添加新任务只需3步
- 继承基类即可
- 最小化代码重复

## 快速使用

### 提纲提取标注数据

```bash
# 进入项目目录
cd pdf_extractor/outline_extractor

# 导出所有数据
python ../labeling/outline/prepare.py --log-dir logs/llm_calls

# 导出前 100 条
python ../labeling/outline/prepare.py --log-dir logs/llm_calls --limit 100

# 导出到指定文件
python ../labeling/outline/prepare.py --log-dir logs/llm_calls --output data/batch_01.json

# 只导出特定文件
python ../labeling/outline/prepare.py --log-dir logs/llm_calls --file-key 0fe25f94c682ec25

# 强制重新导出
python ../labeling/outline/prepare.py --log-dir logs/llm_calls --force
```

### 分批标注工作流

```bash
# 第一批
python ../labeling/outline/prepare.py --log-dir logs/llm_calls --limit 100 --output ../labeling_data/batch_01.json

# 第二批（自动跳过已导出的）
python ../labeling/outline/prepare.py --log-dir logs/llm_calls --limit 100 --output ../labeling_data/batch_02.json

# 第三批
python ../labeling/outline/prepare.py --log-dir logs/llm_calls --limit 100 --output ../labeling_data/batch_03.json
```

## 输出数据格式

### 提纲提取任务

```json
[
  {
    "prompt": "第1页候选内容：\n| 页码 | 行号 | 内容预览 |\n|------|------|----------|\n| 1 | 1 | 标题1 |\n...",
    "response": "【当前页组确认提纲】（第1-12页）\n\n1. [一级] Abstract (1:9)\n..."
  }
]
```

- **prompt**: OCR 提取的候选提纲（LLM 的输入）
- **response**: LLM 提取的提纲结果（待人工修正）

## 断点续传

### 工作原理

1. **记录哈希**: 每条记录生成唯一哈希（基于 timestamp + file_key + content）
2. **状态持久化**: 保存已导出的哈希列表到 `.outline_labeling_state.json`
3. **自动跳过**: 下次运行时自动跳过已导出的记录
4. **增量更新**: 只导出新增的记录

### 查看状态

```bash
cat .outline_labeling_state.json
```

输出：
```json
{
  "exported_record_hashes": ["abc123...", "def456...", ...],
  "last_export_time": "2026-02-08T17:30:00",
  "total_exported": 100
}
```

### 重置状态

```bash
# 删除状态文件
rm .outline_labeling_state.json

# 或使用 --force 强制重新导出
python ../labeling/outline/prepare.py --force
```

## 添加新的标注任务

### 步骤

1. **创建子模块目录**:
   ```bash
   mkdir -p labeling/your_task
   ```

2. **创建 `__init__.py`**:
   ```python
   from .prepare import prepare_your_task_data
   __all__ = ['prepare_your_task_data']
   ```

3. **创建 `prepare.py`**:
   ```python
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent.parent))

   from labeling.utils import BaseLabelingExporter
   import argparse

   class YourTaskExporter(BaseLabelingExporter):
       def __init__(self):
           super().__init__(task_name='your_task_labeling')

       def extract_your_task_data(self, record):
           # 提取你的标注数据
           return {
               'prompt': ...,
               'response': ...
           }

   def parse_args():
       parser = argparse.ArgumentParser(...)
       # 添加参数
       return parser.parse_args()

   def main():
       args = parse_args()
       exporter = YourTaskExporter()
       # ... 导出逻辑

   if __name__ == "__main__":
       main()
   ```

4. **创建 README 文档**:
   ```bash
   # 添加使用说明
   ```

5. **更新模块 `__init__.py`**:
   ```python
   from .your_task.prepare import prepare_your_task_data
   __all__ = [..., 'prepare_your_task_data']
   ```

## 常见问题

### Q: 导出的数据在哪里？

默认输出到 `labeling_data/outline_labeling.json`，可通过 `--output` 参数指定。

### Q: 如何避免重复导出？

使用断点续传机制，无需手动干预。每次运行会自动跳过已导出的记录。

### Q: 如何重新导出所有数据？

使用 `--force` 参数或删除状态文件。

### Q: 标注数据如何用于 Label Studio？

1. 在 Label Studio 中创建新项目
2. 上传导出的 JSON 文件
3. 配置标注界面（prompt 为输入，response 为待修正输出）
4. 开始标注

### Q: 可以同时导出多个任务的数据吗？

可以，每个任务有独立的状态文件，互不干扰：

```bash
python ../labeling/outline/prepare.py --output data/outline.json
python ../labeling/classification/prepare.py --output data/classification.json
```

## 技术细节

### 记录哈希算法

```python
content = f"{record['timestamp']}{record['file_key']}{record['current_batch_content']}"
hash_value = hashlib.md5(content.encode('utf-8')).hexdigest()[:16]
```

### 日志文件格式

JSONL（每行一个 JSON 对象）：
```json
{"timestamp": "...", "response": {...}, "success": true, ...}
{"timestamp": "...", "response": {...}, "success": true, ...}
```

### 状态文件格式

```json
{
  "exported_record_hashes": ["abc123...", "def456..."],
  "last_export_time": "2026-02-08T17:30:00",
  "total_exported": 100
}
```

## 相关文档

- [总体说明](README.md)
- [提纲提取任务说明](outline/README.md)
- [共享工具代码](utils.py)

## 下一步

1. 导出第一批标注数据
2. 在 Label Studio 中配置标注项目
3. 完成人工标注
4. 使用标注数据微调模型
5. 评估模型效果

---

**提示**: 建议使用 `--limit` 参数分批导出，每批 50-100 条，便于管理和标注。
