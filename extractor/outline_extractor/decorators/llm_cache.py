import json
import time
import os
from functools import wraps
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Set
import contextvars
from collections import defaultdict


# 创建 Context Variable 用于存储 LLM 调用的上下文信息
llm_call_context: contextvars.ContextVar[Optional[Dict[str, Any]]] = contextvars.ContextVar(
    "llm_call_context",
    default=None
)


class LLMCallLogger:
    """LLM 调用日志管理器，支持断点续传，按模型名称分文件夹"""

    @staticmethod
    def _sanitize_model_name(model_name: str) -> str:
        """
        清理模型名称，使其可以作为文件夹名称

        Windows 不允许的字符: < > : " / \\ | ? *
        Linux/macOS 不允许的字符: /

        Args:
            model_name: 原始模型名称

        Returns:
            清理后的安全文件夹名称
        """
        # 定义所有不允许的字符（Windows + Linux）
        forbidden_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']

        safe_name = model_name
        for char in forbidden_chars:
            safe_name = safe_name.replace(char, '_')

        # 移除首尾空格和点（Windows 文件夹名不能以点结尾）
        safe_name = safe_name.strip('. ')

        # 如果清理后为空，使用默认名称
        if not safe_name:
            safe_name = "unknown_model"

        return safe_name

    def __init__(self, log_dir: str, run_id: str, model_name: str = None):
        """
        初始化日志管理器

        Args:
            log_dir: 日志目录
            run_id: 运行ID
            model_name: 模型名称（可选，用于创建模型专属文件夹）
        """
        self.log_dir = Path(log_dir)
        self.run_id = run_id
        self.model_name = model_name

        # 如果提供了模型名称，创建模型专属子文件夹
        if model_name:
            safe_model_name = self._sanitize_model_name(model_name)
            self.model_log_dir = self.log_dir / safe_model_name
        else:
            self.model_log_dir = self.log_dir

        # 日志文件路径
        self.log_path = self.model_log_dir / f"{run_id}.jsonl"

        # 创建日志目录（包括模型子文件夹）
        self.model_log_dir.mkdir(parents=True, exist_ok=True)

        # 记录已处理的文件（用于断点续传）
        self.processed_files: Set[str] = set()
        self.file_call_counts: Dict[str, int] = defaultdict(int)

        # 如果日志文件已存在，加载已处理的文件列表
        if self.log_path.exists():
            self._load_processed_files()

    def _load_processed_files(self):
        """从现有日志文件加载已处理的文件列表"""
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                        # 提取文件标识
                        if record.get('file_key'):
                            self.processed_files.add(record['file_key'])
                    except json.JSONDecodeError:
                        continue

            if self.processed_files:
                print(f"[日志] 加载了 {len(self.processed_files)} 个已处理文件")
        except Exception as e:
            print(f"[警告] 加载日志文件失败: {e}")

    def _get_file_key(self, block_info: Dict) -> Optional[str]:
        """
        从块信息中生成唯一文件标识

        Args:
            block_info: 块信息字典

        Returns:
            文件标识（如页码范围或哈希）
        """
        # 使用 page_number 列表作为文件标识
        if isinstance(block_info, list):
            page_numbers = [b.get('page_number') for b in block_info if b.get('page_number')]
            if page_numbers:
                return f"pages_{min(page_numbers)}_{max(page_numbers)}"

        # 单个块
        if isinstance(block_info, dict):
            page_num = block_info.get('page_number')
            if page_num:
                return f"page_{page_num}"

        return None

    def is_file_processed(self, file_key: str) -> bool:
        """检查文件是否已处理"""
        return file_key in self.processed_files

    def mark_file_processed(self, file_key: str):
        """标记文件为已处理"""
        self.processed_files.add(file_key)

    def log_call(self, record: Dict[str, Any]):
        """记录一次 LLM 调用"""
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取日志统计信息

        读取日志目录下所有 .jsonl 文件的统计信息（包括所有模型子文件夹）
        只返回成功处理的文件标识（用于断点续传）
        """
        total_calls = 0
        successful_calls = 0
        failed_calls = 0
        successful_file_keys = set()  # 只收集成功处理的文件
        all_file_keys = set()  # 收集所有文件标识（包括失败的）
        log_files = []

        # 获取日志目录下所有 .jsonl 文件（包括所有子文件夹）
        # 使用集合去重，兼容 Windows 大小写问题
        if self.log_dir.exists():
            # 递归搜索所有子文件夹中的 .jsonl 文件
            log_files = list(set(self.log_dir.rglob('*.jsonl')) | set(self.log_dir.rglob('*.JSONL')))
            log_files.sort()

        # 统计所有日志文件
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            record = json.loads(line)
                            total_calls += 1
                            if record.get('success'):
                                successful_calls += 1
                            else:
                                failed_calls += 1

                            # 收集文件标识
                            if record.get('file_key'):
                                all_file_keys.add(record['file_key'])
                                # 只收集成功处理的文件（用于断点续传）
                                if record.get('success'):
                                    successful_file_keys.add(record['file_key'])
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"[警告] 读取日志文件 {log_file} 失败: {e}")
                continue

        return {
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'failed_calls': failed_calls,
            'processed_files': len(successful_file_keys),  # 只统计成功处理的文件数
            'successful_file_keys': successful_file_keys,  # 成功处理的文件集合
            'all_file_keys': all_file_keys,  # 所有文件标识（包括失败的）
            'log_dir': str(self.log_dir),
            'log_path': str(self.log_path),  # 当前模型文件夹的日志路径
            'log_files_count': len(log_files),
            'model_name': self.model_name  # 当前使用的模型名称
        }


# 全局日志管理器实例（将在运行时初始化）
_logger_instance: Optional[LLMCallLogger] = None


def get_logger() -> Optional[LLMCallLogger]:
    """获取当前的日志管理器实例"""
    return _logger_instance


def init_logger(log_dir: str, run_id: str, model_name: str = None) -> LLMCallLogger:
    """
    初始化日志管理器

    Args:
        log_dir: 日志目录
        run_id: 运行ID
        model_name: 模型名称（可选，用于创建模型专属文件夹）

    Returns:
        LLMCallLogger 实例
    """
    global _logger_instance
    _logger_instance = LLMCallLogger(log_dir, run_id, model_name)
    return _logger_instance


def llm_call_logger(
    log_dir: str,
    run_id: str
):
    """
    LLM 调用日志装饰器

    Args:
        log_dir: 日志目录
        run_id: 运行ID

    Note:
        模型名称会从被装饰函数的返回值中动态提取（如果返回值中有 'used_model' 字段）
    """
    # 初始化日志管理器（如果尚未初始化）
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = init_logger(log_dir, run_id)
    elif _logger_instance.run_id != run_id:
        # 如果 run_id 不同，重新初始化
        _logger_instance = init_logger(log_dir, run_id)

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            global _logger_instance  # 声明使用全局变量
            start = time.time()
            error = None
            response = None

            try:
                response = func(*args, **kwargs)
                success = True

                # 从响应中提取模型名称（如果存在）
                model_name = None
                if isinstance(response, dict) and 'used_model' in response:
                    model_name = response['used_model']

                # 如果模型名称与当前logger不同，重新初始化logger
                if model_name and _logger_instance.model_name != model_name:
                    _logger_instance = init_logger(log_dir, run_id, model_name)

                return response
            except Exception as e:
                error = str(e)
                success = False
                raise
            finally:
                # 从 Context Variable 读取上下文信息
                call_context = llm_call_context.get()

                # 构建精简结构化的日志记录
                record = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "function": func.__name__,
                    "model": _logger_instance.model_name,  # 记录使用的模型
                    "batch": call_context.get("batch") if call_context else None,
                    "history_context": call_context.get("history_context") if call_context else None,
                    "current_batch_content": call_context.get("current_batch_content") if call_context else None,
                    "response": response,
                    "success": success,
                    "error": error,
                    "latency_ms": int((time.time() - start) * 1000)
                }

                # 添加文件标识（用于断点续传）
                if call_context and call_context.get("file_key"):
                    record["file_key"] = call_context["file_key"]

                # 记录日志
                _logger_instance.log_call(record)

        return wrapper

    return decorator
