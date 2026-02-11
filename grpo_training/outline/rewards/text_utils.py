import re

def extract_answer(text: str) -> str:
    """
    从模型原始输出中提取 answer 部分，剔除 think 思考内容。

    功能说明：
    - 若存在 <think>...</think> 标记，则仅保留其后的内容
    - 若存在 <think> 但缺失 </think>，视为异常输出，返回空字符串

    设计目的：
    - 防止将思考链内容误计入 reward
    - 提高 outline / 文本匹配类 reward 的准确性
    - 兼容响应被截断的异常情况

    参数说明：
    - text (str): 模型原始输出文本

    返回值：
    - str: 提取后的 answer 内容
    """

    if "<think>" in text:
        if "</think>" not in text:
            return ""
        text = text.split("</think>", 1)[1]
    return text.strip()


def normalize_lines(text: str) -> list[str]:
    """
    将文本规范化为可用于结构匹配的“有效行”列表。

    修复重点：
    - 正则表达式扩展为支持多级编号（1.1, 1.1.1, 1.1. 等）
    - 移除编号后二次检查空行，避免残留空字符串
    """
    lines = []
    for line in text.splitlines():
        line = line.strip()
        # 跳过原始空行及代码块标记行
        if not line or line.startswith("```"):
            continue
        # 移除行首多级编号前缀（如 "1.", "2.3.1 ", "1.1."）
        line = re.sub(r'^\d[\d.]*\s*', '', line)
        # 关键修复：移除编号后若为空，跳过（避免 [""] 误入结果）
        if not line:
            continue
        lines.append(line)
    return lines