
## 🩺 Active Health Check for HAProxy and Keepalived

### 📄 Step 1: Create Health Check Script

Create a script `/usr/local/bin/check_ha_health.sh`:

```bash
sudo nano /usr/local/bin/check_ha_health.sh
```

Add the following content:

```bash
#!/bin/bash
# ===============================================
# HAProxy & Keepalived Health Check Script
# ===============================================

# Configuration
VIP="192.168.1.100"
INTERFACE="eno1"
LOG_FILE="/var/log/ha_health_check.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Function to log messages
log() {
    echo "[$TIMESTAMP] $1" | tee -a $LOG_FILE
}

# 1️⃣ Check Keepalived VIP presence
if ip addr show $INTERFACE | grep -q $VIP; then
    log "✅ VIP $VIP is present on $INTERFACE."
else
    log "❌ VIP $VIP is missing on $INTERFACE. Restarting Keepalived..."
    sudo systemctl restart keepalived
fi

# 2️⃣ Check HAProxy service health
if systemctl is-active --quiet haproxy; then
    log "✅ HAProxy service is active."
else
    log "❌ HAProxy service is inactive. Restarting..."
    sudo systemctl restart haproxy
fi

# 3️⃣ Test Kubernetes API availability via VIP
if curl -sk https://$VIP:6443/healthz | grep -q "ok"; then
    log "✅ Kubernetes API via VIP ($VIP:6443) is responding."
else
    log "❌ Kubernetes API is not responding through VIP. Possible backend issue."
fi

log "--------------------------------------------------"
```

Make the script executable:

```bash
sudo chmod +x /usr/local/bin/check_ha_health.sh
```

---

### 📅 Step 2: Automate with Systemd Timer (Recommended over Cron)

Create a **systemd service** for the health check:

```bash
sudo nano /etc/systemd/system/ha-health-check.service
```

Add:

```ini
[Unit]
Description=HAProxy & Keepalived Health Check

[Service]
Type=oneshot
ExecStart=/usr/local/bin/check_ha_health.sh
```

Then create a **systemd timer** to run it every 2 minutes:

```bash
sudo nano /etc/systemd/system/ha-health-check.timer
```

Add:

```ini
[Unit]
Description=Run HA Health Check every 2 minutes

[Timer]
OnBootSec=1min
OnUnitActiveSec=2min

[Install]
WantedBy=timers.target
```

Enable and start the timer:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ha-health-check.timer
```

---

### 🧠 Step 3: Verify the Timer

Check timer status:

```bash
systemctl list-timers | grep ha-health-check
```

View logs:

```bash
sudo tail -f /var/log/ha_health_check.log
```

✅ You’ll see periodic log entries showing VIP, HAProxy, and API health results.

---

### ⚙️ Optional: Slack/Email Alert Integration

You can easily extend the script to send alerts when issues occur.

**Example for Slack (using webhook):**

```bash
curl -X POST -H 'Content-type: application/json' \
--data '{"text":"❌ HA Health Alert: VIP or HAProxy issue detected on lb1.k8s.local"}' \
https://hooks.slack.com/services/<YOUR/WEBHOOK/URL>
```

**Example for Email (using mailutils):**

```bash
echo "HAProxy or Keepalived failure detected" | mail -s "HA Health Alert" admin@example.com
```

---

### 🧠 Memorization Trick

> 💡 **“V-H-A” Rule** →
> **V** = Verify VIP →
> **H** = HAProxy service →
> **A** = API health check

If any of these fail, restart and log automatically.

---

**Note** you can extend this with a **Prometheus exporter-style version** (so you can monitor HA health metrics in Grafana)?
