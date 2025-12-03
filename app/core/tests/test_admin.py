from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from faker import Faker
from rest_framework.test import APIClient

from ..models import User as CustomUser
from .factories import UserFactory

User: type[CustomUser] = get_user_model()


class AdminSiteTests(TestCase):
    fake: Faker
    api_client: APIClient
    admin_user: CustomUser
    user: CustomUser

    @classmethod
    def setUpTestData(cls: type[AdminSiteTests]) -> None:
        cls.fake = Faker()
        cls.api_client = APIClient()
        cls.admin_user = User.objects.create_superuser(cls.fake.email(), cls.fake.password())
        cls.api_client.force_login(cls.admin_user)
        cls.user = User.objects.create_user(**UserFactory.build_dict())

    def test_users_list(self) -> None:
        url = reverse("admin:core_user_changelist")
        res = self.api_client.get(url)

        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)

    def test_edit_user_page(self) -> None:
        url = reverse("admin:core_user_change", args=[self.user.id])
        res = self.api_client.get(url)

        self.assertEqual(res.status_code, HTTPStatus.OK)

    def test_create_user_page(self) -> None:
        url = reverse("admin:core_user_add")
        res = self.api_client.get(url)

        self.assertEqual(res.status_code, HTTPStatus.OK)
