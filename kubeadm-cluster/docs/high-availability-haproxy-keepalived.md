# High Availability Kubernetes Control Plane with HAProxy and Keepalived

This guide describes how to provision a highly available Kubernetes control plane using a virtual IP (VIP) managed by HAProxy and Keepalived. This setup ensures API server availability even if one or more control plane nodes fail.

## Architecture

- **Control Plane Nodes:** 192.168.1.1, 192.168.1.3, 192.168.1.5
- **VIP:** 192.168.1.100 (used as `controlPlaneEndpoint` in kubeadm config)
- **HAProxy:** Load balances traffic to all healthy control plane nodes
- **Keepalived:** Manages the VIP failover between control plane nodes

### 🖥️ Change the Hostname

Set a new hostname for your node using the following command:

```bash
sudo hostnamectl set-hostname <new-hostname>
```

*(Replace `<new-hostname>` with your desired hostname, e.g., `lb1.k8s.local` or `cp1.k8s.local`.)*

---

## ⚙️ HAProxy

Update your system packages and install **HAProxy** and **Keepalived**:

```bash
sudo apt update && sudo apt install -y haproxy keepalived
```

*(Run this command on all **load balancer** or **control plane** nodes, depending on your architecture.)*


**Backup the default HAProxy config (recommended):**

```bash
sudo cp /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.bak
```

**Clear the default HAProxy config:**

```bash
echo "" | sudo tee /etc/haproxy/haproxy.cfg

```

**Edit the HAProxy config:**

```bash
sudo nano /etc/haproxy/haproxy.cfg
```

**add the following data in it:**

   ```bash
    # ========== Global settings ==========
    global
        log /dev/log local0              # Log to syslog facility local0
        log /dev/log local1 notice       # Log to syslog facility local1 with notice level
        maxconn 2000                     # Maximum number of concurrent connections
        user haproxy                     # Run as haproxy user
        group haproxy                    # Run as haproxy group
        daemon                           # Run HAProxy as a daemon

    # ========== Default settings ==========
    defaults
        log     global                   # Inherit logging from global
        mode    tcp                      # Kubernetes API server uses raw TCP (not HTTP)
        option  tcplog                   # Enable detailed TCP logging
        option  dontlognull              # Don’t log connections with no data
        timeout connect 5s               # Wait max 5s for a backend to accept connection
        timeout client  30s              # Idle client connections closed after 30s
        timeout server  30s              # Idle server connections closed after 30s

    # ========== Frontend (listener) ==========
    frontend k8s-api
        bind *:6443                      # Listen on all interfaces, port 6443
        default_backend k8s-masters      # Forward all traffic to backend pool

    # ========== Backend (pool of control planes) ==========
    backend k8s-masters
        mode tcp                         # TCP mode for raw API server connections
        balance roundrobin               # Distribute requests evenly across servers
        option tcp-check                 # Perform TCP-level health checks
        timeout connect 5s               # Backend connect timeout
        timeout server 30s               # Backend idle timeout
        timeout check  5s                # Health check timeout

        # Control Plane nodes (API servers on port 6443)
        # fall 3 → mark server as DOWN after 3 failed checks
        # rise 2 → mark server as UP after 2 successful checks
        server pc1 192.168.1.1:6443 check fall 3 rise 2
        server pc3 192.168.1.3:6443 check fall 3 rise 2
        server pc5 192.168.1.5:6443 check fall 3 rise 2


   ```

**Restart haproxy**

```bash
sudo systemctl restart haproxy 
```

## 🧩 Keepalived Configuration

Configure **Keepalived** on each load balancer node to manage the **Virtual IP (VIP)** failover.
Here’s your fully rewritten **Keepalived section**, following the exact structure and tone of your HAProxy setup — clean, consistent, and formatted for clarity:

**Backup the default Keepalived config (recommended):**

```bash
sudo cp /etc/keepalived/keepalived.conf /etc/keepalived/keepalived.conf.bak
```

**Clear the default Keepalived config:**

```bash
echo "" | sudo tee /etc/keepalived/keepalived.conf
```

**If config file is not created, then crete and edit with:**

```bash
sudo nano /etc/keepalived/keepalived.conf
```

**Add the following data in it (on Load Balancer-1 — MASTER):**

```conf
vrrp_instance VI_1 {
    state MASTER
    interface eno1
    virtual_router_id 51
    priority 101
    advert_int 1

    authentication {
        auth_type PASS
        auth_pass 42
    }

    virtual_ipaddress {
        192.168.1.100
    }
}
```

**On Load Balancer-2 (192.168.1.10, BACKUP):**

```conf
vrrp_instance VI_1 {
    state BACKUP
    interface enp2s0
    virtual_router_id 51
    priority 100
    advert_int 1

    authentication {
        auth_type PASS
        auth_pass 42
    }

    virtual_ipaddress {
        192.168.1.100
    }
}
```

---

- Replace `<your_network_interface>` with your actual NIC name (e.g., `eno1`, `eth0`, `enp0s31f6`, `ens33`).
- Restart **Keepalived** on both load balancer nodes — the **VIP `192.168.1.100`** should automatically float between them depending on which node is active.

---

**Restart Keepalived:**

```bash
sudo systemctl restart keepalived
sudo systemctl enable keepalived
```

---

### 🧪 Verify VIP Assignment

Check if the **Virtual IP (VIP)** is currently bound to the **MASTER** load balancer:

```bash
ip a | grep 192.168.1.100
```

- You should see the VIP assigned to the MASTER node (`lb1.k8s.local`).
- If the MASTER node fails, the VIP will automatically shift to the BACKUP node (`lb2.k8s.local`).

---

### ✅ Verifying Keepalived Functionality

1. **Check VIP on MASTER:**

   ```bash
   ip addr show <interface> | grep 192.168.1.100
   # Example:
   ip a | grep eno1
   ```

   ✅ The VIP `192.168.1.100` should appear on the MASTER node.

---

2. **Test Failover:**

   Stop Keepalived on the MASTER node to simulate failure:

   ```bash
   sudo systemctl stop keepalived
   ```

   Then, verify the VIP has moved to the BACKUP node:

   ```bash
   ip a | grep eno1
   ```

   ✅ The VIP `192.168.1.100` should now be visible on the BACKUP node (`lb2.k8s.local`).

---

3. **Restore MASTER Node:**

   Restart Keepalived on the MASTER:

   ```bash
   sudo systemctl start keepalived
   ```

   ✅ The VIP should float back automatically to the MASTER node.

---

### ✅ Verifying HAProxy Functionality

1. **Test Kubernetes API health via the VIP:**

   ```bash
   curl -k https://192.168.1.100:6443/healthz
   ```

   ✅ Expected output:

   ```
   ok
   ```

---

2. **Check HAProxy Logs:**

   View connection forwarding activity:

   ```bash
   sudo tail -f /var/log/haproxy.log
   ```

   or check via systemd journal:

   ```bash
   journalctl -u haproxy -f
   ```

---

3. **Simulate Control Plane Node Failure:**

   Stop the `kubelet` service on one control plane node to simulate an API server failure:

   ```bash
   sudo systemctl stop kubelet
   ```

   Then, test again:

   ```bash
   curl -k https://192.168.1.100:6443/healthz
   ```

   ✅ The response should still be `ok`, indicating that HAProxy successfully rerouted traffic to healthy API servers.

---

4. **Restart Both Services:**

   ```bash
   sudo systemctl restart haproxy keepalived
   ```

---

5. **Set the `controlPlaneEndpoint` in Your kubeadm Configuration:**

   ```yaml
   controlPlaneEndpoint: "192.168.1.100:6443"
   ```

---

## 🩺 High Availability Health Check

For production environments, it’s recommended to implement an **active health check** script (using a `systemd` service or `cron` job) to continuously monitor the **Virtual IP (VIP)** and **HAProxy** health status.

👉 Refer to the detailed implementation guide here:
[**docs/health_check_haproxy.md**](health_check_haproxy.md)

---
## 📘 References

* [Kubernetes High Availability Documentation](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/)
* [HAProxy Documentation](https://www.haproxy.org/)
* [Keepalived Documentation](https://keepalived.readthedocs.io/)

---
