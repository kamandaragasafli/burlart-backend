"""
Django management command for testing EPOINT payment integration
İstifadə: python manage.py test_epoint
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.payment_service import EPointService
import json


class Command(BaseCommand):
    help = 'Test EPOINT payment API integration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--amount',
            type=float,
            default=0.10,
            help='Payment amount (default: 0.10)',
        )
        parser.add_argument(
            '--order-id',
            type=str,
            default=None,
            help='Custom order ID (default: auto-generated)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('EPOINT Production Test'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')

        # Key-ləri yoxla
        public_key = getattr(settings, 'EPOINT_PUBLIC_KEY', None)
        secret_key = getattr(settings, 'EPOINT_SECRET_KEY', None)

        if not public_key or not secret_key:
            self.stdout.write(
                self.style.ERROR('❌ XƏTA: EPOINT_PUBLIC_KEY və EPOINT_SECRET_KEY .env faylında təyin edilməlidir')
            )
            return

        self.stdout.write(f'🔑 Key-lər:')
        self.stdout.write(f'   Public key: {public_key}')
        self.stdout.write(f'   Private key length: {len(secret_key)} chars')
        self.stdout.write('')

        # Test parametrləri
        amount = options['amount']
        order_id = options['order_id']
        description = 'Production test payment'

        self.stdout.write(f'📋 Test Parametrləri:')
        self.stdout.write(f'   Amount: {amount} AZN')
        self.stdout.write(f'   Description: {description}')
        if order_id:
            self.stdout.write(f'   Order ID: {order_id}')
        self.stdout.write('')

        # EPOINT service istifadə et
        self.stdout.write('🚀 EPOINT API-yə request göndərilir...')
        self.stdout.write('')

        try:
            result = EPointService.create_payment(
                amount=amount,
                currency='AZN',
                description=description,
                user=None,
                order_id=order_id,
            )

            if result.get('success'):
                self.stdout.write(self.style.SUCCESS('✅ SUCCESS!'))
                self.stdout.write('')
                self.stdout.write('📋 Response:')
                self.stdout.write(json.dumps(result, indent=2, ensure_ascii=False))
                self.stdout.write('')
                
                if 'payment_url' in result:
                    self.stdout.write(f'🔗 Payment URL: {result["payment_url"]}')
                if 'transaction_id' in result:
                    self.stdout.write(f'🆔 Transaction ID: {result["transaction_id"]}')
            else:
                self.stdout.write(self.style.ERROR('❌ ERROR!'))
                self.stdout.write(f'   Message: {result.get("message", "Unknown error")}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ XƏTA: {str(e)}'))
            import traceback
            traceback.print_exc()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))

