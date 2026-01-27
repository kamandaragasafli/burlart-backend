"""
Management command to renew expired subscriptions.
This should be run daily via cron job or scheduled task.

Usage:
    python manage.py renew_subscriptions
"""

from django.core.management.base import BaseCommand
from accounts.services import SubscriptionService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Renew all expired subscriptions that have auto_renew enabled'

    def handle(self, *args, **options):
        self.stdout.write('Starting subscription renewal process...')
        
        try:
            result = SubscriptionService.renew_expired_subscriptions()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Subscription renewal completed: '
                    f'{result["renewed"]} renewed, {result["failed"]} failed'
                )
            )
        except Exception as e:
            logger.error(f"Error in subscription renewal command: {str(e)}", exc_info=True)
            self.stdout.write(
                self.style.ERROR(f'Error renewing subscriptions: {str(e)}')
            )
