"""
提纲提取标注数据准备脚本

功能：
1. 从 LLM 调用日志中提取提纲提取任务的标注数据
2. prompt: OCR 候选提纲内容（current_batch_content）
3. response: LLM 提取的提纲结果（response.answer）
4. 支持断点续传，避免重复导出

使用方法：
    # 导出所有提纲标注数据（使用默认输出目录）
    python -m labeling.outline.prepare

    # 指定输出目录
    python -m labeling.outline.prepare --output-dir data/labels

    # 指定具体的日志文件列表（支持json和jsonl）
    python -m labeling.outline.prepare --log-files file1.jsonl file2.json

    # 限制导出数量
    python -m labeling.outline.prepare --limit 100

    # 批次模式（自动生成 batch_01.json, batch_02.json...）
    python -m labeling.outline.prepare --batch-mode

    # 只导出特定文件的记录
    python -m labeling.outline.prepare --file-key 0fe25f94c682ec25

    # 强制重新导出
    python -m labeling.outline.prepare --force
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# 添加父目录到路径，以便导入模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from labeling.utils import BaseLabelingExporter


class OutlineLabelingExporter(BaseLabelingExporter):
    """提纲提取标注数据导出器"""

    def __init__(self, log_files: list = None, log_dir: str = None):
        """
        初始化导出器

        Args:
            log_files: 日志文件列表（json或jsonl），优先使用
            log_dir: 日志目录（当log_files为None时使用）
        """
        # 优先使用文件列表，否则使用目录
        if log_files is not None:
            self.log_files = [Path(f) for f in log_files]
            self.use_file_list = True
        else:
            self.log_dir = Path(log_dir) if log_dir else Path('logs/llm_calls')
            self.use_file_list = False

        super().__init__(log_dir=log_dir or 'logs/llm_calls', task_name='outline_labeling')

    def read_log_files(self) -> List[Dict]:
        """
        读取日志文件

        支持两种模式：
        1. 文件列表模式：读取指定的文件列表（支持json和jsonl）
        2. 目录模式：读取目录下所有jsonl文件（向后兼容）

        Returns:
            所有日志记录的列表
        """
        all_records = []

        if self.use_file_list:
            # 模式1：文件列表模式
            print(f"[信息] 读取 {len(self.log_files)} 个指定日志文件")

            for log_file in self.log_files:
                if not log_file.exists():
                    print(f"[警告] 文件不存在，跳过: {log_file}")
                    continue

                suffix = log_file.suffix.lower()

                try:
                    if suffix == '.jsonl':
                        # jsonl 格式：每行一个 JSON 对象
                        records = self._read_jsonl_file(log_file)
                    elif suffix == '.json':
                        # json 格式：JSON 数组
                        records = self._read_json_file(log_file)
                    else:
                        print(f"[警告] 不支持的文件格式: {log_file}")
                        continue

                    all_records.extend(records)
                    print(f"[信息] 从 {log_file.name} 读取 {len(records)} 条记录")

                except Exception as e:
                    print(f"[警告] 读取文件失败 {log_file}: {e}")
                    continue

        else:
            # 模式2：目录模式（向后兼容）
            if not self.log_dir.exists():
                raise FileNotFoundError(f"日志目录不存在: {self.log_dir}")

            # 获取所有 .jsonl 文件（使用集合去重，兼容 Windows 大小写问题）
            jsonl_files = list(set(self.log_dir.glob('*.jsonl')) | set(self.log_dir.glob('*.JSONL')))

            if not jsonl_files:
                raise ValueError(f"日志目录中没有找到 .jsonl 文件: {self.log_dir}")

            # 排序以保证处理顺序一致
            jsonl_files.sort()

            print(f"[信息] 找到 {len(jsonl_files)} 个日志文件")

            for jsonl_file in jsonl_files:
                try:
                    records = self._read_jsonl_file(jsonl_file)
                    all_records.extend(records)
                except Exception as e:
                    print(f"[警告] 读取日志文件 {jsonl_file} 失败: {e}")
                    continue

        print(f"[信息] 共读取 {len(all_records)} 条日志记录")
        return all_records

    def _read_jsonl_file(self, file_path: Path) -> List[Dict]:
        """读取 jsonl 文件（每行一个 JSON 对象）"""
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    records.append(record)
                except json.JSONDecodeError as e:
                    print(f"[警告] 跳过无效的 JSON 行: {e}")
                    continue
        return records

    def _read_json_file(self, file_path: Path) -> List[Dict]:
        """读取 json 文件（JSON 数组）"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # 如果是单个对象，包装成列表
            return [data]
        else:
            print(f"[警告] JSON 文件格式不支持: {file_path}")
            return []

    def extract_outline_data(self, record: dict) -> dict:
        """
        从日志记录中提取提纲标注数据

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

        # 提取 prompt（使用 current_batch_content，这是给 LLM 的输入）
        prompt = response_data.get('prompt')
        if not prompt:
            return None

        return {
            'prompt': prompt,
            'response': answer
        }


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='从 LLM 日志准备提纲提取标注数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认设置（从默认目录读取所有jsonl文件，输出到默认目录）
  python prepare.py

  # 指定具体的日志文件列表（支持json和jsonl）
  python prepare.py --log-files file1.jsonl file2.json data.json

  # 指定输出目录（自动生成带时间戳的文件名）
  python prepare.py --output-dir data/my_labels

  # 限制导出数量（分批标注）
  python prepare.py --limit 100

  # 自动批次模式（每次运行自动生成 batch_01.json, batch_02.json...）
  python prepare.py --batch-mode

  # 只导出特定文件的记录
  python prepare.py --file-key 0fe25f94c682ec25

  # 强制重新导出所有记录
  python prepare.py --force
        """
    )

    parser.add_argument(
        '--log-files',
        nargs='+',
        type=str,
        default=None,
        help='日志文件路径列表（支持 .json 和 .jsonl，可指定多个文件）。如果不指定，则从 --log-dir 读取所有 jsonl 文件'
    )

    parser.add_argument(
        '--log-dir',
        type=str,
        default='../../extractor/outline_extractor/logs/llm_calls',
        help='LLM 日志目录（当未指定 --log-files 时使用，默认: ../../outline_extractor/logs/llm_calls）'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='../../labeling_data/outline',
        help='输出目录路径（默认: ../../labeling_data/outline）'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='限制导出的记录数量（用于分批标注）'
    )

    parser.add_argument(
        '--batch-mode',
        action='store_true',
        help='自动批次模式：自动生成 batch_01.json, batch_02.json 等文件名'
    )

    parser.add_argument(
        '--file-key',
        type=str,
        default=None,
        help='只导出特定文件的处理记录（文件哈希）'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='强制重新导出所有记录，忽略已导出的记录'
    )

    return parser.parse_args()


def get_next_batch_number(output_dir: str) -> int:
    """
    获取下一个批次号

    扫描输出目录中已有的 batch_XX.json 文件，返回下一个批次号

    Args:
        output_dir: 输出目录路径

    Returns:
        下一个批次号（从 01 开始）
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 查找所有 batch_XX.json 文件
    existing_batches = []
    for file in output_path.glob('batch_*.json'):
        try:
            # 提取批次号（如 batch_01.json -> 01）
            batch_num = int(file.stem.split('_')[1])
            existing_batches.append(batch_num)
        except (IndexError, ValueError):
            continue

    if not existing_batches:
        return 1

    # 返回最大批次号 + 1
    return max(existing_batches) + 1


def prepare_outline_labeling_data(
    log_files: list = None,
    log_dir: str = None,
    output_dir: str = None,
    limit: int = None,
    batch_mode: bool = False,
    file_key: str = None,
    force: bool = False
):
    """
    准备提纲提取标注数据

    Args:
        log_files: 日志文件列表（支持json和jsonl），优先使用
        log_dir: 日志目录（当log_files为None时使用）
        output_dir: 输出目录路径
        limit: 导出数量限制
        batch_mode: 是否使用自动批次模式
        file_key: 只导出特定文件的记录
        force: 是否强制重新导出
    """
    print(f"[开始] 准备提纲提取标注数据")

    # 设置默认值
    if log_dir is None:
        log_dir = '../../outline_extractor/logs/llm_calls'
    if output_dir is None:
        output_dir = '../../labeling_data/outline'

    # 显示输入源信息
    if log_files:
        print(f"[配置] 日志文件: {len(log_files)} 个指定文件")
        for f in log_files:
            print(f"    - {f}")
    else:
        print(f"[配置] 日志目录: {log_dir}")

    # 自动生成输出文件路径
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    if batch_mode:
        # 批次模式：batch_01.json, batch_02.json...
        batch_num = get_next_batch_number(str(output_dir_path))
        output_file = str(output_dir_path / f'batch_{batch_num:02d}.json')
        print(f"[配置] 批次模式：自动生成文件名 batch_{batch_num:02d}.json")
    else:
        # 时间戳模式：outline_20260208_173045.json
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = str(output_dir_path / f'outline_{timestamp}.json')
        print(f"[配置] 时间戳模式：自动生成文件名 outline_{timestamp}.json")

    print(f"[配置] 输出目录: {output_dir}")
    print(f"[配置] 输出文件: {output_file}")

    if limit:
        print(f"[配置] 导出数量限制: {limit}")
    if file_key:
        print(f"[配置] 只导出文件: {file_key}")
    if force:
        print(f"[配置] 强制重新导出（忽略断点续传）")

    # 创建导出器（传入log_files或log_dir）
    exporter = OutlineLabelingExporter(log_files=log_files, log_dir=log_dir)

    # 读取所有日志文件
    try:
        all_records = exporter.read_log_files()
    except Exception as e:
        print(f"❌ 错误: {e}")
        return

    # 加载断点续传状态
    if not force:
        state = exporter.load_state()
        exported_hashes = set(state.get('exported_record_hashes', []))
        if exported_hashes:
            print(f"[断点续传] 已有 {len(exported_hashes)} 条导出记录")
    else:
        exported_hashes = None

    # 过滤记录
    filtered_records = exporter.filter_records(
        all_records,
        file_key=file_key,
        exported_hashes=exported_hashes,
        force=force
    )

    if not filtered_records:
        print("[完成] 没有需要导出的记录")
        return

    # 导出标注数据
    exporter.export_data(
        filtered_records,
        output_file,
        data_extractor=exporter.extract_outline_data,
        limit=limit
    )

    print(f"\n[完成] 提纲标注数据准备完成")


def main():
    """命令行入口"""
    args = parse_args()
    prepare_outline_labeling_data(
        log_files=args.log_files,
        log_dir=args.log_dir,
        output_dir=args.output_dir,
        limit=args.limit,
        batch_mode=args.batch_mode,
        file_key=args.file_key,
        force=args.force
    )


if __name__ == "__main__":
    main()
