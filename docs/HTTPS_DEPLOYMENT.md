# HTTPS Production Deployment (Azure VM)

This guide covers enabling HTTPS with Let's Encrypt on your Azure VM.

## Prerequisites

- Domain name pointed to your VM public IP (e.g. `aiops.example.com` → `172.198.64.141`)
- Azure NSG allows ports **80** and **443**
- Docker Compose stack running

## Step 1: Install Certbot on VM

```bash
sudo apt update
sudo apt install -y certbot
```

## Step 2: Obtain certificate (standalone mode)

Stop nginx temporarily if it binds port 80:

```bash
cd ~/aiops-platform/deployment
docker compose stop nginx
sudo certbot certonly --standalone -d aiops.example.com --email you@example.com --agree-tos
```

Certificates are stored at `/etc/letsencrypt/live/aiops.example.com/`.

## Step 3: Configure nginx SSL

Copy `deployment/nginx-ssl.conf.example` to `deployment/nginx-ssl.conf` and update:

- `server_name aiops.example.com;`
- SSL certificate paths

Mount certs in `docker-compose.yml`:

```yaml
nginx:
  volumes:
    - /etc/letsencrypt:/etc/letsencrypt:ro
    - ./nginx-ssl.conf:/etc/nginx/conf.d/default.conf:ro
```

## Step 4: Update environment

In `deployment/.env`:

```
FRONTEND_URL=https://aiops.example.com
CORS_ORIGINS=https://aiops.example.com
```

Rebuild:

```bash
docker compose up --build -d
```

## Step 5: Auto-renewal

```bash
sudo crontab -e
```

Add:

```
0 3 * * * certbot renew --quiet && cd /home/azureuser/aiops-platform/deployment && docker compose restart nginx
```

## Security checklist

- Remove public Postgres port 5432 from Azure NSG
- Use strong `SECRET_KEY` and `POSTGRES_PASSWORD`
- Restrict SSH to your IP in NSG
- Enable Azure Backup for the VM
