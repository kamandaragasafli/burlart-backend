# Generated manually for CreditHold model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_payment'),
    ]

    operations = [
        migrations.CreateModel(
            name='CreditHold',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(choices=[('video', 'Video Generation'), ('image', 'Image Generation')], max_length=20)),
                ('credits_held', models.IntegerField()),
                ('status', models.CharField(choices=[('hold', 'Hold'), ('confirmed', 'Confirmed'), ('released', 'Released')], default='hold', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('confirmed_at', models.DateTimeField(blank=True, null=True)),
                ('released_at', models.DateTimeField(blank=True, null=True)),
                ('image_generation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='credit_hold', to='accounts.imagegeneration')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credit_holds', to=settings.AUTH_USER_MODEL)),
                ('video_generation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='credit_hold', to='accounts.videogeneration')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='credithold',
            index=models.Index(fields=['user', 'status'], name='accounts_cr_user_id_status_idx'),
        ),
        migrations.AddIndex(
            model_name='credithold',
            index=models.Index(fields=['status', 'created_at'], name='accounts_cr_status_created_idx'),
        ),
    ]

