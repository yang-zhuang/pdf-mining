# Label Studio 模板系统文档

## 📐 模板系统架构

### 目录结构

```
labeling/templates/
├── outline/              # 提纲标注模板
│   ├── two_column.xml    # 两栏模板
│   └── three_column.xml  # 三栏模板
├── custom/               # 自定义模板
│   └── README.md         # 自定义模板说明
└── README.md             # 本文档
```

### 模板组件层次

```
View (根容器)
├── Header (页面标题)
├── Style (CSS 样式)
│   ├── .container (容器样式)
│   ├── .column (列样式)
│   ├── .item (项目样式)
│   └── ... (其他样式)
└── Content (内容区域)
    ├── Text (只读文本)
    ├── TextArea (可编辑文本框)
    ├── HyperText (富文本)
    └── ... (其他组件)
```

## 🎯 模板列表和说明

### 1. 两栏模板（two_column.xml）

**文件路径**：`labeling/templates/outline/two_column.xml`

**适用场景**：
- 简单的 prompt-response 标注任务
- 单轮对话标注
- 文本生成任务

**布局特点**：
- 左右两栏布局
- 左栏：只读的 prompt 文本
- 右栏：可编辑的 response 输入框
- 清晰的视觉分隔

**数据字段映射**：

| 模板字段 | 数据字段 | 说明 | 是否可编辑 |
|---------|---------|------|-----------|
| `prompt` | `$prompt` | 待标注的提示文本 | 否 |
| `response` | `response` | 标注者输入的回答 | 是 |

**样式特点**：
- 现代化的渐变背景
- 圆角边框设计
- 自定义滚动条
- 响应式布局

**示例数据**：
```json
{
  "prompt": "请提取文档的提纲结构，并标注层级关系...",
  "response": ""
}
```

### 2. 三栏模板（three_column.xml）

**文件路径**：`labeling/templates/outline/three_column.xml`

**适用场景**：
- 复杂的模型输出对比标注
- 多轮对话标注
- 模型性能评估任务

**布局特点**：
- 三栏布局，每栏宽度为 32% / 33% / 35%
- 第一栏：用户提示信息（原始提示、用户反馈、最终提示）
- 第二栏：模型响应信息（模型名称、推理过程、答案）
- 第三栏：标注区域（可编辑的三个标注框）

**数据字段映射**：

| 模板字段 | 数据字段 | 说明 | 是否可编辑 |
|---------|---------|------|-----------|
| `original_prompt` | `$original_prompt` | 原始用户提示 | 否 |
| `user_feedback` | `$user_feedback` | 用户反馈 | 否 |
| `final_prompt` | `$final_prompt` | 最终提示 | 否 |
| `model_name` | `$model_name` | 模型名称 | 否 |
| `model_reasoning` | `$model_reasoning` | 模型推理过程 | 否 |
| `model_answer` | `$model_answer` | 模型答案 | 否 |
| `annotated_model` | `annotated_model` | 标注的模型名称 | 是 |
| `annotated_reasoning` | `annotated_reasoning` | 标注的推理过程 | 是 |
| `annotated_answer` | `annotated_answer` | 标注的答案 | 是 |

**样式特点**：
- 不同栏目使用不同的颜色主题
- 渐变色标题栏
- 可滚动的内容区域
- 响应式设计

**示例数据**：
```json
{
  "original_prompt": "请分析以下文档的结构...",
  "user_feedback": "需要更详细的层次分析",
  "final_prompt": "请详细分析文档结构，包括一、二、三级提纲...",
  "model_name": "GPT-4",
  "model_reasoning": "首先识别文档的标题格式...",
  "model_answer": "文档包含3个主要部分...",
  "annotated_model": "",
  "annotated_reasoning": "",
  "annotated_answer": ""
}
```

## 🛠️ 如何创建新模板

### 步骤一：设计模板结构

确定模板需要的字段和布局：

```markdown
# 模板需求分析

## 标注任务
[描述标注任务的类型和目的]

## 需要显示的数据
- [ ] 字段1：说明
- [ ] 字段2：说明
- [ ] 字段3：说明

## 需要编辑的字段
- [ ] 字段A：说明
- [ ] 字段B：说明

## 布局设计
- 列数：X 列
- 每列宽度：X% / Y% / Z%
```

### 步骤二：创建模板文件

创建 XML 文件，基本结构如下：

```xml
<?xml version="1.0" encoding="utf-8"?>
<View>
    <!-- Header -->
    <Header value="Your Template Name" />

    <!-- Styles -->
    <Style>
        /* CSS 样式 */
    </Style>

    <!-- Layout -->
    <div class="container">
        <!-- 内容区域 -->
    </div>
</View>
```

### 步骤三：添加 CSS 样式

在 `<Style>` 标签中添加样式：

```xml
<Style>
    /* 容器样式 */
    .container {
        display: flex;
        gap: 20px;
        padding: 20px;
    }

    /* 列样式 */
    .column {
        flex: 1;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
    }

    /* 文本样式 */
    .text-area {
        width: 100%;
        min-height: 100px;
        padding: 8px;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
    }

    /* 自定义滚动条 */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #f1f1f1;
    }

    ::-webkit-scrollbar-thumb {
        background: #cbd5e0;
        border-radius: 4px;
    }
</Style>
```

### 步骤四：添加数据组件

使用 Label Studio 组件显示和编辑数据：

```xml
<div class="container">
    <!-- 只读文本 -->
    <div class="column">
        <div class="header">Read Only Data</div>
        <Text name="field1" value="$field1" />
    </div>

    <!-- 可编辑文本框 -->
    <div class="column">
        <div class="header">Editable Field</div>
        <TextArea name="field2" toName="field1"
                  placeholder="Enter your answer..."
                  rows="10" />
    </div>

    <!-- 富文本 -->
    <div class="column">
        <div class="header">Rich Text</div>
        <HyperText name="field3" value="$field3" />
    </div>
</div>
```

### 步骤五：测试模板

1. 将模板文件保存到 `labeling/templates/` 目录
2. 在 Label Studio 中创建测试项目
3. 导入模板并测试功能

### 步骤六：优化和调整

根据测试结果优化模板：
- 调整样式和布局
- 优化用户体验
- 添加辅助功能

## 📊 数据字段映射

### 变量语法

Label Studio 使用 `$` 符号来引用数据字段：

```xml
<!-- 引用数据字段 -->
<Text name="prompt" value="$prompt" />
<HyperText name="content" value="$content" />

<!-- 嵌套引用 -->
<Text name="title" value="$metadata.title" />
```

### 组件类型

#### Text

只读文本组件，用于显示短文本：

```xml
<Text name="field_name" value="$data_field" />
```

**属性**：
- `name`：组件名称
- `value`：数据字段引用
- `inline`：是否内联显示（默认 false）

#### TextArea

可编辑的多行文本框：

```xml
<TextArea name="field_name" toName="target_field"
          placeholder="Placeholder text"
          rows="10"
          maxSubmissions="1" />
```

**属性**：
- `name`：组件名称
- `toName`：关联的目标字段名称
- `placeholder`：占位符文本
- `rows`：行数
- `maxSubmissions`：最大提交次数

#### HyperText

富文本组件，支持 HTML 格式：

```xml
<HyperText name="field_name" value="$data_field" />
```

**属性**：
- `name`：组件名称
- `value`：数据字段引用
- `inline`：是否内联显示（默认 false）

#### Header

页面标题：

```xml
<Header value="Page Title" />
```

#### Labels

标签选择组件：

```xml
<Labels name="labels" toName="text">
    <Label value="positive" background="green" />
    <Label value="negative" background="red" />
    <Label value="neutral" background="gray" />
</Labels>
```

### 样式定义

CSS 样式定义在 `<Style>` 标签中：

```xml
<Style>
    /* 类选择器 */
    .class-name {
        property: value;
    }

    /* ID 选择器 */
    #element-id {
        property: value;
    }

    /* 元素选择器 */
    element {
        property: value;
    }

    /* 伪类选择器 */
    .class-name:hover {
        property: value;
    }

    /* 响应式设计 */
    @media (max-width: 768px) {
        .container {
            flex-direction: column;
        }
    }
</Style>
```

## 📝 使用示例

### 示例一：简单的文本分类模板

```xml
<?xml version="1.0" encoding="utf-8"?>
<View>
    <Header value="Text Classification" />

    <Style>
        .container {
            display: flex;
            flex-direction: column;
            gap: 16px;
            padding: 20px;
        }

        .text-display {
            background: #f7fafc;
            padding: 16px;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }
    </Style>

    <div class="container">
        <div class="text-display">
            <Text name="text" value="$text" />
        </div>

        <Labels name="label" toName="text">
            <Label value="positive" background="#48bb78" />
            <Label value="negative" background="#f56565" />
            <Label value="neutral" background="#718096" />
        </Labels>
    </div>
</View>
```

**数据格式**：
```json
{
  "text": "这是一段需要分类的文本..."
}
```

### 示例二：对话标注模板

```xml
<?xml version="1.0" encoding="utf-8"?>
<View>
    <Header value="Conversation Annotation" />

    <Style>
        .conversation-container {
            display: flex;
            flex-direction: column;
            gap: 12px;
            padding: 20px;
        }

        .message {
            padding: 12px 16px;
            border-radius: 8px;
            max-width: 80%;
        }

        .user-message {
            background: #e3f2fd;
            align-self: flex-end;
        }

        .assistant-message {
            background: #f5f5f5;
            align-self: flex-start;
        }

        .annotation-area {
            margin-top: 16px;
        }
    </Style>

    <div class="conversation-container">
        <div class="message user-message">
            <Text name="user_input" value="$user_input" />
        </div>

        <div class="message assistant-message">
            <Text name="assistant_response" value="$assistant_response" />
        </div>

        <div class="annotation-area">
            <Labels name="quality" toName="assistant_response">
                <Label value="helpful" />
                <Label value="not_helpful" />
                <Label value="harmful" />
            </Labels>

            <TextArea name="feedback" toName="assistant_response"
                      placeholder="Provide feedback..."
                      rows="4" />
        </div>
    </div>
</View>
```

**数据格式**：
```json
{
  "user_input": "用户输入的问题",
  "assistant_response": "助手的回答..."
}
```

### 示例三：文档结构标注模板

```xml
<?xml version="1.0" encoding="utf-8"?>
<View>
    <Header value="Document Structure Annotation" />

    <Style>
        .layout {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            padding: 20px;
        }

        .panel {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
        }

        .panel-title {
            font-weight: 600;
            margin-bottom: 12px;
            color: #2d3748;
        }

        .section {
            background: #f7fafc;
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 4px;
            border-left: 3px solid #4299e1;
        }
    </Style>

    <div class="layout">
        <div class="panel">
            <div class="panel-title">Document Sections</div>
            <HyperText name="sections" value="$sections" />
        </div>

        <div class="panel">
            <div class="panel-title">Structure Annotation</div>
            <TextArea name="structure" toName="sections"
                      placeholder="Describe the document structure..."
                      rows="10" />

            <Labels name="doc_type" toName="sections">
                <Label value="report" />
                <Label value="paper" />
                <Label value="article" />
                <Label value="other" />
            </Labels>
        </div>
    </div>
</View>
```

**数据格式**：
```json
{
  "sections": "<div class='section'>1. Introduction</div><div class='section'>2. Methodology</div>"
}
```

## 🔧 模板调试技巧

### 1. 使用浏览器开发者工具

- 按 F12 打开开发者工具
- 检查元素结构和样式
- 查看控制台错误信息

### 2. 测试数据格式

```bash
# 验证数据格式
python labeling/validate_data.py --input data.json --template template_name
```

### 3. 分步测试

1. 先测试基本的文本显示
2. 添加样式和布局
3. 添加交互组件
4. 完整功能测试

### 4. 性能优化

- 减少不必要的 DOM 元素
- 优化 CSS 选择器
- 使用虚拟滚动（大数据集）

## 📚 相关资源

### Label Studio 官方文档

- [Label Studio XML 模板文档](https://labelstud.io/guide/tags.html)
- [Label Studio 样式指南](https://labelstud.io/guide/configure_tagging_interface.html)
- [Label Studio 组件参考](https://labelstud.io/tags/)

### 项目资源

- [Label Studio 使用指南](../../docs/label-studio-guide.md)
- [数据格式规范](../../docs/data-format-spec.md)
- [故障排查指南](../../docs/troubleshooting.md)

---

**文档版本**：v1.0
**最后更新**：2026-02-16
**维护者**：PDF Mining Team
