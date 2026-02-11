# 思考模式 Token 分析

## 功能说明

通过 vLLM 调用思考模型，获取思考内容（thinking）和响应（response），然后统计 prompt + thinking + response 的 token 数量。

## 使用前准备

### 1. 启动 vLLM 服务

```bash
# 使用 Qwen 模型
vllm serve Qwen/Qwen2.5-7B-Instruct \
    --port 8000 \
    --max-model-len 8192

# 或使用其他思考模型
vllm serve deepseek-ai/DeepSeek-R1 \
    --port 8000 \
    --max-model-len 16384
```

### 2. 测试连接

```bash
python -c "from token_analysis.thinking.infer import test_vllm_connection; test_vllm_connection()"
```

## 使用方法

### 基础用法

```bash
python -m token_analysis.thinking.analyze \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --vllm-url http://localhost:8000
```

### 建议先用少量数据测试

```bash
python -m token_analysis.thinking.analyze \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --vllm-url http://localhost:8000 \
    --limit 10
```

### 完整参数

```bash
python -m token_analysis.thinking.analyze \
    --input INPUT_FILE \
    --vllm-url VLLM_URL \
    --model-name MODEL_NAME \
    --max-tokens MAX_TOKENS \
    --limit LIMIT \
    --output OUTPUT_FILE
```

## 参数说明

| 参数 | 说明 | 默认值 | 必填 |
|------|------|--------|------|
| `--input` | 输入 JSON 文件路径 | - | ✅ |
| `--vllm-url` | vLLM 服务地址 | `http://localhost:8000` | ❌ |
| `--model-name` | 模型名称 | `Qwen/Qwen2.5-7B-Instruct` | ❌ |
| `--max-tokens` | 推理时的最大生成 token 数 | `4096` | ❌ |
| `--limit` | 限制分析的数据数量 | 无限制 | ❌ |
| `--output` | 输出分析结果文件路径 | - | ❌ |

## 输出示例

```
[步骤 0] 测试 vLLM 连接
[成功] vLLM 服务连接正常
[测试] 发送测试请求...
[成功] 推理测试成功

[步骤 2] 调用思考模型并计算 token 数量
  进度: 1/100
    Prompt: 1234, Thinking: 567, Response: 890, Total: 2691
  ...

============================================================
Thinking Token 统计
============================================================
样本数量: 100

最小值: 200 tokens
最大值: 1,500 tokens
平均值: 650.0 tokens
...

[额外建议] 对于思考模式，建议配置:
  - Thinking 部分 max_tokens: 2,048
  - Response 部分 max_tokens: 4,096
  - 总计 max_tokens: 8,192
```

## 思考内容解析

脚本会尝试从响应中分离思考内容和最终响应：

1. **有思考标签**: 如果响应包含 ``...``，自动提取
2. **无思考标签**: 将整个响应作为 response，thinking 为空

```json
{
  "thinking": "让我分析一下这个文档的结构...",
  "response": "【当前页组确认提纲】..."
}
```

## 性能优化

### 加速分析

1. **增加并发**: 修改 `infer.py` 中的延迟时间
2. **使用 GPU**: 确保 vLLM 使用 GPU 加速
3. **限制数据**: 使用 `--limit` 先分析部分数据

### vLLM 配置优化

```bash
# 使用张量并行
vllm serve Qwen/Qwen2.5-7B-Instruct \
    --port 8000 \
    --tensor-parallel-size 2

# 增加 GPU 内存
vllm serve Qwen/Qwen2.5-7B-Instruct \
    --port 8000 \
    --gpu-memory-utilization 0.9
```

## 常见问题

### Q: vLLM 连接失败怎么办？

A: 检查以下几点：
1. vLLM 服务是否正在运行
2. 端口是否正确（默认 8000）
3. 防火墙是否阻止连接

### Q: 推理速度很慢怎么办？

A:
1. 使用 `--limit` 先测试少量数据
2. 检查 vLLM 是否使用 GPU
3. 减少 `--max-tokens` 限制
4. 考虑使用更小的模型

### Q: 思考内容为空怎么办？

A:
1. 检查模型是否支持思考模式
2. 查看原始响应内容
3. 调整 prompt 以激发模型思考

## 示例

### 示例 1: 本地 vLLM

```bash
# 启动 vLLM
vllm serve Qwen/Qwen2.5-7B-Instruct --port 8000

# 分析
python -m token_analysis.thinking.analyze \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --vllm-url http://localhost:8000
```

### 示例 2: 远程 vLLM

```bash
python -m token_analysis.thinking.analyze \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --vllm-url http://192.168.1.100:8000
```

### 示例 3: 测试模式

```bash
python -m token_analysis.thinking.analyze \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --vllm-url http://localhost:8000 \
    --limit 10 \
    --output test_result.json
```

## 与非思考模式的对比

| 特性 | 非思考模式 | 思考模式 |
|------|-----------|---------|
| 速度 | 快 | 慢（需调用模型） |
| 准确性 | 较准确 | 最准确 |
| 成本 | 无需 GPU | 需要 GPU |
| 适用场景 | 快速评估 | 精确分析 |

建议：
- **开发阶段**: 使用非思考模式快速评估
- **部署前**: 使用思考模式精确分析
