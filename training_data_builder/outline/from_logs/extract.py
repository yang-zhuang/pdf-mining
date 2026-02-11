"""
从日志数据构建训练数据

直接从 LLM 调用日志中提取成功的 prompt 和 response 作为训练数据。
适用于使用顶尖模型生成的日志数据。

使用方法：
    python -m training_data_builder.from_logs.extract \
        --log-dir ../outline_extractor/logs/llm_calls \
        --format alpaca \
        --output training_data/alpaca_from_logs.json
"""

import argparse
import sys
from pathlib import Path
from typing import List

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from training_data_builder.utils import (
    TrainingFormat,
    convert_training_format,
    validate_training_data,
    split_train_val_test,
    save_training_data,
    deduplicate_data,
    filter_data_by_length
)


def read_log_files(log_dir: str) -> List[dict]:
    """
    读取日志目录下的所有 .jsonl 文件

    Args:
        log_dir: 日志目录路径

    Returns:
        所有日志记录的列表
    """
    log_path = Path(log_dir)

    if not log_path.exists():
        raise FileNotFoundError(f"日志目录不存在: {log_dir}")

    # 获取所有 .jsonl 文件（使用集合去重）
    jsonl_files = list(set(log_path.glob('*.jsonl')) | set(log_path.glob('*.JSONL')))
    jsonl_files.sort()

    if not jsonl_files:
        raise ValueError(f"日志目录中没有找到 .jsonl 文件: {log_dir}")

    print(f"[信息] 找到 {len(jsonl_files)} 个日志文件")

    all_records = []
    for jsonl_file in jsonl_files:
        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                        all_records.append(record)
                    except json.JSONDecodeError as e:
                        print(f"[警告] 跳过无效的 JSON 行: {e}")
                        continue
        except Exception as e:
            print(f"[警告] 读取日志文件 {jsonl_file} 失败: {e}")
            continue

    print(f"[信息] 共读取 {len(all_records)} 条日志记录")
    return all_records


def extract_prompt_response_from_log(record: dict) -> dict:
    """
    从日志记录中提取 prompt 和 response

    Args:
        record: 日志记录

    Returns:
        {"prompt": str, "response": str} 或 None
    """
    # 只处理成功的记录
    if not record.get('success'):
        return None

    # 提取 response 字段
    response_data = record.get('response')
    if not response_data or not isinstance(response_data, dict):
        return None

    # 提取 LLM 的回答
    answer = response_data.get('answer')
    if not answer:
        return None

    # 提取 prompt（优先使用原始 prompt，如果没有则使用 current_batch_content）
    prompt = None
    if response_data.get('prompt'):
        prompt = response_data.get('prompt')
    elif record.get('current_batch_content'):
        prompt = record.get('current_batch_content')

    if not prompt:
        return None

    return {
        'prompt': prompt,
        'response': answer
    }


def extract_logs_to_training(
    log_dir: str,
    format: TrainingFormat = "alpaca",
    output_file: str = None,
    limit: int = None,
    deduplicate: bool = True,
    dedup_field: str = "prompt",
    min_length: int = None,
    max_length: int = None,
    split_ratio: str = None,
    shuffle: bool = True,
    seed: int = 42
):
    """
    从日志数据提取训练数据

    Args:
        log_dir: 日志目录路径
        format: 目标训练格式
        output_file: 输出文件路径
        limit: 限制提取的数据数量
        deduplicate: 是否去重
        dedup_field: 去重字段
        min_length: 响应最小长度（字符数）
        max_length: 响应最大长度（字符数）
        split_ratio: 数据集拆分比例
        shuffle: 是否打乱数据
        seed: 随机种子
    """
    print(f"[开始] 从日志数据构建训练数据")
    print(f"[配置] 日志目录: {log_dir}")
    print(f"[配置] 目标格式: {format}")

    if output_file:
        print(f"[配置] 输出文件: {output_file}")

    if limit:
        print(f"[配置] 数据限制: {limit} 条")

    # 步骤 1: 读取日志文件
    print(f"\n[步骤 1] 读取日志文件")
    all_records = read_log_files(log_dir)

    # 步骤 2: 提取 prompt 和 response
    print(f"\n[步骤 2] 提取 prompt 和 response")
    extracted_data = []

    for record in all_records:
        if limit and len(extracted_data) >= limit:
            break

        data = extract_prompt_response_from_log(record)
        if data:
            extracted_data.append(data)

    print(f"[信息] 成功提取 {len(extracted_data)} 条数据（从 {len(all_records)} 条日志记录）")

    if not extracted_data:
        print(f"[错误] 没有提取到有效数据")
        return

    # 步骤 3: 去重（可选）
    if deduplicate:
        print(f"\n[步骤 3] 数据去重（基于 {dedup_field} 字段）")
        extracted_data = deduplicate_data(extracted_data, key_field=dedup_field)

    # 步骤 4: 过滤数据（可选）
    if min_length or max_length:
        print(f"\n[步骤 4] 过滤数据")
        extracted_data = filter_data_by_length(
            extracted_data,
            min_length=min_length,
            max_length=max_length,
            field="response"
        )

    # 步骤 5: 转换格式
    print(f"\n[步骤 5] 转换为 {format} 格式")
    training_data = convert_training_format(extracted_data, format=format)
    print(f"[信息] 转换完成，共 {len(training_data)} 条数据")

    # 步骤 6: 验证数据
    print(f"\n[步骤 6] 验证数据质量")
    validation_result = validate_training_data(training_data, format=format)

    if validation_result["errors"]:
        print(f"[错误] 发现 {len(validation_result['errors'])} 个错误:")
        for error in validation_result["errors"][:10]:
            print(f"  - {error}")

    if validation_result["warnings"]:
        print(f"[警告] 发现 {len(validation_result['warnings'])} 个警告:")
        for warning in validation_result["warnings"][:10]:
            print(f"  - {warning}")

    # 统计信息
    stats = validation_result["stats"]
    print(f"\n[统计]")
    print(f"  总数据: {stats['total']}")
    print(f"  空 prompt: {stats['empty_prompt']}")
    print(f"  空 response: {stats['empty_response']}")

    if not validation_result["valid"]:
        print(f"\n[错误] 数据验证失败，请修复错误后重试")
        return

    # 步骤 7: 拆分数据集（可选）
    if split_ratio:
        print(f"\n[步骤 7] 拆分数据集")
        ratios = [float(r.strip()) for r in split_ratio.split(',')]
        if len(ratios) != 3:
            raise ValueError(f"split_ratio 格式错误，应为 'train,val,test'，例如: '0.8,0.1,0.1'")

        train_data, val_data, test_data = split_train_val_test(
            training_data,
            train_ratio=ratios[0],
            val_ratio=ratios[1],
            test_ratio=ratios[2],
            shuffle=shuffle,
            seed=seed
        )

        # 保存拆分后的数据
        if output_file:
            output_path = Path(output_file)
            base_name = output_path.stem
            output_dir = output_path.parent

            # 保存训练集
            train_file = output_dir / f"{base_name}_train.json"
            save_training_data(train_data, str(train_file), format)

            # 保存验证集
            val_file = output_dir / f"{base_name}_val.json"
            save_training_data(val_data, str(val_file), format)

            # 保存测试集
            test_file = output_dir / f"{base_name}_test.json"
            save_training_data(test_data, str(test_file), format)

            # 保存合并数据
            merged_file = output_dir / f"{base_name}_all.json"
            save_training_data(training_data, str(merged_file), format)
    else:
        # 步骤 7: 保存数据（不拆分）
        if output_file:
            print(f"\n[步骤 7] 保存训练数据")
            save_training_data(training_data, output_file, format)
        else:
            # 生成默认输出文件名
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_output = f"training_data/{format}_from_logs_{timestamp}.json"
            print(f"\n[步骤 7] 保存训练数据")
            save_training_data(training_data, default_output, format)

    print(f"\n[完成] 训练数据构建完成")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='从日志数据构建训练数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基础使用
  python -m training_data_builder.from_logs.extract \\
    --log-dir ../outline_extractor/logs/llm_calls \\
    --format alpaca

  # 限制数据量
  python -m training_data_builder.from_logs.extract \\
    --log-dir ../outline_extractor/logs/llm_calls \\
    --format sharegpt \\
    --limit 1000

  # 去重和过滤
  python -m training_data_builder.from_logs.extract \\
    --log-dir ../outline_extractor/logs/llm_calls \\
    --format alpaca \\
    --deduplicate \\
    --min-length 100 \\
    --max-length 10000 \\
    --output training_data/alpaca_from_logs.json

  # 拆分数据集
  python -m training_data_builder.from_logs.extract \\
    --log-dir ../outline_extractor/logs/llm_calls \\
    --format alpaca \\
    --split-ratio 0.8,0.1,0.1 \\
    --output training_data/alpaca_from_logs.json

  # 组合使用
  python -m training_data_builder.from_logs.extract \\
    --log-dir ../outline_extractor/logs/llm_calls \\
    --format alpaca \\
    --limit 5000 \\
    --deduplicate \\
    --min-length 50 \\
    --max-length 8000 \\
    --split-ratio 0.8,0.1,0.1 \\
    --shuffle \\
    --seed 42 \\
    --output training_data/alpaca_from_logs.json

注意:
  - 只提取成功（success=True）的日志记录
  - 自动跳过缺少 prompt 或 response 的记录
  - 使用 --deduplicate 避免重复数据
        """
    )

    parser.add_argument(
        '--log-dir',
        type=str,
        required=True,
        help='日志目录路径'
    )

    parser.add_argument(
        '--format',
        type=str,
        default='alpaca',
        choices=['alpaca', 'sharegpt', 'instruction', 'openai'],
        help='目标训练格式（默认: alpaca）'
    )

    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='输出文件路径（默认：training_data/{format}_from_logs_{timestamp}.json）'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='限制提取的数据数量'
    )

    parser.add_argument(
        '--deduplicate',
        action='store_true',
        default=True,
        help='是否去重（默认: True）'
    )

    parser.add_argument(
        '--no-deduplicate',
        action='store_false',
        dest='deduplicate',
        help='禁用去重'
    )

    parser.add_argument(
        '--dedup-field',
        type=str,
        default='prompt',
        help='去重字段（默认: prompt）'
    )

    parser.add_argument(
        '--min-length',
        type=int,
        default=None,
        help='响应最小长度（字符数）'
    )

    parser.add_argument(
        '--max-length',
        type=int,
        default=None,
        help='响应最大长度（字符数）'
    )

    parser.add_argument(
        '--split-ratio',
        type=str,
        default=None,
        help='数据集拆分比例，格式: "train,val,test"，例如: "0.8,0.1,0.1"'
    )

    parser.add_argument(
        '--shuffle',
        action='store_true',
        default=True,
        help='是否打乱数据（默认: True）'
    )

    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='随机种子（默认: 42）'
    )

    return parser.parse_args()


def main():
    """命令行入口"""
    args = parse_args()
    extract_logs_to_training(
        log_dir=args.log_dir,
        format=args.format,
        output_file=args.output,
        limit=args.limit,
        deduplicate=args.deduplicate,
        dedup_field=args.dedup_field,
        min_length=args.min_length,
        max_length=args.max_length,
        split_ratio=args.split_ratio,
        shuffle=args.shuffle,
        seed=args.seed
    )


if __name__ == "__main__":
    main()
