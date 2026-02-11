"""
思考模型推理服务

通过 langchain 调用思考模型，获取思考内容和响应结果。
支持单个调用（invoke）和批量调用（batch）两种模式。
"""
import re
from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage
import re


class ThinkingModelInference:
    """
    思考模型推理客户端

    调用 vLLM 部署的思考模型，获取思考过程和最终响应
    支持单个调用和批量并发调用
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        model_name: str = "Qwen3-4B-AWQ",
        api_key: str = "not-needed",
        max_tokens: int = 15000,
        temperature: float = 0
    ):
        """
        初始化推理客户端

        Args:
            base_url: vLLM 服务地址（包含 /v1）
            model_name: 模型名称
            api_key: API 密钥（vLLM 通常不需要）
            max_tokens: 最大生成 token 数
            temperature: 温度参数
        """
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature

        # 初始化 LangChain ChatOpenAI
        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=api_key,
            base_url=self.base_url,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def test_connection(self) -> bool:
        """
        测试与 vLLM 服务的连接

        Returns:
            是否连接成功
        """
        try:
            test_prompt = "测试连接"
            messages = [HumanMessage(content=test_prompt)]
            result = self.llm.invoke(messages)
            return result.content is not None
        except Exception as e:
            print(f"[错误] 无法连接到 vLLM 服务: {e}")
            return False

    def infer_single(self, prompt: str, max_tokens: int = None) -> Dict:
        """
        对单个 prompt 进行推理（使用 invoke）

        Args:
            prompt: 输入提示
            max_tokens: 最大生成 token 数（可选，覆盖初始化时的值）

        Returns:
            {
                "thinking": str,
                "response": str,
                "usage": {
                    "input_tokens": int,
                    "output_tokens": int,
                    "total_tokens": int
                },
                "raw": object
            }
        """
        if max_tokens is None:
            max_tokens = self.max_tokens

        messages = [HumanMessage(content=prompt)]

        try:
            # 使用 langchain 的 invoke 方法
            result = self.llm.invoke(messages)

            # 模型响应：包括了思考内容和答案
            content = result.content

            # 使用的元数据信息（token 统计）
            usage_metadata = result.usage_metadata
            input_tokens = usage_metadata['input_tokens']
            output_tokens = usage_metadata['output_tokens']
            total_tokens = usage_metadata['total_tokens']

            # 尝试分离思考内容和最终响应
            thinking, final_response = self._parse_thinking_content(content)

            return {
                "thinking": thinking,
                "response": final_response,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens
                },
                "raw": content
            }

        except Exception as e:
            print(f"[错误] 推理失败: {e}")
            return {
                "thinking": "",
                "response": "",
                "error": str(e)
            }

    def infer_batch(
        self,
        prompts: List[str],
        max_concurrency: int = 5,
        max_tokens: int = None
    ) -> List[Dict]:
        """
        批量推理（使用 batch 并发调用）

        Args:
            prompts: prompt 列表
            max_concurrency: 最大并发数
            max_tokens: 最大生成 token 数（可选，覆盖初始化时的值）

        Returns:
            推理结果列表
        """
        if max_tokens is None:
            max_tokens = self.max_tokens

        # 准备输入列表
        list_of_inputs = [[HumanMessage(content=prompt)] for prompt in prompts]

        try:
            # 使用 langchain 的 batch 方法进行并发推理
            results = self.llm.batch(
                list_of_inputs,
                config={
                    'max_concurrency': max_concurrency,
                }
            )

            # 解析所有结果
            parsed_results = []
            for result in results:
                content = result.content
                usage_metadata = result.usage_metadata

                thinking, final_response = self._parse_thinking_content(content)

                parsed_results.append({
                    "thinking": thinking,
                    "response": final_response,
                    "usage": {
                        "input_tokens": usage_metadata['input_tokens'],
                        "output_tokens": usage_metadata['output_tokens'],
                        "total_tokens": usage_metadata['total_tokens']
                    },
                    "raw": result
                })

            return parsed_results

        except Exception as e:
            print(f"[错误] 批量推理失败: {e}")
            # 返回错误结果列表
            return [{
                "thinking": "",
                "response": "",
                "error": str(e)
            } for _ in prompts]

    def _parse_thinking_content(self, content: str) -> tuple:
        """
        解析思考内容

        尝试从响应中分离思考内容和最终响应

        Args:
            content: 完整响应内容

        Returns:
            (thinking, response)
        """
        # 尝试匹配 <think> 标签（一些模型使用这种格式）
        if "<think>" in content and "</think>" in content:
            match = re.search('<think>(.*?)</think>(.*?)$', content, re.DOTALL)
            return match.group(1).strip(), match.group(2).strip()

        # 尝试匹配  标签（DeepSeek 等模型使用这种格式）
        if "</think>" in content and "</think>" in content:
            parts = content.split("</think>")
            if len(parts) >= 2:
                thinking_part = parts[1].split("</think>")[0].strip()
                response_part = content.replace(f"</think>{thinking_part}</think>", "").strip()
                return thinking_part, response_part

        # 如果没有思考标签，返回空思考
        return "", content


def test_vllm_connection(
    base_url: str = "http://localhost:8000/v1",
    model_name: str = "Qwen3-4B-AWQ"
):
    """
    测试 vLLM 服务连接

    Args:
        base_url: vLLM 服务地址
        model_name: 模型名称
    """
    print(f"[测试] 连接到 vLLM 服务: {base_url}")

    client = ThinkingModelInference(base_url=base_url, model_name=model_name)

    if client.test_connection():
        print(f"[成功] vLLM 服务连接正常")

        # 测试推理
        print(f"[测试] 发送测试请求...")
        test_prompt = "请简单介绍一下 Python。"
        result = client.infer_single(test_prompt)

        if "error" not in result:
            print(f"[成功] 推理测试成功")
            print(f"[响应] {result['response'][:100]}...")
            print(f"[Token] Input: {result['usage']['input_tokens']}, "
                  f"Output: {result['usage']['output_tokens']}, "
                  f"Total: {result['usage']['total_tokens']}")
        else:
            print(f"[失败] 推理测试失败: {result.get('error')}")
    else:
        print(f"[失败] 无法连接到 vLLM 服务")
        print(f"[提示] 请确保 vLLM 服务正在运行: {base_url}")
