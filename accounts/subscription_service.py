"""
Subscription Service
Handles subscription creation, renewal, and credit management
"""
import logging
from django.utils import timezone
from datetime import timedelta
from .models import Subscription, User
from .constants import SUBSCRIPTION_PLANS

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
        
        # Cancel any existing active subscriptions
        existing = Subscription.objects.filter(
            user=user,
            status='active'
        ).exclude(end_date__lt=timezone.now())
        
        for sub in existing:
            sub.cancel()
        
        # Create new subscription
        end_date = timezone.now() + timedelta(days=plan_config['period_days'])
        
        subscription = Subscription.objects.create(
            user=user,
            plan_type=plan_type,
            status='pending',
            auto_renew=auto_renew,
            end_date=end_date,
            payment_id=payment_id,
        )
        
        # Activate and grant credits
        subscription.activate()
        
        logger.info(
            f"Subscription created - User: {user.email}, Plan: {plan_type}, "
            f"Credits: {plan_config['credits']}, Auto-renew: {auto_renew}"
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
            end_date__lte=renew_date,
            end_date__gte=now  # Not already expired
        )
        
        renewed_count = 0
        failed_count = 0
        
        for subscription in subscriptions_to_renew:
            try:
                if subscription.renew():
                    renewed_count += 1
                    logger.info(
                        f"Subscription renewed - User: {subscription.user.email}, "
                        f"Plan: {subscription.plan_type}"
                    )
                else:
                    failed_count += 1
                    logger.warning(
                        f"Subscription renewal failed - User: {subscription.user.email}, "
                        f"Plan: {subscription.plan_type}"
                    )
            except Exception as e:
                failed_count += 1
                logger.error(
                    f"Error renewing subscription - User: {subscription.user.email}, "
                    f"Plan: {subscription.plan_type}, Error: {str(e)}",
                    exc_info=True
                )
        
        # Mark expired subscriptions
        expired = Subscription.objects.filter(
            status='active',
            end_date__lt=now
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
            f"Subscription cancelled - User: {user.email}, Plan: {subscription.plan_type}"
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
                'end_date': None,
                'auto_renew': False,
                'monthly_credits': 0,
            }
        
        plan_config = SUBSCRIPTION_PLANS.get(subscription.plan_type, {})
        
        return {
            'has_subscription': True,
            'plan': subscription.plan_type,
            'plan_name': plan_config.get('name', subscription.plan_type),
            'status': subscription.status,
            'start_date': subscription.start_date,
            'end_date': subscription.end_date,
            'auto_renew': subscription.auto_renew,
            'monthly_credits': plan_config.get('credits', 0),
            'credits_granted': subscription.credits_granted,
            'credits_used_this_period': subscription.credits_used_this_period,
            'days_remaining': (subscription.end_date - timezone.now()).days if subscription.end_date > timezone.now() else 0,
        }

