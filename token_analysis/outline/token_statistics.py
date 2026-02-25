"""
Token统计脚本 - 用于统计SFT/GRPO/EVAL数据的token长度
"""

import argparse
import json
import os
from glob import glob
from collections import defaultdict
# 兼容不同来源的 tokenizer
try:
    from transformers import AutoTokenizer
    USING_TRANSFORMERS = True
except Exception as e:
    try:
        from modelscope import AutoModelForCausalLM, AutoTokenizer
        USING_TRANSFORMERS = False
    except ImportError:
        raise ImportError(
            "无法导入 AutoTokenizer。请安装 transformers 或 modelscope:\n"
            "  pip install transformers\n"
            "  或\n"
            "  pip install modelscope"
        )


# Token加载（全局缓存，避免重复加载）
_tokenizer = None


def get_tokenizer(model_name="Qwen/Qwen3-0.6B"):
    """获取tokenizer实例（单例模式）"""
    global _tokenizer
    if _tokenizer is None:
        print(f"Loading tokenizer: {model_name}")
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
    return _tokenizer


def apply_chat_template(messages, enable_thinking=True):
    """应用chat template获取文本"""
    tokenizer = get_tokenizer()

    if USING_TRANSFORMERS:
        # Transformers 方式（不包含 enable_thinking 参数）
        try:
            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
        except Exception:
            # 如果 apply_chat_template 不可用，手动构建
            text = ""
            for msg in messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                text += f"<|im_start|>{role}\n{content}<|im_end|>\n"
            text += "<|im_start|>assistant\n"
    else:
        # ModelScope 方式
        try:
            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=enable_thinking
            )
        except TypeError:
            # 旧版本可能不支持 enable_thinking
            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
        except Exception:
            # 回退方案：手动构建
            text = ""
            for msg in messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                text += f"<|im_start|>{role}\n{content}<|im_end|>\n"
            text += "<|im_start|>assistant\n"

    return text


def count_tokens(text):
    """统计文本的token数量"""
    tokenizer = get_tokenizer()
    return len(tokenizer.encode(text))


def load_sft_data(filepath):
    """加载SFT数据"""
    samples = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())
            conversations = data.get('conversations', [])
            if conversations:
                samples.append({
                    'type': 'sft',
                    'data': data
                })
    return samples


def load_grpo_data(filepath):
    """加载GRPO数据"""
    samples = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())
            prompt = data.get('prompt', [])
            if isinstance(prompt, list) and len(prompt) > 0:
                samples.append({
                    'type': 'grpo',
                    'data': data
                })
            elif isinstance(prompt, str):
                samples.append({
                    'type': 'grpo',
                    'data': data
                })
    return samples


def load_eval_data(filepath):
    """加载EVAL数据"""
    samples = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())
            samples.append({
                'type': 'eval',
                'data': data
            })
    return samples


def get_sft_text(sample):
    """获取SFT样本的文本（输入+输出）"""
    data = sample['data']
    conversations = data.get('conversations', [])
    if not conversations:
        return "", ""

    # 分离输入和输出
    input_messages = []
    output_messages = []

    for i, msg in enumerate(conversations):
        if i % 2 == 0:  # user消息
            input_messages.append(msg)
        else:  # assistant消息
            output_messages.append(msg)

    # 应用template
    input_text = apply_chat_template(input_messages, enable_thinking=True)
    output_text = ""
    for msg in output_messages:
        output_text += msg.get('content', '')

    return input_text, output_text


def get_grpo_text(sample):
    """获取GRPO样本的文本（输入: prompt，输出: thinking + solution）"""
    data = sample['data']
    prompt = data.get('prompt', [])

    # 处理输入文本
    if isinstance(prompt, str):
        input_text = prompt
    elif isinstance(prompt, list) and len(prompt) > 0:
        input_text = apply_chat_template(prompt, enable_thinking=True)
    else:
        input_text = ""

    # 处理输出文本（thinking + solution）
    thinking = data.get('thinking', '')
    solution = data.get('solution', '')
    output_text = thinking + solution

    return input_text, output_text


def get_eval_text(sample):
    """获取EVAL样本的文本（输入: prompt，输出: thinking + answer）"""
    data = sample['data']
    prompt = data.get('prompt', [])

    # 处理输入文本
    if isinstance(prompt, str):
        input_text = prompt
    elif isinstance(prompt, list) and len(prompt) > 0:
        input_text = apply_chat_template(prompt, enable_thinking=True)
    else:
        input_text = ""

    # 处理输出文本（thinking + answer）
    thinking = data.get('thinking', '')
    answer = data.get('answer', '')
    output_text = thinking + answer

    return input_text, output_text


def calculate_statistics(token_counts):
    """计算统计信息"""
    if not token_counts:
        return {}

    sorted_counts = sorted(token_counts)
    n = len(sorted_counts)

    total = sum(token_counts)
    mean = total / n
    median = sorted_counts[n // 2] if n % 2 == 1 else (sorted_counts[n // 2 - 1] + sorted_counts[n // 2]) / 2

    # 分位数
    p10 = sorted_counts[int(n * 0.1)]
    p25 = sorted_counts[int(n * 0.25)]
    p50 = sorted_counts[int(n * 0.5)]
    p75 = sorted_counts[int(n * 0.75)]
    p90 = sorted_counts[int(n * 0.9)]
    p95 = sorted_counts[int(n * 0.95)]
    p99 = sorted_counts[int(n * 0.99)]

    return {
        'count': n,
        'total': total,
        'mean': mean,
        'median': median,
        'min': min(token_counts),
        'max': max(token_counts),
        'p10': p10,
        'p25': p25,
        'p50': p50,
        'p75': p75,
        'p90': p90,
        'p95': p95,
        'p99': p99,
    }


def print_statistics(stats, label):
    """打印统计信息"""
    print(f"\n{'=' * 60}")
    print(f"{label} Token统计")
    print(f"{'=' * 60}")
    print(f"样本数:        {stats['count']:,}")
    print(f"总Token数:     {stats['total']:,}")
    print(f"平均Token数:   {stats['mean']:.2f}")
    print(f"中位数Token数: {stats['median']:.2f}")
    print(f"最小值:        {stats['min']:,}")
    print(f"最大值:        {stats['max']:,}")
    print(f"\n分位数:")
    print(f"  P10:  {stats['p10']:,.0f}")
    print(f"  P25:  {stats['p25']:,.0f}")
    print(f"  P50:  {stats['p50']:,.0f}")
    print(f"  P75:  {stats['p75']:,.0f}")
    print(f"  P90:  {stats['p90']:,.0f}")
    print(f"  P95:  {stats['p95']:,.0f}")
    print(f"  P99:  {stats['p99']:,.0f}")


def find_data_files(data_dir, data_types):
    """查找数据文件"""
    files_by_type = defaultdict(list)

    pattern_map = {
        'sft': 'sft_labeled_*.jsonl',
        'grpo': 'grpo_labeled_*.jsonl',
        'eval': 'eval_labeled_*.jsonl',
    }

    for dtype in data_types:
        if dtype not in pattern_map:
            print(f"警告: 未知的数据类型 '{dtype}'，跳过")
            continue

        pattern = os.path.join(data_dir, pattern_map[dtype])
        matched_files = glob(pattern)

        if matched_files:
            files_by_type[dtype].extend(matched_files)
        else:
            print(f"警告: 未找到类型为 '{dtype}' 的文件，模式: {pattern}")

    return dict(files_by_type)


def main():
    parser = argparse.ArgumentParser(description='统计SFT/GRPO/EVAL数据的token长度')
    parser.add_argument(
        '--data-dir',
        type=str,
        default='../../training_data/outline/three_column',
        help='数据文件目录'
    )
    parser.add_argument(
        '--types',
        type=str,
        nargs='+',
        choices=['sft', 'grpo', 'eval'],
        default=['sft', 'grpo', 'eval'],
        help='要统计的数据类型（可多选）'
    )
    parser.add_argument(
        '--model-name',
        type=str,
        default='Qwen/Qwen3-0.6B',
        help='模型名称，用于加载tokenizer'
    )
    parser.add_argument(
        '--enable-thinking',
        action='store_true',
        default=True,
        help='是否启用thinking模式（默认启用）'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细进度'
    )

    args = parser.parse_args()

    # 预加载tokenizer
    get_tokenizer(args.model_name)

    # 查找数据文件
    files_by_type = find_data_files(args.data_dir, args.types)

    if not files_by_type:
        print("错误: 未找到任何数据文件")
        return

    # 按类型加载数据
    loaders = {
        'sft': load_sft_data,
        'grpo': load_grpo_data,
        'eval': load_eval_data,
    }

    text_getters = {
        'sft': get_sft_text,
        'grpo': get_grpo_text,
        'eval': get_eval_text,
    }

    # 收集所有token计数
    all_input_tokens = defaultdict(list)
    all_output_tokens = defaultdict(list)
    all_total_tokens = defaultdict(list)

    for dtype, files in files_by_type.items():
        print(f"\n处理 {dtype} 数据...")
        loader = loaders[dtype]
        text_getter = text_getters[dtype]

        total_samples = 0
        for filepath in files:
            print(f"  加载文件: {filepath}")
            samples = loader(filepath)
            total_samples += len(samples)

            for i, sample in enumerate(samples):
                input_text, output_text = text_getter(sample)

                if input_text:
                    input_tokens = count_tokens(input_text)
                    all_input_tokens[dtype].append(input_tokens)
                    all_total_tokens[dtype].append(input_tokens)

                if output_text:
                    output_tokens = count_tokens(output_text)
                    all_output_tokens[dtype].append(output_tokens)
                    all_total_tokens[dtype][-1] += output_tokens

                if args.verbose and (i + 1) % 100 == 0:
                    print(f"    已处理 {i + 1} 个样本...")

        print(f"  共加载 {total_samples} 个样本")

    # 打印统计结果
    print("\n" + "=" * 60)
    print("总体统计汇总")
    print("=" * 60)

    for dtype in sorted(all_total_tokens.keys()):
        # 总token统计
        if all_total_tokens[dtype]:
            stats = calculate_statistics(all_total_tokens[dtype])
            print_statistics(stats, f"{dtype.upper()} - 总Token")

        # 输入token统计（仅SFT有输出）
        if all_input_tokens[dtype]:
            stats = calculate_statistics(all_input_tokens[dtype])
            print_statistics(stats, f"{dtype.upper()} - 输入Token")

        # 输出token统计
        if all_output_tokens[dtype]:
            stats = calculate_statistics(all_output_tokens[dtype])
            print_statistics(stats, f"{dtype.upper()} - 输出Token")

    # 汇总所有类型的统计
    if all_total_tokens:
        all_tokens = []
        for tokens in all_total_tokens.values():
            all_tokens.extend(tokens)

        print("\n" + "=" * 60)
        print("所有类型合并统计")
        print("=" * 60)
        stats = calculate_statistics(all_tokens)
        print_statistics(stats, "全部 - 总Token")


if __name__ == '__main__':
    main()
