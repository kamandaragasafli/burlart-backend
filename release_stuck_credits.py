#!/usr/bin/env python
"""
Release stuck credit holds that are older than 1 hour.
This script should be run when credits are stuck in 'hold' status.
"""
import os
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from accounts.models import CreditHold

def release_stuck_credits():
    """Release credit holds that are stuck in 'hold' status for more than 1 hour"""
    
    # Find holds older than 1 hour
    one_hour_ago = timezone.now() - timedelta(hours=1)
    
    stuck_holds = CreditHold.objects.filter(
        status='hold',
        created_at__lt=one_hour_ago
    )
    
    print(f"Found {stuck_holds.count()} stuck credit holds older than 1 hour")
    
    total_released = 0
    for hold in stuck_holds:
        user_email = hold.user.email
        credits = hold.credits_held
        created = hold.created_at
        
        print(f"\nReleasing hold:")
        print(f"  User: {user_email}")
        print(f"  Credits: {credits}")
        print(f"  Created: {created}")
        print(f"  Age: {timezone.now() - created}")
        
        # Release the hold
        hold.release()
        total_released += credits
        
        print(f"  ✓ Released! User now has {hold.user.credits} credits")
    
    print(f"\n{'='*50}")
    print(f"Total credits released: {total_released}")
    print(f"Total holds released: {stuck_holds.count()}")
    print(f"{'='*50}")

if __name__ == '__main__':
    print("="*50)
    print("Releasing Stuck Credit Holds")
    print("="*50)
    release_stuck_credits()

