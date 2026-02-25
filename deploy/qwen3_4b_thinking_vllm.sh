vllm serve /mnt/d/modelscope/Qwen3-4B-Thinking-2507  \
--served-model-name Qwen3-4B-Thinking-2507 \
--gpu-memory-utilization 0.85 \
--max-model-len 4096 \
--max-num-seqs 10 \
--port 8000 \
--quantization bitsandbytes