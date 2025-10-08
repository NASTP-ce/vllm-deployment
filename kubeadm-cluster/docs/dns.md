## 🧭 DNS Management for On-Prem Kubernetes HA Cluster

Because your cluster uses **local IPs (192.168.x.x)** and a **custom domain (k8s.local)**, you have a few options to handle name resolution effectively depending on scale and environment.

---

### **Option 1: Local /etc/hosts (Simple, Lab or Small Cluster)** 🧩

**Use when:**
Your environment is small (10–20 nodes), or you don’t have centralized DNS.

Each node must have an identical `/etc/hosts` file mapping all hostnames and the virtual IP:

```bash
192.168.1.100  api.k8s.local
192.168.1.9    lb1.k8s.local
192.168.1.10   lb2.k8s.local
192.168.1.1    pc1.k8s.local
192.168.1.2    pc2.k8s.local
192.168.1.3    pc3.k8s.local
192.168.1.4    pc4.k8s.local
192.168.1.5    pc5.k8s.local
192.168.1.6    pc6.k8s.local
192.168.1.7    pc7.k8s.local
192.168.1.8    pc8.k8s.local
```

You can automate this distribution using Ansible:

```yaml
- name: Distribute /etc/hosts entries to all nodes
  ansible.builtin.lineinfile:
    path: /etc/hosts
    line: "{{ item }}"
    state: present
  loop:
    - "192.168.1.100 api.k8s.local"
    - "192.168.1.9 lb1.k8s.local"
    - "192.168.1.10 lb2.k8s.local"
    - "192.168.1.1 pc1.k8s.local"
    - "192.168.1.2 pc2.k8s.local"
    - "192.168.1.3 pc3.k8s.local"
    - "192.168.1.4 pc4.k8s.local"
    - "192.168.1.5 pc5.k8s.local"
    - "192.168.1.6 pc6.k8s.local"
    - "192.168.1.7 pc7.k8s.local"
    - "192.168.1.8 pc8.k8s.local"
```

**💡 Memorization trick:**
Think of `/etc/hosts` as your **“local phonebook”** — every machine must have the same phonebook to reach the right “person” (node).

---

### **Option 2: Centralized DNS Server (Recommended for Production)** 🧱

**Use when:**
You have a corporate or data center network — ideal for **HA** and **automated resolution**.

You can use:

| Type                   | Example                               | Notes                              |
| ---------------------- | ------------------------------------- | ---------------------------------- |
| **BIND9**              | Open-source, full-featured DNS server | Best for on-premises setups        |
| **Dnsmasq**            | Lightweight, easy to manage           | Perfect for small HA clusters      |
| **CoreDNS**            | Already part of Kubernetes            | Can serve cluster and external DNS |
| **Pi-hole (Optional)** | GUI-based and simple                  | Ideal for lab environments         |

**Example BIND9 zone file (`/etc/bind/db.k8s.local`):**

```
$TTL 86400
@   IN  SOA ns1.k8s.local. admin.k8s.local. (
            2025100801 ; Serial
            3600       ; Refresh
            1800       ; Retry
            1209600    ; Expire
            86400 )    ; Minimum TTL

; Name servers
@       IN  NS  ns1.k8s.local.

; Load balancers
lb1     IN  A   192.168.1.9
lb2     IN  A   192.168.1.10

; Virtual IP
api     IN  A   192.168.1.100

; Control Planes
pc1     IN  A   192.168.1.1
pc3     IN  A   192.168.1.3
pc5     IN  A   192.168.1.5

; Workers
pc2     IN  A   192.168.1.2
pc4     IN  A   192.168.1.4
pc6     IN  A   192.168.1.6
pc7     IN  A   192.168.1.7
pc8     IN  A   192.168.1.8
```

Then configure all nodes’ `/etc/resolv.conf`:

```bash
nameserver 192.168.1.9    # Primary DNS (lb1)
nameserver 192.168.1.10   # Secondary DNS (lb2)
search k8s.local
```

**Advantages:**

* Centralized control
* Scalable and maintainable
* Supports forward/reverse lookups
* Can integrate with DHCP

---

### **Option 3: Integrate with Kubernetes DNS (CoreDNS)** ☸️

Once the cluster is up, **CoreDNS** inside Kubernetes handles **service discovery** within the cluster (`.svc.cluster.local` domain).

However, for **external access (e.g., api.k8s.local)**:

* You must rely on `/etc/hosts` or an external DNS server (Bind/Dnsmasq)
* Optionally, configure an **externalName Service** or **Ingress** for API routing

**Example externalName Service:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api-external
  namespace: kube-system
spec:
  type: ExternalName
  externalName: api.k8s.local
```

---

### ✅ Recommended Setup for You

Since your architecture uses **HAProxy + Keepalived**, here’s the best combination:

| Component                        | Recommended DNS Handling                      |
| -------------------------------- | --------------------------------------------- |
| `api.k8s.local`                  | Maps to Virtual IP `192.168.1.100`            |
| `lb1.k8s.local`, `lb2.k8s.local` | Mapped in centralized DNS (or /etc/hosts)     |
| `pcX.k8s.local`                  | Registered in local zone (Bind or /etc/hosts) |
| Internal Pods                    | Resolved by CoreDNS inside the cluster        |
| External Clients                 | Resolved via Bind/Dnsmasq → `api.k8s.local`   |

---
