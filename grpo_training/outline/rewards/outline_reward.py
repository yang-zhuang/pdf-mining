from rewards.curriculum import get_curriculum_phase
from rewards.prompt_state import PROMPT_STATE, update_ema, push_history
from rewards.prompt_key import prompt_to_key
from rewards.text_utils import extract_answer, normalize_lines
from rewards.env import OUTLINE_RECALL_WEIGHT, OUTLINE_PENALTY_WEIGHT


def curriculum_outline_reward(prompts, completions, completion_ids, **kwargs):
    """
    基于课程学习的结构提纲（Outline）奖励函数。

    功能说明：
    - Early 阶段：仅关注召回率（solution 中的结构是否被覆盖）
    - Mid 阶段：仅惩罚 hallucination（多余结构）
    - Late 阶段：综合召回与惩罚，近似 F1 行为

    核心特性：
    - 使用 prompt 级 EMA 跟踪 recall / penalty 的历史基线
    - 对输出结构进行行级、去格式的精确匹配
    - 对文档难度具有自适应能力

    参数说明：
    - prompts: prompt 列表
    - completions: 模型输出（包含 think / answer）
    - completion_ids: 占位参数，用于接口统一
    - kwargs:
        - solution: 参考提纲（list[str]）
        - trainer_state: 训练状态信息

    返回值：
    - list[float]: 每个 completion 对应的 outline reward
    """

    epoch = kwargs["trainer_state"].epoch
    phase = get_curriculum_phase(epoch)

    solutions = kwargs.get("solution", [])

    rewards = []

    for prompt, completion, solution in zip(prompts, completions, solutions):

        answer = extract_answer(completion[0]["content"])
        answer_lines = normalize_lines(answer)

        solution_lines = normalize_lines(solution)

        recalled_answers = []
        for solution_line in solution_lines:
            if solution_line in answer_lines:
                recalled_answers.append(solution_line)

        hallucinated = []
        for answer_line in answer_lines:
            if answer_line not in solution_lines:
                hallucinated.append(answer_line)

        recall = len(recalled_answers) / len(solution_lines)
        penalty = len(hallucinated) / len(answer_lines)

        if phase == "early":
            reward = recall
        elif phase == "mid":
            reward = -penalty
        else:
            reward = OUTLINE_RECALL_WEIGHT * recall - OUTLINE_PENALTY_WEIGHT * penalty

        rewards.append(reward)

    return rewards