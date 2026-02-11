# 从标注数据构建训练数据

## 功能说明

从 Label Studio 等平台导出的标注数据转换为各种训练格式。

## 使用方法

### 基础用法

```bash
python -m training_data_builder.from_labeled.convert \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --format alpaca
```

### 完整参数

```bash
python -m training_data_builder.from_labeled.convert \
    --input INPUT_FILE \
    --format FORMAT \
    --output OUTPUT_FILE \
    --split-ratio 0.8,0.1,0.1 \
    --min-length 50 \
    --max-length 10000 \
    --shuffle \
    --seed 42
```

## 参数说明

| 参数 | 说明 | 默认值 | 必填 |
|------|------|--------|------|
| `--input` | 输入 JSON 文件路径（标注数据） | - | ✅ |
| `--format` | 目标训练格式 | `alpaca` | ❌ |
| `--output` | 输出文件路径 | 自动生成 | ❌ |
| `--split-ratio` | 数据集拆分比例 | 不拆分 | ❌ |
| `--min-length` | 响应最小长度（字符数） | 无限制 | ❌ |
| `--max-length` | 响应最大长度（字符数） | 无限制 | ❌ |
| `--shuffle` | 是否打乱数据 | True | ❌ |
| `--seed` | 随机种子 | 42 | ❌ |

## 数据格式要求

输入 JSON 文件应为数组格式，每条数据包含 `prompt` 和 `response` 字段：

```json
[
  {
    "id": 1,
    "prompt": "第1页候选内容：...",
    "response": "【当前页组确认提纲】..."
  }
]
```

## 输出示例

### 不拆分数据集

```bash
python -m training_data_builder.from_labeled.convert \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --format alpaca \
    --output training_data/alpaca_batch_01.json
```

输出：
```
training_data/alpaca_batch_01.json  # 所有数据
```

### 拆分数据集

```bash
python -m training_data_builder.from_labeled.convert \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --format alpaca \
    --split-ratio 0.8,0.1,0.1 \
    --output training_data/alpaca_batch_01.json
```

输出：
```
training_data/alpaca_batch_01_train.json  # 80% 训练数据
training_data/alpaca_batch_01_val.json    # 10% 验证数据
training_data/alpaca_batch_01_test.json   # 10% 测试数据
training_data/alpaca_batch_01_all.json    # 100% 所有数据
```

## 工作流程

1. **加载数据**: 读取 JSON 文件
2. **过滤数据**: 根据长度过滤（可选）
3. **转换格式**: 转换为目标训练格式
4. **验证数据**: 检查数据质量和完整性
5. **拆分数据集**: 拆分为 train/val/test（可选）
6. **保存数据**: 保存到文件

## 使用示例

### 示例 1: 转换为 Alpaca 格式

```bash
python -m training_data_builder.from_labeled.convert \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --format alpaca \
    --output training_data/alpaca_batch_01.json
```

### 示例 2: 转换为 ShareGPT 格式并拆分

```bash
python -m training_data_builder.from_labeled.convert \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --format sharegpt \
    --split-ratio 0.8,0.1,0.1 \
    --output training_data/sharegpt_batch_01.json
```

### 示例 3: 过滤短数据

```bash
python -m training_data_builder.from_labeled.convert \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --format alpaca \
    --min-length 100 \
    --max-length 8000 \
    --output training_data/alpaca_filtered.json
```

## 注意事项

1. **数据质量**: 确保标注数据已经过验证和修正
2. **格式选择**: 根据微调框架选择合适的格式
3. **数据量**: 一般需要 500-5000 条标注数据
4. **拆分比例**: 推荐使用 0.8,0.1,0.1
