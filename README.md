# 🧠 vLLM Deployment

This project demonstrates how to deploy **vLLM inference** using the **Llama 3.2 3B Instruct** model and serve a simple **chatbot frontend** through **Nginx**.

---

## ⚙️ Environment Setup

### 1. Create and Activate a Conda Environment

```bash
conda create -n vllm-env python=3.11 -y
conda activate vllm-env
```

### 2. Install Dependencies

```bash
pip install vllm
sudo apt install nginx -y
```

> 💡 *Optional:* Use a **GPU with CUDA** for significantly faster inference.

---

## 📁 Project Structure

```
vllm-deployment/
├── chatbot.html                     # Frontend chatbot UI
├── start_vllm_inference.sh          # (optional) Script to start the vLLM server
├── nginx.conf                       # Nginx configuration for chatbot frontend
└── README.md
```

---

## 📦 Model Download

Download the desired **Llama 3.2** model using Hugging Face CLI:

```bash
huggingface-cli download meta-llama/Llama-3.2-3B-Instruct \
  --local-dir Llama-3.2-3B-Instruct
```

For a smaller model (e.g., 1B):

```bash
huggingface-cli download meta-llama/Llama-3.2-1B \
  --local-dir Llama-3.2-1B
```

---

## 🚀 Components Overview

1. **vLLM Inference Server**
   An OpenAI-compatible API server powered by `vLLM`, optimized for efficient inference.

2. **Frontend Chatbot**
   A lightweight HTML-based chatbot (`chatbot.html`) served through **Nginx**, which communicates with the vLLM API.

---

## 🧩 Run the vLLM Inference Server

Start the inference server:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model /mnt/data/office_work/vllms_inference/Llama-3.2-3B-Instruct \
  --max-num-batched-tokens 4096 \
  --gpu-memory-utilization 0.9
```

Start the inference server with small model:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model ./models/Llama-3.2-1B \
  --max-num-batched-tokens 4096 \
  --gpu-memory-utilization 0.5
```

The API will be available at:

```
http://127.0.0.1:8000/v1
```

> 🧠 Use `--host 0.0.0.0` to make the API accessible from other systems.

---

## 🌐 Serve the Chatbot via Nginx

1. Copy your Nginx configuration file:

   ```bash
   sudo cp /mnt/data/office_work/vllms_inference/nginx.conf /etc/nginx/sites-available/chatbot
   ```

2. Enable and restart Nginx:

   ```bash
   sudo ln -s /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/
   sudo systemctl enable nginx
   sudo systemctl restart nginx
   ```

3. Open the chatbot in your browser:

   ```
   http://localhost
   ```

   or (replace with your system’s IP):

   ```
   http://192.168.1.1
   ```

---

## 🧠 How It Works

1. The **chatbot frontend** sends user input to the **local vLLM API**.
2. **vLLM** processes the input using the **Llama 3.2 3B Instruct** model.
3. The model’s response is returned and displayed in the chat interface.

---

## 🧾 Notes & Tips

* Ensure `chatbot.html` points to the correct backend endpoint:

  ```
  http://localhost:8000/v1/chat/completions
  ```
* Adjust model paths and inference parameters as needed.
* For distributed testing:

  ```bash
  python3 distributed_load_test.py --node-id 1 --users 12
  ```
* Old setup reference:

  ```bash
  python -m vllm.entrypoints.openai.api_server \
    --model /mnt/data/office_work/vllms_inference/llama3_8b \
    --max-num-batched-tokens 4096 \
    --gpu-memory-utilization 0.9
  python3 -m http.server 8080
  ```

---
