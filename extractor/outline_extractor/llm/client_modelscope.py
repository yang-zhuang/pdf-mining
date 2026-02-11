import os
from dotenv import load_dotenv

from extractor.outline_extractor.decorators.llm_cache import llm_call_logger
from extractor.outline_extractor.config.runtime import RUN_ID

from openai import OpenAI
from typing import List, Dict, Tuple

# 加载环境变量
load_dotenv()

# 从环境变量获取配置
MODELSCOPE_API_KEY = os.getenv('MODELSCOPE_API_KEY', '')
MODELSCOPE_BASE_URL = os.getenv('MODELSCOPE_BASE_URL', 'https://api-inference.modelscope.cn/v1')
MODELSCOPE_DEFAULT_MODEL = os.getenv('MODELSCOPE_DEFAULT_MODEL', 'ZhipuAI/GLM-4.7-Flash')

# 验证必需的环境变量
if not MODELSCOPE_API_KEY:
    raise ValueError(
        "MODELSCOPE_API_KEY 环境变量未设置！\n"
        "请创建 .env 文件并设置：MODELSCOPE_API_KEY=your_api_key_here\n"
        "参考 .env.example 文件"
    )

# 创建客户端
client = OpenAI(
    base_url=MODELSCOPE_BASE_URL,
    api_key=MODELSCOPE_API_KEY,
)

# =========================
# 模型能力描述（唯一真相源）
# =========================

MODEL_PROFILES: Dict[str, Dict] = {
    'ZhipuAI/GLM-4.7-Flash': {
        'supports_thinking': False,
        'supports_reasoning_stream': False,
        'supports_multimodal': False,
    },
    'Qwen/Qwen3-235B-A22B': {
        'supports_thinking': True,
        'supports_reasoning_stream': True,
        'supports_multimodal': False,
    },
    'deepseek-ai/DeepSeek-R1-0528': {
        'supports_thinking': False,
        'supports_reasoning_stream': True,
        'supports_multimodal': False,
    },
    'moonshotai/Kimi-K2.5': {
        'supports_thinking': False,
        'supports_reasoning_stream': False,
        'supports_multimodal': True,
        'auto_wrap_text_prompt': True,  # 关键：内部自动适配
    },
    'meituan-longcat/LongCat-Flash-Lite': {
        'supports_thinking': False,
        'supports_reasoning_stream': False,
        'supports_multimodal': False,
    },
}


# =========================
# prompt -> messages 适配
# =========================

def build_messages(model_name: str, prompt: str) -> List[Dict]:
    profile = MODEL_PROFILES[model_name]

    # 多模态模型，但外部只给了文本
    if profile.get('supports_multimodal') and profile.get('auto_wrap_text_prompt'):
        return [{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }]

    # 普通文本模型
    return [{
        "role": "user",
        "content": prompt
    }]


# =========================
# 构建请求参数
# =========================

def build_request(
    model_name: str,
    prompt: str,
    enable_thinking: bool
) -> Dict:
    profile = MODEL_PROFILES[model_name]

    request = {
        "model": model_name,
        "stream": True,
        "messages": build_messages(model_name, prompt),
    }

    if profile.get('supports_thinking') and enable_thinking:
        request["extra_body"] = {
            "enable_thinking": True
        }

    return request

# =========================
# 统一解析流式返回
# =========================

def parse_stream(
    response,
    model_name: str
) -> Tuple[str, str]:
    profile = MODEL_PROFILES[model_name]

    full_thinking = ""
    full_answer = ""
    thinking_done = False

    for chunk in response:
        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta

        # 有推理流的模型
        if profile.get('supports_reasoning_stream'):
            reasoning_chunk = getattr(delta, "reasoning_content", "") or ""
            answer_chunk = delta.content or ""

            if reasoning_chunk:
                full_thinking += reasoning_chunk
                print(reasoning_chunk, end='', flush=True)

            elif answer_chunk:
                if not thinking_done:
                    print("\n\n=== Final Answer ===\n")
                    thinking_done = True
                full_answer += answer_chunk
                print(answer_chunk, end='', flush=True)

        # 普通模型
        else:
            content = delta.content or ""
            full_answer += content
            print(content, end='', flush=True)

    return full_thinking.strip(), full_answer.strip()

@llm_call_logger(
    log_dir="logs/llm_calls",
    run_id=RUN_ID
)
# =========================
# 统一对外入口
# =========================

def call_llm(
    prompt: str,
    enable_thinking: bool = True,
    primary_model: str = None,
    backup_models: List[str] = None,
):
    """
    使用 ModelScope API 调用大模型

    Args:
        prompt: 提示词
        enable_thinking: 是否启用思考模式
        primary_model: 主模型名称（默认从环境变量 MODELSCOPE_DEFAULT_MODEL 获取）
        backup_models: 备份模型列表

    Returns:
        dict: 包含 prompt, thinking, answer, used_model, model_type 的字典
    """
    # 从环境变量获取默认模型
    if primary_model is None:
        primary_model = MODELSCOPE_DEFAULT_MODEL

    if backup_models is None:
        backup_models = [
            'deepseek-ai/DeepSeek-R1-0528',
            'Qwen/Qwen3-235B-A22B',
            'ZhipuAI/GLM-4.7-Flash',
            'meituan-longcat/LongCat-Flash-Lite'
        ]

    models_to_try = [primary_model] + backup_models
    print(f"[ModelScope] 本次待尝试模型：{models_to_try}")

    for model_name in models_to_try:
        try:
            print(f"\n>>> 使用模型: {model_name}")

            request = build_request(
                model_name=model_name,
                prompt=prompt,
                enable_thinking=enable_thinking
            )

            response = client.chat.completions.create(**request)

            thinking, answer = parse_stream(response, model_name)

            return {
                'prompt': prompt,
                "thinking": thinking,
                "answer": answer,
                "used_model": model_name,
                "model_type": "primary" if model_name == primary_model else "backup"
            }

        except Exception as e:
            print(f"\n⚠️ 模型 {model_name} 调用失败: {e}")

    raise RuntimeError(
        f"所有模型调用失败！尝试的模型列表：{models_to_try}"
    )


if __name__ == '__main__':
    # 测试代码
    test_prompt = """请简单介绍一下 Python 的特点。"""

    try:
        result = call_llm(test_prompt)
        print("\n=== 调用成功 ===")
        print(f"使用模型: {result['used_model']}")
        print(f"模型类型: {result['model_type']}")
        print(f"回答: {result['answer'][:200]}...")
    except Exception as e:
        print(f"\n测试失败: {e}")
