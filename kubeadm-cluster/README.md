

# Kubernetes Kubeadm Cluster Deployment (On-Prem, Hybrid Control Plane)

This guide describes how to deploy a Kubernetes cluster on 9 on-prem systems (IP range: 192.168.1.1 - 192.168.1.9) using Ansible and kubeadm, with Flannel as the CNI. Cluster initialization uses a kubeadm YAML config file. The control plane consists of 192.168.1.9, 192.168.1.3, and 192.168.1.8. The nodes 192.168.1.3 and 192.168.1.8 act as both control plane and worker nodes.


## Overview

This repository provides a standardized approach for deploying a Kubernetes cluster on-premises using kubeadm and Ansible automation.

### Architecture
- 9 Linux machines (recommended: Ubuntu)
- Control plane nodes: 192.168.1.9, 192.168.1.3, 192.168.1.8 (hybrid nodes)
- Virtual IP for HA: 192.168.1.100 (managed by HAProxy/Keepalived)
- Flannel CNI for networking

### Prerequisites
- Passwordless SSH access from your Ansible control node
- Ansible installed on your control node

### Usage
- All inventory, configuration, and automation details are managed in the [ansible/README_Ansible.md](ansible/README_Ansible.md) file.
- Refer to the Ansible README for:
  - Inventory and host group setup
  - Playbook usage and orchestration
  - Example configuration files (including kubeadm YAML)
  - Directory structure and automation best practices

---


## Steps

1. **Prepare all nodes** (disable swap, install dependencies)
2. **Install containerd** (or Docker)
3. **Install kubeadm, kubelet, kubectl**
4. **Initialize the first control plane node (192.168.1.9)**:
  ```bash
  kubeadm init --config=kubeadm-config.yaml
  ```
5. **Copy kubeconfig to your user**:
  ```bash
  mkdir -p $HOME/.kube
  sudo cp /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config
  ```
6. **Install Flannel CNI**:
  ```bash
  kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
  ```
7. **Join additional control plane nodes (192.168.1.3, 192.168.1.8)** using the `kubeadm join ... --control-plane` command from the init output.
8. **Join worker nodes** (including hybrid nodes) using the standard join command.



## Using Ansible

- See [ansible/README_Ansible.md](ansible/README_Ansible.md) for all automation and configuration details.

---



## Notes

- This setup uses Flannel for networking.
- 192.168.1.3 and 192.168.1.8 act as both control plane and worker nodes.
- High availability is provided via HAProxy and Keepalived (see [docs/high-availability-haproxy-keepalived.md](docs/high-availability-haproxy-keepalived.md)).
- For troubleshooting and advanced configuration, see other markdown files in this directory.

---

