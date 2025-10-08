**If CoreDNS pods are stuck** because the **CNI binaries are missing**, specifically the `loopback` plugin that every pod needs.

Error:
```
plugin type="loopback" failed (add): failed to find plugin "loopback" in path [/opt/cni/bin]
```

This usually happens when the **Flannel CNI plugin hasn’t installed the binaries into `/opt/cni/bin`**. Flannel’s init containers (`install-cni` or `install-cni-plugin`) are responsible for this.

---

## 🛠 Solution: Ensure CNI plugins are installed

### Step 1: Check Flannel init container logs

```bash
kubectl -n kube-flannel logs -l app=flannel -c install-cni
```

Look for errors — sometimes they fail due to **permission issues**.

---

### Step 2: Manually install CNI plugins (quick fix)

1. Download CNI binaries:

```bash
CNI_VERSION="v1.1.1"
wget https://github.com/containernetworking/plugins/releases/download/$CNI_VERSION/cni-plugins-linux-amd64-$CNI_VERSION.tgz
```

2. Extract them to `/opt/cni/bin`:

```bash
sudo mkdir -p /opt/cni/bin
sudo tar -xzvf cni-plugins-linux-amd64-$CNI_VERSION.tgz -C /opt/cni/bin
```

3. Verify `loopback` exists:

```bash
ls -l /opt/cni/bin | grep loopback
```

You should see `loopback` among other plugins.

---

### Step 3: Restart CoreDNS pods

Delete the CoreDNS pods — they will auto-recreate:

```bash
kubectl delete pod -n kube-system -l k8s-app=kube-dns
```

Check status:

```bash
kubectl get pods -n kube-system -w
```

Within a few seconds, **CoreDNS pods should move to `Running`**.

---

### ✅ Step 4: Verify networking

After CoreDNS is Running:

```bash
kubectl exec -n kube-system coredns-55cb58b774-77wbp -- nslookup kubernetes.default
```

You should get the cluster IP of `kubernetes.default`.

---

💡 **Memorization trick:**

> “CNI missing → no loopback → pods stuck. Fix: drop binaries into `/opt/cni/bin`.”

---
