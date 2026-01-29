"""
Subscription Service
Handles subscription creation, renewal, and credit management
"""
import logging
from django.utils import timezone
from datetime import timedelta
from .models import Subscription, User
from .subscription_constants import SUBSCRIPTION_PLANS

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for managing subscriptions"""
    
    @staticmethod
    def create_subscription(user, plan_type, auto_renew=True, payment_id=None):
        """
        Create a new subscription for user
        
        Args:
            user: User instance
            plan_type: 'starter', 'pro', or 'agency'
            auto_renew: Whether to auto-renew (default: True)
            payment_id: Payment transaction ID (optional)
        
        Returns:
            Subscription instance
        """
        if plan_type not in SUBSCRIPTION_PLANS:
            raise ValueError(f"Invalid plan type: {plan_type}")
        
        plan_config = SUBSCRIPTION_PLANS[plan_type]
        
        # Delete any existing subscription for this user (OneToOneField constraint)
        # We need to delete, not just cancel, because OneToOneField allows only one subscription per user
        existing = Subscription.objects.filter(user=user)
        if existing.exists():
            # Cancel first (to update status)
            for sub in existing:
                try:
                    sub.cancel()
                except:
                    pass
            # Then delete to allow new subscription
            existing.delete()
        
        # Create new subscription
        now = timezone.now()
        period_end = now + timedelta(days=plan_config['period_days'])
        
        subscription = Subscription.objects.create(
            user=user,
            plan=plan_type,
            status='pending',
            auto_renew=auto_renew,
            period_start=now,
            period_end=period_end,
            next_renewal_date=period_end,
            payment_id=payment_id,
        )
        
        # Activate and grant credits only if payment_id is provided (payment already completed)
        if payment_id:
            subscription.activate()
        # Otherwise, subscription stays pending until payment is completed via webhook
        
        logger.info(
            f"Subscription created - User: {user.email}, Plan: {plan_type}, "
            f"Credits: {plan_config['credits']}, Auto-renew: {auto_renew}, "
            f"Status: {'active' if payment_id else 'pending'}"
        )
        
        return subscription
    
    @staticmethod
    def renew_subscriptions():
        """
        Renew all subscriptions that are due for renewal
        This should be called by a cron job or scheduled task
        """
        now = timezone.now()
        
        # Find subscriptions that need renewal
        # Renew 1 day before expiration to ensure continuity
        renew_date = now + timedelta(days=1)
        
        subscriptions_to_renew = Subscription.objects.filter(
            status='active',
            auto_renew=True,
            period_end__lte=renew_date,
            period_end__gte=now  # Not already expired
        )
        
        renewed_count = 0
        failed_count = 0
        
        for subscription in subscriptions_to_renew:
            try:
                if subscription.renew():
                    renewed_count += 1
                    logger.info(
                        f"Subscription renewed - User: {subscription.user.email}, "
                        f"Plan: {subscription.plan}"
                    )
                else:
                    failed_count += 1
                    logger.warning(
                        f"Subscription renewal failed - User: {subscription.user.email}, "
                        f"Plan: {subscription.plan}"
                    )
            except Exception as e:
                failed_count += 1
                logger.error(
                    f"Error renewing subscription - User: {subscription.user.email}, "
                    f"Plan: {subscription.plan}, Error: {str(e)}",
                    exc_info=True
                )
        
        # Mark expired subscriptions
        expired = Subscription.objects.filter(
            status='active',
            period_end__lt=now
        )
        
        expired_count = expired.update(status='expired')
        
        logger.info(
            f"Subscription renewal completed - Renewed: {renewed_count}, "
            f"Failed: {failed_count}, Expired: {expired_count}"
        )
        
        return {
            'renewed': renewed_count,
            'failed': failed_count,
            'expired': expired_count,
        }
    
    @staticmethod
    def cancel_subscription(user, subscription_id=None):
        """
        Cancel user's subscription
        
        Args:
            user: User instance
            subscription_id: Optional subscription ID, if None cancels active subscription
        
        Returns:
            Subscription instance or None
        """
        if subscription_id:
            subscription = Subscription.objects.filter(
                user=user,
                id=subscription_id
            ).first()
        else:
            subscription = user.active_subscription
        
        if not subscription:
            raise ValueError("No active subscription found")
        
        subscription.cancel()
        
        logger.info(
            f"Subscription cancelled - User: {user.email}, Plan: {subscription.plan}"
        )
        
        return subscription
    
    @staticmethod
    def get_user_subscription(user):
        """Get user's active subscription"""
        return user.active_subscription
    
    @staticmethod
    def get_subscription_info(user):
        """Get subscription information for user"""
        subscription = user.active_subscription
        
        if not subscription:
            return {
                'has_subscription': False,
                'plan': None,
                'status': None,
                'period_end': None,
                'auto_renew': False,
                'monthly_credits': 0,
            }
        
        plan_config = SUBSCRIPTION_PLANS.get(subscription.plan, {})
        
        return {
            'has_subscription': True,
            'plan': subscription.plan,
            'plan_name': plan_config.get('name', subscription.plan),
            'status': subscription.status,
            'start_date': subscription.start_date,
            'period_start': subscription.period_start,
            'period_end': subscription.period_end,
            'next_renewal_date': subscription.next_renewal_date,
            'auto_renew': subscription.auto_renew,
            'monthly_credits': plan_config.get('credits', 0),
            'days_remaining': (subscription.period_end - timezone.now()).days if subscription.period_end and subscription.period_end > timezone.now() else 0,
        }

