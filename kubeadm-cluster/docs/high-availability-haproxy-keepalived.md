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

2. **Configure HAProxy** to forward traffic to all control plane nodes' API servers (port 6443):
   Example `/etc/haproxy/haproxy.cfg`:
   ```
   frontend k8s-api
       bind *:6443
       default_backend k8s-masters

   backend k8s-masters
       balance roundrobin
       server cp1 192.168.1.9:6443 check
       server cp2 192.168.1.3:6443 check
       server cp3 192.168.1.8:6443 check
   ```

3. **Configure Keepalived** to manage the VIP (192.168.1.100):
   Example `/etc/keepalived/keepalived.conf`:
   ```
   vrrp_instance VI_1 {
       state MASTER
       interface <your_network_interface>
       virtual_router_id 51
       priority 101  # Lower on backups
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
   - Set `state BACKUP` and lower `priority` on secondary nodes.
   - Replace `<your_network_interface>` with your actual interface name (e.g., `eth0`).

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
