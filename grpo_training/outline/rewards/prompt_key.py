import hashlib

def prompt_to_key(prompt_messages: list[dict]) -> str:
    """
    将 prompt 消息列表转换为稳定、可复现的哈希 key。

    功能说明：
    - 仅使用 system / user 消息内容
    - 忽略 assistant 输出，避免状态污染
    - 通过 SHA1 生成固定长度的 prompt 标识

    设计目的：
    - 为每个 prompt 建立独立的 reward 状态轨道
    - 支持 GRPO 中同一 prompt 多 completion 的状态聚合
    - 避免直接存储长文本带来的内存开销

    参数说明：
    - prompt_messages (list[dict]): 原始 prompt 消息列表

    返回值：
    - str: prompt 对应的哈希 key
    """

    parts = []
    for msg in prompt_messages:
        if msg.get("role") in ("system", "user"):
            parts.append(msg.get("content", "").strip())
    raw = "\n".join(parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()