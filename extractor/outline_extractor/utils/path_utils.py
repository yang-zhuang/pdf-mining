"""
跨平台路径处理工具模块

解决 Windows 系统的 260 字符路径长度限制问题，同时兼容其他操作系统。
"""
import os
import sys
from pathlib import Path
from typing import Union, List


def normalize_path(path: Union[str, Path]) -> str:
    """
    规范化路径，处理 Windows 长路径问题

    Windows 系统默认路径长度限制为 260 字符（MAX_PATH）。
    通过添加 \\?\ 前缀可以绕过这个限制。

    Args:
        path: 原始路径（字符串或 Path 对象）

    Returns:
        str: 规范化后的路径

    Examples:
        >>> normalize_path("C:\\very\\long\\path...")
        "\\\\?\\C:\\very\\long\\path..."
    """
    # 转为字符串
    path_str = str(path)

    # 如果是相对路径，转为绝对路径
    if not os.path.isabs(path_str):
        path_str = os.path.abspath(path_str)

    # Windows 系统：添加长路径前缀
    if sys.platform == "win32":
        # 如果已经添加了前缀，不再重复添加
        if path_str.startswith("\\\\?\\"):
            return path_str

        # 处理 UNC 路径（网络路径）
        if path_str.startswith("\\\\"):
            # \\server\share -> \\?\UNC\server\share
            return "\\\\?\\UNC\\" + path_str[2:]

        # 处理普通本地路径
        # C:\path -> \\?\C:\path
        return "\\\\?\\" + path_str

    # 非 Windows 系统：直接返回绝对路径
    return path_str


def safe_open(file_path: Union[str, Path], mode: str = 'r', **kwargs):
    """
    安全打开文件，自动处理长路径问题

    Args:
        file_path: 文件路径
        mode: 打开模式（如 'r', 'w', 'a' 等）
        **kwargs: 传递给 open() 的其他参数

    Returns:
        文件对象

    Examples:
        >>> with safe_open("very_long_path.txt", 'r', encoding='utf-8') as f:
        ...     content = f.read()
    """
    normalized_path = normalize_path(file_path)
    return open(normalized_path, mode, **kwargs)


def safe_exists(path: Union[str, Path]) -> bool:
    """
    检查路径是否存在，兼容长路径

    Args:
        path: 文件或文件夹路径

    Returns:
        bool: 路径是否存在
    """
    try:
        normalized_path = normalize_path(path)
        return os.path.exists(normalized_path)
    except (OSError, ValueError):
        return False


def safe_isfile(path: Union[str, Path]) -> bool:
    """
    检查路径是否为文件，兼容长路径

    Args:
        path: 路径

    Returns:
        bool: 是否为文件
    """
    try:
        normalized_path = normalize_path(path)
        return os.path.isfile(normalized_path)
    except (OSError, ValueError):
        return False


def safe_isdir(path: Union[str, Path]) -> bool:
    """
    检查路径是否为文件夹，兼容长路径

    Args:
        path: 路径

    Returns:
        bool: 是否为文件夹
    """
    try:
        normalized_path = normalize_path(path)
        return os.path.isdir(normalized_path)
    except (OSError, ValueError):
        return False


def safe_listdir(path: Union[str, Path]) -> List[str]:
    """
    列出文件夹内容，兼容长路径

    Args:
        path: 文件夹路径

    Returns:
        List[str]: 文件/文件夹名称列表
    """
    normalized_path = normalize_path(path)
    return os.listdir(normalized_path)


def safe_glob(path: Union[str, Path], pattern: str) -> List[Path]:
    """
    使用 glob 模式查找文件，兼容长路径

    Args:
        path: 基础路径
        pattern: glob 模式（如 "*.json"）

    Returns:
        List[Path]: 匹配的文件路径列表
    """
    normalized_path = Path(normalize_path(path))
    return list(normalized_path.glob(pattern))


def safe_rglob(path: Union[str, Path], pattern: str) -> List[Path]:
    """
    递归使用 glob 模式查找文件，兼容长路径

    在指定路径及其所有子文件夹中搜索匹配的文件

    Args:
        path: 基础路径
        pattern: glob 模式（如 "*.json"）

    Returns:
        List[Path]: 匹配的文件路径列表

    Examples:
        >>> # 查找文件夹及其子文件夹中所有 JSON 文件
        >>> files = safe_rglob("/path/to/folder", "*.json")
    """
    normalized_path = Path(normalize_path(path))
    return list(normalized_path.rglob(pattern))


def get_relative_path(path: Union[str, Path], base: Union[str, Path]) -> str:
    """
    获取相对路径，用于显示（不用于文件操作）

    注意：返回的相对路径仅用于显示/日志，不应再用于文件操作

    Args:
        path: 目标路径
        base: 基础路径

    Returns:
        str: 相对路径（如果无法计算相对路径则返回绝对路径）
    """
    try:
        path_abs = os.path.abspath(str(path))
        base_abs = os.path.abspath(str(base))

        # 尝试返回相对路径
        if path_abs.startswith(base_abs):
            return os.path.relpath(path_abs, base_abs)

        return path_abs
    except (ValueError, OSError):
        # 无法计算相对路径时，返回绝对路径的简化版本
        path_str = str(path)
        # 移除 Windows 长路径前缀（仅用于显示）
        if path_str.startswith("\\\\?\\"):
            return path_str[4:]
        elif path_str.startswith("\\\\?\\UNC\\"):
            return "\\" + path_str[8:]
        return path_str


def get_path_info(path: Union[str, Path]) -> dict:
    """
    获取路径的详细信息

    Args:
        path: 文件或文件夹路径

    Returns:
        dict: 包含路径信息的字典
    """
    normalized_path = normalize_path(path)

    info = {
        "original": str(path),
        "normalized": normalized_path,
        "exists": safe_exists(path),
        "is_file": safe_isfile(path),
        "is_dir": safe_isdir(path),
    }

    # 获取文件大小（如果是文件）
    if info["is_file"]:
        try:
            info["size"] = os.path.getsize(normalized_path)
        except OSError:
            info["size"] = None

    # 获取文件列表（如果是文件夹）
    if info["is_dir"]:
        try:
            contents = safe_listdir(path)
            info["file_count"] = len([f for f in contents if os.path.isfile(os.path.join(normalized_path, f))])
            info["dir_count"] = len([f for f in contents if os.path.isdir(os.path.join(normalized_path, f))])
        except OSError:
            info["file_count"] = None
            info["dir_count"] = None

    return info


# 创建 __init__.py 使其成为一个包
# 将主要函数导出
__all__ = [
    'normalize_path',
    'safe_open',
    'safe_exists',
    'safe_isfile',
    'safe_isdir',
    'safe_listdir',
    'safe_glob',
    'safe_rglob',
    'get_relative_path',
    'get_path_info',
]
