"""HELPDESK_ALLOW_NON_STAFF_TICKET_UPDATE is limited to ticket updates.

It must not grant general staff/full-access privileges outside the update flow.
"""

from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.urls import reverse

from helpdesk import settings as helpdesk_settings
from helpdesk.models import KBCategory, KBItem, Queue, Ticket
from helpdesk.user import HelpdeskUser


def allow(value):
    return mock.patch.object(
        helpdesk_settings, "HELPDESK_ALLOW_NON_STAFF_TICKET_UPDATE", value
    )


def only_designated(user):
    return user.is_authenticated and user.username == "designated"


class HasFullAccessTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.other = User.objects.create(username="other")
        self.staff = User.objects.create(username="staff", is_staff=True)

    def full_access(self, user):
        return HelpdeskUser(user).has_full_access()

    def test_callable_does_not_grant_full_access_to_non_staff(self):
        with allow(only_designated):
            designated = get_user_model().objects.create(username="designated")
            self.assertFalse(self.full_access(designated))
            self.assertFalse(self.full_access(self.other))
            self.assertFalse(self.full_access(AnonymousUser()))

    def test_true_does_not_grant_full_access_to_non_staff(self):
        with allow(True):
            self.assertFalse(self.full_access(self.other))
            self.assertFalse(self.full_access(AnonymousUser()))

    def test_false_keeps_full_access_to_staff(self):
        with allow(False):
            self.assertTrue(self.full_access(self.staff))
            self.assertFalse(self.full_access(self.other))
            self.assertFalse(self.full_access(AnonymousUser()))


class PrivateKBCategoryTests(TestCase):
    def setUp(self):
        self.category = KBCategory.objects.create(
            title="Internal procedures",
            slug="internal",
            description="d",
            public=False,
        )
        KBItem.objects.create(
            category=self.category,
            title="Escalation",
            question="Who to call?",
            answer="PRIVATE-ANSWER-42",
        )
        self.url = reverse("helpdesk:kb_category", args=[self.category.slug])

    def test_anonymous_user_cannot_read_private_category_with_callable(self):
        with allow(only_designated):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_cannot_read_private_category_with_true(self):
        with allow(True):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_designated_user_cannot_read_private_category(self):
        user = get_user_model().objects.create(username="designated")
        self.client.force_login(user)
        with allow(only_designated):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


class NonStaffSettingScopeTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="submitter",
            password="password",
            email="submitter@example.com",
        )
        self.queue = Queue.objects.create(title="General", slug="general")
        self.ticket = Ticket.objects.create(
            title="Scoped access",
            queue=self.queue,
            submitter_email=self.user.email,
        )

    def test_non_staff_user_cannot_access_dashboard_when_setting_enabled(self):
        self.client.force_login(self.user)
        with allow(True):
            response = self.client.get(reverse("helpdesk:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("helpdesk:login"), response.url)
