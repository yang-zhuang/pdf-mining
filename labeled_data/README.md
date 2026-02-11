# 人工标注数据 (Labeled Data)

本目录用于存放经过 Label Studio 等平台人工标注完成的数据。

## 目录结构

```
labeled_data/
├── README.md                # 本文档
├── .gitignore              # Git 忽略规则
└── outline/                # 提纲提取任务的标注结果
    ├── batch_01_labeled.json      # 第 1 批标注数据
    ├── batch_02_labeled.json      # 第 2 批标注数据
    └── ...
```

## 数据命名规范

### 文件命名格式

```
{任务名}_batch_{批次号:02d}_labeled.json
```

### 示例

- 提纲提取第 1 批：`outline_batch_01_labeled.json`
- 提纲提取第 2 批：`outline_batch_02_labeled.json`
- 分类任务第 1 批：`classification_batch_01_labeled.json`（未来）

### 与待标注数据的对应关系

| 待标注数据 (labeling_data/) | 已标注数据 (labeled_data/) |
|---------------------------|---------------------------|
| `batch_01.json` | `outline_batch_01_labeled.json` |
| `batch_02.json` | `outline_batch_02_labeled.json` |
| `outline_20260208_174448.json` | `outline_20260208_174448_labeled.json` |

## 数据格式

### 输入格式（从 labeling_data 导出）

```json
[
  {
    "prompt": "第1页候选内容：\n| 页码 | 行号 | ...",
    "response": "【当前页组确认提纲】..."
  }
]
```

### 输出格式（标注完成后）

Label Studio 导出的标准格式：

```json
[
  {
    "id": 1,
    "prompt": "第1页候选内容：\n| 页码 | 行号 | ...",
    "response": "【当前页组确认提纲】...",
    "annotator": "user1",
    "created_at": "2026-02-08T18:00:00",
    "annotation_duration": 120,
    "label_score": 5
  }
]
```

## 使用流程

### 1. 导出待标注数据

```bash
cd labeling/outline
python prepare.py --batch-mode --limit 100
# 生成：../../labeling_data/batch_01.json
```

### 2. 在 Label Studio 中标注

1. 创建新项目
2. 导入 `labeling_data/batch_01.json`
3. 配置标注界面
4. 完成人工标注
5. 导出标注结果（JSON 格式）

### 3. 保存标注结果

将 Label Studio 导出的文件保存到本目录：

```bash
# 重命名并移动
mv ~/Downloads/project_1_result.json \
   labeled_data/outline/outline_batch_01_labeled.json
```

### 4. 验证数据格式

```bash
# 检查文件格式是否正确
python -c "import json; data = json.load(open('labeled_data/outline/outline_batch_01_labeled.json')); print(f'共 {len(data)} 条标注数据')"
```

### 5. 用于模型训练

标注数据可用于：

- **微调 LLM 模型**: 训练专用的提纲提取模型
- **评估模型性能**: 对比 LLM 输出和人工标注
- **数据分析**: 分析标注质量和一致性
- **改进算法**: 根据标注结果优化提取算法

## 数据质量要求

### 标注规范

1. **完整性**: 每条数据都必须标注
2. **准确性**: 标注内容必须准确反映真实提纲结构
3. **一致性**: 相同类型的提纲使用相同的标注格式
4. **可追溯**: 保留原始 prompt 和 LLM 的 response

### 质量检查

```python
# 检查标注数据质量
def check_labeled_data(json_file):
    """检查标注数据的完整性和格式"""
    import json

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 检查必填字段
    required_fields = ['id', 'prompt', 'response', 'annotator']
    for item in data:
        for field in required_fields:
            if field not in item:
                print(f"⚠️ 缺少字段: {field} (id={item.get('id')})")

    print(f"✅ 共 {len(data)} 条标注数据")
    return data
```

## 数据管理

### 版本控制

建议使用 Git 管理标注数据，但注意：

```gitignore
# .gitignore
# 忽略临时文件
*.tmp
*.bak

# 但保留标注数据
!outline/*.json
```

### 备份

定期备份标注数据：

```bash
# 创建备份
tar -czf labeled_data_backup_$(date +%Y%m%d).tar.gz labeled_data/

# 或使用 rsync
rsync -av labeled_data/ /backup/labeled_data/
```

### 数据统计

```bash
# 统计各批次的标注数据量
find labeled_data/outline -name "*_labeled.json" -exec sh -c 'echo "{}: $(python -c "import json; print(len(json.load(open(\"$1\"))))" "")"' _ {} \;
```

## 进度跟踪

建议创建一个进度跟踪文件：

```markdown
# 标注进度 (PROGRESS.md)

## 提纲提取任务

| 批次 | 文件名 | 数据量 | 标注人 | 完成时间 | 状态 |
|-----|--------|-------|-------|---------|-----|
| 01 | outline_batch_01_labeled.json | 100 | 张三 | 2026-02-08 | ✅ 完成 |
| 02 | outline_batch_02_labeled.json | 100 | 李四 | 2026-02-09 | 🔄 进行中 |
| 03 | outline_batch_03_labeled.json | 100 | - | - | ⏳ 待开始 |

**总计**: 100/300 (33%)
```

## 常见问题

### Q: 标注数据可以直接用于训练吗？

A: 需要转换为训练格式。可以参考 `labeling/outline/convert_to_training.py` 脚本。

### Q: 如何处理标注错误？

A:
1. 在 Label Studio 中重新标注
2. 重新导出
3. 覆盖原文件（或创建新版本）

### Q: 标注数据需要加密吗？

A: 如果数据敏感，建议：
- 使用 Git LFS 管理大文件
- 加密存储（如 GPG）
- 访问控制（限制谁能访问）

## 相关文档

- [待标注数据准备](../labeling/README.md)
- [提纲提取任务说明](../labeling/outline/README.md)
- [Label Studio 使用指南](https://labelstud.io/guide/)

---

**最后更新**: 2026-02-08
**维护者**: 数据标注团队
