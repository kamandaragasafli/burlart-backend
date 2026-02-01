"""
Django management command for verifying EPOINT environment variables
İstifadə: python manage.py verify_epoint_env
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Verify EPOINT environment variables from .env file'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('EPOINT Environment Variables Verification'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')

        # Settings-dən key-ləri al
        public_key = getattr(settings, 'EPOINT_PUBLIC_KEY', None)
        secret_key = getattr(settings, 'EPOINT_SECRET_KEY', None)

        # Environment variables-dan da yoxla
        env_public_key = os.getenv('EPOINT_PUBLIC_KEY', None)
        env_secret_key = os.getenv('EPOINT_SECRET_KEY', None)

        self.stdout.write('📋 Django Settings (from .env via decouple):')
        self.stdout.write(f'   EPOINT_PUBLIC_KEY: {public_key}')
        self.stdout.write(f'   EPOINT_PUBLIC_KEY length: {len(public_key) if public_key else 0} chars')
        self.stdout.write('')
        self.stdout.write(f'   EPOINT_SECRET_KEY: {secret_key}')
        self.stdout.write(f'   EPOINT_SECRET_KEY length: {len(secret_key) if secret_key else 0} chars')
        self.stdout.write('')

        self.stdout.write('📋 Environment Variables (direct from os.getenv):')
        self.stdout.write(f'   EPOINT_PUBLIC_KEY: {env_public_key}')
        self.stdout.write(f'   EPOINT_PUBLIC_KEY length: {len(env_public_key) if env_public_key else 0} chars')
        self.stdout.write('')
        self.stdout.write(f'   EPOINT_SECRET_KEY: {env_secret_key}')
        self.stdout.write(f'   EPOINT_SECRET_KEY length: {len(env_secret_key) if env_secret_key else 0} chars')
        self.stdout.write('')

        # Şəkildə görünən key
        expected_secret = 'S0WXEqciyVMOOilbHNuvXuV9'
        self.stdout.write('📋 Şəkildə görünən key:')
        self.stdout.write(f'   {expected_secret}')
        self.stdout.write(f'   Length: {len(expected_secret)} chars')
        self.stdout.write('')

        # Müqayisə
        if secret_key == expected_secret:
            self.stdout.write(self.style.SUCCESS('✅ Django Settings key şəkildəki ilə eynidir!'))
        else:
            self.stdout.write(self.style.ERROR('❌ Django Settings key şəkildəki ilə fərqlidir!'))
            if secret_key and expected_secret:
                for i, (a, b) in enumerate(zip(secret_key, expected_secret)):
                    if a != b:
                        self.stdout.write(f'   Position {i}: Settings="{a}" vs Expected="{b}"')

        self.stdout.write('')
        
        if env_secret_key == expected_secret:
            self.stdout.write(self.style.SUCCESS('✅ Environment Variable key şəkildəki ilə eynidir!'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Environment Variable key şəkildəki ilə fərqlidir!'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')
        self.stdout.write('💡 Tövsiyə:')
        self.stdout.write('   1. .env faylında EPOINT_SECRET_KEY-i yoxlayın')
        self.stdout.write('   2. Key-də boşluq və ya xüsusi simvollar olmamalıdır')
        self.stdout.write('   3. Key quotes olmadan yazılmalıdır: EPOINT_SECRET_KEY=key')
        self.stdout.write('   4. Serveri restart edin')
        self.stdout.write('')

