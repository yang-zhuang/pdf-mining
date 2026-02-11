"""
思考模式 Token 分析 - 入口文件

通过 vLLM 调用思考模型，获取思考内容和响应，然后统计 token 数量。

使用方法：
    python -m token_analysis.thinking.analyze --input data.jsonl --use-batch
"""

import argparse
from pathlib import Path

from token_analysis.thinking.processor import ThinkingAnalyzer


def generate_output_path(input_file: str) -> str:
    """
    根据输入文件生成输出文件路径

    Args:
        input_file: 输入文件路径

    Returns:
        输出文件路径
    """
    input_path = Path(input_file)
    input_stem = input_path.stem

    # 输出目录
    output_dir = Path("token_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 输出文件名：thinking_analysis_{input_stem}.jsonl
    output_file = output_dir / f"thinking_analysis_{input_stem}.jsonl"

    return str(output_file)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='思考模式 Token 分析',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基础使用（单个调用模式）
  python -m token_analysis.thinking.analyze \\
    --input ../../training_data/trl_grpo_labeled_2026_02_09_18_12_21.jsonl

  # 使用批量并发模式（推荐）
  python -m token_analysis.thinking.analyze \\
    --input ../../training_data/trl_grpo_labeled_2026_02_09_18_12_21.jsonl \\
    --use-batch \\
    --max-concurrency 5

  # 指定 vLLM 服务地址
  python -m token_analysis.thinking.analyze \\
    --input data.jsonl \\
    --vllm-url http://192.168.1.100:8000/v1 \\
    --model-name Qwen3-4B-AWQ

  # 限制分析数量（测试用）
  python -m token_analysis.thinking.analyze \\
    --input data.jsonl \\
    --use-batch \\
    --limit 10

  # 完整示例
  python -m token_analysis.thinking.analyze \\
    --input ../../training_data/trl_grpo_labeled_2026_02_09_18_12_21.jsonl \\
    --vllm-url http://localhost:8000/v1 \\
    --model-name Qwen3-4B-AWQ \\
    --max-tokens 15000 \\
    --use-batch \\
    --max-concurrency 5 \\
    --limit 100

注意:
  - 确保 vLLM 服务正在运行
  - 推荐使用 --use-batch 批量模式以提高速度
  - 支持断点续传，可以随时中断和继续
  - 结果实时保存到 token_analysis/ 目录
        """
    )

    parser.add_argument(
        '--input',
        type=str,
        default='../../training_data/trl_grpo_labeled_2026_02_09_18_12_21.jsonl',
        help='输入 JSON/JSONL 文件路径（训练数据）'
    )

    parser.add_argument(
        '--vllm-url',
        type=str,
        default='http://localhost:8000/v1',
        help='vLLM 服务地址（默认: http://localhost:8000/v1）'
    )

    parser.add_argument(
        '--model-name',
        type=str,
        default='Qwen3-4B-AWQ',
        help='模型名称（默认: Qwen3-4B-AWQ）'
    )

    parser.add_argument(
        '--max-tokens',
        type=int,
        default=15000,
        help='推理时的最大生成 token 数（默认: 15000）'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='限制分析的数据数量（用于测试）'
    )

    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='输出文件路径（默认：token_analysis/thinking_analysis_{input_stem}.jsonl）'
    )

    parser.add_argument(
        '--use-batch',
        action='store_true',
        default=False,
        help='使用批量并发推理模式（推荐，大幅提升速度）'
    )

    parser.add_argument(
        '--max-concurrency',
        type=int,
        default=5,
        help='批量推理时的最大并发数（默认: 5）'
    )

    return parser.parse_args()


def main():
    """命令行入口"""
    args = parse_args()

    # 设置默认输出文件
    if args.output is None:
        output_file = generate_output_path(args.input)
    else:
        output_file = args.output

    # 创建分析器
    analyzer = ThinkingAnalyzer(
        vllm_url=args.vllm_url,
        model_name=args.model_name,
        max_tokens=args.max_tokens,
        use_batch=args.use_batch,
        max_concurrency=args.max_concurrency
    )

    # 执行分析
    analyzer.analyze(
        input_file=args.input,
        output_file=output_file,
        limit=args.limit
    )


if __name__ == "__main__":
    main()
