"""
标注数据准备共享工具

提供基础的数据导出、断点续传等通用功能
"""

import json
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Set, Optional
from datetime import datetime


class BaseLabelingExporter:
    """
    标注数据导出器基类

    提供通用的日志读取、数据过滤、断点续传等功能
    """

    def __init__(
        self,
        log_dir: str = 'logs/llm_calls',
        state_file: str = None,
        task_name: str = 'labeling'
    ):
        """
        初始化导出器

        Args:
            log_dir: 日志目录路径
            state_file: 状态文件路径（默认为 .{task_name}_state.json）
            task_name: 任务名称（用于生成状态文件名）
        """
        self.log_dir = Path(log_dir)
        self.task_name = task_name

        if state_file is None:
            state_file = f".{task_name}_state.json"
        self.state_file = state_file

    def load_state(self) -> Dict:
        """加载断点续传状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    # 兼容旧格式：确保 exported_record_hashes 是列表
                    if 'exported_record_hashes' in state:
                        if isinstance(state['exported_record_hashes'], set):
                            state['exported_record_hashes'] = list(state['exported_record_hashes'])
                    return state
            except Exception as e:
                print(f"[警告] 加载状态文件失败: {e}")
                return {'exported_record_hashes': []}
        return {'exported_record_hashes': []}

    def save_state(self, state: Dict):
        """保存断点续传状态"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def get_record_hash(self, record: Dict) -> str:
        """
        生成记录的唯一哈希值

        使用 timestamp + file_key + current_batch_content 的哈希值
        可以根据不同任务重写此方法

        Args:
            record: 日志记录

        Returns:
            哈希值字符串
        """
        content = f"{record.get('timestamp', '')}{record.get('file_key', '')}{record.get('current_batch_content', '')}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:16]

    def read_log_files(self) -> List[Dict]:
        """
        读取日志目录下的所有 .jsonl 文件

        Returns:
            所有日志记录的列表
        """
        if not self.log_dir.exists():
            raise FileNotFoundError(f"日志目录不存在: {self.log_dir}")

        # 获取所有 .jsonl 文件（使用集合去重，兼容 Windows 大小写问题）
        jsonl_files = list(set(self.log_dir.glob('*.jsonl')) | set(self.log_dir.glob('*.JSONL')))

        if not jsonl_files:
            raise ValueError(f"日志目录中没有找到 .jsonl 文件: {self.log_dir}")

        # 排序以保证处理顺序一致
        jsonl_files.sort()

        print(f"[信息] 找到 {len(jsonl_files)} 个日志文件")

        all_records = []
        for jsonl_file in jsonl_files:
            try:
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            record = json.loads(line)
                            all_records.append(record)
                        except json.JSONDecodeError as e:
                            print(f"[警告] 跳过无效的 JSON 行: {e}")
                            continue
            except Exception as e:
                print(f"[警告] 读取日志文件 {jsonl_file} 失败: {e}")
                continue

        print(f"[信息] 共读取 {len(all_records)} 条日志记录")
        return all_records

    def filter_records(
        self,
        records: List[Dict],
        file_key: str = None,
        exported_hashes: Set[str] = None,
        force: bool = False,
        success_only: bool = True
    ) -> List[Dict]:
        """
        过滤日志记录

        Args:
            records: 所有日志记录
            file_key: 只处理特定文件的处理记录
            exported_hashes: 已导出的记录哈希集合
            force: 是否强制重新导出（忽略断点续传）
            success_only: 是否只包含成功的记录

        Returns:
            过滤后的记录列表
        """
        filtered = []

        for record in records:
            # 只处理成功的记录
            if success_only and not record.get('success'):
                continue

            # 筛选特定文件的记录
            if file_key and record.get('file_key') != file_key:
                continue

            # 断点续传：跳过已导出的记录
            if not force and exported_hashes:
                record_hash = self.get_record_hash(record)
                if record_hash in exported_hashes:
                    continue

            filtered.append(record)

        print(f"[信息] 过滤后剩余 {len(filtered)} 条记录")
        return filtered

    def export_data(
        self,
        records: List[Dict],
        output_file: str,
        data_extractor: callable,
        limit: int = None,
        append_mode: bool = False
    ):
        """
        导出标注数据（模板方法）

        Args:
            records: 日志记录列表
            output_file: 输出文件路径
            data_extractor: 数据提取函数，接收 record，返回 dict 或 None
            limit: 限制导出数量
            append_mode: 是否追加模式（False=覆盖，True=追加到已有JSON）
        """
        # 加载状态
        state = self.load_state()
        exported_hashes = set(state.get('exported_record_hashes', []))

        # 提取标注数据
        labeling_data = []
        new_exported_hashes = []

        for record in records:
            if limit and len(labeling_data) >= limit:
                break

            # 提取数据
            data = data_extractor(record)
            if data:
                labeling_data.append(data)
                # 记录已导出的哈希
                record_hash = self.get_record_hash(record)
                new_exported_hashes.append(record_hash)

        if not labeling_data:
            print("[提示] 没有找到新的标注数据")
            print("[提示] 如果需要重新导出，请使用 --force 参数")
            return

        # 保存到 JSON 文件
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 根据模式决定是覆盖还是追加
        if append_mode and output_path.exists():
            # 追加模式：读取已有数据并追加
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                if isinstance(existing_data, list):
                    labeling_data = existing_data + labeling_data
                    print(f"[信息] 追加模式：已读取 {len(existing_data)} 条已有数据")
            except Exception as e:
                print(f"[警告] 读取已有文件失败，将覆盖写入: {e}")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(labeling_data, f, ensure_ascii=False, indent=2)

        print(f"\n[成功] 导出 {len(labeling_data)} 条标注数据到: {output_file}")

        # 更新状态（添加新导出的哈希）
        exported_hashes.update(new_exported_hashes)
        state['exported_record_hashes'] = list(exported_hashes)
        state['last_export_time'] = datetime.now().isoformat()
        state['total_exported'] = len(exported_hashes)
        self.save_state(state)

        print(f"[状态] 已更新断点续传状态文件: {self.state_file}")
        print(f"[状态] 总计已导出 {len(exported_hashes)} 条记录（本次新增 {len(new_exported_hashes)} 条）")
