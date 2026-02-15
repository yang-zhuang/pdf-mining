from rewards.env import MAX_COMPLETION_LEN, SOFT_PUNISH_CACHE
from rewards.curriculum import get_curriculum_phase
from rewards.prompt_state import PROMPT_STATE, update_ema, push_history
from rewards.prompt_key import prompt_to_key
from collections import defaultdict
from typing import List


def soft_overlong_penalty(length: int) -> float:
    """
    对超出期望长度范围的输出施加平滑惩罚。

    功能说明：
    - 在安全区间内不惩罚
    - 在缓冲区内线性增加惩罚
    - 超过最大长度时施加固定强惩罚

    设计目的：
    - 防止模型输出无控制增长
    - 避免硬截断带来的梯度不连续问题
    - 与 DAPO 风格长度惩罚保持一致

    参数说明：
    - length (int): 当前 completion 的 token 长度

    返回值：
    - float: 长度惩罚分数（非正值）
    """

    if length <= MAX_COMPLETION_LEN - SOFT_PUNISH_CACHE:
        return 0.0
    elif length <= MAX_COMPLETION_LEN:
        # 缓冲区线性惩罚，非正值
        return - (length - (MAX_COMPLETION_LEN - SOFT_PUNISH_CACHE)) / SOFT_PUNISH_CACHE
    else:
        return -1.0


def curriculum_length_reward(prompts, completions, completion_ids, **kwargs):
    """
    基于课程学习（Curriculum）和 Prompt 自适应的长度奖励函数。

    功能说明：
    - Early 阶段：仅奖励更短输出，不施加惩罚
    - Mid 阶段：仅对长度增长和超长输出施加惩罚
    - Late 阶段：同时奖励更短输出并惩罚过长输出
    - /no_think 模式：跳过长度奖励（返回 0.0），仅依赖 outline_reward

    核心特性：
    - 使用 prompt 级 EMA 作为长度基线
    - 同一 prompt 的多 completion 自动聚合
    - 适配 GRPO / PPO 等 RL 训练框架
    - 对于 /no_think 模式的 prompt，长度奖励失效（因为模型直接输出答案，不进行思考）

    参数说明：
    - prompts: 原始 prompt 列表（支持 string 或 [{"role": "user", "content": "..."}] 格式）
    - completions: 模型输出（未直接使用，仅为接口一致性）
    - completion_ids: token id 序列，用于计算长度
    - kwargs: 额外参数（如 trainer_state）

    返回值：
    - list[float]: 每个 completion 对应的长度 reward
    """

    epoch = kwargs["trainer_state"].epoch
    phase = get_curriculum_phase(epoch)

    rewards: List[float] = []

    # ---------- prompt 级临时聚合器 ----------
    prompt_agg = defaultdict(lambda: {
        "lengths": []
    })

    # ---------- 第一轮：计算 reward（不更新状态） ----------
    for prompt, completion_id in zip(prompts, completion_ids):
        # 提取 prompt 内容（支持 string 和 [{"role": "user", "content": "..."}] 格式）
        prompt_content = ""
        if isinstance(prompt, str):
            prompt_content = prompt
        elif isinstance(prompt, list) and len(prompt) > 0 and isinstance(prompt[0], dict):
            prompt_content = prompt[0].get("content", "")

        # 检查是否为 /no_think 模式，如果是则跳过长度奖励
        # /no_think 模式下模型直接输出答案，长度奖励不适用
        is_no_think = isinstance(prompt_content, str) and prompt_content.rstrip().endswith("/no_think")

        if is_no_think:
            length_reward = 0.0
            completion_length = len(completion_id)
        else:
            prompt_hash = prompt_to_key(prompt)
            state = PROMPT_STATE[prompt_hash]["length"]
            ema_len = state["ema"]

            completion_length = len(completion_id)

            length_reward = 0.0
            if phase == "early":
                if ema_len is None:
                    length_reward = max((MAX_COMPLETION_LEN - completion_length) / MAX_COMPLETION_LEN, 0.0)
                else:
                    length_reward = max((ema_len - completion_length) / ema_len, 0.0)
            elif phase == "mid":
                if ema_len and completion_length > ema_len:
                    length_reward -= (completion_length - ema_len) / ema_len
                length_reward += soft_overlong_penalty(completion_length)
            else:
                if ema_len:
                    if completion_length < ema_len:
                        length_reward += (ema_len - completion_length) / ema_len
                    else:
                        length_reward += -(completion_length - ema_len) / ema_len

                length_reward += soft_overlong_penalty(completion_length)

        rewards.append(length_reward)

        # 聚合（不更新 EMA）
        prompt_hash = prompt_to_key(prompt)
        prompt_agg[prompt_hash]["lengths"].append(completion_length)

    # ---------- 第二轮：prompt 级更新 EMA / history ----------
    for prompt_hash, prompt_agg_stats in prompt_agg.items():
        # length EMA
        mean_len = sum(prompt_agg_stats["lengths"]) / len(prompt_agg_stats["lengths"])

        state = PROMPT_STATE[prompt_hash]["length"]
        ema_len = state["ema"]
        state["ema"] = update_ema(ema_len, mean_len)

        push_history(state["history"], {"epoch": epoch, "length": mean_len})

    return rewards