#!/usr/bin/env python
"""
EPOINT Test Request - Real API Test
Bu script EPOINT API-yə real request göndərir və cavabı göstərir.
"""
import sys
import os
import json
import base64
import hashlib
import requests
from collections import OrderedDict
from decimal import Decimal, ROUND_HALF_UP

# Django settings import etmək üçün
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings


def generate_signature(data_encoded: str, private_key: str) -> str:
    """Generate E-point signature"""
    hash_string = private_key + data_encoded + private_key
    sha1_hash = hashlib.sha1(hash_string.encode('utf-8')).digest()
    signature = base64.b64encode(sha1_hash).decode('utf-8')
    return signature


def main():
    print("=" * 70)
    print("EPOINT Real API Test")
    print("=" * 70)
    print()
    
    # Settings-dən key-ləri al
    public_key = getattr(settings, 'EPOINT_PUBLIC_KEY', None)
    secret_key = getattr(settings, 'EPOINT_SECRET_KEY', None)
    
    # Şəkildə görünən key-lər (test üçün)
    # Public key: 1000200937 (amma kodda i000200937 prefiksi ilə istifadə olunur)
    # Private key: S0WXEqciyVMOOilbHNuvXuV9
    
    if not public_key or not secret_key:
        print("❌ XƏTA: EPOINT_PUBLIC_KEY və EPOINT_SECRET_KEY .env faylında təyin edilməlidir")
        print()
        print("📋 Şəkildə görünən key-lər:")
        print("   Public key: 1000200937 (kodda i000200937 prefiksi ilə)")
        print("   Private key: S0WXEqciyVMOOilbHNuvXuV9")
        print()
        print("⚠️  QEYD: Public key-də 'i' prefiksi olmalıdır!")
        sys.exit(1)
    
    # Public key-də 'i' prefiksi yoxdursa əlavə et
    if not public_key.startswith('i'):
        print(f"⚠️  XƏBƏRDARLIQ: Public key-də 'i' prefiksi yoxdur. Əlavə edilir: i{public_key}")
        public_key = f"i{public_key}"
    
    print(f"🔑 İstifadə olunan key-lər:")
    print(f"   Public key: {public_key}")
    print(f"   Private key length: {len(secret_key) if secret_key else 0} chars")
    print()
    
    # Test parametrləri
    import time
    amount = 0.10
    currency = 'AZN'
    description = 'Test payment'
    order_id = f"TEST_{int(time.time())}"
    
    # Amount-u canonical format-a çevir
    amount_decimal = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    amount_str = format(amount_decimal, 'f')
    
    # JSON string yarad
    payment_data_json = OrderedDict([
        ('public_key', public_key),
        ('amount', amount_str),
        ('currency', currency),
        ('language', 'az'),
    ])
    
    # Description olduğu kimi qalır (payment_service.py ilə eyni)
    if description:
        payment_data_json['description'] = description
    
    payment_data_json['order_id'] = str(order_id)
    
    # JSON string-ə çevir
    json_string = json.dumps(payment_data_json, separators=(',', ':'), ensure_ascii=False, sort_keys=False)
    
    # Base64 encode (UTF-8 ilə encode, ASCII ilə decode - payment_service.py ilə eyni)
    data_encoded = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')
    
    # Base64 padding yoxla
    data_len = len(data_encoded)
    if data_len % 4 != 0:
        print(f"❌ XƏTA: Base64 uzunluğu 4-ə bölünmür: {data_len}, mod 4: {data_len % 4}")
        sys.exit(1)
    
    # Debug: JSON string və data yoxla
    print("🔍 Debug Info:")
    print(f"   JSON string: {json_string}")
    print(f"   JSON string length: {len(json_string)}")
    print(f"   Data encoded length: {data_len}")
    print(f"   Data encoded (first 100): {data_encoded[:100]}...")
    print()
    
    # Signature yarad (payment_service.py ilə eyni metod)
    signature = generate_signature(data_encoded, secret_key)
    
    # Debug: Signature yoxla
    print("🔍 Signature Debug:")
    hash_string = secret_key + data_encoded + secret_key
    print(f"   Hash string length: {len(hash_string)}")
    print(f"   Hash string (first 50): {hash_string[:50]}...")
    print(f"   Signature: {signature}")
    print()
    
    print("📋 Request Parametrləri:")
    print(f"   Amount: {amount_str} {currency}")
    print(f"   Order ID: {order_id}")
    print(f"   Description: {description}")
    print()
    print("🔐 Data (Base64):")
    print(f"   Length: {data_len} chars, mod 4: {data_len % 4} ✅")
    print(f"   {data_encoded}")
    print()
    print("✍️  Signature:")
    print(f"   {signature}")
    print()
    print("=" * 70)
    print("🚀 EPOINT API-yə request göndərilir...")
    print("=" * 70)
    print()
    
    try:
        # EPOINT API-yə request göndər
        response = requests.post(
            'https://epoint.az/api/1/request',
            data={
                'data': data_encoded,
                'signature': signature
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            timeout=30
        )
        
        print(f"📡 Response Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ Response JSON:")
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
                    print(f"⚠️  Unknown status: {result.get('status')}")
                    
            except json.JSONDecodeError:
                print("❌ XƏTA: Response JSON deyil!")
                print(f"   Response text: {response.text[:500]}")
        else:
            print(f"❌ XƏTA: HTTP {response.status_code}")
            print(f"   Response text: {response.text[:500]}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ XƏTA: Request exception - {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ XƏTA: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print()
    print("=" * 70)


if __name__ == '__main__':
    main()

