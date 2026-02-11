"""
思考模式 Token 分析核心逻辑

提供批量处理、断点续传、实时保存等核心功能
"""

import json
from pathlib import Path
from tqdm import tqdm

from .infer import ThinkingModelInference
from .checkpoint import compute_prompt_hash, load_checkpoint
from .statistics import (
    calculate_simple_stats,
    print_stats,
    generate_recommendations,
    save_summary
)


class ThinkingAnalyzer:
    """思考模式 Token 分析器"""

    def __init__(
        self,
        vllm_url: str = "http://localhost:8000/v1",
        model_name: str = "Qwen3-4B-AWQ",
        max_tokens: int = 15000,
        use_batch: bool = False,
        max_concurrency: int = 5
    ):
        """
        初始化分析器

        Args:
            vllm_url: vLLM 服务地址
            model_name: 模型名称
            max_tokens: 最大生成 token 数
            use_batch: 是否使用批量并发
            max_concurrency: 批量并发数
        """
        self.vllm_url = vllm_url
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.use_batch = use_batch
        self.max_concurrency = max_concurrency

        # 创建推理客户端
        self.inference_client = ThinkingModelInference(
            base_url=vllm_url,
            model_name=model_name
        )

    def test_connection(self) -> bool:
        """测试 vLLM 连接"""
        return self.inference_client.test_connection()

    def load_data(self, input_file: str, limit: int = None):
        """
        加载数据

        Args:
            input_file: 输入文件路径
            limit: 数据限制

        Returns:
            (data, prompts, prompt_hashes)
        """
        input_path = Path(input_file)

        if not input_path.exists():
            raise FileNotFoundError(f"文件不存在: {input_file}")

        # 读取 JSONL 文件
        data = []
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    data.append(json.loads(line))

        print(f"[信息] 成功加载 {len(data)} 条数据")

        if limit:
            data = data[:limit]
            print(f"[信息] 限制分析前 {limit} 条数据")

        # 提取 prompts
        def extract_prompt(item):
            prompt_data = item.get('prompt')
            if isinstance(prompt_data, list) and len(prompt_data) > 0:
                return prompt_data[0].get('content', '')
            return str(prompt_data) if prompt_data else ''

        prompts = [extract_prompt(item) for item in data]
        prompt_hashes = [compute_prompt_hash(p) for p in prompts]

        return data, prompts, prompt_hashes

    def process_single_result(self, item, infer_result, idx, output_file_handle=None):
        """
        处理单条推理结果

        Args:
            item: 原始数据项
            infer_result: 推理结果
            idx: 数据索引
            output_file_handle: 输出文件句柄

        Returns:
            处理后的结果字典，如果出错返回 None
        """
        if "error" in infer_result:
            return None

        thinking = infer_result['thinking']
        response = infer_result['response']
        usage = infer_result['usage']

        # 计算 prompt hash
        prompt_data = item.get('prompt')
        if isinstance(prompt_data, list) and len(prompt_data) > 0:
            prompt = prompt_data[0].get('content', '')
        else:
            prompt = str(prompt_data) if prompt_data else ''

        prompt_hash = compute_prompt_hash(prompt)

        result = {
            "id": idx,
            "model_name": self.model_name,
            "prompt_hash": prompt_hash,
            "input_tokens": usage['input_tokens'],
            "output_tokens": usage['output_tokens'],
            "total_tokens": usage['total_tokens'],
            "usage_from_model": usage,
            "inference_result": {
                "thinking": thinking,
                "response": response
            }
        }

        # 实时保存
        if output_file_handle:
            output_file_handle.write(json.dumps(result, ensure_ascii=False) + '\n')
            output_file_handle.flush()

        return result

    def process_batch_mode(
        self,
        data,
        prompts,
        prompt_hashes,
        processed_hashes,
        output_file_handle
    ):
        """
        批量并发模式处理

        Args:
            data: 原始数据
            prompts: prompt 列表
            prompt_hashes: prompt hash 列表
            processed_hashes: 已处理的 hash 集合
            output_file_handle: 输出文件句柄

        Returns:
            (results, input_tokens_list, output_tokens_list, total_tokens_list, skipped_count, processed_count)
        """
        batch_size = self.max_concurrency
        total_count = len(prompts)
        num_batches = (total_count + batch_size - 1) // batch_size

        print(f"[信息] 总数据: {total_count} 条，批大小: {batch_size}，总批次数: {num_batches}")

        all_results = []
        all_input_tokens = []
        all_output_tokens = []
        all_total_tokens = []
        skipped_count = 0
        processed_count = 0

        for batch_idx in tqdm(range(num_batches), desc="批次进度"):
            start = batch_idx * batch_size
            end = min(start + batch_size, total_count)

            # 过滤已处理的数据
            batch_data_filtered = []
            batch_prompts_filtered = []
            batch_indices = []

            for i in range(start, end):
                idx = i + 1
                prompt_hash = prompt_hashes[i]

                if prompt_hash in processed_hashes:
                    skipped_count += 1
                    continue

                batch_data_filtered.append(data[i])
                batch_prompts_filtered.append(prompts[i])
                batch_indices.append((i, idx))

            if not batch_data_filtered:
                continue

            batch_original_size = end - start
            print(f"  批次 {batch_idx + 1}/{num_batches}: 处理 {len(batch_prompts_filtered)} 条 "
                  f"(跳过 {batch_original_size - len(batch_prompts_filtered)} 条)")

            # 批量推理
            batch_infer_results = self.inference_client.infer_batch(
                prompts=batch_prompts_filtered,
                max_concurrency=self.max_concurrency,
                max_tokens=self.max_tokens
            )

            # 处理结果
            for (i, idx), item, infer_result in zip(batch_indices, batch_data_filtered, batch_infer_results):
                result = self.process_single_result(item, infer_result, idx, output_file_handle)

                if result is None:
                    print(f"    ⚠️ 第 {idx} 条推理失败")
                    continue

                all_results.append(result)
                all_input_tokens.append(result['input_tokens'])
                all_output_tokens.append(result['output_tokens'])
                all_total_tokens.append(result['total_tokens'])

                processed_count += 1
                print(f"    第 {idx} 条 - Input: {result['input_tokens']}, "
                      f"Output: {result['output_tokens']}, Total: {result['total_tokens']}")

        return all_results, all_input_tokens, all_output_tokens, all_total_tokens, skipped_count, processed_count

    def process_single_mode(
        self,
        data,
        prompts,
        prompt_hashes,
        processed_hashes,
        output_file_handle
    ):
        """
        单个调用模式处理

        Args:
            data: 原始数据
            prompts: prompt 列表
            prompt_hashes: prompt hash 列表
            processed_hashes: 已处理的 hash 集合
            output_file_handle: 输出文件句柄

        Returns:
            (results, input_tokens_list, output_tokens_list, total_tokens_list, skipped_count, processed_count)
        """
        results = []
        input_tokens_list = []
        output_tokens_list = []
        total_tokens_list = []
        skipped_count = 0
        processed_count = 0

        for idx, item in enumerate(tqdm(data, desc="推理进度"), 1):
            prompt_hash = prompt_hashes[idx - 1]

            if prompt_hash in processed_hashes:
                skipped_count += 1
                continue

            prompt = prompts[idx - 1]
            infer_result = self.inference_client.infer_single(prompt, max_tokens=self.max_tokens)

            result = self.process_single_result(item, infer_result, idx, output_file_handle)

            if result is None:
                tqdm.write(f"  ⚠️ 第 {idx} 条推理失败")
                continue

            results.append(result)
            input_tokens_list.append(result['input_tokens'])
            output_tokens_list.append(result['output_tokens'])
            total_tokens_list.append(result['total_tokens'])

            processed_count += 1
            tqdm.write(f"  第 {idx} 条 - Input: {result['input_tokens']}, "
                      f"Output: {result['output_tokens']}, Total: {result['total_tokens']}")

        return results, input_tokens_list, output_tokens_list, total_tokens_list, skipped_count, processed_count

    def compute_statistics(self, input_tokens_list, output_tokens_list, total_tokens_list):
        """
        计算统计信息

        Args:
            input_tokens_list: Input token 列表
            output_tokens_list: Output token 列表
            total_tokens_list: Total token 列表

        Returns:
            (input_stats, output_stats, total_stats, suggestions)
        """
        print(f"\n[步骤 3] 计算统计信息")

        input_stats = calculate_simple_stats(input_tokens_list)
        output_stats = calculate_simple_stats(output_tokens_list)
        total_stats = calculate_simple_stats(total_tokens_list)

        print_stats("Input Token (Prompt)", input_stats)
        print_stats("Output Token (Thinking + Response)", output_stats)
        print_stats("Total Token (Input + Output)", total_stats)

        suggestions = generate_recommendations(input_stats, output_stats, total_stats)

        return input_stats, output_stats, total_stats, suggestions

    def analyze(
        self,
        input_file: str,
        output_file: str = None,
        limit: int = None
    ):
        """
        分析思考模式数据的 token 数量

        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            limit: 数据限制

        Returns:
            分析结果字典
        """
        print(f"[开始] 思考模式 Token 分析")
        print(f"[配置] vLLM 地址: {self.vllm_url}")
        print(f"[配置] 模型名称: {self.model_name}")
        print(f"[配置] 最大 token: {self.max_tokens}")
        print(f"[配置] 推理模式: {'批量并发' if self.use_batch else '单个调用'}")

        if self.use_batch:
            print(f"[配置] 最大并发数: {self.max_concurrency}")

        if limit:
            print(f"[配置] 数据限制: {limit} 条")

        # 测试连接
        print(f"\n[步骤 0] 测试 vLLM 连接")
        if not self.test_connection():
            print(f"[错误] 无法连接到 vLLM 服务: {self.vllm_url}")
            print(f"[提示] 请确保 vLLM 服务正在运行")
            return None

        # 加载数据
        print(f"\n[步骤 1] 加载数据")
        data, prompts, prompt_hashes = self.load_data(input_file, limit)

        # 断点续传
        output_dir = str(Path(output_file).parent)
        processed_hashes = load_checkpoint(output_dir=output_dir)

        # 创建输出文件
        output_file_handle = None
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_file_handle = open(output_path, 'a', encoding='utf-8')
            print(f"[信息] 结果将实时保存到: {output_file}")

        # 推理和分析
        print(f"\n[步骤 2] 调用思考模型并计算 token 数量")

        if self.use_batch:
            results, input_tokens_list, output_tokens_list, total_tokens_list, skipped_count, processed_count = \
                self.process_batch_mode(data, prompts, prompt_hashes, processed_hashes, output_file_handle)
        else:
            results, input_tokens_list, output_tokens_list, total_tokens_list, skipped_count, processed_count = \
                self.process_single_mode(data, prompts, prompt_hashes, processed_hashes, output_file_handle)

        # 关闭文件
        if output_file_handle:
            output_file_handle.close()

        print(f"\n[完成] 新处理 {processed_count} 条，跳过 {skipped_count} 条，总计 {len(results)} 条")

        # 检查是否有新数据
        if len(results) == 0:
            print(f"\n[跳过] 没有新数据需要分析")
            return None

        # 计算统计信息
        input_stats, output_stats, total_stats, suggestions = self.compute_statistics(
            input_tokens_list, output_tokens_list, total_tokens_list
        )

        # 保存摘要
        if output_file:
            print(f"\n[步骤 4] 保存统计摘要")

            config = {
                "input_file": input_file,
                "vllm_url": self.vllm_url,
                "model_name": self.model_name,
                "use_batch": self.use_batch,
                "max_concurrency": self.max_concurrency,
                "total_processed": len(results)
            }

            stats_dict = {
                "input": input_stats,
                "output": output_stats,
                "total": total_stats
            }

            save_summary(output_file, config, stats_dict, suggestions)

        print(f"\n[完成] 分析完成")

        return {
            "input_stats": input_stats,
            "output_stats": output_stats,
            "total_stats": total_stats,
            "recommendations": suggestions
        }
