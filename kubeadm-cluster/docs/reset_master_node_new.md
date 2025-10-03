## fully reset a kubeadm cluster

---

## **Step 1: Stop Kubernetes services**

```bash
sudo systemctl stop kubelet
sudo systemctl stop containerd   # or docker if you use it
```

Stopping kubelet ensures that pods and manifests don’t interfere while you clean.

---

## **Step 2: Run kubeadm reset**

```bash
sudo kubeadm reset -f
```

**What this does:**

* Stops kubelet
* Deletes cluster manifests (`/etc/kubernetes/manifests`)
* Removes PKI certs (`/etc/kubernetes/pki`)
* Removes admin kubeconfigs in `/etc/kubernetes`

**What it doesn’t do:**

* Remove CNI plugins
* Clear iptables rules / IPVS
* Delete local kubeconfig files
* Remove etcd data (if using external etcd)

---

## **Step 3: Remove CNI plugins**

CNI configs can cause networking issues if not cleaned:

```bash
sudo rm -rf /etc/cni/net.d
```

If you installed CNI binaries manually (e.g., Flannel, Calico), remove them too:

```bash
sudo rm -rf /opt/cni/bin/*
```

---

## **Step 4: Clear iptables rules and IPVS tables**

Kubernetes modifies networking rules; old rules can block new pods.

```bash
# Clear iptables
sudo iptables -F
sudo iptables -t nat -F
sudo iptables -t mangle -F
sudo iptables -X

# Clear IPVS (if kube-proxy uses IPVS)
sudo ipvsadm --clear
```

Check for leftover IPVS rules:

```bash
sudo ipvsadm -L -n
```

---

## **Step 5: Remove kubeconfig files**

```bash
rm -f $HOME/.kube/config
```

> If multiple users were using the cluster, repeat for their `$HOME/.kube/config`.

---

## **Step 6: Remove leftover directories**

Ensure no stale data remains:

```bash
sudo rm -rf /var/lib/etcd
sudo rm -rf /var/lib/kubelet/*
sudo rm -rf /etc/kubernetes
sudo rm -rf /var/run/kubernetes
```

Check `/var/lib/cni/` and remove if it exists:

```bash
sudo rm -rf /var/lib/cni/
```

---

## **Step 7: Optional – Clean up hostnames and DNS**

Sometimes kubeadm fails if the hostname is inconsistent:

```bash
hostnamectl set-hostname <new-hostname>   # if needed
```

Check `/etc/hosts` for old control plane IPs and remove them.

---

## **Step 8: Restart services**

Once fully cleaned:

```bash
sudo systemctl daemon-reload
sudo systemctl restart kubelet containerd
```

Now your node is **clean and ready for `kubeadm init`**.

---

💡 **Pro tip:** After a full reset, also check that your **ports 6443, 2379-2380, 10250, 10251, 10252** are free. You can run:

```bash
sudo netstat -tulpn | grep -E "6443|2379|2380|10250|10251|10252"
```

This ensures the cluster can start without port conflicts.

---

