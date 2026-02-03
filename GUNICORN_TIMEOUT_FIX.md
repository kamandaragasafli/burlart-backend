# Gunicorn Timeout Fix

## Problem
Video generation çox vaxt alır (2-5 dəqiqə) amma Gunicorn default timeout 30 saniyədir.
Nəticədə request timeout verir və kreditlər tutulur amma video yaranmır.

## Həll

### 1. Systemd Service File-ı Redaktə Et

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

### 2. Timeout-u Artır

Gunicorn əmrində `--timeout` parametrini əlavə et:

```ini
[Unit]
Description=gunicorn daemon for burlart backend
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/burlart-backend
Environment="PATH=/var/www/burlart-backend/venv/bin"
ExecStart=/var/www/burlart-backend/venv/bin/gunicorn \
    --workers 3 \
    --timeout 900 \
    --bind unix:/var/www/burlart-backend/gunicorn.sock \
    config.wsgi:application

[Install]
WantedBy=multi-user.target
```

**Əsas parametrlər:**
- `--timeout 900` - 15 dəqiqə timeout (video generation üçün kifayətdir)
- `--workers 3` - 3 worker process
- `--bind unix:...` - Unix socket istifadə et

### 3. Systemd-i Yenilə və Restart Et

```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
sudo systemctl status gunicorn
```

### 4. Nginx Timeout-ları da Artır (əlavə)

```bash
sudo nano /etc/nginx/sites-available/burlart-backend
```

Əlavə et:

```nginx
location / {
    proxy_pass http://unix:/var/www/burlart-backend/gunicorn.sock;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Extended timeouts for long-running requests
    proxy_connect_timeout 900s;
    proxy_send_timeout 900s;
    proxy_read_timeout 900s;
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

## Test

Video generation test et:
- Video 5 dəqiqə çəkə bilər
- Timeout xətası gəlməməlidir
- Kreditlər düzgün tutulmalıdır

## Loglar

```bash
# Gunicorn logları
sudo journalctl -u gunicorn -f

# Nginx error logları
sudo tail -f /var/log/nginx/error.log

# Backend application logları
sudo tail -f /var/log/nginx/access.log
```

