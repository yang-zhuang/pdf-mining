# 从日志数据构建训练数据

## 功能说明

直接从 LLM 调用日志中提取成功的 prompt 和 response 作为训练数据。
适用于使用顶尖模型生成的日志数据，无需人工标注。

## 使用方法

### 基础用法

```bash
python -m training_data_builder.from_logs.extract \
    --log-dir ../outline_extractor/logs/llm_calls \
    --format alpaca
```

### 完整参数

```bash
python -m training_data_builder.from_logs.extract \
    --log-dir LOG_DIR \
    --format FORMAT \
    --output OUTPUT_FILE \
    --limit 10000 \
    --deduplicate \
    --min-length 100 \
    --max-length 10000 \
    --split-ratio 0.8,0.1,0.1 \
    --shuffle \
    --seed 42
```

## 参数说明

| 参数 | 说明 | 默认值 | 必填 |
|------|------|--------|------|
| `--log-dir` | 日志目录路径 | - | ✅ |
| `--format` | 目标训练格式 | `alpaca` | ❌ |
| `--output` | 输出文件路径 | 自动生成 | ❌ |
| `--limit` | 限制提取的数据数量 | 无限制 | ❌ |
| `--deduplicate` | 是否去重 | True | ❌ |
| `--dedup-field` | 去重字段 | `prompt` | ❌ |
| `--min-length` | 响应最小长度 | 无限制 | ❌ |
| `--max-length` | 响应最大长度 | 无限制 | ❌ |
| `--split-ratio` | 数据集拆分比例 | 不拆分 | ❌ |
| `--shuffle` | 是否打乱数据 | True | ❌ |
| `--seed` | 随机种子 | 42 | ❌ |

## 数据提取逻辑

只提取满足以下条件的日志记录：

1. ✅ **成功记录**: `success = true`
2. ✅ **有 response 字段**
3. ✅ **有 answer 内容**
4. ✅ **有 prompt 内容**（优先使用原始 prompt，回退到 current_batch_content）

过滤掉的记录：
- ❌ 失败的调用（`success = false`）
- ❌ 缺少 response 或 answer 的记录
- ❌ 缺少 prompt 的记录

## 工作流程

1. **读取日志**: 读取所有 .jsonl 日志文件
2. **提取数据**: 提取 prompt 和 response
3. **去重**: 基于指定字段去重（默认 prompt）
4. **过滤数据**: 根据长度过滤（可选）
5. **转换格式**: 转换为目标训练格式
6. **验证数据**: 检查数据质量
7. **拆分数据集**: 拆分为 train/val/test（可选）
8. **保存数据**: 保存到文件

## 使用示例

### 示例 1: 提取所有数据

```bash
python -m training_data_builder.from_logs.extract \
    --log-dir ../outline_extractor/logs/llm_calls \
    --format alpaca \
    --output training_data/alpaca_all_logs.json
```

### 示例 2: 限制数据量

```bash
python -m training_data_builder.from_logs.extract \
    --log-dir ../outline_extractor/logs/llm_calls \
    --format alpaca \
    --limit 1000 \
    --output training_data/alpaca_1k.json
```

### 示例 3: 去重和过滤

```bash
python -m training_data_builder.from_logs.extract \
    --log-dir ../outline_extractor/logs/llm_calls \
    --format alpaca \
    --deduplicate \
    --min-length 100 \
    --max-length 8000 \
    --output training_data/alpaca_filtered.json
```

### 示例 4: 拆分数据集

```bash
python -m training_data_builder.from_logs.extract \
    --log-dir ../outline_extractor/logs/llm_calls \
    --format alpaca \
    --split-ratio 0.8,0.1,0.1 \
    --output training_data/alpaca_from_logs.json
```

## 与标注数据的对比

| 特性 | 从标注数据 | 从日志数据 |
|------|-----------|-----------|
| 数据质量 | 高（人工验证） | 中等（模型生成） |
| 数据量 | 500-5000 条 | 1000-100000 条 |
| 成本 | 高（需人工标注） | 低（自动提取） |
| 适用场景 | 最终微调、提高准确率 | 蒸馏、增量训练、预热 |
| 处理速度 | 慢 | 快 |

## 推荐使用策略

### 策略 1: 两阶段训练

```bash
# 阶段 1: 使用日志数据预热（大数据量）
python -m from_logs.extract \
    --log-dir ../outline_extractor/logs/llm_calls \
    --format alpaca \
    --limit 10000 \
    --output training_data/alpaca_pretrain.json

# 阶段 2: 使用标注数据精调（高质量）
python -m from_labeled.convert \
    --input ../labeled_data/outline/all_labeled.json \
    --format alpaca \
    --output training_data/alpaca_finetune.json
```

### 策略 2: 混合数据

```bash
# 提取日志数据
python -m from_logs.extract \
    --log-dir ../outline_extractor/logs/llm_calls \
    --format alpaca \
    --limit 5000 \
    --output alpaca_logs.json

# 转换标注数据
python -m from_labeled.convert \
    --input ../labeled_data/outline/batch_01_labeled.json \
    --format alpaca \
    --output alpaca_labeled.json

# 合并两个数据集（手动）
cat alpaca_logs.json >> alpaca_all.json
cat alpaca_labeled.json >> alpaca_all.json

# 使用合并的数据进行微调
```

## 优化建议

### 1. 去重
```bash
--deduplicate --dedup-field prompt
```
避免重复的 prompt 相同，导致模型过拟合。

### 2. 长度过滤
```bash
--min-length 100 --max-length 8000
```
过滤掉过短或过长的响应：
- 过短：可能信息不足
- 过长：可能包含错误或冗余信息

### 3. 数据量控制
```bash
--limit 5000
```
根据计算资源和时间选择合适的数据量。

## 常见问题

### Q: 提取的数据量为什么比日志记录少？

A: 因为只提取成功的记录，并且会过滤掉缺少 prompt 或 response 的记录。

### Q: 如何提高数据质量？

A:
1. 使用 `--min-length` 过滤过短的响应
2. 使用 `--max-length` 过滤过长的响应
3. 使用 `--deduplicate` 去除重复数据
4. 人工检查部分数据质量

### Q: 应该提取多少数据？

A:
- **预热/蒸馏**: 10000-100000 条
- **增量训练**: 1000-10000 条
- **最终微调**: 使用标注数据

### Q: 可以使用多次提取的数据吗？

A: 可以，但建议：
- 使用不同的 `--seed` 打乱数据
- 使用 `--deduplicate` 避免重复
- 定期更新数据集
