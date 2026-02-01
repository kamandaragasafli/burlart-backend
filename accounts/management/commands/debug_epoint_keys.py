"""
Django management command for debugging EPOINT keys
İstifadə: python manage.py debug_epoint_keys
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import base64
import hashlib


class Command(BaseCommand):
    help = 'Debug EPOINT keys and signature generation'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('EPOINT Keys Debug'))
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

        self.stdout.write('🔑 Key-lər:')
        self.stdout.write(f'   Public key: {public_key}')
        self.stdout.write(f'   Public key length: {len(public_key)} chars')
        self.stdout.write('')
        self.stdout.write(f'   Private key: {secret_key}')
        self.stdout.write(f'   Private key length: {len(secret_key)} chars')
        self.stdout.write('')
        
        # EPOINT panel-dəki key (istifadəçi tərəfindən təyin edilir)
        # Şəkildə görünən key: S0WXEqciyVMOOilbHNuvXuV9
        # Amma istifadəçi deyir ki, panel-də: S0WXEqciyVMOOi1bHNuvXuV9
        expected_key = 'S0WXEqciyVMOOi1bHNuvXuV9'  # Panel-dəki key (14-cü simvol: 1)
        self.stdout.write('📋 Şəkildə görünən key:')
        self.stdout.write(f'   {expected_key}')
        self.stdout.write(f'   Length: {len(expected_key)} chars')
        self.stdout.write('')
        
        if secret_key == expected_key:
            self.stdout.write(self.style.SUCCESS('✅ Private key şəkildəki ilə eynidir!'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Private key şəkildəki ilə fərqlidir!'))
            self.stdout.write('')
            self.stdout.write('Fərqlər:')
            for i, (a, b) in enumerate(zip(secret_key, expected_key)):
                if a != b:
                    self.stdout.write(f'   Position {i}: Production="{a}" vs Expected="{b}"')
            if len(secret_key) != len(expected_key):
                self.stdout.write(f'   Length fərqi: Production={len(secret_key)} vs Expected={len(expected_key)}')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')
        self.stdout.write('💡 Tövsiyə:')
        self.stdout.write('   1. EPOINT panel-dən private key-i yenidən kopyalayın')
        self.stdout.write('   2. .env faylında EPOINT_SECRET_KEY-i yeniləyin')
        self.stdout.write('   3. Serveri restart edin')
        self.stdout.write('')

