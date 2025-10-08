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

  For [DNS Management](docs/dns.md )

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
| Control Plane 2 | `pc3.k8s.local` | `192.168.1.3` | Control Plane + Worker |
| Control Plane 3 | `pc5.k8s.local` | `192.168.1.5` | Control Plane + Worker |

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
                                |               
  +---------------------------------------------------------------------------------------------------++               
  |   pc2.k8s.local     |  pc4.k8s.local      | pc6.k8s.local     | pc7.k8s.local     | pc8.k8s.local  |
  |   192.168.1.2       |   192.168.1.4       | 192.168.1.6       | 192.168.1.7       | 192.168.1.8    |
  +---------------------------------------------------------------------------------------------------++ 
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

🧑‍💻 For **manual deployment** (step-by-step setup and configuration instructions), see:
[**Manual Kubernetes Deployment Guide → docs/2.configure_master_node.md**](kubeadm-cluster/docs/2.configure_master_node.md)

---

## Spinning up Cluster

Here’s a polished and professional rewrite of that section — consistent with your documentation style and structured for clarity:

---

## 🚀 Spinning Up the Cluster

Before initializing the Kubernetes control plane, pull all required container images to ensure faster setup and consistent versions across all nodes:

```bash
sudo kubeadm config images pull
```

---

### 🧩 Sandbox Image Configuration (Automate via Ansible)

Kubeadm expects the **CRI sandbox image**:
`registry.k8s.io/pause:3.9`

However, some container runtimes (e.g., **containerd**) may default to an older version such as `pause:3.8`.
To prevent compatibility warnings during cluster initialization, update the container runtime configuration.

#### For **containerd**:

Edit the configuration file:

```bash
sudo nano /etc/containerd/config.toml
```

Find and update the following line:

```toml
sandbox_image = "registry.k8s.io/pause:3.9"
```

Then restart the containerd service to apply the change:

```bash
sudo systemctl restart containerd
```

✅ **Tip:**
For consistency across all nodes, this configuration can be automated using **Ansible** by applying the same update to each host’s `/etc/containerd/config.toml`.
 
---

**Validate CRI:**

```bash
sudo crictl --runtime-endpoint unix:///var/run/containerd/containerd.sock version   
```

---

## 🧭 Initialize the First Control Plane Node

On the **primary control plane node** (`192.168.1.1`), initialize the cluster using the declarative configuration file:

```bash
sudo kubeadm init --config=kubeadm-config.yaml
```

---

### ⚠️ If You Encounter Initialization Errors

* Review and resolve any reported issues during the process.
* If necessary, reset the kubeadm setup and retry initialization.
  Refer to: [**Reset Control Plane Node → docs/reset_master_node_new.md**](docs/reset_master_node_new.md)

---

### ⚙️ Configure `kubectl` Access

To manage the cluster from the control plane node, set up the Kubernetes admin configuration:

```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

---

### ✅ Verify the Cluster Status

Check that the control plane node is active and ready:

```bash
kubectl get nodes
```

---


### 🧩 Installing the CNI Plugin

You should install the **CNI (Container Network Interface)** plugin **immediately after initializing the first control plane** and **before joining any worker nodes**.

**Reason:**
Worker nodes depend on a functional pod network to communicate with the control plane.
If no CNI is installed, worker nodes may remain in the `NotReady` state.

---

### 🌐 Option 1 — Install **Calico** (Advanced networking)

On the **first control plane node (`192.168.1.1`)**, install Calico after completing `kubeadm init`:

```bash
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/calico.yaml
```

---

### 🌐 Option 2 — Install **Flannel** (Basic overlay network)

Alternatively, deploy **Flannel** to enable pod-to-pod networking:

```bash
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
```

---

### ✅ Verify CNI Installation

Check that all CNI-related pods (Calico or Flannel) are running successfully:

```bash
kubectl get pods -n kube-system
```

Wait until all pods report a `Running` status before proceeding to join other control planes or worker nodes.


## 🧩 Join Additional Control Plane Nodes

Once the first control plane (`192.168.1.1`) is initialized, the remaining control plane nodes (`192.168.1.3` and `192.168.1.5`) can be joined to the cluster for high availability.

### 📜 Generate the Join Command on the Primary Node

On the first control plane node (`192.168.1.1`), generate a join command with a control-plane token and discovery certificate hash:

```bash
kubeadm token create --print-join-command
```

Example output:

```bash
kubeadm join 192.168.1.100:6443 --token <token> \
  --discovery-token-ca-cert-hash sha256:<hash> \
  --control-plane
```

> 🧠 **Tip (Memorization Trick):**
> Remember “**Join–Token–Hash–Control**” → the 4 ingredients for every HA control-plane join.

---

### 🖥️ Run the Join Command on Each Additional Control Plane Node

On nodes `192.168.1.3` and `192.168.1.5`, execute the generated join command:

```bash
sudo kubeadm join 192.168.1.100:6443 --token <token> \
  --discovery-token-ca-cert-hash sha256:<hash> \
  --control-plane
```

> Replace `192.168.1.100` with your **HAProxy VIP** or API load balancer address.

---

### 🔄 Verify Control Plane Nodes

After all control planes are joined, check cluster status from the primary control plane:

```bash
kubectl get nodes -o wide
```

Expected output:

```
NAME            STATUS   ROLES           AGE   VERSION   INTERNAL-IP
cp-1 (192.168.1.1)   Ready    control-plane   10m   v1.30.0   192.168.1.1
cp-2 (192.168.1.3)   Ready    control-plane   2m    v1.30.0   192.168.1.3
cp-3 (192.168.1.5)   Ready    control-plane   1m    v1.30.0   192.168.1.5
```

---

## ⚙️ Join Worker Nodes to the Cluster

After installing the CNI and confirming all control planes are `Ready`, join your worker nodes.

On each worker node (e.g., `192.168.1.7`, `192.168.1.9`), run the **join command** generated from the control plane:

```bash
sudo kubeadm join 192.168.1.100:6443 --token <token> \
  --discovery-token-ca-cert-hash sha256:<hash>
```

> Use the same **HAProxy VIP (192.168.1.100)** for consistent access.

---

### 🧾 Verify the Cluster

From any control plane node:

```bash
kubectl get nodes -o wide
```

Expected output:

```
NAME             STATUS   ROLES           AGE   VERSION   INTERNAL-IP
pc-1             Ready    control-plane   10m   v1.30.0   192.168.1.1
pc-3             Ready    control-plane   8m    v1.30.0   192.168.1.3
pc-5             Ready    control-plane   7m    v1.30.0   192.168.1.5
pc-2         	 Ready    <none>          3m    v1.30.0   192.168.1.7
pc-4         	 Ready    <none>          2m    v1.30.0   192.168.1.9
pc-6         	 Ready    <none>          3m    v1.30.0   192.168.1.7
pc-7         	 Ready    <none>          2m    v1.30.0   192.168.1.9
pc-8         	 Ready    <none>          3m    v1.30.0   192.168.1.7
```


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