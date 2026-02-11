"""
非思考模式 Token 分析

直接统计 prompt + response 的 token 数量，不需要调用模型推理。
适用于非思考模式的微调数据分析和 max_tokens 配置。

使用方法：
    python -m token_analysis.non_thinking.analyze --input ../labeled_data/outline/batch_01_labeled.json
"""

import argparse
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from token_analysis.utils import TokenAnalyzer, print_recommendations


def analyze_non_thinking_tokens(
    input_file: str,
    model_path: str = "Qwen/Qwen2.5-7B-Instruct",
    output_file: str = None
):
    """
    分析非思考模式数据的 token 数量

    Args:
        input_file: 输入 JSON 文件路径
        model_path: 模型路径（用于加载 tokenizer）
        output_file: 输出分析结果文件路径（可选）
    """
    print(f"[开始] 非思考模式 Token 分析")
    print(f"[配置] 输入文件: {input_file}")
    print(f"[配置] 模型路径: {model_path}")

    # 创建分析器
    analyzer = TokenAnalyzer(model_path=model_path)

    # 加载数据
    print(f"\n[步骤 1] 加载已标注数据")
    data = analyzer.load_labeled_data(input_file)

    # 分析每条数据
    print(f"\n[步骤 2] 计算 token 数量")
    results = []
    prompt_tokens_list = []
    response_tokens_list = []
    total_tokens_list = []

    for idx, item in enumerate(data, 1):
        if idx % 10 == 0:
            print(f"  进度: {idx}/{len(data)}")

        prompt = item.get('prompt', '')
        response = item.get('response', '')

        # 计算 token 数量
        token_info = analyzer.count_prompt_response_tokens(prompt, response)

        result = {
            "id": item.get('id', idx),
            "prompt_tokens": token_info["prompt_tokens"],
            "response_tokens": token_info["response_tokens"],
            "total_tokens": token_info["total_tokens"]
        }
        results.append(result)

        prompt_tokens_list.append(token_info["prompt_tokens"])
        response_tokens_list.append(token_info["response_tokens"])
        total_tokens_list.append(token_info["total_tokens"])

    print(f"  完成: {len(data)}/{len(data)}")

    # 计算统计信息
    print(f"\n[步骤 3] 计算统计信息")

    # Prompt 统计
    prompt_stats = analyzer.calculate_statistics(prompt_tokens_list)
    print(analyzer.format_statistics(prompt_stats, "Prompt Token 统计"))

    # Response 统计
    response_stats = analyzer.calculate_statistics(response_tokens_list)
    print(analyzer.format_statistics(response_stats, "Response Token 统计"))

    # Total 统计
    total_stats = analyzer.calculate_statistics(total_tokens_list)
    print(analyzer.format_statistics(total_stats, "Total Token 统计"))

    # 建议配置
    suggestions = analyzer.suggest_max_tokens(total_stats)
    print_recommendations(suggestions)

    # 保存结果
    if output_file:
        print(f"\n[步骤 4] 保存分析结果")
        analysis_result = {
            "mode": "non_thinking",
            "model_path": model_path,
            "input_file": input_file,
            "timestamp": str(Path.cwd()),
            "statistics": {
                "prompt": prompt_stats,
                "response": response_stats,
                "total": total_stats
            },
            "recommendations": suggestions,
            "details": results
        }
        analyzer.save_analysis_result(analysis_result, output_file)

    print(f"\n[完成] 分析完成")
    return {
        "prompt_stats": prompt_stats,
        "response_stats": response_stats,
        "total_stats": total_stats,
        "recommendations": suggestions
    }


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='非思考模式 Token 分析',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基础使用
  python -m token_analysis.non_thinking.analyze --input ../labeled_data/outline/batch_01_labeled.json

  # 指定模型
  python -m token_analysis.non_thinking.analyze --input data.json --model-path Qwen/Qwen2.5-14B-Instruct

  # 保存分析结果
  python -m token_analysis.non_thinking.analyze --input data.json --output token_analysis/result.json

  # 组合使用
  python -m token_analysis.non_thinking.analyze \\
    --input ../labeled_data/outline/batch_01_labeled.json \\
    --model-path Qwen/Qwen2.5-7B-Instruct \\
    --output ../token_analysis/non_thinking_batch_01.json
        """
    )

    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='输入 JSON 文件路径（已标注数据）'
    )

    parser.add_argument(
        '--model-path',
        type=str,
        default='Qwen/Qwen2.5-7B-Instruct',
        help='模型路径或 HuggingFace 模型名称（默认: Qwen/Qwen2.5-7B-Instruct）'
    )

    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='输出分析结果文件路径（可选）'
    )

    return parser.parse_args()


def main():
    """命令行入口"""
    args = parse_args()
    analyze_non_thinking_tokens(
        input_file=args.input,
        model_path=args.model_path,
        output_file=args.output
    )


if __name__ == "__main__":
    main()
