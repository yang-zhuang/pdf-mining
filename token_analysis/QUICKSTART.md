# Token 分析快速开始指南

## 5 分钟快速上手

### 第一步：准备数据

确保你有标注好的数据，格式如下：

```json
[
  {
    "id": 1,
    "prompt": "...",
    "response": "..."
  }
]
```

### 第二步：安装依赖

```bash
pip install transformers torch requests
```

### 第三步：运行分析

#### 非思考模式（推荐先试用）

```bash
cd pdf_extractor/token_analysis

python -m non_thinking.analyze \
    --input ../labeled_data/outline/batch_01_labeled.json
```

#### 思考模式（需要 vLLM）

```bash
# 1. 启动 vLLM（新终端）
vllm serve Qwen/Qwen2.5-7B-Instruct --port 8000

# 2. 运行分析
python -m thinking.analyze \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --vllm-url http://localhost:8000 \
    --limit 10
```

### 第四步：查看结果

分析完成后，会输出：

```
============================================================
Total Token 统计
============================================================
样本数量: 100
最小值: 1,234 tokens
最大值: 3,456 tokens
P99 值: 3,400 tokens

推荐配置: 4,096 tokens
============================================================
```

## 常见使用场景

### 场景 1：快速评估（非思考模式）

```bash
# 适用于：快速了解 token 使用情况
python -m non_thinking.analyze --input data.json
```

### 场景 2：精确分析（思考模式）

```bash
# 适用于：需要准确模拟实际推理过程
python -m thinking.analyze \
    --input data.json \
    --vllm-url http://localhost:8000 \
    --limit 50
```

### 场景 3：批量分析

```bash
# 分析多个批次
for i in {01..05}; do
    python -m non_thinking.analyze \
        --input ../labeled_data/outline/batch_${i}_labeled.json \
        --output ../token_analysis/batch_${i}.json
done
```

### 场景 4：对比分析

```bash
# 对比非思考和思考模式
python -m non_thinking.analyze --input data.json --output non.json
python -m thinking.analyze --input data.json --output thinking.json --limit 20
```

## 理解输出结果

### 统计指标说明

| 指标 | 说明 | 推荐用途 |
|------|------|---------|
| **P50 (中位数)** | 50% 的数据不超过此值 | 常规场景 |
| **P95** | 95% 的数据不超过此值 | 生产环境推荐 |
| **P99** | 99% 的数据不超过此值 | 保守配置 |
| **Max** | 最大值 | 资源充足时 |

### 配置建议说明

```
推荐配置（向上取整到常用值）:
  - 保守配置（覆盖 99% 数据）: 4,096 tokens
  - 完整配置（覆盖所有数据）: 8,192 tokens
```

- **保守配置**: 适用于大多数场景，性价比高
- **完整配置**: 确保所有数据不被截断，但资源消耗大

### 如何选择 max_tokens

```
实际最大值: 3,456 tokens
P99 值: 3,400 tokens

建议:
  开发环境 → 使用 P99-based (4,096)
  生产环境 → 如果资源充足，使用 Max-based (8,192)
  边缘设备 → 使用较小的配置，接受少量截断
```

## 故障排除

### 问题 1：ImportError

```
错误: No module named 'transformers'
解决: pip install transformers
```

### 问题 2：连接 vLLM 失败

```
错误: 无法连接到 vLLM 服务
解决:
  1. 检查 vLLM 是否运行: ps aux | grep vllm
  2. 检查端口: curl http://localhost:8000/health
  3. 检查防火墙
```

### 问题 3：内存不足

```
错误: CUDA out of memory
解决:
  1. 使用更小的模型
  2. 减少 --max-tokens
  3. 使用 --limit 限制数据量
```

## 下一步

1. **保存结果**: 使用 `--output` 保存详细分析
2. **对比分析**: 对比不同模型或不同批次的数据
3. **配置模型**: 根据建议配置 vLLM 或微调脚本
4. **监控生产**: 在生产环境中监控实际 token 使用

## 更多帮助

- [详细文档](README.md)
- [非思考模式说明](non_thinking/README.md)
- [思考模式说明](thinking/README.md)
