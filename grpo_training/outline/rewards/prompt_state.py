from collections import defaultdict
from rewards.env import HISTORY_MAX_LEN, EMA_ALPHA

PROMPT_STATE = defaultdict(lambda: {
    "length": {
        "ema": None,
        "history": [],
    },
    "outline": {
        "ema_recall": None,
        "ema_penalty": None,
        "history": [],
    }
})


def update_ema(old, new):
    """
    更新指数滑动平均（EMA, Exponential Moving Average）。

    功能说明：
    - 若旧 EMA 不存在，则直接使用当前值初始化
    - 否则按 EMA_ALPHA 进行指数平滑更新

    设计目的：
    - 为每个 prompt 建立稳定的历史行为基线
    - 降低单次采样波动对 reward 的影响
    - 支持 prompt-adaptive reward 设计

    参数说明：
    - old (float | None): 历史 EMA 值
    - new (float): 当前观测值（如长度、recall、penalty）

    返回值：
    - float: 更新后的 EMA 值
    """

    if old is None:
        return new
    return EMA_ALPHA * new + (1 - EMA_ALPHA) * old


def push_history(history: list, item: dict):
    """
    向 prompt 的历史记录中追加一条新记录，并自动裁剪长度。

    功能说明：
    - 将当前 epoch 的统计信息加入 history
    - 若历史长度超过上限，则丢弃最旧记录

    设计目的：
    - 保留 prompt 在多个 epoch 上的行为轨迹
    - 支持 reward debug、行为分析和可解释性
    - 避免历史无限增长导致内存问题

    参数说明：
    - history (list): prompt 对应的历史记录列表
    - item (dict): 当前 epoch 的统计信息（如 length / recall / penalty）

    返回值：
    - None（原地修改 history）
    """

    history.append(item)
    if len(history) > HISTORY_MAX_LEN:
        history.pop(0)