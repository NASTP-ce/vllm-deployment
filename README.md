# vllm-deployment


/mnt/data/office_work/vllms_inference/chatbot.html



python -m vllm.entrypoints.openai.api_server   --model /mnt/data/office_work/vllms_inference/Llama-3.2-3B-Instruct   --max-num-batched-tokens 4096   --gpu-memory-utilization 0.9