#!/usr/bin/env python
"""
EPOINT Test Request Generator
Bu script EPOINT API-yə test request göndərmək üçün data və signature yaradır.

İstifadə:
    python test_epoint_request.py

Və ya environment variables ilə:
    EPOINT_PUBLIC_KEY=your_public_key EPOINT_SECRET_KEY=your_secret_key python test_epoint_request.py
"""
import os
import sys
import json
import base64
import hashlib
from collections import OrderedDict
from decimal import Decimal, ROUND_HALF_UP

# Django settings import etmək üçün
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings


def generate_signature(data_encoded: str, private_key: str) -> str:
    """
    Generate E-point signature: base64_encode(sha1(private_key + data + private_key))
    """
    hash_string = private_key + data_encoded + private_key
    sha1_hash = hashlib.sha1(hash_string.encode('utf-8')).digest()
    signature = base64.b64encode(sha1_hash).decode('utf-8')
    return signature


def create_epoint_request(amount, currency='AZN', description='Test payment', order_id=None):
    """
    EPOINT request üçün data və signature yaradır
    """
    # Settings-dən key-ləri al
    public_key = getattr(settings, 'EPOINT_PUBLIC_KEY', None)
    secret_key = getattr(settings, 'EPOINT_SECRET_KEY', None)
    
    if not public_key or not secret_key:
        print("❌ XƏTA: EPOINT_PUBLIC_KEY və EPOINT_SECRET_KEY .env faylında təyin edilməlidir")
        print("\nNümunə .env konfiqurasiyası:")
        print("EPOINT_PUBLIC_KEY=i000000001")
        print("EPOINT_SECRET_KEY=your_secret_key_here")
        sys.exit(1)
    
    # Order ID yoxdursa, generate et
    if not order_id:
        import time
        order_id = f"TEST_{int(time.time())}"
    
    # Amount-u canonical format-a çevir
    amount_decimal = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    amount_str = format(amount_decimal, 'f')  # "0.10", "10.00" kimi
    
    # JSON string yarad (key order vacibdir)
    payment_data_json = OrderedDict([
        ('public_key', public_key),
        ('amount', amount_str),
        ('currency', currency),
        ('language', 'az'),
    ])
    
    # Description ASCII saxla (qeyri-ASCII simvollar problem yarada bilər)
    if description:
        # ASCII-only description for testing
        payment_data_json['description'] = description.encode('ascii', 'ignore').decode('ascii')
    
    payment_data_json['order_id'] = str(order_id)
    
    # JSON string-ə çevir
    # ensure_ascii=False istifadə edirik, amma description artıq ASCII-dir
    json_string = json.dumps(payment_data_json, separators=(',', ':'), ensure_ascii=False, sort_keys=False)
    
    # Base64 encode (UTF-8 ilə)
    data_encoded = base64.b64encode(json_string.encode('utf-8')).decode('ascii')
    
    # Base64 padding yoxla (uzunluq 4-ə bölünməlidir)
    data_len = len(data_encoded)
    padding_needed = (4 - (data_len % 4)) % 4
    if padding_needed > 0:
        print(f"⚠️  XƏBƏRDARLIQ: Base64 padding yoxlanışı - uzunluq: {data_len}, mod 4: {data_len % 4}")
        # Base64 b64encode avtomatik padding əlavə edir, amma yoxlayaq
        # Decode edib yenidən encode edək
        try:
            decoded = base64.b64decode(data_encoded + '=' * padding_needed)
            data_encoded = base64.b64encode(decoded).decode('ascii')
        except Exception:
            pass  # Artıq düzgündür
    
    # Final padding yoxla
    if len(data_encoded) % 4 != 0:
        print(f"❌ XƏTA: Base64 uzunluğu 4-ə bölünmür: {len(data_encoded)}")
        sys.exit(1)
    
    # Signature yarad
    signature = generate_signature(data_encoded, secret_key)
    
    return {
        'json_string': json_string,
        'data_encoded': data_encoded,
        'signature': signature,
        'order_id': order_id,
        'amount': amount_str,
        'data_len': len(data_encoded),
        'data_len_mod4': len(data_encoded) % 4,
    }


def main():
    print("=" * 70)
    print("EPOINT Test Request Generator")
    print("=" * 70)
    print()
    
    # Test parametrləri
    amount = 0.10  # Test məbləği
    currency = 'AZN'
    description = 'Test payment'
    
    try:
        result = create_epoint_request(amount, currency, description)
        
        print("✅ Request hazırlandı!")
        print()
        print("📋 Parametrlər:")
        print(f"   Amount: {result['amount']} {currency}")
        print(f"   Order ID: {result['order_id']}")
        print(f"   Description: {description}")
        print()
        print("📄 JSON String:")
        print(f"   {result['json_string']}")
        print()
        print("🔐 Data (Base64 Encoded):")
        print(f"   Length: {result['data_len']} chars, mod 4: {result['data_len_mod4']} ✅" if result['data_len_mod4'] == 0 else f"   Length: {result['data_len']} chars, mod 4: {result['data_len_mod4']} ❌")
        print(f"   {result['data_encoded']}")
        print()
        print("✍️  Signature:")
        print(f"   {result['signature']}")
        print()
        print("=" * 70)
        print("CURL Command (copy entire block):")
        print("=" * 70)
        print()
        # Single line curl command - easier to copy
        curl_cmd = f"curl -s -X POST \"https://epoint.az/api/1/request\" --data-urlencode \"data={result['data_encoded']}\" --data-urlencode \"signature={result['signature']}\""
        print(curl_cmd)
        print()
        print("=" * 70)
        print("CURL Command (multiline - for readability):")
        print("=" * 70)
        print()
        print("curl -s -X POST \"https://epoint.az/api/1/request\" \\")
        print(f"  --data-urlencode \"data={result['data_encoded']}\" \\")
        print(f"  --data-urlencode \"signature={result['signature']}\"")
        print()
        print("=" * 70)
        print("Və ya Python requests ilə:")
        print("=" * 70)
        print()
        print("import requests")
        print()
        print("response = requests.post(")
        print("    'https://epoint.az/api/1/request',")
        print("    data={")
        print(f"        'data': '{result['data_encoded']}',")
        print(f"        'signature': '{result['signature']}'")
        print("    },")
        print("    headers={'Content-Type': 'application/x-www-form-urlencoded'}")
        print(")")
        print()
        print("print(response.json())")
        print()
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ XƏTA: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

