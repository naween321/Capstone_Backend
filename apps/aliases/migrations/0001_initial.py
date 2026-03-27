import django.db.models.deletion
from django.conf import settings
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Enable pg_trgm for trigram similarity queries.
        TrigramExtension(),

        # ── GlobalProductAlias ───────────────────────────────────────
        migrations.CreateModel(
            name='GlobalProductAlias',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('canonical_name', models.CharField(max_length=255)),
                ('alias_text', models.CharField(max_length=255)),
                ('alias_text_upper', models.CharField(db_index=True, max_length=255)),
                ('category', models.CharField(choices=[
                    ('GROCERY', 'Grocery'), ('HOUSEHOLD', 'Household'),
                    ('BEAUTY_CARE', 'Beauty Care'), ('PHARMACY', 'Pharmacy'),
                    ('CLOTHING', 'Clothing'), ('KIDS', 'Kids'),
                    ('BOOKS_OFFICE', 'Books Office'), ('ELECTRONICS', 'Electronics'),
                    ('HOME_DECOR', 'Home Decor'), ('DINING', 'Dining'),
                    ('PET_SUPPLIES', 'Pet Supplies'), ('FUEL_AUTO', 'Fuel Auto'),
                    ('TRAVEL', 'Travel'), ('FEES_TAX', 'Fees Tax'),
                    ('OTHER', 'Other'),
                ], max_length=50)),
                ('source', models.CharField(default='seed', max_length=50)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='globalproductalias',
            constraint=models.UniqueConstraint(
                fields=('canonical_name', 'alias_text_upper'),
                name='uq_canonical_alias',
            ),
        ),

        # ── UserProductAlias ─────────────────────────────────────────
        migrations.CreateModel(
            name='UserProductAlias',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('receipt_acronym', models.CharField(max_length=255)),
                ('receipt_acronym_upper', models.CharField(max_length=255)),
                ('decoded_name', models.CharField(max_length=255)),
                ('category', models.CharField(choices=[
                    ('GROCERY', 'Grocery'), ('HOUSEHOLD', 'Household'),
                    ('BEAUTY_CARE', 'Beauty Care'), ('PHARMACY', 'Pharmacy'),
                    ('CLOTHING', 'Clothing'), ('KIDS', 'Kids'),
                    ('BOOKS_OFFICE', 'Books Office'), ('ELECTRONICS', 'Electronics'),
                    ('HOME_DECOR', 'Home Decor'), ('DINING', 'Dining'),
                    ('PET_SUPPLIES', 'Pet Supplies'), ('FUEL_AUTO', 'Fuel Auto'),
                    ('TRAVEL', 'Travel'), ('FEES_TAX', 'Fees Tax'),
                    ('OTHER', 'Other'),
                ], max_length=50)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='product_aliases',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='userproductalias',
            constraint=models.UniqueConstraint(
                fields=('user', 'receipt_acronym_upper'),
                name='uq_user_receipt_acronym',
            ),
        ),
        migrations.AddIndex(
            model_name='userproductalias',
            index=models.Index(fields=['user', 'receipt_acronym_upper'], name='idx_user_acronym'),
        ),

        # ── StoreAlias ───────────────────────────────────────────────
        migrations.CreateModel(
            name='StoreAlias',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('vendor_name', models.CharField(max_length=255)),
                ('vendor_name_upper', models.CharField(max_length=255, unique=True)),
                ('category', models.CharField(choices=[
                    ('GROCERY', 'Grocery'), ('HOUSEHOLD', 'Household'),
                    ('BEAUTY_CARE', 'Beauty Care'), ('PHARMACY', 'Pharmacy'),
                    ('CLOTHING', 'Clothing'), ('KIDS', 'Kids'),
                    ('BOOKS_OFFICE', 'Books Office'), ('ELECTRONICS', 'Electronics'),
                    ('HOME_DECOR', 'Home Decor'), ('DINING', 'Dining'),
                    ('PET_SUPPLIES', 'Pet Supplies'), ('FUEL_AUTO', 'Fuel Auto'),
                    ('TRAVEL', 'Travel'), ('FEES_TAX', 'Fees Tax'),
                    ('OTHER', 'Other'),
                ], max_length=50)),
                ('source', models.CharField(default='system', max_length=20)),
                ('created_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='+',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.AddIndex(
            model_name='storealias',
            index=models.Index(fields=['vendor_name_upper'], name='idx_store_vendor_upper'),
        ),

        # ── AliasDonation ────────────────────────────────────────────
        migrations.CreateModel(
            name='AliasDonation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('donation_type', models.CharField(choices=[
                    ('product', 'Product'), ('store', 'Store'),
                ], max_length=20)),
                ('receipt_acronym', models.CharField(max_length=255)),
                ('decoded_name', models.CharField(max_length=255)),
                ('category', models.CharField(choices=[
                    ('GROCERY', 'Grocery'), ('HOUSEHOLD', 'Household'),
                    ('BEAUTY_CARE', 'Beauty Care'), ('PHARMACY', 'Pharmacy'),
                    ('CLOTHING', 'Clothing'), ('KIDS', 'Kids'),
                    ('BOOKS_OFFICE', 'Books Office'), ('ELECTRONICS', 'Electronics'),
                    ('HOME_DECOR', 'Home Decor'), ('DINING', 'Dining'),
                    ('PET_SUPPLIES', 'Pet Supplies'), ('FUEL_AUTO', 'Fuel Auto'),
                    ('TRAVEL', 'Travel'), ('FEES_TAX', 'Fees Tax'),
                    ('OTHER', 'Other'),
                ], max_length=50)),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'), ('approved', 'Approved'),
                        ('rejected', 'Rejected'), ('duplicate', 'Duplicate'),
                    ],
                    default='pending', max_length=20,
                )),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('rejection_reason', models.TextField(blank=True)),
                ('donor_trust_score', models.FloatField(default=0.0)),
                ('donated_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='alias_donations',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('reviewed_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='alias_reviews',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='aliasdonation',
            index=models.Index(fields=['status', '-created_at'], name='idx_donation_status'),
        ),

        # ── UserPreference ───────────────────────────────────────────
        migrations.CreateModel(
            name='UserPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('donate_aliases', models.BooleanField(default=False)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='alias_preferences',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),

        # ── GIN trigram index on GlobalProductAlias.alias_text_upper ─
        migrations.RunSQL(
            sql='CREATE INDEX idx_global_alias_trgm ON aliases_globalproductalias USING gin (alias_text_upper gin_trgm_ops);',
            reverse_sql='DROP INDEX IF EXISTS idx_global_alias_trgm;',
        ),
    ]
