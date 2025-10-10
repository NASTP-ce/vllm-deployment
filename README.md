# 🧠 vLLM Deployment

This project demonstrates how to deploy **vLLM inference** using the **Llama 3.2 3B Instruct** model and serve a simple **chatbot frontend** through **Nginx**.

---

## 📦 Model Download

Download the desired **Llama 3.2** model using Hugging Face CLI:

```bash
huggingface-cli download meta-llama/Llama-3.2-3B-Instruct \
  --local-dir models/Llama-3.2-3B-Instruct
```

For a smaller model (e.g., 1B):

```bash
huggingface-cli download meta-llama/Llama-3.2-1B \
  --local-dir models/Llama-3.2-1B
```

---

## 🚀 Components Overview

1. **vLLM Inference Server**
   An OpenAI-compatible API server powered by `vLLM`, optimized for efficient inference.

2. **Frontend Chatbot**
   A lightweight HTML-based chatbot (`chatbot.html`) served through **Nginx**, which communicates with the vLLM API.

---

## 🧩 Run the vLLM Inference Server (Locally)

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

### 📁 Project Structure

```
vllm-deployment/
├── chatbot.html                     # Frontend chatbot UI
├── nginx.conf                       # Nginx configuration for chatbot frontend
└── README.md
```


### Start the inference server:

```bash
python -m vllm.entrypoints.openai.api_server \
    --model modles/3.1-8b-instruct \
    --max-num-batched-tokens 4096 \
    --gpu-memory-utilization 0.9 \
    --max-model-len 40960 
```

The API will be available at:

```
http://127.0.0.1:8000/v1
```

> 🧠 Use `--host 0.0.0.0` to make the API accessible from other systems.

---

## 🚀 Deployment Methods

You can deploy the **vLLM OpenAI-compatible API server** using one of the following methods based on your environment.

-  Docker Compose (Quick)
-  Plain Docker Command (For Testing)
-  Kubernetes (Complex but resilient and Production Grade)

---

### 🧩 Option 1: Run vLLM with Docker Compose

Use the following command to start the vLLM API server using **Docker Compose** for a simplified, multi-container setup.

```bash
sudo docker compose up
```

📘 For a detailed dockerization workflow and environment configuration, see:
[**Dockerization Guide → docs/dockerize.md**](docs/dockerize.md)

---

### 🐳 Option 2: Run vLLM with Docker Command

Use the following command to launch the **vLLM OpenAI-compatible API server** directly with `docker run`.


```bash
sudo docker run --gpus all \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -v ./models:/app/local_model \
  --env "HUGGING_FACE_HUB_TOKEN=$HF_TOKEN" \
  -p 8000:8000 \
  --ipc=host \
  vllm/vllm-openai:v0.8.0 \
  --model /app/local_model/3.1-8b-instruct \
  --max-model-len 8192
```

**Note:**
- The image `vllm/vllm-openai:v0.8.0` supports **CUDA 12.4**.
- To use the latest CUDA version, switch to `vllm/vllm-openai:latest`.
- Adjust `--max-model-len` according to your GPU’s available memory.


📘 For a detailed dockerization workflow and environment configuration, see:
[**Dockerization Guide → docs/dockerize.md**](docs/dockerize.md)

---

### ☸️ Kubernetes Cluster

🤖 [**Kubernetes Deployment Guide**](kubeadm-cluster/README.md)

---

### ☸️ Option 3: Deploy vLLM on Kubernetes

For **production-grade** or **scalable environments**, vLLM can be deployed as a **Kubernetes workload** using **YAML manifests**, **Helm charts**, or **Kustomize**.

> This deployment integrates seamlessly with the previously configured **Kubernetes High Availability (HA) Cluster Architecture**, ensuring **redundancy**, **resilience**, and **efficient resource utilization**.

#### 🧩 Apply Kubernetes manifests (recommended order):

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

#### ⚙️ Apply all manifests at once:

```bash
kubectl apply -f k8s/
```

> 💡 **Tip:**
>
> * Kubernetes applies YAML files **idempotently**, meaning reapplying them updates only changed resources.
> * However, when deploying from scratch, applying in **logical order** (namespace → config → deployment → service → ingress) ensures dependencies are created correctly.

---

## 5. Test the API

Test the vLLM endpoint using `curl`, change the ip addess accordingly:

```bash
curl http://192.168.1.1:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain in simple terms: What is data science?",
    "max_tokens": 150
  }'
```

- Change the IP address accordingly.

You can also use the **OpenAI Python client** by setting your `base_url` to `http://localhost:8000/v1`.

---

## 🌐 Serve the Chatbot via Nginx

### 🧱 1. Copy the Frontend Website

```bash
# Create a standard web root directory
sudo mkdir -p /var/www/chatbot

# Copy the built frontend files
sudo cp chatbot.html /var/www/chatbot/

# Set proper ownership and permissions for Nginx
sudo chown -R www-data:www-data /var/www/chatbot
sudo chmod -R 755 /var/www/chatbot
```

**📘 Explanation:**

* `/var/www/chatbot` → standard and secure directory for serving web content.
* `www-data` → default Nginx user on Ubuntu/Debian systems.
* `755` permissions → readable by everyone, writable only by owner.

---

### ⚙️ 2. Copy Nginx Configuration Files to System Locations

```bash
# Create the upstreams directory
# (Recommended for modular configs and active health checks)
sudo mkdir -p /etc/nginx/upstreams

# Copy the backend upstream configuration
sudo cp nginx/vllm_backends.conf /etc/nginx/upstreams/vllm_backends.conf

# Copy the main site configuration
sudo cp nginx/nginx.conf /etc/nginx/sites-available/chatbot.conf
```

**📘 Explanation:**

* `/etc/nginx/upstreams/` → keeps backend definitions separate and organized.
* `/etc/nginx/sites-available/` → stores configuration files for all sites.
* `/etc/nginx/sites-enabled/` → holds symbolic links to active sites.

---

### 2. 🔗 Enable the Site

```bash
sudo ln -s /etc/nginx/sites-available/chatbot.conf /etc/nginx/sites-enabled/
```

*(If a file with the same name exists, remove it first: `sudo rm /etc/nginx/sites-enabled/chatbot.conf`)*

---

### 3. ⚙️ Test and Apply Configuration

```bash
# Test syntax
sudo nginx -t

# Apply configuration safely (no downtime)
sudo systemctl reload nginx
```

If Nginx is not running yet:

```bash
sudo systemctl enable nginx
sudo systemctl start nginx
```

---

**(Optional) Nginx Dynamic Health Check:** See the [Dynamci Healthcheck by script](docs/nginx_dynamic_upstreams.md)

Open the chatbot in your browser:

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

