# 提纲提取标注数据

本目录存放提纲提取任务的人工标注结果。

## 数据来源

从 `labeling_data/` 导出 → Label Studio 标注 → 保存到本目录

## 文件列表

| 文件名 | 数据量 | 标注时间 | 状态 | 说明 |
|--------|-------|---------|------|------|
| outline_batch_01_labeled.json | - | - | ⏳ 待添加 | 第 1 批标注数据 |
| outline_batch_02_labeled.json | - | - | ⏳ 待添加 | 第 2 批标注数据 |

## 数据格式

### 输入格式（待标注）

从 `labeling_data/` 导出：

```json
[
  {
    "prompt": "第1页候选内容：\n...",
    "response": "LLM 提取的提纲..."
  }
]
```

### 输出格式（已标注）

Label Studio 标注后的格式：

```json
[
  {
    "id": 1,
    "prompt": "第1页候选内容：\n...",
    "response": "人工修正后的提纲...",
    "original_response": "LLM 原始输出...",
    "annotator": "标注人姓名",
    "created_at": "2026-02-08T18:00:00",
    "updated_at": "2026-02-08T18:30:00",
    "annotation_duration": 1800,
    "changes": 5,
    "label_score": 5
  }
]
```

## 标注指南

### 提纲层级标准

1. **一级提纲**（如：1.、一、Chapter 1）
   - 文档的主要结构
   - 如：摘要、引言、方法、结论

2. **二级提纲**（如：1.1、（一）、§1）
   - 一级提纲的子部分
   - 如：2.1 Related work

3. **三级提纲**（如：1.1.1、（一）、1.）
   - 二级提纲的子部分
   - 如：3.1.1 Datasets

### 格式要求

1. **层级清晰**: 使用缩进表示层级关系
2. **编号规范**: 保持原有编号格式
3. **内容完整**: 包含完整的提纲标题
4. **位置标注**: 标注页码和行号

### 质量标准

- ✅ **准确性**: 提纲层级正确，无遗漏
- ✅ **完整性**: 包含所有重要提纲
- ✅ **一致性**: 格式统一，风格一致
- ✅ **可追溯**: 保留原始位置信息

## 标注流程

### 1. 准备阶段

```bash
# 导出待标注数据
cd ../labeling/outline
python prepare.py --batch-mode --limit 100

# 生成：../../labeling_data/batch_01.json
```

### 2. 标注阶段

1. 打开 Label Studio
2. 导入 `labeling_data/batch_01.json`
3. 配置标注界面：
   - 输入框：显示 `prompt`（OCR 候选）
   - 输出框：编辑 `response`（提纲结果）
4. 开始标注

### 3. 导出阶段

1. 在 Label Studio 中完成标注
2. 导出为 JSON 格式
3. 保存到本目录：

```bash
# 重命名并保存
mv ~/Downloads/project_result.json \
   ../labeled_data/outline/outline_batch_01_labeled.json
```

### 4. 验证阶段

```python
# 验证标注数据
import json

with open('outline_batch_01_labeled.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"数据量: {len(data)}")
print(f"字段: {list(data[0].keys())}")

# 检查必填字段
required = ['id', 'prompt', 'response', 'annotator']
for item in data:
    for field in required:
        if field not in item:
            print(f"⚠️ 缺少字段: id={item.get('id')}, field={field}")
```

## 使用标注数据

### 1. 微调模型

```python
# 转换为训练格式
from labeling.outline.convert_to_training import convert_to_training_format

# 转换
train_data = convert_to_training_format(
    'labeled_data/outline/outline_batch_01_labeled.json',
    format='alpaca'  # 或 'instruction', 'sharegpt'
)

# 保存
with open('training_data/outline_finetune.json', 'w') as f:
    json.dump(train_data, f, ensure_ascii=False, indent=2)
```

### 2. 评估模型

```python
# 评估 LLM 提取结果
from labeling.outline.evaluate import evaluate_extraction

# 加载标注数据
with open('outline_batch_01_labeled.json', 'r') as f:
    labeled_data = json.load(f)

# 评估
metrics = evaluate_extraction(labeled_data, llm_predictions)
print(f"准确率: {metrics['accuracy']}")
print(f"F1 分数: {metrics['f1']}")
```

### 3. 数据分析

```python
# 分析标注质量
from labeling.outline.analyze import analyze_annotations

# 分析
stats = analyze_annotations('outline_batch_01_labeled.json')
print(f"平均标注时间: {stats['avg_duration']} 秒")
print(f"平均修改次数: {stats['avg_changes']}")
print(f"标注一致性: {stats['consistency']}")
```

## 质量控制

### 自动检查

```bash
# 运行质量检查脚本
python ../labeling/outline/check_quality.py \
    --input outline_batch_01_labeled.json \
    --report quality_report.html
```

### 人工审核

1. 抽查 10% 的标注数据
2. 检查层级关系是否正确
3. 检查格式是否统一
4. 记录问题并反馈给标注人

### 一致性检查

- 双人标注：同一批数据由两人独立标注
- 一致性计算：使用 Cohen's Kappa 系数
- 争议解决：第三人仲裁

## 进度跟踪

### 统计信息

```bash
# 查看已完成的批次数
ls -1 outline_batch_*_labeled.json | wc -l

# 查看总标注数量
find . -name "*_labeled.json" -exec sh -c 'echo $(cat "$1" | python -c "import json,sys; print(len(json.load(sys.stdin)))")' _ {} \; | awk '{sum+=$1} END {print sum}'
```

### 更新 README

标注完成后，更新本目录的文件列表表格。

## 常见问题

### Q: 如何处理 LLM 完全错误的输出？

A:
1. 人工重新标注正确的提纲
2. 在 `changes` 字段记录改动次数
3. 可选：在 `notes` 字段添加说明

### Q: 标注时间太长怎么办？

A:
- 熟悉提纲层级标准
- 使用快捷键提高效率
- 分批次标注，避免疲劳

### Q: 如何处理模糊不清的提纲？

A:
- 参考上下文判断
- 标注在 `notes` 字段
- 与团队讨论统一标准

---

**负责人**: 提纲提取团队
**最后更新**: 2026-02-08
