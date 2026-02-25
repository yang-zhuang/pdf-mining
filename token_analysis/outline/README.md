# Token统计工具

统计SFT/GRPO/EVAL数据的token长度分布。

## 功能

- 支持三种数据类型：`sft`、`grpo`、`eval`
- 可指定统计一种或多种数据类型
- 使用Qwen tokenizer进行token统计
- 输出详细的统计信息（平均值、中位数、分位数等）

## 安装依赖

需要安装以下任一库：

```bash
# 方式1: 使用 transformers (推荐)
pip install transformers

# 或方式2: 使用 modelscope
pip install modelscope
```

脚本会自动检测可用的库并使用对应的 `AutoTokenizer`。

## 使用方法

### 基本用法（统计所有类型）

```bash
python token_analysis/outline/statistics.py
```

### 指定数据类型

```bash
# 只统计SFT数据
python token_analysis/outline/statistics.py --types sft

# 统计SFT和GRPO数据
python token_analysis/outline/statistics.py --types sft grpo

# 统计GRPO和EVAL数据
python token_analysis/outline/statistics.py --types grpo eval
```

### 指定数据目录

```bash
python token_analysis/outline/statistics.py --data-dir /path/to/data
```

### 指定模型（用于加载tokenizer）

```bash
python token_analysis/outline/statistics.py --model-name Qwen/Qwen3-0.6B
```

### 显示详细进度

```bash
python token_analysis/outline/statistics.py --verbose
```

### 完整示例

```bash
python token_analysis/outline/statistics.py \
    --data-dir training_data/outline/three_column \
    --types sft grpo \
    --model-name Qwen/Qwen3-0.6B \
    --verbose
```

## 输出说明

脚本会输出以下统计信息：

- **样本数**: 数据集中的样本数量
- **总Token数**: 所有样本的token总数
- **平均Token数**: 每个样本的平均token数量
- **中位数Token数**: token数量的中位数
- **最小值/最大值**: token数量的最小和最大值
- **分位数** (P10, P25, P50, P75, P90, P95, P99): token数量在不同分位点上的值

对于SFT数据，还会分别统计输入和输出的token数量。

## 数据文件格式

脚本会根据文件名前缀自动识别数据类型：

- `sft_labeled_*.jsonl`: SFT数据
- `grpo_labeled_*.jsonl`: GRPO数据
- `eval_labeled_*.jsonl`: EVAL数据
