# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_credithold'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='period_start',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='period_end',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('cancelled', 'Cancelled'), ('expired', 'Expired'), ('pending', 'Pending'), ('past_due', 'Past Due')], default='pending', max_length=20),
        ),
    ]

