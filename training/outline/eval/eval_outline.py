#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
提纲提取评估脚本

使用 vllm 启动的大模型服务对评估数据进行评估，
计算准确率、召回率、F1 值。

使用方法:
    python eval_outline.py --base_url http://localhost:8000/v1 --model_name Qwen3-4B-Thinking-2507
"""

import argparse
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple
from tqdm import tqdm

import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


# ==================== 文本预处理工具 ====================

def extract_answer(text: str, model_name: str = "") -> str:
    """
    从模型原始输出中提取 answer 部分，剔除 think 思考内容。

    功能说明：
    - 若模型名称包含 'instruct'（不区分大小写），则直接返回原始文本
    - 若存在 <thinking> 标记，则仅保留其后的内容
    - 若存在 <thinking> 但缺失 </thinking>，视为异常输出，返回空字符串

    设计目的：
    - 防止将思考链内容误计入 reward
    - 提高 outline / 文本匹配类 reward 的准确性
    - 兼容响应被截断的异常情况
    - 支持 Instruct 模型（无思考内容）

    参数说明：
    - text (str): 模型原始输出文本
    - model_name (str): 模型名称，用于判断是否为 Instruct 模型

    返回值：
    - str: 提取后的 answer 内容
    """
    # 如果是 Instruct 模型，直接返回原始文本
    if model_name and 'instruct' in model_name.lower():
        return text.strip()

    if "</think>" not in text:
        return ""
    text = text.split("</think>", 1)[1]
    return text.strip()


def normalize_lines(text: str) -> List[str]:
    """
    将文本规范化为可用于结构匹配的"有效行"列表。

    修复重点：
    - 正则表达式扩展为支持多级编号（1.1, 1.1.1, 1.1. 等）
    - 移除编号后二次检查空行，避免残留空字符串
    """
    lines = []
    for line in text.splitlines():
        line = line.strip()
        # 跳过原始空行及代码块标记行
        if not line or line.startswith("```"):
            continue
        # 移除行首多级编号前缀（如 "1.", "2.3.1 ", "1.1."）
        line = re.sub(r'^\d[\d.]*\s*', '', line)
        # 关键修复：移除编号后若为空，跳过（避免 [""] 误入结果）
        if not line:
            continue
        lines.append(line)
    return lines


# ==================== VLLM 客户端 ====================

class VLLMClient:
    """VLLM API 客户端"""

    def __init__(self, base_url: str, model_name: str, api_key: str = "empty"):
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def chat_completion(self, prompt: str, max_tokens: int = 4096, temperature: float = 0.1, timeout: int = 300) -> str:
        """
        调用 VLLM API 进行对话补全

        Args:
            prompt: 输入提示词
            max_tokens: 最大生成 token 数
            temperature: 温度参数
            timeout: 请求超时时间（秒）

        Returns:
            模型输出的完整文本（包含 <thinking> 和 answer）
        """
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=timeout)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] VLLM API 调用失败: {e}")
            raise


# ==================== 评估计算 ====================

def compute_metrics(answer_lines: List[str], solution_lines: List[str]) -> Tuple[float, float, float, int, int, int, int]:
    """
    计算评估指标

    Args:
        answer_lines: 模型输出的规范化行列表
        solution_lines: 标准答案的规范化行列表

    Returns:
        (precision, recall, f1, tp, fp, fn, total_pred)
    """
    # 计算召回的答案（在 answer 中出现的 solution 行）
    recalled_answers = []
    for solution_line in solution_lines:
        if solution_line in answer_lines:
            recalled_answers.append(solution_line)

    # 计算幻觉（出现在 answer 中但不在 solution 中的行）
    hallucinated = []
    for answer_line in answer_lines:
        if answer_line not in solution_lines:
            hallucinated.append(answer_line)

    # 计算指标
    tp = len(recalled_answers)  # True Positive: 正确预测的
    fp = len(hallucinated)      # False Positive: 预测但错误的
    fn = len(solution_lines) - tp  # False Negative: 漏掉的
    total_pred = len(answer_lines)

    if len(solution_lines) == 0:
        recall = 1.0 if len(answer_lines) == 0 else 0.0
    else:
        recall = tp / len(solution_lines)

    if len(answer_lines) == 0:
        precision = 1.0 if len(solution_lines) == 0 else 0.0
    else:
        precision = tp / len(answer_lines)

    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)

    return precision, recall, f1, tp, fp, fn, total_pred


# ==================== 主评估逻辑 ====================

def load_eval_files(data_dir: Path) -> List[Tuple[str, str]]:
    """
    加载评估数据文件

    Args:
        data_dir: 数据目录路径

    Returns:
        List of (prompt, answer) tuples
    """
    eval_data = []

    # 查找所有以 'eval' 开头的文件
    eval_files = sorted(data_dir.glob('eval*'))

    print(f"找到 {len(eval_files)} 个评估文件:")
    for f in eval_files:
        print(f"  - {f.name}")

    for file_path in eval_files:
        if file_path.is_file():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            prompt = data.get('prompt', '')
                            answer = data.get('answer', '')
                            if prompt and answer:
                                eval_data.append((prompt, answer))
                        except json.JSONDecodeError as e:
                            print(f"[WARNING] 文件 {file_path.name} 第 {line_num} 行 JSON 解析失败: {e}")
            except Exception as e:
                print(f"[WARNING] 无法读取文件 {file_path.name}: {e}")

    print(f"共加载 {len(eval_data)} 条评估数据")
    return eval_data


def evaluate_single_sample(
    client: VLLMClient,
    prompt: str,
    ground_truth: str,
    sample_idx: int,
    total_samples: int,
    max_tokens: int,
    temperature: float,
    timeout: int
) -> dict:
    """
    评估单个样本

    Args:
        client: VLLM 客户端
        prompt: 输入提示词
        ground_truth: 标准答案
        sample_idx: 当前样本索引
        total_samples: 总样本数
        max_tokens: 最大生成 token 数
        temperature: 温度参数
        timeout: 请求超时时间（秒）

    Returns:
        评估结果字典
    """
    # 调用模型
    start_time = time.time()
    model_output = client.chat_completion(
        prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        timeout=timeout
    )
    inference_time = time.time() - start_time

    # 预处理模型输出
    answer_text = extract_answer(model_output, client.model_name)
    answer_lines = normalize_lines(answer_text)

    # 预处理标准答案
    solution_lines = normalize_lines(ground_truth)

    # 计算指标
    precision, recall, f1, tp, fp, fn, total_pred = compute_metrics(answer_lines, solution_lines)

    return {
        'sample_idx': sample_idx,
        'prompt_length': len(prompt),
        'answer_length': len(ground_truth),
        'model_output_length': len(model_output),
        'inference_time': inference_time,
        'answer_lines_count': len(answer_lines),
        'solution_lines_count': len(solution_lines),
        'tp': tp,
        'fp': fp,
        'fn': fn,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'model_output': model_output,
        'extracted_answer': answer_text
    }


def evaluate_parallel(
    client: VLLMClient,
    eval_data: List[Tuple[str, str]],
    max_workers: int,
    max_tokens: int,
    temperature: float,
    timeout: int,
    temp_details_file: Path = None,
    skip_indices: set = None
) -> List[dict]:
    """
    并行评估所有样本

    Args:
        client: VLLM 客户端
        eval_data: 评估数据列表 (prompt, ground_truth)
        max_workers: 最大并发数
        max_tokens: 最大生成 token 数
        temperature: 温度参数
        timeout: 请求超时时间（秒）
        temp_details_file: 临时详情文件路径（用于断点续传）
        skip_indices: 跳过的样本索引集合（已完成的样本）

    Returns:
        评估结果列表
    """
    if skip_indices is None:
        skip_indices = set()

    results = []
    total_samples = len(eval_data)

    # 计算待处理的任务
    tasks_to_process = [
        (i, prompt, ground_truth)
        for i, (prompt, ground_truth) in enumerate(eval_data)
        if i not in skip_indices
    ]

    # 打印恢复信息
    if skip_indices:
        print(f"[INFO] 跳过已完成的 {len(skip_indices)} 个样本，待评估 {len(tasks_to_process)} 个")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交任务（只提交未完成的）
        future_to_idx = {
            executor.submit(
                evaluate_single_sample,
                client,
                prompt,
                ground_truth,
                i,
                total_samples,
                max_tokens,
                temperature,
                timeout
            ): i
            for i, prompt, ground_truth in tasks_to_process
        }

        # 使用线程锁保护文件写入
        from threading import Lock
        file_lock = Lock()

        # 使用 tqdm 显示进度
        with tqdm(total=len(tasks_to_process), desc="评估进度") as pbar:
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    result = future.result()
                    results.append(result)

                    # 实时保存到临时文件（断点续传）
                    if temp_details_file:
                        summary = {
                            'sample_idx': result['sample_idx'],
                            'prompt_length': result['prompt_length'],
                            'answer_length': result['answer_length'],
                            'model_output_length': result['model_output_length'],
                            'inference_time': result['inference_time'],
                            'answer_lines_count': result['answer_lines_count'],
                            'solution_lines_count': result['solution_lines_count'],
                            'tp': result['tp'],
                            'fp': result['fp'],
                            'fn': result['fn'],
                            'precision': result['precision'],
                            'recall': result['recall'],
                            'f1': result['f1'],
                            'model_output_preview': result['model_output'][:500] + '...' if len(result['model_output']) > 500 else result['model_output']
                        }
                        with file_lock:
                            with open(temp_details_file, 'a', encoding='utf-8') as f:
                                f.write(json.dumps(summary, ensure_ascii=False) + '\n')

                    # 打印当前样本的简要结果
                    print(f"\n[{idx + 1}/{total_samples}] 评估完成")
                    print(f"  Precision: {result['precision']:.4f}, Recall: {result['recall']:.4f}, F1: {result['f1']:.4f}")
                    print(f"  TP: {result['tp']}, FP: {result['fp']}, FN: {result['fn']}")

                except Exception as e:
                    print(f"\n[ERROR] 样本 {idx} 评估失败: {e}")

                pbar.update(1)

    # 按 sample_idx 排序结果
    results.sort(key=lambda x: x['sample_idx'])
    return results


def aggregate_metrics(results: List[dict]) -> dict:
    """
    汇总所有样本的评估结果

    Args:
        results: 单个样本评估结果列表

    Returns:
        汇总指标
    """
    total_tp = sum(r['tp'] for r in results)
    total_fp = sum(r['fp'] for r in results)
    total_fn = sum(r['fn'] for r in results)
    total_pred = sum(r['answer_lines_count'] for r in results)
    total_gt = sum(r['solution_lines_count'] for r in results)
    total_time = sum(r['inference_time'] for r in results)

    # 宏平均（每个样本指标的平均）
    macro_precision = sum(r['precision'] for r in results) / len(results)
    macro_recall = sum(r['recall'] for r in results) / len(results)
    macro_f1 = sum(r['f1'] for r in results) / len(results)

    # 微平均（基于总 TP/FP/FN 计算）
    if total_pred == 0:
        micro_precision = 1.0 if total_gt == 0 else 0.0
    else:
        micro_precision = total_tp / total_pred

    if total_gt == 0:
        micro_recall = 1.0 if total_pred == 0 else 0.0
    else:
        micro_recall = total_tp / total_gt

    if micro_precision + micro_recall == 0:
        micro_f1 = 0.0
    else:
        micro_f1 = 2 * micro_precision * micro_recall / (micro_precision + micro_recall)

    avg_time = total_time / len(results)

    return {
        'macro_precision': macro_precision,
        'macro_recall': macro_recall,
        'macro_f1': macro_f1,
        'micro_precision': micro_precision,
        'micro_recall': micro_recall,
        'micro_f1': micro_f1,
        'total_tp': total_tp,
        'total_fp': total_fp,
        'total_fn': total_fn,
        'total_pred': total_pred,
        'total_gt': total_gt,
        'total_samples': len(results),
        'avg_inference_time': avg_time,
        'total_inference_time': total_time
    }


def print_metrics(metrics: dict):
    """打印评估指标"""
    print("\n" + "=" * 60)
    print("评估结果汇总")
    print("=" * 60)

    print("\n宏平均 (Macro Average):")
    print(f"  准确率 (Precision): {metrics['macro_precision']:.4f} ({metrics['macro_precision']*100:.2f}%)")
    print(f"  召回率 (Recall):    {metrics['macro_recall']:.4f} ({metrics['macro_recall']*100:.2f}%)")
    print(f"  F1 分数 (F1 Score):  {metrics['macro_f1']:.4f} ({metrics['macro_f1']*100:.2f}%)")

    print("\n微平均 (Micro Average):")
    print(f"  准确率 (Precision): {metrics['micro_precision']:.4f} ({metrics['micro_precision']*100:.2f}%)")
    print(f"  召回率 (Recall):    {metrics['micro_recall']:.4f} ({metrics['micro_recall']*100:.2f}%)")
    print(f"  F1 分数 (F1 Score):  {metrics['micro_f1']:.4f} ({metrics['micro_f1']*100:.2f}%)")

    print("\n详细统计:")
    print(f"  样本总数:         {metrics['total_samples']}")
    print(f"  预测总数:         {metrics['total_pred']}")
    print(f"  标准答案总数:     {metrics['total_gt']}")
    print(f"  正确预测 (TP):    {metrics['total_tp']}")
    print(f"  错误预测 (FP):    {metrics['total_fp']}")
    print(f"  漏掉预测 (FN):    {metrics['total_fn']}")
    print(f"  平均推理时间:     {metrics['avg_inference_time']:.2f} 秒")
    print(f"  总推理时间:       {metrics['total_inference_time']:.2f} 秒")

    print("=" * 60)


# ==================== 断点续传 ====================

def find_temp_files(output_dir: Path) -> List[Path]:
    """
    查找所有临时详情文件

    Args:
        output_dir: 输出目录

    Returns:
        临时文件路径列表（按修改时间降序）
    """
    temp_files = list(output_dir.glob('details_*_tmp.jsonl'))
    # 按修改时间降序排序（最新的在前）
    temp_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return temp_files


def load_progress_from_temp(temp_details_file: Path) -> set:
    """
    从临时文件中加载已完成的样本索引

    Args:
        temp_details_file: 临时详情文件路径

    Returns:
        已完成的样本索引集合
    """
    completed_indices = set()
    if not temp_details_file.exists():
        return completed_indices

    try:
        with open(temp_details_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if 'sample_idx' in data:
                        completed_indices.add(data['sample_idx'])
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"[WARNING] 读取临时文件失败: {e}")

    return completed_indices


def prompt_resume(temp_file: Path, completed_count: int) -> bool:
    """
    询问用户是否恢复之前的评估

    Args:
        temp_file: 临时文件路径
        completed_count: 已完成的样本数量

    Returns:
        是否恢复
    """
    print(f"\n{'='*60}")
    print("发现未完成的评估任务")
    print(f"{'='*60}")
    print(f"临时文件: {temp_file}")
    print(f"已完成样本: {completed_count}")
    print(f"修改时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(temp_file.stat().st_mtime))}")
    print(f"{'='*60}")

    while True:
        choice = input("是否恢复之前的评估？ [y/n/ignore]: ").strip().lower()
        if choice in ['y', 'yes']:
            return True
        elif choice in ['n', 'no']:
            # 删除临时文件
            temp_file.unlink()
            print(f"[INFO] 已删除临时文件: {temp_file}")
            return False
        elif choice == 'ignore':
            # 忽略临时文件，创建新的
            new_name = str(temp_file).replace('_tmp.jsonl', f'_old_{int(time.time())}.jsonl')
            temp_file.rename(new_name)
            print(f"[INFO] 已重命名旧临时文件: {new_name}")
            return False
        else:
            print("请输入 y (恢复), n (删除并重新开始), 或 ignore (忽略并新建)")


# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(description='提纲提取评估脚本')
    parser.add_argument(
        '--data_dir',
        type=str,
        default='../../../training_data/outline/three_column',
        help='评估数据目录路径'
    )
    parser.add_argument(
        '--base_url',
        type=str,
        default=None,
        help='VLLM API 基础 URL (默认从环境变量 VLLM_BASE_URL 读取)'
    )
    parser.add_argument(
        '--model_name',
        type=str,
        default='Qwen3-4B-Instruct-2507',
        help='模型名称 (默认从环境变量 VLLM_MODEL_NAME 读取)'
    )
    parser.add_argument(
        '--api_key',
        type=str,
        default=None,
        help='API 密钥 (默认从环境变量 VLLM_API_KEY 读取)'
    )
    parser.add_argument(
        '--max_tokens',
        type=int,
        default=5000,
        help='最大生成 token 数'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=600,
        help='API 请求超时时间（秒）'
    )
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.1,
        help='温度参数'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='results',
        help='结果输出目录'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='限制评估样本数量 (用于测试)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=4,
        help='并发工作线程数 (默认: 4)'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        default=True,
        help='启用断点续传（自动检测并恢复未完成的评估）'
    )
    parser.add_argument(
        '--no-resume',
        action='store_true',
        help='不使用断点续传（忽略临时文件，重新开始）'
    )

    args = parser.parse_args()

    # 从环境变量获取默认值
    base_url = args.base_url or os.getenv('VLLM_BASE_URL', 'http://localhost:8000/v1')
    model_name = args.model_name or os.getenv('VLLM_MODEL_NAME', 'Qwen3-4B-Thinking-2507')
    api_key = args.api_key or os.getenv('VLLM_API_KEY', 'empty')

    # 打印配置
    print("=" * 60)
    print("提纲提取评估脚本")
    print("=" * 60)
    print(f"数据目录:   {args.data_dir}")
    print(f"API 地址:   {base_url}")
    print(f"模型名称:   {model_name}")
    print(f"最大 Token: {args.max_tokens}")
    print(f"温度:       {args.temperature}")
    print(f"超时:       {args.timeout}秒")
    print(f"并发数:     {args.workers}")
    print("=" * 60)

    # 加载评估数据
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"[ERROR] 数据目录不存在: {data_dir}")
        return 1

    eval_data = load_eval_files(data_dir)

    if args.limit:
        eval_data = eval_data[:args.limit]
        print(f"\n[INFO] 限制评估样本数量为: {args.limit}")

    if not eval_data:
        print("[ERROR] 没有找到评估数据")
        return 1

    # 创建 VLLM 客户端
    client = VLLMClient(base_url, model_name, api_key)

    # 准备输出目录和临时文件
    # 将 model_name 拼接到 output_dir，方便区分不同模型的评估结果
    output_dir = Path(args.output_dir) / model_name
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    temp_details_file = output_dir / f"details_{timestamp}_tmp.jsonl"
    skip_indices = set()
    resume_from_file = None

    # 断点续传检测
    if not args.no_resume:
        temp_files = find_temp_files(output_dir)
        if temp_files:
            # 使用最新的临时文件
            latest_temp = temp_files[0]
            completed_indices = load_progress_from_temp(latest_temp)
            if completed_indices:
                resume_from_file = latest_temp
                skip_indices = completed_indices

    # 如果找到临时文件，询问用户
    if resume_from_file and not args.no_resume:
        do_resume = prompt_resume(resume_from_file, len(skip_indices))
        if do_resume:
            # 使用现有临时文件继续
            temp_details_file = resume_from_file
            print(f"[INFO] 将从临时文件恢复评估: {temp_details_file}")
            args.resume = True
        else:
            # 重新开始，清空 skip_indices
            skip_indices = set()
            resume_from_file = None

    # 记录是否为恢复模式
    is_resuming = len(skip_indices) > 0
    if is_resuming:
        print(f"[INFO] 恢复模式：跳过 {len(skip_indices)} 个已完成的样本")

    # 并行评估所有样本
    results = evaluate_parallel(
        client,
        eval_data,
        max_workers=args.workers,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        timeout=args.timeout,
        temp_details_file=temp_details_file,
        skip_indices=skip_indices
    )

    # 汇总结果
    if not results:
        print("[ERROR] 没有成功评估的样本")
        return 1

    # 如果是恢复模式，需要从临时文件读取之前的结果
    if is_resuming:
        # 从临时文件读取所有结果
        all_results = []
        with open(temp_details_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    all_results.append(data)
                except json.JSONDecodeError:
                    continue
        # 按样本索引排序
        all_results.sort(key=lambda x: x['sample_idx'])
        results = all_results
        print(f"[INFO] 从临时文件读取了 {len(results)} 条结果")

    metrics = aggregate_metrics(results)
    print_metrics(metrics)

    # 保存结果
    metrics_file = output_dir / f"metrics_{timestamp}.json"
    details_file = output_dir / f"details_{timestamp}.jsonl"

    # 保存汇总指标
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"\n汇总指标已保存到: {metrics_file}")

    # 如果是恢复模式，直接重命名临时文件为正式文件
    if is_resuming and temp_details_file.exists():
        temp_details_file.rename(details_file)
        print(f"详细结果已保存到: {details_file}")
        print(f"[INFO] 已重命名临时文件")
    else:
        # 保存详细结果
        with open(details_file, 'w', encoding='utf-8') as f:
            for result in results:
                # 只保存关键字段，不保存完整的 model_output（避免文件过大）
                summary = {
                    'sample_idx': result['sample_idx'],
                    'prompt_length': result['prompt_length'],
                    'answer_length': result['answer_length'],
                    'model_output_length': result['model_output_length'],
                    'inference_time': result['inference_time'],
                    'answer_lines_count': result['answer_lines_count'],
                    'solution_lines_count': result['solution_lines_count'],
                    'tp': result['tp'],
                    'fp': result['fp'],
                    'fn': result['fn'],
                    'precision': result['precision'],
                    'recall': result['recall'],
                    'f1': result['f1'],
                    'model_output_preview': result.get('model_output_preview', '')
                }
                f.write(json.dumps(summary, ensure_ascii=False) + '\n')
        print(f"详细结果已保存到: {details_file}")

    return 0


if __name__ == '__main__':
    main()