vllm serve /root/autodl-tmp/modelscope/Qwen3-4B-Thinking-2507  \
--served-model-name Qwen3-4B-Thinking-2507 \
--gpu-memory-utilization 0.85 \
--max-model-len 20480 \
--max-num-seqs 5 \
--port 6006 \
--quantization bitsandbytes \
--enable-lora \
--lora-modules outline=/root/autodl-tmp/modelscope/Qwen3-4B-outline-sft/checkpoint-13 \
--max-lora-rank 32