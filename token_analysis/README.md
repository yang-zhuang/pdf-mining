# Token 分析模块

用于分析微调模型的 token 使用情况，帮助确定合适的 `max_token` 配置。

## 功能说明

### 1. 非思考模式分析
- **适用场景**: 直接使用 prompt → response 的微调数据
- **分析方法**: 直接使用 tokenizer 计算 prompt + response 的 token 数量
- **优点**: 速度快，无需调用模型
- **使用**: `python -m token_analysis.non_thinking.analyze`

### 2. 思考模式分析
- **适用场景**: 使用 prompt → thinking → response 的微调数据
- **分析方法**: 通过 vLLM 调用思考模型，获取思考内容后统计 token
- **优点**: 更准确地反映思考模式的实际 token 使用
- **缺点**: 需要调用模型，速度较慢
- **使用**: `python -m token_analysis.thinking.analyze`

## 目录结构

```
token_analysis/
├── __init__.py              # 模块入口
├── utils.py                 # 共享工具（tokenizer、统计等）
├── README.md                # 本文档
└── (子模块)
    ├── non_thinking/        # 非思考模式分析
    │   ├── __init__.py
    │   ├── analyze.py       # 分析脚本
    │   └── README.md        # 详细说明
    └── thinking/            # 思考模式分析
        ├── __init__.py
        ├── analyze.py       # 分析脚本
        ├── infer.py         # vLLM 推理客户端
        └── README.md        # 详细说明
```

## 快速开始

### 安装依赖

```bash
pip install transformers torch requests
```

### 非思考模式分析

```bash
# 基础使用
cd pdf_extractor/token_analysis
python -m non_thinking.analyze --input ../labeled_data/outline/batch_01_labeled.json

# 指定模型
python -m non_thinking.analyze \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --model-path Qwen/Qwen2.5-14B-Instruct

# 保存结果
python -m non_thinking.analyze \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --output ../token_analysis/non_thinking_batch_01.json
```

### 思考模式分析

```bash
# 首先启动 vLLM 服务
# vllm serve Qwen/Qwen2.5-7B-Instruct --port 8000

# 测试连接（可选）
python -c "from token_analysis.thinking.infer import test_vllm_connection; test_vllm_connection()"

# 分析（先测试少量数据）
python -m thinking.analyze \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --vllm-url http://localhost:8000 \
    --limit 10

# 完整分析
python -m thinking.analyze \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --vllm-url http://localhost:8000 \
    --output ../token_analysis/thinking_batch_01.json
```

## 输出说明

### 统计信息

分析后会输出以下统计指标：

- **样本数量**: 数据总量
- **最小值/最大值**: token 数量的范围
- **平均值**: 平均 token 数量
- **中位数**: 中位数 token 数量
- **标准差**: token 数量的离散程度
- **百分位数**: P25, P50, P75, P90, P95, P99

### 配置建议

基于统计数据提供以下建议：

1. **保守配置**（覆盖 99% 数据）
   - 基于 P99 值 + 20% 安全余量
   - 向上取整到常用值（2048, 4096, 8192, ...）

2. **完整配置**（覆盖所有数据）
   - 基于最大值 + 20% 安全余量
   - 向上取整到常用值

### 示例输出

```
============================================================
Max Tokens 配置建议
============================================================

数据统计:
  - 实际最大值: 3,456 tokens
  - P99 值: 2,890 tokens

建议配置（已预留 20% 安全余量）:
  - 基于 P99: 3,468 tokens
  - 基于 Max: 4,147 tokens

推荐配置（向上取整到常用值）:
  - 保守配置（覆盖 99% 数据）: 4,096 tokens
  - 完整配置（覆盖所有数据）: 8,192 tokens

使用示例:
  vLLM: --max-model-len 4096
  Transformer: max_tokens=4096
============================================================
```

## 数据格式要求

输入 JSON 文件应为数组格式，每条数据包含 `prompt` 和 `response` 字段：

```json
[
  {
    "id": 1,
    "prompt": "第1页候选内容：...",
    "response": "【当前页组确认提纲】..."
  },
  {
    "id": 2,
    "prompt": "第2页候选内容：...",
    "response": "【当前页组确认提纲】..."
  }
]
```

## 常见问题

### Q: 非思考模式和思考模式应该选哪个？

A:
- **非思考模式**: 如果你的微调数据只有 prompt 和 response，使用此模式
- **思考模式**: 如果你的模型会生成思考过程（如 DeepSeek-R1），使用此模式

### Q: 为什么建议预留 20% 的安全余量？

A:
1. 训练数据可能不能完全代表所有实际场景
2. 模型生成的长度可能有波动
3. 避免因 max_tokens 不足而截断

### Q: 思考模式分析很慢怎么办？

A:
1. 使用 `--limit` 参数先分析部分数据
2. 调整 vLLM 的配置（如增加 GPU 数量）
3. 考虑使用非思考模式作为参考

### Q: 如何选择合适的 max_tokens？

A:
1. **开发测试阶段**: 使用保守配置（P99-based）
2. **生产环境**: 如果资源充足，使用完整配置（max-based）
3. **边缘设备**: 使用更小的配置，接受少量截断

### Q: 分析结果可以保存吗？

A: 可以，使用 `--output` 参数保存详细的 JSON 结果，包含：
- 每条数据的详细 token 统计
- 各种统计指标
- 配置建议

## 高级用法

### 批量分析

```bash
# 分析多个批次
for i in {01..05}; do
    python -m non_thinking.analyze \
        --input ../labeled_data/outline/batch_${i}_labeled.json \
        --output ../token_analysis/non_thinking_batch_${i}.json
done
```

### 对比分析

```bash
# 分析同一批数据的非思考和思考模式
python -m non_thinking.analyze --input batch_01.json --output non_thinking.json
python -m thinking.analyze --input batch_01.json --output thinking.json

# 对比结果
python -c "
import json
with open('non_thinking.json') as f1, open('thinking.json') as f2:
    r1 = json.load(f1)['statistics']['total']
    r2 = json.load(f2)['statistics']['total']
    print('非思考模式平均:', r1['mean'])
    print('思考模式平均:', r2['mean'])
    print('增长比例:', (r2['mean'] - r1['mean']) / r1['mean'] * 100, '%')
"
```

## 相关文档

- [非思考模式说明](non_thinking/README.md)
- [思考模式说明](thinking/README.md)
- [vLLM 文档](https://docs.vllm.ai/)

---

**最后更新**: 2026-02-08
**维护者**: PDF 提取团队
