"""
Token 分析共享工具

提供 tokenizer 加载、token 计算、统计分析等通用功能
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Union
import statistics
from datetime import datetime


class TokenAnalyzer:
    """
    Token 分析器基类

    提供通用的 tokenizer 加载、token 计算和统计分析功能
    """

    def __init__(self, model_path: str = "Qwen/Qwen2.5-7B-Instruct"):
        """
        初始化分析器

        Args:
            model_path: 模型路径或 HuggingFace 模型名称
        """
        self.model_path = model_path
        self.tokenizer = None
        self._load_tokenizer()

    def _load_tokenizer(self):
        """延迟加载 tokenizer（避免不使用时加载）"""
        try:
            from transformers import AutoTokenizer
            print(f"[信息] 加载 tokenizer: {self.model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            print(f"[信息] Tokenizer 加载成功")
        except ImportError:
            print("[错误] 需要安装 transformers 库")
            print("[提示] 运行: pip install transformers")
            sys.exit(1)
        except Exception as e:
            print(f"[错误] 加载 tokenizer 失败: {e}")
            sys.exit(1)

    def count_tokens(self, text: str) -> int:
        """
        计算文本的 token 数量

        Args:
            text: 输入文本

        Returns:
            token 数量
        """
        if not text:
            return 0
        tokens = self.tokenizer.encode(text, add_special_tokens=False)
        return len(tokens)

    def count_prompt_response_tokens(self, prompt: str, response: str) -> Dict[str, int]:
        """
        计算 prompt 和 response 的 token 数量

        Args:
            prompt: 提示文本
            response: 响应文本

        Returns:
            {"prompt_tokens": int, "response_tokens": int, "total_tokens": int}
        """
        prompt_tokens = self.count_tokens(prompt)
        response_tokens = self.count_tokens(response)
        return {
            "prompt_tokens": prompt_tokens,
            "response_tokens": response_tokens,
            "total_tokens": prompt_tokens + response_tokens
        }

    def count_thinking_tokens(self, prompt: str, thinking: str, response: str) -> Dict[str, int]:
        """
        计算 prompt + thinking + response 的 token 数量

        Args:
            prompt: 提示文本
            thinking: 思考内容
            response: 响应文本

        Returns:
            {"prompt_tokens": int, "thinking_tokens": int, "response_tokens": int, "total_tokens": int}
        """
        prompt_tokens = self.count_tokens(prompt)
        thinking_tokens = self.count_tokens(thinking)
        response_tokens = self.count_tokens(response)
        return {
            "prompt_tokens": prompt_tokens,
            "thinking_tokens": thinking_tokens,
            "response_tokens": response_tokens,
            "total_tokens": prompt_tokens + thinking_tokens + response_tokens
        }

    def calculate_statistics(self, token_counts: List[int]) -> Dict[str, Union[int, float]]:
        """
        计算 token 数量的统计信息

        Args:
            token_counts: token 数量列表

        Returns:
            包含各种统计指标的字典
        """
        if not token_counts:
            return {}

        sorted_counts = sorted(token_counts)
        n = len(sorted_counts)

        return {
            "count": n,
            "min": min(sorted_counts),
            "max": max(sorted_counts),
            "mean": statistics.mean(sorted_counts),
            "median": statistics.median(sorted_counts),
            "mode": statistics.mode(sorted_counts) if n > 0 else 0,
            "std": statistics.stdev(sorted_counts) if n > 1 else 0,
            "p25": sorted_counts[int(n * 0.25)] if n >= 4 else sorted_counts[0],
            "p50": sorted_counts[int(n * 0.50)] if n >= 2 else sorted_counts[0],
            "p75": sorted_counts[int(n * 0.75)] if n >= 4 else sorted_counts[-1],
            "p90": sorted_counts[int(n * 0.90)] if n >= 10 else sorted_counts[-1],
            "p95": sorted_counts[int(n * 0.95)] if n >= 20 else sorted_counts[-1],
            "p99": sorted_counts[int(n * 0.99)] if n >= 100 else sorted_counts[-1],
        }

    def format_statistics(self, stats: Dict[str, Union[int, float]], title: str = "Token 统计") -> str:
        """
        格式化输出统计信息

        Args:
            stats: 统计信息字典
            title: 标题

        Returns:
            格式化的字符串
        """
        lines = [
            f"\n{'='*60}",
            f"{title}",
            f"{'='*60}",
            f"样本数量: {stats.get('count', 0)}",
            f"",
            f"最小值: {stats.get('min', 0):,} tokens",
            f"最大值: {stats.get('max', 0):,} tokens",
            f"平均值: {stats.get('mean', 0):.1f} tokens",
            f"中位数: {stats.get('median', 0):.1f} tokens",
            f"标准差: {stats.get('std', 0):.1f} tokens",
            f"",
            f"百分位数:",
            f"  P25: {stats.get('p25', 0):,} tokens",
            f"  P50: {stats.get('p50', 0):,} tokens",
            f"  P75: {stats.get('p75', 0):,} tokens",
            f"  P90: {stats.get('p90', 0):,} tokens",
            f"  P95: {stats.get('p95', 0):,} tokens",
            f"  P99: {stats.get('p99', 0):,} tokens",
            f"{'='*60}\n"
        ]
        return "\n".join(lines)

    def suggest_max_tokens(self, stats: Dict[str, Union[int, float]], safety_factor: float = 1.2) -> Dict[str, int]:
        """
        根据统计信息建议 max_tokens 配置

        Args:
            stats: 统计信息字典
            safety_factor: 安全系数（默认 1.2，即预留 20% 余量）

        Returns:
            建议的 max_tokens 配置
        """
        p99 = stats.get('p99', stats.get('max', 0))
        max_val = stats.get('max', 0)

        # 基于 P99 的建议（覆盖 99% 的数据）
        suggested_p99 = int(p99 * safety_factor)

        # 基于 max 的建议（覆盖所有数据）
        suggested_max = int(max_val * safety_factor)

        # 常用配置（2048, 4096, 8192, 16384, 32768）
        common_configs = [2048, 4096, 8192, 16384, 32768]

        # 找到最接近的常用配置
        recommended_p99 = min([c for c in common_configs if c >= suggested_p99], default=32768)
        recommended_max = min([c for c in common_configs if c >= suggested_max], default=32768)

        return {
            "p99_based": recommended_p99,
            "max_based": recommended_max,
            "raw_p99": p99,
            "raw_max": max_val,
            "suggested_p99": suggested_p99,
            "suggested_max": suggested_max,
        }

    def load_labeled_data(self, input_file: str) -> List[Dict]:
        """
        加载已标注数据

        Args:
            input_file: JSON 文件路径

        Returns:
            数据列表
        """
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"文件不存在: {input_file}")

        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("JSON 文件格式错误：应为数组")

        print(f"[信息] 成功加载 {len(data)} 条数据")
        return data

    def load_jsonl_file(self, input_file: str) -> List[Dict]:
        """
        加载 JSONL 文件（每行一个 JSON 对象）

        Args:
            input_file: JSONL 文件路径

        Returns:
            数据列表
        """
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"文件不存在: {input_file}")

        data = []
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    data.append(json.loads(line))

        print(f"[信息] 成功加载 {len(data)} 条数据")
        return data

    def save_analysis_result(self, result: Dict, output_file: str):
        """
        保存分析结果

        Args:
            result: 分析结果字典
            output_file: 输出文件路径
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"[成功] 分析结果已保存到: {output_file}")


def print_recommendations(suggestions: Dict[str, int]):
    """
    打印 max_tokens 配置建议

    Args:
        suggestions: 建议配置字典
    """
    lines = [
        f"\n{'='*60}",
        "Max Tokens 配置建议",
        f"{'='*60}",
        "",
        f"数据统计:",
        f"  - 实际最大值: {suggestions['raw_max']:,} tokens",
        f"  - P99 值: {suggestions['raw_p99']:,} tokens",
        "",
        f"建议配置（已预留 20% 安全余量）:",
        f"  - 基于 P99: {suggestions['suggested_p99']:,} tokens",
        f"  - 基于 Max: {suggestions['suggested_max']:,} tokens",
        "",
        f"推荐配置（向上取整到常用值）:",
        f"  - 保守配置（覆盖 99% 数据）: {suggestions['p99_based']:,} tokens",
        f"  - 完整配置（覆盖所有数据）: {suggestions['max_based']:,} tokens",
        "",
        f"使用示例:",
        f"  vLLM: --max-model-len {suggestions['p99_based']}",
        f"  Transformer: max_tokens={suggestions['p99_based']}",
        f"{'='*60}\n"
    ]
    print("\n".join(lines))
