#!/bin/bash
# EPOINT Test Request - One-liner (serverdə işlədilir)
# İstifadə: bash test_epoint_one_liner.sh

python3 - <<'PY'
import json, base64, hashlib, os

PRIVATE_KEY = os.getenv("EPOINT_SECRET_KEY")
PUBLIC_KEY = os.getenv("EPOINT_PUBLIC_KEY", "i000200937")

if not PRIVATE_KEY:
    print("❌ XƏTA: EPOINT_SECRET_KEY environment variable təyin edilməlidir")
    exit(1)

payload = {
    "public_key": PUBLIC_KEY,
    "amount": "0.10",
    "currency": "AZN",
    "language": "az",
    "description": "Test payment",  # ASCII-only
    "order_id": "TEST_1769966068"
}

json_string = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
data = base64.b64encode(json_string.encode("utf-8")).decode("ascii")

# Base64 padding yoxla
data_len = len(data)
mod4 = data_len % 4
if mod4 != 0:
    print(f"❌ XƏTA: Base64 uzunluğu 4-ə bölünmür: {data_len}, mod 4: {mod4}")
    exit(1)

sgn_string = PRIVATE_KEY + data + PRIVATE_KEY
signature = base64.b64encode(hashlib.sha1(sgn_string.encode("utf-8")).digest()).decode("ascii")

print("=" * 70)
print("EPOINT Test Request - One-liner Output")
print("=" * 70)
print()
print("json:", json_string)
print("data_len:", data_len, "mod4:", mod4, "✅" if mod4 == 0 else "❌")
print("data:", data)
print("signature:", signature)
print()
print("=" * 70)
print("CURL Command:")
print("=" * 70)
print()
print(f'curl -s -X POST "https://epoint.az/api/1/request" \\')
print(f'  --data-urlencode "data={data}" \\')
print(f'  --data-urlencode "signature={signature}"')
print()
PY

