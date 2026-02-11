"""
训练数据构建共享工具

提供数据格式转换、验证、拆分等通用功能
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any, Literal
from datetime import datetime


# 支持的训练数据格式
TrainingFormat = Literal[
    "alpaca",      # Alpaca 格式
    "sharegpt",    # ShareGPT 格式
    "instruction", # Instruction 格式
    "openai",      # OpenAI Chat 格式
    "trl_grpo",    # TRL GRPO 格式（JSONL）
    "custom"       # 自定义格式
]


def convert_to_alpaca(data: List[Dict]) -> List[Dict]:
    """
    转换为 Alpaca 格式

    格式：
    {
        "instruction": str,
        "input": str,
        "output": str
    }

    Args:
        data: 原始数据列表

    Returns:
        Alpaca 格式的数据列表
    """
    alpaca_data = []

    for item in data:
        prompt = item.get('data', {}).get('prompt', '')
        response = item.get('annotations', [])[0].get('result', [])[0].get('value', {}).get('text', [])[0].strip()

        alpaca_item = {
            "input": prompt,
            "output": response
        }
        alpaca_data.append(alpaca_item)

    return alpaca_data

def convert_to_sharegpt(data: List[Dict]) -> List[Dict]:
    """
    转换为 ShareGPT 格式

    格式：
    {
        "conversations": [
            {"from": "human", "value": str},
            {"from": "gpt", "value": str}
        ]
    }

    Args:
        data: 原始数据列表

    Returns:
        ShareGPT 格式的数据列表
    """
    sharegpt_data = []

    for item in data:
        prompt = item.get('data', {}).get('prompt', '')
        response = item.get('annotations', [])[0].get('result', [])[0].get('value', {}).get('text', [])[0].strip()

        sharegpt_item = {
            "conversations": [
                {
                    "from": "human",
                    "value": prompt
                },
                {
                    "from": "gpt",
                    "value": response
                }
            ]
        }
        sharegpt_data.append(sharegpt_item)

    return sharegpt_data


def convert_to_instruction(data: List[Dict]) -> List[Dict]:
    """
    转换为 Instruction 格式

    格式：
    {
        "instruction": str,
        "output": str
    }

    Args:
        data: 原始数据列表

    Returns:
        Instruction 格式的数据列表
    """
    instruction_data = []

    for item in data:
        prompt = item.get('data', {}).get('prompt', '')
        response = item.get('annotations', [])[0].get('result', [])[0].get('value', {}).get('text', [])[0].strip()

        instruction_item = {
            "instruction": prompt,
            "output": response
        }
        instruction_data.append(instruction_item)

    return instruction_data


def convert_to_openai(data: List[Dict]) -> List[Dict]:
    """
    转换为 OpenAI Chat 格式

    格式：
    {
        "messages": [
            {"role": "user", "content": str},
            {"role": "assistant", "content": str}
        ]
    }

    Args:
        data: 原始数据列表

    Returns:
        OpenAI Chat 格式的数据列表
    """
    openai_data = []

    for item in data:
        prompt = item.get('data', {}).get('prompt', '')
        response = item.get('annotations', [])[0].get('result', [])[0].get('value', {}).get('text', [])[0].strip()

        openai_item = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                },
                {
                    "role": "assistant",
                    "content": response
                }
            ]
        }
        openai_data.append(openai_item)

    return openai_data


def convert_to_trl_grpo(data: List[Dict]) -> List[Dict]:
    """
    转换为 TRL GRPO 格式

    格式（JSONL，每行一个 JSON 对象）：
    {
        "prompt": [{"role": "user", "content": str}],
        "ground_truth": str
    }

    Args:
        data: 原始数据列表

    Returns:
        TRL GRPO 格式的数据列表
    """
    trl_grpo_data = []

    for item in data:
        prompt = item.get('data', {}).get('prompt', '')
        response = item.get('annotations', [])[0].get('result', [])[0].get('value', {}).get('text', [])[0].strip()

        trl_grpo_item = {
            "prompt": [{"role": "user", "content": prompt}],
            "solution": response
        }
        trl_grpo_data.append(trl_grpo_item)

    return trl_grpo_data


def convert_training_format(
    data: List[Dict],
    format: TrainingFormat = "alpaca"
) -> List[Dict]:
    """
    转换训练数据格式

    Args:
        data: 原始数据列表（包含 prompt 和 response 字段）
        format: 目标格式

    Returns:
        转换后的数据列表

    Raises:
        ValueError: 不支持的格式
    """
    converters = {
        "alpaca": convert_to_alpaca,
        "sharegpt": convert_to_sharegpt,
        "instruction": convert_to_instruction,
        "openai": convert_to_openai,
        "trl_grpo": convert_to_trl_grpo,
    }

    if format not in converters:
        raise ValueError(f"不支持的格式: {format}，支持的格式: {list(converters.keys())}")

    converter = converters[format]
    return converter(data)


def validate_training_data(data: List[Dict], format: TrainingFormat) -> Dict[str, Any]:
    """
    验证训练数据的质量和完整性

    Args:
        data: 训练数据列表
        format: 数据格式

    Returns:
        验证结果 {"valid": bool, "errors": list, "warnings": list, "stats": dict}
    """
    errors = []
    warnings = []
    stats = {
        "total": len(data),
        "empty_prompt": 0,
        "empty_response": 0,
        "too_short": 0,
        "too_long": 0
    }

    for idx, item in enumerate(data, 1):
        # 检查必填字段
        if format == "alpaca":
            if "instruction" not in item:
                errors.append(f"第 {idx} 条：缺少 instruction 字段")
            if "output" not in item:
                errors.append(f"第 {idx} 条：缺少 output 字段")

            prompt = item.get("input", "")
            response = item.get("output", "")
        elif format == "sharegpt":
            if "conversations" not in item:
                errors.append(f"第 {idx} 条：缺少 conversations 字段")

            conversations = item.get("conversations", [])
            if len(conversations) < 2:
                errors.append(f"第 {idx} 条：conversations 至少需要 2 轮对话")

            # 提取最后一条 assistant 消息作为 response
            last_message = conversations[-1] if conversations else {}
            prompt = conversations[0].get("value", "") if conversations else ""
            response = last_message.get("value", "")
        elif format == "trl_grpo":
            if "prompt" not in item:
                errors.append(f"第 {idx} 条：缺少 prompt 字段")
            if "solution" not in item:
                errors.append(f"第 {idx} 条：缺少 solution 字段")

            prompt_messages = item.get("prompt", [])
            if not isinstance(prompt_messages, list) or len(prompt_messages) == 0:
                errors.append(f"第 {idx} 条：prompt 必须是包含至少一个消息的数组")

            prompt = prompt_messages[0].get("content", "") if prompt_messages else ""
            response = item.get("solution", "")
        else:
            # 其他格式的验证...
            prompt = item.get("prompt", "")
            response = item.get("response", "")

        # 检查空值
        if not prompt or prompt.strip() == "":
            stats["empty_prompt"] += 1
            warnings.append(f"第 {idx} 条：prompt 为空")

        if not response or response.strip() == "":
            stats["empty_response"] += 1
            errors.append(f"第 {idx} 条：response 为空")

        # 检查长度
        prompt_len = len(prompt)
        response_len = len(response)

        if prompt_len < 10:
            stats["too_short"] += 1
            warnings.append(f"第 {idx} 条：prompt 过短（{prompt_len} 字符）")

        if response_len > 100000:
            stats["too_long"] += 1
            warnings.append(f"第 {idx} 条：response 过长（{response_len} 字符）")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": stats
    }


def split_train_val_test(
    data: List[Dict],
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    shuffle: bool = True,
    seed: int = 42
) -> tuple:
    """
    拆分训练集、验证集、测试集

    Args:
        data: 数据列表
        train_ratio: 训练集比例
        val_ratio: 验证集比例
        test_ratio: 测试集比例
        shuffle: 是否打乱数据
        seed: 随机种子

    Returns:
        (train_data, val_data, test_data)
    """
    # 检查比例总和
    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-6:
        raise ValueError(f"比例总和必须为 1.0，当前: {train_ratio + val_ratio + test_ratio}")

    data_copy = data.copy()

    # 打乱数据
    if shuffle:
        random.seed(seed)
        random.shuffle(data_copy)

    # 计算分割点
    total = len(data_copy)
    train_end = int(total * train_ratio)
    val_end = train_end + int(total * val_ratio)

    # 分割
    train_data = data_copy[:train_end]
    val_data = data_copy[train_end:val_end]
    test_data = data_copy[val_end:]

    print(f"[拆分] 总数据: {total}")
    print(f"  训练集: {len(train_data)} ({len(train_data)/total*100:.1f}%)")
    print(f"  验证集: {len(val_data)} ({len(val_data)/total*100:.1f}%)")
    print(f"  测试集: {len(test_data)} ({len(test_data)/total*100:.1f}%)")

    return train_data, val_data, test_data


def save_training_data(
    data: List[Dict],
    output_file: str,
    format: TrainingFormat = "alpaca"
):
    """
    保存训练数据到文件

    Args:
        data: 训练数据列表
        output_file: 输出文件路径
        format: 数据格式
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # TRL GRPO 格式使用 JSONL（每行一个 JSON 对象）
    if format == "trl_grpo":
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in data:
                json.dump(item, f, ensure_ascii=False)
                f.write('\n')
        print(f"[成功] 已保存 {len(data)} 条训练数据到: {output_file} (JSONL 格式)")
    else:
        # 其他格式使用标准 JSON 数组
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[成功] 已保存 {len(data)} 条训练数据到: {output_file}")


def load_json_file(file_path: str) -> List[Dict]:
    """
    加载 JSON 文件

    Args:
        file_path: 文件路径

    Returns:
        数据列表
    """
    file_path_obj = Path(file_path)

    if not file_path_obj.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    with open(file_path_obj, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"JSON 文件格式错误：应为数组，实际类型: {type(data)}")

    print(f"[信息] 成功加载 {len(data)} 条数据")
    return data


def filter_data_by_length(
    data: List[Dict],
    min_length: int = None,
    max_length: int = None,
    field: str = "output"
) -> List[Dict]:
    """
    根据长度过滤数据

    Args:
        data: 数据列表
        min_length: 最小长度（字符数）
        max_length: 最大长度（字符数）
        field: 要检查的字段名

    Returns:
        过滤后的数据列表
    """
    filtered = []

    for item in data:
        content = item.get(field, "")
        length = len(content)

        # 检查最小长度
        if min_length is not None and length < min_length:
            continue

        # 检查最大长度
        if max_length is not None and length > max_length:
            continue

        filtered.append(item)

    print(f"[过滤] 原数据: {len(data)} 条，过滤后: {len(filtered)} 条")
    return filtered


def deduplicate_data(data: List[Dict], key_field: str = "prompt") -> List[Dict]:
    """
    数据去重（基于指定字段）

    Args:
        data: 数据列表
        key_field: 用于去重的字段

    Returns:
        去重后的数据列表
    """
    seen = set()
    deduplicated = []

    for item in data:
        key = item.get(key_field, "")

        # 使用字符串哈希去重
        key_hash = hash(key)

        if key_hash not in seen:
            seen.add(key_hash)
            deduplicated.append(item)

    print(f"[去重] 原数据: {len(data)} 条，去重后: {len(deduplicated)} 条")
    return deduplicated


def compute_data_hash(item: Dict, format: TrainingFormat) -> str:
    """
    计算训练数据的唯一标识（基于内容的 hash）

    Args:
        item: 单条训练数据
        format: 数据格式

    Returns:
        数据的 hash 值（MD5 前 8 位）
    """
    import hashlib

    # 根据不同格式提取关键字段
    if format == "trl_grpo":
        prompt_messages = item.get("prompt", [])
        if isinstance(prompt_messages, list) and len(prompt_messages) > 0:
            prompt = prompt_messages[0].get("content", "")
        else:
            prompt = ""
        response = item.get("ground_truth", "")
    elif format == "alpaca":
        prompt = item.get("input", "")
        response = item.get("output", "")
    elif format == "sharegpt":
        conversations = item.get("conversations", [])
        prompt = conversations[0].get("value", "") if len(conversations) > 0 else ""
        response = conversations[-1].get("value", "") if len(conversations) > 1 else ""
    elif format == "instruction":
        prompt = item.get("instruction", "")
        response = item.get("output", "")
    elif format == "openai":
        messages = item.get("messages", [])
        prompt = messages[0].get("content", "") if len(messages) > 0 else ""
        # 找到第一个 assistant 的回复
        response = ""
        for msg in messages[1:]:
            if msg.get("role") == "assistant":
                response = msg.get("content", "")
                break
    else:
        # 默认处理
        prompt = item.get("prompt", "")
        response = item.get("response", "")

    # 计算 prompt + response 的 hash
    content = f"{prompt}|||{response}"
    hash_value = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]

    return hash_value


def load_existing_hashes(output_dir: str, format: TrainingFormat) -> set:
    """
    从输出文件夹加载已保存数据的 hash 集合

    Args:
        output_dir: 输出文件夹路径
        format: 数据格式

    Returns:
        已存在数据的 hash 集合
    """
    import glob

    output_path = Path(output_dir)
    if not output_path.exists():
        return set()

    existing_hashes = set()

    # 根据格式确定文件扩展名
    ext = '.jsonl' if format == 'trl_grpo' else '.json'

    # 查找所有匹配的文件
    pattern = str(output_path / f"*{ext}")
    files = glob.glob(pattern)

    for file_path in files:
        try:
            if format == "trl_grpo":
                # JSONL 格式：每行一个 JSON 对象
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            item = json.loads(line)
                            hash_value = compute_data_hash(item, format)
                            existing_hashes.add(hash_value)
            else:
                # JSON 格式：整个文件是一个数组
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            hash_value = compute_data_hash(item, format)
                            existing_hashes.add(hash_value)
        except Exception as e:
            print(f"[警告] 读取文件 {file_path} 失败: {e}")
            continue

    print(f"[信息] 从 {len(files)} 个文件中加载了 {len(existing_hashes)} 条已存在的数据")
    return existing_hashes


def filter_new_data(
    data: List[Dict],
    format: TrainingFormat,
    existing_hashes: set = None
) -> tuple:
    """
    过滤出新数据（排除已存在的数据）

    Args:
        data: 训练数据列表
        format: 数据格式
        existing_hashes: 已存在数据的 hash 集合（如果为 None，则返回所有数据）

    Returns:
        (new_data, skipped_count) - 新数据和跳过的数量
    """
    if existing_hashes is None:
        return data, 0

    new_data = []
    skipped_count = 0

    for item in data:
        hash_value = compute_data_hash(item, format)
        if hash_value not in existing_hashes:
            new_data.append(item)
        else:
            skipped_count += 1

    if skipped_count > 0:
        print(f"[过滤] 原数据: {len(data)} 条，新数据: {len(new_data)} 条，跳过已存在: {skipped_count} 条")

    return new_data, skipped_count
