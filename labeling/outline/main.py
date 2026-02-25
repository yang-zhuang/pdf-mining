"""
提纲提取标注数据准备脚本

功能：
1. 从 LLM 调用日志中提取提纲提取任务的标注数据
2. prompt: OCR 候选提纲内容（current_batch_content）
3. response: LLM 提取的提纲结果（response.answer）
4. 支持断点续传，避免重复导出
5. 支持模板系统，可选择不同的标注模板

使用方法：
    # 导出所有提纲标注数据（使用默认输出目录和默认模板）
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

    # 选择模板（两栏或三栏）
    python -m labeling.outline.prepare --template two_column
    python -m labeling.outline.prepare --template three_column

    # 列出所有可用模板
    python -m labeling.outline.prepare --list-templates
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
from labeling.templates.base import get_template, TEMPLATE_REGISTRY
from labeling.templates.outline.config import get_template_info, list_templates
from labeling.templates.outline.converter import OutlineDataConverter


class OutlineLabelingExporter(BaseLabelingExporter):
    """提纲提取标注数据导出器"""

    def __init__(self, log_files: list = None, log_dir: str = None, template_name: str = 'two_column'):
        """
        初始化导出器

        Args:
            log_files: 日志文件列表（json或jsonl），优先使用
            log_dir: 日志目录（当log_files为None时使用）
            template_name: 模板名称（'two_column' 或 'three_column'），默认为 'two_column'
        """
        # 优先使用文件列表，否则使用目录
        if log_files is not None:
            self.log_files = [Path(f) for f in log_files]
            self.use_file_list = True
        else:
            self.log_dir = Path(log_dir) if log_dir else Path('logs/llm_calls')
            self.use_file_list = False

        super().__init__(log_dir=log_dir or 'logs/llm_calls', task_name='outline_labeling')

        # 模板初始化
        self.template_name = template_name
        print(f"[配置] 使用模板: {template_name}")

        # 模板名称映射：将简化名称映射到注册表名称
        template_name_mapping = {
            'two_column': 'outline_two_column',
            'three_column': 'outline_three_column'
        }

        # 获取模板实例
        registry_template_name = template_name_mapping.get(template_name, template_name)
        self.template = get_template(registry_template_name)
        print(f"[配置] 模板描述: {self.template.description}")

        # 初始化数据转换器（不需要传递模板）
        self.converter = OutlineDataConverter()
        print(f"[配置] 数据转换器已初始化")

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
            log_dir_resolved = self.log_dir.resolve()
            if not log_dir_resolved.exists():
                raise FileNotFoundError(f"日志目录不存在: {self.log_dir}")

            # 获取所有 .jsonl 文件（递归查找子目录，使用集合去重，兼容 Windows 大小写问题）
            jsonl_files = list(set(log_dir_resolved.glob('**/*.jsonl')) | set(log_dir_resolved.glob('**/*.JSONL')))

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

        使用模板系统的数据转换器进行提取，保持向后兼容。

        Args:
            record: 日志记录

        Returns:
            提取后的标注数据，或 None
        """
        # 使用转换器提取数据
        return self.converter.extract_from_log(record)

    def export_data(
        self,
        records: List[Dict],
        output_file: str,
        data_extractor: callable = None,
        limit: int = None,
        append_mode: bool = False,
        use_converter: bool = True
    ):
        """
        导出标注数据（支持模板转换器）

        Args:
            records: 日志记录列表
            output_file: 输出文件路径
            data_extractor: 数据提取函数，接收 record，返回 dict 或 None（如果为 None 且 use_converter=True，则使用转换器）
            limit: 限制导出数量
            append_mode: 是否追加模式（False=覆盖，True=追加到已有JSON）
            use_converter: 是否使用模板转换器（默认 True）
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
            if use_converter and hasattr(self, 'converter'):
                # 使用模板转换器
                data = self.converter.extract_from_log(record)
            elif data_extractor:
                # 使用自定义提取函数
                data = data_extractor(record)
            else:
                # 回退到转换器
                data = self.converter.extract_from_log(record)

            if data:
                # 如果使用转换器，添加模板信息
                if use_converter and hasattr(self, 'template_name'):
                    data['_template'] = self.template_name
                    if hasattr(self, 'template') and self.template:
                        data['_template_description'] = self.template.description

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

        # 添加模板信息到状态
        if hasattr(self, 'template_name'):
            state['template_name'] = self.template_name

        self.save_state(state)

        print(f"[状态] 已更新断点续传状态文件: {self.state_file}")
        print(f"[状态] 总计已导出 {len(exported_hashes)} 条记录（本次新增 {len(new_exported_hashes)} 条）")

        # 显示模板信息
        if hasattr(self, 'template_name'):
            print(f"[状态] 当前使用模板: {self.template_name}")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='从 LLM 日志准备提纲提取标注数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认设置（从默认目录读取所有jsonl文件，输出到默认目录，使用默认模板）
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

  # 选择标注模板（两栏或三栏）
  python prepare.py --template two_column
  python prepare.py --template three_column

  # 列出所有可用模板
  python prepare.py --list-templates
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

    parser.add_argument(
        '--template',
        type=str,
        default='three_column',
        choices=['two_column', 'three_column'],
        help='选择标注模板：two_column（两栏）或 three_column（三栏），默认: two_column'
    )

    parser.add_argument(
        '--list-templates',
        action='store_true',
        help='列出所有可用的模板并退出'
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
    force: bool = False,
    template_name: str = 'two_column'
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
        template_name: 模板名称（'two_column' 或 'three_column'），默认为 'two_column'
    """
    print(f"[开始] 准备提纲提取标注数据")
    print(f"[配置] 使用的模板: {template_name}")

    # 验证模板
    template_info = get_template_info(template_name)
    if template_info:
        print(f"[配置] 模板描述: {template_info['display_name']}")
    else:
        print(f"[警告] 模板 '{template_name}' 未找到，将使用默认配置")

    # 设置默认值
    if log_dir is None:
        log_dir = '../../outline_extractor/logs/llm_calls'
    if output_dir is None:
        output_dir = f'../../labeling_data/outline/{template_name}'
    else:
        output_dir = f'{output_dir}/{template_name}'

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

    # 创建导出器（传入log_files或log_dir，以及template_name）
    exporter = OutlineLabelingExporter(log_files=log_files, log_dir=log_dir, template_name=template_name)

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

    # 处理 --list-templates 参数
    if args.list_templates:
        print("\n可用的提纲标注模板：")
        print("=" * 60)

        templates = list_templates(include_metadata=True)
        for template in templates:
            print(f"\n模板名称: {template['name']}")
            print(f"显示名称: {template['display_name']}")
            print(f"描述: {template['description']}")
            print(f"版本: {template['version']}")
            print(f"作者: {template['author']}")

            print("\n特性:")
            for feature in template['features']:
                print(f"  - {feature}")

            print(f"\nUI配置: {template['ui_config']['layout']}")
            print("-" * 60)

        print(f"\n使用方法: python -m labeling.outline.prepare --template <template_name>")
        print(f"例如: python -m labeling.outline.prepare --template two_column")
        print()
        return

    prepare_outline_labeling_data(
        log_files=args.log_files,
        log_dir=args.log_dir,
        output_dir=args.output_dir,
        limit=args.limit,
        batch_mode=args.batch_mode,
        file_key=args.file_key,
        force=args.force,
        template_name=args.template
    )


if __name__ == "__main__":
    main()
