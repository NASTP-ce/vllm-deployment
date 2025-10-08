# On-Premises Kubernetes Cluster with Kubeadm and Ansible

This guide provides a comprehensive approach to deploying a high-availability (HA) Kubernetes cluster on a 9-node on-premises environment. The deployment is automated using Ansible and initialized with `kubeadm`, featuring a hybrid control plane configuration.

Excellent — you’re building a complete **Kubernetes HA cluster design document**, so I’ve merged your new information into the previously polished architecture section.
Here’s the **final, professional, documentation-ready version** — ideal for internal documentation, GitHub repos, or deployment guides.

---

# Cluster Architecture

The Kubernetes cluster is architected for **high availability (HA)**, **scalability**, and **efficient resource utilization**. The design ensures uninterrupted operation and fault tolerance through redundant load balancers, multi-node control planes, and distributed worker nodes.

---

## Overview

* **Operating System:** Linux (Ubuntu recommended)
* **Total Nodes:** 10
* **IP Range:** `192.168.1.1` – `192.168.1.10`
* **Virtual IP (VIP):** `192.168.1.100` — managed by **HAProxy** and **Keepalived** to provide a stable endpoint for the Kubernetes API server
* **Cluster Domain (Example):** `k8s.local`
* **Networking:** [Flannel](https://github.com/flannel-io/flannel) is used as the Container Network Interface (CNI) for cluster networking
* **Cluster Initialization:** The cluster is bootstrapped using a `kubeadm-config.yaml` file for consistent, declarative setup
* **HA Documentation:**
  For complete setup and failover details, see
  👉 [docs/high-availability-haproxy-keepalived.md](docs/high-availability-haproxy-keepalived.md)

---

## Load Balancer Layer

Two dedicated nodes serve as HAProxy load balancers in **active–passive mode**, managed by Keepalived for automatic VIP failover.

| Role            | Hostname / FQDN | IP Address     | Description                       |
| --------------- | --------------- | -------------- | --------------------------------- |
| Load Balancer 1 | `lb1.k8s.local` | `192.168.1.9`  | Primary HAProxy node              |
| Load Balancer 2 | `lb2.k8s.local` | `192.168.1.10` | Secondary HAProxy node (failover) |

**Virtual IP (VIP):** `192.168.1.100` — accessible via `api.k8s.local`

---

## Control Plane Layer

Three hybrid nodes (control + worker) maintain cluster state and provide API server redundancy. Kubernetes control components (API server, etcd, scheduler, controller-manager) are distributed across these nodes.

| Node            | Hostname / FQDN | IP Address    | Role                   |
| --------------- | --------------- | ------------- | ---------------------- |
| Control Plane 1 | `pc1.k8s.local` | `192.168.1.1` | Control Plane + Worker |
| Control Plane 2 | `cp3.k8s.local` | `192.168.1.3` | Control Plane + Worker |
| Control Plane 3 | `cp5.k8s.local` | `192.168.1.5` | Control Plane + Worker |

---

## Worker Node Layer

Dedicated worker nodes handle all user workloads and deployments.

| Node     | Hostname / FQDN     | IP Address    | Role   |
| -------- | ------------------- | ------------- | ------ |
| Worker 1 | `pc2.k8s.local` | `192.168.1.2` | Worker |
| Worker 2 | `pc4.k8s.local` | `192.168.1.4` | Worker |
| Worker 3 | `pc6.k8s.local` | `192.168.1.6` | Worker |
| Worker 4 | `pc7.k8s.local` | `192.168.1.7` | Worker |
| Worker 5 | `pc8.k8s.local` | `192.168.1.8` | Worker |

---

## Textual Topology Diagram

```
                    +-------------------------------------+
                    |  Virtual IP: 192.168.1.100          |
                    |  DNS: api.k8s.local                 |
                    |  (HAProxy + Keepalived)             |
                    +-------------------------------------+
                              /              \
                 +-------------------+   +-------------------+
                 | lb1.k8s.local     |   | lb2.k8s.local     |
                 | 192.168.1.9       |   | 192.168.1.10      |
                 +-------------------+   +-------------------+
                              |
                 ---------------------------------
                 |          API Traffic          |
                 ---------------------------------
                              |
        +-----------------------------------------------+
        |         Control Plane (HA, Hybrid)            |
        | pc1.k8s.local | pc3.k8s.local | pc5.k8s.local |
        | 192.168.1.1   | 192.168.1.3   | 192.168.1.5   |
        +-----------------------------------------------+
                              |
                 ---------------------------------
                 |          Worker Nodes         |
                 ---------------------------------
  pc1.k8s.local | worker2.k8s.local | worker3.k8s.local | worker4.k8s.local | worker5.k8s.local
  192.168.1.2       | 192.168.1.4       | 192.168.1.6       | 192.168.1.7       | 192.168.1.8
```

---

# Prerequisites

Before starting the deployment, ensure all required configuration files and environment settings are properly prepared.

### Configuration Validation

* **`kubeadm-config.yaml`**: Verify that the Kubernetes version and Flannel network settings are correct for your environment.

  * Set the Flannel subnet:

    ```yaml
    podSubnet: "10.244.0.0/16"
    ```
  * Check the latest supported Kubernetes versions at:
    [https://kubernetes.io/releases/](https://kubernetes.io/releases/)

Update these configurations if required **before initializing the cluster**.

---

### Hostname and DNS Configuration

Set Hostname of the systems:

```bash
sudo hostnamectl set-hostname new-hostname
```

Add the hostname-to-IP mappings on each node in `/etc/hosts`.
For example:

```bash
echo "192.168.1.9  lb1.k8s.local" | sudo tee -a /etc/hosts
echo "192.168.1.10 lb2.k8s.local" | sudo tee -a /etc/hosts
echo "192.168.1.1  pc11.k8s.local" | sudo tee -a /etc/hosts
echo "192.168.1.3  pc2.k8s.local" | sudo tee -a /etc/hosts
echo "192.168.1.5  pc3.k8s.local" | sudo tee -a /etc/hosts
echo "192.168.1.2  pc1.k8s.local" | sudo tee -a /etc/hosts
echo "192.168.1.4  pc4.k8s.local" | sudo tee -a /etc/hosts
echo "192.168.1.6  pc6.k8s.local" | sudo tee -a /etc/hosts
echo "192.168.1.7  pc7.k8s.local" | sudo tee -a /etc/hosts
echo "192.168.1.8  pc8.k8s.local" | sudo tee -a /etc/hosts
# (Repeat for all nodes)
```

---

### System Requirements

Before you begin, ensure the following:

* **Ansible Control Node:** A management host with Ansible installed.
* **Passwordless SSH:** Passwordless SSH access from the Ansible control node to all 9 cluster nodes.

---

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

2. **Validate CRI:**

   ```bash
   crictl --runtime-endpoint unix:///var/run/containerd/containerd.sock version   
   ```
   
2. **Initialize the First Control Plane Node**

   On node `192.168.1.9`, run the initialization using the declarative configuration file:

   ```bash
   sudo kubeadm init --config=kubeadm-config.yaml
   ```


2. **If You Encounter Errors During Initialization**

  - Troubleshoot and resolve any reported errors.
  - If needed, reset kubeadm and retry the initialization:

    ```bash
    sudo kubeadm reset -f
    ```

  - For a detailed reset procedure, see: [docs/reset_master_node_new.md](docs/reset_master_node_new.md)

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