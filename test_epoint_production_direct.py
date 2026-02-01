#!/usr/bin/env python
"""
Production serverdə birbaşa test - Django-dan asılı deyil
İstifadə: python test_epoint_production_direct.py
"""
import json
import base64
import hashlib
import requests
from collections import OrderedDict
from decimal import Decimal, ROUND_HALF_UP
import time
import os

# Key-ləri environment-dən al
PUBLIC_KEY = os.getenv('EPOINT_PUBLIC_KEY', 'i000200937')
SECRET_KEY = os.getenv('EPOINT_SECRET_KEY', 'S0WXEqciyVMOOilbHNuvXuV9')

print("=" * 70)
print("EPOINT Direct Test (No Django)")
print("=" * 70)
print()

print(f"🔑 Key-lər:")
print(f"   Public key: {PUBLIC_KEY}")
print(f"   Private key: {SECRET_KEY}")
print(f"   Private key length: {len(SECRET_KEY)} chars")
print()

# Test parametrləri
amount = 0.10
currency = 'AZN'
description = 'Production test payment'
order_id = f"DIRECT_TEST_{int(time.time())}"

# Amount canonical format
amount_decimal = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
amount_str = format(amount_decimal, 'f')

# JSON yarad
payload = OrderedDict([
    ('public_key', PUBLIC_KEY),
    ('amount', amount_str),
    ('currency', currency),
    ('language', 'az'),
])

if description:
    payload['description'] = description

payload['order_id'] = str(order_id)

# JSON string
json_string = json.dumps(payload, separators=(',', ':'), ensure_ascii=False, sort_keys=False)

# Base64 encode
data_encoded = base64.b64encode(json_string.encode('utf-8')).decode('ascii')

# Base64 padding yoxla
if len(data_encoded) % 4 != 0:
    print(f"❌ XƏTA: Base64 uzunluğu 4-ə bölünmür: {len(data_encoded)}")
    exit(1)

# Signature yarad
hash_string = SECRET_KEY + data_encoded + SECRET_KEY
sha1_hash = hashlib.sha1(hash_string.encode('utf-8')).digest()
signature = base64.b64encode(sha1_hash).decode('ascii')

print("📋 Request:")
print(f"   Amount: {amount_str} {currency}")
print(f"   Order ID: {order_id}")
print(f"   Data length: {len(data_encoded)} chars, mod 4: {len(data_encoded) % 4}")
print()
print("🔐 Data (first 100 chars):")
print(f"   {data_encoded[:100]}...")
print()
print("✍️  Signature:")
print(f"   {signature}")
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
            print()
            print("🔍 Debug Info:")
            print(f"   JSON: {json_string}")
            print(f"   Data: {data_encoded}")
            print(f"   Signature: {signature}")
            print(f"   Hash string (first 50): {hash_string[:50]}...")
    else:
        print(f"❌ HTTP {response.status_code}")
        print(f"   Response: {response.text[:500]}")
        
except Exception as e:
    print(f"❌ XƏTA: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)

print()
print("=" * 70)

