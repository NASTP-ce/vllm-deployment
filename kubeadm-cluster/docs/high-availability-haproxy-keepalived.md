# High Availability Kubernetes Control Plane with HAProxy and Keepalived

This guide describes how to provision a highly available Kubernetes control plane using a virtual IP (VIP) managed by HAProxy and Keepalived. This setup ensures API server availability even if one or more control plane nodes fail.

## Architecture

- **Control Plane Nodes:** 192.168.1.9, 192.168.1.3, 192.168.1.8
- **VIP:** 192.168.1.100 (used as `controlPlaneEndpoint` in kubeadm config)
- **HAProxy:** Load balances traffic to all healthy control plane nodes
- **Keepalived:** Manages the VIP failover between control plane nodes

## Steps

1. **Install HAProxy and Keepalived** on all control plane nodes:
   ```bash
   sudo apt update
   sudo apt install haproxy keepalived -y
   ```

1. **Backup the default HAProxy config (recommended):**

    ```bash
    sudo cp /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.bak
    ```

1. **Clear the default HAProxy config:**

    ```bash
    echo "1" | sudo tee /etc/haproxy/haproxy.cfg

    ```

1. **Edit the HAProxy config:**

    ```bash
    sudo nano /etc/haproxy/haproxy.cfg
    ```

2. **add the following data in it:**

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
        server cp1 192.168.1.9:6443 check fall 3 rise 2
        server cp2 192.168.1.3:6443 check fall 3 rise 2
        server cp3 192.168.1.8:6443 check fall 3 rise 2


   ```

**Restart haproxy**

```bash
sudo systemctl restart haproxy 
```

## **Keepalived config** for your 3 control-plane nodes:

---

### `/etc/keepalived/keepalived.conf`

**On control-plane-1 (192.168.1.9, MASTER):**

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

**On control-plane-2 (192.168.1.3, BACKUP):**

```conf
vrrp_instance VI_1 {
    state BACKUP
    interface enp0s31f6
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

**On control-plane-3 (192.168.1.8, BACKUP):**

```conf
vrrp_instance VI_1 {
    state BACKUP
    interface eno1
    virtual_router_id 51
    priority 99
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

✅ Replace `<your_network_interface>` with your NIC (e.g., `eno1` `eth0`, `enp0s31f6` , `ens33`).
✅ Restart Keepalived on all nodes, the VIP `192.168.1.100` should float between them.


---

### ✅ Checking if Keepalived is working

1. **Check VIP on MASTER**

   ```bash
   ip addr show <interface> | grep 192.168.1.100
   # or simply
   ip a | grep eno1
   ```

   ✅ You should see `192.168.1.100` bound to the MASTER node.

2. **Test failover**
   On MASTER:

   ```bash
   sudo systemctl stop keepalived
   ```

   Then on a BACKUP node:

   ```bash
   ip a | grep eno1
   ```

   ✅ The VIP `192.168.1.100` should appear on the BACKUP node.

3. **Restore MASTER**

   ```bash
   sudo systemctl start keepalived
   ```

   ✅ The VIP should float back to the MASTER.

---

### ✅ Checking if HAProxy is working

1. **Test API health via VIP**

   ```bash
   curl -k https://192.168.1.100:6443/healthz
   ```

   ✅ Expected output:

   ```
   ok
   ```

2. **Check HAProxy logs** (shows connections forwarded):

   ```bash
   sudo tail -f /var/log/haproxy.log
   ```

   or check system journal:

   ```bash
   journalctl -u haproxy -f
   ```

3. **Simulate node failure**
   Stop kubelet on one control-plane node (simulating API server down):

   ```bash
   sudo systemctl stop kubelet
   ```

   Then run again:

   ```bash
   curl -k https://192.168.1.100:6443/healthz
   ```

   ✅ It should still return `ok` because HAProxy routes to healthy control-plane nodes.

---

4. **Restart services**:
   ```bash
   sudo systemctl restart haproxy keepalived
   ```

5. **Set `controlPlaneEndpoint` in your kubeadm config to the VIP:**
   ```yaml
   controlPlaneEndpoint: "192.168.1.100:6443"
   ```

## References
- See [Kubernetes HA documentation](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/) for more details.
