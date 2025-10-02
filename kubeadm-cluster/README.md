Excellent! Using Ansible for GPU-enabled Kubernetes cluster setup is a great approach. Let me provide you with a comprehensive Ansible-based solution for your 8 Ubuntu machines with GPUs.

## **Updated Production Architecture for GPU Workloads**

```
┌─────────────────────────────────────────────────────────┐
│              8 Physical Ubuntu Servers with GPUs         │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │    HAProxy + Keepalived (on Control Planes)      │  │
│  │              VIP: 192.168.1.180                   │  │
│  └────────────────────┬─────────────────────────────┘  │
│                       │                                 │
│  ┌────────────────────┼────────────────────┐           │
│  │                    │                    │           │
│  ▼                    ▼                    ▼           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Control     │  │ Control     │  │ Control     │   │
│  │ Plane 1     │  │ Plane 2     │  │ Plane 3     │   │
│  │ (No GPU)    │  │ (No GPU)    │  │ (No GPU)    │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │              GPU Worker Nodes                     │ │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ GPU Worker 1│  │ GPU Worker 2│  │ GPU Worker 3│  │
│  │ NVIDIA GPU  │  │ NVIDIA GPU  │  │ NVIDIA GPU  │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│  ┌─────────────┐  ┌─────────────┐                    │
│  │ GPU Worker 4│  │ GPU Worker 5│                    │
│  │ NVIDIA GPU  │  │ NVIDIA GPU  │                    │
│  └─────────────┘  └─────────────┘                    │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## **Complete Ansible Project Structure**

```
kubernetes-gpu-cluster/
├── ansible.cfg
├── inventory/
│   ├── hosts.ini
│   └── group_vars/
│       ├── all.yml
│       ├── control_plane.yml
│       └── workers.yml
├── playbooks/
│   ├── 01-prepare-all-nodes.yml
│   ├── 02-install-containerd.yml
│   ├── 03-install-kubernetes.yml
│   ├── 04-setup-gpu-drivers.yml
│   ├── 05-init-control-plane.yml
│   ├── 06-join-control-planes.yml
│   ├── 07-join-workers.yml
│   ├── 08-install-cni.yml
│   ├── 09-install-gpu-operator.yml
│   └── 10-verify-cluster.yml
├── roles/
│   ├── common/
│   │   └── tasks/
│   │       └── main.yml
│   ├── containerd/
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   └── templates/
│   │       └── config.toml.j2
│   ├── kubeadm/
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   └── templates/
│   │       └── kubeadm-config.yaml.j2
│   ├── haproxy/
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   └── templates/
│   │       ├── haproxy.cfg.j2
│   │       └── keepalived.conf.j2
│   ├── nvidia-gpu/
│   │   └── tasks/
│   │       └── main.yml
│   └── gpu-operator/
│       └── tasks/
│           └── main.yml
└── README.md
```

---

## **1. Ansible Configuration Files**

### **ansible.cfg**
```ini
[defaults]
inventory = inventory/hosts.ini
remote_user = your_username
host_key_checking = False
retry_files_enabled = False
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible_facts
fact_caching_timeout = 3600

[privilege_escalation]
become = True
become_method = sudo
become_user = root
become_ask_pass = False

[ssh_connection]
pipelining = True
ssh_args = -o ControlMaster=auto -o ControlPersist=60s
```

---

### **inventory/hosts.ini**
```ini
[control_plane]
k8s-cp-1 ansible_host=192.168.1.181 node_ip=192.168.1.181
k8s-cp-2 ansible_host=192.168.1.182 node_ip=192.168.1.182
k8s-cp-3 ansible_host=192.168.1.183 node_ip=192.168.1.183

[workers]
k8s-worker-1 ansible_host=192.168.1.191 node_ip=192.168.1.191
k8s-worker-2 ansible_host=192.168.1.192 node_ip=192.168.1.192
k8s-worker-3 ansible_host=192.168.1.193 node_ip=192.168.1.193
k8s-worker-4 ansible_host=192.168.1.194 node_ip=192.168.1.194
k8s-worker-5 ansible_host=192.168.1.195 node_ip=192.168.1.195

[master]
k8s-cp-1 ansible_host=192.168.1.181 node_ip=192.168.1.181

[secondary_masters]
k8s-cp-2 ansible_host=192.168.1.182 node_ip=192.168.1.182
k8s-cp-3 ansible_host=192.168.1.183 node_ip=192.168.1.183

[gpu_workers]
k8s-worker-1 ansible_host=192.168.1.191 node_ip=192.168.1.191
k8s-worker-2 ansible_host=192.168.1.192 node_ip=192.168.1.192
k8s-worker-3 ansible_host=192.168.1.193 node_ip=192.168.1.193
k8s-worker-4 ansible_host=192.168.1.194 node_ip=192.168.1.194
k8s-worker-5 ansible_host=192.168.1.195 node_ip=192.168.1.195

[all:vars]
ansible_user=your_username
ansible_python_interpreter=/usr/bin/python3
```

---

### **inventory/group_vars/all.yml**
```yaml
---
# Kubernetes Configuration
kubernetes_version: "1.32"
kubernetes_version_full: "1.32.0-1.1"
pod_network_cidr: "172.16.0.0/16"
service_cidr: "10.96.0.0/12"
cluster_name: "gpu-k8s-cluster"

# Control Plane VIP
control_plane_vip: "192.168.1.180"
control_plane_port: 6443

# Network Configuration
network_interface: "enp0s3"  # Change to your interface (use 'ip a')

# Container Runtime
containerd_version: "latest"
containerd_config_dir: "/etc/containerd"

# CNI Plugin
cni_plugin: "calico"  # calico or flannel
calico_version: "v3.27.0"

# GPU Configuration
nvidia_driver_version: "545"  # Latest stable driver
install_cuda: true
cuda_version: "12-3"  # CUDA 12.3

# System Configuration
disable_swap: true
configure_firewall: true
update_system: true

# Hostnames and IPs
hosts_entries:
  - { ip: "192.168.1.180", hostname: "k8s-api-vip k8s-api" }
  - { ip: "192.168.1.181", hostname: "k8s-cp-1" }
  - { ip: "192.168.1.182", hostname: "k8s-cp-2" }
  - { ip: "192.168.1.183", hostname: "k8s-cp-3" }
  - { ip: "192.168.1.191", hostname: "k8s-worker-1" }
  - { ip: "192.168.1.192", hostname: "k8s-worker-2" }
  - { ip: "192.168.1.193", hostname: "k8s-worker-3" }
  - { ip: "192.168.1.194", hostname: "k8s-worker-4" }
  - { ip: "192.168.1.195", hostname: "k8s-worker-5" }
```

---

## **2. Complete Playbooks**

### **playbooks/01-prepare-all-nodes.yml**
```yaml
---
- name: Prepare all nodes for Kubernetes
  hosts: all
  become: true
  
  tasks:
    - name: Update apt cache
      ansible.builtin.apt:
        update_cache: yes
        cache_valid_time: 3600
      when: update_system | default(true)

    - name: Upgrade all packages
      ansible.builtin.apt:
        upgrade: dist
      when: update_system | default(true)

    - name: Install required packages
      ansible.builtin.apt:
        name:
          - apt-transport-https
          - ca-certificates
          - curl
          - gnupg
          - lsb-release
          - software-properties-common
          - net-tools
          - vim
          - git
          - wget
          - htop
          - nfs-common
        state: present

    - name: Set hostnames
      ansible.builtin.hostname:
        name: "{{ inventory_hostname }}"

    - name: Update /etc/hosts
      ansible.builtin.lineinfile:
        path: /etc/hosts
        line: "{{ item.ip }}  {{ item.hostname }}"
        state: present
      loop: "{{ hosts_entries }}"

    - name: Disable swap immediately
      ansible.builtin.command: swapoff -a
      when: ansible_swaptotal_mb > 0

    - name: Remove swap entry from /etc/fstab
      ansible.builtin.replace:
        path: /etc/fstab
        regexp: '^(\S+\s+\S+\s+swap\s+.*)$'
        replace: '# \1'
      when: disable_swap | default(true)

    - name: Ensure swapfile is absent
      ansible.builtin.file:
        path: /swapfile
        state: absent
      ignore_errors: true

    - name: Load kernel modules
      ansible.builtin.copy:
        content: |
          overlay
          br_netfilter
        dest: /etc/modules-load.d/k8s.conf
        mode: '0644'

    - name: Load modules immediately
      community.general.modprobe:
        name: "{{ item }}"
        state: present
      loop:
        - overlay
        - br_netfilter

    - name: Configure sysctl parameters
      ansible.builtin.copy:
        content: |
          net.bridge.bridge-nf-call-iptables  = 1
          net.bridge.bridge-nf-call-ip6tables = 1
          net.ipv4.ip_forward                 = 1
        dest: /etc/sysctl.d/k8s.conf
        mode: '0644'

    - name: Apply sysctl parameters
      ansible.builtin.command: sysctl --system

    - name: Configure UFW firewall for control plane
      community.general.ufw:
        rule: allow
        port: "{{ item }}"
        proto: tcp
      loop:
        - "6443"
        - "2379:2380"
        - "10250"
        - "10259"
        - "10257"
      when: 
        - configure_firewall | default(true)
        - inventory_hostname in groups['control_plane']

    - name: Configure UFW firewall for workers
      community.general.ufw:
        rule: allow
        port: "{{ item.port }}"
        proto: "{{ item.proto }}"
      loop:
        - { port: "10250", proto: "tcp" }
        - { port: "30000:32767", proto: "tcp" }
        - { port: "179", proto: "tcp" }
        - { port: "4789", proto: "udp" }
      when: 
        - configure_firewall | default(true)
        - inventory_hostname in groups['workers']

    - name: Enable UFW
      community.general.ufw:
        state: enabled
      when: configure_firewall | default(true)

    - name: Reboot nodes if needed
      ansible.builtin.reboot:
        reboot_timeout: 300
      when: update_system | default(true)
```

---

### **playbooks/02-install-containerd.yml**
```yaml
---
- name: Install and configure containerd
  hosts: all
  become: true
  
  tasks:
    - name: Add Docker GPG key
      ansible.builtin.apt_key:
        url: https://download.docker.com/linux/ubuntu/gpg
        keyring: /usr/share/keyrings/docker-archive-keyring.gpg
        state: present

    - name: Add Docker repository
      ansible.builtin.apt_repository:
        repo: "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
        state: present
        filename: docker

    - name: Install containerd
      ansible.builtin.apt:
        name: containerd.io
        state: present
        update_cache: yes

    - name: Create containerd config directory
      ansible.builtin.file:
        path: /etc/containerd
        state: directory
        mode: '0755'

    - name: Generate default containerd config
      ansible.builtin.shell: containerd config default > /etc/containerd/config.toml
      args:
        creates: /etc/containerd/config.toml

    - name: Configure containerd to use systemd cgroup
      ansible.builtin.replace:
        path: /etc/containerd/config.toml
        regexp: 'SystemdCgroup = false'
        replace: 'SystemdCgroup = true'

    - name: Update sandbox image in containerd config
      ansible.builtin.replace:
        path: /etc/containerd/config.toml
        regexp: 'sandbox_image = ".*"'
        replace: 'sandbox_image = "registry.k8s.io/pause:3.9"'

    - name: Restart containerd
      ansible.builtin.systemd:
        name: containerd
        state: restarted
        enabled: yes
        daemon_reload: yes

    - name: Wait for containerd to be ready
      ansible.builtin.wait_for:
        timeout: 10
```

---

### **playbooks/03-install-kubernetes.yml**
```yaml
---
- name: Install Kubernetes components
  hosts: all
  become: true
  
  tasks:
    - name: Add Kubernetes GPG key
      ansible.builtin.apt_key:
        url: https://pkgs.k8s.io/core:/stable:/v{{ kubernetes_version }}/deb/Release.key
        keyring: /etc/apt/keyrings/kubernetes-apt-keyring.gpg
        state: present

    - name: Add Kubernetes repository
      ansible.builtin.apt_repository:
        repo: "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v{{ kubernetes_version }}/deb/ /"
        state: present
        filename: kubernetes

    - name: Install Kubernetes components
      ansible.builtin.apt:
        name:
          - kubelet
          - kubeadm
          - kubectl
        state: present
        update_cache: yes

    - name: Hold Kubernetes packages
      ansible.builtin.dpkg_selections:
        name: "{{ item }}"
        selection: hold
      loop:
        - kubelet
        - kubeadm
        - kubectl

    - name: Enable kubelet service
      ansible.builtin.systemd:
        name: kubelet
        enabled: yes
        state: started

    - name: Verify kubeadm installation
      ansible.builtin.command: kubeadm version
      register: kubeadm_version
      changed_when: false

    - name: Display kubeadm version
      ansible.builtin.debug:
        var: kubeadm_version.stdout
```

---

### **playbooks/04-setup-gpu-drivers.yml**
```yaml
---
- name: Install NVIDIA GPU drivers and CUDA
  hosts: gpu_workers
  become: true
  
  tasks:
    - name: Check if NVIDIA driver is already installed
      ansible.builtin.command: nvidia-smi
      register: nvidia_check
      ignore_errors: true
      changed_when: false

    - name: Add NVIDIA package repositories
      ansible.builtin.apt:
        deb: https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
        state: present
      when: nvidia_check.rc != 0

    - name: Update apt cache after adding NVIDIA repos
      ansible.builtin.apt:
        update_cache: yes
      when: nvidia_check.rc != 0

    - name: Install NVIDIA driver
      ansible.builtin.apt:
        name: "nvidia-driver-{{ nvidia_driver_version }}"
        state: present
      when: nvidia_check.rc != 0

    - name: Install CUDA toolkit
      ansible.builtin.apt:
        name: "cuda-{{ cuda_version }}"
        state: present
      when: 
        - nvidia_check.rc != 0
        - install_cuda | default(true)

    - name: Install nvidia-container-toolkit
      block:
        - name: Add NVIDIA Container Toolkit GPG key
          ansible.builtin.get_url:
            url: https://nvidia.github.io/libnvidia-container/gpgkey
            dest: /usr/share/keyrings/nvidia-container-toolkit-keyring.asc

        - name: Add NVIDIA Container Toolkit repository
          ansible.builtin.apt_repository:
            repo: "deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.asc] https://nvidia.github.io/libnvidia-container/stable/deb/$(ARCH) /"
            state: present
            filename: nvidia-container-toolkit

        - name: Install nvidia-container-toolkit
          ansible.builtin.apt:
            name: nvidia-container-toolkit
            state: present
            update_cache: yes

    - name: Configure containerd for NVIDIA runtime
      ansible.builtin.shell: |
        nvidia-ctk runtime configure --runtime=containerd
      when: nvidia_check.rc != 0

    - name: Restart containerd after GPU configuration
      ansible.builtin.systemd:
        name: containerd
        state: restarted

    - name: Reboot GPU workers to load drivers
      ansible.builtin.reboot:
        reboot_timeout: 300
      when: nvidia_check.rc != 0

    - name: Wait for GPU workers to come back
      ansible.builtin.wait_for_connection:
        delay: 30
        timeout: 300
      when: nvidia_check.rc != 0

    - name: Verify NVIDIA driver installation
      ansible.builtin.command: nvidia-smi
      register: nvidia_smi_output
      changed_when: false

    - name: Display nvidia-smi output
      ansible.builtin.debug:
        var: nvidia_smi_output.stdout_lines
```

---

### **playbooks/05-init-control-plane.yml**
```yaml
---
- name: Initialize first control plane node
  hosts: master
  become: true
  
  tasks:
    - name: Install HAProxy and Keepalived
      ansible.builtin.apt:
        name:
          - haproxy
          - keepalived
        state: present

    - name: Configure HAProxy
      ansible.builtin.template:
        src: ../roles/haproxy/templates/haproxy.cfg.j2
        dest: /etc/haproxy/haproxy.cfg
        mode: '0644'

    - name: Configure Keepalived
      ansible.builtin.template:
        src: ../roles/haproxy/templates/keepalived.conf.j2
        dest: /etc/keepalived/keepalived.conf
        mode: '0644'
      vars:
        keepalived_state: "MASTER"
        keepalived_priority: 101

    - name: Start and enable HAProxy and Keepalived
      ansible.builtin.systemd:
        name: "{{ item }}"
        state: started
        enabled: yes
      loop:
        - haproxy
        - keepalived

    - name: Create kubeadm config file
      ansible.builtin.template:
        src: ../roles/kubeadm/templates/kubeadm-config.yaml.j2
        dest: /root/kubeadm-config.yaml
        mode: '0600'

    - name: Initialize Kubernetes cluster
      ansible.builtin.command: kubeadm init --config=/root/kubeadm-config.yaml --upload-certs
      args:
        creates: /etc/kubernetes/admin.conf
      register: kubeadm_init

    - name: Save kubeadm init output
      ansible.builtin.copy:
        content: "{{ kubeadm_init.stdout }}"
        dest: /root/kubeadm-init-output.txt
        mode: '0600'
      when: kubeadm_init.changed

    - name: Extract join command for control planes
      ansible.builtin.shell: |
        grep -A 2 "control-plane" /root/kubeadm-init-output.txt | tail -3 | tr -d '\\' | tr -d '\n'
      register: join_command_control_plane
      when: kubeadm_init.changed

    - name: Extract join command for workers
      ansible.builtin.shell: |
        grep -A 1 "kubeadm join" /root/kubeadm-init-output.txt | tail -2 | tr -d '\\' | tr -d '\n'
      register: join_command_workers
      when: kubeadm_init.changed

    - name: Save join commands to local file
      ansible.builtin.copy:
        content: |
          # Control Plane Join Command
          {{ join_command_control_plane.stdout }}
          
          # Worker Join Command
          {{ join_command_workers.stdout }}
        dest: ./join-commands.txt
        mode: '0600'
      delegate_to: localhost
      when: kubeadm_init.changed

    - name: Create .kube directory for root
      ansible.builtin.file:
        path: /root/.kube
        state: directory
        mode: '0755'

    - name: Copy admin.conf to .kube/config
      ansible.builtin.copy:
        src: /etc/kubernetes/admin.conf
        dest: /root/.kube/config
        remote_src: yes
        mode: '0600'

    - name: Create .kube directory for regular user
      ansible.builtin.file:
        path: "/home/{{ ansible_user }}/.kube"
        state: directory
        owner: "{{ ansible_user }}"
        group: "{{ ansible_user }}"
        mode: '0755'

    - name: Copy admin.conf for regular user
      ansible.builtin.copy:
        src: /etc/kubernetes/admin.conf
        dest: "/home/{{ ansible_user }}/.kube/config"
        remote_src: yes
        owner: "{{ ansible_user }}"
        group: "{{ ansible_user }}"
        mode: '0600'

    - name: Fetch kubeconfig to local machine
      ansible.builtin.fetch:
        src: /etc/kubernetes/admin.conf
        dest: ./kubeconfig
        flat: yes
```

---

### **playbooks/06-join-control-planes.yml**
```yaml
---
- name: Join additional control plane nodes
  hosts: secondary_masters
  become: true
  serial: 1
  
  tasks:
    - name: Install HAProxy and Keepalived
      ansible.builtin.apt:
        name:
          - haproxy
          - keepalived
        state: present

    - name: Configure HAProxy
      ansible.builtin.template:
        src: ../roles/haproxy/templates/haproxy.cfg.j2
        dest: /etc/haproxy/haproxy.cfg
        mode: '0644'

    - name: Configure Keepalived
      ansible.builtin.template:
        src: ../roles/haproxy/templates/keepalived.conf.j2
        dest: /etc/keepalived/keepalived.conf
        mode: '0644'
      vars:
        keepalived_state: "BACKUP"
        keepalived_priority: "{{ 100 if inventory_hostname == 'k8s-cp-2' else 99 }}"

    - name: Start and enable HAProxy and Keepalived
      ansible.builtin.systemd:
        name: "{{ item }}"
        state: started
        enabled: yes
      loop:
        - haproxy
        - keepalived

    - name: Read join command from file
      ansible.builtin.slurp:
        src: ./join-commands.txt
      register: join_commands
      delegate_to: localhost

    - name: Join control plane to cluster
      ansible.builtin.shell: |
        {{ join_commands['content'] | b64decode | regex_search('kubeadm join.*--control-plane.*') }}
      args:
        creates: /etc/kubernetes/admin.conf

    - name: Create .kube directory
      ansible.builtin.file:
        path: /root/.kube
        state: directory
        mode: '0755'

    - name: Copy admin.conf to .kube/config
      ansible.builtin.copy:
        src: /etc/kubernetes/admin.conf
        dest: /root/.kube/config
        remote_src: yes
        mode: '0600'
```

---

### **playbooks/07-join-workers.yml**
```yaml
---
- name: Join worker nodes to cluster
  hosts: workers
  become: true
  serial: 1
  
  tasks:
    - name: Read join command from file
      ansible.builtin.slurp:
        src: ./join-commands.txt
      register: join_commands
      delegate_to: localhost

    - name: Extract worker join command
      ansible.builtin.set_fact:
        worker_join_cmd: "{{ join_commands['content'] | b64decode | regex_search('kubeadm join [^#]*') | regex_replace('\\s+', ' ') }}"

    - name: Join worker to cluster
      ansible.builtin.shell: "{{ worker_join_cmd }}"
      args:
        creates: /etc/kubernetes/kubelet.conf

    - name: Wait for node to be ready
      ansible.builtin.pause:
        seconds: 30
```

---

### **playbooks/08-install-cni.yml**
```yaml
---
- name: Install Calico CNI
  hosts: master
  become: true
  
  tasks:
    - name: Download Calico operator
      ansible.builtin.get_url:
        url: https://raw.githubusercontent.com/projectcalico/calico/{{ calico_version }}/manifests/tigera-operator.yaml
        dest: /root/tigera-operator.yaml
        mode: '0644'

    - name: Apply Calico operator
      ansible.builtin.command: kubectl apply -f /root/tigera-operator.yaml
      environment:
        KUBECONFIG: /etc/kubernetes/admin.conf

    - name: Create Calico custom resources file
      ansible.builtin.copy:
        content: |
          apiVersion: operator.tigera.io/v1
          kind: Installation
          metadata:
            name: default
          spec:
            calicoNetwork:
              ipPools:
              - blockSize: 26
                cidr: {{ pod_network_cidr }}
                encapsulation: VXLANCrossSubnet
                natOutgoing: Enabled
                nodeSelector: all()
          ---
          apiVersion: operator.tigera.io/v1
          kind: APIServer
          metadata:
            name: default
          spec: {}
        dest: /root/calico-custom-resources.yaml
        mode: '0644'

    - name: Apply Calico custom resources
      ansible.builtin.command: kubectl apply -f /root/calico-custom-resources.yaml
      environment:
        KUBECONFIG: /etc/kubernetes/admin.conf

    - name: Wait for Calico pods to be ready
      ansible.builtin.command: kubectl wait --for=condition=Ready pods --all -n calico-system --timeout=300s
      environment:
        KUBECONFIG: /etc/kubernetes/admin.conf
      retries: 3
      delay: 10
```

---

### **playbooks/09-install-gpu-operator.yml**
```yaml
---
- name: Install NVIDIA GPU Operator
  hosts: master
  become: true
  
  tasks:
    - name: Add Helm repository
      ansible.builtin.shell: |
        curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
      args:
        creates: /usr/local/bin/helm

    - name: Add NVIDIA Helm repository
      ansible.builtin.command: helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
      environment:
        KUBECONFIG: /etc/kubernetes/admin.conf

    - name: Update Helm repositories
      ansible.builtin.command: helm repo update
      environment:
        KUBECONFIG: /etc/kubernetes/admin.conf

    - name: Install NVIDIA GPU Operator
      ansible.builtin.command: |
        helm install --wait --generate-name \
          -n gpu-operator --create-namespace \
          nvidia/gpu-operator \
          --set driver.enabled=false
      environment:
        KUBECONFIG: /etc/kubernetes/admin.conf

    - name: Label GPU nodes
      ansible.builtin.command: kubectl label nodes {{ item }} nvidia.com/gpu=true --overwrite
      environment:
        KUBECONFIG: /etc/kubernetes/admin.conf
      loop: "{{ groups['gpu_workers'] }}"

    - name: Wait for GPU operator pods to be ready
      ansible.builtin.command: kubectl wait --for=condition=Ready pods --all -n gpu-operator --timeout=600s
      environment:
        KUBECONFIG: /etc/kubernetes/admin.conf
      retries: 5
      delay: 30
```

---

### **playbooks/10-verify-cluster.yml**
```yaml
---
- name: Verify Kubernetes cluster and GPU setup
  hosts: master
  become: true