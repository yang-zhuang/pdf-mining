# PDF 提纲提取器 - 配置说明

本文档详细说明了 PDF 提纲提取器中所有可用的配置选项。

## 目录

- [配置方式](#配置方式)
- [环境变量列表](#环境变量列表)
- [配置说明](#配置说明)
- [使用示例](#使用示例)

---

## 配置方式

本项目支持三种配置方式，按优先级从高到低：

1. **环境变量**（推荐）：在 `.env` 文件中设置
2. **代码默认值**：在 `config/settings.py` 中定义的默认值
3. **命令行参数**：运行 `main.py` 时通过参数指定

---

## 环境变量列表

### 通用 LLM 配置

| 环境变量 | 说明 | 默认值 | 备注 |
|-----------|------|---------|------|
| `DEFAULT_LLM_MODE` | 默认 LLM 模式：`modelscope` 或 `vllm` | `modelscope` | 通用配置，影响所有 LLM 调用 |
| `MODELSCOPE_API_KEY` | ModelScope API 密钥 | *必需* | 从 https://modelscope.cn/my/myaccesstoken 获取 |
| `MODELSCOPE_BASE_URL` | ModelScope API 地址 | `https://api-inference.modelscope.cn/v1` | 通常不需要修改 |
| `MODELSCOPE_DEFAULT_MODEL` | 默认使用的 ModelScope 模型 | `ZhipuAI/GLM-4.7-Flash` | 可选模型列表见代码 |

### vLLM 专用配置

| 环境变量 | 说明 | 默认值 | 备注 |
|-----------|------|---------|------|
| `VLLM_BASE_URL` | vLLM 服务地址 | `http://localhost:8000/v1` | 需先启动 vLLM 服务 |
| `VLLM_API_KEY` | vLLM API 密钥 | `empty` | 本地服务通常为空 |
| `VLLM_MODEL_NAME` | vLLM 使用的模型名称 | `Qwen3-4B-Instruct-2507` | 需与部署的模型一致 |
| `VLLM_MAX_TOKENS` | 单次请求最大 tokens | `15000` | 根据模型和显存调整 |
| `VLLM_TEMPERATURE` | 生成温度参数 | `0.1` | 0.0-1.0 之间，越高越随机 |

### Outline Extractor 专用配置

所有 Outline Extractor 专用配置都以 `OUTLINE_` 开头，避免与其他模块冲突。

#### 文本构建配置

| 环境变量 | 说明 | 默认值 | 可选值 |
|-----------|------|---------|---------|
| `OUTLINE_SKIP_EMPTY_LINES` | 是否跳过空行 | `true` | `true`/`false`/`1`/`0` |
| `OUTLINE_PREFIXES_TO_REMOVE` | 需要移除的前缀列表（逗号分隔） | `#` | 如：`#,•,◆` |

#### 提纲检测配置

| 环境变量 | 说明 | 默认值 | 可选值 |
|-----------|------|---------|---------|
| `OUTLINE_HEADING_ENABLE_REGEX` | 启用正则表达式检测 | `true` | `true`/`false` |
| `OUTLINE_HEADING_ENABLE_HASH` | 启用 # 前缀检测 | `true` | `true`/`false` |
| `OUTLINE_HEADING_ENABLE_LENGTH` | 启用长度范围检测 | `true` | `true`/`false` |
| `OUTLINE_HEADING_MIN_LENGTH` | 提纲最小长度 | `2` | 数字（字符数） |
| `OUTLINE_HEADING_MAX_LENGTH` | 提纲最大长度 | `40` | 数字（字符数） |

#### Markdown 和 Batching 配置

| 环境变量 | 说明 | 默认值 |
|-----------|------|---------|
| `OUTLINE_MAX_PREVIEW_LENGTH` | Markdown 预览最大长度 | `500` |
| `OUTLINE_MAX_CHARS_PER_BATCH` | 每批最大字符数 | `3000` |

#### Prompt 模板配置

| 环境变量 | 说明 | 默认值 | 特殊说明 |
|-----------|------|---------|---------|
| `OUTLINE_PROMPT_TEMPLATE_PATH` | Prompt 模板路径 | `extractor/outline_extractor/llm/prompts/outline_prompt.txt` | ⚠️ **这是文件系统路径** |

**重要提示**：
- `OUTLINE_PROMPT_TEMPLATE_PATH` 是**文件系统路径**，不是 URL
- 支持绝对路径和相对路径（相对于项目根目录）
- 相对路径示例：`extractor/outline_extractor/llm/prompts/outline_prompt.txt`
- 绝对路径示例：`/home/user/prompts/outline_prompt.txt` 或 `C:\\prompts\\outline_prompt.txt`

---

## 配置说明

### 1. 文本构建配置

**跳过空行**：控制是否从输入中移除空行，提高处理效率

**移除前缀**：指定需要从候选提纲中移除的前缀符号，如 `#`、`•` 等

### 2. 提纲检测配置

**正则表达式检测**：使用正则模式识别数字序号（如 `1.`、`2.`）

**# 前缀检测**：识别以 `#` 开头的 Markdown 标题

**长度范围检测**：只提取长度在指定范围内的候选（默认 2-40 个字符）

### 3. Batching 配置

**每批最大字符数**：将长文本拆分成批次发送给 LLM，避免超出最大 token 限制

### 4. Prompt 模板

使用自定义的 prompt 模板，可以在不修改代码的情况下调整提取策略

---

## 使用示例

### 示例 1：使用默认配置

直接运行，使用所有默认值：

```bash
python extractor/outline_extractor/main.py
```

### 示例 2：禁用长度检测

```bash
python extractor/outline_extractor/main.py --disable-length
```

或通过环境变量：

```env
# .env 文件
OUTLINE_HEADING_ENABLE_LENGTH=false
```

### 示例 3：自定义 Prompt 模板

```bash
# 1. 创建自定义 prompt 文件
cp extractor/outline_extractor/llm/prompts/outline_prompt.txt my_outline_prompt.txt

# 2. 编辑 my_outline_prompt.txt

# 3. 使用自定义 prompt
OUTLINE_PROMPT_TEMPLATE_PATH=my_outline_prompt.txt
```

### 示例 4：使用本地 vLLM

```bash
# 1. 启动 vLLM 服务
# 参考 vLLM 文档启动服务

# 2. 配置环境变量
# .env 文件
DEFAULT_LLM_MODE=vllm
VLLM_BASE_URL=http://localhost:8000/v1

# 3. 运行
python extractor/outline_extractor/main.py --llm-mode vllm
```

### 示例 5：调整 batch 大小

```env
# 减小 batch size，适合显存较小的环境
OUTLINE_MAX_CHARS_PER_BATCH=2000
```

---

## 验证配置

运行验证脚本检查配置是否正确：

```bash
python verify_env.py
```

验证脚本会检查：
- ✅ `.env` 文件是否存在
- ✅ 必需的环境变量是否设置
- ✅ 所有可选配置的值
- ✅ 模块是否能正常加载

---

## 注意事项

1. **路径格式**：
   - Windows 路径使用正斜杠 `/` 或双反斜杠 `\\`
   - 推荐使用正斜杠以避免转义问题

2. **布尔值**：
   - 可接受：`true`、`false`、`1`、`0`、`yes`、`no`
   - 不区分大小写

3. **调试技巧**：
   - 使用 `--start` 和 `--end` 处理文件子集
   - 使用 `--force` 强制重新处理
   - 查看日志目录了解处理进度

---

## 配置优先级

当同一配置有多种来源时，优先级为：

1. **命令行参数**（最高）
2. **环境变量**
3. **代码默认值**（最低）

示例：

```bash
# 代码默认：SKIP_EMPTY_LINES = True
# 环境变量：OUTLINE_SKIP_EMPTY_LINES=false
# 命令行：--no-skip-empty（如果支持）
# 最终使用：false（命令行 > 环境变量 > 代码默认）
```

---

**最后更新时间**: 2025-02-11
