import os
from dotenv import load_dotenv

load_dotenv()

def _get_env(key: str, default, cast):
    """
    从环境变量中读取配置参数的统一工具函数。

    功能说明：
    - 尝试从系统环境变量中读取指定 key
    - 若不存在，则使用默认值 default
    - 对读取到的值使用 cast 进行类型转换

    设计目的：
    - 避免在代码中硬编码超参数
    - 支持通过环境变量快速调参而无需改代码
    - 保证所有 reward / curriculum 参数来源一致

    参数说明：
    - key (str): 环境变量名称
    - default: 当环境变量不存在时使用的默认值
    - cast: 类型转换函数（如 int / float / str）

    返回值：
    - 转换后的参数值
    """

    val = os.getenv(key)
    return default if val is None else cast(val)

# ===== Curriculum =====
CURRICULUM_EARLY_EPOCHS = _get_env("CURRICULUM_EARLY_EPOCHS", 4, int)
CURRICULUM_MID_EPOCHS   = _get_env("CURRICULUM_MID_EPOCHS", 2, int)

# ===== EMA =====
EMA_ALPHA = _get_env("EMA_ALPHA", 0.2, float)
HISTORY_MAX_LEN = _get_env("HISTORY_MAX_LEN", 20, int)

# ===== Length Reward =====
# MAX_COMPLETION_LEN = _get_env("MAX_COMPLETION_LEN", 10000, int)
# SOFT_PUNISH_CACHE  = _get_env("SOFT_PUNISH_CACHE", 2000, int)
MAX_COMPLETION_LEN = _get_env("MAX_COMPLETION_LEN", 5500, int)
SOFT_PUNISH_CACHE  = _get_env("SOFT_PUNISH_CACHE", 2000, int)
LENGTH_WEIGHT      = _get_env("LENGTH_WEIGHT", 1.0, float)

# ===== Outline Reward =====
OUTLINE_RECALL_WEIGHT  = _get_env("OUTLINE_RECALL_WEIGHT", 1.0, float)
OUTLINE_PENALTY_WEIGHT = _get_env("OUTLINE_PENALTY_WEIGHT", 1.0, float)
OUTLINE_WEIGHT         = _get_env("OUTLINE_WEIGHT", 1.0, float)