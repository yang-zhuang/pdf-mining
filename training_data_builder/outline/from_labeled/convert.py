"""
从标注数据构建训练数据

将 Label Studio 导出的标注数据转换为各种训练格式。
支持的数据格式：SFT (unsloth), GRPO, Evaluation

使用方法：
    # 构建SFT/GRPO/评估数据集（指定模板）
    python -m training_data_builder.from_labeled.convert \
        --input-dir ../labeled_data/outline/three_column \
        --output-dir ../../training_data/outline \
        --template three_column
        --seed 42
"""

import argparse
import json
import random
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple


def adjust_answer_indentation(answer: str) -> str:
    """
    调整 answer 的缩进格式

    根据行内是否包含 '[二级]' 或 '[三级]' 来添加相应的空格缩进：
    - 包含 '[二级]' 的行：开头添加 2 个空格
    - 包含 '[三级]' 的行：开头添加 4 个空格
    - 其他行：不添加缩进

    Args:
        answer: 原始 answer 字符串

    Returns:
        调整缩进后的 answer 字符串
    """
    if not answer:
        return answer

    lines = answer.split('\n')
    adjusted_lines = []

    for line in lines:
        # 先去除行首和行尾的空白字符（不包括内部空格）
        stripped_line = line.strip()
        if not stripped_line:
            # 空行保留原样
            adjusted_lines.append('')
            continue

        # 判断是否需要缩进
        if '[三级]' in stripped_line:
            # 三级标题：4个空格缩进
            adjusted_lines.append('    ' + stripped_line)
        elif '[二级]' in stripped_line:
            # 二级标题：2个空格缩进
            adjusted_lines.append('  ' + stripped_line)
        else:
            # 其他行：不缩进
            adjusted_lines.append(stripped_line)

    return '\n'.join(adjusted_lines)


def load_labeled_data(input_dir: str, existing_prompts: set = None) -> List[Dict]:
    """
    从指定文件夹加载标注数据

    Args:
        input_dir: 标注数据文件夹路径
        existing_prompts: 已存在的 prompt 集合，用于断点续传

    Returns:
        提取的数据列表，每条数据包含 prompt, thinking, answer
    """
    if existing_prompts is None:
        existing_prompts = set()

    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"文件夹不存在: {input_dir}")

    # 查找所有 JSON 文件
    json_files = list(input_path.glob("*.json"))
    if not json_files:
        raise ValueError(f"在 {input_dir} 中没有找到 JSON 文件")

    print(f"[开始] 加载标注数据")
    print(f"[配置] 输入文件夹: {input_dir}")
    print(f"[信息] 找到 {len(json_files)} 个 JSON 文件")
    print(f"[信息] 已存在数据: {len(existing_prompts)} 条")

    all_data = []
    skipped_count = 0

    for json_file in json_files:
        print(f"[处理] 读取文件: {json_file.name}")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 处理每个标注项
        for item in data:
            # 提取原始 prompt
            prompt = item.get('data', {}).get('prompt', '')

            # 计算 prompt 的 hash，用于检查是否已存在
            prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()

            # 断点续传：如果 prompt 已存在则跳过
            if prompt_hash in existing_prompts:
                skipped_count += 1
                continue

            # 提取人工标注中的思考内容和答案
            annotations = item.get('annotations', [])
            if not annotations:
                continue

            result = annotations[0].get('result', [])
            if len(result) < 2:
                continue

            # result[0] 是思考内容 (annotated_thinking)
            thinking = result[0].get('value', {}).get('text', [''])[0] if result[0].get('value', {}).get('text') else ''

            # result[1] 是答案 (annotated_answer)
            answer = result[1].get('value', {}).get('text', [''])[0] if len(result) > 1 and result[1].get('value', {}).get('text') else ''

            # 调整 answer 的缩进格式
            answer = adjust_answer_indentation(answer)

            # 构造数据字典
            data_dict = {
                'prompt': prompt,
                'prompt_hash': prompt_hash,
                'thinking': thinking,
                'answer': answer
            }

            all_data.append(data_dict)

    print(f"[完成] 成功加载 {len(all_data)} 条标注数据（跳过已存在: {skipped_count} 条）")
    return all_data


def load_existing_prompts(output_dir: str, template: str = None) -> set:
    """
    从已保存的训练数据中加载所有 prompt 的 hash 集合

    Args:
        output_dir: 输出文件夹路径
        template: 模板名称，用于定位子目录

    Returns:
        已存在的 prompt hash 集合
    """
    existing_prompts = set()

    if template:
        # 如果指定了模板，检查对应的子目录
        output_path = Path(output_dir) / template
    else:
        output_path = Path(output_dir)

    if not output_path.exists():
        return existing_prompts

    # 查找所有相关的 JSONL 文件
    jsonl_files = list(output_path.glob("*.jsonl"))

    for jsonl_file in jsonl_files:
        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                        # 提取 prompt
                        if 'conversations' in item:
                            # SFT 格式
                            prompt = item['conversations'][0]['content']
                        elif 'prompt' in item:
                            # GRPO 格式或评估格式
                            prompt_messages = item.get('prompt', [])
                            if isinstance(prompt_messages, list) and len(prompt_messages) > 0:
                                prompt = prompt_messages[0].get('content', '')
                            else:
                                prompt = item.get('prompt', '')
                        else:
                            continue

                        # 计算 hash 并添加到集合
                        prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()
                        existing_prompts.add(prompt_hash)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"[警告] 读取文件 {jsonl_file} 失败: {e}")
            continue

    return existing_prompts


def calculate_total_length(item: Dict) -> int:
    """计算单条数据的总字符数（prompt + thinking + answer）"""
    return len(item.get('prompt', '')) + len(item.get('thinking', '')) + len(item.get('answer', ''))


def sort_data_by_length(data: List[Dict]) -> List[Dict]:
    """按照总字符数排序数据（从多到少）"""
    sorted_data = sorted(data, key=calculate_total_length, reverse=True)
    print(f"[信息] 数据已按字符数排序（从多到少）")
    if sorted_data:
        print(f"  最多: {calculate_total_length(sorted_data[0])} 字符")
        print(f"  最少: {calculate_total_length(sorted_data[-1])} 字符")
    return sorted_data


def split_into_three_sets(data: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    将数据按照字符数分布拆分为 评估、SFT、GRPO 三组

    拆分策略：
    1. 先将排序好的数据拆成两半
       - 第一半：字符数最多的部分（已排序）
       - 第二半：字符数最少的部分（需要反转）

    2. 评估数据：
       - 从第一半取前 1/3
       - 从第二半取最后 1/3

    3. SFT 数据：
       - 从第一半取中间 1/3
       - 从第二半取中间 1/3

    4. GRPO 数据：
       - 从第一半取最后 1/3
       - 从第二半取前 1/3
    """
    total = len(data)
    half = total // 2

    # 第一半：字符数最多（已排序）
    first_half = data[:half]

    # 第二半：字符数最少，需要反转使开头是最少的
    second_half = data[half:][::-1]

    # 计算各部分的 1/3 数量
    first_third = len(first_half) // 3
    second_third = len(second_half) // 3

    # 评估数据
    eval_data = first_half[:first_third] + second_half[-second_third:]

    # SFT 数据
    sft_first_start = first_third
    sft_first_end = first_third * 2
    sft_second_start = second_third
    sft_second_end = second_third * 2

    sft_data = first_half[sft_first_start:sft_first_end] + second_half[sft_second_start:sft_second_end]

    # GRPO 数据
    grpo_data = first_half[sft_first_end:] + second_half[:second_third]

    print(f"\n[拆分] 数据集拆分结果:")
    print(f"  总数据: {total}")
    print(f"  评估数据: {len(eval_data)} ({len(eval_data)/total*100:.1f}%)")
    print(f"  SFT 数据: {len(sft_data)} ({len(sft_data)/total*100:.1f}%)")
    print(f"  GRPO 数据: {len(grpo_data)} ({len(grpo_data)/total*100:.1f}%)")

    return sft_data, grpo_data, eval_data


def format_sft_data_with_thinking(data: List[Dict]) -> List[Dict]:
    """
    格式化 SFT 数据为 unsloth 格式（带思考内容）

    格式：
    {
        "conversations": [
            {"content": prompt, "role": "user"},
            {"content": "\n\n{thinking}\n\n\n{answer}", "role": "assistant"}
        ]
    }
    """
    sft_formatted = []

    for item in data:
        prompt = item.get('prompt', '')
        thinking = item.get('thinking', '')
        answer = item.get('answer', '')

        # assistant 的 content 是 "\n\n{thinking}\n\n\n{answer}"
        if thinking:
            assistant_content = f"<think>\n{thinking}\n</think>\n\n{answer}"
        else:
            assistant_content = answer
        assistant_content = assistant_content.strip()

        sft_item = {
            "conversations": [
                {
                    "content": prompt,
                    "role": "user"
                },
                {
                    "content": assistant_content,
                    "role": "assistant"
                }
            ]
        }
        sft_formatted.append(sft_item)

    return sft_formatted


def format_sft_data_no_thinking(data: List[Dict]) -> List[Dict]:
    """
    格式化 SFT 数据为 unsloth 格式（无思考内容）

    格式：
    {
        "conversations": [
            {"content": prompt, "role": "user"},
            {"content": answer, "role": "assistant"}
        ]
    }
    """
    sft_formatted = []

    for item in data:
        prompt = item.get('prompt', '')
        answer = item.get('answer', '')

        sft_item = {
            "conversations": [
                {
                    "content": prompt,
                    "role": "user"
                },
                {
                    "content": answer,
                    "role": "assistant"
                }
            ]
        }
        sft_formatted.append(sft_item)

    return sft_formatted


def format_grpo_data(data: List[Dict]) -> List[Dict]:
    """
    格式化 GRPO 数据为 TRL GRPO 格式

    格式：
    {
        "prompt": [{"role": "user", "content": prompt}],
        "solution": "思考内容\n\n答案"
    }
    """
    grpo_formatted = []

    for item in data:
        prompt = item.get('prompt', '')
        thinking = item.get('thinking', '')
        answer = item.get('answer', '')

        grpo_item = {
            "prompt": [{"role": "user", "content": prompt}],
            'thinking': thinking,
            "solution": answer
        }
        grpo_formatted.append(grpo_item)

    return grpo_formatted


def format_eval_data(data: List[Dict]) -> List[Dict]:
    """
    格式化评估数据（保持原始格式）

    格式：{
        "prompt": "...",
        "thinking": "...",
        "answer": "..."
    }
    """
    return data.copy()


def save_jsonl_data(data: List[Dict], output_file: str):
    """保存数据为 JSONL 格式"""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for item in data:
            json.dump(item, f, ensure_ascii=False)
            f.write('\n')

    print(f"[成功] 已保存 {len(data)} 条数据到: {output_file}")


def save_json_data(data: List[Dict], output_file: str):
    """保存数据为 JSON 格式"""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[成功] 已保存 {len(data)} 条数据到: {output_file}")


def convert_labeled_to_training(
    input_dir: str,
    output_dir: str = None,
    template: str = None,
    seed: int = 42,
):
    """
    从标注数据转换为 SFT、GRPO、评估三组数据

    Args:
        input_dir: 输入文件夹路径（标注数据）
        output_dir: 输出文件夹路径（可选，默认: ../../training_data/outline/）
        template: 模板名称（如 three_column），用于创建子目录保存数据
        seed: 随机种子，用于 shuffle 数据
    """
    # 设置默认输出目录
    if output_dir is None:
        output_dir = "../../training_data/outline/"

    output_dir_path = Path(output_dir)

    # 如果指定了模板，创建对应的子目录
    if template:
        output_dir_path = output_dir_path / template
    output_dir_path.mkdir(parents=True, exist_ok=True)

    print(f"[配置] 输出文件夹: {output_dir_path}")

    # 生成时间戳
    timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')

    # 步骤 1: 加载已存在的数据（断点续传）
    print(f"\n[步骤 1] 检查已存在数据（断点续传）")
    existing_prompts = load_existing_prompts(str(output_dir_path.parent if template else output_dir_path), template)

    # 步骤 2: 加载标注数据
    print(f"\n[步骤 2] 加载标注数据")
    data = load_labeled_data(input_dir, existing_prompts)

    if len(data) == 0:
        print(f"\n[完成] 没有新数据需要处理")
        return

    # 步骤 3: 按字符数排序
    print(f"\n[步骤 3] 按字符数排序")
    data = sort_data_by_length(data)

    # 步骤 4: 拆分为三组数据
    print(f"\n[步骤 4] 拆分数据集")
    sft_data, grpo_data, eval_data = split_into_three_sets(data)

    # 打乱数据顺序
    print(f"\n[步骤 5] 打乱数据顺序（seed: {seed}）")
    random.seed(seed)
    random.shuffle(sft_data)
    random.shuffle(grpo_data)
    random.shuffle(eval_data)
    print(f"[信息] 数据已打乱")

    # 步骤 6: 格式化并保存 SFT 数据（带思考内容）
    print(f"\n[步骤 6] 格式化并保存 SFT 数据（带思考内容）")
    sft_formatted_with_thinking = format_sft_data_with_thinking(sft_data)
    sft_file_with_thinking = output_dir_path / f"sft_labeled_with_thinking_{timestamp}.jsonl"
    save_jsonl_data(sft_formatted_with_thinking, str(sft_file_with_thinking))

    # 步骤 6.5: 格式化并保存 SFT 数据（无思考内容）
    print(f"\n[步骤 6.5] 格式化并保存 SFT 数据（无思考内容）")
    sft_formatted_no_thinking = format_sft_data_no_thinking(sft_data)
    sft_file_no_thinking = output_dir_path / f"sft_labeled_no_thinking_{timestamp}.jsonl"
    save_jsonl_data(sft_formatted_no_thinking, str(sft_file_no_thinking))

    # 步骤 7: 格式化并保存 GRPO 数据
    print(f"\n[步骤 7] 格式化并保存 GRPO 数据")
    grpo_formatted = format_grpo_data(grpo_data)
    grpo_file = output_dir_path / f"grpo_labeled_{timestamp}.jsonl"
    save_jsonl_data(grpo_formatted, str(grpo_file))

    # 步骤 8: 格式化并保存评估数据
    print(f"\n[步骤 8] 格式化并保存评估数据")
    eval_formatted = format_eval_data(eval_data)
    eval_file = output_dir_path / f"eval_labeled_{timestamp}.jsonl"
    save_jsonl_data(eval_formatted, str(eval_file))

    print(f"\n[完成] 所有数据处理完成！")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='从标注数据构建训练数据',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--input-dir',
        type=str,
        default="../../../labeled_data/outline/three_column",
        help='输入文件夹路径（标注数据）'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='../../../training_data/outline',
        help='输出文件夹路径（默认：../../training_data/outline/）'
    )

    parser.add_argument(
        '--template',
        type=str,
        default='three_column',
        help='模板名称（如 three_column），用于创建子目录保存数据'
    )

    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='随机种子，用于 shuffle 数据（默认：42）'
    )

    return parser.parse_args()


def main():
    """命令行入口"""
    args = parse_args()
    convert_labeled_to_training(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        template=args.template,
        seed=args.seed
    )


if __name__ == "__main__":
    main()