# 提纲提取标注数据准备

## 任务说明

本模块用于从 LLM 调用日志中提取提纲提取任务的标注数据，用于在 Label Studio 等平台上进行人工标注。

### 数据格式

每条标注数据包含两个字段：

```json
{
  "prompt": "第1页候选内容：\n| 页码 | 行号 | 内容预览（前500字符） |\n|------|------|---------------------|\n| 1 | 1 | (Dis)improved?! How Simplified Language... |\n...",
  "response": "【当前页组确认提纲】（第1-12页）\n\n1. [一级] Abstract (1:9)\n2. [一级] Introduction (1:15)\n..."
}
```

- **prompt**: OCR 提取的候选提纲内容（来自日志的 `current_batch_content` 字段）
- **response**: LLM 提取的提纲结果（来自日志的 `response.answer` 字段）

## 使用方法

### 基础使用

```bash
# 导出所有提纲标注数据
python -m labeling.outline.prepare
```

输出文件：`labeling_data/outline_labeling.json`

### 指定输出文件

```bash
python -m labeling.outline.prepare --output data/my_outline_labels.json
```

### 分批标注

如果数据量很大，可以分批导出进行标注：

```bash
# 第一批：导出 100 条
python -m labeling.outline.prepare --limit 100 --output data/batch_01.json

# 第二批：再导出 100 条（自动跳过已导出的）
python -m labeling.outline.prepare --limit 100 --output data/batch_02.json
```

### 过滤特定文件

只导出某个 PDF 文件的处理记录：

```bash
python -m labeling.outline.prepare --file-key 0fe25f94c682ec25
```

### 强制重新导出

忽略断点续传，重新导出所有记录：

```bash
python -m labeling.outline.prepare --force
```

### 查看断点续传状态

```bash
cat .outline_labeling_state.json
```

输出示例：
```json
{
  "exported_record_hashes": ["abc123...", "def456...", ...],
  "last_export_time": "2026-02-08T17:30:00",
  "total_exported": 100
}
```

## 断点续传机制

本工具使用状态文件（`.outline_labeling_state.json`）来记录已导出的记录：

- **记录标识**: 使用 `timestamp + file_key + content` 的 MD5 哈希值
- **自动跳过**: 已导出的记录会自动跳过
- **增量导出**: 每次运行只导出新增的记录
- **状态持久化**: 导出后自动更新状态文件

### 使用场景

1. **分批标注**: 每次导出少量数据，标注完成后再导出下一批
2. **增量更新**: 当日志文件有新增记录时，只导出新增部分
3. **避免重复**: 防止同一批数据被多次导出

## 导出流程

```
日志文件（.jsonl）
    ↓
读取所有记录
    ↓
过滤（成功 + 文件 + 断点续传）
    ↓
提取 prompt 和 response
    ↓
保存到 JSON 文件
    ↓
更新状态文件
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--log-dir` | 日志目录路径 | `logs/llm_calls` |
| `--output` | 输出 JSON 文件路径 | `labeling_data/outline_labeling.json` |
| `--limit` | 限制导出的记录数量 | 无限制 |
| `--file-key` | 只导出特定文件的处理记录 | 全部文件 |
| `--force` | 强制重新导出所有记录 | 否 |
| `--help` | 显示帮助信息 | - |

## 数据质量

### 包含的数据

- ✅ **成功记录**: 只包含 LLM 调用成功的记录
- ✅ **完整字段**: prompt 和 response 都存在
- ✅ **有效内容**: 非空且有意义的内容

### 排除的数据

- ❌ **失败记录**: LLM 调用失败的记录
- ❌ **缺少字段**: prompt 或 response 不存在的记录
- ❌ **已导出记录**: 断点续传机制自动跳过

## 标注建议

### 在 Label Studio 中使用

1. **创建项目**: 新建一个文本标注项目
2. **导入数据**: 上传导出的 JSON 文件
3. **配置标注界面**:
   - 输入: 显示 `prompt`（候选提纲）
   - 输出: 修正 `response`（LLM 提取的提纲）
4. **标注指南**: 参考提纲提取标准（如层级、格式等）

### 标注重点

1. **层级准确性**: 检查提纲的层级关系是否正确
2. **格式规范性**: 统一编号格式（如 "1."、"1.1"）
3. **内容完整性**: 确保没有遗漏重要的提纲
4. **错误修正**: 修正 LLM 的错误识别和提取

## 后续使用

标注完成后，可以使用标注数据：

1. **微调模型**: 用于训练提纲提取模型
2. **评估质量**: 对比 LLM 输出和人工标注的差异
3. **改进策略**: 根据标注结果优化提取算法

## 相关文件

- `labeling/utils.py`: 共享工具类
- `labeling/outline/prepare.py`: 本脚本
- `.outline_labeling_state.json`: 断点续传状态文件

## 扩展其他标注任务

如需添加其他类型的标注任务（如分类、摘要等），参考本模块的结构：

```
labeling/
├── utils.py                  # 共享工具
├── outline/                  # 提纲提取（当前）
├── classification/           # 分类任务（未来）
└── summarization/            # 摘要任务（未来）
```

## 技术支持

如有问题，请检查：

1. 日志目录是否正确
2. 日志文件是否为 .jsonl 格式
3. 状态文件是否损坏（可删除后重新运行）
4. Python 路径是否正确
