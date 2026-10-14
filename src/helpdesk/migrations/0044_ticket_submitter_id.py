from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("helpdesk", "0043_fix_on_delete_behaviour"),
    ]

    operations = [
        migrations.AddField(
            model_name="ticket",
            name="submitter_id",
            field=models.IntegerField(
                blank=True,
                help_text="Authenticated submitter's Django user id, if known.",
                null=True,
                verbose_name="Submitter ID",
            ),
        ),
    ]
