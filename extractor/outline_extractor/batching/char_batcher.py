from typing import List
from extractor.outline_extractor.models.blocks import OutlineBlock


def batch_by_char_limit(
    blocks: List[OutlineBlock],
    max_chars: int
) -> List[List[OutlineBlock]]:
    """
    按字符数限制对 OutlineBlock 进行分批
    """
    batches = []
    current_batch = []
    current_chars = 0

    for block in blocks:
        if current_chars + block.char_count <= max_chars:
            current_batch.append(block)
            current_chars += block.char_count
        else:
            if current_batch:
                batches.append(current_batch)

            current_batch = [block]
            current_chars = block.char_count

    if current_batch:
        batches.append(current_batch)

    return batches
