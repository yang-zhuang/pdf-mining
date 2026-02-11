# PDF Extractor

基于 LLM 和强化学习的 PDF 内容提取工具集。

## 项目简介

本项目旨在提供一套完整的 PDF 文档内容提取解决方案，支持从 OCR 处理后的 PDF 文档中自动提取多种类型的结构化内容。项目采用模块化设计，每种提取功能（如提纲、表格、图片等）都有独立的处理流程和训练管道。

### 已实现功能

**✅ PDF 提纲提取**
- 多层次提纲检测（正则表达式、# 前缀、长度范围）
- 支持 ModelScope 和 vLLM 两种 LLM 推理模式
- 基于 GRPO 强化学习的模型训练流程
- 断点续传支持，避免重复调用 LLM
- 兼容 Windows 长路径（>260 字符）

### 计划中功能

- ⏳ PDF 关键信息抽取

## 项目结构

```
pdf_mining/
├── docs/                          # 项目文档
│   └── outline-training-workflow.md  # 各功能模块的详细文档
├── sample_data/                    # 示例数据（用于测试）
│   ├── README.md
│   └── ocr_results/              # OCR 处理结果示例
├── extractor/                     # 提取器模块
│   └── outline_extractor/        # 提纲提取器
├── labeling/                      # 标注数据准备工具
│   └── outline/                  # 提纲标注转换
├── labeled_data/                  # 人工标注数据存储
│   └── outline/                  # 提纲标注数据
├── labeling_data/                 # 待标注数据存储
│   └── outline/                  # 提纲待标注数据
├── training_data_builder/         # 训练数据构建工具
│   └── outline/                  # 提纲训练数据
├── training_data/                 # 训练数据存储
│   └── outline/                  # 提纲训练数据
├── grpo_training/                 # GRPO 训练脚本
│   └── outline/                  # 提纲模型训练
└── token_analysis/                # Token 使用分析
    └── outline/                  # 提纲 Token 分析
```

**设计说明**：项目采用模块化设计，每个提取功能（如 `outline`）都有独立的子目录，包含各自的提取器、标注工具、训练脚本等。

## 快速开始

### 环境要求

- Python 3.8+
- PyTorch
- TRL 库
- Label Studio（用于标注）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

1. **复制环境变量模板**

```bash
cp .env.example .env
```

2. **编辑 `.env` 文件，填入你的 API 密钥**

```env
# ModelScope API 配置
MODELSCOPE_API_KEY=your_api_key_here
MODELSCOPE_BASE_URL=https://api-inference.modelscope.cn/v1

# vLLM 配置（如果使用本地 vLLM）
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_API_KEY=empty

# 默认 LLM 模式（modelscope 或 vllm）
DEFAULT_LLM_MODE=modelscope

# 默认模型配置
DEFAULT_PRIMARY_MODEL=ZhipuAI/GLM-4.7-Flash
```

**获取 API Key**：
- ModelScope: 访问 https://modelscope.cn/my/myaccesstoken

**⚠️ 安全提醒**：
- `.env` 文件包含敏感信息，已在 `.gitignore` 中排除
- 切勿将 `.env` 文件提交到版本控制系统
- 团队协作时，各自配置自己的 `.env` 文件

## 功能模块

### PDF 提纲提取 (Outline Extraction)

PDF 提纲提取是本项目的第一个功能模块，提供从 OCR 结果到最终训练模型的完整流程。

#### 快速测试

```bash
# 1. 生成待标注数据（使用示例数据）
cd extractor/outline_extractor
python main.py

# 2. 转换为标注格式
cd ../../labeling/outline
python prepare.py --log-dir ../../extractor/outline_extractor/logs/llm_calls

# 3. 在 Label Studio 中人工标注（手动操作）
# 4. 转换为训练数据
python ../../training_data_builder/outline/from_labeled/convert.py

# 5. 开始 GRPO 训练
cd ../../grpo_training/outline
sh grpo.sh
```

#### 详细文档

**[PDF 提纲提取 - 完整训练流程](docs/outline-training-workflow.md)**

该文档包含：
- 5 个详细步骤说明
- 每步的命令和参数解释
- Label Studio 配置指南
- GRPO 训练配置
- 常见问题解答
- 最佳实践建议

#### 主要特性

- **多层次检测**：正则表达式、# 前缀、长度范围
- **LLM 增强**：支持 ModelScope 和 vLLM 推理
- **强化学习训练**：基于 GRPO 算法的模型优化
- **断点续传**：避免重复调用 LLM，节省成本
- **Windows 长路径支持**：兼容 >260 字符路径

#### 使用示例

```bash
cd extractor/outline_extractor

# 使用示例数据
python main.py

# 使用自定义数据
python main.py --input-path /path/to/ocr_results

# 处理特定文件范围
python main.py --start 0 --end 100

# 强制重新处理
python main.py --force

# 自定义检测参数
python main.py --min-length 2 --max-length 50 --disable-regex
```

## 文档索引

### 提纲提取模块
- **[完整训练流程](docs/outline-training-workflow.md)** - PDF 提纲提取的 5 步训练指南
- **[示例数据说明](sample_data/README.md)** - 示例数据格式和使用方法
- **[标注数据准备](labeling/outline/README.md)** - 将日志转换为标注格式
- **[训练数据构建](training_data_builder/outline/from_labeled/README.md)** - 将标注结果转换为训练数据

## 技术栈

- **LLM 推理**: ModelScope, vLLM
- **训练框架**: TRL (Transformers Reinforcement Learning)
- **强化学习**: GRPO (Group Relative Policy Optimization)
- **标注平台**: Label Studio
- **OCR**: PaddleOCR

## 开发指南

### 添加新的提取功能

项目采用模块化设计，添加新的提取功能（如表格提取）可按以下步骤：

1. **创建提取器**：在 `extractor/` 下创建新的提取器模块
2. **标注工具**：在 `labeling/` 下创建对应的标注转换工具
3. **训练数据构建**：在 `training_data_builder/` 下创建数据转换脚本
4. **训练脚本**：在 `grpo_training/` 下创建训练脚本
5. **文档**：在 `docs/` 下添加对应的训练流程文档

详细的模块开发指南即将推出...

## 最佳实践

1. **数据质量优先**: 从小规模高质量数据开始，逐步扩展
2. **迭代训练**: 每轮训练后评估效果，补充错误样本
3. **版本管理**: 为每轮数据和模型打版本标签
4. **断点续传**: 利用日志功能避免重复调用 LLM

## 常见问题

**Q: 项目支持哪些 OCR 格式？**

A: 支持包含 `pages` 字段的 JSON 格式，每页包含 `lines` 数组，每个 line 包含 `text` 和 `bbox`。详见 [示例数据说明](sample_data/README.md)。

**Q: 如何使用自己的数据？**

A: 将 OCR 处理后的 JSON 文件放到指定目录，然后使用 `--input-path` 参数指定路径。

**Q: 如何调整训练参数？**

A: 编辑对应功能模块的训练脚本（如 `grpo_training/outline/grpo.sh`）。

**Q: 需要多少标注数据？**

A: 建议从小规模开始（100-500 条高质量标注），迭代训练和扩充。

更多问题请参阅各功能模块的详细文档。

## 贡献指南

欢迎提交 Issue 和 Pull Request！

### 贡献方向

- 添加新的提取功能（表格、图片、公式等）
- 优化现有提取算法
- 改进训练流程
- 完善文档
- 报告 Bug 和提出建议

## 许可证

本项目仅供学习和研究使用。

---

**最后更新**: 2025-02-11
