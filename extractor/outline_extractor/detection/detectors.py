import re

def detect_by_outline_regex(text: str) -> bool:
    """
    判断一行是否为提纲标题，**兼容 OCR 常见空格干扰**，例如：
    - "1. 1"
    - "1 . 2"
    - "（ 一 ）"
    - "第 1 条"
    - "§ 2 . 3"

    支持格式包括：
    - 阿拉伯数字层级（带空格）： "1 . 1"、"2 ． 3 ． 1"
    - 中文数字： "一 、"、"（ 二 ）"
    - 字母： "A ."、"（ B ）"
    - 关键词： "附 录"（但谨慎处理，见说明）
    - 条款式： "第 1 条"、"§ 1"
    """
    if not text:
        return False

    # 允许任意空白（包括空格、全角空格、制表符等）
    ws = r"\s*"  # whitespace (zero or more)

    # 中文数字
    cn_nums = "[一二三四五六七八九十]+"

    # 阿拉伯数字层级（如 1, 1.1, 1.2.3），允许点号间有空格
    # 构造：\d+(\s*\.\s*\d+)*
    arabic = rf"\d+{ws}(?:\.{ws}\d+)*"

    # 标点符号（含全角句号 "．"）
    punct = r"[、\.:：．]"

    patterns = [

        # 1. 阿拉伯层级编号 + 标点（如 "1 . 1 ："、"2．3．1."）
        rf"^{arabic}{ws}{punct}",

        # 2. 中文数字 + 标点（如 "一 、"、"二 . "）
        rf"^{cn_nums}{ws}{punct}",

        # 3. 括号形式（允许括号内空格）：如 "( 1 )"、"（ 一 ）"、"( A )"
        rf"^[\(（]{ws}(?:\d+|{cn_nums}|[A-Za-z]){ws}[\)）]",

        # 4. “第 X” 结构（如 "第 1 条"、"第 二 章"）
        rf"^第{ws}(?:{cn_nums}|\d+)",

        # 5. § 符号（如 "§ 1"、"§ 2 . 1"）
        rf"^§{ws}{arabic}",

        # 6. 附字类关键词（**不建议在词内加空格**，因“附 录”易误判；
        #    但若确有需求，可启用下一行；否则保留原紧凑形式）
        r"^附录\s*[：:]?",
        r"^附件\s*[：:]?",
        r"^附表\s*[：:]?",
        r"^附则\s*[：:]?",
    ]

    return any(re.search(p, text) for p in patterns)


def detect_by_hash_prefix(raw):
    return raw.lstrip().startswith("#")


def detect_by_length(text, min_len, max_len):
    return min_len <= len(text) <= max_len
