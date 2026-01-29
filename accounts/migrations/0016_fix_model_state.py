# Manual migration to fix Django model state
# These fields were already removed from database in migration 0014
# But Django's model state still thinks they exist
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_remove_subscription_credits_granted_and_more'),
    ]

    operations = [
        # This is a no-op migration to fix Django's internal model state
        # The fields were already removed from the database in migration 0014
        # We just need to update Django's knowledge of the model state
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # No database operations needed - fields already removed
            ],
            state_operations=[
                # Tell Django these fields don't exist anymore
                migrations.RemoveField(
                    model_name='subscription',
                    name='credits_granted',
                ),
                migrations.RemoveField(
                    model_name='subscription',
                    name='credits_used_this_period',
                ),
                migrations.RemoveField(
                    model_name='subscription',
                    name='end_date',
                ),
                migrations.RemoveField(
                    model_name='subscription',
                    name='payment_method',
                ),
            ],
        ),
    ]

