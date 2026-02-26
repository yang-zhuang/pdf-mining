# 提纲提取评估脚本

用于评估大模型在提纲提取任务上的性能，计算准确率、召回率、F1 值。

## 功能特性

- 支持自动扫描 `training_data/outline/three_column` 目录下所有以 `eval` 开头的评估数据文件
- 使用 VLLM API 进行模型推理
- 自动提取 Qwen3 模型的 `<thinking>` 思考内容
- 计算宏平均（Macro Average）和微平均（Micro Average）指标
- 输出详细的评估结果和汇总统计

## 安装依赖

```bash
pip install -r requirements.txt
```

## 环境配置

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置 VLLM 服务地址：

```env
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_MODEL_NAME=Qwen3-4B-Thinking-2507
VLLM_API_KEY=empty
```

## 使用方法

### 基本使用

```bash
python eval_outline.py
```

### 指定参数

```bash
python eval_outline.py \
  --base_url http://localhost:8000/v1 \
  --model_name Qwen3-4B-Thinking-2507 \
  --data_dir training_data/outline/three_column
```

### 测试模式（只评估前 N 个样本）

```bash
python eval_outline.py --limit 5
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--data_dir` | 评估数据目录路径 | `training_data/outline/three_column` |
| `--base_url` | VLLM API 基础 URL | 从环境变量 `VLLM_BASE_URL` 读取 |
| `--model_name` | 模型名称 | 从环境变量 `VLLM_MODEL_NAME` 读取 |
| `--api_key` | API 密钥 | 从环境变量 `VLLM_API_KEY` 读取 |
| `--max_tokens` | 最大生成 token 数 | `8192` |
| `--temperature` | 温度参数 | `0.1` |
| `--output_dir` | 结果输出目录 | `training/outline/eval/results` |
| `--limit` | 限制评估样本数量（用于测试） | `None` |

## 评估指标

### 宏平均 (Macro Average)

- 对每个样本分别计算 Precision、Recall、F1，然后取平均
- 反映模型在不同样本上的平均表现

### 微平均 (Micro Average)

- 基于 True Positive (TP)、False Positive (FP)、False Negative (FN) 的总数计算
- 反映模型的整体表现，受样本大小影响较大

### 指标定义

- **Precision (准确率)**: `TP / (TP + FP)` - 预测正确的提纲数占总预测数的比例
- **Recall (召回率)**: `TP / (TP + FN)` - 预测正确的提纲数占标准答案数的比例
- **F1 Score**: `2 * P * R / (P + R)` - Precision 和 Recall 的调和平均

## 输出结果

评估完成后，会在 `results` 目录下生成两个文件：

1. `metrics_YYYYMMDD_HHMMSS.json` - 汇总指标
2. `details_YYYYMMDD_HHMMSS.jsonl` - 每个样本的详细结果

### 输出示例

```
============================================================
评估结果汇总
============================================================

宏平均 (Macro Average):
  准确率 (Precision): 0.8234 (82.34%)
  召回率 (Recall):    0.7856 (78.56%)
  F1 分数 (F1 Score):  0.8041 (80.41%)

微平均 (Micro Average):
  准确率 (Precision): 0.8521 (85.21%)
  召回率 (Recall):    0.8112 (81.12%)
  F1 分数 (F1 Score):  0.8312 (83.12%)

详细统计:
  样本总数:         10
  预测总数:         152
  标准答案总数:     145
  正确预测 (TP):    123
  错误预测 (FP):    29
  漏掉预测 (FN):    22
  平均推理时间:     3.45 秒
  总推理时间:       34.50 秒
============================================================
```

## 注意事项

1. 确保已启动 VLLM 服务并能够正常访问
2. 评估数据文件格式为 JSONL，每行包含 `prompt` 和 `answer` 字段
3. 评估过程可能需要较长时间，建议先使用 `--limit` 参数测试
4. 模型输出会被预处理，自动移除 `<thinking>` 标签内的思考内容