# Generated manually on 2026-02-01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0017_change_default_credits_to_zero'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='credits',
            field=models.IntegerField(default=0),
        ),
    ]

