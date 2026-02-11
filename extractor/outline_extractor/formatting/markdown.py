from typing import List, Dict, Any


def format_page_markdown(
    page_number: int,
    page_headings: List[Dict[str, Any]],
    max_preview_length: int
) -> str:
    """
    将单页候选提纲渲染为 Markdown 表格（纯视图）
    """
    lines = []
    lines.append(f"第{page_number}页候选内容：")
    lines.append(f"| 页码 | 行号 | 内容预览（前{max_preview_length}字符） |")
    lines.append("|------|------|---------------------|")

    for line in page_headings:
        line_no = line.original_line_number + 1
        text = line.cleaned_text

        preview = (
            text[:max_preview_length] + "..."
            if len(text) > max_preview_length
            else text
        )

        lines.append(f"| {page_number} | {line_no} | {preview} |")

    return "\n".join(lines)
