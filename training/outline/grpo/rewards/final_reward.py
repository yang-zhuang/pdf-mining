from rewards.env import LENGTH_WEIGHT, OUTLINE_WEIGHT
from rewards.length_reward import curriculum_length_reward
from rewards.outline_reward import curriculum_outline_reward


def final_reward(prompts, completions, completion_ids, **kwargs):
    """
    对外唯一使用的综合奖励函数。

    功能说明：
    - 组合长度奖励与结构提纲奖励
    - 使用可配置权重进行线性加权
    - 对训练框架暴露统一、简洁的 reward 接口

    设计目的：
    - 将复杂 reward 逻辑封装在内部模块中
    - 降低训练脚本复杂度
    - 支持后续无侵入式扩展更多 reward 维度

    参数说明：
    - prompts: prompt 列表
    - completions: 模型输出
    - completion_ids: token id 序列
    - kwargs: 透传给各子 reward 的附加信息

    返回值：
    - list[float]: 每个 completion 的最终 reward
    """

    length_r = curriculum_length_reward(prompts, completions, completion_ids, **kwargs)
    outline_r = curriculum_outline_reward(prompts, completions, completion_ids, **kwargs)

    return [
        LENGTH_WEIGHT * l + OUTLINE_WEIGHT * o
        for l, o in zip(length_r, outline_r)
    ]