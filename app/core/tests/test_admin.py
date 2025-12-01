from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from faker import Faker

from ..models import User as CustomUser
from .factories import UserFactory

User: type[CustomUser] = get_user_model()
fake = Faker()


class AdminSiteTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.admin_user = User.objects.create_superuser(fake.email(), fake.password())
        self.client.force_login(self.admin_user)
        self.user = User.objects.create_user(**UserFactory.build_dict())

    def test_users_list(self) -> None:
        url = reverse("admin:core_user_changelist")
        res = self.client.get(url)

        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)

    def test_edit_user_page(self) -> None:
        url = reverse("admin:core_user_change", args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, HTTPStatus.OK)

    def test_create_user_page(self) -> None:
        url = reverse("admin:core_user_add")
        res = self.client.get(url)

        self.assertEqual(res.status_code, HTTPStatus.OK)
