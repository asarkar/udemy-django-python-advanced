from __future__ import annotations

import copy
from http import HTTPStatus
from typing import Any

from core.models import User as CustomUser
from core.tests.factories import UserFactory
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from faker import Faker
from rest_framework.test import APIClient

User: type[CustomUser] = get_user_model()
fake = Faker()


class PublicUserApiTests(TestCase):
    payload: dict[str, Any]
    create_user_url: str
    token_url: str
    me_url: str
    client: APIClient

    @classmethod
    def setUpTestData(cls: type[PublicUserApiTests]) -> None:
        cls.payload = UserFactory.build_dict()
        cls.create_user_url = reverse("user:create")
        cls.token_url = reverse("user:token")
        cls.me_url = reverse("user:me")
        cls.client = APIClient()

    def test_create_user_success(self) -> None:
        res = self.client.post(self.create_user_url, self.payload)

        self.assertEqual(res.status_code, HTTPStatus.CREATED)
        self.assertNotIn("password", res.data)
        login_successful = self.client.login(
            email=self.payload["email"], password=self.payload["password"]
        )
        self.assertTrue(login_successful)

    def test_user_with_email_exists(self) -> None:
        User.objects.create_user(**self.payload)
        res = self.client.post(self.create_user_url, self.payload)

        self.assertEqual(res.status_code, HTTPStatus.BAD_REQUEST)

    def test_password_too_short_error(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["password"] = "pw"
        res = self.client.post(self.create_user_url, payload)

        self.assertEqual(res.status_code, HTTPStatus.BAD_REQUEST)
        user_exists = User.objects.filter(email=payload["email"]).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self) -> None:
        User.objects.create_user(**self.payload)
        payload = {
            "email": self.payload["email"],
            "password": self.payload["password"],
        }
        res = self.client.post(self.token_url, payload)

        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertIn("token", res.data)

    def test_create_token_bad_credentials(self) -> None:
        User.objects.create_user(**self.payload)
        payload = {
            "email": self.payload["email"],
            "password": fake.password(),
        }
        res = self.client.post(self.token_url, payload)

        self.assertEqual(res.status_code, HTTPStatus.BAD_REQUEST)
        self.assertNotIn("token", res.data)

    def test_create_token_blank_password(self) -> None:
        User.objects.create_user(**self.payload)
        payload = {
            "email": self.payload["email"],
            "password": "",
        }
        res = self.client.post(self.token_url, payload)

        self.assertEqual(res.status_code, HTTPStatus.BAD_REQUEST)
        self.assertNotIn("token", res.data)

    def test_retrieve_user_unauthorized(self) -> None:
        res = self.client.get(self.me_url)

        self.assertEqual(res.status_code, HTTPStatus.UNAUTHORIZED)

    class PrivateUserApiTests(TestCase):
        def setUp(self) -> None:
            self.user = UserFactory.create()
            self.client = APIClient()
            self.client.force_authenticate(user=self.user)
            self.me_url = reverse("user:me")

        def test_retrieve_profile_success(self) -> None:
            res = self.client.get(self.me_url)

            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertEqual(
                res.data,  # type: ignore[attr-defined]
                {"name": self.user.name, "email": self.user.email},
            )

        def test_post_me_not_allowed(self) -> None:
            res = self.client.post(self.me_url, {})

            self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

        def test_update_user_profile(self) -> None:
            payload = {"name": fake.name(), "password": fake.password()}

            res = self.client.patch(self.me_url, payload)
            self.user.refresh_from_db()

            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertEqual(self.user.name, payload["name"])
            self.assertTrue(self.user.check_password(payload["password"]))
