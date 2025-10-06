# 🧠 vLLM Deployment

This repository contains a setup for running **vLLM inference** using **Llama llama3_8b** model and serving a simple **chatbot frontend**.

---

## 📂 Project Structure

```
vllm-deployment/
├── chatbot.html                     # Frontend chatbot UI
├── start_vllm_inference.sh          # (optional) Script to start vLLM server
├── nginx.conf                       # Nginx configuration to serve frontend
└── README.md
```

---

## 🚀 Overview

The setup includes two main components:

1. **vLLM Inference Server**
   Runs an OpenAI-compatible API server using the `vLLM` engine for optimized LLM inference.

2. **Frontend Chatbot**
   A simple HTML chatbot interface (`chatbot.html`) served by **Nginx** and connected to the vLLM backend API.

---

## 🧩 Requirements

Make sure you have the following installed:

* **Python 3.9+**
* **vLLM**

  ```bash
  pip install vllm
  ```
* **Nginx**

  ```bash
  sudo apt install nginx -y
  ```
* (Optional) **GPU** with CUDA for faster inference.

---

## ⚙️ Run the vLLM Inference Server

Start the vLLM OpenAI-compatible API server with your model:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model /mnt/data/office_work/vllms_inference/Llama-3.2-3B-Instruct \
  --max-num-batched-tokens 4096 \
  --gpu-memory-utilization 0.9
```

This will start the inference API at:

```
http://127.0.0.1:8000/v1
```

---

## 🌐 Serve Chatbot Frontend via Nginx

1. Copy your chatbot file to the Nginx web root:

   ```bash
   sudo cp /mnt/data/office_work/vllms_inference/chatbot.html /var/www/html/
   ```

2. Start or restart Nginx:

   ```bash
   sudo systemctl enable nginx
   sudo systemctl restart nginx
   ```

3. Access the chatbot at:

   ```
   http://localhost/chatbot.html
   ```

---

## 🧠 How It Works

* The **chatbot frontend (HTML)** sends requests to the local **vLLM API endpoint**.
* **vLLM** processes the prompt using the **Llama 3.2 3B Instruct** model.
* The response is displayed back in the chat interface.

---

## 🧾 Notes

* Ensure that `chatbot.html` points to the correct backend API (default: `http://localhost:8000/v1/chat/completions`).
* You can customize the model path or parameters as needed.
* Use `--host 0.0.0.0` with vLLM to make it accessible from other machines.

---
