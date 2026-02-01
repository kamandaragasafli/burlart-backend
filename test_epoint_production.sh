#!/bin/bash
# EPOINT Production Test Script
# Bu script production serverdə işlədilir

echo "======================================================================"
echo "EPOINT Production Test"
echo "======================================================================"
echo ""

# Django environment setup
cd /var/www/burlart-backend || cd /path/to/burlart-backend

# Virtual environment aktivləşdir (əgər varsa)
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Python one-liner ilə test
python3 <<'PYTHON_SCRIPT'
import os
import sys
import django

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
import json
import base64
import hashlib
import requests
from collections import OrderedDict
from decimal import Decimal, ROUND_HALF_UP
import time

# Key-ləri yoxla
public_key = getattr(settings, 'EPOINT_PUBLIC_KEY', None)
secret_key = getattr(settings, 'EPOINT_SECRET_KEY', None)

if not public_key or not secret_key:
    print("❌ XƏTA: EPOINT_PUBLIC_KEY və EPOINT_SECRET_KEY .env faylında təyin edilməlidir")
    sys.exit(1)

print(f"🔑 Key-lər:")
print(f"   Public key: {public_key}")
print(f"   Private key length: {len(secret_key)} chars")
print()

# Test parametrləri
amount = 0.10
currency = 'AZN'
description = 'Production test payment'
order_id = f"PROD_TEST_{int(time.time())}"

# Amount canonical format
amount_decimal = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
amount_str = format(amount_decimal, 'f')

# JSON yarad
payment_data_json = OrderedDict([
    ('public_key', public_key),
    ('amount', amount_str),
    ('currency', currency),
    ('language', 'az'),
])

if description:
    payment_data_json['description'] = description

payment_data_json['order_id'] = str(order_id)

# JSON string
json_string = json.dumps(payment_data_json, separators=(',', ':'), ensure_ascii=False, sort_keys=False)

# Base64 encode
data_encoded = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')

# Base64 padding yoxla
if len(data_encoded) % 4 != 0:
    print(f"❌ XƏTA: Base64 uzunluğu 4-ə bölünmür: {len(data_encoded)}")
    sys.exit(1)

# Signature yarad
hash_string = secret_key + data_encoded + secret_key
sha1_hash = hashlib.sha1(hash_string.encode('utf-8')).digest()
signature = base64.b64encode(sha1_hash).decode('utf-8')

print("📋 Request:")
print(f"   Amount: {amount_str} {currency}")
print(f"   Order ID: {order_id}")
print(f"   Data length: {len(data_encoded)} chars, mod 4: {len(data_encoded) % 4}")
print()

print("🚀 EPOINT API-yə request göndərilir...")
print()

# API request
try:
    response = requests.post(
        'https://epoint.az/api/1/request',
        data={
            'data': data_encoded,
            'signature': signature
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=30
    )
    
    print(f"📡 Response Status: {response.status_code}")
    print()
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print()
        
        if result.get('status') == 'success':
            print("🎉 SUCCESS! Payment request uğurla yaradıldı!")
            if 'redirect_url' in result:
                print(f"   Redirect URL: {result['redirect_url']}")
            if 'transaction' in result:
                print(f"   Transaction ID: {result['transaction']}")
        elif result.get('status') == 'error':
            print("❌ ERROR!")
            print(f"   Message: {result.get('message', 'Unknown error')}")
    else:
        print(f"❌ HTTP {response.status_code}")
        print(f"   Response: {response.text[:500]}")
        
except Exception as e:
    print(f"❌ XƏTA: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

PYTHON_SCRIPT

echo ""
echo "======================================================================"

