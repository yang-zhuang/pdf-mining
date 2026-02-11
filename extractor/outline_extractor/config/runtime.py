from datetime import datetime
import hashlib
from pathlib import Path

# 默认 RUN_ID（如果未手动设置）
RUN_ID = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")


def set_run_id(run_id: str):
    """
    设置运行 ID

    Args:
        run_id: 运行标识符（如 "batch_001", "paper_abc" 等）
    """
    global RUN_ID
    RUN_ID = run_id


def get_run_id() -> str:
    """
    获取当前运行 ID

    Returns:
        当前运行 ID
    """
    return RUN_ID


def generate_run_id_from_path(input_path: str) -> str:
    """
    根据输入路径生成固定的运行 ID（不含时间戳）

    使用路径哈希确保相同路径总是生成相同的 RUN_ID，支持断点续传

    Args:
        input_path: 输入路径（文件或文件夹）

    Returns:
        固定的运行 ID（不含时间戳）
    """
    path = Path(input_path).resolve()
    path_str = str(path)

    # 使用路径的 MD5 哈希作为 RUN_ID
    # 这样相同的路径总是生成相同的 RUN_ID
    path_hash = hashlib.md5(path_str.encode('utf-8')).hexdigest()[:12]

    # 获取路径的最后一部分作为可读前缀
    if path.is_file():
        base_name = path.stem
    else:
        base_name = path.name

    # 清理文件名
    base_name = base_name.replace(' ', '_').replace('-', '_')
    base_name = ''.join(c for c in base_name if c.isalnum() or c in '_.')
    base_name = base_name[:20]  # 限制前缀长度

    return f"{base_name}_{path_hash}"


def generate_run_id_with_timestamp(input_path: str) -> str:
    """
    根据输入路径生成唯一的运行 ID（含时间戳）

    Args:
        input_path: 输入路径（文件或文件夹）

    Returns:
        唯一的运行 ID（含时间戳）
    """
    path = Path(input_path)

    # 获取路径的最后一部分作为基础
    if path.is_file():
        base_name = path.stem  # 不包含扩展名
    else:
        base_name = path.name

    # 清理文件名，移除特殊字符
    base_name = base_name.replace(' ', '_').replace('-', '_')
    base_name = ''.join(c for c in base_name if c.isalnum() or c in '_.')

    # 限制长度
    if len(base_name) > 30:
        base_name = base_name[:30]

    # 生成时间戳
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

    return f"{base_name}_{timestamp}"
