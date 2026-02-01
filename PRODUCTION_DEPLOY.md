# Production Deployment - EPOINT Fix

## Problem
Production-da "Signature did not match" xətası alınır, key-lər düzgündür.

## Həll
Base64 encoding-də `.decode('utf-8')` əvəzinə `.decode('ascii')` istifadə edilməlidir, çünki Base64 həmişə ASCII formatındadır.

## Deployment Addımları

### 1. Kod yenilə
```bash
# Production serverdə
cd /var/www/burlart-backend

# Git pull (əgər git istifadə edirsinizsə)
git pull origin main

# Və ya kodları manual upload edin
```

### 2. Yoxla ki, payment_service.py yenilənib
```bash
# Base64 decode-ləri yoxla
grep -n "decode('ascii')" accounts/payment_service.py

# 3 sətir tapılmalıdır:
# - Line 38: signature = base64.b64encode(sha1_hash).decode('ascii')
# - Line 147: data_encoded = base64.b64encode(...).decode('ascii')
# - Line 272: data_encoded = base64.b64encode(...).decode('ascii')
```

### 3. Serveri restart et
```bash
# Gunicorn
sudo systemctl restart gunicorn

# Və ya supervisor
sudo supervisorctl restart burlart-backend

# Və ya uWSGI
sudo systemctl restart uwsgi
```

### 4. Test et
```bash
python manage.py test_epoint
```

## Dəyişikliklər

**payment_service.py** faylında 3 yerdə dəyişiklik:

1. **Line 38** - Signature generation:
   ```python
   # Köhnə:
   signature = base64.b64encode(sha1_hash).decode('utf-8')
   
   # Yeni:
   signature = base64.b64encode(sha1_hash).decode('ascii')
   ```

2. **Line 147** - Payment request data:
   ```python
   # Köhnə:
   data_encoded = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')
   
   # Yeni:
   data_encoded = base64.b64encode(json_string.encode('utf-8')).decode('ascii')
   ```

3. **Line 272** - Status check data:
   ```python
   # Köhnə:
   data_encoded = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')
   
   # Yeni:
   data_encoded = base64.b64encode(json_string.encode('utf-8')).decode('ascii')
   ```

## Qeyd
Base64 encoding həmişə ASCII formatındadır, ona görə `.decode('ascii')` istifadə etmək daha düzgündür. `.decode('utf-8')` də işləyir, amma bəzi sistemlərdə problem yarada bilər.

