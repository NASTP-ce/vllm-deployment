## 1\. Prerequisites 🛠️

Before running the command, ensure you have the following installed and configured:

1.  **Docker:** A containerization platform.
2.  **NVIDIA Drivers:** The latest drivers for your NVIDIA GPU.
3.  **NVIDIA Container Toolkit (nvidia-docker2 or newer):** This allows Docker to use your NVIDIA GPUs.
4.  **Hugging Face Access Token:** You need a **Hugging Face Hub token ($HF\_TOKEN)**, especially if the model you use requires authentication or is private (though **Qwen/Qwen3-0.6B** is public, it's good practice for general use).

-----

## 2\. Prepare the Environment Variables

You need to set the environment variable for your Hugging Face token so Docker can use it.

### **Linux/macOS:**

```bash
export HF_TOKEN="your_huggingface_token_here"
```

**Note:** Replace `"your_huggingface_token_here"` with your actual token.

-----

## 3\. The vLLM Docker Run Command

This is the command you will execute. It pulls the **vllm/vllm-openai:latest** image and starts the server.

### **Command**

```bash
docker run --runtime nvidia --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -v ./models:/app/local_model \
    --env "HUGGING_FACE_HUB_TOKEN=$HF_TOKEN" \
    -p 8000:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --model /app/local_model/Llama-3.2-1B
```

### **Explanation of Options**

| Option | Purpose |
| :--- | :--- |
| `--runtime nvidia` | **Specifies the runtime** to use the **NVIDIA Container Toolkit**, which is necessary for GPU access. |
| `--gpus all` | **Grants access to all available NVIDIA GPUs** inside the container. |
| `-v ~/.cache/huggingface:/root/.cache/huggingface` | **Mounts** your local Hugging Face cache directory into the container. This prevents the model from re-downloading every time you run the container. |
| `--env "HUGGING_FACE_HUB_TOKEN=$HF_TOKEN"` | **Passes your Hugging Face token** as an environment variable to the container, used for model downloads and access. |
| `-p 8000:8000` | **Maps the container's port 8000** to your **host machine's port 8000**. This is the port you'll use to communicate with the vLLM server. |
| `--ipc=host` | **Shares the host's IPC namespace** with the container. This is often recommended for high-performance applications like vLLM to potentially improve communication efficiency. |
| `vllm/vllm-openai:latest` | **The Docker image name**. This image contains vLLM and starts it in **OpenAI API server mode**. |
| `--model Qwen/Qwen3-0.6B` | **The vLLM server argument**. Specifies the Hugging Face model ID (in this case, **Qwen/Qwen3-0.6B**) that vLLM will load and serve. |

-----

## 4\. Verification and Usage

Once you run the command, the server will:

1.  **Pull the Docker Image** (if not already cached).
2.  **Download the Model** (if not already in the mounted cache).
3.  **Start the vLLM Server** on port 8000. You'll see logs indicating the server is running and ready.

### **How to Use the API**

The vLLM server now runs an **OpenAI-compatible API** on your host machine at `http://localhost:8000`. You can test it using a **curl** command for a simple completion:

```bash
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-0.6B",
    "prompt": "Hello, my name is",
    "max_tokens": 10
  }'
```

You can also use standard OpenAI client libraries (like `openai` in Python) by pointing the base URL to `http://localhost:8000/v1`.