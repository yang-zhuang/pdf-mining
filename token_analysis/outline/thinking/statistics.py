"""
统计计算模块

处理 token 分析的统计计算功能
"""

import json
from pathlib import Path


def calculate_simple_stats(token_list):
    """
    计算简单的统计信息

    Args:
        token_list: token 数量列表

    Returns:
        统计信息字典
    """
    if not token_list:
        return {}

    sorted_tokens = sorted(token_list)
    return {
        "min": min(token_list),
        "max": max(token_list),
        "mean": sum(token_list) / len(token_list),
        "median": sorted_tokens[len(sorted_tokens) // 2],
        "p90": sorted_tokens[int(len(sorted_tokens) * 0.9)],
        "p95": sorted_tokens[int(len(sorted_tokens) * 0.95)],
        "p99": sorted_tokens[int(len(sorted_tokens) * 0.99)],
        "count": len(token_list)
    }


def print_stats(name, stats):
    """
    打印统计信息

    Args:
        name: 统计名称
        stats: 统计信息字典
    """
    if not stats:
        return

    print(f"\n[统计] {name}:")
    print(f"  最小值: {stats['min']:,}")
    print(f"  最大值: {stats['max']:,}")
    print(f"  平均值: {stats['mean']:,.1f}")
    print(f"  中位数: {stats['median']:,}")
    print(f"  P90: {stats['p90']:,}")
    print(f"  P95: {stats['p95']:,}")
    print(f"  P99: {stats['p99']:,}")


def generate_recommendations(input_stats, output_stats, total_stats):
    """
    生成 max_tokens 配置建议

    Args:
        input_stats: Input token 统计
        output_stats: Output token 统计
        total_stats: Total token 统计

    Returns:
        建议配置字典
    """
    # 基于 P99 的建议
    p99_input = input_stats.get('p99', 0)
    p99_output = output_stats.get('p99', 0)
    p99_total = total_stats.get('p99', 0)

    # 常见配置
    common_configs = [2048, 4096, 8192, 16384, 32768]

    def suggest_config(value):
        """推荐最接近的常见配置"""
        if value == 0:
            return 2048
        return min([c for c in common_configs if c >= value])

    suggested_input = suggest_config(p99_input)
    suggested_output = suggest_config(p99_output)
    suggested_total = suggest_config(p99_total)

    # 打印建议
    print(f"\n{'='*60}")
    print("[建议] Max Tokens 配置")
    print(f"{'='*60}")

    print(f"\n基于 P99 分位数的建议:")
    print(f"  Input max_tokens:  {suggested_input:,}  (P99 实际值: {p99_input:,})")
    print(f"  Output max_tokens: {suggested_output:,}  (P99 实际值: {p99_output:,})")
    print(f"  Total max_tokens:  {suggested_total:,}  (P99 实际值: {p99_total:,})")

    return {
        "input_p99": p99_input,
        "output_p99": p99_output,
        "total_p99": p99_total,
        "suggested_input": suggested_input,
        "suggested_output": suggested_output,
        "suggested_total": suggested_total
    }


def save_summary(output_file, config, stats, recommendations):
    """
    保存统计摘要

    Args:
        output_file: 输出文件路径（JSONL）
        config: 配置信息
        stats: 统计信息
        recommendations: 建议配置
    """
    # 生成统计摘要文件名
    output_path = Path(output_file)
    summary_file = output_path.parent / f"{output_path.stem}_summary.json"

    analysis_summary = {
        "mode": "thinking",
        "config": config,
        "statistics": stats,
        "recommendations": recommendations
    }

    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_summary, f, ensure_ascii=False, indent=2)

    print(f"\n[成功] 统计摘要已保存到: {summary_file}")
    print(f"[信息] 详细结果已实时保存到: {output_file} (JSONL 格式)")
