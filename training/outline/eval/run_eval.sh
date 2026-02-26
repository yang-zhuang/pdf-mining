#!/bin/bash
# 提纲提取评估便捷启动脚本

# 获取脚本所在目录的父目录（项目根目录）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../" && pwd)"
cd "$PROJECT_ROOT"

# 设置环境变量
export VLLM_BASE_URL=${VLLM_BASE_URL:-"http://localhost:8000/v1"}
export VLLM_MODEL_NAME=${VLLM_MODEL_NAME:-"Qwen3-4B-Thinking-2507"}
export VLLM_API_KEY=${VLLM_API_KEY:-"empty"}

# 运行评估
python training/outline/eval/eval_outline.py "$@"