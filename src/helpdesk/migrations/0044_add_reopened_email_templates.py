from django.db import migrations


REOPENED_TEMPLATE_NAMES = {
    "reopened_cc",
    "reopened_owner",
    "reopened_submitter",
}


def forwards_func(apps, schema_editor):
    EmailTemplate = apps.get_model("helpdesk", "EmailTemplate")
    db_alias = schema_editor.connection.alias
    templates = EmailTemplate.objects.using(db_alias)

    for updated_name, reopened_name, heading_map in (
        ("updated_cc", "reopened_cc", {"Ticket Updated": "Ticket Reopened"}),
        ("updated_owner", "reopened_owner", {"Ticket Updated": "Ticket Reopened"}),
        (
            "updated_submitter",
            "reopened_submitter",
            {"Your Ticket Has Been Updated": "Your Ticket Has Been Reopened"},
        ),
    ):
        for template in templates.filter(template_name=updated_name):
            if templates.filter(
                template_name=reopened_name, locale=template.locale
            ).exists():
                continue

            plain_text = template.plain_text.replace(
                "has been updated", "has been reopened"
            ).replace("an update to that ticket", "that ticket has been reopened")
            html = template.html.replace("has been updated", "has been reopened").replace(
                "an update to that ticket", "that ticket has been reopened"
            )

            if updated_name == "updated_submitter":
                plain_text = plain_text.replace(
                    "The following comment was added to ticket {{ ticket.ticket }}:\r\n\r\n{{ comment }}\r\n\r\n",
                    "Ticket {{ ticket.ticket }} has been reopened.\r\n\r\n",
                )
                html = html.replace(
                    "The following comment was added to ticket <b>{{ ticket.ticket }}</b>:</p>\r\n\r\n<blockquote style=\"font-family: sans-serif; font-size: 1em;\">{{ comment }}</blockquote>",
                    "Ticket <b>{{ ticket.ticket }}</b> has been reopened.</p>",
                )
            else:
                plain_text = plain_text.replace(
                    "The following comment was added:\r\n\r\n{{ comment }}\r\n\r\n",
                    "The ticket has been reopened.\r\n\r\n",
                ).replace(
                    "This information has {% if private %}not {% endif %} been e-mailed to the submitter.",
                    "This reopening has {% if private %}not {% endif %} been e-mailed to the submitter.",
                )
                html = html.replace(
                    "The following comment was added:</p>\r\n\r\n<blockquote style=\"font-family: sans-serif; font-size: 1em;\">{{ comment }}</blockquote>",
                    "The ticket has been reopened.</p>",
                ).replace(
                    "This information has {% if private %}not {% endif %} been e-mailed to the submitter.",
                    "This reopening has {% if private %}not {% endif %} been e-mailed to the submitter.",
                )

            templates.create(
                template_name=reopened_name,
                locale=template.locale,
                subject=template.subject.replace("(Updated)", "(Reopened)"),
                heading=heading_map.get(template.heading, template.heading),
                plain_text=plain_text,
                html=html,
            )


def reverse_func(apps, schema_editor):
    EmailTemplate = apps.get_model("helpdesk", "EmailTemplate")
    db_alias = schema_editor.connection.alias
    EmailTemplate.objects.using(db_alias).filter(
        template_name__in=REOPENED_TEMPLATE_NAMES
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("helpdesk", "0043_fix_on_delete_behaviour"),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
