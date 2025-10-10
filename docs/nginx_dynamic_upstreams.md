# 🧭 Add Active Health Checks to Your Nginx Setup

We’ll configure Nginx to dynamically rebuild the `upstream vllm_backends` block based on which servers successfully respond to `/health`.

---

## 1️⃣ Create a Dedicated Upstream Include File

First, isolate your upstream configuration into its own file.
This allows the health-check script to update it safely without touching your main config.

```bash
/etc/nginx/upstreams/
```

---

## 2️⃣ Create the Health-Check Script

We’ll now create a script that automatically checks backend health and updates Nginx’s upstream configuration.

Open the file for editing:

```bash
sudo nano /usr/local/bin/nginx-healthcheck.sh
```

Paste the following script inside:

```bash
#!/bin/bash

# List of backend servers
BACKENDS=("192.168.1.1" "192.168.1.2" "192.168.1.3" "192.168.1.4" "192.168.1.5" "192.168.1.6" "192.168.1.7" "192.168.1.8")

UPSTREAM_FILE="/etc/nginx/upstreams/vllm_backends.conf"
TEMP_FILE="/tmp/vllm_backends.new"

# Generate the new upstream configuration
{
  echo "# Auto-generated upstream by nginx-healthcheck.sh"
  echo "upstream vllm_backends {"
  echo "    #least_conn;"
  for host in "${BACKENDS[@]}"; do
    if curl -s --max-time 2 http://$host:8000/health | grep -q "OK"; then
      echo "    server $host:8000 max_fails=3 fail_timeout=30s;"
    else
      echo "    # server $host:8000; # unhealthy"
    fi
  done
  echo "}"
} > "$TEMP_FILE"

# Apply changes only if there’s a difference, then reload Nginx
if ! cmp -s "$TEMP_FILE" "$UPSTREAM_FILE"; then
  mv "$TEMP_FILE" "$UPSTREAM_FILE"
  nginx -t && systemctl reload nginx
fi
```

Make the script executable:

```bash
sudo chmod +x /usr/local/bin/nginx-healthcheck.sh
```

---

## 3️⃣ Automate the Health Checks

### Option A — Using **cron**

Edit the root crontab:

```bash
sudo crontab -e
```

Add this line to run every minute:

```bash
* * * * * /usr/local/bin/nginx-healthcheck.sh /var/log/nginx-healthcheck.log 2>&1;
```

## ⚙️ 3️⃣ Verify It’s Working

Check the log file:

```bash
sudo tail -f /var/log/nginx-healthcheck.log
```



view logs in end of this file................................
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,










## 💡 Optional: Rotate the Log File

To prevent the log from growing endlessly, add a simple logrotate rule.

Create a new file /etc/logrotate.d/nginx-healthcheck:

```bash
sudo nano /etc/logrotate.d/nginx-healthcheck
```

Add:

```bash
/var/log/nginx-healthcheck.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

That keeps 7 days of logs, compresses old ones, and avoids errors if the file doesn’t exist.


---

By default, cron supports a minimum interval of 1 minute, so it cannot run a job after less than 1 minute.

So we’ll use one of three methods, depending on what you prefer.

### Option B — Using a **systemd timer** (recommended)

Create the following service and timer units:

**`/etc/systemd/system/nginx-healthcheck.service`**

```ini
[Unit]
Description=Nginx Backend Health Checker

[Service]
Type=oneshot
ExecStart=/usr/local/bin/nginx-healthcheck.sh
```

**`/etc/systemd/system/nginx-healthcheck.timer`**

```ini
[Unit]
Description=Run Nginx Health Check Every Minute

[Timer]
OnBootSec=30
OnUnitActiveSec=60

[Install]
WantedBy=timers.target
```

Enable and start the timer:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nginx-healthcheck.timer
```

---

## 4️⃣ Verify the Setup

Run the script manually once to generate the initial upstream file:

```bash
sudo /usr/local/bin/nginx-healthcheck.sh
cat /etc/nginx/upstreams/vllm_backends.conf
```

If a backend is unhealthy, it will be commented out like this:

```nginx
# server 192.168.1.3:8000; # unhealthy
```

---

## 🧠 Memorization Trick

> **“CURL ➜ CONFIG ➜ COMPARE ➜ RELOAD”**

That’s the entire lifecycle in four simple steps:

1. **CURL** each backend’s `/health` endpoint
2. **CONFIG** file rebuilt dynamically
3. **COMPARE** new vs existing configuration
4. **RELOAD** Nginx only when changes are detected

---











Excellent — that output tells us a lot ✅

Here’s what’s happening:

---

### 🧠 What’s Going On

Your script **is working perfectly** — it:

1. Prints a timestamp and message (`Running NGINX health check` ✅)
2. Iterates over all 8 backend IPs (`192.168.1.1` → `192.168.1.8`)
3. Uses `curl` to hit `/health` on each one
4. Marks all of them as “unhealthy” because `grep -q OK` didn’t match anything
5. Writes a **new temporary upstream config file** `/tmp/vllm_backends.new`
6. Then compares it to `/etc/nginx/upstreams/vllm_backends.conf`
7. If there’s **no change**, it silently exits (so no reload).

That’s why you see no new output after the trace ends.

---

### 💾 Why `/var/log/nginx-healthcheck.log` Is Empty

Because:

* Your script prints to **stdout** (terminal),
* But cron runs it **non-interactively** — only if you **redirect** the output will it go to a log file.
* And previously, cron’s redirection failed due to permission issues.

---

### ✅ Fix It Properly (Recommended Setup)

Let’s fix logging and cron behavior cleanly.

#### 1️⃣ Create a writable log file

```bash
sudo touch /var/log/nginx-healthcheck.log
sudo chmod 666 /var/log/nginx-healthcheck.log
```

*(Or more secure: `chmod 644` if only root runs it.)*

---

#### 2️⃣ Update crontab (as root)

Edit:

```bash
sudo crontab -e
```

Add these lines to run every **15 seconds** and **append** to the log:

```bash
* * * * * bash -c '/usr/local/bin/nginx-healthcheck.sh >> /var/log/nginx-healthcheck.log 2>&1'
* * * * * sleep 15; bash -c '/usr/local/bin/nginx-healthcheck.sh >> /var/log/nginx-healthcheck.log 2>&1'
* * * * * sleep 30; bash -c '/usr/local/bin/nginx-healthcheck.sh >> /var/log/nginx-healthcheck.log 2>&1'
* * * * * sleep 45; bash -c '/usr/local/bin/nginx-healthcheck.sh >> /var/log/nginx-healthcheck.log 2>&1'
```

---

#### 3️⃣ Verify It’s Running

After 1 minute, check:

```bash
sudo tail -n 20 /var/log/nginx-healthcheck.log
```

You should see repeating entries like:

```
Fri Oct 10 01:32:00 PM PKT 2025 - Running NGINX health check
Fri Oct 10 01:32:15 PM PKT 2025 - Running NGINX health check
...
```

---

#### 4️⃣ (Optional) Add Health Status Info

To make the log more useful, modify your script slightly — add inside the `for host in` loop:

```bash
if curl -s --max-time 2 "http://$host:8000/health" | grep -q OK; then
    echo "$(date) - $host is healthy"
else
    echo "$(date) - $host is unhealthy"
fi
```

Now your log will contain readable lines like:

```
Fri Oct 10 13:40:15 PKT 2025 - 192.168.1.3 is unhealthy
```

---

Would you like me to rewrite your full `nginx-healthcheck.sh` script with logging, colored output (for manual runs), and automatic NGINX reload only on config change? It’ll make it production-ready and easier to debug.
