# 训练数据构建模块

用于从不同来源构建微调训练数据。

## 功能概述

本模块提供两种方式构建训练数据：

### 1. 从标注数据构建（`from_labeled/`）
- **数据来源**: Label Studio 等平台人工标注的数据
- **适用场景**: 需要高质量、经过人工验证的训练数据
- **特点**:
  - 数据质量高
  - 已经过人工修正
  - 适合微调以提高准确率

### 2. 从日志数据构建（`from_logs/`）
- **数据来源**: LLM 调用日志（.jsonl 文件）
- **适用场景**: 直接使用顶尖模型生成的数据作为训练数据
- **特点**:
  - 数据量大
  - 无需人工标注
  - 适合蒸馏或增量训练

## 目录结构

```
training_data_builder/
├── __init__.py              # 模块入口
├── utils.py                 # 共享工具（格式转换、验证、拆分等）
├── README.md                # 本文档
├── from_labeled/            # 从标注数据构建
│   ├── __init__.py
│   ├── convert.py           # 转换脚本
│   └── README.md            # 详细说明
└── from_logs/               # 从日志数据构建
    ├── __init__.py
    ├── extract.py           # 提取脚本
    └── README.md            # 详细说明
```

## 支持的训练格式

### 1. Alpaca 格式
```json
{
  "instruction": "从以下候选内容中提取文档提纲",
  "input": "第1页候选内容：...",
  "output": "【当前页组确认提纲】..."
}
```

### 2. ShareGPT 格式
```json
{
  "conversations": [
    {"from": "human", "value": "第1页候选内容：..."},
    {"from": "gpt", "value": "【当前页组确认提纲】..."}
  ]
}
```

### 3. Instruction 格式
```json
{
  "instruction": "任务：从以下候选内容中提取文档提纲\n\n输入内容：\n第1页候选内容：...",
  "output": "【当前页组确认提纲】..."
}
```

### 4. OpenAI Chat 格式
```json
{
  "messages": [
    {"role": "user", "content": "第1页候选内容：..."},
    {"role": "assistant", "content": "【当前页组确认提纲】..."}
  ]
}
```

## 快速开始

### 从标注数据构建

```bash
# 基础使用
python -m training_data_builder.from_labeled.convert \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --format alpaca

# 指定输出文件
python -m training_data_builder.from_labeled.convert \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --format alpaca \
    --output training_data/alpaca_batch_01.json

# 拆分数据集
python -m training_data_builder.from_labeled.convert \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --format alpaca \
    --split-ratio 0.8,0.1,0.1 \
    --output training_data/alpaca_batch_01.json
```

### 从日志数据构建

```bash
# 基础使用
python -m training_data_builder.from_logs.extract \
    --log-dir ../outline_extractor/logs/llm_calls \
    --format alpaca

# 限制数据量
python -m training_data_builder.from_logs.extract \
    --log-dir ../outline_extractor/logs/llm_calls \
    --format alpaca \
    --limit 1000

# 去重和过滤
python -m training_data_builder.from_logs.extract \
    --log-dir ../outline_extractor/logs/llm_calls \
    --format alpaca \
    --deduplicate \
    --min-length 100 \
    --max-length 10000 \
    --output training_data/alpaca_from_logs.json
```

## 数据验证

所有构建的训练数据都会自动验证：

- ✅ **完整性检查**: 检查必填字段
- ✅ **空值检查**: 检测空的 prompt 或 response
- ✅ **长度检查**: 检测过短或过长的数据
- ✅ **格式检查**: 验证目标格式的正确性

## 数据集拆分

支持自动拆分训练集、验证集、测试集：

```bash
--split-ratio 0.8,0.1,0.1
```

会生成三个文件：
- `{basename}_train.json`: 80% 训练数据
- `{basename}_val.json`: 10% 验证数据
- `{basename}_test.json`: 10% 测试数据

## 数据过滤

支持多种过滤方式：

```bash
# 按长度过滤
--min-length 100     # 最小 100 字符
--max-length 10000   # 最大 10000 字符

# 去重（基于 prompt 字段）
--deduplicate
--dedup-field prompt
```

## 常见使用场景

### 场景 1: 从标注数据构建训练集

```bash
# 1. 人工标注完成后
cd labeling/outline
python prepare.py --batch-mode --limit 100

# 2. 在 Label Studio 中标注
# （手动操作）

# 3. 导出标注数据到 labeled_data/

# 4. 转换为训练格式
cd ../training_data_builder
python -m from_labeled.convert \
    --input ../labeled_data/outline/outline_batch_01_labeled.json \
    --format alpaca \
    --split-ratio 0.8,0.1,0.1 \
    --output ../training_data/alpaca_batch_01.json
```

### 场景 2: 从日志数据快速构建训练集

```bash
# 1. 运行提纲提取，生成日志
cd ../outline_extractor
python main.py

# 2. 从日志提取训练数据
cd ../training_data_builder
python -m from_logs.extract \
    --log-dir ../outline_extractor/logs/llm_calls \
    --format alpaca \
    --limit 10000 \
    --deduplicate \
    --output ../training_data/alpaca_from_logs.json
```

### 场景 3: 混合使用两种来源

```bash
# 从标注数据构建（高质量）
python -m from_labeled.convert \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --format alpaca \
    --output training_data/alpaca_labeled.json

# 从日志数据构建（大数据量）
python -m from_logs.extract \
    --log-dir ../outline_extractor/logs/llm_calls \
    --format alpaca \
    --output training_data/alpaca_logs.json

# 合并两个数据集（手动或使用脚本）
```

## 数据质量建议

### 从标注数据
- ✅ **推荐用途**: 最终微调、提高准确率
- ✅ **数据量**: 500-5000 条（视任务复杂度）
- ✅ **质量要求**: 高质量、人工验证
- ✅ **适用格式**: Alpaca, ShareGPT

### 从日志数据
- ✅ **推荐用途**: 蒸馏、增量训练、预热
- ✅ **数据量**: 1000-100000 条
- ✅ **质量要求**: 过滤低质量数据
- ✅ **预处理**: 去重、长度过滤

## 输出文件示例

### 不拆分
```
training_data/alpaca_batch_01.json  # 所有数据
```

### 拆分
```
training_data/alpaca_batch_01_train.json  # 训练集 (80%)
training_data/alpaca_batch_01_val.json    # 验证集 (10%)
training_data/alpaca_batch_01_test.json   # 测试集 (10%)
training_data/alpaca_batch_01_all.json    # 所有数据（可选）
```

## 下一步

训练数据构建完成后，可以：

1. **验证数据**: 使用 `token_analysis` 模块分析 token 使用
2. **开始微调**: 使用各种微调框架（LLaMA-Factory, Firefly 等）
3. **评估模型**: 在验证集上评估微调效果
4. **部署模型**: 部署到生产环境

## 相关文档

- [从标注数据详细说明](from_labeled/README.md)
- [从日志数据详细说明](from_logs/README.md)
- [Token 分析模块](../token_analysis/README.md)

---

**最后更新**: 2026-02-08
**维护者**: PDF 提取团队
