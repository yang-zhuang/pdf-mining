# Label Studio 使用指南

## 📖 简介

### 什么是 Label Studio？

Label Studio 是一个开源的标注平台，支持多种数据类型和标注任务。它提供了一个灵活的界面，可以用于文本标注、图像标注、音频标注等多种场景。

### 为什么使用 Label Studio？

在 PDF 提纲标注项目中，我们使用 Label Studio 的原因包括：

- **🎯 灵活的模板系统**：支持自定义 XML 模板，满足特定标注需求
- **👥 团队协作**：支持多人同时标注，方便团队协作
- **📊 数据管理**：提供完整的数据导入、标注、导出流程
- **🔄 版本控制**：支持标注数据的版本管理和回滚
- **🎨 可视化界面**：提供直观的 Web 界面，提升标注效率

## 🚀 安装和配置

### 环境要求

- Python 3.8+
- Docker（可选）
- 至少 2GB 内存

### 安装方法

#### 方法一：使用 pip 安装（推荐）

```bash
# 创建虚拟环境
conda create -n label-studio python=3.10
conda activate label-studio

# 安装 Label Studio
pip install label-studio
```

#### 方法二：使用 Docker 安装

```bash
# 拉取镜像
docker pull heartexlabs/label-studio:latest

# 运行容器
docker run -it -p 8080:8080 \
  -v $(pwd)/mydata:/label-studio/data \
  heartexlabs/label-studio:latest
```

### 启动 Label Studio

```bash
# 启动 Label Studio
label-studio start

# 指定端口和配置目录
label-studio start --port 8080 --data-dir ./label-studio-data

# 后台运行
label-studio start --port 8080 --data-dir ./label-studio-data --no-browser
```

### 首次登录

1. 打开浏览器访问 `http://localhost:8080`
2. 创建管理员账户
3. 进入主界面

## 🎨 模板系统介绍

Label Studio 使用 XML 格式的模板来定义标注界面。本项目提供了两种主要模板：

### 两栏模板（two_column.xml）

**适用场景**：简单的 prompt-response 标注任务

**布局结构**：
- 左栏：Prompt（只读）
- 右栏：Response（可编辑）

**数据字段**：
- `prompt`：待标注的提示文本
- `response`：标注者输入的回答

**示例**：
```xml
<Text name="prompt" value="$prompt" />
<TextArea name="response" toName="prompt"
          placeholder="Enter your annotation here..."
          rows="25" />
```

### 三栏模板（three_column.xml）

**适用场景**：复杂的模型输出对比标注任务

**布局结构**：
- 第一栏：User Prompts（用户提示）
  - Original Prompt（原始提示）
  - User Feedback（用户反馈）
  - Final Prompt（最终提示）
- 第二栏：Model Response（模型响应）
  - Model Name（模型名称）
  - Reasoning（推理过程）
  - Answer（答案）
- 第三栏：Annotation（标注区域）
  - Annotated Model（标注模型）
  - Annotated Reasoning（标注推理）
  - Annotated Answer（标注答案）

**数据字段**：
- `original_prompt`：原始用户提示
- `user_feedback`：用户反馈
- `final_prompt`：最终提示
- `model_name`：模型名称
- `model_reasoning`：模型推理过程
- `model_answer`：模型答案
- `annotated_model`：标注的模型名称
- `annotated_reasoning`：标注的推理过程
- `annotated_answer`：标注的答案

## 📋 数据准备流程

### 数据格式要求

Label Studio 支持 JSON、JSONL、CSV 等多种数据格式。对于本项目的提纲标注任务，推荐使用 JSON 格式。

#### 两栏模板数据格式

```json
{
  "prompt": "请提取文档的提纲结构...",
  "response": ""
}
```

#### 三栏模板数据格式

```json
{
  "original_prompt": "原始提示文本",
  "user_feedback": "用户反馈文本",
  "final_prompt": "最终提示文本",
  "model_name": "GPT-4",
  "model_reasoning": "推理过程...",
  "model_answer": "答案...",
  "annotated_model": "",
  "annotated_reasoning": "",
  "annotated_answer": ""
}
```

### 数据准备脚本

使用项目提供的数据准备工具：

```bash
# 准备两栏模板数据
python labeling/prepare_data.py --template two_column --input data/raw.jsonl --output labeling_data/outline/data.json

# 准备三栏模板数据
python labeling/prepare_data.py --template three_column --input data/raw.jsonl --output labeling_data/outline/data.json
```

### 数据验证

```bash
# 验证数据格式
python labeling/validate_data.py --input labeling_data/outline/data.json
```

## 🎯 创建标注项目

### 步骤一：创建新项目

1. 登录 Label Studio
2. 点击 "Create" 按钮
3. 选择 "Create new project"
4. 填写项目信息：
   - **Project Name**：提纲标注项目
   - **Description**：PDF 文档提纲结构标注

### 步骤二：配置标注界面

1. 进入项目设置
2. 点击 "Labeling Interface"
3. 选择 "Custom Template"
4. 选择合适的模板：
   - 对于简单任务：选择两栏模板
   - 对于复杂任务：选择三栏模板

#### 导入两栏模板

复制 `labeling/templates/outline/two_column.xml` 的内容到模板编辑器中。

#### 导入三栏模板

复制 `labeling/templates/outline/three_column.xml` 的内容到模板编辑器中。

### 步骤三：配置标签

对于三栏模板，可以配置额外的标签来标记不同的标注状态：

1. 点击 "Add Label"
2. 添加标签：
   - `correct`：正确
   - `needs_review`：需要审核
   - `incorrect`：错误

## 📥 导入标注数据

### 方法一：Web 界面导入

1. 进入项目
2. 点击 "Import"
3. 选择数据源：
   - **Upload files**：上传 JSON/JSONL 文件
   - **Paste data**：直接粘贴 JSON 数据
4. 确认字段映射

### 方法二：CLI 导入

```bash
# 导入 JSON 文件
label-studio import \
  --project-id <PROJECT_ID> \
  --format JSON \
  --input-path labeling_data/outline/data.json

# 导入 JSONL 文件
label-studio import \
  --project-id <PROJECT_ID> \
  --format JSONL \
  --input-path labeling_data/outline/data.jsonl
```

### 批量导入脚本

```bash
# 使用项目提供的批量导入脚本
python labeling/batch_import.py \
  --project-id <PROJECT_ID> \
  --input-dir labeling_data/outline/ \
  --batch-size 100
```

## ✍️ 进行标注

### 标注界面概览

#### 两栏模板标注界面

- **左侧**：显示 prompt 文本（只读）
- **右侧**：输入区域，标注者在此输入回答
- **底部**：标注控制按钮

#### 三栏模板标注界面

- **第一栏**：用户提示信息
  - Original Prompt：原始提示文本
  - User Feedback：用户反馈
  - Final Prompt：最终提示
- **第二栏**：模型响应信息
  - Model Name：模型名称
  - Reasoning：推理过程
  - Answer：答案
- **第三栏**：标注区域
  - Annotated Model：标注模型名称
  - Annotated Reasoning：标注推理过程
  - Annotated Answer：标注答案

### 标注操作步骤

#### 两栏模板标注

1. 阅读左侧的 prompt 文本
2. 在右侧输入区域编写回答
3. 完成后点击 "Submit" 按钮
4. 自动跳转到下一个任务

#### 三栏模板标注

1. 查看第一栏的用户提示信息
2. 查看第二栏的模型响应
3. 在第三栏标注区域：
   - 评估模型名称是否正确
   - 检查推理过程是否合理
   - 验证答案是否准确
4. 如有错误，在对应标注区域进行修改
5. 完成后点击 "Submit" 按钮
6. 自动跳转到下一个任务

### 标注快捷键

- `Ctrl + Enter`：提交标注
- `Ctrl + S`：保存标注草稿
- `Ctrl + Z`：撤销上一步操作
- `Ctrl + Shift + Z`：重做操作
- `Alt + ←`：上一个任务
- `Alt + →`：下一个任务

### 标注质量控制

#### 多人标注模式

1. 进入项目设置
2. 启用 "Multiple annotators"
3. 设置每人标注数量
4. 配置标注一致性检查

#### 审核模式

1. 在项目设置中启用 "Review"
2. 指定审核人员
3. 审核人员可以查看和修改标注结果

#### 一致性评估

```bash
# 计算标注一致性
python labeling/calculate_agreement.py \
  --project-id <PROJECT_ID> \
  --method kappa \
  --output agreement_report.json
```

## 📤 导出标注结果

### 方法一：Web 界面导出

1. 进入项目
2. 点击 "Export"
3. 选择导出格式：
   - **JSON**：包含完整的标注数据
   - **JSONL**：每行一个 JSON 对象
   - **CSV**：表格格式
   - **COCO**：标注对象格式
4. 点击 "Export" 下载文件

### 方法二：CLI 导出

```bash
# 导出为 JSON 格式
label-studio export \
  --project-id <PROJECT_ID> \
  --format JSON \
  --output-path exported_data.json

# 导出为 JSONL 格式
label-studio export \
  --project-id <PROJECT_ID> \
  --format JSONL \
  --output-path exported_data.jsonl

# 只导出已完成的标注
label-studio export \
  --project-id <PROJECT_ID> \
  --format JSON \
  --export-only-completed \
  --output-path completed_data.json
```

### 数据转换

导出的数据可能需要转换为特定格式用于训练：

```bash
# 转换为训练格式
python labeling/convert_export.py \
  --input exported_data.json \
  --output training_data.jsonl \
  --format grpo

# 提取特定字段
python labeling/convert_export.py \
  --input exported_data.json \
  --output prompts.jsonl \
  --extract-field prompt
```

### 批量导出脚本

```bash
# 批量导出多个项目
python labeling/batch_export.py \
  --project-ids <PROJECT_ID_1>,<PROJECT_ID_2> \
  --output-dir exported_data/ \
  --format JSON
```

## ❓ 常见问题解答

### 安装和配置问题

#### Q: 启动 Label Studio 时报错 "Port 8080 is already in use"

**A:** 端口已被占用，可以使用其他端口：

```bash
label-studio start --port 8081
```

#### Q: 无法访问 Label Studio 界面

**A:** 检查防火墙设置和端口是否正确：

```bash
# Windows
netsh advfirewall firewall add rule name="Label Studio" dir=in action=allow protocol=TCP localport=8080

# Linux/Mac
sudo ufw allow 8080
```

### 数据导入问题

#### Q: 导入数据时提示字段不匹配

**A:** 检查数据格式是否与模板要求的字段一致：

```bash
# 使用验证工具检查数据
python labeling/validate_data.py --input data.json --template two_column
```

#### Q: 大批量数据导入失败

**A:** 分批次导入或增加超时时间：

```bash
# 分批次导入
label-studio import --batch-size 100 --input-path data.json

# 增加超时时间
label-studio import --timeout 600 --input-path data.json
```

### 标注操作问题

#### Q: 标注数据没有保存

**A:** 检查网络连接和 Label Studio 服务状态：

```bash
# 检查服务状态
label-studio ps

# 重启服务
label-studio restart
```

#### Q: 如何跳过当前任务

**A:** 点击 "Skip" 按钮跳过当前任务，任务会被标记为 "Skipped"。

### 数据导出问题

#### Q: 导出的数据格式不符合预期

**A:** 使用数据转换工具处理导出数据：

```bash
python labeling/convert_export.py \
  --input exported_data.json \
  --output training_data.jsonl \
  --format custom
```

#### Q: 如何只导出特定状态的标注

**A:** 使用过滤器：

```bash
label-studio export \
  --filter "state=completed" \
  --output-path completed_data.json
```

### 性能问题

#### Q: 标注界面加载缓慢

**A:** 优化数据大小和分页设置：

```bash
# 减少每页显示的任务数
label-studio config --page-size 20
```

#### Q: 内存占用过高

**A:** 增加内存限制或使用数据库后端：

```bash
# 使用 PostgreSQL 后端
label-studio start --db postgresql://user:password@localhost:5432/labelstudio
```

## 💡 最佳实践

### 数据准备

1. **数据清洗**：确保数据格式正确，去除无效字符
2. **数据验证**：使用验证工具检查数据格式
3. **批量处理**：对于大数据集，分批导入和处理
4. **版本控制**：对数据文件进行版本管理

### 模板选择

1. **两栏模板**：适用于简单的 prompt-response 任务
2. **三栏模板**：适用于复杂的模型输出对比任务
3. **自定义模板**：根据特定需求创建自定义模板

### 标注流程

1. **培训标注人员**：提供详细的标注指南和示例
2. **设置标注标准**：明确标注规则和质量标准
3. **定期检查**：定期检查标注质量和一致性
4. **反馈机制**：建立标注反馈和问题报告机制

### 质量控制

1. **多人标注**：重要数据采用多人标注模式
2. **审核机制**：建立标注审核流程
3. **一致性检查**：定期计算标注一致性
4. **质量评估**：使用自动化工具评估标注质量

### 数据管理

1. **定期备份**：定期备份标注数据
2. **版本管理**：对标注数据进行版本控制
3. **数据归档**：完成的项目及时归档
4. **权限管理**：合理设置用户权限

### 团队协作

1. **任务分配**：合理分配标注任务
2. **进度跟踪**：跟踪标注进度和完成情况
3. **沟通协调**：建立有效的沟通机制
4. **知识共享**：分享标注经验和最佳实践

## 📚 相关资源

### 官方文档

- [Label Studio 官方文档](https://labelstud.io/guide/)
- [Label Studio GitHub 仓库](https://github.com/heartexlabs/label-studio)

### 项目文档

- [模板系统文档](../labeling/templates/README.md)
- [故障排查指南](./troubleshooting.md)
- [数据格式规范](./data-format-spec.md)

### 社区资源

- [Label Studio 论坛](https://labelstud.io/guide/forum.html)
- [Stack Overflow - Label Studio 标签](https://stackoverflow.com/questions/tagged/label-studio)

---

**文档版本**：v1.0
**最后更新**：2026-02-16
**维护者**：PDF Mining Team
