# 🚀 Running vLLM with Docker and GPU Support

This guide explains how to run **vLLM** in a **Docker container** with **GPU acceleration**, using a model like **Llama-3.2-1B** or **Qwen3-0.6B**, and how to verify that everything is running properly.

---

## 1. Prerequisites 🛠️

Before running the container, ensure the following are installed and configured on your system:

1. **Docker** — A containerization platform.
2. **NVIDIA Drivers** — The latest GPU drivers for your NVIDIA GPU.
3. **NVIDIA Container Toolkit** (e.g., `nvidia-docker2`) — Enables GPU access from within Docker containers.
4. **Hugging Face Access Token** (`$HF_TOKEN`) — Required for accessing private or gated models (e.g., Llama-3).

   > Note: Public models like `Qwen/Qwen3-0.6B` don’t require authentication, but setting up a token is still good practice.

---

## 2. Set the Hugging Face Token

Export your Hugging Face token as an environment variable so Docker can access it during model loading.

### Linux/macOS

```bash
export HF_TOKEN="your_huggingface_token_here"
```

> Replace `"your_huggingface_token_here"` with your actual token.

---

## 3. Run vLLM in Docker 🧠

Run the following command to start the **vLLM OpenAI-compatible API server** using Docker.

```bash
sudo docker run --gpus all \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -v ./models:/app/local_model \
  --env "HUGGING_FACE_HUB_TOKEN=$HF_TOKEN" \
  -p 8000:8000 \
  --ipc=host \
  vllm/vllm-openai:latest \
  --model /app/local_model/Llama-3.2-1B
```


For 12.4 cuda version, an older image vllm/vllm-openai:v0.8.0:

```bash
sudo docker run --gpus all \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -v ./models:/app/local_model \
  --env "HUGGING_FACE_HUB_TOKEN=$HF_TOKEN" \
  -p 8000:8000 \
  --ipc=host \
  vllm/vllm-openai:v0.8.0 \
  --model /app/local_model/Llama-3.2-1B
```

### Explanation of Options

| Option                                             | Description                                                              |
| :------------------------------------------------- | :----------------------------------------------------------------------- |
| `--gpus all`                                       | Grants access to all GPUs available on the host.                         |
| `-v ~/.cache/huggingface:/root/.cache/huggingface` | Mounts your Hugging Face cache directory to avoid re-downloading models. |
| `-v ./models:/app/local_model`                     | Mounts your local `models` directory into the container.                 |
| `--env "HUGGING_FACE_HUB_TOKEN=$HF_TOKEN"`         | Passes your Hugging Face token to the container.                         |
| `-p 8000:8000`                                     | Maps container port `8000` to the host, exposing the API.                |
| `--ipc=host`                                       | Shares IPC namespace with the host for better performance.               |
| `vllm/vllm-openai:latest`                          | Specifies the Docker image to use.                                       |
| `--model /app/local_model/Llama-3.2-1B`            | Defines the model path or Hugging Face model ID to load.                 |

---

## 4. Verify the Setup ✅

When you run the command, Docker will:

1. Pull the **vLLM image** (if not already cached).
2. Download the **model** (if not present in your mounted cache).
3. Start the **vLLM API server** on `http://localhost:8000`.

You should see logs confirming the server is running.

---

## 5. Test the API

Test the vLLM endpoint using `curl`:

```bash
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-0.6B",
    "prompt": "Hello, my name is",
    "max_tokens": 10
  }'
```

You can also use the **OpenAI Python client** by setting your `base_url` to `http://localhost:8000/v1`.

---

## 6. Enable and Restart Nginx 🌐

If you’re serving a frontend (like a chatbot UI), enable and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/
sudo systemctl enable nginx
sudo nginx -t
sudo systemctl restart nginx
```

---

