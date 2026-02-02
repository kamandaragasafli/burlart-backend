"""
LOCKED SUBSCRIPTION PRICING CONSTANTS
======================================
These constants define the FIXED and LOCKED pricing for subscription plans.
These prices CANNOT be changed from admin panel or API.
Only code modification by owner can change these values.

DO NOT MODIFY THESE VALUES WITHOUT OWNER APPROVAL.
"""

# Subscription plan configuration (LOCKED)
SUBSCRIPTION_PLANS = {
    'demo': {
        'name': 'Demo',
        'price': 0.10,  # ₼ (AZN) - Demo test paketi
        'currency': '₼',
        'credits': 500,
        'period_days': 7,  # 7 gün demo
        'features': [
            'Bütün AI alətlərinə giriş',
            '500 kredit / həftə',
            'Demo paket',
        ],
    },
    'starter': {
        'name': 'Starter',
        'price': 19,  # ₼ (AZN)
        'currency': '₼',
        'credits': 750,
        'period_days': 30,
        'features': [
            'Bütün AI alətlərinə giriş',
            '750 kredit / ay',
            'Avtomatik yenilənmə',
        ],
    },
    'pro': {
        'name': 'Pro',
        'price': 39,  # ₼ (AZN)
        'currency': '₼',
        'credits': 1800,
        'period_days': 30,
        'features': [
            'Bütün AI alətlərinə giriş',
            '1,800 kredit / ay',
            'Avtomatik yenilənmə',
            'Prioritet dəstək',
        ],
    },
    'agency': {
        'name': 'Agency',
        'price': 79,  # ₼ (AZN)
        'currency': '₼',
        'credits': 4000,
        'period_days': 30,
        'features': [
            'Bütün AI alətlərinə giriş',
            '4,000 kredit / ay',
            'Avtomatik yenilənmə',
            'Prioritet dəstək',
            'Dedicated account manager',
        ],
    },
}

