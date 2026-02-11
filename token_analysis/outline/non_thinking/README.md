# 非思考模式 Token 分析

## 功能说明

直接统计 prompt + response 的 token 数量，无需调用模型推理。

## 使用方法

### 基础用法

```bash
python -m token_analysis.non_thinking.analyze --input ../labeled_data/outline/batch_01_labeled.json
```

### 完整参数

```bash
python -m token_analysis.non_thinking.analyze \
    --input INPUT_FILE \
    --model-path MODEL_PATH \
    --output OUTPUT_FILE
```

## 参数说明

| 参数 | 说明 | 默认值 | 必填 |
|------|------|--------|------|
| `--input` | 输入 JSON 文件路径 | - | ✅ |
| `--model-path` | 模型路径（用于加载 tokenizer） | `Qwen/Qwen2.5-7B-Instruct` | ❌ |
| `--output` | 输出分析结果文件路径 | - | ❌ |

## 输出示例

```
============================================================
Token 统计
============================================================
样本数量: 100

最小值: 1,234 tokens
最大值: 3,456 tokens
平均值: 2,345.6 tokens
中位数: 2,300.0 tokens
标准差: 456.7 tokens

百分位数:
  P25: 2,000 tokens
  P50: 2,300 tokens
  P75: 2,700 tokens
  P90: 3,000 tokens
  P95: 3,200 tokens
  P99: 3,400 tokens
============================================================
```

## 注意事项

1. **模型选择**: 建议使用与实际微调相同的模型加载 tokenizer
2. **数据格式**: 确保 JSON 文件包含 `prompt` 和 `response` 字段
3. **保存结果**: 使用 `--output` 参数保存详细的分析结果

## 示例

```bash
# 示例 1: 基础分析
python -m token_analysis.non_thinking.analyze \
    --input ../labeled_data/outline/batch_01_labeled.json

# 示例 2: 使用不同的模型
python -m token_analysis.non_thinking.analyze \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --model-path Qwen/Qwen2.5-14B-Instruct

# 示例 3: 保存结果
python -m token_analysis.non_thinking.analyze \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --output ../token_analysis/non_thinking_batch_01.json
```
