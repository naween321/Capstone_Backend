"""Drop the UserProductAlias table.

Per-install alias corrections are stored exclusively in local SQLite on-device.
The server-side mirror added no active value — nothing on the backend read it
to make a decision. Donations are fed directly from the categorize-all request
body, not from stored UserProductAlias rows.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('aliases', '0002_appinstance_refactor'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='userproductalias',
            name='idx_instance_acronym',
        ),
        migrations.RemoveConstraint(
            model_name='userproductalias',
            name='uq_instance_receipt_acronym',
        ),
        migrations.DeleteModel(
            name='UserProductAlias',
        ),
    ]
