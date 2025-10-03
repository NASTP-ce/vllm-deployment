### Joining Additional Control Plane Node

Follow these steps on your Ubuntu system:

---

#### 1. Copy Certificates from the Primary Control Plane

On **control-plane-1** (`192.168.1.100`), create a tarball of the PKI directory:

```bash
sudo tar -cvf kubernetes-pki-shared.tar -C /etc/kubernetes/pki ca.crt ca.key sa.pub sa.key front-proxy-ca.crt front-proxy-ca.key etcd/ca.crt etcd/ca.key
```

Transfer it to **pc8** (example using `scp`):

```bash
scp kubernetes-pki-shared.tar user@192.168.1.3:~/
```

---

#### 2. Extract Certificates on pc8

On **pc8**, unpack the certificates into the correct directory:

```bash
sudo mkdir -p /etc/kubernetes/pki/etcd
sudo tar -xvf kubernetes-pki-shared.tar -C /etc/kubernetes/pki
```

---

#### 3. Verify Certificate Files

Confirm the required files are present on **pc8**:

```bash
ls -l /etc/kubernetes/pki/{ca.crt,sa.key,front-proxy-ca.crt,etcd/ca.crt}
```

* If any are missing, repeat the copy process and ensure they exist on **control-plane-1**.

---

#### 4. Join pc8 to the Cluster

Run the join command on **pc8** with control plane option and increased verbosity:

```bash
sudo kubeadm join 192.168.1.100:6443 --token am6my1.48msudhcir722vx4 \
  --discovery-token-ca-cert-hash sha256:76aa8ec7d350c4d91cf169754b67d76f2beb0ab5c90a094f5e32b54433bedfcc \
  --control-plane --v=5
```

---
