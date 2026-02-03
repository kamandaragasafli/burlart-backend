# Stuck Credits Fix

## Problem
Əvvəlki uğursuz video generation cəhdlərindən kreditlər "held" statusunda qalıb və release olunmayıb.

```
Available: 224 kredit
Held: 156 kredit ← PROBLEM
Actually Available: 68 kredit
```

## Həll

### 1. Serverdə Script İşlət

```bash
# Backend serverdə
cd /var/www/burlart-backend

# Virtual environment aktivləşdir
source venv/bin/activate

# Script-i işə sal
python release_stuck_credits.py
```

### 2. Django Shell ilə Manual Release

```bash
python manage.py shell
```

```python
from accounts.models import CreditHold
from django.utils import timezone
from datetime import timedelta

# 1 saatdan köhnə held credits-ləri tap
one_hour_ago = timezone.now() - timedelta(hours=1)
stuck_holds = CreditHold.objects.filter(
    status='hold',
    created_at__lt=one_hour_ago
)

print(f"Found {stuck_holds.count()} stuck holds")

# Hamısını release et
for hold in stuck_holds:
    print(f"Releasing {hold.credits_held} credits for {hold.user.email}")
    hold.release()

print("Done!")
```

### 3. Konkret İstifadəçi üçün

```python
from accounts.models import CreditHold, User

# İstifadəçini tap
user = User.objects.get(email='ilkintanat1907@gmail.com')

# Onun held credits-lərini tap
holds = CreditHold.objects.filter(user=user, status='hold')
print(f"User has {holds.count()} held credits totaling {sum(h.credits_held for h in holds)} credits")

# Hamısını release et
for hold in holds:
    hold.release()
    
print(f"User now has {user.credits} available credits")
```

## Avtomatik Həll (Tövsiyə)

### Cron Job Yarat

```bash
# Crontab redaktə et
crontab -e
```

Əlavə et (hər saat işləsin):

```cron
0 * * * * cd /var/www/burlart-backend && /var/www/burlart-backend/venv/bin/python /var/www/burlart-backend/release_stuck_credits.py >> /var/log/release_credits.log 2>&1
```

## Preventive Fix

Backend-də artıq timeout handling var:
- Timeout olarsa, kreditlər avtomatik release olunur
- Exception olarsa, kreditlər avtomatik release olunur

Amma əgər process kill olarsa (server restart, memory issue), held credits qala bilər.

## Monitoring

```bash
# Held credits-ləri yoxla
python manage.py shell
```

```python
from accounts.models import CreditHold
from django.db.models import Sum

# Ümumi held credits
total_held = CreditHold.objects.filter(status='hold').aggregate(
    total=Sum('credits_held')
)['total'] or 0

print(f"Total held credits across all users: {total_held}")

# User-lərə görə
from django.contrib.auth import get_user_model
User = get_user_model()

for user in User.objects.all():
    held = CreditHold.objects.filter(user=user, status='hold').aggregate(
        total=Sum('credits_held')
    )['total'] or 0
    if held > 0:
        print(f"{user.email}: {held} held credits")
```

