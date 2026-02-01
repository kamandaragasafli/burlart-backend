# Production .env Fix - EPOINT_SECRET_KEY

## Problem
Production serverdə "Signature did not match" xətası alınır, key-lər düzgün görünür.

## Ehtimal olunan səbəb
`.env` faylında `EPOINT_SECRET_KEY` quotes və ya whitespace ilə təyin edilmiş ola bilər.

## Həll

### 1. .env faylını yoxla
```bash
cd /var/www/burlart-backend
cat .env | grep EPOINT
```

### 2. .env faylını düzəlt
```bash
nano .env
```

**Düzgün format:**
```bash
EPOINT_PUBLIC_KEY=i000200937
EPOINT_SECRET_KEY=S0WXEqciyVMOOilbHNuvXuV9
```

**Səhv formatlar:**
```bash
# ❌ Quotes ilə
EPOINT_SECRET_KEY="S0WXEqciyVMOOilbHNuvXuV9"

# ❌ Boşluq ilə
EPOINT_SECRET_KEY= S0WXEqciyVMOOilbHNuvXuV9

# ❌ Sonunda boşluq
EPOINT_SECRET_KEY=S0WXEqciyVMOOilbHNuvXuV9 
```

### 3. Key-ləri verify et
```bash
python manage.py verify_epoint_env
```

Bu komanda:
- Django settings-dən key-ləri göstərir
- Environment variables-dan key-ləri göstərir
- Şəkildəki key ilə müqayisə edir

### 4. Serveri restart et
```bash
sudo systemctl restart gunicorn
# və ya
sudo supervisorctl restart burlart-backend
```

### 5. Test et
```bash
python manage.py test_epoint
```

## Qeyd
`settings.py`-də `.strip()` əlavə edildi ki, whitespace-lər avtomatik silinsin. Amma ən yaxşısı `.env` faylında düzgün format istifadə etməkdir.

