import os
from dotenv import load_dotenv

from extractor.outline_extractor.models.structures import HeadingDetectionConfig

# 加载环境变量
load_dotenv()


class AppConfig:
    """
    PDF 提纲提取器配置类

    所有配置项都支持通过环境变量覆盖，方便不同场景下的定制
    环境变量命名规则：OUTLINE_<配置项大写>
    """

    # ---------- 文本构建 ----------
    # 是否跳过空行（环境变量：OUTLINE_SKIP_EMPTY_LINES）
    SKIP_EMPTY_LINES = os.getenv('OUTLINE_SKIP_EMPTY_LINES', 'True').lower() in ('true', '1', 'yes')

    # 需要移除的前缀列表（环境变量：OUTLINE_PREFIXES_TO_REMOVE，逗号分隔）
    PREFIXES_TO_REMOVE = os.getenv('OUTLINE_PREFIXES_TO_REMOVE', '#').split(',')

    # ---------- 提纲检测 ----------
    # 提纲检测配置（环境变量前缀：OUTLINE_HEADING_）
    HEADING_DETECTION = HeadingDetectionConfig(
        enable_regex=os.getenv('OUTLINE_HEADING_ENABLE_REGEX', 'True').lower() in ('true', '1', 'yes'),
        enable_hash=os.getenv('OUTLINE_HEADING_ENABLE_HASH', 'True').lower() in ('true', '1', 'yes'),
        enable_length=os.getenv('OUTLINE_HEADING_ENABLE_LENGTH', 'True').lower() in ('true', '1', 'yes'),
        min_length=int(os.getenv('OUTLINE_HEADING_MIN_LENGTH', '2')),
        max_length=int(os.getenv('OUTLINE_HEADING_MAX_LENGTH', '40'))
    )

    # ---------- Markdown ----------
    # Markdown 预览最大长度（环境变量：OUTLINE_MAX_PREVIEW_LENGTH）
    MAX_PREVIEW_LENGTH = int(os.getenv('OUTLINE_MAX_PREVIEW_LENGTH', '500'))

    # ---------- Batching ----------
    # 每批最大字符数（环境变量：OUTLINE_MAX_CHARS_PER_BATCH）
    MAX_CHARS_PER_BATCH = int(os.getenv('OUTLINE_MAX_CHARS_PER_BATCH', '3000'))

    # ---------- Prompt ----------
    # Prompt 模板路径（相对于项目根目录的路径）
    # 环境变量：OUTLINE_PROMPT_TEMPLATE_PATH
    # 注意：这是文件系统路径，不是URL
    PROMPT_TEMPLATE_PATH = os.getenv(
        'OUTLINE_PROMPT_TEMPLATE_PATH',
        'extractor/outline_extractor/llm/prompts/outline_prompt.txt'
    )

    # ---------- LLM Client ----------
    # LLM 客户端模式: "modelscope" 或 "vllm"
    # 环境变量：DEFAULT_LLM_MODE（注意：这是通用配置，不是outline专用）
    LLM_CLIENT_MODE = os.getenv('DEFAULT_LLM_MODE', 'modelscope')
