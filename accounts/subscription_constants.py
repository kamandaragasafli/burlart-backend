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
    'starter': {
        'name': 'Starter',
        'price': 19,  # ₼ (AZN)
        'currency': '₼',
        'credits': 750,
        'period_days': 30,
    },
    'pro': {
        'name': 'Pro',
        'price': 39,  # ₼ (AZN)
        'currency': '₼',
        'credits': 1800,
        'period_days': 30,
    },
    'agency': {
        'name': 'Agency',
        'price': 79,  # ₼ (AZN)
        'currency': '₼',
        'credits': 4000,
        'period_days': 30,
    },
}

