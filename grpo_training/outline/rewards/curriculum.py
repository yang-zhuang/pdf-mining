from rewards.env import CURRICULUM_EARLY_EPOCHS, CURRICULUM_MID_EPOCHS

def get_curriculum_phase(epoch: int) -> str:
    """
    根据当前训练 epoch 返回所处的课程学习阶段（Curriculum Phase）。

    阶段划分逻辑：
    - early：训练早期，仅提供正向奖励（强调召回、探索）
    - mid  ：训练中期，仅提供惩罚信号（抑制 hallucination / 冗余）
    - late ：训练后期，奖励与惩罚并行（平衡召回与准确率）

    设计目的：
    - 确保所有 reward 模块共享同一套课程调度逻辑
    - 防止不同 reward 在不同阶段产生目标冲突
    - 使训练目标随 epoch 逐步从“敢输出”过渡到“输出正确”

    参数说明：
    - epoch (int): 当前 trainer_state 中的 epoch

    返回值：
    - str: 当前阶段标识，"early" / "mid" / "late"
    """

    if epoch < CURRICULUM_EARLY_EPOCHS:
        return "early"
    if epoch < CURRICULUM_EARLY_EPOCHS + CURRICULUM_MID_EPOCHS:
        return "mid"
    return "late"