"""
LOCKED PRICING CONSTANTS
========================
These constants define the FIXED and LOCKED pricing for all AI models.
These prices CANNOT be changed from admin panel or API.
Only code modification by owner can change these values.

DO NOT MODIFY THESE VALUES WITHOUT OWNER APPROVAL.
"""

# Video model pricing (LOCKED - 5 seconds video)
VIDEO_MODEL_CREDITS = {
    'pika': 52,       # Pika v2.2 (orta) - 52 token
    'seedance': 39,   # Seedance v1 Pro      - 39 token
    'wan': 24,        # Wan v2.6             - 24 token
    'luma': 32,       # Luma Ray-2 Flash     - 32 token
    'kling': 55,      # Kling v2.5 Turbo     - 55 token
    'veo': 238,       # Veo 3 (orta)         - 238 token
    'sora': 79,       # Sora 2               - 79 token
}

# Image model pricing (LOCKED)
IMAGE_MODEL_CREDITS = {
    'gpt-image': 16,      # GPT Image 1.5 (orta)  - 16 token
    'nano-banana': 47,    # Nano Banana Pro (4K)  - 47 token
    'seedream': 6,        # Seedream v4.5         - 6 token
    'flux': 6,            # Flux 2 Pro (orta)     - 6 token
    'z-image': 2,         # Z-Image (Turbo)       - 2 token
    'qwen': 6,            # Qwen Image 2512       - 6 token
}

# ============================================================================
# SUBSCRIPTION PLANS CONFIGURATION
# ============================================================================
# Monthly subscription packages with fixed pricing
# All plans give access to ALL AI tools, difference is only credit amount
# ============================================================================
SUBSCRIPTION_PLANS = {
    'demo': {
        'name': 'Demo',
        'price': 0.10,  # AZN (10 qəpik)
        'currency': '₼',
        'credits': 500,  # Demo credits
        'period_days': 7,
        'features': [
            'Bütün AI alətlərinə demo giriş',
            '500 kredit',
            'Qısa müddətli test paketi',
        ],
    },
    'starter': {
        'name': 'Starter',
        'price': 19,  # AZN
        'currency': '₼',
        'credits': 750,  # Monthly credits
        'period_days': 30,
        'features': [
            'Bütün AI alətlərinə giriş',
            '750 kredit / ay',
            'Avtomatik yenilənmə',
        ],
    },
    'pro': {
        'name': 'Pro',
        'price': 39,  # AZN
        'currency': '₼',
        'credits': 1800,  # Monthly credits
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
        'price': 79,  # AZN
        'currency': '₼',
        'credits': 4000,  # Monthly credits
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

# Validation function to ensure prices match constants
# Note: This function is called from services.py after all imports are complete
def validate_locked_prices(video_config, image_config):
    """
    Validates that service config prices match locked constants.
    This ensures prices cannot be changed accidentally.
    
    Args:
        video_config: VIDEO_TOOL_CONFIG from services.py
        image_config: IMAGE_TOOL_CONFIG from services.py
    """
    errors = []
    
    # Validate video prices
    for tool_id, credits in VIDEO_MODEL_CREDITS.items():
        if tool_id in video_config:
            if video_config[tool_id]['credits'] != credits:
                errors.append(
                    f"Video model '{tool_id}': Config has {video_config[tool_id]['credits']} "
                    f"but locked price is {credits}"
                )
    
    # Validate image prices
    for tool_id, credits in IMAGE_MODEL_CREDITS.items():
        if tool_id in image_config:
            if image_config[tool_id]['credits'] != credits:
                errors.append(
                    f"Image model '{tool_id}': Config has {image_config[tool_id]['credits']} "
                    f"but locked price is {credits}"
                )
    
    if errors:
        raise ValueError(
            "LOCKED PRICING MISMATCH! Prices in services.py do not match constants.py. "
            f"Errors: {', '.join(errors)}"
        )
    
    return True

