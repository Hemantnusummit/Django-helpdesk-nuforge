from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.test.client import Client
from django.urls import reverse

from helpdesk.models import Queue, Ticket

User = get_user_model()


@override_settings(HELPDESK_VIEW_A_TICKET_PUBLIC=True)
class PublicActionsTestCase(TestCase):
    """
    Tests for public actions:
    - View a ticket
    - Add a followup
    - Close resolved case
    """

    def setUp(self):
        """
        Create a queue & ticket we can use for later tests.
        """
        self.queue = Queue.objects.create(
            title="Queue 1",
            slug="q",
            allow_public_submission=True,
            new_ticket_cc="new.public@example.com",
            updated_ticket_cc="update.public@example.com",
        )
        self.ticket = Ticket.objects.create(
            title="Test Ticket",
            queue=self.queue,
            submitter_email="test.submitter@example.com",
            description="This is a test ticket.",
        )

        self.client = Client()

    def test_public_view_ticket(self):
        # Without key, the public lookup form is shown again with an error.
        response = self.client.get(
            "{}?ticket={}&email={}".format(
                reverse("helpdesk:public_view"),
                self.ticket.ticket_for_url,
                "test.submitter@example.com",
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "helpdesk/public_view_form.html")
        self.assertContains(response, "Invalid ticket ID or e-mail address. Please try again.")
        # With a key it works
        response = self.client.get(
            "{}?ticket={}&email={}&key={}".format(
                reverse("helpdesk:public_view"),
                self.ticket.ticket_for_url,
                "test.submitter@example.com",
                self.ticket.secret_key,
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "helpdesk/public_view_ticket.html")

    def test_authenticated_submitter_can_view_ticket_by_submitter_id(self):
        user = User.objects.create(
            username="submitter",
            email="new-address@example.com",
        )
        self.ticket.submitter_id = user.id
        self.ticket.save(update_fields=["submitter_id"])

        self.client.force_login(user)

        response = self.client.get(
            "{}?ticket={}&email={}".format(
                reverse("helpdesk:public_view"),
                self.ticket.ticket_for_url,
                "test.submitter@example.com",
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "helpdesk/public_view_ticket.html")

    def test_authenticated_user_cannot_view_ticket_without_matching_submitter_id(self):
        user = User.objects.create(
            username="other-user",
            email="test.submitter@example.com",
        )
        self.client.force_login(user)

        response = self.client.get(
            "{}?ticket={}&email={}".format(
                reverse("helpdesk:public_view"),
                self.ticket.ticket_for_url,
                "test.submitter@example.com",
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "helpdesk/public_view_form.html")
        self.assertContains(response, "Invalid ticket ID or e-mail address. Please try again.")

    def test_public_close(self):
        old_status = self.ticket.status
        old_resolution = self.ticket.resolution
        resolution_text = "Resolved by test script"

        ticket = Ticket.objects.get(id=self.ticket.id)

        ticket.status = Ticket.RESOLVED_STATUS
        ticket.resolution = resolution_text
        ticket.save()

        current_followups = ticket.followup_set.all().count()

        response = self.client.get(
            "{}?ticket={}&email={}&close&key={}".format(
                reverse("helpdesk:public_view"),
                ticket.ticket_for_url,
                "test.submitter@example.com",
                ticket.secret_key,
            )
        )

        ticket = Ticket.objects.get(id=self.ticket.id)

        self.assertEqual(response.status_code, 302)
        self.assertTemplateNotUsed(response, "helpdesk/public_view_form.html")
        self.assertEqual(ticket.status, Ticket.CLOSED_STATUS)
        self.assertEqual(ticket.resolution, resolution_text)
        self.assertEqual(current_followups + 1, ticket.followup_set.all().count())

        ticket.resolution = old_resolution
        ticket.status = old_status
        ticket.save()
