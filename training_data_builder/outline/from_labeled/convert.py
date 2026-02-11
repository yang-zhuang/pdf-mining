"""
从标注数据构建训练数据

将 Label Studio 导出的标注数据转换为各种训练格式。
支持的数据格式：Alpaca, ShareGPT, Instruction, OpenAI Chat

使用方法：
    python -m training_data_builder.from_labeled.convert \
        --input ../labeled_data/outline/batch_01_labeled.json \
        --format alpaca \
        --output training_data/alpaca_batch_01.json
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from training_data_builder.utils import (
    TrainingFormat,
    load_json_file,
    convert_training_format,
    validate_training_data,
    split_train_val_test,
    save_training_data,
    filter_data_by_length,
    load_existing_hashes,
    filter_new_data
)


def convert_labeled_to_training(
    input_file: str,
    format: TrainingFormat = "alpaca",
    output_dir: str = None,
    output_file: str = None,
    split_ratio: str = None,  # "0.8,0.1,0.1"
    min_length: int = None,
    max_length: int = None,
    shuffle: bool = True,
    seed: int = 42
):
    """
    从标注数据转换为训练数据

    Args:
        input_file: 输入 JSON 文件路径（标注数据）
        format: 目标训练格式
        output_dir: 输出文件夹路径（可选，默认: ../../training_data/）
        output_file: 输出文件名（可选，默认: {format}_labeled_{timestamp}.json 或 .jsonl）
        split_ratio: 数据集拆分比例 "train,val,test"
        min_length: 响应最小长度（字符数）
        max_length: 响应最大长度（字符数）
        shuffle: 是否打乱数据
        seed: 随机种子
    """
    print(f"[开始] 从标注数据构建训练数据")
    print(f"[配置] 输入文件: {input_file}")
    print(f"[配置] 目标格式: {format}")

    # 设置默认输出目录
    if output_dir is None:
        output_dir = "../../training_data/"
    print(f"[配置] 输出文件夹: {output_dir}")

    if output_file:
        print(f"[配置] 输出文件名: {output_file}")

    if split_ratio:
        print(f"[配置] 数据拆分比例: {split_ratio}")

    if min_length or max_length:
        print(f"[配置] 长度过滤: min={min_length}, max={max_length}")

    # 步骤 1: 加载标注数据
    print(f"\n[步骤 1] 加载标注数据")
    data = load_json_file(input_file)

    # 步骤 2: 过滤数据
    if min_length or max_length:
        print(f"\n[步骤 2] 过滤数据")
        data = filter_data_by_length(data, min_length, max_length, field="response")

    # 步骤 3: 转换格式
    print(f"\n[步骤 3] 转换为 {format} 格式")
    training_data = convert_training_format(data, format=format)
    print(f"[信息] 转换完成，共 {len(training_data)} 条数据")

    # 步骤 4: 验证数据
    print(f"\n[步骤 4] 验证数据质量")
    validation_result = validate_training_data(training_data, format=format)

    if validation_result["errors"]:
        print(f"[错误] 发现 {len(validation_result['errors'])} 个错误:")
        for error in validation_result["errors"][:10]:  # 只显示前 10 个
            print(f"  - {error}")
        if len(validation_result["errors"]) > 10:
            print(f"  ... 还有 {len(validation_result['errors']) - 10} 个错误")

    if validation_result["warnings"]:
        print(f"[警告] 发现 {len(validation_result['warnings'])} 个警告:")
        for warning in validation_result["warnings"][:10]:  # 只显示前 10 个
            print(f"  - {warning}")
        if len(validation_result["warnings"]) > 10:
            print(f"  ... 还有 {len(validation_result['warnings']) - 10} 个警告")

    # 统计信息
    stats = validation_result["stats"]
    print(f"\n[统计]")
    print(f"  总数据: {stats['total']}")
    print(f"  空 prompt: {stats['empty_prompt']}")
    print(f"  空 response: {stats['empty_response']}")
    print(f"  过短: {stats['too_short']}")
    print(f"  过长: {stats['too_long']}")

    if not validation_result["valid"]:
        print(f"\n[错误] 数据验证失败，请修复错误后重试")
        return

    # 步骤 5: 拆分数据集（可选）
    if split_ratio:
        print(f"\n[步骤 5] 拆分数据集")

        # 过滤已存在的数据
        print(f"\n[步骤 5.1] 检查并过滤已存在的数据")
        existing_hashes = load_existing_hashes(output_dir, format)
        training_data, skipped_count = filter_new_data(training_data, format, existing_hashes)

        if skipped_count > 0:
            print(f"[信息] 跳过 {skipped_count} 条已存在的数据")

        # 如果没有新数据，提前返回
        if len(training_data) == 0:
            print(f"\n[跳过] 所有数据都已存在，无需保存")
            return

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
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        if output_file:
            # 从用户指定的文件名提取基础名称
            base_name = Path(output_file).stem
        else:
            # 生成默认基础文件名
            timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
            base_name = f"{format}_labeled_{timestamp}"

        # 根据格式确定文件扩展名
        ext = '.jsonl' if format == 'trl_grpo' else '.json'

        # 保存训练集
        train_file = output_dir_path / f"{base_name}_train{ext}"
        save_training_data(train_data, str(train_file), format)

        # 保存验证集
        val_file = output_dir_path / f"{base_name}_val{ext}"
        save_training_data(val_data, str(val_file), format)

        # 保存测试集
        test_file = output_dir_path / f"{base_name}_test{ext}"
        save_training_data(test_data, str(test_file), format)

        # 保存合并数据（可选，用于快速测试）
        merged_file = output_dir_path / f"{base_name}_all{ext}"
        save_training_data(training_data, str(merged_file), format)
    else:
        # 步骤 5: 保存数据（不拆分）

        # 过滤已存在的数据
        print(f"\n[步骤 5.1] 检查并过滤已存在的数据")
        existing_hashes = load_existing_hashes(output_dir, format)
        training_data, skipped_count = filter_new_data(training_data, format, existing_hashes)

        if skipped_count > 0:
            print(f"[信息] 跳过 {skipped_count} 条已存在的数据")

        # 如果没有新数据，提前返回
        if len(training_data) == 0:
            print(f"\n[跳过] 所有数据都已存在，无需保存")
            return

        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        if output_file:
            # 使用用户指定的文件名
            output_path = output_dir_path / output_file
            print(f"\n[步骤 5] 保存训练数据")
            save_training_data(training_data, str(output_path), format)
        else:
            # 生成默认输出文件名
            timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
            ext = '.jsonl' if format == 'trl_grpo' else '.json'
            default_filename = f"{format}_labeled_{timestamp}{ext}"
            default_output = output_dir_path / default_filename
            print(f"\n[步骤 5] 保存训练数据")
            save_training_data(training_data, str(default_output), format)

    print(f"\n[完成] 训练数据构建完成")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='从标注数据构建训练数据',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--input',
        type=str,
        default="../../../labeled_data/outline/project-1-at-2026-02-09-11-53-dc95da81.json",
        help='输入 JSON 文件路径（标注数据）'
    )

    parser.add_argument(
        '--format',
        type=str,
        default='trl_grpo',
        choices=['alpaca', 'sharegpt', 'instruction', 'openai', 'trl_grpo'],
        help='目标训练格式（默认: alpaca）'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='../../../training_data/outline',
        help='输出文件夹路径（默认：../../training_data/）'
    )

    parser.add_argument(
        '--output-file',
        type=str,
        default=None,
        help='输出文件名（默认：{format}_labeled_{timestamp}.json 或 .jsonl）'
    )

    parser.add_argument(
        '--split-ratio',
        type=str,
        default=None,
        help='数据集拆分比例，格式: "train,val,test"，例如: "0.8,0.1,0.1"'
    )

    parser.add_argument(
        '--min-length',
        type=int,
        default=None,
        help='响应最小长度（字符数），过滤过短的响应'
    )

    parser.add_argument(
        '--max-length',
        type=int,
        default=None,
        help='响应最大长度（字符数），过滤过长的响应'
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
    convert_labeled_to_training(
        input_file=args.input,
        format=args.format,
        output_dir=args.output_dir,
        output_file=args.output_file,
        split_ratio=args.split_ratio,
        min_length=args.min_length,
        max_length=args.max_length,
        shuffle=args.shuffle,
        seed=args.seed
    )


if __name__ == "__main__":
    main()
