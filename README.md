# 🧠 vLLM Deployment

This project sets up **vLLM inference** using the **Llama 3.2 3B Instruct** model and serves a simple **chatbot frontend** via **Nginx**.

---

## ⚙️ Setup and Environment

First, create and activate a **Conda environment**:

```bash
conda create -n vllm-env python=3.11 -y
conda activate vllm-env
```

Then install the required dependencies:

```bash
pip install vllm
sudo apt install nginx -y
```

(Optional) Use a **GPU with CUDA** for faster inference.

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

## 🚀 Components

1. **vLLM Inference Server**
   Runs an OpenAI-compatible API server using `vLLM` for optimized model inference.

2. **Frontend Chatbot**
   A simple HTML-based chatbot (`chatbot.html`) served by **Nginx**, connected to the vLLM API.

---

## 🧩 Run the vLLM Inference Server

Start the API server:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model /mnt/data/office_work/vllms_inference/Llama-3.2-3B-Instruct \
  --max-num-batched-tokens 4096 \
  --gpu-memory-utilization 0.9
```

The API will be available at:

```
http://127.0.0.1:8000/v1
```

---

## 🌐 Serve Chatbot via Nginx

1. Copy the chatbot file to the Nginx web root:

   ```bash
   sudo cp /mnt/data/office_work/vllms_inference/ngix.config /etc/nginx/sites-available/chatbot
   ```

2. Enable and restart Nginx:

   ```bash
   sudo systemctl enable nginx
   sudo systemctl restart nginx
   ```

3. Open in your browser:

   ```
   http://localhost
   ```

   or

   ```
   http://192.168.1.1 // replace it with the IP address of the system
   ```

---

## 🧠 How It Works

* The **chatbot frontend** sends user input to the local **vLLM API**.
* **vLLM** processes the request using the **Llama 3.2 3B Instruct** model.
* The model’s response is shown back in the chat interface.

---

## 🧾 Notes

* Make sure `chatbot.html` uses the correct backend endpoint (`http://localhost:8000/v1/chat/completions`).
* You can adjust model paths or parameters as needed.
* Use `--host 0.0.0.0` to allow access from other machines.

---




old config:

python -m vllm.entrypoints.openai.api_server   --model /mnt/data/office_work/vllms_inference/llama3_8b   --max-num-batched-tokens 4096   --gpu-memory-utilization 0.9

python3 -m http.server 8080


 python3 distributed_load_test.py --node-id 1 --users 12


 huggingface-cli download meta-llama/Llama-3.2-3B-Instruct \
  --local-dir /mnt/data/office_work/vllms_inference/Llama-3.2-3B-Instruct