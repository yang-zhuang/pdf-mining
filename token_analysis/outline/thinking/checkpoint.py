"""
断点续传管理

处理 token 分析的断点续传功能，支持：
- 读取已保存的结果
- 基于 prompt hash 的唯一标识
- 支持从多个文件恢复断点
"""

import json
import hashlib
from pathlib import Path
from typing import Set, Dict


def compute_prompt_hash(prompt: str) -> str:
    """
    计算 prompt 的 hash 值，作为唯一标识

    Args:
        prompt: 提示文本

    Returns:
        MD5 hash 值（前8位）
    """
    return hashlib.md5(prompt.encode('utf-8')).hexdigest()[:8]


def load_checkpoint_from_dir(output_dir: str) -> Set[str]:
    """
    从输出目录加载所有断点续传信息

    Args:
        output_dir: 输出目录路径

    Returns:
        已处理的 prompt hash 集合
    """
    processed_hashes = set()
    output_path = Path(output_dir)

    if not output_path.exists():
        return processed_hashes

    # 读取目录下所有 .jsonl 文件
    jsonl_files = list(output_path.glob('*.jsonl'))

    if not jsonl_files:
        return processed_hashes

    print(f"[断点续传] 发现已存在的输出目录: {output_dir}")
    print(f"[断点续传] 正在读取已保存的结果...")

    total_read = 0
    for jsonl_file in jsonl_files:
        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        result = json.loads(line)
                        prompt_hash = result.get('prompt_hash')
                        if prompt_hash:
                            processed_hashes.add(prompt_hash)
                            total_read += 1
        except Exception as e:
            print(f"[警告] 读取文件 {jsonl_file} 失败: {e}")

    print(f"[断点续传] 从 {len(jsonl_files)} 个文件中读取到 {total_read} 条已处理数据")
    print(f"[断点续传] 将跳过 {len(processed_hashes)} 条重复数据")

    return processed_hashes


def load_checkpoint_from_file(output_file: str) -> Set[str]:
    """
    从单个文件加载断点续传信息（兼容旧版本）

    Args:
        output_file: 输出文件路径

    Returns:
        已处理的 prompt hash 集合
    """
    processed_hashes = set()
    output_path = Path(output_file)

    if not output_path.exists():
        return processed_hashes

    print(f"[断点续传] 发现已存在的输出文件: {output_file}")
    print(f"[断点续传] 正在读取已保存的结果...")

    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    result = json.loads(line)
                    prompt_hash = result.get('prompt_hash')
                    if prompt_hash:
                        processed_hashes.add(prompt_hash)

        print(f"[断点续传] 已处理 {len(processed_hashes)} 条数据，将跳过这些数据")
    except Exception as e:
        print(f"[警告] 读取已保存结果失败: {e}，将从头开始处理")
        processed_hashes = set()

    return processed_hashes


def load_checkpoint(output_file: str = None, output_dir: str = None) -> Set[str]:
    """
    加载断点续传信息（智能选择从文件或目录加载）

    优先级：
    1. 如果指定了 output_file，从该文件加载
    2. 否则，如果指定了 output_dir，从该目录加载
    3. 否则，返回空集合

    Args:
        output_file: 输出文件路径
        output_dir: 输出目录路径

    Returns:
        已处理的 prompt hash 集合
    """
    if output_file:
        return load_checkpoint_from_file(output_file)
    elif output_dir:
        return load_checkpoint_from_dir(output_dir)
    else:
        return set()
