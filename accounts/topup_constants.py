"""
LOCKED TOP-UP PRICING CONSTANTS
================================
These constants define the FIXED and LOCKED pricing for top-up credit packages.
These prices CANNOT be changed from admin panel or API.
Only code modification by owner can change these values.

DO NOT MODIFY THESE VALUES WITHOUT OWNER APPROVAL.
"""

# Top-up credit packages (LOCKED)
# Format: package_id -> {price, credits}
TOPUP_PACKAGES = {
    'small': {
        'name': 'Top-up S',
        'price': 10.00,  # ₼ (AZN)
        'currency': '₼',
        'credits': 450,
    },
    'medium': {
        'name': 'Top-up M',
        'price': 25.00,  # ₼ (AZN)
        'currency': '₼',
        'credits': 1150,
        'popular': True,  # Ən çox seçilən
    },
    'large': {
        'name': 'Top-up L',
        'price': 50.00,  # ₼ (AZN)
        'currency': '₼',
        'credits': 2200,
    },
}

# Payment provider configuration
PAYMENT_PROVIDER = 'epoint'  # E-point

# Payment fees (LOCKED)
PAYMENT_COMMISSION_RATE = 0.03  # 3% komissiya
TAX_RATE = 0.04  # 4% vergi (E-point-in köçürdüyü məbləğdən)

