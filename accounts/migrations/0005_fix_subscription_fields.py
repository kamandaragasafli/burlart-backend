# Manual migration to fix Subscription model fields

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_subscription'),
    ]

    operations = [
        # Rename fields using SQL (SQLite doesn't support RENAME COLUMN directly)
        migrations.RunSQL(
            # SQLite workaround: create new table, copy data, drop old, rename new
            sql=[
                # Create new table with correct structure
                """
                CREATE TABLE accounts_subscription_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    auto_renew BOOLEAN NOT NULL DEFAULT 1,
                    start_date DATETIME NOT NULL,
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
                # Copy data (map old fields to new)
                """
                INSERT INTO accounts_subscription_new 
                (id, plan, status, auto_renew, start_date, next_renewal_date, cancelled_at, 
                 last_renewed_at, payment_id, payment_provider, created_at, updated_at, user_id)
                SELECT 
                    id, 
                    plan_type as plan,
                    status,
                    auto_renew,
                    start_date,
                    end_date as next_renewal_date,
                    cancelled_at,
                    last_renewed_at,
                    payment_id,
                    payment_method as payment_provider,
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
                # Reverse migration
                """
                CREATE TABLE accounts_subscription_old (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_type VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    auto_renew BOOLEAN NOT NULL DEFAULT 1,
                    start_date DATETIME NOT NULL,
                    end_date DATETIME NOT NULL,
                    cancelled_at DATETIME NULL,
                    last_renewed_at DATETIME NULL,
                    payment_id VARCHAR(200) NULL,
                    payment_method VARCHAR(50) NULL,
                    credits_granted INTEGER NOT NULL DEFAULT 0,
                    credits_used_this_period INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    user_id INTEGER NOT NULL REFERENCES accounts_user(id) ON DELETE CASCADE
                );
                """,
                """
                INSERT INTO accounts_subscription_old 
                (id, plan_type, status, auto_renew, start_date, end_date, cancelled_at, 
                 last_renewed_at, payment_id, payment_method, credits_granted, credits_used_this_period,
                 created_at, updated_at, user_id)
                SELECT 
                    id, 
                    plan as plan_type,
                    status,
                    auto_renew,
                    start_date,
                    next_renewal_date as end_date,
                    cancelled_at,
                    last_renewed_at,
                    payment_id,
                    payment_provider as payment_method,
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

