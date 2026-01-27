# Generated manually for Payment model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_creditpurchase'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_type', models.CharField(choices=[('subscription', 'Subscription'), ('topup', 'Top-up')], max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled'), ('refunded', 'Refunded')], default='pending', max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='₼', max_length=10)),
                ('epoint_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('commission', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('commission_rate', models.DecimalField(decimal_places=4, default=0.03, max_digits=5)),
                ('tax', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('tax_rate', models.DecimalField(decimal_places=4, default=0.04, max_digits=5)),
                ('net_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('payment_provider', models.CharField(choices=[('epoint', 'E-point')], default='epoint', max_length=20)),
                ('epoint_transaction_id', models.CharField(blank=True, max_length=200, null=True)),
                ('epoint_response', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('credit_purchase', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='accounts.creditpurchase')),
                ('subscription', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='accounts.subscription')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['user', 'status'], name='accounts_pa_user_id_status_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['payment_type', 'status'], name='accounts_pa_payment_status_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['created_at'], name='accounts_pa_created_idx'),
        ),
    ]

