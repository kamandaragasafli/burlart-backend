# Generated manually to add next_renewal_date field
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_rename_plan_type_to_plan'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='next_renewal_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

