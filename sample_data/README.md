# 示例数据

本目录包含用于测试和调试的示例数据。

## 目录结构

```
sample_data/
└── ocr_results/                    # PDF OCR 处理结果示例
    └── example_paper/              # 示例论文
        └── *.json                  # OCR 结果文件
```

## OCR 结果数据格式

OCR 结果文件为 JSON 格式，包含以下字段：

```json
{
  "pages": [
    {
      "page_num": 1,
      "width": 1000,
      "height": 1500,
      "lines": [
        {
          "text": "页面文本内容",
          "bbox": [x1, y1, x2, y2],
          "confidence": 0.98
        }
      ]
    }
  ]
}
```

## 使用方法

在 `extractor/outline_extractor` 目录下运行：

```bash
# 使用示例数据生成待标注数据
python main.py --input-path ../../sample_data/ocr_results
```

## 数据来源

示例数据来自公开的学术论文，仅用于开发和测试目的。

## 添加更多示例数据

如需添加更多测试数据：

1. 将 OCR 处理后的 JSON 文件放入 `sample_data/ocr_results/` 目录
2. 保持原有的目录结构
3. 确保 JSON 文件格式符合上述规范
