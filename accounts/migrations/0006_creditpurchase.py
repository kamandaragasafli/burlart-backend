# Generated manually for CreditPurchase model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_fix_subscription_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='CreditPurchase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('package', models.CharField(choices=[('small', 'Small Pack - ₼9.99 - 100 kredit'), ('medium', 'Medium Pack - ₼19.99 - 250 kredit'), ('large', 'Large Pack - ₼34.99 - 500 kredit (+50 bonus)'), ('xlarge', 'X-Large Pack - ₼59.99 - 1000 kredit (+200 bonus)')], max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('credits_purchased', models.IntegerField()),
                ('bonus_credits', models.IntegerField(default=0)),
                ('total_credits', models.IntegerField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='₼', max_length=10)),
                ('payment_id', models.CharField(blank=True, max_length=200, null=True)),
                ('payment_provider', models.CharField(blank=True, max_length=50, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credit_purchases', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]

