# Generated manually to add payment_provider field
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_add_next_renewal_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='payment_provider',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]

