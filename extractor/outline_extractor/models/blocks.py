from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class OutlineBlock:
    """
    表示一个可被送入 LLM 的最小结构单元（通常为一页）
    """
    page_number: int
    headings: List[Dict[str, Any]]   # 原始候选提纲行（完整元数据）
    markdown: str                    # 用于 prompt 的 Markdown 视图
    char_count: int                  # markdown 字符数
