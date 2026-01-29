# Generated manually to remove old subscription fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_add_payment_provider'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                # Remove old columns (SQLite doesn't support DROP COLUMN directly)
                """
                CREATE TABLE accounts_subscription_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    auto_renew BOOLEAN NOT NULL DEFAULT 1,
                    start_date DATETIME NOT NULL,
                    period_start DATETIME NULL,
                    period_end DATETIME NULL,
                    next_renewal_date DATETIME NULL,
                    cancelled_at DATETIME NULL,
                    last_renewed_at DATETIME NULL,
                    payment_id VARCHAR(200) NULL,
                    payment_provider VARCHAR(50) NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    user_id INTEGER NOT NULL UNIQUE REFERENCES accounts_user(id) ON DELETE CASCADE
                );
                """,
                # Copy data (exclude old fields: end_date, payment_method, credits_granted, credits_used_this_period)
                """
                INSERT INTO accounts_subscription_new 
                (id, plan, status, auto_renew, start_date, period_start, period_end, next_renewal_date, 
                 cancelled_at, last_renewed_at, payment_id, payment_provider, created_at, updated_at, user_id)
                SELECT 
                    id, 
                    plan,
                    status,
                    auto_renew,
                    start_date,
                    period_start,
                    period_end,
                    COALESCE(next_renewal_date, period_end) as next_renewal_date,
                    cancelled_at,
                    last_renewed_at,
                    payment_id,
                    COALESCE(payment_provider, payment_method) as payment_provider,
                    created_at,
                    updated_at,
                    user_id
                FROM accounts_subscription;
                """,
                # Drop old table
                "DROP TABLE accounts_subscription;",
                # Rename new table
                "ALTER TABLE accounts_subscription_new RENAME TO accounts_subscription;",
            ],
            reverse_sql=[
                # Reverse migration (add back old fields with default values)
                """
                CREATE TABLE accounts_subscription_old (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    auto_renew BOOLEAN NOT NULL DEFAULT 1,
                    start_date DATETIME NOT NULL,
                    end_date DATETIME NULL,
                    period_start DATETIME NULL,
                    period_end DATETIME NULL,
                    next_renewal_date DATETIME NULL,
                    cancelled_at DATETIME NULL,
                    last_renewed_at DATETIME NULL,
                    payment_id VARCHAR(200) NULL,
                    payment_method VARCHAR(50) NULL,
                    payment_provider VARCHAR(50) NULL,
                    credits_granted INTEGER NOT NULL DEFAULT 0,
                    credits_used_this_period INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    user_id INTEGER NOT NULL UNIQUE REFERENCES accounts_user(id) ON DELETE CASCADE
                );
                """,
                """
                INSERT INTO accounts_subscription_old 
                (id, plan, status, auto_renew, start_date, end_date, period_start, period_end, next_renewal_date,
                 cancelled_at, last_renewed_at, payment_id, payment_method, payment_provider, 
                 credits_granted, credits_used_this_period, created_at, updated_at, user_id)
                SELECT 
                    id, 
                    plan,
                    status,
                    auto_renew,
                    start_date,
                    period_end as end_date,
                    period_start,
                    period_end,
                    next_renewal_date,
                    cancelled_at,
                    last_renewed_at,
                    payment_id,
                    payment_provider as payment_method,
                    payment_provider,
                    0 as credits_granted,
                    0 as credits_used_this_period,
                    created_at,
                    updated_at,
                    user_id
                FROM accounts_subscription;
                """,
                "DROP TABLE accounts_subscription;",
                "ALTER TABLE accounts_subscription_old RENAME TO accounts_subscription;",
            ],
        ),
    ]

