# Production Direct Test (Django-dan asılı deyil)

Production serverdə bu komandanı işlədin:

```bash
cd /var/www/burlart-backend

# Environment variables export et
export EPOINT_PUBLIC_KEY="i000200937"
export EPOINT_SECRET_KEY="S0WXEqciyVMOOilbHNuvXuV9"

# Python one-liner ilə test
python3 <<'PY'
import json, base64, hashlib, requests, os
from collections import OrderedDict
from decimal import Decimal, ROUND_HALF_UP
import time

PUBLIC_KEY = os.getenv("EPOINT_PUBLIC_KEY", "i000200937")
SECRET_KEY = os.getenv("EPOINT_SECRET_KEY", "S0WXEqciyVMOOilbHNuvXuV9")

print("=" * 70)
print("EPOINT Direct Test")
print("=" * 70)
print()
print(f"Public key: {PUBLIC_KEY}")
print(f"Private key: {SECRET_KEY}")
print(f"Private key length: {len(SECRET_KEY)} chars")
print()

# Test data
amount = 0.10
amount_decimal = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
amount_str = format(amount_decimal, 'f')

payload = OrderedDict([
    ("public_key", PUBLIC_KEY),
    ("amount", amount_str),
    ("currency", "AZN"),
    ("language", "az"),
    ("description", "Production test payment"),
    ("order_id", f"DIRECT_{int(time.time())}")
])

json_string = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
data = base64.b64encode(json_string.encode("utf-8")).decode("ascii")

print(f"JSON: {json_string}")
print(f"Data length: {len(data)}, mod 4: {len(data) % 4}")
print(f"Data (first 100): {data[:100]}...")
print()

sgn_string = SECRET_KEY + data + SECRET_KEY
signature = base64.b64encode(hashlib.sha1(sgn_string.encode("utf-8")).digest()).decode("ascii")

print(f"Signature: {signature}")
print()

print("Sending request...")
response = requests.post(
    "https://epoint.az/api/1/request",
    data={"data": data, "signature": signature},
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=30
)

print(f"Status: {response.status_code}")
result = response.json()
print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")

if result.get("status") == "success":
    print("\n🎉 SUCCESS!")
    print(f"Transaction: {result.get('transaction')}")
    print(f"Redirect URL: {result.get('redirect_url')}")
else:
    print(f"\n❌ ERROR: {result.get('message')}")
PY
```

Bu test Django-dan asılı deyil və birbaşa EPOINT API-yə request göndərir.

