# Run SWASTHYA AI on AWS Lightsail

This deployment runs Streamlit and Ollama on the same Ubuntu server. Ollama
listens only on localhost; Caddy provides HTTPS for the Streamlit app.

## 1. Create the Lightsail instance

1. Create an Ubuntu 24.04 LTS instance in Lightsail.
2. Choose a plan with at least 8 GB RAM for `llama3.2:3b`. A CPU-only
   instance works, but model responses may be slower.
3. Attach a Lightsail static IP to the instance.
4. In the Lightsail networking firewall, allow SSH (TCP 22) only from your IP,
   and HTTP (TCP 80) and HTTPS (TCP 443). Do not open TCP 8501 or 11434.
5. Point a DNS A record for a domain you control to the static IP.

## 2. Install the application and Ollama

Connect to the instance over SSH, then run:

```bash
sudo apt update
sudo apt install -y git python3-venv python3-pip tesseract-ocr curl
sudo git clone https://github.com/prajakta-ronit/Swasthya.git /opt/swasthya
sudo chown -R root:root /opt/swasthya
sudo python3 -m venv /opt/swasthya/venv
sudo /opt/swasthya/venv/bin/pip install -r /opt/swasthya/requirements.txt
sudo useradd --system --create-home --home-dir /var/lib/swasthya --shell /usr/sbin/nologin swasthya
```

Install Ollama using its official Linux instructions:
<https://docs.ollama.com/linux>. Then start it and download the model:

```bash
sudo systemctl enable --now ollama
ollama pull llama3.2:3b
```

The app's default Ollama URL is `http://localhost:11434`. Keep Ollama bound to
localhost; do not make its API publicly accessible.

## 3. Start Streamlit with systemd

Before starting the app, configure the encryption key used for saved report
files and filenames. Generate a Fernet key:

```bash
/opt/swasthya/venv/bin/python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Create a root-only environment file and add the generated key. Do not commit
this key or include it in backups alongside the encrypted reports:

```bash
sudo install -d -o root -g root -m 700 /etc/swasthya
sudo install -o root -g root -m 600 /dev/null /etc/swasthya/swasthya.env
sudo nano /etc/swasthya/swasthya.env
```

Add this line, replacing the value with the generated key:

```text
SWASTHYA_REPORT_ENCRYPTION_KEY=your-generated-fernet-key
```

Back up the key separately in a secure password manager or secret manager.
Losing or changing it makes saved reports unrecoverable. Existing plaintext
reports are encrypted when the account's saved reports are next opened.

Install the included service file:

```bash
sudo cp /opt/swasthya/deploy/aws-lightsail/swasthya.service /etc/systemd/system/swasthya.service
sudo systemctl daemon-reload
sudo systemctl enable --now swasthya
sudo systemctl status swasthya
```

The service listens on `127.0.0.1:8501`, not on the public network interface.
To inspect logs:

```bash
sudo journalctl -u swasthya -f
```

## 4. Configure HTTPS with Caddy

Install Caddy using its official Debian/Ubuntu instructions:
<https://caddyserver.com/docs/install>.

Replace `app.example.com` in the included Caddyfile with the DNS name pointed
at your Lightsail static IP, then install and reload the configuration:

```bash
sudo cp /opt/swasthya/deploy/aws-lightsail/Caddyfile /etc/caddy/Caddyfile
sudo nano /etc/caddy/Caddyfile
sudo systemctl enable --now caddy
sudo systemctl reload caddy
```

Caddy obtains and renews the HTTPS certificate automatically when the DNS
record resolves to the instance and ports 80 and 443 are reachable.

Open the configured domain in a browser. On this server, the AI Assistant is
enabled by default because there are no Streamlit Cloud secrets overriding the
setting. To use a different local Ollama model, edit `OLLAMA_MODEL` in
`/etc/systemd/system/swasthya.service`, then run:

```bash
sudo systemctl daemon-reload
sudo systemctl restart swasthya
```

## Updating the app

After pushing changes to GitHub:

```bash
cd /opt/swasthya
sudo git pull --ff-only
sudo /opt/swasthya/venv/bin/pip install -r requirements.txt
sudo systemctl restart swasthya
```

Do not copy your development `.env` file or API keys to this server. Ollama
does not need an API key for this local setup.
