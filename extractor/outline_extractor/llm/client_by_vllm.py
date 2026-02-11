import os
import re
from typing import List
from dotenv import load_dotenv

from extractor.outline_extractor.decorators.llm_cache import llm_call_logger
from extractor.outline_extractor.config.runtime import RUN_ID

from langchain.messages import HumanMessage
from langchain_openai import ChatOpenAI

# 加载环境变量
load_dotenv()

# 从环境变量获取 vLLM 配置
VLLM_BASE_URL = os.getenv('VLLM_BASE_URL', 'http://localhost:8000/v1')
VLLM_API_KEY = os.getenv('VLLM_API_KEY', 'empty')
VLLM_MODEL_NAME = os.getenv('VLLM_MODEL_NAME', 'Qwen3-4B-Instruct-2507')
VLLM_MAX_TOKENS = int(os.getenv('VLLM_MAX_TOKENS', '15000'))
VLLM_TEMPERATURE = float(os.getenv('VLLM_TEMPERATURE', '0.1'))

# vLLM 客户端配置
llm = ChatOpenAI(
    model=VLLM_MODEL_NAME,
    api_key=VLLM_API_KEY,
    base_url=VLLM_BASE_URL,
    max_tokens=VLLM_MAX_TOKENS,
    temperature=VLLM_TEMPERATURE
)


@llm_call_logger(
    log_dir="logs/llm_calls",
    run_id=RUN_ID
)
def call_modelscope_chat(
    prompt: str,
    enable_thinking: bool = True,
    primary_model: str = None,
    backup_models: List[str] = None
) -> dict:
    """
    使用本地 vLLM 服务调用大模型

    Args:
        prompt: 提示词
        enable_thinking: 是否启用思考模式（解析 <thinking> 标签）
        primary_model: 主模型名称（默认从环境变量 VLLM_MODEL_NAME 获取）
        backup_models: 备份模型列表（vLLM 模式下暂不使用，保留接口兼容性）

    Returns:
        dict: 包含 prompt, thinking, answer, used_model, model_type 的字典
    """
    # 从环境变量获取默认模型
    if primary_model is None:
        primary_model = VLLM_MODEL_NAME

    if backup_models is None:
        backup_models = []

    # vLLM 模式只使用 primary_model，忽略 backup_models
    print(f"[vLLM模式] 使用模型: {primary_model}")
    print(f"[vLLM模式] 服务地址: {VLLM_BASE_URL}")
    print(f"[vLLM模式] 最大tokens: {VLLM_MAX_TOKENS}")
    print(f"[vLLM模式] 温度: {VLLM_TEMPERATURE}")

    try:
        messages = [
            HumanMessage(content=prompt),
        ]

        response = llm.invoke(messages)
        content = response.content

        # 解析 thinking 和 answer
        if '<think>' in content:
            # 优先尝试匹配 Qwen3 格式：<think>...</think> 后跟答案直到结尾
            qwen_match = re.search(r'<think>(.*?)</think>(.*?)$', content, re.DOTALL)
            if qwen_match:
                thinking = qwen_match.group(1).strip()
                answer = qwen_match.group(2).strip()
            else:
                # 回退到旧格式（带 <answer> 标签）
                thinking_match = re.search(r'<think>(.*?)</think>', content, re.DOTALL)
                answer_match = re.search(r'<answer>(.*?)</answer>', content, re.DOTALL)
                if thinking_match and answer_match:
                    thinking = thinking_match.group(1).strip()
                    answer = answer_match.group(1).strip()
                else:
                    # 保底：整个内容作为 answer
                    thinking = ''
                    answer = content.strip()
        else:
            # 没有 <thinking> 标签
            thinking = ''
            answer = content.strip()

        return {
            'prompt': prompt,
            "thinking": thinking,
            "answer": answer,
            "used_model": primary_model,
            "model_type": "vllm"  # 标识为 vLLM 模式
        }

    except Exception as e:
        error_msg = f"vLLM 模型调用失败: {e}"
        print(f"\\n[ERROR] {error_msg}")
        raise RuntimeError(error_msg) from e


if __name__ == '__main__':
    # 测试代码
    test_prompt = """请简单介绍一下 Python 的特点。"""

    try:
        result = call_modelscope_chat(test_prompt)
        print("=== 调用成功 ===")
        print(f"使用模型: {result['used_model']}")
        print(f"模型类型: {result['model_type']}")
        print(f"思考过程: {result['thinking'][:100] if result['thinking'] else '无'}...")
        print(f"回答: {result['answer'][:200]}...")
    except Exception as e:
        print(f"测试失败: {e}")
