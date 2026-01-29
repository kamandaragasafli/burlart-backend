# Generated manually to fix plan_type -> plan field rename
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_alter_user_managers_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='subscription',
            old_name='plan_type',
            new_name='plan',
        ),
        migrations.AlterField(
            model_name='subscription',
            name='plan',
            field=models.CharField(
                choices=[
                    ('demo', 'Demo'),
                    ('starter', 'Starter'),
                    ('pro', 'Pro'),
                    ('agency', 'Agency'),
                ],
                max_length=20
            ),
        ),
    ]

