"""Replace User FKs with AppInstance FKs across all per-instance models.

Safe to run on the current database because:
  - UserProductAlias, UserPreference, AliasDonation.donated_by, StoreAlias.created_by
    all contain zero rows (no real per-user data exists yet).
  - GlobalProductAlias (687K seed rows) is untouched.
  - AliasDonation.reviewed_by stays as a User FK (admin staff only).
"""
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aliases', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [

        # ── 1. Create AppInstance ────────────────────────────────────
        migrations.CreateModel(
            name='AppInstance',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('instance_id', models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True, serialize=False,
                )),
                ('instance_token_hash', models.CharField(
                    max_length=64,
                    help_text='SHA-256 hex digest of the raw secret. Never store the raw token.',
                )),
                ('platform', models.CharField(blank=True, max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('last_seen_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),

        # ── 2. UserProductAlias: swap user FK → app_instance FK ──────

        # 2a. Drop old unique constraint and index that referenced 'user'
        migrations.RemoveConstraint(
            model_name='userproductalias',
            name='uq_user_receipt_acronym',
        ),
        migrations.RemoveIndex(
            model_name='userproductalias',
            name='idx_user_acronym',
        ),
        # 2b. Remove old user FK
        migrations.RemoveField(
            model_name='userproductalias',
            name='user',
        ),
        # 2c. Add app_instance FK (nullable during migration, then enforce below)
        migrations.AddField(
            model_name='userproductalias',
            name='app_instance',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='product_aliases',
                to='aliases.appinstance',
            ),
        ),
        # 2d. Make app_instance non-nullable
        migrations.AlterField(
            model_name='userproductalias',
            name='app_instance',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='product_aliases',
                to='aliases.appinstance',
            ),
        ),
        # 2e. Restore unique constraint and index under new names
        migrations.AddConstraint(
            model_name='userproductalias',
            constraint=models.UniqueConstraint(
                fields=('app_instance', 'receipt_acronym_upper'),
                name='uq_instance_receipt_acronym',
            ),
        ),
        migrations.AddIndex(
            model_name='userproductalias',
            index=models.Index(
                fields=['app_instance', 'receipt_acronym_upper'],
                name='idx_instance_acronym',
            ),
        ),

        # ── 3. UserPreference: swap user OneToOne → app_instance ─────
        migrations.RemoveField(
            model_name='userpreference',
            name='user',
        ),
        migrations.AddField(
            model_name='userpreference',
            name='app_instance',
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='alias_preferences',
                to='aliases.appinstance',
            ),
        ),
        migrations.AlterField(
            model_name='userpreference',
            name='app_instance',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='alias_preferences',
                to='aliases.appinstance',
            ),
        ),

        # ── 4. AliasDonation.donated_by: User FK → AppInstance FK ────
        migrations.RemoveField(
            model_name='aliasdonation',
            name='donated_by',
        ),
        migrations.AddField(
            model_name='aliasdonation',
            name='donated_by',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='alias_donations',
                to='aliases.appinstance',
            ),
        ),

        # ── 5. StoreAlias.created_by: User FK → AppInstance FK ───────
        migrations.RemoveField(
            model_name='storealias',
            name='created_by',
        ),
        migrations.AddField(
            model_name='storealias',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to='aliases.appinstance',
            ),
        ),
    ]
