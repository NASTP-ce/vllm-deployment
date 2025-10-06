# 🚀 Deploying vLLM on Kubernetes

vLLM provides an OpenAI-compatible API server for inference with large language models. To run it efficiently on Kubernetes, you need GPU-enabled nodes, correct drivers, and proper YAML configurations.

---

## **1. Prepare Your Cluster**

Before deploying, make sure your Kubernetes environment is **GPU-ready**:

1. **GPU Nodes**
   Ensure your worker/control-plane nodes have NVIDIA GPUs like **A100, V100, T4, RTX 3090, RTX 4090**, etc.

   ```bash
   nvidia-smi
   ```

   If this command shows GPU details, drivers are installed.

2. **Install NVIDIA Drivers + Container Toolkit**
   On **each GPU node**:

   ```bash
   # Install NVIDIA drivers (Ubuntu example)
   sudo apt update && sudo apt install -y nvidia-driver-535

   # Install NVIDIA container toolkit for Docker/Containerd
   curl -s -L https://nvidia.github.io/nvidia-container-toolkit/gpgkey | sudo apt-key add -
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-container-toolkit/$distribution/nvidia-container-toolkit.list | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
   sudo apt update
   sudo apt install -y nvidia-container-toolkit
   ```

   Restart container runtime (`docker` or `containerd`) after installation.

3. **Deploy NVIDIA Device Plugin DaemonSet**
   This plugin lets Kubernetes schedule pods with GPUs.

   ```bash
   kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/main/deployments/static/nvidia-device-plugin.yml
   ```

   ✅ Now GPUs are visible inside Kubernetes pods.

---

## **2. Create a Namespace**

Organize workloads by creating a dedicated namespace for vLLM:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: vllm
```

Apply:

```bash
kubectl apply -f namespace.yaml
```

---

## **3. Deployment for vLLM**

Here’s a **Deployment YAML** to run `vllm.entrypoints.openai.api_server`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-deployment
  namespace: vllm
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vllm
  template:
    metadata:
      labels:
        app: vllm
    spec:
      containers:
      - name: vllm
        image: vllm/vllm-openai:latest   # Official vLLM image
        command: ["python3", "-m", "vllm.entrypoints.openai.api_server"]
        args:
          - "--model"
          - "/models/Llama-3.2-3B-Instruct"
          - "--max-num-batched-tokens"
          - "4096"
          - "--gpu-memory-utilization"
          - "0.9"
        ports:
        - containerPort: 8000
        resources:
          limits:
            nvidia.com/gpu: 1   # Request 1 GPU
        volumeMounts:
        - name: model-storage
          mountPath: /models
      volumes:
      - name: model-storage
        hostPath:
          path: /mnt/data/office_work/vllms_inference
```

Apply:

```bash
kubectl apply -f deployment.yaml
```


### 🔑 Key Points

* `nvidia.com/gpu: 1` → Ensures pod is scheduled on GPU node.
* `hostPath` → Mounts local directory with models.
  👉 In production, replace `hostPath` with **PVC** (PersistentVolumeClaim) or **object storage** for scalability.

---

## **4. Expose vLLM API via Service**

To make the API accessible:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: vllm-service
  namespace: vllm
spec:
  selector:
    app: vllm
  ports:
    - protocol: TCP
      port: 80         # External port
      targetPort: 8000 # Container port
  type: LoadBalancer   # NodePort/ClusterIP also possible
```

Apply:

```bash
kubectl apply -f service.yaml
```


Now, the API is available at:
`http://<service-ip>/v1/completions`

---

## **5. (Optional) Ingress for Domain + TLS**

If you want to expose vLLM with a domain name (`vllm.example.com`):

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: vllm-ingress
  namespace: vllm
  annotations:
    kubernetes.io/ingress.class: "nginx"
spec:
  rules:
  - host: vllm.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: vllm-service
            port:
              number: 80
```


Apply:

```bash
kubectl apply -f ingress.yaml
```



👉 Add a TLS block if you’re using **cert-manager** or Let’s Encrypt.

---

## **6. Verify Deployment**

1. Check pods:

   ```bash
   kubectl -n vllm get pods
   ```

2. View logs:

   ```bash
   kubectl -n vllm logs -f <vllm-pod-name>
   ```

3. Test API with `curl`:

   ```bash
   curl http://<service-ip>/v1/completions \
     -H "Content-Type: application/json" \
     -d '{
           "model": "Llama-3.2-3B-Instruct",
           "prompt": "Hello world",
           "max_tokens": 50
         }'
   ```

   ✅ You should see a JSON response like OpenAI’s API.

---
