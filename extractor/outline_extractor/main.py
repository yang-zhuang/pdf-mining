import sys
import os
import json
import argparse
from pathlib import Path
from tqdm import tqdm
from document.builder import (
    build_document_lines,
    mark_page_headings,
    extract_page_headings
)
from pipeline.outline_pipeline import run_outline_pipeline
from models.structures import HeadingDetectionConfig
from config.settings import AppConfig
from config.runtime import generate_run_id_from_path, set_run_id
from decorators.llm_cache import init_logger, get_logger
from utils.path_utils import (
    safe_open,
    safe_exists,
    safe_isfile,
    safe_isdir,
    safe_glob,
    safe_rglob,
    get_relative_path,
    get_path_info,
)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='PDF 提纲提取工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        '--llm-mode',
        type=str,
        choices=['modelscope', 'vllm'],
        default='modelscope',
        help='LLM 客户端模式: modelscope (在线API) 或 vllm (本地服务)，默认: vllm'
    )

    parser.add_argument(
        '--input-path',
        type=str,
        default='../../sample_data/ocr_results',
        help='OCR 结果文件路径或文件夹路径（文件夹会递归搜索所有子文件夹中的 .json 文件）。默认使用示例数据：../../sample_data/ocr_results。完整数据路径示例："D:\\papers\\ACL-2025-paper\\ACL\\ACL-2025-paper-parse-result"'
    )

    parser.add_argument(
        '--run-id',
        type=str,
        default=None,
        help='运行ID（用于日志和断点续传）。如果不指定，会根据输入路径自动生成'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='强制重新处理所有文件，忽略已有的日志记录'
    )

    parser.add_argument(
        '--log-dir',
        type=str,
        default='logs/llm_calls',
        help='LLM 调用日志目录，默认: logs/llm_calls'
    )

    parser.add_argument(
        '--start',
        type=int,
        default=None,
        help='开始处理的文件索引（从 0 开始）。例如：--start 0 表示从第 1 个文件开始，--start 100 表示从第 101 个文件开始'
    )

    parser.add_argument(
        '--end',
        type=int,
        default=None,
        help='结束处理的文件索引（不包含）。例如：--end 100 表示处理到第 100 个文件（不包括第 100 个）'
    )

    # ========== 提纲检测配置 ==========
    parser.add_argument(
        '--enable-regex',
        action='store_true',
        default=None,
        help='启用正则表达式检测提纲（默认启用，使用 --disable-regex 禁用）'
    )

    parser.add_argument(
        '--disable-regex',
        action='store_true',
        help='禁用正则表达式检测提纲'
    )

    parser.add_argument(
        '--enable-hash',
        action='store_true',
        default=None,
        help='启用 # 前缀检测提纲（默认启用，使用 --disable-hash 禁用）'
    )

    parser.add_argument(
        '--disable-hash',
        action='store_true',
        help='禁用 # 前缀检测提纲'
    )

    parser.add_argument(
        '--enable-length',
        action='store_true',
        default=None,
        help='启用长度范围检测提纲（默认启用，使用 --disable-length 禁用）'
    )

    parser.add_argument(
        '--disable-length',
        action='store_true',
        help='禁用长度范围检测提纲'
    )

    parser.add_argument(
        '--min-length',
        type=int,
        default=None,
        help='提纲最小长度（默认: 2）'
    )

    parser.add_argument(
        '--max-length',
        type=int,
        default=None,
        help='提纲最大长度（默认: 40）'
    )

    # ========== 文本构建配置 ==========
    parser.add_argument(
        '--skip-empty',
        action='store_true',
        default=None,
        help='跳过空行（默认启用，使用 --no-skip-empty 禁用）'
    )

    parser.add_argument(
        '--no-skip-empty',
        action='store_true',
        help='不禁用跳过空行'
    )

    parser.add_argument(
        '--prefixes-to-remove',
        type=str,
        default=None,
        help='需要移除的前缀列表（逗号分隔），例如：--prefixes-to-remove "#,•,•"（默认: "#"）'
    )

    # ========== Markdown 配置 ==========
    parser.add_argument(
        '--max-preview-length',
        type=int,
        default=None,
        help='Markdown 预览最大长度（默认: 500）'
    )

    # ========== Batching 配置 ==========
    parser.add_argument(
        '--max-chars-per-batch',
        type=int,
        default=None,
        help='每批最大字符数（默认: 3000）'
    )

    # ========== Prompt 配置 ==========
    parser.add_argument(
        '--prompt-template',
        type=str,
        default=None,
        help='Prompt 模板文件路径（默认: llm/prompts/outline_prompt.txt）'
    )

    return parser.parse_args()


def load_json_file(file_path: str) -> dict:
    """
    加载单个 JSON 文件

    使用 safe_open 自动处理 Windows 长路径问题（>260 字符）

    Args:
        file_path: JSON 文件路径

    Returns:
        dict: JSON 数据
    """
    with safe_open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data


def get_json_files(input_path: str) -> list:
    """
    获取输入路径对应的所有 JSON 文件

    兼容 Windows 长路径限制，自动处理路径规范化
    支持递归搜索子文件夹

    Args:
        input_path: 文件路径或文件夹路径

    Returns:
        list: JSON 文件路径列表
    """
    # 检查路径是否存在
    if not safe_exists(input_path):
        raise FileNotFoundError(f"路径不存在: {input_path}")

    # 如果是文件，直接返回
    if safe_isfile(input_path):
        path = Path(input_path)
        if path.suffix.lower() != '.json':
            raise ValueError(f"文件格式错误，期望 .json 文件: {input_path}")
        return [str(path)]

    # 如果是文件夹，递归查找所有 JSON 文件
    if safe_isdir(input_path):
        # 使用 safe_rglob 递归查找文件（兼容长路径）
        # 只使用小写模式，避免重复（Windows 系统文件名不区分大小写）
        json_files = safe_rglob(input_path, '*.json')

        if not json_files:
            raise ValueError(f"文件夹及其子文件夹中没有找到 .json 文件: {input_path}")

        # 使用集合去重（防止 Windows 上的大小写重复）
        json_files = list(set(json_files))

        # 排序以保证处理顺序一致
        json_files.sort()

        # 显示找到的文件数量和分布情况
        print(f"[信息] 在 {len(json_files)} 个位置找到 JSON 文件")
        if len(json_files) > 1:
            # 统计子文件夹数量
            parent_dirs = set(str(f.parent) for f in json_files)
            if len(parent_dirs) > 1:
                print(f"[信息] 文件分布在 {len(parent_dirs)} 个文件夹中")

        return [str(f) for f in json_files]

    raise ValueError(f"无效的路径: {input_path}")


def process_single_file(json_file_path: str, config: AppConfig, prompt_template: str, call_llm=None, file_key: str = None) -> list:
    """
    处理单个 JSON 文件

    Args:
        json_file_path: JSON 文件路径
        config: 应用配置
        prompt_template: 提示词模板
        call_llm: LLM 客户端函数（如果提供，则不重新获取）
        file_key: 文件唯一标识（用于断点续传）

    Returns:
        list: 提取的提纲列表
    """
    # 获取相对路径用于显示（更友好）
    display_path = get_relative_path(json_file_path, os.getcwd())

    # 使用 tqdm.write 避免破坏进度条
    tqdm.write(f"\n{'='*60}")
    tqdm.write(f"[处理文件] {display_path}")
    tqdm.write(f"{'='*60}")

    # 显示路径信息（调试用）
    path_info = get_path_info(json_file_path)
    if path_info.get('size'):
        size_mb = path_info['size'] / (1024 * 1024)
        tqdm.write(f"[文件大小] {size_mb:.2f} MB")

    # 加载 OCR 数据（使用 safe_open 处理长路径）
    ocr_data = load_json_file(json_file_path)

    # 检查数据格式
    if 'pages' not in ocr_data:
        tqdm.write(f"⚠️ 跳过：JSON 文件中没有 'pages' 字段")
        return []

    ocr_pages = ocr_data['pages']

    tqdm.write(f"[信息] 共 {len(ocr_pages)} 页")

    # 构建文档行
    pages = build_document_lines(
        ocr_pages,
        skip_empty=config.SKIP_EMPTY_LINES,
        prefixes_to_remove=config.PREFIXES_TO_REMOVE
    )

    # 标记页面标题
    mark_page_headings(pages, config)

    # 提取页面标题
    outline_pages = extract_page_headings(pages)

    # 运行提纲提取管道（传入 call_llm 和 file_key 避免重复初始化并支持断点续传）
    final_outline = run_outline_pipeline(
        outline_pages,
        prompt_template=prompt_template,
        app_config=config,
        call_llm=call_llm,
        file_key=file_key  # 传递文件标识
    )

    return final_outline


def get_file_key(file_path: str) -> str:
    """
    生成文件唯一标识（用于断点续传）

    使用文件路径的哈希值作为唯一标识

    Args:
        file_path: 文件路径

    Returns:
        文件唯一标识
    """
    import hashlib
    path = Path(file_path)
    # 使用文件路径的绝对路径生成唯一标识
    abs_path = str(path.resolve())
    return hashlib.md5(abs_path.encode('utf-8')).hexdigest()


def main():
    # 解析命令行参数
    args = parse_args()

    # 生成或设置 RUN_ID
    if args.run_id:
        run_id = args.run_id
    else:
        run_id = generate_run_id_from_path(args.input_path)

    # 设置全局 RUN_ID（供装饰器使用）
    set_run_id(run_id)

    # 初始化日志管理器
    logger = init_logger(args.log_dir, run_id)

    print(f"[Main] 运行 ID: {run_id}")
    print(f"[Main] 日志目录: {args.log_dir}")
    print(f"[Main] LLM 模式: {args.llm_mode}")
    print(f"[Main] 输入路径: {args.input_path}")

    # 创建配置并设置 LLM 模式
    config = AppConfig()
    config.LLM_CLIENT_MODE = args.llm_mode

    # ========== 应用命令行参数到配置 ==========
    # 提纲检测配置
    if args.disable_regex:
        config.HEADING_DETECTION.enable_regex = False
    if args.disable_hash:
        config.HEADING_DETECTION.enable_hash = False
    if args.disable_length:
        config.HEADING_DETECTION.enable_length = False
    if args.min_length is not None:
        config.HEADING_DETECTION.min_length = args.min_length
    if args.max_length is not None:
        config.HEADING_DETECTION.max_length = args.max_length

    # 文本构建配置
    if args.no_skip_empty:
        config.SKIP_EMPTY_LINES = False
    if args.prefixes_to_remove is not None:
        config.PREFIXES_TO_REMOVE = [p.strip() for p in args.prefixes_to_remove.split(',')]

    # Markdown 配置
    if args.max_preview_length is not None:
        config.MAX_PREVIEW_LENGTH = args.max_preview_length

    # Batching 配置
    if args.max_chars_per_batch is not None:
        config.MAX_CHARS_PER_BATCH = args.max_chars_per_batch

    # Prompt 模板路径
    if args.prompt_template is not None:
        prompt_template_path = args.prompt_template
    else:
        prompt_template_path = "llm/prompts/outline_prompt.txt"

    # 显示配置信息
    print(f"\n[配置信息]")
    print(f"  - 提纲检测: regex={config.HEADING_DETECTION.enable_regex}, "
          f"hash={config.HEADING_DETECTION.enable_hash}, "
          f"length={config.HEADING_DETECTION.enable_length}")
    print(f"  - 长度范围: {config.HEADING_DETECTION.min_length}-{config.HEADING_DETECTION.max_length}")
    print(f"  - 跳过空行: {config.SKIP_EMPTY_LINES}")
    print(f"  - 移除前缀: {config.PREFIXES_TO_REMOVE}")
    print(f"  - Markdown 预览长度: {config.MAX_PREVIEW_LENGTH}")
    print(f"  - 每批最大字符数: {config.MAX_CHARS_PER_BATCH}")
    print(f"  - Prompt 模板: {prompt_template_path}")

    # 获取日志统计（用于断点续传）
    stats = logger.get_stats()

    # 显示日志统计信息
    if not args.force and stats['total_calls'] > 0:
        print(f"\n[断点续传] 发现已有日志记录:")
        if stats.get('model_name'):
            print(f"  - 当前模型: {stats['model_name']}")
        print(f"  - 日志目录: {stats['log_dir']}")
        print(f"  - 日志文件数: {stats['log_files_count']}")
        print(f"  - 总调用次数: {stats['total_calls']}")
        print(f"  - 成功: {stats['successful_calls']}")
        print(f"  - 失败: {stats['failed_calls']}")
        print(f"  - 已处理文件: {stats['processed_files']}")
        if stats['failed_calls'] > 0:
            print(f"  ⚠️ 有失败记录，建议使用 --force 重新处理")

    # 获取所有待处理的 JSON 文件（兼容长路径）
    try:
        json_files = get_json_files(args.input_path)
    except Exception as e:
        print(f"❌ 错误: {e}")
        print(f"\n提示：如果路径超过 260 字符，本工具会自动处理 Windows 长路径限制。")
        return

    print(f"\n[Main] 找到 {len(json_files)} 个 JSON 文件待处理")

    # 如果是长路径，给出提示
    if len(args.input_path) > 200:
        print(f"[提示] 检测到较长路径，已自动启用 Windows 长路径支持")

    # 应用文件范围筛选（如果指定了 --start 或 --end）
    original_count = len(json_files)
    if args.start is not None or args.end is not None:
        start_idx = args.start if args.start is not None else 0
        end_idx = args.end if args.end is not None else len(json_files)

        # 验证索引范围
        if start_idx < 0:
            print(f"⚠️ 警告: --start 不能为负数，已自动调整为 0")
            start_idx = 0
        if start_idx >= len(json_files):
            print(f"❌ 错误: --start ({start_idx}) 超出文件总数 ({len(json_files)})")
            return
        if end_idx > len(json_files):
            print(f"⚠️ 警告: --end ({end_idx}) 超出文件总数，已自动调整为 {len(json_files)}")
            end_idx = len(json_files)
        if end_idx <= start_idx:
            print(f"❌ 错误: --end ({end_idx}) 必须大于 --start ({start_idx})")
            return

        json_files = json_files[start_idx:end_idx]
        print(f"[范围] 将处理第 {start_idx} 到第 {end_idx-1} 个文件（共 {len(json_files)} 个，总数 {original_count}）")

    # 加载提示词模板
    try:
        with open(prompt_template_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        print(f"❌ 错误: 找不到 Prompt 模板文件: {prompt_template_path}")
        return

    # 预先初始化 LLM 客户端（避免每个文件都重新导入）
    from pipeline.outline_pipeline import _get_llm_client
    call_llm_func = _get_llm_client(args.llm_mode)
    print(f"[优化] LLM 客户端已预加载，将在所有文件间复用")

    # 处理所有文件
    all_outlines = []
    success_count = 0
    skipped_count = 0
    failed_files = []

    # 从日志统计中获取成功处理的文件哈希集合（已包含所有日志文件的统计）
    processed_file_keys = stats.get('successful_file_keys', set())

    if processed_file_keys and not args.force:
        print(f"[断点续传] 已加载 {len(processed_file_keys)} 个成功处理的文件记录（来自 {stats['log_files_count']} 个日志文件）")

        # 显示失败文件数量
        failed_file_count = len(stats.get('all_file_keys', set())) - len(processed_file_keys)
        if failed_file_count > 0:
            print(f"[断点续传] 检测到 {failed_file_count} 个处理失败的文件，将重新处理")

    # 使用 tqdm 进度条
    print(f"\n[开始] 处理文件...")
    for idx, json_file in enumerate(tqdm(json_files, desc="处理进度", unit="文件"), 1):
        # 生成文件标识（使用文件路径哈希）
        file_key = get_file_key(json_file)

        # 检查是否已处理（精确匹配文件哈希）
        if not args.force and file_key in processed_file_keys:
            display_path = get_relative_path(json_file, os.getcwd())
            tqdm.write(f"\n[跳过] {display_path}")
            tqdm.write(f"        原因: 已在日志中找到处理记录（哈希: {file_key[:8]}...）")
            tqdm.write(f"        提示: 使用 --force 可强制重新处理")
            skipped_count += 1
            continue

        # 在进度条外显示详细信息
        tqdm.write(f"\n{'='*60}")
        tqdm.write(f"[{idx}/{len(json_files)}] 处理文件: {get_relative_path(json_file, os.getcwd())}")
        tqdm.write(f"{'='*60}")

        try:
            # 传入预加载的 call_llm_func 和 file_key，避免重复初始化并支持断点续传
            outline = process_single_file(json_file, config, prompt_template, call_llm=call_llm_func, file_key=file_key)

            if outline:
                all_outlines.extend(outline)
                success_count += 1

                # 输出当前文件的提纲结果
                tqdm.write(f"\n[结果] 提取到 {len(outline)} 条提纲:")
                for line in outline:
                    tqdm.write(line)
            else:
                tqdm.write(f"[结果] 未提取到提纲")
                success_count += 1  # 虽然没有提纲，但处理成功

        except Exception as e:
            failed_files.append(json_file)
            tqdm.write(f"\n❌ 处理文件失败: {e}")
            import traceback
            traceback.print_exc()
            continue

    # 汇总信息
    print(f"\n\n{'='*60}")
    print(f"[完成] 共处理 {len(json_files)} 个文件")
    print(f"[成功] {success_count} 个文件")
    if skipped_count > 0:
        print(f"[跳过] {skipped_count} 个已处理文件")
    if failed_files:
        print(f"[失败] {len(failed_files)} 个文件")
        for failed_file in failed_files:
            display_path = get_relative_path(failed_file, os.getcwd())
            print(f"  - {display_path}")
    print(f"[总计] 提取到 {len(all_outlines)} 条提纲")

    # 显示最终日志统计
    final_stats = logger.get_stats()
    print(f"\n[日志统计]")
    if final_stats.get('model_name'):
        print(f"  - 当前模型: {final_stats['model_name']}")
    print(f"  - 日志目录: {final_stats['log_dir']}")
    print(f"  - 日志文件: {final_stats['log_path']}")
    print(f"  - 日志文件总数: {final_stats['log_files_count']}")
    print(f"  - LLM 调用次数: {final_stats['total_calls']}")
    print(f"  - 成功: {final_stats['successful_calls']}")
    print(f"  - 失败: {final_stats['failed_calls']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
