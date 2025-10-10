# 🧭 Add Active Health Checks to Your Nginx Setup

We’ll make Nginx regenerate the `upstream vllm_backends` section dynamically, based on which servers respond healthy to `/health`.

---

## 1️⃣ Create a separate upstream include file

Move the `upstream` block into a separate file that the script can rewrite safely:

```bash
sudo mkdir -p /etc/nginx/upstreams
sudo mv /etc/nginx/sites-available/chatbot /etc/nginx/sites-available/chatbot.conf
```

Then edit `/etc/nginx/sites-available/chatbot.conf` like this 👇

### ✅ `/etc/nginx/sites-available/chatbot.conf`

```nginx
# Dynamic upstream (auto-managed by health check script)
include /etc/nginx/upstreams/vllm_backends.conf;

server {
    listen 80;
    server_name _;
    root /mnt/data/office_work/vllms_inference;
    index chatbot.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location /v1/ {
        proxy_pass http://vllm_backends;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 5s;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;

        proxy_next_upstream error timeout invalid_header http_502 http_503 http_504;
        proxy_next_upstream_tries 2;
    }
}
```

---

## 2️⃣ Create the health-check script

Create the script at `/usr/local/bin/nginx-healthcheck.sh`:

```bash
#!/bin/bash

# Backend IPs
BACKENDS=("192.168.1.1" "192.168.1.2" "192.168.1.3" "192.168.1.4" "192.168.1.5" "192.168.1.6" "192.168.1.7" "192.168.1.8")

UPSTREAM_FILE="/etc/nginx/upstreams/vllm_backends.conf"
TEMP_FILE="/tmp/vllm_backends.new"

# Start building the upstream block
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

# Replace file if there’s any difference, then reload nginx
if ! cmp -s "$TEMP_FILE" "$UPSTREAM_FILE"; then
  mv "$TEMP_FILE" "$UPSTREAM_FILE"
  nginx -t && systemctl reload nginx
fi
```

Make it executable:

```bash
sudo chmod +x /usr/local/bin/nginx-healthcheck.sh
```

---

## 3️⃣ Schedule automatic checks

### Option A — via **cron**

```bash
sudo crontab -e
```

Add this line:

```bash
* * * * * /usr/local/bin/nginx-healthcheck.sh >/dev/null 2>&1
```

### Option B — via **systemd timer** (more reliable)

Create:

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

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nginx-healthcheck.timer
```

---

## 4️⃣ Verify

Run once manually to create the upstream file:

```bash
sudo /usr/local/bin/nginx-healthcheck.sh
cat /etc/nginx/upstreams/vllm_backends.conf
```

If a backend is down, it’ll be commented out like:

```nginx
# server 192.168.1.3:8000; # unhealthy
```

---

## 🧠 Memorization Trick

> **“CURL ➜ CONFIG ➜ COMPARE ➜ RELOAD”**

That’s the lifecycle:

1. **CURL** each backend’s `/health`
2. **CONFIG** file rebuilt
3. **COMPARE** with old config
4. **RELOAD** Nginx only if changed

---
