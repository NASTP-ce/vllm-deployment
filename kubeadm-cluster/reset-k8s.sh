#!/bin/bash
# -------------------------------------------------------------------------
# Script: reset-k8s.sh
# Purpose: Completely reset a Kubernetes node (control-plane or worker)
# Author: Jagz version
# -------------------------------------------------------------------------

set -e

echo "🚀 Starting Kubernetes reset on $(hostname)..."

# 1️⃣ Stop kubelet and container runtime
echo "🧩 Stopping kubelet and container runtime..."
sudo systemctl stop kubelet || true
sudo systemctl stop containerd || true
sudo systemctl stop docker || true

# 2️⃣ Reset kubeadm
echo "⚙️  Running kubeadm reset..."
sudo kubeadm reset -f

# 3️⃣ Remove Kubernetes directories
echo "🧹 Removing Kubernetes configuration and certificates..."
sudo rm -rf /etc/kubernetes
sudo rm -rf /var/lib/etcd
sudo rm -rf /var/lib/kubelet
sudo rm -rf /etc/cni/net.d
sudo rm -rf /var/lib/cni/
sudo rm -rf /var/run/kubernetes
sudo rm -rf ~/.kube

echo "[3] Kill leftover control-plane processes..."
# kube-apiserver, kube-controller-manager, kube-scheduler may still be running
pkill -9 kube-apiserver || true
pkill -9 kube-controller-manager || true
pkill -9 kube-scheduler || true
pkill -9 etcd || true

# 4️⃣ Clean up networking (Flannel, Calico, etc.)
echo "🌐 Cleaning up CNI network interfaces..."
sudo ip link delete cni0 2>/dev/null || true
sudo ip link delete flannel.1 2>/dev/null || true
sudo ip link delete vxlan.calico 2>/dev/null || true
sudo ip link delete kube-ipvs0 2>/dev/null || true
sudo ip link delete dummy0 2>/dev/null || true

# 5️⃣ Flush iptables and IPVS rules
echo "🔥 Flushing iptables and IPVS rules..."
sudo iptables -F
sudo iptables -t nat -F
sudo iptables -t mangle -F
sudo iptables -X
if command -v ipvsadm &> /dev/null; then
    sudo ipvsadm --clear
fi

# 6️⃣ Remove leftover container images (optional but recommended)
echo "🐳 Cleaning up old container images..."
sudo crictl rm --all --force >/dev/null 2>&1 || true
sudo crictl rmi --all >/dev/null 2>&1 || true
sudo docker system prune -af >/dev/null 2>&1 || true

# 7️⃣ Restart runtime (optional)
echo "🔁 Restarting container runtime..."
sudo systemctl restart containerd || true

# 8️⃣ Final check
echo "✅ Node $(hostname) has been completely reset!"
echo "👉 You can now re-initialize the cluster with:"
echo "   sudo kubeadm init --config kubeadm-config.yaml --upload-certs"
echo
