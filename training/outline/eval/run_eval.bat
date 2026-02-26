@echo off
REM 提纲提取评估便捷启动脚本 (Windows)

REM 设置环境变量
if not defined VLLM_BASE_URL set VLLM_BASE_URL=http://localhost:8000/v1
if not defined VLLM_MODEL_NAME set VLLM_MODEL_NAME=Qwen3-4B-Thinking-2507
if not defined VLLM_API_KEY set VLLM_API_KEY=empty

REM 运行评估
python training\outline\eval\eval_outline.py %*