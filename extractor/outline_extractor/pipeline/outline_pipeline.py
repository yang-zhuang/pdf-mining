from typing import List, Callable
from extractor.outline_extractor.models.blocks import OutlineBlock
from extractor.outline_extractor.formatting.markdown import format_page_markdown
from extractor.outline_extractor.batching.char_batcher import batch_by_char_limit
from extractor.outline_extractor.parsing.outline_parser import extract_outline_lines
from extractor.outline_extractor.decorators.llm_cache import llm_call_context


# 客户端缓存（只导入一次）
_client_cache: dict = {}


def _get_llm_client(mode: str) -> Callable:
    """
    根据模式获取对应的 LLM 客户端（带缓存）

    使用缓存避免重复导入和初始化

    Args:
        mode: "modelscope" 或 "vllm"

    Returns:
        callable: LLM 客户端函数
    """
    # 检查缓存
    if mode in _client_cache:
        return _client_cache[mode]

    # 首次调用，执行导入并缓存
    if mode == "vllm":
        from extractor.outline_extractor.llm.client_vllm import call_llm
    else:  # 默认使用 modelscope
        from extractor.outline_extractor.llm.client_modelscope import call_llm

    _client_cache[mode] = call_llm
    return call_llm


def run_outline_pipeline(
    pages,
    prompt_template: str,
    app_config,
    call_llm: Callable = None,
    file_key: str = None
) -> List[str]:

    # 获取配置的 LLM 客户端模式
    llm_mode = getattr(app_config, 'LLM_CLIENT_MODE', 'modelscope')

    # 如果没有传入 call_llm，则获取（支持向后兼容）
    if call_llm is None:
        call_llm = _get_llm_client(llm_mode)
        print(f"[Pipeline] 使用 LLM 模式: {llm_mode} (首次初始化)")
    else:
        print(f"[Pipeline] 使用 LLM 模式: {llm_mode} (复用客户端)")

    # 1. 构建结构化 blocks
    blocks: List[OutlineBlock] = []

    for i, page in enumerate(pages):
        if not page:
            continue

        markdown = format_page_markdown(
            i + 1,
            page,
            app_config.MAX_PREVIEW_LENGTH
        )

        blocks.append(
            OutlineBlock(
                page_number=i + 1,
                headings=page,
                markdown=markdown,
                char_count=len(markdown)
            )
        )

    # 2. 分 batch（仍然是结构化）
    batches = batch_by_char_limit(
        blocks,
        app_config.MAX_CHARS_PER_BATCH
    )

    history: List[str] = []
    all_parts: List[List[str]] = []

    # 3. 调用 LLM
    for batch_idx, batch in enumerate(batches):
        batch_markdown = "\n\n".join(
            block.markdown for block in batch
        )

        history_context = "\n".join(history)

        prompt = prompt_template.format(
            历史上下文提纲=history_context,
            当前候选提纲=batch_markdown
        )

        # 将 batch 转换为可序列化的格式
        batch_serializable = [
            {
                "page_number": block.page_number,
                "headings": [
                    {
                        "original_line_number": h.original_line_number,
                        "raw_text": h.raw_text,
                        "cleaned_text": h.cleaned_text
                    }
                    for h in block.headings
                ],
                "markdown": block.markdown,
                "char_count": block.char_count
            }
            for block in batch
        ]

        # 设置 Context Variable
        token = llm_call_context.set({
            "batch": batch_serializable,
            "history_context": history_context,
            "current_batch_content": batch_markdown,
            "file_key": file_key  # 添加文件标识，用于断点续传
        })

        try:
            response = call_llm(prompt)
            extracted = extract_outline_lines(response["answer"])

            all_parts.append(extracted)
            history.extend([l for l in extracted if l.strip()])
        finally:
            # 重置 Context Variable（推荐做法）
            llm_call_context.reset(token)

    # 4. 合并最终提纲
    final_outline = []
    for part in all_parts:
        final_outline.extend(part)

    return final_outline
