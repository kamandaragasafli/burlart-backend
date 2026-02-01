# EPOINT Production Fix - Signature Mismatch

## Problem
Production-da "Signature did not match" xətası alınır.

## Səbəb
Production serverdəki `EPOINT_SECRET_KEY` EPOINT panel-dəki key ilə uyğun gəlmir.

## Həll

### 1. Key-ləri yoxla
Production serverdə:
```bash
python manage.py debug_epoint_keys
```

### 2. EPOINT panel-dən key-i kopyala
1. EPOINT panel-ə daxil ol: https://epoint.az
2. "API Idarəetmə" → "Bağlantı parametrləri" bölməsinə get
3. "Şəxsi açar" (Private key) yanındakı "Kopyalamaq" düyməsinə bas
4. Key-i kopyala: `S0WXEqciyVMOOilbHNuvXuV9`

### 3. Production .env faylını yenilə
```bash
# Serverdə .env faylını redaktə et
nano /var/www/burlart-backend/.env

# EPOINT_SECRET_KEY sətirini yenilə:
EPOINT_SECRET_KEY=S0WXEqciyVMOOilbHNuvXuV9

# Yadda saxla və çıx (Ctrl+X, Y, Enter)
```

### 4. Serveri restart et
```bash
# Gunicorn restart (əgər istifadə edirsinizsə)
sudo systemctl restart gunicorn

# Və ya supervisor restart
sudo supervisorctl restart burlart-backend

# Və ya uWSGI restart
sudo systemctl restart uwsgi
```

### 5. Yenidən test et
```bash
python manage.py test_epoint
```

## Yoxlama
Test uğurlu olmalıdır:
```
✅ SUCCESS!
📋 Response:
{
  "success": true,
  "transaction_id": "...",
  "payment_url": "https://ecomm.pashabank.az/...",
  ...
}
```

## Qeyd
- Key-də boşluq və ya xüsusi simvollar olmamalıdır
- Key tam kopyalanmalıdır (24 chars)
- `.env` faylında quotes olmamalıdır: `EPOINT_SECRET_KEY=key` (düzgün), `EPOINT_SECRET_KEY="key"` (səhv)

