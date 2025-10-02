
-----


# On-Premises Kubernetes Cluster with Kubeadm and Ansible

This guide provides a comprehensive approach to deploying a high-availability (HA) Kubernetes cluster on a 9-node on-premises environment. The deployment is automated using Ansible and initialized with `kubeadm`, featuring a hybrid control plane configuration.

## Cluster Architecture

The cluster is designed for resilience and efficient resource utilization with the following architecture:

  * **Total Nodes**: 9 Linux systems (Ubuntu recommended).
  * **IP Range**: `192.168.1.1` - `192.168.1.9`.
  * **Control Plane**: A 3-node HA control plane is established on the following nodes:
      * `192.168.1.9` (dedicated control plane)
      * `192.168.1.3` (hybrid: control plane + worker)
      * `192.168.1.8` (hybrid: control plane + worker)
  * **High Availability**: A virtual IP (`192.168.1.100`) managed by HAProxy and Keepalived acts as a stable endpoint for the Kubernetes API server.
  **For complete instructions on High Availability, please refer to [docs/high-availability-haproxy-keepalived.md](docs/high-availability-haproxy-keepalived.md)**
  * **Networking**: Flannel is used as the Container Network Interface (CNI) for cluster networking.
  * **Initialization**: The cluster is bootstrapped using a `kubeadm-config.yaml` file to ensure a consistent and declarative setup.

## Prerequisites

Before starting, verify and update your configuration files as needed:

- **kubeadm-config.yaml**: Ensure the Kubernetes version and Flannel pod network settings are correct for your environment.
  - For Flannel, set `podSubnet: "10.244.0.0/16"` in your config.
  - For Kubernetes version, check the latest release at: [https://kubernetes.io/releases/](https://kubernetes.io/releases/)

Update these files if required before running the cluster initialization steps.

---

### Add it to /etc/hosts. For example:

```bash
echo "192.168.1.9  control-plane-1" | sudo tee -a /etc/hosts
```

---

Before you begin, ensure the following requirements are met:

  * **Ansible Control Node**: A machine with Ansible installed.
  * **Passwordless SSH**: Configure passwordless SSH access from the Ansible control node to all 9 cluster nodes.
  * **Node Preparation**: All cluster nodes must have swap disabled.

## Automated Deployment (Recommended)

This repository is designed for automation. All inventory, configuration variables, and playbooks are managed within the `ansible/` directory.

**For complete instructions on automated deployment, please refer to [ansible/README_Ansible.md](ansible/README_Ansible.md)**

This includes details on:

  * Setting up the Ansible inventory and host groups.
  * Customizing cluster configuration variables.
  * Executing the deployment playbooks.
  * Directory structure and automation best practices.

## Manual Deployment Steps

For reference or manual setup, the following steps outline the process performed by the automation scripts.

**Prepare All Nodes**

      * Disable swap.
      * Install container runtime (e.g., `containerd`).
      * Install Kubernetes packages: `kubeadm`, `kubelet`, and `kubectl`.

---

## Spinning up Cluster

### Sandbox Image Note (change it with ansible for all nodes)

Kubeadm expects the CRI sandbox image `registry.k8s.io/pause:3.9`, but some runtimes (e.g., containerd) may default to `pause:3.8`. To avoid warnings during cluster initialization, update your container runtime configuration.

For **containerd**, edit `/etc/containerd/config.toml` and set:

```toml
sandbox_image = "registry.k8s.io/pause:3.9"
```

Then restart containerd:

```bash
sudo systemctl restart containerd
```

---


1. **Stop HAProxy Temporarily**

   Stop the HAProxy service so that port **6443** is free for the cluster initialization (recommended).

   ```bash
   sudo systemctl stop haproxy
   ```

2. **Initialize the First Control Plane Node**

   On node `192.168.1.9`, run the initialization using the declarative configuration file:

   ```bash
   sudo kubeadm init --config=kubeadm-config.yaml
   ```

3. **Restart HAProxy**

   After the initialization completes, start the HAProxy service again:

   ```bash
   sudo systemctl start haproxy
   ```

---


3.  **Configure `kubectl`**

      * To manage the cluster from the control plane node, copy the admin configuration:
        ```bash
        mkdir -p $HOME/.kube
        sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
        sudo chown $(id -u):$(id -g) $HOME/.kube/config
        ```

4.  **Install the CNI Plugin**

      * Deploy Flannel to enable pod-to-pod communication:
        ```bash
        kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
        ```

5.  **Join Additional Nodes**

      * **Control Plane Nodes**: Use the `kubeadm join` command provided in the output of the `init` step (with the `--control-plane` flag) to join `192.168.1.3` and `192.168.1.8`.
      * **Worker Nodes**: Use the standard `kubeadm join` command to add the remaining worker nodes to the cluster.


---

### 📝 (Optional) Removing Control-Plane Taints (Hybrid Setup)

By default, Kubernetes taints all control-plane nodes with:

```bash
node-role.kubernetes.io/control-plane:NoSchedule
```

This prevents workloads from being scheduled on control-plane nodes.
Since we are running a **hybrid control-plane + worker setup**, we must remove these taints.

Run the following commands after initializing the cluster and joining all control-plane nodes:

```bash
# Remove taint from control-plane-1
kubectl taint nodes control-plane-1 node-role.kubernetes.io/control-plane:NoSchedule-

# Remove taint from control-plane-2
kubectl taint nodes control-plane-2 node-role.kubernetes.io/control-plane:NoSchedule-

# Remove taint from control-plane-3
kubectl taint nodes control-plane-3 node-role.kubernetes.io/control-plane:NoSchedule-
```

---

✅ **Verification:**
After running the commands, check that no taints remain:

```bash
kubectl describe node control-plane-1 | grep Taints
kubectl describe node control-plane-2 | grep Taints
kubectl describe node control-plane-3 | grep Taints
```

Output should be:

```bash
Taints:     <none>
```

---

💡 **Tip (memorization):** Think of the taint as a **“No-Entry 🚫 sign”**. Running `kubectl taint … -` is like **erasing the sign**, allowing pods to enter and run on your control-plane nodes.

---

👉 Do you also want me to give you a **one-liner command** that removes the taint from *all control-plane nodes at once*, instead of listing them one by one?


-----

### Additional Information

  * **Hybrid Nodes**: The nodes `192.168.1.3` and `192.168.1.8` are configured to run workloads alongside control plane components.
  * **HA Configuration**: For a detailed explanation of the HAProxy and Keepalived setup, see the document in `docs/high-availability-haproxy-keepalived.md`.
  * **Troubleshooting**: Refer to other markdown files in this repository for advanced configuration and troubleshooting tips.